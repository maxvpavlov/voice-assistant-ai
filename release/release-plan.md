# Release Plan: Unified Voice Assistant Script

## Overview

Create a **single, production-ready script** (`voice-part.py`) that handles the complete voice interaction pipeline for cross-host orchestration demos.

## Use Case: Cross-Host Voice Orchestration Demo

### Host 1 (Raspberry Pi or Mac): Voice Input
```
voice-part.py → Wake Word Training (if needed)
             → Wake Word Detection (always listening)
             → Voice Recognition (after wake word detected)
             → Send transcript to Host 2 via HTTP/TCP
```

### Host 2 (Inference Server): AI Processing
```
Receives transcript from Host 1
Processes with LLM/AI model
Returns response
```

## Unified Script: `voice-part.py`

### Design Philosophy
- **Single file** - One script to rule them all
- **Stateful** - Remembers training, resumes automatically
- **Zero-config** - Works out of box with sensible defaults
- **Production-ready** - Robust error handling, logging
- **Demo-friendly** - Clear console output, visual feedback

### Core Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INITIALIZATION                                           │
│    Check for existing wake word model                       │
│    ├─ Found? → Load and start detection                     │
│    └─ Not found? → Guide through training                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. WAKE WORD DETECTION (Always On)                          │
│    Listen for configured wake word                          │
│    Visual indicator: "● Listening for 'hey edge'..."        │
└─────────────────────────────────────────────────────────────┘
                            ↓ (Wake word detected!)
┌─────────────────────────────────────────────────────────────┐
│ 3. VOICE RECOGNITION (Activated)                            │
│    Start Vosk/Whisper speech recognition                    │
│    Visual indicator: "🎙️ Listening... (speak now)"         │
│    Accumulate transcript in real-time                       │
│    Monitor for silence (3s timeout)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓ (Silence detected)
┌─────────────────────────────────────────────────────────────┐
│ 4. SEND TO INFERENCE HOST                                   │
│    POST transcript to configured endpoint                   │
│    Format: {"transcript": "...", "timestamp": "..."}        │
│    Handle response (optional display)                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
           Return to step 2 (Wake Word Detection)
```

## Component Architecture

### State Management
```python
# .voice-assistant-state.json
{
  "wake_word": "hey edge",
  "model_path": "models/hey_edge_v0.1.onnx",
  "model_trained": true,
  "last_training": "2025-11-15T12:00:00",
  "inference_endpoint": "http://192.168.1.100:8000/process",
  "recognition_engine": "vosk",  # or "whisper"
  "silence_timeout": 3.0
}
```

### Module Integration

#### 1. Wake Word Detection
- **Reuse**: Existing `WakeWordDetector` class
- **Source**: `src/voice_assistant/wake_word_detector.py`
- **Changes**: None needed, already production-ready

#### 2. Model Training
- **Reuse**: `train-full-model.py` logic
- **Integration**: Inline functions for recording + training
- **Simplification**: Remove CLI arguments, use state file

#### 3. Voice Recognition (NEW)
- **Engine**: Vosk (recommended for Raspberry Pi)
- **Alternatives**: Whisper (better accuracy, more resources)
- **Features**:
  - Real-time streaming recognition
  - Silence detection (VAD - Voice Activity Detection)
  - English language model
  - Offline operation

#### 4. Network Communication (NEW)
- **Protocol**: HTTP POST (simple, debuggable)
- **Fallback**: TCP socket (lower latency)
- **Format**: JSON
- **Retry logic**: 3 attempts with exponential backoff

## Voice Recognition Engine Comparison

### Option 1: Vosk (RECOMMENDED for Raspberry Pi)

**Pros:**
- ✅ Very lightweight (~50MB model)
- ✅ Works great on Raspberry Pi (low CPU/RAM)
- ✅ Real-time streaming
- ✅ Built-in VAD (silence detection)
- ✅ 100% offline
- ✅ Python bindings excellent
- ✅ Active development

**Cons:**
- ⚠️ Lower accuracy than Whisper
- ⚠️ Limited punctuation

**Performance:**
- Raspberry Pi 5: 0.5x - 1.0x real-time (fast enough!)
- M4 Mac: 5x+ real-time
- RAM: ~100MB
- Model size: 40MB (small) to 1.8GB (large)

**Installation:**
```bash
pip install vosk
# Download model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/
```

### Option 2: Whisper (Better accuracy, more resources)

**Pros:**
- ✅ State-of-the-art accuracy
- ✅ Excellent punctuation
- ✅ Multiple languages
- ✅ OpenAI quality

**Cons:**
- ❌ Slower on Raspberry Pi (1-3s latency)
- ❌ Larger model (~1-3GB)
- ❌ Higher RAM usage (~500MB-2GB)
- ⚠️ Batch processing (not true streaming)

**Performance:**
- Raspberry Pi 5: 0.1x - 0.3x real-time (too slow for real-time)
- M4 Mac: 2x - 5x real-time
- Requires: `pip install openai-whisper`

### Option 3: faster-whisper (Compromise)

**Pros:**
- ✅ 4x faster than Whisper
- ✅ Good accuracy
- ✅ Quantized models available

**Cons:**
- ⚠️ Still slower than Vosk on Pi
- ⚠️ More RAM than Vosk

**Recommendation:** Vosk for Raspberry Pi, Whisper for Mac demos

## Implementation Plan

### Phase 1: Core Script Structure ✓
```python
#!/usr/bin/env python3
"""
voice-part.py - Unified Voice Assistant

Complete voice pipeline:
- Wake word training (guided, first-run)
- Wake word detection (always on)
- Voice recognition (activated by wake word)
- Network transmission (to inference host)
"""

