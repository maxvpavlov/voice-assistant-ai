# Voice Assistant - Production Release

Single-script voice assistant with wake word detection, speech recognition, and **ReAct-powered inference agent**.

## 🆕 New: Intelligent Inference Agent

The voice assistant now includes an **inference agent** that uses ReAct (Reasoning + Acting) pattern to process voice commands with LLM-powered reasoning!

**Quick Start with Agent**: See [AGENT_QUICKSTART.md](AGENT_QUICKSTART.md)

**Features**:
- 🧠 **ReAct reasoning** - LLM reasons about commands and takes actions
- 🏠 **Smart home control** - Lights, temperature, timers, weather
- 🔧 **Extensible tools** - Add custom integrations easily
- 📊 **Transparent reasoning** - See how the agent thinks
- 🚀 **Streaming responses** - Fast first-token delivery

**Example**:
```
You: "hey edge"
You: "turn on the lights and set temperature to 72"

Agent:
  💭 Thought: User wants lights on and temperature set
  🔧 Action: control_light(living_room, on)
  👁️  Observation: Light in living_room turned on
  🔧 Action: control_temperature(72, F)
  👁️  Observation: Temperature set to 72°F
  💬 Final Answer: I've turned on the lights and set the temperature to 72°F
```

## Platform Support

- ✅ **macOS** - Full support (tested on M4)
- ✅ **Raspberry Pi 5** - Full support with ARM optimizations
- ✅ **Linux** - Full support
- ⚠️ **Raspberry Pi 4** - Supported but slower training (~15-20 min)
- ❌ **Windows** - Not tested (may work with WSL)

