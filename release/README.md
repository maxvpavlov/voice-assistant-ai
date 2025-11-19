# Voice Assistant with AI Inference Agent

Complete voice-controlled AI assistant system with two coordinated components:

1. **`voice-part.py`** - Voice interface (wake word + speech recognition)
2. **`inference-agent.py`** - AI reasoning engine (ReAct-based LLM agent)

## 🎯 Quick Start

### Two-Terminal Setup

**Terminal 1: Start the AI Agent**
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

**First run**: `voice-part.py` will guide you through training a wake word (5 minutes)

**Usage**:
1. Say your wake word (e.g., "hey edge")
2. Give a command (e.g., "turn on the lights")
3. Wait 3 seconds
4. Agent processes and responds

See [AUDIO_TEST_GUIDE.md](AUDIO_TEST_GUIDE.md) for detailed testing instructions.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VOICE ASSISTANT                         │
│                        (voice-part.py)                          │
│                                                                 │
│  1. Wake Word Detection → 2. Speech Recognition                │
│     (openWakeWord)           (Vosk)                             │
│                                                                 │
│  Microphone → Audio → Transcript                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP POST
                           │ {"transcript": "turn on lights"}
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      INFERENCE AGENT                            │
│                    (inference-agent.py)                         │
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

## 📦 The Two Scripts

### 1. `voice-part.py` - Voice Interface

**What it does**:
- Listens for custom wake word (e.g., "hey edge")
- Captures speech after wake word detection
- Transcribes speech to text using Vosk
- Sends transcript to inference agent via HTTP

**Key features**:
- Train custom wake words (5 samples, ~3 min training)
- Real-time speech recognition
- Automatic silence detection (3s default)
- State persistence across sessions
- Adjustable detection threshold

**Usage**:
```bash
# First run - trains wake word
./voice-part.py

# Retrain wake word
./voice-part.py --retrain

# Adjust sensitivity
./voice-part.py --threshold 0.3  # More sensitive
./voice-part.py --threshold 0.7  # Less sensitive

# Configure endpoint
./voice-part.py --endpoint http://192.168.1.100:8000/process
```

See [WAKE_WORD_TROUBLESHOOTING.md](WAKE_WORD_TROUBLESHOOTING.md) if detection issues occur.

### 2. `inference-agent.py` - AI Reasoning Engine

**What it does**:
- Receives voice transcripts from voice-part.py
- Uses LLM (Ollama) with ReAct pattern to reason about commands
- Executes actions using available tools
- Returns structured responses with reasoning steps

**Key features**:
- ReAct (Reasoning + Acting) pattern
- Multi-step reasoning
- Tool execution (lights, temperature, timers, etc.)
- Extensible tool system
- Transparent reasoning process

**Usage**:
```bash
# Start agent (default: port 8000)
./inference-agent.py
```

**Test without voice**:
```bash
# Send test commands via HTTP
./test-agent.py "turn on the lights"
./test-agent.py  # Interactive mode
```

See [TEST_AGENT_GUIDE.md](TEST_AGENT_GUIDE.md) for testing the agent independently.

## 🎤 Example Session

```bash
# Terminal 1: Agent running
./inference-agent.py
🚀 Starting server on http://localhost:8000

# Terminal 2: Voice assistant
./voice-part.py
● Listening for 'hey edge'...

You: "hey edge"
> 🎯 WAKE WORD DETECTED! (52.3%)
> 🎙️  Listening for command...

You: "turn on the living room lights and set temperature to 72"
> 🎤 Listening...
>    ... turn on the living room lights
>    > turn on the living room lights
> 📤 Sending sentence #1...
>
>    ... and set temperature to seventy two
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
🔄 Resuming wake word detection...
● Listening for 'hey edge'...
```

## 🔧 Installation

### Prerequisites
- Python 3.9+ (3.10+ recommended)
- Ollama installed with model (gemma3:12b recommended)
- Microphone
- 2GB RAM available
- ~2GB disk space

### Setup

```bash
# 1. Install Ollama (if not already installed)
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull LLM model
ollama pull gemma3:12b

# 3. Clone and setup
cd release/
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# 4. Run
./inference-agent.py  # Terminal 1
./voice-part.py       # Terminal 2
```

## 📋 Testing & Debugging

### Test Agent Without Voice

```bash
# Interactive testing
./test-agent.py

# Single command
./test-agent.py "turn on the lights"

# Batch tests
./test-agent.py  # Select option 2
```

### Test Voice Detection

```bash
# Diagnostic tool
./diagnose-wake-word.py

# Test with different thresholds
./voice-part.py --threshold 0.3
```

### Full End-to-End Test

See [AUDIO_TEST_GUIDE.md](AUDIO_TEST_GUIDE.md) for complete testing guide.

## ⚙️ Configuration

### Voice Assistant State (`.voice-assistant-state.json`)

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

### Inference Agent Tools

Edit `inference-agent.py` to add custom tools:

```python
def my_custom_tool(arg1: str, arg2: int) -> str:
    """Your custom tool description."""
    # Your implementation
    return "Result"

TOOLS = {
    "my_custom_tool": my_custom_tool,
    # ... existing tools
}
```

Update the `SYSTEM_PROMPT` to include your tool in the available tools list.

## 🌐 Network Setup (Cross-Host)

Run voice interface on one machine, agent on another:

### Host 1 (Voice - Raspberry Pi/Mac with microphone)
```bash
./voice-part.py --endpoint http://192.168.1.100:8000/process
```

