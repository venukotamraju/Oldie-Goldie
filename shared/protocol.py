# shared/protocol.py
"""This file contains info and methods for defining how the messages are structured and (de)serialized."""

import json
from datetime import datetime
import base64
from .crypto.encryption_handlers import EncryptionUtilsForOG

# Protocol Version
PROTOCOL_VERSION = "1.0"

# === Chat Messages === #

# Chat message structure:
# {
#     "protocol_version": "1.0",
#     "type": "chat_message",
#     "sender": "username",
#     "message": "Hello, world!",
#     "timestamp": "2023-10-01T12:34:56.789Z"
# }

# Function to encode a chat message
# Takes a sender, message, and an optional timestamp
def encode_message(
        sender: str, 
        message: str, 
        timestamp = None, 
        type: str = 'chat_message', 
        session_key: bytes = None,
        **kwargs) -> str:
    """
    Encodes a chat message (or other type) into a JSON string with support for extra fields.
    If session_key is provided, encrypts the JSON string and returns an 'encrypted_message' wrapper instead.
    Ensure you pass `target` via **kwargs, if the message is intended for a peer/recipient
    """
    
    # Validate inputs
    if not sender or not message:
        raise ValueError("Sender and message cannot be empty.")
    if not isinstance(sender, str) or not isinstance(message, str):
        raise TypeError("Sender and message must be strings.")
    if timestamp and not isinstance(timestamp, str):
        raise TypeError("Timestamp must be a string or None.")
    if len(sender) > 50:
        raise ValueError("Sender name cannot exceed 50 characters.")
    if len(message) > 500:
        raise ValueError("Message cannot exceed 500 characters.")
    
    # If timestamp is not provided, use the current time in ISO format
    # with timezone information
    if timestamp is None:
        timestamp = datetime.now().astimezone().isoformat()
    
    # Construct base message
    message_dict = {
            "protocol_version": PROTOCOL_VERSION,
            "type": type,
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        }
    
    # Add any additional fields
    message_dict.update(kwargs)

    # If no session_key -> return plaintext JSON
    if session_key is None:
        return json.dumps(message_dict)
    
    # Else: encrypt the full JSON string
    inner_json = json.dumps(message_dict)
    encrypted_bytes = EncryptionUtilsForOG.encrypt_message(session_key=session_key, message=inner_json)

    # Wrap as encrypted message
    return json.dumps({
        "protocol_version":PROTOCOL_VERSION,
        "type": "encrypted_message",
        "sender":sender,
        "payload_b64": base64.b64encode(encrypted_bytes).decode('ascii'),
        "timestamp": timestamp,
        "target": kwargs.get('target', None)        
    })
    

# Function to decode a chat message
# Takes a JSON string and returns a dictionary
def decode_message(message_str: str, session_key: bytes = None) -> dict:
    """
    Decodes a chat message from a JSON string into a dictionary.
    If the message is 'encrypted_message' and session_key is provided,
    it will decrypt and then decode the inner message.
    """

    try:
        msg = json.loads(message_str)
    except json.JSONDecodeError:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "type": "system_message",
            "sender": "System",
            "message": "[Malformed Message]",
            "timestamp": datetime.now().astimezone().isoformat()
        }
    
    if msg.get('type') == 'encrypted_message':
        if session_key is None:
            # Can't decrypt, return as-is
            return msg
        payload = base64.b64decode(msg["payload_b64"])
        inner_json = EncryptionUtilsForOG.decrypt_message(session_key=session_key, encrypted_message=payload)
        return json.loads(inner_json)
    
    return msg

# === Control Messages === #
# Control messages are used for user registration, connection requests, and system notifications.
def make_register_message(username: str) -> str:
    """Creates a registration message for a new user."""
    
    return json.dumps({
        "protocol_version": PROTOCOL_VERSION,
        "type": "register",
        "username": username,
        "timestamp": datetime.now().astimezone().isoformat()
    })

def make_connect_request(username: str, target: str) -> str:
    """Creates a connection request message."""
    
    return json.dumps({
        "protocol_version": PROTOCOL_VERSION,
        "type": "connect_request",
        "sender": username,
        "target": target,
        "timestamp": datetime.now().astimezone().isoformat()
    })

def make_connect_response(sender: str, accepted: bool, reason: str = "") -> str:
    """Creates a connection response message."""
    
    return json.dumps({
        "protocol_version": PROTOCOL_VERSION,
        "type": "connect_response",
        "sender": sender,
        "accepted": accepted,
        "reason": reason,
        "timestamp": datetime.now().astimezone().isoformat()
    })

def make_user_disconnected_message(username: str) -> str:
    """Creates a user disconnected message."""
    
    return json.dumps({
        "protocol_version": PROTOCOL_VERSION,
        "type": "user_disconnected",
        "sender": "Server",
        "username": username,
        "message": f"{username} has disconnected.",
        "timestamp": datetime.now().astimezone().isoformat()
    })

def make_system_notification(message: str) -> str:
    """Creates a system notification message."""
    
    return json.dumps({
        "protocol_version": PROTOCOL_VERSION,
        "type": "system_message",
        "sender": "System",
        "message": message,
        "timestamp": datetime.now().astimezone().isoformat()
    })

def make_system_request(need: str, username: str) -> str:
    """Make general requests to the server that are not personalised to any user.

    Args:
        need (str)
            supported needs:
            1. list_users
        
        username (str)

    Returns:
        str:
            return a json string
    """
    return json.dumps({
        'protocol_version': PROTOCOL_VERSION,
        'type': 'system_request',
        'need': need,
        'sender': username,
        'timestamp': datetime.now().astimezone().isoformat()        
    })

def make_system_response(res_obj: any = None, res_need: str = None):
    """Respond to the system request with this structure
    """
    return json.dumps({
        'protocol_version': PROTOCOL_VERSION,
        'sender':'server',
        'type':'system_response',
        'response_need':res_need,
        'res_info': res_obj,
        'timestamp': datetime.now().astimezone().isoformat()
    })
