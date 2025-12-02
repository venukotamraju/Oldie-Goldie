import asyncio
from typing import Any
import websockets
import logging
import base64
from datetime import datetime
import argparse

from oldie_goldie.client.helpers.tunnel_activity import TunnelActivityUtilsForOG

from oldie_goldie.shared import encode_message, decode_message, make_register_message,make_system_request
from oldie_goldie.shared import version_banner
from oldie_goldie.shared import SecureMethodsForOG

# Importing the CommandHandler class from shared.command_handler module
# This class is responsible for managing commands and their execution in the chat client.
from oldie_goldie.shared import CommandHandler

from importlib.metadata import version, PackageNotFoundError

# Importing the async input utility function and async print utility function
# These functions are used to handle asynchronous input and output in the chat client.

# Importing ainput from the utility module
# This utility function is used to handle asynchronous input without blocking the event loop.
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.application import get_app_or_none
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import FormattedText


session = PromptSession()

# expose session and allow external refresh
get_prompt_session = lambda: session

# Importing aprint from the utility module ## Deprecated, utility module is no longer needed using prompt_toolkit as a default dependency
# This utility function is used to handle asynchronous output without blocking the event loop.

async def prompt_async_print(*args, **kwargs) -> None:
        """Async print function using asyncio's run_in_executor with prompt_toolkit's patch_stdout
        
        Supports:
        - Colored print with text wrapped in html tags containing names of the ansi colors.  
            ex: `<ansired>hello world!</ansired>`  
            - Available ANSI colors:  
                - **Low intensity, dark.  (One or two components 0x80, the other 0x00.)**  
                  - ansiblack, ansired, ansigreen, ansiyellow, ansiblue
                  ansimagenta, ansicyan, ansigray  
                - **High intensity, bright**  
                  - ansibrightblack, ansibrightred, ansibrightgreen, ansibrightyellow
                  ansibrightblue, ansibrightmagenta, ansibrightcyan, ansiwhite
        """

        # Use patch_stdout to ensure that the output is flushed immediately
        # and does not interfere with the prompt_toolkit's input handling
        with patch_stdout():
            # Use asyncio's run_in_executor to print asynchronously
            # This allows us to print without blocking the event loop
            # and ensures that the output is flushed immediately
            loop = asyncio.get_event_loop_policy().get_event_loop()

            # If there are any HTML tags, we can handle them
            if any('<' in arg and '>' in arg for arg in args):
                await loop.run_in_executor(None, lambda: print_formatted_text(HTML(*args, **kwargs)))
            else:
                # If no HTML tags are found, just print plain text
                await loop.run_in_executor(None, lambda: print(*args, **kwargs))

aprint = prompt_async_print

# Importing the command handler for managing commands
command_handler = CommandHandler()

# === Configuration === #
SERVER_URI = "wss://results-facial-stories-newer.trycloudflare.com"
# "ws://localhost:8765"

logging.basicConfig(
    level=logging.INFO,
    format= "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
    )
logger = logging.getLogger(__name__)

active_websocket: websockets.ClientConnection
current_username: str

tunnel_utils = TunnelActivityUtilsForOG()

# === Input management state === #
input_mode = 'chat' # other possible value: "chat", "psk", "locked","encrypted"
input_future: asyncio.Future | None = None

def set_input_mode(mode: str):
    global input_mode
    input_mode = mode

    # Immediately force the prompt refresh using prompt_toolkit
    try:
        app = get_app_or_none()
        if app:
            app.invalidate()

            # Only call exit() if the prompt application is running
            if app.is_running:
                app.exit()
            else:
                logger.debug("[set_input_mode] Prompt app is not running; skipping exit().")
        else:
            logger.debug("[set_input_mode] No active prompt application found.")

    except Exception as e:
        logger.error(f"[set_input_mode] Failed to interrupt prompt: {e}")

# === Client Global Events Object For Protocol Type === #
client_event_types = {
    'TUNNEL_EXIT': 'tunnel_exit',
    'KEY_SHARE': 'key_share',
    'ENCRYPTED_MESSAGE': 'encrypted_message',
    'SYSTEM_RESPONSE': 'system_response'
}

# =========== #


# ======================== #
# Safe Input
# ======================== #

async def safe_input(prompt: str = "> ", password: bool = False, color: str = None) -> str:
    """ Asynchronous, safe user input wrapper with prompt_toolkit.
    
    - Uses async prompt to avoid blocking event loop.

    Supports:
    - password masking via `password=True`.
    - colorized prompts
    - Graceful Ctrl+C / EOF handling.
    
    

    Args:
        prompt (str, optional): The text that should be displayed as the prompt while taking in user input. Defaults to "> ".
        password (bool, optional): If True, the text input will be taken in as password format else plain text format. Defaults to False.
        color (str, optional): 
            Available ANSI colors:
                /# Low intensity, dark.  (One or two components 0x80, the other 0x00.)
                    ansiblack, ansired, ansigreen, ansiyellow, ansiblue
                    ansimagenta, ansicyan, ansigray

                /# High intensity, bright
                    ansibrightblack, ansibrightred, ansibrightgreen, ansibrightyellow
                    ansibrightblue, ansibrightmagenta, ansibrightcyan, ansiwhite        
            \n Defaults to None.

    Raises:
        KeyboardInterrupt: When Ctrl^C is pressed. (Ctrl^C registers as a termination syscall in windows systems and in most linux systems)

    Returns:
        str: the user input entered as a string
    """
    
    # Build colored prompt
    ## First take in normal prompt if color is not passed
    workable_prompt = prompt

    ## Now validate the color
    available_color = ('ansiblack', 'ansired', 'ansigreen', 'ansiyellow', 'ansiblue'
                'ansimagenta', 'ansicyan', 'ansigray','ansibrightblack', 'ansibrightred', 'ansibrightgreen', 'ansibrightyellow'
                'ansibrightblue', 'ansibrightmagenta', 'ansibrightcyan', 'ansiwhite')
    
    if color:
        if color not in available_color:
            color = None
            # Don't make any changes to workable prompt, just pass in the prompt as is, prompt_toolkit will take care of assigning a default color.
        else:
        ## Update workable prompt if color is passed
            workable_prompt = FormattedText([
                (f"{color} bold", prompt)
            ])

    

    try:
        with patch_stdout():
            # Use password masking if requested
            return await session.prompt_async(
                workable_prompt,
                is_password=password,
                enable_history_search=True,
                wrap_lines=False,
            )

    except (KeyboardInterrupt, EOFError):
        
        logger.debug("[safe_input] Keyboard interrupt or EOF detected")
        await aprint("----\n<ansiyellow>!</ansiyellow> <ansigray>Received Keyboard Interrupt</ansigray>\n----")
        
        raise KeyboardInterrupt



