import json
import threading
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class ChatMessage:
    """Represents a chat message"""
    Message: str
    SenderID: str
    SenderNick: str
    Timestamp: str = None
    
    def __post_init__(self):
        if self.Timestamp is None:
            self.Timestamp = datetime.now().isoformat()


class ChatRoom:
    """
    Chat room for P2P messaging
    Manages message publishing and receiving
    """
    
    def __init__(self, room_name: str, nickname: str, peer_id: str, p2p_host):
        self.room_name = room_name
        self.nickname = nickname
        self.peer_id = peer_id
        self.p2p_host = p2p_host
        self.messages: List[ChatMessage] = []
        self.message_lock = threading.Lock()
        
        # Register message handler with P2P host
        self.p2p_host.add_message_handler(self._handle_incoming_message)
    
    @staticmethod
    def topic_name(room_name: str) -> str:
        """Generate topic name from room name"""
        return f"chat-room:{room_name}"
    
    def publish(self, message: str):
        """
        Publish a message to the chat room
        
        Args:
            message: Text message to send
        """
        chat_msg = ChatMessage(
            Message=message,
            SenderID=self.peer_id,
            SenderNick=self.nickname
        )
        
        # Add to local messages
        with self.message_lock:
            self.messages.append(chat_msg)
        
        # Broadcast to peers
        broadcast_data = {
            'type': 'chat_message',
            'room': self.room_name,
            'data': asdict(chat_msg)
        }
        
        self.p2p_host.broadcast_message(broadcast_data)
        print(f"📤 Sent: [{self.nickname}] {message}")
    
    def _handle_incoming_message(self, message_data: dict):
        """Handle incoming message from peer"""
        try:
            # Check if it's a chat message for this room
            if message_data.get('type') != 'chat_message':
                return
            
            if message_data.get('room') != self.room_name:
                return
            
            # Parse chat message
            data = message_data.get('data', {})
            chat_msg = ChatMessage(**data)
            
            # Don't add our own messages again
            if chat_msg.SenderID == self.peer_id:
                return
            
            # Add to messages
            with self.message_lock:
                # Check for duplicates
                if not any(m.SenderID == chat_msg.SenderID and 
                          m.Message == chat_msg.Message and 
                          m.Timestamp == chat_msg.Timestamp 
                          for m in self.messages):
                    self.messages.append(chat_msg)
                    print(f"📥 Received: [{chat_msg.SenderNick}] {chat_msg.Message}")
                    
        except Exception as e:
            print(f"Error handling incoming message: {e}")
    
    def get_messages(self) -> List[str]:
        """Get all messages formatted as strings"""
        with self.message_lock:
            return [f"[{msg.SenderNick}]: {msg.Message}" for msg in self.messages]
    
    def get_message_objects(self) -> List[ChatMessage]:
        """Get all message objects"""
        with self.message_lock:
            return self.messages.copy()
    
    def clear_messages(self):
        """Clear all messages"""
        with self.message_lock:
            self.messages.clear()


def join_chat_room(room_name: str, nickname: str, peer_id: str, p2p_host) -> ChatRoom:
    """
    Join a chat room
    
    Args:
        room_name: Name of the room to join
        nickname: User's nickname
        peer_id: Peer ID of the user
        p2p_host: P2P host instance
        
    Returns:
        ChatRoom instance
    """
    chat_room = ChatRoom(room_name, nickname, peer_id, p2p_host)
    print(f"✓ Joined chat room: {room_name}")
    return chat_room