## Building a Private, Offline Voice Assistant on a CPU-Only Edge Device (Ryzen 7)

This post describes how to build a local, privacy-preserving voice assistant that runs fully offline on an AMD Ryzen 7 without a GPU. It uses whisper.cpp for STT, llama.cpp with Mistral 7B Instruct for the LLM, and Kokoro (ONNX) for TTS. We’ll cover the architecture, why you need a router, model choices tailored to CPU-only hardware, and why STT is still the most failure-prone step.

### Why local and offline?
- **Privacy**: Audio stays on the device.
- **Latency**: No network round trips.
- **Cost and control**: No API bills or vendor lock-in.
- **Resilience**: Works without internet.

## Hardware Profile

- **CPU**: AMD Ryzen 7 (8C/16T class), AVX2-capable
- **RAM**: 16–32 GB recommended
- **Disk**: NVMe SSD
- **Audio I/O**: USB mic (cardioid) + speakers/headphones
- **OS/Audio**: Linux with PipeWire/PulseAudio

All inference runs on CPU with quantized models and efficient runtimes.

## System Architecture

```
[mic/audio]
  → [wake word + VAD]
  → [STT: whisper.cpp]
  → [Router: intent + tool selection]
  → [LLM: llama.cpp + Mistral 7B Instruct]
  → [TTS: Kokoro ONNX]
  → [speaker/audio out]
```

- **STT**: Streams partial transcripts to keep latency low.
- **Router**: Classifies intent, picks the right skill/tool, and applies safety checks.
- **LLM**: Generates responses and orchestrates tools.
- **TTS**: Speaks the response, ideally streaming.

### Core Features

- **Wake word + VAD** for reliability and CPU efficiency
- **Streaming STT and TTS** for responsiveness
- **Barge-in** so users can interrupt TTS
- **Router-led skills**: timers, weather, local search, system controls, RAG
- **Safety**: confirmations on low-confidence transcripts or sensitive actions
- **Multi-language** (model-dependent)

## Why You Need a Router

- **Intent routing**: Direct structured commands (timers, system control) to deterministic handlers; send open Q&A to the LLM.
- **Safety and confirmations**: Gate destructive actions behind explicit confirmations when STT confidence or intent certainty is low.
- **Model/tool selection**: Adjust prompts or toolchains based on task complexity.
- **Fallbacks**: Route low-confidence transcripts to clarifications.

Practically, combine:
- **Rules** for fast, predictable triggers
- **Lightweight classifier** (embeddings + thresholds)
- **LLM-mediated routing** as a last resort

## Component Choices for CPU-Only (Your Stack)

### STT: whisper.cpp (via fastrtc_whisper_cpp), English small.en
- **Why it fits Ryzen 7**:
  - The `small.en` model is a strong speed/accuracy compromise on CPU.
  - whisper.cpp is optimized (GGML/GGUF), supports streaming and low latency.
  - Works well with lightweight VAD and wake-word detectors.
- **Common add-ons**:
  - VAD: Silero or WebRTC VAD
  - Wake word: openWakeWord
  - Domain boosts or LM rescoring (if your wrapper supports it) for repeated names/commands

### LLM: llama.cpp + Mistral 7B Instruct (Q4_K_M GGUF)
- **Why it fits Ryzen 7**:
  - Mistral 7B Instruct is a capable general assistant in the 7B class.
  - The Q4_K_M quantization balances quality and speed for CPU-only inference.
  - llama.cpp and llama-cpp-python offer great CPU efficiency and flexible batching/threads.
- **On parameter count**:
  - Models **>4B parameters** generally show a notable jump in “intelligent” responses vs smaller ones on CPU. At 7B, Mistral Instruct is a solid sweet spot.
- **Tuning tips**:
  - Use Mistral’s instruction format (e.g., [INST]) or set the runtime’s chat template.
  - Increase `n_threads` to match CPU cores; experiment with `n_batch` for throughput.
  - Keep prompts concise for command skills; allow longer generations for Q&A.

