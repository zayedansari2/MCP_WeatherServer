# weather — Minimal MCP server demo

<img width="1123" height="869" alt="Screenshot 2025-11-15 at 6 37 38 PM" src="https://github.com/user-attachments/assets/717f5316-8553-4d96-a139-93d56ba17b3e" />

<img width="318" height="245" alt="Screenshot 2025-11-15 at 7 23 28 PM" src="https://github.com/user-attachments/assets/ac1a0203-d479-4a26-aa33-1392c84f2f1b" />


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
