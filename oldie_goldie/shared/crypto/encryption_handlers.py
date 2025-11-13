# crypto/encryption_handlers.py

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

class EncryptionUtilsForOG:
    """
    AES-256-GCM encrypt/decrypt helpers.
    Format: nonce(12) || tag(16) || ciphertext
    """

    @staticmethod
    def encrypt_message(session_key:bytes, message:str) -> bytes:
        """Encrypt `message` with AES-256-GCM and return nonce||tag||ciphertext."""
        if not isinstance(session_key, (bytes, bytearray)) or len(session_key) != 32:
            raise ValueError("session_key must be 322 bytes for AES-256-GCM")

        # Generate a random nonce for each message
        nonce = os.urandom(12) # 12 bytes for AES-GCM

        # Pad the message to be a multiple of block size
        # PKCS7 pad (block size 128 bits = 16 bytes)
        padder = padding.PKCS7(128).padder()
        padded_message = padder.update(message.encode()) + padder.finalize()

        # Create the cipher object
        cipher = Cipher(algorithms.AES(session_key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()

        # Encrypt the message
        ciphertext = encryptor.update(padded_message) + encryptor.finalize()
        
        # Fetch the tag
        tag = encryptor.tag # 16 bytes

        # Return the concatenated nonce, ciphertext, and the tag
        return nonce + tag + ciphertext
    
    @staticmethod
    def decrypt_message(session_key: bytes, encrypted_message:bytes) -> str:
        """Decrypt a message with the provided session key using AES-256-GCM."""
        if not isinstance(session_key, (bytes, bytearray)) or len(session_key) != 32:
            raise ValueError("session_key must be 32 bytes for AES-256-GCM")
        
        if len(encrypted_message) < 12 + 16:
            raise ValueError("Encrypted message is too short")

        # Extract the nonce, tag, and ciphertext
        nonce = encrypted_message[:12]
        tag = encrypted_message[12:28]
        ciphertext = encrypted_message[28:]

        # Create the cipher object
        cipher = Cipher(algorithms.AES(session_key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the message
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode('utf-8')
        