"""
Unicrium Production Blockchain
Complete blockchain with all features integrated
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.pos import ProofOfStake
from core.finality import FinalityManager
from core.slashing import SlashingManager
from core.merkle import compute_tx_root
from storage.storage import PersistentStorage as Storage
from storage.ledger import Ledger
from blockchain.models import Block, Transaction
import time
import logging

logger = logging.getLogger(__name__)


class Blockchain:
    """Production blockchain with all features"""
    
    def __init__(self, chain_id: str = "unicrium-mainnet-1"):
        self.chain_id = chain_id
        self.storage = Storage("blockchain_data")
        self.ledger = Ledger()
        self.consensus = ProofOfStake()
        self.finality = FinalityManager()
        self.slashing = SlashingManager()
        
        self.blocks = []
        self.pending_transactions = []
        
        self._load_state()
        logger.info(f"Blockchain initialized: {len(self.blocks)} blocks")
    
    def _load_state(self):
        """Load blockchain state"""
        meta = self.storage.get_metadata()
        if not meta:
            return
        
        height = int(meta.get('height', -1))
        for h in range(max(0, height - 100), height + 1):
            block = self.storage.load_block(h)
            if block:
                self.blocks.append(block)
        
        # Load ledger state
        state = self.storage.load_state()
        if state:
            self.ledger.load_state(state)
    
    def get_latest_block(self):
        """Get latest block"""
        return self.blocks[-1] if self.blocks else None
    
    def get_height(self):
        """Get current height"""
        return len(self.blocks) - 1 if self.blocks else -1
    
    def add_transaction(self, tx: Transaction) -> bool:
        """Add transaction to mempool"""
        if tx.verify_signature():
            self.pending_transactions.append(tx)
            return True
        return False
    
    def create_block(self, proposer: str) -> Block:
        """Create new block"""
        height = self.get_height() + 1
        prev_block = self.get_latest_block()
        prev_hash = prev_block.hash if prev_block else "0" * 64
        
        # Select transactions
        txs = self.pending_transactions[:100]
        
        # Create block
        block = Block(
            height=height,
            prev_hash=prev_hash,
            timestamp=int(time.time()),
            validator=proposer,
            transactions=txs
        )
        
        # Compute merkle root
        block.tx_root = compute_tx_root(txs)
        
        return block
    
    def add_block(self, block: Block) -> bool:
        """Add block to chain"""
        # Validate
        if not self._validate_block(block):
            return False
        
        # Apply transactions
        for tx in block.transactions:
            try:
                self.ledger.apply_transaction(tx)
            except Exception as e:
                logger.error(f"Failed to apply tx: {e}")
                return False
        
        # Add block
        self.blocks.append(block)
        self.storage.save_block(block)
        
        # Update consensus
        self.consensus.record_block(block.validator)
        
        # Check slashing
        validators = {v.address: v.stake for v in self.consensus.get_active_validators()}
        self.slashing.process_block(block.height, block.validator, block.hash, validators)
        
        # Save state
        self.storage.save_state(self.ledger.get_state())
        self.storage.save_metadata({
            'height': block.height,
            'latest_hash': block.hash
        })
        
        # Remove processed transactions
        self.pending_transactions = [
            tx for tx in self.pending_transactions 
            if tx not in block.transactions
        ]
        
        return True
    
    def _validate_block(self, block: Block) -> bool:
        """Validate block"""
        # Check height
        if block.height != self.get_height() + 1:
            return False
        
        # Check prev hash
        prev_block = self.get_latest_block()
        if prev_block and block.prev_hash != prev_block.hash:
            return False
        
        # Check validator
        validator = self.consensus.get_validator(block.validator)
        if not validator or not validator.is_active:
            return False
        
        return True
    
    def get_balance(self, address: str) -> int:
        """Get account balance"""
        return self.ledger.get_balance(address)
