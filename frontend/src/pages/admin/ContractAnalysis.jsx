import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { DCard, Badge, EmptyState } from '../../components/UI';
import DIcon from '../../components/DIcon';
import { authFetch } from '../../utils/auth';

/* ── Couleurs score ── */
const scoreColors = {
  excellent: { bg: '#e8f5e9', text: '#2e7d32', ring: '#4caf50' },
  bon: { bg: '#e3f2fd', text: '#1565c0', ring: '#2196f3' },
  attention: { bg: '#fff3e0', text: '#e65100', ring: '#ff9800' },
  critique: { bg: '#ffebee', text: '#c62828', ring: '#f44336' },
};

const severityColors = {
  critical: { bg: '#ffebee', text: '#c62828', border: '#ef5350' },
  major: { bg: '#fff3e0', text: '#e65100', border: '#ff9800' },
  minor: { bg: '#fffde7', text: '#f57f17', border: '#ffee58' },
};

/* ── Score Ring SVG ── */
function ScoreRing({ score, category, size = 120 }) {
  const colors = scoreColors[category] || scoreColors.attention;
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={8} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={colors.ring} strokeWidth={8}
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: size * 0.3, fontWeight: 800, color: colors.text, lineHeight: 1 }}>{score}</span>
        <span style={{ fontSize: 10, color: colors.text, fontWeight: 600, marginTop: 2 }}>/100</span>
      </div>
    </div>
  );
}

