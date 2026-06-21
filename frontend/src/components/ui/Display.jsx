// Primitives d'affichage : Badge, Tag, Avatar, FilterChip.

export const Badge = ({ children, variant = 'neutral', size = 'sm' }) => {
  const colors = {
    success: { bg: 'var(--success-bg)', color: 'var(--success)', border: 'rgba(45,106,79,0.15)' },
    warning: { bg: 'var(--warning-bg)', color: 'var(--warning)', border: 'rgba(184,134,11,0.15)' },
    error: { bg: 'var(--error-bg)', color: 'var(--error)', border: 'rgba(185,28,28,0.15)' },
    info: { bg: 'var(--info-bg)', color: 'var(--info)', border: 'rgba(30,86,160,0.15)' },
    gold: { bg: 'var(--gold-bg)', color: 'var(--gold-dark)', border: 'var(--gold-10)' },
    neutral: { bg: 'var(--surface-active)', color: 'var(--text-secondary)', border: 'var(--border)' },
  };
  const c = colors[variant] || colors.neutral;
  const sz = size === 'sm' ? { fontSize: 11, padding: '2px 8px' } : { fontSize: 12, padding: '3px 10px' };
  return <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, borderRadius: 99, fontWeight: 600, background: c.bg, color: c.color, border: `1px solid ${c.border}`, whiteSpace: 'nowrap', letterSpacing: '0.01em', ...sz }}>{children}</span>;
};

export const Tag = ({ children, variant = 'neutral' }) => {
  const c = { gold: { bg: 'var(--gold-bg)', color: 'var(--gold-dark)' }, info: { bg: 'var(--info-bg)', color: 'var(--info)' }, neutral: { bg: 'var(--navy-50)', color: 'var(--text-secondary)' } };
  const v = c[variant] || c.neutral;
  return <span style={{ display: 'inline-block', padding: '1px 7px', borderRadius: 4, fontSize: 11, fontWeight: 500, background: v.bg, color: v.color }}>{children}</span>;
};

export const Avatar = ({ name, size = 32 }) => {
  const initials = name.split(' ').map(n => n[0]).join('').slice(0, 2);
  return <div style={{ width: size, height: size, borderRadius: '50%', background: 'var(--gold-10)', color: 'var(--gold-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: size * 0.36, fontWeight: 600, flexShrink: 0 }}>{initials}</div>;
};

export const FilterChip = ({ label, active, onClick }) => (
  <button className="ui-filter-chip" onClick={onClick} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '5px 12px', borderRadius: 99, fontSize: 12, fontWeight: 500, background: active ? 'var(--navy)' : 'var(--surface)', color: active ? '#fff' : 'var(--text-secondary)', border: active ? 'none' : '1px solid var(--border)', cursor: 'pointer' }}>{label}</button>
);
