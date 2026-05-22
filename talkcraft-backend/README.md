# TalkCraft - Phase 2: Real-Time Multimodal Communication Coach

A lightweight, CPU-friendly real-time communication analysis system for low-end laptops (i3 CPU, 8GB RAM, no GPU).

## Features

### Phase 1 (Speech Analysis)
- Real-time speech-to-text
- Grammar correction
- Filler-word detection
- Speaking pace analysis
- Live feedback dashboard

### Phase 2 (Vision Analysis) - NEW
- Continuous webcam streaming (10-15 FPS)
- Real-time face detection and analysis
- Eye-contact percentage tracking
- Head posture analysis (pitch, yaw, roll)
- Basic hand gesture tracking
- Real-time confidence scoring
- Multimodal communication feedback
- Live webcam overlay visualization

## Architecture

```
Webcam → MediaPipe → Face/Gesture Analysis → Confidence Engine → Feedback Engine → Live Dashboard
                                    ↓
                              Speech Data (Phase 1)
                                    ↓
                          Multimodal Fusion → WebSocket → Frontend
```

## Project Structure

```
talkcraft-backend/
├── main.py                      # Entry point and backend orchestrator
├── server.py                    # WebSocket server for frontend integration
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── core/
│   ├── pipeline.py              # Thread-safe processing pipeline
│   ├── webcam.py                # Webcam capture with frame queue
│   └── orchestrator.py          # Main multimodal orchestrator
├── analyzers/
│   ├── face_analyzer.py         # Eye contact & head posture analysis
│   └── hand_analyzer.py         # Hand gesture tracking
├── engines/
│   ├── confidence_engine.py     # Multimodal confidence scoring
│   └── feedback_engine.py       # Real-time feedback generation
├── dashboard/
│   └── app.py                   # Streamlit live dashboard
└── utils/                       # Utility modules
```

## Tech Stack

- **Python 3.10+**
- **OpenCV** - Webcam capture and image processing
- **MediaPipe** - Face mesh and hand tracking (CPU-optimized)
- **Streamlit** - Live dashboard visualization
- **WebSockets** - Real-time communication with frontend
- **threading/queue** - Non-blocking pipeline architecture

## Performance Constraints

- CPU-only inference (no GPU required)
- Low latency (<100ms processing)
- Low RAM usage (<500MB)
- 10-15 FPS webcam processing
- Queue/thread-based architecture
- Non-blocking real-time pipeline

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Webcam (built-in or external)
- 8GB RAM minimum
- i3 CPU or equivalent

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Streamlit Dashboard (Recommended)

Run the standalone dashboard with webcam overlay:

```bash
streamlit run dashboard/app.py
```

The dashboard will open at `http://localhost:8501`

### Option 2: Backend + WebSocket Server

Run the backend with WebSocket server for frontend integration:

```bash
python server.py
```

This starts:
- Webcam processing pipeline
- WebSocket server on `ws://localhost:8765`
- Real-time broadcast to connected clients

### Option 3: Backend Only (CLI)

Run the backend without dashboard:

```bash
python main.py --webcam 0 --fps 12
```

Options:
- `--webcam`: Webcam device index (default: 0)
- `--fps`: Target processing FPS (default: 12)
- `--dashboard`: Launch Streamlit dashboard

### Option 4: Integrated with Phase 1 Frontend

1. Start the Phase 1 frontend:
```bash
cd talkcraft-frontend
npm run dev
```

2. Start the Phase 2 WebSocket server:
```bash
cd talkcraft-backend
python server.py
```

3. Update frontend WebSocket URL to include multimodal data

## API Reference

### WebSocket Messages

**Client → Server:**
```json
{
  "command": "update_speech",
  "data": {
    "current_wpm": 120,
    "filler_rate": 0.05,
    "grammar_errors": 0,
    "transcription": "Hello world"
  }
}
```

**Server → Client (Broadcast):**
```json
{
  "type": "multimodal_update",
  "face_detected": true,
  "eye_contact_score": 0.85,
  "gaze_direction": "center",
  "posture_stability": 0.75,
  "head_pitch": 2.3,
  "head_yaw": -1.5,
  "head_roll": 0.8,
  "hands_detected": 1,
  "hand_activity": 0.45,
  "gestures": [{"hand": "Right", "gesture": "open_palm"}],
  "confidence_score": 0.78,
  "confidence_level": "good",
  "feedback": [{"message": "Great eye contact!", "priority": 1}],
  "session_duration": 45.2
}
```

## Confidence Scoring

The confidence score is calculated using weighted components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Eye Contact | 30% | Gaze direction and camera focus |
| Posture Stability | 25% | Head movement steadiness |
| Speech Pace | 20% | Words per minute (optimal: 100-150) |
| Filler Rate | 15% | Frequency of um/uh/like |
| Hand Gesture | 10% | Natural hand movement activity |

**Confidence Levels:**
- Excellent: ≥85%
- Good: ≥70%
- Moderate: ≥50%
- Needs Improvement: ≥30%
- Low: <30%

## Feedback Rules

The system provides real-time feedback based on:
- Eye contact quality
- Head posture stability
- Speaking pace
- Filler word frequency
- Hand gesture activity
- Overall confidence score

Feedback is debounced with cooldown periods to avoid overwhelming the user.

## CPU Optimization

- MediaPipe models run on CPU with optimized inference
- Frame resolution capped at 640x480
- Processing pipeline uses non-blocking queues
- Threading prevents UI blocking
- Frame dropping when queue is full
- Efficient landmark-based analysis (no heavy CNNs)

## Troubleshooting

### Webcam not detected
- Check device index: `python main.py --webcam 1`
- Ensure no other application is using the webcam
- On Windows, check Privacy settings for camera access

### Low FPS
- Reduce target FPS: `python main.py --fps 10`
- Close other CPU-intensive applications
- Check if MediaPipe is using CPU correctly

### Streamlit dashboard not loading
- Ensure port 8501 is not in use
- Try: `streamlit run dashboard/app.py --server.port 8502`

### WebSocket connection refused
- Ensure server.py is running
- Check firewall settings for port 8765

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
