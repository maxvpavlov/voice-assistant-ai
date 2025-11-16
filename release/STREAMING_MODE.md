# Streaming Sentence Mode

Real-time sentence-by-sentence transmission to inference endpoint.

## Overview

The voice assistant now sends each sentence to the inference endpoint **immediately** when Vosk detects a sentence boundary, instead of waiting for silence and batching all sentences together.

## How It Works

### Old Behavior (Batched)
```
User: "turn on the lights and set temperature to 70"

   ... turn on the lights
   > turn on the lights          ← Detected but waits
   ... and set temperature
   > and set temperature to seventy  ← Detected but waits
⏸️  Silence detected (3.0s)
📝 Transcript: 'turn on the lights and set temperature to seventy'
📤 Sending to: http://localhost:8000/process    ← Sent once, combined
```

### New Behavior (Streaming)
```
User: "turn on the lights and set temperature to 70"

   ... turn on the lights
   > turn on the lights          ← Detected!
📤 Sending sentence #1...
📤 Sending to: http://localhost:8000/process
✓ Response: {...}

   ... and set temperature
   > and set temperature to seventy  ← Detected!
📤 Sending sentence #2...
📤 Sending to: http://localhost:8000/process
✓ Response: {...}

⏸️  Silence detected (3.0s)
✅ Sent 2 sentence(s) total
```

## Benefits

### 1. **Lower Latency**
- Sentence sent **immediately** when detected
- No waiting for 3-second silence timeout
- First response arrives ~2-3 seconds faster

### 2. **Progressive Processing**
- Backend can start processing first sentence while user speaks second
- Parallel processing opportunity
- Better for multi-step commands

### 3. **Better UX**
- User sees immediate feedback
- Feels more responsive
- Can interrupt if needed

### 4. **Natural Conversation Flow**
- Matches human conversation patterns
- Each thought/sentence processed separately
- More intuitive for complex commands

## Technical Implementation

### VoskRecognizer Changes

Added `on_sentence_callback` parameter:

```python
def recognize_stream(self, silence_timeout=3.0, max_duration=30.0, on_sentence_callback=None):
    """
    Args:
        on_sentence_callback: Optional callback(sentence_text) called when sentence boundary detected
    """
    # ... audio processing ...

    if self.recognizer.AcceptWaveform(data):
        # Sentence boundary detected!
        text = result.get("text", "").strip()

        if text and on_sentence_callback:
            on_sentence_callback(text)  # Send immediately
```

### Voice Assistant Changes

Callback defined in `on_wake_word_detected`:

```python
def on_sentence_detected(sentence_text):
    """Called by Vosk when sentence boundary detected."""
    if self.state["send_to_inference"] and sentence_text.strip():
        self.sentences_sent += 1
        print(f"\n📤 Sending sentence #{self.sentences_sent}...")
        self.send_to_inference(sentence_text)  # Send each sentence as detected

sentences = self.speech_recognizer.recognize_stream(
    silence_timeout=self.state["silence_timeout"],
    on_sentence_callback=on_sentence_detected  # Stream mode enabled
)
```

## Timing Comparison

### Example: "Turn on lights. Set temperature to 70."

**Old (Batched) Mode:**
```
0.0s  - Wake word detected
0.5s  - Start speech recognition
1.0s  - User: "turn on lights"
2.0s  - Vosk detects sentence (internal)
2.5s  - User: "set temperature to 70"
4.0s  - Vosk detects sentence (internal)
7.0s  - Silence timeout (3s)
7.1s  - Send combined transcript
7.2s  - Backend receives, starts processing
```
**Total time to first response: ~7.2 seconds**

**New (Streaming) Mode:**
```
0.0s  - Wake word detected
0.5s  - Start speech recognition
1.0s  - User: "turn on lights"
2.0s  - Vosk detects sentence → Send #1 immediately!
2.1s  - Backend receives, starts processing (parallel)
2.5s  - User: "set temperature to 70"
4.0s  - Vosk detects sentence → Send #2 immediately!
4.1s  - Backend receives, starts processing
7.0s  - Silence timeout (3s)
7.1s  - Recognition complete
```
**Total time to first response: ~2.1 seconds** ✅
**Improvement: 5 seconds faster!**

## Network Protocol

### Request Format (Per Sentence)

Each sentence boundary triggers a separate HTTP POST:

```json
{
  "transcript": "turn on the lights",
  "timestamp": "2025-11-16T12:34:56.789Z",
  "source": "voice-assistant",
  "wake_word": "hey edge"
}
```

**Then immediately:**

```json
{
  "transcript": "set temperature to seventy degrees",
  "timestamp": "2025-11-16T12:34:58.123Z",
  "source": "voice-assistant",
  "wake_word": "hey edge"
}
```

### Server Requirements

Backend should handle:
1. **Multiple requests per wake word activation**
2. **Rapid succession** (< 1 second apart possible)
3. **Independent processing** (each sentence may be separate command)

