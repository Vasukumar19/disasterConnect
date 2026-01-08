import threading
import time
from discovery import broadcast_presence, listen_for_peers
from peer_server import start_server
from engine_api import run_api
from config import TCP_PORT
from leader_election import elect_leader

threading.Thread(target=start_server, daemon=True).start()
threading.Thread(target=broadcast_presence, args=(TCP_PORT,), daemon=True).start()
threading.Thread(target=listen_for_peers, daemon=True).start()
run_api()

time.sleep(3)
print("DISASTER NODE STARTED")
print("LEADER:", elect_leader())

while True:
    time.sleep(10)
