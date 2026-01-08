import json
import os
import threading

BUFFER_FILE = "message_buffer.json"
lock = threading.Lock()
buffer = {}

def load_buffer():
    global buffer
    if os.path.exists(BUFFER_FILE):
        with open(BUFFER_FILE, "r") as f:
            buffer = json.load(f)

def save_buffer():
    with open(BUFFER_FILE, "w") as f:
        json.dump(buffer, f)

def buffer_message(ip, message):
    with lock:
        buffer.setdefault(ip, []).append(message)
        save_buffer()

def flush_buffer(ip, port, send_func):
    with lock:
        msgs = buffer.get(ip, [])
        remaining = []
        for msg in msgs:
            if not send_func(ip, port, msg):
                remaining.append(msg)
        buffer[ip] = remaining
        save_buffer()
