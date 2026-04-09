import sqlite3
from prettytable import PrettyTable

def display_users():
    conn = sqlite3.connect("bank_data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username, balance, bank, ifsc, uid, mobile, mmid FROM users")
    users = cursor.fetchall()

    if users:
        table = PrettyTable()
        table.field_names = ["Username", "Balance", "Bank", "IFSC", "UID", "Mobile", "MMID"]
        for user in users:
            table.add_row(user)
        print("\n[All Users]")
        print(table)
    else:
        print("\n[No Users Found]")

    conn.close()

def display_merchants():
    conn = sqlite3.connect("bank_data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, balance, bank, ifsc, mid FROM merchants")
    merchants = cursor.fetchall()

    if merchants:
        table = PrettyTable()
        table.field_names = ["Merchant Name", "Balance", "Bank", "IFSC", "MID"]
        for merchant in merchants:
            table.add_row(merchant)
        print("\n[All Merchants]")
        print(table)
    else:
        print("\n[No Merchants Found]")

    conn.close()

if __name__ == "__main__":
    while True:
        print("\nBank Dashboard")
        print("1. Display All Users")
        print("2. Display All Merchants")
        print("3. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            display_users()
        elif choice == "2":
            display_merchants()
        elif choice == "3":
            print("Exiting Bank Dashboard. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")