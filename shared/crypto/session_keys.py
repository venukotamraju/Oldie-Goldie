# crypto/session_keys.py

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import hashlib
import base64

class SecureMethodsForOG:

    # === Step 1: Generate ephemeral key pair === #
    @staticmethod
    def generate_key_pair() -> tuple[x25519.X25519PrivateKey, x25519.X25519PublicKey]:
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key
    
    # === Step 2: Derive shared secret === #
    @staticmethod
    def derive_shared_secret(private_key: x25519.X25519PrivateKey, peer_public_bytes: bytes) -> bytes:
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
        return private_key.exchange(peer_public_key)
    
    # === Step 3: Hash PSK === #
    @staticmethod
    def hash_psk(psk: str) -> bytes:
        return hashlib.sha256(psk.encode()).digest()
    
    # === Step 4. Use HKDF to combine shared secret + PSK into AES key === #
    @staticmethod
    def derive_session_key(shared_secret: bytes, psk_hash: bytes) -> bytes:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32, # For AES-256-GCM
            salt=psk_hash,
            info=b"oldie-goldie-secure-chat-session",
            backend=default_backend()
        )
        return hkdf.derive(shared_secret) # Final AES key (32 bytes)
    
    