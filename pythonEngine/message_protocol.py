import json
import time
import uuid

def create_message(msg_type, sender, text):
    return {
        "id": str(uuid.uuid4()),
        "type": msg_type,
        "sender": sender,
        "timestamp": time.time(),
        "payload": {"text": text}
    }

def encode_message(msg):
    return json.dumps(msg).encode()

def decode_message(data):
    return json.loads(data)
