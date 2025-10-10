import asyncio
import websockets
import websockets.legacy.server
from websockets.legacy.server import WebSocketServerProtocol
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

# Blocked usernames set (non-persistent)
blocked_usernames: set[str] = set()

# Pending tunnel validation states
pending_validations: dict[tuple[str, str], dict] = {}

# active tunnels. This is of no consequence
active_tunnels: set[tuple[WebSocketServerProtocol, WebSocketServerProtocol]] = set()

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
                elif username in blocked_usernames:
                    await websocket.send(encode_message(
                        type="register_error",
                        sender="Server",
                        message=f"⛔ Username '{username}' has been blocked. Restart required with a new identity."
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

            # Establishing peer connection
            decoded = decode_message(message_str=message) #type: ignore

            #### Connection Request Handling ####
            # check if it's a connect request
            if decoded.get("type") == "connect_request":
                
                source_user = user_reg_web.get(websocket)
                target_user = decoded.get("target")

                logger.info(f"[broadcast] received `connect_request` from @{source_user} to @{target_user} ")
                
                # checking if target's connected
                if not source_user or not target_user or target_user not in user_reg_id:
                    await websocket.send(
                        encode_message(
                            type="connect_error",
                            sender="Server",
                            message=f"Could not find user '{target_user}' to connect."
                        )
                    )

                # Forward the request to the target user
                else:
                    await user_reg_id[target_user].send(
                        encode_message(
                            type="connect_request",
                            sender=source_user,
                            message=f"Connection request from @{source_user}. Use /accept or /deny."
                        )
                    )
                
            #### Connect Busy ####
            # If peer already has a `connect_request`
            if decoded.get("type") == 'connect_busy':
                requester = decoded['target'] # The one who initiated the request
                responder = user_reg_web[websocket]

                logger.info(f"[broadcast] (server) Connection request from @{requester} to @{responder} denied by server. @{responder} is not idle, they either have pending connection requests or is in a private tunnel.")

                await user_reg_id[requester].send(
                    encode_message(
                        type='connect_busy',
                        sender=responder,
                        message=f"(server) Connection request to @{responder} denied. They may either have \n- pending connection requests or \n- could be in a private tunnel.\n"
                    )
                )

            #### Connect Accept ####
            if decoded.get("type") == "connect_accept":
                responder = user_reg_web[websocket]
                requester = decoded["target"] # The user who initiated request

                if requester not in user_reg_id:
                    await websocket.send(encode_message(
                        type="connect_error",
                        sender="Server",
                        message=f"Requester @{requester} not found."
                    ))
                
                await user_reg_id[requester].send(
                    encode_message(
                        type="connect_accept",
                        sender=responder,
                        message=f"@{responder} accepted your connection. Tunnel validation will start."
                    )
                )
                
                logger.info(f"[broadcast] connect_accept: (responder) @{responder} <-> (requester) @{requester}.")
                               
                # Accepting connection - trigger tunnel validation
                await user_reg_id[requester].send(
                    encode_message(
                        type="tunnel_validate",
                        sender="Server",
                        message="Enter the pre-shared secret to validate the tunnel (within 10 seconds)"
                    )
                )
                await user_reg_id[responder].send(encode_message(
                    type="tunnel_validate",
                    sender="Server",
                    message="Enter the pre-shared secret to validate the tunnel (within 10 seconds)"
                ))

                # Save validation state
                pending_validations[(requester, responder)] = {
                    "websockets": (user_reg_id[requester], user_reg_id[responder]),
                    "secrets": {},
                    "deadline": asyncio.get_event_loop().time() + 10
                }
            
            #### Connection Deny ####
            if decoded.get("type") == "connect_deny":
                responder = user_reg_web[websocket]
                requester= decoded.get("target")

                logger.info(f"[broadcast] received `connect_deny` from {responder} for {requester}")

                if requester in user_reg_id:
                    await user_reg_id[requester].send(
                        encode_message(
                            type="connect_deny",
                            sender=responder,
                            message=f"@{responder} denied your connection request."
                        )
                    )
                    logger.info(f"[server] connect_deny: @{responder} rejected @{requester}")
            
            #### Tunnel Secret Submission ####
            # Now when a user submits their secret
            if decoded.get("type") == "tunnel_secret":
                sender = user_reg_web.get(websocket)
                secret = decoded.get("secret")

                logger.info(f"[broadcast.tunnel_secret] sender: @{sender}, secret: @{secret}")

                # Find the pending validation involving this sender
                for (a, b), val_data in list(pending_validations.items()):
                    if sender in (a, b):
                        val_data["secrets"][sender] = secret

                        logger.info(f"[broadcast.tunnel_secret] Tunnel Secrets now: {pending_validations}")
                        
                        # check if both responded
                        if len(val_data["secrets"]) == 2:
                            s1, s2 = val_data["secrets"].values()
                            ws1, ws2 = val_data["websockets"]
                            
                            logger.info(f"[broadcast.tunnel_secret] Both have entered secrets.\n{(a, b)}: {val_data['secrets']} ")

                            if s1 == s2:
                                # Success
                                # add the websockets to the active_tunnels holder
                                active_tunnels.add((ws1, ws2))

                                # Send the message stating that the secret is verified and initialise key generation and transfer
                                await ws1.send(encode_message(
                                    type="tunnel_ok_key_init",
                                    sender="Server",
                                    message="Tunnel successfully established!"
                                ))
                                await ws2.send(encode_message(
                                    type="tunnel_ok_key_init",
                                    sender="Server",
                                    message="Tunnel successfully established!"
                                ))
                            else:
                                # Failure
                                for u in (a, b):
                                    blocked_usernames.add(u)
                                await ws1.send(encode_message(
                                    type="tunnel_failed",
                                    sender="Server",
                                    message="Validation failed. This username is now blocked."
                                ))
                                await ws2.send(encode_message(
                                    type="tunnel_failed",
                                    sender="Server",
                                    message="Validation failed. This username is now blocked."
                                ))
                                await ws1.close()
                                await ws2.close()

                            del pending_validations[(a, b)]

            if decoded.get('type') == 'key_share':
                sender = user_reg_web.get(websocket)
                target = decoded.get('target')
                key = decoded.get('key')
                logger.info(f'[broadcast.key_share] Received Public key from @{sender}: {key}')
                
                if target in user_reg_id:
                    target_websocket = user_reg_id.get(target)
                    await target_websocket.send(
                        encode_message(
                            type='key_share',
                            sender=sender,
                            key = key,
                            message=f"@{sender} is sharing their public key"
                        )
                    )
                else:
                    logger.warning(f'[broadcast.key_share] Target: {target} not found in user_reg_id')
                    await websocket.send(encode_message(
                        type="connect_error",
                        sender="Server",
                        message=f"Requester @{requester} not found."
                    ))

            #### TUNNEL EXIT ####
            if decoded.get("type") == "tunnel_exit":
                source_user = user_reg_web.get(websocket)
                target_user = decoded.get("target")

                logger.info(f"[broadcast] received `tunnel_exit` by {source_user}. Forwarding to {target_user}")
                
                # checking if target's connected
                if not source_user or not target_user or target_user not in user_reg_id:
                    await websocket.send(
                        encode_message(
                            type="connect_error",
                            sender="Server",
                            message=f"Could not find user '{target_user}' to connect."
                        )
                    )
                
                # Forward the `tunnel_exit` notification to the target user
                else:
                    await user_reg_id[target_user].send(
                        encode_message(
                            type="tunnel_exit",
                            sender=source_user,
                            message=f"(server) {source_user} has exited the tunnel"
                        )
                    )

                    # Remove the pair from active_tunnels
                    for ws_pair in list(active_tunnels):
                        if websocket in ws_pair:
                            logger.info(f'[broadcast.tunnel_exit] Removing ({source_user, target_user}) from active tunnel set')
                            active_tunnels.remove(ws_pair)
                    
                    # Log the updated active tunnel set
                    logger.info(f'Updated Active Tunnel Set: {active_tunnels}')                

            if decoded.get('type') == 'encrypted_message':
                source_user = user_reg_web.get(websocket)
                target_user = decoded.get('target')

                logger.info(f'[broadcast.encrypted_message.debug] Target: `{target_user}`')

                # Log the event
                logger.info(f'[broadcast] Received `encrypted_message` from {source_user}. Relaying to {target_user} ')

                # Relay the payload
                # Check for the presence of peer connection
                # Check for the presence in active_tunnel
                # If any of the peer is not present in any of either, respond to the sender with a connect error
                source_user_web = websocket
                target_user_web = user_reg_id.get(target_user)
                if (not source_user) or (not target_user) or (target_user not in user_reg_id):
                    await source_user_web.send(
                        encode_message(
                            type='connect_error',
                            sender='Server',
                            message=f'Could not find user @{target_user} to connect.'
                        )
                    )
                else:
                    for ws_pair in active_tunnels:
                        if source_user_web in ws_pair and target_user_web in ws_pair:
                            # Relay the message
                            await target_user_web.send(message=message)
                        else:
                            source_user_web.send(
                                encode_message(
                                    type='connect_error',
                                    sender='Server',
                                    message=f'User @{target_user} is not participating in an active tunnel with you.'
                                )
                            )                

            # Normal broadcast (only for idle chat)
            if decoded["type"] == 'chat_message':
                broadcast_to = list(user_reg_web.values())
                current_user = user_reg_web.get(websocket)
                if current_user in broadcast_to:
                    broadcast_to.remove(current_user)

                logger.info(f"[broadcast] Received message from: {user_reg_web.get(websocket)}\nDecoded message: {decode_message(str(message))}\nBroadcasting to these users: {broadcast_to}")
                
                for client_ws in user_reg_id.values():
                    if client_ws != websocket:
                        await client_ws.send(message)

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
        
        # Remove the pair if present from the active_tunnel when faced a client disconnect instead of a tunnel disconnect via exit_tunnel
        for ws_pair in list(active_tunnels):
            if websocket in ws_pair:
                
                # Log the removal via disconnection
                logger.info('[handler] Client\'s presence found in active tunnel set. Removing the pair.')

                active_tunnels.remove(ws_pair)

                # Log the updated active tunnel set
                logger.info(f'[handler] updated active tunnel set: {active_tunnels}')

        # Notify all connected clients about the disconnection
        disconnect_message = make_user_disconnected_message(username=username) # type: ignore
        logger.info(f"[handler] [!] User '{username}' has disconnected. Sending disconnection message to all clients.")
        print('user_registry_update: ', user_registry_by_id)      
        
        # Send the disconnection message to all connected clients
        # This informs all other clients that the user has disconnected        
        for client_ws in list(user_registry_by_id.values()): # ignore the list warning as we are trying to protect against concurrent overlapping and error due to in-loop dict modification.
            
            try:
                await client_ws.send(disconnect_message)
            
            except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK):
                # If the client is already disconnected, we can ignore this error
                logger.info(f"[handler] [!] Client {client_ws} is already disconnected.")

# If one user never sends their secret, the pending_validations entry remains forever. We should schedule a timeout cleanup task.
async def check_tunnel_timeouts():
    while True:
        now = asyncio.get_event_loop().time()
        expired = [pair for pair, data in pending_validations.items() if now > data["deadline"]]
        for pair in expired:
            ws1, ws2 = pending_validations[pair]["websockets"]
            for ws in (ws1, ws2):
                try:
                    await ws.send(encode_message(
                        type="tunnel_failed",
                        sender="Server",
                        message="Validation timeout. Usernames are blocked"
                    ))
                    await ws.close()
                except Exception:
                    pass
            for u in pair:
                blocked_usernames.add(u)
            del pending_validations[pair]
        await asyncio.sleep(1)

async def main():
    # welcome banner
    print('server\n', BANNER)
    asyncio.create_task(check_tunnel_timeouts()) # Start background task
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future() # Run Forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("[__main__] KeyboardInterrupt received. Server shutting down.")
