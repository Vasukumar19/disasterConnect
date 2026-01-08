import os
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    return open(KEY_FILE, "rb").read()

fernet = Fernet(load_key())

def encrypt(text):
    return fernet.encrypt(text.encode())

def decrypt(data):
    return fernet.decrypt(data).decode()
