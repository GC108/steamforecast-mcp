# steamforecast-mcp

[![CI](https://github.com/GC108/steamforecast-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/GC108/steamforecast-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/steamforecast-mcp.svg)](https://pypi.org/project/steamforecast-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Model Context Protocol server for [SteamForecast][slf], the Steam launch
revenue forecaster. Exposes calibrated revenue cones (P10–P90; ~82% nominal
coverage, 81–86% realized per wishlist tier on 6,422 held-out launches) to
Claude, ChatGPT, and any MCP-aware AI agent as tool calls.

[slf]: https://steamforecast.app

## What it does

Five tools, all backed by the public steamforecast.app API:

| Tool | What it does |
|---|---|
| `get_forecast(appid)` | Calibrated P10/P50/P90 revenue cone for a Steam game by appid |
| `get_comps(appid, k)` | Top-K nearest-neighbor comparable games (cosine sim over BGE embeddings) |
| `boxleiter_estimate(review_count, price_cents)` | Pure-compute Boxleiter rule-of-thumb sanity check |
| `get_calibration_summary()` | Latest published live coverage table (per-stratum) |
| `get_methodology()` | Pulls llms.txt — high-quality URL inventory for ingestion |

`get_forecast` and `get_comps` make HTTPS calls to steamforecast.app. The
other three are pure compute / static reference, so they work offline once
the package is installed.

## Install

```bash
pip install steamforecast-mcp
```

## Configure your MCP client

### Claude Desktop / Claude Code

Add to your MCP config (typically `~/.claude.json` or
`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "steamforecast": {
      "command": "steamforecast-mcp"
    }
  }
}
```

Or via the Claude Code CLI:

```bash
claude mcp add steamforecast -- steamforecast-mcp
```

### Other MCP clients (Cursor, Cline, etc.)

Use the standard stdio MCP config; the executable is `steamforecast-mcp`
and takes no arguments.

## Quick usage

Once configured, ask your AI agent things like:

> *"Pull a calibrated revenue forecast for Hades on Steam (appid 1145360)
> and compare it to the Boxleiter rule of thumb. Are they consistent?"*

The agent will call `get_forecast(1145360)`, then call
`boxleiter_estimate(review_count, price_cents)` with values from the
forecast result, then surface the divergence to you.

> *"What's the live calibration coverage on the strategy_sim stratum?"*

The agent calls `get_calibration_summary()` and reads the `per_stratum`
table.

## Why a separate server when the website exists?

Because LLMs and AI agents shouldn't have to scrape HTML to use a
calibrated forecast. The MCP surface is structured (typed JSON), versioned,
and rate-limit-aware, which is the right contract for tool-using models.

It also lets you build automations without manually copying numbers from
the website into spreadsheets — e.g., a nightly Claude Code routine that
pulls a forecast for every appid in a publisher's portfolio and writes a
report.

## Configuration

| Env var | Purpose | Default |
|---|---|---|
| `STEAMFORECAST_BASE_URL` | Override the API base URL (useful for local dev / staging) | `https://steamforecast.app` |

## Development

```bash
git clone https://github.com/GC108/steamforecast-mcp
cd steamforecast-mcp
pip install -e ".[dev]"
pytest
ruff check .
```

## License

MIT — see [LICENSE](LICENSE).

## Related

- **[SteamForecast][slf]** — calibrated launch revenue cones (~82% nominal coverage, 81–86% realized per wishlist tier on 6,422 held-out launches).
- **[The Calibration Gap (Q2 2026 report)](https://steamforecast.app/reports/calibration-gap-q2-2026)** — methodology + live coverage evidence.
- **[steam-page-stats](https://github.com/GC108/steam-page-stats)** — companion OSS Python client for Steam Storefront + Boxleiter rule-of-thumb (no MCP, just a library + CLI).
- **[Model Context Protocol](https://modelcontextprotocol.io)** — the open standard this server implements.
