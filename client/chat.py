import asyncio
import websockets
from shared.protocol import encode_message, decode_message

SERVER_URI = "ws://localhost:8765"

async def send_messages(websocket, username):
    while True:
        try:
            message = await asyncio.to_thread(input, "")
            if not message.strip():
                continue
            encoded = encode_message(message=message, sender=username)
            await websocket.send(encoded)
        except KeyboardInterrupt:
            print("\n [Exiting Chat]")
            break

async def receive_messages(websocket):
    while True:
        try:
            message = await websocket.recv()
            decoded = decode_message(message_str=message)
            print(f"\n [{decoded['timestamp']}] {decoded['sender']}: {decoded['message']}")
        except websockets.exceptions.ConnectionClosed:
            print("[Disconnected from server]")
            break

        
async def main():
    username = input("Enter your username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    async with websockets.connect(SERVER_URI) as websocket:
        print(f"Connected to secure chat websocket server at ws://localhost:8765 as '{username}'")
        await asyncio.gather(
            send_messages(websocket, username),
            receive_messages(websocket)
        )        
        
        
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Chat Client Closed.")