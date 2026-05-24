import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import DIcon from '../../components/DIcon';
import { Badge, DCard, Avatar, EmptyState } from '../../components/UI';
import { authFetch, getUser } from '../../utils/auth';

export default function Users() {
  const { t, i18n } = useTranslation();
  const [users, setUsers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [sending, setSending] = useState(false);
  const currentUser = getUser();
  const orgId = currentUser?.organization_id;
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  async function loadData() {
    setLoading(true);
    try {
      const [usersRes, invRes] = await Promise.allSettled([
        orgId ? authFetch(`/api/v1/auth/organizations/${orgId}/users?limit=100`).then(r => r.json()) : Promise.resolve([]),
        authFetch('/api/v1/auth/invitations').then(r => r.json()),
      ]);
      setUsers(usersRes.status === 'fulfilled' ? (Array.isArray(usersRes.value) ? usersRes.value : usersRes.value.users || []) : []);
      setInvitations(invRes.status === 'fulfilled' ? (Array.isArray(invRes.value) ? invRes.value : invRes.value.invitations || []) : []);
    } catch {
      // User and invitation lists fall back to the current empty state.
    }
    setLoading(false);
  }

  const sendInvite = async () => {
    if (!inviteEmail.trim()) return;
    setSending(true);
    try {
      const res = await authFetch('/api/v1/auth/invitations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: inviteEmail }),
      });
      if (res.ok) { setInviteEmail(''); setShowInvite(false); loadData(); }
    } catch {
      // Invitation failures leave the form open for retry.
    }
    setSending(false);
  };

  const roleVariant = (r) => ({ super_admin: 'error', owner: 'gold', admin: 'info', member: 'neutral', viewer: 'neutral' }[r] || 'neutral');

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { void Promise.resolve().then(loadData); }, []);

  return (
    <div style={{ padding: '28px 32px', maxWidth: 1200 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('users_page.title')}</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{t('users_page.members', { count: users.length })}</p>
        </div>
        <button onClick={() => setShowInvite(true)} style={{ padding: '10px 20px', borderRadius: 'var(--radius-md)', background: 'var(--navy)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, border: 'none' }}>
          <DIcon name="plus" size={16} /> {t('users_page.invite')}
        </button>
      </div>

      {showInvite && (
        <DCard style={{ marginBottom: 20 }} title={t('users_page.inviteMember')}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: 5 }}>{t('users_page.emailAddress')}</label>
              <input value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} placeholder="email@entreprise.tn" style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, outline: 'none' }} />
            </div>
            <button onClick={sendInvite} disabled={sending} style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--navy)', color: '#fff', fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer' }}>
              {sending ? t('common.sending') : t('common.send')}
            </button>
            <button onClick={() => setShowInvite(false)} style={{ padding: '10px 16px', borderRadius: 8, background: 'var(--surface-active)', color: 'var(--text-secondary)', fontSize: 13, border: 'none', cursor: 'pointer' }}>{t('common.cancel')}</button>
          </div>
        </DCard>
      )}

      <DCard title={t('users_page.membersTitle')} noPad>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>{t('common.loading')}</div>
        ) : users.length === 0 ? (
          <EmptyState icon="users" title={t('users_page.noMembers')} desc={t('users_page.noMembersDesc')} />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['member', 'email', 'role', 'status', 'lastLogin'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{t(`users_page.cols.${h}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id || u._id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <Avatar name={u.full_name || u.email || '?'} size={30} />
                        <span style={{ fontWeight: 500 }}>{u.full_name || '-'}</span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{u.email}</td>
                    <td style={{ padding: '12px 16px' }}><Badge variant={roleVariant(u.role)}>{u.role}</Badge></td>
                    <td style={{ padding: '12px 16px' }}><Badge variant={u.is_active ? 'success' : 'error'}>{u.is_active ? t('common.active') : t('common.inactive')}</Badge></td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 12 }}>{u.last_login ? new Date(u.last_login).toLocaleDateString(locale) : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DCard>

      {invitations.length > 0 && (
        <DCard title={t('users_page.pendingInvites')} noPad style={{ marginTop: 20 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['email', 'role', 'status', 'expiresAt'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{t(`users_page.cols.${h}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {invitations.map(inv => (
                  <tr key={inv.id || inv._id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 500 }}>{inv.email}</td>
                    <td style={{ padding: '12px 16px' }}><Badge variant="info">{inv.role || 'member'}</Badge></td>
                    <td style={{ padding: '12px 16px' }}><Badge variant="warning">{inv.status || 'pending'}</Badge></td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 12 }}>{inv.expires_at ? new Date(inv.expires_at).toLocaleDateString(locale) : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DCard>
      )}
    </div>
  );
}
