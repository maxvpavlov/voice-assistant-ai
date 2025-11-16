# Quick Multilingual Examples

## Test Different Languages

Here are quick examples showing how to train wake words in different languages:

### Spanish (Español)
```bash
./guided-training.py
# Enter your wake word: oye asistente
# (Say "oye asistente" 5 times)
```

### French (Français)
```bash
./guided-training.py
# Enter your wake word: écoute ordinateur
# (Say "écoute ordinateur" 5 times)
```

### German (Deutsch)
```bash
./guided-training.py
# Enter your wake word: hallo computer
# (Say "hallo computer" 5 times)
```

### Mandarin Chinese (中文)
```bash
./guided-training.py
# Enter your wake word: 你好电脑
# (Say "nǐ hǎo diàn nǎo" 5 times - keep tones consistent!)
```

### Japanese (日本語)
```bash
./guided-training.py
# Enter your wake word: コンピューター起動
# (Say "konpyūtā kidō" 5 times)
```

### Arabic (العربية)
```bash
./guided-training.py
# Enter your wake word: مرحبا كمبيوتر
# (Say "marhaban kambiutar" 5 times)
```

### Russian (Русский)
```bash
./guided-training.py
# Enter your wake word: привет компьютер
# (Say "privet komp'yuter" 5 times)
```

### Portuguese (Português)
```bash
./guided-training.py
# Enter your wake word: olá computador
# (Say "olá computador" 5 times)
```

### Italian (Italiano)
```bash
./guided-training.py
# Enter your wake word: ciao computer
# (Say "ciao computer" 5 times)
```

### Korean (한국어)
```bash
./guided-training.py
# Enter your wake word: 컴퓨터 시작
# (Say "keompyuteo sijak" 5 times)
```

### Hindi (हिन्दी)
```bash
./guided-training.py
# Enter your wake word: नमस्ते कंप्यूटर
# (Say "namaste kampyootar" 5 times)
```

### Mixed Languages (Code-Switching)
```bash
# English-Spanish
./guided-training.py
# Enter your wake word: hey computadora

# English-French
./guided-training.py
# Enter your wake word: hello ordinateur

# English-Mandarin
./guided-training.py
# Enter your wake word: hello 电脑
```

## Tips by Language Family

### Tonal Languages (Mandarin, Vietnamese, Thai)
- Record 20-50 samples (more than usual)
- Maintain consistent tones
- Practice pronunciation before recording

### Accent-Heavy Languages (French, Portuguese, Vietnamese)
- Enunciate clearly
- Record in quiet environment
- More samples help with accent variations

### Long Compound Words (German, Finnish, Turkish)
- Break into natural syllables when speaking
- Record at normal speaking speed
- Our time-stretching handles length variations

### Right-to-Left Scripts (Arabic, Hebrew, Urdu)
- Script direction doesn't matter for audio!
- Train exactly like left-to-right languages
- Audio processing is script-agnostic

## All Work Identically!

The beauty of our audio-based approach: **every language uses the exact same process**:

1. Record 5 samples of your wake word
2. Synthetic augmentation generates 80+ variations
3. Train neural network (~3 minutes)
4. Test and deploy!

No language-specific configuration needed! 🌍
