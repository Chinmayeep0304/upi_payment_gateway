import socket
import json
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
BANK_SERVER_IP = f"{IPAddr}"  # Replace with the actual IP if needed
BANK_SERVER_PORT = 9001

def view_blockchain(bank_name):
    request = {
        "type": "view_blockchain",
        "bank_name": bank_name
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((BANK_SERVER_IP, BANK_SERVER_PORT))
            sock.send(json.dumps(request).encode())
            response_data = sock.recv(4096).decode()
            response = json.loads(response_data)

            if response["status"] == "success":
                print(f"\n[{bank_name} Blockchain]")
                for i, block in enumerate(response["blockchain"]):
                    print(f"Block {i}:")
                    print(f"  Transaction ID: {block['transaction_id']}")
                    print(f"  Previous Hash: {block['previous_hash']}")
                    print(f"  Timestamp: {block['timestamp']}")
                    print(f"  Data: {block['data']}")
                    print(f"  Hash: {block['hash']}")
                    print("-" * 50)
            else:
                print(f"[ERROR] {response['message']}")

    except Exception as e:
        print(f"[ERROR] {e}")

def search_transaction(bank_name, txn_id):
    request = {
        "type": "view_blockchain",
        "bank_name": bank_name
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((BANK_SERVER_IP, BANK_SERVER_PORT))
            sock.send(json.dumps(request).encode())
            response_data = sock.recv(4096).decode()
            response = json.loads(response_data)

            if response["status"] == "success":
                for block in response["blockchain"]:
                    if block["transaction_id"] == txn_id:
                        print(f"\nTransaction Found in {bank_name} Blockchain:")
                        print(f"  Transaction ID: {block['transaction_id']}")
                        print(f"  Previous Hash: {block['previous_hash']}")
                        print(f"  Timestamp: {block['timestamp']}")
                        print(f"  Data: {block['data']}")
                        print(f"  Hash: {block['hash']}")
                        return
                print(f"[INFO] Transaction ID {txn_id} not found in {bank_name} Blockchain.")
            else:
                print(f"[ERROR] {response['message']}")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    while True:
        print("\nBlockchain Explorer")
        print("1. View HDFC Blockchain")
        print("2. View ICICI Blockchain")
        print("3. View SBI Blockchain")
        print("4. Search for a Transaction")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            view_blockchain("HDFC")
        elif choice == "2":
            view_blockchain("ICICI")
        elif choice == "3":
            view_blockchain("SBI")
        elif choice == "4":
            bank_name = input("Enter bank name (HDFC/ICICI/SBI): ").strip()
            txn_id = input("Enter transaction ID: ").strip()
            search_transaction(bank_name, txn_id)
        elif choice == "5":
            print("Exiting Blockchain Explorer.")
            break
        else:
            print("Invalid choice. Please try again.")