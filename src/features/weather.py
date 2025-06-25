import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class WeatherProvider(ABC):
    """Abstract base class for weather providers."""
    
    @abstractmethod
    def get_current_weather(self, location: str) -> Dict:
        pass
    
    @abstractmethod
    def get_forecast(self, location: str, hours: int = 24) -> Dict:
        pass

class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo weather provider (completely free, no API key required)."""
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1"
    
    def _get_coordinates(self, location: str) -> Tuple[float, float]:
        """Get coordinates for a location using Open-Meteo geocoding."""
        try:
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                'name': location,
                'count': 1,
                'language': 'en',
                'format': 'json'
            }
            
            response = requests.get(geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('results'):
                result = data['results'][0]
                return result['latitude'], result['longitude']
            else:
                raise ValueError(f"Location '{location}' not found")
                
        except Exception as e:
            logger.error(f"Error getting coordinates for {location}: {e}")
            raise ValueError(f"Could not find location: {location}")
    
    def get_current_weather(self, location: str) -> Dict:
        """Get current weather for a location."""
        try:
            lat, lon = self._get_coordinates(location)
            
            url = f"{self.base_url}/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,pressure_msl,visibility',
                'timezone': 'auto',
                'forecast_days': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            current = data['current']
            
            # Convert weather code to description
            weather_description = self._weather_code_to_description(current['weather_code'])
            
            return {
                'location': location,
                'temperature': round(current['temperature_2m']),
                'feels_like': round(current['apparent_temperature']),
                'humidity': current['relative_humidity_2m'],
                'description': weather_description,
                'wind_speed': current['wind_speed_10m'],
                'pressure': current['pressure_msl'],
                'visibility': current['visibility'] / 1000,  # Convert to km
                'precipitation': current['precipitation'],
                'timestamp': current['time']
            }
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return {'error': f"Failed to fetch weather data: {str(e)}"}
    
    def get_forecast(self, location: str, hours: int = 24) -> Dict:
        """Get weather forecast for a location."""
        try:
            lat, lon = self._get_coordinates(location)
            
            url = f"{self.base_url}/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'hourly': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m',
                'timezone': 'auto',
                'forecast_days': min(7, max(1, hours // 24 + 1))
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            forecast_data = []
            current_time = datetime.now()
            
            for i, time_str in enumerate(data['hourly']['time']):
                forecast_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                
                # Only include future forecasts within the requested hours
                if (forecast_time - current_time).total_seconds() <= hours * 3600:
                    forecast_data.append({
                        'time': forecast_time.strftime('%Y-%m-%d %H:%M'),
                        'temperature': round(data['hourly']['temperature_2m'][i]),
                        'feels_like': round(data['hourly']['apparent_temperature'][i]),
                        'humidity': data['hourly']['relative_humidity_2m'][i],
                        'description': self._weather_code_to_description(data['hourly']['weather_code'][i]),
                        'wind_speed': data['hourly']['wind_speed_10m'][i],
                        'precipitation': data['hourly']['precipitation'][i]
                    })
            
            return {
                'location': location,
                'forecast': forecast_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return {'error': f"Failed to fetch forecast data: {str(e)}"}
    
    def _weather_code_to_description(self, code: int) -> str:
        """Convert WMO weather codes to descriptions."""
        weather_codes = {
            0: "clear sky",
            1: "mainly clear",
            2: "partly cloudy",
            3: "overcast",
            45: "foggy",
            48: "depositing rime fog",
            51: "light drizzle",
            53: "moderate drizzle",
            55: "dense drizzle",
            56: "light freezing drizzle",
            57: "dense freezing drizzle",
            61: "slight rain",
            63: "moderate rain",
            65: "heavy rain",
            66: "light freezing rain",
            67: "heavy freezing rain",
            71: "slight snow fall",
            73: "moderate snow fall",
            75: "heavy snow fall",
            77: "snow grains",
            80: "slight rain showers",
            81: "moderate rain showers",
            82: "violent rain showers",
            85: "slight snow showers",
            86: "heavy snow showers",
            95: "thunderstorm",
            96: "thunderstorm with slight hail",
            99: "thunderstorm with heavy hail"
        }
        return weather_codes.get(code, "unknown")

class WeatherAPIProvider(WeatherProvider):
    """WeatherAPI.com provider (1M free calls/month)."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._get_api_key()
        self.base_url = "http://api.weatherapi.com/v1"
    
    def _get_api_key(self) -> str:
        """Get API key from environment variable."""
        import os
        api_key = os.getenv('WEATHERAPI_KEY')
        if not api_key:
            raise ValueError(
                "WeatherAPI key not found. Please set WEATHERAPI_KEY "
                "environment variable or pass api_key parameter."
            )
        return api_key
    
    def get_current_weather(self, location: str) -> Dict:
        """Get current weather for a location."""
        try:
            url = f"{self.base_url}/current.json"
            params = {
                'key': self.api_key,
                'q': location,
                'aqi': 'no'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            current = data['current']
            location_data = data['location']
            
            return {
                'location': location_data['name'],
                'country': location_data['country'],
                'temperature': round(current['temp_c']),
                'feels_like': round(current['feelslike_c']),
                'humidity': current['humidity'],
                'description': current['condition']['text'],
                'wind_speed': current['wind_kph'] / 3.6,  # Convert to m/s
                'pressure': current['pressure_mb'],
                'visibility': current['vis_km'],
                'timestamp': current['last_updated']
            }
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return {'error': f"Failed to fetch weather data: {str(e)}"}
    
    def get_forecast(self, location: str, hours: int = 24) -> Dict:
        """Get weather forecast for a location."""
        try:
            url = f"{self.base_url}/forecast.json"
            params = {
                'key': self.api_key,
                'q': location,
                'days': min(3, max(1, hours // 24 + 1)),
                'aqi': 'no',
                'alerts': 'no'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            forecast_data = []
            current_time = datetime.now()
            
            for day in data['forecast']['forecastday']:
                for hour in day['hour']:
                    forecast_time = datetime.fromisoformat(hour['time'])
                    
                    # Only include future forecasts within the requested hours
                    if (forecast_time - current_time).total_seconds() <= hours * 3600:
                        forecast_data.append({
                            'time': forecast_time.strftime('%Y-%m-%d %H:%M'),
                            'temperature': round(hour['temp_c']),
                            'feels_like': round(hour['feelslike_c']),
                            'humidity': hour['humidity'],
                            'description': hour['condition']['text'],
                            'wind_speed': hour['wind_kph'] / 3.6,  # Convert to m/s
                            'precipitation': hour['precip_mm']
                        })
            
            return {
                'location': data['location']['name'],
                'country': data['location']['country'],
                'forecast': forecast_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return {'error': f"Failed to fetch forecast data: {str(e)}"}

class WeatherForecast:
    def __init__(self, provider: str = "openmeteo", api_key: str = None):
        """
        Initialize the weather forecast service.
        
        Args:
            provider: Weather provider ('openmeteo', 'weatherapi', 'openweathermap')
            api_key: API key (only needed for some providers)
        """
        self.provider_name = provider.lower()
        
        if self.provider_name == "openmeteo":
            self.provider = OpenMeteoProvider()
        elif self.provider_name == "weatherapi":
            self.provider = WeatherAPIProvider(api_key)
        elif self.provider_name == "openweathermap":
            # Keep the original OpenWeatherMap implementation
            self.provider = OpenWeatherMapProvider(api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}. Supported: openmeteo, weatherapi, openweathermap")
    
    def _is_weather_query(self, text: str) -> bool:
        """
        Check if the transcription is a weather-related query.
        
        Args:
            text: The transcribed text
            
        Returns:
            True if it's a weather query, False otherwise
        """
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Weather-related keywords and patterns
        weather_keywords = [
            'weather', 'temperature', 'forecast', 'rain', 'snow', 'sunny', 
            'cloudy', 'hot', 'cold', 'humid', 'wind', 'storm', 'thunder',
            'drizzle', 'fog', 'mist', 'hail', 'sleet', 'precipitation',
            'degrees', 'celsius', 'fahrenheit', '°c', '°f'
        ]
        
        # Weather question patterns
        weather_patterns = [
            r'\b(what\'?s?|how\'?s?)\s+(the\s+)?weather',
            r'\b(is\s+it\s+)(raining|snowing|sunny|cloudy|hot|cold)',
            r'\b(weather\s+)(in|for|at)',
            r'\b(temperature\s+)(in|for|at)',
            r'\b(forecast\s+)(for|in)',
        ]
        
        # Check for weather keywords
        for keyword in weather_keywords:
            if keyword in text_lower:
                return True
        
        # Check for weather patterns
        for pattern in weather_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _parse_time_reference(self, text: str) -> Tuple[str, Optional[str]]:
        """
        Parse time references from natural language text.
        
        Args:
            text: Natural language text containing time references
            
        Returns:
            Tuple of (time_reference, time_period)
        """
        text_lower = text.lower()
        
        # Time periods
        time_periods = {
            'now': 'current',
            'today': 'current',
            'tonight': 'current',
            'this evening': 'current',
            'this afternoon': 'current',
            'this morning': 'current',
            'evening': 'evening',
            'afternoon': 'afternoon',
            'morning': 'morning',
            'night': 'night',
            'tonight': 'night',
            'tomorrow': 'tomorrow',
            'tomorrow morning': 'tomorrow_morning',
            'tomorrow afternoon': 'tomorrow_afternoon',
            'tomorrow evening': 'tomorrow_evening',
            'tomorrow night': 'tomorrow_night',
            'next hour': 'next_hour',
            'in an hour': 'next_hour',
            'in 1 hour': 'next_hour',
            'in 2 hours': 'next_2_hours',
            'in 3 hours': 'next_3_hours',
            'in 4 hours': 'next_4_hours',
            'in 5 hours': 'next_5_hours',
        }
        
        # Find time reference
        time_reference = 'current'  # default
        time_period = None
        
        for period, reference in time_periods.items():
            if period in text_lower:
                time_reference = reference
                time_period = period
                break
                
        return time_reference, time_period
    
    def _extract_location(self, text: str) -> str:
        """
        Extract location from natural language text.
        
        Args:
            text: Natural language text containing location
            
        Returns:
            Extracted location string
        """
        # Common patterns for location extraction
        patterns = [
            r'in\s+([A-Za-z\s,]+?)(?:\s+now|\s+tonight|\s+this\s+evening|\s+tomorrow|\s+in\s+\d+\s+hours?|[?!.,]|$)',
            r'weather\s+in\s+([A-Za-z\s,]+?)(?:\s+now|\s+tonight|\s+this\s+evening|\s+tomorrow|\s+in\s+\d+\s+hours?|[?!.,]|$)',
            r'([A-Za-z\s,]+?)\s+weather(?:\s+now|\s+tonight|\s+this\s+evening|\s+tomorrow|\s+in\s+\d+\s+hours?|[?!.,]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up common words that might be captured
                # Also filter out time-related words that should not be treated as locations
                location = re.sub(r'\b(what\'?s?|the|is|it|raining|snowing|sunny|cloudy|weather|evening|morning|afternoon|night|tonight|tomorrow|now|today)\b', '', location, flags=re.IGNORECASE)
                location = location.strip(' ,.')
                if location:
                    return location
        
        # If no pattern matches, try to extract any capitalized words (likely city names)
        words = text.split()
        potential_locations = []
        for word in words:
            if word[0].isupper() and len(word) > 2:
                potential_locations.append(word)
        
        if potential_locations:
            return ' '.join(potential_locations)
        
        # Default to Berlin if no location is found
        return "Berlin"
    
    def get_current_weather(self, location: str) -> Dict:
        """Get current weather for a location."""
        return self.provider.get_current_weather(location)
    
    def get_forecast(self, location: str, hours: int = 24) -> Dict:
        """Get weather forecast for a location."""
        return self.provider.get_forecast(location, hours)
    
    def get_weather_for_time(self, location: str, time_reference: str) -> Dict:
        """
        Get weather for a specific time reference.
        
        Args:
            location: City name or coordinates
            time_reference: Time reference (current, evening, tomorrow, etc.)
            
        Returns:
            Dictionary containing weather information
        """
        if time_reference in ['current', 'now', 'today']:
            return self.get_current_weather(location)
        
        # For future times, get forecast and find the closest match
        forecast_data = self.get_forecast(location, hours=48)
        
        if 'error' in forecast_data:
            return forecast_data
        
        current_time = datetime.now()
        target_time = None
        
        if time_reference == 'evening':
            # Evening is typically 6 PM to 9 PM
            target_time = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
        elif time_reference == 'afternoon':
            # Afternoon is typically 2 PM to 5 PM
            target_time = current_time.replace(hour=14, minute=0, second=0, microsecond=0)
        elif time_reference == 'morning':
            # Morning is typically 8 AM to 11 AM
            target_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        elif time_reference == 'night':
            # Night is typically 10 PM to 6 AM
            target_time = current_time.replace(hour=22, minute=0, second=0, microsecond=0)
        elif time_reference == 'tomorrow':
            # Tomorrow at current time
            target_time = current_time + timedelta(days=1)
        elif time_reference.startswith('tomorrow_'):
            # Tomorrow at specific time
            tomorrow = current_time + timedelta(days=1)
            if 'morning' in time_reference:
                target_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
            elif 'afternoon' in time_reference:
                target_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
            elif 'evening' in time_reference:
                target_time = tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
            elif 'night' in time_reference:
                target_time = tomorrow.replace(hour=22, minute=0, second=0, microsecond=0)
        elif time_reference.startswith('next_'):
            # Next few hours
            hours_ahead = int(time_reference.split('_')[-1]) if time_reference.split('_')[-1].isdigit() else 1
            target_time = current_time + timedelta(hours=hours_ahead)
        
        if target_time:
            # Find the closest forecast entry to target time
            closest_forecast = None
            min_diff = float('inf')
            
            for forecast in forecast_data['forecast']:
                forecast_time = datetime.strptime(forecast['time'], '%Y-%m-%d %H:%M')
                diff = abs((forecast_time - target_time).total_seconds())
                
                if diff < min_diff:
                    min_diff = diff
                    closest_forecast = forecast
            
            if closest_forecast:
                return {
                    'location': forecast_data['location'],
                    'country': forecast_data.get('country', ''),
                    'target_time': target_time.strftime('%Y-%m-%d %H:%M'),
                    **closest_forecast
                }
        
        # Fallback to current weather
        return self.get_current_weather(location)
    
    def format_weather_response(self, weather_data: Dict, time_period: str = None) -> str:
        """
        Format weather data into a natural language response.
        
        Args:
            weather_data: Weather data dictionary
            time_period: Time period reference
            
        Returns:
            Formatted weather response string
        """
        if 'error' in weather_data:
            return f"Sorry, I couldn't get the weather information: {weather_data['error']}"
        
        location = weather_data.get('location', 'Unknown location')
        temp = weather_data.get('temperature', 'N/A')
        description = weather_data.get('description', 'unknown conditions')
        humidity = weather_data.get('humidity', 'N/A')
        wind_speed = weather_data.get('wind_speed', 'N/A')
        
        time_info = ""
        if time_period:
            time_info = f" for {time_period}"
        
        response = f"The weather in {location}{time_info} is {temp}°C with {description}. "
        # TODO: Add humidity and wind speed to the response if needed
        # response += f"Humidity is {humidity}% and wind speed is {int(wind_speed)} ."
        
        return response
    
    def process_weather_query(self, query: str) -> str:
        """
        Process a natural language weather query.
        
        Args:
            query: Natural language weather query
            
        Returns:
            Formatted weather response
        """
        # Extract location and time reference
        location = self._extract_location(query)
        time_reference, time_period = self._parse_time_reference(query)
        
        logger.info(f"Processing weather query: location={location}, time={time_reference}")
        
        # Get weather data
        weather_data = self.get_weather_for_time(location, time_reference)
        
        # Format response
        return self.format_weather_response(weather_data, time_period)

# Example usage and testing
def test_weather_queries():
    """Test function for weather queries."""
    try:
        # Test with Open-Meteo (no API key needed)
        print("Testing with Open-Meteo (free, no API key required):")
        weather = WeatherForecast(provider="openmeteo")
        
        test_queries = [
            "What's the weather in Berlin now?",
            "Is it raining now?",
            "the weather in the evening?",
            "the weather in London?",
            "the weather tomorrow"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            response = weather.process_weather_query(query)
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_weather_queries()
