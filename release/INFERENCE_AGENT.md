# Voice Inference Agent with ReAct Reasoning

HTTP server that receives voice transcripts from `voice-part.py` and processes them using **ReAct** (Reasoning + Acting) pattern with Ollama LLM.

## Overview

The inference agent acts as the "brain" of the voice assistant, receiving voice commands and:
1. **Reasoning** about what the user wants
2. **Taking actions** using available tools (smart home control, shell commands, etc.)
3. **Responding** with natural language confirmation

### Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Voice Assistant│  HTTP   │  Inference Agent │  Calls  │      Tools      │
│  (voice-part.py)│────────▶│ (inference-agent)│────────▶│  (Smart Home)   │
│                 │  POST   │                  │         │  (Shell, etc.)  │
│  Wake Word      │         │  ReAct Pattern   │         │                 │
│  Speech-to-Text │◀────────│  Ollama LLM      │◀────────│  Observations   │
│                 │  JSON   │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## Features

### ReAct Pattern

The agent uses **ReAct** (Reasoning and Acting) to iteratively solve problems:

1. **Thought**: Reason about what to do next
2. **Action**: Call a tool if needed
3. **Observation**: See the result of the action
4. **Repeat** until the answer is found
5. **Final Answer**: Respond to the user

### Available Tools

#### Smart Home Control
- `control_light(location, state)` - Control lights
- `control_temperature(temperature, unit)` - Set thermostat
- `get_weather(location)` - Get weather information
- `set_timer(duration, label)` - Set timers

#### System Control
- `run_shell_command(command)` - Execute shell commands (use carefully)

### Example Interaction

**User says**: "Turn on the living room lights and set temperature to 72 degrees"

**Agent reasoning**:
```
Step 1:
  💭 Thought: User wants to control two things: lights and temperature
  🔧 Action: control_light: living_room, on
  👁️  Observation: Light in living_room turned on

Step 2:
  💭 Thought: Now I need to set the temperature
  🔧 Action: control_temperature: 72, F
  👁️  Observation: Temperature set to 72°F

Step 3:
  💬 Final Answer: I've turned on the living room lights and set the temperature to 72°F
```

## Installation

### Prerequisites

1. **Ollama** with a compatible model:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh

   # Pull a model
   ollama pull llama3.1:8b
   ```

2. **Python dependencies**:
   ```bash
   cd release/
   source venv/bin/activate
   pip install flask rich ollama
   ```

### Quick Start

1. **Start the inference agent**:
   ```bash
   ./inference-agent.py
   ```

   Should see:
   ```
   ┌────────────────────────────────────────┐
   │   Voice Inference Agent                │
   │   ReAct-based reasoning for voice      │
   │   commands                             │
   │                                        │
   │   Tools available: control_light,      │
   │   control_temperature, get_weather,    │
   │   set_timer, run_shell_command         │
   │   Model: llama3.1:8b                   │
   └────────────────────────────────────────┘

   🚀 Starting server on http://localhost:8000
   ```

2. **Start voice assistant** (in another terminal):
   ```bash
   cd release/
   source venv/bin/activate
   ./voice-part.py
   ```

3. **Speak commands**:
   - Say wake word: "hey edge"
   - Give command: "turn on the lights"
   - Watch the agent reason and respond!

## Configuration

### Change Model

Edit `inference-agent.py` line 159:
```python
def get_llm_response(history, stream=True):
    return ollama.chat(
        model='llama3.1:8b',  # ← Change this
        messages=history,
        stream=stream
    )
```

Available models:
- `llama3.1:8b` - Good balance (4.7GB)
- `llama3.1:70b` - Best quality (40GB)
- `gemma2:9b` - Fast and efficient (5.5GB)
- `mistral:7b` - Fast alternative (4.1GB)

### Change Port

Edit `inference-agent.py` line 404:
```python
app.run(host='0.0.0.0', port=8000, debug=False)  # ← Change port
```

Then update `voice-part.py` inference endpoint:
```bash
./voice-part.py --inference-endpoint http://localhost:YOUR_PORT/process
```

### Add Custom Tools

Add your own tools to `inference-agent.py`:

```python
def my_custom_tool(arg1: str, arg2: int) -> str:
    """
    Description of what your tool does.

    Args:
        arg1: Description
        arg2: Description

    Returns:
        str: Result description
    """
    # Your implementation
    return "Tool result"

