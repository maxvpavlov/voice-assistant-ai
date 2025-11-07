#!/usr/bin/env python3
"""
Test if base model activates on the recorded samples.
This helps diagnose why custom verifier training is failing.
"""

import sys
from pathlib import Path
import wave
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "src"))

from openwakeword.model import Model

def test_model_on_samples(wake_word="hey_edge", base_model="hey_jarvis"):
    """Test if base model activates on recorded samples."""

    # Get sample directory
    samples_dir = Path("training_data") / wake_word.replace(" ", "_") / "positive"

    if not samples_dir.exists():
        print(f"❌ No samples found at {samples_dir}")
        return

    sample_files = sorted(samples_dir.glob("*.wav"))

    if not sample_files:
        print(f"❌ No WAV files found in {samples_dir}")
        return

    print(f"Testing {base_model} model on {len(sample_files)} samples...")
    print(f"Sample directory: {samples_dir}")
    print("-" * 70)

    # Load model
    model_name = f"{base_model}_v0.1"
    print(f"\nLoading model: {model_name}")
    oww = Model(wakeword_models=[model_name], inference_framework="onnx")
    print(f"✓ Model loaded: {list(oww.models.keys())}\n")

    # Test each sample
    print("Testing samples:")
    print("-" * 70)

    for i, sample_file in enumerate(sample_files, 1):
        # Read WAV file
        with wave.open(str(sample_file), 'rb') as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Process audio in chunks (model expects 1280 samples at a time)
        chunk_size = 1280
        max_score = 0.0
        scores = []

        for j in range(0, len(audio_array) - chunk_size, chunk_size):
            chunk = audio_array[j:j + chunk_size]
            predictions = oww.predict(chunk)
            score = predictions.get(model_name, 0.0)
            scores.append(score)
            max_score = max(max_score, score)

        # Show results
        avg_score = np.mean(scores) if scores else 0.0
        status = "✅" if max_score >= 0.5 else "⚠️ " if max_score >= 0.3 else "❌"

        print(f"{status} Sample {i}: {sample_file.name}")
        print(f"   Max score: {max_score:.4f}, Avg score: {avg_score:.4f}, Duration: {len(audio_array)/16000:.2f}s")

    print()
    print("=" * 70)
    print("Analysis:")
    print("=" * 70)
    print(f"✅ Score >= 0.5: Features will be extracted (good for training)")
    print(f"⚠️  Score 0.3-0.5: Marginal - training might fail")
    print(f"❌ Score < 0.3: Too low - training will definitely fail")
    print()
    print("The custom verifier requires base model scores >= 0.5 to extract features.")
    print("If all samples scored below 0.5, that's why training failed!")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test base model activation on samples")
    parser.add_argument("--wake-word", default="hey edge", help="Wake word to test")
    parser.add_argument("--base-model", default="hey_jarvis", help="Base model to test")

    args = parser.parse_args()

    test_model_on_samples(args.wake_word, args.base_model)
