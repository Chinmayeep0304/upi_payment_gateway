import socket
import json
import sqlite3
import hashlib
import time
from speck import SpeckCipher  # Make sure speck.py is in your project directory
from blockchain import Block,Blockchain  # Make sure blockchain.py is in your project directory
from datetime import datetime
# Constants
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
BANK_NAME = "Central Bank Server"
BANK_HOST = f"{IPAddr}" 
BANK_PORT = 9001  # Keep this open on your UPI Machine

# Valid IFSCs for verification only
branches = {
    "HDFC001": {}, "HDFC002": {}, "HDFC003": {},
    "SBI001": {}, "SBI002": {}, "SBI003": {},
    "ICICI001": {}, "ICICI002": {}, "ICICI003": {},
}
hdfc_blockchain = Blockchain()
icici_blockchain = Blockchain()
sbi_blockchain = Blockchain()

def get_bank_from_ifsc(ifsc):
    if ifsc.startswith("HDFC"):
        return "HDFC"
    elif ifsc.startswith("SBI"):
        return "SBI"
    elif ifsc.startswith("ICICI"):
        return "ICICI"
    else:
        return "UNKNOWN"

def generate_mid(name, password):
    timestamp = str(time.time())
    raw_string = name + password + timestamp
    hash_object = hashlib.sha256(raw_string.encode())
    hex_digest = hash_object.hexdigest()
    return hex_digest[:16]  # 16-digit hex MID


def generate_uid(name, password):
    timestamp = str(time.time())
    raw_string = name + password + timestamp
    hash_object = hashlib.sha256(raw_string.encode())
    return hash_object.hexdigest()[:16]

def generate_mmid(uid, mobile):
    raw_string = uid + mobile
    hash_object = hashlib.sha256(raw_string.encode())
    return hash_object.hexdigest()[:16]


