# Wake Word Manager - Stateful Training & Inference

## Overview

`wake-word-manager.py` is a stateful management tool that provides:
- **Persistent state tracking** for all trained models
- **Smart detection** of existing training
- **Interactive resume** or retrain options
- **Unified interface** for training and inference

## Key Features

### 1. State Persistence
- Tracks all trained models in `.wake-word-state.json`
- Remembers training details (samples, method, timestamps)
- Survives script restarts
- No need to remember model paths

### 2. Smart Resume
```
User: "I want to train 'hey edge'"
Manager: "You already trained this! Last updated: 2025-11-14"
          Options:
          1. Use existing model (go to inference)
          2. Retrain from scratch
          3. Cancel
```

### 3. Unified Workflow
- Train → Test → Use (all in one session)
- List all models across restarts
- Switch between models easily

## Usage

### Start the Manager

```bash
./wake-word-manager.py
```

### Main Menu

```
What would you like to do?
  1. Train a new wake word
  2. Run wake word detection
  3. List all models
  4. Delete a model
  5. Exit
```

## Workflows

### First-Time Training

```
You → Train a new wake word
Manager → Enter your wake word: computer activate
Manager → 🎙️  Recording training samples...
         [Records 5 samples]
Manager → 🧠 Training neural network...
         [Generates 80+ synthetic variations]
         [Trains model ~3 minutes]
Manager → ✅ Training complete!
Manager → Test the model now? (y/n): y
Manager → 🎙️  Listening... (say "computer activate")
```

### Resuming Existing Training

```
You → Train a new wake word
Manager → Enter your wake word: computer activate

Manager → 📊 Existing Model Found
         Wake Word: 'computer activate'
         Model Path: models/computer_activate_v0.1.onnx
         Last Updated: 2025-11-14
         Training Samples: 5
         Training Method: full_model

Manager → What would you like to do?
         1. Use existing model (go to inference)
         2. Retrain from scratch
         3. Cancel and go back

You → 1 (use existing)
Manager → Detection threshold (default: 0.5): [Enter]
Manager → 🎙️  Listening...
```

### Running Inference on Existing Models

```
You → Run wake word detection

Manager → 📋 Available Models
         1. [✓] hey edge
            Path: models/hey_edge_v0.1.onnx
            Updated: 2025-11-14

         2. [✓] computer activate
            Path: models/computer_activate_v0.1.onnx
            Updated: 2025-11-14

Manager → Select a model: 1
Manager → Detection threshold (default: 0.5): 0.6
Manager → 🎙️  Listening for 'hey edge'...
```

### Listing All Models

```
You → List all models

Manager → 📋 Available Models
         1. [✓] hey edge
            Path: models/hey_edge_v0.1.onnx
            Updated: 2025-11-14

         2. [✗] old model
            Path: models/old_model_v0.1.onnx
            Updated: 2025-11-10
            (model file not found)
```

## State File Structure

`.wake-word-state.json`:

```json
{
  "models": {
    "hey_edge": {
      "model_path": "models/hey_edge_v0.1.onnx",
      "num_samples": 5,
      "method": "full_model",
      "wake_word": "hey edge",
      "last_updated": "2025-11-14T10:23:00.123456"
    },
    "computer_activate": {
      "model_path": "models/computer_activate_v0.1.onnx",
      "num_samples": 10,
      "method": "full_model",
      "wake_word": "computer activate",
      "last_updated": "2025-11-14T15:30:00.654321"
    }
  }
}
```

### Fields Explained

- **Key** (`hey_edge`): Normalized wake word name (lowercase, underscores)
- **model_path**: Path to deployed ONNX model
- **num_samples**: Number of original samples recorded
- **method**: Training method (`full_model` or `verifier`)
- **wake_word**: Original wake word with proper casing/spacing
- **last_updated**: ISO format timestamp of last training

## State Detection Logic

### 1. Check State File
```python
# Does .wake-word-state.json exist?
# Does it contain entry for this wake word?
```

### 2. Check Model Files
```python
# Does models/{wake_word}_v0.1.onnx exist?
# Does trained_models/{wake_word}/{wake_word}_v0.1.onnx exist?
```

### 3. Check Training Data
```python
# Does training_data/{wake_word}/positive/*.wav exist?
# How many samples?
```

### 4. Decision Matrix

