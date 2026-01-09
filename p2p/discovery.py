"""Peer discovery using UDP broadcast for local network"""

import socket
import json
import threading
import time
from typing import Callable, Set


class PeerDiscovery:
    """Peer discovery using UDP broadcast"""
    
    BROADCAST_PORT = 37020
    DISCOVERY_INTERVAL = 5  # seconds between announcements
    
    def __init__(self, peer_id: str, p2p_port: int, 
                 on_peer_found: Callable):
        """
        Initialize peer discovery
        
        Args:
            peer_id: This peer's unique identifier
            p2p_port: P2P communication port
            on_peer_found: Callback when peer discovered
        """
        self.peer_id = peer_id
        self.p2p_port = p2p_port
        self.on_peer_found = on_peer_found
        self.running = False
        self.discovered_peers: Set[str] = set()
        
        # Create UDP socket for broadcasting
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Create UDP socket for listening
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.rendezvous = ""
    
    def start(self, rendezvous: str):
        """
        Start peer discovery
        
        Args:
            rendezvous: Service name/rendezvous point for discovery
        """
        self.rendezvous = rendezvous
        self.running = True
        
        # Bind listen socket to broadcast port
        try:
            self.listen_socket.bind(('', self.BROADCAST_PORT))
        except OSError as e:
            print(f"⚠ Port {self.BROADCAST_PORT} already in use: {e}")
            print("  Discovery may be limited to locally initiated connections")
        
        # Start broadcaster thread
        broadcast_thread = threading.Thread(
            target=self._broadcast_presence,
            daemon=True
        )
        broadcast_thread.start()
        
        # Start listener thread
        listen_thread = threading.Thread(
            target=self._listen_for_peers,
            daemon=True
        )
        listen_thread.start()
        
        print(f"✓ Peer discovery started")
        print(f"  Rendezvous: {rendezvous}")
        print(f"  Broadcasting on UDP port {self.BROADCAST_PORT}")
    
    def _broadcast_presence(self):
        """Periodically broadcast presence to local network"""
        while self.running:
            try:
                announcement = {
                    'type': 'peer_announcement',
                    'peer_id': self.peer_id,
                    'p2p_port': self.p2p_port,
                    'rendezvous': self.rendezvous
                }
                
                message = json.dumps(announcement).encode('utf-8')
                self.broadcast_socket.sendto(
                    message,
                    ('255.255.255.255', self.BROADCAST_PORT)
                )
                
            except Exception as e:
                if self.running:
                    print(f"Broadcast error: {e}")
            
            time.sleep(self.DISCOVERY_INTERVAL)
    
    def _listen_for_peers(self):
        """Listen for peer announcements from network"""
        self.listen_socket.settimeout(1.0)
        
        while self.running:
            try:
                data, addr = self.listen_socket.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                
                # Ignore our own broadcasts
                if message.get('peer_id') == self.peer_id:
                    continue
                
                # Check if it's for our rendezvous point
                if message.get('rendezvous') != self.rendezvous:
                    continue
                
                peer_id = message.get('peer_id')
                peer_port = message.get('p2p_port')  # FIXED: Use this, not addr[1]
                peer_ip = addr[0]  # IP from packet is still correct
                
                # New peer discovered
                if peer_id and peer_id not in self.discovered_peers:
                    self.discovered_peers.add(peer_id)
                    print(f"✓ Discovered peer: {peer_id} at {peer_ip}:{peer_port}")
                    
                    # Notify callback
                    if self.on_peer_found:
                        try:
                            self.on_peer_found(peer_id, peer_ip, peer_port)  # Now correct port
                        except Exception as e:
                            print(f"Error in peer discovery callback: {e}")
                            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Listen error: {e}")

    
    def get_discovered_peers(self) -> Set[str]:
        """Get set of discovered peer IDs"""
        return self.discovered_peers.copy()
    
    def stop(self):
        """Stop peer discovery"""
        self.running = False
        try:
            self.broadcast_socket.close()
            self.listen_socket.close()
        except:
            pass
        print("✓ Peer discovery stopped")


def init_mdns(peer_id: str, p2p_port: int, rendezvous: str, 
              on_peer_found: Callable) -> PeerDiscovery:
    """
    Initialize peer discovery service
    
    Args:
        peer_id: This peer's ID
        p2p_port: P2P communication port
        rendezvous: Service name for discovery
        on_peer_found: Callback when peer discovered
        
    Returns:
        PeerDiscovery instance
    """
    discovery = PeerDiscovery(peer_id, p2p_port, on_peer_found)
    discovery.start(rendezvous)
    return discovery
