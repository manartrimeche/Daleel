import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import DIcon from '../components/DIcon';
import { FormField, LangSwitch } from '../components/UI';
import { setTokens, setUser } from '../utils/auth';
import { useAuth } from '../utils/AuthContext';

const styles = {
  page: { display: 'flex', height: '100vh', overflow: 'hidden' },
  left: { flex: '0 0 52%', background: 'var(--navy)', position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '60px 72px', color: '#fff', overflow: 'hidden' },
  right: { flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '48px 64px', background: 'var(--bg)', overflowY: 'auto' },
  pattern: { position: 'absolute', inset: 0, opacity: 0.035, backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 24px, rgba(255,255,255,0.4) 24px, rgba(255,255,255,0.4) 25px)', pointerEvents: 'none' },
  glow: { position: 'absolute', top: '-20%', right: '-10%', width: 500, height: 500, borderRadius: '50%', background: 'radial-gradient(circle, rgba(198,125,74,0.12) 0%, transparent 70%)', pointerEvents: 'none' },
};

const featureKeys = [
  { icon: 'search', titleKey: 'feat_search', descKey: 'feat_search_desc' },
  { icon: 'shieldCheck', titleKey: 'feat_compliance', descKey: 'feat_compliance_desc' },
  { icon: 'sparkle', titleKey: 'feat_sources', descKey: 'feat_sources_desc' },
  { icon: 'layers', titleKey: 'feat_watch', descKey: 'feat_watch_desc' },
];

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { updateUser } = useAuth();
  const { t } = useTranslation();
  const [mode, setMode] = useState(searchParams.get('mode') === 'register' ? 'register' : 'login');
  const [email, setEmail] = useState('');
  const [pass, setPass] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [name, setName] = useState('');
  const [org, setOrg] = useState('');
  const [sector, setSector] = useState('banque');
  const [customSector, setCustomSector] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError('');
    setMessage('');
    if (mode === 'forgot') {
      if (!email.trim()) {
        setError(t('login.emailRequired'));
        return;
      }
      setLoading(true);
      try {
        const res = await fetch('/api/v1/auth/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || t('login.resetRequestError'));
        setMessage(data.message || t('login.resetRequestSuccess'));
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
      return;
    }
    if (mode === 'register' && pass !== confirmPass) {
      setError(t('login.passwordMismatch'));
      return;
    }
    const submittedSector = sector === 'autre' ? customSector.trim() : sector;
    if (mode === 'register' && sector === 'autre' && submittedSector.length < 2) {
      setError(t('login.customSectorRequired'));
      return;
    }
    setLoading(true);
    try {
      const endpoint = mode === 'login' ? '/api/v1/auth/login' : '/api/v1/auth/register';
      const body = mode === 'login'
        ? { email, password: pass }
        : { email, password: pass, full_name: name, organization_name: org, sector: submittedSector };

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Erreur de connexion');
      }

      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      setUser(data.user);
      updateUser(data.user);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div style={styles.page} onKeyDown={handleKeyDown}>
      <div style={{ position: 'absolute', top: 16, right: 24, zIndex: 10 }}>
        <LangSwitch />
      </div>
      <div style={styles.left}>
        <div style={styles.pattern} />
        <div style={styles.glow} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 48 }}>
            <div style={{ width: 44, height: 44, borderRadius: 10, background: 'linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-heading)' }}>د</div>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-heading)', letterSpacing: '-0.02em' }}>Daleel</div>
              <div style={{ fontSize: 11, opacity: 0.5, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Legal Intelligence Platform</div>
            </div>
          </div>

          <h2 style={{ fontSize: 26, fontWeight: 600, fontFamily: 'var(--font-heading)', marginBottom: 12, lineHeight: 1.3, whiteSpace: 'pre-line' }}>{t('login.heroTitle')}</h2>
          <p style={{ fontSize: 15, opacity: 0.55, lineHeight: 1.7, marginBottom: 40, maxWidth: 440 }}>{t('login.heroDesc')}</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {featureKeys.map((f, i) => (
              <div key={i} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'var(--gold-light)' }}><DIcon name={f.icon} size={17} /></div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 2 }}>{t(`login.${f.titleKey}`)}</div>
                  <div style={{ fontSize: 13, opacity: 0.5, lineHeight: 1.4 }}>{t(`login.${f.descKey}`)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={styles.right}>
        <div style={{ maxWidth: 380, width: '100%', margin: '0 auto' }}>
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 6 }}>{mode === 'forgot' ? t('login.forgotTitle') : mode === 'login' ? t('login.title') : t('login.titleRegister')}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              {mode === 'forgot' ? t('login.forgotSubtitle') : mode === 'login' ? t('login.subtitle') : t('login.subtitleRegister')}
            </p>
          </div>

          {mode !== 'forgot' && <div style={{ display: 'flex', gap: 0, marginBottom: 24, background: 'var(--surface-active)', borderRadius: 8, padding: 3 }}>
            {['login', 'register'].map(m => (
              <button key={m} onClick={() => { setMode(m); setError(''); setMessage(''); setConfirmPass(''); setCustomSector(''); }} style={{ flex: 1, padding: '8px 0', borderRadius: 6, fontSize: 13, fontWeight: mode === m ? 600 : 400, background: mode === m ? 'var(--surface)' : 'transparent', color: mode === m ? 'var(--text)' : 'var(--text-muted)', border: 'none', cursor: 'pointer', boxShadow: mode === m ? 'var(--shadow-sm)' : 'none', transition: 'all .15s' }}>
                {m === 'login' ? t('login.tabLogin') : t('login.tabRegister')}
              </button>
            ))}
          </div>}

          {error && (
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--error-bg)', color: 'var(--error)', fontSize: 13, marginBottom: 16, border: '1px solid rgba(185,28,28,0.15)' }}>{error}</div>
          )}
          {message && (
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--success-bg)', color: 'var(--success)', fontSize: 13, marginBottom: 16, border: '1px solid rgba(45,106,79,0.15)' }}>{message}</div>
          )}

          {mode === 'register' && (
            <FormField label={t('login.fullName')} value={name} onChange={setName} placeholder="Mohamed Ben Ali" icon="user" />
          )}
          <FormField label={t('login.email')} type="email" value={email} onChange={setEmail} placeholder="nom@entreprise.tn" icon="mail" />
          {mode !== 'forgot' && <FormField label={t('login.password')} type="password" value={pass} onChange={setPass} placeholder="••••••••" icon="lock" />}
          {mode === 'register' && (
            <>
              <FormField label={t('login.confirmPassword')} type="password" value={confirmPass} onChange={setConfirmPass} placeholder="••••••••" icon="lock" />
              <FormField label={t('login.orgName')} value={org} onChange={setOrg} placeholder="Banque de Tunis" icon="database" />
              <FormField label={t('login.sector')} type="select" value={sector} onChange={(value) => { setSector(value); if (value !== 'autre') setCustomSector(''); }} options={[
                { value: 'banque', label: t('login.sectors.banque') },
                { value: 'assurance', label: t('login.sectors.assurance') },
                { value: 'industrie', label: t('login.sectors.industrie') },
                { value: 'telecom', label: t('login.sectors.telecom') },
                { value: 'sante', label: t('login.sectors.sante') },
                { value: 'public', label: t('login.sectors.public') },
                { value: 'autre', label: t('login.sectors.autre') },
              ]} />
              {sector === 'autre' && (
                <FormField label={t('login.customSector')} value={customSector} onChange={setCustomSector} placeholder={t('login.customSectorPlaceholder')} icon="edit" />
              )}
            </>
          )}

          {mode === 'login' && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, marginTop: -4 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                <input type="checkbox" defaultChecked style={{ accentColor: 'var(--gold)' }} /> {t('login.rememberMe')}
              </label>
              <button type="button" onClick={() => { setMode('forgot'); setError(''); setMessage(''); }} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('login.forgotPassword')}</button>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading}
            style={{ width: '100%', padding: '12px', borderRadius: 10, background: 'var(--navy)', color: '#fff', fontSize: 14, fontWeight: 600, cursor: loading ? 'wait' : 'pointer', border: 'none', marginTop: 12, transition: 'opacity .15s', opacity: loading ? 0.7 : 1 }}
            onMouseEnter={e => { if (!loading) e.target.style.opacity = '0.9'; }}
            onMouseLeave={e => { e.target.style.opacity = loading ? '0.7' : '1'; }}
          >
            {loading ? t('login.submitting') : mode === 'forgot' ? t('login.sendResetLink') : mode === 'login' ? t('login.submit') : t('login.submitRegister')}
          </button>

          {mode === 'forgot' && (
            <button
              type="button"
              onClick={() => { setMode('login'); setError(''); setMessage(''); }}
              style={{ width: '100%', padding: '10px', marginTop: 10, borderRadius: 10, background: 'transparent', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600, cursor: 'pointer', border: '1px solid var(--border)' }}
            >
              {t('login.backToLogin')}
            </button>
          )}

        </div>
      </div>
    </div>
  );
}
