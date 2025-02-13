from dataclasses import dataclass
import os
from typing import List, Dict
import json

@dataclass
class Message:
    role: str
    content: str

class ChatError(Exception):
    def __init__(self, error: str):
        super().__init__(error)
        self.error = error

class ChatManager:
    def __init__(self):
        system_prompt_file_name = os.environ.get("SYSTEM_PROMPT_FILE")
        system_prompt_file_path = os.path.join(os.path.dirname(__file__), system_prompt_file_name)
        try:
            with open(system_prompt_file_path, "r") as system_prompt_file:
                system_prompt_content = system_prompt_file.read()
        except OSError:
            print(f"Could not open system prompt file {system_prompt_file_path}. Make sure it exists.")
            exit(1)

        # Initialize with a system message.
        self.messages: List[Message] = [Message("system", system_prompt_content)]

    def add_user_message(self, content: str) -> None:
        # Allow a user message only if the last message is not already a user message.
        if self.messages[-1].role == "user":
            raise ChatError("Invalid order: Cannot add consecutive user messages without an assistant response")
        self.messages.append(Message("user", content))

    def add_assistant_message(self, content: str) -> None:
        # Allow an assistant message only if the last message is a user message.
        if self.messages[-1].role != "user":
            raise ChatError("Invalid order: Assistant messages must follow a user message")
        self.messages.append(Message("assistant", content))

    def get_messages(self) -> List[Dict[str, str]]:
        return [msg.__dict__ for msg in self.messages]
    

   