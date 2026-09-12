"use client";
import { useEffect, useState } from "react";
import { api, type Envelope } from "@/lib/api";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";
import { EnvelopeView } from "@/components/EnvelopeView";
import { BarChart, type Bar } from "@/components/BarChart";

export default function AssetDeepDive({ params }: { params: { symbol: string } }) {
  const { symbol } = params;
  const { lang } = useLang();
  const [env, setEnv] = useState<Envelope | null>(null);
  const [prices, setPrices] = useState<Bar[]>([]);
  const [currency, setCurrency] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Price history is observed data — show it as a magnitude chart on load.
  useEffect(() => {
    api
      .getPrices(symbol, 60)
      .then((p) => {
        setCurrency(p.currency);
        // sample ~20 points so bars stay legible
        const step = Math.max(1, Math.floor(p.bars.length / 20));
        setPrices(
          p.bars
            .filter((_, i) => i % step === 0)
            .map((b) => ({ label: new Date(b.ts).toLocaleDateString(undefined, { month: "short", day: "numeric" }), value: b.close })),
        );
      })
      .catch(() => setPrices([]));
  }, [symbol]);

  async function run() {
    setLoading(true);
    setError("");
    try {
      setEnv(await api.deepDive(symbol, lang));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <h1 style={{ marginInlineEnd: "auto" }}>{symbol.toUpperCase()}</h1>
        <button onClick={run} disabled={loading}>
          {loading ? "…" : t("deepDive", lang)}
        </button>
      </div>

      {prices.length > 0 && (
        <section className="card">
          <BarChart
            data={prices}
            mode="magnitude"
            height={200}
            unit={currency ? ` ${currency}` : ""}
            title={t("priceHistory", lang)}
          />
        </section>
      )}

      {error && <p className="muted">{error}</p>}
      {env && <EnvelopeView env={env} />}
    </div>
  );
}
