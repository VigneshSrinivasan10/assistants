#!/usr/bin/env python3
"""
Interactive test script for the LLM model.
This script allows you to chat directly with the Mistral-7B model via Ollama.
"""

import os
import sys
import time
from pathlib import Path

# Add the voice_assistant directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "voice_assistant"))

from model import LLM
from omegaconf import OmegaConf
import hydra

def load_llm():
    """Load the LLM model."""
    print("🔧 Loading LLM model with Ollama...")

    try:
        # Initialize the LLM with Ollama
        llm = LLM(model_name="mistral:7b-instruct-q4_K_M")
        print("✅ LLM loaded successfully with Ollama!")
        return llm
    except Exception as e:
        print(f"❌ Error loading LLM: {e}")
        print("Please ensure:")
        print("1. Ollama is installed (curl -fsSL https://ollama.com/install.sh | sh)")
        print("2. Ollama service is running (ollama serve)")
        print("3. Model is downloaded (poe download-llm or ollama pull mistral:7b-instruct-q4_K_M)")
        return None


def interactive_chat(llm):
    """Start an interactive chat session with the LLM."""
    print("\n💬 Interactive Chat Session")
    print("Type 'quit', 'exit', or 'bye' to end the session")
    print("Type 'help' for available commands")
    print("-" * 50)
    
    conversation_history = []
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            # Check for help command
            if user_input.lower() == 'help':
                print("\n📖 Available commands:")
                print("- quit/exit/bye: End the session")
                print("- help: Show this help message")
                print("- clear: Clear conversation history")
                print("- stats: Show conversation statistics")
                print("- Any other text will be sent to the LLM")
                continue
            
            # Check for clear command
            if user_input.lower() == 'clear':
                conversation_history.clear()
                print("🗑️ Conversation history cleared")
                continue
            
            # Check for stats command
            if user_input.lower() == 'stats':
                print(f"📊 Conversation Statistics:")
                print(f"- Total messages: {len(conversation_history)}")
                if conversation_history:
                    avg_time = sum(msg['time'] for msg in conversation_history) / len(conversation_history)
                    print(f"- Average response time: {avg_time:.2f} seconds")
                continue
            
            # Skip empty input
            if not user_input:
                continue
            
            # Generate response
            print("🤖 Assistant: ", end="", flush=True)
            start_time = time.time()
            
            response = llm.generate(user_input)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(response)
            print(f"⏱️ Response time: {elapsed_time:.2f} seconds")
            
            # Store in conversation history
            conversation_history.append({
                'user': user_input,
                'assistant': response,
                'time': elapsed_time
            })
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.")


def main():
    """Main function."""
    print("🚀 Interactive LLM Test")
    print("=" * 30)
    
    # Load the LLM
    llm = load_llm()
    if not llm:
        return
    
    # Start interactive chat
    interactive_chat(llm)


if __name__ == "__main__":
    main() 