#!/usr/bin/env python3
"""Quick test to check model predictions on training samples."""

import numpy as np
import onnxruntime as ort
import librosa
import sys

def extract_features(audio_path):
    """Extract mel spectrogram features."""
    audio, sr = librosa.load(audio_path, sr=16000)
    mel = librosa.feature.melspectrogram(
        y=audio, 
        sr=sr,
        n_mels=32,
        n_fft=512,
        hop_length=160
    )
    mel_db = librosa.power_to_db(mel, ref=np.max)
    
    # Normalize
    mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)
    
    return mel_db

def test_model(model_path, audio_path):
    """Test model on audio file."""
    # Load model
    session = ort.InferenceSession(model_path)
    
    # Extract features
    features = extract_features(audio_path)
    
    # Reshape for model input (batch, channels, height, width)
    features = features[:, :96]  # Limit to 96 time steps
    features = features.reshape(1, 1, features.shape[0], features.shape[1])
    features = features.astype(np.float32)
    
    # Run inference
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: features})
    
    score = outputs[0][0][0]
    return score

if __name__ == "__main__":
    model_path = "models/hey_bender_v0.1.onnx"
    
    print(f"Testing model: {model_path}\n")
    
    for i in range(1, 6):
        audio_path = f"training_data/hey_bender/positive/positive_{i:04d}.wav"
        try:
            score = test_model(model_path, audio_path)
            print(f"Sample {i}: score = {score:.4f} {'✓ DETECT' if score > 0.5 else '✗ miss'}")
        except Exception as e:
            print(f"Sample {i}: ERROR - {e}")
