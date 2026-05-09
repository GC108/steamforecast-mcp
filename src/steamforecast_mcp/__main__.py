"""stdio entrypoint: `steamforecast-mcp` runs the MCP server on stdin/stdout.

Used by MCP clients (Claude Desktop, Claude Code, etc.) configured to launch
the server as a subprocess.
"""
from steamforecast_mcp.server import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
