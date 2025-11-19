# Raspberry Pi 5 Setup Guide

Complete setup instructions for running the voice assistant on Raspberry Pi 5.

## Hardware Requirements

### Minimum Specs
- **Raspberry Pi 5** (4GB RAM minimum, 8GB recommended)
- **MicroSD Card**: 32GB+ (Class 10 or better)
- **USB Microphone** or USB sound card with microphone
- **Power Supply**: Official 27W USB-C power supply
- **Cooling**: Active cooling recommended (training generates heat)

### Recommended Hardware
- Raspberry Pi 5 8GB
- 64GB+ high-speed microSD (UHS-I U3 or better)
- USB condenser microphone (e.g., Blue Snowball, Samson Meteor)
- Heatsink or active cooling fan

## Software Compatibility

### ✅ Fully Compatible
- **Python**: 3.9+ (Python 3.11 recommended)
- **OS**: Raspberry Pi OS (64-bit) Bookworm or later
- **openwakeword**: ARM64 builds available
- **Vosk**: Native ARM64 support
- **PyAudio**: ARM builds available
- **NumPy/SciPy**: Optimized ARM builds

### ⚠️ Special Considerations
- **PyTorch**: Use ARM64 wheel (instructions below)
- **ONNX Runtime**: ARM builds available via pip
- **Training**: ~5-10 minutes on Pi 5 (vs ~3 minutes on M4 Mac)

### ❌ Not Recommended for Pi
- Whisper (too slow, CPU-intensive) - Stick with Vosk
- Large PyTorch models (memory intensive)

## Initial Setup

### 1. Install Raspberry Pi OS

**Download and Flash:**
```bash
# Use Raspberry Pi Imager
# Select: Raspberry Pi OS (64-bit) - Debian Bookworm
# Enable SSH in advanced options (recommended)
```

**First Boot Setup:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv git portaudio19-dev python3-dev build-essential
```

### 2. Clone Repository

```bash
cd ~
git clone https://github.com/maxpavlov/voice-activation-and-recognition.git
cd voice-activation-and-recognition/release
```

### 3. Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 4. Install Dependencies

#### Option A: Standard Installation (Recommended)

```bash
# Install most dependencies
pip install openwakeword pyaudio numpy scipy vosk sounddevice requests

# Install PyTorch for ARM64
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install ONNX
pip install onnx onnxruntime onnxscript torchmetrics
```

#### Option B: From requirements.txt (May need adjustments)

```bash
# This might fail on some packages, use Option A if issues occur
pip install -r requirements.txt
```

### 5. Setup Audio

#### Check Audio Devices

```bash
# List recording devices
arecordplay -l

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

#### Configure Default Device

If your USB mic isn't default:

```bash
# Create/edit ~/.asoundrc
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type asym
    capture.pcm "mic"
}
pcm.mic {
    type plug
    slave {
        pcm "hw:1,0"  # Adjust based on arecord -l output
    }
}
EOF
```

#### Fix Permissions

```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Log out and back in for changes to take effect
```

## Running the Voice Assistant

### First Run (Training)

```bash
cd ~/voice-activation-and-recognition/release
source venv/bin/activate

# Run with automatic setup
./voice-part.py

# Or specify wake word
./voice-part.py --wake-word "hey robot"
```

**Training Process:**
1. Enter wake word (e.g., "hey edge")
2. Microphone test (~5 seconds)
3. Record 5 samples (~15 seconds)
4. Train model (~5-10 minutes on Pi 5)
5. Start detection

### Subsequent Runs

```bash
source venv/bin/activate
./voice-part.py
# Use existing model? y
```

### Run as Background Service

```bash
# Keep running after SSH disconnect
nohup ./voice-part.py -y > voice-assistant.log 2>&1 &

# Check logs
tail -f voice-assistant.log
```

## Performance Optimization

### Reduce Training Time

```bash
# Use fewer augmentations (faster, slightly less accurate)
# Edit voice-part.py line 243:
--augmentations 10  # Instead of 20
```

### Reduce Memory Usage

```bash
# Monitor memory
free -h

# If low memory, reduce batch size in train-full-model.py:
batch_size = 16  # Instead of 32
```

### CPU Governor (Performance Mode)

