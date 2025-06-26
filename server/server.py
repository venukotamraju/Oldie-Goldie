import asyncio
import websockets
from shared.protocol import encode_message, decode_message

connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"Connected Clients: {connected_clients}")
    try:
        async for message in websocket:
            print(f"{websocket} has send {message}")
            # Broadcast the message to all connected clients
            for client in connected_clients:
                if client != websocket:
                    await client.send(message)
    except websockets.exceptions.ConnectionClosedError:
        print(f"this is for connection closed error, check if any clients are affected: {connected_clients }")
    finally:
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Secure chat websocker server is running on ws://0.0.0.0:8765")
        await asyncio.Future() # Run Forever

if __name__ == "__main__":
    asyncio.run(main())
