"""
Unit tests for Spotify integration.

Run with: pytest tests/test_spotify.py -v
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from voice_assistant.features.spotify import SpotifyService
from voice_assistant.routing import SpotifyHandler


class TestSpotifyService:
    """Test SpotifyService functionality."""

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_initialization_with_credentials(self, mock_oauth, mock_spotify):
        """Test service initializes with valid credentials."""
        service = SpotifyService(
            client_id="test_id",
            client_secret="test_secret"
        )
        assert service.client_id == "test_id"
        assert service.client_secret == "test_secret"
        assert service.sp is not None

    def test_initialization_without_credentials(self):
        """Test service raises error without credentials."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Spotify credentials not found"):
                SpotifyService()

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_search_track_found(self, mock_oauth, mock_spotify):
        """Test searching for a track that exists."""
        service = SpotifyService(client_id="test", client_secret="test")

        # Mock search results
        service.sp.search = Mock(return_value={
            'tracks': {
                'items': [{
                    'uri': 'spotify:track:123',
                    'name': 'Test Song',
                    'artists': [{'name': 'Test Artist'}],
                    'album': {'name': 'Test Album'},
                    'id': '123'
                }]
            }
        })

        result = service.search_track("test song")

        assert result is not None
        assert result['name'] == 'Test Song'
        assert result['artist'] == 'Test Artist'
        assert result['uri'] == 'spotify:track:123'

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_search_track_not_found(self, mock_oauth, mock_spotify):
        """Test searching for a track that doesn't exist."""
        service = SpotifyService(client_id="test", client_secret="test")

        service.sp.search = Mock(return_value={'tracks': {'items': []}})

        result = service.search_track("nonexistent song")

        assert result is None

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_play_track_success(self, mock_oauth, mock_spotify):
        """Test playing a track successfully."""
        service = SpotifyService(client_id="test", client_secret="test")

        # Mock devices and search
        service.sp.devices = Mock(return_value={'devices': [{'id': 'device123'}]})
        service.sp.search = Mock(return_value={
            'tracks': {
                'items': [{
                    'uri': 'spotify:track:123',
                    'name': 'Test Song',
                    'artists': [{'name': 'Test Artist'}],
                    'album': {'name': 'Test Album'},
                    'id': '123'
                }]
            }
        })
        service.sp.start_playback = Mock()

        response = service.play_track("test song")

        assert "Now playing Test Song by Test Artist" in response
        service.sp.start_playback.assert_called_once()

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_play_track_no_devices(self, mock_oauth, mock_spotify):
        """Test playing when no devices are available."""
        service = SpotifyService(client_id="test", client_secret="test")

        service.sp.devices = Mock(return_value={'devices': []})

        response = service.play_track("test song")

        assert "No active Spotify devices found" in response

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_pause_playback(self, mock_oauth, mock_spotify):
        """Test pausing playback."""
        service = SpotifyService(client_id="test", client_secret="test")
        service.sp.pause_playback = Mock()

        response = service.pause_playback()

        assert "Paused playback" in response
        service.sp.pause_playback.assert_called_once()

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_resume_playback(self, mock_oauth, mock_spotify):
        """Test resuming playback."""
        service = SpotifyService(client_id="test", client_secret="test")
        service.sp.start_playback = Mock()

        response = service.resume_playback()

        assert "Resumed playback" in response
        service.sp.start_playback.assert_called_once()

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_next_track(self, mock_oauth, mock_spotify):
        """Test skipping to next track."""
        service = SpotifyService(client_id="test", client_secret="test")
        service.sp.next_track = Mock()

        response = service.next_track()

        assert "Skipped to next track" in response
        service.sp.next_track.assert_called_once()

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_previous_track(self, mock_oauth, mock_spotify):
        """Test going to previous track."""
        service = SpotifyService(client_id="test", client_secret="test")
        service.sp.previous_track = Mock()

        response = service.previous_track()

        assert "Playing previous track" in response
        service.sp.previous_track.assert_called_once()

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_get_now_playing(self, mock_oauth, mock_spotify):
        """Test getting current playback info."""
        service = SpotifyService(client_id="test", client_secret="test")

        service.sp.current_playback = Mock(return_value={
            'item': {
                'name': 'Current Song',
                'artists': [{'name': 'Current Artist'}]
            },
            'is_playing': True
        })

        response = service.get_now_playing()

        assert "playing: Current Song by Current Artist" in response