# ======================== #
# Exit Confirmation
# ======================== #

# Helper method for confirming exit
# Async input for confirmation (still works fine with ainput)
async def confirm_exit() -> bool:
    """ Prompt the user to confirm if they really want to exit """

    while True:
        response = await safe_input(prompt="Confirm your will to exit (y/n) ", color='ansired')
        response = response.strip().lower()
        
        if response == "y":
            return True
        
        elif response == "n":
            
            logger.debug(msg="[confirm_exit] Resuming chat. User decided not to exit.")            
            return False
        
        else:

            logger.debug("You have to enter something [y/n]. come on -_-")
            await aprint("----\n<ansigray>You have to enter something [y/n]. come on -_-</ansigray>\n----")

# ======================== #
# Built-in Commands
# ======================== #

# Registering commands with the command handler
# This allows the chat client to recognize and execute commands like /help, /exit, etc
# Register built-in commands
async def cmd_exit(_: str):
    """ Command to exit the chat client """
    
    logger.debug("[cmd_exit] User requested exit command.")
    
    should_exit = await confirm_exit()
    
    if should_exit:
        
        logger.debug("[cmd_exit] User confirmed exit. Raising CancelledError to signal shutdown.")
        await aprint("----\n<ansired>Exit Confirmed</ansired>\n----")
        
        raise asyncio.CancelledError
    
    else:
        
        logger.debug("[cmd_exit] User chose not to exit. Resuming chat.")
        await aprint("----\n<ansigreen>Exit Revoked, Resuming Chat</ansigreen>\n----")

async def cmd_help(_: str):
    """ Command to display help information """
    help_text = (
        "Available commands:\n"
        "/help - Show this help message\n"
        "/exit - Exit the chat client\n"
        "/whoami - Show your connection details (For now only username)\n"
        "/connect - Connect with peers; usage `/connect @{username}`\n"
        "/pending - List current connection status\n"
        "/deny - Cancel pending connection (incoming or outgoing)\n"
        "/accept - Accept incoming connection request\n"
        "/list_users - List the users connected to the server you are connected to.\n"
        "/exit_tunnel - Close an active private tunnel\n"
        "Type your message and press Enter to send it.\n"
    )

    # Let's build colored help_text
    # We need to split on '\n'
    # Iterate from the second element
    # Split on '-'
    # Add html tags for the first element
    # Join on '-'
    # Join on '\n'
    formatted_help_text = '\n'.join(['-'.join([f"<ansicyan>{command_text}</ansicyan>" if '/' in command_text else command_text for command_text in line.split('-')]) for line in help_text.splitlines()])
    await aprint(formatted_help_text)

async def cmd_whoami(_: str):
    """ Command to display the client's registered username """

    await aprint(f"----\nYou are registered as:\n<ansigray>username</ansigray>: '<ansiyellow>{current_username}</ansiyellow>'\n----")

command_handler.register_command("/exit", cmd_exit)
command_handler.register_command("/help", cmd_help)
command_handler.register_command("/whoami", cmd_whoami)
# More can be registered like '/connect', 'whoami', etc. as needed

# ========================== #
# Connection State
# ========================== #

connection_state: dict[str, str | None] = {
    "status": "idle",   # idle, request_sent, request_received, wait_tunnel_trigger, tunnel_validating, tunnel_active
    "target": None,     # Who we are talking to or requesting
    "direction": None,  # incoming or outgoing
}

TUNNEL_TIMEOUT = 10 # seconds
# This section handles the connection state logic and respective command methods for the chat client.

async def reset_connection_state():
    """Helper to reset the connection state."""

    logger.debug("[reset_connection_state] Resetting connection state to idle.")
    await aprint("----\n<ansigray>Resetting Your Connection State</ansigray>\n----")

    connection_state.update({
        "status": "idle",
        "target": None,
        "direction": None,
    })

