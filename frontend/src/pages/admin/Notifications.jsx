import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import DIcon from '../../components/DIcon';
import { DCard, DButton, EmptyState, Skeleton, useConfirm, useToast } from '../../components/UI';
import { authFetch, getUser } from '../../utils/auth';

const PAGE_SIZE = 25;

// Notify the NotificationBell (in App.jsx) to refresh its unread count.
// ``delta`` is an optimistic adjustment applied immediately; a real fetch
// follows to reconcile.
function emitUnreadRefresh(delta = 0) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent('notifications:refresh', { detail: { delta } }));
}

const TYPE_ICONS = {
  amendment_impact: 'layers',
  amendment_summary: 'layers',
  approval_organization: 'globe',
  approval_invitation: 'mail',
  approval_document: 'fileText',
  approval_amendment: 'fileText',
  subscription_expiring: 'alertTriangle',
  account_login: 'logout',
  account_updated: 'edit',
  account_deactivated: 'lock',
  member_joined: 'users',
  invitation_revoked: 'x',
  organization_approved: 'check',
  organization_rejected: 'x',
};

const ROLE_NOTIFICATION_TYPES = {
  super_admin: new Set([
    'approval_organization',
    'approval_invitation',
    'approval_document',
    'approval_amendment',
    'amendment_summary',
  ]),
  owner: new Set([
    'amendment_impact',
    'subscription_expiring',
    'account_login',
    'account_updated',
    'account_deactivated',
    'member_joined',
    'invitation_revoked',
    'organization_approved',
    'organization_rejected',
  ]),
};

