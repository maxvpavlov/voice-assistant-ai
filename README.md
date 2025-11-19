# Voice-Controlled AI Assistant

Complete voice-controlled AI assistant system with wake word detection, speech recognition, and ReAct-based inference agent.

**Two coordinated scripts working together:**
1. **`release/voice-part.py`** - Voice interface (wake word + speech recognition)
2. **`release/inference-agent.py`** - AI reasoning engine (LLM-powered ReAct agent)

## Quick Start

### Prerequisites
- Python 3.9+ (3.10+ recommended)
- Ollama with LLM model (gemma3:12b recommended)
- Microphone
- 2GB RAM available

### Installation

```bash
# 1. Install Ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull LLM model
ollama pull gemma3:12b

# 3. Setup project
cd release/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Two-Terminal Setup

**Terminal 1: Start AI Agent**
```bash
cd release/
source venv/bin/activate
./inference-agent.py
```

**Terminal 2: Start Voice Assistant**
```bash
cd release/
source venv/bin/activate
./voice-part.py
```

**First run**: `voice-part.py` guides you through training a wake word (5 minutes)

### Usage

1. Say your wake word (e.g., "hey edge")
2. Give a voice command (e.g., "turn on the lights")
3. Wait 3 seconds for silence detection
4. Agent processes with reasoning and responds

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE ASSISTANT                              │
│                   (voice-part.py)                               │
│                                                                 │
│  Wake Word Detection → Speech Recognition                       │
│  (openWakeWord)         (Vosk)                                  │
│                                                                 │
│  Microphone → Audio → Transcript                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP POST
                           │ {"transcript": "turn on lights"}
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   INFERENCE AGENT                               │
│                 (inference-agent.py)                            │
│                                                                 │
│  ReAct Reasoning Loop (Ollama LLM):                             │
│    💭 Thought → 🔧 Action → 👁️ Observation → 💬 Answer        │
│                                                                 │
│  Available Tools:                                               │
│    • control_light() - Smart home lights                        │
│    • control_temperature() - Thermostat                         │
│    • get_weather() - Weather info                               │
│    • set_timer() - Timers & reminders                           │
│    • run_shell_command() - System commands                      │
└─────────────────────────────────────────────────────────────────┘
```

## The Two Scripts

### voice-part.py - Voice Interface

**What it does:**
- Listens for custom wake word (e.g., "hey edge")
- Captures speech after wake word detection
- Transcribes speech to text using Vosk
- Sends transcript to inference agent via HTTP

**Features:**
- Train custom wake words (5 samples, ~3 min training)
- Real-time speech recognition
- Automatic silence detection (3s default)
- Adjustable detection threshold
- State persistence across sessions

**Usage:**
```bash
# First run - trains wake word
./voice-part.py

# Retrain wake word
./voice-part.py --retrain

# Adjust sensitivity
./voice-part.py --threshold 0.3

# Configure endpoint
./voice-part.py --endpoint http://192.168.1.100:8000/process
```

### inference-agent.py - AI Reasoning Engine

**What it does:**
- Receives voice transcripts via HTTP
- Uses LLM (Ollama) with ReAct pattern to reason about commands
- Executes actions using available tools
- Returns structured responses with reasoning steps

**Features:**
- ReAct (Reasoning + Acting) pattern
- Multi-step reasoning
- Tool execution (lights, temperature, timers, etc.)
- Extensible tool system
- Transparent reasoning display

**Usage:**
```bash
# Start agent (port 8000)
./inference-agent.py

# Test without voice
./test-agent.py "turn on the lights"
./test-agent.py  # Interactive mode
```

## Example Session

```
Terminal 2: Voice Assistant
─────────────────────────────────────────────────────────────────
● Listening for 'hey edge'...

You: "hey edge"
> 🎯 WAKE WORD DETECTED! (52.3%)
> 🎙️  Listening for command...

You: "turn on the living room lights and set temperature to 72"
> 🎤 Listening...
>    > turn on the living room lights
> 📤 Sending sentence #1...
>
>    > and set temperature to seventy two
> 📤 Sending sentence #2...

╔════════════════════════════════════════════════════════════════╗
║ 🤖 AGENT RESPONSE                                              ║
╚════════════════════════════════════════════════════════════════╝

┌─ 💬 Answer
│ I've turned on the living room lights and set the temperature to 72°F.
└────────────────────────────────────────────────────────────────

┌─ 📋 Reasoning Process
│
│  Step 1:
│    💭 User wants living room lights on
│    🔧 control_light: living_room, on
│    👁️  Light in living_room turned on
│
│  Step 2:
│    💭 Now setting temperature to 72°F
│    🔧 control_temperature: 72, F
│    👁️  Temperature set to 72°F
│
│  ✓ Completed in 3 step(s) [Status: success]
└────────────────────────────────────────────────────────────────

⏸️  Silence detected (3.0s)
✅ Sent 2 sentence(s) total
● Listening for 'hey edge'...
```

## Features

### Wake Word Training
- Record 5 samples (5 minutes)
- Automatic synthetic augmentation (20x = 105 total samples)
- Neural network training with PyTorch
- ONNX export for production use
- Any language supported

