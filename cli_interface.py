"""
CLI Interface for terminal-based messaging
Allows typing messages directly in the terminal while HTTP server runs
- Only shows errors, no success spam
- Clean chat experience
"""

import threading
import sys
from typing import Optional


class TerminalInterface:
    """
    Handles terminal input for P2P messaging
    Runs in separate thread while Flask HTTP server runs
    """
    
    def __init__(self, chat_room, nickname: str):
        """
        Initialize terminal interface
        
        Args:
            chat_room: ChatRoom instance
            nickname: User's nickname
        """
        self.chat_room = chat_room
        self.nickname = nickname
        self.running = True
    
    def start(self):
        """Start the terminal input loop in a background thread"""
        terminal_thread = threading.Thread(
            target=self._input_loop,
            daemon=True
        )
        terminal_thread.start()
    
    def _input_loop(self):
        """
        Main loop for reading terminal input
        Similar to Go version with bufio.NewReader
        """
        print("\n" + "="*70)
        print("📝 Terminal Input Enabled")
        print("="*70)
        print("Type your messages and press Enter to send")
        print("Type 'quit' or 'exit' to stop (or press Ctrl+C)")
        print("="*70 + "\n")
        
        while self.running:
            try:
                # Read from stdin (like Go's bufio.NewReader)
                message = input(f"[{self.nickname}] > ").strip()
                
                # Check for exit commands
                if message.lower() in ['quit', 'exit', 'q']:
                    print("\n🛑 Exiting terminal interface...\n")
                    self.running = False
                    break
                
                # Skip empty messages (silently)
                if not message:
                    continue
                
                # Send message (silently on success)
                try:
                    success = self.chat_room.publish(message)
                    
                    # ONLY show error messages, not success
                    if not success:
                        print(f"❌ Failed to send message")
                    # else: Silent success - don't interrupt chat
                    
                except Exception as e:
                    # Only show actual errors
                    print(f"❌ Error: {e}")
                
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully (silent)
                print("\n\n🛑 Exiting...")
                self.running = False
                break
            except EOFError:
                # Handle EOF (end of input) gracefully
                self.running = False
                break
            except Exception as e:
                # Only show critical errors
                print(f"❌ Critical error: {e}")
                continue
    
    def stop(self):
        """Stop the terminal interface"""
        self.running = False


def start_terminal_interface(chat_room, nickname: str) -> Optional[TerminalInterface]:
    """
    Start terminal interface in background thread
    
    Args:
        chat_room: ChatRoom instance
        nickname: User's nickname
        
    Returns:
        TerminalInterface instance
    """
    terminal = TerminalInterface(chat_room, nickname)
    terminal.start()
    return terminal
