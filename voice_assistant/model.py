import numpy as np
from omegaconf import DictConfig
from pathlib import Path
import hydra
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastrtc import get_stt_model, get_tts_model, KokoroTTSOptions, AdditionalOutputs
from fastrtc_whisper_cpp import get_stt_model as get_stt_model_whisper_cpp
from llama_cpp import Llama

from voice_assistant.util import timer
from voice_assistant.features.weather import WeatherForecast
from voice_assistant.features.memory import ConversationMemory
from voice_assistant.features.smart_memory import SmartConversationMemory
from voice_assistant.features.spotify import SpotifyService
from voice_assistant.features.calculator import Calculator
from voice_assistant.features.datetime_info import DateTimeInfo
from voice_assistant.features.system_info import SystemInfo
from voice_assistant.routing import (
    HandlerRegistry, WeatherHandler, SpotifyHandler,
    CalculatorHandler, DateTimeHandler, SystemInfoHandler
)
import logging

logger = logging.getLogger(__name__)

class STT:
    def __init__(self, model: str = "moonshine/base", use_gpu: bool = True):
        """
        Initialize STT with optimized model.
        
        Args:
            model: Model to use (base.en, small.en, medium.en, etc.)
            use_gpu: Enable GPU acceleration (auto-detected by whisper.cpp)
        
        Note: whisper.cpp will automatically use GPU if CUDA is available.
        Advanced parameters (beam_size, threads, etc.) are set via environment
        variables or whisper.cpp config, not through this wrapper.
        """
        # Use whisper.cpp for best performance
        # GPU acceleration is automatic if CUDA is available
        self.stt_model = get_stt_model_whisper_cpp(model=model)
        self.model_name = model
        logger.info(f"STT initialized with model={model}")
        logger.info("Whisper.cpp will use GPU automatically if CUDA is available")

    @timer
    def speech_to_text(self, audio: tuple[int, np.ndarray]):
        """
        Convert speech to text with optimized processing.
        
        Args:
            audio: Tuple of (sample_rate, audio_data)
            
        Returns:
            Transcribed text
        """
        # Validate audio length to avoid unnecessary processing
        sample_rate, audio_data = audio
        duration_ms = len(audio_data) / sample_rate * 1000
        
        # Skip very short audio (likely just noise/clicks)
        if duration_ms < 100:
            logger.debug(f"Skipping audio: too short ({duration_ms:.0f}ms)")
            return ""
        
        # Run STT
        result = self.stt_model.stt(audio)
        
        if result:
            logger.debug(f"STT result ({duration_ms:.0f}ms audio): '{result}'")
        
        return result

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
                        use_smart_memory: bool = True,
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
        
        # Use smart memory by default (quality filtering + relevance scoring)
        if use_smart_memory:
            self.memory = SmartConversationMemory(
                max_context_tokens=n_ctx // 2,  # Use half context for memory
                quality_threshold=0.3,
                relevance_threshold=0.2,
                save_file=memory_file,
            )
            logger.info("Using SmartConversationMemory (quality filtering enabled)")
        else:
            self.memory = ConversationMemory(
                max_conversations=max_conversations,
                save_file=memory_file
            )
            logger.info("Using basic ConversationMemory (legacy mode)")
        
        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.max_tokens = max_tokens
        self.stop = ["Q:", "\n", "<|end|>"]
        self.echo = echo
        
    @timer
    def generate(self, prompt: str):
        # Get conversation history context (with relevance scoring if smart memory)
        if isinstance(self.memory, SmartConversationMemory):
            context = self.memory.get_context(current_query=prompt)
        else:
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

        # Extract and clean the response text
        response_text = response["choices"][0]["text"].strip()

        # Remove any stop tokens that might have leaked through
        for stop_token in self.stop:
            response_text = response_text.replace(stop_token, "")

        return response_text.strip()
    
    def add_to_memory(self, user_message: str, assistant_response: str, handler: str = None):
        """Add conversation to memory with optional handler info"""
        if isinstance(self.memory, SmartConversationMemory):
            self.memory.add_conversation(user_message, assistant_response, handler=handler)
        else:
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
        
        # Initialize calculator
        self.calculator = Calculator()
        
        # Initialize datetime info
        self.datetime_info = DateTimeInfo()
        
        # Initialize system info
        self.system_info = SystemInfo()

        # Initialize Spotify service (optional - only if credentials are available)
        self.spotify = None
        try:
            self.spotify = SpotifyService()
            logger.info("Spotify service initialized successfully")
        except (ValueError, Exception) as e:
            logger.warning(f"Spotify service not initialized: {e}")
            logger.info("Spotify features will be disabled. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to enable.")

        # Setup hybrid routing system (fast path + LLM fallback)
        self.router = HandlerRegistry()
        
        # Register handlers by priority (highest first)
        self.router.register(WeatherHandler(self.weather, priority=10))
        
        # Register Spotify handler if service is available
        if self.spotify:
            self.router.register(SpotifyHandler(self.spotify, priority=9))
        
        # Register other handlers
        self.router.register(CalculatorHandler(self.calculator, priority=8))
        self.router.register(DateTimeHandler(self.datetime_info, priority=8))
        self.router.register(SystemInfoHandler(self.system_info, priority=7))
        
        logger.info(f"Registered {len(self.router)} handlers")

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
            
            # Add conversation to memory with handler info
            self.llm.add_to_memory(transcription, response_text, handler=handler_name)
            
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