### Host 2 (Agent - Any machine with Ollama)
```bash
./inference-agent.py  # Listens on 0.0.0.0:8000
```

## 🎯 Platform Support

| Platform | voice-part.py | inference-agent.py | Notes |
|----------|---------------|-------------------|-------|
| macOS (M1/M2/M3) | ✅ Full | ✅ Full | Best performance |
| Raspberry Pi 5 | ✅ Full | ✅ Full | Recommended |
| Raspberry Pi 4 | ✅ Full | ⚠️  Slow | Training takes 15-20 min |
| Linux (x86) | ✅ Full | ✅ Full | Tested on Ubuntu |
| Windows | ❌ Untested | ❌ Untested | May work with WSL |

## 📊 Performance

| Metric | Raspberry Pi 5 | M4 Mac |
|--------|---------------|---------|
| Wake word latency | < 500ms | < 100ms |
| Speech recognition | Real-time | Real-time |
| Agent reasoning | 5-10s | 2-5s |
| Total response time | 6-12s | 3-7s |
| CPU (idle) | 5-10% | 2-5% |
| RAM usage | ~400MB | ~300MB |

## 🐛 Troubleshooting

### Wake Word Not Detecting

**Quick fixes**:
```bash
# Lower threshold
./voice-part.py --threshold 0.3

# Retrain with better samples
./voice-part.py --retrain
```

See [WAKE_WORD_TROUBLESHOOTING.md](WAKE_WORD_TROUBLESHOOTING.md) for complete guide.

### Agent Not Responding

**Check**:
1. Agent is running (`./inference-agent.py`)
2. Ollama is running (`ollama list`)
3. Port 8000 is free (`lsof -i :8000`)
4. Endpoint is correct (check `.voice-assistant-state.json`)

### Connection Refused

**Cause**: Agent not running or wrong endpoint

**Fix**:
```bash
# Terminal 1: Start agent
./inference-agent.py

# Terminal 2: Check endpoint
cat .voice-assistant-state.json | grep endpoint
```

### Missing Dependencies

```bash
# Training dependency
pip install pyyaml

# Audio processing
pip install librosa  # For diagnostics only
```

## 📚 Documentation

- **[AUDIO_TEST_GUIDE.md](AUDIO_TEST_GUIDE.md)** - Complete testing guide with voice
- **[TEST_AGENT_GUIDE.md](TEST_AGENT_GUIDE.md)** - Test agent without voice
- **[WAKE_WORD_TROUBLESHOOTING.md](WAKE_WORD_TROUBLESHOOTING.md)** - Fix detection issues
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture details
- **[AGENT_QUICKSTART.md](AGENT_QUICKSTART.md)** - Agent-specific quickstart

## 🔄 Typical Workflow

### Development & Testing
1. Start agent: `./inference-agent.py`
2. Test agent: `./test-agent.py "test command"`
3. Start voice: `./voice-part.py`
4. Test with voice: Say wake word + command

### Production Use
1. Train wake word once: `./voice-part.py` (first run)
2. Start agent (Terminal 1): `./inference-agent.py`
3. Start voice (Terminal 2): `./voice-part.py`
4. Use naturally: wake word → command → response

### Switching Wake Words
```bash
# Option 1: New wake word from scratch
./voice-part.py --wake-word "hey friday"

# Option 2: Interactive choice
./voice-part.py
# Choose "n" when asked about existing model
# Select "1. Train a NEW wake word"
```

## 🚀 Advanced Usage

### Change LLM Model

Edit `inference-agent.py`:
```python
def get_llm_response(history, stream=True):
    return ollama.chat(
        model='mistral:7b',  # Change model here
        messages=history,
        stream=stream
    )
```

Faster models: `mistral:7b`, `phi:3`
Better reasoning: `gemma3:12b`, `llama3:13b`

### Add Custom Tools

1. Define tool function in `inference-agent.py`
2. Add to `TOOLS` dictionary
3. Update `SYSTEM_PROMPT` with tool description

### Increase Training Quality

```bash
# More epochs (slower but better)
python3 train-full-model.py --wake-word "hey edge" --epochs 100 --augmentations 30
cp trained_models/hey_edge/hey_edge_v0.1.onnx* models/
```

## 🎓 How It Works

### Voice Part (voice-part.py)
1. Trains wake word model from 5 samples + 20x synthetic augmentation
2. Listens continuously with openWakeWord
3. On detection, pauses wake word, starts Vosk speech recognition
4. Sends complete sentences immediately to agent
5. Resumes wake word detection after 3s silence

### Inference Agent (inference-agent.py)
1. Receives transcript via HTTP POST
2. Processes with ReAct loop:
   - **Thought**: LLM reasons about what to do
   - **Action**: Calls appropriate tool
   - **Observation**: Gets tool result
   - Repeat until final answer
3. Returns structured response with reasoning steps

## 🛠️ Development

Built from: https://github.com/maxvpavlov/voice-activation-and-recognition

**Key Technologies**:
- **openWakeWord** - Wake word detection (ONNX)
- **Vosk** - Offline speech recognition
- **Ollama** - Local LLM inference
- **PyTorch** - Model training
- **Flask** - HTTP server for agent

## 📝 License

See parent repository for license information.

## 🤝 Support

Issues: https://github.com/maxvpavlov/voice-activation-and-recognition/issues

---

**Remember**: Always run both scripts together for full functionality:
- `inference-agent.py` - The AI brain (Terminal 1)
- `voice-part.py` - The voice interface (Terminal 2)
