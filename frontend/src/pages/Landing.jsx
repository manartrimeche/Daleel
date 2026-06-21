import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import DIcon from '../components/DIcon';
import { LangSwitch } from '../components/UI';
import legalAiComplianceBg from '../assets/legal-ai-compliance-bg.webp';

const featureKeys = [
  { icon: 'eye', titleKey: 'feat_search', descKey: 'feat_search_desc' },
  { icon: 'search', titleKey: 'feat_compliance', descKey: 'feat_compliance_desc' },
  { icon: 'sparkle', titleKey: 'feat_sources', descKey: 'feat_sources_desc' },
  { icon: 'fileText', titleKey: 'feat_watch', descKey: 'feat_watch_desc' },
  { icon: 'shieldCheck', titleKey: 'feat_docs', descKey: 'feat_docs_desc' },
  { icon: 'users', titleKey: 'feat_users', descKey: 'feat_users_desc' },
];

function formatCount(value, locale) {
  if (!Number.isFinite(value)) return null;
  return new Intl.NumberFormat(locale).format(value);
}

export default function Landing() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [platformStats, setPlatformStats] = useState(null);

  useEffect(() => {
    let ignore = false;
    fetch('/api/v1/platform/stats')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!ignore) setPlatformStats(data);
      })
      .catch(() => {
        if (!ignore) setPlatformStats(null);
      });
    return () => { ignore = true; };
  }, []);

  const locale = i18n.language || 'fr';
  const unavailable = t('landing.stat_unavailable');
  const stats = [
    { value: formatCount(platformStats?.legal_texts_indexed, locale) ?? unavailable, labelKey: 'stat_texts', icon: 'database' },
    { value: formatCount(811, locale), labelKey: 'stat_articles', icon: 'fileSearch' },
    { value: '85%', labelKey: 'stat_precision', icon: 'shieldCheck' },
    { value: formatCount(platformStats?.supported_languages, locale) ?? unavailable, labelKey: 'stat_langs', icon: 'globe' },
  ];

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
      <header style={{ position: 'sticky', top: 0, zIndex: 30, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', padding: '8px clamp(16px, 4vw, 32px)', borderBottom: '1px solid rgba(255,255,255,0.12)', backgroundImage: `linear-gradient(135deg, rgba(8, 22, 30, 0.9) 0%, rgba(12, 30, 48, 0.82) 48%, rgba(8, 22, 30, 0.92) 100%), url(${legalAiComplianceBg})`, backgroundSize: 'cover', backgroundPosition: 'center top', backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)', boxShadow: '0 10px 24px rgba(8, 22, 30, 0.18)' }}>
        <img
          src="/didax-logo-light.png"
          alt="Didax IT"
          style={{ width: 'clamp(170px, 32vw, 280px)', height: 48, objectFit: 'contain', objectPosition: 'left center', display: 'block', flexShrink: 0 }}
        />
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap', maxWidth: '100%' }}>
          <button className="landing-button landing-button-ghost" onClick={() => navigate('/login')} style={{ padding: '5px 10px', borderRadius: 6, background: 'rgba(255,255,255,0.07)', color: '#fff', fontSize: 11, fontWeight: 600, border: '1px solid rgba(255,255,255,0.18)', cursor: 'pointer', minHeight: 28 }}>
            {t('landing.connexion')}
          </button>
          <button className="landing-button landing-button-gold" onClick={() => navigate('/login?mode=register')} style={{ padding: '5px 10px', borderRadius: 6, background: 'var(--gold)', color: '#fff', fontSize: 11, fontWeight: 600, border: 'none', cursor: 'pointer', minHeight: 28 }}>
            {t('landing.inscription')}
          </button>
          <LangSwitch dark />
        </div>
      </header>

      <section style={{
        backgroundImage: `linear-gradient(135deg, rgba(8, 22, 30, 0.88) 0%, rgba(12, 30, 48, 0.78) 48%, rgba(8, 22, 30, 0.9) 100%), url(${legalAiComplianceBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        color: '#fff',
        padding: '80px 40px',
        minHeight: 520,
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
      }}>
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          <img
            src="/daleel-logo-light.png?v=20260526"
            alt="Daleel"
            style={{ width: 'clamp(130px, 18vw, 180px)', height: 'auto', objectFit: 'contain', display: 'block', margin: '0 auto 16px', filter: 'brightness(0) invert(1)' }}
          />
          <h1 style={{ fontSize: 36, fontWeight: 700, fontFamily: 'var(--font-heading)', lineHeight: 1.2, marginBottom: 16 }}>
            {t('landing.heroTitle')}
          </h1>
          <p style={{ fontSize: 16, lineHeight: 1.7, color: 'rgba(255,255,255,0.75)', marginBottom: 36 }}>
            {t('landing.heroDesc')}
          </p>
          <div style={{ display: 'flex', gap: 14, justifyContent: 'center' }}>
              <button className="landing-button landing-button-gold" onClick={() => navigate('/login?mode=register')} style={{ padding: '12px 28px', borderRadius: 'var(--radius-md)', background: 'var(--gold)', color: '#fff', fontSize: 14, fontWeight: 600, border: 'none', cursor: 'pointer' }}>
                {t('landing.createAccount')}
              </button>
              <button className="landing-button landing-button-ghost" onClick={() => navigate('/login')} style={{ padding: '12px 28px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.1)', color: '#fff', fontSize: 14, fontWeight: 600, border: '1px solid rgba(255,255,255,0.2)', cursor: 'pointer' }}>
                {t('landing.login')}
              </button>
          </div>
        </div>
      </section>

      <section style={{ padding: '64px 40px', background: 'var(--bg)' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <h2 style={{ fontSize: 26, fontWeight: 700, fontFamily: 'var(--font-heading)', textAlign: 'center', marginBottom: 8 }}>{t('landing.statsTitle', 'Nos chiffres')}</h2>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', textAlign: 'center', marginBottom: 40 }}>{t('landing.statsDesc', 'Une base juridique structurée pour accélérer votre conformité.')}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 20 }}>
          {stats.map((s, i) => (
            <div className="landing-card" key={i} style={{ minHeight: 154, padding: '24px 18px 22px', borderRadius: 'var(--radius-lg)', background: 'var(--surface)', border: '1px solid var(--border)', borderTop: '4px solid var(--gold)', boxShadow: '0 12px 30px rgba(15, 35, 50, 0.07)', textAlign: 'center' }}>
              <div style={{ width: 42, height: 42, borderRadius: 'var(--radius-md)', margin: '0 auto 16px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold-dark)', background: 'var(--gold-bg)', border: '1px solid rgba(196,149,62,0.18)' }}>
                <DIcon name={s.icon} size={21} />
              </div>
              <div style={{ fontSize: 34, fontWeight: 800, fontFamily: 'var(--font-heading)', color: 'var(--navy)', lineHeight: 1, marginBottom: 10 }}>{s.value}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 700, letterSpacing: 0, textTransform: 'uppercase' }}>{t(`landing.${s.labelKey}`)}</div>
            </div>
          ))}
          </div>
        </div>
      </section>

      <section style={{ padding: '64px 40px', background: 'linear-gradient(135deg, rgba(246,248,249,0.96) 0%, rgba(237,242,243,0.92) 52%, rgba(249,246,238,0.92) 100%)' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <h2 style={{ fontSize: 26, fontWeight: 700, fontFamily: 'var(--font-heading)', textAlign: 'center', marginBottom: 8 }}>{t('landing.features')}</h2>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', textAlign: 'center', marginBottom: 40 }}>{t('landing.featuresDesc')}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20 }}>
            {featureKeys.map((f, i) => (
              <div className="landing-card" key={i} style={{ position: 'relative', minHeight: 178, padding: '24px', borderRadius: 'var(--radius-lg)', background: 'var(--surface)', border: '1px solid var(--border)', borderTop: '4px solid var(--gold)', boxShadow: '0 12px 30px rgba(15, 35, 50, 0.07)', transition: 'all .2s', textAlign: 'center' }}>
                <div style={{ width: 42, height: 42, borderRadius: 'var(--radius-md)', background: 'var(--gold-bg)', border: '1px solid rgba(196,149,62,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold-dark)', margin: '0 auto 16px' }}>
                  <DIcon name={f.icon} size={21} />
                </div>
                <h3 style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 8, color: 'var(--navy)' }}>{t(`landing.${f.titleKey}`)}</h3>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>{t(`landing.${f.descKey}`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{
        padding: '64px 40px',
        backgroundImage: `linear-gradient(135deg, rgba(8, 22, 30, 0.9) 0%, rgba(12, 30, 48, 0.84) 52%, rgba(8, 22, 30, 0.92) 100%), url(${legalAiComplianceBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center 62%',
        textAlign: 'center',
      }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', color: '#fff', marginBottom: 12 }}>{t('landing.ctaTitle')}</h2>
          <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.65)', marginBottom: 24 }}>{t('landing.ctaDesc')}</p>
          <button className="landing-button landing-button-gold" onClick={() => navigate('/login?mode=register')} style={{ padding: '12px 32px', borderRadius: 'var(--radius-md)', background: 'var(--gold)', color: '#fff', fontSize: 14, fontWeight: 600, border: 'none', cursor: 'pointer' }}>
            {t('landing.ctaButton')}
          </button>
        </div>
      </section>

      <footer style={{ padding: '20px 40px', borderTop: '1px solid var(--border)', background: 'var(--surface)', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 14, flexWrap: 'wrap' }}>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>{t('landing.footer')}</p>
        </div>
      </footer>
    </div>
  );
}
