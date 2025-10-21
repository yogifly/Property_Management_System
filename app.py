import streamlit as st
import hashlib, json, time, os, uuid
from typing import List, Dict, Any

# -------------------------
# Data Storage Setup
# -------------------------
DATA_DIR = "data_demo"
CHAIN_FILE = os.path.join(DATA_DIR, "chain.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
PROPS_FILE = os.path.join(DATA_DIR, "properties.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def hash_object(obj: Any) -> str:
    s = json.dumps(obj, sort_keys=True).encode()
    return hashlib.sha256(s).hexdigest()

def now_ts():
    return int(time.time())

# -------------------------
# Blockchain Classes
# -------------------------
class Block:
    def __init__(self, index:int, previous_hash:str, timestamp:int, transactions:List[Dict], nonce:int=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce

    def to_dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "nonce": self.nonce
        }

    def hash(self):
        return hash_object(self.to_dict())

class Blockchain:
    def __init__(self, difficulty=2):
        self.difficulty = difficulty
        self.chain: List[Block] = []
        if os.path.exists(CHAIN_FILE):
            self.load()
        else:
            self.create_genesis()

    def create_genesis(self):
        genesis = Block(0, "0"*64, now_ts(), [{"type":"genesis","msg":"Genesis Block"}], nonce=0)
        self.chain = [genesis]
        self.save()

    def last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, transactions: List[Dict]) -> Block:
        index = len(self.chain)
        previous_hash = self.last_block().hash()
        block = Block(index, previous_hash, now_ts(), transactions)
        mined = self.proof_of_work(block)
        self.chain.append(mined)
        self.save()
        return mined

    def proof_of_work(self, block: Block) -> Block:
        prefix = "0" * self.difficulty
        while True:
            h = block.hash()
            if h.startswith(prefix):
                return block
            block.nonce += 1

    def is_chain_valid(self) -> bool:
        prefix = "0" * self.difficulty
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i-1]
            if curr.previous_hash != prev.hash():
                return False
            if not curr.hash().startswith(prefix):
                return False
        return True

    def to_json(self):
        return [b.to_dict() for b in self.chain]

    def save(self):
        ensure_data_dir()
        with open(CHAIN_FILE, "w") as f:
            json.dump(self.to_json(), f, indent=2)

    def load(self):
        with open(CHAIN_FILE, "r") as f:
            raw = json.load(f)
        self.chain = []
        for b in raw:
            block = Block(b["index"], b["previous_hash"], b["timestamp"], b["transactions"], b.get("nonce",0))
            self.chain.append(block)

# -------------------------
# Accounts & Properties
# -------------------------
def load_accounts():
    ensure_data_dir()
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    else:
        demo = {
            "alice": {"id":"alice", "name":"Alice Demo"},
            "bob": {"id":"bob", "name":"Bob Demo"},
            "carlos": {"id":"carlos", "name":"Carlos Demo"},
        }
        save_accounts(demo)
        return demo

def save_accounts(accounts):
    ensure_data_dir()
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)

def load_properties():
    ensure_data_dir()
    if os.path.exists(PROPS_FILE):
        with open(PROPS_FILE, "r") as f:
            return json.load(f)
    else:
        save_properties({})
        return {}

def save_properties(props):
    ensure_data_dir()
    with open(PROPS_FILE, "w") as f:
        json.dump(props, f, indent=2)

# -------------------------
# Property Logic
# -------------------------
def create_property(props, owner_id, title, description):
    pid = str(uuid.uuid4())
    prop = {
        "id": pid,
        "title": title,
        "description": description,
        "owner": owner_id,
        "created_at": now_ts(),
        "rented_to": None,
        "history": [
            {"type":"created","owner":owner_id,"timestamp":now_ts()}
        ]
    }
    props[pid] = prop
    save_properties(props)
    return prop

def transfer_property(props, property_id, new_owner_id, blockchain:Blockchain):
    if property_id not in props:
        return False, "Property not found"
    prop = props[property_id]
    prev_owner = prop["owner"]
    if new_owner_id == prev_owner:
        return False, "Cannot transfer to same owner"

    tx = {
        "type": "transfer",
        "property_id": property_id,
        "from": prev_owner,
        "to": new_owner_id,
        "timestamp": now_ts()
    }
    block = blockchain.add_block([tx])

    prop["owner"] = new_owner_id
    prop["rented_to"] = None
    prop["history"].append({"type":"transfer","from":prev_owner,"to":new_owner_id,"timestamp":now_ts(),"block_index": block.index})
    save_properties(props)
    return True, block