# Register it
TOOLS = {
    # ... existing tools ...
    "my_custom_tool": my_custom_tool,
}
```

Update the system prompt to include your tool:
```python
SYSTEM_PROMPT = '''
...
Available tools:
- my_custom_tool: Description (args: arg1, arg2)
...
'''
```

## API Reference

### POST /process

Process a voice transcript with ReAct reasoning.

**Request**:
```json
{
  "transcript": "turn on the living room lights",
  "timestamp": "2025-11-17T10:30:00.123Z",
  "source": "voice-assistant",
  "wake_word": "hey edge"
}
```

**Response (Success)**:
```json
{
  "status": "success",
  "query": "turn on the living room lights",
  "final_answer": "I've turned on the living room lights",
  "reasoning_steps": [
    {
      "step": 1,
      "thought": "User wants to control lights",
      "action": "control_light: living_room, on",
      "observation": "Light in living_room turned on",
      "final_answer": null
    },
    {
      "step": 2,
      "thought": "Task completed",
      "action": null,
      "observation": null,
      "final_answer": "I've turned on the living room lights"
    }
  ],
  "steps_taken": 2
}
```

**Response (Error)**:
```json
{
  "status": "error",
  "message": "Error description"
}
```

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "voice-inference-agent",
  "model": "llama3.1:8b",
  "tools_available": ["control_light", "control_temperature", ...]
}
```

### GET /

Service information.

**Response**:
```json
{
  "service": "Voice Inference Agent",
  "version": "1.0.0",
  "description": "ReAct-based inference agent for voice commands",
  "endpoints": {
    "/process": "POST - Process voice transcript",
    "/health": "GET - Health check"
  },
  "tools": ["control_light", "control_temperature", ...]
}
```

## Integration with Smart Home

### Home Assistant

```python
def control_light(location: str, state: str) -> str:
    """Control lights via Home Assistant API."""
    import requests

    ha_url = "http://homeassistant.local:8123"
    token = "YOUR_TOKEN_HERE"

    entity_id = f"light.{location}"
    service = "turn_on" if state == "on" else "turn_off"

    response = requests.post(
        f"{ha_url}/api/services/light/{service}",
        headers={"Authorization": f"Bearer {token}"},
        json={"entity_id": entity_id}
    )

    if response.status_code == 200:
        return f"Light in {location} turned {state}"
    else:
        return f"Error controlling light: {response.text}"
```

### Philips Hue

```python
def control_light(location: str, state: str) -> str:
    """Control Philips Hue lights."""
    from phue import Bridge

    bridge = Bridge('192.168.1.100')  # Your bridge IP
    lights = bridge.get_light_objects('name')

    if location in lights:
        light = lights[location]
        light.on = (state == "on")
        return f"Light {location} turned {state}"
    else:
        return f"Light {location} not found"
```

### Nest Thermostat

```python
def control_temperature(temperature: int, unit: str = "F") -> str:
    """Control Nest thermostat."""
    import requests

    # Convert to Celsius if needed
    temp_c = temperature if unit == "C" else (temperature - 32) * 5/9

    nest_url = "https://developer-api.nest.com"
    token = "YOUR_TOKEN_HERE"
    device_id = "YOUR_DEVICE_ID"

    response = requests.put(
        f"{nest_url}/devices/thermostats/{device_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_temperature_c": temp_c}
    )

    if response.status_code == 200:
        return f"Temperature set to {temperature}°{unit}"
    else:
        return f"Error setting temperature: {response.text}"
```

## Troubleshooting

### Agent Not Starting

**Error**: `ModuleNotFoundError: No module named 'ollama'`

**Fix**:
```bash
pip install ollama flask rich
```

### Ollama Connection Failed

**Error**: Connection refused when calling Ollama

**Fix**:
1. Check Ollama is running: `ollama list`
2. If not: `ollama serve`
3. Test manually: `ollama run llama3.1:8b "hello"`

### Model Not Found

**Error**: `Error: model 'llama3.1:8b' not found`

**Fix**:
```bash
ollama pull llama3.1:8b
```

Available models: https://ollama.com/library

### Slow Responses

**Issue**: Agent takes too long to respond

**Solutions**:
1. Use smaller model: `gemma2:9b` or `mistral:7b`
2. Reduce max_steps: Edit line 269 in `inference-agent.py`
   ```python
   result = run_agent(transcript, max_steps=3)  # Default: 5
   ```
3. Use GPU acceleration (if available)

