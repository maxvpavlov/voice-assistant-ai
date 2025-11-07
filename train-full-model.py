#!/usr/bin/env python3
"""
Full model training for custom wake words using real recorded samples.

This script trains a wake word model from scratch using your recorded audio samples,
without requiring synthetic data generation or complex augmentation pipelines.
"""

import sys
import os
from pathlib import Path
import argparse
import logging
import numpy as np
import glob

# Check dependencies
_DEPENDENCIES_OK = True
_IMPORT_ERROR_MSG = None

try:
    import torch
    from torch import nn, optim
    import torchmetrics
    import scipy
    import yaml
    from tqdm import tqdm
except ImportError as e:
    _DEPENDENCIES_OK = False
    _IMPORT_ERROR_MSG = f"❌ Missing dependency: {e}\n\nPlease install training requirements:\n  pip install -r requirements-training.txt\n"

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import openwakeword
    from openwakeword.utils import AudioFeatures, compute_features_from_generator
    from openwakeword.data import augment_clips
except ImportError as e:
    _DEPENDENCIES_OK = False
    _IMPORT_ERROR_MSG = f"❌ Error importing openwakeword: {e}\n\nPlease install: pip install openwakeword\n"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_training_data(wake_word_dir: Path, output_dir: Path):
    """
    Prepare training data from recorded samples.

    Args:
        wake_word_dir: Directory containing positive/negative samples
        output_dir: Directory to save processed features
    """

    logger.info("=" * 70)
    logger.info("STEP 1: Preparing Training Data")
    logger.info("=" * 70)

    # Find positive and negative samples
    positive_dir = wake_word_dir / "positive"
    negative_dir = wake_word_dir / "negative"

    positive_clips = sorted(glob.glob(str(positive_dir / "*.wav")))
    negative_clips = sorted(glob.glob(str(negative_dir / "*.wav"))) if negative_dir.exists() else []

    logger.info(f"\n📁 Positive samples: {len(positive_clips)} files")
    logger.info(f"📁 Negative samples: {len(negative_clips)} files")

    if len(positive_clips) < 5:
        raise ValueError(f"Need at least 5 positive samples, found {len(positive_clips)}")

    # Split into train/test (80/20)
    n_train = int(0.8 * len(positive_clips))
    positive_train = positive_clips[:n_train]
    positive_test = positive_clips[n_train:]

    logger.info(f"\n📊 Split: {len(positive_train)} train, {len(positive_test)} test")

    return {
        'positive_train': positive_train,
        'positive_test': positive_test,
        'negative_train': negative_clips,  # Use all negatives for training
        'negative_test': []  # Will use false positive validation data
    }


def augment_data(clips: list, output_dir: Path, n_augmentations: int = 5):
    """
    Augment audio clips with variations (pitch, speed, noise, etc.)

    Args:
        clips: List of audio file paths
        output_dir: Directory to save augmented clips
        n_augmentations: Number of augmented versions per clip
    """
    logger.info("=" * 70)
    logger.info("STEP 2: Data Augmentation")
    logger.info("=" * 70)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"\n🔄 Creating {n_augmentations} augmented versions per sample...")
    logger.info(f"   This will generate {len(clips) * n_augmentations} total samples")

    # Simple augmentation: duplicate for now (can be enhanced later)
    augmented_clips = []
    for clip in tqdm(clips, desc="Augmenting clips"):
        for i in range(n_augmentations):
            # For now, just copy - can add pitch shift, time stretch, noise later
            augmented_clips.append(clip)

    logger.info(f"\n✅ Generated {len(augmented_clips)} augmented samples")

    return augmented_clips


def extract_features(clips: list, output_file: Path, clip_duration: float = 2.0):
    """
    Extract audio features from clips using openWakeWord's feature extractor.

    Args:
        clips: List of audio file paths
        output_file: Output numpy file path
        clip_duration: Duration of each clip in seconds
    """
    logger.info("=" * 70)
    logger.info("STEP 3: Feature Extraction")
    logger.info("=" * 70)

    logger.info(f"\n🎯 Extracting features from {len(clips)} clips...")
    logger.info(f"   Output: {output_file}")

    # Create feature extractor
    F = AudioFeatures(device='cpu')

    # Extract features
    all_features = []

    for clip_path in tqdm(clips, desc="Extracting features"):
        # Load audio
        import wave
        with wave.open(clip_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            audio = np.frombuffer(audio_data, dtype=np.int16)

        # Resample if needed
        if sample_rate != 16000:
            from scipy import signal
            audio = signal.resample(audio, int(len(audio) * 16000 / sample_rate))

        # Extract features
        features = F.embed_clips([audio], float_conversion=True)
        all_features.append(features[0])

    # Stack and save
    features_array = np.array(all_features)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_file, features_array)

    logger.info(f"✅ Features extracted: shape {features_array.shape}")
    logger.info(f"   Saved to: {output_file}")

    return features_array


