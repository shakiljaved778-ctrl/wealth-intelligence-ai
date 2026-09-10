"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, getToken, type Portfolio } from "@/lib/api";
import { useLang } from "./providers";
import { t } from "@/lib/i18n";

export default function Dashboard() {
  const { lang } = useLang();
  const [authed, setAuthed] = useState(false);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [email, setEmail] = useState("demo@wealthintelligence.ai");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");

  useEffect(() => {
    setAuthed(!!getToken());
  }, []);

  useEffect(() => {
    if (!authed) return;
    api.listPortfolios().then(setPortfolios).catch((e) => setError(String(e)));
  }, [authed]);

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
      <div className="card" style={{ maxWidth: 420 }}>
        <h2>{t("login", lang)}</h2>
        <div style={{ display: "grid", gap: 10 }}>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            placeholder="password"
          />
          <button onClick={doLogin}>{t("login", lang)}</button>
          {error && <p className="muted">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1>{t("dashboard", lang)}</h1>
      <div className="grid">
        {portfolios.map((p) => (
          <div className="card" key={p.id}>
            <h3>{p.name}</h3>
            <p className="muted">
              {p.kind} · {p.base_currency} · {p.positions.length} positions
            </p>
            <Link className="btn" href={`/portfolios?id=${p.id}`}>
              {t("riskMetrics", lang)} →
            </Link>
          </div>
        ))}
        {portfolios.length === 0 && <p className="muted">No portfolios yet.</p>}
      </div>

      <div className="card">
        <h3>{t("assets", lang)}</h3>
        <p className="muted">
          Search any asset for an {t("deepDive", lang)}:{" "}
          <Link href="/assets/NVDA">NVDA</Link>, <Link href="/assets/AAPL">AAPL</Link>,{" "}
          <Link href="/assets/SPY">SPY</Link>, <Link href="/assets/QNBK">QNBK</Link>
        </p>
      </div>
    </div>
  );
}
