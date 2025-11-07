# Using Hey Jarvis as Base Model

## Quick Fix for "Hey Edge" Training

Since your wake word is "hey edge", you should use a "hey_*" base model instead of "alexa".

## Steps:

1. **Copy hey_jarvis models to git** (on your Mac):

```bash
# Update copy-models-to-git.py to include hey_jarvis
# Or manually copy:
python3 -c "
import shutil
from pathlib import Path
import openwakeword

pkg_path = Path(openwakeword.__file__).parent
source = pkg_path / 'resources' / 'models'
dest = Path('models')

for model in ['hey_jarvis_v0.1.onnx', 'hey_jarvis_v0.1.tflite']:
    src_file = source / model
    if src_file.exists():
        shutil.copy2(src_file, dest / model)
        print(f'Copied {model}')
"

git add models/
git commit -m "Add hey_jarvis base model for hey edge training"
git push
```

2. **Train with hey_jarvis base** (modify the command):

```bash
./edge-wake-word train-local --wake-word "hey edge" --base-model hey_jarvis
```

## Why This Works

- "hey edge" and "hey jarvis" both start with "hey"
- Phonetically similar enough for custom verifier feature extraction
- Much faster than full model training (5 seconds vs hours)
- Still uses your 5 voice samples for personalization

## If You Want Full Training Instead

Full model training (like Colab) requires:
- PyTorch
- Piper TTS (neural text-to-speech)
- Room impulse response datasets
- Background noise datasets
- False positive validation data
- Several hours of training time

Let me know which approach you prefer!
