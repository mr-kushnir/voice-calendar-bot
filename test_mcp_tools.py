"""Test MCP Tracker tools availability"""
import subprocess
import json
import sys

def test_mcp_proxy():
    """Test MCP proxy by sending initialize and tools/list requests"""

    # Start proxy
    proxy = subprocess.Popen(
        ['python', 'mcp_tracker_proxy.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        print("Sending initialize request...")
        proxy.stdin.write(json.dumps(init_request) + "\n")
        proxy.stdin.flush()

        # Read response
        response = proxy.stdout.readline()
        if response:
            print(f"Initialize response: {response.strip()}")
            result = json.loads(response)

            if "result" in result:
                print("✅ MCP proxy initialized successfully!")

                # Now request tools list
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                print("\nSending tools/list request...")
                proxy.stdin.write(json.dumps(tools_request) + "\n")
                proxy.stdin.flush()

                tools_response = proxy.stdout.readline()
                if tools_response:
                    print(f"Tools response: {tools_response.strip()}")
                    tools_result = json.loads(tools_response)

                    if "result" in tools_result:
                        tools = tools_result["result"].get("tools", [])
                        print(f"\n✅ Available tools ({len(tools)}):")
                        for tool in tools:
                            print(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
                    else:
                        print(f"❌ Error: {tools_result.get('error')}")
            else:
                print(f"❌ Error: {result.get('error')}")
        else:
            print("❌ No response from proxy")

        # Check stderr for errors
        proxy.stdin.close()
        stderr = proxy.stderr.read()
        if stderr:
            print(f"\nProxy stderr:\n{stderr}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        proxy.terminate()
        proxy.wait(timeout=2)


if __name__ == "__main__":
    test_mcp_proxy()
