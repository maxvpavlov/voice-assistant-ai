# Voice Assistant - Wake Word Detection & Speech Recognition

A modular voice assistant library designed for Raspberry Pi 5 and macOS. Features wake word detection using openWakeWord with custom training capabilities and speech recognition.

## Features

- **Wake Word Detection**: Always-listening wake word detection using openWakeWord
- **Custom Training**: Record and train your own wake words
- **Cross-Platform**: Works on both Raspberry Pi 5 and macOS
- **Low Resource Usage**: Optimized for embedded devices
- **Multiple Wake Words**: Support for multiple pre-trained wake words
- **CLI Tool**: Complete command-line interface for training, testing, and running
- **Extensible**: Modular design for easy extension with speech recognition

## Current Status

✅ **Phase 1: Wake Word Detection & Training** (Complete)
- openWakeWord integration
- Audio capture and processing
- Multi-threaded detection
- Audio recording for training data collection
- Complete CLI tool (`edge-wake-word`)

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

2. **Quick Setup** (Recommended):
```bash
source setup-and-enter-venv.sh
```

This will automatically:
- Install system dependencies (PortAudio)
- Create a virtual environment
- Install Python dependencies
- Activate the environment

**Alternative - Manual Setup:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Using edge-wake-word CLI

The `edge-wake-word` command provides three modes: train, test, and run.

### Test Mode - Try Pre-trained Wake Words

Test with pre-trained wake words like "Alexa" or "Hey Jarvis":

```bash
./edge-wake-word test
```

Test specific wake words:
```bash
./edge-wake-word test --wake-words alexa hey_jarvis
```

Adjust detection sensitivity:
```bash
./edge-wake-word test --threshold 0.6
```

### Train Mode - Create Custom Wake Words

Train your own custom wake word in 3 steps:

**Step 1: Test your microphone**
```bash
./edge-wake-word train --test-mic --list-devices
```

**Step 2: Record training samples**
```bash
./edge-wake-word train --wake-word "hey edge" --num-samples 50
```

This will:
- Record 50 samples of you saying "hey edge"
- Save them to `training_data/hey_edge/positive/`
- Guide you through the recording process

**Step 3: Train your model**

After recording samples, use the openWakeWord training notebook:
1. Open: https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb
2. Upload your audio samples
3. Follow the notebook instructions
4. Download your trained `.onnx` or `.tflite` model

**Step 4: Test your custom model**
```bash
./edge-wake-word test --model path/to/your/model.onnx
```

### Advanced Training Options

Record with negative samples (improves accuracy):
```bash
./edge-wake-word train --wake-word "hey edge" \
  --num-samples 50 \
  --with-negatives \
  --duration 2.5
```

Customize output location:
```bash
./edge-wake-word train --wake-word "hey edge" \
  --output-dir ./my_training_data \
  --num-samples 100
```

### Run Mode - Production Use

Run the voice assistant in production mode:

```bash
./edge-wake-word run
```

Run with specific wake words:
```bash
./edge-wake-word run --wake-words alexa hey_jarvis
```

Run with custom threshold (less sensitive, fewer false positives):
```bash
./edge-wake-word run --threshold 0.7 --quiet
```

## CLI Reference

### Train Mode
```bash
edge-wake-word train [OPTIONS]
```

**Options:**
- `--wake-word TEXT`: Wake word to train (required)
- `--num-samples INT`: Number of samples to record (default: 50)
- `--duration FLOAT`: Duration of each sample in seconds (default: 2.0)
- `--output-dir PATH`: Output directory for samples (default: training_data)
- `--with-negatives`: Also collect negative samples
- `--test-mic`: Test microphone before recording
- `--list-devices`: List available audio devices

### Test Mode
```bash
edge-wake-word test [OPTIONS]
```

**Options:**
- `--model PATH`: Path to custom model file (.tflite or .onnx)
- `--wake-words WORD [WORD ...]`: Specific wake words to test
- `--threshold FLOAT`: Detection confidence threshold (default: 0.5)

### Run Mode
```bash
edge-wake-word run [OPTIONS]
```

**Options:**
- `--wake-words WORD [WORD ...]`: Wake words to detect
- `--threshold FLOAT`: Detection confidence threshold (default: 0.5)
- `--quiet`: Suppress status messages

## Project Structure

