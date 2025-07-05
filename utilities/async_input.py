# async_input.py
"""Utility module for async input handling in Python.
This module provides an asynchronous input function `ainput` that can be used to read user input"""

import asyncio
import sys
import warnings
import platform
import subprocess
from typing import Callable

def get_pip_install_hint(package: str = "aioconsole") -> str:
    """Returns a hint for installing the specified package using pip."""
    
    python_exec = sys.executable or "python"

    # Check if pip is available via subprocess
    try:
        subprocess.run([python_exec, "-m", "pip", "--version"], check=True, capture_output=True)
        return f"To install {package}, run:\n\n    {python_exec} -m pip install {package}\n or\n    pip install {package}\n"
    except (subprocess.SubprocessError, FileNotFoundError):
        return f"To install {package}, ensure pip is installed and run:\n\n    {python_exec} -m ensurepip\n    {python_exec} -m pip install {package}\n or\n    pip install {package}\n"
    

# Import ainput from aioconsole if available, otherwise fallback to readline inside executor
try:
    from aioconsole import ainput as async_input # type: ignore
    USES_AIOCONSOLE = True

except ImportError:
    # fallback to using asyncio's run_in_executor with readline
    USES_AIOCONSOLE = False
    
    current_os = platform.system()
    
    # Define hints based on the current OS
    # These hints are based on the OS and whether aioconsole is available or not
    os_hints= {
        "Linux": "We have tested on Linux and Blocking input may hang the event loop and prevent graceful exit while using ctrl+c or ctrl+d or when the server closes the connection. aioconsole is highly recommended or you may face a traceback.",
        "Darwin": "We have not tested this on macOS, but it should work similarly to Linux and aioconsole is strongly recommended.",
        "Windows": "We have tested this on Windows and you may face issues with input blocking while exiting when server closes the connection. aioconsole is still preferred for better experience, but you may not face issues with ctrl+c or ctrl+d.",
        "FreeBSD": "We have not tested this on FreeBSD, but it should work similarly to Linux and aioconsole is strongly recommended.",
        "OpenBSD": "We have not tested this on OpenBSD, but it should work similarly to Linux and aioconsole is strongly recommended.",
        "NetBSD": "We have not tested this on NetBSD, but it should work similarly to Linux and aioconsole is strongly recommended.",
        "SunOS": "We have not tested this on SunOS, but it should work similarly to Linux and aioconsole is strongly recommended.",
        "AIX": "We have not tested this on AIX, but it should work similarly to Linux and aioconsole is strongly recommended.",
        "HP-UX": "We have not tested this on HP-UX, but it should work similarly to Linux and aioconsole is strongly recommended.",
        "Other": "We have not tested this on your OS, but it should work similarly to Linux and aioconsole is strongly recommended. Install aioconsole for full async input support."
    }
    
    # Get the hint message based on the current OS
    hint_message = os_hints.get(current_os, os_hints["Other"])

    # Get the pip install hint for aioconsole
    install_hint = get_pip_install_hint("aioconsole")
    
    warnings.simplefilter("default", category=ImportWarning)
    warnings.warn(
        f"aioconsole not available. Falling back to blocking input via sys.stdin.readline for simulating async input.\n"
        f"This may block the event loop and affect performance.\n"
        f"You will face issues with input and observe compromised exit handling. Please install aioconsole for better async input handling.\n\n"
        f"{hint_message}\n\n{install_hint}", 
        ImportWarning, 
        stacklevel=2)
    
    async def fallback_async_input(prompt: str = "") -> str:
        """ Async input using asyncio's run_in_executor with readline """
        
        sys.stdout.write(prompt)
        sys.stdout.flush()  # Ensure the prompt is printed immediately
        loop = asyncio.get_event_loop_policy().get_event_loop()
        return (await loop.run_in_executor(None, sys.stdin.readline)).rstrip("\n")

def get_async_input() -> Callable:
    """ Returns the async input function based on availability of aioconsole """
    if USES_AIOCONSOLE:
        return async_input  # return the ainput function from aioconsole
    else:
        return fallback_async_input  # fallback to the defined ainput function using run_in_executor