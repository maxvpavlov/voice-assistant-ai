# Complete Training Guide for Custom Wake Words

This guide covers all methods for training custom wake words, from beginner-friendly to advanced.

## 🎯 Quick Comparison

| Method | Time | Samples | Best For | Complexity |
|--------|------|---------|----------|------------|
| **Guided Training** | 5-10 min | 5 (auto-augmented to 84) | First-time users | ⭐ Easy |
| Custom Verifier | 2-3 min | 5-100 | Quick prototypes | ⭐⭐ Medium |
| Full Model Training | 5-15 min | 5+ (auto-augmented) | Production quality | ⭐⭐⭐ Advanced |

---

## Method 1: Guided Training (🆕 Recommended)

### What It Does
- **Interactive step-by-step process**
- Records 5 samples from your voice
- Generates 80+ synthetic variations automatically
- Trains a full neural network
- Tests the model with you

### Usage

```bash
./guided-training.py
```

Just follow the on-screen prompts! The script will:
1. Ask for your wake word
2. Test your microphone
3. Guide you through recording 5 samples
4. Generate synthetic data (pitch shifts, speed changes, noise)
5. Train a model (~3 minutes)
6. Let you test it immediately

### Technical Details
- **Positive samples**: 5 real + 80 synthetic = 84 total
- **Negative samples**: 252 (random, shuffled, transformed)
- **Training samples**: 336 total (84 positive, 252 negative)
- **Model**: PyTorch neural network exported to ONNX
- **Augmentation**: Pitch (±2 semitones), speed (95-105%), noise, volume (85-115%)

### Output
```
training_data/{wake_word}/positive/    # Your recorded samples
trained_models/{wake_word}/            # Full training artifacts
models/{wake_word}_v0.1.onnx          # Deployed model
```

### Testing Your Model
```bash
./edge-wake-word test --model models/{wake_word}_v0.1.onnx --threshold 0.5
```

---

## Method 2: Custom Verifier (Quick Training)

### What It Does
- Uses existing base model (e.g., "alexa", "hey_jarvis")
- Trains a lightweight verifier on top
- Fast training (seconds)
- Good for prototyping

### Limitations
⚠️ **Important**: Requires base model to activate first!
- "hey edge" won't work with "alexa" base model (too different)
- Best for wake words similar to existing models
- Example: "hey jarvis" base → "hey jacob" custom

### Usage

```bash
# Step 1: Record samples
./edge-wake-word train --wake-word "hey jacob" --num-samples 50

# Step 2: Train verifier
./edge-wake-word train-local --wake-word "hey jacob" --base-model hey_jarvis

# Step 3: Test
./edge-wake-word test-custom --wake-word "hey jacob" --base-model hey_jarvis
```

### Technical Details
- Uses openWakeWord's Custom Verifier approach
- Trains logistic regression on base model features
- Minimum 3-5 samples (50-100 recommended)
- Speaker-specific model

---

## Method 3: Full Model Training (Advanced)

### What It Does
- Trains a complete neural network from scratch
- Most flexible - works with any wake word
- Requires more setup but highest quality

### Prerequisites

```bash
# Install training dependencies (one-time, ~500MB)
pip install -r requirements-training.txt
```

This installs:
- PyTorch 2.0+
- torchmetrics
- scipy
- onnxscript

### Usage

```bash
# Step 1: Record samples (manual)
./edge-wake-word train --wake-word "computer activate" --num-samples 5

# Step 2: Train with synthetic augmentation
python3 train-full-model.py --wake-word "computer activate" --epochs 50 --augmentations 20

# Step 3: Copy model to deployment directory
cp trained_models/computer_activate/computer_activate_v0.1.onnx* models/

# Step 4: Test
./edge-wake-word test --model models/computer_activate_v0.1.onnx --threshold 0.5
```

### Advanced Options

```bash
# More augmentations (slower but potentially better)
python3 train-full-model.py --wake-word "my phrase" --augmentations 50

# More training epochs
python3 train-full-model.py --wake-word "my phrase" --epochs 100

# Custom output directory
python3 train-full-model.py --wake-word "my phrase" --output-dir ./my_models
```

### Technical Details

**Synthetic Data Generation** (following openWakeWord Colab approach):
- **Pitch shifting**: ±2 semitones (50% chance per sample)
- **Time stretching**: 95-105% speed (50% chance)
- **Noise injection**: 0.2-0.8% Gaussian noise (70% chance)
- **Volume variation**: 85-115% amplitude (always applied)

