#!/usr/bin/env python3
"""
Test script for the LLM model used in the voice assistant.
This script loads the Mistral-7B model and tests it with various prompts.
"""

import os
import sys
import time
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "voice_assistant"))

from model import LLM
from util import timer


def test_llm_loading():
    """Test that the LLM can be loaded successfully."""
    print("🔧 Testing LLM loading...")
    
    # Get the model path from the project structure
    model_path = Path(__file__).parent.parent / "voice_assistant" / "models" / "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
    
    if not model_path.exists():
        print(f"❌ Model not found at: {model_path}")
        print("Please run 'poe download-llm' first to download the model.")
        return False
    
    try:
        # Initialize the LLM with the same parameters as in the main app
        llm = LLM(str(model_path), n_ctx=512)
        print("✅ LLM loaded successfully!")
        return llm
    except Exception as e:
        print(f"❌ Error loading LLM: {e}")
        return False


def test_basic_prompts(llm):
    """Test the LLM with basic prompts."""
    print("\n🧪 Testing basic prompts...")
    
    test_prompts = [
        "Hello, how are you?",
        "What is 2 + 2?",
        "Tell me a short joke.",
        "What is the capital of France?",
        "Explain quantum computing in one sentence."
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Prompt: {prompt}")
        
        try:
            start_time = time.time()
            response = llm.generate(prompt)
            end_time = time.time()
            
            print(f"Response: {response}")
            print(f"Time taken: {end_time - start_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")


def test_conversation_flow(llm):
    """Test the LLM with a conversation flow."""
    print("\n💬 Testing conversation flow...")
    
    conversation = [
        "Hi, my name is Alice.",
        "What's my name?",
        "Can you help me with a math problem?",
        "What is 15 * 23?",
        "Thank you for your help!"
    ]
    
    for i, prompt in enumerate(conversation, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {prompt}")
        
        try:
            start_time = time.time()
            response = llm.generate(prompt)
            end_time = time.time()
            
            print(f"Assistant: {response}")
            print(f"Time taken: {end_time - start_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error in conversation: {e}")


def test_edge_cases(llm):
    """Test the LLM with edge cases and unusual inputs."""
    print("\n🔍 Testing edge cases...")
    
    edge_cases = [
        "",  # Empty prompt
        "   ",  # Whitespace only
        "A" * 1000,  # Very long prompt
        "What is the meaning of life?",  # Philosophical question
        "Write a haiku about programming",  # Creative request
        "Translate 'hello world' to Spanish",  # Translation request
    ]
    
    for i, prompt in enumerate(edge_cases, 1):
        print(f"\n--- Edge Case {i} ---")
        print(f"Prompt: {repr(prompt)}")
        
        try:
            start_time = time.time()
            response = llm.generate(prompt)
            end_time = time.time()
            
            print(f"Response: {response}")
            print(f"Time taken: {end_time - start_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error with edge case: {e}")


def test_performance(llm):
    """Test the LLM performance with multiple rapid requests."""
    print("\n⚡ Testing performance...")
    
    test_prompt = "Say hello in a friendly way."
    num_tests = 5
    
    times = []
    
    for i in range(num_tests):
        print(f"\n--- Performance Test {i+1}/{num_tests} ---")
        
        try:
            start_time = time.time()
            response = llm.generate(test_prompt)
            end_time = time.time()
            
            elapsed = end_time - start_time
            times.append(elapsed)
            
            print(f"Response: {response}")
            print(f"Time taken: {elapsed:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error in performance test: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Performance Summary:")
        print(f"Average response time: {avg_time:.2f} seconds")
        print(f"Fastest response: {min_time:.2f} seconds")
        print(f"Slowest response: {max_time:.2f} seconds")


def main():
    """Main test function."""
    print("🚀 Starting LLM Test Suite")
    print("=" * 50)
    
    # Test LLM loading
    llm = test_llm_loading()
    if not llm:
        print("\n❌ Failed to load LLM. Exiting.")
        return
    
    # Run all tests
    test_basic_prompts(llm)
    test_conversation_flow(llm)
    test_edge_cases(llm)
    test_performance(llm)
    
    print("\n" + "=" * 50)
    print("✅ LLM Test Suite completed!")
    print("\n💡 Tips:")
    print("- If responses are slow, consider using a smaller model")
    print("- If responses are poor quality, try adjusting temperature or other parameters")
    print("- The model uses llama-cpp-python for inference")


if __name__ == "__main__":
    main() 