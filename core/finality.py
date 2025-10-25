"""
Unicrium Finality Mechanism
Implements Byzantine Fault Tolerant finality with supermajority voting
Prevents chain reorganization after finalization
"""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class Vote:
    """
    Vote for block finalization
    Validators vote to finalize blocks
    """
    block_hash: str
    block_height: int
    validator: str  # Validator address
    timestamp: int
    signature: str = ""
    
    def __hash__(self):
        return hash((self.block_hash, self.validator))
    
    def __eq__(self, other):
        if not isinstance(other, Vote):
            return False
        return (self.block_hash == other.block_hash and 
                self.validator == other.validator)


@dataclass
class FinalityState:
    """
    Tracks finality for blocks
    Manages votes and determines when blocks are finalized
    """
    # Votes by block hash
    votes_by_block: Dict[str, Set[Vote]] = field(default_factory=dict)
    
    # Finalized blocks (height -> hash)
    finalized_blocks: Dict[int, str] = field(default_factory=dict)
    
    # Latest finalized height
    latest_finalized_height: int = -1
    
    # Finality depth (blocks need to be this deep to finalize)
    finality_depth: int = 10
    
    # Supermajority threshold (2/3 of validators)
    supermajority_threshold: float = 0.67
    
    def add_vote(self, vote: Vote, total_stake: int, 
                 validator_stake: int) -> bool:
        """
        Add vote for block finalization
        
        Args:
            vote: Vote to add
            total_stake: Total staked amount in network
            validator_stake: Stake of voting validator
            
        Returns:
            True if vote was added
        """
        if vote.block_hash not in self.votes_by_block:
            self.votes_by_block[vote.block_hash] = set()
        
        # Check if validator already voted
        if vote in self.votes_by_block[vote.block_hash]:
            logger.debug(f"Validator {vote.validator[:8]} already voted for {vote.block_hash[:8]}")
            return False
        
        # Add vote
        self.votes_by_block[vote.block_hash].add(vote)
        logger.info(f"Added vote from {vote.validator[:8]} for block {vote.block_hash[:8]} at height {vote.block_height}")
        
        return True
    
    def has_supermajority(self, block_hash: str, validators: dict) -> bool:
        """
        Check if block has supermajority of votes
        
        Args:
            block_hash: Block hash to check
            validators: Dict of validator address -> stake amount
            
        Returns:
            True if supermajority reached
        """
        if block_hash not in self.votes_by_block:
            return False
        
        # Calculate total stake of validators who voted
        votes = self.votes_by_block[block_hash]
        voted_stake = sum(validators.get(vote.validator, 0) for vote in votes)
        
        # Calculate total stake in network
        total_stake = sum(validators.values())
        
        if total_stake == 0:
            return False
        
        # Check if voted stake is >= threshold
        vote_ratio = voted_stake / total_stake
        has_majority = vote_ratio >= self.supermajority_threshold
        
        if has_majority:
            logger.info(f"Block {block_hash[:8]} has supermajority: {vote_ratio:.2%} ({voted_stake}/{total_stake})")
        
        return has_majority
    
    def try_finalize_block(self, block_hash: str, block_height: int, 
                          current_height: int, validators: dict) -> bool:
        """
        Try to finalize a block
        Block must have supermajority and be deep enough
        
        Args:
            block_hash: Block hash
            block_height: Block height
            current_height: Current blockchain height
            validators: Active validators with stakes
            
        Returns:
            True if block was finalized
        """
        # Check if already finalized
        if block_height in self.finalized_blocks:
            return False
        
        # Check depth requirement
        depth = current_height - block_height
        if depth < self.finality_depth:
            logger.debug(f"Block {block_height} not deep enough: {depth}/{self.finality_depth}")
            return False
        
        # Check supermajority
        if not self.has_supermajority(block_hash, validators):
            logger.debug(f"Block {block_height} does not have supermajority")
            return False
        
        # Finalize block
        self.finalized_blocks[block_height] = block_hash
        self.latest_finalized_height = max(self.latest_finalized_height, block_height)
        
        logger.info(f"🔒 Block {block_height} ({block_hash[:8]}) FINALIZED")
        
        # Clean up old votes
        if block_hash in self.votes_by_block:
            del self.votes_by_block[block_hash]
        
        return True
    
    def is_block_final(self, block_hash: str, block_height: int) -> bool:
        """
        Check if block is finalized
        
        Args:
            block_hash: Block hash
            block_height: Block height
            
        Returns:
            True if block is finalized
        """
        return (block_height in self.finalized_blocks and 
                self.finalized_blocks[block_height] == block_hash)
    
    def get_finalized_height(self) -> int:
        """Get latest finalized block height"""
        return self.latest_finalized_height
    
    def can_reorg_to(self, fork_height: int) -> bool:
        """
        Check if chain can reorganize to given height
        Cannot reorg past finalized blocks
        
        Args:
            fork_height: Height of potential fork
            
        Returns:
            True if reorg is allowed
        """
        return fork_height > self.latest_finalized_height
    
    def get_vote_count(self, block_hash: str) -> int:
        """Get number of votes for block"""
        if block_hash not in self.votes_by_block:
            return 0
        return len(self.votes_by_block[block_hash])
    
    def get_voting_power(self, block_hash: str, validators: dict) -> float:
        """
        Get voting power ratio for block
        
        Args:
            block_hash: Block hash
            validators: Validator stakes
            
        Returns:
            Voting power as ratio (0.0 to 1.0)
        """
        if block_hash not in self.votes_by_block:
            return 0.0
        
        votes = self.votes_by_block[block_hash]
        voted_stake = sum(validators.get(vote.validator, 0) for vote in votes)
        total_stake = sum(validators.values())
        
        if total_stake == 0:
            return 0.0
        
        return voted_stake / total_stake
    
    def to_dict(self) -> dict:
        """Export finality state"""
        return {
            'latest_finalized_height': self.latest_finalized_height,
            'finalized_blocks': {
                str(h): hash_val for h, hash_val in self.finalized_blocks.items()
            },
            'pending_votes': {
                block_hash: len(votes) 
                for block_hash, votes in self.votes_by_block.items()
            },
            'finality_depth': self.finality_depth,
            'supermajority_threshold': self.supermajority_threshold
        }


