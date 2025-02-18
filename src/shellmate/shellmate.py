#! /usr/bin/env python3
import os
import sys
from os.path import join, dirname
from dotenv import load_dotenv
from .extractcmd import extract_commands
from .stream_handler import handle_response
import openai
from .chat_manager import ChatManager, ChatError, Message
from .shell import Shell
from .edit_env import edit_env

welcome_message = "ShellMate v0.1\nType '/env' to edit environment variables.\nType '/exit' to quit the program.\nType Ctrl+C to terminate the program at any time.\n"


def main():
    dotenv_path = join(dirname(__file__), '.env')
    if not load_dotenv(dotenv_path=dotenv_path, verbose=True):
        edit_env()
    print_all = "-v" in sys.argv[1:]
    print(welcome_message)
    client = openai.OpenAI(
        api_key=os.environ.get("API_KEY"),
        base_url=os.environ.get("ENDPOINT"),
    )

    chat = ChatManager()
    shell = Shell()
    has_command_output = False

    while True:
        if not has_command_output:
            user_prompt = input("\nUser> ")
            if user_prompt == "/exit":
                break
            if user_prompt == "/env":
                edit_env()
                continue
            chat.add_user_message(user_prompt)

        stream = client.chat.completions.create(
            messages=chat.get_messages(),
            model=os.environ.get("MODEL"),
            stream=True,
            temperature=int(os.environ.get("TEMP", "0.8"))
        )

        response = handle_response(stream, printAll=print_all)
                
        chat.add_assistant_message(response)
        commands = extract_commands(response)
        if (len(commands) == 0): 
            has_command_output = False
            continue

        result = shell.executeCommand(commands[0])
        chat.add_user_message(result.__repr__())
        has_command_output = True


if __name__ == "__main__":
    exit(main())

