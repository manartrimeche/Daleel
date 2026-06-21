import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import DIcon from '../components/DIcon';
import { FormField } from '../components/UI';

export default function Invite() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get('token') || '';
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleAccept = async () => {
    if (!password || !name) { setError(t('invite.fillAll')); return; }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/v1/auth/invitations/accept', {
        method: 'POST',
        credentials: 'include', // receive HttpOnly refresh cookie
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, full_name: name, password }),
      });
      if (res.ok) {
        setSuccess(true);
        setTimeout(() => navigate('/login'), 2000);
      } else {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || t('invite.acceptError'));
      }
    } catch {
      setError(t('invite.connectionError'));
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)', padding: 24 }}>
      <div style={{ maxWidth: 420, width: '100%', background: 'var(--surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', padding: 40, boxShadow: 'var(--shadow-lg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 18, fontWeight: 700, fontFamily: 'var(--font-heading)' }}>د</div>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-heading)' }}>Daleel</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t('invite.joinTitle')}</div>
          </div>
        </div>

        {success ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', color: 'var(--success)' }}>
              <DIcon name="check" size={24} />
            </div>
            <h3 style={{ fontSize: 18, fontFamily: 'var(--font-heading)', marginBottom: 8 }}>{t('invite.successTitle')}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{t('invite.successDesc')}</p>
          </div>
        ) : (
          <>
            <h3 style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 6 }}>{t('invite.createAccount')}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>{t('invite.createDesc')}</p>

            {error && <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--error-bg)', color: 'var(--error)', fontSize: 13, marginBottom: 16 }}>{error}</div>}

            <FormField label={t('invite.fullName')} value={name} onChange={setName} placeholder={t('invite.namePlaceholder')} icon="user" />
            <FormField label={t('invite.password')} type="password" value={password} onChange={setPassword} placeholder={t('invite.passwordPlaceholder')} icon="lock" />

            <button onClick={handleAccept} disabled={loading} style={{ width: '100%', padding: 12, borderRadius: 10, background: 'var(--navy)', color: '#fff', fontSize: 14, fontWeight: 600, border: 'none', cursor: 'pointer', marginTop: 8 }}>
              {loading ? t('invite.creating') : t('invite.accept')}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
