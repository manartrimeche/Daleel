import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, DCard, StatCard, EmptyState } from '../../components/UI';
import { authFetch } from '../../utils/auth';

export default function Cases() {
  const { t, i18n } = useTranslation();
  const [cases, setCases] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  async function loadData() {
    setLoading(true);
    try {
      const [casesRes, summaryRes] = await Promise.allSettled([
        authFetch('/api/v1/cases?skip=0&limit=25').then(r => r.json()),
        authFetch('/api/v1/cases/summary').then(r => r.json()),
      ]);
      setCases(casesRes.status === 'fulfilled' ? (Array.isArray(casesRes.value) ? casesRes.value : casesRes.value.cases || []) : []);
      setSummary(summaryRes.status === 'fulfilled' ? summaryRes.value : null);
    } catch {
      // Cases and summary are best-effort dashboard data.
    }
    setLoading(false);
  }

  const loadDetail = async (c) => {
    setSelected(c);
    try {
      const res = await authFetch(`/api/v1/cases/${c.id || c._id}/summary`);
      if (res.ok) setDetail(await res.json());
    } catch {
      // Keep the selected case visible even if the summary fails.
    }
  };

  const statusVariant = (s) => ({ open: 'info', in_progress: 'warning', under_review: 'gold', resolved: 'success', closed: 'neutral' }[s] || 'neutral');
  const priorityVariant = (p) => ({ critical: 'error', high: 'warning', medium: 'gold', low: 'neutral' }[p] || 'neutral');

  useEffect(() => { void Promise.resolve().then(loadData); }, []);

  return (
    <div style={{ padding: '28px 32px', maxWidth: 1200 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('cases.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>{t('cases.subtitle')}</p>

      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 24 }}>
          <StatCard icon="shieldCheck" label={t('cases.open')} value={summary.by_status?.open || 0} />
          <StatCard icon="clock" label={t('cases.inProgress')} value={summary.by_status?.in_progress || 0} variant="warning" />
          <StatCard icon="eye" label={t('cases.underReview')} value={summary.by_status?.under_review || 0} />
          <StatCard icon="check" label={t('cases.resolved')} value={summary.by_status?.resolved || 0} />
          <StatCard icon="alertTriangle" label={t('cases.critical')} value={summary.by_priority?.critical || 0} variant="error" />
        </div>
      )}

      <div style={{ display: 'flex', gap: 20 }}>
        <div style={{ flex: 1 }}>
          <DCard title={t('cases.allCases')} noPad>
            {loading ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>{t('common.loading')}</div>
            ) : cases.length === 0 ? (
              <EmptyState icon="shieldCheck" title={t('cases.noCases')} desc={t('cases.noCasesDesc')} />
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      {['title', 'status', 'priority', 'updated'].map(h => (
                        <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t(`cases.cols.${h}`)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cases.map(c => (
                      <tr key={c.id || c._id} onClick={() => loadDetail(c)} style={{ borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer', background: selected?.id === c.id ? 'var(--surface-hover)' : 'transparent' }}>
                        <td style={{ padding: '12px 16px', fontWeight: 500 }}>{c.title}</td>
                        <td style={{ padding: '12px 16px' }}><Badge variant={statusVariant(c.status)}>{c.status}</Badge></td>
                        <td style={{ padding: '12px 16px' }}><Badge variant={priorityVariant(c.priority)}>{c.priority}</Badge></td>
                        <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 12 }}>{c.updated_at ? new Date(c.updated_at).toLocaleDateString(locale) : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </DCard>
        </div>

        {selected && detail && (
          <div style={{ width: 360, flexShrink: 0 }}>
            <DCard title={selected.title}>
              <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <Badge variant={statusVariant(selected.status)}>{selected.status}</Badge>
                <Badge variant={priorityVariant(selected.priority)}>{selected.priority}</Badge>
              </div>
              {selected.description && <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.5 }}>{selected.description}</p>}
              {detail.facts_known?.length > 0 && (
                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>{t('cases.knownFacts')} ({detail.facts_known.length})</div>
                  {detail.facts_known.map((f, i) => <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '3px 0' }}>- {f}</div>)}
                </div>
              )}
              {detail.facts_missing?.length > 0 && (
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--warning)', marginBottom: 6 }}>{t('cases.missingFacts')} ({detail.facts_missing.length})</div>
                  {detail.facts_missing.map((f, i) => <div key={i} style={{ fontSize: 12, color: 'var(--text-muted)', padding: '3px 0' }}>- {f}</div>)}
                </div>
              )}
            </DCard>
          </div>
        )}
      </div>
    </div>
  );
}
