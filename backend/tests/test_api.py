"""End-to-end API tests over the three-layer envelope + audit trail."""


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_auth_required(client):
    assert client.get("/v1/portfolios").status_code == 401


def test_usable_without_lifespan():
    # Some serverless runtimes (e.g. Vercel's Python runtime) do not run ASGI
    # lifespan startup. create_app() seeds eagerly so the app is still usable.
    # A plain TestClient (no context manager) does NOT run lifespan — mirroring
    # that environment.
    from fastapi.testclient import TestClient

    from app.main import create_app

    c = TestClient(create_app())
    r = c.post(
        "/v1/auth/token",
        data={"username": "demo@wealthintelligence.ai", "password": "demo1234", "grant_type": "password"},
    )
    assert r.status_code == 200, "eager seed() must make login work without lifespan startup"
    assert r.json()["access_token"]


def test_deep_dive_returns_three_layer_envelope(client, auth_headers):
    r = client.post("/v1/assets/NVDA/deep-dive", json={"language": "en"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "observed" in body and "derived" in body and "narrative" in body
    assert body["observed"], "must carry observed facts with source + as_of"
    assert all("source" in o and "as_of" in o for o in body["observed"])
    assert body["disclaimers"], "client-facing output must carry a disclaimer"
    assert body["audit_record_id"], "every AI output must be auditable"


def test_audit_record_is_retrievable(client, auth_headers):
    r = client.post("/v1/assets/AAPL/deep-dive", json={"language": "en"}, headers=auth_headers)
    aid = r.json()["audit_record_id"]
    a = client.get(f"/v1/audit/{aid}", headers=auth_headers)
    assert a.status_code == 200
    rec = a.json()
    assert rec["models"], "audit record names the models/versions used"
    assert rec["inputs"], "audit record lists the observed inputs used"


def test_portfolio_analyze_has_derived_metrics(client, auth_headers):
    pf_id = client.get("/v1/portfolios", headers=auth_headers).json()[0]["id"]
    r = client.post(
        f"/v1/portfolios/{pf_id}/analyze",
        json={"language": "en", "scenarios": [{"name": "rate_shock", "shocks": {"rates_bps": 100}}]},
        headers=auth_headers,
    )
    assert r.status_code == 200
    metrics = {d["metric"] for d in r.json()["derived"]}
    assert "concentration" in metrics
    assert "factor_exposure" in metrics
    # scenario output is marked speculative in the narrative
    assert any(n.get("speculative") for n in r.json()["narrative"])


def test_signal_generation(client, auth_headers):
    r = client.post("/v1/signals/generate", json={"symbol": "SPY", "horizon": "swing"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["direction"] in ("long", "short", "neutral")
    assert body["risk_reward"] and body["audit_record_id"]


def test_arabic_report(client, auth_headers):
    r = client.post(
        "/v1/reports",
        json={"kind": "deep_dive", "subject_type": "asset", "subject_id": "NVDA", "language": "ar"},
        headers=auth_headers,
    )
    assert r.status_code == 202
    rid = r.json()["id"]
    got = client.get(f"/v1/reports/{rid}", headers=auth_headers).json()
    assert got["status"] in ("ready", "generating", "queued")


def test_portfolio_construction_respects_constraints(client, auth_headers):
    r = client.post(
        "/v1/portfolios/construct",
        json={"risk_profile": "growth", "max_position_weight": 0.4, "language": "en"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    tw = next(d for d in body["derived"] if d["metric"] == "target_weights")["value"]
    assert abs(sum(tw.values()) - 1.0) < 1e-6, "weights sum to 1"
    assert all(w <= 0.4 + 1e-6 for w in tw.values()), "max position weight enforced"
    assert body["audit_record_id"]


def test_watchlist_scan_raises_alerts_and_notifies_webhooks(client, auth_headers):
    # Register a webhook for alert.raised
    wh = client.post(
        "/v1/webhooks",
        json={"url": "https://example.test/hook", "events": ["alert.raised"]},
        headers=auth_headers,
    )
    assert wh.status_code == 201

    # Create a watchlist containing NVDA (which has filing/news evidence in the corpus)
    wl = client.post(
        "/v1/watchlists",
        json={"name": "Tech", "symbols": ["NVDA"]},
        headers=auth_headers,
    )
    assert wl.status_code == 201
    wl_id = wl.json()["id"]

    scan = client.post(f"/v1/watchlists/{wl_id}/scan", headers=auth_headers)
    assert scan.status_code == 200
    alerts = scan.json()
    assert any(a["severity"] in ("material", "critical") for a in alerts)

    # The raised alert is visible via the alerts endpoint
    listing = client.get("/v1/alerts", headers=auth_headers).json()
    assert any(a["id"] == alerts[0]["id"] for a in listing)


def test_webhook_lifecycle(client, auth_headers):
    created = client.post(
        "/v1/webhooks",
        json={"url": "https://example.test/h2", "events": ["report.ready"]},
        headers=auth_headers,
    ).json()
    assert created["active"] is True
    assert client.delete(f"/v1/webhooks/{created['id']}", headers=auth_headers).status_code == 204
    remaining = client.get("/v1/webhooks", headers=auth_headers).json()
    deleted = next(w for w in remaining if w["id"] == created["id"])
    assert deleted["active"] is False
