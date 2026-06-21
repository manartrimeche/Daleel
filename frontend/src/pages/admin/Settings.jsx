import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import DIcon from '../../components/DIcon';
import { DCard, DButton, Badge, EmptyState, Skeleton } from '../../components/UI';
import { authFetch, getUser } from '../../utils/auth';

export default function Settings() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const user = getUser();
  const [archives, setArchives] = useState([]);
  const [loadingArchives, setLoadingArchives] = useState(true);
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  const loadArchives = async () => {
    setLoadingArchives(true);
    try {
      const res = await authFetch('/api/v1/chat-history?archived=true&limit=50');
      if (res.ok) {
        const data = await res.json();
        setArchives(data.entries || []);
      }
    } catch {
      // Archives are optional settings content.
    }
    setLoadingArchives(false);
  };

  useEffect(() => { void Promise.resolve().then(loadArchives); }, []);

  const archiveTitle = (entry) => entry.conversation_title || entry.title || entry.question || t('chat.untitledConversation');

  const openArchive = (entry) => {
    if (!entry.conversation_id) return;
    navigate(`/chat?conversation=${encodeURIComponent(entry.conversation_id)}`);
  };

  const restoreArchive = async (entry) => {
    if (!entry.conversation_id) return;
    const res = await authFetch(`/api/v1/chat-history/conversation/${encodeURIComponent(entry.conversation_id)}/archive`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ archived: false }),
    });
    if (res.ok) loadArchives();
  };

  return (
    <div style={{ padding: '44px 32px 28px', maxWidth: 900 }}>
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
          <DButton variant="ghost" size="sm">{t('common.edit')}</DButton>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>{t('settings.twoFactor')}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('settings.twoFactorDesc')}</div>
          </div>
          <Badge variant="neutral">{t('settings.notEnabled')}</Badge>
        </div>
      </DCard>

      <DCard title={t('settings.archivedConversations')} style={{ marginBottom: 20 }}>
        {loadingArchives ? (
          <Skeleton height={52} count={3} />
        ) : archives.length === 0 ? (
          <EmptyState icon="archive" title={t('settings.noArchivedConversations')} desc={t('settings.noArchivedConversationsDesc')} />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {archives.map((entry, i) => (
              <div key={entry.conversation_id || i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '11px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface)' }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--surface-active)', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <DIcon name="archive" size={16} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{archiveTitle(entry)}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                    {entry.created_at ? new Date(entry.created_at).toLocaleDateString(locale, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'}
                    {entry.message_count > 1 ? ` · ${entry.message_count} ${t('settings.messages')}` : ''}
                  </div>
                </div>
                <DButton size="sm" icon="messageCircle" onClick={() => openArchive(entry)}>
                  {t('settings.open')}
                </DButton>
                <DButton variant="ghost" size="sm" onClick={() => restoreArchive(entry)}>
                  {t('settings.restore')}
                </DButton>
              </div>
            ))}
          </div>
        )}
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
