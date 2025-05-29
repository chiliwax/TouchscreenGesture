import time
import json
import os
import socket
import struct

# Create a Unix domain socket for touch events
SOCKET_PATH = "/tmp/virtual_touchscreen/touch.sock"
os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)

# Create the socket server
server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
if os.path.exists(SOCKET_PATH):
    os.unlink(SOCKET_PATH)
server_socket.bind(SOCKET_PATH)
server_socket.listen(1)
os.chmod(SOCKET_PATH, 0o666)

print("Touch event server ready at", SOCKET_PATH)

# Wait for the virtual touchscreen to be ready
while not os.path.exists("/tmp/virtual_touchscreen/state.json"):
    print("Waiting for virtual touchscreen...")
    time.sleep(1)

print("Virtual touchscreen user ready")
while True:
    try:
        with open("/tmp/virtual_touchscreen/state.json", "r") as f:
            state = json.load(f)
            
            # Accept any waiting connections
            try:
                client_socket, _ = server_socket.accept()
                # Send the current state
                event_data = struct.pack('!iii', 
                    state["x"],
                    state["y"],
                    1 if state["touch"] else 0
                )
                client_socket.send(event_data)
                client_socket.close()
            except socket.error:
                # No clients waiting, that's fine
                pass
                
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(0.01) 