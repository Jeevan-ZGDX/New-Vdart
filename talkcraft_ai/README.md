# TalkCraft Phase 3 — Real-time AI Conversation Intelligence

A lightweight, CPU-efficient conversational AI system that turns TalkCraft into an interactive communication coach. Users practice speaking with AI agents in real time while TalkCraft continuously evaluates communication quality.

## Features

### 10 Core Capabilities
1. **Real-time AI voice conversation** — Speak naturally with AI agents
2. **AI interviewer simulation** — Practice job interviews
3. **Public speaking practice mode** — Improve presentation skills
4. **Debate/conversation practice mode** — Hone argumentation skills
5. **Follow-up question generation** — AI suggests relevant follow-ups
6. **Conversation memory** — Session-aware context (not persistent)
7. **Real-time communication scoring** — Continuous quality evaluation
8. **Live conversational feedback** — Instant improvement suggestions
9. **Dynamic difficulty adaptation** — Auto-adjusts to your skill level
10. **Topic-based conversation modes** — Structured practice sessions

### 5 AI Modes
| Mode | Description |
|------|-------------|
| **HR Interviewer** | Practice job interviews with structured questions and feedback |
| **Casual Conversation Partner** | Natural everyday conversation practice |
| **Public Speaking Coach** | Structured speaking exercises with detailed feedback |
| **Debate Opponent** | Argumentation and critical thinking practice |
| **Presentation Evaluator** | Full presentation practice with evaluation |

### Real-time Feedback Dimensions
- Grammar quality
- Confidence level
- Eye-contact quality
- Filler-word usage
- Speaking pace
- Clarity score
- Conversation engagement score

## Architecture

```
User Speech / Text
    ↓
Conversation Engine ← → Conversation Memory
    ↓
AI Response Generator ← → LLM API (streaming)
    ↓
Text-to-Speech (optional)
    ↓
Feedback Engine ← → Scoring Engine ← Phase 1 & 2
    ↓
Live Dashboard (Streamlit)
```

### Pipeline (Thread/Queue Based)
```
Transcription Queue → AI Request Queue → AI Response Queue → TTS Queue
      ↓                     ↓                    ↓               ↓
 Transcription       LLM Request          Response           Speech
 Worker              Worker               Worker             Worker
```

## Tech Stack

- **Python 3.10+**
- **OpenAI-compatible LLM API** (Ollama, OpenAI, Together, Groq, etc.)
- **Streamlit** — Real-time dashboard
- **FastAPI** — WebSocket + REST server
- **pyttsx3** — Offline text-to-speech
- **threading + queue** — Non-blocking pipeline
- **requests** — Lightweight HTTP client

### CPU Optimization

- Tiny LLM models (1B-3B parameters) via Ollama
- Streaming responses for low latency
- Queue-based non-blocking architecture
- Minimal dependency footprint
- Optional TTS (disable for lower CPU usage)
- No GPU required

## Performance Targets

| Metric | Target |
|--------|--------|
| Response latency | < 3 seconds (streaming) |
| Pipeline throughput | < 500ms processing |
| RAM usage | < 500 MB (without local LLM) |
| CPU usage | < 30% on i3 processor |
| Dashboard refresh | 250ms intervals |

## Project Structure

