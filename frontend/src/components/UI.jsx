import { useState, useEffect, useRef } from 'react';
import DIcon from './DIcon';
import { useTranslation } from 'react-i18next';

function applyDocumentLanguage(lang) {
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  document.documentElement.lang = lang;
}

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

export const StatCard = ({ icon, label, value, sub, variant = 'default' }) => {
  const accentColor = variant === 'warning' ? 'var(--warning)' : variant === 'error' ? 'var(--error)' : 'var(--gold)';
  const bgColor = variant === 'warning' ? 'var(--warning-bg)' : variant === 'error' ? 'var(--error-bg)' : 'var(--gold-bg)';
  return (
    <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius-lg)', padding: '18px 20px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 10, boxShadow: 'var(--shadow-sm)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ width: 34, height: 34, borderRadius: 'var(--radius-md)', background: bgColor, display: 'flex', alignItems: 'center', justifyContent: 'center', color: accentColor }}><DIcon name={icon} size={17} /></div>
        {sub && <span style={{ fontSize: 11, color: sub.includes('critique') || sub.includes('-') ? 'var(--error)' : 'var(--success)', fontWeight: 500 }}>{sub}</span>}
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

export const Avatar = ({ name, size = 32 }) => {
  const initials = name.split(' ').map(n => n[0]).join('').slice(0, 2);
  return <div style={{ width: size, height: size, borderRadius: '50%', background: 'var(--gold-10)', color: 'var(--gold-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: size * 0.36, fontWeight: 600, flexShrink: 0 }}>{initials}</div>;
};

export const Tag = ({ children, variant = 'neutral' }) => {
  const c = { gold: { bg: 'var(--gold-bg)', color: 'var(--gold-dark)' }, info: { bg: 'var(--info-bg)', color: 'var(--info)' }, neutral: { bg: 'var(--navy-50)', color: 'var(--text-secondary)' } };
  const v = c[variant] || c.neutral;
  return <span style={{ display: 'inline-block', padding: '1px 7px', borderRadius: 4, fontSize: 11, fontWeight: 500, background: v.bg, color: v.color }}>{children}</span>;
};

export const DTabs = ({ items, active, onChange }) => (
  <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
    {items.map(item => (
      <button key={item.id} onClick={() => onChange(item.id)} style={{ padding: '8px 16px', fontSize: 13, fontWeight: active === item.id ? 600 : 400, color: active === item.id ? 'var(--navy)' : 'var(--text-secondary)', borderBottom: `2px solid ${active === item.id ? 'var(--gold)' : 'transparent'}`, marginBottom: -1, transition: 'all .15s', background: 'none', cursor: 'pointer' }}>
        {item.label}
        {item.count != null && <span style={{ marginLeft: 6, fontSize: 11, padding: '0 6px', borderRadius: 99, background: active === item.id ? 'var(--gold-bg)' : 'var(--surface-active)', fontWeight: 500 }}>{item.count}</span>}
      </button>
    ))}
  </div>
);

export const DCard = ({ children, title, action, style: s = {}, noPad = false }) => (
  <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)', ...s }}>
    {title && <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, fontFamily: 'var(--font-heading)' }}>{title}</h3>{action}
    </div>}
    {!noPad ? <div style={{ padding: '16px 20px' }}>{children}</div> : children}
  </div>
);

export const FilterChip = ({ label, active, onClick }) => (
  <button onClick={onClick} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '5px 12px', borderRadius: 99, fontSize: 12, fontWeight: 500, background: active ? 'var(--navy)' : 'var(--surface)', color: active ? '#fff' : 'var(--text-secondary)', border: active ? 'none' : '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s' }}>{label}</button>
);

export const TimelineItem = ({ time, title, desc, variant = 'neutral' }) => {
  const dot = { gold: 'var(--gold)', success: 'var(--success)', warning: 'var(--warning)', error: 'var(--error)', neutral: 'var(--text-muted)' };
  return (
    <div style={{ display: 'flex', gap: 12, paddingBottom: 14 }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 2 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: dot[variant], flexShrink: 0 }} />
        <div style={{ width: 1, flex: 1, background: 'var(--border)', marginTop: 4 }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>{title}</div>
        {desc && <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>{desc}</div>}
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>{time}</div>
      </div>
    </div>
  );
};

export const EmptyState = ({ icon = 'fileText', title, desc, action }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 24px', textAlign: 'center' }}>
    <div style={{ width: 56, height: 56, borderRadius: 16, background: 'var(--surface-active)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', marginBottom: 16 }}><DIcon name={icon} size={24} /></div>
    <div style={{ fontSize: 15, fontWeight: 600, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{title}</div>
    {desc && <div style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 320, marginBottom: 16 }}>{desc}</div>}
    {action}
  </div>
);

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

export const LangSwitch = ({ value, onChange, alwaysOpen }) => {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const current = value || i18n.language || 'fr';
  const langs = ['FR', 'AR', 'EN'];
  const handleChange = (lang) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('daleel_lang', lang);
    applyDocumentLanguage(lang);
    if (onChange) onChange(lang);
    setOpen(false);
  };

  useEffect(() => {
    if (!open) return;
    const handle = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [open]);

  const langBar = (
    <div style={{ display: 'flex', background: 'var(--surface-active)', borderRadius: 6, padding: 2, gap: 1 }}>
      {langs.map(l => (
        <button key={l} onClick={() => handleChange(l.toLowerCase())} style={{ padding: '3px 8px', borderRadius: 4, fontSize: 11, fontWeight: current === l.toLowerCase() ? 600 : 400, background: current === l.toLowerCase() ? 'var(--surface)' : 'transparent', color: current === l.toLowerCase() ? 'var(--text)' : 'var(--text-muted)', border: 'none', cursor: 'pointer', boxShadow: current === l.toLowerCase() ? 'var(--shadow-sm)' : 'none' }}>{l}</button>
      ))}
    </div>
  );

  if (alwaysOpen) return langBar;

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 34, height: 34, borderRadius: 8, background: open ? 'var(--surface-active)' : 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s', fontSize: 12, fontWeight: 600 }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-active)'}
        onMouseLeave={e => { if (!open) e.currentTarget.style.background = 'transparent'; }}
      >
        {current.toUpperCase()}
      </button>
      {open && (
        <div style={{ position: 'absolute', top: 'calc(100% + 6px)', right: 0, zIndex: 1000, animation: 'langDropIn .12s ease-out' }}>
          <style>{`@keyframes langDropIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }`}</style>
          {langBar}
        </div>
      )}
    </div>
  );
};

export const FormField = ({ label, type = 'text', value, onChange, placeholder, options, icon }) => (
  <div style={{ marginBottom: 14 }}>
    {label && <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 5 }}>{label}</label>}
    <div style={{ position: 'relative' }}>
      {icon && <DIcon name={icon} size={16} style={{ position: 'absolute', left: 12, top: 11, color: 'var(--text-muted)' }} />}
      {type === 'select' ? (
        <select value={value} onChange={e => onChange(e.target.value)} style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'var(--surface)', color: 'var(--text)', outline: 'none', appearance: 'none' }}>
          {options?.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      ) : (
        <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} style={{ width: '100%', padding: icon ? '10px 14px 10px 36px' : '10px 14px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'var(--surface)', color: 'var(--text)', outline: 'none' }} />
      )}
    </div>
  </div>
);

export const DetailField = ({ label, children }) => (
  <div style={{ marginBottom: 12 }}>
    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 13 }}>{children}</div>
  </div>
);
