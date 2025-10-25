"""
Cryptographic primitives for production blockchain
Uses Ed25519 for signatures and SHA3-256 for hashing
"""
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError


def sha3_256(data: bytes) -> str:
    """SHA3-256 hash returning hex string"""
    return hashlib.sha3_256(data).hexdigest()


def hash_object(obj: Any) -> str:
    """Deterministic hash of any JSON-serializable object"""
    canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return sha3_256(canonical.encode('utf-8'))


@dataclass(frozen=True)
class KeyPair:
    """Ed25519 keypair for signing"""
    private_key: bytes  # 32 bytes seed
    public_key: bytes   # 32 bytes
    
    @classmethod
    def generate(cls) -> 'KeyPair':
        """Generate new random keypair"""
        signing_key = SigningKey.generate()
        return cls(
            private_key=bytes(signing_key),
            public_key=bytes(signing_key.verify_key)
        )
    
    @classmethod
    def from_seed(cls, seed: str) -> 'KeyPair':
        """Generate deterministic keypair from seed (for testing)"""
        # Hash seed to get 32 bytes
        seed_hash = sha3_256(seed.encode())
        seed_bytes = bytes.fromhex(seed_hash)[:32]
        signing_key = SigningKey(seed_bytes)
        return cls(
            private_key=bytes(signing_key),
            public_key=bytes(signing_key.verify_key)
        )
    
    @classmethod
    def from_private_key(cls, private_key: bytes) -> 'KeyPair':
        """Create keypair from private key"""
        signing_key = SigningKey(private_key)
        return cls(
            private_key=private_key,
            public_key=bytes(signing_key.verify_key)
        )
    
    def address(self) -> str:
        """Get address from public key (last 40 chars of hash)"""
        return sha3_256(self.public_key)[-40:]
    
    def public_key_hex(self) -> str:
        """Get public key as hex string"""
        return self.public_key.hex()
    
    def private_key_hex(self) -> str:
        """Get private key as hex string"""
        return self.private_key.hex()
    
    def sign(self, message: bytes) -> bytes:
        """Sign a message, returns 64-byte signature"""
        signing_key = SigningKey(self.private_key)
        signed = signing_key.sign(message)
        return signed.signature  # Just the signature, not the message
    
    def sign_dict(self, data: dict) -> str:
        """Sign a dictionary, returns hex signature"""
        message = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        signature = self.sign(message)
        return signature.hex()


