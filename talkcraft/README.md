# TalkCraft - Real-Time Communication Coach

TalkCraft is a lightweight, real-time AI-powered speech analysis system that provides instant feedback on speaking pace, filler word usage, and grammar. Designed to run efficiently on low-end hardware (Intel i3, 8GB RAM, no GPU).

## Architecture

### Real-Time Pipeline

```
Microphone Input
        ↓
Audio Stream Buffer  (circular buffer, 2s chunks)
        ↓
Chunk Processor  (non-blocking queue put)
        ↓
Speech-to-Text Engine  (faster-whisper tiny.en)
        ↓
Async Analysis Queue
    ├── Grammar Analysis  (LanguageTool / heuristic fallback)
    ├── Filler Detection  (regex-based pattern matching)
    ├── Speaking Pace     (WPM calculation with sliding window)
        ↓
Feedback Engine  (rule-based, cooldown-aware)
        ↓
Live Dashboard Updates  (Streamlit, 250ms refresh)
```

### Threading Model

| Thread | Role | Queue |
|--------|------|-------|
| Main | UI rendering (Streamlit) | N/A |
| Microphone | Audio capture → audio_queue | audio_queue |
| Transcription | Transcribe audio → transcription_queue | transcription_queue |
| Analysis | Analyze text → analysis_queue | analysis_queue |
| Feedback | Generate feedback → feedback_queue | feedback_queue |
| UI Refresh | Update shared state → dashboard | ui_update_queue |

### Queue Architecture (Producer-Consumer)

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Mic Thread   │────▶│ Audio Queue      │────▶│ Transcription   │
│ (Producer)   │     │ (maxsize=10)     │     │ Worker (Consumer)│
└──────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Transcription    │
                                              │ Queue            │
                                              │ (maxsize=10)     │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Analysis Worker  │
                                              │ (Grammar/Filler/ │
                                              │  Pace)           │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Analysis Queue   │
                                              │ (maxsize=20)     │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Feedback Worker  │
                                              │ (Rule Engine)    │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Feedback Queue   │
                                              │ (maxsize=20)     │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ UI Refresh Worker│
                                              │ → Dashboard      │
                                              └──────────────────┘
```

## Setup

### Prerequisites

- Python 3.11 or higher
- 8GB RAM minimum
- Microphone
- Windows, macOS, or Linux

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd talkcraft

# Create virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### CPU Optimization Notes

The system is configured for CPU-only inference:

- **Model**: `tiny.en` (39M parameters) — the smallest Whisper variant
- **Compute type**: `int8` — quantized inference reduces memory bandwidth
- **Beam size**: 1 — greedy decoding for speed
- **VAD filter**: enabled — skips silent audio chunks
- **Thread count**: 4 CPU threads for inference

To further reduce CPU usage:
```bash
# Use even smaller model (less accurate)
# Edit talkcraft/utils/config.py → model_size = "tiny"

# Increase chunk size (less frequent transcription)
# Edit chunk_duration to 3.0 seconds
```

## Usage

```bash
# Start TalkCraft
python -m talkcraft.main

# Or directly with Streamlit
streamlit run talkcraft/ui/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`.

## Real-Time Streaming Explained

1. **Audio Capture**: sounddevice captures microphone input in 1024-sample blocks via a non-blocking callback.

2. **Chunk Assembly**: Blocks are accumulated into 2-second chunks (32,000 samples at 16kHz) using a float32 buffer.

3. **Queue Dispatch**: Each complete chunk is placed on the audio queue. If the queue is full, the chunk is dropped (overflow protection).

4. **Transcription**: The transcription worker reads chunks from the queue and runs faster-whisper inference. The tiny.en model processes a 2-second chunk in ~500ms on an i3 CPU.

5. **Parallel Analysis**: The transcribed text is dispatched to three analysis modules running sequentially in a single worker thread (to avoid contention):
   - Grammar: LanguageTool API or regex fallback
   - Fillers: Regex matching against a configurable word list
   - Pace: WPM calculation with configurable min/max thresholds

6. **Feedback Generation**: A rule-based engine evaluates analysis results and produces prioritized feedback messages with cooldown periods to avoid spam.

7. **UI Update**: A dedicated worker polls feedback and transcription queues, writing to a thread-safe shared state that Streamlit reads on its 250ms refresh cycle.

## Latency Targets

| Stage | Target | Typical |
|-------|--------|---------|
| Audio chunking | 2-3s | 2s |
| Speech transcription | <2s | 0.5-1.5s |
| Feedback generation | <3s from speech | ~1.5-2.5s |
| UI refresh | Near-instant | 250ms |

## Performance on Low-End Hardware

On an Intel i3 + 8GB RAM:
- CPU: ~30-50% during active speech
- RAM: ~1.5-2GB (mostly the Whisper model)
- Latency: ~1-2s end-to-end

## Module Overview

```
talkcraft/
├── audio/
│   ├── microphone.py       # Microphone capture and chunk assembly
│   ├── stream_handler.py   # sounddevice InputStream wrapper
│   └── audio_buffer.py     # Thread-safe circular buffer
├── transcription/
│   ├── whisper_engine.py   # faster-whisper singleton wrapper
│   └── transcription_worker.py  # Queue-based transcription thread
├── analysis/
│   ├── grammar_checker.py  # LanguageTool / regex fallback
│   ├── filler_detector.py  # Regex-based filler word detection
│   └── speaking_pace.py    # WPM calculation with sliding window
├── realtime/
│   ├── queues.py           # Monitored thread-safe queues
│   ├── workers.py          # Worker thread implementations
│   └── event_manager.py    # Pub/sub event system
├── feedback/
│   └── feedback_engine.py  # Rule-based feedback generation
├── ui/
│   └── dashboard.py        # Streamlit real-time dashboard
├── utils/
│   ├── config.py           # Configuration dataclasses
│   └── logger.py           # Logging setup
├── main.py                 # Application entry point
└── requirements.txt        # Python dependencies
```

## Configuration

Edit `talkcraft/utils/config.py` or create a JSON config:

```python
# Key settings
config.audio.chunk_duration = 2.0     # seconds per chunk
config.audio.sample_rate = 16000      # Hz
config.transcription.model_size = "tiny.en"
config.transcription.compute_type = "int8"
config.analysis.max_words_per_minute = 160.0
config.analysis.min_words_per_minute = 100.0
```

## Troubleshooting

### Microphone not detected
```bash
# List audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"

# Set device in config
config.audio.device = 1  # index from above list
```

### High CPU usage
- Reduce model size to `tiny` (not `tiny.en`)
- Increase chunk duration to 3 seconds
- Set `vad_filter = True` to skip silence

### Out of memory
- Close other applications
- Reduce queue maxsizes
- Use `compute_type = "int8"` (default)

### No transcription
- Check microphone permissions
- Verify sounddevice can access the mic
- Check logs: `talkcraft.log`

### LanguageTool not available
Grammar checking falls back to a regex-based heuristic. To install LanguageTool:
```bash
pip install language-tool-python
# First run downloads the LanguageTool server jar (~200MB)
```

## License

MIT
