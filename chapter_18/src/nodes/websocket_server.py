#!/usr/bin/env python3
"""
Mock Robot WebSocket Server

This script creates a mock WebSocket server that simulates communication
with a robot. It listens for robot_action messages and sends back
simulated responses.

Installation and Usage:
1. Install dependencies:
    pip install websockets
2. Run the WebSocket server:
    python websocket_server.py

The server will:
- Listen for connections on port 8080
- Accept robot_action messages in the expected format
- Simulate processing and send back action_response messages
"""

import asyncio
import json
from datetime import datetime
import websockets


async def handle_connection(websocket, path):
    """Handle a single WebSocket connection."""
    print('Robot connected to mock server')

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f'Received from robot client: {data}')

                # Log the action received
                if data.get('type') == 'robot_action':
                    print(f"Action received: {data.get('data')}")
                    print(f"Original query: {data.get('original_query')}")

                    # Echo back a simulated response after a short delay
                    await asyncio.sleep(1)

                    response = {
                        'type': 'action_response',
                        'status': 'executed',
                        'action': data.get('data'),
                        'timestamp': datetime.now().isoformat()
                    }

                    await websocket.send(json.dumps(response))
                    print(f'Sent response back to client: {response}')

            except json.JSONDecodeError as e:
                print(f'Error parsing message: {e}')
            except Exception as e:
                print(f'Error handling message: {e}')

    except websockets.exceptions.ConnectionClosed:
        print('Robot disconnected from mock server')
    except Exception as e:
        print(f'WebSocket error: {e}')


async def main():
    """Start the WebSocket server."""
    server = await websockets.serve(handle_connection, 'localhost', 8080)
    print('Mock Robot WebSocket Server running on port 8080')

    # Run forever
    await server.wait_closed()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nServer stopped')