**Negative Sample Strategies**:
1. Random Gaussian: Simulates silence/random audio
2. Shuffled features: Destroys temporal patterns
3. Transformed features: Scaled/shifted to represent other speech

**Model Architecture**:
- Input: (16, 96) feature embeddings from openWakeWord
- Hidden layers: 2x 128 units with LayerNorm + ReLU + Dropout(0.3)
- Output: Single neuron with sigmoid activation
- Loss: Binary cross-entropy
- Optimizer: Adam with learning rate 0.001

---

## Best Practices

### Recording Quality
1. **Environment**: Record where you'll use the device
2. **Consistency**: Speak naturally but clearly
3. **Variation**: Try different volumes, speeds, tones
4. **Distance**: Vary your distance from microphone
5. **Quiet**: Minimize background noise during recording

### Sample Counts

| Purpose | Recommended Samples |
|---------|-------------------|
| Quick demo | 5 samples |
| Testing/prototyping | 10-20 samples |
| Personal use | 50 samples |
| Production | 100+ samples |

### Improving Accuracy

1. **Record more samples**: More diverse data = better accuracy
2. **Include negatives**: Use `--with-negatives` flag
3. **Adjust threshold**: Lower = more sensitive, higher = more precise
4. **Retrain periodically**: Add samples and retrain
5. **Test thoroughly**: Various volumes, distances, environments

---

## Troubleshooting

### Model constantly detects (false positives)

**Cause**: Overfitting - model too simple or not enough negative data

**Solution**:
- Use guided training or full model training (better negative samples)
- Increase threshold: `--threshold 0.7`
- Record with `--with-negatives`

### Model never detects (false negatives)

**Cause**: Model is too strict or training samples didn't capture your voice well

**Solution**:
- Lower threshold: `--threshold 0.3`
- Record more samples with variation
- Check microphone quality
- Ensure samples are clear and loud enough

### "Base model doesn't activate" error (Custom Verifier)

**Cause**: Wake word too different from base model

**Solution**:
- Use full model training instead: `python3 train-full-model.py`
- Or choose wake word similar to base model
- Or use guided training (handles this automatically)

### Training very slow

**Cause**: CPU-only training with PyTorch

**Expected**:
- 50 epochs with 84 samples: ~3-5 minutes on M4 Mac
- 50 epochs with 84 samples: ~5-10 minutes on Raspberry Pi 5

**Optimization**:
- Reduce epochs: `--epochs 30`
- Reduce augmentations: `--augmentations 10`
- Use smaller sample count (for quick prototypes)

---

## Comparison with Cloud Training (Colab)

### Cloud Training (Original Colab Notebook)
✅ Uses large pretrained embeddings (~2000 hours ACAV100M)
✅ Can download background noise (AudioSet, FMA)
✅ Uses Piper TTS for unlimited synthetic samples
❌ Requires internet connection
❌ Requires Google account
❌ Privacy concerns (samples uploaded to cloud)

### Local Training (Our Implementation)
✅ **100% local** - no internet needed after setup
✅ **Private** - your voice never leaves your device
✅ Works on Mac and Raspberry Pi
✅ Instant feedback
✅ Guided experience
✅ Same augmentation techniques (pitch, speed, noise, volume)
✅ Similar negative sampling strategies
⚠️ Uses smaller dataset (your samples only)
⚠️ No TTS generation (uses real samples with augmentation)

**Result**: Good accuracy with 5-10 samples, excellent with 50-100 samples!

---

## Next Steps After Training

### 1. Integration into Applications

```python
from voice_assistant import WakeWordDetector

def on_wake_word(word, confidence):
    print(f"Activated! {word} ({confidence:.2%})")
    # Your code here

detector = WakeWordDetector(
    wake_words=["models/my_wake_word_v0.1.onnx"],
    threshold=0.5,
    on_detection=on_wake_word
)
detector.start()
```

### 2. Production Deployment

```bash
# Run as service
./edge-wake-word run --model models/my_wake_word_v0.1.onnx --threshold 0.6 --quiet
```

### 3. Continuous Improvement

- Collect edge cases (false positives/negatives)
- Add them as training samples
- Retrain periodically
- A/B test different thresholds

---

## Summary

- **Start with Guided Training** (`./guided-training.py`) - easiest option
- **Use Custom Verifier** for quick prototypes with similar wake words
- **Use Full Training** for any wake word or production quality
- **Record 50-100 samples** for best results
- **Test thoroughly** in your actual use environment
- **Adjust threshold** to balance sensitivity vs false positives

Happy training! 🎉