def verify_signature(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Verify Ed25519 signature"""
    try:
        verify_key = VerifyKey(public_key)
        verify_key.verify(message, signature)
        return True
    except (BadSignatureError, ValueError):
        return False


def verify_dict_signature(public_key: bytes, data: dict, signature_hex: str) -> bool:
    """Verify signature on a dictionary"""
    try:
        message = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        signature = bytes.fromhex(signature_hex)
        return verify_signature(public_key, message, signature)
    except (ValueError, TypeError):
        return False


def address_from_public_key(public_key: bytes) -> str:
    """Convert public key to address"""
    return sha3_256(public_key)[-40:]


def is_valid_address(address: str) -> bool:
    """Check if address format is valid"""
    if not isinstance(address, str):
        return False
    if len(address) != 40:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False


# VRF (Verifiable Random Function) using Ed25519-VRF
class VRF:
    """
    Simplified VRF for validator selection
    Production would use a proper VRF like Ed25519-VRF
    """
    
    @staticmethod
    def prove(keypair: KeyPair, seed: bytes) -> tuple[bytes, bytes]:
        """
        Generate VRF proof
        Returns (output, proof)
        """
        # Sign the seed
        proof = keypair.sign(seed)
        
        # Output is hash of (public_key || proof)
        output_input = keypair.public_key + proof
        output = sha3_256(output_input).encode()
        
        return output, proof
    
    @staticmethod
    def verify(public_key: bytes, seed: bytes, output: bytes, proof: bytes) -> bool:
        """Verify VRF proof"""
        # Verify signature
        if not verify_signature(public_key, seed, proof):
            return False
        
        # Verify output
        expected_output_input = public_key + proof
        expected_output = sha3_256(expected_output_input).encode()
        
        return output == expected_output
    
    @staticmethod
    def output_to_number(output: bytes) -> int:
        """Convert VRF output to number"""
        return int.from_bytes(output[:8], 'big')


# Merkle tree for transaction batches
class MerkleTree:
    """Simple Merkle tree for transaction verification"""
    
    @staticmethod
    def build_tree(leaves: list[str]) -> str:
        """Build Merkle tree and return root hash"""
        if not leaves:
            return sha3_256(b"")
        
        if len(leaves) == 1:
            return leaves[0]
        
        # Ensure even number of leaves
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])
        
        # Build next level
        next_level = []
        for i in range(0, len(leaves), 2):
            combined = leaves[i] + leaves[i + 1]
            next_level.append(sha3_256(combined.encode()))
        
        return MerkleTree.build_tree(next_level)
    
    @staticmethod
    def compute_root(txids: list[str]) -> str:
        """Compute Merkle root from transaction IDs"""
        if not txids:
            return sha3_256(b"EMPTY_BLOCK")
        return MerkleTree.build_tree(txids)


# Key derivation
def derive_key(password: str, salt: bytes, iterations: int = 100_000) -> bytes:
    """Derive key from password using PBKDF2"""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)


if __name__ == "__main__":
    # Test the crypto module
    print("=== Cryptography Module Test ===\n")
    
    # Generate keypair
    kp = KeyPair.generate()
    print(f"Generated keypair")
    print(f"Address: {kp.address()}")
    print(f"Public key: {kp.public_key_hex()[:32]}...")
    
    # Sign and verify
    message = b"Hello, Blockchain!"
    signature = kp.sign(message)
    print(f"\nSigned message: {message.decode()}")
    print(f"Signature: {signature.hex()[:32]}...")
    
    valid = verify_signature(kp.public_key, message, signature)
    print(f"Signature valid: {valid}")
    
    # Test with wrong message
    wrong_valid = verify_signature(kp.public_key, b"Wrong message", signature)
    print(f"Wrong message valid: {wrong_valid}")
    
    # VRF test
    print("\n=== VRF Test ===")
    seed = b"block_123"
    output, proof = VRF.prove(kp, seed)
    print(f"VRF output: {output.hex()[:32]}...")
    print(f"VRF number: {VRF.output_to_number(output)}")
    
    vrf_valid = VRF.verify(kp.public_key, seed, output, proof)
    print(f"VRF proof valid: {vrf_valid}")
    
    # Merkle tree test
    print("\n=== Merkle Tree Test ===")
    txids = [f"tx_{i}" for i in range(5)]
    root = MerkleTree.compute_root(txids)
    print(f"Merkle root: {root[:32]}...")


def keypair_from_mnemonic(mnemonic: str, passphrase: str = "") -> 'KeyPair':
    """
    Create KeyPair from mnemonic phrase
    
    Args:
        mnemonic: 12 or 24 word mnemonic
        passphrase: Optional passphrase
        
    Returns:
        KeyPair instance
    """
    from core.mnemonic import mnemonic_to_seed, validate_mnemonic
    
    # Validate mnemonic
    if not validate_mnemonic(mnemonic):
        raise ValueError("Invalid mnemonic phrase")
    
    # Convert to seed
    seed = mnemonic_to_seed(mnemonic, passphrase)
    
    # Derive private key from seed (first 32 bytes)
    private_key_int = int.from_bytes(seed[:32], 'big')
    
    # Ensure it's in valid range for secp256k1
    private_key_int = private_key_int % CURVE_ORDER
    if private_key_int == 0:
        private_key_int = 1
    
    private_key = ecdsa.SigningKey.from_secret_exponent(
        private_key_int,
        curve=ecdsa.SECP256k1,
        hashfunc=hashlib.sha256
    )
    
    public_key = private_key.get_verifying_key()
    
    return KeyPair(private_key, public_key)

# Add method to KeyPair class
KeyPair.from_mnemonic = staticmethod(keypair_from_mnemonic)
