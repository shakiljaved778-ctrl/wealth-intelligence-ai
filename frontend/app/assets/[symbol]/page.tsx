"use client";
import { useState } from "react";
import { api, type Envelope } from "@/lib/api";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";
import { EnvelopeView } from "@/components/EnvelopeView";

export default function AssetDeepDive({ params }: { params: { symbol: string } }) {
  const { symbol } = params;
  const { lang } = useLang();
  const [env, setEnv] = useState<Envelope | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
      <h1>{symbol.toUpperCase()}</h1>
      <button onClick={run} disabled={loading}>
        {loading ? "…" : t("deepDive", lang)}
      </button>
      {error && <p className="muted">{error}</p>}
      <div style={{ marginTop: 16 }}>{env && <EnvelopeView env={env} />}</div>
    </div>
  );
}
