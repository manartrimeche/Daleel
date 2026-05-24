import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import DIcon from '../../components/DIcon';
import { DCard, EmptyState } from '../../components/UI';
import { authFetch, getUser } from '../../utils/auth';

export default function Notifications() {
  const { t, i18n } = useTranslation();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const currentUser = getUser();
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  async function loadNotifications() {
    try {
      const endpoint = currentUser?.role === 'super_admin'
        ? '/api/v1/admin/notifications?limit=50'
        : '/api/v1/notifications/mine?limit=50';
      const res = await authFetch(endpoint);
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || (Array.isArray(data) ? data : []));
      }
    } catch {
      // Notification list failures are represented by the empty state.
    }
    setLoading(false);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { void Promise.resolve().then(loadNotifications); }, []);

  const markRead = async (id) => {
    try {
      await authFetch(`/api/v1/notifications/${id}/read`, { method: 'POST' });
      setNotifications(prev => prev.map(n => (n.id || n._id) === id ? { ...n, read: true } : n));
    } catch {
      // Mark-as-read failures leave the item unread.
    }
  };

  const typeIcon = (t) => ({ amendment_impact: 'layers', approval_organization: 'globe', approval_invitation: 'mail' }[t] || 'bell');
  const unread = notifications.filter(n => !n.read);
  const read = notifications.filter(n => n.read);
  const visibleNotifications = filter === 'unread' ? unread : filter === 'read' ? read : notifications;
  const listTitle = filter === 'unread'
    ? t('notifications.unreadTitle', { count: unread.length })
    : filter === 'read'
      ? t('notifications.readTitle')
      : t('notifications.allCount', { count: notifications.length });
  const filters = [
    { key: 'all', label: t('notifications.all'), count: notifications.length },
    { key: 'unread', label: t('notifications.unreadLabel'), count: unread.length },
    { key: 'read', label: t('notifications.readLabel'), count: read.length },
  ];

  return (
    <div style={{ padding: '28px 32px', maxWidth: 900 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('notifications.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 18 }}>{t('notifications.unread', { count: unread.length })}</p>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>{t('common.loading')}</div>
      ) : notifications.length === 0 ? (
        <DCard><EmptyState icon="bell" title={t('notifications.noNotifications')} desc={t('notifications.noNotificationsDesc')} /></DCard>
      ) : (
        <>
          <div style={{ display: 'inline-flex', gap: 4, padding: 4, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', marginBottom: 20 }}>
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

          {visibleNotifications.length === 0 ? (
            <DCard><EmptyState icon="bell" title={t('notifications.noNotifications')} desc={t('notifications.noNotificationsDesc')} /></DCard>
          ) : (
            <DCard title={listTitle}>
              {visibleNotifications.map(n => {
                const isUnread = !n.read;
                return (
                <div key={n.id || n._id} style={{
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
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{new Date(n.created_at).toLocaleDateString(locale, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
                  </div>
                  {isUnread && (
                    <button onClick={() => markRead(n.id || n._id)} style={{ padding: '4px 10px', borderRadius: 6, background: 'var(--surface-active)', color: 'var(--text-secondary)', fontSize: 11, border: 'none', cursor: 'pointer', whiteSpace: 'nowrap' }}>{t('notifications.markRead')}</button>
                  )}
                </div>
                );
              })}
            </DCard>
          )}
        </>
      )}
    </div>
  );
}