def register_account(data):
    account_type = data.get("account_type")  # "user" or "merchant"
    name = data.get("name")
    password = data.get("password")
    pin = data.get("pin")  # Users only
    ifsc = data.get("ifsc")
    balance = float(data.get("balance", 0))

    if not (name and password and ifsc):
        return {"status": "error", "message": "Missing required fields."}

    if ifsc not in branches:
        return {"status": "error", "message": f"Invalid IFSC code: {ifsc}"}

    conn = sqlite3.connect("bank_data.db")
    cursor = conn.cursor()

    try:
        if account_type == "user":
            mobile = data.get("mobile")
            cursor.execute("SELECT * FROM users WHERE username = ?", (name,))
            if cursor.fetchone():
                return {"status": "error", "message": f"User '{name}' already exists."}
            if not pin:
                return {"status": "error", "message": "User registration requires UPI PIN."}
            if len(pin) < 4 or not pin.isdigit():
                return {"status": "error", "message": "UPIP PIN must be at least 4 digits."}
            uid = generate_uid(name, password)
            mmid = generate_mmid(uid, mobile)
            cursor.execute("""
                INSERT INTO users (username, password, pin, balance, bank, ifsc, uid, mobile, mmid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, password, pin, balance, get_bank_from_ifsc(ifsc), ifsc, uid, mobile, mmid))
            conn.commit()
            return {
                "status": "success",
                "message": f"User '{name}' registered in {ifsc}, UID: {uid}, MMID: {mmid}."
            }

        elif account_type == "merchant":
            cursor.execute("SELECT * FROM merchants WHERE name = ?", (name,))
            if cursor.fetchone():
                return {"status": "error", "message": f"Merchant '{name}' already exists."}
            mid = generate_mid(name, password)
            cursor.execute("""
                INSERT INTO merchants (name, password, balance, bank, ifsc, mid)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, password, balance, get_bank_from_ifsc(ifsc), ifsc, mid))
            conn.commit()
            return {
                "status": "success",
                "message": f"Merchant '{name}' registered in {ifsc}, MID: {mid}."
            }

        else:
            return {"status": "error", "message": "Invalid account type."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

def decrypt_vmid(vmid_hex):
    try:
        # Convert the VMID from hex to an integer
        vmid_int = int(vmid_hex, 16)
        
        # Initialize Speck Cipher (64-bit block, 96-bit key)
        key = 0x123456789ABCDEF123456789  # 96-bit key
        cipher = SpeckCipher(key, key_size=96, block_size=64)

        # Decrypt the VMID
        mid_int = cipher.decrypt(vmid_int)

        # Convert the decrypted integer to a hex string
        mid_hex = hex(mid_int)[2:].zfill(16)  # Ensure it's 16 characters long

        return mid_hex
    except Exception as e:
        raise ValueError(f"Failed to decrypt VMID: {e}")

def handle_transaction(data):
    conn = sqlite3.connect("bank_data.db")
    cursor = conn.cursor()
    try:
        from_data = data["from"]
        to_data = data["to"]

        amount = float(data["amount"])

        mmid = from_data["mmid"]
        pin = from_data["pin"]

        vmid = to_data["vmid"]
        print(vmid)

        

        # Lookup user by MMID
        cursor.execute("SELECT * FROM users WHERE mmid = ?", (mmid,))
        sender = cursor.fetchone()
        if not sender:
            return {"status": "error", "message": "User not found."}
        if sender[2] != pin:
            return {"status": "error", "message": "Invalid UPI PIN."}
        if sender[3] < amount:
            return {"status": "error", "message": "Insufficient balance."}

        from_name = sender[0]
        from_ifsc = sender[5]

        # Decrypt VMID ➝ Get MID ➝ Lookup merchant
        mid = decrypt_vmid(vmid)
        print(mid)
        # Check if MID exists
        cursor.execute("SELECT * FROM merchants WHERE mid = ?", (mid,))
        receiver = cursor.fetchone()
        if not receiver:
            return {"status": "error", "message": f"Invalid VMID."}
        
        

        to_name = receiver[0]  # Merchant name
        to_ifsc = receiver[4]  # Merchant IFSC
        # Perform transaction
        new_sender_balance = sender[3] - amount
        new_receiver_balance = receiver[2] + amount

        txn_id = hashlib.sha256(f"{sender[6]}{mid}{datetime.now()}{amount}".encode()).hexdigest() # Generate a unique transaction ID here from blockchain
        cursor.execute("UPDATE users SET balance = ? WHERE mmid = ?", (new_sender_balance, mmid))
        cursor.execute("UPDATE merchants SET balance = ? WHERE mid = ?", (new_receiver_balance, mid))
        cursor.execute("""
            INSERT INTO transactions (txn_id, from_user, from_ifsc, to_merchant, to_ifsc, amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (txn_id, from_name, from_ifsc, to_name, to_ifsc, amount, "approved"))
        conn.commit()
        sender_bank = get_bank_from_ifsc(from_ifsc)
        receiver_bank = get_bank_from_ifsc(to_ifsc)
        blockchains = {
            "HDFC": hdfc_blockchain,
            "ICICI": icici_blockchain,
            "SBI": sbi_blockchain
        }
        if sender_bank in blockchains:
            previous_hash = blockchains[sender_bank].get_latest_block().hash
            blockchains[sender_bank].add_block(Block(
                txn_id, previous_hash, str(datetime.now()), {  # Updated to use time.time()
                    "from_user": from_name,
                    "to_merchant": to_name,
                    "amount": amount
                }
            ))

        # Add transaction to receiver's bank blockchain (if different)
        if sender_bank != receiver_bank and receiver_bank in blockchains:
            previous_hash = blockchains[receiver_bank].get_latest_block().hash
            blockchains[receiver_bank].add_block(Block(
                txn_id, previous_hash, str(datetime.now()), {
                    "from_user": from_name,
                    "to_merchant": to_name,
                    "amount": amount
                }
            ))

        print(f"[{BANK_NAME}] ✅ TXN SUCCESS - ID: {txn_id} | ₹{amount} | {from_name} ({from_ifsc}) ➝ {to_name} ({to_ifsc})")

        return {
            "status": "approved",
            "message": "Transaction successful.",
            "transaction_id": txn_id
        }

    except Exception as e:
        return {"status": "error", "message": f"Transaction failed: {str(e)}"}
    finally:
        conn.close()

def handle_connection(sock, address):
    print(f"[{BANK_NAME}] Connected to client at {address}")
    try:
        data = sock.recv(2048).decode()
        request = json.loads(data)

        request_type = request.get("type")

        if request_type == "register":
            response = register_account(request)
        elif request_type == "transaction":
            response = handle_transaction(request)
        elif request_type == "view_blockchain":
            bank_name = request.get("bank_name")
            response = get_blockchain_data(bank_name)
        else:
            response = {"status": "error", "message": "Unknown request type."}

        sock.send(json.dumps(response).encode())

    except Exception as e:
        print(f"[ERROR] {e}")
        sock.send(json.dumps({"status": "error", "message": str(e)}).encode())
    finally:
        sock.close()

def start_bank_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((BANK_HOST, BANK_PORT))
    server_socket.listen(5)
    print(f"[{BANK_NAME}] Bank Server is listening on {BANK_HOST}:{BANK_PORT}...")

    while True:
        sock, addr = server_socket.accept()
        handle_connection(sock, addr)


def init_db():
    conn = sqlite3.connect("bank_data.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        pin TEXT NOT NULL,
        balance REAL NOT NULL,
        bank TEXT NOT NULL,
        ifsc TEXT NOT NULL,
        uid TEXT UNIQUE NOT NULL,
        mobile TEXT NOT NULL,
        mmid TEXT UNIQUE NOT NULL
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merchants (
        name TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        balance REAL NOT NULL,
        bank TEXT NOT NULL,
        ifsc TEXT NOT NULL,
        mid TEXT UNIQUE NOT NULL
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        txn_id TEXT PRIMARY KEY,
        from_user TEXT NOT NULL,
        from_ifsc TEXT NOT NULL,
        to_merchant TEXT NOT NULL,
        to_ifsc TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    
    



    conn.commit()
    conn.close()

def get_blockchain_data(bank_name):
    blockchains = {
        "HDFC": hdfc_blockchain,
        "ICICI": icici_blockchain,
        "SBI": sbi_blockchain
    }

    if bank_name not in blockchains:
        return {"status": "error", "message": f"Invalid bank name: {bank_name}"}

    blockchain = blockchains[bank_name]
    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            "transaction_id": block.transaction_id,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp,
            "data": block.data,
            "hash": block.hash
        })

    return {"status": "success", "blockchain": chain_data}

if __name__ == "__main__":
    init_db()
    start_bank_server()