**For Raspberry Pi users**: See [PI_QUICKSTART.md](PI_QUICKSTART.md) or [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# venv\Scripts\activate   # On Windows

# Install requirements
pip install -r requirements.txt
```

### 2. Run

```bash
./voice-part.py
```

**First run**: Will guide you through training a wake word (5-10 minutes)

**Subsequent runs**: Loads existing model and starts listening immediately

## What It Does

```
1. Wake Word Training (first run only)
   → Records 5 samples of your voice
   → Generates 80+ synthetic variations
   → Trains neural network (~3 minutes)

2. Wake Word Detection (always listening)
   → Listens for your custom wake word
   → Low CPU usage (~5-10% on Raspberry Pi)

3. Speech Recognition (activated by wake word)
   → Captures what you say after wake word
   → Stops after 3 seconds of silence
   → Uses Vosk for real-time transcription

4. Network Transmission
   → Sends transcript to inference endpoint
   → Default: http://localhost:8000/process
   → Configurable for cross-host demos
```

## Usage Examples

### Basic Usage

```bash
# Default - auto-detect existing model
./voice-part.py

# Say wake word → voice recognition activates → transcript sent to server
```

### Configure Inference Endpoint

```bash
# Send to specific host
./voice-part.py --endpoint http://192.168.1.100:5000/inference

# Disable network sending (local demo)
# Edit .voice-assistant-state.json: "send_to_inference": false
```

### Force Retrain

```bash
# Retrain wake word model
./voice-part.py --retrain
```

### Adjust Sensitivity

```bash
# More sensitive (0.3-0.4)
./voice-part.py --threshold 0.3

# Less sensitive (0.6-0.8)
./voice-part.py --threshold 0.7
```

### Silence Timeout

```bash
# Longer timeout (5 seconds)
./voice-part.py --silence-timeout 5.0

# Shorter timeout (2 seconds)
./voice-part.py --silence-timeout 2.0
```

## Configuration

State is persisted in `.voice-assistant-state.json`:

```json
{
  "wake_word": "hey edge",
  "model_path": "models/hey_edge_v0.1.onnx",
  "model_trained": true,
  "inference_endpoint": "http://localhost:8000/process",
  "recognition_engine": "vosk",
  "silence_timeout": 3.0,
  "detection_threshold": 0.5,
  "send_to_inference": true
}
```

Edit this file to change configuration without command-line arguments.

## Cross-Host Demo Setup

### Host 1: Voice Input (Raspberry Pi or Mac)

```bash
# Terminal 1
./voice-part.py --endpoint http://192.168.1.100:8000/process

# Say wake word
# Say command
# [3 seconds silence]
# Transcript sent to Host 2
```

### Host 2: Inference Server (Any machine)

```bash
# Terminal 2
python3 << 'EOF'
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    transcript = data['transcript']

    print(f"Received: {transcript}")

    # Your AI inference code here
    response = f"Processed: {transcript}"

    return jsonify({
        "status": "success",
        "response": response
    })

app.run(host='0.0.0.0', port=8000)
EOF
```

## System Requirements

### Minimum (Raspberry Pi 4)
- Python 3.8+
- 1GB RAM available
- 500MB storage
- Microphone

### Recommended (Raspberry Pi 5 or Mac)
- Python 3.10+
- 2GB RAM available
- 2GB storage
- Quality USB microphone

## Troubleshooting

### "No module named 'voice_assistant'"

**Cause**: Running from wrong directory

**Solution**: Run from repository root where `src/` exists, or adjust paths

### "Vosk model not found"

**Cause**: Model not downloaded

**Solution**: Script will auto-download on first run, or manual:
```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/
```

### "Audio device errors"

**Cause**: Microphone permissions or wrong device

**Solution**:
- Mac: Grant microphone permissions in System Preferences
- Linux: Add user to audio group: `sudo usermod -a -G audio $USER`
- List devices: Run AudioRecorder test from parent directory

### "Connection refused" to inference endpoint

**Cause**: Inference server not running

**Solution**: Start mock server (see Cross-Host Demo Setup above)

### Poor wake word detection

**Solution**:
- Retrain: `./voice-part.py --retrain`
- Record 20-50 samples for better accuracy
- Adjust threshold: `--threshold 0.4` (more sensitive)

### Speech recognition not working

**Cause**: Vosk model missing or wrong configuration

**Solution**:
- Check `models/vosk-model-small-en-us-0.15/` exists
- Verify model path in `.voice-assistant-state.json`
- Test: `python3 -c "import vosk; print('OK')"`

## Architecture

```
voice-part.py
    ↓
Check State → Train (if needed) → Wake Word Detection (listening...)
                                        ↓
                                   Wake Word Detected!
                                        ↓
                            [Pause wake word detector]
                                        ↓
                                  Speech Recognition
                                        ↓
                                  Network Send (HTTP)
                                        ↓
                            [Resume wake word detector]
                                        ↓
                                  Return to Detection (listening...)
```

**Key Behavior:**
- Wake word detector pauses during speech recognition to avoid microphone conflicts
- After speech completes, detector automatically resumes
- This ensures clean audio capture for both wake word and speech recognition

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## File Structure

```
release/
├── voice-part.py              # Main application
├── recognizers/
│   ├── __init__.py
│   └── vosk_recognizer.py     # Vosk speech recognition
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── ARCHITECTURE.md            # Technical details
├── release-plan.md            # Development plan
├── models/                    # Downloaded models (auto-created)
│   └── vosk-model-small-en-us-0.15/
└── .voice-assistant-state.json  # Runtime state (auto-created)
```

## Performance

| Metric | Raspberry Pi 5 | M4 Mac |
|--------|---------------|---------|
| Wake word latency | < 500ms | < 100ms |
| Speech recognition | < 1s | < 200ms |
| CPU usage (idle) | 5-10% | 2-5% |
| RAM usage | ~200MB | ~150MB |

## Network Protocol

### Request (POST /process)

```json
{
  "transcript": "turn on the lights",
  "timestamp": "2025-11-15T12:34:56.789Z",
  "source": "voice-assistant",
  "wake_word": "hey edge"
}
```

### Response

```json
{
  "status": "success",
  "response": "Lights turned on",
  "processing_time_ms": 123
}
```

## Development

Built from https://github.com/maxvpavlov/voice-activation-and-recognition

Uses:
- **openWakeWord**: Wake word detection
- **Vosk**: Speech recognition
- **PyTorch**: Model training
- **sounddevice**: Audio I/O

## License

See parent repository for license information.

## Support

For issues, see parent repository or create an issue at:
https://github.com/maxvpavlov/voice-activation-and-recognition/issues
