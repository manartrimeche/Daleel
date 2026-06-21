import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FormField, LangSwitch } from '../components/UI';
import { setTokens, setUser } from '../utils/auth';
import { useAuth } from '../utils/AuthContext';
import loginLegalBg from '../assets/login-legal-bg.webp';

const styles = {
  page: { display: 'flex', height: '100vh', overflow: 'hidden' },
  left: { flex: '0 0 52%', backgroundColor: 'var(--navy)', backgroundImage: `linear-gradient(135deg, rgba(5, 25, 48, 0.94), rgba(13, 69, 115, 0.82)), url(${loginLegalBg})`, backgroundSize: 'cover', backgroundPosition: 'center', position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '28px 72px', color: '#fff', overflow: 'hidden' },
  right: { flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '48px 64px', background: 'var(--bg)', overflowY: 'auto' },
};

// Numéro E.164 simple : "+" optionnel puis 8 à 15 chiffres commençant par 1-9.
const PHONE_REGEX = /^\+?[1-9]\d{7,14}$/;

const COUNTRY_META = {
  tunisia: { dialCode: '+216', jurisdiction: 'tunisia', phonePlaceholder: '98 123 456', phoneLen: 8 },
  uae:     { dialCode: '+971', jurisdiction: 'uae',     phonePlaceholder: '50 123 4567', phoneLen: 9 },
};


