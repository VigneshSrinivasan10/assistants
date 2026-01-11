# Hybrid Routing System

The voice assistant uses a **hybrid routing system** that combines fast keyword matching with LLM fallback for robust query handling.

## Architecture

```
User Query → Handler Registry (Fast Path) → Specialized Handler
                      ↓ (no match)
                    LLM (Fallback)
```

## Features

✨ **Fast keyword matching** for common queries
⚡ **Priority-based routing** (highest priority checked first)
🔌 **Plugin-based extensibility** (easy to add new handlers)
🛡️ **Error handling** (continues to next handler on error)
📊 **Logging & monitoring** (tracks which handler processes each query)

## How It Works

1. **Fast Path**: Query is checked against registered handlers in priority order
2. **Match Found**: Handler processes the query and returns response
3. **No Match**: Falls back to LLM for general conversation

## Adding a New Handler

### Step 1: Create Handler Class

```python
from voice_assistant.routing import Handler

class CalculatorHandler(Handler):
    def __init__(self, priority: int = 8):
        super().__init__(name="Calculator", priority=priority)

    def can_handle(self, query: str) -> bool:
        """Fast check using keywords/regex"""
        keywords = ['calculate', 'multiply', 'divide', 'add', 'subtract']
        return any(kw in query.lower() for kw in keywords)

    def process(self, query: str) -> str:
        """Process the calculation"""
        # Your logic here
        return "The result is 42"

    def get_keywords(self) -> list:
        """Optional: for optimization"""
        return ['calculate', 'multiply', 'divide', 'add', 'subtract']
```

### Step 2: Register Handler

In `voice_assistant/model.py`:

```python
from voice_assistant.routing import CalculatorHandler

class VoiceAssistant:
    def __init__(self, cfg: DictConfig):
        # ... existing init ...

        # Register your handler
        self.router.register(CalculatorHandler(priority=8))
```

That's it! 🎉

## Current Handlers

| Handler | Priority | Keywords |
|---------|----------|----------|
| Weather | 10 | weather, temperature, rain, forecast, etc. |
| Calculator | - | (placeholder, not implemented) |
| Reminder | - | (placeholder, not implemented) |

## Priority Guidelines

- **10**: Critical/frequently-used handlers (Weather)
- **8-9**: Important handlers (Calculator, Reminders)
- **5-7**: Optional/specialized handlers
- **1-4**: Experimental handlers

Higher priority = checked first

## Handler API

### Required Methods

- `can_handle(query: str) -> bool`: Fast check if handler can process query
- `process(query: str) -> str`: Process query and return response

### Optional Methods

- `get_keywords() -> List[str]`: Return keywords for optimization/indexing

## Examples

### Weather Query
```
User: "What's the weather in Berlin?"
→ WeatherHandler.can_handle() → True
→ WeatherHandler.process() → "The weather in Berlin is 15°C with clear skies."
```

### General Query
```
User: "Tell me a joke"
→ All handlers.can_handle() → False
→ Fallback to LLM → "Why did the chicken cross the road?..."
```

### Calculator Query (when implemented)
```
User: "Calculate 5 times 7"
→ CalculatorHandler.can_handle() → True
→ CalculatorHandler.process() → "5 times 7 equals 35"
```

## Debugging

Get routing information:

```python
assistant = VoiceAssistant(cfg)
info = assistant.get_routing_info()
print(info)
# {'total_handlers': 1, 'handlers': [{'name': 'Weather', 'priority': 10, 'keywords': [...]}]}
```

Enable logging:

```python
import logging
logging.getLogger('voice_assistant.routing').setLevel(logging.DEBUG)
```

## Testing

Run routing tests:

```bash
python tests/test_routing.py
```

## Benefits Over Simple If-Else

### Before (Simple If-Else)
```python
if weather._is_weather_query(query):
    return weather.process(query)
else:
    return llm.generate(query)
```

❌ Hard to add new features
❌ No priority system
❌ No error handling
❌ Difficult to test

### After (Handler Registry)
```python
handler_name, response = router.route(query)
if response is None:
    response = llm.generate(query)
```

✅ Easy to add handlers (just register)
✅ Priority-based routing
✅ Built-in error handling
✅ Easy to test & monitor

## Future Enhancements

Possible improvements:

1. **LLM-based routing** for complex queries
2. **Confidence scores** for each handler
3. **A/B testing** different handlers
4. **Handler chaining** (preprocessing/postprocessing)
5. **Async handlers** for I/O-bound operations
6. **Caching** frequently-accessed handler results

---

**Questions?** See `voice_assistant/routing.py` for implementation details.
