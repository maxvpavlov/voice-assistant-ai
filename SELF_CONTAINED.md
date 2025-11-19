# Self-Contained Release Mode

The `release/` directory is now **fully self-contained** and can be deployed independently without requiring the parent repository.

## What Changed

### Before (Coupled to Root)

```
voice-part.py
├─ Used: release/venv/         ✅
├─ Used: release/src/           ✅
└─ subprocess calls:
   ├─ cd .. && ../venv/         ❌ Root venv
   ├─ ../edge-wake-word         ❌ Root script
   ├─ ../train-full-model.py    ❌ Root script
   ├─ ../training_data/         ❌ Root folder
   └─ ../trained_models/        ❌ Root folder
```

**Problem**: Could not deploy release/ alone

### After (Self-Contained)

```
voice-part.py
├─ Uses: release/venv/          ✅
├─ Uses: release/src/           ✅
├─ Uses: release/train-full-model.py  ✅
├─ Uses: release/training_data/       ✅
└─ Uses: release/trained_models/      ✅
```

**Solution**: Everything needed is in release/

## Directory Structure

```
release/
├── voice-part.py              # Main application
├── train-full-model.py        # Training script (copied from root)
├── requirements.txt           # All dependencies
│
├── venv/                      # Virtual environment
│
├── src/                       # Source modules
│   └── voice_assistant/
│       ├── __init__.py
│       ├── wake_word_detector.py
│       ├── audio_recorder.py
│       └── model_trainer.py
│
├── recognizers/               # Speech recognition
│   ├── __init__.py
│   └── vosk_recognizer.py
│
├── models/                    # Downloaded & trained models
│   ├── vosk-model-small-en-us-0.15/  # Vosk (downloaded)
│   └── hey_edge_v0.1.onnx     # User's trained model
│
├── training_data/             # User's voice samples
│   └── hey_edge/
│       └── positive/
│           ├── positive_0001.wav
│           └── ...
│
└── trained_models/            # Training output
    └── hey_edge/
        ├── hey_edge_v0.1.onnx
        └── features/
```

## Installation (Self-Contained)

### Option 1: Clone Entire Repo

```bash
git clone <repo>
cd voice-activation-and-recognition/release
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./voice-part.py
```

### Option 2: Deploy Release Only

```bash
# On development machine
cd voice-activation-and-recognition
tar czf voice-assistant-release.tar.gz release/

# Transfer to production machine
scp voice-assistant-release.tar.gz pi@raspberrypi:~/

# On production machine
tar xzf voice-assistant-release.tar.gz

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./voice-part.py
```

## Changes Made

### 1. Copied Training Script

**File**: `release/train-full-model.py`
- Full model training with synthetic data
- No parent directory dependencies
- Works from release/ directory

### 2. Updated voice-part.py

**Microphone Testing**:
- Old: `cd .. && ./edge-wake-word train --test-mic`
- New: Direct AudioRecorder initialization

**Sample Recording**:
- Old: `cd .. && ./edge-wake-word train`
- New: Direct AudioRecorder.record_sample()

**Model Training**:
- Old: `cd .. && source venv/bin/activate && python3 train-full-model.py`
- New: `source venv/bin/activate && python3 train-full-model.py`

**Model Paths**:
- Old: `../trained_models/` and `../models/`
- New: `trained_models/` and `models/`

### 3. Created Data Directories

```bash
release/training_data/    # Voice samples
release/trained_models/   # Training output
```

### 4. Updated .gitignore

Ignores:
- `release/venv/`
- `release/training_data/`
- `release/trained_models/`
- `release/.voice-assistant-state.json`

Keeps:
- `release/models/vosk-model-small-en-us-0.15/` (bundled)
- Source code
- Documentation

## Benefits

### 1. Independent Deployment

```bash
# Just copy release/
scp -r release/ user@host:~/voice-assistant/
```

No need to bring parent repo along.

### 2. Clear Separation

```
root/                 # Development
└── release/          # Production
```

Development work stays in root, production in release/.

### 3. Simplified Installation

Single directory to manage:
```bash

pip install -r requirements.txt
./voice-part.py
```

### 4. Portable

Move release/ anywhere:
- Different machine
- Different user
- Different OS
Works the same.

## Root vs Release

### Root Directory (Development)

**Purpose**: Development, experimentation, testing
**Contains**:
- Original scripts
- Development venv (optional)
- Experimental features
- Test data

**Usage**:
```bash
cd voice-activation-and-recognition
python3 -m venv venv  # Optional
source venv/bin/activate
python3 train-full-model.py --wake-word "test"
```

### Release Directory (Production)

**Purpose**: Deployment, end-users, production
**Contains**:
- Stable features only
- Self-contained scripts
- User documentation
- Production venv

**Usage**:
```bash
cd voice-activation-and-recognition/release
source venv/bin/activate
./voice-part.py
```

## Migration from Old Setup

If you have existing data in root:

### Move Training Data

```bash
# From root to release
cp -r training_data/* release/training_data/
```

### Move Trained Models

```bash
# From root to release
cp -r trained_models/* release/trained_models/
```

### Move User Models

```bash
# From root models/ to release models/
cp models/*.onnx release/models/
cp models/*.onnx.data release/models/
```

## Testing Self-Containment

Verify release/ works independently:

```bash
# Create test directory
mkdir /tmp/test-release
cp -r release/* /tmp/test-release/
cd /tmp/test-release

# Should work without parent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./voice-part.py --wake-word "test"
```

If successful, release/ is truly self-contained!

## Maintenance

### Updating Release from Root

When you improve scripts in root:

```bash
# Copy updated script
cp train-full-model.py release/

# Test in release
cd release
./voice-part.py --retrain

# Commit if working
git add release/train-full-model.py
git commit -m "Update training script in release"
```

### Keeping Root and Release in Sync

**Automated** (future):
```bash
# Build script could sync
./build-release.sh
```

**Manual** (current):
- Copy changed files manually
- Test in release/
- Commit when stable

## Cleanup from Old Dual-Venv Setup

### Optional: Remove Root Venv

If you don't need root venv for development:

```bash
# Archive it first
mv venv venv.old

# Or delete (after confirming release works)
rm -rf venv
```

Saves ~3-4GB of disk space.

### Clean Root Training Data

If you moved everything to release:

```bash
# Archive
tar czf old-training-data.tar.gz training_data/ trained_models/

# Move to archive
mkdir archive
mv training_data/ trained_models/ archive/
```

## Troubleshooting

### Import Errors

If you see:
```
ModuleNotFoundError: No module named 'voice_assistant'
```

Check:
```bash
# Are you in release/?
pwd  # Should show .../release

# Is src/ present?
ls -d src/

# Is venv activated?
which python  # Should show release/venv/bin/python
```

### Path Errors

If you see:
```
FileNotFoundError: ../training_data/...
```

This means the code is still looking in parent directory.
Report this as a bug - should use local paths only.

### Training Fails

If training fails:
```bash
# Verify train-full-model.py exists
ls -l train-full-model.py

# Check it's executable
chmod +x train-full-model.py

# Run directly to see errors
source venv/bin/activate
python3 train-full-model.py --wake-word "test" --epochs 5
```

## Summary

**Before**: release/ depended on root venv and scripts
**After**: release/ is fully self-contained

**Benefits**:
- ✅ Independent deployment
- ✅ Clear separation (dev/prod)
- ✅ Simpler installation
- ✅ Portable across machines
- ✅ No parent dependencies

**Usage**:
```bash

source venv/bin/activate
./voice-part.py
```

Everything just works!
