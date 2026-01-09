"""P2P Host implementation for peer-to-peer communication"""

import socket
import json
import threading
import uuid
from typing import Callable, Optional, Dict, Tuple, List


class P2PHost:
    """P2P Host for peer-to-peer communication"""
    
    def __init__(self, port: int):
        """
        Initialize P2P Host
        
        Args:
            port: Port number for P2P communication
        """
        self.port = port
        self.peer_id = str(uuid.uuid4())[:8]
        self.peers: Dict[str, Tuple[str, int]] = {}  # {peer_id: (ip, port)}
        self.message_handlers: List[Callable] = []
        self.running = False
        
        # Create TCP socket for peer communication
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.peer_lock = threading.Lock()
    
    def start(self) -> str:
        """
        Start the P2P host and listen for incoming connections
        
        Returns:
            Peer ID of this host
        """
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"✓ P2P Host started")
            print(f"  Peer ID: {self.peer_id}")
            print(f"  Listening on: 0.0.0.0:{self.port}")
            
            # Start listening thread for incoming connections
            listen_thread = threading.Thread(
                target=self._listen_for_connections,
                daemon=True
            )
            listen_thread.start()
            
            return self.peer_id
            
        except Exception as e:
            print(f"✗ Failed to start P2P host: {e}")
            raise
    
    def _listen_for_connections(self):
        """Listen for incoming peer connections"""
        while self.running:
            try:
                # FIXED: Set timeout per-accept, not on listening socket
                client_socket, address = self.socket.accept()  # Blocks indefinitely
                client_socket.settimeout(10.0)  # Timeout for this client only
                
                # Handle connection in separate thread
                thread = threading.Thread(
                    target=self._handle_peer_connection,
                    args=(client_socket, address),
                    daemon=True
                )
                thread.start()
                
            except socket.timeout:
                continue  # Loop continues if timeout
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")

    
    def _handle_peer_connection(self, client_socket: socket.socket, address: Tuple[str, int]):
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if data:
                message = json.loads(data)

                # DELETE this whole block:
                # if 'peer_id' in message:
                #     with self.peer_lock:
                #         self.peers[message['peer_id']] = address

                for handler in self.message_handlers:
                    try:
                        handler(message)
                    except Exception as e:
                        print(f"Error in message handler: {e}")

        except Exception as e:
            print(f"Error handling peer connection: {e}")
        finally:
            client_socket.close()

    
    def connect_to_peer(self, peer_ip: str, peer_port: int, peer_id: str) -> bool:
        """Connect to a discovered peer"""
        try:
            with self.peer_lock:
                self.peers[peer_id] = (peer_ip, peer_port)
            
            # NEW: Send handshake immediately to establish connection
            handshake = {'type': 'handshake', 'peer_id': self.peer_id}
            self._send_to_peer(peer_id, handshake)
            
            print(f"✓ Connected to peer {peer_id} at {peer_ip}:{peer_port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to peer {peer_id}: {e}")
            return False

# NEW helper method
    def _send_to_peer(self, peer_id: str, message: dict):
        """Internal send to single peer"""
        try:
            ip, port = self.peers[peer_id]
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.settimeout(3.0)
            peer_socket.connect((ip, port))
            peer_socket.send(json.dumps(message).encode('utf-8'))
            peer_socket.close()
        except Exception as e:
            print(f"✗ Send failed to {peer_id}: {e}")
            with self.peer_lock:
                self.peers.pop(peer_id, None)

    
    def broadcast_message(self, message: dict) -> int:
        message['peer_id'] = self.peer_id
        message_json = json.dumps(message)
        successful_sends = 0
        
        with self.peer_lock:
            peers_copy = list(self.peers.items())
        
        for peer_id, (ip, port) in peers_copy:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.settimeout(3.0)  # Slightly longer timeout
                peer_socket.connect((ip, port))
                peer_socket.send(message_json.encode('utf-8'))
                peer_socket.close()
                successful_sends += 1
                print(f"[DEBUG] ✓ Sent to {peer_id} ({ip}:{port})")
            except Exception as e:
                print(f"✗ Failed to send to peer {peer_id} ({ip}:{port}): {type(e).__name__}: {e}")
                # Don't remove immediately - retry next time
                # with self.peer_lock:
                #     self.peers.pop(peer_id, None)  # Comment out for now
        return successful_sends

    
    def add_message_handler(self, handler: Callable):
        """
        Add a message handler callback
        
        Args:
            handler: Callable that accepts message dict
        """
        self.message_handlers.append(handler)
    
    def get_peer_count(self) -> int:
        """Get number of connected peers"""
        with self.peer_lock:
            return len(self.peers)
    
    def get_peers(self) -> Dict[str, Tuple[str, int]]:
        """Get copy of connected peers dictionary"""
        with self.peer_lock:
            return self.peers.copy()
    
    def stop(self):
        """Stop the P2P host"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
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