class VoiceAssistant:
    def __init__(self, state_file=".voice-assistant-state.json"):
        self.state = self.load_state()
        self.wake_detector = None
        self.speech_recognizer = None
        self.is_listening_for_speech = False

    def load_state(self): ...
    def save_state(self): ...

    def ensure_model_trained(self): ...  # Train if needed
    def start_wake_detection(self): ...   # Always listening
    def start_speech_recognition(self): ... # After wake word
    def send_to_inference(self, transcript): ... # Network

    def run(self): ...  # Main loop
```

### Phase 2: Wake Word Integration ✓
- Import existing `WakeWordDetector`
- Import training functions from `train-full-model.py`
- Check state file for existing model
- Guide training if needed
- Start detection loop

### Phase 3: Vosk Integration (NEW)
```python
import vosk
import json
import queue
import sounddevice as sd

class VoskRecognizer:
    def __init__(self, model_path="models/vosk-model-small-en-us-0.15"):
        self.model = vosk.Model(model_path)
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        self.audio_queue = queue.Queue()

    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        self.audio_queue.put(bytes(indata))

    def recognize_stream(self, silence_timeout=3.0):
        """Recognize speech until silence detected"""
        transcript = []
        last_speech_time = time.time()

        with sd.RawInputStream(samplerate=16000, blocksize=8000,
                               dtype='int16', channels=1,
                               callback=self.audio_callback):
            while True:
                data = self.audio_queue.get()

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    if result.get("text"):
                        transcript.append(result["text"])
                        last_speech_time = time.time()

                # Check for silence
                if time.time() - last_speech_time > silence_timeout:
                    break

        return " ".join(transcript)
```

### Phase 4: Network Communication (NEW)
```python
import requests
import socket
import json

class InferenceClient:
    def __init__(self, endpoint="http://localhost:8000/process"):
        self.endpoint = endpoint
        self.use_http = endpoint.startswith("http")

    def send_transcript(self, transcript):
        """Send transcript to inference host"""
        payload = {
            "transcript": transcript,
            "timestamp": datetime.now().isoformat(),
            "source": "voice-assistant"
        }

        if self.use_http:
            return self._send_http(payload)
        else:
            return self._send_tcp(payload)

    def _send_http(self, payload):
        for attempt in range(3):
            try:
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    timeout=5.0
                )
                return response.json()
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def _send_tcp(self, payload):
        # TCP socket implementation
        pass
```

### Phase 5: Main Loop Integration
```python
def run(self):
    """Main application loop"""
    # Ensure model is trained
    if not self.ensure_model_trained():
        return

    # Start wake word detection
    print("🎙️  Voice Assistant Ready")
    print(f"   Listening for: '{self.state['wake_word']}'")
    print(f"   Inference endpoint: {self.state['inference_endpoint']}")

    detector = WakeWordDetector(
        model_paths=[self.state["model_path"]],
        on_detection=self.on_wake_word_detected
    )

    with detector:
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")

def on_wake_word_detected(self, wake_word, confidence):
    """Callback when wake word is detected"""
    print(f"\n🎯 Wake word detected! ({confidence:.1%})")
    print("🎙️  Listening for command...")

    # Start speech recognition
    transcript = self.speech_recognizer.recognize_stream(
        silence_timeout=self.state["silence_timeout"]
    )

    if transcript:
        print(f"📝 Transcript: {transcript}")

        # Send to inference host
        try:
            response = self.inference_client.send_transcript(transcript)
            print(f"💬 Response: {response}")
        except Exception as e:
            print(f"⚠️  Network error: {e}")

    print(f"\n● Listening for '{self.state['wake_word']}'...")
```

## File Structure

```
release/
├── voice-part.py              # Main unified script
├── release-plan.md            # This file
├── requirements.txt           # Dependencies
├── models/                    # Pre-downloaded models
│   └── vosk-model-small-en-us-0.15/
├── .voice-assistant-state.json  # Runtime state (auto-generated)
└── README.md                  # Quick start guide
```

## Dependencies

### Core (Already Have)
```
openwakeword>=0.5.0
pyaudio>=0.2.13
numpy>=1.24.0
scipy>=1.10.0
```

### Training (Already Have)
```
torch>=2.0.0
onnx>=1.14.0
onnxscript>=0.1.0
```

### NEW - Voice Recognition
```
vosk>=0.3.45              # Speech recognition
sounddevice>=0.4.6        # Audio I/O (alternative to PyAudio)
requests>=2.31.0          # HTTP client
```

### Optional
```
openai-whisper>=20230314  # Alternative to Vosk (Mac demos)
```

## Configuration

### Command Line Arguments
```bash
# Default mode: Check training, start detection
./voice-part.py

