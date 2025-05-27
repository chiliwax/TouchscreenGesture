#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3-evdev xdotool
elif command -v dnf &> /dev/null; then
    dnf install -y python3-evdev xdotool
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm python-evdev xdotool
else
    echo "Unsupported package manager. Please install python3-evdev and xdotool manually."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p /etc/touchgesture
mkdir -p /usr/local/bin

# Copy configuration
echo "Installing configuration..."
cp config/default.yaml /etc/touchgesture/

# Install main script
echo "Installing main script..."
cp touchgesture.py /usr/local/bin/touchgesture
chmod +x /usr/local/bin/touchgesture

# Setup input device permissions
echo "Setting up input device permissions..."
if ! getent group input > /dev/null; then
    groupadd input
fi

# Add current user to input group
CURRENT_USER=$(logname)
usermod -a -G input "$CURRENT_USER"

echo "Installation complete!"
echo "Please log out and log back in for group changes to take effect."
echo "You can then run 'touchgesture' to start the daemon." 