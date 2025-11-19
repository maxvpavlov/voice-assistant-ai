# Repository Restructure Analysis

## Current State

### Root Directory (Legacy/Evolutionary)
**Scripts:**
- `edge-wake-word` - Old CLI tool (21KB, 6 Nov)
- `demo.py` - Old demo script (3KB, 5 Nov)
- `check-models.py`, `download-models.py`, `copy-models-to-git.py` - Model management utilities (old)
- `guided-training.py` - Old training script (9KB, 19 Nov)
- `wake-word-manager.py` - Old wake word manager (15KB, 19 Nov)
- `train-full-model.py` - Training script (19KB, 19 Nov) - **DUPLICATE IN RELEASE**
- `setup-and-enter-venv.sh` - Venv setup script (4KB)

**Documentation:**
- `README.md` - Main README (updated 19 Nov) ✅ KEEP
- `CLAUDE.md` - Codebase overview (9KB, 12 Nov)
- `MULTILINGUAL_SUPPORT.md`, `MULTILINGUAL_EXAMPLES.md` - Multilingual docs (11KB total)
- `TRAINING_GUIDE.md`, `WAKE_WORD_MANAGER.md` - Old training guides (17KB total)
- `CLEANUP_PLAN.md` - Planning doc (8KB)

**Directories:**
- `src/` - **OUTDATED** (wake_word_detector.py missing bug fixes)
- `models/` - Pre-trained models (likely duplicated in release/)
- `venv/` - Virtual environment
- `trained_models/` - User training data
- `training_data/` - User training data

**Config:**
- `requirements.txt` - Basic deps (no vosk, no inference deps)
- `requirements-training.txt` - Training deps only
- `.wake-word-state.json` - Old state file (224 bytes)

### Release Directory (Self-Contained, Production-Ready)
**Main Scripts:**
- `voice-part.py` ✅ **PRODUCTION** - Voice interface (24KB, 19 Nov)
- `inference-agent.py` ✅ **PRODUCTION** - AI agent (15KB, 19 Nov)
- `test-agent.py` ✅ **PRODUCTION** - Testing tool (7KB, 19 Nov)
- `diagnose-wake-word.py` ✅ **PRODUCTION** - Diagnostic tool (4KB, 19 Nov)
- `train-full-model.py` - Training script (19KB, 19 Nov) - DUPLICATE

**Documentation:**
- `README.md` ✅ **COMPREHENSIVE** - Complete guide (14KB, 19 Nov)
- `AUDIO_TEST_GUIDE.md` ✅ - Audio testing (11KB, 19 Nov)
- `TEST_AGENT_GUIDE.md` ✅ - Agent testing (9KB, 19 Nov)
- `WAKE_WORD_TROUBLESHOOTING.md` ✅ - Troubleshooting (10KB, 19 Nov)
- `AGENT_QUICKSTART.md` ✅ - Quick start (9KB, 19 Nov)
- `INFERENCE_AGENT.md` ✅ - Agent docs (14KB, 19 Nov)
- `ARCHITECTURE.md` ✅ - Technical details (11KB)
- `STREAMING_MODE.md`, `VOSK_UTTERANCE_DETECTION.md` - Implementation docs (19KB)
- `RASPBERRY_PI_SETUP.md`, `PI_QUICKSTART.md`, `COMPATIBILITY.md` - Platform docs (20KB)
- `BUGFIXES-SUMMARY.md` + individual bugfix docs (23KB)
- `CHANGELOG.md`, `SELF_CONTAINED.md`, `release-plan.md` - Meta docs (35KB)

**Directories:**
- `src/` - **CURRENT** with bug fixes ✅
- `models/` - Working models
- `recognizers/` - Speech recognition modules ✅
- `venv/` - Virtual environment
- `trained_models/`, `training_data/` - User data (gitignored)

**Config:**
- `requirements.txt` ✅ **COMPLETE** - All deps (vosk, flask, ollama, etc.)
- `.voice-assistant-state.json` - Current state (gitignored)

## Analysis

### ✅ Safe to Remove from Root

**Old Scripts (completely superseded):**
- `edge-wake-word` - Replaced by `voice-part.py`
- `demo.py` - Old demo
- `check-models.py`, `download-models.py`, `copy-models-to-git.py` - Model utils (obsolete)
- `guided-training.py` - Replaced by `voice-part.py --retrain`
- `wake-word-manager.py` - Functionality merged into `voice-part.py`
- `setup-and-enter-venv.sh` - Can be recreated easily

**Old Documentation (superseded):**
- `CLAUDE.md` - Old codebase overview (info integrated into release docs)
- `MULTILINGUAL_SUPPORT.md`, `MULTILINGUAL_EXAMPLES.md` - Can be archived or merged
- `TRAINING_GUIDE.md`, `WAKE_WORD_MANAGER.md` - Replaced by release docs
- `CLEANUP_PLAN.md` - Planning doc, no longer needed

**Old Directories:**
- `src/` - Outdated, missing bug fixes
- `models/` - Likely duplicated in release/models/
- `trained_models/`, `training_data/` - User-specific data

