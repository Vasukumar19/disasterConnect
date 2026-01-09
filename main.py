"""
DisasterConnect - P2P Emergency Communication System
Main Flask application with BOTH HTTP API and Terminal Interface
"""
import logging



# Disable Werkzeug request logging, keep only your own prints



import sys
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS

from p2p.host import create_host
from p2p.discovery import init_mdns
from p2p.chatroom import join_chat_room
from cli_interface import start_terminal_interface  # NEW IMPORT

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global instances
p2p_host = None
chat_room = None
peer_discovery = None
terminal_interface = None  # NEW
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True


# ==================== HTTP API ENDPOINTS ====================

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
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                "status": "error", 
                "message": "Message cannot be empty"
            }), 400
        
        if not chat_room:
            return jsonify({
                "status": "error",
                "message": "Chat room not initialized"
            }), 503
        
        success = chat_room.publish(message)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Message sent successfully"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send message"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route('/peers', methods=['GET'])
def get_peers():
    """Get list of connected peers"""
    if p2p_host:
        peers_dict = p2p_host.get_peers()
        peers = [
            {
                "peer_id": pid,
                "address": f"{ip}:{port}"
            }
            for pid, (ip, port) in peers_dict.items()
        ]
        return jsonify({
            "self_id": p2p_host.peer_id,
            "peers": peers,
            "peer_count": len(peers)
        })
    return jsonify({
        "self_id": "unknown",
        "peers": [],
        "peer_count": 0
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "peer_id": p2p_host.peer_id if p2p_host else "unknown",
        "room": chat_room.room_name if chat_room else "unknown",
        "message_count": chat_room.get_message_count() if chat_room else 0,
        "connected_peers": p2p_host.get_peer_count() if p2p_host else 0,
        "terminal_enabled": terminal_interface is not None  # NEW
    })


@app.route('/room-info', methods=['GET'])
def room_info():
    """Get information about current chat room"""
    if chat_room:
        return jsonify(chat_room.get_room_info())
    return jsonify({
        "error": "Not connected to any room"
    }), 503


@app.route('/clear-messages', methods=['POST'])
def clear_messages():
    """Clear all messages from the chat room"""
    if chat_room:
        chat_room.clear_messages()
        return jsonify({
            "status": "success",
            "message": "Messages cleared"
        })
    return jsonify({
        "status": "error",
        "message": "Chat room not initialized"
    }), 503


# ==================== P2P EVENT HANDLERS ====================

def on_peer_discovered(peer_id: str, peer_ip: str, peer_port: int):
    """Callback when a new peer is discovered"""
    if p2p_host:
        success = p2p_host.connect_to_peer(peer_ip, peer_port, peer_id)
        if success:
            print(f"📡 Peer discovered and connected: {peer_id}")


# ==================== INITIALIZATION ====================

def initialize_p2p(p2p_port: int, room_name: str, nickname: str, 
                   enable_terminal: bool = True):  # NEW PARAMETER
    """
    Initialize P2P networking and chat room
    
    Args:
        p2p_port: Port for P2P communication
        room_name: Chat room name to join
        nickname: User's display nickname
        enable_terminal: Enable terminal input interface (NEW)
    """
    global p2p_host, chat_room, peer_discovery, terminal_interface
    
    print("\n" + "="*70)
    print("🚨 DisasterConnect - P2P Emergency Communication System")
    print("="*70)
    
    try:
        # Create P2P host
        print("\n[1/3] Initializing P2P Host...")
        p2p_host = create_host(p2p_port)
        
        # Start peer discovery
        print("[2/3] Starting Peer Discovery...")
        peer_discovery = init_mdns(
            peer_id=p2p_host.peer_id,
            p2p_port=p2p_port,
            rendezvous=room_name,
            on_peer_found=on_peer_discovered
        )
        
        # Join chat room
        print("[3/3] Joining Chat Room...")
        chat_room = join_chat_room(room_name, nickname, p2p_host.peer_id, p2p_host)
        
        # Send welcome message
        chat_room.publish(f"{nickname} joined the chat!")
        
        # NEW: Start terminal interface if enabled
        if enable_terminal:
            print("[4/4] Starting Terminal Interface...")
            terminal_interface = start_terminal_interface(chat_room, nickname)
        
        print(f"\n✓ System initialized successfully!")
        print(f"  Room Name: {room_name}")
        print(f"  Nickname: {nickname}")
        print(f"  Peer ID: {p2p_host.peer_id}")
        print(f"  P2P Port: {p2p_port}")
        print(f"  Terminal Enabled: {'Yes ✓' if enable_terminal else 'No'}")  # NEW
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Failed to initialize P2P system: {e}")
        raise


