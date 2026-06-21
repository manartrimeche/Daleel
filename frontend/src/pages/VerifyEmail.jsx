import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [state, setState] = useState('loading'); // loading | success | error
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    (async () => {
      const token = params.get('token');
      if (!token) {
        setState('error');
        setErrorMsg(t('verifyEmail.missingToken'));
        return;
      }
      try {
        const res = await fetch('/api/v1/auth/verify-email', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || t('verifyEmail.error'));
        setState('success');
      } catch (err) {
        setErrorMsg(err.message);
        setState('error');
      }
    })();
  }, [params, t]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)', padding: 24 }}>
      <div style={{ maxWidth: 480, width: '100%', padding: 32, borderRadius: 12, background: 'var(--surface)', border: '1px solid var(--border)', textAlign: 'center' }}>
        {state === 'loading' && (
          <>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>{t('verifyEmail.loadingTitle')}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{t('verifyEmail.loadingDesc')}</p>
          </>
        )}
        {state === 'success' && (
          <>
            <div style={{ fontSize: 48, marginBottom: 12 }}>✓</div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>{t('verifyEmail.successTitle')}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 20 }}>{t('verifyEmail.successDesc')}</p>
            <button onClick={() => navigate('/login')} className="hover-opacity" style={{ padding: '10px 24px', borderRadius: 8, background: 'var(--navy)', color: '#fff', border: 'none', fontWeight: 600, cursor: 'pointer' }}>
              {t('verifyEmail.toLogin')}
            </button>
          </>
        )}
        {state === 'error' && (
          <>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8, color: 'var(--error)' }}>{t('verifyEmail.errorTitle')}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 20 }}>{errorMsg}</p>
            <button onClick={() => navigate('/login')} style={{ padding: '10px 24px', borderRadius: 8, background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border)', fontWeight: 600, cursor: 'pointer' }}>
              {t('verifyEmail.toLogin')}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
