"""Steam Launch Forecaster MCP server.

Exposes calibrated Steam revenue forecasts to Claude, ChatGPT, and other
MCP-aware AI agents as tool calls.
"""
from steamforecast_mcp.server import mcp

__version__ = "0.1.0"
__all__ = ["mcp"]
