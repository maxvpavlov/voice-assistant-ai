#!/usr/bin/env python3
"""
Voice Inference Agent with ReAct Reasoning

HTTP server that receives voice transcripts from voice-part.py and processes them
using ReAct (Reasoning + Acting) pattern with Ollama LLM.

The agent reasons about the request, takes actions using available tools, and returns
results back to the voice assistant.
"""

import ollama
import subprocess
import json
import re
from datetime import datetime
from flask import Flask, request, jsonify
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule

app = Flask(__name__)
console = Console()

# Available tools for the agent
def run_shell_command(command: str) -> str:
    """
    Execute a shell command and return its output.

    Args:
        command: The shell command to execute.

    Returns:
        str: The output of the command, or an error message.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Command execution timed out"
    except Exception as e:
        return f"Exception: {str(e)}"

def control_light(location: str, state: str) -> str:
    """
    Control smart lights in different locations.

    Args:
        location: Location of the light (living_room, bedroom, kitchen, etc.)
        state: Desired state (on, off, dim, bright)

    Returns:
        str: Confirmation message
    """
    # Placeholder - integrate with actual smart home API
    console.print(f"[cyan]💡 Light Control: {location} -> {state}[/cyan]")
    return f"Light in {location} turned {state}"

def control_temperature(temperature: int, unit: str = "F") -> str:
    """
    Set thermostat temperature.

    Args:
        temperature: Target temperature
        unit: Temperature unit (F or C)

    Returns:
        str: Confirmation message
    """
    # Placeholder - integrate with actual thermostat API
    console.print(f"[cyan]🌡️  Temperature Control: {temperature}°{unit}[/cyan]")
    return f"Temperature set to {temperature}°{unit}"

def get_weather(location: str = "current") -> str:
    """
    Get current weather information.

    Args:
        location: Location to check weather for

    Returns:
        str: Weather information
    """
    # Placeholder - integrate with weather API
    return f"Weather for {location}: Sunny, 72°F"

def set_timer(duration: str, label: str = "") -> str:
    """
    Set a timer.

    Args:
        duration: Timer duration (e.g., "5 minutes", "1 hour")
        label: Optional label for the timer

    Returns:
        str: Confirmation message
    """
    # Placeholder - integrate with timer/notification system
    label_text = f" for {label}" if label else ""
    console.print(f"[cyan]⏲️  Timer: {duration}{label_text}[/cyan]")
    return f"Timer set for {duration}{label_text}"

# Map tool names to functions
TOOLS = {
    "run_shell_command": run_shell_command,
    "control_light": control_light,
    "control_temperature": control_temperature,
    "get_weather": get_weather,
    "set_timer": set_timer,
}

# System prompt for ReAct pattern
SYSTEM_PROMPT = '''
You are an AI assistant that controls a smart home system via voice commands.
You use Reasoning and Acting (ReAct) to process requests.

Your response MUST be in the following format:
|Thought:| [Your reasoning about what to do]
|Action:| [tool_name: argument]
OR
|Final Answer:| [your response to the user]

Available tools:
- run_shell_command: Execute shell commands (use carefully)
- control_light: Control smart lights (args: location, state)
- control_temperature: Set thermostat (args: temperature, unit)
- get_weather: Get weather information (args: location)
- set_timer: Set a timer (args: duration, label)

Rules:
- ONE |Thought:| per response (put all reasoning there)
- EITHER |Action:| OR |Final Answer:|, never both
- If no action needed, just provide |Final Answer:|
- Keep responses concise and natural
- Confirm actions before finishing
'''

def get_llm_response(history, stream=True):
    """Query Ollama with conversation history."""
    return ollama.chat(
        model='llama3.1:8b',  # Change to your preferred model
        messages=history,
        stream=stream
    )

def parse_output(output: str):
    """Parse LLM output for Thought, Action, or Final Answer."""
    thought_match = re.search(r"\|Thought:\|(.*?)(?:\|Action:|\|Final Answer:|$)", output, re.DOTALL)
    action_match = re.search(r"\|Action:\|(.*?)(?:\|Thought:|\|Final Answer:|$)", output, re.DOTALL)
    final_answer_match = re.search(r"\|Final Answer:\|(.*?)(?:\|Thought:|\|Action:|$)", output, re.DOTALL)

    thought = thought_match.group(1).strip() if thought_match else ""
    action_str = action_match.group(1).strip() if action_match else ""
    final_answer = final_answer_match.group(1).strip() if final_answer_match else ""

    action = None
    if action_str and ':' in action_str:
        tool, arg = action_str.split(':', 1)
        action = (tool.strip(), arg.strip())

    return thought, action, final_answer

def run_agent(query: str, max_steps: int = 5):
    """
    Main agent loop implementing ReAct pattern.

    Args:
        query: User's voice command/question
        max_steps: Maximum reasoning steps

    Returns:
        dict: Response with reasoning steps and final answer
    """
    console.print(Rule(f"[bold blue]New Request: {query}"))

    history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]

    reasoning_steps = []

    for step in range(1, max_steps + 1):
        console.print(f"\n[bold cyan]Step {step}[/bold cyan]")

        # Get LLM response (streaming)
        output = ""
        for chunk in get_llm_response(history, stream=True):
            output += chunk['message']['content']

        console.print(Panel(output, title="LLM Output", border_style="yellow"))

        # Parse output
        thought, action, final_answer = parse_output(output)

        step_data = {
            "step": step,
            "thought": thought,
            "action": None,
            "observation": None,
            "final_answer": None
        }

        if thought:
            console.print(f"[green]💭 Thought:[/green] {thought}")
            step_data["thought"] = thought

        if final_answer:
            console.print(Panel(final_answer, title="Final Answer", border_style="sky_blue1"))
            step_data["final_answer"] = final_answer
            reasoning_steps.append(step_data)

            return {
                "status": "success",
                "query": query,
                "final_answer": final_answer,
                "reasoning_steps": reasoning_steps,
                "steps_taken": step
            }

        if action:
            tool_name, arg = action
            step_data["action"] = f"{tool_name}: {arg}"

            if tool_name in TOOLS:
                console.print(f"[orange1]🔧 Action:[/orange1] {tool_name}({arg})")

                # Execute tool
                try:
                    observation = TOOLS[tool_name](arg)
                    console.print(f"[blue]👁️  Observation:[/blue] {observation}")
                    step_data["observation"] = observation

                    # Add to history
                    history.append({"role": "assistant", "content": output})
                    history.append({"role": "user", "content": f"Observation: {observation}"})

                except Exception as e:
                    error_msg = f"Error executing {tool_name}: {str(e)}"
                    console.print(f"[red]❌ Error:[/red] {error_msg}")
                    step_data["observation"] = error_msg
                    history.append({"role": "assistant", "content": output})
                    history.append({"role": "user", "content": f"Error: {error_msg}"})
            else:
                error_msg = f"Unknown tool: {tool_name}"
                console.print(f"[red]❌ Error:[/red] {error_msg}")
                step_data["observation"] = error_msg
                history.append({"role": "assistant", "content": output})
                history.append({"role": "user", "content": error_msg})
        else:
            # No action or final answer - continue
            history.append({"role": "assistant", "content": output})

        reasoning_steps.append(step_data)

    # Max steps reached
    return {
        "status": "incomplete",
        "query": query,
        "final_answer": "I couldn't complete the request within the step limit. Please try rephrasing.",
        "reasoning_steps": reasoning_steps,
        "steps_taken": max_steps
    }

@app.route('/process', methods=['POST'])
def process_transcript():
    """
    HTTP endpoint to receive voice transcripts and process them.

    Expected JSON payload:
    {
        "transcript": "turn on the living room lights",
        "timestamp": "2025-11-17T...",
        "source": "voice-assistant",
        "wake_word": "hey edge"
    }

    Returns:
    {
        "status": "success",
        "query": "...",
        "final_answer": "...",
        "reasoning_steps": [...],
        "steps_taken": 3
    }
    """
    try:
        data = request.json

        if not data or 'transcript' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'transcript' in request"
            }), 400

        transcript = data['transcript']
        timestamp = data.get('timestamp', datetime.now().isoformat())

        console.print(f"\n[bold magenta]📥 Received transcript:[/bold magenta] {transcript}")
        console.print(f"[dim]Timestamp: {timestamp}[/dim]")

        # Process with ReAct agent
        result = run_agent(transcript)

        console.print(Rule("[bold green]Request Complete"))

        return jsonify(result)

    except Exception as e:
        console.print(f"[bold red]Error processing request:[/bold red] {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "voice-inference-agent",
        "model": "llama3.1:8b",
        "tools_available": list(TOOLS.keys())
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with service info."""
    return jsonify({
        "service": "Voice Inference Agent",
        "version": "1.0.0",
        "description": "ReAct-based inference agent for voice commands",
        "endpoints": {
            "/process": "POST - Process voice transcript",
            "/health": "GET - Health check"
        },
        "tools": list(TOOLS.keys())
    })

if __name__ == '__main__':
    console.print(Panel.fit(
        "[bold cyan]Voice Inference Agent[/bold cyan]\n"
        "ReAct-based reasoning for voice commands\n\n"
        f"Tools available: {', '.join(TOOLS.keys())}\n"
        "Model: llama3.1:8b",
        border_style="cyan"
    ))

    console.print("\n[green]🚀 Starting server on http://localhost:8000[/green]\n")

    # Run Flask server
    app.run(host='0.0.0.0', port=8000, debug=False)
