# Spotify Integration Setup Guide

This voice assistant now supports Spotify playback control! You can play songs, control playback, and more using voice commands.

## Prerequisites

- A Spotify account (Free or Premium)
- Python environment with the project dependencies installed
- An active Spotify device (desktop app, mobile app, or web player)

## Setup Instructions

### 1. Create a Spotify Developer App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create app"**
4. Fill in the app details:
   - **App name**: Voice Assistant (or any name you prefer)
   - **App description**: Personal voice assistant for Spotify control
   - **Redirect URI**: `http://localhost:8888/callback`
   - **APIs used**: Select "Web API"
5. Accept the terms and click **"Save"**
6. Click on **"Settings"** to view your credentials
7. Copy your **Client ID** and **Client Secret**

### 2. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Spotify credentials:
   ```bash
   SPOTIFY_CLIENT_ID=your_actual_client_id_here
   SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
   ```

   **Important:** Never commit your `.env` file to git! It's already in `.gitignore` for security.

### 3. Install Dependencies

If you haven't already installed the project dependencies, run:

```bash
poe install
```

This will install the `spotipy` library and all other required packages.

### 4. First-Time Authentication

The first time you use a Spotify command, the assistant will:

1. Open your default web browser for authentication
2. Ask you to log in to Spotify (if not already logged in)
3. Ask for permission to control your Spotify playback
4. Redirect you to `http://localhost:8888/callback`
5. Save the authentication token in `.spotify_cache` (this file is in `.gitignore`)

After this initial setup, you won't need to authenticate again unless the token expires.

## Voice Commands

Once configured, you can use these voice commands:

### Playing Music

- **"Play [song name]"** - Search and play a specific song
  - Example: "Play Bohemian Rhapsody"
  - Example: "Play the song Imagine by John Lennon"

- **"Play songs by [artist name]"** - Play top tracks by an artist
  - Example: "Play songs by The Beatles"
  - Example: "Play music by Taylor Swift"

### Playback Control

- **"Pause music"** / **"Stop music"** - Pause current playback
- **"Resume music"** / **"Play music"** - Resume paused playback
- **"Next song"** / **"Skip"** - Skip to next track
- **"Previous song"** / **"Go back"** - Play previous track

### Status

- **"What's playing?"** / **"Now playing"** - Get current track info
- **"What song is this?"** - Get current song name and artist

## How It Works

The Spotify integration uses a **handler-based architecture**:

1. **Voice Input**: You speak a command to the voice assistant
2. **Speech-to-Text**: Whisper transcribes your voice to text
3. **Handler Routing**: The `SpotifyHandler` checks if the query is Spotify-related
4. **Spotify API**: If matched, it calls the Spotify API to perform the action
5. **Response**: The assistant speaks the result back to you

The Spotify handler has **priority 9** (high priority), so music commands are quickly routed without needing the LLM.

## Troubleshooting

### "No active Spotify device found"

**Solution**: Open Spotify on any device (desktop app, mobile app, or web player) and start playing something. The device needs to be active for the API to work.

### "Spotify credentials not found"

**Solution**: Make sure you've created the `.env` file with your `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.

### "Failed to authenticate with Spotify"

**Solutions**:
1. Check that your credentials in `.env` are correct
2. Verify the redirect URI in your Spotify app settings is exactly: `http://localhost:8888/callback`
3. Delete `.spotify_cache` and try authenticating again

### Browser doesn't open for authentication

**Solution**: The authentication URL will be printed in the console. Copy and paste it into your browser manually.

### "Sorry, I couldn't find [song name]"

**Solutions**:
1. Try rephrasing the song name
2. Include the artist name: "Play [song] by [artist]"
3. Check that the song exists on Spotify

## Architecture Details

### Files Added/Modified

- **`voice_assistant/features/spotify.py`**: Spotify API service wrapper
- **`voice_assistant/routing.py`**: Added `SpotifyHandler` class
- **`voice_assistant/model.py`**: Registers Spotify handler in the routing system
- **`pyproject.toml`**: Added `spotipy` dependency
- **`.env.example`**: Template for environment variables
- **`.gitignore`**: Added `.spotify_cache` and `.env` to ignored files

### Security

- ✅ Credentials are stored in `.env` (not committed to git)
- ✅ Authentication tokens cached in `.spotify_cache` (not committed to git)
- ✅ OAuth 2.0 flow for secure authentication
- ✅ Minimal scopes requested (only playback control)

### Scopes Used

The integration requests these Spotify API scopes:

- `user-modify-playback-state`: Control playback (play, pause, skip)
- `user-read-playback-state`: Read current playback state
- `user-read-currently-playing`: Get currently playing track

## Optional: Advanced Configuration

### Custom Cache Path

You can change where the Spotify auth cache is stored by modifying `model.py`:

```python
self.spotify = SpotifyService(cache_path="/path/to/custom/.spotify_cache")
```

### Different Redirect URI

If you want to use a different redirect URI:

1. Update your Spotify app settings in the Developer Dashboard
2. Set `SPOTIFY_REDIRECT_URI` in your `.env` file
3. Modify the `SpotifyService` initialization in `model.py`

## Support

If you encounter issues:

1. Check the console logs for error messages
2. Verify your Spotify app settings in the Developer Dashboard
3. Ensure your `.env` file has the correct credentials
4. Make sure Spotify is open and active on at least one device

## Future Enhancements

Possible additions for future versions:

- Playlist management (create, modify, delete playlists)
- Volume control ("Set volume to 50%")
- Search and play albums
- Like/unlike songs
- Queue management
- Shuffle and repeat controls

---

**Enjoy controlling your Spotify with your voice!** 🎵
