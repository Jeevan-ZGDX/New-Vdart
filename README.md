# TalkCraft — Real-time AI Communication Coach

A multimodal communication coaching system with three phases:

## Phase 1: `talkcraft/` — Speech Analysis
- Real-time speech-to-text (faster-whisper)
- Grammar correction (LanguageTool + regex)
- Filler-word detection
- Speaking pace analysis
- Real-time feedback dashboard

## Phase 2: `talkcraft-backend/` — Vision Analysis
- Face analysis (MediaPipe FaceLandmarker)
- Eye-contact tracking
- Posture analysis
- Hand gesture tracking (MediaPipe GestureRecognizer)
- Confidence scoring
- Multimodal feedback

## Phase 3: `talkcraft_ai/` — AI Conversation Intelligence (NEW)
- Real-time AI voice conversation
- 5 AI modes: HR Interviewer, Casual Conversation Partner, Public Speaking Coach, Debate Opponent, Presentation Evaluator
- Session conversation memory
- Real-time communication scoring
- Live conversational feedback
- Dynamic difficulty adaptation
- Topic-based conversation modes
- Follow-up question generation
- Lightweight TTS (pyttsx3)
- Queue/thread-based non-blocking architecture
- CPU-optimized for i3 + 8GB RAM

## Frontend: `talkcraft-frontend/` — React Dashboard
- Next.js/React unified dashboard
- Dual WebSocket connections to speech and vision servers
- Real-time metric display and feedback

## Quick Start

```bash
# Phase 1 - Speech Analysis
cd talkcraft
pip install -r requirements.txt
python main.py

# Phase 2 - Vision Analysis (separate terminal)
cd talkcraft-backend
pip install -r requirements.txt
python main.py

# Phase 3 - AI Conversation (separate terminal)
cd talkcraft_ai
pip install -r requirements.txt
python main.py          # Streamlit dashboard
python main.py console  # Terminal mode
python main.py server   # FastAPI server

# Frontend (separate terminal)
cd talkcraft-frontend
npm install
npm run dev
```

See individual README files in each module for detailed setup instructions.
