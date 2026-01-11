"""
Hybrid routing system for voice assistant.

Features:
- Handler Registry Pattern for extensibility
- Fast keyword/pattern matching for common queries
- LLM fallback for complex queries
- Priority-based routing
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Handler(ABC):
    """Base class for all query handlers."""

    def __init__(self, name: str, priority: int = 5):
        """
        Initialize handler.

        Args:
            name: Name of the handler (e.g., "Weather", "Calculator")
            priority: Higher priority handlers are checked first (0-10 scale)
        """
        self.name = name
        self.priority = priority

    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """
        Fast check if this handler can process the query.
        Should use lightweight checks (keywords, regex, etc.)

        Args:
            query: User's transcribed query

        Returns:
            True if this handler should process the query
        """
        pass

    @abstractmethod
    def process(self, query: str) -> str:
        """
        Process the query and return response.

        Args:
            query: User's transcribed query

        Returns:
            Response text
        """
        pass

    def get_keywords(self) -> List[str]:
        """
        Return keywords for fast matching (optional).
        Can be used for optimization/indexing.

        Returns:
            List of keywords this handler responds to
        """
        return []

    def __repr__(self):
        return f"<{self.name}Handler priority={self.priority}>"


class HandlerRegistry:
    """Registry for managing and routing to handlers."""

    def __init__(self):
        self.handlers: List[Handler] = []
        self._keyword_index = {}  # Optional: for O(1) keyword lookup

    def register(self, handler: Handler):
        """
        Register a handler.

        Args:
            handler: Handler instance to register
        """
        self.handlers.append(handler)
        # Sort by priority (highest first)
        self.handlers.sort(key=lambda h: h.priority, reverse=True)

        # Build keyword index for optimization
        for keyword in handler.get_keywords():
            if keyword not in self._keyword_index:
                self._keyword_index[keyword] = []
            self._keyword_index[keyword].append(handler)

        logger.info(f"Registered handler: {handler}")

    def unregister(self, handler_name: str):
        """
        Unregister a handler by name.

        Args:
            handler_name: Name of handler to remove
        """
        self.handlers = [h for h in self.handlers if h.name != handler_name]
        # Rebuild keyword index
        self._rebuild_keyword_index()
        logger.info(f"Unregistered handler: {handler_name}")

    def _rebuild_keyword_index(self):
        """Rebuild the keyword index after handler changes."""
        self._keyword_index = {}
        for handler in self.handlers:
            for keyword in handler.get_keywords():
                if keyword not in self._keyword_index:
                    self._keyword_index[keyword] = []
                self._keyword_index[keyword].append(handler)

    def route(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Route query to appropriate handler using fast path.

        Args:
            query: User's transcribed query

        Returns:
            Tuple of (handler_name, response_text)
            Returns (None, None) if no handler can process the query
        """
        # Fast path: check each handler in priority order
        for handler in self.handlers:
            try:
                if handler.can_handle(query):
                    logger.info(f"Routing to {handler.name} (priority={handler.priority})")
                    response = handler.process(query)
                    return (handler.name, response)
            except Exception as e:
                logger.error(f"Error in {handler.name} handler: {e}", exc_info=True)
                continue  # Try next handler

        # No handler found
        logger.info("No specialized handler found, will fallback to LLM")
        return (None, None)

    def get_handlers_info(self) -> List[dict]:
        """
        Get information about registered handlers.

        Returns:
            List of handler info dictionaries
        """
        return [
            {
                "name": h.name,
                "priority": h.priority,
                "keywords": h.get_keywords()
            }
            for h in self.handlers
        ]

    def __len__(self):
        return len(self.handlers)

    def __repr__(self):
        return f"<HandlerRegistry handlers={len(self.handlers)}>"


class WeatherHandler(Handler):
    """Handler for weather-related queries."""

    def __init__(self, weather_service, priority: int = 10):
        """
        Initialize weather handler.

        Args:
            weather_service: WeatherForecast instance
            priority: Priority level (default: 10 - highest)
        """
        super().__init__(name="Weather", priority=priority)
        self.weather = weather_service

    def can_handle(self, query: str) -> bool:
        """Check if query is weather-related using fast keyword matching."""
        return self.weather._is_weather_query(query)

    def process(self, query: str) -> str:
        """Process weather query."""
        return self.weather.process_weather_query(query)

    def get_keywords(self) -> List[str]:
        """Return weather-related keywords."""
        return [
            'weather', 'temperature', 'forecast', 'rain', 'snow',
            'sunny', 'cloudy', 'hot', 'cold', 'humid', 'wind'
        ]


# Example handlers for future implementation
class CalculatorHandler(Handler):
    """Handler for math calculations (placeholder for future)."""

    def __init__(self, priority: int = 8):
        super().__init__(name="Calculator", priority=priority)

    def can_handle(self, query: str) -> bool:
        # TODO: Implement math detection
        return False

    def process(self, query: str) -> str:
        # TODO: Implement calculation
        return "Calculator not yet implemented"

    def get_keywords(self) -> List[str]:
        return ['calculate', 'multiply', 'divide', 'add', 'subtract', 'math']


class ReminderHandler(Handler):
    """Handler for reminders (placeholder for future)."""

    def __init__(self, priority: int = 9):
        super().__init__(name="Reminder", priority=priority)

    def can_handle(self, query: str) -> bool:
        # TODO: Implement reminder detection
        return False

    def process(self, query: str) -> str:
        # TODO: Implement reminder creation
        return "Reminder not yet implemented"

    def get_keywords(self) -> List[str]:
        return ['remind', 'reminder', 'schedule', 'set alarm', 'alarm']
