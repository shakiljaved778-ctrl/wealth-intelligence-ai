"use client";
// Lightweight inline-SVG bar chart — no chart library (keeps deps/build clean).
// Follows the dataviz rules: thin marks with a 2px surface gap, 4px rounded
// data-ends anchored to the baseline, recessive axis, a title naming the single
// series (no legend), and a per-bar hover tooltip via <title>.
//
//   mode="magnitude" → single brand-green series (e.g. price).
//   mode="polarity"  → green for ≥0, navy for <0, around a zero baseline
//                      (e.g. standardized factor scores in [-1, 1]).

export interface Bar {
  label: string;
  value: number;
}

const GREEN = "#6fc493";
const NAVY = "#1f2a63";
const AXIS = "#c7cddd";
const INK = "#6b7690";

export function BarChart({
  data,
  mode = "magnitude",
  height = 200,
  unit = "",
  title,
}: {
  data: Bar[];
  mode?: "magnitude" | "polarity";
  height?: number;
  unit?: string;
  title?: string;
}) {
  if (data.length === 0) return <p className="muted">No data.</p>;

  const W = 640;
  const H = height;
  const padX = 8;
  const padTop = 8;
  const padBottom = 22;
  const plotH = H - padTop - padBottom;
  const n = data.length;
  const slot = (W - padX * 2) / n;
  const gap = 2; // 2px surface gap between adjacent bars
  const barW = Math.max(1, slot - gap);
  const r = Math.min(4, barW / 2);

  const values = data.map((d) => d.value);
  const maxAbs = Math.max(1e-9, ...values.map((v) => Math.abs(v)));

  if (mode === "polarity") {
    const zeroY = padTop + plotH / 2;
    const scale = plotH / 2 / maxAbs;
    return (
      <figure style={{ margin: 0 }}>
        {title && <figcaption className="muted" style={{ marginBottom: 6 }}>{title}</figcaption>}
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={title || "chart"}>
          <line x1={padX} y1={zeroY} x2={W - padX} y2={zeroY} stroke={AXIS} strokeWidth={1} />
          {data.map((d, i) => {
            const x = padX + i * slot + gap / 2;
            const h = Math.abs(d.value) * scale;
            const y = d.value >= 0 ? zeroY - h : zeroY;
            const fill = d.value >= 0 ? GREEN : NAVY;
            return (
              <g key={i}>
                <rect x={x} y={y} width={barW} height={Math.max(h, 0.5)} rx={r} fill={fill}>
                  <title>{`${d.label}: ${d.value.toFixed(2)}${unit}`}</title>
                </rect>
                <text x={x + barW / 2} y={H - 7} textAnchor="middle" fontSize={10} fill={INK}>
                  {d.label.length > 6 ? d.label.slice(0, 5) + "…" : d.label}
                </text>
              </g>
            );
          })}
        </svg>
      </figure>
    );
  }

  // magnitude: single green series, bars grow from the baseline
  const scale = plotH / maxAbs;
  const baseY = padTop + plotH;
  const showLabels = n <= 16;
  return (
    <figure style={{ margin: 0 }}>
      {title && <figcaption className="muted" style={{ marginBottom: 6 }}>{title}</figcaption>}
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={title || "chart"}>
        <line x1={padX} y1={baseY} x2={W - padX} y2={baseY} stroke={AXIS} strokeWidth={1} />
        {data.map((d, i) => {
          const x = padX + i * slot + gap / 2;
          const h = Math.abs(d.value) * scale;
          return (
            <g key={i}>
              <rect x={x} y={baseY - h} width={barW} height={Math.max(h, 0.5)} rx={r} fill={GREEN}>
                <title>{`${d.label}: ${d.value.toLocaleString()}${unit}`}</title>
              </rect>
              {showLabels && (
                <text x={x + barW / 2} y={H - 7} textAnchor="middle" fontSize={10} fill={INK}>
                  {d.label.length > 6 ? d.label.slice(0, 5) + "…" : d.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
