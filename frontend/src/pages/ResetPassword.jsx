import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FormField, LangSwitch } from '../components/UI';

const styles = {
  page: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, background: 'var(--bg)' },
  panel: { width: '100%', maxWidth: 420, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, boxShadow: 'var(--shadow-md)', padding: 32 },
};

export default function ResetPassword() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError('');
    setMessage('');
    if (!token) {
      setError(t('resetPassword.missingToken'));
      return;
    }
    if (password !== confirmPassword) {
      setError(t('login.passwordMismatch'));
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || t('resetPassword.error'));
      setMessage(data.message || t('resetPassword.success'));
      setPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') handleSubmit();
  };

  return (
    <div style={styles.page} onKeyDown={handleKeyDown}>
      <div style={{ position: 'absolute', top: 16, right: 24 }}>
        <LangSwitch />
      </div>
      <div style={styles.panel}>
        <div style={{ marginBottom: 24 }}>
          <div style={{ width: 42, height: 42, borderRadius: 8, background: 'linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 16 }}>د</div>
          <h1 style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 6 }}>{t('resetPassword.title')}</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{t('resetPassword.subtitle')}</p>
        </div>

        {error && (
          <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--error-bg)', color: 'var(--error)', fontSize: 13, marginBottom: 16, border: '1px solid rgba(185,28,28,0.15)' }}>{error}</div>
        )}
        {message && (
          <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--success-bg)', color: 'var(--success)', fontSize: 13, marginBottom: 16, border: '1px solid rgba(45,106,79,0.15)' }}>{message}</div>
        )}

        <FormField label={t('resetPassword.newPassword')} type="password" value={password} onChange={setPassword} placeholder="••••••••" icon="lock" />
        <FormField label={t('resetPassword.confirmPassword')} type="password" value={confirmPassword} onChange={setConfirmPassword} placeholder="••••••••" icon="lock" />

        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{ width: '100%', padding: '12px', borderRadius: 10, background: 'var(--navy)', color: '#fff', fontSize: 14, fontWeight: 600, cursor: loading ? 'wait' : 'pointer', border: 'none', marginTop: 4, opacity: loading ? 0.7 : 1 }}
        >
          {loading ? t('common.saving') : t('resetPassword.submit')}
        </button>
        <button
          type="button"
          onClick={() => navigate('/login')}
          style={{ width: '100%', padding: '10px', marginTop: 10, borderRadius: 10, background: 'transparent', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600, cursor: 'pointer', border: '1px solid var(--border)' }}
        >
          {t('login.backToLogin')}
        </button>
      </div>
    </div>
  );
}
