import asyncio
import time
from typing import Optional
import websockets
import websockets.legacy.server
from websockets.legacy.server import WebSocketServerProtocol
import logging
from shared import encode_message, decode_message, make_register_message, make_user_disconnected_message, make_system_response
from shared import SYMBOL_BANNER, version_banner
import argparse
import sys
import shutil
import subprocess
from .helpers.tunnel_manager import TunnelManager
import secrets
from importlib.metadata import version, PackageNotFoundError

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

# If invite_tokens is passed for authorization
invite_tokens = {}

invite_token = False

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

async def handle_registration(websocket, bound_username:str) -> str | None:
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
                elif bound_username and (username != bound_username):
                    await websocket.send(
                        encode_message(
                            type="register_error",
                            sender="Server",
                            message=f"⛔ You are using a token bound to another username. If you have misspelled please try again else do not misuse the token that's not meant for you!"
                        )
                    )
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

            #### Client System Request Events #####
            # this includes the response to following needs:
            # 1. 'list_users'
            if decoded['type'] == 'system_request':
                sender = decoded['sender']
                if decoded['need'] == 'list_users':
                    await websocket.send(
                        make_system_response(
                            res_need='list_users',
                            res_obj=list(user_reg_id.keys())
                        )
                    )
            
            # Normal broadcast (only for idle chat)
            if decoded["type"] == 'chat_message':

                # this is to create a list for logging, it has not functional use
                broadcast_to = list(user_reg_web.values())
                current_user = user_reg_web.get(websocket)
                if current_user in broadcast_to:
                    broadcast_to.remove(current_user)

                logger.info(f"[broadcast] Received message from: {user_reg_web.get(websocket)}\nDecoded message: {decode_message(str(message))}\nBroadcasting to these users: {broadcast_to}")
                
                # Before broadcasting, we have to make sure not to broadcast to active tunnel users
                # For this, since we have the `active_tunnels` of type set[tuple], we will create a new one dimensional iterable object to help speed up the iteration
                active_tunnels_iter:set[WebSocketServerProtocol] = set()
                for ws_pair in active_tunnels:
                    active_tunnels_iter.add(ws_pair[0])
                    active_tunnels_iter.add(ws_pair[1])

                for client_ws in user_reg_id.values():
                    if client_ws != websocket and client_ws not in active_tunnels_iter:
                        await client_ws.send(message)

    except websockets.exceptions.ConnectionClosed:
        pass

async def handler(websocket):
    """Handles incoming websocket connections and registration of users."""
    global invite_tokens

    # Extract the token from connection info
    token = websocket.request.headers.get('Authorization')
    token_bound_username = None
    
    if invite_token:
        if not token or (token not in invite_tokens):
            logger.info(f"[handler] Invalid Token, Closing connection")
            await websocket.close(code=4001, reason='Invalid or missing token')
            return
        
        token_bound_username = invite_tokens[token]['username']
        
        if not token_bound_username:
            del invite_tokens[token]
            logger.info(f'[handler] Consuming token {token}. Updated invite_tokens: {invite_tokens}')

    try:
        # Receive the initial (register) message from the client
        # This is expected to be a registration message containing the username
        logger.info("[handler] Starting registration phase...")
        username = await handle_registration(websocket=websocket, bound_username=token_bound_username)
        
        if username is None:
            logger.info("[handler] Registration failed or timed out")
            return

        if token_bound_username and username:
            del invite_tokens[token]

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
        # 
        # And while informing the clients, there are two flows:
        # We should not inform the disconnection of general users to tunnel users to not disturb the session
        # if a tunnel user is disconnected, all the users should be informed
        active_tunnels_iter = set()
        for ws_pair in active_tunnels:
            active_tunnels_iter.add(ws_pair[0])
            active_tunnels_iter.add(ws_pair[1])

        # Now we are ready with a one dimensional iterable object containing the active_tunnel users
        for client_ws in list(user_registry_by_id.values()): # ignore the list warning as we are trying to protect against concurrent overlapping and error due to in-loop dict modification.
            
            # This is assuming, the one disconnected is not in the active_tunnels list or has been terminated from it
            # So not disturbing the ones in the active_tunnels list
            if client_ws not in active_tunnels_iter:
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
        
        # Clean Up Expired Invite Tokens
        expired_tokens = [
            tok for tok, meta in invite_tokens.items() 
            if meta['expiry'] is not None and now > meta['expiry']
            ]
        for tok in expired_tokens:
            del invite_tokens[tok]

        await asyncio.sleep(1)

