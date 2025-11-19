# Wake Word Detection Troubleshooting Guide

Complete guide for fixing wake word detection issues.

## Quick Diagnosis

If your wake word isn't triggering, follow these steps:

### Step 1: Run the Diagnostic Tool

```bash
./diagnose-wake-word.py
```

This will test your model at different threshold levels and tell you exactly what's wrong.

### Step 2: Interpret Results

**Scenario A: No detections at any threshold**
- **Problem**: Model quality is poor
- **Solution**: Retrain with more samples (see below)

**Scenario B: Detections only at 0.2-0.3**
- **Problem**: Model is weak but functional
- **Solution**: Lower the threshold OR retrain

**Scenario C: Detections at 0.4-0.6**
- **Problem**: None - model is working well!
- **Solution**: Current threshold (0.5) should work

## Common Issues and Solutions

### Issue 1: Wake Word Never Triggers

**Symptoms**:
- Say the wake word multiple times
- Nothing happens
- No detection message

**Causes**:
1. Model trained with too few samples (5 is minimum, not ideal)
2. Training samples were inconsistent
3. Threshold too high

**Solutions**:

#### Option A: Lower the Threshold (Quick Fix)

```bash
# Try threshold 0.3 instead of 0.5
./voice-part.py --threshold 0.3
```

Or edit `.voice-assistant-state.json`:
```json
{
  "detection_threshold": 0.3
}
```

#### Option B: Retrain with More Samples (Best Fix)

```bash
./voice-part.py --retrain
```

The system now records **15 samples** instead of 5. Tips for better training:

1. **Vary your voice**:
   - Some samples louder, some quieter
   - Some faster, some slower
   - Different emotional tones

2. **Be consistent**:
   - Always say the exact wake word
   - Don't add extra words
   - Maintain clear pronunciation

3. **Good environment**:
   - Quiet room (minimal background noise)
   - 1-2 feet from microphone
   - No music or TV playing

### Issue 2: False Positives

**Symptoms**:
- Wake word triggers on random sounds
- Activates when you say similar words
- Triggers too frequently

**Cause**: Threshold too low

**Solution**:

```bash
# Increase threshold to 0.6 or 0.7
./voice-part.py --threshold 0.6
```

### Issue 3: Inconsistent Detection

**Symptoms**:
- Sometimes works, sometimes doesn't
- Works when you speak loudly but not softly
- Works at certain speeds only

**Cause**: Training data lacked variety

**Solution**: Retrain with varied samples:

```bash
./voice-part.py --retrain
```

When recording the 15 samples:
- Samples 1-5: Normal volume and speed
- Samples 6-10: Quieter or faster
- Samples 11-15: Louder or slower

### Issue 4: Model File Missing

**Symptoms**:
```
ValueError: Could not find pretrained model for model name 'models/hey_xxx_v0.1.onnx'
```

**Cause**: Training completed but model wasn't copied correctly

**Solution**:

```bash
# Check if model exists in trained_models
ls trained_models/hey_xxx/

# Copy manually if needed
cp trained_models/hey_xxx/hey_xxx_v0.1.onnx models/
cp trained_models/hey_xxx/hey_xxx_v0.1.onnx.data models/
```

### Issue 5: Can't Switch Wake Words

**Symptoms**:
- Trained a new wake word
- System still uses old one

**Solution**:

```bash
# Start fresh with new wake word
./voice-part.py --wake-word "hey friday"
```

Or choose option 1 when prompted (Train a NEW wake word).

## Best Practices for Training

### Recording Environment

✅ **Do**:
- Use a quiet room
- Stand 1-2 feet from microphone
- Test microphone first (microphone test in training)
- Close windows (reduce outside noise)

❌ **Don't**:
- Have TV/music playing
- Train in noisy environment
- Be too far from microphone (>3 feet)
- Have fan or AC running loudly

### Sample Quality

✅ **Do**:
- Speak clearly and naturally
- Say the exact wake word each time
- Vary your tone and speed across samples
- Record 15 samples (new default)

❌ **Don't**:
- Whisper or shout
- Say extra words ("um, hey edge")
- Rush through all samples identically
- Skip samples or use fewer than recommended

### Wake Word Choice

✅ **Good Wake Words**:
- "hey edge" (2 syllables, distinct sounds)
- "hey friday" (3 syllables, clear)
- "hello robot" (4 syllables, very distinct)

❌ **Problematic Wake Words**:
- "ok" (too short, 1 syllable)
- Common words like "the" or "and"
- Words that sound like common speech

## Advanced Troubleshooting

### Check Model Output Manually

If the diagnostic tool doesn't help, you can check the model's raw predictions:

```bash
# Install required dependencies
source venv/bin/activate
pip install librosa

# Play one of your training samples and check what the model predicts
# (This requires you to write a simple test script - see test_model.py)
```

### Increase Training Epochs

The default is 50 epochs. For difficult wake words, try more:

```bash
# After recording samples, manually train with more epochs
source venv/bin/activate
python3 train-full-model.py --wake-word "hey bender" --epochs 100 --augmentations 30
```

