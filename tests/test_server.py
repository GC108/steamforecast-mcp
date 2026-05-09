"""Tests for the MCP tool functions (boxleiter math + calibration summary)."""
from __future__ import annotations

import pytest

from steamforecast_mcp.server import boxleiter_estimate, get_calibration_summary


def test_boxleiter_basic():
    out = boxleiter_estimate(review_count=1000, price_cents=2000)
    assert out["revenue_low_cents"] == 1000 * 30 * 2000
    assert out["revenue_median_cents"] == 1000 * 50 * 2000
    assert out["revenue_high_cents"] == 1000 * 63 * 2000
    assert out["revenue_low_cents"] < out["revenue_median_cents"] < out["revenue_high_cents"]
    assert "warning" in out
    assert "24%" in out["warning"]


def test_boxleiter_zero_reviews():
    out = boxleiter_estimate(review_count=0, price_cents=2000)
    assert out["revenue_median_cents"] == 0


def test_boxleiter_negative_rejected():
    with pytest.raises(ValueError):
        boxleiter_estimate(review_count=-1, price_cents=2000)
    with pytest.raises(ValueError):
        boxleiter_estimate(review_count=1000, price_cents=-100)


def test_boxleiter_dollar_helpers_match_cents():
    out = boxleiter_estimate(review_count=500, price_cents=1500)
    assert out["revenue_low_dollars"] == out["revenue_low_cents"] / 100
    assert out["revenue_median_dollars"] == out["revenue_median_cents"] / 100


def test_calibration_summary_shape():
    s = get_calibration_summary()
    assert s["aggregate_coverage_pct"] == 88.4
    assert s["n_forecasts"] == 11921
    assert s["target_coverage_pct"] == 80.0
    assert len(s["per_stratum"]) == 5
    for stratum in s["per_stratum"]:
        assert stratum["coverage_pct"] >= 80.0
        assert stratum["n"] > 0
        assert stratum["in_cone"] <= stratum["n"]
    total_n = sum(st["n"] for st in s["per_stratum"])
    assert total_n == s["n_forecasts"]
