"use client";
// The product's signature UI: render observed / derived / narrative distinctly,
// with sources, methodology, citations, speculative markers, and the audit link.
import type { Envelope } from "@/lib/api";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";

export function EnvelopeView({ env }: { env: Envelope }) {
  const { lang } = useLang();
  return (
    <div>
      {/* OBSERVED — facts */}
      <section className="card">
        <span className="badge observed">{t("observed", lang)}</span>
        <div style={{ marginTop: 10 }}>
          {env.observed.length === 0 && <p className="muted">—</p>}
          {env.observed.map((o, i) => (
            <div className="kv" key={i}>
              <span>
                <code>{o.field}</code> {String(o.value)} {o.unit ?? ""}
              </span>
              <span className="muted">
                {t("source", lang)}: {o.source} · {new Date(o.as_of).toLocaleDateString()}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* DERIVED — computed metrics with exposed methodology */}
      <section className="card">
        <span className="badge derived">{t("derived", lang)}</span>
        <div style={{ marginTop: 10 }}>
          {env.derived.length === 0 && <p className="muted">—</p>}
          {env.derived.map((d, i) => (
            <div className="kv" key={i} style={{ flexDirection: "column", alignItems: "stretch" }}>
              <span>
                <code>{d.metric}</code> {JSON.stringify(d.value)}
              </span>
              <span className="muted">
                {t("methodology", lang)}: {d.methodology} · <code>{d.model_version}</code>
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* NARRATIVE — AI interpretation, cited, speculative flagged */}
      <section className="card">
        <span className="badge narrative">{t("narrative", lang)}</span>
        <div style={{ marginTop: 10 }}>
          {env.narrative.map((n, i) => (
            <div key={i} style={{ marginBottom: 12 }}>
              {n.speculative && (
                <span className="badge speculative">{t("speculative", lang)}</span>
              )}
              <p style={{ whiteSpace: "pre-wrap", margin: "6px 0" }}>{n.text}</p>
              {n.citations.length > 0 && (
                <p className="muted">
                  ↳ {n.citations.map((c) => (
                    <code key={c} style={{ marginInlineEnd: 6 }}>
                      {c}
                    </code>
                  ))}
                </p>
              )}
            </div>
          ))}
        </div>
      </section>

      {env.disclaimers.map((d, i) => (
        <p className="disclaimer" key={i}>
          {t("disclaimer", lang)}: {d}
        </p>
      ))}
      {env.audit_record_id && (
        <p className="muted">
          {t("auditTrail", lang)}: <code>{env.audit_record_id}</code>
        </p>
      )}
    </div>
  );
}
