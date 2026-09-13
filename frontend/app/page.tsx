"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, getToken, API_BASE, type Envelope, type Portfolio } from "@/lib/api";
import { useLang } from "./providers";
import { t } from "@/lib/i18n";
import { BarChart, type Bar } from "@/components/BarChart";
import { InsightList, type Insight } from "@/components/InsightList";

const FACTOR_ORDER = ["value", "growth", "momentum", "quality", "size", "volatility"];

export default function Dashboard() {
  const { lang } = useLang();
  const [authed, setAuthed] = useState(false);
  const [email, setEmail] = useState("demo@wealthintelligence.ai");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");

  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [env, setEnv] = useState<Envelope | null>(null);
  const [loading, setLoading] = useState(false);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [fav, setFav] = useState(false);
  const [reportMsg, setReportMsg] = useState("");

  const [remoteHost, setRemoteHost] = useState(false);

  useEffect(() => setAuthed(!!getToken()), []);
  useEffect(() => {
    // Deployed (non-local) host? Computed client-side to avoid hydration mismatch.
    const h = window.location.hostname;
    setRemoteHost(!["localhost", "127.0.0.1", "0.0.0.0", ""].includes(h));
  }, []);

  // Classic "deployed but nothing loads": the build never received the API URL,
  // so the browser is trying to call the visitor's own machine.
  const apiPointsLocal = /localhost|127\.0\.0\.1/.test(API_BASE);
  const apiMisconfigured = remoteHost && apiPointsLocal;

  useEffect(() => {
    if (!authed) return;
    api.listPortfolios().then((p) => {
      setPortfolios(p);
      if (p[0]) setSelected(p[0].id);
    });
  }, [authed]);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setFav(false);
    api
      .analyzePortfolio(selected, lang, [
        { name: "rate_shock", shocks: { rates_bps: 100 } },
        { name: "oil_shock", shocks: { oil_pct: -20 } },
      ])
      .then(setEnv)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [selected, lang]);

  const derived = useMemo(() => {
    const by: Record<string, Record<string, number>> = {};
    for (const d of env?.derived ?? []) by[d.metric] = (d.value ?? {}) as Record<string, number>;
    return by;
  }, [env]);

  const factorBars: Bar[] = useMemo(() => {
    const f = derived["factor_exposure"] ?? {};
    return FACTOR_ORDER.filter((k) => !hidden.has(k) && k in f).map((k) => ({
      label: k[0].toUpperCase() + k.slice(1),
      value: Number(f[k] ?? 0),
    }));
  }, [derived, hidden]);

  const insights: Insight[] = useMemo(() => {
    const out: Insight[] = [];
    const c = derived["concentration"];
    if (c)
      out.push({
        tile: "C",
        stat: `HHI ${(c.hhi ?? 0).toFixed(2)}`,
        pct: `${(c.effective_holdings ?? 0).toFixed(1)} eff.`,
        label: `Concentration · top-1 ${((c.top1_weight ?? 0) * 100).toFixed(0)}%`,
      });
    const dr = derived["downside_risk"];
    if (dr && dr.annualized_vol != null)
      out.push({
        tile: "R",
        stat: `Vol ${((dr.annualized_vol ?? 0) * 100).toFixed(1)}%`,
        pct: `MDD ${((dr.max_drawdown ?? 0) * 100).toFixed(1)}%`,
        label: `Downside risk · VaR ${((dr.var ?? 0) * 100).toFixed(1)}%`,
      });
    const f = derived["factor_exposure"];
    if (f) {
      const top = Object.entries(f).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];
      if (top)
        out.push({
          tile: "F",
          stat: `${top[0][0].toUpperCase() + top[0].slice(1)} ${top[1].toFixed(2)}`,
          label: "Largest factor tilt",
        });
    }
    for (const s of env?.derived ?? [])
      if (s.metric.startsWith("scenario:")) {
        const v = (s.value as Record<string, number>).estimated_return ?? 0;
        out.push({
          tile: "S",
          stat: `${(v * 100).toFixed(1)}%`,
          label: `Scenario: ${s.metric.replace("scenario:", "")} (speculative)`,
        });
      }
    return out;
  }, [derived, env]);

  async function requestReport() {
    setReportMsg("");
    try {
      await api.requestReport({
        kind: "portfolio_analysis",
        subject_type: "portfolio",
        subject_id: selected,
        language: lang,
      });
      setReportMsg(lang === "ar" ? "تم طلب التقرير" : "Report requested");
    } catch (e) {
      setReportMsg(String(e));
    }
  }

  async function doLogin() {
    try {
      await api.login(email, password);
      setAuthed(true);
      setError("");
    } catch (e) {
      setError(String(e));
    }
  }

  if (!authed) {
    return (
      <div className="card" style={{ maxWidth: 420, marginTop: 24 }}>
        <h2>{t("login", lang)}</h2>
        <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            placeholder="password"
          />
          <button onClick={doLogin}>{t("login", lang)}</button>
          {error && <p className="muted">{error}</p>}
          {apiMisconfigured && <p className="notice">{t("apiMisconfigured", lang)}</p>}
          <p className="muted" style={{ marginBottom: 0 }}>
            {t("apiEndpoint", lang)}: <code>{API_BASE}</code>
          </p>
        </div>
      </div>
    );
  }

  const pf = portfolios.find((p) => p.id === selected);

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18, flexWrap: "wrap" }}>
        <div style={{ marginInlineEnd: "auto" }}>
          <h1>{t("dashboard", lang)}</h1>
          <p className="muted">{t("insightSubtitle", lang)}</p>
        </div>
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          {portfolios.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button className="secondary" onClick={() => setFav((v) => !v)}>
          {fav ? "★" : "☆"} {t("addFavourite", lang)}
        </button>
        <button onClick={requestReport}>
          {t("downloadReport", lang)}
          <span className="icon-btn" aria-hidden style={{ width: 22, height: 22 }}>↓</span>
        </button>
      </div>
      {reportMsg && <p className="muted" style={{ marginTop: -8, marginBottom: 12 }}>{reportMsg}</p>}

      <div className="insight-shell">
        <InsightList title={t("insightList", lang)} items={insights} />

        <div>
          <section className="card">
            <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
              <h2 style={{ marginInlineEnd: "auto" }}>{t("insight", lang)}</h2>
              <span className="muted">{pf ? `${pf.name} · ${pf.base_currency}` : ""}</span>
            </div>

            {/* factor chips (removable) — SageExpress "Factors" row */}
            <div className="chip-row" style={{ margin: "12px 0 16px" }}>
              {FACTOR_ORDER.map((k) => (
                <button
                  key={k}
                  className="chip"
                  onClick={() =>
                    setHidden((h) => {
                      const next = new Set(h);
                      next.has(k) ? next.delete(k) : next.add(k);
                      return next;
                    })
                  }
                  style={{ opacity: hidden.has(k) ? 0.4 : 1 }}
                  title={hidden.has(k) ? "Show factor" : "Hide factor"}
                >
                  {k[0].toUpperCase() + k.slice(1)} <span className="x">×</span>
                </button>
              ))}
            </div>

            {loading ? (
              <p className="muted">…</p>
            ) : (
              <BarChart
                data={factorBars}
                mode="polarity"
                height={220}
                title={t("factorExposure", lang) + " (−1 … +1)"}
              />
            )}
          </section>

          {/* the AI insight (narrative) */}
          {env?.narrative?.[0] && (
            <section className="card">
              <span className="badge narrative">{t("narrative", lang)}</span>
              <p style={{ whiteSpace: "pre-wrap", marginTop: 10 }}>{env.narrative[0].text}</p>
              {env.disclaimers[0] && <p className="disclaimer">{env.disclaimers[0]}</p>}
              {env.audit_record_id && (
                <p className="muted">
                  {t("auditTrail", lang)}: <code>{env.audit_record_id}</code>
                </p>
              )}
            </section>
          )}
        </div>
      </div>

      <section className="card" style={{ marginTop: 4 }}>
        <h3>{t("assets", lang)}</h3>
        <p className="muted" style={{ marginBottom: 0 }}>
          {t("deepDive", lang)}:{" "}
          {["NVDA", "AAPL", "MSFT", "SPY", "QNBK", "BRENT"].map((s, i) => (
            <span key={s}>
              {i > 0 && " · "}
              <Link href={`/assets/${s}`}>{s}</Link>
            </span>
          ))}
        </p>
      </section>
    </div>
  );
}
