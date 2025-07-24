import asyncio
import websockets
import websockets.legacy.server
import logging
from shared import encode_message, decode_message, make_register_message, make_connect_request, make_connect_response, make_user_disconnected_message, make_system_notification
from shared import BANNER
# Logging configuration and setup
# This will log messages to the console with a specific format
# You can change the logging level
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create a logger for this module
# This allows us to log messages specific to this module
logger = logging.getLogger(__name__)

# This will hold all connected clients' websockets
# The keys are usernames and the values are the respective websocket connections
# This allows us to keep track of connected users and their respective websockets
user_registry_by_id: dict[str, websockets.legacy.server.WebSocketServerProtocol] = {}

# This will hold the mapping of websockets to usernames
# This allows us to quickly find the username associated with a given websocket connection
user_registry_by_websocket: dict[websockets.legacy.server.WebSocketServerProtocol, str] = {}

def is_valid_username_format(username: str) -> tuple[bool, str]:
    """Validates the format of the username and returns a tuple of (is_valid, reason)"""
    reserved_keywords = {
        "None", "True", "False", "and", "or", "not", "if", "else", "elif", "while", "for", "in", "def", "class", "import", "from", "as", "return", "break", "continue"
    }

    if not username:
        return False, "Username is required."
    if not isinstance(username, str):
        return False, "Username is not a string."
    if not username.islower():
        return False, "Username must only contain lowercase alphabetical characters and/or numerical characters."
    if not username[0].isalpha():
        return False, "Username must start with a letter."
    if not username.isalnum():
        return False, "Username must be either alphabetic or alphanumeric."
    if len(username) > 50:
        return False, "Username must be no longer than 50 characters."
    if username in reserved_keywords:
        return False, "Username is a reserved keyword."
    if username == "server":
        return False, "Username 'server' is not for you bro 😤"
    return True, ""

async def handle_registration(websocket) -> str | None:
    TIMEOUT = 10
    MAX_ATTEMPTS = 4
    attempts = 0
    start_time = asyncio.get_event_loop().time()

    while True:
        time_left = TIMEOUT - (asyncio.get_event_loop().time() - start_time)
        if time_left <=0:
            await websocket.send(encode_message(
                type="register_error",
                sender="Server",
                message="⏰ Time expired bruh! You didn't register in time. Connection will be closed.\n Try again sooner this time 👍"
            ))
            await websocket.close()
            return None
        
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=time_left)
            decoded = decode_message(message)
            if decoded.get("type") != "register" or "username" not in decoded or not decoded.get("username"):
                await websocket.send(encode_message(
                    type="register_error",
                    sender="Server",
                    message="❌ Invalid registration format. Must send a 'register' message with 'username'."
                ))
                attempts += 1
            else:
                username = decoded["username"].strip()
                is_valid, reason = is_valid_username_format(username=username)
                if not is_valid:
                    attempts += 1
                    if attempts >= MAX_ATTEMPTS:
                        await websocket.send(encode_message(
                            type="register_error",
                            sender="Server",
                            message=f"❌ Invalid username: {reason}\n⚠️ Maximum attempts reached. Disconnecting."
                        ))
                        await websocket.close()
                        return None
                    await websocket.send(encode_message(
                        type="register_error",
                        sender="Server",
                        message=f"❌ Invalid username: {reason}\n🔁 Attempts remaining: {MAX_ATTEMPTS - attempts}"
                    ))
                elif username in user_registry_by_id:
                    await websocket.send(encode_message(
                        type="register_error",
                        sender="Server",
                        message=f"⚠️ Username '{username}' is already taken. Try another.\n⌛ Time left: {int(time_left)}s"
                    ))
                else:
                    return username # ✅ Success
        except asyncio.TimeoutError:
            await websocket.send(encode_message(
                type="register_error",
                sender="Server",
                message="🥚 Timeout waiting for username. Connection closing."
            ))
            await websocket.close()
            return None
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("[handle_registration] Registration cancelled from user's side")
            return None
        except Exception as e:
            logger.exception(f"Error during registration: {e}")
            await websocket.send(encode_message(
                type="register_error",
                sender="Server",
                message="❌ Unexpected error occurred. Try again later."
            ))
            await websocket.close()
            return None


