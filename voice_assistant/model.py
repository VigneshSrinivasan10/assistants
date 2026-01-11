import numpy as np
from omegaconf import DictConfig
from pathlib import Path
import hydra

from fastrtc import get_stt_model, get_tts_model, KokoroTTSOptions, AdditionalOutputs
from fastrtc_whisper_cpp import get_stt_model as get_stt_model_whisper_cpp
import ollama

from voice_assistant.util import timer
from voice_assistant.features.weather import WeatherForecast
from voice_assistant.features.memory import ConversationMemory
from voice_assistant.routing import HandlerRegistry, WeatherHandler

class STT:
    def __init__(self, model: str = "moonshine/base"):
        #self.stt_model = get_stt_model(model=stt_model)
        self.stt_model = get_stt_model_whisper_cpp(model=model)

    @timer
    def speech_to_text(self, audio: tuple[int, np.ndarray]):
        return self.stt_model.stt(audio)

class TTS:
    def __init__(self, model: str = "kokoro", 
                 voice: str = "af_heart", 
                 speed: float = 1.0, 
                 lang: str = "en-us",
                 ):
        self.tts_model = get_tts_model(model=model)
        self.options = KokoroTTSOptions(voice=voice, speed=speed, lang=lang)

    @timer
    def text_to_speech(self, text: str):
        return self.tts_model.tts(text, options=self.options)

class LLM:
    def __init__(self, model_name: str = "mistral:7b-instruct-q4_K_M",
                        max_conversations: int = 10,
                        memory_file: str = "./data/conversation_memory.json",
                        temperature: float = 0.2,
                        top_p: float = 0.9,
                        repeat_penalty: float = 1.2,
                        max_tokens: int = 50):
        self.model_name = model_name
        self.client = ollama.Client()
        self.memory = ConversationMemory(max_conversations=max_conversations, save_file=memory_file)
        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.max_tokens = max_tokens
        self.stop = ["Q:", "\n", "<|end|>"]
        
    @timer
    def generate(self, prompt: str):
        # Get conversation history context
        context = self.memory.get_context()

        # Build messages for Ollama chat API
        messages = []

        if context:
            messages.append({
                "role": "system",
                "content": f"You are a helpful assistant. Here is the conversation history:\n{context}"
            })
        else:
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant."
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        # Call Ollama API
        response = self.client.chat(
            model=self.model_name,
            messages=messages,
            options={
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty,
                "num_predict": self.max_tokens,
                "stop": self.stop,
            }
        )

        # Extract and clean the response text
        response_text = response["message"]["content"].strip()

        # Remove any stop tokens that might have leaked through
        for stop_token in self.stop:
            response_text = response_text.replace(stop_token, "")

        return response_text.strip()
    
    def add_to_memory(self, user_message: str, assistant_response: str):
        """Add conversation to memory"""
        self.memory.add_conversation(user_message, assistant_response)
    
    def get_memory_info(self) -> dict:
        """Get information about the conversation memory"""
        return self.memory.get_memory_info()

class VoiceAssistant:
    def __init__(self, cfg: DictConfig):
        # Initialize models
        self.stt = hydra.utils.instantiate(cfg.stt)
        self.tts = hydra.utils.instantiate(cfg.tts)
        self.llm = hydra.utils.instantiate(cfg.llm)

        # Initialize features here such as weather forecast, etc.
        self.weather = WeatherForecast(provider="openmeteo")

        # Setup hybrid routing system (fast path + LLM fallback)
        self.router = HandlerRegistry()
        self.router.register(WeatherHandler(self.weather, priority=10))
        # Future handlers can be registered here:
        # self.router.register(CalculatorHandler(priority=8))
        # self.router.register(ReminderHandler(priority=9))

        self.latest_transcription = None
        self.latest_response = None

    def speech_to_speech(self, audio: tuple[int, np.ndarray]):
        # Convert audio to text using Moonshine
        transcription = self.stt.speech_to_text(audio)
        self.latest_transcription = transcription
        print(f"Transcription: {transcription}")

        yield AdditionalOutputs({"role": "user", "content": transcription})

        if transcription not in ["", " ", None]:

            # Try routing to specialized handler first (fast path)
            handler_name, response_text = self.router.route(transcription)

            if response_text is None:
                # Fallback to LLM for general conversation
                handler_name = "LLM"
                response_text = self.llm.generate(transcription)

            self.latest_response = response_text
            print(f"[Router] Handled by: {handler_name}")
            print(f"Response: {response_text}")
            
            # Add conversation to memory
            self.llm.add_to_memory(transcription, response_text)
            
             # Send response text to browser through AdditionalOutputs
            yield AdditionalOutputs({"role": "assistant", "content": response_text})
            
            # Convert text back to speech using Kokoro
            audio = self.tts.text_to_speech(response_text)
            
            # Store the response text in a class variable that can be accessed by the web interface
            self.current_response = response_text
            
            yield audio
        else:
            audio = None
            yield audio
    
    def get_memory_info(self) -> dict:
        """Get information about the conversation memory"""
        return self.llm.get_memory_info()

    def get_routing_info(self) -> dict:
        """Get information about registered handlers"""
        return {
            "total_handlers": len(self.router),
            "handlers": self.router.get_handlers_info()
        }