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
        self.client = None
        self.initialized = False

    async def ensure_connected(self):
        """Ensure connection to SSE server"""
        if self.session_id:
            return True

        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)

        try:
            sys.stderr.write(f"[MCP Proxy] Connecting to {self.sse_url}/sse...\n")
            sys.stderr.flush()

            # Get session endpoint from SSE
            response = await self.client.get(
                f"{self.sse_url}/sse",
                headers={"Accept": "text/event-stream"}
            )

            sse_data = response.text
            sys.stderr.write(f"[MCP Proxy] SSE response received: {len(sse_data)} bytes\n")
            sys.stderr.flush()

            # Parse session ID from SSE response
            for line in sse_data.split('\n'):
                line = line.strip()
                if line.startswith('data:'):
                    endpoint = line[5:].strip()  # Remove 'data:' prefix
                    sys.stderr.write(f"[MCP Proxy] Endpoint: {endpoint}\n")
                    sys.stderr.flush()

                    if 'sessionId=' in endpoint:
                        self.session_id = endpoint.split('sessionId=')[1].strip()
                        self.message_url = f"{self.sse_url}{endpoint}"
                        sys.stderr.write(f"[MCP Proxy] Connected! Session: {self.session_id}\n")
                        sys.stderr.write(f"[MCP Proxy] Message URL: {self.message_url}\n")
                        sys.stderr.flush()
                        return True

            sys.stderr.write("[MCP Proxy] ERROR: No session ID found in SSE response\n")
            sys.stderr.flush()
            return False

        except Exception as e:
            sys.stderr.write(f"[MCP Proxy] Connection error: {e}\n")
            sys.stderr.flush()
            return False

    async def send_request(self, method: str, params: dict = None, req_id = None) -> dict:
        """Send JSON-RPC request to MCP server"""
        if not await self.ensure_connected():
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32001,
                    "message": "Failed to connect to MCP server"
                }
            }

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": req_id if req_id is not None else self.request_id,
            "method": method,
            "params": params or {}
        }

        try:
            sys.stderr.write(f"[MCP Proxy] Sending {method} request...\n")
            sys.stderr.flush()

            response = await self.client.post(
                self.message_url,
                json=request,
                headers={"Content-Type": "application/json"}
            )

            sys.stderr.write(f"[MCP Proxy] Response status: {response.status_code}\n")
            sys.stderr.flush()

            if response.status_code == 200:
                result = response.json()
                sys.stderr.write(f"[MCP Proxy] Success: {json.dumps(result)[:200]}...\n")
                sys.stderr.flush()
                return result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                sys.stderr.write(f"[MCP Proxy] Error: {error_msg}\n")
                sys.stderr.flush()
                return {
                    "jsonrpc": "2.0",
                    "id": req_id if req_id is not None else self.request_id,
                    "error": {
                        "code": -32000,
                        "message": error_msg
                    }
                }
        except Exception as e:
            error_msg = str(e)
            sys.stderr.write(f"[MCP Proxy] Exception: {error_msg}\n")
            sys.stderr.flush()
            return {
                "jsonrpc": "2.0",
                "id": req_id if req_id is not None else self.request_id,
                "error": {
                    "code": -32000,
                    "message": error_msg
                }
            }

    async def handle_stdin(self):
        """Handle stdin messages from Claude Code"""
        sys.stderr.write("[MCP Proxy] Started, waiting for requests on stdin...\n")
        sys.stderr.flush()

        while True:
            try:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    sys.stderr.write("[MCP Proxy] EOF on stdin, exiting\n")
                    sys.stderr.flush()
                    break

                line = line.strip()
                if not line:
                    continue

                sys.stderr.write(f"[MCP Proxy] Received request: {line[:100]}...\n")
                sys.stderr.flush()

                # Parse JSON-RPC request
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                req_id = request.get("id")

                # Forward request to SSE server
                response = await self.send_request(method, params, req_id)

                # Send response to stdout
                response_str = json.dumps(response)
                sys.stdout.write(response_str + "\n")
                sys.stdout.flush()

                sys.stderr.write(f"[MCP Proxy] Sent response: {response_str[:100]}...\n")
                sys.stderr.flush()

            except json.JSONDecodeError as e:
                sys.stderr.write(f"[MCP Proxy] JSON decode error: {e}\n")
                sys.stderr.flush()
                continue
            except Exception as e:
                sys.stderr.write(f"[MCP Proxy] Error: {e}\n")
                sys.stderr.flush()

    async def run(self):
        """Main run loop"""
        try:
            await self.handle_stdin()
        finally:
            if self.client:
                await self.client.aclose()


async def main():
    sse_url = "https://db8ss12906fjgalcbbtf.5p9km096.mcpgw.serverless.yandexcloud.net"
    proxy = MCPTrackerProxy(sse_url)
    await proxy.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.stderr.write("\n[MCP Proxy] Interrupted by user\n")
        sys.stderr.flush()
