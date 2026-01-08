import time
import threading
from config import SOS_RETRY_COUNT, SOS_ACK_TIMEOUT

pending_acks = {}
lock = threading.Lock()

def register_ack(msg_id, peers):
    with lock:
        pending_acks[msg_id] = set(peers)

def handle_ack(msg_id):
    with lock:
        pending_acks.pop(msg_id, None)

def wait_for_acks(msg_id):
    for _ in range(SOS_RETRY_COUNT):
        time.sleep(SOS_ACK_TIMEOUT)
        with lock:
            if msg_id not in pending_acks:
                return True
    return False
