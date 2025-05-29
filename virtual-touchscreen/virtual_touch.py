from flask import Flask, request, render_template_string
import os
import time
import threading
import json
from pathlib import Path
import socket
import struct

app = Flask(__name__)

# Create a directory for our virtual device
VIRTUAL_DEVICE_DIR = "/tmp/virtual_touchscreen"
os.makedirs(VIRTUAL_DEVICE_DIR, exist_ok=True)

# Create a Unix domain socket for touch events
SOCKET_PATH = os.path.join(VIRTUAL_DEVICE_DIR, "touch.sock")
if os.path.exists(SOCKET_PATH):
    os.unlink(SOCKET_PATH)

# Create the socket server
server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server_socket.bind(SOCKET_PATH)
server_socket.listen(1)
os.chmod(SOCKET_PATH, 0o666)

# Device state
device_state = {
    "touch": False,
    "x": 0,
    "y": 0
}

# Simple HTML interface
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Virtual Touchscreen</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .touch-area {
            width: 800px;
            height: 480px;
            border: 2px solid #ccc;
            position: relative;
            margin: 20px 0;
        }
        .touch-point {
            width: 20px;
            height: 20px;
            background: red;
            border-radius: 50%;
            position: absolute;
            transform: translate(-50%, -50%);
            display: none;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <h2>Virtual Touchscreen</h2>
    <div class="touch-area" id="touchArea">
        <div class="touch-point" id="touchPoint"></div>
    </div>
    <div>
        <button onclick="doTap()">Tap Center</button>
        <button onclick="doSwipe()">Swipe Left to Right</button>
    </div>
    <script>
        const touchArea = document.getElementById('touchArea');
        const touchPoint = document.getElementById('touchPoint');
        
        function updateTouchPoint(x, y, visible) {
            touchPoint.style.left = x + 'px';
            touchPoint.style.top = y + 'px';
            touchPoint.style.display = visible ? 'block' : 'none';
        }

        function doTap() {
            fetch('/tap', { method: 'POST' });
        }

        function doSwipe() {
            fetch('/swipe', { method: 'POST' });
        }

        touchArea.addEventListener('mousedown', (e) => {
            const rect = touchArea.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            fetch('/touch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x, y, touch: true })
            });
            updateTouchPoint(x, y, true);
        });

        touchArea.addEventListener('mouseup', () => {
            fetch('/touch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ touch: false })
            });
            updateTouchPoint(0, 0, false);
        });

        touchArea.addEventListener('mousemove', (e) => {
            if (e.buttons === 1) {
                const rect = touchArea.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                fetch('/touch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ x, y, touch: true })
                });
                updateTouchPoint(x, y, true);
            }
        });
    </script>
</body>
</html>
"""

def update_device_state(x=None, y=None, touch=None):
    global device_state
    if x is not None:
        device_state["x"] = int(x)
    if y is not None:
        device_state["y"] = int(y)
    if touch is not None:
        device_state["touch"] = touch
    
    # Write state to file
    with open(os.path.join(VIRTUAL_DEVICE_DIR, "state.json"), "w") as f:
        json.dump(device_state, f)
    
    # Send event through Unix socket
    try:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_PATH)
        event_data = struct.pack('!iii', 
            device_state["x"],
            device_state["y"],
            1 if device_state["touch"] else 0
        )
        client_socket.send(event_data)
        client_socket.close()
    except Exception as e:
        print(f"Error sending event: {e}")

def do_tap(x=400, y=240):
    update_device_state(x=x, y=y, touch=True)
    time.sleep(0.2)
    update_device_state(touch=False)

def do_swipe(x1=200, y1=240, x2=600, y2=240, steps=10, duration=0.5):
    dx = (x2 - x1) / steps
    dy = (y2 - y1) / steps
    
    update_device_state(x=x1, y=y1, touch=True)
    time.sleep(0.05)
    
    for i in range(steps):
        x = x1 + dx * i
        y = y1 + dy * i
        update_device_state(x=x, y=y)
        time.sleep(duration / steps)
    
    update_device_state(touch=False)

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML)

@app.route('/tap', methods=['POST'])
def tap():
    threading.Thread(target=do_tap).start()
    return "OK"

@app.route('/swipe', methods=['POST'])
def swipe():
    threading.Thread(target=do_swipe).start()
    return "OK"

@app.route('/touch', methods=['POST'])
def touch():
    data = request.get_json()
    update_device_state(
        x=data.get('x'),
        y=data.get('y'),
        touch=data.get('touch')
    )
    return "OK"

@app.route('/state', methods=['GET'])
def get_state():
    return device_state

if __name__ == '__main__':
    print("Serving on http://0.0.0.0:5000 ...")
    print(f"Virtual device state available at {VIRTUAL_DEVICE_DIR}/state.json")
    print(f"Touch events available at {SOCKET_PATH}")
    app.run(host='0.0.0.0', port=5000)