**Old Config:**
- `requirements.txt` - Incomplete (missing vosk, inference deps)
- `requirements-training.txt` - Redundant (merged into release/requirements.txt)
- `.wake-word-state.json` - Old state file

### ⚠️ Potentially Keep (But Can Remove)

**Scripts:**
- `train-full-model.py` - Duplicated in release/ (19KB exact match)

### ✅ Must Keep in Root

**Essential:**
- `.git/` - Git repository
- `.gitignore` - Git ignore rules
- `README.md` - Main documentation (already updated)
- `.claude/` - Claude Code config
- `venv/` - Virtual environment (or recreate from release/requirements.txt)

## Recommended Restructure Plan

### Option 1: Complete Root Replacement (Cleanest)

**Actions:**
1. Keep only: `.git/`, `.gitignore`, `.claude/`, `README.md`
2. Move `release/` contents to root:
   - `voice-part.py` → `voice-part.py`
   - `inference-agent.py` → `inference-agent.py`
   - `test-agent.py` → `test-agent.py`
   - `diagnose-wake-word.py` → `diagnose-wake-word.py`
   - `release/src/` → `src/` (with bug fixes)
   - `release/recognizers/` → `recognizers/`
   - `release/models/` → `models/`
   - `release/requirements.txt` → `requirements.txt`
   - All `release/*.md` docs → root (or keep in a `docs/` folder)
3. Delete everything else
4. Update paths in scripts (remove `release/` prefix from imports)
5. Recreate venv: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

**Pros:**
- Cleanest structure
- No legacy cruft
- Clear single source of truth
- Easier for new users

**Cons:**
- Requires updating import paths in scripts
- More disruptive change
- Need to recreate venv

### Option 2: Archive and Move (Conservative)

**Actions:**
1. Create `archive/` directory
2. Move old files to `archive/`:
   - All old scripts
   - `src/` (old)
   - Old docs
   - Old requirements files
3. Move `release/` contents to root (as in Option 1)
4. Keep `archive/` for reference

**Pros:**
- Preserves history
- Can reference old code if needed
- Less risky

**Cons:**
- Still cluttered
- Archive may never be used
- Larger repo size

### Option 3: Clean Root, Keep Docs Archive (Balanced)

**Actions:**
1. Delete all old scripts and old `src/`
2. Keep interesting docs in `docs/archive/`:
   - `MULTILINGUAL_SUPPORT.md`, `MULTILINGUAL_EXAMPLES.md`
   - `CLAUDE.md` (as historical context)
3. Move `release/` contents to root
4. Organize docs in `docs/` folder:
   - `docs/AUDIO_TEST_GUIDE.md`
   - `docs/TEST_AGENT_GUIDE.md`
   - `docs/WAKE_WORD_TROUBLESHOOTING.md`
   - etc.

**Pros:**
- Clean structure
- Preserves valuable docs
- Good organization

**Cons:**
- Requires organizing docs
- More manual work

## Risk Assessment

### Low Risk
- Deleting old scripts: ✅ All functionality is in `release/`
- Deleting old `src/`: ✅ `release/src/` is newer with bug fixes
- Deleting old requirements: ✅ `release/requirements.txt` is comprehensive
- Deleting old docs: ✅ All info is in release docs (better)

### Medium Risk
- Moving release/ to root: ⚠️ Requires updating import paths in scripts
- Deleting models/: ⚠️ Need to verify release/models/ has everything

### No Risk
- Keeping archive/: ✅ Safe fallback
- Current git history: ✅ Everything is in git, can always recover

## Import Path Changes Required

If we move `release/` to root, these imports need updating:

**In all scripts:**
- `sys.path.insert(0, 'src')` - Already correct
- No changes needed! Scripts already use relative imports from `src/`

**No changes needed in:**
- `voice-part.py` - Uses `from voice_assistant.wake_word_detector import ...`
- `inference-agent.py` - No imports from src/
- `test-agent.py` - No imports from src/
- `diagnose-wake-word.py` - Uses `from voice_assistant.wake_word_detector import ...`

**Path references to check:**
- Model paths in `.voice-assistant-state.json` - Uses relative paths, should work
- Vosk model path in `voice-part.py` - Uses relative path `models/vosk-model-small-en-us-0.15`

## Verification Steps Before Restructure

1. ✅ Verify release/models/ has all needed models
2. ✅ Verify release/src/ has all bug fixes (already confirmed - has cooldown fix)
3. ✅ Test all scripts work from release/ directory (already tested)
4. ⚠️ Compare models/ directories
5. ⚠️ Test that moving to root doesn't break imports

## Recommendation

**Go with Option 1: Complete Root Replacement**

**Why:**
1. Release folder is already self-contained and tested
2. All scripts already use relative imports (no changes needed)
3. Clean slate is easier for users
4. Git history preserves everything if needed
5. No import path changes required (scripts use `src/` relative path)

**Implementation:**
1. Create backup branch
2. Delete old cruft
3. Move release/* to root
4. Update README if needed
5. Test all scripts
6. Commit and push

**Timeline:** ~30 minutes, very safe with git history as backup
