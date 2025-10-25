"""
Core data models for the blockchain
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
import time

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.crypto import hash_object, verify_dict_signature, is_valid_address


class TxType(Enum):
    """Transaction types"""
    TRANSFER = "transfer"
    STAKE = "stake"
    UNSTAKE = "unstake"
    DELEGATE = "delegate"
    UNDELEGATE = "undelegate"
    VOTE = "vote"
    CREATE_VALIDATOR = "create_validator"
    EDIT_VALIDATOR = "edit_validator"


class TxStatus(Enum):
    """Transaction status"""
    PENDING = "pending"
    INCLUDED = "included"
    FAILED = "failed"


@dataclass(frozen=True)
class Transaction:
    """Blockchain transaction"""
    sender: str  # Address (40 hex chars)
    sender_pubkey: str = ""  # Public key hex (for verification)
    nonce: int = 0
    tx_type: str = ""  # TxType value
    amount: int = 0
    recipient: Optional[str] = None
    fee: int = 0
    gas_limit: int = 100_000
    data: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    timestamp: int = field(default_factory=lambda: int(time.time()))
    
    def __post_init__(self):
        """Validate transaction"""
        if not is_valid_address(self.sender):
            raise ValueError(f"Invalid sender address: {self.sender}")
        
        if self.recipient and not is_valid_address(self.recipient):
            raise ValueError(f"Invalid recipient address: {self.recipient}")
        
        if self.amount < 0 or self.fee < 0:
            raise ValueError("Amount and fee must be non-negative")
        
        if self.nonce < 0:
            raise ValueError("Nonce must be non-negative")
    
    def payload(self) -> dict:
        """Get signable payload (excludes signature)"""
        return {
            "sender": self.sender,
            "sender_pubkey": self.sender_pubkey,
            "nonce": self.nonce,
            "tx_type": self.tx_type,
            "amount": self.amount,
            "recipient": self.recipient,
            "fee": self.fee,
            "gas_limit": self.gas_limit,
            "data": self.data,
            "timestamp": self.timestamp,
        }
    
    def txid(self) -> str:
        """Get transaction ID (hash of payload)"""
        return hash_object(self.payload())
    
    def sign(self, keypair) -> Transaction:
        """Sign transaction with keypair"""
        from crypto import KeyPair
        # Create payload WITH sender_pubkey before signing
        payload_with_pubkey = {
            **self.payload(),
            "sender_pubkey": keypair.public_key_hex()
        }
        signature = keypair.sign_dict(payload_with_pubkey)
        return Transaction(
            **{
                **self.__dict__, 
                "signature": signature,
                "sender_pubkey": keypair.public_key_hex()
            }
        )
    
    def verify_signature(self) -> bool:
        """Verify transaction signature"""
        if not self.signature or not self.sender_pubkey:
            return False
        try:
            public_key = bytes.fromhex(self.sender_pubkey)
            return verify_dict_signature(public_key, self.payload(), self.signature)
        except (ValueError, TypeError):
            return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> Transaction:
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ValidatorInfo:
    """Validator information"""
    address: str
    public_key: str
    stake: int
    delegated_stake: int
    commission_rate: float  # 0.0 to 1.0
    jailed: bool = False
    jailed_until: int = 0
    total_blocks_proposed: int = 0
    total_blocks_missed: int = 0
    created_at: int = field(default_factory=lambda: int(time.time()))
    
    def total_stake(self) -> int:
        """Total voting power"""
        return self.stake + self.delegated_stake
    
    def is_active(self, current_height: int, min_stake: int) -> bool:
        """Check if validator is active"""
        if self.jailed and current_height < self.jailed_until:
            return False
        return self.total_stake() >= min_stake
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> ValidatorInfo:
        return cls(**data)


@dataclass
class Delegation:
    """Delegation record"""
    delegator: str
    validator: str
    amount: int
    created_at: int = field(default_factory=lambda: int(time.time()))
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> Delegation:
        return cls(**data)


@dataclass
class UnbondingEntry:
    """Unbonding/undelegation entry"""
    address: str
    validator: Optional[str]  # None for unstaking, address for undelegation
    amount: int
    completion_height: int
    created_at: int = field(default_factory=lambda: int(time.time()))
    
    def is_mature(self, current_height: int) -> bool:
        """Check if unbonding is complete"""
        return current_height >= self.completion_height
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> UnbondingEntry:
        return cls(**data)


@dataclass
class Block:
    """Blockchain block"""
    height: int
    prev_hash: str
    timestamp: int
    proposer: str  # Address
    proposer_pubkey: str = ""  # Public key for verification
    transactions: List[Transaction] = field(default_factory=list)
    state_root: str = ""
    validator_set_hash: str = ""
    next_validator_set_hash: str = ""
    consensus_hash: str = ""  # Hash of consensus parameters
    app_hash: str = ""  # Application state hash
    total_fees: int = 0
    block_reward: int = 0
    signature: str = ""
    hash: str = ""
    
    def header(self) -> dict:
        """Get block header"""
        return {
            "height": self.height,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "proposer": self.proposer,
            "proposer_pubkey": self.proposer_pubkey,
            "state_root": self.state_root,
            "validator_set_hash": self.validator_set_hash,
            "next_validator_set_hash": self.next_validator_set_hash,
            "consensus_hash": self.consensus_hash,
            "app_hash": self.app_hash,
            "tx_count": len(self.transactions),
            "tx_merkle_root": self._compute_tx_root(),
            "total_fees": self.total_fees,
            "block_reward": self.block_reward,
        }
    
    def _compute_tx_root(self) -> str:
        """Compute Merkle root of transactions"""
        from crypto import MerkleTree
        if not self.transactions:
            return hash_object("EMPTY")
        txids = [tx.txid() for tx in self.transactions]
        return MerkleTree.compute_root(txids)
    
    def compute_hash(self) -> str:
        """Compute block hash"""
        header_data = self.header()
        header_data["signature"] = self.signature
        return hash_object(header_data)
    
    def sign(self, keypair) -> Block:
        """Sign block with proposer's key"""
        # Create header WITH proposer_pubkey before signing
        header_with_pubkey = {
            **self.header(),
            "proposer_pubkey": keypair.public_key_hex()
        }
        signature = keypair.sign_dict(header_with_pubkey)
        new_block = Block(
            **{
                **self.__dict__, 
                "signature": signature,
                "proposer_pubkey": keypair.public_key_hex()
            }
        )
        new_block.hash = new_block.compute_hash()
        return new_block
    
    def verify_signature(self) -> bool:
        """Verify block signature"""
        if not self.signature or not self.proposer_pubkey:
            return False
        try:
            public_key = bytes.fromhex(self.proposer_pubkey)
            return verify_dict_signature(public_key, self.header(), self.signature)
        except (ValueError, TypeError):
            return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            **asdict(self),
            "transactions": [tx.to_dict() for tx in self.transactions],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Block:
        """Create from dictionary"""
        txs = [Transaction.from_dict(tx) for tx in data.pop("transactions", [])]
        return cls(transactions=txs, **data)


