#!/usr/bin/env python3
"""
voice-part.py - Unified Voice Assistant

Complete voice interaction pipeline:
1. Wake word training (guided, if needed)
2. Wake word detection (always listening)
3. Speech recognition (activated by wake word)
4. Network transmission (to inference host)

Usage:
    ./voice-part.py                           # Auto-detect, train if needed
    ./voice-part.py --retrain                 # Force retraining
    ./voice-part.py --endpoint http://...     # Specify inference endpoint
    ./voice-part.py --wake-word "hey robot"   # Set wake word
"""

import sys
import os
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path (try both release/src and parent/src)
release_src = Path(__file__).parent / "src"
parent_src = Path(__file__).parent.parent / "src"

if release_src.exists():
    sys.path.insert(0, str(release_src))
elif parent_src.exists():
    sys.path.insert(0, str(parent_src))
else:
    # Try current directory
    sys.path.insert(0, str(Path(__file__).parent))

# Import our existing components
try:
    from voice_assistant import WakeWordDetector, AudioRecorder
except ImportError:
    print("❌ Error: Could not import voice_assistant module.")
    print("   Make sure you're running from the repository root.")
    sys.exit(1)

# State file for persistence
STATE_FILE = ".voice-assistant-state.json"


class VoiceAssistantState:
    """Manages persistent state across sessions."""

    def __init__(self, state_file=STATE_FILE):
        self.state_file = Path(state_file)
        self.state = self.load_state()

    def load_state(self):
        """Load state from JSON file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Warning: Could not load state file: {e}")
                return self._default_state()
        return self._default_state()

    def _default_state(self):
        """Return default state."""
        return {
            "wake_word": None,
            "model_path": None,
            "model_trained": False,
            "last_training": None,
            "inference_endpoint": "http://localhost:8000/process",
            "recognition_engine": "vosk",
            "vosk_model_path": "models/vosk-model-small-en-us-0.15",
            "silence_timeout": 3.0,
            "detection_threshold": 0.5,
            "send_to_inference": True
        }

    def save_state(self):
        """Save state to JSON file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Warning: Could not save state: {e}")

    def update(self, **kwargs):
        """Update state values."""
        self.state.update(kwargs)
        self.save_state()


