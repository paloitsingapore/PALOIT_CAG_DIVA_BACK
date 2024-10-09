import asyncio
import websockets
import json
import sys
import os

# Add the path to your Lambda function
sys.path.append('./assisted_wayfinding_backend/lambda_functions/orchestration')
from index import handler

class MockContext:
    def __init__(self):
        self.function_name = "local-orchestration-lambda"
        self.function_version = "$LATEST"

async def websocket_handler(websocket, path):
    connection_id = str(id(websocket))
    print(f"New connection: {connection_id}")

    try:
        async for message in websocket:
            print(f"Received message: {message}")
            
            # Create the event object
            event = {
                'requestContext': {'connectionId': connection_id},
                'body': message
            }
            
            # Set any necessary environment variables
            os.environ['WEBSOCKET_API_ENDPOINT'] = 'http://localhost:8765'
            
            # Call the Lambda handler directly
            result = handler(event, MockContext())
            
            # print(f"Lambda function result: {result}")
            
            # Send the response back to the client
            await websocket.send(json.dumps(result))
    
    finally:
        print(f"Connection closed: {connection_id}")

async def main():
    server = await websockets.serve(websocket_handler, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())