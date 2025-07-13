# shared/protocol.py
"""This file contains info and methods for defining how the messages are structured and (de)serialized."""

import json
from datetime import datetime

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
def encode_message(sender: str, message: str, timestamp = None, type: str = 'chat_message' ) -> str:
    """Encodes a chat message into a JSON string."""
    
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
    
    return json.dumps(
        {
            "protocol_version": PROTOCOL_VERSION,
            "type": type,
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        }
    )

# Function to decode a chat message
# Takes a JSON string and returns a dictionary
def decode_message(message_str: str) -> dict:
    """Decodes a chat message from a JSON string into a dictionary."""
    
    try:
        return json.loads(message_str)
    except json.JSONDecodeError:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "type": "system_message",
            "sender": "System",
            "message": "[Malformed Message]",
            "timestamp": datetime.now().astimezone().isoformat()
        }

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



