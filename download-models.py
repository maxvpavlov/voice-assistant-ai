#!/usr/bin/env python3
"""
Manually download openWakeWord models
"""
import sys
from pathlib import Path
import urllib.request
import os

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import openwakeword

    # Get the models directory
    pkg_path = Path(openwakeword.__file__).parent
    models_dir = pkg_path / 'resources' / 'models'

    print("OpenWakeWord Model Downloader")
    print("="*70)
    print(f"\nTarget directory: {models_dir}")

    # Create the directory if it doesn't exist
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created models directory: {models_dir}")

    # Try using the built-in download utility first
    print("\nAttempting to download models using openwakeword utility...")
    print("-"*70)

    try:
        from openwakeword.utils import download_models
        print("Calling openwakeword.utils.download_models()...")
        download_models()

        # Check if models were downloaded
        models = list(models_dir.glob('*.onnx'))
        if models:
            print("\n✓ Models downloaded successfully!")
            print(f"\nAvailable models in {models_dir}:")
            for f in sorted(models):
                size_mb = f.stat().st_size / (1024*1024)
                print(f"  ✓ {f.name} ({size_mb:.1f} MB)")

            print("\n" + "="*70)
            print("✅ SUCCESS! You can now run:")
            print("   ./edge-wake-word train-local --wake-word \"hey edge\"")
            print("="*70)
            return
        else:
            print("⚠️  download_models() completed but no models found")
            print("Trying manual download from Hugging Face...\n")
    except Exception as e:
        print(f"⚠️  Utility download failed: {e}")
        print("Trying manual download from Hugging Face...\n")

    # Model to download from Hugging Face
    model_name = "alexa_v0.1.onnx"
    model_url = f"https://huggingface.co/davidscripka/openwakeword/resolve/main/{model_name}"
    output_path = models_dir / model_name

    print(f"Downloading {model_name}...")
    print(f"From: {model_url}")
    print(f"To: {output_path}")
    print()

    def download_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 / total_size)
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r  Progress: [{bar}] {percent:.1f}%", end='', flush=True)

    try:
        urllib.request.urlretrieve(model_url, output_path, reporthook=download_progress)
        print("\n")

        # Verify the file
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024*1024)
            print(f"✓ Download complete! ({size_mb:.1f} MB)")
            print(f"✓ Model saved to: {output_path}")

            # List all models
            print(f"\nAvailable models in {models_dir}:")
            for f in sorted(models_dir.glob('*.onnx')):
                size_mb = f.stat().st_size / (1024*1024)
                print(f"  ✓ {f.name} ({size_mb:.1f} MB)")

            print("\n" + "="*70)
            print("✅ SUCCESS! You can now run:")
            print("   ./edge-wake-word train-local --wake-word \"hey edge\"")
            print("="*70)
        else:
            print("❌ Download failed - file not found")

    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\nTrying alternative method...")

        # Try with requests library
        try:
            import requests
            print(f"Downloading with requests library...")
            response = requests.get(model_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = downloaded * 100 / total_size if total_size > 0 else 0
                        bar_length = 40
                        filled = int(bar_length * percent / 100)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        print(f"\r  Progress: [{bar}] {percent:.1f}%", end='', flush=True)

            print("\n")
            size_mb = output_path.stat().st_size / (1024*1024)
            print(f"✓ Download complete! ({size_mb:.1f} MB)")
            print("✅ SUCCESS! Model downloaded.")

        except ImportError:
            print("requests library not available. Please install: pip install requests")
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")
            print("\nManual download instructions:")
            print(f"1. Download from: {model_url}")
            print(f"2. Save to: {output_path}")

except ImportError as e:
    print(f"Error: {e}")
    print("Please run: pip install openwakeword")
