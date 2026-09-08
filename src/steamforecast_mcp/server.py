"""MCP server exposing SteamForecast (the Steam launch forecaster) tools to AI agents.

Five tools are registered:
  - get_forecast(appid)       — calibrated P10/P50/P90 revenue cone
  - get_comps(appid, k)        — top-K nearest-neighbor comparable games
  - boxleiter_estimate(...)   — pure-compute rule-of-thumb sanity check
  - get_calibration_summary() — current live coverage table summary
  - get_methodology()         — link card + summary of how the forecaster works

Calibration numbers in get_calibration_summary are sourced from the latest
quarterly report. They refresh slowly (per-quarter); the live daily-updated
table is at https://steamforecast.app/methodology.
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from steamforecast_mcp.client import SteamforecastClient

mcp = FastMCP("steamforecast")
_client = SteamforecastClient()

# Boxleiter rule-of-thumb multiplier brackets (sales per Steam review).
# Documented bias: ~24% of games are off by >30% per the rule's own author.
BOXLEITER_LOW = 30
BOXLEITER_MEDIAN = 50
BOXLEITER_HIGH = 63


@mcp.tool()
async def get_forecast(
    appid: int,
    wishlist: int | None = None,
    followers: int | None = None,
) -> dict[str, Any]:
    """Fetch a calibrated P10–P90 revenue cone for a Steam game by appid.

    Uses the same v1.1 model that powers the public steamforecast.app site.
    Returns a JSON object with cone bounds in cents + dollars, the model
    version, the genre cluster used for stratified calibration, and links
    back to the methodology page + latest calibration report.

    Args:
        appid: Steam app ID (e.g. 1145360 for Hades).
        wishlist: Optional override for catalog wishlist count (what-if mode).
        followers: Optional override for catalog SteamCommunity follower count.

    Returns:
        Dict with appid, name, genres, p10/p50/p90 revenue, methodology URL.

    Raises:
        httpx.HTTPStatusError: 404 if appid not in v1.1 catalog (~49K apps);
        503 if forecast model is briefly unloaded during a deploy.
    """
    return await _client.get_forecast(appid, wishlist=wishlist, followers=followers)


@mcp.tool()
async def get_comps(appid: int, k: int = 5) -> dict[str, Any]:
    """Fetch top-K nearest-neighbor comparable Steam games for an appid.

    Comps are surfaced via pgvector cosine-similarity over a 1024-dim BGE
    embedding of game metadata (genres, tags, language, platform support,
    multiplayer features). Useful for sanity-checking a forecast: if the
    nearest comps cluster in a tight revenue band, the cone is likely
    well-anchored; if they're dispersed, the cone correctly widens.

    Args:
        appid: Steam app ID to find comps for.
        k: Number of comps to return (1-20, default 5).

    Returns:
        Dict with appid + list of comps, each including release year,
        price, follower count, week-1 + lifetime revenue, cosine similarity.
    """
    return await _client.get_comps(appid, k=k)


@mcp.tool()
def boxleiter_estimate(review_count: int, price_cents: int) -> dict[str, Any]:
    """Apply the Boxleiter rule-of-thumb (review_count × multiplier × price).

    A heuristic sanity check, NOT a calibrated forecast. Per the formula's
    own author (Mike Boxleiter, 2023 retrospective), ~24% of games are off
    by more than 30% from a single-multiplier estimate. Useful to compare
    against get_forecast() — large divergence between the heuristic and
    the calibrated cone signals an interesting outlier worth investigating.

    Args:
        review_count: Total Steam reviews on the game's page.
        price_cents: List price in cents (e.g. 2499 for $24.99).

    Returns:
        Dict with low (×30) / median (×50) / high (×63) revenue brackets
        in cents + dollars + a calibration warning.
    """
    if review_count < 0 or price_cents < 0:
        raise ValueError("review_count and price_cents must be non-negative")
    low = review_count * BOXLEITER_LOW * price_cents
    median = review_count * BOXLEITER_MEDIAN * price_cents
    high = review_count * BOXLEITER_HIGH * price_cents
    return {
        "review_count": review_count,
        "price_cents": price_cents,
        "revenue_low_cents": low,
        "revenue_median_cents": median,
        "revenue_high_cents": high,
        "revenue_low_dollars": round(low / 100, 2),
        "revenue_median_dollars": round(median / 100, 2),
        "revenue_high_dollars": round(high / 100, 2),
        "multipliers": {"low": BOXLEITER_LOW, "median": BOXLEITER_MEDIAN, "high": BOXLEITER_HIGH},
        "warning": (
            "Heuristic only. ~24% of games are off by >30% per the Boxleiter "
            "formula's own author. For a calibrated launch cone (~82% nominal "
            "coverage, 81-86% realized per wishlist tier on 6,422 held-out "
            "launches), see get_forecast() or "
            "https://steamforecast.app/methodology"
        ),
    }


@mcp.tool()
def get_calibration_summary() -> dict[str, Any]:
    """Return the latest published live calibration coverage summary.

    Numbers are from the Q2 2026 quarterly report. Live-refreshed table
    is at https://steamforecast.app/methodology — fetch get_methodology()
    for the canonical current values.

    Returns:
        Dict with aggregate coverage, per-stratum coverage table, sample
        sizes, and link to the live page + quarterly report.
    """
    return {
        "report_version": "Q2-2026",
        "report_url": "https://steamforecast.app/reports/calibration-gap-q2-2026",
        "live_url": "https://steamforecast.app/methodology",
        "as_of": "2026-05-09",
        "n_forecasts": 11921,
        "aggregate_coverage_pct": 88.4,
        "target_coverage_pct": 80.0,
        "per_stratum": [
            {"stratum": "action_arcade", "n": 5246, "in_cone": 4611, "coverage_pct": 87.9},
            {"stratum": "strategy_sim", "n": 3865, "in_cone": 3450, "coverage_pct": 89.3},
            {"stratum": "rpg_adventure", "n": 2006, "in_cone": 1757, "coverage_pct": 87.6},
            {"stratum": "casual_puzzle", "n": 453, "in_cone": 409, "coverage_pct": 90.3},
            {"stratum": "other", "n": 351, "in_cone": 309, "coverage_pct": 88.0},
        ],
        "note": (
            "Coverage = fraction of forecasts where realized week-1 revenue "
            "fell inside the predicted P10-P90 cone. Target was 80%; "
            "every stratum overshoots, meaning cones are slightly wider than "
            "needed (the safer failure mode for budget planning)."
        ),
    }


@mcp.tool()
async def get_methodology() -> str:
    """Return the AI-crawler-friendly methodology summary (llms.txt).

    Pulls the canonical content discovery file from steamforecast.app/llms.txt,
    which lists high-quality URLs (methodology, guides, reports, tools) for
    AI agents to ingest. Useful when a model wants the full sitemap of
    authoritative content rather than a single forecast.

    Returns:
        Plaintext content of /llms.txt (markdown-formatted per llmstxt.org).
    """
    return await _client.get_llms_txt()
