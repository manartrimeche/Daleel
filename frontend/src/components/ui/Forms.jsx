// Champs et boutons : FormField, DetailField, DButton.

import DIcon from '../DIcon';

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

export const DButton = ({ children, variant = 'primary', size = 'md', icon, disabled, className = '', style: s, ...rest }) => {
  const cls = `d-btn d-btn-${variant} d-btn-${size} ${className}`.trim();
  return (
    <button className={cls} disabled={disabled} style={s} {...rest}>
      {icon && <DIcon name={icon} size={size === 'sm' ? 14 : 16} />}
      {children}
    </button>
  );
};
