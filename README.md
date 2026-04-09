# UPI Payment System

A simulated **Unified Payments Interface (UPI)** banking system built with Python, SQLite, and socket programming. It replicates core UPI transaction functionality between Users, Merchants, and Banks across a shared LAN.

---

**Group Members**

| Name | ID |
|---|---|
| Chinmayee P | 2021B4A82327H |
| Anuraag Akella | 2021A8PS1887H |
| Hasini Vemula | 2021A8PS1960H |
| Laasya Cheemalamarri | 2021A3PS0993H |
| Srinija Reddy Golipally | 2021B4AA2455H |

---

## Architecture

The system is composed of three key components:

**Bank Server (`bank.py`)** — Hosts all banks and handles user/merchant registrations, validations, and balance updates.

**UPI Machine (`upi_machine.py`)** — Acts as the central node for merchant registration and QR/VMID-based transaction initiation.

**User Client (`user_client.py`)** — Used by customers to register and perform UPI transactions using MMID and VMID.

---

## Features

**User**
- Register with a bank branch using name, IFSC, mobile, password, and UPI PIN
- Receive a UID and MMID (generated via SHA-256)
- Perform transactions using Merchant VMIDs

**Merchant**
- Register via the UPI Machine with name, IFSC, and password
- Receive a MID (Merchant ID) — 16-digit hexadecimal string
- Generate a VMID by encrypting the MID using the SPECK cipher
- VMID is encoded in a QR Code for transaction initiation

**Transaction**
- User provides MMID, PIN, and Merchant VMID
- UPI Machine forwards the transaction to the appropriate Bank Server
- If verified, funds are transferred from User to Merchant

---

## Getting Started

### Prerequisites

- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

> Required packages: `simonshorcipher`, `qrcode`, `pillow`

### 1. Start the Bank Server

```bash
python bank.py
```

Launches the Bank Server with support for HDFC, SBI, and ICICI.

### 2. Register a Merchant

> Before running, replace the IP addresses in `user.py` and `upi_machine.py` with your LAN IP.
> Find your IP using `ipconfig` (Windows) or `ifconfig` (Linux/macOS).

```bash
python upi_machine.py
```

Select option `1` to register a merchant, then option `2` to generate a VMID and QR code.

### 3. Register and Transact as a User

```bash
python user_client.py
```

- Choose `1` to register
- Choose `2` to initiate a transaction — you'll need your MMID, UPI PIN, the merchant's VMID, and the amount

### 4. View the Bank Dashboard

```bash
python bank_dashboard.py
```

Displays registered users, merchants, their details, and transaction history.

---

## Notes

- Replace IP addresses in `user.py` and `upi_machine.py` with your LAN IP (`192.168.x.x` or `172.x.x.x`)
- Ensure your firewall allows connections on ports **8000** and **9001**
- Each user and merchant is linked to a specific bank via their IFSC code
