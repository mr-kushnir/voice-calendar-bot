"""Test MCP Yandex Tracker server"""
import asyncio
import httpx
import json

MCP_SERVER_URL = "https://db8ss12906fjgalcbbtf.5p9km096.mcpgw.serverless.yandexcloud.net"


async def test_mcp():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Get SSE endpoint
        print("1. Getting SSE endpoint...")
        response = await client.get(f"{MCP_SERVER_URL}/sse")
        sse_data = response.text
        print(f"SSE Response: {sse_data}")

        # Parse session ID from SSE response
        # Format: event: endpoint\ndata: /message?sessionId=XXX\n\n
        session_id = None
        for line in sse_data.split('\n'):
            if line.startswith('data:'):
                endpoint = line.split('data:')[1].strip()
                if 'sessionId=' in endpoint:
                    session_id = endpoint.split('sessionId=')[1]
                    print(f"Session ID: {session_id}")
                    break

        if not session_id:
            print("Failed to get session ID")
            return

        # 2. Initialize connection
        print("\n2. Initializing MCP connection...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "tracker-test",
                    "version": "1.0"
                }
            }
        }

        try:
            response = await client.post(
                f"{MCP_SERVER_URL}/message?sessionId={session_id}",
                json=init_request,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200:
                result = response.json()
                print(f"\nInitialized successfully!")
                print(f"Server capabilities: {json.dumps(result.get('result', {}), indent=2)}")

                # 3. List available tools
                print("\n3. Listing available tools...")
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                response = await client.post(
                    f"{MCP_SERVER_URL}/message?sessionId={session_id}",
                    json=tools_request
                )

                if response.status_code == 200:
                    tools = response.json()
                    print(f"Available tools: {json.dumps(tools.get('result', {}), indent=2)}")
                else:
                    print(f"Failed to list tools: {response.text}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_mcp())