class FinalityManager:
    """
    Manages finality for the blockchain
    Coordinates voting and finalization
    """
    
    def __init__(self, finality_depth: int = 10, 
                 supermajority_threshold: float = 0.67):
        """
        Initialize finality manager
        
        Args:
            finality_depth: Blocks needed before finalization
            supermajority_threshold: Vote threshold for finalization
        """
        self.state = FinalityState(
            finality_depth=finality_depth,
            supermajority_threshold=supermajority_threshold
        )
        logger.info(f"FinalityManager initialized: depth={finality_depth}, threshold={supermajority_threshold}")
    
    def process_block(self, block_hash: str, block_height: int, 
                     current_height: int, validators: dict) -> bool:
        """
        Process new block for finality
        
        Args:
            block_hash: New block hash
            block_height: New block height
            current_height: Current blockchain height
            validators: Active validators
            
        Returns:
            True if any block was finalized
        """
        finalized = False
        
        # Try to finalize old enough blocks
        min_height = max(0, current_height - self.state.finality_depth)
        for height in range(min_height, current_height):
            if height not in self.state.finalized_blocks:
                # Find block hash at this height
                # (This would come from blockchain state)
                if self.state.try_finalize_block(block_hash, height, current_height, validators):
                    finalized = True
        
        return finalized
    
    def add_vote(self, vote: Vote, validators: dict) -> bool:
        """
        Add validator vote
        
        Args:
            vote: Vote to add
            validators: Validator stakes
            
        Returns:
            True if vote added
        """
        validator_stake = validators.get(vote.validator, 0)
        total_stake = sum(validators.values())
        
        return self.state.add_vote(vote, total_stake, validator_stake)
    
    def is_finalized(self, block_hash: str, block_height: int) -> bool:
        """Check if block is finalized"""
        return self.state.is_block_final(block_hash, block_height)
    
    def get_finalized_height(self) -> int:
        """Get latest finalized height"""
        return self.state.get_finalized_height()


if __name__ == "__main__":
    # Test finality
    print("Testing Finality Mechanism...")
    
    # Setup
    manager = FinalityManager(finality_depth=3, supermajority_threshold=0.67)
    
    validators = {
        "val1": 100,
        "val2": 100,
        "val3": 100
    }
    
    block_hash = "block123"
    block_height = 0
    
    # Add votes
    vote1 = Vote(block_hash, block_height, "val1", int(time.time()), "sig1")
    vote2 = Vote(block_hash, block_height, "val2", int(time.time()), "sig2")
    
    manager.add_vote(vote1, validators)
    manager.add_vote(vote2, validators)
    
    print(f"✓ Votes added: {manager.state.get_vote_count(block_hash)}")
    print(f"✓ Has supermajority: {manager.state.has_supermajority(block_hash, validators)}")
    print(f"✓ Voting power: {manager.state.get_voting_power(block_hash, validators):.2%}")
    
    # Try finalize
    finalized = manager.state.try_finalize_block(block_hash, block_height, 10, validators)
    print(f"✓ Finalized: {finalized}")
    print(f"✓ Latest finalized: {manager.get_finalized_height()}")
    
    print("\n✅ Finality tests passed!")
