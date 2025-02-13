# Project Overview

This project is a command-line application that integrates with OpenAI's API to execute shell commands and provide responses based on AI output. It includes components for managing chat interactions, extracting shell commands, and handling AI response streams.

## Key Components

- **chat_manager.py**: Manages chat interactions and error handling.
- **extractcmd.py**: Extracts shell commands from input strings using regex.
- **main.py**: Entry point for the application, loading environment variables and initiating interactions with the OpenAI API.
- **shell.py**: Handles shell command execution and logging.
- **stream_handler.py**: Manages AI response streams and processes outputs.
- **thinkinganimation.py**: Provides visual feedback during processing.

## Setup

1. Ensure Python is installed on your system.
2. Set up a virtual environment:
   
   ```shell
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scriptsctivate`
   ```

3. Install dependencies:
   
   ```shell
   pip install -r requirements.txt
   ```

4. Set up environment variables in a `.env` file. Refer to `.env.example` for needed variables.

## Usage

Run the application using:

```shell
python main.py
```

Follow the on-screen instructions to interact with the AI model and execute shell commands.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