| State File | Model File | Training Data | Action |
|------------|------------|---------------|--------|
| ✓ | ✓ | ✓ | Offer resume or retrain |
| ✓ | ✗ | ✓ | Retrain (model missing) |
| ✗ | ✓ | ✓ | Add to state, offer resume |
| ✗ | ✗ | ✓ | Retrain using existing data |
| ✗ | ✗ | ✗ | Fresh training |

## Comparison with Other Scripts

### wake-word-manager.py (New - Stateful)
```
✅ Remembers all models
✅ Detects existing training
✅ Offers smart resume
✅ Multi-session workflow
✅ List/manage models
```

### guided-training.py (Linear)
```
✅ One-shot guided experience
✅ Perfect for first-time users
❌ No state persistence
❌ No resume capability
❌ Single model per session
```

### train-full-model.py (Manual)
```
✅ Direct training control
✅ Advanced options
❌ No state tracking
❌ Manual path management
❌ CLI arguments required
```

## Use Cases

### 1. Iterative Development
```bash
# Session 1: Initial training
./wake-word-manager.py
# Train "hey robot" → Test → Not satisfied

# Session 2: Retrain with more samples
./wake-word-manager.py
# Train "hey robot" → Manager detects existing → Retrain
```

### 2. Multiple Wake Words
```bash
# Morning session
./wake-word-manager.py
# Train "good morning"

# Afternoon session
./wake-word-manager.py
# Train "hey assistant"

# Evening session
./wake-word-manager.py
# List models → Select "good morning" → Test
```

### 3. Production Deployment
```bash
# Development
./wake-word-manager.py
# Train multiple models, test, refine

# Deployment
./wake-word-manager.py
# List models → Select production model → Run
# (Or use inference mode directly)
```

## Advanced Usage

### Non-Interactive Mode (Future)

Currently interactive-only. For automation, use:
```bash
# Direct training (no state)
python3 train-full-model.py --wake-word "my word" --epochs 50

# Direct inference (no state)
./edge-wake-word test --model models/my_word_v0.1.onnx
```

### State File Backup

```bash
# Backup state
cp .wake-word-state.json .wake-word-state.backup.json

# Restore state
cp .wake-word-state.backup.json .wake-word-state.json
```

### Sharing Models Between Machines

```bash
# Machine 1: Train and export
./wake-word-manager.py  # Train model
tar -czf my-model.tar.gz models/my_word_v0.1.onnx* .wake-word-state.json

# Machine 2: Import
tar -xzf my-model.tar.gz
./wake-word-manager.py  # State loaded, model available
```

## Troubleshooting

### "No models found" but you know you trained one

**Cause**: State file missing or corrupted

**Solution**:
```bash
# Rebuild state from existing models
python3 << EOF
import json
from pathlib import Path

state = {"models": {}}

for model in Path("models").glob("*_v0.1.onnx"):
    name = model.stem.replace("_v0.1", "")
    wake_word = name.replace("_", " ")
    state["models"][name] = {
        "model_path": str(model),
        "num_samples": "unknown",
        "method": "full_model",
        "wake_word": wake_word,
        "last_updated": "unknown"
    }

with open(".wake-word-state.json", "w") as f:
    json.dump(state, f, indent=2)

print("State rebuilt!")
EOF
```

### "Model file not found" warning

**Cause**: Model was deleted but state still references it

**Solution**:
1. Use "Delete a model" option to clean state
2. Or retrain the model

### State file locked/permission error

**Cause**: Multiple instances running simultaneously

**Solution**: Exit all instances, restart one

## Best Practices

1. **Use manager for iterative development**
   - Great for testing different wake words
   - Easy to switch between models

2. **Use guided-training.py for demos**
   - Better for showing to users
   - More explanatory

3. **Use train-full-model.py for automation**
   - Good for batch processing
   - CI/CD pipelines

4. **Backup state file periodically**
   - Especially after successful training
   - Include in version control (optional)

5. **Clean up old models**
   - Use "Delete a model" option
   - Manually remove model files if needed

## Summary

**wake-word-manager.py** provides a stateful, user-friendly interface for managing wake word models across sessions. It's perfect for:
- Iterative development and testing
- Managing multiple wake words
- Avoiding redundant retraining
- Quick switching between models

The state persistence makes it feel like a "persistent application" rather than a one-shot script!
