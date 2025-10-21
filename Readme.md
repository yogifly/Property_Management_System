# 🏠 PropertyChain — Blockchain Property Management

PropertyChain is a demo project that simulates property management on a blockchain.  
It allows users to **create properties, transfer ownership, and rent properties**, all recorded on a blockchain ledger.  
This is a **simplified version** without any money or balance transactions, intended for demonstration and learning purposes.

---

## Features

- Default demo users: Alice, Bob, Carlos  
- Add new users dynamically  
- Create properties by any user  
- Transfer property ownership (on-chain)  
- Rent a property to another user (owner stays the same)  
- View property history and blockchain transactions  
- Blockchain explorer with proof-of-work simulation  
- Fully functional in **Streamlit** with a simple UI

---

## Tech Stack

- Python 3.10+  
- Streamlit  
- JSON files for storage (`accounts.json`, `properties.json`, `chain.json`)  
- hashlib for blockchain hashing  
- UUID for property IDs

## Project Structure

```bash
propertychain/
│
├── app.py              # Main Streamlit app
├── README.md           # Project documentation
└── data_demo/          # Stores blockchain, users, and properties
    ├── accounts.json
    ├── properties.json
    └── chain.json
``` 
## Usage
1. Select Active User
Use the sidebar to select one of the default users or create a new user.

2. Create Property
Navigate to the Create Property tab to add a new property with title and description.
All created properties are recorded on the blockchain.

3. Transfer Ownership
Go to Transfer / Rent tab.
Only the owner can transfer ownership to another user.
Property history is updated in the blockchain.

4. Rent Property
Owner can rent a property to any other user without changing the owner.
Rented properties are tracked in the property data and blockchain.

5. Blockchain Explorer
View the last N blocks of the blockchain.
Each block shows all transactions (property creation, transfer, rent).
Proof-of-work is simulated with adjustable difficulty.