Then copy the model:
```bash
cp trained_models/hey_bender/hey_bender_v0.1.onnx models/
cp trained_models/hey_bender/hey_bender_v0.1.onnx.data models/
```

### Check Audio Input Device

Make sure the right microphone is being used:

```bash
# macOS: System Settings > Sound > Input
# Linux: pavucontrol or alsamixer
# Raspberry Pi: arecord -l
```

### Review Training Data

Listen to your recorded samples:

```bash
# Play your training samples
afplay training_data/hey_xxx/positive/positive_0001.wav
afplay training_data/hey_xxx/positive/positive_0002.wav
# ... etc
```

If samples sound:
- Too quiet → Record again closer to mic
- Distorted → Lower input volume
- Have background noise → Find quieter environment

## Command Reference

### Training Commands

```bash
# Train new wake word (15 samples, interactive)
./voice-part.py

# Retrain existing wake word
./voice-part.py --retrain

# Force retrain without prompts
./voice-part.py --retrain --yes

# Train with specific wake word
./voice-part.py --wake-word "hey friday"
```

### Testing Commands

```bash
# Run diagnostic (tests thresholds 0.2-0.6)
./diagnose-wake-word.py

# Test with specific threshold
./voice-part.py --threshold 0.3

# Test with lower silence timeout (faster response)
./voice-part.py --silence-timeout 2.0
```

### State Management

```bash
# View current configuration
cat .voice-assistant-state.json

# Reset to defaults (delete state file)
rm .voice-assistant-state.json
```

## Threshold Tuning Guide

The detection threshold determines how confident the model must be before triggering.

| Threshold | Use Case | Trade-off |
|-----------|----------|-----------|
| 0.2-0.3 | Weak model or maximum sensitivity | More false positives |
| 0.4-0.5 | Balanced (default) | Good for most cases |
| 0.6-0.7 | Strong model or minimal false positives | Might miss some detections |
| 0.8+ | Extreme precision | Very difficult to trigger |

**Recommendation**: Start at 0.5, then adjust based on results.

## Training Data Volume Guide

More samples = better model, but diminishing returns:

| Samples | Quality | Training Time | Recommendation |
|---------|---------|---------------|----------------|
| 5 | Minimum | ~3 min | Only for testing |
| 15 | Good | ~5 min | **Default, recommended** |
| 30 | Better | ~10 min | For production use |
| 50+ | Best | ~15+ min | Overkill for most cases |

The system now uses **15 samples by default** (changed from 5).

## Synthetic Augmentation

The training process automatically creates synthetic variations:

- **20x augmentation** (default)
- 15 original samples × 20 augmentations = **300 training samples**
- Techniques: pitch shift, time stretch, noise injection, volume variation

This helps the model generalize to different speaking styles.

## Getting Help

If none of these solutions work:

1. Run the diagnostic: `./diagnose-wake-word.py`
2. Check training samples: `ls -la training_data/hey_xxx/positive/`
3. Verify model exists: `ls -la models/hey_xxx_v0.1.onnx*`
4. Check state file: `cat .voice-assistant-state.json`
5. Review logs for errors

## Common Error Messages

### "Could not find pretrained model"

```
ValueError: Could not find pretrained model for model name 'models/hey_xxx_v0.1.onnx'
```

**Fix**: Model file missing. Copy from `trained_models/` to `models/`:
```bash
cp trained_models/hey_xxx/hey_xxx_v0.1.onnx* models/
```

### "No such file or directory: .onnx.data"

```
filesystem error: in file_size: No such file or directory ["models/hey_xxx_v0.1.onnx.data"]
```

**Fix**: Missing companion .data file:
```bash
cp trained_models/hey_xxx/hey_xxx_v0.1.onnx.data models/
```

### "Missing dependency: No module named 'yaml'"

```
❌ Missing dependency: No module named 'yaml'
```

**Fix**: Install training dependencies:
```bash
source venv/bin/activate
pip install pyyaml
```

### "AudioRecorder.record_sample() got an unexpected keyword argument"

```
TypeError: AudioRecorder.record_sample() got an unexpected keyword argument 'sample_type'
```

**Fix**: Update to latest voice-part.py (this was fixed in recent commit)

## Summary: Recommended Workflow

1. **Initial Training**:
   ```bash
   ./voice-part.py
   # Record 15 samples, vary tone/speed/volume
   ```

2. **Test Detection**:
   ```bash
   ./voice-part.py --threshold 0.5
   # Try saying wake word
   ```

3. **If Not Working**:
   ```bash
   # Run diagnostic
   ./diagnose-wake-word.py

   # If weak: lower threshold
   ./voice-part.py --threshold 0.3

   # OR: retrain with more care
   ./voice-part.py --retrain
   ```

4. **Fine-Tune**:
   - Adjust threshold based on false positive/negative rate
   - Retrain if model quality is fundamentally poor
   - Use 0.3-0.4 for challenging wake words
   - Use 0.5-0.6 for well-trained models

The key is: **Good training data >> threshold tuning**. If the model is poorly trained, no amount of threshold adjustment will fix it.
