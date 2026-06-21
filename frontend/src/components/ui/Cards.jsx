// Conteneurs et indicateurs : DCard, StatCard, ProgressBar, ScoreRing, EmptyState.

import DIcon from '../DIcon';

export const DCard = ({ children, title, action, style: s = {}, noPad = false, className = '' }) => (
  <div className={`ui-card ${className}`.trim()} style={{ background: 'var(--surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)', ...s }}>
    {title && <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, fontFamily: 'var(--font-heading)' }}>{title}</h3>{action}
    </div>}
    {!noPad ? <div style={{ padding: '16px 20px' }}>{children}</div> : children}
  </div>
);

const STATCARD_ACCENT = {
  default: { color: 'var(--gold)', bg: 'var(--gold-bg)' },
  warning: { color: 'var(--warning)', bg: 'var(--warning-bg)' },
  error: { color: 'var(--error)', bg: 'var(--error-bg)' },
  success: { color: 'var(--success)', bg: 'var(--success-bg)' },
};

const STATCARD_SUB_TONE = {
  positive: 'var(--success)',
  negative: 'var(--error)',
  neutral: 'var(--text-muted)',
};

// `sub` est un libellé court (ex. "+12% vs last month").
// `subTone` indique explicitement la couleur : 'positive' (défaut), 'negative', 'neutral'.
export const StatCard = ({ icon, label, value, sub, subTone = 'positive', variant = 'default' }) => {
  const accent = STATCARD_ACCENT[variant] || STATCARD_ACCENT.default;
  const subColor = STATCARD_SUB_TONE[subTone] || STATCARD_SUB_TONE.positive;
  return (
    <div className="ui-card ui-stat-card" style={{ background: 'var(--surface)', borderRadius: 'var(--radius-lg)', padding: '18px 20px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 10, boxShadow: 'var(--shadow-sm)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ width: 34, height: 34, borderRadius: 'var(--radius-md)', background: accent.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: accent.color }}><DIcon name={icon} size={17} /></div>
        {sub && <span style={{ fontSize: 11, color: subColor, fontWeight: 500 }}>{sub}</span>}
      </div>
      <div>
        <div style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--text)', lineHeight: 1.1 }}>{value}</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 3 }}>{label}</div>
      </div>
    </div>
  );
};

export const ProgressBar = ({ value, label, sub, variant = 'gold' }) => {
  const c = { gold: 'var(--gold)', success: 'var(--success)', warning: 'var(--warning)', error: 'var(--error)', info: 'var(--info)' };
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 13, fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: c[variant] || 'var(--gold)' }}>{value}%</span>
      </div>
      <div style={{ height: 5, borderRadius: 3, background: 'var(--surface-active)', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${value}%`, borderRadius: 3, background: c[variant] || 'var(--gold)', transition: 'width .6s ease' }} />
      </div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>{sub}</div>}
    </div>
  );
};

export const ScoreRing = ({ value, size = 56, label, variant = 'gold' }) => {
  const c = { gold: 'var(--gold)', success: 'var(--success)', warning: 'var(--warning)', error: 'var(--error)' };
  const r = (size - 8) / 2, circ = 2 * Math.PI * r, offset = circ * (1 - value / 100);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--surface-active)" strokeWidth="5"/>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={c[variant]||c.gold} strokeWidth="5" strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"/>
      </svg>
      <span style={{ position: 'relative', marginTop: -size/2-8, fontSize: size*0.28, fontWeight: 700, fontFamily: 'var(--font-heading)', color: c[variant] }}>{value}%</span>
      {label && <span style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: size*0.18 }}>{label}</span>}
    </div>
  );
};

export const EmptyState = ({ icon = 'fileText', title, desc, action }) => (
  <div className="ui-empty-state" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 24px', textAlign: 'center' }}>
    <div style={{ width: 56, height: 56, borderRadius: 16, background: 'var(--surface-active)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', marginBottom: 16 }}><DIcon name={icon} size={24} /></div>
    <div style={{ fontSize: 15, fontWeight: 600, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{title}</div>
    {desc && <div style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 320, marginBottom: 16 }}>{desc}</div>}
    {action}
  </div>
);
