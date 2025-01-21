#! /usr/bin/env python3

import os
import re
import subprocess
import sys
import itertools
import threading
import time
from select import select
from typing import Optional, List, Dict, Any, Generator
import openai
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Note: python-dotenv not installed. Will not load from .env file.")

SYSTEM_PROMPT = """You are a terminal assistant that can execute shell commands.

RULES:
1. NEVER explain commands before executing them
2. NEVER output example results
3. Use <think> tags only for internal reasoning
4. After command execution, explain the actual results clearly
5. Keep responses concise and focused
6. If you need to execute a command, place it at the very end of your response. The system will respond with the command output.
7. Place commands in ```shell\n<command>\n``` blocks
8. DO NOT instruct the user to execute any commands. You are responsible for completing any user-assigned tasks.
9. Output ONE command per response, at the end of the response. The system will respond with the command output. You may then respond to the user directly, or execute a follow-up command.

YOU are responsible for executing any tasks the user requests. Continue executing commands and thinking how to execute the tasks until they are completed.


Example interaction:
User: What's in my home directory?
<think>
I'll use ls to show the contents
</think>
```shell
ls ~
```
System: 
Documents
Downloads
Projects
README.md
.bashrc
<think>
Got the output, let me analyze it
</think>
System:
Documents   Downloads   Projects    README.md   .bashrc
Assistant:
Your home directory contains 3 folders (Documents, Downloads, Projects) and 2 files (README.md, .bashrc).

Example with multiple commands:

User: Show disk space usage in human readable format
<think>
I'll check both disk and directory usage
</think>
```shell
df -h
```
System:
Filesystem        Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s1s1   460Gi    10Gi   229Gi     5%    412k  2.4G    0%   /
devfs            230Ki   230Ki     0Bi   100%     796     0  100%   /dev
/dev/disk3s6     460Gi   2.0Gi   229Gi     1%       2  2.4G    0%   /System/Volumes/VM
/dev/disk3s2     460Gi   6.4Gi   229Gi     3%    1.2k  2.4G    0%   /System/Volumes/Preboot
/dev/disk3s4     460Gi   3.6Mi   229Gi     1%      53  2.4G    0%   /System/Volumes/Update
/dev/disk1s2     500Mi   6.0Mi   483Mi     2%       1  4.9M    0%   /System/Volumes/xarts
/dev/disk1s1     500Mi   5.4Mi   483Mi     2%      33  4.9M    0%   /System/Volumes/iSCPreboot
/dev/disk1s3     500Mi   1.0Mi   483Mi     1%      89  4.9M    0%   /System/Volumes/Hardware
/dev/disk3s5     460Gi   211Gi   229Gi    48%    2.2M  2.4G    0%   /System/Volumes/Data
map auto_home      0Bi     0Bi     0Bi   100%       0     0     -   /System/Volumes/Data/home
/dev/disk5s1     8.4Gi   8.1Gi   248Mi    98%      13  2.5M    0%   /Library/Developer/CoreSimulator/Cryptex/Images/bundle/SimRuntimeBundle-00E8F4CA-A907-4740-B926-0DEA50653918
/dev/disk7s1      18Gi    18Gi   472Mi    98%    459k  4.8M    9%   /Library/Developer/CoreSimulator/Volumes/iOS_22C150
/dev/disk9s1     8.0Gi   7.8Gi   239Mi    98%      13  2.4M    0%   /Library/Developer/CoreSimulator/Cryptex/Images/bundle/SimRuntimeBundle-747C571F-302E-4B91-9405-A019F1406135
/dev/disk11s1     18Gi    17Gi   461Mi    98%    444k  4.7M    9%   /Library/Developer/CoreSimulator/Volumes/iOS_22A3351
/dev/disk13s1    8.2Gi   8.0Gi   245Mi    98%      13  2.5M    0%   /Library/Developer/CoreSimulator/Cryptex/Images/bundle/SimRuntimeBundle-7CB3D7EB-EE32-4C74-8B32-9A2DDEB1F013
/dev/disk15s1     18Gi    18Gi   467Mi    98%    452k  4.8M    9%   /Library/Developer/CoreSimulator/Volumes/iOS_22B81
/dev/disk3s3     460Gi   986Mi   229Gi     1%      38  2.4G    0%   /Volumes/Recovery
Assistant:
<think>
Now checking directory sizes
</think>
```shell
du -sh *
```
System:
 14G    Applications
 15G    CLionProjects
 28K    CascadeProjects
1.5G    Desktop
 28M    Documents
 16K    Downloads
 56G    Library
494M    Movies
6.1M    Music
8.2G    Pictures
  0B    Public
2.9M    VirtualBox VMs
259M    WebstormProjects
1.2M    XCodeProjects
 15M    Zotero
 43M    eclipse-workspace
2.1G    freqtrade
2.8M    genesis
4.0K    temp.txt
4.0K    twillio-code.txt
 74M    zls
Assistant:
<think>
Analyzing both outputs to give a clear summary
</think>
Your system has 100GB total space with 50GB free. The largest directories are:
- Downloads: 20GB
- Documents: 15GB
- Projects: 10GB

Example handling failures:
User: Show nginx version
<think>
Let's check nginx version
</think>
```shell
nginx -v
```
System:
bash: nginx: command not found
Assistant:
<think>
Command failed, nginx might not be installed. Let's check another way
</think>
```shell
which nginx
```
System:
Assistant:
<think>
The command shows nginx is not installed
</think>
Nginx is not installed on your system."""

