import asyncio
import websockets
import logging
from shared.protocol import encode_message, decode_message

# Importing the CommandHandler class from shared.command_handler module
# This class is responsible for managing commands and their execution in the chat client.
from shared.command_handler import CommandHandler

# Importing the async input utility function and async print utility function
# These functions are used to handle asynchronous input and output in the chat client.
from utilities import get_async_input, get_async_print

# Importing ainput from the utility module
# This utility function is used to handle asynchronous input without blocking the event loop.
ainput = get_async_input()

# Importing aprint from the utility module
# This utility function is used to handle asynchronous output without blocking the event loop.
aprint = get_async_print()

# === Configuration === #
SERVER_URI = "ws://localhost:8765"

logging.basicConfig(
    level=logging.INFO,
    format= "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
    )
logger = logging.getLogger(__name__)
# ===================== #

# Importing the command handler for managing commands
command_handler = CommandHandler()



# Helper method for confirming exit
# Async input for confirmation (still works fine with ainput)
async def confirm_exit() -> bool:
    """ Prompt the user to confirm if they really want to exit """

    while True:
        response = await ainput("\n Confirm your will to exit (y/n) ")
        response = response.strip().lower()
        if response == "y":
            return True
        elif response == "n":
            logger.info(msg="[confirm_exit] Resuming chat. User decided not to exit.")
            return False
        else:
            logger.warning("You have to enter something [y/n]. come on -_-")

async def safe_input(prompt: str = "> ") -> str:
    """ Safe input wrapper with exception handling for keyboard interrupts and EOF errors as well as natively async input handling so to not block the event loop which happens when we use conventional input which is blocking in nature. (eliminates the need for spawning threads)\n
    This function is a wrapper around the ainput function from aioconsole, which allows for asynchronous input handling.\n
    If a KeyboardInterrupt or EOFError occurs, it logs a warning and raises a KeyboardInterrupt to signal the user that input was interrupted.

    Args:
        prompt (str): The prompt to display to the user for input. Defaults to an empty string.
    
    Returns:
        str: The user input as a string.
    
    Raises:
        KeyboardInterrupt: If the user interrupts the input with Ctrl+C or EOF is detected.
    """

    try:
        return await ainput(prompt)
    
    except (KeyboardInterrupt, EOFError):
        logger.warning(" [safe_input] keyboard interrupt or EOF detected")
        raise KeyboardInterrupt("Input interrupted by user or EOF detected. Exiting input loop.")

# Registering commands with the command handler
# This allows the chat client to recognize and execute commands like /help, /exit, etc
# Register built-in commands
async def cmd_exit(_: str):
    """ Command to exit the chat client """
    logger.info("[cmd_exit] User requested exit command.")
    should_exit = await confirm_exit()
    
    if should_exit:
        logger.info("[cmd_exit] User confirmed exit. Raising CancelledError to signal shutdown.")
        raise asyncio.CancelledError
    else:
        logger.info("[cmd_exit] User chose not to exit. Resuming chat.")

async def cmd_help(_: str):
    """ Command to display help information """
    help_text = (
        "\nAvailable commands:\n"
        "/help - Show this help message\n"
        "/exit - Exit the chat client\n"
        "Type your message and press Enter to send it.\n"
    )
    await aprint(help_text)

command_handler.register_command("/exit", cmd_exit)
command_handler.register_command("/help", cmd_help)
# More can be registered like '/connect', 'whoami', etc. as needed

# ========================== #
# 💬Connection State Logic   #
# ========================== #

# This section handles the connection state logic for the chat client.

connection_state = {
    "status": "idle",   # idle, waiting, requested
    "target": None,     # Who we are talking to or requesting
    "direction": None,  # incoming or outgoing
}

