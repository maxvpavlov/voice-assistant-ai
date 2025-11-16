# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modular voice assistant library designed for Raspberry Pi 5 and macOS featuring wake word detection using openWakeWord with custom training capabilities. The project is currently in Phase 1 (wake word detection complete), with Phase 2 (speech recognition) planned.

## Core Architecture

### Three-Module Design

1. **WakeWordDetector** (`src/voice_assistant/wake_word_detector.py`)
   - Multi-threaded wake word detection using openWakeWord
   - Audio capture via PyAudio with callback-based streaming
   - Supports both pre-trained models (alexa, hey_jarvis, etc.) and custom verifier models
   - Uses queue-based architecture: audio callback thread → queue → detection loop thread
   - Detection threshold configurable (default: 0.5)
   - Audio config: 16kHz, mono, 16-bit PCM, 1280-sample chunks (80ms)

2. **AudioRecorder** (`src/voice_assistant/audio_recorder.py`)
   - Records training samples with countdown timers
   - Batch recording for positive/negative samples
   - Microphone testing with visual level indicators
   - Outputs to `training_data/{wake_word}/{positive|negative}/` structure

3. **ModelTrainer** (`src/voice_assistant/model_trainer.py`)
   - Trains custom verifier models using openWakeWord's verifier approach
   - Requires minimum 3-5 positive samples (50-100 recommended for production)
   - Outputs `.pkl` files to `training_data/{wake_word}/models/`
   - Uses base models (default: alexa) + lightweight personalized layer

### CLI Tool (`edge-wake-word`)

Main entry point implementing 5 modes:
- **train**: Record audio samples for custom wake words
- **train-local**: Train custom verifier models locally (no cloud required)
- **test-custom**: Test locally-trained custom models with verifier
- **test**: Test pre-trained wake word models
- **run**: Production mode for voice activation

## Common Development Commands

### Setup and Dependencies

```bash
# Quick setup (recommended) - installs all dependencies and activates venv
source setup-and-enter-venv.sh

# Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install training dependencies (PyTorch, ~500MB)
pip install -r requirements-training.txt
```

### Testing Wake Words

```bash
# Test with pre-trained models
./edge-wake-word test

# Test specific wake words
./edge-wake-word test --wake-words alexa hey_jarvis

# Adjust sensitivity
./edge-wake-word test --threshold 0.6
```

### Training Custom Wake Words

**Option 1: Guided Training (Recommended for Beginners)**
```bash
# Interactive step-by-step training with synthetic data generation
./guided-training.py
```
This interactive script:
- Walks you through the entire process
- Records 5 samples from your voice
- Generates 80+ synthetic variations automatically
- Trains a full neural network model
- Tests the model with you

**Option 2: Manual Training (Custom Verifier - Quick)**
```bash
# Step 1: Test microphone
./edge-wake-word train --test-mic --list-devices

# Step 2: Record samples (default: 5 for demo, use 50-100 for production)
./edge-wake-word train --wake-word "hey edge" --num-samples 50

# Step 3: Train model locally
./edge-wake-word train-local --wake-word "hey edge"

# Step 4: Test custom model
./edge-wake-word test-custom --wake-word "hey edge"
```

**Option 3: Full Model Training (Advanced)**
```bash
# Record samples first
./edge-wake-word train --wake-word "hey edge" --num-samples 5

# Train with synthetic data augmentation
python3 train-full-model.py --wake-word "hey edge" --epochs 50 --augmentations 20
```

### Running in Production

```bash
# Run with default settings
./edge-wake-word run

# Run with custom threshold (less sensitive)
./edge-wake-word run --threshold 0.7 --quiet
```

## Key Implementation Details

### Threading Model

- **Audio Callback Thread**: PyAudio callback captures audio chunks, pushes to queue
- **Detection Thread**: Runs continuously, pulls from queue, processes with openWakeWord
- **Main Thread**: Handles CLI, signals, and user callbacks
- All threads coordinated via `is_running` flag and queue timeouts

### Custom Verifier Workflow

1. Base model (e.g., alexa) provides initial activation signal
2. Custom verifier (trained .pkl) adds personalized verification layer
3. Two thresholds: base model threshold (default 0.5) + verifier threshold (default 0.3)
4. Training uses openWakeWord's `train_custom_verifier` function

### Audio Configuration Constants

