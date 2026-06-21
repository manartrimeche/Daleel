// Toast + Confirm : UIProvider, useToast, useConfirm.

import { useState, useEffect, useRef, createContext, useContext, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import DIcon from '../DIcon';

const UICtx = createContext({
  toast: { success: () => {}, error: () => {}, info: () => {}, warning: () => {} },
  confirm: () => Promise.resolve(false),
});

// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => useContext(UICtx).toast;
// eslint-disable-next-line react-refresh/only-export-components
export const useConfirm = () => useContext(UICtx).confirm;

const TOAST_STYLES = {
  success: { bg: 'var(--success-bg)', color: 'var(--success)', border: 'var(--success)', icon: 'check' },
  error:   { bg: 'var(--error-bg)',   color: 'var(--error)',   border: 'var(--error)',   icon: 'alertTriangle' },
  warning: { bg: 'var(--warning-bg)', color: 'var(--warning)', border: 'var(--warning)', icon: 'alertTriangle' },
  info:    { bg: 'var(--info-bg)',    color: 'var(--info)',    border: 'var(--info)',    icon: 'info' },
};

function ToastItem({ toast, onClose }) {
  const s = TOAST_STYLES[toast.variant] || TOAST_STYLES.info;
  return (
    <div role="alert" style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '11px 14px', borderRadius: 10,
      background: s.bg, color: s.color,
      border: '1px solid rgba(27,43,66,0.08)',
      borderLeft: `3px solid ${s.border}`,
      boxShadow: 'var(--shadow-md)',
      minWidth: 280, maxWidth: 420,
      fontSize: 13, fontWeight: 500,
      animation: 'toastIn .18s ease-out',
    }}>
      <DIcon name={s.icon} size={16} style={{ flexShrink: 0 }} />
      <span style={{ flex: 1, color: 'var(--text)' }}>{toast.message}</span>
      <button onClick={onClose} aria-label="Close" style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 2, display: 'flex' }}>
        <DIcon name="x" size={14} />
      </button>
    </div>
  );
}

function ConfirmDialog({ message, options, onConfirm, onCancel }) {
  const { t } = useTranslation();
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); onCancel(); }
      else if (e.key === 'Enter') { e.preventDefault(); onConfirm(); }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onConfirm, onCancel]);

  const isDanger = options.variant === 'danger';
  return (
    <div role="dialog" aria-modal="true" onClick={onCancel} style={{
      position: 'fixed', inset: 0, zIndex: 10000,
      background: 'rgba(27,43,66,0.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 16, animation: 'fadeIn .12s ease-out',
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: '100%', maxWidth: 380, background: 'var(--surface)',
        borderRadius: 'var(--radius-lg)', padding: 22,
        boxShadow: 'var(--shadow-lg)',
        animation: 'dialogIn .14s ease-out',
      }}>
        {options.title && <h3 style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 8, color: 'var(--text)' }}>{options.title}</h3>}
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: 18 }}>{message}</p>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button type="button" onClick={onCancel} style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
            {options.cancelLabel || t('common.cancel')}
          </button>
          <button type="button" autoFocus onClick={onConfirm} style={{ padding: '8px 14px', borderRadius: 8, border: 'none', background: isDanger ? 'var(--error)' : 'var(--navy)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
            {options.confirmLabel || t('common.confirm')}
          </button>
        </div>
      </div>
    </div>
  );
}

export function UIProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [confirmState, setConfirmState] = useState(null);
  const idRef = useRef(0);

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(item => item.id !== id));
  }, []);

  const show = useCallback((message, variant = 'info', duration = 4000) => {
    if (!message) return;
    const id = ++idRef.current;
    setToasts(prev => [...prev, { id, message: String(message), variant }]);
    if (duration > 0) setTimeout(() => dismiss(id), duration);
  }, [dismiss]);

  const toast = useMemo(() => ({
    success: (msg, d) => show(msg, 'success', d),
    error:   (msg, d) => show(msg, 'error',   d),
    warning: (msg, d) => show(msg, 'warning', d),
    info:    (msg, d) => show(msg, 'info',    d),
  }), [show]);

  const confirm = useCallback((message, options = {}) =>
    new Promise(resolve => setConfirmState({ message, options, resolve })), []);

  const close = (ok) => {
    if (confirmState) confirmState.resolve(ok);
    setConfirmState(null);
  };

  const value = useMemo(() => ({ toast, confirm }), [toast, confirm]);

  return (
    <UICtx.Provider value={value}>
      {children}
      <div style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 10001, display: 'flex', flexDirection: 'column', gap: 8, pointerEvents: 'none' }}>
        {toasts.map(item => (
          <div key={item.id} style={{ pointerEvents: 'auto' }}>
            <ToastItem toast={item} onClose={() => dismiss(item.id)} />
          </div>
        ))}
      </div>
      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          options={confirmState.options}
          onConfirm={() => close(true)}
          onCancel={() => close(false)}
        />
      )}
    </UICtx.Provider>
  );
}
