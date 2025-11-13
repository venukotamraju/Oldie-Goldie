# crypto/session_keys.py

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import hashlib
from cryptography.hazmat.primitives import serialization

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
        """
        Derives a shared secret using the private key and peer's public key bytes.
        """
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
        return private_key.exchange(peer_public_key)
    
    # === Step 3: Hash PSK === #
    @staticmethod
    def hash_psk(psk: str) -> bytes:
        """
        Hash the Pre-Shared Key (PSK) using SHA-256
        """
        return hashlib.sha256(psk.encode()).digest()
    
    # === Step 4. Use HKDF to combine shared secret + PSK into AES key === #
    @staticmethod
    def derive_session_key(shared_secret: bytes, psk_hash: bytes) -> bytes:
        """
        Derives the session key using HKDF based on the shared secret and hashed PSK
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32, # For AES-256-GCM (32 bytes for AES key)
            salt=psk_hash,
            info=b"oldie-goldie-secure-chat-session",
            backend=default_backend()
        )
        return hkdf.derive(shared_secret) # Final AES key (32 bytes)
    
    # Helper method for serializing the public key (raw bytes)
    @staticmethod
    def public_key_to_bytes(public_key: x25519.X25519PublicKey) -> bytes:
        """
        Converts the X5519 public key to raw bytes format.
        """
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
