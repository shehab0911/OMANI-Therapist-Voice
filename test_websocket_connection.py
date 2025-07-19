import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket successfully!")
            
            # Send a test message
            test_message = {
                "message": "مرحبا",
                "user_id": "test_user"
            }
            await websocket.send(json.dumps(test_message))
            print("Sent test message:", test_message)
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            print("Received response:", response)
            
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())