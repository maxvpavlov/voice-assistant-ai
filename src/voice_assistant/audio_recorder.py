"""
Audio Recorder Module
Handles recording audio samples for wake word training.
"""

import logging
import numpy as np
import pyaudio
import wave
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioRecorder:
    """
    Records audio samples for training data collection.
    """

    # Audio configuration (matching wake word detector settings)
    SAMPLE_RATE = 16000
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    CHUNK_SIZE = 1024

    def __init__(self, output_dir: str = "training_data"):
        """
        Initialize the audio recorder.

        Args:
            output_dir: Directory to save recorded audio files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.audio = pyaudio.PyAudio()
        logger.info(f"Audio recorder initialized. Output: {self.output_dir}")

    def record_sample(
        self,
        duration: float,
        filename: Optional[str] = None,
        countdown: int = 3
    ) -> Path:
        """
        Record a single audio sample.

        Args:
            duration: Recording duration in seconds
            filename: Optional custom filename (auto-generated if None)
            countdown: Countdown seconds before recording starts

        Returns:
            Path to the saved audio file
        """
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sample_{timestamp}.wav"

        output_path = self.output_dir / filename

        # Countdown
        if countdown > 0:
            for i in range(countdown, 0, -1):
                print(f"  Recording in {i}...", end="\r", flush=True)
                time.sleep(1)
            print(" " * 30, end="\r")  # Clear line

        print(f"🔴 RECORDING... ({duration}s)", flush=True)

        # Open stream
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK_SIZE
        )

        # Record audio
        frames = []
        num_chunks = int(self.SAMPLE_RATE / self.CHUNK_SIZE * duration)

        for _ in range(num_chunks):
            data = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
            frames.append(data)

        # Stop and close stream
        stream.stop_stream()
        stream.close()

        print("✓ Recording complete!")

        # Save to file
        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(b''.join(frames))

        logger.info(f"Saved audio sample: {output_path}")
        return output_path

    def record_batch(
        self,
        wake_word: str,
        num_samples: int,
        duration: float = 2.0,
        sample_type: str = "positive"
    ):
        """
        Record multiple audio samples for training.

        Args:
            wake_word: The wake word being recorded
            num_samples: Number of samples to record
            duration: Duration of each sample in seconds
            sample_type: Type of sample ('positive' or 'negative')
        """
        # Create subdirectory for this wake word and type
        sample_dir = self.output_dir / wake_word / sample_type
        sample_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*70}")
        print(f"Recording {num_samples} {sample_type} samples for '{wake_word}'")
        print(f"Duration: {duration}s per sample")
        print(f"Output: {sample_dir}")
        print(f"{'='*70}\n")

        if sample_type == "positive":
            print(f"📢 Say the wake word clearly: '{wake_word}'")
        else:
            print(f"📢 Say anything EXCEPT the wake word '{wake_word}'")

        print("\nPress Enter when ready to start, or Ctrl+C to cancel...", end="", flush=True)
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            return

        successful_recordings = 0

        for i in range(num_samples):
            print(f"\n[Sample {i+1}/{num_samples}]")

            try:
                filename = f"{sample_type}_{i+1:04d}.wav"
                self.record_sample(
                    duration=duration,
                    filename=filename,
                    countdown=2
                )

                successful_recordings += 1

                # Pause between recordings
                if i < num_samples - 1:
                    print("\nGet ready for next sample...")
                    time.sleep(1.5)

            except KeyboardInterrupt:
                print("\n\n⚠️  Recording interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error recording sample {i+1}: {e}")
                print(f"❌ Failed to record sample {i+1}")

        print(f"\n{'='*70}")
        print(f"✓ Completed: {successful_recordings}/{num_samples} samples recorded")
        print(f"  Location: {sample_dir}")
        print(f"{'='*70}\n")

    def test_microphone(self, duration: float = 3.0):
        """
        Test microphone by recording and displaying audio levels.

        Args:
            duration: Test duration in seconds
        """
        print(f"\n🎤 Testing microphone for {duration} seconds...")
        print("Speak into your microphone...\n")

        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK_SIZE
        )

        num_chunks = int(self.SAMPLE_RATE / self.CHUNK_SIZE * duration)

        for _ in range(num_chunks):
            data = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
            audio_array = np.frombuffer(data, dtype=np.int16)

            # Calculate volume level
            volume = np.abs(audio_array).mean()
            max_volume = 32768  # Max for 16-bit audio

            # Create visual bar
            bar_length = 40
            filled = int((volume / max_volume) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(f"\r  Level: [{bar}] {volume:>5.0f}", end="", flush=True)

        stream.stop_stream()
        stream.close()

        print("\n\n✓ Microphone test complete!\n")

    def list_devices(self):
        """List all available audio input devices."""
        print("\n📱 Available audio input devices:\n")

        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')

        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                print(f"  [{i}] {device_info.get('name')}")
                print(f"      Sample Rate: {int(device_info.get('defaultSampleRate'))} Hz")
                print(f"      Input Channels: {device_info.get('maxInputChannels')}")
                print()

    def cleanup(self):
        """Cleanup audio resources."""
        if hasattr(self, 'audio'):
            self.audio.terminate()

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()
