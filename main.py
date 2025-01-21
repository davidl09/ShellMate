#! /usr/bin/env python3

import os
import re
import subprocess
import sys
from select import select
from typing import Optional, List, Generator
import openai

SYSTEM_PROMPT = """
You are an efficient terminal assistant. Follow these rules ABSOLUTELY:

1. Response Structure:
- ONLY THREE response types allowed:
  A. Command:	 ```shell
			<commands...>
		 ``` 
  B. Execution Summary: "Result: [metric1], [metric2], [anomaly]"
  C. Error: "Error: [type] - [solution]"

2. Command Phase:
- If command needed: Output ONLY ```shell <commands...> ``` block
- NO explanations/justifications
- IMMEDIATELY stop after ```shell <commands...> ```
- NEVER combine command with other content

3. Execution Phase:
- After command output: SILENT until results
- Process output: generate SINGLE-LINE summary

4. Absolute Prohibitions:
- NO pre-command text
- NO post-command commentary
- NO process explanations
- NO security advice
- NO markdown/formatting

Example Valid Interaction:
User: List my processes
Assistant: [shell]ps aux | grep $USER[/shell]
[After execution]
Assistant: Result: 142 processes, 58% CPU (Ollama), 2.1GB RAM (Safari), 0 suspicious

"""

# Configuration
CONFIG = {
    "ollama_base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "model": "deepseek-r1:14b",
    "timeout": 10,
    "safe_mode": True,
    "shell": os.name == 'posix'
}

client = openai.OpenAI(base_url=CONFIG["ollama_base_url"], api_key=CONFIG["api_key"])

def stream_generator(stream: Generator) -> Generator:
    """Yield characters from a stream with slight delays for natural feel"""
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            for char in content:
                yield char
                sleep(0.02)  # Natural typing speed

def execute_command_streaming(command: str) -> str:
    """Execute command and stream output in real-time"""
    full_output = []
    try:
        proc = subprocess.Popen(
            command if CONFIG["shell"] else ["cmd", "/C", command],
            shell=CONFIG["shell"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Stream output in real-time
        while True:
            reads = [proc.stdout.fileno(), proc.stderr.fileno()]
            ret = select(reads, [], [], CONFIG["timeout"])

            for fd in ret[0]:
                if fd == proc.stdout.fileno():
                    line = proc.stdout.readline()
                    if line:
                        sys.stdout.write(line)
                        sys.stdout.flush()
                        full_output.append(f"STDOUT: {line}")
                if fd == proc.stderr.fileno():
                    line = proc.stderr.readline()
                    if line:
                        sys.stderr.write(line)
                        sys.stderr.flush()
                        full_output.append(f"STDERR: {line}")

            if proc.poll() is not None:
                break

        # Capture remaining output after process exits
        for line in proc.stdout.readlines():
            sys.stdout.write(line)
            full_output.append(f"STDOUT: {line}")
        for line in proc.stderr.readlines():
            sys.stderr.write(line)
            full_output.append(f"STDERR: {line}")

    except subprocess.TimeoutExpired:
        print("\nCommand timed out")
        full_output.append("Command timed out")
        proc.kill()
    except Exception as e:
        print(f"\nError: {str(e)}")
        full_output.append(f"Error: {str(e)}")
    
    return "\n".join(full_output)

def extract_command(buffer: str) -> Optional[str]:
    """Detect command in streaming buffer"""
    match = re.search(r"```(?:shell|bash|sh)\n(.*?)\n```", buffer, re.DOTALL)
    return match.group(1).strip() if match else None

def chat_loop():
    messages = [{
        "role": "system",
        "content": SYSTEM_PROMPT
	}]

    print("\nShell Assistant (type 'exit' to quit)\n")
    while True:
        try:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ('exit', 'quit'):
                break

            messages.append({"role": "user", "content": user_input})

            # Stream initial response
            print("\nAssistant: ", end="", flush=True)
            buffer = ""
            command = None
            stream = client.chat.completions.create(
                model=CONFIG["model"],
                messages=messages,
                temperature=0.7,
                stream=True
            )

            # Stream response and detect commands
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                buffer += content
                
                # Check for command in buffer
                if not command:
                    command = extract_command(buffer)

            messages.append({"role": "assistant", "content": buffer})

            # Execute command flow
            if command:
                if CONFIG["safe_mode"]:
                    print(f"\n\nDetected command:\n> {command}")
                    if input("Execute? [y/N] ").lower().strip() != 'y':
                        continue

                print("\nExecuting command...\n")
                command_output = execute_command_streaming(command)
                
                # Add command output to conversation
                messages.append({
                    "role": "user",
                    "content": f"Command output:\n{command_output}"
                })

                # Stream final explanation
                print("\n\nAssistant: ", end="", flush=True)
                final_response = ""
                stream = client.chat.completions.create(
                    model=CONFIG["model"],
                    messages=messages,
                    temperature=0.7,
                    stream=True
                )

                for chunk in stream:
                    content = chunk.choices[0].delta.content or ""
                    print(content, end="", flush=True)
                    final_response += content

                messages.append({"role": "assistant", "content": final_response})

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            break

if __name__ == "__main__":
    print("⚠️  Warning: This tool executes shell commands. Use with caution! ⚠️")
    try:
        chat_loop()
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)
