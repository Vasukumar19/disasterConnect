import socket
import threading
from config import TCP_PORT, BUFFER_SIZE
from message_protocol import decode_message, create_message
from message_router import handle_ack

def handle_client(conn, addr):
    data = conn.recv(BUFFER_SIZE)
    if not data:
        return
    msg = decode_message(data.decode())

    if msg["type"] == "ACK":
        handle_ack(msg["payload"]["ack_id"])
    else:
        print(f"\n[{msg['type']}] {addr[0]}: {msg['payload']['text']}")
        if msg["type"] == "SOS":
            ack = create_message("ACK", "local", "")
            ack["payload"]["ack_id"] = msg["id"]
            conn.sendall(str(ack).encode())

    conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", TCP_PORT))
    s.listen()
    while True:
        c, a = s.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()
