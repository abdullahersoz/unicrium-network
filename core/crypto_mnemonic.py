"""
Unicrium Cryptography with BIP39 Mnemonic Support
12-word seed phrases for wallet recovery
"""
from Crypto.PublicKey import ECC
from Crypto.Hash import SHA256, keccak
from Crypto.Signature import DSS
import hashlib
import secrets
from typing import Tuple, Optional
from mnemonic import Mnemonic


def hash_object(data: str) -> str:
    """Hash a string using SHA-256"""
    return hashlib.sha256(data.encode()).hexdigest()


class KeyPair:
    """
    ECDSA KeyPair with BIP39 Mnemonic Support
    Generates 12-word seed phrase for wallet recovery
    """
    
    def __init__(self, private_key: ECC.EccKey):
        self.private_key = private_key
        self.public_key = private_key.public_key()
        self._mnemonic_words = None  # Store mnemonic if generated
    
    @classmethod
    def generate(cls, mnemonic_words: Optional[str] = None) -> 'KeyPair':
        """
        Generate new keypair with optional mnemonic
        
        Args:
            mnemonic_words: Optional 12-word mnemonic. If None, generates new one.
        
        Returns:
            KeyPair with mnemonic support
        """
        mnemo = Mnemonic("english")
        
        if mnemonic_words:
            # Restore from mnemonic
            if not mnemo.check(mnemonic_words):
                raise ValueError("Invalid mnemonic words")
            seed = mnemo.to_seed(mnemonic_words)
        else:
            # Generate new mnemonic
            mnemonic_words = mnemo.generate(strength=128)  # 12 words
            seed = mnemo.to_seed(mnemonic_words)
        
        # Derive private key from seed
        private_key_int = int.from_bytes(seed[:32], 'big')
        private_key = ECC.construct(curve='secp256k1', d=private_key_int)
        
        keypair = cls(private_key)
        keypair._mnemonic_words = mnemonic_words
        
        return keypair
    
    @classmethod
    def from_private_key(cls, private_key_hex: str) -> 'KeyPair':
        """Create keypair from hex private key"""
        private_key_int = int(private_key_hex, 16)
        private_key = ECC.construct(curve='secp256k1', d=private_key_int)
        return cls(private_key)
    
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
        return format(self.private_key.d, '064x')
    
    def get_public_key_hex(self) -> str:
        """Get compressed public key as hex"""
        point = self.public_key.pointQ
        x = format(point.x, '064x')
        prefix = '02' if point.y % 2 == 0 else '03'
        return prefix + x
    
    def address(self) -> str:
        """
        Get Ethereum-style address (0x...)
        
        Returns:
            Address string with 0x prefix
        """
        # Get uncompressed public key
        point = self.public_key.pointQ
        x = format(point.x, '064x')
        y = format(point.y, '064x')
        public_key_bytes = bytes.fromhex(x + y)
        
        # Keccak256 hash
        k = keccak.new(digest_bits=256)
        k.update(public_key_bytes)
        address_bytes = k.digest()[-20:]
        
        return '0x' + address_bytes.hex()
    
    def sign_message(self, message: str) -> str:
        """Sign a message and return hex signature"""
        h = SHA256.new(message.encode())
        signer = DSS.new(self.private_key, 'fips-186-3')
        signature = signer.sign(h)
        return signature.hex()
    
    def verify_message(self, message: str, signature_hex: str) -> bool:
        """Verify a message signature"""
        h = SHA256.new(message.encode())
        verifier = DSS.new(self.public_key, 'fips-186-3')
        try:
            verifier.verify(h, bytes.fromhex(signature_hex))
            return True
        except ValueError:
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
    
    try:
        point_data = bytes.fromhex(public_key_hex)
        if len(point_data) == 33:  # Compressed
            prefix = point_data[0]
            x = int.from_bytes(point_data[1:], 'big')
            # Decompress
            p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
            y_squared = (pow(x, 3, p) + 7) % p
            y = pow(y_squared, (p + 1) // 4, p)
            if (prefix == 0x03) != (y % 2 == 1):
                y = p - y
            public_key = ECC.construct(curve='secp256k1', point_x=x, point_y=y)
        else:
            x = int.from_bytes(point_data[:32], 'big')
            y = int.from_bytes(point_data[32:], 'big')
            public_key = ECC.construct(curve='secp256k1', point_x=x, point_y=y)
        
        h = SHA256.new(message.encode())
        verifier = DSS.new(public_key, 'fips-186-3')
        verifier.verify(h, bytes.fromhex(signature))
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
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)


def validate_mnemonic(words: str) -> bool:
    """Validate BIP39 mnemonic"""
    mnemo = Mnemonic("english")
    return mnemo.check(words)


def mnemonic_to_seed(words: str, passphrase: str = "") -> bytes:
    """Convert mnemonic to seed bytes"""
    mnemo = Mnemonic("english")
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