export default function Notifications() {
  const { t, i18n } = useTranslation();
  const toast = useToast();
  const confirm = useConfirm();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [filter, setFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [hasMore, setHasMore] = useState(false);
  const [totalUnread, setTotalUnread] = useState(0);
  const [processingId, setProcessingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const currentUser = getUser();
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';
  const canDeleteNotifications = ['owner', 'super_admin'].includes(currentUser?.role);

  const endpointBase = currentUser?.role === 'super_admin'
    ? '/api/v1/admin/notifications'
    : '/api/v1/notifications/mine';
  const allowedTypes = ROLE_NOTIFICATION_TYPES[currentUser?.role] || null;

  async function fetchPage(skip) {
    const res = await authFetch(`${endpointBase}?skip=${skip}&limit=${PAGE_SIZE}`);
    if (!res.ok) return { items: [], total: 0 };
    const data = await res.json();
    const rawItems = data.notifications || (Array.isArray(data) ? data : []);
    const items = allowedTypes
      ? rawItems.filter(n => allowedTypes.has(n.alert_type))
      : rawItems;
    return { items, total: data.total ?? items.length };
  }

  async function fetchUnreadCount() {
    try {
      const res = await authFetch('/api/v1/notifications/unread-count');
      if (res.ok) {
        const data = await res.json();
        setTotalUnread(data.unread || 0);
      }
    } catch { /* non-blocking */ }
  }

  async function loadNotifications() {
    try {
      const [page] = await Promise.all([fetchPage(0), fetchUnreadCount()]);
      setNotifications(page.items);
      setHasMore(page.items.length < page.total);
    } catch {
      // Notification list failures are represented by the empty state.
    }
    setLoading(false);
  }

  async function loadMore() {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const { items, total } = await fetchPage(notifications.length);
      setNotifications(prev => [...prev, ...items]);
      setHasMore(notifications.length + items.length < total);
    } catch {
      // ignore — keep current list
    }
    setLoadingMore(false);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { void Promise.resolve().then(loadNotifications); }, []);

  const [markingAll, setMarkingAll] = useState(false);

  const markRead = async (id) => {
    try {
      const res = await authFetch(`/api/v1/notifications/${id}/read`, { method: 'POST' });
      if (res && res.ok) {
        setNotifications(prev => prev.map(n => (n.id || n._id) === id ? { ...n, read: true } : n));
        setTotalUnread(prev => Math.max(0, prev - 1));
        emitUnreadRefresh(-1);
      }
    } catch {
      // Mark-as-read failures leave the item unread.
    }
  };

  const markAllRead = async () => {
    if (markingAll || totalUnread === 0) return;
    setMarkingAll(true);
    let bulkOk;
    try {
      const res = await authFetch('/api/v1/notifications/read-all', { method: 'POST' });
      bulkOk = res.ok;
    } catch {
      bulkOk = false;
    }
    if (!bulkOk) {
      const unreadIds = notifications.filter(n => !n.read).map(n => n.id || n._id).filter(Boolean);
      if (unreadIds.length > 0) {
        const results = await Promise.allSettled(
          unreadIds.map(id => authFetch(`/api/v1/notifications/${id}/read`, { method: 'POST' }))
        );
        bulkOk = results.some(r => r.status === 'fulfilled' && r.value && r.value.ok);
      }
    }
    if (bulkOk) {
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setTotalUnread(0);
      emitUnreadRefresh(-totalUnread);
    }
    setMarkingAll(false);
  };

  const processApproval = async (notification, decision) => {
    const id = notification.id || notification._id;
    if (!id || processingId) return;
    setProcessingId(id);
    try {
      const res = await authFetch(`/api/v1/admin/notifications/${id}/${decision}`, { method: 'POST' });
      if (!res.ok) throw new Error('approval_failed');
      const wasUnread = !notification.read;
      setNotifications(prev => prev.map(n => (n.id || n._id) === id ? {
        ...n,
        read: true,
        details: {
          ...(n.details || {}),
          approval_status: decision === 'approve' ? 'approved' : 'rejected',
        },
      } : n));
      if (wasUnread) {
        setTotalUnread(prev => Math.max(0, prev - 1));
        emitUnreadRefresh(-1);
      }
      toast.success(
        decision === 'approve'
          ? t('notifications.approved', { defaultValue: 'Approuvé' })
          : t('notifications.rejected', { defaultValue: 'Refusé' })
      );
    } catch {
      toast.error(t('notifications.actionFailed', { defaultValue: "L'action n'a pas pu être effectuée." }));
    }
    setProcessingId(null);
  };

  const deleteNotification = async (notification) => {
    const id = notification.id || notification._id;
    if (!id || deletingId) return;
    const ok = await confirm(t('notifications.deleteConfirm'), {
      variant: 'danger',
      confirmLabel: t('common.delete'),
    });
    if (!ok) return;

    setDeletingId(id);
    try {
      const res = await authFetch(`/api/v1/notifications/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('delete_failed');
      const wasUnread = !notification.read;
      setNotifications(prev => prev.filter(n => (n.id || n._id) !== id));
      if (wasUnread) {
        setTotalUnread(prev => Math.max(0, prev - 1));
        emitUnreadRefresh(-1);
      }
      toast.success(t('notifications.deleted'));
    } catch {
      toast.error(t('notifications.deleteFailed'));
    }
    setDeletingId(null);
  };

  const typeIcon = (type) => TYPE_ICONS[type] || 'bell';

  const availableTypes = useMemo(() => {
    const seen = new Set();
    notifications.forEach(n => { if (n.alert_type) seen.add(n.alert_type); });
    return Array.from(seen).sort();
  }, [notifications]);

  const baseFiltered = typeFilter === 'all'
    ? notifications
    : notifications.filter(n => n.alert_type === typeFilter);
  const unread = baseFiltered.filter(n => !n.read);
  const read = baseFiltered.filter(n => n.read);
  const visibleNotifications = filter === 'unread' ? unread : filter === 'read' ? read : baseFiltered;
  const listTitle = filter === 'unread'
    ? t('notifications.unreadTitle', { count: unread.length })
    : filter === 'read'
      ? t('notifications.readTitle')
      : t('notifications.allCount', { count: baseFiltered.length });
  const filters = [
    { key: 'all', label: t('notifications.all'), count: baseFiltered.length },
    { key: 'unread', label: t('notifications.unreadLabel'), count: unread.length },
    { key: 'read', label: t('notifications.readLabel'), count: read.length },
  ];

  return (
    <div style={{ padding: '44px 32px 28px', maxWidth: 900 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('notifications.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 18 }}>{t('notifications.unread', { count: totalUnread })}</p>

      {loading ? (
        <Skeleton height={56} count={4} />
      ) : notifications.length === 0 ? (
        <DCard><EmptyState icon="bell" title={t('notifications.noNotifications')} desc={t('notifications.noNotificationsDesc')} /></DCard>
      ) : (
        <>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center', marginBottom: 20 }}>
            <div style={{ display: 'inline-flex', gap: 4, padding: 4, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)' }}>
              {filters.map(f => (
                <button
                  key={f.key}
                  type="button"
                  onClick={() => setFilter(f.key)}
                  style={{
                    border: 'none',
                    borderRadius: 6,
                    background: filter === f.key ? 'var(--navy)' : 'transparent',
                    color: filter === f.key ? '#fff' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: 12,
                    fontWeight: 600,
                    padding: '7px 11px',
                    minWidth: 86,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {f.label} ({f.count})
                </button>
              ))}
            </div>
            {availableTypes.length > 1 && (
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                aria-label={t('notifications.typeFilter')}
                style={{
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  background: 'var(--surface)',
                  color: 'var(--text)',
                  fontSize: 12,
                  fontWeight: 600,
                  padding: '8px 11px',
                  cursor: 'pointer',
                }}
              >
                <option value="all">{t('notifications.allTypes')}</option>
                {availableTypes.map(type => (
                  <option key={type} value={type}>{t(`notifications.type_${type}`, { defaultValue: type })}</option>
                ))}
              </select>
            )}
          </div>

          {visibleNotifications.length === 0 ? (
            <DCard><EmptyState icon="bell" title={t('notifications.noNotifications')} desc={t('notifications.noNotificationsDesc')} /></DCard>
          ) : (
            <DCard
              title={listTitle}
              action={filter !== 'read' && totalUnread > 0 ? (
                <DButton
                  variant="ghost"
                  size="sm"
                  onClick={markAllRead}
                  disabled={markingAll}
                >
                  {markingAll ? t('common.loading') : t('notifications.markAllRead')}
                </DButton>
              ) : null}
            >
              {visibleNotifications.map(n => {
                const isUnread = !n.read;
                const isApproval = currentUser?.role === 'super_admin' && (n.alert_type || '').startsWith('approval_');
                const isPendingApproval = isApproval && isUnread && (n.details?.approval_status || 'pending_approval') === 'pending_approval';
                const currentId = n.id || n._id;
                return (
                <div key={currentId} style={{
                  display: 'flex',
                  gap: 12,
                  padding: '12px 10px',
                  borderBottom: '1px solid var(--border-subtle)',
                  alignItems: 'flex-start',
                  background: isUnread ? 'var(--gold-bg)' : 'transparent',
                  borderRadius: 8,
                  marginBottom: 4,
                  opacity: isUnread ? 1 : 0.68,
                }}>
                  <div style={{
                    width: 34,
                    height: 34,
                    borderRadius: 8,
                    background: isUnread ? 'rgba(184,134,11,0.16)' : 'var(--surface-hover)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: isUnread ? 'var(--gold)' : 'var(--text-muted)',
                    flexShrink: 0,
                  }}>
                    <DIcon name={typeIcon(n.alert_type)} size={16} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: isUnread ? 700 : 500, marginBottom: 2 }}>{n.title}</div>
                    <div style={{ fontSize: 12, color: isUnread ? 'var(--text-secondary)' : 'var(--text-muted)', lineHeight: 1.5, whiteSpace: 'pre-line' }}>{n.message}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{new Date(n.created_at).toLocaleString(locale, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
                    {isPendingApproval && (
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                        <DButton
                          size="sm"
                          icon="check"
                          disabled={processingId === currentId}
                          onClick={() => processApproval(n, 'approve')}
                        >
                          {t('notifications.approve', { defaultValue: 'Approuver' })}
                        </DButton>
                        <DButton
                          variant="danger"
                          size="sm"
                          icon="x"
                          disabled={processingId === currentId}
                          onClick={() => processApproval(n, 'reject')}
                        >
                          {t('notifications.reject', { defaultValue: 'Refuser' })}
                        </DButton>
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexShrink: 0, alignItems: 'center' }}>
                    {isUnread && !isPendingApproval && (
                      <DButton variant="ghost" size="sm" onClick={() => markRead(currentId)}>{t('notifications.markRead')}</DButton>
                    )}
                    {canDeleteNotifications && (
                      <DButton
                        variant="danger"
                        size="sm"
                        icon="trash"
                        title={t('common.delete')}
                        aria-label={t('common.delete')}
                        disabled={deletingId === currentId || processingId === currentId}
                        onClick={() => deleteNotification(n)}
                        style={{ width: 34, height: 30, padding: 0, justifyContent: 'center' }}
                      >
                      </DButton>
                    )}
                  </div>
                </div>
                );
              })}
              {hasMore && (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '14px 0 4px' }}>
                  <DButton variant="ghost" size="sm" onClick={loadMore} disabled={loadingMore}>
                    {loadingMore ? t('common.loading') : t('notifications.loadMore')}
                  </DButton>
                </div>
              )}
            </DCard>
          )}
        </>
      )}
    </div>
  );
}
