# ShellMate

ShellMate is a command-line application that interfaces with OpenAI's API to execute shell commands and provide intelligent responses. It orchestrates chat management, command extraction, and response handling to offer a seamless user experience.

## Installation

Ensure Python 3.6+ is installed on your system.

The recommended way to install this application is throught pip:

```shell
pip install shmate
```

1. **Create and activate a virtual environment:**

   ```shell
   python -m venv .venv
   source .venv/bin/activate  # On Windows use .venv\\Scripts\\activate
   ```

2. **Install dependencies:**

   ```shell
   pip install .
   ```

3. **Environment Setup:**
   The package provides a `.env.example` file. You will be prompted to modify this file using your API credentials of choice. You must restart the tool after editing environment variables.

## Usage

Run the application using:

```shell
shellmate
```

Follow the on-screen prompts to interact with the AI model, execute commands, and receive feedback.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