async def start_tunnel_validation(peer: str):
    """Ask user for PSK and send to server within timeout."""
    global input_future

    connection_state["status"] = "tunnel_validating"

    logger.debug(f"[start_tunnel_validation] Private tunnel with @{peer} requires PSK entry.")
    await aprint(f"----\nPrivate tunnel with @<ansicyan>{peer}</ansicyan> requires PSK entry\n----")

    set_input_mode("psk")
    input_future = asyncio.get_event_loop().create_future()

    try:
        psk_entered = await asyncio.wait_for(input_future, timeout=TUNNEL_TIMEOUT)
        
        # Hash the psk to confidentially send it to the server for validation
        hashed_psk = SecureMethodsForOG.hash_psk(psk=psk_entered)
        logger.debug('[start_tunnel_validation] Hashing PSK')
        
        # set the psk_hash in the tunnel utils, to use its functionality if the psk gets verified
        tunnel_utils.set_psk_hash(psk_hash=hashed_psk)

        # encode the bytes to make them suitable for transmission
        encoded_psk_hash = base64.b64encode(hashed_psk).decode('utf-8')
        logger.debug('[start_tunnel_validation] Encoding the psk hash to base 64')

        # Send encoded PSK hash to server
        await active_websocket.send(
            encode_message(
                type="tunnel_secret",
                sender=current_username,
                secret=encoded_psk_hash,
                message="tunnel_secret"
            )
        )

        logger.debug("[start_tunnel_validation] PSK submitted. Waiting for server confirmation.")
        await aprint("----\n<ansigray>PSK submitted\nAwaiting for server confirmation.</ansigray>\n----")
        
        return True
    
    except (KeyboardInterrupt, EOFError):
        
        logger.debug("[start_tunnel_validation] Validation interrupted. Closing tunnel.")
        await aprint("----\n<ansired>!</ansired> <ansigray>Validation interrupted\nClosing tunnel.</ansigray>\n----")

        return False

    except asyncio.TimeoutError:
        
        logger.debug("[start_tunnel_validation] PSK entry timed out. Connection attempt cancelled.")
        await aprint("----\n<ansired>!</ansired> <ansigray>PSK entry timed out\nConnection attempt cancelled.</ansigray>\n----")
        
        return False
    
    finally:
        input_future = None
        # set_input_mode('chat')

# ========================== #
# Connection Commands
# ========================== #
async def cmd_connect(line: str):
    """ Initiate a connection request to another user """

    parts = line.strip().split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        
        logger.debug("[cmd_connect] Usage: /connect @username")
        await aprint("----\n<ansicyan>?</ansicyan> <ansigray>Usage:</ansigray> /connect @username\n----")
        
        return
    
    target_username = parts[1][1:]  # Remove the '@' symbol
    if target_username == "":
        
        logger.debug("[cmd_connect] Invalid username. Please provide a valid username starting with '@'.")
        await aprint("----\n<ansicyan>?</ansicyan><ansired>!</ansired> <ansigray>Invalid username\nPlease provide a valid username starting with '@'.</ansigray>\n----")
        
        return
    
    if connection_state["status"] != "idle":
        
        logger.debug("[cmd_connect] Already in a connection state. Use /pending or /deny.")
        await aprint("----\n<ansicyan>?</ansicyan><ansired>!</ansired> <ansigray>You already are in a connection state\nTip: Use</ansigray>\n`<ansicyan>/pending</ansicyan>`: To view pending requests\n`<ansicyan>/deny</ansicyan>`: To deny pending requests.\n----")
        
        return

    connection_state.update({
        "status": "request_sent",
        "target": target_username,
        "direction": "outgoing",
    })

    logger.debug(f"[cmd_connect] Connection request sent to @{target_username}.")
    await aprint(f"----\n<ansigray>Connection request sent to</ansigray> @<ansiyellow>{target_username}</ansiyellow>\n----")

    # Send message to server (async task)
    task = asyncio.create_task(
        active_websocket.send(
            encode_message(
                type="connect_request",
                sender=current_username,
                target=target_username,
                message="connect_request"
            )
        )
    )

    # Ensure that task is awaited for clean handling
    _ = asyncio.create_task(wait_and_log_task(task, "cmd_connect"))

async def cmd_accept(_: str):
    """ Accept a pending incoming connection request """
    
    if connection_state["status"] != "request_received":

        logger.debug("[cmd_accept] No incoming connection request.")
        await aprint("----\n<ansigray>No incoming connection request.</ansigray>\n----")

        return
    
    peer = connection_state["target"]
    
    logger.debug(f"[cmd_accept] Accepting connection from @{peer}")
    await aprint(f"----\n<ansigray>Accepting connection from @</ansigray><ansiyellow>{peer}</ansiyellow>\n----")

    task = asyncio.create_task(
        active_websocket.send(
            encode_message(
                type="connect_accept",
                sender=current_username,
                target=peer,
                message="connect_request"
            )
        )
    )
    await wait_and_log_task(task, "cmd_accept")   
    connection_state["status"] = 'wait_tunnel_trigger'

async def cmd_deny(_: str):
    """ Deny a pending incoming/outgoing connection """
    
    if connection_state["status"] not in ("request_received", "request_sent"):
        
        logger.debug("[cmd_deny] No incoming request to deny.")
        await aprint("----<ansigray>No pending request to deny.</ansigray>----\n")
        
        return
    
    peer = connection_state["target"]
    if connection_state["direction"] == "outgoing":
        
        logger.debug(f"[cmd_deny] Cancelled outgoing connection request to @{peer}.")
        await aprint(f"----\n<ansigray>Cancelled outgoing connection request to @</ansigray><ansiyellow>{peer}</ansiyellow>.\n----")

    else:
        
        logger.debug(f"[cmd_deny] Denied connection request from @{peer}.")
        await aprint(f"----\n<ansigray>Denied incoming connection request from @</ansigray><ansiyellow>{peer}</ansiyellow>.\n----")

    await reset_connection_state()

    task = asyncio.create_task(
        active_websocket.send(
            encode_message(
                type="connect_deny",
                sender=current_username,
                target=peer,
                message="connect_deny"
            )
        )
    )

    __ = asyncio.create_task(wait_and_log_task(task, "cmd_deny"))

