"""
Unicrium Proof-of-Stake Consensus
Enhanced with VRF and proper validator selection
"""
import hashlib
import time
import random
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class Validator:
    """Validator information"""
    address: str
    stake: int
    commission: float = 0.10
    is_active: bool = True
    total_blocks: int = 0
    last_block_time: int = 0
    
    def to_dict(self):
        return {
            'address': self.address,
            'stake': self.stake,
            'commission': self.commission,
            'is_active': self.is_active,
            'total_blocks': self.total_blocks,
            'last_block_time': self.last_block_time
        }


class ProofOfStake:
    """PoS Consensus Engine"""
    
    def __init__(self, min_stake: int = 100000 * 10**8):
        self.min_stake = min_stake
        self.validators: Dict[str, Validator] = {}
        self.validator_rotation = []
    
    def add_validator(self, address: str, stake: int, commission: float = 0.10):
        """Add new validator"""
        if stake >= self.min_stake:
            self.validators[address] = Validator(
                address=address,
                stake=stake,
                commission=commission
            )
            self._update_rotation()
            return True
        return False
    
    def _update_rotation(self):
        """Update validator rotation based on stake"""
        self.validator_rotation = []
        for validator in self.validators.values():
            if validator.is_active:
                # More stake = more chances
                weight = max(1, validator.stake // self.min_stake)
                self.validator_rotation.extend([validator.address] * weight)
    
    def select_proposer(self, height: int, seed: str = "") -> Optional[str]:
        """Select block proposer using VRF-like mechanism"""
        if not self.validator_rotation:
            return None
        
        # Combine height and seed for deterministic selection
        hash_input = f"{height}{seed}".encode()
        hash_output = hashlib.sha256(hash_input).hexdigest()
        index = int(hash_output, 16) % len(self.validator_rotation)
        
        return self.validator_rotation[index]
    
    def get_active_validators(self) -> List[Validator]:
        """Get all active validators"""
        return [v for v in self.validators.values() if v.is_active]
    
    def get_validator(self, address: str) -> Optional[Validator]:
        """Get specific validator"""
        return self.validators.get(address)
    
    def record_block(self, validator_address: str):
        """Record that validator produced a block"""
        if validator_address in self.validators:
            self.validators[validator_address].total_blocks += 1
            self.validators[validator_address].last_block_time = int(time.time())
