#! /usr/bin/env python3

import os
import re
import subprocess
import sys
from time import sleep
from typing import Optional, List

import openai

# Configuration
CONFIG = {
    "ollama_base_url": "http://localhost:11434/v1",
    "api_key": "ollama",  # Default for local Ollama
    "model": "deepseek-r1:14b",    # Default model
    "timeout": 10,        # Command timeout in seconds
    "safe_mode": True,    # Require user confirmation
    "shell": os.name == 'posix'  # Use bash for UNIX, cmd.exe for Windows
}

# Initialize OpenAI client
client = openai.OpenAI(base_url=CONFIG["ollama_base_url"], api_key=CONFIG["api_key"])

def execute_command(command: str) -> str:
    """Execute a shell command safely and return output."""
    try:
        result = subprocess.run(
            command if CONFIG["shell"] else ["cmd", "/C", command],
            shell=CONFIG["shell"],
            capture_output=True,
            text=True,
            timeout=CONFIG["timeout"]
        )
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        output = "Command timed out."
    except Exception as e:
        output = f"Error: {str(e)}"
    return output.strip()

def extract_command(llm_response: str) -> Optional[str]:
    """Extract shell command from LLM response using markdown code blocks."""
    match = re.search(r"```(?:shell|bash|sh)\n(.*?)\n```", llm_response, re.DOTALL)
    return match.group(1).strip() if match else None

def get_user_confirmation(command: str) -> bool:
    """Prompt user for command execution confirmation."""
    print(f"\nCommand to execute:\n> {command}")
    return input("Execute? [y/N] ").lower().strip() == 'y'

def chat_loop():
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Generate shell commands wrapped in ```shell blocks. Explain results clearly."}
    ]

    print("Shell Assistant (type 'exit' to quit)")
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() in ('exit', 'quit'):
            break

        messages.append({"role": "user", "content": user_input})

        # Get LLM response
        response = client.chat.completions.create(
            model=CONFIG["model"],
            messages=messages,
            temperature=0.7
        )
        llm_response = response.choices[0].message.content
        print(f"\nAssistant: {llm_response}")

        # Extract and execute command
        command = extract_command(llm_response)
        if command:
            if CONFIG["safe_mode"] and not get_user_confirmation(command):
                continue

            print("Executing...")
            command_output = execute_command(command)
            print(f"\nCommand output:\n{command_output}")

            # Add results to conversation context
            messages.append({
                "role": "assistant",
                "content": f"Command executed. Output:\n{command_output}"
            })

if __name__ == "__main__":
    print("Warning: This tool executes shell commands. Supervise all actions!\n")
    try:
        chat_loop()
    except KeyboardInterrupt:
        print("\nExiting safely.")
        sys.exit(0)