def rent_property(props, property_id, renter_id, blockchain:Blockchain):
    if property_id not in props:
        return False, "Property not found"
    prop = props[property_id]
    owner = prop["owner"]
    if renter_id == owner:
        return False, "Owner cannot rent to themselves"
    
    tx = {
        "type": "rent",
        "property_id": property_id,
        "owner": owner,
        "renter": renter_id,
        "timestamp": now_ts()
    }
    block = blockchain.add_block([tx])
    prop["rented_to"] = renter_id
    prop["history"].append({"type":"rent","owner":owner,"renter":renter_id,"timestamp":now_ts(),"block_index": block.index})
    save_properties(props)
    return True, block

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="PropertyChain Simplified", layout="wide")
st.title("🏠 PropertyChain — Simplified Property Management System")
st.caption("Create, transfer, and rent properties on a blockchain demo. No money, just ownership tracking.")

ensure_data_dir()
blockchain = Blockchain(difficulty=2)
accounts = load_accounts()
properties = load_properties()

# Sidebar: user selection
st.sidebar.header("Select Active User")
user_id = st.sidebar.selectbox("Active Account", options=list(accounts.keys()), format_func=lambda x: accounts[x]['name'])
if st.sidebar.button("Reload"):
    st.rerun()

# Sidebar: create new user
st.sidebar.markdown("---")
st.sidebar.subheader("Add New User")
new_id = st.sidebar.text_input("New user ID")
new_name = st.sidebar.text_input("New user name")
if st.sidebar.button("Create User"):
    if new_id in accounts:
        st.sidebar.error("User ID already exists.")
    else:
        accounts[new_id] = {"id": new_id, "name": new_name}
        save_accounts(accounts)
        st.sidebar.success(f"User {new_name} added!")
        st.rerun()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Properties", "Create Property", "Transfer / Rent", "Blockchain Explorer"])

# --- View Properties
with tab1:
    st.header("All Properties")
    if not properties:
        st.info("No properties yet. Create one in the next tab.")
    else:
        for pid, p in properties.items():
            st.subheader(f"{p['title']}")
            st.write(f"**Owner:** {accounts.get(p['owner'], {'name':'Unknown'})['name']} ({p['owner']})")
            if p.get('rented_to'):
                st.write(f"**Currently rented to:** {accounts.get(p['rented_to'], {'name':'Unknown'})['name']} ({p['rented_to']})")
            st.write(f"Description: {p['description']}")
            st.write("History:")
            for h in reversed(p['history'][-5:]):
                st.write(h)
            st.markdown("---")

# --- Create Property
with tab2:
    st.header("Create New Property")
    with st.form("create_property"):
        title = st.text_input("Property Title", "Cozy Apartment")
        description = st.text_area("Description", "2BHK with balcony")
        submitted = st.form_submit_button("Create Property")
        if submitted:
            prop = create_property(properties, user_id, title, description)
            tx = {"type":"create_property","property_id":prop["id"],"owner":user_id,"timestamp":now_ts()}
            block = blockchain.add_block([tx])
            st.success(f"Property created by {user_id}. Block #{block.index} mined.")
            st.rerun()

# --- Transfer / Rent
with tab3:
    st.header("Transfer Ownership or Rent Property")

    if not properties:
        st.warning("No properties to modify yet.")
    else:
        selected_pid = st.selectbox("Select Property", options=list(properties.keys()), format_func=lambda x: properties[x]['title'])
        prop = properties[selected_pid]
        st.write(f"Owner: {accounts[prop['owner']]['name']} ({prop['owner']})")
        st.write(f"Rented to: {prop.get('rented_to') if prop.get('rented_to') else 'None'}")

        st.markdown("#### Transfer Ownership")
        new_owner = st.selectbox("Select New Owner", options=[u for u in accounts.keys() if u != prop['owner']])
        if st.button("Transfer Ownership"):
            if user_id != prop['owner']:
                st.error("Only the owner can transfer ownership.")
            else:
                ok, res = transfer_property(properties, selected_pid, new_owner, blockchain)
                if ok:
                    st.success(f"Transferred to {new_owner}. Block #{res.index} mined.")
                    st.rerun()
                else:
                    st.error(res[1])

        st.markdown("#### Rent Property to Another User")
        renter = st.selectbox("Select Renter", options=[u for u in accounts.keys() if u != prop['owner']])
        if st.button("Give on Rent"):
            if user_id != prop['owner']:
                st.error("Only the owner can rent out this property.")
            else:
                ok, res = rent_property(properties, selected_pid, renter, blockchain)
                if ok:
                    st.success(f"Property rented to {renter}. Block #{res.index} mined.")
                    st.rerun()
                else:
                    st.error(res[1])

# --- Blockchain Explorer
with tab4:
    st.header("Blockchain Explorer")
    chain_len = len(blockchain.chain)
    if chain_len <= 1:
        st.info("Only the genesis block exists.")
        num = 1
    else:
        num = st.slider("Show last N blocks", 1, chain_len, min(5, chain_len))

    last_blocks = blockchain.chain[-num:]
    for b in reversed(last_blocks):
        st.subheader(f"Block #{b.index}")
        st.write("Timestamp:", time.ctime(b.timestamp))
        st.write("Prev hash:", b.previous_hash)
        st.write("Nonce:", b.nonce)
        st.write("Transactions:")
        for t in b.transactions:
            st.json(t)
        st.markdown("---")
