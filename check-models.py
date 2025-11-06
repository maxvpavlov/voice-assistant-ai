#!/usr/bin/env python3
"""
Download and list openWakeWord models
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import openwakeword
    from openwakeword.model import Model
    from pathlib import Path

    # Get the models directory
    pkg_path = Path(openwakeword.__file__).parent
    models_dir = pkg_path / 'resources' / 'models'

    print("OpenWakeWord Models Check")
    print("="*70)
    print(f"\nPackage location: {pkg_path}")
    print(f"Models directory: {models_dir}")
    print(f"Directory exists: {models_dir.exists()}")

    if models_dir.exists():
        print("\nAvailable model files:")
        models = sorted(models_dir.glob('*'))
        if models:
            for f in models:
                print(f"  ✓ {f.name}")
        else:
            print("  (no models found)")

    print("\n" + "="*70)
    print("Testing model download...")
    print("="*70)

    # Try to initialize a model (this will auto-download)
    print("\nInitializing 'alexa' model (will auto-download if needed)...")
    try:
        model = Model(wakeword_models=["alexa"], inference_framework="onnx")
        print("✓ Model loaded successfully!")
        print(f"\nLoaded models: {list(model.models.keys())}")
    except Exception as e:
        print(f"❌ Error loading model: {e}")

    print("\n" + "="*70)
    print("Checking models again after download attempt...")
    print("="*70)

    if models_dir.exists():
        print("\nAvailable model files:")
        models = sorted(models_dir.glob('*'))
        for f in models:
            size_mb = f.stat().st_size / (1024*1024)
            print(f"  ✓ {f.name} ({size_mb:.1f} MB)")

except ImportError as e:
    print(f"Error: {e}")
    print("Please run: pip install openwakeword")
    sys.exit(1)
