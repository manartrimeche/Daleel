import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import DIcon from '../components/DIcon';
import { StatCard, DCard, ProgressBar, Badge, ScoreRing } from '../components/UI';
import { authFetch, getUser } from '../utils/auth';

// ─── Helper: safe fetch with fallback ───
async function safeFetch(url) {
  try {
    const res = await authFetch(url);
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

// ─── Super Admin Dashboard ───
function SuperAdminDashboard({ t, locale, navigate }) {
  const [stats, setStats] = useState(null);
  const [orgs, setOrgs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [cases, setCases] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      safeFetch('/api/v1/admin/stats'),
      safeFetch('/api/v1/auth/organizations?limit=5'),
      safeFetch('/api/v1/admin/notifications?limit=5'),
      safeFetch('/api/v1/cases/summary'),
    ]).then(([s, o, n, c]) => {
      setStats(s);
      const orgData = Array.isArray(o) ? o : o?.organizations || o?.items || [];
      setOrgs(orgData);
      setNotifications(n?.notifications || []);
      setCases(c);
      setLoading(false);
    });
  }, []);

  const num = (v) => (typeof v === 'object' && v !== null) ? (v.total ?? 0) : (v ?? 0);
  const docCount = num(stats?.documents);
  const lawCount = num(stats?.lois);
  const orgCount = orgs.length || num(stats?.organizations);
  const userCount = orgs.reduce((sum, o) => sum + (o.member_count || 0), 0) || num(stats?.users);

  return (
    <>
      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        <StatCard icon="fileText" label={t('dashboard.docsIndexed')} value={loading ? '...' : docCount} />
        <StatCard icon="layers" label={t('dashboard.activeLaws')} value={loading ? '...' : lawCount} />
        <StatCard icon="globe" label={t('dashboard.organizations')} value={loading ? '...' : orgCount} />
        <StatCard icon="users" label={t('dashboard.totalUsers')} value={loading ? '...' : userCount} />
      </div>

      {/* Stats plateforme + Orgs récentes */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <DCard title={t('dashboard.platformStats')}>
          {loading ? <LoadingPlaceholder /> : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: t('dashboard.exigences'), value: num(stats?.exigences), icon: 'shieldCheck' },
                { label: t('dashboard.questionsAsked'), value: num(stats?.questions), icon: 'messageCircle' },
                { label: t('dashboard.openCases'), value: cases?.total_cases ?? num(stats?.cases), icon: 'target' },
                { label: t('dashboard.amendments'), value: num(stats?.amendments), icon: 'edit' },
              ].map((s, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--gold-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold)' }}>
                    <DIcon name={s.icon} size={16} />
                  </div>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'var(--font-heading)' }}>{s.value}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{s.label}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </DCard>

        <DCard title={t('dashboard.recentOrgs')} action={
          <button onClick={() => navigate('/admin/organizations')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : orgs.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {orgs.slice(0, 5).map((org, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 28, height: 28, borderRadius: 6, background: 'var(--navy)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 11, fontWeight: 600 }}>
                      {(org.name || '?')[0].toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{org.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{org.member_count || 0} {t('dashboard.orgMembers').toLowerCase()}</div>
                    </div>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {org.created_at ? new Date(org.created_at).toLocaleDateString(locale) : ''}
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noActivity')} />}
        </DCard>
      </div>

      {/* Notifications */}
      <DCard title={t('dashboard.notifications')} action={
        <button onClick={() => navigate('/admin/notifications')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
      }>
        {loading ? <LoadingPlaceholder /> : notifications.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {notifications.slice(0, 5).map((n, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 'var(--radius-md)', background: n.read ? 'transparent' : 'var(--gold-bg)', border: '1px solid var(--border-subtle)' }}>
                <DIcon name="bell" size={15} style={{ color: 'var(--gold)' }} />
                <div style={{ flex: 1, fontSize: 13 }}>{n.message || n.title || n.type}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{n.created_at ? new Date(n.created_at).toLocaleDateString(locale) : ''}</div>
              </div>
            ))}
          </div>
        ) : <EmptyText text={t('dashboard.noNotifications')} />}
      </DCard>
    </>
  );
}

// ─── Owner / Admin Dashboard ───
function AdminDashboard({ t, locale, navigate, user }) {
  const [stats, setStats] = useState(null);
  const [docs, setDocs] = useState([]);
  const [cases, setCases] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [compliance, setCompliance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const orgId = user?.organization_id;
    Promise.all([
      safeFetch('/api/v1/documents?limit=5'),
      safeFetch('/api/v1/cases/summary'),
      safeFetch('/api/v1/chat-history?limit=5'),
      safeFetch('/api/v1/notifications/mine?limit=5'),
      orgId ? safeFetch(`/api/v1/auth/organizations/${orgId}/users?limit=100`) : Promise.resolve(null),
      safeFetch('/api/v1/company-profiles?limit=1'),
    ]).then(async ([d, c, ch, n, u, profiles]) => {
      const docsData = Array.isArray(d) ? d : d?.documents || [];
      setDocs(docsData);
      setCases(c);
      setChatHistory(ch?.entries || (Array.isArray(ch) ? ch : []));
      setNotifications(n?.notifications || []);

      // Fetch compliance posture if company profile exists
      const profileList = Array.isArray(profiles) ? profiles : profiles?.profiles || [];
      if (profileList.length > 0) {
        const posture = await safeFetch(`/api/v1/compliance/posture/${profileList[0].id}`);
        setCompliance(posture);
      }

      setStats({
        documents: Array.isArray(d) ? d.length : d?.total || docsData.length,
        users: Array.isArray(u) ? u.length : u?.total || 0,
      });
      setLoading(false);
    });
  }, [user]);

  const caseStatus = cases?.by_status || {};
  const openCases = cases?.open_count || cases?.open || caseStatus.open || 0;
  const inProgressCases = cases?.in_progress_count || cases?.in_progress || caseStatus.in_progress || 0;
  const closedCases = cases?.closed_count || cases?.closed || caseStatus.closed || 0;
  const complianceScore = compliance?.overall_score || compliance?.score || 0;

  return (
    <>
      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 28 }}>
        <StatCard icon="fileText" label={t('dashboard.docsIndexed')} value={loading ? '...' : (typeof stats?.documents === 'object' ? stats.documents.total : stats?.documents) || 0} />
        <StatCard icon="messageCircle" label={t('dashboard.questionsAsked')} value={loading ? '...' : chatHistory.length} />
        <StatCard icon="users" label={t('dashboard.users')} value={loading ? '...' : (typeof stats?.users === 'object' ? stats.users.total : stats?.users) || 0} />
        <StatCard icon="target" label={t('dashboard.openCases')} value={loading ? '...' : openCases + inProgressCases} variant={openCases > 0 ? 'warning' : 'default'} />
        <StatCard icon="shieldCheck" label={t('dashboard.complianceScore')} value={loading ? '...' : complianceScore ? `${complianceScore}%` : '--'} variant={complianceScore >= 80 ? 'success' : complianceScore >= 50 ? 'warning' : 'error'} />
      </div>

      {/* Conformité + Dossiers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <DCard title={t('dashboard.compliance')} action={<Badge variant="gold">{complianceScore ? `${complianceScore}%` : t('dashboard.inProgress')}</Badge>}>
          {loading ? <LoadingPlaceholder /> : compliance ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 20 }}>
                <ScoreRing value={complianceScore} size={80} variant={complianceScore >= 80 ? 'success' : complianceScore >= 50 ? 'warning' : 'error'} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{t('dashboard.globalScore')}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{t('dashboard.globalScoreDesc')}</div>
                </div>
              </div>
              {compliance.coverage !== undefined && (
                <ProgressBar value={Math.round(compliance.coverage * 100) || compliance.coverage} label={t('dashboard.complianceCoverage')} variant="success" />
              )}
              {compliance.gaps_count !== undefined && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', fontSize: 13 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{t('dashboard.complianceGaps')}</span>
                  <span style={{ fontWeight: 600, color: 'var(--error)' }}>{compliance.gaps_count}</span>
                </div>
              )}
              {compliance.controls_count !== undefined && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', fontSize: 13 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{t('dashboard.complianceControls')}</span>
                  <span style={{ fontWeight: 600, color: 'var(--success)' }}>{compliance.controls_count}</span>
                </div>
              )}
            </>
          ) : (
            <EmptyText text={t('dashboard.noComplianceData')} />
          )}
        </DCard>

        <DCard title={t('dashboard.caseSummary')} action={
          <button onClick={() => navigate('/admin/cases')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : cases ? (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
                {[
                  { label: t('dashboard.caseOpen'), value: openCases, color: 'var(--warning)' },
                  { label: t('dashboard.caseInProgress'), value: inProgressCases, color: 'var(--info)' },
                  { label: t('dashboard.caseClosed'), value: closedCases, color: 'var(--success)' },
                ].map((c, i) => (
                  <div key={i} style={{ textAlign: 'center', padding: '14px 8px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-heading)', color: c.color }}>{c.value}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{c.label}</div>
                  </div>
                ))}
              </div>
              {cases.by_priority && (
                <>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>{t('dashboard.caseByPriority')}</div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {[
                      { label: t('dashboard.priorityHigh'), value: cases.by_priority.high || 0, variant: 'error' },
                      { label: t('dashboard.priorityMedium'), value: cases.by_priority.medium || 0, variant: 'warning' },
                      { label: t('dashboard.priorityLow'), value: cases.by_priority.low || 0, variant: 'info' },
                    ].map((p, i) => (
                      <Badge key={i} variant={p.variant}>{p.label}: {p.value}</Badge>
                    ))}
                  </div>
                </>
              )}
            </>
          ) : <EmptyText text={t('dashboard.noCases')} />}
        </DCard>
      </div>

      {/* Documents récents + Questions récentes */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <DCard title={t('dashboard.recentDocs')} action={
          <button onClick={() => navigate('/admin/documents')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : docs.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {docs.slice(0, 5).map((doc, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
                    <DIcon name="fileText" size={15} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                    <span style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.filename || doc.title || doc.name}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                    <Badge variant={['processed', 'ready'].includes(doc.status) ? 'success' : doc.status === 'error' ? 'error' : 'neutral'}>
                      {['processed', 'ready'].includes(doc.status) ? t('dashboard.statusProcessed') : doc.status === 'error' ? t('dashboard.statusError') : t('dashboard.statusPending')}
                    </Badge>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', minWidth: 65, textAlign: 'right' }}>
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString(locale) : ''}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noDocs')} />}
        </DCard>

        <DCard title={t('dashboard.recentQuestions')} action={
          <button onClick={() => navigate('/admin/history')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : chatHistory.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {chatHistory.slice(0, 5).map((entry, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 12px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <DIcon name="messageCircle" size={15} style={{ color: 'var(--info)', marginTop: 2, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.question}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {entry.user_name && <span>{entry.user_name} · </span>}
                      {entry.created_at ? new Date(entry.created_at).toLocaleDateString(locale) : ''}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noQuestions')} />}
        </DCard>
      </div>

      {/* Notifications + Actions rapides */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <DCard title={t('dashboard.notifications')} action={
          <button onClick={() => navigate('/admin/notifications')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : notifications.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {notifications.slice(0, 4).map((n, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 'var(--radius-md)', background: n.read ? 'transparent' : 'var(--gold-bg)', border: '1px solid var(--border-subtle)' }}>
                  <DIcon name="bell" size={15} style={{ color: 'var(--gold)' }} />
                  <div style={{ flex: 1, fontSize: 13 }}>{n.message || n.title || n.type}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{n.created_at ? new Date(n.created_at).toLocaleDateString(locale) : ''}</div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noNotifications')} />}
        </DCard>

        <DCard title={t('dashboard.quickActions')}>
          <div style={{ display: 'flex', gap: 12 }}>
            {[
              { icon: 'messageCircle', label: t('dashboard.askQuestion'), color: 'var(--gold)', path: '/chat' },
              { icon: 'upload', label: t('dashboard.importDoc'), color: 'var(--info)', path: '/admin/documents' },
              { icon: 'edit', label: t('dashboard.importAmendment'), color: 'var(--success)', path: '/admin/amendments' },
            ].map((action, i) => (
              <button key={i} onClick={() => navigate(action.path)} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s' }}
                onMouseEnter={e => e.currentTarget.style.borderColor = action.color}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
              >
                <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', background: `${action.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: action.color }}>
                  <DIcon name={action.icon} size={16} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{action.label}</span>
              </button>
            ))}
          </div>
        </DCard>
      </div>
    </>
  );
}

// ─── Member Dashboard ───
function MemberDashboard({ t, locale, navigate }) {
  const [cases, setCases] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      safeFetch('/api/v1/cases?limit=5'),
      safeFetch('/api/v1/chat-history?limit=5'),
      safeFetch('/api/v1/notifications/mine?limit=5'),
    ]).then(([c, ch, n]) => {
      setCases(c);
      setChatHistory(ch?.entries || (Array.isArray(ch) ? ch : []));
      setNotifications(n?.notifications || []);
      setLoading(false);
    });
  }, []);

  const caseList = Array.isArray(cases) ? cases : cases?.cases || [];

  return (
    <>
      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 28 }}>
        <StatCard icon="target" label={t('dashboard.myCases')} value={loading ? '...' : caseList.length} />
        <StatCard icon="messageCircle" label={t('dashboard.questionsAsked')} value={loading ? '...' : chatHistory.length} />
        <StatCard icon="bell" label={t('dashboard.activeAlerts')} value={loading ? '...' : notifications.filter(n => !n.read).length} variant={notifications.filter(n => !n.read).length > 0 ? 'warning' : 'default'} />
      </div>

      {/* Dossiers + Questions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <DCard title={t('dashboard.myCases')} action={
          <button onClick={() => navigate('/admin/cases')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : caseList.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {caseList.slice(0, 5).map((c, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
                    <DIcon name="target" size={15} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                    <span style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
                  </div>
                  <Badge variant={c.priority === 'high' ? 'error' : c.priority === 'medium' ? 'warning' : 'neutral'}>{c.status}</Badge>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noCases')} />}
        </DCard>

        <DCard title={t('dashboard.recentQuestions')} action={
          <button onClick={() => navigate('/chat')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : chatHistory.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {chatHistory.slice(0, 5).map((entry, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 12px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <DIcon name="messageCircle" size={15} style={{ color: 'var(--info)', marginTop: 2, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.question}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {entry.created_at ? new Date(entry.created_at).toLocaleDateString(locale) : ''}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noQuestions')} />}
        </DCard>
      </div>

      {/* Notifications + Actions rapides */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <DCard title={t('dashboard.notifications')}>
          {loading ? <LoadingPlaceholder /> : notifications.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {notifications.slice(0, 4).map((n, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 'var(--radius-md)', background: n.read ? 'transparent' : 'var(--gold-bg)', border: '1px solid var(--border-subtle)' }}>
                  <DIcon name="bell" size={15} style={{ color: 'var(--gold)' }} />
                  <div style={{ flex: 1, fontSize: 13 }}>{n.message || n.title || n.type}</div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noNotifications')} />}
        </DCard>

        <DCard title={t('dashboard.quickActions')}>
          <div style={{ display: 'flex', gap: 12 }}>
            {[
              { icon: 'messageCircle', label: t('dashboard.askQuestion'), color: 'var(--gold)', path: '/chat' },
              { icon: 'target', label: t('dashboard.newCase'), color: 'var(--info)', path: '/admin/cases' },
              { icon: 'bell', label: t('dashboard.notifications'), color: 'var(--success)', path: '/admin/notifications' },
            ].map((action, i) => (
              <button key={i} onClick={() => navigate(action.path)} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s' }}
                onMouseEnter={e => e.currentTarget.style.borderColor = action.color}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
              >
                <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', background: `${action.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: action.color }}>
                  <DIcon name={action.icon} size={16} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{action.label}</span>
              </button>
            ))}
          </div>
        </DCard>
      </div>
    </>
  );
}

// ─── Viewer Dashboard ───
function ViewerDashboard({ t, locale, navigate }) {
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    safeFetch('/api/v1/chat-history?limit=5').then((ch) => {
      setChatHistory(ch?.entries || (Array.isArray(ch) ? ch : []));
      setLoading(false);
    });
  }, []);

  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16, marginBottom: 28 }}>
        <StatCard icon="messageCircle" label={t('dashboard.questionsAsked')} value={loading ? '...' : chatHistory.length} />
        <StatCard icon="eye" label={t('settings.role')} value="viewer" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <DCard title={t('dashboard.recentQuestions')} action={
          <button onClick={() => navigate('/chat')} style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : chatHistory.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {chatHistory.slice(0, 5).map((entry, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 12px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <DIcon name="messageCircle" size={15} style={{ color: 'var(--info)', marginTop: 2, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.question}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {entry.created_at ? new Date(entry.created_at).toLocaleDateString(locale) : ''}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noQuestions')} />}
        </DCard>

        <DCard title={t('dashboard.quickActions')}>
          <button onClick={() => navigate('/chat')} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s' }}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--gold)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', background: 'var(--gold-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold)' }}>
              <DIcon name="messageCircle" size={16} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 500 }}>{t('dashboard.askQuestion')}</span>
          </button>
        </DCard>
      </div>
    </>
  );
}

// ─── Shared components ───
function LoadingPlaceholder() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {[1, 2, 3].map(i => (
        <div key={i} style={{ height: 40, borderRadius: 8, background: 'var(--surface-active)', animation: 'pulse 1.5s ease-in-out infinite' }} />
      ))}
      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}

function EmptyText({ text }) {
  return <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>{text}</div>;
}

// ─── Main Dashboard ───
export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const user = getUser();
  const role = user?.role || 'member';
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  const subtitle = role === 'super_admin' ? t('dashboard.subtitleSuperAdmin')
    : ['owner', 'admin'].includes(role) ? t('dashboard.subtitleAdmin')
    : t('dashboard.subtitleMember');

  return (
    <div style={{ padding: '28px 32px', maxWidth: 1200 }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>
          {t('dashboard.greeting', { name: user?.full_name || user?.email || '' })}
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{subtitle}</p>
      </div>

      {/* Role-based dashboard */}
      {role === 'super_admin' && <SuperAdminDashboard t={t} locale={locale} navigate={navigate} />}
      {['owner', 'admin'].includes(role) && <AdminDashboard t={t} locale={locale} navigate={navigate} user={user} />}
      {role === 'member' && <MemberDashboard t={t} locale={locale} navigate={navigate} />}
      {role === 'viewer' && <ViewerDashboard t={t} locale={locale} navigate={navigate} />}
    </div>
  );
}
