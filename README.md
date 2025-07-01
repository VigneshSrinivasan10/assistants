# Voice Assistant

A low-latency voice assistant that listens for commands and responds. 

## Features

- Responds to questions
- Checks weather status 
- Has a memory of the last 10 conversations

### To do
- Fast song search and playback on Spotify

## Project Structure

```
└── assistants/
    ├── README.md
    ├── pyproject.toml
    ├── src/
    │   ├── __init__.py
    │   ├── index.html
    │   ├── logger.py
    │   ├── main.py
    │   ├── model.py
    │   ├── util.py
    │   ├── cli/
    │   │   ├── __init__.py
    │   │   └── conf/
    │   │       ├── __init__.py
    │   │       └── base.yaml
    │   └── features/
    │       ├── __init__.py
    │       ├── memory.py
    │       └── weather.py
    └── tests/
        ├── __init__.py
        ├── interactive_llm_test.py
        ├── test_llm.py
        └── weather.py
```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/vigneshsrinivasan10/assistants.git
   cd assistants
   ```

2. Install poethepoet:
   ```
   pipx install poethepoet 
   ```
3. Poe will then install the `.venv`, download the LLM and start the voice assistant: 
   ```
   poe smart-run
   ```
   Then open the link on your favorite browser: 
   ```
   http://127.0.0.1:7860
   ```
   and click on `start conversation`.  

## Usage
### Wake word and pause detection

- By default, the wake word is set to `computer`. 
- Pause detection and interruption is performed using the `fastrtc` library. 

## How it works

1. The assistant continuously listens for the wake word "computer"
2. When detected, it transcribes what you speak
3. It queries the transcription to an LLM
4. Converts the output of the LLM to audio and responds

E.g.: 
```
User: Computer(wake-word), what is the capital of Japan.
Response: The capital of Japan is Tokyo.
```
![Example Conversation](images/example_conversation.png)

## Configuration

All configuration is stored in `assistant/src/cli/conf/base.yaml`:

### Models Used

- Speech-to-text 
Whisper simple model from the library `fastrtc_whisper_cpp`: 
```small.en```
Smaller models like `base` and `tiny` can be used to make this faster but the quality suffers. 

- LLM 
Mistral 7B from TheBloke using the library `llama_cpp`: 
```mistral-7b-instruct-v0.1.Q4_K_M.gguf``` 

- Text-to-speech 
Kokoro used within the library `fastrtc`.  

## License

MIT 
