import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, DCard, EmptyState } from '../../components/UI';
import { authFetch } from '../../utils/auth';

export default function Organizations() {
  const { t, i18n } = useTranslation();
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [renewTypes, setRenewTypes] = useState({});
  const [renewing, setRenewing] = useState({});
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  useEffect(() => {
    (async () => {
      try {
        const res = await authFetch('/api/v1/auth/organizations?limit=100');
        if (res.ok) {
          const data = await res.json();
          setOrgs(Array.isArray(data) ? data : data.organizations || []);
        }
      } catch {
        // Organization listing failures are represented by the empty state.
      }
      setLoading(false);
    })();
  }, []);

  const renewOrganization = async (org) => {
    const id = org.id || org._id;
    const subscriptionType = renewTypes[id] || org.subscription_type || 'monthly';
    setRenewing(prev => ({ ...prev, [id]: true }));
    try {
      const res = await authFetch(`/api/v1/auth/organizations/${id}/renew`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subscription_type: subscriptionType }),
      });
      if (res.ok) {
        const updated = await res.json();
        setOrgs(prev => prev.map(o => (o.id || o._id) === id ? updated : o));
      }
    } catch {
      // Renewal failures leave the organization unchanged.
    }
    setRenewing(prev => ({ ...prev, [id]: false }));
  };

  return (
    <div style={{ padding: '28px 32px', maxWidth: 1200 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('organizations.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>{t('organizations.count', { count: orgs.length })}</p>

      <DCard noPad>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>{t('common.loading')}</div>
        ) : orgs.length === 0 ? (
          <EmptyState icon="globe" title={t('organizations.noOrgs')} />
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['name', 'sector', 'size', 'members', 'subscription', 'status', 'created', 'expires', 'renewal'].map(h => (
                  <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t(`organizations.cols.${h}`)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {orgs.map(o => {
                const id = o.id || o._id;
                const inactive = o.status === 'inactive';
                const statusLabel = o.status === 'active'
                  ? t('common.active')
                  : o.status === 'inactive'
                    ? t('common.inactive')
                    : (o.status || '-');
                return (
                  <tr key={id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600 }}>{o.name}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{o.sector || '-'}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{o.size || '-'}</td>
                    <td style={{ padding: '12px 16px' }}>{o.member_count || 0}</td>
                    <td style={{ padding: '12px 16px' }}><Badge variant="gold">{o.subscription_type || '-'}</Badge></td>
                    <td style={{ padding: '12px 16px' }}><Badge variant={o.status === 'active' ? 'success' : 'error'}>{statusLabel}</Badge></td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 12 }}>{o.created_at ? new Date(o.created_at).toLocaleDateString(locale) : '-'}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 12 }}>{o.subscription_ends_at ? new Date(o.subscription_ends_at).toLocaleDateString(locale) : '-'}</td>
                    <td style={{ padding: '12px 16px' }}>
                      {inactive ? (
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', minWidth: 210 }}>
                          <select
                            value={renewTypes[id] || o.subscription_type || 'monthly'}
                            onChange={e => setRenewTypes(prev => ({ ...prev, [id]: e.target.value }))}
                            style={{ padding: '7px 9px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-secondary)' }}
                          >
                            <option value="monthly">{t('organizations.monthly')}</option>
                            <option value="annual">{t('organizations.annual')}</option>
                          </select>
                          <button
                            type="button"
                            onClick={() => renewOrganization(o)}
                            disabled={!!renewing[id]}
                            style={{ padding: '7px 11px', borderRadius: 6, border: 'none', background: 'var(--navy)', color: '#fff', fontSize: 12, fontWeight: 700, cursor: renewing[id] ? 'default' : 'pointer', opacity: renewing[id] ? 0.65 : 1, whiteSpace: 'nowrap' }}
                          >
                            {renewing[id] ? t('common.saving') : t('organizations.renew')}
                          </button>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>-</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </DCard>
    </div>
  );
}
