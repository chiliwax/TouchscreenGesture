import socket
import struct
import time

# Connect to the touch event socket
SOCKET_PATH = "/tmp/virtual_touchscreen/touch.sock"

def connect_to_touchscreen():
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(SOCKET_PATH)
        return client
    except socket.error as e:
        print(f"Error connecting to touchscreen: {e}")
        return None

def read_touch_event(client):
    try:
        # Read 12 bytes (3 integers: x, y, touch)
        data = client.recv(12)
        if len(data) == 12:
            x, y, touch = struct.unpack('!iii', data)
            return {
                'x': x,
                'y': y,
                'touch': bool(touch)
            }
    except socket.error as e:
        print(f"Error reading touch event: {e}")
    return None

def main():
    print("Connecting to virtual touchscreen...")
    client = connect_to_touchscreen()
    
    if not client:
        print("Failed to connect to touchscreen")
        return

    print("Connected to touchscreen!")
    print("Waiting for touch events...")
    
    try:
        while True:
            event = read_touch_event(client)
            if event:
                print(f"Touch event: x={event['x']}, y={event['y']}, touch={event['touch']}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
    finally:
        client.close()

if __name__ == "__main__":
    main() 