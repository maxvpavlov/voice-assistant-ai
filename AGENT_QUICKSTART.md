# Inference Agent Quickstart

Get the voice assistant with ReAct reasoning running in 5 minutes!

## Prerequisites

- macOS or Linux (Raspberry Pi 5 supported)
- Python 3.9+
- ~6GB free RAM (for Ollama + model)

## Step 1: Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model (will download ~4.7GB)
ollama pull llama3.1:8b
```

Test Ollama:
```bash
ollama run llama3.1:8b "hello"
# Should respond with a greeting
```

## Step 2: Install Dependencies

```bash

source venv/bin/activate
pip install flask rich ollama
```

## Step 3: Start the Inference Agent

In **Terminal 1**:
```bash
./inference-agent.py
```

Should see:
```
┌────────────────────────────────────────┐
│   Voice Inference Agent                │
│   ReAct-based reasoning for voice      │
│   commands                             │
│                                        │
│   Tools available: control_light,      │
│   control_temperature, get_weather,    │
│   set_timer, run_shell_command         │
│   Model: llama3.1:8b                   │
└────────────────────────────────────────┘

🚀 Starting server on http://localhost:8000
```

## Step 4: Start Voice Assistant

In **Terminal 2**:
```bash

source venv/bin/activate
./voice-part.py
```

If no trained model exists, it will guide you through training.

## Step 5: Use Voice Commands

1. **Say the wake word**: "hey edge"

   Should see:
   ```
   ======================================================================
   🎯 WAKE WORD DETECTED! (XX.X%)
   ======================================================================
   ```

2. **Give a command**: "turn on the lights"

3. **Watch the magic happen**:
   ```
   📤 Sending sentence #1...
   📤 Sending to: http://localhost:8000/process

   ======================================================================
   🤖 AGENT RESPONSE
   ======================================================================

   💬 I've turned on the lights

   📋 Reasoning Process:

     Step 1:
       💭 Thought: User wants to turn on lights
       🔧 Action: control_light: living_room, on
       👁️  Observation: Light in living_room turned on

   ✓ Completed in 2 step(s) [Status: success]
   ======================================================================
   ```

## Example Commands to Try

### Smart Home
- "Turn on the living room lights"
- "Set temperature to 72 degrees"
- "Turn off the bedroom lights"
- "What's the weather?"

### Timers
- "Set a timer for 5 minutes"
- "Set a 10 minute timer for cooking"

### System
- "What's my current directory?"
- "List files in the home folder"
- "What's the current date?"

### Complex
- "Turn on the lights and set temperature to 70"
- "Check the weather and if it's cold turn on the heater"

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ YOU                                                          │
│  ↓ (speak)                                                   │
│ "hey edge" ──► Wake Word Detected                           │
│  ↓ (speak)                                                   │
│ "turn on lights" ──► Speech Recognition                     │
│  ↓                                                           │
│ Transcript: "turn on lights"                                │
└─────────────────────────────────────────────────────────────┘
                    ↓ HTTP POST
┌─────────────────────────────────────────────────────────────┐
│ INFERENCE AGENT (inference-agent.py)                        │
│                                                              │
│  Step 1: 💭 User wants lights on                            │
│  Step 2: 🔧 control_light(living_room, on)                  │
│  Step 3: 👁️  "Light turned on"                              │
│  Step 4: 💬 "I've turned on the lights"                     │
└─────────────────────────────────────────────────────────────┘
                    ↓ HTTP Response
┌─────────────────────────────────────────────────────────────┐
│ VOICE ASSISTANT (voice-part.py)                             │
│                                                              │
│  Displays reasoning and response                            │
│  Waits 3 seconds for more speech                            │
│  Resumes wake word detection                                │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Wake Word Detection
- Always listening for "hey edge" (or your custom wake word)
- Uses openWakeWord with trained ONNX model
- Low CPU usage (~5%)

### 2. Speech Recognition
- Activated when wake word detected
- Uses Vosk for offline speech-to-text
- Sends each sentence immediately (streaming mode)
- Continues listening for 3 seconds after last speech

### 3. ReAct Reasoning
- Receives transcript via HTTP POST
- LLM reasons about what to do
- Takes actions using available tools
- Iterates until task complete
- Returns natural language response

### 4. Response Display
- Shows agent's reasoning process
- Displays actions taken
- Shows final answer
- Returns to wake word detection

## Troubleshooting

### "Ollama connection failed"

```bash
# Start Ollama service
ollama serve

# In another terminal, verify
ollama list
```

### "Model not found"

```bash
# Pull the model
ollama pull llama3.1:8b

# Verify
ollama list
```

### "ModuleNotFoundError: No module named 'flask'"

```bash
# Ensure venv is activated
source venv/bin/activate

# Install dependencies
pip install flask rich ollama
```

### Agent is slow

**Try a faster model**:
```bash
ollama pull gemma2:9b  # Faster alternative
```

Then edit `inference-agent.py` line 159:
```python
model='gemma2:9b',  # Changed from llama3.1:8b
```

### Port 8000 already in use

**Option 1**: Kill the process using port 8000
```bash
lsof -ti:8000 | xargs kill -9
```

**Option 2**: Use different port

Edit `inference-agent.py` line 404:
```python
app.run(host='0.0.0.0', port=8001, debug=False)  # Changed port
```

Then update voice assistant:
```bash
./voice-part.py --inference-endpoint http://localhost:8001/process
```

## Next Steps

### Customize Tools

Edit `inference-agent.py` and add your own tools:

```python
def my_tool(argument: str) -> str:
    """What your tool does."""
    # Your code here
    return "Result"

TOOLS = {
    # ... existing tools ...
    "my_tool": my_tool,
}
```

### Integrate Real Smart Home

See `INFERENCE_AGENT.md` for integration examples with:
- Home Assistant
- Philips Hue
- Nest Thermostat
- And more...

### Improve Prompts

Edit `SYSTEM_PROMPT` in `inference-agent.py` to:
- Add personality
- Customize behavior
- Add domain-specific knowledge

### Deploy on Raspberry Pi

See `RASPBERRY_PI_SETUP.md` for Raspberry Pi 5 deployment guide.

## Performance Tips

1. **Keep Ollama warm**: Test query on startup
   ```bash
   ollama run llama3.1:8b "ready" > /dev/null
   ```

2. **Use GPU** (if available): Ollama automatically uses GPU

3. **Reduce max_steps**: Faster responses
   ```python
   result = run_agent(transcript, max_steps=3)  # Default: 5
   ```

4. **Use smaller model**: Trade quality for speed
   ```bash
   ollama pull mistral:7b  # Faster than llama3.1:8b
   ```

## Resources

- **Full documentation**: `INFERENCE_AGENT.md`
- **Voice assistant docs**: `README.md`
- **Raspberry Pi setup**: `RASPBERRY_PI_SETUP.md`
- **Ollama models**: https://ollama.com/library
- **ReAct paper**: https://arxiv.org/abs/2210.03629

## Support

Issues? Check:
1. Both terminals are running
2. Ollama is working: `ollama list`
3. Dependencies installed: `pip list | grep flask`
4. Port 8000 is free: `lsof -i :8000`

Still stuck? Review the full documentation in `INFERENCE_AGENT.md`.

## What's Next?

Now that you have the basic setup working, explore:

1. **Add custom tools** for your specific use case
2. **Integrate real smart home devices** (lights, thermostat, etc.)
3. **Create custom wake words** for different contexts
4. **Deploy on Raspberry Pi** for always-on voice control
5. **Add voice output** (TTS) for full conversational experience

The system is designed to be modular and extensible - have fun building on it!
