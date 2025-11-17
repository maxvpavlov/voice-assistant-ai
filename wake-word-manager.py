#!/usr/bin/env python3
"""
Wake Word Manager - Stateful Training & Inference

This script manages the complete lifecycle of wake word models:
- Detects existing training
- Offers to resume or retrain
- Manages state between sessions
- Provides training and inference modes

State is persisted to .wake-word-state.json
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

STATE_FILE = ".wake-word-state.json"


class WakeWordState:
    """Manages persistent state for wake word training."""

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
                return {"models": {}}
        return {"models": {}}

    def save_state(self):
        """Save state to JSON file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Warning: Could not save state: {e}")

    def get_model_info(self, wake_word):
        """Get information about a trained model."""
        normalized = wake_word.lower().replace(" ", "_")
        return self.state["models"].get(normalized)

    def set_model_info(self, wake_word, info):
        """Store information about a trained model."""
        normalized = wake_word.lower().replace(" ", "_")
        info["last_updated"] = datetime.now().isoformat()
        self.state["models"][normalized] = info
        self.save_state()

    def list_models(self):
        """List all known models."""
        return self.state["models"]

    def delete_model_info(self, wake_word):
        """Remove model information from state."""
        normalized = wake_word.lower().replace(" ", "_")
        if normalized in self.state["models"]:
            del self.state["models"][normalized]
            self.save_state()


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_section(title):
    """Print a section separator."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}\n")


def run_command(command, description, show_output=True):
    """Run a shell command."""
    if show_output:
        print(f"🔄 {description}...\n")

    try:
        full_command = f"source venv/bin/activate && {command}"
        result = subprocess.run(
            full_command,
            shell=True,
            executable='/bin/bash',
            capture_output=not show_output,
            text=True
        )

        if result.returncode == 0:
            if show_output:
                print(f"\n✅ {description} complete!")
            return True, result.stdout if not show_output else ""
        else:
            print(f"\n⚠️  Command exited with code {result.returncode}")
            return False, result.stderr if not show_output else ""

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        return False, ""
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False, str(e)


def check_model_exists(wake_word):
    """Check if a model exists on disk."""
    normalized = wake_word.lower().replace(" ", "_")

    # Check for trained model
    model_path = Path(f"models/{normalized}_v0.1.onnx")
    if model_path.exists():
        return True, str(model_path)

    # Check in trained_models directory
    alt_path = Path(f"trained_models/{normalized}/{normalized}_v0.1.onnx")
    if alt_path.exists():
        return True, str(alt_path)

    return False, None


def check_training_data_exists(wake_word):
    """Check if training data exists."""
    normalized = wake_word.lower().replace(" ", "_")
    data_dir = Path(f"training_data/{normalized}/positive")

    if not data_dir.exists():
        return False, 0

    wav_files = list(data_dir.glob("*.wav"))
    return len(wav_files) > 0, len(wav_files)


def display_model_info(wake_word, info, model_path):
    """Display information about an existing model."""
    print_section("📊 Existing Model Found")
    print(f"Wake Word: '{wake_word}'")
    print(f"Model Path: {model_path}")
    print(f"Last Updated: {info.get('last_updated', 'Unknown')}")
    print(f"Training Samples: {info.get('num_samples', 'Unknown')}")
    print(f"Training Method: {info.get('method', 'Unknown')}")

    if info.get('accuracy'):
        print(f"Reported Accuracy: {info['accuracy']}")


def get_user_choice(prompt, options):
    """Get user choice from a list of options."""
    print(f"\n{prompt}\n")
    for i, (key, description) in enumerate(options.items(), 1):
        print(f"  {i}. {description}")

    while True:
        try:
            choice = input("\nEnter your choice (number): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return list(options.keys())[idx]
            print("⚠️  Invalid choice. Please try again.")
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled.")
            sys.exit(0)


def train_wake_word(wake_word, state, force_retrain=False):
    """Train a wake word model."""
    normalized = wake_word.lower().replace(" ", "_")

    print_section(f"🎓 Training Wake Word: '{wake_word}'")

    # Check existing training data
    has_data, num_samples = check_training_data_exists(wake_word)

    if has_data and not force_retrain:
        print(f"✓ Found {num_samples} existing training samples")
        use_existing = input("\nUse existing samples? (y/n): ").strip().lower()

        if use_existing != 'y':
            print("\n🎙️  Recording new samples (this will replace existing data)...")
            success, _ = run_command(
                f'./edge-wake-word train --wake-word "{wake_word}" --num-samples 5',
                "Recording training samples"
            )
            if not success:
                return False
            num_samples = 5
    else:
        print("\n🎙️  Recording training samples...")
        success, _ = run_command(
            f'./edge-wake-word train --wake-word "{wake_word}" --num-samples 5',
            "Recording training samples"
        )
        if not success:
            return False
        num_samples = 5

    # Train model
    print("\n🧠 Training neural network with synthetic data augmentation...")
    print("   This will take 2-5 minutes...\n")

    success, _ = run_command(
        f'python3 train-full-model.py --wake-word "{wake_word}" --epochs 50 --augmentations 20',
        "Training model"
    )

    if not success:
        print("\n❌ Training failed.")
        return False

    # Copy model to deployment directory
    print("\n📦 Installing model...")
    subprocess.run(
        f"cp trained_models/{normalized}/{normalized}_v0.1.onnx* models/",
        shell=True,
        check=False
    )

    # Update state
    model_path = f"models/{normalized}_v0.1.onnx"
    state.set_model_info(wake_word, {
        "model_path": model_path,
        "num_samples": num_samples,
        "method": "full_model",
        "wake_word": wake_word
    })

    print("\n✅ Training complete!")
    print(f"   Model saved to: {model_path}")

    return True


def run_inference(wake_word, model_path, threshold=0.5):
    """Run wake word detection."""
    print_section(f"🎙️  Wake Word Detection: '{wake_word}'")
    print(f"Model: {model_path}")
    print(f"Threshold: {threshold}")
    print("\nListening... (Press Ctrl+C to exit)\n")

    subprocess.run(
        f"source venv/bin/activate && ./edge-wake-word test --model {model_path} --threshold {threshold}",
        shell=True,
        executable='/bin/bash'
    )


def list_all_models(state):
    """List all available models."""
    print_section("📋 Available Models")

    models = state.list_models()

    if not models:
        print("No models found. Train a model first!")
        return []

    model_list = []
    for i, (name, info) in enumerate(models.items(), 1):
        exists, path = check_model_exists(info.get('wake_word', name))
        status = "✓" if exists else "✗"

        print(f"{i}. [{status}] {info.get('wake_word', name)}")
        print(f"   Path: {info.get('model_path', 'Unknown')}")
        print(f"   Updated: {info.get('last_updated', 'Unknown')[:10]}")

        if exists:
            model_list.append((info.get('wake_word', name), path))
        print()

    return model_list


def main():
    """Main application logic."""
    state = WakeWordState()

    print_header("🎙️  WAKE WORD MANAGER")
    print("Manage your custom wake word models with persistent state.\n")

    # Main loop
    while True:
        action = get_user_choice(
            "What would you like to do?",
            {
                "train": "Train a new wake word",
                "inference": "Run wake word detection",
                "list": "List all models",
                "delete": "Delete a model",
                "quit": "Exit"
            }
        )

        if action == "quit":
            print("\n👋 Goodbye!\n")
            break

        elif action == "list":
            list_all_models(state)
            continue

        elif action == "train":
            # Get wake word
            print_section("New Wake Word Training")
            wake_word = input("Enter your wake word: ").strip()

            if not wake_word:
                print("⚠️  Wake word cannot be empty.")
                continue

            # Check if model already exists
            model_info = state.get_model_info(wake_word)
            model_exists, model_path = check_model_exists(wake_word)

            if model_exists and model_info:
                display_model_info(wake_word, model_info, model_path)

                choice = get_user_choice(
                    "This wake word already has a trained model. What would you like to do?",
                    {
                        "use": "Use existing model (go to inference)",
                        "retrain": "Retrain from scratch",
                        "cancel": "Cancel and go back"
                    }
                )

                if choice == "use":
                    threshold = 0.5
                    custom_threshold = input(f"\nDetection threshold (default: {threshold}): ").strip()
                    if custom_threshold:
                        try:
                            threshold = float(custom_threshold)
                        except ValueError:
                            print("⚠️  Invalid threshold, using default.")

                    run_inference(wake_word, model_path, threshold)
                    continue

                elif choice == "retrain":
                    if train_wake_word(wake_word, state, force_retrain=True):
                        print("\n🎉 Model retrained successfully!")

                        test_now = input("\nTest the model now? (y/n): ").strip().lower()
                        if test_now == 'y':
                            _, new_path = check_model_exists(wake_word)
                            run_inference(wake_word, new_path, 0.5)

                else:  # cancel
                    continue

            else:
                # New model - train it
                if train_wake_word(wake_word, state):
                    print("\n🎉 Model trained successfully!")

                    test_now = input("\nTest the model now? (y/n): ").strip().lower()
                    if test_now == 'y':
                        _, model_path = check_model_exists(wake_word)
                        run_inference(wake_word, model_path, 0.5)

        elif action == "inference":
            # List available models
            available_models = list_all_models(state)

            if not available_models:
                print("\n⚠️  No trained models available. Please train a model first.")
                continue

            # Get model choice
            print("Select a model:")
            for i, (wake_word, path) in enumerate(available_models, 1):
                print(f"  {i}. {wake_word}")

            try:
                choice = int(input("\nEnter model number: ").strip()) - 1
                if 0 <= choice < len(available_models):
                    wake_word, model_path = available_models[choice]

                    # Get threshold
                    threshold = 0.5
                    custom_threshold = input(f"\nDetection threshold (default: {threshold}): ").strip()
                    if custom_threshold:
                        try:
                            threshold = float(custom_threshold)
                        except ValueError:
                            print("⚠️  Invalid threshold, using default.")

                    run_inference(wake_word, model_path, threshold)
                else:
                    print("⚠️  Invalid choice.")
            except (ValueError, KeyboardInterrupt):
                print("\n⚠️  Invalid input.")

        elif action == "delete":
            available_models = list_all_models(state)

            if not available_models:
                print("\n⚠️  No models to delete.")
                continue

            print("Select a model to delete:")
            for i, (wake_word, path) in enumerate(available_models, 1):
                print(f"  {i}. {wake_word}")

            try:
                choice = int(input("\nEnter model number: ").strip()) - 1
                if 0 <= choice < len(available_models):
                    wake_word, model_path = available_models[choice]

                    confirm = input(f"\n⚠️  Delete '{wake_word}' model? (yes/no): ").strip().lower()
                    if confirm == "yes":
                        state.delete_model_info(wake_word)
                        print(f"\n✓ Model info removed from state.")
                        print(f"Note: Files still exist at: {model_path}")
                        print(f"      Delete manually if needed.")
                    else:
                        print("\nCancelled.")
                else:
                    print("⚠️  Invalid choice.")
            except (ValueError, KeyboardInterrupt):
                print("\n⚠️  Invalid input.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