async def cmd_exit_tunnel(_: str):
    """Exit the active private tunnel."""

    if connection_state["status"] != "tunnel_active":
        
        logger.debug("[cmd_exit_tunnel] No active tunnel.")
        await aprint("----\n<ansigray>No active tunnel to exit from.</ansigray>\n----")
        
        return
    
    # Notify Server that a peer has exited the tunnel, so that that server would forward the same to the fellow peer, and they too can reset their state.
    task = asyncio.create_task(
        active_websocket.send(
            encode_message(
                type=client_event_types["TUNNEL_EXIT"],
                sender=current_username,
                target=connection_state["target"],
                message="tunnel_exit"
            )
        )
    )
    await wait_and_log_task(task, "cmd_exit_tunnel")

    logger.debug(f"[cmd_exit_tunnel] Tunnel with @{connection_state['target']} closed.")
    await aprint(f"----\n<ansigray>Tunnel closed with @</ansigray><ansiyellow>{connection_state['target']}</ansiyellow>\n----")
    
    await reset_connection_state()
    set_input_mode('chat')

async def cmd_pending(_: str):
    """ Check the current connection state """
    status = connection_state["status"]
    if status == "idle":
        
        logger.debug("[cmd_pending] No active or pending connections.")
        await aprint("----\nNo active or pending connections.\n----")
    
    else:
        
        logger.debug(f"[cmd_pending] Status: {connection_state['status']}, Target: @{connection_state['target']}, Direction: {connection_state['direction']}")
        await aprint(f"----\n<ansigray>Status:</ansigray> {connection_state['status']}\n<ansigray>Target:</ansigray> @<ansiyellow>{connection_state['target']}</ansiyellow>\n<ansigray>Direction:</ansigray> {connection_state['direction']}\n----")

async def cmd_list_users(_:str):
    """
    Lists all the users connected along with you to the server.
    """
    await active_websocket.send(
        message = make_system_request(need='list_users', username=current_username)
    )
    logger.debug('[cmd_list_users] Sent a request to server for a list of users.')    

# Helper for task logging (to make sonarQube happy)
async def wait_and_log_task(task: asyncio.Task, context: str):
    """Wait for a task and log any exception"""

    try:
        await task
    except Exception as e:
        logger.error(f"[{context}] Task failed: {e}")

# Register additional commands
command_handler.register_command("/connect", cmd_connect)
command_handler.register_command("/accept", cmd_accept)
command_handler.register_command("/deny", cmd_deny)
command_handler.register_command("/exit_tunnel", cmd_exit_tunnel)
command_handler.register_command("/pending", cmd_pending)
command_handler.register_command("/list_users", cmd_list_users)

# ========================== #
# Messaging
# ========================== #

async def handle_chat_input(message: str, websocket: websockets.ClientConnection, username: str, session_key: bytes):
    
    # Handle custom commands
    if message.strip().startswith("/"):
        
        if command_handler.has_command(message):
            # Execute the command using the command handler
            try:
                await command_handler.execute_command(message)

            except asyncio.CancelledError:
                # If the command raises a CancelledError, we handle it here
                logger.debug("[send_messages] Command execution cancelled. Exiting message loop.")
                
                # This exception is raised when the /exit is processed and confirmed from the send_messages() 
                # which raises and propogates `exception of the same` up-ward towards the event loop 
                # alerting any other tasks that catches this exception to handle the cancelling.
                # Even if any of the tasks miss this signal, there is a preventative measure to cancel all the tasks in the main method                        
                raise

            except Exception as e:
                # If any other exception occurs during command execution, log it
                logger.error(f"[send_messages] Error executing command '{message}': {e}")                   

        # If the command is not recognized, we log a warning
        else:
            
            logger.debug(f"[send_messages] Command '{message}' not recognized. Use /help to see available commands.")
            await aprint(f"----\n<ansired>?</ansired> <ansigray>Command</ansigray> `<ansired>{message}</ansired>` <ansigray>not recognized\nUse</ansigray> <ansicyan>/help</ansicyan> <ansigray>to see available commands.</ansigray>\n----")
    
    # Send the message if everything is fine
    else:
        if not session_key:
            encoded = encode_message(message=message, sender=username)
            await websocket.send(encoded)
        elif session_key:
            encoded = encode_message(message=message, sender=username, type='encrypted_message', session_key=session_key, target=connection_state['target'])
            await websocket.send(encoded)

