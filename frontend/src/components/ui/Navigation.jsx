// Navigation : DTabs, TimelineItem, LangSwitch.

import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';

function applyDocumentLanguage(lang) {
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  document.documentElement.lang = lang;
}

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

const FlagIcon = ({ code }) => {
  const frameStyle = {
    width: 22,
    height: 16,
    display: 'block',
    overflow: 'hidden',
    borderRadius: 3,
    boxShadow: '0 0 0 1px rgba(27,43,66,0.12)',
    flexShrink: 0,
  };
  const svgStyle = { width: '100%', height: '100%', display: 'block' };

  if (code === 'fr') {
    return (
      <span aria-hidden="true" style={frameStyle}>
        <svg viewBox="0 0 3 2" style={svgStyle}>
          <rect width="1" height="2" fill="#0055A4" />
          <rect x="1" width="1" height="2" fill="#FFFFFF" />
          <rect x="2" width="1" height="2" fill="#EF4135" />
        </svg>
      </span>
    );
  }

  if (code === 'ar') {
    return (
      <span aria-hidden="true" style={frameStyle}>
        <svg viewBox="0 0 30 20" style={svgStyle}>
          <rect width="30" height="20" fill="#E70013" />
          <circle cx="15" cy="10" r="5.3" fill="#FFFFFF" />
          <circle cx="13.4" cy="10" r="3.1" fill="#E70013" />
          <circle cx="14.4" cy="10" r="2.55" fill="#FFFFFF" />
          <path d="M18.2 7.6l.55 1.6h1.7l-1.38 1 .52 1.62-1.39-1-1.38 1 .52-1.62-1.38-1h1.7z" fill="#E70013" />
        </svg>
      </span>
    );
  }

  return (
    <span aria-hidden="true" style={frameStyle}>
      <svg viewBox="0 0 60 30" style={svgStyle}>
        <rect width="60" height="30" fill="#012169" />
        <path d="M0 0l60 30M60 0L0 30" stroke="#FFFFFF" strokeWidth="6" />
        <path d="M0 0l60 30M60 0L0 30" stroke="#C8102E" strokeWidth="3.4" />
        <path d="M30 0v30M0 15h60" stroke="#FFFFFF" strokeWidth="10" />
        <path d="M30 0v30M0 15h60" stroke="#C8102E" strokeWidth="6" />
      </svg>
    </span>
  );
};

export const LangSwitch = ({ value, onChange, alwaysOpen, plain = false, floating = false, dark = false, transparent = false }) => {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const current = (value || i18n.language || 'fr').slice(0, 2).toLowerCase();
  const langs = [
    { code: 'fr', label: 'Francais' },
    { code: 'ar', label: 'Arabe' },
    { code: 'en', label: 'English' },
  ];
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
    <div style={{
      display: 'flex',
      background: dark ? 'rgba(8,22,30,0.86)' : (transparent ? 'rgba(255,255,255,0.92)' : 'var(--surface-active)'),
      borderRadius: 6,
      padding: 2,
      gap: 1,
      border: dark ? '1px solid rgba(255,255,255,0.14)' : (transparent ? '1px solid rgba(27,43,66,0.10)' : 'none'),
      boxShadow: dark ? '0 12px 26px rgba(0,0,0,0.18)' : (transparent ? '0 12px 26px rgba(27,43,66,0.10)' : 'none'),
      backdropFilter: transparent ? 'blur(14px)' : 'none',
      WebkitBackdropFilter: transparent ? 'blur(14px)' : 'none',
    }}>
      {langs.map(l => (
        <button key={l.code} onClick={() => handleChange(l.code)} aria-label={l.label} title={l.label} style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 34, height: 30, padding: 0, borderRadius: 4, background: current === l.code ? (dark ? 'rgba(255,255,255,0.16)' : 'var(--surface)') : 'transparent', border: 'none', cursor: 'pointer', boxShadow: current === l.code && !dark ? 'var(--shadow-sm)' : 'none' }}>
          <FlagIcon code={l.code} />
        </button>
      ))}
    </div>
  );

  if (alwaysOpen) return langBar;

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        className={floating || transparent ? 'hover-lift app-navbar-control' : plain ? '' : 'hover-bg-active'}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: floating ? 42 : 32,
          height: floating ? 36 : 28,
          borderRadius: plain ? 0 : (floating ? 10 : 6),
          background: dark ? 'rgba(255,255,255,0.07)' : (transparent ? (open ? 'rgba(255,255,255,0.34)' : 'rgba(255,255,255,0.14)') : (floating ? 'rgba(255,255,255,0.9)' : (plain ? 'transparent' : (open ? 'var(--surface-active)' : 'transparent')))),
          color: dark ? '#fff' : 'var(--text-secondary)',
          border: plain ? 'none' : (dark ? '1px solid rgba(255,255,255,0.18)' : (transparent ? '1px solid rgba(27,43,66,0.10)' : (floating ? '1px solid rgba(27,43,66,0.12)' : '1px solid var(--border)'))),
          boxShadow: transparent ? 'none' : (floating ? '0 10px 24px rgba(27,43,66,0.14)' : 'none'),
          backdropFilter: floating || transparent ? 'blur(12px)' : 'none',
          WebkitBackdropFilter: floating || transparent ? 'blur(12px)' : 'none',
          cursor: 'pointer',
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        <FlagIcon code={langs.some(l => l.code === current) ? current : 'en'} />
      </button>
      {open && (
        <div style={{ position: 'absolute', top: 'calc(100% + 6px)', right: 0, zIndex: 1000, animation: 'langDropIn .12s ease-out' }}>
          {langBar}
        </div>
      )}
    </div>
  );
};
