# shared/protocol.py
"""This file contains info and methods for defining how the messages are structured and (de)serialized."""

import json
from datetime import datetime

def encode_message(sender: str, message: str, timestamp = None ) -> str:
    if timestamp is None:
        timestamp = datetime.now().astimezone().isoformat()
    return json.dumps(
        {
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        }
    )

def decode_message(message_str: str) -> dict:
    try:
        return json.loads(message_str)
    except json.JSONDecodeError:
        return {
            "sender": "System",
            "message": "[Malformed Message]",
            "timestamp": datetime.now().astimezone().isoformat()
        }