export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { updateUser } = useAuth();
  const { t } = useTranslation();
  const [mode, setMode] = useState(searchParams.get('mode') === 'register' ? 'register' : 'login');
  // Étape du wizard d'inscription : 'profile' → 'contact' → 'verify' → 'done'.
  const [step, setStep] = useState('profile');

  // ── Champs login / forgot ──
  const [email, setEmail] = useState('');
  const [pass, setPass] = useState('');

  // ── Champs inscription : profil entreprise (étape 1) ──
  const [org, setOrg] = useState('');
  const [country, setCountry] = useState('tunisia');
  const [sector, setSector] = useState('banque');
  const [customSector, setCustomSector] = useState('');
  const [size, setSize] = useState('small');
  const [employees, setEmployees] = useState('');
  const [activities, setActivities] = useState('');

  // ── Champs inscription : contact (étape 2) ──
  const [name, setName] = useState('');
  const [phoneLocal, setPhoneLocal] = useState(''); // partie locale sans indicatif
  const [confirmPass, setConfirmPass] = useState('');

  const meta = COUNTRY_META[country] || COUNTRY_META.other;
  const fullPhone = meta.dialCode + phoneLocal.replace(/[\s\-()]/g, '');

  // ── Vérification (étape 3) ──
  const [userId, setUserId] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [, setOtpSent] = useState(true); // l'OTP est envoyé automatiquement par /register
  const [, setPhoneVerified] = useState(false);

  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
    setStep('profile');
    setError(''); setMessage('');
    setPass(''); setConfirmPass(''); setOtpCode('');
    setOtpSent(true); setPhoneVerified(false); setUserId('');
  };

  // ── Étape 1 → 2 : validation du profil entreprise ──
  const handleProfileNext = () => {
    setError('');
    if (org.trim().length < 2) return setError(t('login.errOrgName'));
    if (!country) return setError(t('login.errCountry'));
    const submittedSector = sector === 'autre' ? customSector.trim() : sector;
    if (sector === 'autre' && submittedSector.length < 2) return setError(t('login.customSectorRequired'));
    setStep('contact');
  };

  // ── Étape 2 : POST /register (pas de token, juste user_id) ──
  const handleRegister = async () => {
    setError('');
    if (name.trim().length < 2) return setError(t('login.errFullName'));
    if (!email.trim()) return setError(t('login.emailRequired'));
    const localDigits = phoneLocal.replace(/[\s\-()]/g, '');
    if (meta.phoneLen > 0 && localDigits.length !== meta.phoneLen) {
      return setError(t('login.errPhoneLen', { len: meta.phoneLen, code: meta.dialCode }));
    }
    if (!PHONE_REGEX.test(fullPhone)) return setError(t('login.errPhone'));
    if (pass.length < 8) return setError(t('login.errPasswordShort'));
    if (pass !== confirmPass) return setError(t('login.passwordMismatch'));

    const submittedSector = sector === 'autre' ? customSector.trim() : sector;
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          phone: fullPhone,
          password: pass,
          full_name: name.trim(),
          organization_name: org.trim(),
          sector: submittedSector,
          size,
          employees: employees ? Number(employees) : undefined,
          activities: activities.trim() || undefined,
          country,
          jurisdiction: country,
          needs: [],
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || t('login.serverError'));
      setUserId(data.user_id);
      setMessage(data.message || t('login.registrationPending'));
      setStep('verify');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Étape 3 : renvoi OTP / vérification du code ──
  const resendOtp = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/verify-phone/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || t('login.otpResendError'));
      setOtpSent(true);
      setMessage(t('login.otpResent'));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    setError('');
    if (!/^\d{4,8}$/.test(otpCode)) return setError(t('login.errOtpFormat'));
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/verify-phone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, code: otpCode }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || t('login.otpVerifyError'));
      setPhoneVerified(true);
      setMessage(t('login.otpVerified'));
      setStep('done');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Login / forgot inchangés ──
  const handleSubmit = async () => {
    setError(''); setMessage('');
    if (mode === 'forgot') {
      if (!email.trim()) return setError(t('login.emailRequired'));
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
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: pass }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 401) throw new Error(t('login.invalidCredentials'));
        if (res.status >= 500) throw new Error(t('login.serverError'));
        throw new Error(data.detail || t('login.serverError'));
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
    if (e.key !== 'Enter') return;
    if (mode === 'register') {
      if (step === 'profile') handleProfileNext();
      else if (step === 'contact') handleRegister();
      else if (step === 'verify') verifyOtp();
    } else {
      handleSubmit();
    }
  };

  // ── Render helpers : titre + sous-titre selon mode/étape ──
  const headerTitle = mode === 'forgot' ? t('login.forgotTitle')
    : mode === 'login' ? t('login.title')
    : step === 'profile' ? t('login.wizard.profileTitle')
    : step === 'contact' ? t('login.wizard.contactTitle')
    : step === 'verify' ? t('login.wizard.verifyTitle')
    : t('login.wizard.doneTitle');
  const headerSubtitle = mode === 'forgot' ? t('login.forgotSubtitle')
    : mode === 'login' ? t('login.subtitle')
    : step === 'profile' ? t('login.wizard.profileSubtitle')
    : step === 'contact' ? t('login.wizard.contactSubtitle')
    : step === 'verify' ? t('login.wizard.verifySubtitle')
    : t('login.wizard.doneSubtitle');

  return (
    <div style={styles.page} onKeyDown={handleKeyDown}>
      <div style={{ position: 'absolute', top: 16, right: 24, zIndex: 10 }}>
        <LangSwitch />
      </div>
      <div style={styles.left}>
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
          <button
            type="button"
            onClick={() => navigate('/')}
            aria-label="Daleel landing page"
            style={{ display: 'block', padding: 0, border: 'none', background: 'transparent', cursor: 'pointer', margin: '0 auto 100px' }}
          >
            <img
              src="/daleel-logo-dark.png?v=20260526d"
              alt="Daleel"
              style={{ width: 360, height: 112, objectFit: 'contain', objectPosition: 'center', display: 'block', transform: 'scale(1.08)', transformOrigin: 'center' }}
            />
          </button>
          <h2 style={{ fontSize: 24, fontWeight: 600, fontFamily: 'var(--font-heading)', marginBottom: 10, lineHeight: 1.22, whiteSpace: 'pre-line' }}>{t('login.heroTitle')}</h2>
          <p style={{ fontSize: 14, opacity: 0.55, lineHeight: 1.55, maxWidth: 440, margin: '0 auto' }}>{t('login.heroDesc')}</p>
        </div>
      </div>

      <div style={styles.right}>
        <div style={{ maxWidth: 420, width: '100%', margin: '0 auto' }}>
          <div style={{ marginBottom: 24, textAlign: 'center' }}>
            <h3 style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 6 }}>{headerTitle}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{headerSubtitle}</p>
            {mode === 'register' && step !== 'done' && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 12 }}>
                {['profile', 'contact', 'verify'].map((s, i) => (
                  <div key={s} style={{ width: 28, height: 4, borderRadius: 2, background: step === s ? 'var(--gold)' : i < ['profile', 'contact', 'verify'].indexOf(step) ? 'var(--navy)' : 'var(--border)' }} />
                ))}
              </div>
            )}
          </div>

          {error && (
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--error-bg)', color: 'var(--error)', fontSize: 13, marginBottom: 16, border: '1px solid rgba(185,28,28,0.15)' }}>{error}</div>
          )}
          {message && (
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--success-bg)', color: 'var(--success)', fontSize: 13, marginBottom: 16, border: '1px solid rgba(45,106,79,0.15)' }}>{message}</div>
          )}

          {/* ── LOGIN / FORGOT ── */}
          {mode !== 'register' && (
            <>
              <FormField label={t('login.email')} type="email" value={email} onChange={setEmail} placeholder="nom@entreprise.tn" icon="mail" />
              {mode !== 'forgot' && <FormField label={t('login.password')} type="password" value={pass} onChange={setPass} placeholder="*************" icon="lock" />}
              {mode === 'login' && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, marginTop: -4 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <input type="checkbox" defaultChecked style={{ accentColor: 'var(--gold)' }} /> {t('login.rememberMe')}
                  </label>
                  <button type="button" onClick={() => { setMode('forgot'); setError(''); setMessage(''); }} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('login.forgotPassword')}</button>
                </div>
              )}
              <button onClick={handleSubmit} disabled={loading} className="hover-opacity" style={{ width: '100%', padding: '12px', borderRadius: 10, background: 'var(--navy)', color: '#fff', fontSize: 14, fontWeight: 600, cursor: loading ? 'wait' : 'pointer', border: 'none', marginTop: 12, opacity: loading ? 0.7 : 1 }}>
                {loading ? t('login.submitting') : mode === 'forgot' ? t('login.sendResetLink') : t('login.submit')}
              </button>
              {mode === 'forgot' && (
                <button type="button" onClick={() => { setMode('login'); setError(''); setMessage(''); }} style={{ width: '100%', padding: '10px', marginTop: 10, borderRadius: 10, background: 'transparent', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600, cursor: 'pointer', border: '1px solid var(--border)' }}>
                  {t('login.backToLogin')}
                </button>
              )}
              <div style={{ marginTop: 18, textAlign: 'center', fontSize: 13, color: 'var(--text-secondary)' }}>
                {mode === 'login' ? t('login.noAccount') : t('login.hasAccount')}{' '}
                <button type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); resetForm(); }} style={{ color: 'var(--gold)', fontWeight: 700, background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}>
                  {mode === 'login' ? t('login.createAccountLink') : t('login.signInLink')}
                </button>
              </div>
            </>
          )}

          {/* ── REGISTER ÉTAPE 1 : PROFIL ENTREPRISE ── */}
          {mode === 'register' && step === 'profile' && (
            <>
              <FormField label={t('login.orgName')} value={org} onChange={setOrg} placeholder="Banque de Tunis" icon="database" />
              <FormField label={t('login.country')} type="select" value={country} onChange={setCountry} options={[
                { value: 'tunisia', label: t('login.countries.tunisia') },
                { value: 'uae', label: t('login.countries.uae') },
              ]} />
              <FormField label={t('login.sector')} type="select" value={sector} onChange={(v) => { setSector(v); if (v !== 'autre') setCustomSector(''); }} options={[
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
              <FormField label={t('login.size')} type="select" value={size} onChange={setSize} options={[
                { value: 'micro', label: t('login.sizes.micro') },
                { value: 'small', label: t('login.sizes.small') },
                { value: 'medium', label: t('login.sizes.medium') },
                { value: 'large', label: t('login.sizes.large') },
              ]} />
              <FormField label={t('login.employees')} type="number" value={employees} onChange={setEmployees} placeholder="50" />
              <FormField label={t('login.activities')} value={activities} onChange={setActivities} placeholder={t('login.activitiesPlaceholder')} icon="edit" />

              <button onClick={handleProfileNext} disabled={loading} className="hover-opacity" style={{ width: '100%', padding: '12px', borderRadius: 10, background: 'var(--navy)', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer', border: 'none', marginTop: 12 }}>
                {t('login.wizard.next')}
              </button>
              <div style={{ marginTop: 18, textAlign: 'center', fontSize: 13, color: 'var(--text-secondary)' }}>
                {t('login.hasAccount')}{' '}
                <button type="button" onClick={() => { setMode('login'); resetForm(); }} style={{ color: 'var(--gold)', fontWeight: 700, background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}>
                  {t('login.signInLink')}
                </button>
              </div>
            </>
          )}

          {/* ── REGISTER ÉTAPE 2 : CONTACT ── */}
          {mode === 'register' && step === 'contact' && (
            <>
              <FormField label={t('login.fullName')} value={name} onChange={setName} placeholder="Mohamed Ben Ali" icon="user" />
              <FormField label={t('login.email')} type="email" value={email} onChange={setEmail} placeholder={
                country === 'uae' ? 'name@company.ae' : 'nom@entreprise.tn'
              } icon="mail" />
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 5 }}>{t('login.phone')}</label>
                <div style={{ display: 'flex', gap: 0 }}>
                  <div style={{ padding: '10px 12px', borderRadius: '8px 0 0 8px', border: '1px solid var(--border)', borderRight: 'none', background: 'var(--border)', fontSize: 13, fontWeight: 600, color: 'var(--text)', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center' }}>
                    {meta.dialCode}
                  </div>
                  <input
                    type="tel"
                    value={phoneLocal}
                    onChange={e => setPhoneLocal(e.target.value)}
                    placeholder={meta.phonePlaceholder}
                    style={{ flex: 1, padding: '10px 14px', borderRadius: '0 8px 8px 0', border: '1px solid var(--border)', fontSize: 13, background: 'var(--surface)', color: 'var(--text)', outline: 'none' }}
                  />
                </div>
                {meta.phoneLen > 0 && (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>
                    {t('login.phoneHint', { len: meta.phoneLen, code: meta.dialCode })}
                  </div>
                )}
              </div>
              <FormField label={t('login.password')} type="password" value={pass} onChange={setPass} placeholder="*************" icon="lock" />
              <FormField label={t('login.confirmPassword')} type="password" value={confirmPass} onChange={setConfirmPass} placeholder="*************" icon="lock" />

              <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
                <button type="button" onClick={() => setStep('profile')} disabled={loading} style={{ flex: 1, padding: '12px', borderRadius: 10, background: 'transparent', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600, cursor: 'pointer', border: '1px solid var(--border)' }}>
                  {t('login.wizard.back')}
                </button>
                <button onClick={handleRegister} disabled={loading} className="hover-opacity" style={{ flex: 2, padding: '12px', borderRadius: 10, background: 'var(--navy)', color: '#fff', fontSize: 14, fontWeight: 600, cursor: loading ? 'wait' : 'pointer', border: 'none', opacity: loading ? 0.7 : 1 }}>
                  {loading ? t('login.submitting') : t('login.wizard.submitRegister')}
                </button>
              </div>
            </>
          )}

          {/* ── REGISTER ÉTAPE 3 : VÉRIFICATIONS ── */}
          {mode === 'register' && step === 'verify' && (
            <>
              <div style={{ padding: '12px 14px', borderRadius: 8, background: 'var(--surface)', border: '1px solid var(--border)', fontSize: 13, marginBottom: 14 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{t('login.verify.emailTitle')}</div>
                <div style={{ color: 'var(--text-secondary)' }}>{t('login.verify.emailDesc', { email })}</div>
              </div>

              <div style={{ padding: '12px 14px', borderRadius: 8, background: 'var(--surface)', border: '1px solid var(--border)', fontSize: 13, marginBottom: 14 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{t('login.verify.phoneTitle')}</div>
                <div style={{ color: 'var(--text-secondary)', marginBottom: 10 }}>{t('login.verify.phoneDesc', { phone: fullPhone })}</div>
                <FormField label={t('login.verify.otpLabel')} value={otpCode} onChange={setOtpCode} placeholder="123456" icon="lock" />
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" onClick={resendOtp} disabled={loading} style={{ flex: 1, padding: '10px', borderRadius: 8, background: 'transparent', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600, cursor: 'pointer', border: '1px solid var(--border)' }}>
                    {t('login.verify.resend')}
                  </button>
                  <button type="button" onClick={verifyOtp} disabled={loading || !otpCode} className="hover-opacity" style={{ flex: 2, padding: '10px', borderRadius: 8, background: 'var(--navy)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: loading ? 'wait' : 'pointer', border: 'none', opacity: (loading || !otpCode) ? 0.6 : 1 }}>
                    {loading ? t('login.submitting') : t('login.verify.confirm')}
                  </button>
                </div>
              </div>

              <button type="button" onClick={() => { setMode('login'); resetForm(); }} style={{ width: '100%', padding: '10px', marginTop: 8, borderRadius: 10, background: 'transparent', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600, cursor: 'pointer', border: '1px solid var(--border)' }}>
                {t('login.backToLogin')}
              </button>
            </>
          )}

          {/* ── REGISTER ÉTAPE 4 : ATTENTE D'APPROBATION ── */}
          {mode === 'register' && step === 'done' && (
            <>
              <div style={{ padding: '20px', borderRadius: 12, background: 'var(--surface)', border: '1px solid var(--border)', textAlign: 'center', marginBottom: 16 }}>
                <div style={{ fontSize: 48, marginBottom: 12 }}>✓</div>
                <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>{t('login.wizard.doneHeading')}</div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{t('login.wizard.doneBody')}</div>
              </div>
              <button type="button" onClick={() => { setMode('login'); resetForm(); }} className="hover-opacity" style={{ width: '100%', padding: '12px', borderRadius: 10, background: 'var(--navy)', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer', border: 'none' }}>
                {t('login.backToLogin')}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
