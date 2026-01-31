"""
LibrespotPlayer - Direct Spotify audio playback using librespot-python.

This module provides direct audio streaming from Spotify without requiring
an external Spotify app to be running. Requires a Spotify Premium account.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Optional, Callable, List

import numpy as np
import sounddevice as sd
from librespot.core import Session
from librespot.metadata import TrackId
from librespot.structure import AudioQualityPicker
from librespot.proto import Metadata_pb2 as Metadata

logger = logging.getLogger(__name__)


class VorbisQualityPicker(AudioQualityPicker):
    """Audio quality picker that prefers Vorbis format at highest quality."""

    def get_file(self, files: List[Metadata.AudioFile]) -> Metadata.AudioFile:
        """Select the best Vorbis file from available formats."""
        # Vorbis format IDs (prefer higher quality)
        # OGG_VORBIS_320 = 0, OGG_VORBIS_160 = 1, OGG_VORBIS_96 = 2
        vorbis_formats = [0, 1, 2]  # 320, 160, 96 kbps

        for fmt in vorbis_formats:
            for file in files:
                if file.format == fmt:
                    return file

        # Fallback: return first available
        if files:
            return files[0]
        return None

# Project root for credential caching
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_CREDENTIALS_PATH = str(_PROJECT_ROOT / ".librespot_credentials")


class LibrespotPlayer:
    """
    Direct Spotify audio player using librespot.

    Handles OAuth authentication, credential caching, and audio playback
    in a background thread.
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize the LibrespotPlayer.

        Args:
            credentials_path: Path to store cached credentials (defaults to project root)
        """
        self.credentials_path = credentials_path or _DEFAULT_CREDENTIALS_PATH
        self.session: Optional[Session] = None
        self.is_premium: bool = False

        # Playback state
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._current_track_uri: Optional[str] = None
        self._is_playing = False

        # Track queue for playlist/artist playback
        self._track_queue: list = []
        self._queue_index: int = 0

    def authenticate(self) -> bool:
        """
        Authenticate with Spotify using OAuth browser flow or cached credentials.

        Returns:
            True if authentication succeeded, False otherwise
        """
        try:
            # Check for cached credentials first
            creds_path = Path(self.credentials_path)
            if creds_path.exists():
                logger.info("Found cached credentials, attempting to restore session")
                try:
                    with open(self.credentials_path, 'r') as f:
                        stored_creds = f.read().strip()

                    builder = Session.Builder()
                    builder.stored(stored_creds)
                    self.session = builder.create()
                    logger.info(f"Session restored for user: {self.session.username()}")
                except Exception as e:
                    logger.warning(f"Failed to restore session: {e}")
                    creds_path.unlink(missing_ok=True)
                    self.session = None

            # If no session, do OAuth flow
            if self.session is None:
                logger.info("Starting OAuth authentication flow")
                print("\n" + "="*70)
                print("SPOTIFY AUTHENTICATION REQUIRED")
                print("="*70)
                print("\nA browser window will open for Spotify login.")
                print("Log in with your Spotify Premium account.")
                print("The callback server runs on port 5588.")
                print("="*70 + "\n")

                def on_oauth_url(url):
                    print("\nOpen this URL in your browser:\n")
                    print(url)
                    print("\nWaiting for authentication on port 5588...\n")

                builder = Session.Builder()
                builder.oauth(on_oauth_url)
                self.session = builder.create()

                # Save credentials for future use
                stored_creds = self.session.stored()
                if stored_creds:
                    with open(self.credentials_path, 'w') as f:
                        f.write(stored_creds)
                    logger.info(f"Credentials saved to {self.credentials_path}")

                logger.info("OAuth authentication successful")
                print(f"\nSuccessfully authenticated as: {self.session.username()}\n")

            # Check if user has Premium
            self._check_premium_status()

            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            print(f"\nAuthentication failed: {e}")
            print("Make sure you have a Spotify Premium account.\n")
            return False

    def _check_premium_status(self):
        """Check if the authenticated user has Premium."""
        if self.session is None:
            self.is_premium = False
            return

        try:
            user_type = self.session.get_user_attribute("type")
            self.is_premium = user_type == "premium"

            if self.is_premium:
                logger.info("Spotify Premium account confirmed")
            else:
                logger.warning(f"Account type: {user_type} - playback may not work")
                print("\nWARNING: Premium account required for playback.\n")

        except Exception as e:
            logger.warning(f"Could not verify Premium status: {e}")
            self.is_premium = True  # Assume and let it fail if not

    def get_access_token(self, scope: str = "") -> Optional[str]:
        """
        Get an access token for use with Spotipy (search API).

        Returns:
            Access token string or None if not authenticated
        """
        if self.session is None:
            return None

        try:
            token = self.session.tokens().get("playlist-read-private")
            return token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            return None

    def play_uri(self, uri: str, on_track_end: Optional[Callable] = None) -> bool:
        """
        Stream and play a Spotify track by URI.

        Args:
            uri: Spotify track URI (e.g., 'spotify:track:xxx')
            on_track_end: Callback when track finishes

        Returns:
            True if playback started, False otherwise
        """
        if self.session is None:
            logger.error("Not authenticated")
            return False

        if not self.is_premium:
            logger.error("Premium required for playback")
            return False

        # Stop any current playback
        self.stop()

        self._current_track_uri = uri
        self._stop_event.clear()
        self._pause_event.clear()
        self._is_playing = True

        # Start playback in background thread
        self._playback_thread = threading.Thread(
            target=self._playback_worker,
            args=(uri, on_track_end),
            daemon=True
        )
        self._playback_thread.start()

        return True

    def _playback_worker(self, uri: str, on_track_end: Optional[Callable] = None):
        """Background thread for audio playback."""
        try:
            # Extract track ID from URI
            track_id = TrackId.from_uri(uri)

            # Get audio stream from Spotify
            content_feeder = self.session.content_feeder()

            # Load the track - this returns a LoadedStream
            quality_picker = VorbisQualityPicker()
            loaded_stream = content_feeder.load_track(
                track_id,
                quality_picker,
                False,
                None
            )

            streamer = loaded_stream.input_stream
            stream = streamer.stream()

            # Read all audio data (it's in OGG Vorbis format)
            total_size = streamer.size
            audio_bytes = stream.read(total_size)
            logger.info(f"Read {len(audio_bytes)} bytes of audio data (codec: {streamer.codec()})")

            # Decode OGG Vorbis using pyogg
            import tempfile
            import pyogg

            # Write to temp file (pyogg needs a file path)
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
                temp_path = f.name
                f.write(audio_bytes)

            try:
                # Decode with pyogg
                vorbis_file = pyogg.VorbisFile(temp_path)

                pcm_data = vorbis_file.buffer
                channels = vorbis_file.channels
                sample_rate = vorbis_file.frequency

                logger.info(f"Decoded: {len(pcm_data)} bytes, {channels}ch, {sample_rate}Hz")

                # Convert to numpy array
                audio_array = np.frombuffer(pcm_data, dtype=np.int16)
                if channels == 2:
                    audio_array = audio_array.reshape(-1, 2)

                # Play audio in chunks
                chunk_size = 4096
                position = 0

                with sd.OutputStream(
                    samplerate=sample_rate,
                    channels=channels,
                    dtype='int16'
                ) as audio_stream:
                    while position < len(audio_array) and not self._stop_event.is_set():
                        # Handle pause
                        while self._pause_event.is_set() and not self._stop_event.is_set():
                            time.sleep(0.1)

                        if self._stop_event.is_set():
                            break

                        # Get and play chunk
                        end_pos = min(position + chunk_size, len(audio_array))
                        audio_stream.write(audio_array[position:end_pos])
                        position = end_pos

            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)

            self._is_playing = False

            # Call track end callback if not stopped manually
            if on_track_end and not self._stop_event.is_set():
                on_track_end()

        except Exception as e:
            logger.error(f"Playback error: {e}")
            import traceback
            traceback.print_exc()
            self._is_playing = False

    def pause(self):
        """Pause current playback."""
        if self._is_playing:
            self._pause_event.set()
            logger.info("Playback paused")

    def resume(self):
        """Resume paused playback."""
        if self._pause_event.is_set():
            self._pause_event.clear()
            logger.info("Playback resumed")

    def stop(self):
        """Stop playback and reset state."""
        self._stop_event.set()
        self._pause_event.clear()

        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)

        self._playback_thread = None
        self._current_track_uri = None
        self._is_playing = False
        logger.info("Playback stopped")

    def set_queue(self, track_uris: list):
        """Set a queue of tracks to play."""
        self._track_queue = track_uris
        self._queue_index = 0
        logger.info(f"Queue set with {len(track_uris)} tracks")

    def play_next_in_queue(self) -> bool:
        """Play the next track in the queue."""
        if self._queue_index < len(self._track_queue):
            uri = self._track_queue[self._queue_index]
            self._queue_index += 1
            return self.play_uri(uri, on_track_end=self._on_track_end)
        return False

    def _on_track_end(self):
        """Callback when a track ends - play next in queue."""
        if self._queue_index < len(self._track_queue):
            self.play_next_in_queue()

    def skip_to_next(self) -> bool:
        """Skip to the next track in the queue."""
        self.stop()
        return self.play_next_in_queue()

    def skip_to_previous(self) -> bool:
        """Skip to the previous track in the queue."""
        if self._queue_index > 1:
            self._queue_index -= 2
            self.stop()
            return self.play_next_in_queue()
        elif self._queue_index == 1:
            self._queue_index = 0
            self.stop()
            return self.play_next_in_queue()
        return False

    @property
    def is_paused(self) -> bool:
        """Check if playback is paused."""
        return self._pause_event.is_set()

    @property
    def current_track(self) -> Optional[str]:
        """Get the currently playing track URI."""
        return self._current_track_uri

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if self.session:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None
