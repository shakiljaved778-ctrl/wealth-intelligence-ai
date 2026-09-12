"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";

interface ReportRow {
  id: string;
  kind: string;
  subject_type: string;
  subject_id: string;
  language: string;
  status: string;
}

const KINDS = ["client_report", "deep_dive", "portfolio_analysis", "memo"];

export default function ReportsPage() {
  const { lang } = useLang();
  const [reports, setReports] = useState<ReportRow[]>([]);
  const [subject, setSubject] = useState("NVDA");
  const [kind, setKind] = useState("client_report");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setReports((await api.listReports()) as ReportRow[]);
  }
  useEffect(() => {
    refresh();
  }, []);

  async function request() {
    setBusy(true);
    try {
      await api.requestReport({
        kind,
        subject_type: kind === "portfolio_analysis" ? "portfolio" : "asset",
        subject_id: subject,
        language: lang,
      });
      setTimeout(refresh, 400); // generation runs async on the backend
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-head">
        <div className="grow">
          <h1>{t("reports", lang)}</h1>
          <p className="muted">{t("reportsSubtitle", lang)}</p>
        </div>
      </div>

      {/* request a report */}
      <section className="card">
        <div className="controls">
          <label className="muted" style={{ display: "grid", gap: 4 }}>
            {t("subjectSymbol", lang)}
            <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="NVDA" />
          </label>
          <label className="muted" style={{ display: "grid", gap: 4 }}>
            {t("kind", lang)}
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              {KINDS.map((k) => (
                <option key={k} value={k}>
                  {k.replace("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <span className="chip" style={{ alignSelf: "end" }}>
            {lang.toUpperCase()}
          </span>
          <button onClick={request} disabled={busy} style={{ alignSelf: "end" }}>
            {busy ? "…" : t("requestReport", lang)}
          </button>
          <button
            className="secondary icon-btn"
            onClick={refresh}
            title={t("refresh", lang)}
            aria-label={t("refresh", lang)}
            style={{ alignSelf: "end" }}
          >
            ↻
          </button>
        </div>
      </section>

      {/* report list */}
      {reports.length === 0 && <p className="muted">{t("noReports", lang)}</p>}
      {reports.map((r) => (
        <div className="insight-card" key={r.id} style={{ alignItems: "center" }}>
          <div className="tile">{r.language.toUpperCase()}</div>
          <div style={{ marginInlineEnd: "auto" }}>
            <div className="stat">{r.kind.replace("_", " ")}</div>
            <div className="muted">
              {r.subject_type}: {r.subject_id}
            </div>
          </div>
          <span className={`badge status-${r.status}`}>{r.status}</span>
        </div>
      ))}
    </div>
  );
}
