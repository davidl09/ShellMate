#! /usr/bin/env python3

import os
import re
import subprocess
import sys
import itertools
import threading
import time
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
Assistant:  
```shell
ps aux | grep $USER
```
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

class ThinkingAnimation:
    def __init__(self):
        self.thinking = False
        self.spinner = itertools.cycle(['/', '-', '\\', '|'])
        self.thread = None

    def start(self):
        if not self.thinking:
            self.thinking = True
            self.thread = threading.Thread(target=self._animate, daemon=True)
            self.thread.start()

    def stop(self):
        self.thinking = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None
        sys.stdout.write('\r' + ' ' * (len("thinking ") + 1) + '\r')
        sys.stdout.flush()

    def _animate(self):
        while self.thinking:
            for symbol in self.spinner:
                if not self.thinking:
                    break
                sys.stdout.write(f'\rthinking {symbol}')
                sys.stdout.flush()
                time.sleep(0.1)

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

    thinking_anim = ThinkingAnimation()
    print("\nShell Assistant (type 'exit' to quit)\n")
    
    while True:
        try:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ('exit', 'quit'):
                break

            messages.append({"role": "user", "content": user_input})
            print("\nAssistant: ", end="", flush=True)
            
            buffer = ""
            command = None
            in_think_block = False
            stream = client.chat.completions.create(
                model=CONFIG["model"],
                messages=messages,
                temperature=0.7,
                stream=True
            )

            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                buffer += content

                # Process think blocks
                if not in_think_block and '<think>' in buffer:
                    parts = buffer.split('<think>', 1)
                    print(parts[0], end='', flush=True)
                    buffer = parts[1] if len(parts) > 1 else ''
                    thinking_anim.start()
                    in_think_block = True

                if in_think_block and '</think>' in buffer:
                    parts = buffer.split('</think>', 1)
                    buffer = parts[1] if len(parts) > 1 else ''
                    thinking_anim.stop()
                    in_think_block = False

                if not in_think_block and buffer:
                    print(buffer, end='', flush=True)
                    buffer = ''

                if not command:
                    command = extract_command(content)

            messages.append({"role": "assistant", "content": buffer})

            if command:
                if CONFIG["safe_mode"]:
                    print(f"\n\nDetected command:\n> {command}")
                    if input("Execute? [y/N] ").lower().strip() != 'y':
                        continue

                print("\nExecuting command...\n")
                command_output = execute_command_streaming(command)
                
                messages.append({
                    "role": "user",
                    "content": f"Command output:\n{command_output}"
                })

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
            thinking_anim.stop()
            print("\n\nOperation cancelled by user")
            break

if __name__ == "__main__":
    print("⚠️  Warning: This tool executes shell commands. Use with caution! ⚠️")
    try:
        chat_loop()
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

