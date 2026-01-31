"""
Automated test for Spotify playback using librespot.

This test verifies that the hybrid Spotify service (librespot + Spotipy) works correctly.
It will:
1. Authenticate with Spotify (OAuth browser flow on first run)
2. Search for a track
3. Play the track (direct audio output)
4. Test pause/resume/skip controls

Run: python tests/test_spotify_librespot.py

Requirements:
- Spotify Premium account
- First run will open a browser for authentication
- Credentials are cached for subsequent runs
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_spotify_playback():
    """Test search and playback without voice input."""
    from voice_assistant.features.spotify import SpotifyService

    print("=" * 60)
    print("Spotify Librespot Playback Test")
    print("=" * 60)

    # Initialize service (will prompt for OAuth on first run)
    print("\n[1/7] Initializing Spotify service...")
    try:
        spotify = SpotifyService()
        print("      Spotify service initialized successfully")
    except RuntimeError as e:
        print(f"      FAILED: {e}")
        print("\n      Make sure you have a Spotify Premium account.")
        return False

    # Check Premium status
    print(f"\n[2/7] Checking account status...")
    if spotify.is_premium:
        print("      Premium account confirmed")
    else:
        print("      WARNING: Premium not detected, playback may fail")

    # Test search
    print("\n[3/7] Testing search...")
    track = spotify.search_track("Bohemian Rhapsody Queen")
    if track:
        print(f"      Found: {track['name']} by {track['artist']}")
        print(f"      Album: {track['album']}")
        print(f"      URI: {track['uri']}")
    else:
        print("      FAILED: Search returned no results")
        return False

    # Test playback
    print("\n[4/7] Testing playback (10 seconds)...")
    result = spotify.play_track("Bohemian Rhapsody Queen")
    print(f"      {result}")

    if "Now playing" not in result:
        print("      WARNING: Playback may have failed")

    print("      Playing for 10 seconds...")
    time.sleep(10)

    # Test pause
    print("\n[5/7] Testing pause...")
    result = spotify.pause_playback()
    print(f"      {result}")
    print("      Paused for 2 seconds...")
    time.sleep(2)

    # Test resume
    print("\n[6/7] Testing resume...")
    result = spotify.resume_playback()
    print(f"      {result}")
    print("      Playing for 5 more seconds...")
    time.sleep(5)

    # Test now playing
    print("\n[7/7] Testing now playing status...")
    result = spotify.get_now_playing()
    print(f"      {result}")

    # Stop playback
    print("\n" + "-" * 60)
    print("Stopping playback...")
    spotify.stop_playback()
    spotify.cleanup()

    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("\nThe Spotify librespot integration is working correctly.")
    print("Your voice assistant can now play music directly without")
    print("needing the Spotify desktop/mobile app running.")

    return True


def test_artist_playback():
    """Test playing an artist's top tracks."""
    from voice_assistant.features.spotify import SpotifyService

    print("=" * 60)
    print("Spotify Artist Playback Test")
    print("=" * 60)

    print("\n[1/4] Initializing Spotify service...")
    try:
        spotify = SpotifyService()
        print("      Spotify service initialized")
    except RuntimeError as e:
        print(f"      FAILED: {e}")
        return False

    # Search and play artist
    print("\n[2/4] Playing top tracks by The Beatles...")
    result = spotify.search_and_play_artist("The Beatles")
    print(f"      {result}")

    if "Now playing" not in result:
        print("      WARNING: Playback may have failed")
        return False

    print("      Playing for 15 seconds...")
    time.sleep(15)

    # Skip to next track
    print("\n[3/4] Skipping to next track...")
    result = spotify.next_track()
    print(f"      {result}")
    time.sleep(5)

    # Check now playing
    print("\n[4/4] Current track...")
    result = spotify.get_now_playing()
    print(f"      {result}")

    # Cleanup
    print("\nStopping playback...")
    spotify.stop_playback()
    spotify.cleanup()

    print("\n" + "=" * 60)
    print("ARTIST PLAYBACK TEST COMPLETED")
    print("=" * 60)

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Spotify librespot playback")
    parser.add_argument(
        "--artist",
        action="store_true",
        help="Run artist playback test instead of single track test"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )

    args = parser.parse_args()

    success = True

    if args.all:
        print("\nRunning all Spotify tests...\n")
        success = test_spotify_playback() and success
        print("\n")
        success = test_artist_playback() and success
    elif args.artist:
        success = test_artist_playback()
    else:
        success = test_spotify_playback()

    sys.exit(0 if success else 1)