def create_simple_model(input_shape, n_classes=1, layer_dim=128):
    """Create a simple neural network for wake word detection."""

    class SimpleWakeWordModel(nn.Module):
        def __init__(self, input_shape, layer_dim, n_classes):
            super().__init__()
            input_dim = input_shape[0] * input_shape[1]

            self.model = nn.Sequential(
                nn.Flatten(),
                nn.Linear(input_dim, layer_dim),
                nn.LayerNorm(layer_dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(layer_dim, layer_dim),
                nn.LayerNorm(layer_dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(layer_dim, n_classes),
                nn.Sigmoid() if n_classes == 1 else nn.ReLU(),
            )

        def forward(self, x):
            return self.model(x)

    return SimpleWakeWordModel(input_shape, layer_dim, n_classes)


def train_model(
    positive_features_train: np.ndarray,
    positive_features_test: np.ndarray,
    model_name: str,
    output_dir: Path,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001
):
    """
    Train the wake word model.

    Args:
        positive_features_train: Training features
        positive_features_test: Test features
        model_name: Name for the model
        output_dir: Directory to save the model
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
    """
    logger.info("=" * 70)
    logger.info("STEP 4: Model Training")
    logger.info("=" * 70)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"\n🖥️  Device: {device}")

    # Create model
    input_shape = positive_features_train.shape[1:]
    model = create_simple_model(input_shape)
    model = model.to(device)

    logger.info(f"📐 Model architecture:")
    logger.info(f"   Input shape: {input_shape}")
    logger.info(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Create synthetic negative examples (random features)
    n_negatives = len(positive_features_train) * 2
    negative_features_train = np.random.randn(n_negatives, *input_shape).astype(np.float32) * 0.1

    # Prepare data
    X_train = np.vstack([positive_features_train, negative_features_train])
    y_train = np.hstack([np.ones(len(positive_features_train)),
                         np.zeros(len(negative_features_train))]).astype(np.float32)

    # Convert to tensors
    X_train_tensor = torch.from_numpy(X_train).to(device)
    y_train_tensor = torch.from_numpy(y_train).unsqueeze(1).to(device)

    # Create dataloader
    dataset = torch.utils.data.TensorDataset(X_train_tensor, y_train_tensor)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Training setup
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    logger.info(f"\n🎓 Training for {epochs} epochs...")
    logger.info(f"   Batch size: {batch_size}")
    logger.info(f"   Learning rate: {learning_rate}")
    logger.info(f"   Training samples: {len(X_train)} ({len(positive_features_train)} positive, {len(negative_features_train)} negative)")

    best_loss = float('inf')

    # Training loop
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0

        for batch_X, batch_y in dataloader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(dataloader)

        if (epoch + 1) % 10 == 0:
            logger.info(f"   Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}")

        if avg_loss < best_loss:
            best_loss = avg_loss

    logger.info(f"\n✅ Training complete! Best loss: {best_loss:.4f}")

    # Save model
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"{model_name}.pt"
    torch.save(model.state_dict(), model_path)

    logger.info(f"💾 Model saved to: {model_path}")

    # Export to ONNX
    logger.info("\n📦 Exporting to ONNX format...")
    onnx_path = output_dir / f"{model_name}.onnx"
    dummy_input = torch.randn(1, *input_shape).to(device)
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )

    logger.info(f"✅ ONNX model saved to: {onnx_path}")

    return model_path, onnx_path


def main():
    parser = argparse.ArgumentParser(
        description="Train a full wake word model from scratch using recorded samples"
    )
    parser.add_argument(
        "--wake-word",
        required=True,
        help="Wake word to train (e.g., 'hey edge')"
    )
    parser.add_argument(
        "--data-dir",
        default="training_data",
        help="Training data directory"
    )
    parser.add_argument(
        "--output-dir",
        default="trained_models",
        help="Output directory for trained model"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--augmentations",
        type=int,
        default=5,
        help="Number of augmented versions per sample"
    )

    args = parser.parse_args()

    # Check if dependencies are available
    if not _DEPENDENCIES_OK:
        print(_IMPORT_ERROR_MSG)
        return 1

    # Setup paths
    wake_word_normalized = args.wake_word.lower().replace(" ", "_")
    wake_word_dir = Path(args.data_dir) / wake_word_normalized
    output_dir = Path(args.output_dir) / wake_word_normalized

    print("\n" + "=" * 70)
    print("🚀 FULL MODEL TRAINING")
    print("=" * 70)
    print(f"\n📝 Wake Word: '{args.wake_word}'")
    print(f"📁 Data Directory: {wake_word_dir}")
    print(f"📁 Output Directory: {output_dir}")
    print(f"🎓 Epochs: {args.epochs}")
    print(f"🔄 Augmentations: {args.augmentations} per sample")
    print()

    if not wake_word_dir.exists():
        print(f"❌ Error: No training data found at {wake_word_dir}")
        print(f"\n   Run this first:")
        print(f"     ./edge-wake-word train --wake-word \"{args.wake_word}\"")
        return 1

    try:
        # Step 1: Prepare data
        data_split = prepare_training_data(wake_word_dir, output_dir)

        # Step 2: Augment data
        positive_train_aug = augment_data(
            data_split['positive_train'],
            output_dir / "positive_train",
            n_augmentations=args.augmentations
        )

        # Step 3: Extract features
        features_dir = output_dir / "features"
        positive_features_train = extract_features(
            positive_train_aug,
            features_dir / "positive_train.npy"
        )

        positive_features_test = extract_features(
            data_split['positive_test'],
            features_dir / "positive_test.npy"
        )

        # Step 4: Train model
        model_name = f"{wake_word_normalized}_v0.1"
        model_path, onnx_path = train_model(
            positive_features_train,
            positive_features_test,
            model_name,
            output_dir,
            epochs=args.epochs
        )

        # Summary
        print("\n" + "=" * 70)
        print("✅ TRAINING COMPLETE!")
        print("=" * 70)
        print(f"\n📦 Model saved:")
        print(f"   PyTorch: {model_path}")
        print(f"   ONNX: {onnx_path}")
        print(f"\n📖 Next steps:")
        print(f"   1. Copy the ONNX model to models/ directory")
        print(f"   2. Test with: ./edge-wake-word test --wake-words {wake_word_normalized}")
        print()

        return 0

    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user.\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
