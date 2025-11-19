"""
Vosk Speech Recognizer

Real-time speech recognition using Vosk with silence detection.
Optimized for Raspberry Pi and low-resource devices.
"""

import json
import queue
import time
import numpy as np
import sounddevice as sd


class VoskRecognizer:
    """
    Vosk-based speech recognizer with streaming and silence detection.
    """

    def __init__(self, model_path="models/vosk-model-small-en-us-0.15", sample_rate=16000):
        """
        Initialize Vosk recognizer.

        Args:
            model_path: Path to Vosk model directory
            sample_rate: Audio sample rate (default: 16000 Hz)
        """
        import vosk

        self.sample_rate = sample_rate
        self.model = vosk.Model(model_path)
        self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate)
        self.audio_queue = queue.Queue()

        # Silence detection parameters
        self.silence_threshold = 500  # RMS threshold for silence
        self.min_audio_level = 100    # Minimum level to consider as speech

    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            print(f"⚠️  Audio status: {status}")

        # Add audio data to queue
        self.audio_queue.put(bytes(indata))

    def is_silence(self, audio_data):
        """
        Check if audio data is silence.

        Args:
            audio_data: Raw audio bytes

        Returns:
            True if silence, False otherwise
        """
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Calculate RMS (Root Mean Square) for volume level
        rms = np.sqrt(np.mean(audio_array**2))

        return rms < self.silence_threshold

    def recognize_stream(self, silence_timeout=3.0, max_duration=30.0, on_sentence_callback=None):
        """
        Recognize speech from microphone with silence detection.

        Args:
            silence_timeout: Stop after this many seconds of silence
            max_duration: Maximum recognition duration in seconds
            on_sentence_callback: Optional callback(sentence_text) called when sentence boundary detected

        Returns:
            List of recognized sentences (or single string if no callback provided)
        """
        transcript_parts = []
        last_speech_time = time.time()
        start_time = time.time()
        recognition_started = False

        # Reset recognizer
        self.recognizer = self.recognizer.__class__(self.model, self.sample_rate)

        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        print("🎤 Listening...")

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            ):
                while True:
                    # Check max duration
                    if time.time() - start_time > max_duration:
                        print("\n⏱️  Max duration reached")
                        break

                    # Get audio data
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    # Check if silence
                    is_silent = self.is_silence(data)

                    # Feed to recognizer
                    if self.recognizer.AcceptWaveform(data):
                        # Got a result - sentence boundary detected!
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").strip()

                        if text:
                            transcript_parts.append(text)
                            last_speech_time = time.time()
                            recognition_started = True
                            print(f"   > {text}")

                            # Call callback immediately when sentence detected
                            if on_sentence_callback:
                                try:
                                    on_sentence_callback(text)
                                except Exception as e:
                                    print(f"\n⚠️  Callback error: {e}")

                    else:
                        # Partial result
                        partial = json.loads(self.recognizer.PartialResult())
                        partial_text = partial.get("partial", "")

                        if partial_text:
                            # Got some speech
                            last_speech_time = time.time()
                            recognition_started = True

                            # Show progress
                            print(f"\r   ... {partial_text}", end="", flush=True)

                    # Check for silence timeout
                    if recognition_started:
                        silence_duration = time.time() - last_speech_time

                        if silence_duration > silence_timeout:
                            print(f"\n⏸️  Silence detected ({silence_timeout}s)")
                            break

        except KeyboardInterrupt:
            print("\n⚠️  Recognition interrupted")

        # Get final result
        final_result = json.loads(self.recognizer.FinalResult())
        final_text = final_result.get("text", "").strip()

        if final_text and final_text not in transcript_parts:
            transcript_parts.append(final_text)
            # Send final result via callback too
            if on_sentence_callback and final_text:
                try:
                    on_sentence_callback(final_text)
                except Exception as e:
                    print(f"\n⚠️  Callback error: {e}")

        # Return list if using callbacks, combined string otherwise
        if on_sentence_callback:
            return transcript_parts
        else:
            return " ".join(transcript_parts).strip()

    def test_microphone(self, duration=5.0):
        """
        Test microphone input with volume visualization.

        Args:
            duration: Test duration in seconds
        """
        print(f"\n🎤 Testing microphone for {duration} seconds...")
        print("Speak into your microphone...\n")

        def callback(indata, frames, time_info, status):
            if status:
                print(f"⚠️  {status}")

            # Calculate volume
            audio_array = np.frombuffer(indata, dtype=np.int16)
            volume = np.abs(audio_array).mean()
            max_volume = 32768

            # Visual bar
            bar_length = 40
            filled = int((volume / max_volume) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(f"\r  Level: [{bar}] {volume:>5.0f}", end="", flush=True)

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=1024,
                dtype='int16',
                channels=1,
                callback=callback
            ):
                time.sleep(duration)

        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted")

        print("\n\n✓ Microphone test complete!\n")