async def send_messages(websocket: websockets.ClientConnection, username: str):
    """ 
    Handles sending messages through the websocket.
    
    This coroutine runs as a task and handles user input in a loop.
    If the user types `/exit`, it raises a `CancelledError` to signal shutdown
    to the event loop and other concurrent tasks.
    """
    global input_future
    previous_mode = None

    while True:
        try:
            if input_mode != previous_mode:
                
                logger.debug(f"[send_messages] Mode changed: {previous_mode} → {input_mode}")
                await aprint(f"...\nMode changed: {previous_mode} → {input_mode}\n...")
                
                previous_mode = input_mode
                set_input_mode(input_mode)

            # If we are in PSK input mode, reroute the input
            if input_mode == "psk":
                # Only prompt once
                if input_future and not input_future.done():
                    message = await safe_input(prompt='🔐 Enter PSK: ', password=True, color='ansiyellow')
                    input_future.set_result(message)
                set_input_mode('locked')

                continue
            
            elif input_mode in ('chat', 'encrypted'):
                message = await safe_input(prompt=f"Enter {input_mode} message: ", color="ansibrightmagenta")
                
                # If the message is empty, we skip sending it
                if message:
                    if message.strip() == "":
                        
                        logger.debug("[send_messages] Empty message entered. Skipping send.")
                        await aprint("----\n<ansigray>Empty message entered. Skipping send.</ansigray>")

                    else:
                        if input_mode == 'chat':
                            await handle_chat_input(message=message,websocket=websocket, username=username, session_key=None)
                        
                        elif input_mode == 'encrypted':
                            session_key = tunnel_utils.get_session_key()
                            
                            if session_key:
                                await handle_chat_input(message=message, websocket=websocket, username=username, session_key=session_key)
                            
                            else:
                                
                                logger.debug('[send_messages] No session key, switching input mode to chat')
                                set_input_mode('chat')
            
            elif input_mode == "locked":
                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            # This exception occurs when the user presses Ctrl+C
            # This exception caught here is raised from the safe_input() method
            # which is used to handle asynchronous input without blocking the event loop.
            # It is caught here to prevent the event loop from crashing and to allow graceful shutdown.
            # We log a warning and break the loop to exit gracefully.
            # This is a good place to handle any cleanup or final messages before exiting.
            # This is also caught in the main method to handle the cancellation of tasks.
                        
            logger.debug("[send_messages] Keyboard interrupt detected. Exiting message loop.")
            break

        except asyncio.CancelledError:
            logger.debug("[send_messages] Task cancelled cleanly.")
            raise

        except websockets.exceptions.ConnectionClosed:
            # This exception occurs when the websocket connection is closed from/by the server
            # or if the server is not running.
            
            logger.debug("[send_messages] Websocket connection closed from/by server.")
            await aprint("----\n<ansired>!</ansired> <ansigray>Connection Closed From/By Server</ansigray>\n----")
            
            return

        except Exception as e:
            logger.error(f"[send_messages] Exception: {e}")

