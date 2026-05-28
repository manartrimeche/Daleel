import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import DIcon from '../components/DIcon';
import { LangSwitch } from '../components/UI';

const featureKeys = [
  { icon: 'search', titleKey: 'feat_search', descKey: 'feat_search_desc' },
  { icon: 'shieldCheck', titleKey: 'feat_compliance', descKey: 'feat_compliance_desc' },
  { icon: 'sparkle', titleKey: 'feat_sources', descKey: 'feat_sources_desc' },
  { icon: 'layers', titleKey: 'feat_watch', descKey: 'feat_watch_desc' },
  { icon: 'fileText', titleKey: 'feat_docs', descKey: 'feat_docs_desc' },
  { icon: 'users', titleKey: 'feat_users', descKey: 'feat_users_desc' },
];

const stats = [
  { value: '50+', labelKey: 'stat_texts' },
  { value: '10k+', labelKey: 'stat_articles' },
  { value: '99%', labelKey: 'stat_precision' },
  { value: '3', labelKey: 'stat_langs' },
];

export default function Landing() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 40px', borderBottom: '1px solid var(--border)', background: 'var(--surface)' }}>
        <img
          src="/daleel-logo-light.png?v=20260526"
          alt="Daleel"
          style={{ width: 230, height: 72, objectFit: 'contain', objectPosition: 'left center', display: 'block', flexShrink: 0 }}
        />
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button onClick={() => navigate('/login')} style={{ padding: '8px 20px', borderRadius: 'var(--radius-md)', background: 'transparent', color: 'var(--navy)', fontSize: 13, fontWeight: 600, border: '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s' }}>
            {t('landing.connexion')}
          </button>
          <button onClick={() => navigate('/login?mode=register')} style={{ padding: '8px 20px', borderRadius: 'var(--radius-md)', background: 'var(--navy)', color: '#fff', fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer', transition: 'all .15s' }}>
            {t('landing.inscription')}
          </button>
          <LangSwitch />
        </div>
      </header>

      <section style={{ background: 'linear-gradient(135deg, var(--navy) 0%, #2a3f5f 100%)', color: '#fff', padding: '80px 40px', textAlign: 'center' }}>
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          <div style={{ width: 64, height: 64, borderRadius: 16, background: 'rgba(255,255,255,0.92)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px', boxShadow: '0 12px 30px rgba(0,0,0,0.12)', overflow: 'hidden' }}>
            <img src="/daleel-mark-light.png?v=20260526" alt="" aria-hidden="true" style={{ width: 48, height: 46, objectFit: 'contain', display: 'block' }} />
          </div>
          <h1 style={{ fontSize: 36, fontWeight: 700, fontFamily: 'var(--font-heading)', lineHeight: 1.2, marginBottom: 16 }}>
            {t('landing.heroTitle')}
          </h1>
          <p style={{ fontSize: 16, lineHeight: 1.7, color: 'rgba(255,255,255,0.75)', marginBottom: 36 }}>
            {t('landing.heroDesc')}
          </p>
          <div style={{ display: 'flex', gap: 14, justifyContent: 'center' }}>
            <button onClick={() => navigate('/login?mode=register')} style={{ padding: '12px 28px', borderRadius: 'var(--radius-md)', background: 'var(--gold)', color: '#fff', fontSize: 14, fontWeight: 600, border: 'none', cursor: 'pointer' }}>
              {t('landing.createAccount')}
            </button>
            <button onClick={() => navigate('/login')} style={{ padding: '12px 28px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.1)', color: '#fff', fontSize: 14, fontWeight: 600, border: '1px solid rgba(255,255,255,0.2)', cursor: 'pointer' }}>
              {t('landing.login')}
            </button>
          </div>
        </div>
      </section>

      <section style={{ padding: '40px 40px', background: 'var(--surface)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 900, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 24, textAlign: 'center' }}>
          {stats.map((s, i) => (
            <div key={i}>
              <div style={{ fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--gold-dark)' }}>{s.value}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{t(`landing.${s.labelKey}`)}</div>
            </div>
          ))}
        </div>
      </section>

      <section style={{ padding: '60px 40px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <h2 style={{ fontSize: 26, fontWeight: 700, fontFamily: 'var(--font-heading)', textAlign: 'center', marginBottom: 8 }}>{t('landing.features')}</h2>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', textAlign: 'center', marginBottom: 40 }}>{t('landing.featuresDesc')}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
            {featureKeys.map((f, i) => (
              <div key={i} style={{ padding: '24px', borderRadius: 'var(--radius-lg)', background: 'var(--surface)', border: '1px solid var(--border)', transition: 'all .2s' }}>
                <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: 'var(--gold-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold)', marginBottom: 14 }}>
                  <DIcon name={f.icon} size={20} />
                </div>
                <h3 style={{ fontSize: 15, fontWeight: 600, fontFamily: 'var(--font-heading)', marginBottom: 6 }}>{t(`landing.${f.titleKey}`)}</h3>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{t(`landing.${f.descKey}`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ padding: '50px 40px', background: 'var(--navy)', textAlign: 'center' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', color: '#fff', marginBottom: 12 }}>{t('landing.ctaTitle')}</h2>
          <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.65)', marginBottom: 24 }}>{t('landing.ctaDesc')}</p>
          <button onClick={() => navigate('/login?mode=register')} style={{ padding: '12px 32px', borderRadius: 'var(--radius-md)', background: 'var(--gold)', color: '#fff', fontSize: 14, fontWeight: 600, border: 'none', cursor: 'pointer' }}>
            {t('landing.ctaButton')}
          </button>
        </div>
      </section>

      <footer style={{ padding: '20px 40px', borderTop: '1px solid var(--border)', background: 'var(--surface)', textAlign: 'center' }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('landing.footer')}</p>
      </footer>
    </div>
  );
}
