"""
Wake Word Detector Module
Uses openWakeWord for detecting activation phrases.
"""

import logging
import numpy as np
from typing import Callable, Optional, List
import threading
import queue

try:
    from openwakeword.model import Model
    import pyaudio
except ImportError as e:
    raise ImportError(
        f"Required dependencies not installed: {e}. "
        "Please run: pip install -r requirements.txt"
    )


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Detects wake words using openWakeWord library.

    Supports multiple pre-trained wake words and custom models.
    Runs in a separate thread to avoid blocking the main application.
    """

    # Audio configuration
    CHUNK_SIZE = 1280  # 80ms at 16kHz (recommended by openWakeWord)
    SAMPLE_RATE = 16000
    CHANNELS = 1
    FORMAT = pyaudio.paInt16

    def __init__(
        self,
        wake_words: Optional[List[str]] = None,
        threshold: float = 0.5,
        on_detection: Optional[Callable[[str, float], None]] = None,
        custom_verifier_models: Optional[dict] = None,
        custom_verifier_threshold: float = 0.3
    ):
        """
        Initialize the wake word detector.

        Args:
            wake_words: List of wake words to detect. If None, uses all available models.
                       Available: "alexa", "hey_jarvis", "hey_mycroft", etc.
            threshold: Detection confidence threshold (0.0 to 1.0)
            on_detection: Callback function called when wake word is detected.
                         Receives wake_word name and confidence score.
            custom_verifier_models: Dict mapping model name to verifier .pkl path
                                   Example: {"alexa": "path/to/verifier.pkl"}
            custom_verifier_threshold: Threshold for custom verifier activation (default: 0.3)
        """
        self.wake_words = wake_words
        self.threshold = threshold
        self.on_detection = on_detection

        # Initialize model
        logger.info("Loading openWakeWord models...")
        model_kwargs = {
            "wakeword_models": wake_words if wake_words else []
        }

        if custom_verifier_models:
            model_kwargs["custom_verifier_models"] = custom_verifier_models
            model_kwargs["custom_verifier_threshold"] = custom_verifier_threshold
            logger.info(f"Loading custom verifier models: {list(custom_verifier_models.keys())}")

        self.model = Model(**model_kwargs)
        logger.info(f"Loaded models: {list(self.model.models.keys())}")

        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

        # Threading
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.audio_queue = queue.Queue()

    def list_available_models(self) -> List[str]:
        """List all available wake word models."""
        return list(self.model.models.keys())

    def start(self):
        """Start listening for wake words in a background thread."""
        if self.is_running:
            logger.warning("Wake word detector is already running")
            return

        logger.info("Starting wake word detector...")
        self.is_running = True

        # Open audio stream
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK_SIZE,
            stream_callback=self._audio_callback
        )

        # Start detection thread
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()

        self.stream.start_stream()
        logger.info("Wake word detector started. Listening...")

    def stop(self):
        """Stop listening for wake words."""
        if not self.is_running:
            return

        logger.info("Stopping wake word detector...")
        self.is_running = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None

        logger.info("Wake word detector stopped")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback to capture audio data."""
        if status:
            logger.warning(f"Audio callback status: {status}")

        self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def _detection_loop(self):
        """Main detection loop running in background thread."""
        logger.info("Detection loop started")

        while self.is_running:
            try:
                # Get audio data from queue (with timeout to allow stopping)
                audio_data = self.audio_queue.get(timeout=0.1)

                # Convert bytes to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Run prediction
                predictions = self.model.predict(audio_array)

                # Check for detections
                for wake_word, confidence in predictions.items():
                    if confidence >= self.threshold:
                        logger.info(f"Wake word detected: '{wake_word}' (confidence: {confidence:.2f})")

                        # Call the callback if provided
                        if self.on_detection:
                            try:
                                self.on_detection(wake_word, confidence)
                            except Exception as e:
                                logger.error(f"Error in detection callback: {e}")

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                if not self.is_running:
                    break

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        self.audio.terminate()

    def __del__(self):
        """Cleanup on deletion."""
        self.stop()
        if hasattr(self, 'audio'):
            self.audio.terminate()