async def receive_messages(websocket: websockets.ClientConnection):
    """ Handles receiving and decoding messages from the websocket server. """
    global input_mode

    while True:

        try:
            message = await websocket.recv()
            decoded = decode_message(message_str=str(message), session_key=tunnel_utils.get_session_key())
            msg_type = decoded.get("type")

            # ==========================
            # Handle Connection Events
            # ==========================
            if msg_type == "connect_request":
                peer = decoded.get("sender")
                if connection_state["status"] == 'idle':
                    
                    logger.debug(f"[receive_messages] Incoming connection request from @{peer}. Use /accept or /deny.")
                    await aprint(f"----\n<ansigray>Incoming connection request from @</ansigray><ansiyellow>{peer}</ansiyellow>\n<ansigray>Use</ansigray> <ansicyan>/accept</ansicyan> or <ansicyan>/deny</ansicyan>\n----")

                    connection_state.update({
                        "status": "request_received", 
                        "target": peer, 
                        "direction": "incoming",
                        })

                else:
                    await websocket.send(
                        encode_message(
                            type='connect_busy',
                            sender=current_username,
                            target=peer,
                            message='connect_busy',
                        )
                    )
            
            elif msg_type in ('connect_busy', 'connect_error'):
                peer = decoded.get("sender")
                message = decoded.get("message")
                await aprint(f"----\n<ansiyellow>{peer}</ansiyellow>: <ansigray>{message}</ansigray>\n----")
                await reset_connection_state()

            elif msg_type == "connect_accept":
                peer = decoded.get("sender")
                
                logger.debug(f"[receive_messages] @{peer} accepted your connection request.")
                await aprint(f"----\n<ansigray>Connection request accepted by @</ansigray> <ansiyellow>{peer}</ansiyellow>\n----")

                connection_state["status"] = "wait_tunnel_trigger"

            elif msg_type == "connect_deny":
                peer = decoded.get("sender")
                
                logger.debug(f"[receive_messages] @{peer} denied your connection request.")
                await aprint(f"----\n<ansigray>Connection request denied by @</ansigray> <ansiyellow>{peer}</ansiyellow>\n----")
                
                await reset_connection_state()
            
            # ==========================
            # Tunnel Validation Events
            # ==========================
            
            elif msg_type == 'tunnel_validate':
                # Start PSK validation prompt for the initiator
                peer = decoded.get("sender")
                
                logger.debug("[receive_messages.tunnel_validate] Triggering tunnel validation.")
                await aprint("----\n<ansiblue>!</ansiblue> <ansigray>Triggering Tunnel Validation</ansigray>\n----")

                task = asyncio.create_task(start_tunnel_validation(peer=str(peer)))
                psk_entry = await task
                
                if not psk_entry:
                    await reset_connection_state()

            elif msg_type == "tunnel_ok_key_init":
                peer = connection_state['target']

                # Server confirms PSK exchange
                logger.debug("[receive_messages.tunnel_ok_key_init] Tunnel PSK confirmed. Invoking key share.\n")
                await aprint("----\n<ansigreen>!</ansigreen> <ansigray>Tunnel PSK confirmed\nInvoking key share</ansigray>\n----")

                connection_state["status"] = "tunnel_active"
                input_mode = "chat"

                # Invoke the helper method to establish changes like generating
                # key pair and sharing public key in accordance of the active tunnel.
                logger.debug('[receive_messages.tunnel_established] Utilizing TunnelActivityUtilsForOG, Generating Key Pair, Sending public key to peer')
                
                task = asyncio.create_task(tunnel_utils.handle_key_share(target=str(peer), username=current_username, websocket=active_websocket))
                await task

            elif msg_type == "tunnel_failed":
                
                logger.debug("[receive_messages] Tunnel validation failed. PSK mismatch.")
                await aprint("<ansibrightred>----</ansibrightred>\n<ansired>!</ansired> Tunnel validation failed\n<ansired>Bye Bye !</ansired>\n<ansibrightred>----</ansibrightred>")
                
                await reset_connection_state()
                input_mode = "chat"
            
            # ========================== 
            # Tunnel Core Events
            # ========================== 
            elif msg_type == client_event_types['KEY_SHARE']:
                sender = decoded.get('sender')
                encoded_public_key = decoded.get('key')
                if connection_state.get('target') == sender:
                    tunnel_utils.set_peer_public_key(encoded_peer_public_key=encoded_public_key)
                    
                    logger.debug(f"[receive_messages] Received Public Key from @{sender}")
                    await aprint(f"----\n<ansigreen>!</ansigreen> <ansigray>Received Public Key from @</ansigray><ansiyellow>{sender}</ansiyellow>\n----")

                    # invoke handler for session secret
                    if tunnel_utils.get_peer_public_key_bytes():
                        tunnel_utils.handle_shared_secret()

                    # Also invoke handler for session_secret
                    if tunnel_utils.get_peer_public_key_bytes() and tunnel_utils.get_psk_hash():
                        tunnel_utils.handle_session_secret()
                    
                    # Now, Introduce a new chat mode. Call it `encrypted`. Add support in send_messages for the new chat state.
                    set_input_mode('encrypted')
            
            elif msg_type == client_event_types['ENCRYPTED_MESSAGE']:
                
                logger.debug(f'[receive_messages.encrypted_message] Received message: {decoded}')
                
                readable_timestamp = datetime.fromisoformat(decoded.get('timestamp'))
                sender = decoded.get('sender','unknown')
                text = decoded.get('message','')
                _type = decoded.get('type','')
                
                await aprint(f"\n[{readable_timestamp}] [{_type}] <ansiyellow>{sender}</ansiyellow>: {text}")                

            # ========================== 
            # Tunnel Exit Event
            # ========================== 

            elif msg_type == "tunnel_exit":
                
                logger.debug(f"[receive_messages] {decoded.get('message')}")
                await aprint(f"---\n{decoded.get('message')}\n---")
                
                await reset_connection_state()
                await tunnel_utils.reset()
                set_input_mode('chat')

            # ========================== 
            # System Request and Response Events
            # ==========================
            elif msg_type == client_event_types['SYSTEM_RESPONSE']:
                readable_timestamp = datetime.fromisoformat(decoded['timestamp'] if decoded['timestamp'] != '???' else '???')
                sender = decoded.get('sender')
                res_obj = decoded.get('res_info')
                formatted_list = None

                if res_obj:
                    formatted_list = ['<ansiyellow>' + name + '</ansiyellow>' for name in res_obj]
                
                logger.debug(f'[receive_messages.system_response.list_users] [{readable_timestamp}] {sender}: {res_obj}, type:{type(res_obj)}')
                await aprint(f'{sender}: {formatted_list}')

            # ========================== 
            # Disconnection Event
            # ========================== 
            
            elif msg_type == "user_disconnected":
                user = decoded.get("username")
                
                logger.debug(f"[receive_messages] User @{user} disconnected.")
                await aprint(f"----\n@<ansiyellow>{user}</ansiyellow> <ansigray>disconnected</ansigray>\n----")
                
                if connection_state.get("target") == user:
                    await reset_connection_state()
                    await tunnel_utils.reset()
                    set_input_mode('chat')

            # ==========================
            # Normal Broadcast/Chat Messages
            # ========================== 
            else:
                timestamp = decoded.get("timestamp", "???")
                readable_timestamp = datetime.fromisoformat(timestamp) if timestamp != '???' else '???'
                sender = decoded.get("sender", "unknown")
                text = decoded.get("message", "")
                await aprint(f"\n[{readable_timestamp}] <ansiyellow>{sender}</ansiyellow>: {text}")

        except websockets.exceptions.ConnectionClosed:
            # This exception occurs when a keyboard interrupt is experienced 
            # which first interrupts the event_loop where the websocket connection is 
            # terminated and as a side effect this exception is recognised.
            
            logger.debug("[receive_messages] Websocket connection closed from/by server")
            await aprint("----\n<ansired>!</ansired> <ansigray>Connection Closed From/By Server</ansigray>\n----")
            return

        except asyncio.CancelledError:
            # When this task detects the propogation of cancellation signal in the event loop.

            logger.debug("[receive_messages] Task received cancellation signal.")
            raise

        except Exception as e:
            logger.error(f"[receive_messages] Unexpected error: {e}")

# ========================== #
# Username Registration
# ========================== #

# Utility method to ask for the username
async def ask_for_username() -> str:
    """ 
    Asks the user for their username until a non-empty value is provided.
    
    This function is used to ensure that the user provides a valid username before connecting to the server.
    It will keep prompting the user until they enter a non-empty username.
    """
    logger.info("[ask_for_username] Prompting user for a username.")

    # Loop until a valid username is provided
    # This will keep asking the user for a username until they provide a valid one
    while True:
        username = await safe_input("\n Enter your username: ")
        if username.strip():
            return username.strip()
        else:
            
            logger.debug("[ask_for_username] Username cannot be empty. Please try again.")
            await aprint("----\n<ansired>!</ansired> Username cannot be empty\nPlease try again\n----")


