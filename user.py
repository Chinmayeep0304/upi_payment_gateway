import socket
import json
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
UPI_MACHINE_IP = "172.20.10.6"  # Replace with the actual IP of machine hosting UPI_MACHINE
UPI_MACHINE_PORT = 8000

BANK_SERVER_IP = "172.20.10.6"  # Replace with the actual IP of machine hosting BANK_SERVER
BANK_SERVER_PORT = 9001

def register_user():
    print("\n[User Registration]")
    name = input("Enter your name: ")
    password = input("Set password: ")
    pin = input("Set 4-digit UPI PIN: ")
    ifsc = input("Enter IFSC code (e.g., HDFC001): ")
    mobile = input("Enter your mobile number: ")
    balance = float(input("Initial balance: "))

    user_data = {
        "type": "register",
        "account_type": "user",
        "name": name,
        "password": password,
        "pin": pin,
        "ifsc": ifsc,
        "balance": balance,
        "mobile": mobile,
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((BANK_SERVER_IP, BANK_SERVER_PORT))
            sock.send(json.dumps(user_data).encode())
            response_data = sock.recv(2048).decode()
            response = json.loads(response_data)
            print(f"[Bank Response] {response}")
    except Exception as e:
        print(f"[Error] {e}")

def perform_transaction():
    print("\n[Perform UPI Transaction]")
    
    txn = {
        "type": "transaction",
        "to": {
            "vmid": input("Enter merchant VMID: ").strip(),
        },
        "from": {
            "mmid": input("Enter your MMID: ").strip(),
            "pin": input("Enter UPI PIN: ").strip()
        },
        "amount": float(input("Enter amount to pay: "))
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((UPI_MACHINE_IP, UPI_MACHINE_PORT))
            sock.send(json.dumps(txn).encode())

            print(f"[User] Sent transaction request to UPI machine.")

            response_data = sock.recv(2048).decode()
            response = json.loads(response_data)
            print(f"[User] Received response: {response}")

    except Exception as e:
        print(f"[User] Error: {e}")


if __name__ == "__main__":
    while True:
        print("\nSelect action:")
        print("1. Register as User")
        print("2. Perform UPI Transaction")
        print("3. Exit")
        choice = input("Enter choice: ").strip()
    
        if choice == "1":
            register_user()
        elif choice == "2":
            perform_transaction()
        elif choice == "3":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid option.")


