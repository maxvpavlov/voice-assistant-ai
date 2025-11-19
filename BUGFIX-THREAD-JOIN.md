# Thread Join Deadlock Fix

## Problem

After wake word detection, the speech recognition microphone wouldn't activate. The error log showed:

```
🎯 WAKE WORD DETECTED! (51.7%)
🎙️  Listening for command... (speak now)
⏸️  Pausing wake word detection...
INFO:voice_assistant.wake_word_detector:Stopping wake word detector...
ERROR:voice_assistant.wake_word_detector:Error in detection callback: cannot join current thread
```

Speech recognition never started because the callback crashed.

### Root Cause

**Threading deadlock** - The detection callback was trying to stop its own thread:

1. Wake word detected in detection thread
2. Callback (`on_wake_word_detected`) is called **from within** detection thread
3. Callback calls `wake_detector.stop()`
4. `stop()` tries to `thread.join()` on the detection thread
5. **Deadlock**: Thread cannot join itself
6. Python raises: `RuntimeError: cannot join current thread`
7. Callback crashes, speech recognition never starts

### Thread Execution Flow

```
Main Thread:
  └─ Creates WakeWordDetector
      └─ Starts detection_thread

detection_thread:
  └─ Audio callback loop
      └─ Detects wake word
          └─ Calls on_wake_word_detected()  ← WE ARE HERE
              └─ Calls wake_detector.stop()
                  └─ Calls self.thread.join()  ← TRYING TO JOIN OURSELVES!
                      └─ ❌ RuntimeError: cannot join current thread
```

## Solution

Modified `WakeWordDetector.stop()` to accept a `wait` parameter that prevents thread join when called from within the callback.

### Changes Made

**1. wake_word_detector.py:131-155** - Added `wait` parameter:

```python
def stop(self, wait=True):
    """Stop listening for wake words.

    Args:
        wait: If True, waits for thread to finish. Set to False when calling from callback.
    """
    if not self.is_running:
        return

    logger.info("Stopping wake word detector...")
    self.is_running = False

    if self.stream:
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None

    if self.thread and wait:
        # Check if we're being called from the detection thread itself
        import threading
        if threading.current_thread() != self.thread:
            self.thread.join(timeout=2.0)
        self.thread = None

    logger.info("Wake word detector stopped")
```

**2. voice-part.py:376-379** - Call with `wait=False` from callback:

```python
# Temporarily stop wake word detector to free microphone
if self.wake_detector:
    print("⏸️  Pausing wake word detection...")
    # Don't wait for thread since we're being called FROM that thread
    self.wake_detector.stop(wait=False)
```

## How It Works

### Before Fix

```
detection_thread executes callback
  ├─ Callback calls stop()
  ├─ stop() calls thread.join()
  ├─ Thread tries to wait for itself to finish
  └─ ❌ Deadlock / RuntimeError
```

### After Fix

```
detection_thread executes callback
  ├─ Callback calls stop(wait=False)
  ├─ stop() sets is_running = False
  ├─ stop() closes audio stream
  ├─ stop() SKIPS thread.join() (wait=False)
  ├─ Callback returns
  ├─ Detection loop sees is_running = False
  └─ ✅ Thread exits naturally
```

## Technical Details

### Why This Works

1. **Non-blocking stop**: Setting `is_running = False` signals the thread to exit
2. **Stream cleanup**: Audio stream is closed immediately, freeing microphone
3. **Natural exit**: Thread exits on next loop iteration (checking `is_running`)
4. **No deadlock**: We don't wait for thread to finish when we're IN that thread
5. **Clean restart**: When `start()` is called again, it creates a fresh thread

### When to Use `wait` Parameter

- `wait=True` (default): Called from main thread or another thread
  - Blocks until detection thread fully stops
  - Safe cleanup

- `wait=False`: Called from detection thread callback
  - Non-blocking, signals thread to exit
  - Avoids deadlock

## Testing

**Expected behavior:**

```bash
./voice-part.py -y

● Listening for: 'hey edge'
Ready! Say your wake word to activate.

[Say "hey edge"]

🎯 WAKE WORD DETECTED! (51.7%)
🎙️  Listening for command... (speak now)
⏸️  Pausing wake word detection...
INFO:voice_assistant.wake_word_detector:Stopping wake word detector...
INFO:voice_assistant.wake_word_detector:Wake word detector stopped
🎤 Listening...
   ... your speech here
📝 Transcript: 'your speech here'
🔄 Resuming wake word detection...
INFO:voice_assistant.wake_word_detector:Starting wake word detector...
● Listening for 'hey edge'...
```

## Files Modified

- `src/voice_assistant/wake_word_detector.py:131-155` - Added `wait` parameter to `stop()`
- `voice-part.py:376-379` - Call `stop(wait=False)` from callback

## Related Concepts

- **Threading deadlock**: Thread waiting for itself
- **Context switching**: Callback executes in caller's thread context
- **Graceful shutdown**: Signaling thread to exit vs forcing termination
- **Resource cleanup**: Stream must close before thread joins

## Prevention

To avoid similar issues in the future:

1. ✅ Never call `thread.join()` from within that same thread
2. ✅ Use flags (`is_running`) for graceful thread termination
3. ✅ Provide non-blocking variants of blocking operations
4. ✅ Document which thread context functions are called from
