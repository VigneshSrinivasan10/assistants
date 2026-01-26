# New Features Added to Voice Assistant

## Summary
Added 3 new feature handlers to the voice assistant:
- **Calculator** - Math calculations
- **DateTime Info** - Time and date queries  
- **System Info** - CPU, memory, disk usage

## Features

### 1. Calculator (Priority: 8)
**Location:** `voice_assistant/features/calculator.py`

**Voice Commands:**
- "What is 5 plus 3"
- "Calculate 10 times 7"
- "What's 100 divided by 4"
- "Compute 2 to the power of 8"
- "What is 25 squared"

**Examples:**
- User: "Computer, what is 15 plus 27"
- Assistant: "15+27 equals 42"

### 2. DateTime Info (Priority: 8)
**Location:** `voice_assistant/features/datetime_info.py`

**Voice Commands:**
- "What time is it"
- "What's the date"
- "What day is today"
- "What month is it"
- "What year is it"

**Examples:**
- User: "Computer, what time is it"
- Assistant: "It's 9:31 PM"
- User: "Computer, what's the date"
- Assistant: "Today is Monday, January 26th, 2026"

### 3. System Info (Priority: 7)
**Location:** `voice_assistant/features/system_info.py`

**Voice Commands:**
- "CPU usage"
- "Memory usage" / "RAM usage"
- "Disk space" / "Storage space"
- "Battery status" (laptops only)
- "System status" (overall summary)

**Examples:**
- User: "Computer, CPU usage"
- Assistant: "CPU usage is 5.2% across 16 cores"
- User: "Computer, how much memory am I using"
- Assistant: "Memory usage is 15%. Using 4.6 GB out of 30.8 GB"

## Technical Details

### Architecture
- Each feature has a dedicated service class
- Handlers use priority-based routing (fast path)
- High priority = checked first, avoiding LLM overhead
- All features work offline (no external APIs needed)

### Priority Levels
1. Weather (10) - highest
2. Spotify (9) - high (when enabled)
3. Calculator (8) - medium-high
4. DateTime (8) - medium-high
5. SystemInfo (7) - medium
6. LLM fallback - lowest (for general conversation)

### Dependencies Added
- `psutil` - for system information (CPU, memory, disk, battery)

### Files Modified
1. `voice_assistant/routing.py` - Added 3 new handler classes
2. `voice_assistant/model.py` - Initialized services and registered handlers
3. `pyproject.toml` - Added psutil dependency
4. `uv.lock` - Updated lockfile

### Files Created
1. `voice_assistant/features/calculator.py`
2. `voice_assistant/features/datetime_info.py`
3. `voice_assistant/features/system_info.py`

## Testing

### Manual Testing
```bash
cd ~/Projects/assistants
.venv/bin/python3 -c "
from voice_assistant.features.calculator import Calculator
calc = Calculator()
print(calc.calculate('what is 5 plus 3'))
"
```

### Integration Testing
Run the voice assistant and try the voice commands above!

## Future Feature Ideas
- **Timer/Alarm** - Set timers and reminders
- **Web Search** - Quick web searches via DuckDuckGo/Brave
- **File Operations** - Find files, open applications
- **Music Control** - Control local music players (not just Spotify)
- **Smart Home** - Control lights, thermostat, etc.
- **Email** - Read recent emails, send quick messages
- **Calendar** - Check schedule, upcoming events
- **News** - Get latest headlines
- **Jokes** - Tell jokes for fun! 😄

## Next Steps

1. **Test the features** - Start the assistant and try the voice commands
2. **Add more features** - Pick from the future ideas list
3. **Improve accuracy** - Fine-tune keyword detection for better matching
4. **Add tests** - Write unit tests for each feature

## Notes

- All features are **offline-first** - no internet required
- Fast response times via handler priority system
- Easy to extend - just create a new feature class and handler
- Weather and Spotify already working (Spotify pending auth fix)
