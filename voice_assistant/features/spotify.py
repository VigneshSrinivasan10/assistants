"""
Hybrid Spotify service using librespot for playback and Spotipy for search.

This module provides:
- Direct audio playback via librespot (no external Spotify app needed)
- Search functionality via Spotipy (using librespot's OAuth token)
- Requires Spotify Premium account for playback
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import logging
from typing import Optional, Dict, List
import re
from pathlib import Path
from dotenv import load_dotenv

from voice_assistant.features.librespot_player import LibrespotPlayer

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get the project root directory (two levels up from this file)
_PROJECT_ROOT = Path(__file__).parent.parent.parent


class SpotifyService:
    """
    Hybrid Spotify service combining librespot playback with Spotipy search.

    Key features:
    - No external Spotify app required for playback
    - OAuth browser flow for authentication (no developer app needed)
    - Direct audio output via sounddevice
    - Requires Spotify Premium account
    """

    def __init__(self):
        """
        Initialize Spotify service with librespot player and Spotipy search.

        Raises:
            RuntimeError: If authentication fails
        """
        # Initialize librespot player for direct playback
        self.player = LibrespotPlayer()

        # Authenticate with Spotify
        if not self.player.authenticate():
            raise RuntimeError(
                "Failed to authenticate with Spotify. "
                "Make sure you have a Spotify Premium account."
            )

        self.is_premium = self.player.is_premium

        # Initialize Spotipy for search using librespot's token
        self.sp = self._create_spotipy_client()

        # Current playback state
        self._current_track: Optional[Dict] = None
        self._is_playing = False

        logger.info("Spotify service initialized (librespot + Spotipy hybrid)")

    def _create_spotipy_client(self) -> Optional[spotipy.Spotify]:
        """
        Create a Spotipy client using librespot's access token.

        Returns:
            Spotipy client instance or None if token unavailable
        """
        token = self.player.get_access_token()

        if token:
            return spotipy.Spotify(auth=token)
        else:
            logger.warning("Could not get access token for Spotipy")
            return None

    def _refresh_spotipy_token(self):
        """Refresh the Spotipy client token if needed."""
        token = self.player.get_access_token()
        if token:
            self.sp = spotipy.Spotify(auth=token)

    def search_track(self, query: str, limit: int = 1) -> Optional[Dict]:
        """
        Search for a track on Spotify.

        Args:
            query: Search query (song name, artist, etc.)
            limit: Number of results to return

        Returns:
            Dictionary with track information or None if not found
        """
        if self.sp is None:
            self._refresh_spotipy_token()

        if self.sp is None:
            logger.error("Spotipy client not available for search")
            return None

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
        except spotipy.exceptions.SpotifyException as e:
            # Token might be expired, try refreshing
            if e.http_status == 401:
                self._refresh_spotipy_token()
                return self.search_track(query, limit)
            logger.error(f"Error searching for track '{query}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching for track '{query}': {e}")
            return None

    def search_artist(self, artist_name: str) -> Optional[Dict]:
        """
        Search for an artist on Spotify.

        Args:
            artist_name: Name of the artist

        Returns:
            Dictionary with artist information or None if not found
        """
        if self.sp is None:
            self._refresh_spotipy_token()

        if self.sp is None:
            return None

        try:
            results = self.sp.search(q=f"artist:{artist_name}", type='artist', limit=1)
            if results['artists']['items']:
                artist = results['artists']['items'][0]
                return {
                    'id': artist['id'],
                    'uri': artist['uri'],
                    'name': artist['name'],
                    'genres': artist.get('genres', [])
                }
            return None
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 401:
                self._refresh_spotipy_token()
                return self.search_artist(artist_name)
            logger.error(f"Error searching for artist '{artist_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching for artist '{artist_name}': {e}")
            return None

    def get_artist_top_tracks(self, artist_id: str) -> List[Dict]:
        """
        Get top tracks for an artist.

        Args:
            artist_id: Spotify artist ID

        Returns:
            List of track dictionaries
        """
        if self.sp is None:
            self._refresh_spotipy_token()

        if self.sp is None:
            return []

        try:
            results = self.sp.artist_top_tracks(artist_id)
            tracks = []
            for track in results.get('tracks', [])[:10]:
                tracks.append({
                    'uri': track['uri'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'id': track['id']
                })
            return tracks
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 401:
                self._refresh_spotipy_token()
                return self.get_artist_top_tracks(artist_id)
            logger.error(f"Error getting top tracks for artist '{artist_id}': {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting top tracks for artist '{artist_id}': {e}")
            return []

    def play_track(self, query: str) -> str:
        """
        Search for and play a track.

        Args:
            query: Search query for the track

        Returns:
            Response message
        """
        if not self.is_premium:
            return "Spotify playback requires a Premium account."

        # Search for the track
        track = self.search_track(query)
        if not track:
            return f"Sorry, I couldn't find '{query}' on Spotify."

        # Set as single-track queue and play
        self.player.set_queue([track['uri']])
        if self.player.play_next_in_queue():
            self._current_track = track
            self._is_playing = True
            return f"Now playing {track['name']} by {track['artist']}"
        else:
            return "Sorry, I couldn't start playback."

    def pause_playback(self) -> str:
        """Pause current playback."""
        if not self._is_playing:
            return "Nothing is currently playing."

        self.player.pause()
        return "Paused playback"

    def resume_playback(self) -> str:
        """Resume current playback."""
        if self.player.is_paused:
            self.player.resume()
            return "Resumed playback"
        elif not self._is_playing and self._current_track:
            # Restart the current track
            self.player.play_uri(self._current_track['uri'])
            self._is_playing = True
            return f"Resumed playing {self._current_track['name']}"
        else:
            return "Nothing to resume."

    def stop_playback(self) -> str:
        """Stop current playback."""
        self.player.stop()
        self._is_playing = False
        return "Stopped playback"

    def next_track(self) -> str:
        """Skip to next track in queue."""
        if self.player.skip_to_next():
            return "Skipped to next track"
        else:
            self._is_playing = False
            return "No more tracks in queue"

    def previous_track(self) -> str:
        """Go to previous track."""
        if self.player.skip_to_previous():
            return "Playing previous track"
        else:
            return "No previous track available"

    def get_current_playback(self) -> Optional[Dict]:
        """Get information about current playback."""
        if self._current_track:
            return {
                'name': self._current_track['name'],
                'artist': self._current_track['artist'],
                'is_playing': self._is_playing and not self.player.is_paused
            }
        return None

    def get_now_playing(self) -> str:
        """Get currently playing track."""
        playback = self.get_current_playback()
        if playback:
            status = "playing" if playback['is_playing'] else "paused"
            return f"Currently {status}: {playback['name']} by {playback['artist']}"
        return "Nothing is currently playing."

    def set_volume(self, volume_percent: int) -> str:
        """
        Set playback volume.

        Note: librespot doesn't support Spotify volume API.
        Use system volume controls instead.

        Args:
            volume_percent: Volume level (0-100)

        Returns:
            Response message
        """
        return "Volume control is not available. Please use your system's volume controls."

    def search_and_play_artist(self, artist_name: str) -> str:
        """Search for and play top tracks from an artist."""
        if not self.is_premium:
            return "Spotify playback requires a Premium account."

        # Search for artist
        artist = self.search_artist(artist_name)
        if not artist:
            return f"Sorry, I couldn't find artist '{artist_name}' on Spotify."

        # Get artist's top tracks
        tracks = self.get_artist_top_tracks(artist['id'])
        if not tracks:
            return f"Sorry, couldn't find tracks for {artist['name']}."

        # Set up queue with top tracks
        track_uris = [track['uri'] for track in tracks]
        self.player.set_queue(track_uris)

        # Start playing first track
        if self.player.play_next_in_queue():
            self._current_track = tracks[0]
            self._is_playing = True
            return f"Now playing top songs by {artist['name']}"
        else:
            return f"Sorry, I couldn't start playback for {artist['name']}."

    def cleanup(self):
        """Clean up resources."""
        self.player.cleanup()
