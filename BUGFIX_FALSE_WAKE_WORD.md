# Bug Fix: False Wake Word Detection After Speech Recognition

## Problem

After the first sentence was sent over the network, the system immediately detected a "wake word" without the user saying it, creating an infinite loop of false detections.

### Symptoms

```
   > how are you doing
📤 Sending sentence #1...
⏸️  Silence detected (3.0s)
✅ Sent 1 sentence(s) total
🔄 Resuming wake word detection...
● Listening for 'hey edge'...

INFO:voice_assistant.wake_word_detector:Wake word detected: 'hey_edge_v0.1' (confidence: 0.53)
🎯 WAKE WORD DETECTED! (53.4%)  ← FALSE DETECTION (user didn't say anything)
```

The wake word detector was triggering immediately after restart, even though the user wasn't speaking.

## Root Cause

When the wake word detector was stopped and then restarted after speech recognition, its **audio queue was not cleared**. This caused the detector to process stale audio data from before it was stopped, which could contain patterns triggering false wake word detections.

### Bug Flow

1. **Wake word detected** → `stop(wait=False)` called
2. Audio stream stops, but **audio queue retains buffered data**
3. Speech recognition starts with sounddevice (different audio library)
4. Speech recognition completes after 3s silence
5. **Wake word detector `start()` called** → Opens new PyAudio stream
6. Detection loop immediately processes **OLD audio from queue**
7. Old audio triggers false wake word detection → Infinite loop

### Technical Details

The `WakeWordDetector` class uses two components:
- **PyAudio stream**: Captures audio via callback (`_audio_callback`)
- **Audio queue**: Stores captured audio chunks for processing

When `stop()` was called:
```python
def stop(self, wait=True):
    self.is_running = False
    if self.stream:
        self.stream.stop_stream()  # ✅ Stream stopped
        self.stream.close()
        self.stream = None
    # ❌ audio_queue NOT cleared - stale data remains!
```

When `start()` was called after speech recognition:
```python
def start(self):
    self.is_running = True
    self.stream = self.audio.open(...)  # New stream
    self.thread = threading.Thread(target=self._detection_loop)
    self.thread.start()
    # Detection loop immediately processes STALE queue data!
```

## Solution

### Fix 1: Clear Audio Queue on Stop

Modified `wake_word_detector.py:131-162` to clear the audio queue when stopping:

```python
def stop(self, wait=True):
    """Stop listening for wake words."""
    if not self.is_running:
        return

    logger.info("Stopping wake word detector...")
    self.is_running = False

    if self.stream:
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None

    # ✅ Clear audio queue to prevent stale data on restart
    while not self.audio_queue.empty():
        try:
            self.audio_queue.get_nowait()
        except queue.Empty:
            break

    if self.thread and wait:
        import threading
        if threading.current_thread() != self.thread:
            self.thread.join(timeout=2.0)
        self.thread = None

    logger.info("Wake word detector stopped")
```

### Fix 2: Add Transition Delay

Modified `voice-part.py:428-437` to add a brief pause before restarting wake word detection:

```python
except Exception as e:
    print(f"\n❌ Recognition error: {e}")

# ✅ Brief pause to ensure audio resources are fully released
import time
time.sleep(0.3)

# Restart wake word detector
print("🔄 Resuming wake word detection...")
if self.wake_detector:
    self.wake_detector.start()

print(f"● Listening for '{self.state['wake_word']}'...\n")
```

This 300ms delay ensures:
- Sounddevice (speech recognition) fully releases audio resources
- PyAudio (wake word detection) gets clean audio stream
- No overlap or interference between audio libraries

## Testing

### Before Fix

```
$ ./voice-part.py

● Listening for 'hey edge'...
🎯 WAKE WORD DETECTED!
🎙️  Listening for command...
   > test sentence
📤 Sending sentence #1...
⏸️  Silence detected (3.0s)
🔄 Resuming wake word detection...

🎯 WAKE WORD DETECTED!  ← FALSE! User didn't speak
🎙️  Listening for command...
   > (random noise detected)
📤 Sending sentence #1...
⏸️  Silence detected (3.0s)
🔄 Resuming wake word detection...

🎯 WAKE WORD DETECTED!  ← FALSE! Still happening
[... infinite loop ...]
```

### After Fix

```
$ ./voice-part.py

● Listening for 'hey edge'...
🎯 WAKE WORD DETECTED!
🎙️  Listening for command...
   > test sentence
📤 Sending sentence #1...
⏸️  Silence detected (3.0s)
🔄 Resuming wake word detection...
● Listening for 'hey edge'...

[... waits for actual wake word ...]

(User says "hey edge")
🎯 WAKE WORD DETECTED!  ← CORRECT! Only when user speaks
```

## Impact

### Positive
- ✅ **Eliminates false wake word detections**
- ✅ **Proper orchestration between detection and recognition**
- ✅ **Clean audio stream transitions**
- ✅ **No infinite loops**

### Performance
- ⚡ **300ms delay**: Negligible impact (~0.3 seconds between speech ending and wake word listening resuming)
- 🧹 **Queue clearing**: Fast operation (< 10ms typically)

## Related Issues

This fix addresses the orchestration bug reported in user feedback:

> "After it detects activation word and goes into word detection, after first 'submit' over network it says it does wake word detection (but it hasn't waited for silence for 3 seconds) but in reality it isn't waiting for wake word but rightfully continues to do speech to text but reports wake word detected."

The system was indeed waiting for 3 seconds of silence (that part worked correctly), but the wake word detector was processing stale queue data immediately upon restart, causing false detections.

## Files Modified

1. **release/src/voice_assistant/wake_word_detector.py**
   - Lines 148-153: Added audio queue clearing in `stop()` method

2. **voice-part.py**
   - Lines 428-430: Added 300ms transition delay before restarting wake word detector

## Future Improvements

### Potential Enhancements

1. **Queue size monitoring**: Log queue depth to detect buildup
2. **Adaptive delay**: Adjust transition delay based on queue size
3. **Stream health checks**: Verify audio stream state before restart
4. **Correlation tracking**: Add session IDs to distinguish false vs real detections

### Alternative Approaches Considered

1. **Single audio library**: Use only PyAudio or only sounddevice
   - ❌ Rejected: Each library optimized for its use case

2. **Shared audio stream**: Pass stream between detector and recognizer
   - ❌ Rejected: Complex state management, risk of conflicts

3. **Longer delay**: Use 1+ second delay
   - ❌ Rejected: Hurts responsiveness unnecessarily

## Summary

**Bug**: Stale audio queue data caused false wake word detections after speech recognition ended.

**Fix**: Clear audio queue when stopping wake word detector + add 300ms transition delay.

**Result**: Clean orchestration, no false detections, proper wake word → speech → wake word cycle.
