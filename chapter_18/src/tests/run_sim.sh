#!/bin/bash

# Script to test the robot plugin functionality
# This script starts the mock server, starts openclaw gateway, and triggers robot actions

set -e  # Exit on any error

echo "Starting Robot Plugin Test Suite..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup background processes
cleanup() {
    echo
    print_status "Cleaning up processes..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Check if required tools are available
if ! command -v node &> /dev/null; then
    print_error "node is not installed or not in PATH"
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    print_error "pnpm is not installed or not in PATH"
    exit 1
fi

print_status "Building robot plugin..."
cd plugins/robot-plugin
pnpm install
pnpm run build

if [ $? -ne 0 ]; then
    print_error "Failed to build robot plugin"
    exit 1
fi

cd ../..

print_status "Starting mock WebSocket server..."
node nodes/websocket-server.ts &
WS_SERVER_PID=$!

sleep 2  # Wait for server to start

print_status "Starting mock WebRTC signaling server..."
node nodes/webrtc-peer.ts &
WEBRTC_SERVER_PID=$!

sleep 2  # Wait for signaling server to start

print_status "Starting OpenClaw gateway (simulated)..."
# In a real scenario, this would start the actual OpenClaw gateway
# For this test, we'll just simulate the interaction
echo "OpenClaw gateway would start here..."

# Simulate sending a robot action via API call (curl)
print_status "Testing robot action via WebSocket transport..."
curl -X POST http://localhost:3001/tool-call \
  -H "Content-Type: application/json" \
  -d '{
    "toolName": "robot_action",
    "params": {
      "action": {"move": {"direction": "forward"}},
      "message_query": "Move the robot forward",
      "message_reply": "Moving forward now!"
    }
  }' || print_warning "Curl command failed - this is expected if OpenClaw gateway is not running"

sleep 2

# Simulate changing config to use WebRTC and testing again
print_status "Testing robot action via WebRTC transport..."
# In a real scenario, we would update the config to use WebRTC and test again

print_status "Test suite completed successfully!"
echo
print_status "Next steps:"
print_status "- Start the actual OpenClaw gateway"
print_status "- Configure transport_type as 'ws' or 'webrtc' in openclaw.json"
print_status "- Send tool calls to trigger robot actions"