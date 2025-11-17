#!/usr/bin/env python3
"""
Guided Wake Word Training - Interactive Console App

This script provides step-by-step guidance for:
1. Recording training samples from your voice
2. Generating synthetic variations
3. Training a custom wake word model
4. Testing the trained model

No prior ML knowledge required!
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step_num, total_steps, title):
    """Print a step header."""
    print(f"\n{'─' * 70}")
    print(f"📍 STEP {step_num}/{total_steps}: {title}")
    print(f"{'─' * 70}\n")


def wait_for_enter(message="Press Enter to continue..."):
    """Wait for user to press Enter."""
    try:
        input(f"\n{message}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(0)


def run_command(command, description, timeout=None):
    """Run a shell command and show output."""
    print(f"🔄 {description}...")
    print(f"   Command: {command}\n")

    try:
        # Activate venv and run command
        full_command = f"source venv/bin/activate && {command}"
        result = subprocess.run(
            full_command,
            shell=True,
            executable='/bin/bash',
            capture_output=False,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            print(f"\n⚠️  Warning: Command exited with code {result.returncode}")
            return False

        print(f"\n✅ {description} complete!")
        return True

    except subprocess.TimeoutExpired:
        print(f"\n⏱️  Command timed out after {timeout} seconds")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Main guided training workflow."""

    # Welcome
    print_header("🎙️  GUIDED WAKE WORD TRAINING")
    print("Welcome! This interactive tool will help you create a custom wake word")
    print("for voice activation. The process takes about 5-10 minutes.\n")
    print("What you'll do:")
    print("  1. Choose your custom wake word (e.g., 'hey edge', 'computer')")
    print("  2. Record 5 voice samples")
    print("  3. Let the AI generate 80+ synthetic variations")
    print("  4. Train a neural network model")
    print("  5. Test your wake word detection!")

    wait_for_enter("\nReady to begin? Press Enter to start...")

    # Step 1: Get wake word
    print_step(1, 5, "Choose Your Wake Word")
    print("Choose a wake word that is:")
    print("  • Easy to pronounce consistently")
    print("  • 2-4 syllables (e.g., 'hey edge', 'computer activate')")
    print("  • Not too common in everyday speech\n")

    while True:
        wake_word = input("Enter your wake word: ").strip()
        if wake_word:
            wake_word_normalized = wake_word.lower().replace(" ", "_")
            print(f"\n✓ Wake word: '{wake_word}'")
            print(f"  Normalized: '{wake_word_normalized}'")

            confirm = input("\nIs this correct? (y/n): ").strip().lower()
            if confirm == 'y':
                break
        else:
            print("⚠️  Please enter a wake word.")

    # Step 2: Microphone test
    print_step(2, 5, "Test Your Microphone")
    print("Before recording, let's make sure your microphone works properly.\n")

    wait_for_enter("Press Enter to test your microphone...")

    success = run_command(
        f"./edge-wake-word train --test-mic",
        "Testing microphone",
        timeout=10
    )

    if not success:
        print("\n⚠️  Microphone test had issues. Check your audio settings.")
        cont = input("Continue anyway? (y/n): ").strip().lower()
        if cont != 'y':
            print("\nExiting. Please fix microphone issues and try again.")
            sys.exit(1)

    # Step 3: Record samples
    print_step(3, 5, "Record Training Samples")
    print(f"Now you'll record 5 samples of yourself saying '{wake_word}'.\n")
    print("💡 Tips for best results:")
    print("   • Speak clearly and naturally")
    print("   • Use your normal voice volume")
    print("   • Try slight variations (tone, speed)")
    print("   • Record in the environment where you'll use it")
    print("   • Wait for the countdown before speaking\n")

    wait_for_enter("Ready to record? Press Enter to begin...")

    success = run_command(
        f'./edge-wake-word train --wake-word "{wake_word}" --num-samples 5',
        f"Recording 5 samples of '{wake_word}'",
        timeout=300
    )

    if not success:
        print("\n❌ Recording failed. Please try again.")
        sys.exit(1)

    # Step 4: Train with synthetic data
    print_step(4, 5, "Train Your Model")
    print("Great! Now we'll:")
    print("  1. Generate 80 synthetic variations (pitch, speed, noise)")
    print("  2. Create 252 negative examples (things that aren't your wake word)")
    print("  3. Train a neural network (50 epochs, ~2-3 minutes)\n")
    print("This is all automatic - sit back and relax! ☕")

    wait_for_enter("Press Enter to start training...")

    # Check if training dependencies are installed
    print("\n🔍 Checking training dependencies...")
    try:
        subprocess.run(
            "source venv/bin/activate && python3 -c 'import torch'",
            shell=True,
            executable='/bin/bash',
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        print("\n📦 Installing training dependencies (PyTorch, ~500MB)...")
        print("This is a one-time installation and may take a few minutes.\n")

        success = run_command(
            "pip install -r requirements-training.txt",
            "Installing training dependencies",
            timeout=600
        )

        if not success:
            print("\n❌ Failed to install dependencies. Please check your internet connection.")
            sys.exit(1)

    print("✓ Dependencies ready!\n")

    # Run training
    success = run_command(
        f'python3 train-full-model.py --wake-word "{wake_word}" --epochs 50 --augmentations 20',
        "Training your custom model",
        timeout=600
    )

    if not success:
        print("\n❌ Training failed. Check the output above for errors.")
        sys.exit(1)

    # Copy model to models directory
    print("\n📦 Installing model...")
    model_src = f"trained_models/{wake_word_normalized}/{wake_word_normalized}_v0.1.onnx*"
    subprocess.run(f"cp {model_src} models/", shell=True)

    # Step 5: Test the model
    print_step(5, 5, "Test Your Wake Word!")
    print("🎉 Training complete! Your model is ready.\n")
    print("Now let's test it. When you run the test:")
    print(f"  • Say '{wake_word}' into your microphone")
    print("  • The detector will show when it recognizes your voice")
    print("  • Try different volumes and distances")
    print("  • Press Ctrl+C to exit\n")

    model_path = f"models/{wake_word_normalized}_v0.1.onnx"

    wait_for_enter("Ready to test? Press Enter to start detection...")

    print("\n" + "=" * 70)
    print("🎙️  WAKE WORD DETECTION TEST")
    print("=" * 70)
    print(f"\nListening for: '{wake_word}'")
    print("Speak into your microphone and watch for detections!")
    print("Press Ctrl+C to exit when done.\n")

    # Run test with no timeout - user controls exit with Ctrl+C
    subprocess.run(
        f"source venv/bin/activate && ./edge-wake-word test --model {model_path} --threshold 0.5",
        shell=True,
        executable='/bin/bash'
    )

    # Completion
    print("\n\n" + "=" * 70)
    print("✅ GUIDED TRAINING COMPLETE!")
    print("=" * 70 + "\n")

    print(f"Your wake word '{wake_word}' is now trained and ready to use!\n")
    print("📁 Files created:")
    print(f"   Training data: training_data/{wake_word_normalized}/")
    print(f"   Model: models/{wake_word_normalized}_v0.1.onnx")
    print(f"   Full training output: trained_models/{wake_word_normalized}/\n")

    print("🚀 How to use your model:")
    print(f"   # Test mode (with visual feedback)")
    print(f"   ./edge-wake-word test --model models/{wake_word_normalized}_v0.1.onnx\n")
    print(f"   # Production mode (no visual feedback)")
    print(f"   ./edge-wake-word run --model models/{wake_word_normalized}_v0.1.onnx\n")

    print("💡 Tips for improvement:")
    print("   • Record 50-100 samples for production quality")
    print("   • Include negative samples (--with-negatives)")
    print("   • Retrain if accuracy is low")
    print("   • Adjust --threshold (0.3-0.7) for sensitivity\n")

    print("Thank you for using the Guided Wake Word Training tool! 🎉\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Training cancelled by user.")
        print("Your progress has been saved. Run this script again to resume.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
