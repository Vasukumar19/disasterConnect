from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
from discovery import peers, lock
from peer_client import send_message
from message_protocol import create_message
from message_router import register_ack, wait_for_acks

ENGINE_PORT = 9000

class API(BaseHTTPRequestHandler):
    def _res(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/peers":
            with lock:
                self._res(200, peers)
        else:
            self._res(404, {})

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(length))
        msg = create_message(body["type"], "UI", body["text"])

        with lock:
            targets = list(peers.items())

        if msg["type"] == "SOS":
            register_ack(msg["id"], [ip for ip, _ in targets])

        for ip, port in targets:
            send_message(ip, port, msg)

        if msg["type"] == "SOS":
            self._res(200, {"delivered": wait_for_acks(msg["id"])})
        else:
            self._res(200, {"status": "sent"})

def start_api():
    HTTPServer(("localhost", ENGINE_PORT), API).serve_forever()

def run_api():
    threading.Thread(target=start_api, daemon=True).start()
