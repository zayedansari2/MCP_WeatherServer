# weather — Minimal MCP server demo

![Project image](assets/hero.png)

Short, hands-on MCP (Model Context Protocol) server demo that registers async tools for weather data (alerts and forecasts) using the NWS public APIs.

## Quick start

1. Install uv (macOS / Linux):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# restart your terminal
```

2. Create project, venv and install deps:

```bash
uv init weather
cd weather
uv venv
source .venv/bin/activate
uv add "mcp[cli]" httpx
```

3. Run the server:

```bash
uv run weather.py
```

## Files to check

- `weather.py` — MCP server (FastMCP), tools: `get_alerts(state)` and `get_forecast(lat,lon)`.
- `main.py` — tiny runner/entrypoint.

## Notes

- Python 3.11+ (see `pyproject.toml`).
- The server uses stdio transport by default; use an MCP client (Claude Desktop, `mcp` CLI, or another client) to send/receive messages.

## License

Apache License 2.0 — see `LICENSE`. Replace the placeholder year/name in `LICENSE` if needed.

---
