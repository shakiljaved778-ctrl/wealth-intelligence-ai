"""End-to-end API tests over the three-layer envelope + audit trail."""


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_auth_required(client):
    assert client.get("/v1/portfolios").status_code == 401


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
