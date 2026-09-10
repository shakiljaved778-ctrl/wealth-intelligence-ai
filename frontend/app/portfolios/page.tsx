"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, type Envelope, type Portfolio } from "@/lib/api";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";
import { EnvelopeView } from "@/components/EnvelopeView";

function PortfoliosInner() {
  const { lang } = useLang();
  const params = useSearchParams();
  const preselect = params.get("id");
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selected, setSelected] = useState<string | null>(preselect);
  const [env, setEnv] = useState<Envelope | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listPortfolios().then((p) => {
      setPortfolios(p);
      if (!selected && p[0]) setSelected(p[0].id);
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function analyze() {
    if (!selected) return;
    setLoading(true);
    try {
      // A standard rate + FX stress scenario, marked speculative by the backend.
      const scenarios: { name: string; shocks: Record<string, number> }[] = [
        { name: "rate_shock", shocks: { rates_bps: 100 } },
        { name: "fx_shock", shocks: { fx_usd_pct: 5 } },
      ];
      setEnv(await api.analyzePortfolio(selected, lang, scenarios));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>{t("portfolios", lang)}</h1>
      <div className="card" style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <select value={selected ?? ""} onChange={(e) => setSelected(e.target.value)}>
          {portfolios.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button onClick={analyze} disabled={loading || !selected}>
          {loading ? "…" : t("analyze", lang)}
        </button>
      </div>
      {env && <EnvelopeView env={env} />}
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