# Force retrain
./voice-part.py --retrain

# Specify inference endpoint
./voice-part.py --endpoint http://192.168.1.100:8000/process

# Use Whisper instead of Vosk
./voice-part.py --recognizer whisper

# Adjust silence timeout
./voice-part.py --silence-timeout 5.0

# Configure wake word
./voice-part.py --wake-word "computer activate"
```

### State File Configuration
Users can edit `.voice-assistant-state.json`:
```json
{
  "wake_word": "hey edge",
  "model_path": "models/hey_edge_v0.1.onnx",
  "model_trained": true,
  "inference_endpoint": "http://192.168.1.100:8000/process",
  "recognition_engine": "vosk",
  "vosk_model_path": "models/vosk-model-small-en-us-0.15",
  "silence_timeout": 3.0,
  "detection_threshold": 0.5,
  "send_to_inference": true
}
```

## Testing Strategy

### Unit Tests
- State management (load/save)
- Vosk integration (mock audio)
- Network client (mock server)
- Wake word detection (existing tests)

### Integration Tests
```bash
# Test 1: Fresh install
rm .voice-assistant-state.json
./voice-part.py
# Should guide through training

# Test 2: Resume
./voice-part.py
# Should load existing model, start detection

# Test 3: Network
python3 -m http.server 8000 &  # Mock server
./voice-part.py --endpoint http://localhost:8000
# Say wake word + command
# Check server receives POST
```

### Demo Script
```bash
# Terminal 1: Inference server (mock)
python3 << 'EOF'
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    print(f"Received: {data['transcript']}")
    return jsonify({"response": "Processing complete!"})

app.run(port=8000)
EOF

# Terminal 2: Voice assistant
./voice-part.py --endpoint http://localhost:8000/process
# Say: "hey edge"
# Say: "turn on the lights"
# [3 seconds silence]
# Check Terminal 1 for received transcript
```

## Deployment Scenarios

### Scenario 1: Raspberry Pi → Mac Inference
```bash
# Raspberry Pi
./voice-part.py --endpoint http://192.168.1.100:5000/inference

# Mac (inference server)
# Your LLM/AI processing server listening on :5000
```

### Scenario 2: Mac → Remote Server
```bash
# Mac
./voice-part.py --endpoint https://api.example.com/process

# Remote server
# Cloud-hosted inference API
```

### Scenario 3: Standalone Demo
```bash
# Single machine
./voice-part.py --endpoint http://localhost:8000/process
# Mock inference server on same machine
```

## Success Criteria

- ✅ Single script handles full pipeline
- ✅ Zero-config first run (guides training)
- ✅ State persists across restarts
- ✅ Works on Raspberry Pi 5 (real-time)
- ✅ Works on macOS (demo quality)
- ✅ Network communication reliable
- ✅ Clear visual feedback
- ✅ Graceful error handling
- ✅ < 500ms wake word latency
- ✅ < 1s speech recognition latency (Vosk on Pi)

## Timeline Estimate

- **Phase 1**: Core structure (1-2 hours) ✓
- **Phase 2**: Wake word integration (30 min) ✓
- **Phase 3**: Vosk integration (2-3 hours)
- **Phase 4**: Network communication (1 hour)
- **Phase 5**: Testing & polish (2 hours)

**Total**: 6-8 hours development time

## Next Steps

1. ✅ Create `release/` directory
2. ✅ Write this plan
3. → Implement `voice-part.py` core structure
4. → Integrate Vosk speech recognition
5. → Add network communication
6. → Test end-to-end pipeline
7. → Create release README
8. → Package for distribution

## Questions to Resolve

1. **Vosk model size**: Small (40MB) vs Medium (100MB) vs Large (1.8GB)?
   - **Recommendation**: Start with Small for Pi, Large for Mac

2. **Network protocol**: HTTP only or support TCP?
   - **Recommendation**: HTTP primary, TCP optional future

3. **Response handling**: Display? Speak? Ignore?
   - **Recommendation**: Print to console (simple), TTS optional future

4. **Error recovery**: Retry? Fallback? Queue?
   - **Recommendation**: Retry 3x, then continue (don't block detection)

5. **Multi-user**: Support different wake words per user?
   - **Recommendation**: Single wake word per installation (simple)

## Notes

- Keep existing development scripts in repo root
- `release/` folder is self-contained for deployment
- Can copy `release/` to Raspberry Pi as standalone package
- State file makes it "appliance-like" - configure once, run forever
