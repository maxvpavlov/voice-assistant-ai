# Vosk Utterance Detection

Understanding how Vosk detects sentence boundaries and when to send transcripts for processing.

## How It Works

### Two-Level Detection System

Our implementation uses **two complementary methods**:

1. **Vosk's Built-in Sentence Detection** (Primary)
2. **Silence Timeout** (Fallback)

### Vosk Sentence Detection

Vosk's `AcceptWaveform()` method returns `True` when it detects a **natural sentence boundary**.

**What you see:**
```
🎤 Listening...
   ... turn on the lights        ← Partial (in-progress)
   > turn on the lights          ← Final (sentence complete!)
   ... and set temperature       ← Partial (continuing)
   > and set temperature         ← Final (another sentence!)
```

**In the code** (`vosk_recognizer.py:117-126`):
```python
if self.recognizer.AcceptWaveform(data):
    # Vosk detected a sentence boundary
    result = json.loads(self.recognizer.Result())
    text = result.get("text", "").strip()

    if text:
        transcript_parts.append(text)  # Collect completed sentences
        print(f"   > {text}")           # Show final result
```

### Silence Detection (Fallback)

If user stops speaking without clear sentence boundaries, the **3-second silence timeout** triggers.

**What you see:**
```
🎤 Listening...
   ... hello there
   ... hello there
   ... hello there
⏸️  Silence detected (3.0s)      ← Timeout triggered
```

**In the code** (`vosk_recognizer.py:141-147`):
```python
if recognition_started:
    silence_duration = time.time() - last_speech_time

    if silence_duration > silence_timeout:
        print(f"\n⏸️  Silence detected ({silence_timeout}s)")
        break  # Stop recognition, send transcript
```

## Vosk's Detection Signals

Vosk uses multiple acoustic and linguistic features:

### 1. Acoustic Pause Detection
- Detects silence/low energy regions
- Typical pause: 200-500ms
- Distinguishes from within-word pauses

### 2. Language Model Patterns
- Recognizes grammatical sentence structures
- Identifies natural phrase boundaries
- Uses n-gram probabilities

### 3. Prosodic Features
- Pitch dropping at sentence end
- Speaking rate changes
- Energy contour patterns

### 4. Decoder Confidence
- High confidence in current hypothesis
- Low probability of continuation
- Stable recognition state

## Output Format

### Partial Results
While still speaking or processing:

```json
{
  "partial": "turn on the"
}
```

**Displayed as:**
```
   ... turn on the
```

**Characteristics:**
- Updates in real-time
- May change as more audio arrives
- Not sentence-complete
- Use for UI feedback, not processing

### Final Results
When sentence boundary detected:

```json
{
  "text": "turn on the lights"
}
```

**Displayed as:**
```
   > turn on the lights
```

**Characteristics:**
- Sentence is complete
- Won't change
- Ready for processing
- This is what gets sent to inference

## Current Implementation Flow

```
Wake Word Detected
       ↓
Start Vosk Recognition
       ↓
[Loop] Feed audio → Vosk
       ↓
   ┌────────────────────┐
   │ AcceptWaveform()   │
   └─────┬──────────────┘
         │
    ┌────┴────┐
    │ False   │  True
    │         │
    ↓         ↓
Partial    Final Result
Result     → Add to transcript
→ Display  → Display with ">"
→ Continue → Continue listening

       ↓
Check Silence Timeout (3s)
       ↓
   ┌────────────────┐
   │ Timeout?       │
   └─────┬──────────┘
         │
    ┌────┴────┐
    │ No      │  Yes
    │         │
    ↓         ↓
Continue    Stop Recognition
Loop        ↓
         Combine all final results
         ↓
         Return full transcript
         ↓
         Send to inference endpoint
```

## Optimization Options

### Option 1: Faster Response (Less Text)

Stop after **first sentence** instead of waiting for silence:

```python
# In vosk_recognizer.py:117-127
if self.recognizer.AcceptWaveform(data):
    result = json.loads(self.recognizer.Result())
    text = result.get("text", "").strip()

    if text:
        transcript_parts.append(text)
        print(f"   > {text}")

        # NEW: Stop after first complete sentence
        break  # Immediately return instead of continuing
```

**Effect:**
- User says: "turn on the lights and set temperature to 70"
- **Current**: Waits for 3s silence, gets full command
- **Modified**: Stops after "turn on the lights", misses rest

**Use case**: Quick single commands

### Option 2: Variable Timeout

Adjust timeout based on context:

```python
# Short timeout for simple commands
./voice-part.py --silence-timeout 1.5

# Long timeout for complex requests
./voice-part.py --silence-timeout 5.0
```