class TestSpotifyHandler:
    """Test SpotifyHandler routing functionality."""

    def test_handler_initialization(self):
        """Test handler initializes correctly."""
        mock_service = Mock()
        handler = SpotifyHandler(mock_service, priority=9)

        assert handler.name == "Spotify"
        assert handler.priority == 9
        assert handler.spotify == mock_service

    def test_can_handle_play_song(self):
        """Test handler recognizes play song commands."""
        mock_service = Mock()
        handler = SpotifyHandler(mock_service)

        assert handler.can_handle("play bohemian rhapsody")
        assert handler.can_handle("play some music")
        assert handler.can_handle("play song by the beatles")

    def test_can_handle_pause(self):
        """Test handler recognizes pause commands."""
        mock_service = Mock()
        handler = SpotifyHandler(mock_service)

        assert handler.can_handle("pause the music")
        assert handler.can_handle("stop playing")

    def test_can_handle_status(self):
        """Test handler recognizes status queries."""
        mock_service = Mock()
        handler = SpotifyHandler(mock_service)

        assert handler.can_handle("what's playing")
        assert handler.can_handle("now playing")
        assert handler.can_handle("current song")

    def test_cannot_handle_non_music(self):
        """Test handler doesn't match non-music queries."""
        mock_service = Mock()
        handler = SpotifyHandler(mock_service)

        assert not handler.can_handle("what's the weather")
        assert not handler.can_handle("set a reminder")
        assert not handler.can_handle("hello there")

    def test_process_pause(self):
        """Test processing pause command."""
        mock_service = Mock()
        mock_service.pause_playback = Mock(return_value="Paused playback")
        handler = SpotifyHandler(mock_service)

        response = handler.process("pause the music")

        assert "Paused playback" in response
        mock_service.pause_playback.assert_called_once()

    def test_process_play_song(self):
        """Test processing play song command."""
        mock_service = Mock()
        mock_service.play_track = Mock(return_value="Now playing Test Song")
        handler = SpotifyHandler(mock_service)

        response = handler.process("play bohemian rhapsody")

        mock_service.play_track.assert_called_once()

    def test_process_next_track(self):
        """Test processing next track command."""
        mock_service = Mock()
        mock_service.next_track = Mock(return_value="Skipped to next track")
        handler = SpotifyHandler(mock_service)

        response = handler.process("next song")

        assert "Skipped to next track" in response
        mock_service.next_track.assert_called_once()

    def test_get_keywords(self):
        """Test handler returns correct keywords."""
        mock_service = Mock()
        handler = SpotifyHandler(mock_service)

        keywords = handler.get_keywords()

        assert 'play' in keywords
        assert 'pause' in keywords
        assert 'spotify' in keywords
        assert 'song' in keywords


class TestSpotifyIntegration:
    """Integration tests for Spotify routing."""

    @patch('voice_assistant.features.spotify.spotipy.Spotify')
    @patch('voice_assistant.features.spotify.SpotifyOAuth')
    def test_end_to_end_play_command(self, mock_oauth, mock_spotify):
        """Test complete flow from query to playback."""
        from voice_assistant.routing import HandlerRegistry

        # Create service and handler
        service = SpotifyService(client_id="test", client_secret="test")
        handler = SpotifyHandler(service, priority=9)

        # Mock the Spotify API responses
        service.sp.devices = Mock(return_value={'devices': [{'id': 'device123'}]})
        service.sp.search = Mock(return_value={
            'tracks': {
                'items': [{
                    'uri': 'spotify:track:123',
                    'name': 'Bohemian Rhapsody',
                    'artists': [{'name': 'Queen'}],
                    'album': {'name': 'A Night at the Opera'},
                    'id': '123'
                }]
            }
        })
        service.sp.start_playback = Mock()

        # Register handler
        registry = HandlerRegistry()
        registry.register(handler)

        # Route query
        handler_name, response = registry.route("play bohemian rhapsody")

        assert handler_name == "Spotify"
        assert "Now playing Bohemian Rhapsody by Queen" in response
        service.sp.start_playback.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
