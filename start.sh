#!/bin/bash

# Set up X11 environment
export DISPLAY=:99
export XAUTHORITY=/home/touchgesture/.Xauthority

# Start Xvfb with proper configuration
Xvfb :99 -screen 0 1024x768x24 -ac &
XVFB_PID=$!

# Wait for Xvfb to be ready
for i in $(seq 1 10); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        break
    fi
    echo "Waiting for Xvfb to be ready... ($i/10)"
    sleep 1
done

# Start virtual touchscreen
java -jar /opt/touchgesture/virtual_touchscreen.jar &
TOUCH_PID=$!

# Wait for virtual touchscreen
sleep 2

cat /proc/bus/input/devices

# Start xterm
xterm &
XTERM_PID=$!

# Start TouchGesture in verbose mode
cd /opt/touchgesture
python3 touchgesture.py --verbose &
TOUCHGESTURE_PID=$!

# Keep the script running and handle cleanup
trap "kill $XVFB_PID $TOUCH_PID $XTERM_PID $TOUCHGESTURE_PID" EXIT
wait