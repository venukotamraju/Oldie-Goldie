# async_fallbacks.py
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
    

try:

    from prompt_toolkit.patch_stdout import patch_stdout # type: ignore
    from prompt_toolkit.shortcuts import PromptSession # type: ignore

    session = PromptSession()

    async def prompt_async_input(prompt: str = "") -> str:
        """Async input using prompt_toolkit's PromptSession"""
        
        with patch_stdout():
            return await session.prompt_async(prompt)
    
    async def prompt_async_print(*args, **kwargs) -> None:
        """Async print function using asyncio's run_in_executor with prompt_toolkit's patch_stdout"""

        # Use patch_stdout to ensure that the output is flushed immediately
        # and does not interfere with the prompt_toolkit's input handling
        with patch_stdout():
            # Use asyncio's run_in_executor to print asynchronously
            # This allows us to print without blocking the event loop
            # and ensures that the output is flushed immediately
            loop = asyncio.get_event_loop_policy().get_event_loop()
            await loop.run_in_executor(None, print, *args, **kwargs)
        
        

    USES_PROMPT_TOOLKIT = True # prompt_toolkit is used instead of aioconsole
    USES_AIOCONSOLE = False # aioconsole is not used when prompt_toolkit is available

except ImportError:
    # If prompt_toolkit is not available, we will use aioconsole or fallback to sys.stdin.readline
    USES_PROMPT_TOOLKIT = False

    # Determine the current operating system
    # This is used to provide hints for the user based on the OS they are using
    current_os = platform.system()

    os_hints= {
            "Linux": "We have tested on Linux and line redraw and input preservation does not work properly, so `prompt_toolkit` is strongly recommended.",
            "Darwin": "We have not tested this on macOS, but it should work similarly to Linux and `prompt_toolkit` is strongly recommended.",
            "Windows": "We have tested this on Windows and line redraw and input preservation does not work properly, so `prompt_toolkit` is strongly recommended.",
            "FreeBSD": "We have not tested this on FreeBSD, but it should work similarly to Linux and `prompt_toolkit` is strongly recommended.",
            "OpenBSD": "We have not tested this on OpenBSD, but it should work similarly to Linux and `prompt_toolkit` is strongly recommended.",
            "NetBSD": "We have not tested this on NetBSD, but it should work similarly to Linux and `prompt_toolkit` is strongly recommended.",
            "SunOS": "We have not tested this on SunOS, but it should work similarly to Linux and `prompt_toolkit` is strongly recommended.",
            "AIX": "We have not tested this on AIX, but it should work similarly to Linux and `prompt_toolkit` is strongly recommended.",
            "HP-UX": "We have not tested this on HP-UX, but it should work similarly to Linux and `prompt_toolkit` is strongly recommended.",
            "Other": "We have not tested this on your OS, but it should work similarly to Linux and `prompt_toolkit` is strongly recommended. Install `prompt_toolkit` for full async input support and prompt compatability."
        }
    
    # Get the hint message based on the current OS
    hint_message = os_hints.get(current_os, os_hints["Other"])

    # Get the pip install hint for prompt_toolkit
    install_hint = get_pip_install_hint(package="prompt_toolkit")

    # Warn about the missing prompt_toolkit and suggest using aioconsole or fallback to readline
    warnings.simplefilter("default", category=ImportWarning)
    warnings.warn(
        "prompt_toolkit not available. Falling back to aioconsole.\n"
        "The input is non-blocking but still may not preserve input history or redraw lines properly.\n"
        "Please install prompt_toolkit for better async input handling, line redraw and input preservation.\n\n"
        f"[{current_os}] {hint_message}\n\n {install_hint}",
        ImportWarning, 
        stacklevel=2)

    # Fallback to ainput from aioconsole if available, otherwise fallback to readline inside executor
    try:
        from aioconsole import ainput as async_input # type: ignore
        from aioconsole import aprint as async_print # type: ignore
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
        
        # Fallback async input function using asyncio's run_in_executor with sys.stdin.readline
        # This is a last resort and should only be used if aioconsole is not available
        async def fallback_async_input(prompt: str = "") -> str:
            """ Async input using asyncio's run_in_executor with readline """
            
            sys.stdout.write(prompt)
            sys.stdout.flush()  # Ensure the prompt is printed immediately
            loop = asyncio.get_event_loop_policy().get_event_loop()
            return (await loop.run_in_executor(None, sys.stdin.readline)).rstrip("\n")
        
        async def fallback_async_print(*args, **kwargs) -> None:
            """ Async print function using asyncio's run_in_executor """

            loop = asyncio.get_event_loop_policy().get_event_loop()
            await loop.run_in_executor(None, print, *args, **kwargs)

def get_async_input() -> Callable:
    """ Returns the async input function based on availability of aioconsole """

    if USES_PROMPT_TOOLKIT:
        return prompt_async_input # return the async input function from prompt_toolkit
    elif USES_AIOCONSOLE:
        return async_input  # return the ainput function from aioconsole
    else:
        return fallback_async_input  # fallback to the defined ainput function using run_in_executor
    

def get_async_print() -> Callable:
    """ Returns the async print function based on availability of aioconsole """

    if USES_PROMPT_TOOLKIT:
        return prompt_async_print  # return the async print function from prompt_toolkit
    elif USES_AIOCONSOLE:
        return async_print  # return the aprint function from aioconsole
    else:
        return fallback_async_print  # fallback to the defined aprint function using run_in_executor