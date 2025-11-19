# Test Agent Guide

Quick reference for testing the inference agent with `test-agent.py`.

## Prerequisites

1. **Inference agent must be running**:
   ```bash
   ./inference-agent.py
   ```

2. **Dependencies installed**:
   ```bash
   pip install requests flask rich ollama
   ```

3. **Ollama model available**:
   ```bash
   ollama pull gemma3:12b
   ```

## Usage Modes

### Mode 1: Single Command (Command Line)

**Best for**: Quick one-off tests, scripting, automation

```bash
./test-agent.py "your command here"
```

**Examples**:
```bash
# Simple command
./test-agent.py "turn on the lights"

# Complex command
./test-agent.py "turn on living room lights and set temperature to 72"

# Question
./test-agent.py "what is the weather like today"

# Multi-step
./test-agent.py "dim bedroom lights and set a 10 minute timer for cooking"
```

**Output**:
```
🔍 Testing health check...
✅ Agent is healthy!

📝 Single command mode: "turn on the lights"

======================================================================
📤 Sending: "turn on the lights"
======================================================================

💬 Okay, I've turned on all the lights.

📋 Reasoning Process:

  Step 1:
    💭 Thought: User wants lights on, assuming all locations
    🔧 Action: control_light: location=all, state=on
    👁️  Observation: Light in all turned on

✅ Completed in 2 step(s) [Status: success]
======================================================================
```

### Mode 2: Interactive (Free Text Input)

**Best for**: Exploring agent capabilities, demos, multiple tests

```bash
./test-agent.py
# Select: 1
```

**Session example**:
```
╔════════════════════════════════════════════════════════════════════╗
║           Interactive Mode - Send Custom Commands                 ║
╚════════════════════════════════════════════════════════════════════╝

Enter your commands and the agent will process them with ReAct reasoning.
Type 'exit', 'quit', or press Ctrl+C to quit.

🎤 You: turn on the lights
[Agent processes with full reasoning output...]

🎤 You: what's the temperature
[Agent processes...]

🎤 You: set a timer for 5 minutes
[Agent processes...]

🎤 You: exit
👋 Goodbye!
```

**Features**:
- Continuous conversation
- Full reasoning displayed for each command
- Natural language interaction
- Easy to explore different commands

### Mode 3: Batch Testing (Predefined Tests)

**Best for**: Regression testing, verification, CI/CD

```bash
./test-agent.py
# Select: 2
```

**Runs these tests**:
1. "turn on the lights"
2. "what's the current directory"
3. "set temperature to 72 degrees"
4. "turn on the living room lights and set temperature to 70"
5. "check the weather"
6. "list files in the home directory"

**Output**:
```
🧪 Test 1/6
[Full reasoning for command 1...]

🧪 Test 2/6
[Full reasoning for command 2...]

...

📊 Test Summary
======================================================================
✅ Passed: 6
❌ Failed: 0
📈 Total:  6
======================================================================
```

## Example Commands to Try

### Smart Home Control

```bash
# Lights
./test-agent.py "turn on the living room lights"
./test-agent.py "dim the bedroom lights"
./test-agent.py "turn off all lights"

# Temperature
./test-agent.py "set temperature to 72 degrees"
./test-agent.py "set thermostat to 68 fahrenheit"
./test-agent.py "make it warmer"

# Combined
./test-agent.py "turn on lights and set temperature to 70"
```

### Timers & Reminders

```bash
./test-agent.py "set a timer for 5 minutes"
./test-agent.py "set a 10 minute timer for cooking"
./test-agent.py "remind me in 15 minutes"
```

### Information Queries

```bash
./test-agent.py "what's the weather"
./test-agent.py "what's the weather like today"
./test-agent.py "check the weather forecast"
```

### System Commands

```bash
./test-agent.py "what's my current directory"
./test-agent.py "list files in the home directory"
./test-agent.py "what's the date"
```

### Complex Multi-Step

```bash
# Multiple actions
./test-agent.py "turn on bedroom lights, set temperature to 70, and set a 10 minute timer"

# Conditional logic
./test-agent.py "check the weather and if it's cold turn on the heater"

# Sequential tasks
./test-agent.py "dim the lights and then set a 5 minute timer"
```

## Understanding the Output

### Reasoning Process Display

Each response shows:

1. **Final Answer** 💬
   - The agent's natural language response
   - What the user sees/hears

2. **Reasoning Steps** 📋
   - How the agent thought through the problem
   - What actions it took
   - What it observed

