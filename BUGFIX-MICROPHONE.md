# Microphone Conflict Fix

## Problem

After wake word detection triggered speech recognition, the microphone would not resume listening for the wake word. The logs showed "Listening for 'hey edge'..." but no audio was being captured.

### Root Cause

Both the WakeWordDetector and VoskRecognizer were trying to use the microphone simultaneously:

1. WakeWordDetector opens PyAudio stream on startup
2. Wake word detected → callback fired
3. VoskRecognizer.recognize_stream() opens its own sounddevice stream
4. **Conflict**: Two streams competing for same microphone
5. After speech recognition completes, WakeWordDetector's stream was broken/inactive

## Solution

Modified `voice-part.py` to pause and resume the wake word detector:

### Changes Made

**1. Store detector reference** (line 479):
```python
self.wake_detector = WakeWordDetector(...)
```

**2. Pause before speech recognition** (lines 371-373):
```python
if self.wake_detector:
    print("⏸️  Pausing wake word detection...")
    self.wake_detector.stop()
```

**3. Resume after speech recognition** (lines 395-397):
```python
print("🔄 Resuming wake word detection...")
if self.wake_detector:
    self.wake_detector.start()
```

## Flow

```
[Wake Word Detector Running] → Listening for wake word
          ↓
[Wake Word Detected] → Callback fired
          ↓
[Pause Detector] → Stop audio stream, free microphone
          ↓
[Speech Recognition] → Vosk captures speech (3s timeout)
          ↓
[Send to Inference] → HTTP POST with transcript
          ↓
[Resume Detector] → Restart audio stream
          ↓
[Wake Word Detector Running] → Ready for next activation
```

## Testing

The fix ensures:
- ✅ No microphone conflicts between wake word and speech recognition
- ✅ Clean audio capture for both stages
- ✅ Proper resume after each recognition cycle
- ✅ Clear user feedback (pause/resume messages)

## User Experience

**Before Fix:**
```
🎯 WAKE WORD DETECTED!
🎙️  Listening for command...
   > hello world
📝 Transcript: 'hello world'
● Listening for 'hey edge'...
[❌ Microphone not actually listening - silent failure]
```

**After Fix:**
```
🎯 WAKE WORD DETECTED!
🎙️  Listening for command...
⏸️  Pausing wake word detection...
   > hello world
📝 Transcript: 'hello world'
🔄 Resuming wake word detection...
● Listening for 'hey edge'...
[✅ Microphone actively listening - can detect next wake word]
```

## Technical Details

- **WakeWordDetector**: Uses PyAudio with callback-based streaming
- **VoskRecognizer**: Uses sounddevice with blocking I/O
- **Conflict**: Both libraries try to acquire exclusive microphone access
- **Solution**: Explicit start/stop ensures only one stream active at a time

## Files Modified

- `voice-part.py:356-399` - Added pause/resume logic in callback
- `voice-part.py:479` - Store detector reference as instance variable
- `README.md:224-247` - Updated architecture diagram with pause/resume flow
