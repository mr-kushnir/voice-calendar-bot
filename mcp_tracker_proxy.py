#!/usr/bin/env python3
"""
MCP Proxy for Yandex Tracker SSE Server

This proxy connects to the SSE MCP server and provides stdio transport for Claude Code.
"""
import sys
import json
import asyncio
import httpx
from typing import Optional


class MCPTrackerProxy:
    def __init__(self, sse_url: str):
        self.sse_url = sse_url
        self.session_id: Optional[str] = None
        self.message_url: Optional[str] = None
        self.request_id = 0
        self.client = httpx.AsyncClient(timeout=30.0)

    async def connect(self):
        """Connect to SSE server and get session ID"""
        try:
            response = await self.client.get(f"{self.sse_url}/sse")
            sse_data = response.text

            # Parse session ID from SSE response
            for line in sse_data.split('\n'):
                if line.startswith('data:'):
                    endpoint = line.split('data:')[1].strip()
                    if 'sessionId=' in endpoint:
                        self.session_id = endpoint.split('sessionId=')[1]
                        self.message_url = f"{self.sse_url}{endpoint}"
                        return True
            return False
        except Exception as e:
            sys.stderr.write(f"Connection error: {e}\n")
            return False

    async def send_request(self, method: str, params: dict = None) -> dict:
        """Send JSON-RPC request to MCP server"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        try:
            response = await self.client.post(
                self.message_url,
                json=request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "error": {
                        "code": -32000,
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }

    async def handle_stdin(self):
        """Handle stdin messages from Claude Code"""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                request = json.loads(line.strip())
                method = request.get("method")
                params = request.get("params", {})

                # Forward request to SSE server
                response = await self.send_request(method, params)

                # Send response to stdout
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            except json.JSONDecodeError:
                continue
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")

    async def run(self):
        """Main run loop"""
        # Connect to SSE server
        if not await self.connect():
            sys.stderr.write("Failed to connect to MCP server\n")
            return

        sys.stderr.write(f"Connected to MCP server (session: {self.session_id})\n")

        # Initialize MCP connection
        init_response = await self.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "claude-code-proxy",
                    "version": "1.0.0"
                }
            }
        )

        sys.stderr.write(f"Initialization: {json.dumps(init_response, indent=2)}\n")

        # Start handling stdin
        await self.handle_stdin()


async def main():
    sse_url = "https://db8ss12906fjgalcbbtf.5p9km096.mcpgw.serverless.yandexcloud.net"
    proxy = MCPTrackerProxy(sse_url)
    await proxy.run()


if __name__ == "__main__":
    asyncio.run(main())
