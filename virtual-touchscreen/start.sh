#!/bin/bash

# Create necessary directories
mkdir -p /dev/input

# Create uinput device if it doesn't exist
if [ ! -e /dev/uinput ]; then
    mknod /dev/uinput c 10 223
fi

# Set proper permissions
chmod 666 /dev/uinput

# Try to load uinput module
if ! lsmod | grep -q uinput; then
    modprobe uinput || true
fi

# Ensure the device exists and is accessible
if [ ! -e /dev/uinput ]; then
    echo "Error: /dev/uinput device not found"
    exit 1
fi

# Check if we can write to the device
if [ ! -w /dev/uinput ]; then
    echo "Error: Cannot write to /dev/uinput"
    exit 1
fi

echo "Uinput device is ready"
echo "Starting virtual touchscreen..."

# Start the Python application
exec python /app/virtual_touch.py 