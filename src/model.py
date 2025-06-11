import numpy as np
from omegaconf import DictConfig

from fastrtc import get_stt_model, get_tts_model, KokoroTTSOptions, AdditionalOutputs
from fastrtc_whisper_cpp import get_stt_model as get_stt_model_whisper_cpp
from llama_cpp import Llama

from util import timer

class STT:
    def __init__(self, stt_model: str = "moonshine/base"):
        #self.stt_model = get_stt_model(model=stt_model)
        self.stt_model = get_stt_model_whisper_cpp(model=stt_model)

    @timer
    def speech_to_text(self, audio: tuple[int, np.ndarray]):
        return self.stt_model.stt(audio)

class TTS:
    def __init__(self, tts_model: str = "kokoro", 
                 voice: str = "af_heart", 
                 speed: float = 1.0, 
                 lang: str = "en-us",
                 stream: bool = True):
        self.tts_model = get_tts_model(model=tts_model)
        self.options = KokoroTTSOptions(voice=voice, speed=speed, lang=lang)

    @timer
    def text_to_speech(self, text: str):
        return self.tts_model.tts(text, options=self.options)

class LLM:
    def __init__(self, model_path: str, n_ctx: int):
        self.llm = Llama(model_path=model_path, 
                         n_ctx=n_ctx,
                         n_threads=16,
                         n_batch=16,
                         n_gpu_layers=0)
        
    @timer
    def generate(self, prompt: str):
        text_prompt = (
            f"<|system|>\nYou are a helpful assistant.<|end|>\n"
            f"<|user|>\n{prompt}\n<|end|>\n"
            f"<|assistant|>\n"
        )
        response = self.llm(text_prompt, 
                            temperature=0.2, 
                            top_p=0.9, 
                            repeat_penalty=1.2, 
                            max_tokens=50,
                            stop=["Q:", "\n"],
                            echo=False)
        return response["choices"][0]["text"].strip()
        
class VoiceAssistant:
    def __init__(self, cfg: DictConfig):
        # Initialize models
        self.stt = STT(cfg.stt.model)
        self.tts = TTS(cfg.tts.model, cfg.tts.voice, cfg.tts.speed, cfg.tts.lang)
        self.llm = LLM(cfg.llm.model_path, cfg.llm.n_ctx)
        self.latest_transcription = None
        self.latest_response = None

    def speech_to_speech(self, audio: tuple[int, np.ndarray]):
        # Convert audio to text using Moonshine
        transcription = self.stt.speech_to_text(audio)
        self.latest_transcription = transcription
        print(f"Transcription: {transcription}")

        yield AdditionalOutputs({"role": "user", "content": transcription})
     

        if transcription not in ["", " ", None]:
            # LLM generate response
            response_text = self.llm.generate(transcription)
            self.latest_response = response_text
            print(f"Response: {response_text}")
            
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