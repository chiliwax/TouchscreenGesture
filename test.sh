#!/bin/bash

# Build and start the container
docker-compose up --build -d

# Wait for the container to be ready
echo "Waiting for container to be ready..."
sleep 5

# Connect to VNC
echo "Starting VNC viewer..."
echo "Connect to localhost:5900 with VNC viewer"
echo "Default password is empty"

# Keep the script running
echo "Press Ctrl+C to stop the container"
docker-compose logs -f 