"""Process-local, in-memory store used by the scaffold."""

from __future__ import annotations

from app.models import (
    Alert,
    ApiKey,
    Asset,
    FundamentalSnapshot,
    Organization,
    Portfolio,
    PriceBar,
    Report,
    Signal,
    UsageRecord,
    User,
    Watchlist,
    Webhook,
)


class Repository:
    def __init__(self) -> None:
        self.organizations: dict[str, Organization] = {}
        self.users: dict[str, User] = {}
        self.assets: dict[str, Asset] = {}
        self.portfolios: dict[str, Portfolio] = {}
        self.signals: dict[str, Signal] = {}
        self.reports: dict[str, Report] = {}
        self.alerts: dict[str, Alert] = {}
        self.api_keys: dict[str, ApiKey] = {}
        self.watchlists: dict[str, Watchlist] = {}
        self.webhooks: dict[str, Webhook] = {}
        self.usage: list[UsageRecord] = []
        # Raw, append-only fact stores keyed by asset id.
        self._prices: dict[str, list[PriceBar]] = {}
        self._fundamentals: dict[str, list[FundamentalSnapshot]] = {}

    # ---- entities (mutable metadata) --------------------------------------
    def add_org(self, org: Organization) -> Organization:
        self.organizations[org.id] = org
        return org

    def add_user(self, user: User) -> User:
        self.users[user.id] = user
        return user

    def user_by_email(self, email: str) -> User | None:
        return next((u for u in self.users.values() if u.email == email), None)

    def add_asset(self, asset: Asset) -> Asset:
        self.assets[asset.id] = asset
        return asset

    def asset_by_symbol(self, symbol: str) -> Asset | None:
        return next((a for a in self.assets.values() if a.symbol.upper() == symbol.upper()), None)

    def search_assets(self, q: str | None, asset_class: str | None) -> list[Asset]:
        out = list(self.assets.values())
        if q:
            ql = q.lower()
            out = [a for a in out if ql in a.symbol.lower() or ql in a.name.lower()]
        if asset_class:
            out = [a for a in out if a.asset_class == asset_class]
        return out

    def add_portfolio(self, pf: Portfolio) -> Portfolio:
        self.portfolios[pf.id] = pf
        return pf

    def add_signal(self, sig: Signal) -> Signal:
        self.signals[sig.id] = sig
        return sig

    def add_report(self, rep: Report) -> Report:
        self.reports[rep.id] = rep
        return rep

    def add_alert(self, alert: Alert) -> Alert:
        self.alerts[alert.id] = alert
        return alert

    def add_api_key(self, key: ApiKey) -> ApiKey:
        self.api_keys[key.id] = key
        return key

    def api_key_by_hash(self, hashed: str) -> ApiKey | None:
        return next(
            (k for k in self.api_keys.values() if k.hashed_key == hashed and not k.revoked),
            None,
        )

    def add_watchlist(self, wl: Watchlist) -> Watchlist:
        self.watchlists[wl.id] = wl
        return wl

    def add_webhook(self, wh: Webhook) -> Webhook:
        self.webhooks[wh.id] = wh
        return wh

    def webhooks_for_event(self, org_id: str, event: str) -> list[Webhook]:
        return [w for w in self.webhooks.values() if w.organization_id == org_id and w.active and event in w.events]

    def record_usage(self, record: UsageRecord) -> None:
        self.usage.append(record)

    # ---- raw facts: APPEND-ONLY (no update / no delete) -------------------
    def append_prices(self, bars: list[PriceBar]) -> None:
        """Append raw price bars. Corrections must arrive as new versions."""
        for bar in bars:
            self._prices.setdefault(bar.asset_id, []).append(bar)

    def latest_prices(self, asset_id: str, limit: int = 260) -> list[PriceBar]:
        """Return the newest *version* per timestamp, most recent last."""
        by_ts: dict[str, PriceBar] = {}
        for bar in self._prices.get(asset_id, []):
            key = bar.ts.isoformat()
            if key not in by_ts or bar.version > by_ts[key].version:
                by_ts[key] = bar
        bars = sorted(by_ts.values(), key=lambda b: b.ts)
        return bars[-limit:]

    def append_fundamentals(self, snap: FundamentalSnapshot) -> None:
        self._fundamentals.setdefault(snap.asset_id, []).append(snap)

    def latest_fundamental(self, asset_id: str) -> FundamentalSnapshot | None:
        snaps = self._fundamentals.get(asset_id, [])
        if not snaps:
            return None
        return max(snaps, key=lambda s: (s.as_of, s.version))


repo = Repository()