def parse_args():
    p = argparse.ArgumentParser(
        description="Oldie-Goldie's secure server. To serve, run: python -m server.server --host {local|public}",
        epilog=(
            "When using both --bind and --token-count, the value for --token-count must not be less than the number of usernames provided via --bind.\n"
            "Explanation:\n"
            "The --token-count value determines the total number of tokens to generate. Tokens are first mapped to the usernames passed via --bind. Any remaining tokens (up to the specified count) will be generated as unmapped tokens.\n"
            "Example:\n"
            "  --bind user1 user2 --token-count 3\n"
            "  → Generates two mapped tokens (for user1 and user2) and one unmapped token."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,  # keeps formatting & newlines
    )
    p.add_argument('--host', choices=['local','public'], required=True, help='local or public (cloudflared)')
    p.add_argument('--port', type=int, default=8765, help='port to run the server on. default is 8765')
    p.add_argument('--invite-token', action='store_true', help='generate single-use invite tokens on startup. Default expiry is 10 min')
    p.add_argument('--bind', nargs='+', help='optional list of usernames to bind tokens to (only when --invite-token used)')
    p.add_argument('--token-count', type=int, help='how many tokens to create per bound username or globally')
    p.add_argument('--no-expiry', action='store_true', help='remove expiration of tokens. The tokens will however be discarded when server is closed.')
    
    # 👇 Add version flag
    try:
        pkg_version = version("oldie-goldie")
    except PackageNotFoundError:
        pkg_version = "0.0.0-dev"
    
    p.add_argument("--version", action="version", version=f"Oldie Goldie {pkg_version}")
    
    return p.parse_args()

def validate_args(args: argparse.Namespace):
    """
    Validate arguments: enforce that --bind and --token-count are only used together with
    --invite-token, and that when --invite-token is set you get either --token-count (>0)
    or at least one username in --bind.
    """

    # If --bind was given (non-empty list), it must be accompanied by --invite-token
    if args.bind is not None and len(args.bind) > 0:
        if not args.invite_token:
            logger.error("[validate_args] Error: --bind is only valid together with --invite-token", file=sys.stderr)
            sys.exit(1)
        
        # Edge cases
        # 1. If comma separated values are passed, it will be like ['user1,user2']
        if len(args.bind) == 1:
            if len(args.bind[0].split(',')) > 1:
                logger.error('[validate_args] Enter space separated usernames. Example: --bind user1 user2 ...')
                sys.exit(1)
        # 2. For every name check the validation using is_valid_username_format method from above the code.
        for username in args.bind:
            valid, reason = is_valid_username_format(username)
            if not valid:
                logger.error(f"[validate_args] '{username}' is not a valid username format, reason: {reason}")
                sys.exit(1)

    # If --token-count was given, it must be accompanied by --invite-token
    if args.token_count is not None:
        if not args.invite_token:
            logger.error("[validate_args] Error: --token-count is only valid together with --invite-token", file=sys.stderr)
            sys.exit(1)
        if args.token_count <= 0:
            logger.error("[validate_args] Error: --token-count must be > 0", file=sys.stderr)
            sys.exit(1)

    # If --invite-token is requested, require either token_count or at least one bind username
    if args.invite_token:
        has_bind = (args.bind is not None and len(args.bind) > 0)
        has_token_count = (args.token_count is not None and args.token_count > 0)
        if not (has_bind or has_token_count):
            logger.error("[validate_args] Error: when using --invite-token you must pass either --token-count N (N>0) or --bind <username> [users...]", file=sys.stderr)
            sys.exit(1)
        if has_bind and has_token_count:
            if args.token_count < len(args.bind):
                logger.error("[validate args] Error: When using both --bind and --token-count, the value for --token-count must not be less than the number of usernames provided via --bind.\nExplanation:\nThe --token-count value determines the total number of tokens to generate. Tokens are first mapped to the usernames passed via --bind. Any remaining tokens (up to the specified count) will be generated as unmapped tokens.\nExample:\n--bind user1 user2 --token-count 3\n→ Generates two mapped tokens (for user1 and user2) and one unmapped token.")
                sys.exit(1)

    # If --no-expiry is used without --invite-tokens
    if args.no_expiry:
        if not args.invite_token:
            logger.error("[validate_args] --no-expiry should be passed only when --invite-tokens is invoked")
            sys.exit(1)

def launch_tunnel(port: int) -> Optional[TunnelManager]:
    """
    Launch an ephemeral cloudflared tunnel to localhost:port.
    Returns a TunnelManager or None if cloudflared not found or failed to start.
    """
    cmd = shutil.which('cloudflared')
    if not cmd:
        print('❌ Cloudflared not found on PATH.')
        print('Install it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/')
        return None

    print(f"✅ Launching Cloudflare tunnel for localhost:{port} ...")
    try:
        proc = subprocess.Popen(
            [cmd, 'tunnel', '--url', f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except Exception as e:
        print('Failed to launch cloudflared:', e)
        return None

    return TunnelManager(proc)

async def wait_for_tunnel_url(manager: TunnelManager, timeout: float = 5.0) -> Optional[str]:
    """
    Async helper to wait up to `timeout` seconds for manager.url to become available.
    Returns the URL or None on timeout.
    """
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if manager.url:
            return manager.url
        await asyncio.sleep(0.1)
    return manager.url  # might be None

# Invite Token Generation
def generate_invite_tokens(args):
    """Generate Invite Tokens if invite_tokens is true in the args dictionary.
    Added to Validtions:
    1. If bind is passed, there is no need of passing the token_count.
    2. If bind and token_count, both are passed, the token_count should not be less than the number of usernames given for bind

    Args:
        args (args.Namespace): args object provided by Argparser
    """

    global invite_tokens
    global invite_token

    invite_token = True

    expiry_time = (time.time() + 600) if not args.no_expiry else None # Token valid for 10 minutes
    expiry_display = None

    if expiry_time:
        expiry_minutes = (expiry_time - time.time()) / 60
        expiry_display = f"{expiry_minutes:.2f}"
    else:
        expiry_display = expiry_time

    if args.invite_token:
        if args.bind:
            for username in args.bind:
                # These are mapped tokens
                token = secrets.token_urlsafe(16)
                invite_tokens[token] = {"username":username, "expiry":expiry_time}
                logger.info(f"[generate_invite_tokens] [+] Mapped Token for {username}: {token} with Expiry (in minutes): {expiry_display}")
            if args.token_count and args.token_count > len(args.bind):
                # If both --bind and --token-count are present
                for _ in range (args.token_count - len(args.bind)):
                    # These are left out unmapped tokens after mapped tokens are done generating
                    token = secrets.token_urlsafe(16)
                    invite_tokens[token] = {"username": None, "expiry": expiry_time}
                    logger.info(f"[generate_invite_tokens] [+] General Token, Username: None, Token: {token}, Expiry (in minutes): {expiry_display}")
        else:
            # Only if --token-count is given
            for _ in range (args.token_count):
                token = secrets.token_urlsafe(16)
                invite_tokens[token] = {"username": None, "expiry": expiry_time}
                logger.info(f"[+] General Token: {token}, Expiry (in minutes): {expiry_display}")

async def process_request(connection, request):
    """
    This runs before the websocket handshake.
    We can reject unauthorized clients here.
    """
    now = time.time()

    # Clean up expired tokens
    expired = [tok for tok, meta in invite_tokens.items() if now > meta["expiry"]]
    for tok in expired:
        del invite_tokens[tok]
    
     # Skip check if no tokens configured
    if not invite_token:
        return None  # continue to handshake
    
    # Only check if tokens are enabled
    auth_header = request.headers.get('Authorization')

    # Invalid or missing token → return 401 and skip handler
    if not auth_header or (auth_header not in invite_tokens):
        logger.warning(f"[process_request] Invalid/missing token: {auth_header}")

        # Build proper HTTP 401 response
        response = (
            b"HTTP/1.1 401 Unauthorized\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: 23\r\n"
            b"Connection: close\r\n"
            b"\r\n"
            b"Unauthorized or invalid.\n"
        )

        # Send response directly over the transport
        try:
            connection.transport.write(response)
        # yield control to flush socket buffer
            await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"[process_request] Error sending response: {e}")
        finally:
            connection.transport.close()
        return # stop handshake
        
    
    # Valid token, Don't consume token here; just allow connection
    return None # Continue to handshake

async def main():
    # Add support for command line arguments to take in an optional port number
    args = parse_args()
    validate_args(args=args)
    logger.debug('[main] args: ', args)

    # welcome banner
    app_name = 'Protected Server' if args.invite_token else 'Unprotected Server'
    print(version_banner(app_name=app_name))

    tunnel_mgr = None
    if args.host == 'public':
        tunnel_mgr = launch_tunnel(args.port)
        if tunnel_mgr is None:
            print("⚠️ Failed to start cloudflared. Falling back to local only mode.")
        else:
            url = await wait_for_tunnel_url(tunnel_mgr, timeout=8.0)
            if url:
                print(f"\nPublic ephemeral URL: {url}\n")
            else:
                print("⚠️ Cloudflared started but URL not yet available (continuing anyway).")
    
    if args.invite_token:
        generate_invite_tokens(args=args)
    
    asyncio.create_task(check_tunnel_timeouts()) # Start background task

    try:
        async with websockets.serve(handler, "0.0.0.0", port=args.port, process_request=process_request):
            logger.info(f"Serving on port {args.port} (host={args.host})")
            await asyncio.Future() # Run Forever
    finally:
        # ensure tunnel is shut down when server exits
        if tunnel_mgr is not None:
            tunnel_mgr.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("[__main__] KeyboardInterrupt received. Server shutting down.")

def cli():
    """Entry point for 'og-client' command."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[og-client] KeyboardInterrupt received. Exiting...")