from fastrtc import Stream, ReplyOnPause, ReplyOnStopWords, AlgoOptions, SileroVadOptions
from fastrtc import get_twilio_turn_credentials
from gradio.utils import get_space
from model import VoiceAssistant
from logger import setup_logging

import json
import hydra
from omegaconf import DictConfig, OmegaConf
import logging


from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

@hydra.main(config_path="../cli/conf", config_name="base")
def main(cfg: DictConfig):
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Config: {OmegaConf.to_yaml(cfg)}")
    
    # Initialize models
    voice_assistant = VoiceAssistant(cfg)

    # Create the pause-based handler for normal conversation
    pause_handler = ReplyOnPause(
        voice_assistant.speech_to_speech,
        algo_options=AlgoOptions(
            audio_chunk_duration=cfg.stream.algo_options.audio_chunk_duration,
            started_talking_threshold=cfg.stream.algo_options.started_talking_threshold,
            speech_threshold=cfg.stream.algo_options.speech_threshold,
        ),
        model_options=SileroVadOptions(
            threshold=cfg.stream.model_options.threshold,
            min_speech_duration_ms=cfg.stream.model_options.min_speech_duration_ms,
            max_speech_duration_s=cfg.stream.model_options.max_speech_duration_s,
            min_silence_duration_ms=cfg.stream.model_options.min_silence_duration_ms,
            window_size_samples=cfg.stream.model_options.window_size_samples,
            speech_pad_ms=cfg.stream.model_options.speech_pad_ms,
        ),
        can_interrupt=cfg.stream.can_interrupt,
    )

    # Create the stop word handler for wake word detection
    def on_wake_word_detected(audio):
        # Switch to pause handler after wake word is detected
        stream.handler = pause_handler
        # Process the audio with the pause handler
        return voice_assistant.speech_to_speech(audio)

    stop_word_handler = ReplyOnStopWords(
        on_wake_word_detected,
        stop_words=["computer"],  # Add your desired wake words here
        input_sample_rate=16000,  # Required for stop word detection
        algo_options=AlgoOptions(
            audio_chunk_duration=cfg.stream.algo_options.audio_chunk_duration,
            started_talking_threshold=cfg.stream.algo_options.started_talking_threshold,
            speech_threshold=cfg.stream.algo_options.speech_threshold,
        ),
        model_options=SileroVadOptions(
            threshold=cfg.stream.model_options.threshold,
            min_speech_duration_ms=cfg.stream.model_options.min_speech_duration_ms,
            max_speech_duration_s=cfg.stream.model_options.max_speech_duration_s,
            min_silence_duration_ms=cfg.stream.model_options.min_silence_duration_ms,
            window_size_samples=cfg.stream.model_options.window_size_samples,
            speech_pad_ms=cfg.stream.model_options.speech_pad_ms,
        ),
        can_interrupt=cfg.stream.can_interrupt,
    )

    # Create the stream with the stop word handler initially
    stream = Stream(
        handler=stop_word_handler,
        modality=cfg.stream.modality,
        mode=cfg.stream.mode,
        rtc_configuration=get_twilio_turn_credentials() if get_space() else None,
    )

    # Launch the UI
    #stream.ui.launch()


    app = FastAPI()

    stream.mount(app)


    @app.get("/")
    async def _():
        rtc_config = get_twilio_turn_credentials() if get_space() else None
        html_content = open("/home/vsrinivasan/Projects/assistants/src/index.html").read()
        html_content = html_content.replace("__RTC_CONFIGURATION__", json.dumps(rtc_config))
        return HTMLResponse(content=html_content)

    @app.get("/outputs")
    def _(webrtc_id: str):
        async def output_stream():
            import json

            async for output in stream.output_stream(webrtc_id):
                s = json.dumps(output.args[0])
                yield f"event: output\ndata: {s}\n\n"

        return StreamingResponse(output_stream(), media_type="text/event-stream")
    
    import uvicorn

    uvicorn.run(app, port=7860)
if __name__ == "__main__":
    main()