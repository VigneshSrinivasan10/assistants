"""
Hybrid routing system for voice assistant.

Features:
- Handler Registry Pattern for extensibility
- Fast keyword/pattern matching for common queries
- LLM fallback for complex queries
- Priority-based routing
"""
import re
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


class SpotifyHandler(Handler):
    """Handler for Spotify music playback queries."""

    def __init__(self, spotify_service, priority: int = 9):
        """
        Initialize Spotify handler.

        Args:
            spotify_service: SpotifyService instance
            priority: Priority level (default: 9 - high)
        """
        super().__init__(name="Spotify", priority=priority)
        self.spotify = spotify_service

    def can_handle(self, query: str) -> bool:
        """Check if query is Spotify-related using keyword matching."""
        query_lower = query.lower()

        # Playback control keywords
        playback_keywords = ['pause', 'stop', 'resume', 'skip', 'next', 'previous', 'back']
        music_keywords = ['song', 'music', 'track', 'artist', 'album', 'spotify']
        status_keywords = ['playing', "what's playing", 'now playing', 'current song']

        # "play" is special - it can work alone with a target (e.g., "play Beatles")
        # Match "play" followed by something (not just "play" alone)
        play_match = re.match(r'^play\s+.+', query_lower)

        # Check for other playback controls + music context
        has_playback_control = any(keyword in query_lower for keyword in playback_keywords)
        has_music_context = any(keyword in query_lower for keyword in music_keywords)
        has_status = any(keyword in query_lower for keyword in status_keywords)

        # Match if:
        # 1. "play [something]" - direct play command
        # 2. Other playback control + music context (e.g., "pause the music")
        # 3. Status query (e.g., "what's playing")
        # 4. Explicit "spotify" mention
        return (
            play_match is not None or
            (has_playback_control and has_music_context) or
            has_status or
            'spotify' in query_lower
        )

    def process(self, query: str) -> str:
        """Process Spotify query."""
        # Clean up query: lowercase and remove trailing punctuation
        query_lower = query.lower().strip()
        query_lower = re.sub(r'[.!?]+$', '', query_lower)

        # Pause/Stop
        if any(word in query_lower for word in ['pause', 'stop']):
            return self.spotify.pause_playback()

        # Resume
        if 'resume' in query_lower or (('play' in query_lower or 'start' in query_lower)
                                       and 'music' in query_lower
                                       and not any(word in query_lower for word in ['song', 'track', 'artist', 'album', 'play '])):
            return self.spotify.resume_playback()

        # Next track
        if 'next' in query_lower or 'skip' in query_lower:
            return self.spotify.next_track()

        # Previous track
        if 'previous' in query_lower or 'back' in query_lower or 'last' in query_lower:
            return self.spotify.previous_track()

        # Now playing / What's playing
        if any(phrase in query_lower for phrase in ['now playing', "what's playing", 'current song', 'playing now']):
            return self.spotify.get_now_playing()

        # Play specific content
        if 'play' in query_lower:
            # Try to extract artist intent (e.g., "play songs by Beatles", "play music by Taylor Swift")
            if 'by' in query_lower:
                artist_match = re.search(r'play\s+(?:songs?\s+by\s+|music\s+by\s+|.*\s+by\s+)([\w\s]+)', query_lower)
                if artist_match:
                    artist = artist_match.group(1).strip()
                    if artist:
                        return self.spotify.search_and_play_artist(artist)

            # Simple "play [something]" - extract everything after "play"
            play_match = re.search(r'play\s+(?:the\s+song\s+|the\s+track\s+|song\s+|track\s+)?(.*)', query_lower)
            if play_match:
                track_query = play_match.group(1).strip()
                if track_query:
                    return self.spotify.play_track(track_query)

        # Default fallback
        return "I'm not sure what you want to do with Spotify. Try saying 'play [song name]' or 'pause music'."

    def get_keywords(self) -> List[str]:
        """Return Spotify-related keywords."""
        return [
            'play', 'pause', 'stop', 'resume', 'skip', 'next', 'previous',
            'song', 'music', 'track', 'spotify', 'artist', 'album',
            'now playing', 'what\'s playing', 'current song'
        ]