```bash
# Check current governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Set to performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Revert to default
echo ondemand | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## Systemd Service (Auto-Start on Boot)

### Create Service File

```bash
sudo nano /etc/systemd/system/voice-assistant.service
```

**Contents:**
```ini
[Unit]
Description=Voice Assistant with Wake Word Detection
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/voice-activation-and-recognition/release
ExecStart=/home/pi/voice-activation-and-recognition/release/venv/bin/python3 /home/pi/voice-activation-and-recognition/voice-part.py -y
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable voice-assistant

# Start now
sudo systemctl start voice-assistant

# Check status
sudo systemctl status voice-assistant

# View logs
sudo journalctl -u voice-assistant -f
```

## Troubleshooting

### PyAudio Installation Fails

```bash
# Install system dependencies
sudo apt install portaudio19-dev python3-dev

# Then retry
pip install pyaudio
```

### PyTorch Installation Fails

```bash
# Use specific ARM wheel
pip install torch==2.0.0 --index-url https://download.pytorch.org/whl/cpu
```

### Microphone Not Found

```bash
# Check devices
arecord -l

# Test with specific device
arecord -D hw:1,0 -d 3 test.wav

# Update ~/.asoundrc with correct hw:X,Y
```

### ONNX Runtime Error

```bash
# Try older version
pip install onnxruntime==1.15.0
```

### Low Memory During Training

```bash
# Close other applications
# Or add swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Audio Underruns/Overruns

```bash
# Increase buffer size in recognizers/vosk_recognizer.py:
blocksize=16000  # Line 96, instead of 8000
```

## Performance Benchmarks

### Raspberry Pi 5 (8GB)

| Operation | Time | CPU | Memory |
|-----------|------|-----|--------|
| Model training (50 epochs) | 5-10 min | 100% | 1.5GB |
| Wake word detection (idle) | - | 8-12% | 200MB |
| Wake word latency | <500ms | - | - |
| Speech recognition | <2s | 40% | +100MB |

### Raspberry Pi 5 (4GB)

| Operation | Time | CPU | Memory |
|-----------|------|-----|--------|
| Model training (50 epochs) | 6-12 min | 100% | 1.5GB |
| Wake word detection (idle) | - | 10-15% | 200MB |

**Note**: 4GB works but training is slower and may require closing other apps.

## Network Setup (Cross-Host Demo)

### Pi as Voice Input

```bash
./voice-part.py --endpoint http://192.168.1.100:8000/process
```

### Pi as Inference Server

```bash
# Install Flask
pip install flask

# Run simple server (see QUICKSTART.md for code)
python3 inference_server.py
```

## Recommended Workflow

### Development

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Activate environment
cd ~/voice-activation-and-recognition/release
source venv/bin/activate

# Run interactively
./voice-part.py
```

### Production

```bash
# Use systemd service
sudo systemctl start voice-assistant
sudo journalctl -u voice-assistant -f
```

## Storage Requirements

- **Minimum**: 2GB free for installation
- **Recommended**: 5GB+ free
  - Python packages: ~1.5GB
  - Vosk model: 40MB
  - Trained models: ~20MB each
  - Training data: ~100MB

## Power Consumption

- **Idle (detection)**: ~3-4W
- **Training**: ~8-10W
- **Use official 27W PSU** to avoid throttling

## Tips for Best Results

1. **Training**: Do in quiet environment
2. **Microphone**: Position 30-50cm from mouth
3. **Cooling**: Ensure good airflow during training
4. **Updates**: Keep OS and packages updated
5. **Backup**: Save trained models to avoid retraining

## Known Limitations

- ❌ Whisper too slow (use Vosk instead)
- ❌ Real-time streaming limited by CPU
- ⚠️ Training slower than desktop (acceptable)
- ⚠️ Large batch sizes may cause memory issues

## Next Steps

1. Complete setup above
2. Train wake word model
3. Test wake word detection
4. Configure systemd service
5. Set up cross-host inference (optional)

## Support

For issues specific to Raspberry Pi:
- Check system logs: `dmesg | tail`
- Monitor resources: `htop`
- Check temperature: `vcgencmd measure_temp`

For general issues, see main README.md and TROUBLESHOOTING sections.