async def cmd_connect(line: str):
    """ Initiate a connection request to another user """

    parts = line.strip().split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        await aprint("Usage: /connect @username")
        return
    
    target_username = parts[1][1:]  # Remove the '@' symbol
    if target_username == "":
        await aprint("Invalid username. Please provide a valid username starting with '@'.")
        return
    if connection_state["status"] != "idle":
        await aprint("⚠️  You are already in a pending connection request. Use /deny to cancel it or /accept if it's incoming.\n Hint: Use /pending to check your current connection state.")
        return
    
    # Simulate sending a connection request
    connection_state["status"] = "waiting"
    connection_state["target"] = target_username
    connection_state["direction"] = "outgoing"

    await aprint(f"📡 Connection request sent to @{target_username}. Waiting for them to /accept or /deny...")
    # (Server interaction would go here, e.g., sending a control message to the server)

async def cmd_accept(_: str):
    """ Accept a pending incoming connection request """
    if connection_state["status"] != "requested" or connection_state["direction"] != "incoming":
        await aprint("❌  No incoming connection request to accept. Use /connect to initiate a new one.")
        return
    
    target_username = connection_state["target"]
    await aprint(f"✅  Connection request with @{target_username} accepted. 🔐  Handshake to be initiated...")

    # Simulate entering secure tunnel (add handshake Logic later)
    connection_state["status"] = "idle"
    connection_state["target"] = None
    connection_state["direction"] = None

async def cmd_deny(_: str):
    """ Deny a pending incoming/outgoing connection """
    if connection_state["status"] not in ("waiting", "requested"):
        await aprint("❌ No connection request to deny or cancel.")
        return

    who = connection_state["target"]
    if connection_state["direction"] == "incoming":
        await aprint(f"🚫  You denied the connection request from @{who}.")
    else:
        await aprint(f"🚫  You cancelled the connection request to @{who}.")
    
    # Reset connection state
    connection_state["status"] = "idle"
    connection_state["target"] = None
    connection_state["direction"] = None

async def cmd_pending(_: str):
    """ Check the current connection state """
    if connection_state["status"] == "idle":
        await aprint("No pending connections.")
    else:
        status = connection_state["status"]
        target = connection_state["target"]
        direction = connection_state["direction"]
        await aprint(f"Current connection status: {status}, Target: @{target}, Direction: {direction}")

# Registering the connect, accept, and deny commands
command_handler.register_command("/connect", cmd_connect)
command_handler.register_command("/accept", cmd_accept)
command_handler.register_command("/deny", cmd_deny)
command_handler.register_command("/pending", cmd_pending)


async def send_messages(websocket: websockets.ClientConnection, username: str):
    """ 
    Handles sending messages through the websocket.
    
    This coroutine runs as a task and handles user input in a loop.
    If the user types `/exit`, it raises a `CancelledError` to signal shutdown
    to the event loop and other concurrent tasks.
    """

    while True:
        try:
            message = await safe_input()

            # If the message is empty, we skip sending it
            if message.strip() == "":
                logger.info("[send_messages] Empty message entered. Skipping send.")
                continue
            
            # Handle custom commands
            elif message.strip().startswith("/"):
                
                if command_handler.has_command(message):

                    # Execute the command using the command handler
                    try:
                        await command_handler.execute_command(message)

                    except asyncio.CancelledError:
                        # If the command raises a CancelledError, we handle it here
                        
                        logger.info("[send_messages] Command execution cancelled. Exiting message loop.")

                        # This exception is raised when the /exit is processed and confirmed from the send_messages() 
                        # which raises and propogates `exception of the same` up-ward towards the event loop 
                        # alerting any other tasks that catches this exception to handle the cancelling.
                        # Even if any of the tasks miss this signal, there is a preventative measure to cancel all the tasks in the main method                        
                        raise

                    except Exception as e:
                        # If any other exception occurs during command execution, log it
                        
                        logger.error(f"[send_messages] Error executing command '{message}': {e}")                   
                        continue

                else:
                    # If the command is not recognized, we log a warning
                    
                    logger.warning(f"[send_messages] Command '{message}' not recognized. Use /help to see available commands.")
                    continue
            
            # Send the message if everything is fine
            else:
                encoded = encode_message(message=message, sender=username)
                await websocket.send(encoded)

        except KeyboardInterrupt:
            # This exception occurs when the user presses Ctrl+C
            # This exception caught here is raised from the safe_input() method
            # which is used to handle asynchronous input without blocking the event loop.
            # It is caught here to prevent the event loop from crashing and to allow graceful shutdown.
            # We log a warning and break the loop to exit gracefully.
            # This is a good place to handle any cleanup or final messages before exiting.
            # This is also caught in the main method to handle the cancellation of tasks.
                        
            logger.warning("[send_messages] Keyboard interrupt detected. Exiting message loop.")
            break

        except asyncio.CancelledError:
            logger.info("[send_messages] Task cancelled cleanly.")
            raise

        except websockets.exceptions.ConnectionClosed:
            # This exception occurs when the websocket connection is closed from/by the server
            # or if the server is not running.
            
            logger.warning("[send_messages] Websocket connection closed from/by server.")
            return

