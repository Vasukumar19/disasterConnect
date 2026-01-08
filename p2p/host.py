import socket
import json
import threading
import uuid
from typing import Callable, Optional


class P2PHost:
    """P2P Host for peer-to-peer communication"""
    
    def __init__(self, port: int):
        self.port = port
        self.peer_id = str(uuid.uuid4())[:8]
        self.peers = {}  # {peer_id: (ip, port)}
        self.message_handlers = []
        self.running = False
        
        # Create TCP socket for peer communication
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def start(self):
        """Start the P2P host"""
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"✓ P2P Host started")
            print(f"  Peer ID: {self.peer_id}")
            print(f"  Listening on: 0.0.0.0:{self.port}")
            
            # Start listening thread
            listen_thread = threading.Thread(target=self._listen_for_connections, daemon=True)
            listen_thread.start()
            
            return self.peer_id
            
        except Exception as e:
            print(f"✗ Failed to start P2P host: {e}")
            raise
    
    def _listen_for_connections(self):
        """Listen for incoming peer connections"""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                client_socket, address = self.socket.accept()
                
                # Handle connection in separate thread
                thread = threading.Thread(
                    target=self._handle_peer_connection,
                    args=(client_socket, address),
                    daemon=True
                )
                thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
    
    def _handle_peer_connection(self, client_socket, address):
        """Handle incoming peer connection"""
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if data:
                message = json.loads(data)
                
                # Register peer
                if 'peer_id' in message:
                    self.peers[message['peer_id']] = address
                
                # Notify message handlers
                for handler in self.message_handlers:
                    handler(message)
                    
        except Exception as e:
            print(f"Error handling peer connection: {e}")
        finally:
            client_socket.close()
    
    def connect_to_peer(self, peer_ip: str, peer_port: int, peer_id: str):
        """Connect to a peer"""
        self.peers[peer_id] = (peer_ip, peer_port)
        print(f"✓ Connected to peer {peer_id} at {peer_ip}:{peer_port}")
    
    def broadcast_message(self, message: dict):
        """Broadcast message to all connected peers"""
        message['peer_id'] = self.peer_id
        message_json = json.dumps(message)
        
        for peer_id, (ip, port) in list(self.peers.items()):
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.settimeout(2.0)
                peer_socket.connect((ip, port))
                peer_socket.send(message_json.encode('utf-8'))
                peer_socket.close()
            except Exception as e:
                print(f"✗ Failed to send to peer {peer_id}: {e}")
    
    def add_message_handler(self, handler: Callable):
        """Add a message handler callback"""
        self.message_handlers.append(handler)
    
    def stop(self):
        """Stop the P2P host"""
        self.running = False
        self.socket.close()
        print("✓ P2P Host stopped")


def create_host(port: int) -> P2PHost:
    """
    Create and start a P2P host
    
    Args:
        port: Port number for P2P communication
        
    Returns:
        P2PHost instance
    """
    host = P2PHost(port)
    host.start()
    return host