@dataclass
class Vote:
    """Validator vote on a block"""
    validator: str
    height: int
    block_hash: str
    timestamp: int
    signature: str = ""
    
    def payload(self) -> dict:
        return {
            "validator": self.validator,
            "height": self.height,
            "block_hash": self.block_hash,
            "timestamp": self.timestamp,
        }
    
    def sign(self, keypair) -> Vote:
        signature = keypair.sign_dict(self.payload())
        return Vote(**{**self.__dict__, "signature": signature})
    
    def verify_signature(self) -> bool:
        if not self.signature:
            return False
        try:
            public_key = bytes.fromhex(self.validator)
            return verify_dict_signature(public_key, self.payload(), self.signature)
        except (ValueError, TypeError):
            return False


@dataclass
class Evidence:
    """Evidence of misbehavior"""
    evidence_type: str  # "double_sign", "missed_blocks"
    validator: str
    height: int
    timestamp: int
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> Evidence:
        return cls(**data)


if __name__ == "__main__":
    # Test models
    print("=== Data Models Test ===\n")
    
    # Test transaction
    tx = Transaction(
        sender="a" * 40,
        nonce=0,
        tx_type=TxType.TRANSFER.value,
        amount=1000,
        recipient="b" * 40,
        fee=10
    )
    print(f"Transaction ID: {tx.txid()}")
    print(f"Valid sender: {is_valid_address(tx.sender)}")
    
    # Test validator
    val = ValidatorInfo(
        address="v" * 40,
        public_key="pk" * 32,
        stake=10_000,
        delegated_stake=5_000,
        commission_rate=0.1
    )
    print(f"\nValidator total stake: {val.total_stake()}")
    print(f"Active: {val.is_active(0, 1000)}")
