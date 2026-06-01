// BI Charts — lightweight SVG components for the dashboard.
// No external dependency; renders inline SVGs with smooth interpolation.

/**
 * MiniLineChart — sparkline for KPI cards.
 * @param {{ data: number[], width?: number, height?: number, color?: string, fillOpacity?: number }} props
 */
export const MiniLineChart = ({ data = [], width = 120, height = 36, color = 'var(--gold)', fillOpacity = 0.15 }) => {
  if (!data.length) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const pad = 2;
  const pts = data.map((v, i) => [
    pad + (i / Math.max(data.length - 1, 1)) * (width - pad * 2),
    pad + (1 - (v - min) / range) * (height - pad * 2),
  ]);
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
  const area = `${line} L${pts[pts.length - 1][0].toFixed(1)},${height} L${pts[0][0].toFixed(1)},${height} Z`;
  return (
    <svg width={width} height={height} style={{ display: 'block', overflow: 'visible' }}>
      <path d={area} fill={color} opacity={fillOpacity} />
      <path d={line} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
      {pts.length > 0 && (
        <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r={2.5} fill={color} />
      )}
    </svg>
  );
};

/**
 * AreaLineChart — full-width time-series chart with axis labels.
 * @param {{ data: {label:string, value:number}[], height?: number, color?: string, yLabel?: string }} props
 */
export const AreaLineChart = ({ data = [], height = 180, color = 'var(--gold)', yLabel = '' }) => {
  if (!data.length) return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>Aucune donnee</div>;

  const values = data.map(d => d.value);
  const max = Math.max(...values, 1);
  const ySteps = 4;
  const padL = 36;
  const padR = 12;
  const padT = 12;
  const padB = 28;
  const chartW = `calc(100% - ${padL + padR}px)`;

  return (
    <div style={{ position: 'relative', height, width: '100%' }}>
      {/* Y axis labels */}
      {Array.from({ length: ySteps + 1 }, (_, i) => {
        const v = Math.round((max / ySteps) * (ySteps - i));
        const top = padT + (i / ySteps) * (height - padT - padB);
        return (
          <div key={i} style={{ position: 'absolute', left: 0, top, width: padL - 6, textAlign: 'right', fontSize: 10, color: 'var(--text-muted)', transform: 'translateY(-50%)' }}>
            {v}
          </div>
        );
      })}
      {/* Grid lines */}
      <svg width="100%" height={height} style={{ position: 'absolute', top: 0, left: padL }}>
        {Array.from({ length: ySteps + 1 }, (_, i) => {
          const y = padT + (i / ySteps) * (height - padT - padB);
          return <line key={i} x1="0" y1={y} x2="100%" y2={y} stroke="var(--border-subtle)" strokeWidth={0.5} />;
        })}
      </svg>
      {/* Chart SVG */}
      <svg viewBox={`0 0 1000 ${height}`} preserveAspectRatio="none" width={chartW} height={height} style={{ position: 'absolute', top: 0, left: padL }}>
        {(() => {
          const pts = values.map((v, i) => [
            (i / Math.max(values.length - 1, 1)) * 1000,
            padT + (1 - v / max) * (height - padT - padB),
          ]);
          const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
          const area = `${line} L1000,${height - padB} L0,${height - padB} Z`;
          return (
            <>
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity="0.25" />
                  <stop offset="100%" stopColor={color} stopOpacity="0.02" />
                </linearGradient>
              </defs>
              <path d={area} fill="url(#areaGrad)" />
              <path d={line} fill="none" stroke={color} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
            </>
          );
        })()}
      </svg>
      {/* X axis labels */}
      <div style={{ position: 'absolute', bottom: 0, left: padL, right: padR, display: 'flex', justifyContent: 'space-between' }}>
        {data.filter((_, i) => {
          const step = Math.max(1, Math.floor(data.length / 6));
          return i % step === 0 || i === data.length - 1;
        }).map((d, i) => (
          <span key={i} style={{ fontSize: 10, color: 'var(--text-muted)' }}>{d.label}</span>
        ))}
      </div>
      {yLabel && <div style={{ position: 'absolute', top: 0, left: 0, fontSize: 10, color: 'var(--text-muted)' }}>{yLabel}</div>}
    </div>
  );
};

/**
 * DonutChart — ring chart with center label.
 * @param {{ segments: {value:number, color:string, label:string}[], size?: number, thickness?: number, centerLabel?: string, centerValue?: string|number }} props
 */
export const DonutChart = ({ segments = [], size = 140, thickness = 22, centerLabel = '', centerValue = '' }) => {
  const total = segments.reduce((s, seg) => s + seg.value, 0) || 1;
  const r = (size - thickness) / 2;
  const circ = 2 * Math.PI * r;
  const segmentArcs = segments.reduce((acc, seg) => {
    const dash = (seg.value / total) * circ;
    return {
      offset: acc.offset + dash,
      items: [...acc.items, { seg, dash, offset: acc.offset }],
    };
  }, { offset: -circ / 4, items: [] });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-active)" strokeWidth={thickness} />
          {segmentArcs.items.map(({ seg, dash, offset }, i) => (
            <circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={seg.color}
              strokeWidth={thickness}
              strokeDasharray={`${dash} ${circ - dash}`}
              strokeDashoffset={-offset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dasharray 0.6s ease, stroke-dashoffset 0.6s ease' }}
            />
          ))}
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          {centerValue !== '' && <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--text)' }}>{centerValue}</div>}
          {centerLabel && <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: -2 }}>{centerLabel}</div>}
        </div>
      </div>
      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 14px', justifyContent: 'center' }}>
        {segments.filter(s => s.value > 0).map((seg, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--text-secondary)' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: seg.color, flexShrink: 0 }} />
            {seg.label} ({seg.value})
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * HorizontalBarChart — horizontal bars with labels.
 * @param {{ items: {label:string, value:number, color?:string, maxValue?:number}[], barHeight?: number }} props
 */
export const HorizontalBarChart = ({ items = [], barHeight = 22 }) => {
  const maxVal = Math.max(...items.map(it => it.maxValue ?? it.value), 1);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {items.map((item, i) => (
        <div key={i}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text)' }}>{item.label}</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: item.color || 'var(--gold)' }}>{item.value}%</span>
          </div>
          <div style={{ height: barHeight, borderRadius: barHeight / 2, background: 'var(--surface-active)', overflow: 'hidden', position: 'relative' }}>
            <div style={{
              height: '100%',
              width: `${Math.min(100, (item.value / (item.maxValue ?? maxVal)) * 100)}%`,
              borderRadius: barHeight / 2,
              background: item.color || 'var(--gold)',
              transition: 'width 0.6s ease',
              opacity: 0.85,
            }} />
          </div>
        </div>
      ))}
    </div>
  );
};
