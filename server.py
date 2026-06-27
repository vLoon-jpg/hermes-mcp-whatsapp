"""
MCP server that gives Hermes the ability to initiate outbound WhatsApp calls
through a running Pipecat bot.

Usage:
  python server.py

Or in Hermes config.yaml:
  mcp_servers:
    whatsapp:
      command: "uv"
      args: ["run", "python", "C:/Users/LENOVO/projects/hermes-mcp-whatsapp/server.py"]
      env:
        PIPECAT_BOT_URL: "http://localhost:7860"
"""

import json
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server

# --- Configuration ---
BOT_URL = os.getenv("PIPECAT_BOT_URL", "http://localhost:7860")

server = Server("hermes-whatsapp-outbound")


@server.list_tools()
async def list_tools():
    return [
        {
            "name": "whatsapp_outbound_call",
            "description": (
                "Initiate an outbound WhatsApp voice call through the Pipecat bot. "
                "The bot will dial the target number and start a voice conversation. "
                "Requires the bot to have previously received an inbound call from "
                "this number (WhatsApp Business 7-day reply window). "
                "Use this when the user asks you to call someone on WhatsApp."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "to_number": {
                        "type": "string",
                        "description": (
                            "Target WhatsApp phone number in international format "
                            "without the '+' prefix. Example: '6281234567890'"
                        ),
                    },
                },
                "required": ["to_number"],
            },
        },
        {
            "name": "whatsapp_check_status",
            "description": (
                "Check if the Pipecat WhatsApp bot is running and reachable."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    import urllib.request
    import urllib.error

    if name == "whatsapp_check_status":
        try:
            req = urllib.request.Request(
                f"{BOT_URL}/whatsapp/outbound",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return [{"type": "text", "text": f"Bot is reachable at {BOT_URL} (status {resp.status})"}]
        except urllib.error.HTTPError as e:
            # 405 Method Not Allowed is fine — endpoint exists, just GET not POST
            if e.code == 405:
                return [{"type": "text", "text": f"Bot is reachable at {BOT_URL} — WhatsApp endpoint ready"}]
            return [{"type": "text", "text": f"Bot returned HTTP {e.code}: {e.reason}"}]
        except Exception as e:
            return [{
                "type": "text",
                "text": f"Bot is NOT reachable at {BOT_URL}: {e}\n\nMake sure the Pipecat bot is running with --whatsapp flag and the URL is correct.",
            }]

    elif name == "whatsapp_outbound_call":
        to_number = arguments["to_number"]
        payload = json.dumps({"to": to_number}).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"{BOT_URL}/whatsapp/outbound",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": result.get("success", False),
                        "call_id": result.get("call_id", "unknown"),
                        "to": result.get("to", to_number),
                        "message": (
                            f"Call initiated to {to_number}! "
                            f"Their WhatsApp should be ringing. "
                            f"Call ID: {result.get('call_id', 'unknown')}"
                        ),
                    }, indent=2),
                }]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else "No response body"
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": f"Bot returned HTTP {e.code}",
                    "detail": error_body,
                    "hint": "Make sure the bot is running and the target number has called in before (7-day window).",
                }, indent=2),
            }]
        except Exception as e:
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": str(e),
                    "hint": f"Is the Pipecat bot running at {BOT_URL}?",
                }, indent=2),
            }]

    else:
        return [{"type": "text", "text": f"Unknown tool: {name}"}]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
