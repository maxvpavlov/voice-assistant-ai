# Raspberry Pi 5 - Quick Start

Get your voice assistant running on Raspberry Pi 5 in under 30 minutes!

## Prerequisites

- Raspberry Pi 5 (4GB+ RAM)
- Raspberry Pi OS 64-bit (Bookworm)
- USB microphone
- Internet connection

## Installation (One-Time Setup)

```bash
# 1. Install system dependencies (~2 min)
sudo apt update && sudo apt install -y \
    python3-pip python3-venv git \
    portaudio19-dev python3-dev build-essential

# 2. Clone repository (~1 min)
cd ~
git clone https://github.com/maxpavlov/voice-activation-and-recognition.git
cd voice-activation-and-recognition/release

# 3. Create virtual environment (~1 min)
python3 -m venv venv
source venv/bin/activate

# 4. Install Python packages (~5-10 min)
pip install --upgrade pip

# Core packages
pip install openwakeword pyaudio numpy scipy vosk sounddevice requests

# PyTorch (ARM version)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# ONNX and training tools
pip install onnx onnxruntime onnxscript torchmetrics

# 5. Setup audio permissions
sudo usermod -a -G audio $USER
# Log out and back in after this step
```

## First Run (Training)

```bash
# Activate environment
cd ~/voice-activation-and-recognition/release
source venv/bin/activate

# Run voice assistant
./voice-part.py
```

**What happens:**
1. ✅ Choose wake word (e.g., "hey edge")
2. ✅ Mic test (5 seconds)
3. ✅ Record 5 samples (15 seconds)
4. ✅ Train model (5-10 minutes)
5. ✅ Start detection

**Training time on Pi 5**: ~5-10 minutes (be patient!)

## Subsequent Runs

```bash
cd ~/voice-activation-and-recognition/release
source venv/bin/activate
./voice-part.py
# Use existing model? y
```

## Test It Out

```bash
# Start the assistant
./voice-part.py -y

# Say your wake word
"hey edge"

# Then speak a command
"turn on the lights"

# See the transcript!
```

## Common Issues

### Microphone not found
```bash
# Check devices
arecord -l

# Test recording
arecord -d 3 test.wav
aplay test.wav
```

### PyAudio won't install
```bash
sudo apt install portaudio19-dev python3-dev
pip install pyaudio
```

### Out of memory during training
```bash
# Close other apps
# Or reduce augmentations:
./voice-part.py --retrain
# (Training will be faster but slightly less accurate)
```

### Permission denied (audio)
```bash
sudo usermod -a -G audio $USER
# Log out and log back in
```

## Performance Tips

### Speed up training
- Close browser and other apps
- Use fewer samples: Edit voice-part.py line 228 (change 5 to 3)
- Use fewer augmentations: Edit line 243 (change 20 to 10)

### Improve detection accuracy
- Train in quiet environment
- Use good quality USB microphone
- Position mic 30-50cm from mouth
- Record 10-20 samples instead of 5

### Enable performance mode
```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## Auto-Start on Boot (Optional)

```bash
# Create service file
sudo tee /etc/systemd/system/voice-assistant.service > /dev/null << 'EOF'
[Unit]
Description=Voice Assistant
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/voice-activation-and-recognition/release
ExecStart=/home/pi/voice-activation-and-recognition/release/venv/bin/python3 voice-part.py -y
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant

# Check status
sudo systemctl status voice-assistant
```

## Usage Commands

```bash
# Basic run
./voice-part.py

# Force retrain
./voice-part.py --retrain

# Different wake word
./voice-part.py --wake-word "hey robot"

# Send to remote inference server
./voice-part.py --endpoint http://192.168.1.100:8000/process

# More sensitive detection
./voice-part.py --threshold 0.3

# Longer silence timeout
./voice-part.py --silence-timeout 5.0

# Run in background
nohup ./voice-part.py -y > assistant.log 2>&1 &
```

## Storage Requirements

- **Installation**: ~2GB
- **Vosk model**: 40MB (auto-downloaded)
- **Trained model**: 20MB per wake word
- **Recommended free space**: 5GB

## Benchmark (Pi 5 8GB)

| Task | Time |
|------|------|
| Training | 5-10 min |
| Wake word detection | <500ms |
| Speech recognition | <2s |
| CPU usage (idle) | 8-12% |
| Memory usage | ~200MB |

## Next Steps

1. ✅ Complete installation
2. ✅ Train your wake word
3. ✅ Test detection
4. 📖 Read full docs: `RASPBERRY_PI_SETUP.md`
5. 🚀 Set up cross-host inference (optional)

## Support

- **Full guide**: See `RASPBERRY_PI_SETUP.md`
- **General help**: See `README.md`
- **Quick tips**: See `QUICKSTART.md`

## What Works on Pi 5

✅ Wake word training (5-10 min)
✅ Wake word detection (real-time)
✅ Vosk speech recognition (fast)
✅ Network inference
✅ Multiple wake words
✅ Continuous operation

❌ Whisper (too slow, use Vosk)
❌ Large models (memory limit)

## Success Criteria

You know it's working when:
1. Training completes without errors
2. You see "● Listening for 'your wake word'..."
3. Wake word triggers detection (🎯 WAKE WORD DETECTED!)
4. Speech is transcribed correctly
5. Detector resumes after each recognition

Happy voice controlling! 🎤🤖
