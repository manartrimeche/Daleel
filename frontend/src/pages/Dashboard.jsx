import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import DIcon from '../components/DIcon';
import { StatCard, DCard, ProgressBar, Badge, ScoreRing, Skeleton, MiniLineChart, AreaLineChart, DonutChart, useConfirm, useToast } from '../components/UI';
import { authFetch, getUser } from '../utils/auth';

// ─── Count-up hook ───
function useCountUp(target, duration = 900) {
  const [value, setValue] = useState(0);
  const prev = useRef(0);
  useEffect(() => {
    const from = prev.current;
    const to = typeof target === 'number' ? target : 0;
    if (to === from) return;
    prev.current = to;
    const start = performance.now();
    let raf;
    const step = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const ease = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setValue(Math.round(from + (to - from) * ease));
      if (t < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

// ─── Helper: safe fetch with fallback ───
async function safeFetch(url) {
  try {
    const res = await authFetch(url);
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

// ─── BI KPI Card (gradient bg + count-up + fade-in cascade) ───
function BICard({ icon, label, value, sub, subColor, sparkData, sparkColor, loading, onClick, accent = '#b8860b', delay = 0 }) {
  const displayValue = useCountUp(loading ? 0 : (typeof value === 'number' ? value : parseInt(value, 10) || 0), 1000);

  return (
    <div
      onClick={onClick}
      style={{
        background: `linear-gradient(135deg, var(--surface) 55%, ${accent}0C 100%)`,
        borderRadius: 'var(--radius-lg)', padding: '18px 20px',
        border: '1px solid var(--border)',
        borderLeft: `3px solid ${accent}`,
        display: 'flex', flexDirection: 'column', gap: 6,
        boxShadow: 'var(--shadow-sm)', cursor: onClick ? 'pointer' : 'default',
        transition: 'box-shadow .2s, transform .2s',
        animation: `biCardIn 0.45s ease ${delay}ms both`,
      }}
      className={onClick ? 'hover-lift' : undefined}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ width: 34, height: 34, borderRadius: 'var(--radius-md)', background: `${accent}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: accent }}>
          <DIcon name={icon} size={17} />
        </div>
        {sparkData && sparkData.length > 1 && <MiniLineChart data={sparkData} color={sparkColor || accent} />}
      </div>
      <div>
        <div style={{ fontSize: 26, fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--text)', lineHeight: 1.1 }}>
          {loading ? '...' : displayValue}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 3, display: 'flex', alignItems: 'center', gap: 6 }}>
          {label}
          {sub && <span style={{ fontSize: 11, fontWeight: 600, color: subColor || 'var(--text-muted)' }}>{sub}</span>}
        </div>
      </div>
    </div>
  );
}

// ─── Colors ───
const COLORS = {
  gold: 'var(--gold)', navy: 'var(--navy)', info: 'var(--info)',
  success: 'var(--success)', warning: 'var(--warning)', error: 'var(--error)',
  muted: 'var(--text-muted)',
  donut: ['#b8860b', '#1b2b42', '#2d6a4f', '#e74c3c', '#3498db', '#9b59b6', '#e67e22', '#1abc9c'],
};

function asPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.round(numeric > 1 ? numeric : numeric * 100);
}

function complianceCoveragePercent(compliance) {
  return asPercent(
    compliance?.coverage
      ?? compliance?.overall_coverage_score
      ?? compliance?.overall_score
      ?? compliance?.score
      ?? 0
  );
}

// ─── Super Admin Dashboard (BI) ───
function coverageSuggestionLabel(t, status) {
  if (status === 'fully_covered') return t('dashboard.coverageSuggestedFully');
  return t('dashboard.coverageSuggestedNone');
}

function coverageSuggestionColor(status) {
  if (status === 'fully_covered') return 'var(--success)';
  return 'var(--error)';
}

function SuperAdminDashboard({ t, locale, navigate }) {
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [orgs, setOrgs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [cases, setCases] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      safeFetch('/api/v1/admin/stats'),
      safeFetch('/api/v1/admin/analytics?days=30'),
      safeFetch('/api/v1/auth/organizations?limit=5'),
      safeFetch('/api/v1/admin/notifications?limit=5'),
      safeFetch('/api/v1/cases/summary'),
    ]).then(([s, a, o, n, c]) => {
      setStats(s);
      setAnalytics(a);
      const orgData = Array.isArray(o) ? o : o?.organizations || o?.items || [];
      setOrgs(orgData);
      setNotifications(n?.notifications || []);
      setCases(c);
      setLoading(false);
    });
  }, []);

  const num = (v) => (typeof v === 'object' && v !== null) ? (v.total ?? 0) : (v ?? 0);
  const docCount = stats?.documents?.by_status?.ready ?? num(stats?.documents);
  const lawCount = stats?.lois?.indexed_total ?? num(stats?.lois);
  const orgCount = num(stats?.organizations) || orgs.length;
  const userCount = num(stats?.users) || orgs.reduce((sum, o) => sum + (o.member_count || 0), 0);
  const exigCount = num(stats?.exigences);
  const questionCount = num(stats?.questions);
  const caseStatus = cases?.by_status || stats?.cases?.by_status || {};
  const openCaseCount = (caseStatus.open || 0) + (caseStatus.in_progress || 0);

  // ── Donut: documents by status
  const docsByStatus = stats?.documents?.by_status || {};
  const docSegments = Object.entries(docsByStatus).map(([k, v], i) => ({
    label: k === 'ready' ? t('dashboard.statusProcessed') : k === 'error' ? t('dashboard.statusError') : k,
    value: v,
    color: k === 'ready' ? COLORS.success : k === 'error' ? COLORS.error : k === 'pending' ? COLORS.warning : COLORS.donut[i % COLORS.donut.length],
  }));

  // ── Donut: cases by priority
  const casesByPriority = stats?.cases?.by_priority || cases?.by_priority || {};
  const caseSegments = [
    { label: t('dashboard.priorityHigh'), value: casesByPriority.high || 0, color: COLORS.error },
    { label: t('dashboard.priorityMedium'), value: casesByPriority.medium || 0, color: COLORS.warning },
    { label: t('dashboard.priorityLow'), value: casesByPriority.low || 0, color: COLORS.info },
  ];

  // ── Donut: exigences by type
  const exigByType = stats?.exigences?.by_type || {};
  const exigSegments = Object.entries(exigByType).map(([k, v], i) => ({
    label: k, value: v, color: COLORS.donut[i % COLORS.donut.length],
  }));

  // ── Time-series chart data
  const qaChartData = (analytics?.qa_daily || []).map(d => ({
    label: new Date(d.date).toLocaleDateString(locale, { day: '2-digit', month: 'short' }),
    value: d.count,
  }));

  return (
    <>
      {/* ── Row 1: KPIs (compact) ───────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12, marginBottom: 16 }}>
        <BICard icon="fileText" label={t('dashboard.docsIndexed')} value={docCount} loading={loading} onClick={() => navigate('/admin/documents')} accent="#b8860b" delay={0} />
        <BICard icon="layers" label={t('dashboard.activeLaws')} value={lawCount} loading={loading} accent="#1b2b42" delay={60} />
        <BICard icon="globe" label={t('dashboard.organizations')} value={orgCount} loading={loading} onClick={() => navigate('/admin/organizations')} accent="#2d6a4f" delay={120} />
        <BICard icon="users" label={t('dashboard.totalUsers')} value={userCount} loading={loading} accent="#7c3aed" delay={180} />
        <BICard icon="shieldCheck" label={t('dashboard.exigences')} value={exigCount} loading={loading} accent="#3498db" delay={240} />
        <BICard icon="messageCircle" label={t('dashboard.questionsAsked')} value={questionCount} loading={loading} accent="#e67e22" delay={300} />
      </div>

      {/* ── Row 2: Chart + 3 donuts side-by-side ──────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '5fr 2fr 2fr 2fr', gap: 14, marginBottom: 16 }}>
        <div style={{ animation: 'biCardIn 0.45s ease 380ms both' }}>
        <DCard title={t('dashboard.qaActivity')}>
          {loading ? <LoadingPlaceholder /> : (
            <AreaLineChart data={qaChartData} height={170} color={COLORS.info} />
          )}
        </DCard>
        </div>

        <div style={{ animation: 'biCardIn 0.45s ease 440ms both' }}>
        <DCard title={t('dashboard.docsByStatus')}>
          {loading ? <LoadingPlaceholder /> : docSegments.length > 0 ? (
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <DonutChart segments={docSegments} centerValue={num(stats?.documents)} centerLabel={t('dashboard.total')} size={100} thickness={16} />
            </div>
          ) : <EmptyText text={t('dashboard.noDocs')} />}
        </DCard>
        </div>

        <div style={{ animation: 'biCardIn 0.45s ease 500ms both' }}>
        <DCard title={t('dashboard.casesByPriority')}>
          {loading ? <LoadingPlaceholder /> : (
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <DonutChart segments={caseSegments} centerValue={num(stats?.cases)} centerLabel={t('dashboard.total')} size={100} thickness={16} />
            </div>
          )}
        </DCard>
        </div>

        <div style={{ animation: 'biCardIn 0.45s ease 560ms both' }}>
        <DCard title={t('dashboard.exigencesByType')}>
          {loading ? <LoadingPlaceholder /> : exigSegments.length > 0 ? (
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <DonutChart segments={exigSegments} centerValue={exigCount} centerLabel={t('dashboard.total')} size={100} thickness={16} />
            </div>
          ) : <EmptyText text={t('dashboard.noData')} />}
        </DCard>
        </div>
      </div>

      {/* ── Row 3: Stats + Orgs + Notifs — dense 3-col ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14, marginBottom: 16 }}>
        {/* Platform mini-stats */}
        <div style={{ animation: 'biCardIn 0.45s ease 640ms both' }}>
        <DCard title={t('dashboard.platformStats')}>
          {loading ? <LoadingPlaceholder /> : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {[
                { label: t('dashboard.openCases'), value: openCaseCount, icon: 'target', color: openCaseCount > 0 ? COLORS.warning : COLORS.success },
                { label: t('dashboard.amendments'), value: num(stats?.amendments), icon: 'edit', color: COLORS.navy },
                { label: t('dashboard.totalArticles'), value: num(stats?.articles), icon: 'hash', color: COLORS.info },
                { label: t('dashboard.auditLogs'), value: num(stats?.audit_logs), icon: 'eye', color: COLORS.muted },
              ].map((s, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 8px', borderRadius: 6, background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ width: 26, height: 26, borderRadius: 6, background: `${s.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: s.color, flexShrink: 0 }}>
                    <DIcon name={s.icon} size={13} />
                  </div>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-heading)', lineHeight: 1 }}>{s.value}</div>
                    <div style={{ fontSize: 9, color: 'var(--text-secondary)' }}>{s.label}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </DCard>
        </div>

        {/* Orgs */}
        <div style={{ animation: 'biCardIn 0.45s ease 700ms both' }}>
        <DCard title={t('dashboard.recentOrgs')} action={
          <button onClick={() => navigate('/admin/organizations')} style={{ fontSize: 11, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : orgs.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {orgs.slice(0, 4).map((org, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '5px 8px', borderRadius: 6, background: 'var(--surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 22, height: 22, borderRadius: 5, background: 'var(--navy)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 9, fontWeight: 600 }}>
                      {(org.name || '?')[0].toUpperCase()}
                    </div>
                    <div style={{ fontSize: 11, fontWeight: 500 }}>{org.name}</div>
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>
                    {org.member_count || 0} {t('dashboard.orgMembers').toLowerCase()}
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noActivity')} />}
        </DCard>
        </div>

        {/* Notifications */}
        <div style={{ animation: 'biCardIn 0.45s ease 760ms both' }}>
        <DCard title={t('dashboard.notifications')} action={
          <button onClick={() => navigate('/admin/notifications')} style={{ fontSize: 11, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
        }>
          {loading ? <LoadingPlaceholder /> : notifications.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {notifications.slice(0, 4).map((n, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 8px', borderRadius: 6, background: n.read ? 'transparent' : 'var(--gold-bg)', border: '1px solid var(--border-subtle)' }}>
                  <DIcon name="bell" size={12} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                  <div style={{ flex: 1, fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.title || n.type}</div>
                </div>
              ))}
            </div>
          ) : <EmptyText text={t('dashboard.noNotifications')} />}
        </DCard>
        </div>
      </div>

      {/* ── Row 4: Quick actions — inline bar ──────────────── */}
      <div style={{ display: 'flex', gap: 10, animation: 'biCardIn 0.45s ease 900ms both' }}>
        {[
          { icon: 'messageCircle', label: t('dashboard.askQuestion'), color: COLORS.gold, path: '/chat' },
          { icon: 'upload', label: t('dashboard.importDoc'), color: COLORS.info, path: '/admin/documents' },
          { icon: 'edit', label: t('dashboard.importAmendment'), color: COLORS.success, path: '/admin/amendments' },
          { icon: 'target', label: t('dashboard.newCase'), color: COLORS.warning, path: '/admin/cases' },
        ].map((action, i) => (
          <button key={i} onClick={() => navigate(action.path)} className="hover-border-accent" style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderRadius: 'var(--radius-md)', background: 'var(--surface)', border: '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ width: 26, height: 26, borderRadius: 6, background: `${action.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: action.color }}>
              <DIcon name={action.icon} size={13} />
            </div>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{action.label}</span>
          </button>
        ))}
      </div>
    </>
  );
}

// ─── CTA Empty State ───
function EmptyCTA({ icon, text, actionLabel, onAction }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '28px 16px', textAlign: 'center', gap: 12 }}>
      <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--gold-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold)' }}>
        <DIcon name={icon} size={20} />
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: 240 }}>{text}</div>
      {actionLabel && onAction && (
        <button onClick={onAction} className="hover-border-accent" style={{ padding: '8px 18px', borderRadius: 8, background: 'var(--navy)', color: '#fff', fontSize: 12, fontWeight: 600, border: 'none', cursor: 'pointer', transition: 'opacity .15s' }}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}

// ─── Owner / Admin Dashboard (BI style) ───
function AdminDashboard({ t, locale, navigate, user }) {
  const [stats, setStats] = useState(null);
  const [docs, setDocs] = useState([]);
  const [cases, setCases] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [compliance, setCompliance] = useState(null);
  const [profileId, setProfileId] = useState(null);
  const [coveringGapId, setCoveringGapId] = useState(null);
  const [initializingProfile, setInitializingProfile] = useState(false);
  const [suggestingCoverage, setSuggestingCoverage] = useState(false);
  const [coverageSuggestions, setCoverageSuggestions] = useState({});
  const [loading, setLoading] = useState(true);
  const toast = useToast();
  const confirm = useConfirm();

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

      const profileList = Array.isArray(profiles) ? profiles : profiles?.profiles || [];
      if (profileList.length > 0) {
        const currentProfileId = profileList[0].id;
        setProfileId(currentProfileId);
        const posture = await safeFetch(`/api/v1/compliance/posture/${currentProfileId}`);
        setCompliance(posture);
        setCoverageSuggestions({});
      } else {
        setProfileId(null);
        setCompliance(null);
        setCoverageSuggestions({});
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
  const totalCases = openCases + inProgressCases + closedCases;
  const complianceScore = complianceCoveragePercent(compliance);
  const hasComplianceData = Number(compliance?.total_applicable || 0) > 0;
  const complianceGaps = compliance?.gaps_count ?? (Array.isArray(compliance?.gaps) ? compliance.gaps.length : undefined);
  const visibleComplianceGaps = Array.isArray(compliance?.gaps) ? compliance.gaps.slice(0, 4) : [];
  const canManageCoverage = user?.role === 'owner';
  const docCount = (typeof stats?.documents === 'object' ? stats.documents.total : stats?.documents) || 0;
  const userCount = (typeof stats?.users === 'object' ? stats.users.total : stats?.users) || 0;

  const coverGap = async (gap, suggestion = null) => {
    if (!canManageCoverage || !profileId || !gap?.exigence_id) return;
    const ok = await confirm(t('dashboard.coverRequirementConfirm'), {
      title: t('dashboard.coverRequirement'),
      confirmLabel: t('dashboard.coverRequirement'),
    });
    if (!ok) return;

    setCoveringGapId(gap.exigence_id);
    try {
      const titleSource = gap.exigence_title || gap.exigence_id;
      const suggestedJustification = suggestion?.rationale
        ? `${t('dashboard.manualCoverageJustification')} ${t('dashboard.coverageSuggestion')}: ${suggestion.rationale}`
        : t('dashboard.manualCoverageJustification');
      const res = await authFetch(`/api/v1/compliance/posture/${profileId}/cover/${gap.exigence_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          control_title: `${t('dashboard.coverageControlPrefix')}: ${String(titleSource).slice(0, 180)}`,
          justification: suggestedJustification,
          linked_by: user?.email || user?.full_name || 'dashboard',
        }),
      });
      if (!res.ok) throw new Error('coverage-update-failed');
      const updatedPosture = await res.json();
      setCompliance(updatedPosture);
      setCoverageSuggestions(prev => {
        const next = { ...prev };
        delete next[gap.exigence_id];
        return next;
      });
      toast.success(t('dashboard.coverageUpdated'));
    } catch {
      toast.error(t('dashboard.coverageUpdateFailed'));
    } finally {
      setCoveringGapId(null);
    }
  };

  const initializeComplianceProfile = async () => {
    if (initializingProfile) return;
    setInitializingProfile(true);
    try {
      const res = await authFetch('/api/v1/company-profiles/ensure-current', {
        method: 'POST',
      });
      if (!res.ok) throw new Error('compliance-init-failed');
      const data = await res.json();
      const nextProfileId = data?.profile?.id;
      if (!nextProfileId) throw new Error('missing-profile');
      setProfileId(nextProfileId);
      const posture = await safeFetch(`/api/v1/compliance/posture/${nextProfileId}`);
      setCompliance(posture);
      setCoverageSuggestions({});
      if (Number(data?.applicability_total || 0) > 0 || Number(posture?.total_applicable || 0) > 0) {
        toast.success(t('dashboard.complianceInitialized'));
      } else {
        toast.info(t('dashboard.complianceNeedsEvaluation'));
      }
    } catch {
      toast.error(t('dashboard.complianceInitFailed'));
    } finally {
      setInitializingProfile(false);
    }
  };

  const suggestCoverage = async () => {
    if (!profileId || suggestingCoverage) return;
    setSuggestingCoverage(true);
    try {
      const res = await authFetch(`/api/v1/compliance/posture/${profileId}/suggest-coverage?limit=8`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('coverage-suggestions-failed');
      const data = await res.json();
      const byExigence = {};
      for (const suggestion of data?.suggestions || []) {
        if (suggestion?.exigence_id) byExigence[suggestion.exigence_id] = suggestion;
      }
      setCoverageSuggestions(byExigence);
      toast.success(t('dashboard.coverageSuggestionsReady'));
    } catch {
      toast.error(t('dashboard.coverageSuggestionsFailed'));
    } finally {
      setSuggestingCoverage(false);
    }
  };

  // Donut: cases
  const caseSegments = [
    { label: t('dashboard.caseOpen'), value: openCases, color: 'var(--warning)' },
    { label: t('dashboard.caseInProgress'), value: inProgressCases, color: 'var(--info)' },
    { label: t('dashboard.caseClosed'), value: closedCases, color: 'var(--success)' },
  ];

  return (
    <>
      <div className="owner-kpi-grid">
        <BICard icon="fileText" label={t('dashboard.docsIndexed')} value={docCount} loading={loading} onClick={() => navigate('/admin/documents')} accent="#b8860b" delay={0} />
        <BICard icon="messageCircle" label={t('dashboard.questionsAsked')} value={chatHistory.length} loading={loading} accent="#e67e22" delay={60} />
        <BICard icon="users" label={t('dashboard.users')} value={userCount} loading={loading} accent="#7c3aed" delay={120} />
        <BICard icon="target" label={t('dashboard.openCases')} value={openCases + inProgressCases} loading={loading} accent="#3498db" delay={180} />
        <BICard icon="shieldCheck" label={t('dashboard.complianceScore')} value={hasComplianceData ? complianceScore : 0} loading={loading} accent="#2d6a4f" delay={240} sub={hasComplianceData ? '%' : null} />
      </div>

      <div className="owner-dashboard-layout">
        <div className="owner-main-stack">
          <div style={{ animation: 'biCardIn 0.45s ease 320ms both' }}>
            <DCard title={t('dashboard.complianceCoverage')} style={{ height: '100%' }} action={hasComplianceData ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {canManageCoverage && visibleComplianceGaps.length > 0 && (
                  <button
                    type="button"
                    onClick={suggestCoverage}
                    disabled={suggestingCoverage}
                    title={t('dashboard.coverageAnalyze')}
                    aria-label={t('dashboard.coverageAnalyze')}
                    style={{ height: 28, padding: '0 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--navy)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 700, cursor: suggestingCoverage ? 'wait' : 'pointer', whiteSpace: 'nowrap' }}
                  >
                    <DIcon name="sparkle" size={12} />
                    {suggestingCoverage ? t('dashboard.coverageAnalyzing') : t('dashboard.coverageAnalyze')}
                  </button>
                )}
                <Badge variant="gold">{complianceScore}%</Badge>
              </div>
            ) : null}>
              {loading ? <LoadingPlaceholder /> : hasComplianceData ? (
                <>
                  <div className="owner-compliance-summary">
                    <ScoreRing value={complianceScore} size={76} variant={complianceScore >= 80 ? 'success' : complianceScore >= 50 ? 'warning' : 'error'} />
                    <div className="owner-compliance-copy">
                      <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>{t('dashboard.globalScore')}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.55 }}>{t('dashboard.globalScoreDesc')}</div>
                    </div>
                    <div className="owner-compliance-facts">
                      {complianceGaps !== undefined && (
                        <div className="owner-fact-pill">
                          <span>{t('dashboard.complianceGaps')}</span>
                          <strong style={{ color: 'var(--error)' }}>{complianceGaps}</strong>
                        </div>
                      )}
                      {compliance.controls_count !== undefined && (
                        <div className="owner-fact-pill">
                          <span>{t('dashboard.complianceControls')}</span>
                          <strong style={{ color: 'var(--success)' }}>{compliance.controls_count}</strong>
                        </div>
                      )}
                    </div>
                  </div>
                  <ProgressBar value={complianceScore} label={t('dashboard.complianceCoverage')} variant={complianceScore >= 80 ? 'success' : complianceScore >= 50 ? 'warning' : 'error'} />
                  {canManageCoverage && visibleComplianceGaps.length > 0 && (
                    <div className="owner-gap-list">
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0 }}>
                        {t('dashboard.coverageGapList')}
                      </div>
                      {visibleComplianceGaps.map((gap) => {
                        const isCovering = coveringGapId === gap.exigence_id;
                        const suggestion = coverageSuggestions[gap.exigence_id];
                        const suggestionStatus = suggestion?.suggested_status;
                        const suggestionPercent = Math.round(Number(suggestion?.confidence || 0) * 100);
                        const showSuggestionPercent = suggestionStatus === 'fully_covered';
                        return (
                          <div key={gap.exigence_id} className="owner-gap-item">
                            <div style={{ minWidth: 0, flex: 1 }}>
                              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {gap.exigence_title || gap.exigence_id}
                              </div>
                              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
                                {gap.coverage_status || 'not_covered'}
                              </div>
                              {suggestion && (
                                <>
                                  <div style={{ marginTop: 5, display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, fontWeight: 700, color: coverageSuggestionColor(suggestionStatus) }}>
                                    <DIcon name="sparkle" size={10} />
                                    <span>
                                      {t('dashboard.coverageSuggestion')}: {coverageSuggestionLabel(t, suggestionStatus)}
                                      {showSuggestionPercent ? ` · ${suggestionPercent}%` : ` · ${t('dashboard.coverageInsufficientEvidence')}`}
                                    </span>
                                  </div>
                                  <div title={suggestion.rationale} style={{ marginTop: 2, fontSize: 10, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {suggestion.rationale}
                                  </div>
                                </>
                              )}
                            </div>
                            <button
                              type="button"
                              onClick={() => coverGap(gap, suggestion)}
                              disabled={Boolean(coveringGapId)}
                              title={t('dashboard.coverRequirement')}
                              aria-label={t('dashboard.coverRequirement')}
                              style={{ minWidth: 92, height: 30, marginTop: 2, padding: '0 9px', borderRadius: 6, border: '1px solid var(--success)', background: isCovering ? 'var(--success-bg)' : 'transparent', color: 'var(--success)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, fontSize: 11, fontWeight: 700, cursor: coveringGapId ? 'wait' : 'pointer', whiteSpace: 'nowrap' }}
                            >
                              <DIcon name="check" size={13} />
                              {isCovering ? '...' : t('dashboard.coverRequirement')}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </>
              ) : (
                <>
                  <ProgressBar value={0} label={t('dashboard.complianceCoverage')} variant="error" />
                  <EmptyCTA
                    icon="shieldCheck"
                    text={t('dashboard.noComplianceData')}
                    actionLabel={initializingProfile ? t('dashboard.initializingCompliance') : t('dashboard.initializeCompliance')}
                    onAction={initializeComplianceProfile}
                  />
                </>
              )}
            </DCard>
          </div>

          <div style={{ animation: 'biCardIn 0.45s ease 500ms both' }}>
            <DCard title={t('dashboard.recentDocs')} action={
              <button onClick={() => navigate('/admin/documents')} style={{ fontSize: 11, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
            }>
              {loading ? <LoadingPlaceholder /> : docs.length > 0 ? (
                <div className="owner-list">
                  {docs.slice(0, 4).map((doc, i) => (
                    <div key={i} className="owner-list-item">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 9, flex: 1, minWidth: 0 }}>
                        <DIcon name="fileText" size={14} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                        <span style={{ fontSize: 12, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.filename || doc.title || doc.name}</span>
                      </div>
                      <Badge variant={['processed', 'ready'].includes(doc.status) ? 'success' : doc.status === 'error' ? 'error' : 'neutral'}>
                        {['processed', 'ready'].includes(doc.status) ? t('dashboard.statusProcessed') : doc.status === 'error' ? t('dashboard.statusError') : t('dashboard.statusPending')}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : <EmptyCTA icon="fileText" text={t('dashboard.noDocs')} actionLabel={t('dashboard.importDoc')} onAction={() => navigate('/admin/documents')} />}
            </DCard>
          </div>
        </div>

        <div className="owner-side-stack">
          <div style={{ animation: 'biCardIn 0.45s ease 380ms both' }}>
            <DCard title={t('dashboard.caseSummary')} style={{ height: '100%' }}>
              {loading ? <LoadingPlaceholder /> : totalCases > 0 ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '6px 0' }}>
                  <DonutChart segments={caseSegments} centerValue={totalCases} centerLabel={t('dashboard.total')} size={124} thickness={18} />
                </div>
              ) : (
                <EmptyCTA icon="target" text={t('dashboard.noCases')} actionLabel={t('dashboard.newCase')} onAction={() => navigate('/admin/cases')} />
              )}
            </DCard>
          </div>

          <div style={{ animation: 'biCardIn 0.45s ease 440ms both' }}>
            <DCard title={t('dashboard.quickActions')} style={{ height: '100%' }}>
              <div className="owner-action-grid">
                {[
                  { icon: 'messageCircle', label: t('dashboard.askQuestion'), color: 'var(--gold)', bg: 'var(--gold-bg)', path: '/chat' },
                  { icon: 'upload', label: t('dashboard.importDoc'), color: 'var(--info)', bg: 'var(--info-bg)', path: '/admin/documents' },
                  { icon: 'edit', label: t('dashboard.importAmendment'), color: 'var(--success)', bg: 'var(--success-bg)', path: '/admin/amendments' },
                  { icon: 'target', label: t('dashboard.newCase'), color: 'var(--warning)', bg: 'var(--warning-bg)', path: '/admin/cases' },
                ].map((action, i) => (
                  <button key={i} onClick={() => navigate(action.path)} className="owner-action-button hover-border-accent" style={{ '--action-color': action.color }}>
                    <div style={{ width: 28, height: 28, borderRadius: 7, background: action.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: action.color }}>
                      <DIcon name={action.icon} size={13} />
                    </div>
                    <span>{action.label}</span>
                  </button>
                ))}
              </div>
            </DCard>
          </div>
        </div>
      </div>

      <div className="owner-activity-grid">
        <div style={{ animation: 'biCardIn 0.45s ease 560ms both' }}>
          <DCard title={t('dashboard.recentQuestions')} style={{ height: '100%' }} action={
            <button onClick={() => navigate('/admin/history')} style={{ fontSize: 11, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
          }>
            {loading ? <LoadingPlaceholder /> : chatHistory.length > 0 ? (
              <div className="owner-list">
                {chatHistory.slice(0, 4).map((entry, i) => (
                  <div key={i} className="owner-list-item owner-list-item-start">
                    <DIcon name="messageCircle" size={14} style={{ color: 'var(--info)', marginTop: 2, flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.question}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>
                        {entry.created_at ? new Date(entry.created_at).toLocaleDateString(locale) : ''}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : <EmptyText text={t('dashboard.noQuestions')} />}
          </DCard>
        </div>

        <div style={{ animation: 'biCardIn 0.45s ease 620ms both' }}>
          <DCard title={t('dashboard.notifications')} style={{ height: '100%' }} action={
            <button onClick={() => navigate('/admin/notifications')} style={{ fontSize: 11, color: 'var(--gold)', fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer' }}>{t('common.seeAll')}</button>
          }>
            {loading ? <LoadingPlaceholder /> : notifications.length > 0 ? (
              <div className="owner-list">
                {notifications.slice(0, 4).map((n, i) => (
                  <div key={i} className="owner-list-item" style={{ background: n.read ? 'var(--surface-hover)' : 'var(--gold-bg)' }}>
                    <DIcon name="bell" size={13} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                    <div style={{ flex: 1, fontSize: 12, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.title || n.type}</div>
                  </div>
                ))}
              </div>
            ) : <EmptyText text={t('dashboard.noNotifications')} />}
          </DCard>
        </div>
      </div>
    </>
  );
}

// ─── Member Dashboard ───
function MemberDashboard({ t, locale, navigate }) {
  const [cases, setCases] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [compliance, setCompliance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      safeFetch('/api/v1/cases?limit=5'),
      safeFetch('/api/v1/chat-history?limit=5'),
      safeFetch('/api/v1/notifications/mine?limit=5'),
      safeFetch('/api/v1/company-profiles?limit=1'),
    ]).then(async ([c, ch, n, profiles]) => {
      setCases(c);
      setChatHistory(ch?.entries || (Array.isArray(ch) ? ch : []));
      setNotifications(n?.notifications || []);

      const profileList = Array.isArray(profiles) ? profiles : profiles?.profiles || [];
      if (profileList.length > 0) {
        const posture = await safeFetch(`/api/v1/compliance/posture/${profileList[0].id}`);
        setCompliance(posture);
      }

      setLoading(false);
    });
  }, []);

  const caseList = Array.isArray(cases) ? cases : cases?.cases || [];
  const complianceCoverage = complianceCoveragePercent(compliance);
  const hasComplianceData = Number(compliance?.total_applicable || 0) > 0;

  return (
    <>
      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 28 }}>
        <StatCard icon="target" label={t('dashboard.myCases')} value={loading ? '...' : caseList.length} />
        <StatCard icon="messageCircle" label={t('dashboard.questionsAsked')} value={loading ? '...' : chatHistory.length} />
        <StatCard icon="bell" label={t('dashboard.activeAlerts')} value={loading ? '...' : notifications.filter(n => !n.read).length} variant={notifications.filter(n => !n.read).length > 0 ? 'warning' : 'default'} />
      </div>

      {/* Conformité + Dossiers + Questions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20, marginBottom: 24 }}>
        <DCard title={t('dashboard.complianceCoverage')}>
          {loading ? <LoadingPlaceholder /> : hasComplianceData ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <ProgressBar value={complianceCoverage} label={t('dashboard.complianceCoverage')} variant={complianceCoverage >= 80 ? 'success' : complianceCoverage >= 50 ? 'warning' : 'error'} />
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: 12 }}>
                <span style={{ color: 'var(--text-secondary)' }}>{t('dashboard.complianceGaps')}</span>
                <span style={{ fontWeight: 600, color: 'var(--error)' }}>{Array.isArray(compliance.gaps) ? compliance.gaps.length : 0}</span>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <ProgressBar value={0} label={t('dashboard.complianceCoverage')} variant="error" />
              <EmptyText text={t('dashboard.noComplianceData')} />
            </div>
          )}
        </DCard>

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
              <button key={i} onClick={() => navigate(action.path)} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s', '--action-color': action.color }}
                className="hover-border-accent"
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
          <button onClick={() => navigate('/chat')} className="hover-border-accent" style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderRadius: 'var(--radius-md)', background: 'var(--surface-hover)', border: '1px solid var(--border)', cursor: 'pointer', transition: 'all .15s' }}
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
  return <Skeleton height={40} count={3} />;
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
    <div style={{ padding: '44px 32px 28px', maxWidth: 1200 }}>
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
