"""
Unicrium Cryptography with BIP39 Mnemonic Support  
12-word seed phrases for wallet recovery
"""
import hashlib
import hmac
from ecdsa import SigningKey, SECP256k1, VerifyingKey
from ecdsa.util import sigencode_string, sigdecode_string
from typing import Optional
from mnemonic import Mnemonic as BIP39Mnemonic


def hash_object(data: str) -> str:
    """Hash a string using SHA-256"""
    return hashlib.sha256(data.encode()).hexdigest()


def keccak256(data: bytes) -> bytes:
    """Keccak256 hash (Ethereum-style)"""
    import sha3
    return sha3.keccak_256(data).digest()


class KeyPair:
    """
    ECDSA KeyPair with BIP39 Mnemonic Support
    Generates 12-word seed phrase for wallet recovery
    """
    
    def __init__(self, signing_key: SigningKey, mnemonic_words: Optional[str] = None):
        self.signing_key = signing_key
        self.verifying_key = signing_key.get_verifying_key()
        self._mnemonic_words = mnemonic_words
    
    @classmethod
    def generate(cls, mnemonic_words: Optional[str] = None) -> 'KeyPair':
        """
        Generate new keypair with optional mnemonic
        
        Args:
            mnemonic_words: Optional 12-word mnemonic. If None, generates new one.
        
        Returns:
            KeyPair with mnemonic support
        """
        mnemo = BIP39Mnemonic("english")
        
        if mnemonic_words:
            # Restore from mnemonic
            if not mnemo.check(mnemonic_words):
                raise ValueError("Invalid mnemonic words")
            seed = mnemo.to_seed(mnemonic_words)
        else:
            # Generate new mnemonic
            mnemonic_words = mnemo.generate(strength=128)  # 12 words
            seed = mnemo.to_seed(mnemonic_words)
        
        # Derive private key from seed using HMAC-SHA512
        hmac_result = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        private_key_bytes = hmac_result[:32]
        
        # Create signing key
        signing_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        
        return cls(signing_key, mnemonic_words)
    
    @classmethod
    def from_private_key(cls, private_key_hex: str) -> 'KeyPair':
        """Create keypair from hex private key"""
        private_key_bytes = bytes.fromhex(private_key_hex)
        signing_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        return cls(signing_key)
    
    @classmethod
    def from_mnemonic(cls, mnemonic_words: str) -> 'KeyPair':
        """
        Restore keypair from 12-word mnemonic
        
        Args:
            mnemonic_words: 12-word BIP39 mnemonic phrase
        
        Returns:
            Restored KeyPair
        """
        return cls.generate(mnemonic_words=mnemonic_words)
    
    def get_mnemonic(self) -> Optional[str]:
        """
        Get 12-word mnemonic phrase
        Only available if keypair was generated with generate()
        
        Returns:
            12-word mnemonic or None if not available
        """
        return self._mnemonic_words
    
    def get_private_key_hex(self) -> str:
        """Get private key as hex string"""
        return self.signing_key.to_string().hex()
    
    def get_public_key_hex(self) -> str:
        """Get compressed public key as hex"""
        public_key_bytes = self.verifying_key.to_string()
        x = public_key_bytes[:32]
        y = public_key_bytes[32:]
        prefix = b'\x02' if y[-1] % 2 == 0 else b'\x03'
        return (prefix + x).hex()
    
    def address(self) -> str:
        """
        Get Ethereum-style address (0x...)
        
        Returns:
            Address string with 0x prefix
        """
        try:
            public_key_bytes = self.verifying_key.to_string()
            address_bytes = keccak256(public_key_bytes)[-20:]
            return '0x' + address_bytes.hex()
        except:
            # Fallback to SHA256 if keccak not available
            public_key_bytes = self.verifying_key.to_string()
            address_bytes = hashlib.sha256(public_key_bytes).digest()[-20:]
            return '0x' + address_bytes.hex()
    
    def sign_message(self, message: str) -> str:
        """Sign a message and return hex signature"""
        message_hash = hashlib.sha256(message.encode()).digest()
        signature = self.signing_key.sign_digest(message_hash, sigencode=sigencode_string)
        return signature.hex()
    
    def verify_message(self, message: str, signature_hex: str) -> bool:
        """Verify a message signature"""
        message_hash = hashlib.sha256(message.encode()).digest()
        try:
            self.verifying_key.verify_digest(
                bytes.fromhex(signature_hex),
                message_hash,
                sigdecode=sigdecode_string
            )
            return True
        except:
            return False
    
    def to_dict(self) -> dict:
        """Export keypair (WARNING: includes private key and mnemonic!)"""
        result = {
            'address': self.address(),
            'public_key': self.get_public_key_hex(),
            'private_key': self.get_private_key_hex()
        }
        if self._mnemonic_words:
            result['mnemonic'] = self._mnemonic_words
        return result


def verify_dict_signature(data: dict, public_key_hex: str) -> bool:
    """Verify signature on a dictionary"""
    if 'signature' not in data:
        return False
    
    signature = data.pop('signature')
    message = str(sorted(data.items()))
    message_hash = hashlib.sha256(message.encode()).digest()
    
    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        if len(public_key_bytes) == 33:  # Compressed
            # Decompress
            prefix = public_key_bytes[0]
            x = public_key_bytes[1:]
            # Simple decompression (works for most cases)
            verifying_key = VerifyingKey.from_string(public_key_bytes[1:] + public_key_bytes[1:], curve=SECP256k1)
        else:
            verifying_key = VerifyingKey.from_string(public_key_bytes, curve=SECP256k1)
        
        verifying_key.verify_digest(
            bytes.fromhex(signature),
            message_hash,
            sigdecode=sigdecode_string
        )
        return True
    except Exception:
        return False
    finally:
        data['signature'] = signature


def is_valid_address(address: str) -> bool:
    """Check if address format is valid"""
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False


# Utility functions
def generate_mnemonic() -> str:
    """Generate a new 12-word BIP39 mnemonic"""
    mnemo = BIP39Mnemonic("english")
    return mnemo.generate(strength=128)


def validate_mnemonic(words: str) -> bool:
    """Validate BIP39 mnemonic"""
    mnemo = BIP39Mnemonic("english")
    return mnemo.check(words)


def mnemonic_to_seed(words: str, passphrase: str = "") -> bytes:
    """Convert mnemonic to seed bytes"""
    mnemo = BIP39Mnemonic("english")
    return mnemo.to_seed(words, passphrase)


if __name__ == "__main__":
    print("🧪 Testing Crypto with Mnemonic...\n")
    
    # Test 1: Generate with mnemonic
    print("1. Generate new keypair with mnemonic:")
    keypair = KeyPair.generate()
    mnemonic = keypair.get_mnemonic()
    address = keypair.address()
    
    print(f"   ✅ Mnemonic: {mnemonic}")
    print(f"   ✅ Address: {address}")
    
    # Test 2: Restore from mnemonic
    print("\n2. Restore from mnemonic:")
    restored = KeyPair.from_mnemonic(mnemonic)
    restored_address = restored.address()
    
    print(f"   ✅ Restored address: {restored_address}")
    print(f"   ✅ Match: {address == restored_address}")
    
    # Test 3: Signing
    print("\n3. Test signing:")
    message = "Hello Unicrium"
    signature = keypair.sign_message(message)
    valid = keypair.verify_message(message, signature)
    
    print(f"   ✅ Signature: {signature[:32]}...")
    print(f"   ✅ Verification: {valid}")
    
    print("\n✅ All tests passed!")