### TTS: Kokoro (ONNX) via fastrtc
- **Why it fits Ryzen 7**:
  - Fast CPU synthesis with clear voices; minimal overhead.
  - ONNX runtime delivers low latency and predictable performance.
  - TTS quality is mature and largely “solved” for single-speaker voices, so Kokoro performs reliably offline.

## Example Config (reflecting your setup)

```yaml
stt:
  model: "small.en"        # whisper.cpp via fastrtc_whisper_cpp

tts:
  model: "kokoro"          # Kokoro ONNX via fastrtc
  voice: "af_heart"
  speed: 1.0
  lang: "en-us"

llm:
  model_path: "models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"  # llama.cpp
  n_ctx: 2048
  temperature: 0.2
  top_p: 0.9
  repeat_penalty: 1.2
  max_tokens: 128
```

Notes:
- Consider bumping `max_tokens` above 25 for more helpful answers (128–256).
- If memory and latency allow, `n_ctx: 4096` yields longer conversations.

## Latency and Resource Targets (CPU-only Ryzen 7)

- **Wake**: <150 ms typical
- **STT first partial**: 200–500 ms; short utterances ~0.7–1.5 s
- **LLM first tokens**: 200–700 ms; 10–20 tok/s on 7B Q4 with tuned batch/threads
- **TTS start**: 100–300 ms; stream playback early
- **RAM**: 7B Q4_K_M ~4–6 GB; `small.en` STT ~1–2 GB; leave headroom

## Why STT Fails the Most

- **Human variability**: Accents, disfluencies, and coarticulation are hard.
- **Environment**: Room acoustics and noise degrade signal quality.
- **Segmentation**: VAD boundaries and overlap handling can drop or merge words.
- **Rare tokens**: Names, addresses, niche jargon need domain adaptation.
- **Confidence**: Acting on low-confidence transcripts can be risky; not acting feels unresponsive.

LLMs do degrade with heavy quantization, but choosing **>4B parameters** (like Mistral 7B Q4) preserves instruction-following and coherence on CPU. TTS is not interpreting human input; with Kokoro, synthesis is fast and stable—hence it “just works” far more often.

## Practical Tuning for Your Stack

- **Audio chain**:
  - Use a decent USB mic; apply RNNoise/SpeexDSP if your room is noisy.
  - Tune VAD/wake-word thresholds to your environment.
- **STT**:
  - Keep streaming enabled for responsiveness.
  - Consider phrase boosts or rescoring for personal names and recurring terms.
  - Add confirmations for sensitive actions when STT confidence is low.
- **Router**:
  - Separate “control” intents from chat.
  - Use thresholds for intent certainty; add clarify prompts on borderline cases.
- **LLM (llama.cpp + Mistral 7B)**:
  - Use the Mistral instruction template; remove overly aggressive stop tokens like "\n".
  - Set `n_threads = os.cpu_count()`; experiment with `n_batch` (e.g., 64–256) for throughput.
  - Keep control prompts short and structured; rely on tools for math/dates/system actions.
- **TTS (Kokoro)**:
  - Stream output as it’s generated.
  - Cache frequent phrases (alarms, confirmations).

## Alternatives and Trade-offs

- **STT**: Faster-Whisper (CTranslate2) for additional speed; Vosk/Kaldi for classical pipelines with domain LM.
- **LLM**: If latency is high, try a strong 4–5B model (e.g., Phi-3.5 Mini) at Q4; if quality is lacking and RAM allows, try Q5_K_M or a better-tuned 7B.
- **TTS**: Piper for ultra-low-latency synthesis and a large voice catalog; Mimic3 as another CPU-first option.

## Closing Thoughts

With whisper.cpp (`small.en`) for STT, llama.cpp + Mistral 7B Instruct (Q4_K_M) for the LLM, and Kokoro ONNX for TTS, a Ryzen 7 can deliver a practical, fully offline assistant. Expect most issues to trace back to the audio/STT layer; invest in mic quality, environment tuning, and router safeguards. The LLM remains capable at 7B Q4 on CPU, and TTS is fast and reliable—together delivering a smooth private voice experience without a GPU.