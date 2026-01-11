import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import logging
from typing import Optional, Dict, List
import re

logger = logging.getLogger(__name__)

class SpotifyService:
    """Service for interacting with Spotify API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: str = "http://localhost:8888/callback",
        cache_path: str = ".spotify_cache"
    ):
        """
        Initialize Spotify service.

        Args:
            client_id: Spotify application client ID (from env if not provided)
            client_secret: Spotify application client secret (from env if not provided)
            redirect_uri: OAuth redirect URI
            cache_path: Path to cache authentication tokens
        """
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = redirect_uri
        self.cache_path = cache_path

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
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                cache_path=self.cache_path,
                open_browser=True
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Successfully authenticated with Spotify")
        except Exception as e:
            logger.error(f"Failed to authenticate with Spotify: {e}")
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