async def receive_messages(websocket):
    """ Handles receiving and decoding messages from the websocket. """

    while True:

        try:
            message = await websocket.recv()
            decoded = decode_message(message_str=message)
            print(f"\n\n [{decoded['timestamp']}] {decoded['sender']}: {decoded['message']}\n\n> ", end="")

        except websockets.exceptions.ConnectionClosed:
            # This exception occurs when a keyboard interrupt is experienced 
            # which first interrupts the event_loop where the websocket connection is 
            # terminated and as a side effect this exception is recognised.
            
            logger.warning("[receive_messages] Websocket connection closed from/by server")
            return

        except asyncio.CancelledError:
            # When this task detects the propogation of cancellation signal in the event loop.

            logger.info("[receive_messages] Task received cancellation signal.")
            raise

async def main(username: str | None = None):
    """ Main event loop handling input/output task coordination and handle the following tasks:
    1. send_messages
    2. receive_messages
    """

    if username == None:

        # Get the username until the user enters a non-empty value
        while True:
            username = await ainput("\n Enter your username: ")
            if username:
                username = username.strip()
                break
            if not username:
                logger.warning("[main] Username cannot be empty... come on bro! :/")
    
    # Connect to the websocket server via async context manager
    async with websockets.connect(SERVER_URI) as websocket:
        # Send the username to the server
        encoded_username = encode_message(message=username, sender=username)

        logger.info(f"Connected to secure chat websocket server at ws://localhost:8765 as '{username}'")
        send_task = asyncio.create_task(send_messages(websocket, username))
        receive_task = asyncio.create_task(receive_messages(websocket))

        try:

            # Process the tasks by waiting them accordingly
            done, pending = await asyncio.wait(
                [send_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel other tasks that did not finish
            for task in pending:                
                task.cancel()
                
                try:
                    await task
                    
                except asyncio.CancelledError:
                    logger.info(f"[main] Cancelled pending task: {task.get_coro().__name__}")  # type: ignore    
            
            # Get the exceptions of tasks which have not been handled appropriately 
            for task in done:
                if task.exception():
                    logger.error(f"[main] Exception from task {task.get_coro().__name__} raised: {task.exception()}") # type: ignore 
                    raise task.exception() # type: ignore
                
        except asyncio.CancelledError:
            logger.info("[main] Main task cancelled.")
            raise

        except websockets.exceptions.ConnectionClosed:
            logger.warning("[main] Server closed the connection. Press 'Enter' to finish exiting")
            raise

        finally:
            logger.info("[main] All tasks completed or cancelled. The app will exit automatically if not press 'Enter' to finish exiting. Thanks for using Secure Chat Client :)")


if __name__ == "__main__":
    """ Run the event loop / manager. Entry point for chat client. """
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("[root] Keyboard interrupt detected. Client shutting down :(")
    except ConnectionRefusedError:
        logger.error("[root] Connection refused - server may be offline :(")
    except asyncio.CancelledError:
        logger.info("[root] Shutdown handled via cancellation.")
    except websockets.exceptions.ConnectionClosed:
        logger.info("[root] Connection Sucessfully Closed.")
    