### Voice Assistant Can't Reach Agent

**Error**: Connection refused to http://localhost:8000

**Fix**:
1. Ensure agent is running: `./inference-agent.py`
2. Check port: `lsof -i :8000`
3. Try different port if 8000 is occupied
4. Check firewall settings

## Performance

### Response Time

Typical response times with `llama3.1:8b` on M1 Mac:

- **Simple command** (1 action): ~2-3 seconds
- **Complex command** (2-3 actions): ~5-8 seconds
- **Multi-step reasoning**: ~10-15 seconds

### Memory Usage

- **Agent process**: ~200MB
- **Ollama (llama3.1:8b)**: ~5GB
- **Total**: ~5.2GB

### Optimization Tips

1. **Keep Ollama warm**: Run a test query on startup
2. **Use streaming**: Already implemented for faster first-token
3. **Cache common responses**: Add response caching layer
4. **Batch actions**: Combine related actions in single step

## Security Considerations

### Shell Command Safety

The `run_shell_command` tool can execute arbitrary commands. Consider:

1. **Whitelist commands**: Only allow specific commands
2. **Add confirmation**: Require user confirmation for dangerous commands
3. **Sandbox execution**: Use Docker or restricted user
4. **Disable entirely**: Remove from TOOLS if not needed

Example whitelist:
```python
SAFE_COMMANDS = ['ls', 'pwd', 'date', 'uptime', 'whoami']

def run_shell_command(command: str) -> str:
    base_cmd = command.split()[0]
    if base_cmd not in SAFE_COMMANDS:
        return f"Command '{base_cmd}' not allowed"

    # Execute if safe
    ...
```

### Network Security

1. **Use HTTPS**: In production, use HTTPS with SSL certificates
2. **Add authentication**: Require API keys or tokens
3. **Rate limiting**: Prevent abuse
4. **Input validation**: Sanitize all inputs

## Future Enhancements

### Planned Features

1. **Multi-user support**: Track different users and preferences
2. **Context persistence**: Remember previous conversations
3. **Custom wake word responses**: Personalized greetings
4. **Voice output**: TTS responses (speak back to user)
5. **Skill plugins**: Modular tool loading
6. **Web dashboard**: Monitor agent activity
7. **Analytics**: Usage statistics and popular commands

### Contributing

To add new tools or improve reasoning:

1. Add tool function to `inference-agent.py`
2. Register in `TOOLS` dict
3. Update `SYSTEM_PROMPT` with tool description
4. Test with various commands
5. Document usage in this file

## Examples

### Example 1: Multi-step Command

**User**: "Check the weather and if it's cold, turn on the heater"

**Agent reasoning**:
```
Step 1:
  💭 Thought: First I need to check the weather
  🔧 Action: get_weather: current
  👁️  Observation: Weather for current: Cloudy, 45°F

Step 2:
  💭 Thought: 45°F is cold, user wants heater on
  🔧 Action: control_temperature: 72, F
  👁️  Observation: Temperature set to 72°F

Step 3:
  💬 Final Answer: The weather is 45°F and cloudy, so I've turned on
                    the heater and set it to 72°F for you.
```

### Example 2: Information Query

**User**: "What's my current directory?"

**Agent reasoning**:
```
Step 1:
  💭 Thought: User wants to know current directory, I'll use pwd command
  🔧 Action: run_shell_command: pwd
  👁️  Observation: /Users/pavlovmaksym/Documents/GitHub/voice-assistant

Step 2:
  💬 Final Answer: Your current directory is
                    /Users/pavlovmaksym/Documents/GitHub/voice-assistant
```

### Example 3: Complex Smart Home

**User**: "Set up movie mode"

**Agent reasoning**:
```
Step 1:
  💭 Thought: Movie mode typically means: dim lights, close blinds,
              comfortable temperature
  🔧 Action: control_light: living_room, dim
  👁️  Observation: Light in living_room dimmed

Step 2:
  💭 Thought: Set comfortable temperature
  🔧 Action: control_temperature: 68, F
  👁️  Observation: Temperature set to 68°F

Step 3:
  💬 Final Answer: Movie mode activated! I've dimmed the living room
                    lights and set the temperature to 68°F. Enjoy your movie!
```

## References

- **Ollama**: https://ollama.com
- **ReAct Paper**: https://arxiv.org/abs/2210.03629
- **Flask**: https://flask.palletsprojects.com
- **Rich**: https://rich.readthedocs.io
