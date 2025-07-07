# shared/command_handler.py

from typing import Callable, Awaitable

CommandFunction = Callable[[str], Awaitable[None]] # Receives full command line string and returns an awaitable coroutine

class CommandHandler:
    """A class to handle command registration and execution in an asynchronous context."""

    def __init__(self):
        self._commands: dict[str, CommandFunction] = {}

    def register_command(self, command:str, func: CommandFunction):
            """Register a command with its associated function."""
            if command.startswith("/"):
                self._commands[command] = func
            else:
                raise ValueError("Command must start with '/'")
        
    def has_command(self, command: str) -> bool:
            """Check if a command is registered."""
            return command.split()[0] in self._commands
        
    async def execute_command(self, command_line: str):
            """Execute a registered command with its arguments if registered, otherwise raise an error."""
            cmd = command_line.strip().split()[0]
            if cmd in self._commands:
                await self._commands[cmd](command_line)
            else:
                raise ValueError(f"Command '{cmd}' not recognized. Use /help to see available commands.")

            
            
