"""Simple proxy test"""
import subprocess
import json
import time

# Start proxy
proxy = subprocess.Popen(
    ['python', 'mcp_tracker_proxy.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

try:
    # Wait a bit for startup
    time.sleep(2)

    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }

    print("Sending initialize request...")
    proxy.stdin.write(json.dumps(init_request) + "\n")
    proxy.stdin.flush()

    # Read response with timeout
    import select
    import sys

    # Wait for response (5 seconds max)
    for i in range(50):
        if proxy.stdout.readable():
            response = proxy.stdout.readline()
            if response:
                print(f"Response: {response.strip()}")
                break
        time.sleep(0.1)
    else:
        print("No response within 5 seconds")

    # Print stderr
    time.sleep(1)
    stderr = proxy.stderr.read()
    if stderr:
        print(f"\nProxy stderr:\n{stderr}")

finally:
    proxy.terminate()
    proxy.wait(timeout=2)