async def handle_username_registration(websocket) -> str | None:
    """Handle timed username registration with retries and feedback from the server"""
    TIMEOUT = 10
    MAX_ATTEMPTS = 4
    INTERRUPT_SENTINEL = "<INTERRUPTED>"
    attempts = 0
    start_time = asyncio.get_event_loop().time()

    async def safe_username_input() -> str | None:
        """ A exception handling wrapper for safe input used only for handle_username_registration as there is traceback occurring with KeyboardInterrupt when safe_input is declared as a task to prompt for username """
        try:
            return await safe_input(prompt='Enter Username: ', color='ansiyellow')
        except KeyboardInterrupt:
            
            logger.debug("[handle_username_registration] Suppressed KeyboardInterrupt *inside* safe_username_input.")
            
            # Return a Sentinel Value (object or str)
            return INTERRUPT_SENTINEL
    
    while True:
        time_left = TIMEOUT - (asyncio.get_event_loop().time() - start_time)
        if time_left <= 0:
            await aprint("\n⏰ Time expired! You took too long to register.")
            return None
        
        await aprint(f"\n🔐 Username Attempt (Attempts left: {MAX_ATTEMPTS - attempts}, Time left: {int(time_left)}s):")
        
        try:
            username_task = asyncio.create_task(safe_username_input())
            timer_task = asyncio.create_task(asyncio.sleep(time_left))
            
           
            done, _ = await asyncio.wait(
                [username_task, timer_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            if timer_task in done:
                username_task.cancel()
                await asyncio.gather(username_task, return_exceptions=True)                
                
                logger.debug("[handle_username_registration] Time expired waiting for input")
                await aprint("----\n<ansired>!</ansired> Time expired waiting for input\n----")
                
                return None
            
            username_input = await username_task
           
            if username_input == INTERRUPT_SENTINEL:
                
                logger.debug("[handle_username_registration] KeyboardInterrupt detected from input task. Exiting registration.")
                await aprint("----\n<ansired>!</ansired>KeyboardInterrupt\nExiting registration\n----")
                
                return None
            
            username = (username_input or "").split()[0] if username_input else ""

            logger.debug(msg=f"[handle_username_registration] username from task result: {username}")
            
            if not username:
                
                logger.debug("❗Username cannot be empty. Try better bro...😑")
                await aprint("----\n<ansired>!</ansired> Username cannot be empty\nTry better bro...😑\n----")
                
                continue

            await websocket.send(make_register_message(username=username)) #type: ignore

            # Wait for the server response with remaining time
            remaining = TIMEOUT - (asyncio.get_event_loop().time() - start_time)
            if remaining <= 0:
                await aprint("----\n⏰ Time expired waiting for server response\n----")
                return None

            response = await asyncio.wait_for(websocket.recv(), timeout=time_left)
            decoded = decode_message(response)

            if decoded["type"] == "user_disconnected":
                
                logger.debug(f"User @{decoded['username']} has disconnected.")
                await aprint(f"----\nUser @<ansiyellow>{decoded['username']}</ansiyellow> has disconnected\n----")

                # Optionally: clear connection_state if this was our peer
                if connection_state["target"] == decoded["username"]:
                    connection_state["status"] = "idle"
                    connection_state["target"] = None
                    connection_state["direction"] = None
                continue

            if decoded["type"] == "register":
                
                logger.debug(f"[handle_username_registration] Received confirmation from the server. Welcome `{username}`!")
                await aprint(f"----\n<ansigray>Confirmation received\nWelcome</ansigray>`<ansiyellow>{username}</ansiyellow>`!----\n")
                
                return username #type: ignore

            elif decoded["type"] == "register_error":
                await aprint(f"----\n<ansired>!</ansired> {decoded['message']}\n----")

                # Only increment attempts for format errors
                if "Invalid username" in decoded["message"]:
                    attempts += 1
                if attempts >= MAX_ATTEMPTS:
                    await aprint("----\n⚠️ Maximum attempts reached\n<ansired>Exiting</ansired>\n----")
                    return None

        except asyncio.CancelledError:
            return None
        except asyncio.TimeoutError:
            
            logger.debug("\n🥚 Timeout waiting for server response.")
            await aprint("----\n🥚 Timeout waiting for server response\n----")
            
            return None
        except (KeyboardInterrupt, EOFError):
            
            logger.info("\n Username Registration Cancelled via Keyboard Interrupt")
            await aprint("----\n<ansired>!</ansired> Username Registration Cancelled via Keyboard Interrupt\n----")
            
            return None
        except Exception as e:
            logger.error(f"\n Unexpected error: {e}")
            return None


# Utility method to parse the arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description="Oldie-Goldie's original client. Tightly integrated with Oldie-Goldie's secure server.  To serve, run: python -m client.chat --server-host {local|public}",
        epilog=(
        "Example:\n"
        "  python myscript.py --token=-sdLr8H8FWy5fHq7lMW52A\n"
        "  python myscript.py --token -- -sdLr8H8FWy5fHq7lMW52A\n\n"
        "Note: Use '--' to safely pass arguments that begin with '-'."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,  # keeps formatting & newlines
    )

    parser.add_argument('--server-host', choices=['local','public'], required=True, help="Server type: 'local' or 'public'")
    parser.add_argument('--server-port', type=int, default=8765, help='Port to connect to (default: 8765)')
    parser.add_argument('--url', help='Public Websocket URL (required if --server-host=public)')
    parser.add_argument('--token', help="Authorization token (optional). Required if it is a protected server. Find out with the server provider. If it starts with '-', prefix it with '--' or use '=' syntax.")

    # 👇 Add version flag
    try:
        pkg_version = version("oldie-goldie")
    except PackageNotFoundError:
        pkg_version = "0.0.0-dev"
    
    parser.add_argument("--version", action="version", version=f"Oldie Goldie {pkg_version}")

    args = parser.parse_args()

    # --- validation ---
    if args.server_host == "public" and not args.url:
        parser.error('--url is required when --server-host=public')

    return args


# ========================== #
# Main
# ========================== #
async def main():
    """ Main event loop handling input/output task coordination and handle the following tasks:
    1. send_messages
    2. receive_messages
    """

    # Get the command line args
    args = parse_args()

    # --- build the connection url ---
    if args.server_host == 'local':
        uri=f"ws://localhost:{args.server_port}"
    else:
        uri = args.url.strip()
        
        # auto convert https:// -> wss:// (and http:// -> ws://)
        if uri.startswith('https://'):
            uri = 'wss://' + uri[len('https://'):]
        elif uri.startswith('http://'):
            uri = 'ws://' + uri[len('http://'):]
    
    # --- prepare headers if token is given ---
    headers = [('Authorization', args.token)] if args.token else None
    # if args.token:
    #     headers['Authorization'] = args.token

    # Welcome banner
    await aprint(version_banner(app_name='Client'))
    global active_websocket, current_username

    if headers:
        
        logger.debug(f"[main] Using Authorization header: {args.token[:6]}...")
        await aprint(f"----\nUsing Authorization header: {args.token[:6]}...\n----")
        
    
    # Connect to the websocket server via async context manager
    async with websockets.connect(uri, additional_headers=headers) as websocket:
        
        # Log the connection to the server
        logger.debug(f"Connected to secure chat websocket server at {uri}, Beginning username registration...")
        await aprint(f"----\n<ansigreen>!!</ansigreen> Connected to secure chat websocket server at {uri}\nBeginning username registration...\n----")

        active_websocket = websocket
        
        username = await handle_username_registration(websocket=websocket)
        
        if username is None:
            
            logger.debug("[main] Username registration failed or cancelled.")
            raise asyncio.CancelledError # Gracefully exit
        
        current_username = username
        
        # Now continue as before
        tasks = [
            asyncio.create_task(send_messages(websocket=websocket, username=username)),
            asyncio.create_task(receive_messages(websocket=websocket))
            ]

        try:

            # Process the tasks by waiting them accordingly
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel other tasks that did not finish
            for task in pending:                
                task.cancel()
                
                try:
                    await task
                    
                except asyncio.CancelledError:
                    logger.debug(f"[main] Cancelled pending task: {task.get_coro().__name__}")  # type: ignore    
            
            # Get the exceptions of tasks which have not been handled appropriately 
            for task in done:
                if task.exception():
                    logger.error(f"[main] Exception from task {task.get_coro().__name__} raised: {task.exception()}") # type: ignore 
                    raise task.exception() # type: ignore
                
        except asyncio.CancelledError:
            logger.debug("[main] Main task cancelled.")
            raise

        except websockets.exceptions.ConnectionClosed:
            
            logger.debug("[main] Server closed the connection. Press 'Enter' to finish exiting")
            await aprint("----\n<ansired>!!</ansired>Server closed the connection\nPress 'Enter' to finish exiting\n----")
            
            raise

        finally:
            logger.debug("[main] All tasks completed or cancelled. The app will exit automatically. If the input seems to be blocked then press 'Enter' to finish exiting. Thanks for using Secure Chat Client :)")
            await aprint("<ansigreen>----</ansigreen>\nAll tasks completed or cancelled\nThe app will exit automatically\nIf the input seems to be blocked then press 'Enter' to finish exiting\nThanks for using <ansigreen>Oldie Goldie</ansigreen> Client :)\n<ansigreen>----</ansigreen>")


if __name__ == "__main__":
    """ Run the event loop / manager. Entry point for chat client. """
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        logger.warning("[root] Keyboard interrupt detected. Client shutting down :(")
    except ConnectionRefusedError:
        logger.error("[root] Connection refused - server may be offline :(")
    except asyncio.CancelledError:
        logger.info("[root] Shutdown handled via cancellation.")
    except websockets.exceptions.ConnectionClosed:
        logger.info("[root] Connection Sucessfully Closed.")
    except websockets.exceptions.InvalidStatus:
        logger.info("[root] Invalid Auth Token")
    except websockets.exceptions.InvalidURI:
        logger.error("[root] Invalid URI. Please check the url passed via --url argument. URI Scheme should be of either wss or wss or http or https.")

def cli():
    """Entry point for 'og-client' command."""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        logger.warning("[root] Keyboard interrupt detected. Client shutting down :(")
    except ConnectionRefusedError:
        logger.error("[root] Connection refused - server may be offline :(")
    except asyncio.CancelledError:
        logger.info("[root] Shutdown handled via cancellation.")
    except websockets.exceptions.ConnectionClosed:
        logger.info("[root] Connection Sucessfully Closed.")
    except websockets.exceptions.InvalidStatus:
        logger.info("[root] Invalid Auth Token or Server Is Offline")
    except websockets.exceptions.InvalidURI:
        logger.error("[root] Invalid URI. Please check the url passed via --url argument. URI Scheme should be of either wss or wss or http or https.")