### Speech Recognition
- Offline using Vosk (no cloud)
- Real-time streaming
- Sentence boundary detection
- Immediate sentence transmission
- 3-second silence timeout

### AI Inference
- Local LLM (Ollama)
- ReAct reasoning pattern
- Transparent thought process
- Tool execution
- Multi-step complex commands

## Testing & Debugging

### Test Agent Without Voice
```bash
cd release/
./test-agent.py "turn on the lights"
./test-agent.py  # Interactive mode
```

### Test Voice Detection
```bash
./diagnose-wake-word.py  # Test at different thresholds
./voice-part.py --threshold 0.3  # Lower threshold
```

### Full End-to-End Test
See `release/AUDIO_TEST_GUIDE.md` for complete testing guide.

## Configuration

All configuration in `release/.voice-assistant-state.json`:

```json
{
  "wake_word": "hey edge",
  "model_path": "models/hey_edge_v0.1.onnx",
  "inference_endpoint": "http://localhost:8000/process",
  "recognition_engine": "vosk",
  "silence_timeout": 3.0,
  "detection_threshold": 0.5,
  "send_to_inference": true
}
```

## Documentation

Located in `release/` directory:

- **[README.md](release/README.md)** - Complete guide for release scripts
- **[AUDIO_TEST_GUIDE.md](release/AUDIO_TEST_GUIDE.md)** - End-to-end voice testing
- **[TEST_AGENT_GUIDE.md](release/TEST_AGENT_GUIDE.md)** - Test agent without voice
- **[WAKE_WORD_TROUBLESHOOTING.md](release/WAKE_WORD_TROUBLESHOOTING.md)** - Fix detection issues
- **[ARCHITECTURE.md](release/ARCHITECTURE.md)** - Technical details

## Network Setup (Cross-Host)

Run voice on one machine, agent on another:

**Host 1 (Voice - Raspberry Pi/Mac with microphone)**
```bash
./voice-part.py --endpoint http://192.168.1.100:8000/process
```

**Host 2 (Agent - Any machine with Ollama)**
```bash
./inference-agent.py  # Listens on 0.0.0.0:8000
```

## Platform Support

| Platform | voice-part.py | inference-agent.py | Notes |
|----------|---------------|-------------------|-------|
| macOS (M1/M2/M3) | ✅ Full | ✅ Full | Best performance |
| Raspberry Pi 5 | ✅ Full | ✅ Full | Recommended |
| Raspberry Pi 4 | ✅ Full | ⚠️  Slow | Training: 15-20 min |
| Linux (x86) | ✅ Full | ✅ Full | Tested on Ubuntu |

## Performance

| Metric | Raspberry Pi 5 | M4 Mac |
|--------|---------------|---------|
| Wake word latency | < 500ms | < 100ms |
| Speech recognition | Real-time | Real-time |
| Agent reasoning | 5-10s | 2-5s |
| Total response time | 6-12s | 3-7s |

## Troubleshooting

### Wake Word Not Detecting
```bash
./voice-part.py --threshold 0.3  # More sensitive
./voice-part.py --retrain  # Better samples
./diagnose-wake-word.py  # Test thresholds
```

### Agent Not Responding
```bash
# Check agent running
lsof -i :8000

# Start agent
./inference-agent.py

# Check Ollama
ollama list
```

### Connection Refused
Check endpoint in `.voice-assistant-state.json` matches running agent.

## Advanced Usage

### Change LLM Model

Edit `inference-agent.py` line 145:
```python
model='mistral:7b',  # Faster
model='llama3:13b',  # Better reasoning
```

### Add Custom Tools

Edit `inference-agent.py`:
```python
def my_tool(arg: str) -> str:
    """Your tool description."""
    return "Result"

TOOLS = {
    "my_tool": my_tool,
    # ... existing tools
}

# Update SYSTEM_PROMPT to include tool description
```

## How It Works

### Voice Part
1. Trains wake word from 5 samples + 20x synthetic augmentation
2. Listens continuously with openWakeWord
3. On detection, pauses wake word detector
4. Starts Vosk speech recognition
5. Sends sentences immediately to agent
6. Resumes wake word after 3s silence

### Inference Agent
1. Receives transcript via HTTP POST
2. Processes with ReAct loop:
   - **Thought**: LLM reasons about what to do
   - **Action**: Calls appropriate tool
   - **Observation**: Gets tool result
   - Repeats until final answer
3. Returns structured response with full reasoning

## Technologies

- **openWakeWord** - Wake word detection (ONNX)
- **Vosk** - Offline speech recognition
- **Ollama** - Local LLM inference
- **PyTorch** - Model training
- **Flask** - HTTP server for agent
- **PyAudio** - Audio I/O

## License

See individual component licenses.

## Repository

https://github.com/maxvpavlov/voice-assistant-ai

---

**Remember**: Always run both scripts together:
- `release/inference-agent.py` - The AI brain (Terminal 1)
- `release/voice-part.py` - The voice interface (Terminal 2)
