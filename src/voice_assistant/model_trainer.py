"""
Model Training Module
Trains custom verifier models using recorded audio samples.
"""

import logging
from pathlib import Path
from typing import List, Optional
import glob

try:
    import openwakeword
    from openwakeword import train_custom_verifier
except ImportError as e:
    raise ImportError(
        f"Training dependencies not installed: {e}. "
        "Please run: pip install -r requirements.txt"
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trains custom verifier models for wake word detection.

    Uses openWakeWord's custom verifier training which requires:
    - Minimum 3-5 positive samples (saying the wake word)
    - Optional negative samples (background noise/other speech)
    """

    def __init__(self, training_data_dir: str = "training_data"):
        """
        Initialize the model trainer.

        Args:
            training_data_dir: Root directory containing training samples
        """
        self.training_data_dir = Path(training_data_dir)
        logger.info(f"Model trainer initialized. Data directory: {self.training_data_dir}")

    def train_verifier(
        self,
        wake_word: str,
        base_model: str = "alexa",
        output_path: Optional[str] = None,
        verifier_threshold: float = 0.3
    ) -> Path:
        """
        Train a custom verifier model using recorded samples.

        Args:
            wake_word: Name of wake word (e.g., 'hey_edge')
            base_model: Base openWakeWord model to use (default: 'alexa')
            output_path: Optional custom output path for the model
            verifier_threshold: Threshold for verifier activation (default: 0.3)

        Returns:
            Path to the trained verifier model (.pkl file)
        """
        wake_word_normalized = wake_word.lower().replace(" ", "_")

        # Find positive samples
        positive_dir = self.training_data_dir / wake_word_normalized / "positive"
        if not positive_dir.exists():
            raise ValueError(
                f"No positive samples found at {positive_dir}. "
                f"Run: ./edge-wake-word train --wake-word \"{wake_word}\" first"
            )

        positive_clips = sorted(glob.glob(str(positive_dir / "*.wav")))

        if len(positive_clips) < 3:
            logger.warning(
                f"Only {len(positive_clips)} positive samples found. "
                "Minimum 3 recommended for best results."
            )

        logger.info(f"Found {len(positive_clips)} positive samples")

        # Find negative samples (optional)
        negative_dir = self.training_data_dir / wake_word_normalized / "negative"
        negative_clips = []

        if negative_dir.exists():
            negative_clips = sorted(glob.glob(str(negative_dir / "*.wav")))
            logger.info(f"Found {len(negative_clips)} negative samples")
        else:
            logger.info("No negative samples found (optional)")

        # Determine output path
        if output_path is None:
            models_dir = self.training_data_dir / wake_word_normalized / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            output_path = models_dir / f"{wake_word_normalized}_verifier.pkl"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"\nTraining custom verifier model...")
        logger.info(f"  Wake word: {wake_word}")
        logger.info(f"  Base model: {base_model}")
        logger.info(f"  Positive samples: {len(positive_clips)}")
        logger.info(f"  Negative samples: {len(negative_clips)}")
        logger.info(f"  Output: {output_path}")

        # Train the verifier model
        try:
            train_custom_verifier(
                positive_reference_clips=positive_clips,
                negative_reference_clips=negative_clips if negative_clips else None,
                output_path=str(output_path),
                model_name=f"{base_model}.tflite"  # Use .tflite extension
            )

            logger.info(f"\n✅ Model training complete!")
            logger.info(f"   Saved to: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

    def list_available_wake_words(self) -> List[str]:
        """List all wake words with recorded training data."""
        if not self.training_data_dir.exists():
            return []

        wake_words = []
        for item in self.training_data_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                positive_dir = item / "positive"
                if positive_dir.exists() and any(positive_dir.glob("*.wav")):
                    wake_words.append(item.name)

        return sorted(wake_words)

    def get_sample_counts(self, wake_word: str) -> dict:
        """
        Get count of positive and negative samples for a wake word.

        Args:
            wake_word: Name of the wake word

        Returns:
            Dictionary with 'positive' and 'negative' counts
        """
        wake_word_normalized = wake_word.lower().replace(" ", "_")

        positive_dir = self.training_data_dir / wake_word_normalized / "positive"
        negative_dir = self.training_data_dir / wake_word_normalized / "negative"

        counts = {
            'positive': len(list(positive_dir.glob("*.wav"))) if positive_dir.exists() else 0,
            'negative': len(list(negative_dir.glob("*.wav"))) if negative_dir.exists() else 0
        }

        return counts
