import socket
import json
import time
import threading
from config import DISCOVERY_PORT, BROADCAST_IP, DISCOVERY_INTERVAL

peers = {}
lock = threading.Lock()

def broadcast_presence(tcp_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        msg = json.dumps({"tcp_port": tcp_port}).encode()
        sock.sendto(msg, (BROADCAST_IP, DISCOVERY_PORT))
        time.sleep(DISCOVERY_INTERVAL)

def listen_for_peers():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))

    while True:
        data, addr = sock.recvfrom(1024)
        ip = addr[0]
        info = json.loads(data.decode())
        with lock:
            peers[ip] = info["tcp_port"]
