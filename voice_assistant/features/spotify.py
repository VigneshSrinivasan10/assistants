import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import logging
from typing import Optional, Dict, List
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get the project root directory (two levels up from this file)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_CACHE_PATH = str(_PROJECT_ROOT / ".spotify_cache")

class SpotifyService:
    """Service for interacting with Spotify API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        cache_path: Optional[str] = None
    ):
        """
        Initialize Spotify service.

        Args:
            client_id: Spotify application client ID (from env if not provided)
            client_secret: Spotify application client secret (from env if not provided)
            redirect_uri: OAuth redirect URI (from SPOTIFY_REDIRECT_URI env if not provided)
            cache_path: Path to cache authentication tokens (defaults to project root)
        """
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        self.cache_path = cache_path or _DEFAULT_CACHE_PATH

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Spotify credentials not found. Please set SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET environment variables or pass them to the constructor."
            )

        # Scopes needed for playback control
        self.scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"

        # Initialize Spotify client
        self.sp = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Spotify using OAuth."""
        try:
            # Check if we already have a cached token
            cache_exists = os.path.exists(self.cache_path)
            
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                cache_path=self.cache_path,
                open_browser=False  # Never auto-open, always manual
            )
            
            # If no cache, do manual auth flow
            if not cache_exists:
                auth_url = auth_manager.get_authorize_url()
                print("\n" + "="*70)
                print("🎵 SPOTIFY AUTHENTICATION REQUIRED")
                print("="*70)
                print(f"\n1. Open this URL in ANY browser (phone/PC/tablet):\n")
                print(f"   {auth_url}\n")
                print("2. Log in to Spotify and click 'Agree'")
                print("3. After clicking 'Agree', you'll see an error page OR blank page")
                print("   ⚠️  This is NORMAL! The page doesn't matter.")
                print("\n4. Look at the URL in your browser's address bar")
                print("   It will look like: http://...?code=AQXXXXXXXXXXXXX")
                print("\n5. Copy JUST THE CODE (the long string after 'code=')")
                print("   Example: If URL is http://localhost:8888/callback?code=AQB123xyz")
                print("            Copy only: AQB123xyz")
                print("\n" + "="*70)
                
                auth_code = input("\n📋 Paste the code here: ").strip()
                
                # Clean up the code if user pasted full URL by mistake
                if 'code=' in auth_code:
                    auth_code = auth_code.split('code=')[1].split('&')[0]
                
                # Get access token using the code
                token_info = auth_manager.get_access_token(auth_code, as_dict=True, check_cache=False)
                
                if not token_info:
                    raise Exception("Failed to get access token")
                
                print("\n✅ Successfully authenticated with Spotify!\n")
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Successfully authenticated with Spotify")
        except Exception as e:
            logger.error(f"Failed to authenticate with Spotify: {e}")
            print(f"\n❌ Authentication failed: {e}")
            print("Try again or check your credentials in .env file")
            raise

    def search_track(self, query: str, limit: int = 1) -> Optional[Dict]:
        """
        Search for a track on Spotify.

        Args:
            query: Search query (song name, artist, etc.)
            limit: Number of results to return

        Returns:
            Dictionary with track information or None if not found
        """
        try:
            results = self.sp.search(q=query, type='track', limit=limit)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return {
                    'uri': track['uri'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'id': track['id']
                }
            return None
        except Exception as e:
            logger.error(f"Error searching for track '{query}': {e}")
            return None

    def play_track(self, query: str) -> str:
        """
        Search for and play a track.

        Args:
            query: Search query for the track

        Returns:
            Response message
        """
        try:
            # Get available devices
            devices = self.sp.devices()
            if not devices['devices']:
                return "No active Spotify devices found. Please open Spotify on your device first."

            # Search for the track
            track = self.search_track(query)
            if not track:
                return f"Sorry, I couldn't find '{query}' on Spotify."

            # Play the track
            self.sp.start_playback(uris=[track['uri']])
            return f"Now playing {track['name']} by {track['artist']}"

        except Exception as e:
            logger.error(f"Error playing track: {e}")
            if "NO_ACTIVE_DEVICE" in str(e):
                return "No active Spotify device found. Please open Spotify on your device first."
            return f"Sorry, I couldn't play that song. Error: {str(e)}"

    def pause_playback(self) -> str:
        """Pause current playback."""
        try:
            self.sp.pause_playback()
            return "Paused playback"
        except Exception as e:
            logger.error(f"Error pausing playback: {e}")
            return "Sorry, I couldn't pause the playback."

    def resume_playback(self) -> str:
        """Resume current playback."""
        try:
            self.sp.start_playback()
            return "Resumed playback"
        except Exception as e:
            logger.error(f"Error resuming playback: {e}")
            return "Sorry, I couldn't resume the playback."

    def next_track(self) -> str:
        """Skip to next track."""
        try:
            self.sp.next_track()
            return "Skipped to next track"
        except Exception as e:
            logger.error(f"Error skipping track: {e}")
            return "Sorry, I couldn't skip to the next track."

    def previous_track(self) -> str:
        """Go to previous track."""
        try:
            self.sp.previous_track()
            return "Playing previous track"
        except Exception as e:
            logger.error(f"Error going to previous track: {e}")
            return "Sorry, I couldn't go to the previous track."

    def get_current_playback(self) -> Optional[Dict]:
        """Get information about current playback."""
        try:
            playback = self.sp.current_playback()
            if playback and playback.get('item'):
                return {
                    'name': playback['item']['name'],
                    'artist': playback['item']['artists'][0]['name'],
                    'is_playing': playback['is_playing']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting current playback: {e}")
            return None

    def get_now_playing(self) -> str:
        """Get currently playing track."""
        try:
            playback = self.get_current_playback()
            if playback:
                status = "playing" if playback['is_playing'] else "paused"
                return f"Currently {status}: {playback['name']} by {playback['artist']}"
            return "Nothing is currently playing on Spotify."
        except Exception as e:
            logger.error(f"Error getting now playing: {e}")
            return "Sorry, I couldn't get the current playback information."

    def set_volume(self, volume_percent: int) -> str:
        """
        Set playback volume.

        Args:
            volume_percent: Volume level (0-100)

        Returns:
            Response message
        """
        try:
            volume_percent = max(0, min(100, volume_percent))  # Clamp to 0-100
            self.sp.volume(volume_percent)
            return f"Set volume to {volume_percent}%"
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return "Sorry, I couldn't change the volume."

    def search_and_play_artist(self, artist_name: str) -> str:
        """Search for and play top tracks from an artist."""
        try:
            # Search for artist
            results = self.sp.search(q=f"artist:{artist_name}", type='artist', limit=1)
            if not results['artists']['items']:
                return f"Sorry, I couldn't find artist '{artist_name}' on Spotify."

            artist = results['artists']['items'][0]
            artist_uri = artist['uri']

            # Get artist's top tracks
            top_tracks = self.sp.artist_top_tracks(artist['id'])
            if not top_tracks['tracks']:
                return f"Sorry, couldn't find tracks for {artist['name']}."

            # Play top tracks
            track_uris = [track['uri'] for track in top_tracks['tracks'][:10]]
            self.sp.start_playback(uris=track_uris)

            return f"Now playing top songs by {artist['name']}"

        except Exception as e:
            logger.error(f"Error playing artist: {e}")
            return f"Sorry, I couldn't play songs by that artist. Error: {str(e)}"
