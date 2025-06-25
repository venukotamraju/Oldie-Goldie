import asyncio
import time
import websockets

async def echo(websocket):
    async for message in websocket:
        print(f"Received: {message}")
        await websocket.send(f"You said: {message}")

async def main():
    async with websockets.serve(echo, "localhost", 8765): # type: ignore
        print("Websocket server running at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
