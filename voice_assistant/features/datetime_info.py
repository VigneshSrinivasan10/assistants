"""
Date and time feature for voice assistant.
Tells current time, date, day of week, etc.
"""
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DateTimeInfo:
    """Provides date and time information."""

    def __init__(self):
        """Initialize datetime info provider."""
        pass

    def _is_time_query(self, query: str) -> bool:
        """
        Check if query is asking about time or date.
        
        Args:
            query: User's query
            
        Returns:
            True if query is about time/date
        """
        query_lower = query.lower()
        
        time_keywords = [
            'time', 'clock', 'hour', 'minute',
            'date', 'day', 'today', 'month', 'year',
            'what day', 'what\'s the date'
        ]
        
        return any(keyword in query_lower for keyword in time_keywords)

    def get_time_info(self, query: str) -> str:
        """
        Process time/date query and return info.
        
        Args:
            query: User's query
            
        Returns:
            Time/date information as string
        """
        if not self._is_time_query(query):
            return None
        
        now = datetime.now()
        query_lower = query.lower()
        
        # Check what specifically is being asked
        if 'time' in query_lower:
            # Format: "3:45 PM"
            time_str = now.strftime("%I:%M %p").lstrip('0')
            return f"It's {time_str}"
        
        elif 'date' in query_lower or 'today' in query_lower:
            # Format: "Monday, January 26th, 2026"
            day_suffix = self._get_day_suffix(now.day)
            date_str = now.strftime(f"%A, %B {now.day}{day_suffix}, %Y")
            return f"Today is {date_str}"
        
        elif 'day' in query_lower:
            # Just the day of week
            day_str = now.strftime("%A")
            return f"It's {day_str}"
        
        elif 'month' in query_lower:
            month_str = now.strftime("%B")
            return f"It's {month_str}"
        
        elif 'year' in query_lower:
            year_str = now.strftime("%Y")
            return f"It's {year_str}"
        
        else:
            # Default: give both time and date
            time_str = now.strftime("%I:%M %p").lstrip('0')
            day_suffix = self._get_day_suffix(now.day)
            date_str = now.strftime(f"%A, %B {now.day}{day_suffix}")
            return f"It's {time_str} on {date_str}"

    def _get_day_suffix(self, day: int) -> str:
        """
        Get suffix for day (st, nd, rd, th).
        
        Args:
            day: Day of month (1-31)
            
        Returns:
            Suffix string
        """
        if 11 <= day <= 13:
            return 'th'
        
        suffix_map = {1: 'st', 2: 'nd', 3: 'rd'}
        return suffix_map.get(day % 10, 'th')
