#!/usr/bin/env python3
"""
Test script for inference agent.

Simulates voice assistant sending transcripts to the agent and displays results.
"""

import requests
import json
from datetime import datetime
import time

AGENT_URL = "http://localhost:8000"

def test_health_check():
    """Test that agent is running."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{AGENT_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent is healthy!")
            print(f"   Service: {data['service']}")
            print(f"   Model: {data['model']}")
            print(f"   Tools: {', '.join(data['tools_available'])}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to agent. Is it running?")
        print("   Start it with: ./inference-agent.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def send_transcript(text):
    """Send a transcript to the agent and display results."""
    print(f"\n{'='*70}")
    print(f"📤 Sending: \"{text}\"")
    print('='*70)

    payload = {
        "transcript": text,
        "timestamp": datetime.now().isoformat(),
        "source": "test-script",
        "wake_word": "test"
    }

    try:
        response = requests.post(
            f"{AGENT_URL}/process",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()

            # Display final answer
            print(f"\n💬 {result.get('final_answer', 'No answer')}\n")

            # Display reasoning
            if result.get('reasoning_steps'):
                print("📋 Reasoning Process:")
                for step in result['reasoning_steps']:
                    step_num = step.get('step', '?')
                    print(f"\n  Step {step_num}:")

                    if step.get('thought'):
                        print(f"    💭 Thought: {step['thought']}")

                    if step.get('action'):
                        print(f"    🔧 Action: {step['action']}")

                    if step.get('observation'):
                        print(f"    👁️  Observation: {step['observation']}")

            # Display metadata
            steps_taken = result.get('steps_taken', '?')
            status = result.get('status', 'unknown')
            print(f"\n✅ Completed in {steps_taken} step(s) [Status: {status}]")
            print('='*70)

            return True
        else:
            print(f"❌ Server returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out (agent may be processing)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run test scenarios."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║              Inference Agent Test Script                          ║
╚════════════════════════════════════════════════════════════════════╝
""")

    # Check health
    if not test_health_check():
        print("\n⚠️  Agent must be running before tests can proceed.")
        print("   Start agent with: ./inference-agent.py")
        return

    print("\n" + "="*70)
    print("🧪 Running Test Scenarios")
    print("="*70)

    # Test scenarios
    test_cases = [
        # Simple commands
        "turn on the lights",
        "what's the current directory",
        "set temperature to 72 degrees",

        # Complex commands
        "turn on the living room lights and set temperature to 70",
        "check the weather",

        # Multi-step
        "list files in the home directory",
    ]

    print("\nℹ️  Will test these commands:")
    for i, cmd in enumerate(test_cases, 1):
        print(f"  {i}. \"{cmd}\"")

    print("\n" + "="*70)
    input("Press ENTER to start tests (or Ctrl+C to cancel)...")
    print()

    # Run tests
    passed = 0
    failed = 0

    for i, command in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}/{len(test_cases)}")

        if send_transcript(command):
            passed += 1
        else:
            failed += 1

        # Brief pause between tests
        if i < len(test_cases):
            time.sleep(2)

    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total:  {passed + failed}")
    print("="*70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
