# Testing Guide for Spotify Integration

This guide explains how to test the Spotify voice control feature before creating a PR.

## ✅ Pre-Flight Checks (Already Done)

These checks were run automatically:

- ✅ **Syntax validation**: All Python files compile without syntax errors
- ✅ **Import structure**: Module imports are correctly structured
- ✅ **Dependency added**: `spotipy` added to `pyproject.toml`
- ✅ **Security**: Credentials properly configured in `.gitignore`

## 🔧 Setup (When You're Back)

### 1. Install Dependencies

```bash
cd /home/user/assistants

# Install all dependencies including spotipy
poe install
# or: uv sync
```

### 2. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the details:
   - **App name**: "Voice Assistant" (or any name)
   - **App description**: "Personal voice assistant"
   - **Redirect URI**: `http://localhost:8888/callback`
5. Click "Save"
6. Copy your **Client ID** and **Client Secret**

### 3. Configure Credentials

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials
nano .env  # or use any editor
```

Your `.env` should look like:
```
SPOTIFY_CLIENT_ID=your_actual_client_id_here
SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
```

**Important**: Never commit the `.env` file! It's already in `.gitignore`.

## 🧪 Running Tests

### Option 1: Unit Tests (Recommended First)

These tests use mocks and don't require real Spotify credentials:

```bash
# Run all Spotify unit tests
pytest tests/test_spotify.py -v

# Run specific test class
pytest tests/test_spotify.py::TestSpotifyService -v

# Run with coverage
pytest tests/test_spotify.py --cov=voice_assistant.features.spotify --cov-report=term-missing
```

**Expected output**: All tests should pass (✅)

### Option 2: Manual Integration Test

This tests with real Spotify API calls (requires credentials):

```bash
# Make the script executable
chmod +x tests/test_spotify_manual.py

# Run the manual test
python tests/test_spotify_manual.py
```

**Prerequisites**:
- ✅ `.env` file configured
- ✅ Spotify app open on at least one device (computer, phone, etc.)

**What it tests**:
- ✅ Authentication with Spotify API
- ✅ Searching for tracks
- ✅ Handler routing and keyword detection
- ✅ (Optional) Actual playback control

### Option 3: End-to-End Voice Test

Test with the actual voice assistant:

```bash
# Start the voice assistant
poe assistant

# Or: python -m voice_assistant.main
```

**Test these voice commands**:

1. **Play a song**:
   - "Computer, play Bohemian Rhapsody"
   - "Computer, play songs by The Beatles"

2. **Control playback**:
   - "Computer, pause music"
   - "Computer, resume music"
   - "Computer, next song"
   - "Computer, previous song"

3. **Get status**:
   - "Computer, what's playing?"
   - "Computer, now playing"

**Expected behavior**:
- Voice assistant responds via Spotify handler (not LLM)
- Songs play on your active Spotify device
- Playback controls work correctly

## 🔍 Validation Checklist

Before creating a PR, verify:

### Code Quality
- [ ] All unit tests pass (`pytest tests/test_spotify.py`)
- [ ] Manual integration test passes
- [ ] No syntax errors or import issues
- [ ] Code follows project style

### Functionality
- [ ] Can search and play songs
- [ ] Can control playback (pause/resume/skip)
- [ ] Can query current playback status
- [ ] Graceful handling when Spotify not configured
- [ ] Graceful handling when no devices available

### Security
- [ ] `.env` file is in `.gitignore`
- [ ] `.spotify_cache` is in `.gitignore`
- [ ] No credentials committed to git
- [ ] `.env.example` provides clear template

### Documentation
- [ ] `SPOTIFY_SETUP.md` is clear and complete
- [ ] Voice commands are documented
- [ ] Troubleshooting section covers common issues

## 🐛 Troubleshooting

### "No module named 'spotipy'"

**Solution**: Install dependencies
```bash
poe install
# or: uv sync
```

### "Spotify credentials not found"

**Solution**:
1. Check `.env` file exists in project root
2. Verify `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are set
3. No extra spaces or quotes around values

### "No active Spotify devices found"

**Solution**:
1. Open Spotify on your computer, phone, or tablet
2. Start playing something (then pause it)
3. Try the voice command again

### Authentication browser doesn't open

**Solution**:
1. Check redirect URI is `http://localhost:8888/callback` in Spotify Dashboard
2. Try opening the URL manually from terminal output
3. Complete authentication in browser

### Handler not routing to Spotify

**Check**:
1. Use music-related keywords: "play", "pause", "song", "music", "spotify"
2. Check logs for routing decisions
3. Verify SpotifyHandler is registered (check startup logs)

## 📊 Test Results Template

Use this when reporting test results:

```
## Test Results

**Environment**:
- Python version: 3.x.x
- OS: Linux/Mac/Windows
- Date: YYYY-MM-DD

**Unit Tests**:
- [ ] test_spotify.py: X/Y passed

**Integration Tests**:
- [ ] Authentication: ✅/❌
- [ ] Search: ✅/❌
- [ ] Playback: ✅/❌
- [ ] Routing: ✅/❌

**Voice Tests**:
- [ ] Play song: ✅/❌
- [ ] Pause: ✅/❌
- [ ] Skip: ✅/❌
- [ ] Status: ✅/❌

**Issues Found**: None / [List issues]
```

## 🚀 Quick Test Script

For a super quick test, run:

```bash
# Quick validation script
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

print("🧪 Quick Spotify Integration Test\n")

# 1. Check dependencies
try:
    import spotipy
    print("✅ spotipy installed")
except ImportError:
    print("❌ spotipy not installed - run 'poe install'")
    sys.exit(1)

# 2. Check imports
try:
    from voice_assistant.features.spotify import SpotifyService
    from voice_assistant.routing import SpotifyHandler
    print("✅ Imports work")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# 3. Check .env
import os
from pathlib import Path
env_file = Path(".env")
if env_file.exists():
    print("✅ .env file exists")
    with open(env_file) as f:
        content = f.read()
        if "SPOTIFY_CLIENT_ID" in content:
            print("✅ Credentials configured")
        else:
            print("⚠️  Credentials not set in .env")
else:
    print("⚠️  .env file not found")

# 4. Check gitignore
gitignore = Path(".gitignore")
if gitignore.exists():
    with open(gitignore) as f:
        content = f.read()
        if ".env" in content and ".spotify_cache" in content:
            print("✅ Security: .env and .spotify_cache in .gitignore")
        else:
            print("⚠️  Check .gitignore settings")

print("\n✨ Basic checks complete!")
print("Run 'pytest tests/test_spotify.py' for full unit tests")
EOF
```

## 📝 Next Steps After Testing

1. ✅ All tests pass
2. ✅ Create PR with test results
3. ✅ Reference this testing guide in PR description
4. ✅ Include example voice commands in PR

## 💡 Tips

- **Start with unit tests**: They're fast and don't need real credentials
- **Test incrementally**: Test each feature as you configure
- **Check logs**: Use `LOG_LEVEL=DEBUG` for detailed output
- **Device active**: Keep Spotify open during tests
- **Browser auth**: First run will open browser for OAuth

Good luck with testing! 🎉
