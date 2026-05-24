import { useTranslation } from 'react-i18next';
import { DCard, Badge } from '../../components/UI';
import { getUser } from '../../utils/auth';

export default function Settings() {
  const { t } = useTranslation();
  const user = getUser();

  return (
    <div style={{ padding: '28px 32px', maxWidth: 900 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('settings.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>{t('settings.subtitle')}</p>

      <DCard title={t('settings.accountInfo')} style={{ marginBottom: 20 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>{t('settings.name')}</div>
            <div style={{ fontSize: 14, fontWeight: 500 }}>{user?.full_name || '-'}</div>
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>{t('settings.email')}</div>
            <div style={{ fontSize: 14 }}>{user?.email || '-'}</div>
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>{t('settings.role')}</div>
            <Badge variant="gold">{user?.role || '-'}</Badge>
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>{t('settings.organization')}</div>
            <div style={{ fontSize: 14 }}>{user?.organization_name || '-'}</div>
          </div>
        </div>
      </DCard>

      <DCard title={t('settings.security')} style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid var(--border-subtle)' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>{t('settings.password')}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('settings.lastModified')}</div>
          </div>
          <button style={{ padding: '6px 14px', borderRadius: 6, background: 'var(--surface-active)', color: 'var(--text-secondary)', fontSize: 12, border: '1px solid var(--border)', cursor: 'pointer' }}>{t('common.edit')}</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>{t('settings.twoFactor')}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('settings.twoFactorDesc')}</div>
          </div>
          <Badge variant="neutral">{t('settings.notEnabled')}</Badge>
        </div>
      </DCard>

      <DCard title={t('settings.notifTitle')}>
        {[t('settings.notif_compliance'), t('settings.notif_docs'), t('settings.notif_legislative')].map((label, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: i < 2 ? '1px solid var(--border-subtle)' : 'none' }}>
            <span style={{ fontSize: 13 }}>{label}</span>
            <input type="checkbox" defaultChecked style={{ accentColor: 'var(--gold)', width: 16, height: 16 }} />
          </div>
        ))}
      </DCard>
    </div>
  );
}
