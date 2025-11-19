#!/usr/bin/env python3
"""
Diagnostic tool for wake word detection issues.

Tests the model and provides recommendations for improving detection.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, 'src')

from voice_assistant.wake_word_detector import WakeWordDetector
import time


def test_detection_sensitivity(model_path, wake_word_name):
    """Test detection at different threshold levels."""

    print("=" * 70)
    print("Wake Word Detection Diagnostic")
    print("=" * 70)
    print(f"\nModel: {model_path}")
    print(f"Wake word: {wake_word_name}\n")

    # Test at different thresholds
    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6]

    print("Testing detection sensitivity...")
    print(f"\nSay '{wake_word_name}' multiple times at different volumes and speeds.")
    print("We'll test at different threshold levels.\n")

    for threshold in thresholds:
        print(f"\n{'='*70}")
        print(f"Testing with threshold: {threshold}")
        print(f"{'='*70}")

        detections = []

        def on_detection(wake_word, confidence):
            detections.append(confidence)
            print(f"  ✓ DETECTED! Confidence: {confidence:.1%}")

        detector = WakeWordDetector(
            wake_words=[model_path],
            threshold=threshold,
            on_detection=on_detection
        )

        detector.start()

        print(f"\nListening for 10 seconds...")
        print(f"Say '{wake_word_name}' now (threshold={threshold})...\n")

        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(0.1)

        detector.stop()

        if detections:
            avg_conf = sum(detections) / len(detections)
            print(f"\n  Results: {len(detections)} detection(s), avg confidence: {avg_conf:.1%}")
        else:
            print(f"\n  Results: No detections")

        time.sleep(1)

    print("\n" + "=" * 70)
    print("Diagnostic Complete")
    print("=" * 70)

    print("\n📊 Recommendations:")
    print("\nIf you had:")
    print("  • No detections at any threshold:")
    print("    → Model needs retraining with more/better samples")
    print("    → Try recording 10-15 samples instead of 5")
    print("    → Speak clearly and consistently")
    print()
    print("  • Detections only at 0.2-0.3:")
    print("    → Model works but is weak")
    print("    → Lower threshold to 0.3 in state file")
    print("    → OR retrain with more samples")
    print()
    print("  • Detections at 0.4-0.6:")
    print("    → Model is working well!")
    print("    → Current threshold (0.5) should be fine")
    print()
    print("\n💡 To retrain with more samples:")
    print("   ./voice-part.py --retrain")
    print()


def main():
    parser = argparse.ArgumentParser(description="Diagnose wake word detection issues")
    parser.add_argument("--model", default=None, help="Model path (default: from state file)")
    parser.add_argument("--wake-word", default=None, help="Wake word name (default: from state file)")

    args = parser.parse_args()

    # Load from state if not provided
    if not args.model or not args.wake_word:
        import json
        try:
            with open('.voice-assistant-state.json', 'r') as f:
                state = json.load(f)
            model_path = args.model or state.get('model_path', 'models/hey_edge_v0.1.onnx')
            wake_word = args.wake_word or state.get('wake_word', 'hey edge')
        except:
            print("❌ Could not load state file. Please provide --model and --wake-word")
            return
    else:
        model_path = args.model
        wake_word = args.wake_word

    # Check model exists
    if not Path(model_path).exists():
        print(f"❌ Model not found: {model_path}")
        return

    test_detection_sensitivity(model_path, wake_word)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrupted by user")
