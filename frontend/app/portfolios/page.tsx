"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, type Envelope, type Portfolio } from "@/lib/api";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";
import { EnvelopeView } from "@/components/EnvelopeView";
import { BarChart, type Bar } from "@/components/BarChart";
import { InsightList, type Insight } from "@/components/InsightList";

const FACTOR_ORDER = ["value", "growth", "momentum", "quality", "size", "volatility"];

function PortfoliosInner() {
  const { lang } = useLang();
  const params = useSearchParams();
  const preselect = params.get("id");
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selected, setSelected] = useState<string>(preselect ?? "");
  const [env, setEnv] = useState<Envelope | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportMsg, setReportMsg] = useState("");

  useEffect(() => {
    api.listPortfolios().then((p) => {
      setPortfolios(p);
      setSelected((cur) => cur || p[0]?.id || "");
    });
  }, []);

  async function analyze() {
    if (!selected) return;
    setLoading(true);
    try {
      setEnv(
        await api.analyzePortfolio(selected, lang, [
          { name: "rate_shock", shocks: { rates_bps: 100 } },
          { name: "fx_shock", shocks: { fx_usd_pct: 5 } },
        ]),
      );
    } finally {
      setLoading(false);
    }
  }

  async function downloadReport() {
    if (!selected) return;
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

  const derived = useMemo(() => {
    const by: Record<string, Record<string, number>> = {};
    for (const d of env?.derived ?? []) by[d.metric] = (d.value ?? {}) as Record<string, number>;
    return by;
  }, [env]);

  const factorBars: Bar[] = useMemo(() => {
    const f = derived["factor_exposure"] ?? {};
    return FACTOR_ORDER.filter((k) => k in f).map((k) => ({
      label: k[0].toUpperCase() + k.slice(1),
      value: Number(f[k] ?? 0),
    }));
  }, [derived]);

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

  const pf = portfolios.find((p) => p.id === selected);

  return (
    <div>
      <div className="page-head">
        <div className="grow">
          <h1>{t("portfolios", lang)}</h1>
          <p className="muted">{t("portfoliosSubtitle", lang)}</p>
        </div>
        <div className="controls">
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            {portfolios.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <button onClick={analyze} disabled={loading || !selected}>
            {loading ? "…" : t("analyze", lang)}
          </button>
          <button className="secondary" onClick={downloadReport} disabled={!selected}>
            {t("downloadReport", lang)}
          </button>
        </div>
      </div>
      {reportMsg && <p className="muted" style={{ marginTop: -8, marginBottom: 12 }}>{reportMsg}</p>}

      {/* holdings */}
      {pf && (
        <section className="card">
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <h3 style={{ marginInlineEnd: "auto" }}>{t("holdings", lang)}</h3>
            <span className="muted">
              {pf.kind} · {pf.base_currency} · {pf.positions.length}
            </span>
          </div>
          <div style={{ marginTop: 8 }}>
            {pf.positions.map((p, i) => (
              <div className="kv" key={i}>
                <code>{p.asset_id}</code>
                <span className="muted">{p.quantity.toLocaleString()} units</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* analysis */}
      {env && (
        <div className="insight-shell">
          <InsightList title={t("insightList", lang)} items={insights} />
          <div>
            <section className="card">
              <h2>{t("factorExposure", lang)}</h2>
              <div style={{ marginTop: 12 }}>
                <BarChart data={factorBars} mode="polarity" height={220} title="−1 … +1" />
              </div>
            </section>
            <EnvelopeView env={env} />
          </div>
        </div>
      )}
    </div>
  );
}

export default function PortfoliosPage() {
  return (
    <Suspense fallback={<p className="muted">…</p>}>
      <PortfoliosInner />
    </Suspense>
  );
}
