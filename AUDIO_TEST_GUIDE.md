# Audio Testing Guide

Complete end-to-end testing with voice input.

## Quick Start

### Terminal 1: Start Inference Agent

```bash

source venv/bin/activate
./inference-agent.py
```

**You should see**:
```
╭──────────────────────────────────────────────────────────────────╮
│ Voice Inference Agent                                            │
│ ReAct-based reasoning for voice commands                         │
│                                                                  │
│ Tools available: run_shell_command, control_light,              │
│ control_temperature, get_weather, set_timer                     │
│ Model: gemma3:12b                                               │
╰──────────────────────────────────────────────────────────────────╯

🚀 Starting server on http://localhost:8000
```

**Leave this running!** This is your AI agent that processes commands.

### Terminal 2: Start Voice Assistant

```bash

source venv/bin/activate
./voice-part.py
```

**You should see**:
```
● Listening for 'hey edge'...
```

**Now you're ready to talk!**

## How to Use

### 1. Say the Wake Word

**Say**: "hey edge"

**You should see**:
```
======================================================================
🎯 WAKE WORD DETECTED! (XX.X%)
======================================================================
🎙️  Listening for command... (speak now)
⏸️  Pausing wake word detection...
```

### 2. Give Your Command

**Say your command** immediately after seeing "Listening for command..."

**Examples**:
- "turn on the lights"
- "set temperature to 72 degrees"
- "what's the weather"
- "dim the bedroom lights and set a timer for 10 minutes"

### 3. Watch the Magic

**Speech Recognition**:
```
🎤 Listening...
   ... turn on the lights
   > turn on the lights

📤 Sending sentence #1...
```

**Agent Processing** (in Terminal 1):
```
📥 Received transcript: turn on the lights

Step 1
💭 Thought: User wants lights on, assuming all locations
🔧 Action: control_light(location=all, state=on)
💡 Light Control: all -> on
👁️  Observation: Light in all turned on

Step 2
💬 Final Answer: Okay, I've turned on all the lights.
```

**Response Display** (in Terminal 2):
```
======================================================================
🤖 AGENT RESPONSE
======================================================================

💬 Okay, I've turned on all the lights.

📋 Reasoning Process:

  Step 1:
    💭 Thought: User wants lights on, assuming all locations
    🔧 Action: control_light: location=all, state=on
    👁️  Observation: Light in all turned on

✓ Completed in 2 step(s) [Status: success]
======================================================================

⏸️  Silence detected (3.0s)
✅ Sent 1 sentence(s) total
🔄 Resuming wake word detection...
● Listening for 'hey edge'...
```

### 4. System Returns to Listening

After the response, the system automatically returns to listening for the wake word. You can say "hey edge" again and give another command.

## Full Session Example

```
Terminal 2 (Voice Assistant):
─────────────────────────────────────────────────────────────────

● Listening for 'hey edge'...

[User says: "hey edge"]

======================================================================
🎯 WAKE WORD DETECTED! (52.3%)
======================================================================
🎙️  Listening for command... (speak now)

[User says: "turn on the living room lights and set temperature to 72"]

🎤 Listening...
   ... turn on the living room lights
   > turn on the living room lights

📤 Sending sentence #1...

   ... and set temperature to seventy two
   > and set temperature to seventy two

📤 Sending sentence #2...

⏸️  Silence detected (3.0s)

======================================================================
🤖 AGENT RESPONSE (for sentence 1)
======================================================================
💬 I've turned on the living room lights.
...
======================================================================

======================================================================
🤖 AGENT RESPONSE (for sentence 2)
======================================================================
💬 I've set the temperature to 72°F.
...
======================================================================

✅ Sent 2 sentence(s) total
🔄 Resuming wake word detection...
● Listening for 'hey edge'...
```

## Commands to Try

### Simple Commands

```
"hey edge"
→ "turn on the lights"

"hey edge"
→ "set temperature to 70 degrees"

"hey edge"
→ "what's the weather"
```

### Complex Multi-Step

```
"hey edge"
→ "turn on the living room lights and set temperature to 72"

"hey edge"
→ "dim the bedroom lights and set a timer for 10 minutes"

"hey edge"
→ "check the weather and turn on the heater if it's cold"
```

### Information Queries

```
"hey edge"
→ "what's my current directory"

"hey edge"
→ "what's the date"
```

## Troubleshooting

### Wake Word Not Detected

**Problem**: You say "hey edge" but nothing happens

**Solutions**:
1. **Speak clearly** - Say it naturally, not too fast or slow
2. **Check microphone** - Make sure Terminal has microphone permissions
3. **Adjust threshold** - Try `./voice-part.py --threshold 0.3` (more sensitive)
4. **Check Terminal 2** - Should show "● Listening for 'hey edge'..."
5. **Retrain model** - If all else fails: `./voice-part.py --retrain`

### Speech Not Recognized

**Problem**: Wake word detected, but command not transcribed correctly

