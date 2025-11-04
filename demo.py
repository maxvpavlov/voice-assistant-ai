#!/usr/bin/env python3
"""
Voice Assistant Demo
Demonstrates wake word detection functionality.
"""

import sys
import time
import signal
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from voice_assistant import WakeWordDetector


class VoiceAssistantDemo:
    """Simple demo application for wake word detection."""

    def __init__(self):
        self.detector = None
        self.running = True
        self.detection_count = 0

    def on_wake_word_detected(self, wake_word: str, confidence: float):
        """
        Callback when a wake word is detected.

        Args:
            wake_word: The detected wake word
            confidence: Detection confidence (0.0 to 1.0)
        """
        self.detection_count += 1
        print(f"\n🎙️  ACTIVATED! Wake word: '{wake_word}' (confidence: {confidence:.2%})")
        print(f"    [Detection #{self.detection_count}]")
        print("    → This is where voice recognition would activate")
        print("    → Listening for your command...")
        print()

    def run(self):
        """Run the demo application."""
        print("=" * 70)
        print("Voice Assistant - Wake Word Detection Demo")
        print("=" * 70)
        print()
        print("Initializing wake word detector...")

        # Create detector with callback
        # Using default models (will download if not cached)
        self.detector = WakeWordDetector(
            threshold=0.5,  # Confidence threshold
            on_detection=self.on_wake_word_detected
        )

        # Show available models
        models = self.detector.list_available_models()
        print(f"\nLoaded {len(models)} wake word models:")
        for model in models:
            print(f"  • {model}")

        print("\n" + "-" * 70)
        print("STATUS: Listening for wake words...")
        print("TIP: Try saying 'Alexa' or 'Hey Jarvis'")
        print("Press Ctrl+C to exit")
        print("-" * 70)
        print()

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

        # Start detection
        self.detector.start()

        # Keep running until stopped
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\nShutting down...")
        self.running = False

    def _cleanup(self):
        """Cleanup resources."""
        if self.detector:
            self.detector.stop()
        print(f"\nTotal detections: {self.detection_count}")
        print("Goodbye! 👋\n")


def main():
    """Main entry point."""
    demo = VoiceAssistantDemo()

    try:
        demo.run()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print("\nMake sure you have installed dependencies:")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