class CommandResult:
    def __init__(self, output: str, error: Optional[str] = None, return_code: int = 0):
        self.output = output
        self.error = error
        self.return_code = return_code
        self.success = return_code == 0

    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}\nOutput: {self.output}"

class CommandExecutor:
    def __init__(self, shell: bool = True, timeout: int = 10):
        self.shell = shell
        self.timeout = timeout

    def execute(self, command: str) -> CommandResult:
        """Execute a shell command and return the result"""
        try:
            proc = subprocess.Popen(
                command if self.shell else ["cmd", "/C", command],
                shell=self.shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            output_lines = []
            while True:
                reads = [proc.stdout.fileno(), proc.stderr.fileno()]
                ret = select(reads, [], [], self.timeout)

                if not ret[0]:  # Timeout
                    proc.kill()
                    raise subprocess.TimeoutExpired(cmd=command, timeout=self.timeout)

                for fd in ret[0]:
                    if fd == proc.stdout.fileno():
                        line = proc.stdout.readline()
                        if line:
                            sys.stdout.write(line)
                            sys.stdout.flush()
                            output_lines.append(line.strip())
                    if fd == proc.stderr.fileno():
                        line = proc.stderr.readline()
                        if line:
                            sys.stderr.write(line)
                            sys.stderr.flush()
                            output_lines.append(line.strip())

                if proc.poll() is not None:
                    break

            return CommandResult(
                output="\n".join(output_lines),
                return_code=proc.returncode
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                output="",
                error="Command timed out",
                return_code=1
            )
        except Exception as e:
            return CommandResult(
                output="",
                error=str(e),
                return_code=1
            )

@dataclass
class Message:
    role: str
    content: str

class ChatHistory:
    def __init__(self, system_prompt: str):
        self.messages: List[Message] = [Message("system", system_prompt)]

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message("user", content))

    def add_assistant_message(self, content: str) -> None:
        self.messages.append(Message("assistant", content))

    def get_messages(self) -> List[Dict[str, str]]:
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

class Config:
    DEFAULT_CONFIG = {
        "ollama_base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "deepseek-r1:14b",
        "timeout": 10,
        "safe_mode": True,
        "shell": os.name == 'posix'
    }

    def __init__(self, **kwargs):
        self.ollama_base_url = kwargs.get("ollama_base_url", self.DEFAULT_CONFIG["ollama_base_url"])
        self.api_key = kwargs.get("api_key", self.DEFAULT_CONFIG["api_key"])
        self.model = kwargs.get("model", self.DEFAULT_CONFIG["model"])
        self.timeout = kwargs.get("timeout", self.DEFAULT_CONFIG["timeout"])
        self.safe_mode = kwargs.get("safe_mode", self.DEFAULT_CONFIG["safe_mode"])
        self.shell = kwargs.get("shell", self.DEFAULT_CONFIG["shell"])

    @classmethod
    def load(cls, env_file: Optional[str] = None) -> 'Config':
        """
        Load configuration from multiple sources in order of precedence:
        1. Environment variables
        2. .env file (if exists and python-dotenv is available)
        3. Default values
        
        Args:
            env_file: Optional path to .env file. If None, will look for .env in current directory
        """
        config_dict = cls.DEFAULT_CONFIG.copy()
        
        # Try to load from .env file if available
        if DOTENV_AVAILABLE:
            if env_file is None:
                # Look for .env in the same directory as the script
                script_dir = Path(__file__).parent
                env_file = str(script_dir / '.env')
            
            if os.path.exists(env_file):
                load_dotenv(env_file)
                print(f"Loaded configuration from {env_file}")
        
        # Environment variable names
        env_vars = {
            "ollama_base_url": "OLLAMA_BASE_URL",
            "api_key": "OLLAMA_API_KEY",
            "model": "OLLAMA_MODEL",
            "timeout": "COMMAND_TIMEOUT",
            "safe_mode": "SAFE_MODE",
        }
        
        # Update config from environment variables (including those loaded from .env)
        for config_key, env_var in env_vars.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                if config_key == "timeout":
                    try:
                        config_dict[config_key] = int(env_value)
                    except ValueError:
                        print(f"Warning: Invalid {env_var} value '{env_value}'. Using default: {config_dict[config_key]}")
                elif config_key == "safe_mode":
                    config_dict[config_key] = env_value.lower() in ('1', 'true', 'yes', 'on')
                else:
                    config_dict[config_key] = env_value
        
        return cls(**config_dict)

    def __str__(self) -> str:
        """Return a string representation of the current configuration"""
        return "\n".join([
            "Current Configuration:",
            f"  Ollama Base URL: {self.ollama_base_url}",
            f"  Model: {self.model}",
            f"  Command Timeout: {self.timeout}s",
            f"  Safe Mode: {'Enabled' if self.safe_mode else 'Disabled'}",
            f"  Shell: {'Posix' if self.shell else 'Windows'}"
        ])

