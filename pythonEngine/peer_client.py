import socket
from config import BUFFER_SIZE
from message_protocol import encode_message
from store_forward import buffer_message

def send_message(ip, port, msg):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, port))
        s.sendall(encode_message(msg))
        s.close()
        return True
    except:
        buffer_message(ip, msg)
        return False
