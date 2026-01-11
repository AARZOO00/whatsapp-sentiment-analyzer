#!/usr/bin/env python3
"""Simple test to check if server is running."""
import socket
import time

def is_port_open(host='127.0.0.1', port=8000, timeout=1):
    """Check if a port is open."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

print("Checking if port 8000 is open...")
for i in range(30):  # 30 seconds
    if is_port_open():
        print(f"Port 8000 is open! (after {i} seconds)")
        break
    else:
        print(f"  Attempt {i+1}/30: Port closed, waiting...")
        time.sleep(1)
else:
    print("Port 8000 never opened!")
