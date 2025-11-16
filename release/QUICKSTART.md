# Quick Start Guide

Get your voice assistant running in 5 minutes!

## Step 1: Setup (2 minutes)

```bash
# Navigate to release directory
cd release/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: First Run (3-5 minutes)

```bash
./voice-part.py
```

**You'll be guided through:**

1. Choose a wake word (e.g., "hey edge")
2. Test microphone
3. Record 5 samples
4. Train model (~3 minutes)
5. Test detection

## Step 3: Use It!

After training completes:

```
● Listening for 'hey edge'...
```

Say your wake word, then speak a command:

```
🎯 WAKE WORD DETECTED!
🎙️  Listening for command...
   > turn on the lights
   > set temperature to 72 degrees

📝 Transcript: 'turn on the lights set temperature to 72 degrees'
```

## Cross-Host Demo

### Terminal 1: Voice Input

```bash
./voice-part.py --endpoint http://192.168.1.100:8000/process
```

### Terminal 2: Inference Server (Mock)

```bash
# On the same or different machine
python3 -m flask run --host 0.0.0.0 --port 8000
```

Or use this simple server:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        print(f"📥 Received: {data['transcript']}")

        response = {"status": "success", "response": "Processed!"}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

server = HTTPServer(('0.0.0.0', 8000), Handler)
print("🚀 Inference server listening on :8000")
server.serve_forever()
```

## Common Commands

```bash
# Default run
./voice-part.py

# Force retrain
./voice-part.py --retrain

# Different endpoint
./voice-part.py --endpoint http://192.168.1.50:5000/api

# More sensitive
./voice-part.py --threshold 0.3

# Longer silence timeout
./voice-part.py --silence-timeout 5.0

# Skip prompts (auto-yes)
./voice-part.py -y
```

## Troubleshooting

### "No module named voice_assistant"

```bash
# Make sure to run from repository root, not release/
cd ..
./release/voice-part.py
```

Or copy `src/` to `release/`:

```bash
cp -r ../src .
```

### Microphone not working

**Mac:**
1. System Preferences → Security & Privacy → Microphone
2. Grant permission to Terminal/IDE

**Linux:**
```bash
sudo usermod -a -G audio $USER
# Log out and back in
```

### Model training fails

Check you have training dependencies:

```bash
pip install torch onnx onnxscript torchmetrics
```

## Next Steps

- Read [README.md](README.md) for full documentation
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [release-plan.md](release-plan.md) for development roadmap

## Tips

1. **Record in quiet environment** for best wake word accuracy
2. **Say wake word clearly** before each command
3. **Wait for "Listening..." prompt** before speaking
4. **Pause 3 seconds** after command to trigger sending
5. **Adjust threshold** if too many/few false positives

Enjoy your voice assistant! 🎉