```
talkcraft-ai/
├── __init__.py
├── main.py              # Entry point (dashboard/server/console)
├── server.py            # FastAPI + WebSocket server
├── requirements.txt
├── README.md
├── config.json          # Auto-generated configuration
│
├── conversation/        # Conversation engine
│   ├── engine.py        # Main orchestrator
│   ├── memory.py        # Session conversation memory
│   ├── modes.py         # AI mode personalities
│   └── difficulty.py    # Dynamic difficulty adaptation
│
├── agents/              # AI agent components
│   ├── llm_client.py    # OpenAI-compatible API client
│   ├── response_generator.py  # Streaming response handler
│   └── followup_generator.py  # Follow-up question generation
│
├── audio/
│   └── tts_engine.py    # pyttsx3 TTS with queue
│
├── scoring/
│   ├── conversation_scorer.py  # Multi-dimensional scoring
│   ├── engagement.py    # Engagement analysis
│   └── clarity.py       # Clarity analysis
│
├── feedback/
│   └── live_feedback.py # Real-time feedback engine
│
├── realtime/
│   ├── queues.py        # Monitored thread-safe queues
│   └── pipelines.py     # Queue/thread conversation pipeline
│
├── dashboard/
│   └── app.py           # Streamlit dashboard
│
└── utils/
    ├── config.py        # Configuration management
    └── logger.py        # Logging setup
```

## Setup

### Prerequisites
- Python 3.10 or higher
- An LLM API endpoint (recommended: [Ollama](https://ollama.ai) for local)

### Quick Start

```bash
# 1. Install dependencies
cd talkcraft-ai
pip install -r requirements.txt

# 2. (Optional) Install and start Ollama for local LLM
# https://ollama.ai
# ollama pull llama3.2:1b
# ollama serve

# 3. Start the dashboard
python main.py

# Or start the server
python main.py server --port 8002

# Or use console mode
python main.py console
```

### Configuration

Edit `config.json` (auto-generated on first run) or set environment variables:

```json
{
  "llm": {
    "api_base": "http://localhost:11434/v1",
    "api_key": "sk-placeholder",
    "model": "llama3.2:1b",
    "temperature": 0.7,
    "max_tokens": 256,
    "streaming": true
  },
  "tts": {
    "enabled": true,
    "rate": 180,
    "volume": 0.9
  }
}
```

### LLM Provider Options

| Provider | API Base | Model Example |
|----------|----------|---------------|
| **Ollama** (local) | `http://localhost:11434/v1` | `llama3.2:1b`, `phi:2.7b` |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` |
| **Groq** | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` |
| **Together** | `https://api.together.xyz/v1` | `mistralai/Mixtral-8x7B-Instruct-v0.1` |

## Usage Modes

### Dashboard Mode (Default)
Full Streamlit interface with conversation transcript, metrics, feedback, and mode selection.

```bash
python main.py
# Opens at http://localhost:8502
```

### Server Mode
WebSocket + REST API server for integration with the existing TalkCraft frontend.

```bash
python main.py server --port 8002
```

### Console Mode
Simple terminal-based conversation practice.

```bash
python main.py console
```

## Integration with Phase 1 & 2

This module is designed to work alongside the existing TalkCraft components:

- **Phase 1 (talkcraft/)** : Speech-to-text, grammar, fillers, pace analysis
- **Phase 2 (talkcraft-backend/)** : Face/eye/hand analysis, confidence scoring
- **Phase 3 (talkcraft-ai/)** : AI conversation engine, TTS, conversation scoring

Phase 3 can consume analysis data from Phases 1 and 2 to provide richer feedback. It also operates standalone with text input.

## Real-time Feedback

The feedback engine evaluates multiple dimensions with configurable cooldowns:

- **Grammar**: Sentence structure and correctness
- **Fillers**: Filler word frequency and impact
- **Pace**: Speaking speed appropriateness
- **Engagement**: Response depth and interactivity
- **Clarity**: Sentence clarity and vocabulary richness
- **Confidence**: Projected confidence level
- **Eye Contact**: Gaze maintenance (from Phase 2)

## Dynamic Difficulty

The system automatically adapts to user performance:

| Level | Description |
|-------|-------------|
| **Beginner** | Simple vocabulary, encouraging tone, straightforward questions |
| **Intermediate** | Moderate complexity, normal conversation |
| **Advanced** | Sophisticated vocabulary, analytical questions |
| **Expert** | Challenging arguments, critical thinking required |

Difficulty increases after 5 consecutive good responses and decreases after 3 poor ones.

## License

MIT License — See root LICENSE file.