```
voice-activation-and-recognition/
├── src/
│   └── voice_assistant/
│       ├── __init__.py              # Package initialization
│       ├── wake_word_detector.py    # Wake word detection module
│       └── audio_recorder.py        # Audio recording for training
├── tests/                           # Unit tests (future)
├── edge-wake-word                   # Main CLI tool
├── demo.py                          # Simple demo (legacy)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Python API Usage

You can also use the library programmatically:

### Wake Word Detection

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

### Audio Recording for Training

```python
from voice_assistant import AudioRecorder

recorder = AudioRecorder(output_dir="my_training_data")

# Record a batch of samples
recorder.record_batch(
    wake_word="hey_edge",
    num_samples=50,
    duration=2.0,
    sample_type="positive"
)

# Test microphone
recorder.test_microphone(duration=3.0)
```

### Context Manager

```python
with WakeWordDetector(threshold=0.5, on_detection=callback) as detector:
    # Detector automatically starts
    while True:
        # Your application logic
        pass
    # Detector automatically stops
```

## Configuration

### Detection Threshold

The `--threshold` parameter controls sensitivity:
- **0.3-0.4**: More sensitive, may have false positives
- **0.5**: Balanced (recommended default)
- **0.6-0.8**: Less sensitive, fewer false positives

### Available Pre-trained Wake Words

The openWakeWord library includes:
- `alexa`
- `hey_jarvis`
- `hey_mycroft`
- `hey_rhasspy`
- `ok_nabu`
- And more (models downloaded automatically on first use)

### Audio Parameters

Default settings (optimized for openWakeWord):
- Sample Rate: 16kHz
- Chunk Size: 1280 samples (80ms)
- Format: 16-bit PCM
- Channels: Mono

## Training Best Practices

For best results when training custom wake words:

1. **Record Enough Samples**: 50-100 minimum, more is better
2. **Vary Conditions**:
   - Different volumes (quiet, normal, loud)
   - Different distances from microphone
   - Different speaking speeds
   - Different tones/inflections
3. **Quality Over Quantity**: Ensure clear recordings without clipping
4. **Negative Samples**: Optional but helpful for reducing false positives
5. **Background Noise**: Record in the environment where you'll use it

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

### Microphone Not Working

List available devices:
```bash
./edge-wake-word train --list-devices
```

Test your microphone:
```bash
./edge-wake-word train --test-mic
```

### Poor Detection Accuracy

- Lower the threshold: `--threshold 0.4`
- Ensure you're using the correct wake word pronunciation
- Record more training samples with varied conditions
- Check microphone placement and quality

## Performance

### Raspberry Pi 5
- Can run 15-20 wake word models simultaneously
- ~5-10% CPU usage per model
- Low latency (<100ms detection time)
- Recommended for production deployment

### macOS
- Negligible CPU usage on modern Macs
- Real-time performance with multiple models
- Great for development and testing

## Next Steps

1. **Add Speech Recognition**: Integrate Vosk for Raspberry Pi and Whisper for macOS
2. **Command Processing**: Build command parsing and execution pipeline
3. **Audio Feedback**: Add beep or LED indication on wake word detection
4. **Web Interface**: Optional web UI for configuration and monitoring
5. **Home Assistant Integration**: Connect with home automation systems

## Contributing

This is a demo/proof-of-concept project. Feel free to extend and customize for your needs.

## License

This project uses the following open-source libraries:
- **openWakeWord**: Apache 2.0 License
- **PyAudio**: MIT License

## Resources

- [openWakeWord GitHub](https://github.com/dscripka/openWakeWord)
- [openWakeWord Training Notebook](https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb)
- [Home Assistant Wake Words Collection](https://github.com/fwartner/home-assistant-wakewords-collection)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review openWakeWord documentation
3. Test with `./edge-wake-word train --test-mic`
4. Open an issue in this repository

## Examples

### Quick Test
```bash
# Install and test in under 5 minutes
source setup-and-enter-venv.sh
./edge-wake-word test
# Say "Alexa" or "Hey Jarvis"
```

### Train Custom Wake Word
```bash
# Full training workflow
./edge-wake-word train --wake-word "computer activate" --num-samples 100 --with-negatives
# Upload samples to Colab notebook for training
# Download trained model
./edge-wake-word test --model my_model.onnx
```

### Production Deployment
```bash
# Run on Raspberry Pi with custom settings
./edge-wake-word run --wake-words alexa --threshold 0.65 --quiet
```