class VoiceAssistant:
    """Main voice assistant orchestrator."""

    def __init__(self, args):
        self.args = args
        self.state_manager = VoiceAssistantState()
        self.state = self.state_manager.state
        self.wake_detector = None
        self.speech_recognizer = None
        self.is_listening_for_speech = False

        # Apply command-line overrides
        if args.wake_word:
            self.state["wake_word"] = args.wake_word
        if args.endpoint:
            self.state["inference_endpoint"] = args.endpoint
        if args.threshold:
            self.state["detection_threshold"] = args.threshold
        if args.silence_timeout:
            self.state["silence_timeout"] = args.silence_timeout

    def print_header(self, text):
        """Print a formatted header."""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70 + "\n")

    def print_section(self, title):
        """Print a section separator."""
        print(f"\n{'─' * 70}")
        print(f"  {title}")
        print(f"{'─' * 70}\n")

    def check_model_exists(self):
        """Check if wake word model exists."""
        if not self.state["wake_word"]:
            return False, None

        normalized = self.state["wake_word"].lower().replace(" ", "_")

        # Check local release/models/ directory first (preferred)
        local_path = Path(f"models/{normalized}_v0.1.onnx")
        if local_path.exists():
            return True, str(local_path)

        # Check parent models directory
        parent_model_path = Path(f"../models/{normalized}_v0.1.onnx")
        if parent_model_path.exists():
            return True, str(parent_model_path)

        # Check training output directory
        trained_path = Path(f"../trained_models/{normalized}/{normalized}_v0.1.onnx")
        if trained_path.exists():
            return True, str(trained_path)

        return False, None

    def ensure_model_trained(self):
        """Ensure a wake word model is trained and ready."""

        # Check if we should force retrain
        if self.args.retrain:
            print("🔄 Force retrain requested...")
            return self.train_wake_word()

        # Check existing model
        exists, model_path = self.check_model_exists()

        if exists and self.state["model_trained"]:
            print(f"✓ Found existing model: {self.state['wake_word']}")
            print(f"  Path: {model_path}")
            print(f"  Last trained: {self.state.get('last_training', 'Unknown')[:19]}")

            # Ask user if they want to retrain
            if not self.args.yes:
                choice = input("\nUse existing model? (y/n): ").strip().lower()
                if choice != 'y':
                    return self.train_wake_word()

            self.state["model_path"] = model_path
            self.state_manager.save_state()
            return True

        # No model found - guide training
        print("⚠️  No trained wake word model found.")
        return self.train_wake_word()

    def train_wake_word(self):
        """Guide user through wake word training."""

        self.print_header("🎓 WAKE WORD TRAINING")

        # Get wake word if not set
        if not self.state["wake_word"]:
            print("Choose a wake word that is:")
            print("  • Easy to pronounce consistently")
            print("  • 2-4 syllables (e.g., 'hey edge', 'computer')")
            print("  • Not too common in everyday speech\n")

            wake_word = input("Enter your wake word: ").strip()
            if not wake_word:
                print("❌ Wake word cannot be empty.")
                return False

            self.state["wake_word"] = wake_word
            self.state_manager.save_state()

        wake_word = self.state["wake_word"]
        normalized = wake_word.lower().replace(" ", "_")

        print(f"\n✓ Wake word: '{wake_word}'")

        # Step 1: Test microphone (optional, quick)
        print("\n📱 Testing microphone...")
        test_result = subprocess.run(
            f"cd .. && source venv/bin/activate && timeout 5 ./edge-wake-word train --test-mic 2>&1 | head -20",
            shell=True,
            executable='/bin/bash',
            capture_output=True
        )
        if test_result.returncode == 0 or test_result.returncode == 124:  # timeout is ok
            print("✓ Microphone ready")

        # Step 2: Record samples
        self.print_section("🎙️  Recording Training Samples")
        print(f"Recording 5 samples of '{wake_word}'...\n")
        print("Tips:")
        print("  • Speak clearly and naturally")
        print("  • Use normal volume")
        print("  • Try slight variations\n")

        if not self.args.yes:
            input("Press Enter when ready...")

        record_result = subprocess.run(
            f'cd .. && source venv/bin/activate && ./edge-wake-word train --wake-word "{wake_word}" --num-samples 5',
            shell=True,
            executable='/bin/bash'
        )

        if record_result.returncode != 0:
            print("\n❌ Recording failed.")
            return False

        # Step 3: Train model with synthetic data
        self.print_section("🧠 Training Neural Network")
        print("Generating synthetic variations and training...")
        print("This takes about 3-5 minutes...\n")

        train_result = subprocess.run(
            f'cd .. && source venv/bin/activate && python3 train-full-model.py --wake-word "{wake_word}" --epochs 50 --augmentations 20',
            shell=True,
            executable='/bin/bash'
        )

        if train_result.returncode != 0:
            print("\n❌ Training failed.")
            return False

        # Step 4: Copy model to release directory
        print("\n📦 Installing model...")

        # Create models directory if it doesn't exist
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)

        # Copy model files
        subprocess.run(
            f"cp ../trained_models/{normalized}/{normalized}_v0.1.onnx* models/",
            shell=True
        )

        model_path = f"models/{normalized}_v0.1.onnx"

        # Update state
        self.state_manager.update(
            model_path=model_path,
            model_trained=True,
            last_training=datetime.now().isoformat()
        )

        print(f"\n✅ Training complete!")
        print(f"   Model: {model_path}")

        return True

    def setup_speech_recognition(self):
        """Initialize speech recognition engine."""

        engine = self.state["recognition_engine"]

        if engine == "vosk":
            return self.setup_vosk()
        elif engine == "whisper":
            return self.setup_whisper()
        else:
            print(f"❌ Unknown recognition engine: {engine}")
            return None

    def setup_vosk(self):
        """Setup Vosk speech recognizer."""

        try:
            import vosk
        except ImportError:
            print("❌ Vosk not installed. Installing...")
            subprocess.run(
                "pip install vosk sounddevice",
                shell=True,
                check=True
            )
            import vosk

        model_path = self.state["vosk_model_path"]

        # Check if model exists
        if not Path(model_path).exists():
            print(f"⚠️  Vosk model not found at: {model_path}")
            print("📥 Downloading Vosk model...")
            print("   This is a one-time download (~40MB)...")

            # Download model
            import urllib.request
            import zipfile

            url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
            zip_path = "vosk-model.zip"

            try:
                urllib.request.urlretrieve(url, zip_path)

                # Extract
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("models/")

                os.remove(zip_path)
                print("✓ Model downloaded")

            except Exception as e:
                print(f"❌ Download failed: {e}")
                print("\nManual download:")
                print(f"  1. Download: {url}")
                print("  2. Extract to: models/")
                return None

        # Load model
        print(f"Loading Vosk model from {model_path}...")
        try:
            from recognizers.vosk_recognizer import VoskRecognizer
            recognizer = VoskRecognizer(model_path)
            print("✓ Vosk ready")
            return recognizer
        except ImportError:
            # Vosk recognizer not yet implemented - will add next
            print("⚠️  Vosk recognizer module not yet implemented")
            print("   Speech recognition will be skipped")
            return None

    def setup_whisper(self):
        """Setup Whisper speech recognizer."""
        print("⚠️  Whisper not yet implemented")
        return None

    def on_wake_word_detected(self, wake_word, confidence):
        """Callback when wake word is detected."""

        print(f"\n{'='*70}")
        print(f"🎯 WAKE WORD DETECTED! ({confidence:.1%})")
        print(f"{'='*70}")

        if not self.speech_recognizer:
            print("⚠️  Speech recognition not available - skipping")
            print(f"● Listening for '{self.state['wake_word']}'...\n")
            return

        print("🎙️  Listening for command... (speak now)")

        # Temporarily stop wake word detector to free microphone
        if self.wake_detector:
            print("⏸️  Pausing wake word detection...")
            # Don't wait for thread since we're being called FROM that thread
            self.wake_detector.stop(wait=False)

        # Counter for sentences sent
        self.sentences_sent = 0

        # Define callback to send each sentence immediately
        def on_sentence_detected(sentence_text):
            """Called by Vosk when sentence boundary detected."""
            if self.state["send_to_inference"] and sentence_text.strip():
                self.sentences_sent += 1
                print(f"\n📤 Sending sentence #{self.sentences_sent}...")
                self.send_to_inference(sentence_text)

        # Start speech recognition with callback
        try:
            sentences = self.speech_recognizer.recognize_stream(
                silence_timeout=self.state["silence_timeout"],
                on_sentence_callback=on_sentence_detected
            )

            if sentences:
                if self.sentences_sent > 0:
                    print(f"\n✅ Sent {self.sentences_sent} sentence(s) total")
                else:
                    print("\n⚠️  No sentences detected")
            else:
                print("\n⚠️  No speech detected")

        except Exception as e:
            print(f"\n❌ Recognition error: {e}")

        # Restart wake word detector
        print("🔄 Resuming wake word detection...")
        if self.wake_detector:
            self.wake_detector.start()

        print(f"● Listening for '{self.state['wake_word']}'...\n")

    def send_to_inference(self, transcript):
        """Send transcript to inference endpoint."""

        endpoint = self.state["inference_endpoint"]
        print(f"\n📤 Sending to: {endpoint}")

        try:
            import requests

            payload = {
                "transcript": transcript,
                "timestamp": datetime.now().isoformat(),
                "source": "voice-assistant",
                "wake_word": self.state["wake_word"]
            }

            # Retry logic
            for attempt in range(3):
                try:
                    response = requests.post(
                        endpoint,
                        json=payload,
                        timeout=5.0
                    )

                    if response.status_code == 200:
                        result = response.json()
                        print(f"✓ Response: {result}")
                        return

                    print(f"⚠️  Server returned {response.status_code}")

                except requests.exceptions.RequestException as e:
                    if attempt == 2:
                        raise
                    print(f"⚠️  Retry {attempt + 1}/3...")
                    time.sleep(2 ** attempt)

        except ImportError:
            print("⚠️  requests module not installed")
            print(f"   Would send: {transcript}")
        except Exception as e:
            print(f"⚠️  Network error: {e}")
            print("   Continuing with wake word detection...")

    def run(self):
        """Main application loop."""

        self.print_header("🎙️  VOICE ASSISTANT")

        print("Configuration:")
        print(f"  Wake word: {self.state.get('wake_word', 'Not set')}")
        print(f"  Inference endpoint: {self.state['inference_endpoint']}")
        print(f"  Recognition engine: {self.state['recognition_engine']}")
        print(f"  Silence timeout: {self.state['silence_timeout']}s")

        # Ensure model is trained
        print("\n📋 Checking wake word model...")
        if not self.ensure_model_trained():
            print("❌ Model training failed or cancelled.")
            return 1

        # Setup speech recognition
        print("\n🎤 Setting up speech recognition...")
        self.speech_recognizer = self.setup_speech_recognition()

        if not self.speech_recognizer:
            print("⚠️  Proceeding without speech recognition")
            print("   (Only wake word detection will work)")

        # Start wake word detection
        self.print_section("🎧 Starting Wake Word Detection")

        print(f"● Listening for: '{self.state['wake_word']}'")
        print(f"  Model: {self.state['model_path']}")
        print(f"  Threshold: {self.state['detection_threshold']}")
        print("\nReady! Say your wake word to activate.")
        print("Press Ctrl+C to exit\n")

        try:
            self.wake_detector = WakeWordDetector(
                wake_words=[self.state["model_path"]],
                threshold=self.state["detection_threshold"],
                on_detection=self.on_wake_word_detected
            )

            with self.wake_detector:
                while True:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
            return 0
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Entry point."""

    parser = argparse.ArgumentParser(
        description="Unified voice assistant with wake word and speech recognition"
    )

    parser.add_argument(
        "--wake-word",
        help="Wake word to use (e.g., 'hey edge')"
    )

    parser.add_argument(
        "--retrain",
        action="store_true",
        help="Force retraining even if model exists"
    )

    parser.add_argument(
        "--endpoint",
        help="Inference endpoint URL (default: http://localhost:8000/process)"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        help="Wake word detection threshold (default: 0.5)"
    )

    parser.add_argument(
        "--silence-timeout",
        type=float,
        help="Silence timeout in seconds (default: 3.0)"
    )

    parser.add_argument(
        "--recognizer",
        choices=["vosk", "whisper"],
        help="Speech recognition engine (default: vosk)"
    )

    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    # Create and run assistant
    assistant = VoiceAssistant(args)
    return assistant.run()


if __name__ == "__main__":
    sys.exit(main())