async def broadcast(websocket:websockets.legacy.server.WebSocketServerProtocol, user_reg_id:dict[str, websockets.legacy.server.WebSocketServerProtocol], user_reg_web:dict[websockets.legacy.server.WebSocketServerProtocol, str]) -> None:
    try:
        async for message in websocket:            
            # Broadcast the message to all connected clients
            broadcast_to = list(user_reg_web.values())
            broadcast_to.remove(user_reg_web[websocket])
            logger.info(f"[broadcast] Received message from {user_reg_web.get(websocket)}. Broadcasting to these users:\n[{broadcast_to}]")
            
            for client_ws in user_reg_id.values():
                if client_ws != websocket:
                    await client_ws.send(message)
        return None
    except websockets.exceptions.ConnectionClosed:
        pass


async def handler(websocket):
    """Handles incoming websocket connections and registration of users."""

    try:
        # Receive the initial (register) message from the client
        # This is expected to be a registration message containing the username
        logger.info("[handler] Starting registration phase...")
        username = await handle_registration(websocket=websocket)
        
        if username is None:
            logger.info("[handler] Registration failed or timed out")
            return

        # Register the user in the user registry
        logger.info(f"[handler] Registering user '{username}' with websocket {websocket}")

        # Store the websocket connection in the user registry
        # This allows us to keep track of connected users and their respective websockets
        user_registry_by_id[username] = websocket

        # Store the username in the user registry by websocket
        # This allows us to quickly find the username associated with a given websocket connection
        user_registry_by_websocket[websocket] = username

        # Log the registration
        logger.info(f"[handler] [+] User '{username}' has been registered with {websocket}")
        
        # Send a confirmation message back to the client
        confirmation_message = make_register_message(username=username)
        await websocket.send(confirmation_message)
    
    except websockets.exceptions.ConnectionClosedOK:
        logger.warning("[handler] [!] Connection closed from client while registration")
        return

    except Exception as e:
        # If any error occurs during the registration process, log the error and close the connection
        logger.error(f"[handler] [!] Error during registration: {e}")
        error_message = encode_message(message="An error occurred during registration. Please try again later.", sender="Server")
        await websocket.send(error_message)
        await websocket.close()
        return

    try:

        await broadcast(
            websocket=websocket,
            user_reg_id=user_registry_by_id,
            user_reg_web=user_registry_by_websocket
        )  
    
    except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK) as e:
        # Handle the case where the connection is closed unexpectedly
        logger.error(f"[handler] [!] Connection closed unexpectedly for user '{user_registry_by_websocket.get(websocket)}'. Error: {e}")

    finally:
        # find which user is disconnecting
        username = user_registry_by_websocket.get(websocket)

        # Remove the user from the user registry
        if username in user_registry_by_id:
            del user_registry_by_id[username]
            del user_registry_by_websocket[websocket]
            logger.info(f"[handler] [-] User '{username}' has been removed from the registry.")
        
        # Notify all connected clients about the disconnection
        disconnect_message = make_user_disconnected_message(username=username) # type: ignore
        logger.info(f"[handler] [!] User '{username}' has disconnected. Sending disconnection message to all clients.")
        print('user_registry_update: ', user_registry_by_id)      
        
        # Send the disconnection message to all connected clients
        # This informs all other clients that the user has disconnected        
        for client_ws in user_registry_by_id.values():
            
            try:
                await client_ws.send(disconnect_message)
            
            except websockets.exceptions.ConnectionClosedError:
                # If the client is already disconnected, we can ignore this error
                logger.info(f"[handler] [!] Client {client_ws} is already disconnected.")


async def main():
    # welcome banner
    print('server\n', BANNER)
    async with websockets.serve(handler, "0.0.0.0", 8765):

        await asyncio.Future() # Run Forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("[__main__] KeyboardInterrupt received. Server shutting down.")
