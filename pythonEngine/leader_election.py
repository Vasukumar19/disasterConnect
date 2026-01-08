import socket
from discovery import peers

def my_ip():
    return socket.gethostbyname(socket.gethostname())

def elect_leader():
    return max(list(peers.keys()) + [my_ip()])
