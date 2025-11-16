# Voice Assistant Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         voice-part.py                                │
│                    (Single Unified Script)                           │
└─────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Wake Word       │ │  Speech      │ │  Network     │
    │  Detection       │ │  Recognition │ │  Client      │
    │  (openWakeWord)  │ │  (Vosk)      │ │  (HTTP/TCP)  │
    └──────────────────┘ └──────────────┘ └──────────────┘
```

## State Machine

```
┌─────────────┐
│   STARTUP   │
│ Check State │
└──────┬──────┘
       │
       ├─ Model exists? ─────────┐
       │                         │
       │ No                      │ Yes
       ▼                         ▼
┌─────────────┐          ┌─────────────┐
│  TRAINING   │          │  DETECTION  │
│ Guide User  │──────────▶│ Listen for │◀──┐
│ Train Model │          │ Wake Word   │   │
└─────────────┘          └──────┬──────┘   │
                                │          │
                          Wake word!       │
                                │          │
                                ▼          │
                         ┌─────────────┐   │
                         │ RECOGNITION │   │
                         │ Capture     │   │
                         │ Speech      │   │
                         └──────┬──────┘   │
                                │          │
                          Silence (3s)     │
                                │          │
                                ▼          │
                         ┌─────────────┐   │
                         │   TRANSMIT  │   │
                         │ Send to     │   │
                         │ Inference   │   │
                         └──────┬──────┘   │
                                │          │
                                └──────────┘
```

## Component Breakdown

### 1. State Manager
```python
{
  "wake_word": "hey edge",
  "model_trained": true,
  "inference_endpoint": "http://192.168.1.100:8000/process"
}
```
- Persists configuration
- Survives restarts
- JSON format

### 2. Wake Word Detector
- **Engine**: openWakeWord + custom trained model
- **Latency**: < 500ms
- **CPU**: 5-10% (Raspberry Pi 5)
- **Always on**: Continuous listening

### 3. Speech Recognizer
- **Engine**: Vosk (recommended) or Whisper
- **Model**: vosk-model-small-en-us-0.15 (40MB)
- **Latency**: < 1s (real-time on Pi)
- **Activated**: Only after wake word
- **Timeout**: 3s silence → deactivate

### 4. Network Client
- **Protocol**: HTTP POST
- **Format**: JSON
- **Retry**: 3 attempts with backoff
- **Non-blocking**: Returns to detection if fails

## Data Flow

```
Microphone
    │
    ▼
┌────────────────┐
│ Audio Stream   │ 16kHz, mono, int16
│ (PyAudio)      │
└────────────────┘
    │
    ├─────────────────────────┬────────────────────────┐
    │                         │                        │
    ▼                         ▼                        ▼
┌────────────┐     ┌──────────────────┐    ┌─────────────────┐
│ Wake Word  │     │ Speech Recognizer│    │ (inactive)      │
│ Detection  │     │ (when active)    │    │                 │
└────────────┘     └──────────────────┘    └─────────────────┘
    │                         │
    │ Match!                  │ Transcript
    ▼                         ▼
┌────────────┐     ┌──────────────────┐
│ Activate   │────▶│ Send to Inference│
│ Recognition│     │ Host             │
└────────────┘     └──────────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │ HTTP POST        │
                   │ {                │
                   │   "transcript":  │
                   │   "..."          │
                   │ }                │
                   └──────────────────┘
```

## Network Protocol

### Request Format
```json
POST /process HTTP/1.1
Host: 192.168.1.100:8000
Content-Type: application/json

{
  "transcript": "turn on the lights",
  "timestamp": "2025-11-15T12:34:56.789Z",
  "source": "voice-assistant",
  "wake_word": "hey edge",
  "confidence": 0.95
}
```

### Response Format
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "response": "Lights turned on",
  "processing_time_ms": 123
}
```

## Performance Targets

| Metric | Raspberry Pi 5 | M4 Mac | Target |
|--------|---------------|--------|--------|
| Wake word latency | < 500ms | < 100ms | ✓ |
| Speech recognition | < 1s | < 200ms | ✓ |
| Network round-trip | < 100ms | < 50ms | ✓ |
| Total pipeline | < 2s | < 500ms | ✓ |
| CPU usage (idle) | 5-10% | 2-5% | ✓ |
| RAM usage | ~200MB | ~150MB | ✓ |

## Error Handling

```
┌─────────────┐
│  Operation  │
└──────┬──────┘
       │
       ├─ Success ──────────────▶ Continue
       │
       ├─ Retryable Error ──────▶ Retry (3x)
       │                              │
       │                              ├─ Success ──▶ Continue
       │                              └─ Failed ───▶ Log + Continue
       │
       └─ Fatal Error ──────────────▶ Log + Shutdown
```

### Error Categories

1. **Retryable**: Network timeouts, temporary failures
2. **Recoverable**: Audio device issues (restart component)
3. **Fatal**: Missing models, invalid config (exit with error)

## Deployment Topology

### Single Host Demo
```
┌──────────────────────────────────────┐
│  Raspberry Pi / Mac                  │
│                                      │
│  ┌────────────────┐                 │
│  │ voice-part.py  │                 │
│  └────────┬───────┘                 │
│           │                          │
│           ▼                          │
│  ┌────────────────┐                 │
│  │ localhost:8000 │ (mock server)   │
│  └────────────────┘                 │
└──────────────────────────────────────┘
```

### Cross-Host Production
```
┌──────────────────────────┐         ┌─────────────────────────┐
│  Raspberry Pi (Edge)     │         │  Server (Inference)     │
│                          │         │                         │
│  ┌────────────────┐     │  HTTP   │  ┌───────────────────┐ │
│  │ voice-part.py  │─────┼─────────▶  │ LLM/AI Inference  │ │
│  │                │     │  POST   │  │ API Server        │ │
│  │ • Wake detect  │     │         │  │ (Flask/FastAPI)   │ │
│  │ • Speech rec   │◀────┼─────────│  └───────────────────┘ │
│  └────────────────┘     │ Response│                         │
│                          │         │                         │
│  192.168.1.50            │         │  192.168.1.100:8000     │
└──────────────────────────┘         └─────────────────────────┘
```

## File Layout (Release Package)

```
release/
├── voice-part.py           # Main script (500-800 lines)
├── requirements.txt        # Dependencies
├── README.md              # Quick start
├── ARCHITECTURE.md        # This file
├── models/                # Runtime models
│   └── vosk-model-small-en-us-0.15/
└── .voice-assistant-state.json  # Auto-generated on first run
```

## Technology Stack

| Component | Technology | Size | Speed |
|-----------|-----------|------|-------|
| Wake Word | openWakeWord + PyTorch | ~1MB model | < 500ms |
| Training | PyTorch + augmentation | ~800KB | 3 min |
| Speech Rec | Vosk | 40MB model | Real-time |
| Audio I/O | PyAudio | System dep | N/A |
| Network | requests | ~500KB | < 100ms |
| State | JSON | < 1KB | Instant |

## Resource Requirements

### Minimum (Raspberry Pi 4)
- CPU: 1.5 GHz quad-core
- RAM: 1GB available
- Storage: 500MB free
- Network: 100 Mbps

### Recommended (Raspberry Pi 5)
- CPU: 2.4 GHz quad-core
- RAM: 2GB available
- Storage: 2GB free
- Network: 1 Gbps

### Optimal (Development Mac)
- CPU: Apple Silicon M1+
- RAM: 4GB available
- Storage: 5GB free
- Network: WiFi 6
