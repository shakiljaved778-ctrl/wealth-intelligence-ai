"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";

interface ReportRow {
  id: string;
  kind: string;
  subject_id: string;
  language: string;
  status: string;
}

export default function ReportsPage() {
  const { lang } = useLang();
  const [reports, setReports] = useState<ReportRow[]>([]);
  const [subject, setSubject] = useState("NVDA");

  async function refresh() {
    setReports((await api.listReports()) as ReportRow[]);
  }
  useEffect(() => {
    refresh();
  }, []);

  async function request() {
    await api.requestReport({
      kind: "client_report",
      subject_type: "asset",
      subject_id: subject,
      language: lang,
    });
    setTimeout(refresh, 300); // generation runs async on the backend
  }

  return (
    <div>
      <h1>{t("reports", lang)}</h1>
      <div className="card" style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="symbol" />
        <button onClick={request}>
          {t("reports", lang)} ({lang.toUpperCase()})
        </button>
        <button className="secondary" onClick={refresh}>
          ↻
        </button>
      </div>
      {reports.map((r) => (
        <div className="kv card" key={r.id}>
          <span>
            <code>{r.kind}</code> · {r.subject_id} · {r.language.toUpperCase()}
          </span>
          <span className="badge">{r.status}</span>
        </div>
      ))}
      {reports.length === 0 && <p className="muted">No reports yet.</p>}
    </div>
  );
}
