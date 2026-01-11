"""
Test cases for the routing system.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice_assistant.routing import HandlerRegistry, Handler, WeatherHandler
from voice_assistant.features.weather import WeatherForecast


class MockHandler(Handler):
    """Mock handler for testing."""

    def __init__(self, name: str, priority: int, keywords: list):
        super().__init__(name, priority)
        self._keywords = keywords
        self.call_count = 0

    def can_handle(self, query: str) -> bool:
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self._keywords)

    def process(self, query: str) -> str:
        self.call_count += 1
        return f"{self.name} processed: {query}"

    def get_keywords(self) -> list:
        return self._keywords


def test_handler_registry():
    """Test basic handler registry functionality."""
    print("\n=== Test: Handler Registry ===")

    registry = HandlerRegistry()

    # Register handlers with different priorities
    calculator = MockHandler("Calculator", priority=8, keywords=["calculate", "math"])
    reminder = MockHandler("Reminder", priority=9, keywords=["remind", "reminder"])

    registry.register(calculator)
    registry.register(reminder)

    print(f"Registered handlers: {len(registry)}")
    assert len(registry) == 2, "Should have 2 handlers"

    # Check priority ordering (reminder should be first due to higher priority)
    assert registry.handlers[0].name == "Reminder", "Reminder should be first (priority 9)"
    assert registry.handlers[1].name == "Calculator", "Calculator should be second (priority 8)"

    print("✓ Handler registration and priority ordering works")


def test_routing():
    """Test query routing to correct handler."""
    print("\n=== Test: Query Routing ===")

    registry = HandlerRegistry()

    calculator = MockHandler("Calculator", priority=8, keywords=["calculate", "math"])
    reminder = MockHandler("Reminder", priority=9, keywords=["remind", "reminder"])

    registry.register(calculator)
    registry.register(reminder)

    # Test routing to calculator
    handler_name, response = registry.route("calculate 5 plus 3")
    assert handler_name == "Calculator", "Should route to Calculator"
    assert calculator.call_count == 1, "Calculator should be called once"
    print(f"✓ Routed 'calculate 5 plus 3' to {handler_name}")

    # Test routing to reminder
    handler_name, response = registry.route("remind me to call mom")
    assert handler_name == "Reminder", "Should route to Reminder"
    assert reminder.call_count == 1, "Reminder should be called once"
    print(f"✓ Routed 'remind me to call mom' to {handler_name}")

    # Test fallback (no handler)
    handler_name, response = registry.route("tell me a joke")
    assert handler_name is None, "Should return None for unhandled query"
    assert response is None, "Should return None response for unhandled query"
    print(f"✓ Unhandled query returns None (will fallback to LLM)")


def test_weather_handler():
    """Test weather handler integration."""
    print("\n=== Test: Weather Handler ===")

    # Initialize weather service
    weather = WeatherForecast(provider="openmeteo")

    # Create registry with weather handler
    registry = HandlerRegistry()
    registry.register(WeatherHandler(weather, priority=10))

    # Test weather query routing
    weather_queries = [
        "What's the weather like?",
        "Is it going to rain today?",
        "What's the temperature in Berlin?",
    ]

    for query in weather_queries:
        handler_name, response = registry.route(query)
        assert handler_name == "Weather", f"Should route '{query}' to Weather"
        assert response is not None, "Should get a weather response"
        print(f"✓ Weather query: '{query}' -> {handler_name}")

    # Test non-weather query
    handler_name, response = registry.route("Tell me about Python programming")
    assert handler_name is None, "Non-weather query should not route to Weather"
    print(f"✓ Non-weather query correctly returns None")


def test_priority_override():
    """Test that higher priority handlers are checked first."""
    print("\n=== Test: Priority Override ===")

    registry = HandlerRegistry()

    # Both handlers match the word "time"
    low_priority = MockHandler("LowPriority", priority=5, keywords=["time"])
    high_priority = MockHandler("HighPriority", priority=10, keywords=["time"])

    registry.register(low_priority)
    registry.register(high_priority)

    # High priority should handle it
    handler_name, response = registry.route("what time is it")
    assert handler_name == "HighPriority", "Higher priority handler should be chosen"
    assert high_priority.call_count == 1, "High priority handler should be called"
    assert low_priority.call_count == 0, "Low priority handler should not be called"
    print(f"✓ Higher priority handler takes precedence")


def test_handler_info():
    """Test getting handler information."""
    print("\n=== Test: Handler Info ===")

    registry = HandlerRegistry()
    calculator = MockHandler("Calculator", priority=8, keywords=["calculate", "math"])
    registry.register(calculator)

    info = registry.get_handlers_info()
    assert len(info) == 1, "Should have info for 1 handler"
    assert info[0]["name"] == "Calculator", "Name should match"
    assert info[0]["priority"] == 8, "Priority should match"
    assert info[0]["keywords"] == ["calculate", "math"], "Keywords should match"
    print(f"✓ Handler info: {info[0]}")


def run_all_tests():
    """Run all routing tests."""
    print("\n" + "=" * 50)
    print("Running Routing System Tests")
    print("=" * 50)

    try:
        test_handler_registry()
        test_routing()
        test_weather_handler()
        test_priority_override()
        test_handler_info()

        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
