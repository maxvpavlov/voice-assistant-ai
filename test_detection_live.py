#!/usr/bin/env python3
"""
Test wake word detection with live scoring output.
Shows what confidence scores the model is producing.
"""

import sys
import time
sys.path.insert(0, 'src')

from voice_assistant.wake_word_detector import WakeWordDetector

def on_detection(wake_word, confidence):
    print(f"\n🎯 DETECTED: {wake_word} ({confidence:.1%})")

# Create detector
detector = WakeWordDetector(
    wake_words=["models/hey_bender_v0.1.onnx"],
    threshold=0.3,  # Lower threshold for testing
    on_detection=on_detection
)

print("=" * 70)
print("Wake Word Detection Test")
print("=" * 70)
print(f"Model: models/hey_bender_v0.1.onnx")
print(f"Threshold: 0.3 (lowered for testing)")
print(f"Say 'hey bender' to test...")
print("Press Ctrl+C to exit\n")

# Start listening
detector.start()

try:
    while True:
        # Get predictions every 0.5 seconds
        time.sleep(0.5)
        
        # Get latest scores from the model
        if hasattr(detector.model, 'prediction_buffer'):
            scores = detector.model.prediction_buffer
            if 'hey_bender_v0.1' in scores:
                score = scores['hey_bender_v0.1']
                if score > 0.01:  # Only show if above noise floor
                    bars = '█' * int(score * 50)
                    print(f"\r[{bars:<50}] {score:.3f}", end='', flush=True)
except KeyboardInterrupt:
    print("\n\nStopping...")
    detector.stop()
