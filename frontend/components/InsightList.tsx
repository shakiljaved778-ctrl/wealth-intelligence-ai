"use client";
// SageExpress-style "Insight List": a column of stat cards. Each card has a
// colored tile, a bold stat line, and a small label.

export interface Insight {
  tile: string; // 1-2 char glyph for the tile
  stat: string; // bold headline, e.g. "HHI 0.31"
  pct?: string; // optional green-accented figure, e.g. "3.6 eff. holdings"
  label: string; // small caption
}

export function InsightList({ title, items }: { title: string; items: Insight[] }) {
  return (
    <aside>
      <h3 style={{ marginBottom: 12 }}>{title}</h3>
      {items.length === 0 && <p className="muted">No insights yet.</p>}
      {items.map((it, i) => (
        <div className="insight-card" key={i}>
          <div className="tile">{it.tile}</div>
          <div>
            <div className="stat">
              {it.stat} {it.pct && <span className="pct">{it.pct}</span>}
            </div>
            <div className="muted">{it.label}</div>
          </div>
        </div>
      ))}
    </aside>
  );
}