- `SAMPLE_RATE = 16000` (16kHz - required by openWakeWord)
- `CHUNK_SIZE = 1280` (80ms chunks - recommended by openWakeWord)
- `CHANNELS = 1` (mono)
- `FORMAT = paInt16` (16-bit PCM)

### Model Storage

- Pre-trained models: Downloaded automatically by openWakeWord to `~/.cache/openwakeword/`
- Git-tracked models: `models/` directory (optional, use `copy-models-to-git.py`)
- Custom verifier models: `training_data/{wake_word}/models/{wake_word}_verifier.pkl`

## Platform-Specific Notes

### macOS
- Requires PortAudio: `brew install portaudio`
- PyAudio may need reinstall after PortAudio: `pip install --upgrade --force-reinstall pyaudio`
- Excellent performance on M-series chips for local training

### Raspberry Pi 5
- Install via apt: `sudo apt-get install python3-pyaudio portaudio19-dev`
- Can run 15-20 wake word models simultaneously
- ~5-10% CPU per model
- Optimized for embedded deployment

## File Structure Reference

```
voice-activation-and-recognition/
├── edge-wake-word                   # Main CLI entry point (Python 3 script)
├── guided-training.py               # 🆕 Interactive guided training (recommended for users)
├── src/voice_assistant/
│   ├── __init__.py                  # Exports: WakeWordDetector, AudioRecorder, ModelTrainer
│   ├── wake_word_detector.py       # Core detection with threading
│   ├── audio_recorder.py           # Training data collection
│   └── model_trainer.py            # Local verifier training
├── setup-and-enter-venv.sh         # Auto-setup script (detects OS, installs deps)
├── train-full-model.py             # Full model training with synthetic data augmentation
├── requirements.txt                # Core runtime dependencies
├── requirements-training.txt       # Training dependencies (PyTorch, etc.)
├── training_data/                  # Training samples and trained models
│   └── {wake_word}/
│       ├── positive/               # Samples saying wake word
│       ├── negative/               # Background/other speech samples
│       └── models/                 # Trained .pkl verifier models
├── trained_models/                 # Full model training outputs
│   └── {wake_word}/
│       ├── {wake_word}_v0.1.onnx   # Trained ONNX model
│       └── features/               # Extracted feature cache
└── models/                         # Deployed models for detection
```

## Python API Usage

### Programmatic Detection

```python
from voice_assistant import WakeWordDetector

def on_detected(wake_word: str, confidence: float):
    print(f"Detected: {wake_word} ({confidence:.2%})")

# Context manager (recommended)
with WakeWordDetector(threshold=0.5, on_detection=on_detected) as detector:
    # Detector auto-starts/stops
    while True:
        pass

# Manual control
detector = WakeWordDetector(threshold=0.5, on_detection=on_detected)
detector.start()
# ... application logic ...
detector.stop()
```

### Custom Verifier Models

```python
detector = WakeWordDetector(
    wake_words=["alexa"],
    threshold=0.5,
    custom_verifier_models={"alexa": "path/to/verifier.pkl"},
    custom_verifier_threshold=0.3,
    on_detection=callback
)
```

## Future Development (Phase 2)

Planned additions for speech recognition:
- Vosk integration for Raspberry Pi (offline, low resource)
- Whisper support for macOS (higher accuracy, more resources)
- Command processing pipeline after wake word activation
- Currently commented out in `requirements.txt`

## Troubleshooting Common Issues

### Audio Stream Errors
- Check PortAudio installation
- On Linux, add user to audio group: `sudo usermod -a -G audio $USER`
- Test mic: `./edge-wake-word train --test-mic`

### Poor Detection Accuracy
- Lower threshold (0.3-0.4 for more sensitive)
- Record more training samples (50-100 recommended)
- Ensure similar recording conditions (distance, volume, noise)
- For custom models, adjust `--verifier-threshold`

### Import Errors
- Ensure virtual environment is activated: `source venv/bin/activate`
- For training: `pip install -r requirements-training.txt`
- Check Python version: 3.8+ required

## Detection Threshold Guide

- **0.3-0.4**: More sensitive, may have false positives
- **0.5**: Balanced (recommended default)
- **0.6-0.8**: Less sensitive, fewer false positives

For custom verifiers, adjust both `--threshold` (base model) and `--verifier-threshold` (verifier layer).