export default function ContractAnalysis() {
  const { t } = useTranslation();
  const [docs, setDocs] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const pollRef = useRef(null);

  /* ── Charger les documents ── */
  useEffect(() => {
    authFetch('/api/v1/documents?skip=0&limit=100')
      .then(r => r.json())
      .then(data => {
        const list = Array.isArray(data) ? data : data.documents || [];
        setDocs(list);
      })
      .catch(() => {});
  }, []);

  /* ── Charger l'analyse si document selectionne ── */
  useEffect(() => {
    if (!selectedDocId) { setAnalysis(null); return; }
    setLoading(true);
    authFetch(`/api/v1/documents/${selectedDocId}/contract-analysis`)
      .then(r => {
        if (r.status === 404) return null;
        return r.json();
      })
      .then(data => {
        setAnalysis(data);
        if (data && data.status === 'analyzing') startPolling();
        setLoading(false);
      })
      .catch(() => { setAnalysis(null); setLoading(false); });
    return () => stopPolling();
  }, [selectedDocId]);

  /* ── Polling pour analyse en cours ── */
  function startPolling() {
    stopPolling();
    setAnalyzing(true);
    pollRef.current = setInterval(async () => {
      try {
        const res = await authFetch(`/api/v1/documents/${selectedDocId}/contract-analysis`);
        if (!res.ok) return;
        const data = await res.json();
        setAnalysis(data);
        if (data.status !== 'analyzing') {
          setAnalyzing(false);
          stopPolling();
        }
      } catch { /* polling is best-effort */ }
    }, 4000);
  }

  function stopPolling() {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  }

  /* ── Lancer l'analyse ── */
  async function triggerAnalysis() {
    if (!selectedDocId) return;
    setAnalyzing(true);
    setActiveTab('overview');
    try {
      const res = await authFetch(`/api/v1/documents/${selectedDocId}/contract-analysis`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setAnalysis(data);
        startPolling();
      }
    } catch { setAnalyzing(false); }
  }

  /* ── Supprimer l'analyse ── */
  async function deleteAnalysis() {
    if (!selectedDocId) return;
    await authFetch(`/api/v1/documents/${selectedDocId}/contract-analysis`, { method: 'DELETE' });
    setAnalysis(null);
  }

  const tabs = [
    { key: 'overview', label: t('contracts.tabs.overview'), icon: 'grid' },
    { key: 'risks', label: t('contracts.tabs.risks'), icon: 'alertTriangle', count: analysis?.findings_summary?.total },
    { key: 'missing', label: t('contracts.tabs.missing'), icon: 'search', count: analysis?.missing_clauses?.length },
    { key: 'recommendations', label: t('contracts.tabs.recommendations'), icon: 'sparkle' },
  ];

  const a = analysis;
  const colors = scoreColors[a?.score_category] || scoreColors.attention;

  return (
    <div style={{ padding: '28px 32px', maxWidth: 1200 }}>
      {/* ── Header ── */}
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>
        {t('contracts.title')}
      </h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
        {t('contracts.subtitle')}
      </p>

      {/* ── Document Selector + Action ── */}
      <DCard style={{ padding: '16px 20px', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
        <DIcon name="fileSearch" size={22} style={{ color: 'var(--gold)' }} />
        <select
          value={selectedDocId}
          onChange={e => setSelectedDocId(e.target.value)}
          style={{
            flex: 1, minWidth: 200, padding: '8px 12px', borderRadius: 8,
            border: '1px solid var(--border)', background: 'var(--surface)',
            color: 'var(--text)', fontSize: 13,
          }}
        >
          <option value="">{t('contracts.selectDocument')}</option>
          {docs.map(d => (
            <option key={d.id || d._id} value={d.id || d._id}>
              {d.filename || d.name || d.id}
            </option>
          ))}
        </select>

        <button
          onClick={triggerAnalysis}
          disabled={!selectedDocId || analyzing}
          style={{
            padding: '8px 20px', borderRadius: 8, border: 'none',
            background: (!selectedDocId || analyzing) ? 'var(--border)' : 'var(--gold)',
            color: '#fff', fontSize: 13, fontWeight: 600, cursor: (!selectedDocId || analyzing) ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 6,
          }}
        >
          <DIcon name={analyzing ? 'refresh' : 'sparkle'} size={15} style={analyzing ? { animation: 'spin 1s linear infinite' } : {}} />
          {a?.status === 'completed' ? t('contracts.reAnalyze') : t('contracts.analyze')}
        </button>

        {a?.status === 'completed' && (
          <button
            onClick={deleteAnalysis}
            style={{
              padding: '8px 14px', borderRadius: 8, border: '1px solid var(--border)',
              background: 'transparent', color: 'var(--text-secondary)',
              fontSize: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
            }}
          >
            <DIcon name="trash" size={14} />
            {t('contracts.delete')}
          </button>
        )}
      </DCard>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>

      {/* ── States: empty / loading / analyzing / failed / completed ── */}
      {!selectedDocId && (
        <EmptyState icon="fileSearch" title={t('contracts.noAnalysis')} message={t('contracts.noAnalysisDesc')} />
      )}

      {selectedDocId && loading && !analyzing && (
        <DCard style={{ padding: 40, textAlign: 'center' }}>
          <DIcon name="refresh" size={28} style={{ color: 'var(--text-muted)', animation: 'spin 1s linear infinite' }} />
        </DCard>
      )}

      {analyzing && (
        <DCard style={{ padding: 40, textAlign: 'center' }}>
          <DIcon name="refresh" size={36} style={{ color: 'var(--gold)', animation: 'spin 1.2s linear infinite', marginBottom: 12 }} />
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>{t('contracts.analyzing')}</div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{t('contracts.analyzingDesc')}</div>
        </DCard>
      )}

      {a?.status === 'failed' && !analyzing && (
        <DCard style={{ padding: 32, textAlign: 'center' }}>
          <DIcon name="alertTriangle" size={32} style={{ color: 'var(--error)', marginBottom: 8 }} />
          <div style={{ fontSize: 14, color: 'var(--error)', fontWeight: 600 }}>{t('contracts.failedDesc')}</div>
          {a.error_message && <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>{a.error_message}</div>}
        </DCard>
      )}

      {/* ── RESULTATS ── */}
      {a?.status === 'completed' && !analyzing && (
        <>
          {/* Score + Summary header */}
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 20, marginBottom: 20 }}>
            {/* Score */}
            <DCard style={{ padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minWidth: 180 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {t('contracts.score')}
              </div>
              <ScoreRing score={a.score} category={a.score_category} />
              <Badge
                variant={a.score_category === 'excellent' ? 'success' : a.score_category === 'bon' ? 'info' : a.score_category === 'attention' ? 'warning' : 'error'}
                style={{ marginTop: 12, fontSize: 12, padding: '4px 14px' }}
              >
                {t(`contracts.${a.score_category}`)}
              </Badge>
            </DCard>

            {/* Summary */}
            <DCard style={{ padding: 20 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>{t('contracts.contractType')}</div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{a.contract_type_label || a.contract_type}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>{t('contracts.parties')}</div>
                  <div style={{ fontSize: 13 }}>{(a.parties || []).join(' — ') || '—'}</div>
                </div>
              </div>
              {a.summary && (
                <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>{t('contracts.summary')}</div>
                  <div style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)' }}>{a.summary}</div>
                </div>
              )}
              <div style={{ display: 'flex', gap: 16, marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
                <MiniStat icon="alertTriangle" label={t('contracts.findings')} value={a.findings_summary?.total || 0} color="var(--error)" />
                <MiniStat icon="search" label={t('contracts.missingClauses')} value={a.missing_clauses?.length || 0} color="var(--gold)" />
                <MiniStat icon="layers" label={t('contracts.chunksAnalyzed')} value={a.total_chunks_analyzed} color="var(--text-secondary)" />
                <MiniStat icon="clock" label={t('contracts.duration')} value={a.analysis_duration_ms ? `${Math.round(a.analysis_duration_ms / 1000)}s` : '—'} color="var(--text-secondary)" />
              </div>
            </DCard>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: 4, marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 0 }}>
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  padding: '8px 16px', fontSize: 13, fontWeight: activeTab === tab.key ? 700 : 400,
                  color: activeTab === tab.key ? 'var(--gold)' : 'var(--text-secondary)',
                  border: 'none', borderBottom: activeTab === tab.key ? '2px solid var(--gold)' : '2px solid transparent',
                  background: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
                  marginBottom: -1,
                }}
              >
                <DIcon name={tab.icon} size={15} />
                {tab.label}
                {tab.count > 0 && (
                  <span style={{
                    fontSize: 10, fontWeight: 700, background: 'var(--gold-bg)', color: 'var(--gold)',
                    borderRadius: 99, padding: '1px 7px', lineHeight: '16px',
                  }}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === 'overview' && <OverviewTab analysis={a} t={t} />}
          {activeTab === 'risks' && <RisksTab findings={a.findings || []} t={t} />}
          {activeTab === 'missing' && <MissingTab clauses={a.missing_clauses || []} t={t} />}
          {activeTab === 'recommendations' && <RecommendationsTab recs={a.recommendations || []} t={t} />}
        </>
      )}
    </div>
  );
}

/* ── Mini stat ── */
function MiniStat({ icon, label, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
      <DIcon name={icon} size={16} style={{ color }} />
      <div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>{value}</div>
        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{label}</div>
      </div>
    </div>
  );
}

/* ── Overview Tab: score breakdown ── */
function OverviewTab({ analysis: a, t }) {
  const breakdown = a.score_breakdown || {};
  const items = [
    { label: `${t('contracts.severity.critical')} ${t('contracts.tabs.risks').toLowerCase()}`, value: breakdown.critical_risks, max: -45 },
    { label: `${t('contracts.severity.major')} ${t('contracts.tabs.risks').toLowerCase()}`, value: breakdown.major_risks, max: -32 },
    { label: `${t('contracts.severity.minor')} ${t('contracts.tabs.risks').toLowerCase()}`, value: breakdown.minor_risks, max: -15 },
    { label: `${t('contracts.importance.mandatory')} ${t('contracts.missingClauses').toLowerCase()}`, value: breakdown.missing_mandatory, max: -40 },
    { label: `${t('contracts.importance.recommended')} ${t('contracts.missingClauses').toLowerCase()}`, value: breakdown.missing_recommended, max: -12 },
  ];

  return (
    <DCard style={{ padding: 20 }}>
      <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>Score Breakdown</div>
      {items.map((item, i) => {
        const pct = item.max !== 0 ? Math.abs((item.value || 0) / item.max) * 100 : 0;
        return (
          <div key={i} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{item.label}</span>
              <span style={{ fontWeight: 700, color: item.value < 0 ? 'var(--error)' : 'var(--text-muted)' }}>{item.value || 0}</span>
            </div>
            <div style={{ height: 6, borderRadius: 3, background: 'var(--border)' }}>
              <div style={{
                height: 6, borderRadius: 3, width: `${Math.min(pct, 100)}%`,
                background: pct > 60 ? 'var(--error)' : pct > 30 ? 'var(--gold)' : 'var(--border)',
                transition: 'width .6s ease-out',
              }} />
            </div>
          </div>
        );
      })}
    </DCard>
  );
}

/* ── Risks Tab ── */
function RisksTab({ findings, t }) {
  if (!findings.length) {
    return <EmptyState icon="check" title={t('contracts.findings')} message="Aucun probleme identifie." />;
  }

  const grouped = { critical: [], major: [], minor: [] };
  findings.forEach(f => {
    const s = f.severity || 'minor';
    (grouped[s] || grouped.minor).push(f);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {['critical', 'major', 'minor'].map(severity => {
        const items = grouped[severity];
        if (!items.length) return null;
        const sc = severityColors[severity];
        return items.map((f, i) => (
          <DCard key={f.id || i} style={{ padding: 16, borderLeft: `4px solid ${sc.border}` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Badge variant={severity === 'critical' ? 'error' : severity === 'major' ? 'warning' : 'gold'}>
                {t(`contracts.severity.${severity}`)}
              </Badge>
              <Badge variant="neutral" style={{ fontSize: 10 }}>
                {f.category === 'risk' ? 'Risque' : f.category === 'legal_flaw' ? 'Vice juridique' : 'Ambiguité'}
              </Badge>
            </div>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'var(--text)' }}>{f.title}</div>
            <div style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)', marginBottom: 8 }}>{f.description}</div>
            {f.clause_reference && (
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                <strong>Clause :</strong> {f.clause_reference}
              </div>
            )}
            {f.recommendation && (
              <div style={{ fontSize: 12, padding: '8px 12px', borderRadius: 6, background: 'var(--gold-bg)', color: 'var(--gold-dark)', marginTop: 6 }}>
                <DIcon name="sparkle" size={12} style={{ marginRight: 4 }} />
                {f.recommendation}
              </div>
            )}
          </DCard>
        ));
      })}
    </div>
  );
}

/* ── Missing Clauses Tab ── */
function MissingTab({ clauses, t }) {
  if (!clauses.length) {
    return <EmptyState icon="check" title={t('contracts.missingClauses')} message="Toutes les clauses attendues sont presentes." />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {clauses.map((c, i) => (
        <DCard key={c.id || i} style={{ padding: 16, borderLeft: `4px solid ${c.importance === 'mandatory' ? '#f44336' : '#ff9800'}` }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Badge variant={c.importance === 'mandatory' ? 'error' : 'warning'}>
              {t(`contracts.importance.${c.importance}`)}
            </Badge>
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>{c.clause_name}</div>
          {c.legal_basis && (
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
              <DIcon name="bookmark" size={12} style={{ marginRight: 4 }} />
              {c.legal_basis}
            </div>
          )}
          {c.risk_if_missing && (
            <div style={{ fontSize: 13, lineHeight: 1.5, color: 'var(--text-secondary)' }}>
              <strong>{t('contracts.riskIfMissing')} :</strong> {c.risk_if_missing}
            </div>
          )}
        </DCard>
      ))}
    </div>
  );
}

/* ── Recommendations Tab ── */
function RecommendationsTab({ recs, t }) {
  if (!recs.length) {
    return <EmptyState icon="sparkle" title={t('contracts.tabs.recommendations')} message="Aucune recommandation." />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {recs.map((r, i) => (
        <DCard key={i} style={{ padding: 14, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
          <div style={{
            width: 26, height: 26, borderRadius: '50%', background: 'var(--gold-bg)',
            color: 'var(--gold)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 12, fontWeight: 800, flexShrink: 0,
          }}>
            {i + 1}
          </div>
          <div style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text)' }}>{r}</div>
        </DCard>
      ))}
    </div>
  );
}
