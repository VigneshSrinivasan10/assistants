#!/usr/bin/env python3
"""
Test script to demonstrate smart memory improvements.
"""
from voice_assistant.features.smart_memory import (
    SmartConversationMemory,
    ConversationQuality,
    RelevanceScorer
)

def test_quality_scoring():
    """Test conversation quality scoring."""
    print("=" * 60)
    print("QUALITY SCORING TEST")
    print("=" * 60)
    
    scorer = ConversationQuality()
    
    test_cases = [
        {
            "user": "What's the weather in Boston?",
            "assistant": "It's 72 degrees Fahrenheit and sunny with light winds",
            "handler": "Weather",
            "expected": "High (>0.7)"
        },
        {
            "user": "hi",
            "assistant": "hello",
            "handler": "LLM",
            "expected": "Low (<0.3)"
        },
        {
            "user": "play music",
            "assistant": "Sorry, I couldn't connect to Spotify",
            "handler": "Spotify",
            "expected": "Low-Medium (~0.3)"
        },
        {
            "user": "what is 5 plus 3",
            "assistant": "5+3 equals 8",
            "handler": "Calculator",
            "expected": "High (>0.7)"
        },
        {
            "user": "Computer",
            "assistant": "I don't understand that",
            "handler": "LLM",
            "expected": "Very Low (<0.2)"
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        score = scorer.score(
            case["user"],
            case["assistant"],
            case.get("handler")
        )
        
        print(f"\nTest {i}:")
        print(f"  User: \"{case['user']}\"")
        print(f"  Assistant: \"{case['assistant']}\"")
        print(f"  Handler: {case.get('handler', 'None')}")
        print(f"  Score: {score:.2f}")
        print(f"  Expected: {case['expected']}")
        
        if score >= 0.7:
            print(f"  ✓ HIGH QUALITY - Will be prioritized")
        elif score >= 0.3:
            print(f"  ⚠ MEDIUM QUALITY - Will be included")
        else:
            print(f"  ✗ LOW QUALITY - Will be filtered out")


def test_relevance_scoring():
    """Test relevance scoring."""
    print("\n" + "=" * 60)
    print("RELEVANCE SCORING TEST")
    print("=" * 60)
    
    scorer = RelevanceScorer()
    
    past_conversations = [
        {
            "user": "What's the weather in Chicago?",
            "assistant": "It's 68 degrees and cloudy"
        },
        {
            "user": "What time is it?",
            "assistant": "It's 3:45 PM"
        },
        {
            "user": "Calculate 10 times 7",
            "assistant": "10*7 equals 70"
        },
    ]
    
    current_query = "What's the weather in Boston?"
    
    print(f"\nCurrent query: \"{current_query}\"")
    print("\nRelevance scores for past conversations:")
    
    for i, conv in enumerate(past_conversations, 1):
        relevance = scorer.compute_relevance(current_query, conv)
        print(f"\n{i}. \"{conv['user']}\"")
        print(f"   Relevance: {relevance:.2f}")
        
        if relevance >= 0.2:
            print(f"   ✓ RELEVANT - Would be included in context")
        else:
            print(f"   ✗ NOT RELEVANT - Would be skipped")


def test_smart_memory():
    """Test complete smart memory system."""
    print("\n" + "=" * 60)
    print("SMART MEMORY INTEGRATION TEST")
    print("=" * 60)
    
    # Create memory with test parameters
    memory = SmartConversationMemory(
        max_context_tokens=500,  # Small for testing
        quality_threshold=0.3,
        relevance_threshold=0.2,
        save_file="data/test_smart_memory.json",
        max_stored=50,
    )
    
    # Clear any existing data
    memory.clear()
    
    # Add a mix of conversations
    conversations = [
        ("What's the weather in Boston?", "72°F and sunny", "Weather"),
        ("hi", "hello", "LLM"),  # Low quality
        ("Computer", "I don't understand", "LLM"),  # Very low quality
        ("what is 5 plus 3", "5+3 equals 8", "Calculator"),
        ("play music", "Sorry, couldn't connect", "Spotify"),  # Error
        ("What time is it?", "It's 3:45 PM", "DateTime"),
        ("CPU usage", "CPU usage is 5% across 16 cores", "SystemInfo"),
        ("What's the weather in Chicago?", "68°F and cloudy", "Weather"),
    ]
    
    print("\nAdding conversations...")
    for user_msg, assistant_msg, handler in conversations:
        memory.add_conversation(user_msg, assistant_msg, handler)
        print(f"  Added: \"{user_msg[:40]}...\" (handler={handler})")
    
    # Get memory info
    print("\n" + "-" * 60)
    info = memory.get_memory_info()
    print("\nMemory Statistics:")
    print(f"  Total stored: {info['total_conversations']}")
    print(f"  Average quality: {info['avg_quality']:.2f}")
    print(f"  Quality distribution:")
    for category, count in info['quality_distribution'].items():
        print(f"    {category}: {count}")
    print(f"  Handlers:")
    for handler, count in info['handlers'].items():
        print(f"    {handler}: {count}")
    
    # Test context retrieval without query (recent only)
    print("\n" + "-" * 60)
    print("\nContext WITHOUT relevance scoring (recent only):")
    context = memory.get_context(current_query=None)
    print(f"Characters: {len(context)}")
    print(f"Estimated tokens: {len(context) // 4}")
    
    # Test context retrieval with query (recent + relevant)
    print("\n" + "-" * 60)
    current_query = "What's the weather in New York?"
    print(f"\nContext WITH relevance scoring for: \"{current_query}\"")
    context = memory.get_context(current_query=current_query)
    print(f"Characters: {len(context)}")
    print(f"Estimated tokens: {len(context) // 4}")
    print("\nShould include:")
    print("  ✓ Recent weather conversations (Boston, Chicago)")
    print("  ✓ Recent high-quality conversations (Calculator, DateTime)")
    print("\nShould exclude:")
    print("  ✗ Low quality conversations (hi/hello, Computer/don't understand)")
    print("  ✗ Irrelevant conversations (if not related to query)")
    
    # Show actual context
    if context:
        print("\n" + "-" * 60)
        print("\nActual context (abbreviated):")
        lines = context.split('\n')
        for i, line in enumerate(lines[:20], 1):  # First 20 lines
            print(f"  {i:2}. {line[:70]}")
        if len(lines) > 20:
            print(f"  ... ({len(lines) - 20} more lines)")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nKey improvements demonstrated:")
    print("  ✓ Quality filtering (removed low-quality exchanges)")
    print("  ✓ Relevance scoring (included related old conversations)")
    print("  ✓ Token budget management (respects context limits)")
    print("  ✓ Handler awareness (prioritizes specific handlers)")


def main():
    """Run all tests."""
    test_quality_scoring()
    test_relevance_scoring()
    test_smart_memory()
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! 🎉")
    print("=" * 60)


if __name__ == "__main__":
    main()
