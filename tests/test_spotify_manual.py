#!/usr/bin/env python3
"""
Manual integration test for Spotify feature.

This script tests the actual Spotify integration with real API calls.
You MUST have Spotify credentials set up before running this.

Prerequisites:
1. Set up .env file with SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
2. Have Spotify app open on at least one device
3. Run: python tests/test_spotify_manual.py

This will test:
- Authentication
- Searching for songs
- Playing songs (if device is active)
- Playback controls (pause, resume, skip)
- Now playing status
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice_assistant.features.spotify import SpotifyService
from voice_assistant.routing import SpotifyHandler, HandlerRegistry


def print_test(name: str, status: str = "RUNNING"):
    """Print test status."""
    symbols = {
        "RUNNING": "⏳",
        "PASS": "✅",
        "FAIL": "❌",
        "SKIP": "⏭️"
    }
    print(f"{symbols.get(status, '❓')} {name}... ", end="", flush=True)
    if status != "RUNNING":
        print()


def main():
    """Run manual integration tests."""
    print("\n" + "="*60)
    print("Spotify Integration Manual Test Suite")
    print("="*60 + "\n")

    # Check for environment variables
    print("Checking environment setup...")
    if not os.getenv("SPOTIFY_CLIENT_ID") or not os.getenv("SPOTIFY_CLIENT_SECRET"):
        print("❌ FAIL: Environment variables not set!")
        print("\nPlease set up your .env file with:")
        print("  SPOTIFY_CLIENT_ID=your_client_id")
        print("  SPOTIFY_CLIENT_SECRET=your_client_secret")
        sys.exit(1)
    print("✅ Environment variables found\n")

    # Test 1: Service initialization
    print_test("Service initialization", "RUNNING")
    try:
        service = SpotifyService()
        print_test("Service initialization", "PASS")
    except Exception as e:
        print_test("Service initialization", "FAIL")
        print(f"   Error: {e}")
        sys.exit(1)

    # Test 2: Handler initialization
    print_test("Handler initialization", "RUNNING")
    try:
        handler = SpotifyHandler(service, priority=9)
        assert handler.name == "Spotify"
        assert handler.priority == 9
        print_test("Handler initialization", "PASS")
    except Exception as e:
        print_test("Handler initialization", "FAIL")
        print(f"   Error: {e}")
        sys.exit(1)

    # Test 3: Search for a track
    print_test("Search for track", "RUNNING")
    try:
        track = service.search_track("Bohemian Rhapsody Queen")
        if track:
            print_test("Search for track", "PASS")
            print(f"   Found: {track['name']} by {track['artist']}")
        else:
            print_test("Search for track", "FAIL")
            print("   No results found")
    except Exception as e:
        print_test("Search for track", "FAIL")
        print(f"   Error: {e}")

    # Test 4: Check for active devices
    print_test("Check for active devices", "RUNNING")
    try:
        devices = service.sp.devices()
        if devices['devices']:
            print_test("Check for active devices", "PASS")
            print(f"   Found {len(devices['devices'])} device(s):")
            for device in devices['devices']:
                print(f"     - {device['name']} ({device['type']})")
            has_device = True
        else:
            print_test("Check for active devices", "SKIP")
            print("   No active devices. Open Spotify app to test playback.")
            has_device = False
    except Exception as e:
        print_test("Check for active devices", "FAIL")
        print(f"   Error: {e}")
        has_device = False

    # Test 5: Handler keyword detection
    print_test("Handler keyword detection", "RUNNING")
    test_queries = [
        ("play bohemian rhapsody", True),
        ("pause the music", True),
        ("what's playing", True),
        ("next song", True),
        ("what's the weather", False),
    ]
    all_passed = True
    for query, should_match in test_queries:
        result = handler.can_handle(query)
        if result != should_match:
            all_passed = False
            print(f"\n   FAIL: '{query}' should_match={should_match}, got={result}")

    if all_passed:
        print_test("Handler keyword detection", "PASS")
    else:
        print_test("Handler keyword detection", "FAIL")

    # Test 6: Get current playback status
    print_test("Get current playback", "RUNNING")
    try:
        response = service.get_now_playing()
        print_test("Get current playback", "PASS")
        print(f"   {response}")
    except Exception as e:
        print_test("Get current playback", "FAIL")
        print(f"   Error: {e}")

    # Test 7: Test routing system integration
    print_test("Routing system integration", "RUNNING")
    try:
        registry = HandlerRegistry()
        registry.register(handler)

        # Test routing
        handler_name, response = registry.route("play bohemian rhapsody")

        if handler_name == "Spotify":
            print_test("Routing system integration", "PASS")
            print(f"   Handler: {handler_name}")
            print(f"   Response: {response}")
        else:
            print_test("Routing system integration", "FAIL")
            print(f"   Expected 'Spotify' handler, got: {handler_name}")
    except Exception as e:
        print_test("Routing system integration", "FAIL")
        print(f"   Error: {e}")

    # Interactive tests (only if device is available)
    if has_device:
        print("\n" + "="*60)
        print("Interactive Tests (with active device)")
        print("="*60 + "\n")
        print("⚠️  WARNING: This will control your Spotify playback!")

        response = input("\nDo you want to run interactive playback tests? (y/N): ")

        if response.lower() == 'y':
            # Test play
            print_test("Play a song", "RUNNING")
            try:
                response = service.play_track("test")
                print_test("Play a song", "PASS")
                print(f"   {response}")

                # Wait a bit
                import time
                time.sleep(3)

                # Test pause
                print_test("Pause playback", "RUNNING")
                response = service.pause_playback()
                print_test("Pause playback", "PASS")
                print(f"   {response}")

            except Exception as e:
                print_test("Interactive playback", "FAIL")
                print(f"   Error: {e}")
        else:
            print("⏭️  Skipped interactive tests")

    # Summary
    print("\n" + "="*60)
    print("Test Suite Complete!")
    print("="*60)
    print("\nIf all tests passed, your Spotify integration is working! 🎉")
    print("\nNext steps:")
    print("1. Test with the actual voice assistant")
    print("2. Try voice commands like:")
    print("   - 'Play Bohemian Rhapsody'")
    print("   - 'Pause music'")
    print("   - 'What's playing?'")
    print("3. Create a pull request when ready")
    print()


if __name__ == "__main__":
    # Load environment variables
    from pathlib import Path
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

    main()
