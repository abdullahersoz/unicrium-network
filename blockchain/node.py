"""
Unicrium Network Node
Full blockchain node
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from blockchain.blockchain import Blockchain
from core.crypto import KeyPair
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Node:
    """Blockchain node"""
    
    def __init__(self, validator_key: str = None):
        self.chain = Blockchain()
        self.validator_key = validator_key
        self.is_validator = validator_key is not None
        
        if self.is_validator:
            self.keypair = KeyPair.from_private_key(validator_key)
            self.address = self.keypair.get_address()
            logger.info(f"Node initialized as validator: {self.address[:10]}...")
        else:
            logger.info("Node initialized in full node mode")
    
    def run(self):
        """Run node"""
        logger.info("🚀 Node starting...")
        logger.info(f"Chain ID: {self.chain.chain_id}")
        logger.info(f"Height: {self.chain.get_height()}")
        logger.info(f"Validators: {len(self.chain.consensus.get_active_validators())}")
        
        if self.is_validator:
            self.run_validator()
        else:
            self.run_full_node()
    
    def run_validator(self):
        """Run as validator"""
        logger.info("🔥 Running as validator...")
        
        while True:
            try:
                # Check if we should propose
                height = self.chain.get_height() + 1
                proposer = self.chain.consensus.select_proposer(height)
                
                if proposer == self.address:
                    logger.info(f"📦 Proposing block {height}")
                    block = self.chain.create_block(self.address)
                    
                    # Sign block
                    block.sign(self.keypair)
                    
                    # Add block
                    if self.chain.add_block(block):
                        logger.info(f"✅ Block {height} added: {block.hash[:16]}...")
                    else:
                        logger.error(f"❌ Block {height} rejected")
                
                time.sleep(6)  # Block time
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(1)
    
    def run_full_node(self):
        """Run as full node"""
        logger.info("📡 Running as full node...")
        
        while True:
            try:
                # Just maintain sync
                time.sleep(10)
                logger.info(f"Height: {self.chain.get_height()}")
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break


if __name__ == "__main__":
    # Get validator key from environment or argument
    validator_key = os.environ.get("VALIDATOR_KEY")
    
    node = Node(validator_key)
    node.run()