**Effect:**
- 1.5s: Faster response, might cut off long sentences
- 5.0s: More complete text, slower response

### Option 3: Vosk-Only (No Silence Timeout)

Remove silence detection, rely only on Vosk:

```python
# Remove lines 141-147 in vosk_recognizer.py
# Keep only max_duration check
```

**Effect:**
- Respects natural speech patterns
- No artificial timeout
- Waits for user to stop talking naturally
- Risk: Never stops if user doesn't pause properly

### Option 4: Punctuation-Based

Stop on sentence-ending punctuation:

```python
if text and text.endswith(('.', '!', '?')):
    # Sentence clearly ended
    transcript_parts.append(text)
    break
```

**Note**: Vosk doesn't add punctuation by default, would need post-processing.

## Recommended Settings

### For Short Commands (Smart Home)
```bash
./voice-part.py --silence-timeout 2.0
```
- Quick response (2 seconds)
- Good for "turn on lights", "set temperature"
- Less waiting time

### For Long Queries (Conversational)
```bash
./voice-part.py --silence-timeout 4.0
```
- More patient (4 seconds)
- Good for "search for Italian restaurants near me with outdoor seating"
- Captures complex requests

### For Dictation/Transcription
```bash
./voice-part.py --silence-timeout 5.0
```
- Very patient (5 seconds)
- Multiple sentences
- Long-form content

## Example Session

### Scenario 1: Quick Command
```
User: "Hey edge"
🎯 WAKE WORD DETECTED!
🎙️  Listening for command...
⏸️  Pausing wake word detection...
🎤 Listening...

User: "turn on the lights"
   ... turn on the
   ... turn on the lights
   > turn on the lights          ← Vosk detected sentence end
[waits ~1 second for more]
⏸️  Silence detected (3.0s)

📝 Transcript: 'turn on the lights'
```

### Scenario 2: Multi-Sentence
```
User: "Hey edge"
🎯 WAKE WORD DETECTED!
🎙️  Listening for command...
🎤 Listening...

User: "turn on the lights. set temperature to 70 degrees."
   ... turn on the
   ... turn on the lights
   > turn on the lights          ← First sentence
   ... set temperature
   ... set temperature to seventy
   ... set temperature to seventy degrees
   > set temperature to seventy degrees  ← Second sentence
[waits 3 seconds]
⏸️  Silence detected (3.0s)

📝 Transcript: 'turn on the lights set temperature to seventy degrees'
```

## Technical Details

### Vosk Decoder States

Vosk uses a **Finite State Transducer (FST)** decoder:

1. **Active State**: Processing audio, building hypotheses
2. **Final State**: Reached sentence boundary, stable hypothesis
3. **Partial State**: Mid-sentence, hypothesis may change

`AcceptWaveform()` returns `True` when transitioning to **Final State**.

### Timing Characteristics

| Event | Typical Latency |
|-------|-----------------|
| Partial result update | ~80-100ms |
| Final result (sentence) | ~200-500ms after pause |
| Silence timeout (3s) | 3000ms after last speech |
| Total response time | 3.2-3.5s typical |

## Best Practices

### For UI Feedback
- ✅ Show partial results (`... text`)
- ✅ Update in real-time
- ✅ Clear visual distinction from final results

### For Processing
- ✅ Only use final results (`> text`)
- ✅ Collect all final results before timeout
- ✅ Send combined transcript to inference

### For User Experience
- ✅ Keep timeout reasonable (2-4s)
- ✅ Give visual feedback on listening state
- ✅ Show when silence detected

## Comparison to Other Approaches

### Vosk (Current)
- ✅ Natural sentence boundaries
- ✅ Real-time partial results
- ✅ Offline, no network
- ⚠️ No punctuation
- ⚠️ Requires silence for final result

### Alternative: Voice Activity Detection (VAD)
- ✅ Detects speech/non-speech
- ❌ Doesn't understand sentences
- ❌ Cuts off mid-sentence easily

### Alternative: Fixed Duration
- ✅ Predictable timing
- ❌ Cuts off long sentences
- ❌ Wastes time on short sentences

### Our Hybrid Approach (Best)
- ✅ Vosk detects sentence boundaries naturally
- ✅ Silence timeout prevents hanging
- ✅ Collects multiple sentences if spoken quickly
- ✅ Responsive yet complete

## Summary

**What the arrows mean:**
- `... text` = Still processing (partial)
- `> text` = Sentence complete (final)

**When transcript is sent:**
- After 3 seconds of silence (default)
- Includes all `> text` results
- Multiple sentences collected if spoken continuously

**Tuning:**
- Shorter timeout = Faster but might cut off
- Longer timeout = More complete but slower response
- Current 3s is good balance for most use cases
