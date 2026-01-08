import sys
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

from p2p.host import create_host
from p2p.discovery import init_mdns
from p2p.chatroom import join_chat_room

app = Flask(__name__)
CORS(app)

# Global instances
p2p_host = None
chat_room = None
peer_discovery = None


@app.route('/messages', methods=['GET'])
def get_messages():
    """Get all messages from the chat room"""
    if chat_room:
        msgs = chat_room.get_messages()
        return jsonify(msgs)
    return jsonify([])


@app.route('/send', methods=['POST'])
def send_message():
    """Send a message to the chat room"""
    data = request.get_json()
    message = data.get('message', '')
    
    if message and chat_room:
        chat_room.publish(message)
        return jsonify({"status": "success", "message": "Message sent"})
    
    return jsonify({"status": "error", "message": "No message provided"}), 400


@app.route('/peers', methods=['GET'])
def get_peers():
    """Get list of connected peers"""
    if p2p_host:
        peers = [{"peer_id": pid, "address": f"{ip}:{port}"} 
                for pid, (ip, port) in p2p_host.peers.items()]
        return jsonify({
            "self_id": p2p_host.peer_id,
            "peers": peers,
            "peer_count": len(peers)
        })
    return jsonify({"peers": [], "peer_count": 0})


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "peer_id": p2p_host.peer_id if p2p_host else "unknown",
        "room": chat_room.room_name if chat_room else "unknown"
    })


def on_peer_discovered(peer_id: str, peer_ip: str, peer_port: int):
    """Callback when a new peer is discovered"""
    if p2p_host:
        p2p_host.connect_to_peer(peer_ip, peer_port, peer_id)


def initialize_p2p(p2p_port: int, room_name: str, nickname: str):
    """Initialize P2P networking and chat room"""
    global p2p_host, chat_room, peer_discovery
    
    print("\n" + "="*60)
    print("🚨 DisasterNet - P2P Emergency Chat System")
    print("="*60)
    
    # Create P2P host
    p2p_host = create_host(p2p_port)
    
    # Start peer discovery
    peer_discovery = init_mdns(
        peer_id=p2p_host.peer_id,
        p2p_port=p2p_port,
        rendezvous=room_name,
        on_peer_found=on_peer_discovered
    )
    
    # Join chat room
    chat_room = join_chat_room(room_name, nickname, p2p_host.peer_id, p2p_host)
    
    # Send welcome message
    chat_room.publish("joined the chat!")
    
    print(f"\n✓ System initialized successfully")
    print(f"  Room: {room_name}")
    print(f"  Nickname: {nickname}")
    print("="*60 + "\n")


def run_flask(http_port: int):
    """Run Flask HTTP server"""
    print(f"🌐 Starting HTTP API server on port {http_port}")
    print(f"   API endpoint: http://localhost:{http_port}")
    print(f"\n💡 Connect your frontend to: http://localhost:{http_port}")
    print(f"\n⚠️  Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=http_port, debug=False, use_reloader=False)


if __name__ == '__main__':
    # Configuration from command line arguments
    P2P_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    HTTP_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
    ROOM_NAME = sys.argv[3] if len(sys.argv) > 3 else "disaster-relief"
    NICKNAME = sys.argv[4] if len(sys.argv) > 4 else "Anonymous"
    
    try:
        # Initialize P2P system
        initialize_p2p(P2P_PORT, ROOM_NAME, NICKNAME)
        
        # Start HTTP server
        run_flask(HTTP_PORT)
        
    except OSError as e:
        if "10013" in str(e) or "permission" in str(e).lower():
            print("\n" + "="*60)
            print("❌ PORT ACCESS ERROR")
            print("="*60)
            print("\n⚠️  The ports you're trying to use are restricted.\n")
            print("Quick Fix - Try these commands:\n")
            print(f"1. Use higher port numbers:")
            print(f"   python main.py 5000 5001 {ROOM_NAME} {NICKNAME}\n")
            print(f"2. Run as Administrator (Windows):")
            print(f"   Right-click Command Prompt → 'Run as Administrator'")
            print(f"   Then run: python main.py {P2P_PORT} {HTTP_PORT} {ROOM_NAME} {NICKNAME}\n")
            print(f"3. Find available ports:")
            print(f"   python fix_ports.py\n")
            print("="*60 + "\n")
        else:
            print(f"\n❌ Network error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down DisasterNet...")
        if peer_discovery:
            peer_discovery.stop()
        if p2p_host:
            p2p_host.stop()
        print("✓ Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)