**Example breakdown**:
```
Step 1:
  💭 Thought: "User wants lights on and temperature set"
      ↓ Agent reasoning
  🔧 Action: control_light: living_room, on
      ↓ Tool call
  👁️  Observation: "Light in living_room turned on"
      ↓ Tool result

Step 2:
  💭 Thought: "Now setting temperature"
  🔧 Action: control_temperature: 72, F
  👁️  Observation: "Temperature set to 72°F"

Step 3:
  💭 Thought: "Both tasks complete, confirming"
  💬 Final Answer: "I've turned on the living room lights and
                    set the temperature to 72°F"
```

### Status Indicators

- ✅ **Completed** - Successfully processed
- ⚠️  **Warning** - Partial success or recoverable issue
- ❌ **Failed** - Error occurred

## Troubleshooting

### "Cannot connect to agent"

**Problem**: Agent not running or wrong port

**Solution**:
```bash
# Terminal 1: Start agent
./inference-agent.py

# Terminal 2: Test
./test-agent.py "test command"
```

### "Agent returned 500"

**Problem**: Agent encountered error processing request

**Check**:
1. Agent terminal for error messages
2. Ollama is running: `ollama list`
3. Model loaded: `ollama pull gemma3:12b`

### "Request timed out"

**Problem**: Agent taking too long (LLM processing)

**Solutions**:
1. Use faster model: Edit `inference-agent.py` → change to `mistral:7b`
2. Increase timeout in test-agent.py (currently 30s)
3. Check system resources (CPU/RAM)

### Slow responses

**Performance tips**:
1. **Use smaller model**: `mistral:7b` instead of `gemma3:12b`
2. **Warm up Ollama**: Run test query first
   ```bash
   ollama run gemma3:12b "ready" > /dev/null
   ```
3. **Close other apps**: Free up RAM for LLM

## Advanced Usage

### Scripting

```bash
#!/bin/bash
# Test suite script

commands=(
    "turn on lights"
    "set temperature to 70"
    "check weather"
)

for cmd in "${commands[@]}"; do
    echo "Testing: $cmd"
    ./test-agent.py "$cmd" | grep "Final Answer"
    echo "---"
done
```

### CI/CD Integration

```yaml
# Example GitHub Actions
test-agent:
  runs-on: ubuntu-latest
  steps:
    - name: Start Ollama
      run: ollama serve &

    - name: Pull model
      run: ollama pull gemma3:12b

    - name: Start agent
      run: ./inference-agent.py &

    - name: Run tests
      run: ./test-agent.py  # Select mode 2
```

### Logging Output

```bash
# Save reasoning to file
./test-agent.py "turn on lights" > agent-test.log 2>&1

# JSON output (modify test-agent.py to add --json flag)
./test-agent.py --json "turn on lights" > result.json
```

## Tips & Tricks

### 1. Natural Language Works

The agent understands various phrasings:
```bash
# All equivalent
./test-agent.py "turn on the lights"
./test-agent.py "lights on"
./test-agent.py "turn the lights on please"
./test-agent.py "can you turn on the lights"
```

### 2. Context-Free Commands

Each command is independent (no conversation history):
```bash
# Won't work - agent doesn't remember previous commands
./test-agent.py "turn on lights"
./test-agent.py "and set temperature to 70"  # "and" has no context

# Do this instead
./test-agent.py "turn on lights and set temperature to 70"
```

### 3. Explicit is Better

More specific commands get better results:
```bash
# Vague
./test-agent.py "lights"  # Might not understand

# Better
./test-agent.py "turn on the lights"  # Clear action

# Even better
./test-agent.py "turn on the living room lights"  # Specific location
```

### 4. Watch the Agent Terminal

See the full LLM output and tool execution:
```bash
# Terminal 1: Agent shows detailed reasoning
./inference-agent.py

# Terminal 2: Send commands
./test-agent.py "your command"
```

## Quick Reference

| Mode | Command | Use Case |
|------|---------|----------|
| Single | `./test-agent.py "cmd"` | Quick tests |
| Interactive | `./test-agent.py` → 1 | Exploration |
| Batch | `./test-agent.py` → 2 | Regression |

| Output | Meaning |
|--------|---------|
| 💭 | Agent's thought |
| 🔧 | Tool being called |
| 👁️ | Tool result |
| 💬 | Final answer |
| ✅ | Success |
| ❌ | Error |

## Next Steps

1. **Try it out**: Start with simple commands
2. **Explore tools**: See what the agent can do
3. **Test edge cases**: Try unusual commands
4. **Customize**: Add your own test scenarios
5. **Integrate**: Use in your workflow

The agent learns from the tools available - check `inference-agent.py` to see all available tools and add your own!
