#!/usr/bin/env python3
"""
Automatically find and copy openWakeWord models to git-trackable location.
This script locates models in your openwakeword installation and copies them
to the models/ directory so they can be committed to git.
"""
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Find and copy models to git-trackable location."""
    print("OpenWakeWord Model Copy Utility")
    print("=" * 70)

    try:
        import openwakeword

        # Find the openwakeword models directory
        pkg_path = Path(openwakeword.__file__).parent
        source_models_dir = pkg_path / 'resources' / 'models'

        print(f"\n📁 Found openwakeword installation at:")
        print(f"   {pkg_path}")
        print(f"\n📦 Source models directory:")
        print(f"   {source_models_dir}")

        if not source_models_dir.exists():
            print(f"\n❌ Models directory not found!")
            print(f"   Please run: python3 download-models.py first")
            return 1

        # Create local models directory
        repo_root = Path(__file__).parent
        dest_models_dir = repo_root / 'models'
        dest_models_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📂 Destination directory:")
        print(f"   {dest_models_dir}")
        print()

        # Models needed for training with custom verifiers
        required_models = [
            # Base wake word models
            'alexa_v0.1.onnx',
            'alexa_v0.1.tflite',
            'hey_jarvis_v0.1.onnx',      # For "hey" phrases like "hey edge"
            'hey_jarvis_v0.1.tflite',    # For "hey" phrases like "hey edge"
            'hey_mycroft_v0.1.onnx',     # Alternative for "hey" phrases
            'hey_mycroft_v0.1.tflite',   # Alternative for "hey" phrases

            # Required preprocessing models
            'embedding_model.onnx',
            'embedding_model.tflite',
            'melspectrogram.onnx',
            'melspectrogram.tflite',
        ]

        copied_count = 0
        skipped_count = 0
        missing_count = 0

        print("Copying models:")
        print("-" * 70)

        for model_name in required_models:
            source_file = source_models_dir / model_name
            dest_file = dest_models_dir / model_name

            if not source_file.exists():
                print(f"  ⚠️  {model_name:30} - NOT FOUND (skipping)")
                missing_count += 1
                continue

            # Check file size to verify it's valid
            file_size = source_file.stat().st_size

            if file_size < 1024:  # Less than 1KB is likely corrupted
                print(f"  ⚠️  {model_name:30} - CORRUPTED ({file_size} bytes)")
                missing_count += 1
                continue

            # Check if already exists and is identical
            if dest_file.exists():
                if dest_file.stat().st_size == file_size:
                    size_mb = file_size / (1024 * 1024)
                    print(f"  ✓  {model_name:30} - already exists ({size_mb:.1f} MB)")
                    skipped_count += 1
                    continue

            # Copy the file
            shutil.copy2(source_file, dest_file)
            size_mb = file_size / (1024 * 1024)
            print(f"  ✅ {model_name:30} - copied ({size_mb:.1f} MB)")
            copied_count += 1

        print()
        print("=" * 70)
        print(f"Summary:")
        print(f"  ✅ Copied: {copied_count}")
        print(f"  ✓  Already existed: {skipped_count}")
        print(f"  ⚠️  Missing/Corrupted: {missing_count}")
        print()

        if missing_count > 0:
            print("⚠️  Some models are missing or corrupted.")
            print("   Run: python3 download-models.py")
            print()

        # Check what's now available
        available_models = sorted(dest_models_dir.glob('*.onnx'))
        if available_models:
            print(f"Available ONNX models in {dest_models_dir}:")
            for model_file in available_models:
                size_mb = model_file.stat().st_size / (1024 * 1024)
                print(f"  • {model_file.name:30} ({size_mb:.1f} MB)")
            print()

        print("=" * 70)
        print("✅ Models are ready to commit to git!")
        print()
        print("Next steps:")
        print("  1. git add models/")
        print("  2. git commit -m 'Add base openWakeWord models'")
        print("  3. git push")
        print("=" * 70)

        return 0

    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease install openwakeword first:")
        print("  pip install openwakeword onnxruntime")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
