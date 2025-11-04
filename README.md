# Voice Assistant - Wake Word Detection & Speech Recognition

A modular voice assistant library designed for Raspberry Pi 5 and macOS. Features wake word detection using openWakeWord and speech recognition capabilities.

## Features

- **Wake Word Detection**: Always-listening wake word detection using openWakeWord
- **Cross-Platform**: Works on both Raspberry Pi 5 and macOS
- **Low Resource Usage**: Optimized for embedded devices
- **Multiple Wake Words**: Support for multiple pre-trained wake words
- **Extensible**: Modular design for easy extension with speech recognition

## Current Status

✅ **Phase 1: Wake Word Detection** (Complete)
- openWakeWord integration
- Audio capture and processing
- Multi-threaded detection
- Demo application

🚧 **Phase 2: Speech Recognition** (Coming Next)
- Vosk integration for Raspberry Pi
- Optional Whisper support for macOS
- Command processing pipeline

## Quick Start

### Prerequisites

**macOS:**
```bash
brew install portaudio
```

**Raspberry Pi 5 (Debian/Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install -y python3-pyaudio portaudio19-dev
```

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd voice-activation-and-recognition
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Demo

```bash
python3 demo.py
```

The demo will:
1. Load pre-trained wake word models (downloads on first run)
2. Start listening for wake words like "Alexa" or "Hey Jarvis"
3. Print detection events with confidence scores
4. Show where voice recognition would activate

### Available Wake Words

The openWakeWord library includes several pre-trained models:
- `alexa`
- `hey_jarvis`
- `hey_mycroft`
- And more (models downloaded automatically on first use)

## Project Structure

```
voice-activation-and-recognition/
├── src/
│   └── voice_assistant/
│       ├── __init__.py              # Package initialization
│       └── wake_word_detector.py    # Wake word detection module
├── tests/                           # Unit tests (future)
├── demo.py                          # Demo application
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Usage

### Basic Wake Word Detection

```python
from voice_assistant import WakeWordDetector

def on_detected(wake_word: str, confidence: float):
    print(f"Detected: {wake_word} ({confidence:.2%})")

# Create detector
detector = WakeWordDetector(
    threshold=0.5,
    on_detection=on_detected
)

# Start listening
detector.start()

# ... your application logic ...

# Stop when done
detector.stop()
```

### Using Context Manager

```python
with WakeWordDetector(threshold=0.5, on_detection=callback) as detector:
    # Detector automatically starts
    while True:
        # Your application logic
        pass
    # Detector automatically stops
```

### Specific Wake Words

```python
# Only load specific wake words
detector = WakeWordDetector(
    wake_words=["alexa", "hey_jarvis"],
    threshold=0.6
)
```

## Configuration

### Detection Threshold

The `threshold` parameter controls sensitivity:
- **Lower (0.3-0.4)**: More sensitive, may have false positives
- **Medium (0.5)**: Balanced (recommended)
- **Higher (0.6-0.8)**: Less sensitive, fewer false positives

### Audio Parameters

Default settings (optimized for openWakeWord):
- Sample Rate: 16kHz
- Chunk Size: 1280 samples (80ms)
- Format: 16-bit PCM

## Troubleshooting

### macOS: PortAudio Issues

If you get audio errors, install PortAudio:
```bash
brew install portaudio
pip install --upgrade --force-reinstall pyaudio
```

### Raspberry Pi: Permission Denied

If you get audio permission errors:
```bash
sudo usermod -a -G audio $USER
# Log out and back in
```

### Models Not Downloading

If models fail to download, check your internet connection. Models are cached in:
- macOS: `~/.cache/openwakeword/`
- Linux: `~/.cache/openwakeword/`

## Performance

### Raspberry Pi 5
- Can run 15-20 wake word models simultaneously
- ~5-10% CPU usage per model
- Low latency (<100ms detection time)

### macOS
- Negligible CPU usage on modern Macs
- Real-time performance with multiple models

## Next Steps

1. **Add Speech Recognition**: Integrate Vosk for Raspberry Pi and Whisper for macOS
2. **Command Processing**: Build command parsing and execution pipeline
3. **Custom Wake Words**: Add support for training custom wake words
4. **Audio Feedback**: Add beep or LED indication on wake word detection
5. **Web Interface**: Optional web UI for configuration and monitoring

## Contributing

This is a demo/proof-of-concept project. Feel free to extend and customize for your needs.

## License

This project uses the following open-source libraries:
- **openWakeWord**: Apache 2.0 License
- **PyAudio**: MIT License

## Resources

- [openWakeWord GitHub](https://github.com/dscripka/openWakeWord)
- [openWakeWord Documentation](https://github.com/dscripka/openWakeWord/blob/main/docs/README.md)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review openWakeWord documentation
3. Open an issue in this repository
