import asyncio
import websockets
import json
import sys

async def test_websocket():
    uri = "ws://localhost:8001/ws/orders"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket!")
            
            # Receive the initial data
            print("Waiting for initial data...")
            initial_data = await websocket.recv()
            print(f"Received data: {initial_data[:100]}...")
            
            # Send a ping message
            print("Sending a ping message...")
            await websocket.send("ping")
            
            # Receive the echo response
            print("Waiting for echo response...")
            echo_data = await websocket.recv()
            print(f"Received echo: {echo_data}")
            
            # Keep connection open for a bit
            print("Keeping connection open for 5 seconds...")
            await asyncio.sleep(5)
            
            print("Test completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_websocket()) 