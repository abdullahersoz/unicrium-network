"""
Ledger - State management for the blockchain
Handles balances, stakes, validators, delegations, etc.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from collections import defaultdict
import copy
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from blockchain.models import (
    Transaction, TxType, ValidatorInfo, Delegation, UnbondingEntry
)
from core.crypto import hash_object


@dataclass
class Account:
    """Account state"""
    balance: int = 0
    nonce: int = 0
    staked: int = 0
    
    def to_dict(self) -> dict:
        return {
            "balance": self.balance,
            "nonce": self.nonce,
            "staked": self.staked,
        }


class Ledger:
    """
    Blockchain state manager
    Tracks all accounts, validators, delegations
    """
    
    def __init__(self):
        self.accounts: Dict[str, Account] = defaultdict(Account)
        self.validators: Dict[str, ValidatorInfo] = {}
        self.delegations: Dict[tuple[str, str], Delegation] = {}  # (delegator, validator)
        self.unbonding: List[UnbondingEntry] = []
        
        # Caches
        self._total_supply: Optional[int] = None
        self._total_staked: Optional[int] = None
    
    def snapshot(self) -> dict:
        """Create deterministic snapshot of state"""
        return {
            "accounts": {
                addr: acc.to_dict() 
                for addr, acc in sorted(self.accounts.items())
                if acc.balance > 0 or acc.nonce > 0 or acc.staked > 0
            },
            "validators": {
                addr: val.to_dict() 
                for addr, val in sorted(self.validators.items())
            },
            "delegations": [
                {"delegator": d, "validator": v, **delegation.to_dict()}
                for (d, v), delegation in sorted(self.delegations.items())
            ],
            "unbonding": [
                entry.to_dict() for entry in self.unbonding
            ],
        }
    
    def state_root(self) -> str:
        """Compute state root hash"""
        return hash_object(self.snapshot())
    
    def clone(self) -> Ledger:
        """Create a deep copy of the ledger"""
        new_ledger = Ledger()
        new_ledger.accounts = {
            addr: Account(**acc.to_dict())
            for addr, acc in self.accounts.items()
        }
        new_ledger.validators = {
            addr: ValidatorInfo.from_dict(val.to_dict())
            for addr, val in self.validators.items()
        }
        new_ledger.delegations = {
            key: Delegation.from_dict(delegation.to_dict())
            for key, delegation in self.delegations.items()
        }
        new_ledger.unbonding = [
            UnbondingEntry.from_dict(entry.to_dict())
            for entry in self.unbonding
        ]
        return new_ledger
    
    # Account operations
    def get_balance(self, address: str) -> int:
        """Get account balance"""
        return self.accounts[address].balance
    
    def get_nonce(self, address: str) -> int:
        """Get account nonce"""
        return self.accounts[address].nonce
    
    def get_stake(self, address: str) -> int:
        """Get staked amount"""
        return self.accounts[address].staked
    
    def has_sufficient_balance(self, address: str, amount: int) -> bool:
        """Check if account has sufficient balance"""
        return self.accounts[address].balance >= amount
    
    # Transaction application
    def apply_transaction(self, tx: Transaction, min_stake_unit: int = 1, current_height: int = 0) -> None:
        """Apply a single transaction to state"""
        # Verify signature
        if not tx.verify_signature():
            raise ValueError(f"Invalid signature for tx {tx.txid()}")
        
        # Check nonce
        if self.accounts[tx.sender].nonce != tx.nonce:
            raise ValueError(
                f"Invalid nonce for {tx.sender}: "
                f"expected {self.accounts[tx.sender].nonce}, got {tx.nonce}"
            )
        
        # Check fee
        if tx.fee < 0:
            raise ValueError("Negative fee not allowed")
        
        if not self.has_sufficient_balance(tx.sender, tx.fee):
            raise ValueError(f"Insufficient balance for fee: {tx.sender}")
        
        # Deduct fee
        self.accounts[tx.sender].balance -= tx.fee
        
        # Process by type
        if tx.tx_type == TxType.TRANSFER.value:
            self._apply_transfer(tx)
        elif tx.tx_type == TxType.STAKE.value:
            self._apply_stake(tx, min_stake_unit)
        elif tx.tx_type == TxType.UNSTAKE.value:
            self._apply_unstake(tx, current_height)
        elif tx.tx_type == TxType.DELEGATE.value:
            self._apply_delegate(tx)
        elif tx.tx_type == TxType.UNDELEGATE.value:
            self._apply_undelegate(tx)
        elif tx.tx_type == TxType.CREATE_VALIDATOR.value:
            self._apply_create_validator(tx, min_stake_unit)
        elif tx.tx_type == TxType.EDIT_VALIDATOR.value:
            self._apply_edit_validator(tx)
        else:
            raise ValueError(f"Unknown transaction type: {tx.tx_type}")
        
        # Increment nonce
        self.accounts[tx.sender].nonce += 1
        
        # Invalidate caches
        self._total_supply = None
        self._total_staked = None
    
    def _apply_transfer(self, tx: Transaction) -> None:
        """Apply transfer transaction"""
        if not tx.recipient:
            raise ValueError("Transfer requires recipient")
        
        if tx.amount < 0:
            raise ValueError("Negative amount not allowed")
        
        if not self.has_sufficient_balance(tx.sender, tx.amount):
            raise ValueError(f"Insufficient balance: {tx.sender}")
        
        self.accounts[tx.sender].balance -= tx.amount
        self.accounts[tx.recipient].balance += tx.amount
    
    def _apply_stake(self, tx: Transaction, min_stake_unit: int) -> None:
        """Apply stake transaction (self-stake)"""
        if tx.amount <= 0:
            raise ValueError("Stake amount must be positive")
        
        if tx.amount % min_stake_unit != 0:
            raise ValueError(f"Stake must be multiple of {min_stake_unit}")
        
        if not self.has_sufficient_balance(tx.sender, tx.amount):
            raise ValueError(f"Insufficient balance to stake: {tx.sender}")
        
        self.accounts[tx.sender].balance -= tx.amount
        self.accounts[tx.sender].staked += tx.amount
        
        # Update validator stake if they are a validator
        if tx.sender in self.validators:
            self.validators[tx.sender].stake += tx.amount
    
    def _apply_unstake(self, tx: Transaction, current_height: int = 0, unbonding_blocks: int = 1_814_400) -> None:
        """Apply unstake transaction with proper unbonding period"""
        if tx.amount <= 0:
            raise ValueError("Unstake amount must be positive")
        
        if self.accounts[tx.sender].staked < tx.amount:
            raise ValueError(f"Insufficient staked amount: {tx.sender}")
        
        self.accounts[tx.sender].staked -= tx.amount
        
        # Update validator stake if they are a validator
        if tx.sender in self.validators:
            self.validators[tx.sender].stake -= tx.amount
        
        # FIXED: Create unbonding entry instead of immediate return
        completion_height = current_height + unbonding_blocks
        unbonding_entry = UnbondingEntry(
            address=tx.sender,
            validator=None,  # None for self-unstaking
            amount=tx.amount,
            completion_height=completion_height
        )
        self.unbonding.append(unbonding_entry)
        
        # Funds will be returned when unbonding completes
        # NOT immediately!
    
    def _apply_delegate(self, tx: Transaction) -> None:
        """Apply delegation transaction"""
        if not tx.recipient:
            raise ValueError("Delegate requires validator address")
        
        if tx.recipient not in self.validators:
            raise ValueError(f"Validator not found: {tx.recipient}")
        
        if tx.amount <= 0:
            raise ValueError("Delegation amount must be positive")
        
        if not self.has_sufficient_balance(tx.sender, tx.amount):
            raise ValueError(f"Insufficient balance to delegate: {tx.sender}")
        
        self.accounts[tx.sender].balance -= tx.amount
        
        key = (tx.sender, tx.recipient)
        if key in self.delegations:
            self.delegations[key].amount += tx.amount
        else:
            self.delegations[key] = Delegation(
                delegator=tx.sender,
                validator=tx.recipient,
                amount=tx.amount
            )
        
        self.validators[tx.recipient].delegated_stake += tx.amount
    
    def _apply_undelegate(self, tx: Transaction) -> None:
        """Apply undelegation transaction"""
        if not tx.recipient:
            raise ValueError("Undelegate requires validator address")
        
        key = (tx.sender, tx.recipient)
        if key not in self.delegations:
            raise ValueError(f"No delegation found for {tx.sender} -> {tx.recipient}")
        
        delegation = self.delegations[key]
        if delegation.amount < tx.amount:
            raise ValueError(f"Insufficient delegated amount: {tx.sender}")
        
        delegation.amount -= tx.amount
        if delegation.amount == 0:
            del self.delegations[key]
        
        self.validators[tx.recipient].delegated_stake -= tx.amount
        
        # Return funds immediately (in production: unbonding period)
        self.accounts[tx.sender].balance += tx.amount
    
    def _apply_create_validator(self, tx: Transaction, min_stake_unit: int) -> None:
        """Create new validator"""
        if tx.sender in self.validators:
            raise ValueError(f"Validator already exists: {tx.sender}")
        
        # Parse validator data from tx.data
        commission_rate = tx.data.get("commission_rate", 0.1)
        if not (0 <= commission_rate <= 1):
            raise ValueError("Commission rate must be between 0 and 1")
        
        min_self_stake = tx.data.get("min_self_stake", min_stake_unit)
        if tx.amount < min_self_stake:
            raise ValueError(f"Initial stake must be at least {min_self_stake}")
        
        if not self.has_sufficient_balance(tx.sender, tx.amount):
            raise ValueError(f"Insufficient balance to create validator: {tx.sender}")
        
        # Deduct stake
        self.accounts[tx.sender].balance -= tx.amount
        self.accounts[tx.sender].staked += tx.amount
        
        # Create validator
        self.validators[tx.sender] = ValidatorInfo(
            address=tx.sender,
            public_key=tx.sender,  # Assuming address is derived from public key
            stake=tx.amount,
            delegated_stake=0,
            commission_rate=commission_rate
        )
    
    def _apply_edit_validator(self, tx: Transaction) -> None:
        """Edit validator information"""
        if tx.sender not in self.validators:
            raise ValueError(f"Validator not found: {tx.sender}")
        
        validator = self.validators[tx.sender]
        
        # Update commission rate if provided
        if "commission_rate" in tx.data:
            commission_rate = tx.data["commission_rate"]
            if not (0 <= commission_rate <= 1):
                raise ValueError("Commission rate must be between 0 and 1")
            validator.commission_rate = commission_rate
    
    # Validator operations
    def get_active_validators(self, min_stake: int, current_height: int) -> List[ValidatorInfo]:
        """Get list of active validators"""
        active = [
            val for val in self.validators.values()
            if val.is_active(current_height, min_stake)
        ]
        # Sort by stake (descending) for deterministic ordering
        active.sort(key=lambda v: (-v.total_stake(), v.address))
        return active
    
    def slash_validator(self, validator_addr: str, fraction: float, reason: str) -> int:
        """
        Slash validator stake
        Returns amount slashed
        """
        if validator_addr not in self.validators:
            return 0
        
        validator = self.validators[validator_addr]
        slash_amount = int(validator.total_stake() * fraction)
        
        if slash_amount <= 0:
            return 0
        
        # Slash self-stake first
        self_slash = min(slash_amount, validator.stake)
        validator.stake -= self_slash
        self.accounts[validator_addr].staked -= self_slash
        
        remaining_slash = slash_amount - self_slash
        
        # Slash delegations proportionally
        if remaining_slash > 0 and validator.delegated_stake > 0:
            for (delegator, val_addr), delegation in list(self.delegations.items()):
                if val_addr == validator_addr:
                    delegation_slash = min(
                        remaining_slash,
                        int(delegation.amount * fraction)
                    )
                    delegation.amount -= delegation_slash
                    validator.delegated_stake -= delegation_slash
                    remaining_slash -= delegation_slash
                    
                    if delegation.amount == 0:
                        del self.delegations[(delegator, val_addr)]
        
        return slash_amount
    
    def jail_validator(self, validator_addr: str, until_height: int) -> None:
        """Jail validator until specified height"""
        if validator_addr in self.validators:
            validator = self.validators[validator_addr]
            validator.jailed = True
            validator.jailed_until = until_height
    
    def unjail_validator(self, validator_addr: str) -> None:
        """Unjail validator"""
        if validator_addr in self.validators:
            validator = self.validators[validator_addr]
            validator.jailed = False
            validator.jailed_until = 0
    
    # Block rewards
    def apply_block_reward(self, proposer: str, reward: int, fees: int) -> None:
        """Apply block reward and fees to proposer"""
        total_reward = reward + fees
        if total_reward > 0:
            self.accounts[proposer].balance += total_reward
            self._total_supply = None
    
    # Statistics
    def total_supply(self) -> int:
        """Calculate total supply (cached)"""
        if self._total_supply is None:
            self._total_supply = sum(
                acc.balance + acc.staked
                for acc in self.accounts.values()
            )
        return self._total_supply
    
    def total_staked(self) -> int:
        """Calculate total staked amount (cached)"""
        if self._total_staked is None:
            self._total_staked = sum(
                val.total_stake()
                for val in self.validators.values()
            )
        return self._total_staked
    
    def staking_ratio(self) -> float:
        """Calculate staking ratio"""
        supply = self.total_supply()
        if supply == 0:
            return 0.0
        return self.total_staked() / supply
    
    def process_mature_unbonding(self, current_height: int) -> int:
        """
        Process and complete mature unbonding entries
        Returns number of completed unbondings
        """
        completed = []
        
        for entry in self.unbonding:
            if entry.is_mature(current_height):
                # Return funds to account
                self.accounts[entry.address].balance += entry.amount
                completed.append(entry)
        
        # Remove completed entries
        for entry in completed:
            self.unbonding.remove(entry)
        
        # Invalidate caches
        if completed:
            self._total_supply = None
        
        return len(completed)
    
    def get_unbonding_for_address(self, address: str) -> List[UnbondingEntry]:
        """Get all unbonding entries for an address"""
        return [
            entry for entry in self.unbonding 
            if entry.address == address
        ]


if __name__ == "__main__":
    # Test ledger
    print("=== Ledger Test ===\n")
    
    from crypto import KeyPair
    
    ledger = Ledger()
    
    # Create accounts
    alice = KeyPair.from_seed("alice")
    bob = KeyPair.from_seed("bob")
    
    alice_addr = alice.address()
    bob_addr = bob.address()
    
    # Initialize balances
    ledger.accounts[alice_addr].balance = 10_000
    ledger.accounts[bob_addr].balance = 5_000
    
    print(f"Alice balance: {ledger.get_balance(alice_addr)}")
    print(f"Bob balance: {ledger.get_balance(bob_addr)}")
    print(f"Total supply: {ledger.total_supply()}")
    
    # Create and apply transfer
    tx = Transaction(
        sender=alice_addr,
        nonce=0,
        tx_type=TxType.TRANSFER.value,
        amount=1_000,
        recipient=bob_addr,
        fee=10
    ).sign(alice)
    
    ledger.apply_transaction(tx)
    
    print(f"\nAfter transfer:")
    print(f"Alice balance: {ledger.get_balance(alice_addr)}")
    print(f"Bob balance: {ledger.get_balance(bob_addr)}")
    
    print(f"\nState root: {ledger.state_root()[:32]}...")
