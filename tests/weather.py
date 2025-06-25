#!/usr/bin/env python3
"""
Weather feature test script.

This script tests the weather functionality using the Open-Meteo provider
which is free and doesn't require an API key.
"""

import sys
import os

# Add the src directory to the Python path so we can import the weather module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features.weather import WeatherForecast

def test_weather_queries():
    """Test function for weather queries."""
    try:
        # Test with Open-Meteo (no API key needed)
        print("Testing with Open-Meteo:")
        weather = WeatherForecast(provider="openmeteo")
        
        test_queries = [
            "What's the weather in Berlin now?",
            "Is it raining now?",
            "the weather in the evening?",
            "the weather in London?",
            "the weather tomorrow",
            "the rain and day" # just to check errors from transcription
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            response = weather.process_weather_query(query)
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_current_weather():
    """Test current weather functionality."""
    try:
        print("\n=== Testing Current Weather ===")
        weather = WeatherForecast(provider="openmeteo")
        
        # Test current weather for different locations
        locations = ["Berlin", "London", "New York", "Tokyo"]
        
        for location in locations:
            print(f"\nGetting current weather for {location}:")
            current_weather = weather.get_current_weather(location)
            
            if 'error' in current_weather:
                print(f"Error: {current_weather['error']}")
            else:
                print(f"Temperature: {current_weather.get('temperature', 'N/A')}°C")
                print(f"Description: {current_weather.get('description', 'N/A')}")
                print(f"Humidity: {current_weather.get('humidity', 'N/A')}%")
                print(f"Wind Speed: {current_weather.get('wind_speed', 'N/A')} m/s")
                
    except Exception as e:
        print(f"Error in current weather test: {e}")

def test_forecast():
    """Test forecast functionality."""
    try:
        print("\n=== Testing Weather Forecast ===")
        weather = WeatherForecast(provider="openmeteo")
        
        # Test forecast for different time periods
        location = "Berlin"
        hours_list = [6, 12, 24]
        
        for hours in hours_list:
            print(f"\nGetting {hours}-hour forecast for {location}:")
            forecast = weather.get_forecast(location, hours)
            
            if 'error' in forecast:
                print(f"Error: {forecast['error']}")
            else:
                print(f"Location: {forecast.get('location', 'N/A')}")
                print(f"Number of forecast entries: {len(forecast.get('forecast', []))}")
                
                # Show first few entries
                for i, entry in enumerate(forecast.get('forecast', [])[:3]):
                    print(f"  {i+1}. {entry.get('time', 'N/A')}: {entry.get('temperature', 'N/A')}°C, {entry.get('description', 'N/A')}")
                
    except Exception as e:
        print(f"Error in forecast test: {e}")

def test_weather_detection():
    """Test weather query detection."""
    try:
        print("\n=== Testing Weather Query Detection ===")
        weather = WeatherForecast(provider="openmeteo")
        
        test_texts = [
            "What's the weather like?",
            "How hot is it today?",
            "Is it going to rain tomorrow?",
            "What's the temperature in Paris?",
            "Hello, how are you?",  # Non-weather query
            "What time is it?",     # Non-weather query
            "The weather is nice today",
            "Temperature is 25 degrees",
            "It's raining outside",
        ]
        
        for text in test_texts:
            is_weather = weather._is_weather_query(text)
            print(f"'{text}' -> Weather query: {is_weather}")
            
    except Exception as e:
        print(f"Error in weather detection test: {e}")

if __name__ == "__main__":
    print("Weather Feature Test Suite")
    print("=" * 50)
    
    # Run all tests
    test_weather_queries()
    test_current_weather()
    test_forecast()
    test_weather_detection()
    
    print("\n" + "=" * 50)
    print("Test suite completed!") 