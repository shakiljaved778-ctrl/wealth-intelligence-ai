"""Tests for the platform's non-negotiable invariants."""

from datetime import UTC

import pytest

from app.services.data.connectors import ingest_asset


def test_no_crypto_ingest():
    with pytest.raises(ValueError, match="crypto"):
        ingest_asset(symbol="BTC-USD", name="Bitcoin", asset_class="equity", metadata={"is_crypto": True})


def test_no_leverage_ingest():
    with pytest.raises(ValueError, match="leverage|leveraged"):
        ingest_asset(
            symbol="TQQQ", name="ProShares UltraPro QQQ 3x", asset_class="etf", metadata={"leverage_factor": 3}
        )


def test_raw_prices_are_append_only():
    """Repository exposes no update/delete for raw facts; corrections are new versions."""
    from app.repository import Repository

    assert not hasattr(Repository, "update_price")
    assert not hasattr(Repository, "delete_price")


def test_latest_prices_prefers_newest_version():
    from datetime import datetime

    from app.models import PriceBar
    from app.repository.memory import Repository

    r = Repository()
    ts = datetime(2025, 1, 1, tzinfo=UTC)
    r.append_prices([PriceBar(asset_id="a", ts=ts, open=1, high=1, low=1, close=10, volume=1, source="v1", version=1)])
    # a correction arrives as a NEW version, original retained
    r.append_prices([PriceBar(asset_id="a", ts=ts, open=1, high=1, low=1, close=11, volume=1, source="v2", version=2)])
    bars = r.latest_prices("a")
    assert len(bars) == 1 and bars[0].close == 11  # newest version wins
    assert len(r._prices["a"]) == 2  # original NOT overwritten