def run_flask(http_port: int):
    """Run Flask HTTP server"""
    print(f"🌐 Starting HTTP API Server...")
    print(f"   API Endpoint: http://localhost:{http_port}")
    print(f"   Messages: GET  {http_port}/messages")
    print(f"   Send:     POST {http_port}/send")
    print(f"   Peers:    GET  {http_port}/peers")
    print(f"   Health:   GET  {http_port}/health")
    print(f"\n💡 Connect your frontend to: http://localhost:{http_port}")
    print(f"⚠️  Press Ctrl+C to stop\n")
    
    app.run(
        host='0.0.0.0',
        port=http_port,
        debug=False,
        use_reloader=False,
        threaded=True
    )


# ==================== ERROR HANDLING ====================

def handle_port_error(p2p_port: int, http_port: int, room_name: str, nickname: str):
    """Handle port access errors with helpful suggestions"""
    print("\n" + "="*70)
    print("❌ PORT ACCESS ERROR")
    print("="*70)
    print("\n⚠️  The ports you're trying to use are restricted or in use.\n")
    print("Quick Solutions:\n")
    print(f"1️⃣  Try higher port numbers:")
    print(f"   python main.py 8000 8001 {room_name} {nickname}\n")
    print(f"2️⃣  Run as Administrator (Windows):")
    print(f"   • Right-click Command Prompt → 'Run as Administrator'")
    print(f"   • Then: python main.py {p2p_port} {http_port} {room_name} {nickname}\n")
    print(f"3️⃣  Check available ports:")
    print(f"   • Linux/Mac: netstat -tuln | grep LISTEN")
    print(f"   • Windows: netstat -ano | findstr LISTENING\n")
    print("="*70 + "\n")


# ==================== MAIN ENTRY POINT ====================

if __name__ == '__main__':
    # Configuration from command line arguments
    P2P_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    HTTP_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
    ROOM_NAME = sys.argv[3] if len(sys.argv) > 3 else "disaster-relief"
    NICKNAME = sys.argv[4] if len(sys.argv) > 4 else "Anonymous"
    
    # NEW: Check if terminal should be enabled (default: yes)
    # Can be disabled with: python main.py 5000 5001 room nick --no-terminal
    ENABLE_TERMINAL = "--no-terminal" not in sys.argv
    
    try:
        # Initialize P2P system with terminal option
        initialize_p2p(P2P_PORT, ROOM_NAME, NICKNAME, ENABLE_TERMINAL)
        
        # Start HTTP server
        run_flask(HTTP_PORT)
        
    except OSError as e:
        error_str = str(e)
        if "10013" in error_str or "permission" in error_str.lower() or "address already in use" in error_str.lower():
            handle_port_error(P2P_PORT, HTTP_PORT, ROOM_NAME, NICKNAME)
        else:
            print(f"\n❌ Network error: {e}\n")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down DisasterConnect...")
        if terminal_interface:
            terminal_interface.stop()
        if peer_discovery:
            peer_discovery.stop()
        if p2p_host:
            p2p_host.stop()
        print("✓ Goodbye!\n")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
