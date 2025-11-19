# Changelog

All notable changes to the voice assistant project.

## [Unreleased] - 2025-11-17

### Added - ReAct Inference Agent

#### New Files
- **inference-agent.py** - HTTP server with ReAct reasoning
  - LLM-powered command processing using Ollama
  - Implements ReAct (Reasoning + Acting) pattern
  - Streaming responses for low latency
  - Structured reasoning steps + final answer

- **AGENT_QUICKSTART.md** - 5-minute setup guide
  - Installation instructions
  - Example commands
  - Troubleshooting tips

- **INFERENCE_AGENT.md** - Comprehensive documentation (550+ lines)
  - Architecture overview
  - API reference
  - Smart home integration examples
  - Custom tool development guide
  - Security considerations
  - Performance optimization

#### Smart Home Tools
- `control_light(location, state)` - Control lights
- `control_temperature(temperature, unit)` - Set thermostat
- `get_weather(location)` - Get weather info
- `set_timer(duration, label)` - Create timers
- `run_shell_command(command)` - Execute system commands

#### Voice Assistant Enhancements
- New `display_agent_response()` method
  - Shows reasoning process step-by-step
  - Displays actions and observations
  - Highlights final answer
  - Shows completion status

#### Dependencies
- `flask>=3.0.0` - HTTP server framework
- `rich>=13.0.0` - Beautiful terminal output
- `ollama>=0.1.0` - LLM integration

### Changed
- **README.md** - Added inference agent section with examples
- **voice-part.py** - Enhanced to display agent reasoning
- **requirements.txt** - Added inference agent dependencies

### Architecture
```
Voice Assistant (voice-part.py)
    ↓ HTTP POST
Inference Agent (inference-agent.py)
    ↓ Tool calls
Smart Home / System Tools
```

### Example Workflow
1. User says: "hey edge"
2. User says: "turn on lights and set temperature to 72"
3. Voice → Speech-to-text → HTTP POST to agent
4. Agent reasons and acts:
   ```
   💭 Thought: User wants lights + temperature
   🔧 Action: control_light(living_room, on)
   👁️  Observation: Light turned on
   🔧 Action: control_temperature(72, F)
   👁️  Observation: Temperature set to 72°F
   💬 Final Answer: "Done! Lights on, temp 72°F"
   ```
5. Voice assistant displays reasoning
6. Returns to wake word detection

## [1.1.0] - 2025-11-17

### Fixed - False Wake Word Detection Bug

#### Root Cause
Wake word detector's audio queue retained stale data after `stop()`, causing false detections when restarted after speech recognition.

#### Changes
- **wake_word_detector.py**
  - Added queue clearing in `stop()` method (lines 148-153)
  - Prevents stale audio from triggering false detections

- **voice-part.py**
  - Added 300ms transition delay before restarting detector (lines 428-430)
  - Ensures clean audio resource handoff between libraries

#### Impact
- ✅ Eliminates false wake word detections
- ✅ Proper orchestration: wake word → speech → wake word cycle
- ✅ No performance impact (300ms delay negligible)

#### Documentation
- **BUGFIX_FALSE_WAKE_WORD.md** - Full technical details

## [1.0.0] - 2025-11-17

### Added - Self-Contained Release

#### Major Change
Made `release/` directory fully self-contained and independently deployable.

#### Before (Coupled to Root)
```
voice-part.py
├─ Used: release/venv/         ✅
├─ Used: release/src/           ✅
└─ subprocess calls:
   ├─ cd .. && ../venv/         ❌ Root venv
   ├─ ../edge-wake-word         ❌ Root script
   ├─ ../train-full-model.py    ❌ Root script
   ├─ ../training_data/         ❌ Root folder
   └─ ../trained_models/        ❌ Root folder
```

#### After (Self-Contained)
```
voice-part.py
├─ Uses: release/venv/          ✅
├─ Uses: release/src/           ✅
├─ Uses: release/train-full-model.py  ✅
├─ Uses: release/training_data/       ✅
└─ Uses: release/trained_models/      ✅
```

#### Changes
1. **Copied Training Script**
   - `release/train-full-model.py` (from root)
   - No parent directory dependencies

2. **Updated voice-part.py**
   - Mic testing: Direct AudioRecorder (no subprocess)
   - Sample recording: AudioRecorder.record_sample()
   - Training: Local venv and script
   - Model paths: Local directories

3. **Created Data Directories**
   - `release/training_data/`
   - `release/trained_models/`

4. **Updated .gitignore**
   - Ignores venv, training data, trained models
   - Keeps bundled Vosk model

#### Benefits
- ✅ Independent deployment (just copy release/)
- ✅ Clear separation (dev/prod)
- ✅ Simplified installation
- ✅ Portable across machines
- ✅ No parent dependencies

#### Documentation
- **SELF_CONTAINED.md** - Full migration guide

### Added - Streaming Sentence Mode

