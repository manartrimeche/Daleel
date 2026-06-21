import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { DCard, Badge, StatCard } from '../../components/UI';
import { authFetch, getUser } from '../../utils/auth';

export default function CompanyProfile() {
  const { t } = useTranslation();
  const currentUser = getUser();
  const orgId = currentUser?.organization_id;
  const [org, setOrg] = useState(null);
  const [loading, setLoading] = useState(() => Boolean(orgId));
  const [saving, setSaving] = useState(false);

  async function loadOrg() {
    try {
      const res = await authFetch(`/api/v1/auth/organizations/${orgId}`);
      if (res.ok) setOrg(await res.json());
    } catch {
      // Missing organization details are handled by the empty state.
    }
    setLoading(false);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (orgId) void Promise.resolve().then(loadOrg); }, [orgId]);

  const saveOrg = async () => {
    if (!org || !orgId) return;
    setSaving(true);
    try {
      await authFetch(`/api/v1/auth/organizations/${orgId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: org.name, sector: org.sector, size: org.size, employees: org.employees, jurisdiction: org.jurisdiction }),
      });
    } catch {
      // Saving errors currently leave the edited form in place.
    }
    setSaving(false);
  };

  if (loading) return <div style={{ padding: '28px 32px', color: 'var(--text-muted)' }}>{t('common.loading')}</div>;
  if (!org) return <div style={{ padding: '28px 32px' }}><h1 style={{ fontSize: 24, fontFamily: 'var(--font-heading)' }}>{t('company.title')}</h1><p style={{ color: 'var(--text-muted)', marginTop: 8 }}>{t('company.noOrg')}</p></div>;

  const update = (field, value) => setOrg(prev => ({ ...prev, [field]: value }));
  const orgStatus = org.status || (org.is_active === false ? 'inactive' : 'active');
  const statusLabel = {
    active: t('common.active'),
    inactive: t('common.inactive'),
    suspended: t('organizations.statusSuspended'),
    pending_approval: t('organizations.statusPendingApproval'),
    rejected: t('organizations.statusRejected'),
  }[orgStatus] || orgStatus || '-';
  const statusVariant = {
    active: 'success',
    inactive: 'error',
    suspended: 'warning',
    pending_approval: 'info',
    rejected: 'error',
  }[orgStatus] || 'neutral';

  return (
    <div style={{ padding: '44px 32px 28px', maxWidth: 1200 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('company.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>{t('company.subtitle')}</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
        <StatCard icon="database" label={t('company.organization')} value={org.name || '-'} />
        <StatCard icon="users" label={t('company.employees')} value={org.employees || '-'} />
        <StatCard icon="globe" label={t('company.sector')} value={org.sector || '-'} />
        <StatCard icon="shieldCheck" label={t('company.subscription')} value={org.subscription_type || '-'} />
      </div>

      <DCard title={t('company.info')}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {[
            { label: t('company.name'), field: 'name', type: 'text' },
            { label: t('company.sector'), field: 'sector', type: 'text' },
            { label: t('company.size'), field: 'size', type: 'select', options: ['micro', 'small', 'medium', 'large'] },
            { label: t('company.employees'), field: 'employees', type: 'number' },
            { label: t('company.jurisdiction'), field: 'jurisdiction', type: 'text' },
          ].map(f => (
            <div key={f.field}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: 5 }}>{f.label}</label>
              {f.type === 'select' ? (
                <select value={org[f.field] || ''} onChange={e => update(f.field, e.target.value)} style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'var(--surface)', outline: 'none' }}>
                  {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                </select>
              ) : (
                <input type={f.type} value={org[f.field] || ''} onChange={e => update(f.field, f.type === 'number' ? parseInt(e.target.value) || 0 : e.target.value)} style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, outline: 'none' }} />
              )}
            </div>
          ))}
        </div>
        <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
          <button onClick={saveOrg} disabled={saving} style={{ padding: '10px 24px', borderRadius: 8, background: 'var(--navy)', color: '#fff', fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer' }}>
            {saving ? t('common.saving') : t('common.save')}
          </button>
          <Badge variant={statusVariant}>{statusLabel}</Badge>
        </div>
      </DCard>
    </div>
  );
}
