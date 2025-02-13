# ShellMate

ShellMate is a command-line application that interfaces with OpenAI's API to execute shell commands and provide intelligent responses. It orchestrates chat management, command extraction, and response handling to offer a seamless user experience.

## Key Components

- **main.py**: The entry point for the application. Sets up the environment and initiates interactions with OpenAI's API.
- **chat_manager.py**: Manages chat interactions and error handling. Utilizes environment configs for system prompts.
- **extractcmd.py**: Extracts shell commands from input strings using regular expressions.
- **stream_handler.py**: Handles AI response streams, processing data chunks and managing animations.
- **shell.py**: Executes shell commands, logs activities, and captures execution results.
- **thinkinganimation.py**: Provides spinner animations to indicate processing status.

## Installation

Ensure Python 3.6+ is installed on your system.

1. **Create and activate a virtual environment:**

   ```shell
   python -m venv .venv
   source .venv/bin/activate  # On Windows use .venv\\Scripts\\activate
   ```

2. **Install dependencies:**

   Using `requirements.txt`:
   ```shell
   pip install -r requirements.txt
   ```

   Or using `pyproject.toml` for modern setups:
   ```shell
   pip install .
   ```

3. **Environment Setup:**
   Configure your `.env` file. Refer to `.env.example` for required variables.

## Usage

Run the application using:

```shell
python main.py
```

Follow the on-screen prompts to interact with the AI model, execute commands, and receive feedback.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.