#### Feature
Voice assistant now sends each sentence to inference endpoint **immediately** when detected, instead of waiting for silence and batching.

#### Old Behavior (Batched)
```
User speaks: "turn on lights and set temp to 70"
  ... wait for 3s silence ...
  Send combined: "turn on lights and set temp to 70"
```

#### New Behavior (Streaming)
```
User speaks: "turn on lights"
  → Immediately send: "turn on lights"
User speaks: "and set temp to 70"
  → Immediately send: "and set temp to 70"
  ... wait for 3s silence ...
  Done
```

#### Changes
- **VoskRecognizer.recognize_stream()**
  - Added `on_sentence_callback` parameter
  - Calls callback immediately when sentence detected

- **voice-part.py**
  - Callback sends each sentence via HTTP POST
  - Continues listening for 3 seconds after last speech
  - Tracks number of sentences sent

#### Benefits
- ⚡ ~5 seconds faster first response
- 🎯 Progressive processing (backend can start early)
- 💬 Natural conversation flow
- 🔄 Better multi-step commands

#### Documentation
- **STREAMING_MODE.md** - Full technical details

## [0.9.0] - 2025-11-16

### Added - Initial Production Release

#### Core Features
- Wake word training with synthetic data augmentation
- Real-time wake word detection (openWakeWord)
- Speech recognition (Vosk)
- HTTP inference endpoint integration
- State persistence across sessions
- Cross-platform support (macOS, Linux, Raspberry Pi)

#### Files
- `voice-part.py` - Main unified application
- `src/voice_assistant/` - Core modules
  - `wake_word_detector.py`
  - `audio_recorder.py`
  - `model_trainer.py`
- `recognizers/vosk_recognizer.py` - Speech recognition
- `train-full-model.py` - Model training script

#### Documentation
- `README.md` - User guide
- `QUICKSTART.md` - Quick start
- `RASPBERRY_PI_SETUP.md` - Pi setup
- `PI_QUICKSTART.md` - Pi quick start
- `ARCHITECTURE.md` - Technical architecture
- `MULTILINGUAL_SUPPORT.md` - Language support
- `MULTILINGUAL_EXAMPLES.md` - Training examples

#### Bug Fixes (from development)
1. **Microphone conflict**: Pause/resume detector during speech
2. **Model path resolution**: Prioritize local models
3. **Thread deadlock**: Non-blocking stop from callback

## Summary

### Latest Version Features

✅ **Self-contained deployment** - Copy release/ anywhere
✅ **ReAct inference agent** - LLM-powered reasoning
✅ **Smart home tools** - Lights, temperature, timers, weather
✅ **Streaming sentences** - Low-latency command processing
✅ **No false detections** - Fixed audio queue bug
✅ **Cross-platform** - macOS, Linux, Raspberry Pi 5
✅ **Extensible** - Easy to add custom tools
✅ **Production-ready** - Error handling, retry logic, state persistence

### File Structure

```
release/
├── voice-part.py              # Main voice assistant
├── inference-agent.py         # ReAct inference agent
├── train-full-model.py        # Training script
├── requirements.txt           # All dependencies
│
├── src/                       # Source modules
│   └── voice_assistant/
│       ├── wake_word_detector.py
│       ├── audio_recorder.py
│       └── model_trainer.py
│
├── recognizers/               # Speech recognition
│   └── vosk_recognizer.py
│
├── models/                    # Downloaded & trained models
│   ├── vosk-model-small-en-us-0.15/
│   └── *.onnx (user's trained models)
│
├── training_data/             # User's voice samples
│   └── <wake_word>/
│       └── positive/
│
├── trained_models/            # Training output
│   └── <wake_word>/
│
└── Documentation/
    ├── README.md              # Main guide
    ├── AGENT_QUICKSTART.md    # Agent setup (5 min)
    ├── INFERENCE_AGENT.md     # Agent reference (550 lines)
    ├── QUICKSTART.md          # Voice assistant setup
    ├── RASPBERRY_PI_SETUP.md  # Pi deployment
    ├── PI_QUICKSTART.md       # Pi quick start
    ├── ARCHITECTURE.md        # Technical details
    ├── STREAMING_MODE.md      # Sentence streaming
    ├── SELF_CONTAINED.md      # Self-contained mode
    ├── BUGFIX_FALSE_WAKE_WORD.md  # Bug fix details
    ├── MULTILINGUAL_SUPPORT.md    # Language support
    └── MULTILINGUAL_EXAMPLES.md   # Training examples
```

### Getting Started

**Without Inference Agent**:
```bash

source venv/bin/activate
pip install -r requirements.txt
./voice-part.py
```

**With Inference Agent**:
```bash
# Terminal 1: Start inference agent
./inference-agent.py

# Terminal 2: Start voice assistant
./voice-part.py
```

See **AGENT_QUICKSTART.md** for full setup guide.
