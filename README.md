# Hermes MCP — WhatsApp Outbound Calls

MCP server that lets Hermes initiate outbound WhatsApp voice calls via Pipecat.

## Setup

```bash
pip install mcp
```

## Usage

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  whatsapp:
    command: "python"
    args: ["C:/Users/LENOVO/projects/hermes-mcp-whatsapp/server.py"]
    env:
      PIPECAT_BOT_URL: "http://localhost:7860"
```

Then restart Hermes. You'll get two tools:

- `mcp_whatsapp_whatsapp_outbound_call` — dial a WhatsApp number
- `mcp_whatsapp_whatsapp_check_status` — check if bot is reachable

## Requirements

- Pipecat bot running with `--whatsapp` flag at PIPECAT_BOT_URL
- WhatsApp Business API credentials configured on the bot
- Target number must have called in within last 7 days
