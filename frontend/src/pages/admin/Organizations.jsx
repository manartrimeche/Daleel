import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, DCard, DButton, EmptyState, SkeletonRow } from '../../components/UI';
import { authFetch } from '../../utils/auth';

export default function Organizations() {
  const { t, i18n } = useTranslation();
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [renewTypes, setRenewTypes] = useState({});
  const [renewing, setRenewing] = useState({});
  const [statusChanging, setStatusChanging] = useState({});
  const [acting, setActing] = useState({});
  const [rejectFor, setRejectFor] = useState(null); // org en cours de refus (modal motif)
  const [rejectReason, setRejectReason] = useState('');
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  const reload = async () => {
    try {
      const res = await authFetch('/api/v1/auth/organizations?limit=100');
      if (res.ok) {
        const data = await res.json();
        setOrgs(Array.isArray(data) ? data : data.organizations || []);
      }
    } catch {
      // Organization listing failures are represented by the empty state.
    }
  };

  useEffect(() => {
    (async () => { await reload(); setLoading(false); })();
  }, []);

  const approveOrg = async (org) => {
    const id = org.id || org._id;
    setActing(p => ({ ...p, [id]: 'approve' }));
    try {
      const res = await authFetch(`/api/v1/auth/organizations/${id}/approve`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setOrgs(prev => prev.map(o => (o.id || o._id) === id ? updated : o));
      } else {
        const data = await res.json().catch(() => ({}));
        alert(data.detail || t('organizations.approveError'));
      }
    } finally {
      setActing(p => ({ ...p, [id]: null }));
    }
  };

  const submitReject = async () => {
    if (!rejectFor) return;
    const id = rejectFor.id || rejectFor._id;
    if (rejectReason.trim().length < 3) return;
    setActing(p => ({ ...p, [id]: 'reject' }));
    try {
      const res = await authFetch(`/api/v1/auth/organizations/${id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: rejectReason.trim() }),
      });
      if (res.ok) {
        const updated = await res.json();
        setOrgs(prev => prev.map(o => (o.id || o._id) === id ? updated : o));
        setRejectFor(null);
        setRejectReason('');
      } else {
        const data = await res.json().catch(() => ({}));
        alert(data.detail || t('organizations.rejectError'));
      }
    } finally {
      setActing(p => ({ ...p, [id]: null }));
    }
  };

  const pending = orgs.filter(o => o.status === 'pending_approval');
  const manualStatuses = ['active', 'inactive', 'suspended'];
  const statusLabel = (status) => ({
    active: t('common.active'),
    inactive: t('common.inactive'),
    suspended: t('organizations.statusSuspended'),
    pending_approval: t('organizations.statusPendingApproval'),
    rejected: t('organizations.statusRejected'),
  }[status] || status || '-');
  const statusVariant = (status) => ({
    active: 'success',
    inactive: 'error',
    suspended: 'warning',
    pending_approval: 'info',
    rejected: 'error',
  }[status] || 'neutral');

  const updateOrganizationStatus = async (org, status) => {
    const id = org.id || org._id;
    if (!id || status === org.status) return;
    setStatusChanging(prev => ({ ...prev, [id]: true }));
    try {
      const res = await authFetch(`/api/v1/auth/organizations/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        const updated = await res.json();
        setOrgs(prev => prev.map(o => (o.id || o._id) === id ? updated : o));
      } else {
        const data = await res.json().catch(() => ({}));
        alert(data.detail || t('organizations.statusUpdateError'));
      }
    } finally {
      setStatusChanging(prev => ({ ...prev, [id]: false }));
    }
  };

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
    <div style={{ padding: '44px 32px 28px', maxWidth: 1200 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('organizations.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>{t('organizations.count', { count: orgs.length })}</p>

      {pending.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>{t('organizations.pendingTitle', { count: pending.length })}</h2>
          <DCard noPad>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['name', 'country', 'sector', 'contact', 'verified', 'needs', 'actions'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t(`organizations.pendingCols.${h}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pending.map(o => {
                  const id = o.id || o._id;
                  const isActing = !!acting[id];
                  const canApprove = o.contact_email_verified && o.contact_phone_verified;
                  return (
                    <tr key={id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '12px 16px', fontWeight: 600 }}>{o.name}</td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{o.country || o.jurisdiction || '-'}</td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{o.sector || '-'}</td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: 12 }}>
                        <div>{o.requested_by_email || '-'}</div>
                        <div>{o.requested_by_phone || '-'}</div>
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: 12 }}>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <Badge variant={o.contact_email_verified ? 'success' : 'error'}>{o.contact_email_verified ? t('organizations.emailOk') : t('organizations.emailKo')}</Badge>
                          <Badge variant={o.contact_phone_verified ? 'success' : 'error'}>{o.contact_phone_verified ? t('organizations.phoneOk') : t('organizations.phoneKo')}</Badge>
                        </div>
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: 12 }}>{(o.needs || []).join(', ') || '-'}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <DButton size="sm" onClick={() => approveOrg(o)} disabled={isActing || !canApprove} title={canApprove ? '' : t('organizations.approveBlocked')}>
                            {isActing && acting[id] === 'approve' ? t('common.saving') : t('organizations.approve')}
                          </DButton>
                          <DButton size="sm" variant="danger" onClick={() => { setRejectFor(o); setRejectReason(''); }} disabled={isActing}>
                            {t('organizations.reject')}
                          </DButton>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </DCard>
        </div>
      )}

      {rejectFor && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'var(--bg)', padding: 24, borderRadius: 12, maxWidth: 480, width: '90%' }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>{t('organizations.rejectTitle', { name: rejectFor.name })}</h3>
            <textarea
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              placeholder={t('organizations.rejectPlaceholder')}
              rows={4}
              style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)', fontSize: 13, marginBottom: 12, resize: 'vertical' }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <DButton size="sm" variant="secondary" onClick={() => { setRejectFor(null); setRejectReason(''); }}>{t('common.cancel')}</DButton>
              <DButton size="sm" variant="danger" onClick={submitReject} disabled={rejectReason.trim().length < 3 || acting[rejectFor.id || rejectFor._id] === 'reject'}>
                {acting[rejectFor.id || rejectFor._id] === 'reject' ? t('common.saving') : t('organizations.rejectConfirm')}
              </DButton>
            </div>
          </div>
        </div>
      )}

      <DCard noPad>
        {loading ? (
          <div style={{ padding: 16 }}><SkeletonRow cols={7} /><SkeletonRow cols={7} /><SkeletonRow cols={7} /></div>
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
                const canManuallyChangeStatus = manualStatuses.includes(o.status);
                return (
                  <tr key={id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600 }}>{o.name}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{o.sector || '-'}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{o.size || '-'}</td>
                    <td style={{ padding: '12px 16px' }}>{o.member_count || 0}</td>
                    <td style={{ padding: '12px 16px' }}><Badge variant="gold">{o.subscription_type || '-'}</Badge></td>
                    <td style={{ padding: '12px 16px' }}>
                      {canManuallyChangeStatus ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 150 }}>
                          <select
                            value={o.status}
                            onChange={e => updateOrganizationStatus(o, e.target.value)}
                            disabled={!!statusChanging[id]}
                            aria-label={t('organizations.manualStatus')}
                            title={t('organizations.manualStatus')}
                            style={{ padding: '7px 9px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-secondary)', minWidth: 118 }}
                          >
                            {manualStatuses.map(status => (
                              <option key={status} value={status}>{statusLabel(status)}</option>
                            ))}
                          </select>
                          {statusChanging[id] && <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{t('common.saving')}</span>}
                        </div>
                      ) : (
                        <Badge variant={statusVariant(o.status)}>{statusLabel(o.status)}</Badge>
                      )}
                    </td>
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
                          <DButton size="sm" onClick={() => renewOrganization(o)} disabled={!!renewing[id]}>
                            {renewing[id] ? t('common.saving') : t('organizations.renew')}
                          </DButton>
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
