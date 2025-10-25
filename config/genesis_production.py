"""Unicrium Production Genesis"""
from storage import PersistentStorage as Storage
import hashlib, json, time

FAUCET_ADDRESS = "0xfaucet123456789abcdef123456789abcdef12345"
FAUCET_ALLOCATION = 1_000_000 * 10**8

FOUNDER_ADDRESS = "0xbfb0ccc63e08e83eec1a5f7925ce3a655b530d67"
FOUNDER_ALLOCATION = 10_000_000 * 10**8

TREASURY_ADDRESS = "0xtreasury456789abcdef123456789abcdef12345"
TREASURY_ALLOCATION = 89_000_000 * 10**8

class GenesisBlock:
    def __init__(self, height, prev_hash, timestamp, validator, transactions, block_hash):
        self.height = height
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.validator = validator
        self.proposer = validator
        self.transactions = transactions
        self.hash = block_hash
        self.state_root = "genesis"
        self.validator_set_hash = "genesis"
        self.next_validator_set_hash = "genesis"
    
    def to_dict(self):
        return {
            'height': self.height,
            'prev_hash': self.prev_hash,
            'timestamp': self.timestamp,
            'validator': self.validator,
            'proposer': self.proposer,
            'transactions': self.transactions,
            'hash': self.hash,
            'state_root': self.state_root,
            'validator_set_hash': self.validator_set_hash,
            'next_validator_set_hash': self.next_validator_set_hash
        }

def create_genesis():
    print("Creating Production Genesis...")
    storage = Storage("blockchain_data")
    
    timestamp = int(time.time())
    genesis_data = {
        'height': 0,
        'prev_hash': '0' * 64,
        'timestamp': timestamp,
        'validator': 'genesis',
        'transactions': []
    }
    
    block_string = json.dumps(genesis_data, sort_keys=True)
    genesis_hash = hashlib.sha256(block_string.encode()).hexdigest()
    
    genesis_block = GenesisBlock(
        height=0,
        prev_hash='0' * 64,
        timestamp=timestamp,
        validator='genesis',
        transactions=[],
        block_hash=genesis_hash
    )
    
    storage.save_block(genesis_block)
    
    initial_state = {
        'accounts': {
            FAUCET_ADDRESS: {'balance': FAUCET_ALLOCATION, 'nonce': 0},
            FOUNDER_ADDRESS: {'balance': FOUNDER_ALLOCATION, 'nonce': 0},
            TREASURY_ADDRESS: {'balance': TREASURY_ALLOCATION, 'nonce': 0}
        },
        'total_supply': FAUCET_ALLOCATION + FOUNDER_ALLOCATION + TREASURY_ALLOCATION,
        'genesis_time': timestamp
    }
    
    storage.save_state(initial_state)
    storage.save_metadata({'height': 0, 'latest_hash': genesis_hash, 'genesis_time': timestamp})
    
    print("✅ Genesis created!")
    storage.close()

if __name__ == "__main__":
    create_genesis()
