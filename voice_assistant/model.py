import numpy as np
from omegaconf import DictConfig
from pathlib import Path
import hydra

from fastrtc import get_stt_model, get_tts_model, KokoroTTSOptions, AdditionalOutputs
from fastrtc_whisper_cpp import get_stt_model as get_stt_model_whisper_cpp
from llama_cpp import Llama

from voice_assistant.util import timer
from voice_assistant.features.weather import WeatherForecast
from voice_assistant.features.memory import ConversationMemory

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
    def __init__(self, model_path: str, 
                        n_ctx: int, 
                        max_conversations: int = 10, 
                        memory_file: str = "./data/conversation_memory.json", 
                        temperature: float = 0.2, 
                        top_p: float = 0.9, 
                        repeat_penalty: float = 1.2, 
                        max_tokens: int = 50, 
                        echo: bool = False):
        project_root = Path(__file__).parents[0]  # Go up to project root
        model_path = str((project_root / model_path).resolve())
        
        self.llm = Llama(model_path=model_path, 
                         n_ctx=n_ctx,
                         n_threads=16,
                         n_batch=16,
                         n_gpu_layers=0)
        self.memory = ConversationMemory(max_conversations=max_conversations, save_file=memory_file)
        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.max_tokens = max_tokens
        self.stop = ["Q:", "\n", "<|end|>"]
        self.echo = echo
        
    @timer
    def generate(self, prompt: str):
        # Get conversation history context
        context = self.memory.get_context()
        
        # Build the complete prompt with memory context
        if context:
            text_prompt = (
                f"<|system|>\nYou are a helpful assistant. Here is the conversation history:\n{context}\n<|end|>\n"
                f"<|user|>\n{prompt}\n<|end|>\n"
                f"<|assistant|>\n"
            )
        else:
            text_prompt = (
                f"<|system|>\nYou are a helpful assistant.<|end|>\n"
                f"<|user|>\n{prompt}\n<|end|>\n"
                f"<|assistant|>\n"
            )

        response = self.llm(text_prompt, 
                            temperature=self.temperature, 
                            top_p=self.top_p, 
                            repeat_penalty=self.repeat_penalty, 
                            max_tokens=self.max_tokens,
                            stop=self.stop,
                            echo=self.echo)
        return response["choices"][0]["text"].strip()
    
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
        
        self.latest_transcription = None
        self.latest_response = None

    def speech_to_speech(self, audio: tuple[int, np.ndarray]):
        # Convert audio to text using Moonshine
        transcription = self.stt.speech_to_text(audio)
        self.latest_transcription = transcription
        print(f"Transcription: {transcription}")

        yield AdditionalOutputs({"role": "user", "content": transcription})     

        if transcription not in ["", " ", None]:

            if self.weather._is_weather_query(transcription):
                print(f"Weather query detected, routing to weather system...")
                # Route to weather forecast
                response_text = self.weather.process_weather_query(transcription)
            else: 
                # LLM generate response
                response_text = self.llm.generate(transcription)
                
            self.latest_response = response_text
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