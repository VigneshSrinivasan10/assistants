import json
import os
from collections import deque
from typing import Optional

class ConversationMemory:
    def __init__(self, max_conversations: int = 10, save_file: str = "./data/conversation_memory.json"):
        self.max_conversations = max_conversations
        # Limited deque for LLM context (last N conversations)
        self.conversations = deque(maxlen=max_conversations)
        # Full list for persistent storage (all conversations)
        self.all_conversations = []
        self.save_file = save_file
        
        # Load existing conversations from file
        self.load_memory()
    
    def add_conversation(self, user_message: str, assistant_response: str):
        """Add a new conversation pair to memory"""
        conversation = {
            "user": user_message,
            "assistant": assistant_response
        }
        
        # Add to limited deque for LLM context
        self.conversations.append(conversation)
        
        # Add to full list for persistent storage
        self.all_conversations.append(conversation)
        
        # Save to file after each addition
        self.save_memory()
    
    def get_context(self) -> str:
        """Get formatted conversation history for LLM context (last N conversations only)"""
        if not self.conversations:
            return ""
        
        context_parts = []
        for conv in self.conversations:
            context_parts.append(f"<|user|>\n{conv['user']}\n<|end|>")
            context_parts.append(f"<|assistant|>\n{conv['assistant']}\n<|end|>")
        
        return "\n".join(context_parts)
    
    def save_memory(self):
        """Save all conversations to JSON file"""
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "conversations": self.all_conversations,  # Save all conversations
                }, f, indent=2, ensure_ascii=False)
            
            print(f"Conversation memory saved to {self.save_file} ({len(self.all_conversations)} total conversations)")
        except Exception as e:
            print(f"Error saving conversation memory: {e}")
    
    def load_memory(self):
        """Load conversations from JSON file"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load all conversations
                all_conversations_list = data.get("conversations", [])
                self.all_conversations = all_conversations_list
                
                # Load only the last N conversations into the limited deque
                recent_conversations = all_conversations_list[-self.max_conversations:] if all_conversations_list else []
                for conv in recent_conversations:
                    self.conversations.append(conv)
                
                print(f"Loaded {len(all_conversations_list)} total conversations, using last {len(self.conversations)} for context")
            else:
                print(f"No existing conversation memory file found at {self.save_file}")
                
            # Create the base directory for the save file if it doesn't exist
            save_dir = os.path.dirname(self.save_file)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
                print(f"Created directory: {save_dir}")
        except Exception as e:
            print(f"Error loading conversation memory: {e}")
            # Continue with empty memory if loading fails
    
    def get_memory_info(self) -> dict:
        """Get information about the current memory state"""
        return {
            "total_conversations": len(self.all_conversations),
            "context_conversations": len(self.conversations),
            "max_conversations": self.max_conversations,
            "save_file": self.save_file,
            "file_exists": os.path.exists(self.save_file)
        }
    
    def get_all_conversations(self) -> list:
        """Get all stored conversations (for debugging/analysis)"""
        return self.all_conversations.copy() 