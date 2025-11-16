"""
Voice Assistant - Wake Word Detection and Speech Recognition
A modular voice assistant library for Raspberry Pi 5 and macOS.
"""

__version__ = "0.1.0"
__author__ = "Voice Assistant Team"

from .wake_word_detector import WakeWordDetector
from .audio_recorder import AudioRecorder
from .model_trainer import ModelTrainer

__all__ = ["WakeWordDetector", "AudioRecorder", "ModelTrainer"]
