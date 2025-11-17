# Repository Cleanup Plan

## Current Issues

1. **Two virtual environments**:
   - Root: `venv/` (older, 3.9GB+ with all dependencies)
   - Release: `release/venv/` (newer, cleaner)

2. **Dual dependencies**:
   - `release/voice-part.py` calls root scripts via subprocess
   - Cannot run release independently
   - Confusing for users

3. **Scattered files**:
   - Training scripts in root
   - Release scripts in release/
   - Duplicated src/ folder

## Goals

1. ✅ Make `release/` **fully self-contained**
2. ✅ Single virtual environment in release/
3. ✅ Clear separation: development (root) vs production (release/)
4. ✅ Easy deployment (just copy release/ folder)

## Current Dependencies

### What release/ uses from root/

```
release/voice-part.py
    ↓ (subprocess)
../venv/bin/activate                  ← Root venv
../edge-wake-word train               ← Root script
../train-full-model.py                ← Root training script
    ↓
../src/                               ← Root source (but also copied to release/src/)
../training_data/                     ← Shared data
../trained_models/                    ← Shared output
```

## Solution Options

### Option 1: Make Release Self-Contained (RECOMMENDED)

**Pros:**
- Clean deployment
- No parent dependencies
- Easy to understand
- Portable

**Cons:**
- Need to copy/adapt training scripts
- Slightly more code duplication

**Changes:**
1. Copy `train-full-model.py` to `release/`
2. Copy `edge-wake-word` script to `release/`
3. Update `voice-part.py` to use local scripts
4. Update paths to use `release/venv`
5. Keep root/ for development/testing only

### Option 2: Shared Scripts, Separate Venvs

**Pros:**
- No code duplication
- Shared training scripts

**Cons:**
- Still coupled to root
- Confusing deployment
- Can't move release/ independently

### Option 3: Root as Development, Release as Distribution

**Pros:**
- Clear separation
- Root for experimentation
- Release for production

**Cons:**
- Need build/sync process
- Two places to maintain

## Recommended Approach: Option 1

### Step 1: Copy Training Scripts to Release

```bash
# Copy training script
cp train-full-model.py release/

# Copy edge-wake-word (or create simplified version)
# Adapt for release environment
```

### Step 2: Update voice-part.py

Change subprocess calls from:
```python
cd .. && source venv/bin/activate && python3 train-full-model.py
```

To:
```python
source venv/bin/activate && python3 train-full-model.py
# (run from release/ directory)
```

### Step 3: Update Paths

Create release/training_data/ and release/trained_models/ directories:
```bash
mkdir -p release/training_data
mkdir -p release/trained_models
```

### Step 4: Clean Root

Remove/archive old venv:
```bash
# After confirming release works
rm -rf venv/  # or mv venv/ venv.old/
```

### Step 5: Update .gitignore

```gitignore
# Virtual environments
venv/
release/venv/

# Training data and models
training_data/
trained_models/
models/*.onnx
models/*.onnx.data

# State files
.wake-word-state.json
release/.voice-assistant-state.json

# Temporary files
*.pyc
__pycache__/
```

## File Structure (After Cleanup)

```
voice-activation-and-recognition/
├── README.md                      # Points to release/
├── CLAUDE.md                      # Development docs
├── MULTILINGUAL_*.md              # Docs
├── src/                           # Development source
│   └── voice_assistant/
├── edge-wake-word                 # Development CLI
├── guided-training.py             # Development scripts
├── train-full-model.py            # Development scripts
├── wake-word-manager.py           # Development scripts
│
└── release/                       # PRODUCTION (self-contained)
    ├── README.md                  # User guide
    ├── QUICKSTART.md
    ├── PI_QUICKSTART.md
    ├── RASPBERRY_PI_SETUP.md
    ├── requirements.txt           # Production deps
    ├── voice-part.py              # Main script
    ├── train-full-model.py        # Training (copied from root)
    ├── venv/                      # ONLY venv needed
    ├── src/                       # Production source
    │   └── voice_assistant/
    ├── recognizers/
    │   └── vosk_recognizer.py
    ├── models/                    # Models
    │   ├── vosk-model-small-en-us-0.15/
    │   └── hey_edge_v0.1.onnx
    ├── training_data/             # User's training data
    └── trained_models/            # User's models
```

## Migration Steps

### For Users

**Current (confusing):**
```bash
cd voice-activation-and-recognition
cd release
source venv/bin/activate
./voice-part.py  # Uses ../venv and ../scripts
```

**After cleanup (clear):**
```bash
cd voice-activation-and-recognition/release
source venv/bin/activate
./voice-part.py  # Everything self-contained
```

### For Developers

```bash
# Development in root
cd voice-activation-and-recognition
python3 -m venv venv  # Optional, for development
source venv/bin/activate
python3 train-full-model.py  # Test changes

# When ready, copy to release
cp train-full-model.py release/
cd release
# Test production version
```

## Cleanup Checklist

- [ ] Copy `train-full-model.py` to `release/`
- [ ] Update `voice-part.py` subprocess calls
- [ ] Create `release/training_data/` directory
- [ ] Create `release/trained_models/` directory
- [ ] Test training flow in release/ only
- [ ] Test wake word detection in release/ only
- [ ] Update release/README.md with new paths
- [ ] Archive or remove root venv/
- [ ] Update root README.md to point to release/
- [ ] Add .gitignore entries
- [ ] Test on clean clone
- [ ] Update documentation

## Benefits After Cleanup

1. **Users**: Simple, clear installation
   ```bash
   git clone <repo>
   cd release/
   pip install -r requirements.txt
   ./voice-part.py
   ```

2. **Deployment**: Just copy `release/` folder
   ```bash
   scp -r release/ pi@raspberrypi:~/voice-assistant/
   ```

3. **Understanding**: Clear structure
   - `root/` = Development/experimentation
   - `release/` = Production/deployment

4. **Maintenance**: Single source of truth per environment

## Testing After Cleanup

```bash
# 1. Clean clone test
cd /tmp
git clone <repo> test-repo
cd test-repo/release

# 2. Install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Train
./voice-part.py --wake-word "test"
# Should work without accessing parent directory

# 4. Detect
./voice-part.py
# Should work independently
```

## Rollback Plan

If issues occur:
```bash
# Keep old structure in branch
git checkout -b pre-cleanup-backup

# After cleanup on main
git checkout main

# If problems
git checkout pre-cleanup-backup
```

## Timeline

1. **Create backup branch** (5 min)
2. **Copy scripts to release/** (10 min)
3. **Update voice-part.py** (15 min)
4. **Test training flow** (10 min)
5. **Test detection flow** (5 min)
6. **Update documentation** (10 min)
7. **Clean root venv** (2 min)
8. **Final testing** (15 min)

**Total: ~1 hour**

## Questions to Consider

1. Keep root venv or delete?
   - **Recommendation**: Delete (or rename to venv.old)

2. Keep development scripts in root?
   - **Recommendation**: Yes, for future development

3. Sync changes from root to release?
   - **Recommendation**: Manual copy when stable

4. Should release/ be a separate repository?
   - **Recommendation**: No, keep together but independent

## Next Steps

1. Review this plan
2. Create backup branch
3. Implement Option 1 (self-contained release)
4. Test thoroughly
5. Update documentation
6. Commit and push

Would you like me to proceed with the cleanup?