class ThinkingAnimation:
    def __init__(self):
        self.thinking = False
        self.spinner = itertools.cycle(['⣷','⣯','⣟','⡿','⢿','⣻','⣽','⣾'])
        self.thread = None

    def start(self):
        if not self.thinking:
            self.thinking = True
            # Move to new line for spinner
            sys.stdout.write('\n')
            sys.stdout.flush()
            self.thread = threading.Thread(target=self._animate, daemon=True)
            self.thread.start()

    def stop(self):
        self.thinking = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None
            # Clear spinner line and move cursor back up
            sys.stdout.write('\r\033[K')  # Clear current line
            sys.stdout.write('\033[1A')   # Move cursor up one line
            sys.stdout.flush()

    def _animate(self):
        while self.thinking:
            for symbol in self.spinner:
                if not self.thinking:
                    break
                sys.stdout.write(f'\r{symbol} ')
                sys.stdout.flush()
                time.sleep(0.1)

def extract_command(buffer: str) -> Optional[str]:
    """Improved command extraction"""
    block_match = re.search(r"```(?:shell|bash|sh)\n(.*?)\n```", buffer, re.DOTALL)
    return block_match.group(1).strip() if block_match else None

def chat_loop():
    config = Config.load()
    print(f"\n{config}\n")
    print("⚠️  Warning: Executes shell commands. Use carefully! ⚠️\n")
    client = openai.OpenAI(base_url=config.ollama_base_url, api_key=config.api_key)
    executor = CommandExecutor(shell=config.shell, timeout=config.timeout)
    history = ChatHistory(SYSTEM_PROMPT)
    thinking_anim = ThinkingAnimation()
    
    print("\nShell Assistant (type 'exit' to quit)\n")
    
    while True:
        try:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ('exit', 'quit'):
                break

            history.add_user_message(user_input)
            print("\nAssistant: ", end="", flush=True)
            
            while True:  # Loop to handle multiple commands in one response
                buffer = ""
                think_buffer = ""
                in_think_block = False
                stream = client.chat.completions.create(
                    model=config.model,
                    messages=history.get_messages(),
                    temperature=0.7,
                    stream=True
                )

                command_found = False
                for chunk in stream:
                    content = chunk.choices[0].delta.content or ""
                    
                    # Check for think block markers
                    if '<think>' in content:
                        in_think_block = True
                        thinking_anim.start()
                        content = content.split('<think>', 1)[0]
                    elif '</think>' in content:
                        in_think_block = False
                        thinking_anim.stop()
                        content = content.split('</think>', 1)[1]
                    
                    # Handle content based on whether we're in a think block
                    if in_think_block:
                        think_buffer += content
                    else:
                        if content:
                            # Strip any "Assistant:" prefix that the model might add
                            if buffer == "" and content.lower().startswith(("a:", "assistant:", "assistant: ")):
                                content = content.split(":", 1)[1].lstrip()
                            print(content, end='', flush=True)
                            buffer += content
                    
                    # Check for command after adding content
                    command = extract_command(buffer)
                    if command and not command_found:
                        command_found = True
                        if config.safe_mode:
                            print(f"\n\nDetected command:\n> {command}")
                            confirm = input("Execute? [y/N] ").lower().strip()
                            if confirm != 'y':
                                print("Command cancelled")
                                history.add_user_message("User cancelled command")
                                break

                        print("\nExecuting command...\n")
                        result = executor.execute(command)
                        
                        # Add command and its output to history
                        history.add_user_message(f"Command output:\n{str(result)}")
                        
                        # If command failed, let the model try again
                        if not result.success:
                            history.add_user_message(f"Command failed. Error: {result.error}")
                            break  # Break the chunk loop to let model respond to failure
                        
                        # Continue processing chunks to allow for more commands
                        buffer = buffer.split("```", 2)[2] if "```" in buffer else ""  # Remove the executed command block

                if not command_found:
                    # No more commands in the response
                    history.add_assistant_message(buffer)
                    break  # Break the outer loop
                
                # If we had a command but no more content, or command failed,
                # let the model continue with a new response
                if command_found and (not buffer.strip() or not result.success):
                    continue  # Continue the outer loop for more potential commands
                
                # If we had commands and more content after them, we're done
                if command_found and buffer.strip():
                    history.add_assistant_message(buffer)
                    break  # Break the outer loop

        except KeyboardInterrupt:
            thinking_anim.stop()
            print("\n\nOperation cancelled")
            break

if __name__ == "__main__":
    try:
        chat_loop()
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)