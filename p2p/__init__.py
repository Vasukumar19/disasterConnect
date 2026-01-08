"""
DisasterNet P2P Module

Provides peer-to-peer networking functionality for emergency communication
without requiring internet connectivity.
"""

from .host import create_host
from .discovery import init_mdns
from .chatroom import ChatRoom, ChatMessage, join_chat_room

__all__ = [
    'create_host',
    'init_mdns', 
    'ChatRoom',
    'ChatMessage',
    'join_chat_room'
]

__version__ = '1.0.0'