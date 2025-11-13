"""_summary_
first what do we need to do
1. Generate key pair
2. Create a Global Object to store both the keys in session
3. Then send/receive the public key to/from server
4. Compute shared secret
"""
import websockets
from shared import SecureMethodsForOG
import base64
from shared import encode_message
import logging
logging.basicConfig(
    level=logging.INFO,
    format= "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
    )
logger = logging.getLogger(__name__)

class TunnelActivityUtilsForOG:

    def __init__(self):
        self._private_key = None
        self._public_key = None
        self._shared_secret = None
        self._session_key = None
        self._peer_public_key_bytes = None
        self._psk_hash = None

    async def handle_key_share(self, websocket: websockets.ClientConnection, username: str, target: str):
        try:
            priv_key, pub_key = SecureMethodsForOG.generate_key_pair()

            # Update the instance variables
            self._private_key = priv_key
            self._public_key = pub_key

            # the pub_key is of type X25519PublicKey, convert it to bytes
            pub_key_bytes = SecureMethodsForOG.public_key_to_bytes(pub_key)

            # encode those bytes to base 64 to make it
            #  suitable for json transport
            encoded_pub_key_bytes = base64.b64encode(pub_key_bytes).decode()

            logger.info(f'[TunnelActivityUtilsForOG.handle_key_share] Encoded Pub Key: {encoded_pub_key_bytes}')

            # build the message to send over to server
            message = encode_message(
                sender=username,
                type='key_share',
                key=encoded_pub_key_bytes,
                target = target,
                message='sharing public key'
            )

            await websocket.send(message=message)
        except Exception as e:
            logger.error(f"[TunnelActivityUtilsForOG.handle_key_share] Unknown Exception: {e}")

    def handle_shared_secret(self):
        shared_secret = SecureMethodsForOG.derive_shared_secret(self._private_key, self._peer_public_key_bytes)
        self._shared_secret = shared_secret
    
    def handle_session_secret(self):
        session_key = SecureMethodsForOG.derive_session_key(psk_hash=self._psk_hash, shared_secret=self._shared_secret)
        self._session_key = session_key
    
    def set_peer_public_key(self, encoded_peer_public_key: str):
        decoded_peer_public_key_bytes = base64.b64decode(encoded_peer_public_key)
        self._peer_public_key_bytes = decoded_peer_public_key_bytes
    
    def set_psk_hash(self, psk_hash: bytes) -> None:
        self._psk_hash = psk_hash

    def get_peer_public_key_bytes(self) -> bytes | None:
        return self._peer_public_key_bytes
    
    def get_psk_hash(self) -> bytes | None:
        return self._psk_hash
    
    def get_session_key(self) -> None:
        return self._session_key
    
    async def reset(self) -> None:
        self._private_key = None
        self._public_key = None
        self._shared_secret = None
        self._session_key = None
        self._peer_public_key_bytes = None
        self._psk_hash = None