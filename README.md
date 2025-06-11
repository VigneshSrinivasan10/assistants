# Voice Assistant

A low-latency voice assistant that listens for commands and responds. 

## Features

- Responds to questions

### To do
- Fast song search and playback on Spotify
- Check weather status 

## Project Structure

```
assistants/
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── model.py
│   ├── util.py
│   └── index.html
└── cli/
    ├── __init__.py
    └── conf/
    |  ├── __init__.py
    |  └── base.yaml
```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/vigneshsrinivasan10/assistants.git
   cd assistants
   ```

2. Install the package:
   ```
   uv venv venv
   source venv/bin/activate 
   uv pip install -e .
   ```

## Usage


## How It Works

1. The assistant continuously listens for the wake word "computer"
2. When detected, it transcribes what you speak until after a pause
3. It quearies the transcription to an LLM
4. Converts the output of the LLM to audio and responds

## Configuration

All configuration is stored in `assistant/cli/conf/base.yaml`:

## License

MIT 