**Solutions**:
1. **Speak clearly** - Natural pace, not too fast
2. **Wait for "Listening..."** - Make sure you see the prompt
3. **Check Vosk model** - Should be in `models/vosk-model-small-en-us-0.15/`
4. **No background noise** - Minimize ambient sound

### Agent Not Responding

**Problem**: Command sent but no agent response

**Check**:
1. **Terminal 1 running** - Agent should be showing activity
2. **No errors in Terminal 1** - Check for Python errors
3. **Ollama running** - Test: `ollama list`
4. **Port 8000 free** - Only one agent should be running

### "Connection refused"

**Problem**: Voice assistant can't reach agent

**Solutions**:
```bash
# Check agent is running
lsof -i :8000

# If not, start it
./inference-agent.py

# Check endpoint in voice assistant
# Should be: http://localhost:8000/process
```

## Tips for Best Results

### 1. Wake Word Detection

✅ **Do**:
- Say "hey edge" clearly and naturally
- Wait for the detection confirmation
- Speak from 1-3 feet from microphone

❌ **Don't**:
- Whisper or shout
- Say it too fast ("heyedge")
- Have TV/music playing loudly

### 2. Giving Commands

✅ **Do**:
- Wait for "Listening for command..." prompt
- Speak naturally, like talking to a person
- Pause briefly between thoughts
- Be specific ("living room lights" not just "lights")

❌ **Don't**:
- Start speaking before the prompt
- Speak very slowly or robot-like
- Use multiple wake words ("hey edge, hey edge")

### 3. Multi-Sentence Commands

The system sends each sentence immediately:

```
You: "turn on the lights"
     [Agent processes...]
You: "and set temperature to 70"
     [Agent processes...]
[3 seconds silence]
[System returns to wake word detection]
```

**Tip**: You can continue speaking naturally - each sentence is processed as you speak!

### 4. Watching Both Terminals

- **Terminal 1 (Agent)**: See detailed reasoning and tool execution
- **Terminal 2 (Voice)**: See speech recognition and final responses

This helps you understand what's happening at each step.

## Advanced Usage

### Custom Endpoint

Send to different agent/host:
```bash
./voice-part.py --inference-endpoint http://192.168.1.100:8000/process
```

### Adjust Sensitivity

More sensitive (catches wake word easier):
```bash
./voice-part.py --threshold 0.3
```

Less sensitive (fewer false positives):
```bash
./voice-part.py --threshold 0.7
```

### Longer Listening Window

More time to speak:
```bash
./voice-part.py --silence-timeout 5.0
```

Faster timeout:
```bash
./voice-part.py --silence-timeout 2.0
```

### Disable Network Sending

Test locally without agent:
```bash
./voice-part.py
# Edit .voice-assistant-state.json: "send_to_inference": false
```

## Understanding the Flow

```
1. YOU say wake word
   ↓
2. Wake word detector hears "hey edge"
   ↓
3. System activates speech recognition
   ↓
4. YOU give command
   ↓
5. Vosk converts speech → text (each sentence)
   ↓
6. Each sentence sent immediately to agent via HTTP
   ↓
7. Agent (Ollama + ReAct) reasons and acts
   ↓
8. Agent response shown in Terminal 2
   ↓
9. After 3s silence, return to step 1
```

## Performance Notes

### Response Time

**Typical latency**:
- Wake word detection: ~500ms
- Speech recognition: Real-time (immediate)
- First sentence sent: ~2s after speaking
- Agent reasoning: 2-5s per sentence
- **Total**: ~5-10s from wake word to final response

### Optimization

**Faster responses**:
1. Use smaller model in agent (`mistral:7b`)
2. Reduce `max_steps` in `inference-agent.py`
3. Warm up Ollama before first use
4. Close other applications

**Better accuracy**:
1. Retrain wake word with more samples
2. Speak clearly and naturally
3. Minimize background noise
4. Use better microphone

## System Requirements

### Minimum
- macOS / Linux / Raspberry Pi 5
- Python 3.9+
- 6GB RAM (for Ollama + model)
- Microphone
- ~10GB disk space

### Recommended
- 8GB+ RAM
- Good quality microphone
- Quiet environment
- Fast CPU (M1/M2 Mac or modern Intel)

## Quick Checklist

Before starting:
- [ ] Ollama installed and model pulled (`gemma3:12b`)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Wake word model trained (or run `./voice-part.py --retrain`)
- [ ] Microphone connected and working
- [ ] Terminal has microphone permissions

To test:
- [ ] Terminal 1: `./inference-agent.py` running
- [ ] Terminal 2: `./voice-part.py` running
- [ ] See "● Listening for 'hey edge'..."
- [ ] Say wake word clearly
- [ ] See detection confirmation
- [ ] Give command
- [ ] See agent response
- [ ] System returns to listening

## Next Steps

Once basic testing works:

1. **Try different commands** - Explore agent capabilities
2. **Test multi-step** - Complex commands with multiple actions
3. **Customize tools** - Add your own smart home integrations
4. **Deploy on Pi** - Run 24/7 voice assistant
5. **Add voice output** - TTS for full conversation

The system is production-ready and works end-to-end with real voice input!