### Example Server Implementation

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    transcript = data['transcript']
    timestamp = data['timestamp']

    print(f"[{timestamp}] Received: {transcript}")

    # Process immediately - don't wait for more sentences
    response = process_command(transcript)

    return jsonify({
        "status": "success",
        "response": response,
        "sentence": transcript
    })

def process_command(text):
    """Process single sentence command."""
    # Your AI/logic here
    return f"Processed: {text}"
```

## Use Cases

### Smart Home Commands (Multi-Step)

**User**: "Turn on the living room lights and set temperature to 72 degrees"

**Streaming sends:**
1. "turn on the living room lights" → Lights on immediately
2. "set temperature to seventy two degrees" → Temperature adjusting

**Backend can:**
- Execute first command while user still speaking
- Provide faster feedback
- Parallel execution

### Voice Search (Long Queries)

**User**: "Search for Italian restaurants in downtown with outdoor seating and good reviews"

**Streaming sends:**
1. "search for italian restaurants in downtown" → Initial results
2. "with outdoor seating and good reviews" → Refine results

**Backend can:**
- Start search immediately
- Refine as more context arrives
- Progressive disclosure

### Dictation (Multiple Thoughts)

**User**: "Dear John. I hope this email finds you well. I wanted to follow up on our meeting."

**Streaming sends:**
1. "dear john" → Start composing
2. "i hope this email finds you well" → Add sentence
3. "i wanted to follow up on our meeting" → Add sentence

**Backend can:**
- Build document progressively
- Show real-time updates
- Better UX

## Configuration

### Enable/Disable Streaming

Currently **always enabled**. To disable (use old batched mode):

```python
# In voice-part.py, replace:
sentences = self.speech_recognizer.recognize_stream(
    silence_timeout=self.state["silence_timeout"],
    on_sentence_callback=on_sentence_detected  # Remove this line
)

# With:
transcript = self.speech_recognizer.recognize_stream(
    silence_timeout=self.state["silence_timeout"]
    # No callback = batched mode
)
```

### Adjust Timing

```bash
# Shorter silence timeout (more responsive)
./voice-part.py --silence-timeout 2.0

# Longer silence timeout (more complete)
./voice-part.py --silence-timeout 4.0
```

## Backward Compatibility

### Old Inference Servers

Existing inference servers work without changes:
- Receive multiple requests instead of one
- Each request is valid standalone
- No protocol changes needed

### Network Reliability

If backend is slow/unavailable:
- Each sentence sends independently
- Retry logic per sentence (3 attempts)
- Failures don't block subsequent sentences

## Performance Impact

### Positive
- ✅ Faster first response (~5 seconds improvement)
- ✅ Lower perceived latency
- ✅ Progressive processing possible
- ✅ Better multi-step command handling

### Considerations
- ⚠️ More HTTP requests (N sentences = N requests)
- ⚠️ Backend sees separate requests (may need correlation)
- ⚠️ Network overhead per sentence

### Mitigation
- Requests are small (<1KB each)
- Only sent when speech active
- Connection pooling recommended

## Example Session Log

```
======================================================================
🎯 WAKE WORD DETECTED! (51.7%)
======================================================================
🎙️  Listening for command... (speak now)
⏸️  Pausing wake word detection...
INFO:voice_assistant.wake_word_detector:Stopping wake word detector...
INFO:voice_assistant.wake_word_detector:Wake word detector stopped
🎤 Listening...
   ... turn on the lights
   > turn on the lights

📤 Sending sentence #1...

📤 Sending to: http://localhost:8000/process
✓ Response: {'status': 'success', 'response': 'Lights turned on'}
   ... and set temperature to seventy degrees
   > and set temperature to seventy degrees

📤 Sending sentence #2...

📤 Sending to: http://localhost:8000/process
✓ Response: {'status': 'success', 'response': 'Temperature set to 70°F'}

⏸️  Silence detected (3.0s)

✅ Sent 2 sentence(s) total
🔄 Resuming wake word detection...
INFO:voice_assistant.wake_word_detector:Starting wake word detector...
● Listening for 'hey edge'...
```

## Future Enhancements

### Potential Improvements

1. **Sentence Correlation**
   - Add session ID to track related sentences
   - Backend can correlate multi-sentence commands

2. **Streaming Partial Results**
   - Send partial results for ultra-low latency
   - Show real-time transcription

3. **Smart Batching**
   - Batch very short sentences
   - Stream long sentences
   - Adaptive based on timing

4. **Duplex Communication**
   - Backend can interrupt/clarify
   - Two-way conversation

## Summary

**Streaming mode** sends each sentence immediately when detected, providing:
- ⚡ 5+ seconds faster first response
- 🎯 Progressive processing
- 💬 Natural conversation flow
- 🔄 Better multi-step commands

The system continues listening for 3 seconds after last speech, allowing multiple sentences per wake word activation while maintaining low latency for each individual sentence.
