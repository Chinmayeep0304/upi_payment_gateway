import socket
import json
import threading
import uuid
from speck import SpeckCipher
import qrcode
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
UPI_MACHINE_HOST = f"{IPAddr}" 
UPI_MACHINE_PORT = 8000

BANK_SERVER_IP = f"{IPAddr}" # Replace with the actual IP of machine hosting BANK_SERVER
BANK_SERVER_PORT = 9001

# ✅ Global merchant info
MERCHANT_IFSC = None
MERCHANT_MID = None
MERCHANT_VMID = None

def register_merchant():
    print("\n[Merchant Registration]")
    name = input("Enter merchant name: ")
    password = input("Set password: ")
    ifsc = input("Enter IFSC code (e.g., HDFC001): ")
    balance = float(input("Initial balance: "))

    merchant_data = {
        "type": "register",
        "account_type": "merchant",
        "name": name,
        "password": password,
        "ifsc": ifsc,
        "balance": balance
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((BANK_SERVER_IP, BANK_SERVER_PORT))
            sock.send(json.dumps(merchant_data).encode())
            response_data = sock.recv(2048).decode()
            response = json.loads(response_data)
            print(f"[Bank Response] {response}")
    except Exception as e:
        print(f"[Error] {e}")

def forward_transaction_to_bank(transaction):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as bank_sock:
            bank_sock.connect((BANK_SERVER_IP, BANK_SERVER_PORT))
            bank_sock.send(json.dumps(transaction).encode())
            response_data = bank_sock.recv(2048).decode()
            return json.loads(response_data)
    except Exception as e:
        return {"status": "error", "message": str(e)}

def handle_user_transaction(client_sock, addr):
    try:
        data = client_sock.recv(2048).decode()
        transaction = json.loads(data)
        print(f"[UPI] Received transaction from {addr}")

        # Forward transaction to bank
        response = forward_transaction_to_bank(transaction)
        print(f"[UPI] Bank responded: {response}")

        # Send response back to user
        client_sock.send(json.dumps(response).encode())
    except Exception as e:
        client_sock.send(json.dumps({"status": "error", "message": str(e)}).encode())
    finally:
        client_sock.close()

def generate_vmid(mid_hex):
    # Ensure MID is a 16-digit hex
    if len(mid_hex) != 16:
        raise ValueError("MID must be a 16-digit hex string")

    # Convert MID to integer
    mid_int = int(mid_hex, 16)

    # Initialize Speck Cipher (64-bit block, 96-bit key)
    key = 0x123456789ABCDEF123456789  # 96-bit key
    cipher = SpeckCipher(key, key_size=96, block_size=64)

    # Encrypt the MID
    vmid_int = cipher.encrypt(mid_int)

    # Convert to hex string for VMID
    vmid_hex = hex(vmid_int)[2:].zfill(16)

    return vmid_hex

def generate_vmid_qr(vmid_hex):
    qr = qrcode.make(vmid_hex)
    qr.save("vmid_qr.png")
    print(f"QR Code saved as vmid_qr.png")

def start_upi_transaction_listener():
    global MERCHANT_MID, MERCHANT_IFSC, MERCHANT_VMID

    MERCHANT_MID = input("Enter your 16-digit Merchant ID (MID): ").strip()
    if len(MERCHANT_MID) != 16:
        print("Invalid MID length. Must be 16 hexadecimal digits.")
        return
    MERCHANT_VMID = generate_vmid(MERCHANT_MID)

    print(f"[VMID] Generated VMID: {MERCHANT_VMID}")
    generate_vmid_qr(MERCHANT_VMID)  # Optional

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((UPI_MACHINE_HOST, UPI_MACHINE_PORT))
    server_socket.listen(5)
    print(f"[UPI] UPI Machine listening on {UPI_MACHINE_PORT}...")

    while True:
        client_sock, addr = server_socket.accept()
        threading.Thread(target=handle_user_transaction, args=(client_sock, addr)).start()

if __name__ == "__main__":
    while True:
        print("\nSelect action:")
        print("1. Register a Merchant")
        print("2. Generate QR Code for UPI Transactions")
        print("3. Exit")
    
        choice = input("Enter choice: ").strip()
        if choice == "1":
            register_merchant()
        elif choice == "2":
            start_upi_transaction_listener()
        elif choice == "3":
            break
        else:
            print("Invalid choice.")

