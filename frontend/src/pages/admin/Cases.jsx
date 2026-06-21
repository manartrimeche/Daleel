import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, DCard, DButton, StatCard, EmptyState, SkeletonRow, useToast } from '../../components/UI';
import DIcon from '../../components/DIcon';
import { authFetch } from '../../utils/auth';
import { useAuth } from '../../utils/AuthContext';

export default function Cases() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const toast = useToast();
  const [cases, setCases] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  // Création conversationnelle
  const [creating, setCreating] = useState(false);
  const [situation, setSituation] = useState('');
  const [submitting, setSubmitting] = useState(false);

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

  useEffect(() => { void Promise.resolve().then(loadData); }, []);

  const statusVariant = (s) => ({ open: 'info', in_progress: 'warning', under_review: 'gold', resolved: 'success', closed: 'neutral' }[s] || 'neutral');
  const priorityVariant = (p) => ({ critical: 'error', high: 'warning', medium: 'gold', low: 'neutral' }[p] || 'neutral');

  const createdBy = user?.email || user?.full_name || 'user';

  const submitSituation = async () => {
    if (situation.trim().length < 10) {
      toast.warning(t('cases.minChars'));
      return;
    }
    setSubmitting(true);
    try {
      const res = await authFetch('/api/v1/cases/from-conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ situation: situation.trim(), created_by: createdBy }),
      });
      if (res.ok) {
        const turn = await res.json();
        toast.success(t('cases.createSuccess'));
        setSituation('');
        setCreating(false);
        await loadData();
        if (turn.case_id) setSelected({ id: turn.case_id });
      } else {
        toast.error(t('cases.createError'));
      }
    } catch {
      toast.error(t('cases.createError'));
    }
    setSubmitting(false);
  };

  return (
    <div style={{ padding: '44px 32px 28px', maxWidth: 1200 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('cases.title')}</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{t('cases.subtitle')}</p>
        </div>
        <DButton icon="plus" onClick={() => setCreating(v => !v)}>{t('cases.newCase')}</DButton>
      </div>

      {creating && (
        <DCard style={{ marginBottom: 20 }} title={t('cases.describeSituation')}>
          <textarea
            value={situation}
            onChange={e => setSituation(e.target.value)}
            placeholder={t('cases.situationPlaceholder')}
            rows={4}
            style={{ width: '100%', padding: '12px 14px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, fontFamily: 'inherit', background: 'var(--surface)', color: 'var(--text)', outline: 'none', resize: 'vertical', lineHeight: 1.5 }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
            <DButton variant="ghost" onClick={() => { setCreating(false); setSituation(''); }}>{t('common.cancel')}</DButton>
            <DButton onClick={submitSituation} disabled={submitting || situation.trim().length < 10}>
              {submitting ? t('cases.creating') : t('cases.create')}
            </DButton>
          </div>
        </DCard>
      )}

      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 24 }}>
          <StatCard icon="shieldCheck" label={t('cases.open')} value={summary.by_status?.open || 0} />
          <StatCard icon="clock" label={t('cases.inProgress')} value={summary.by_status?.in_progress || 0} variant="warning" />
          <StatCard icon="eye" label={t('cases.underReview')} value={summary.by_status?.under_review || 0} />
          <StatCard icon="check" label={t('cases.resolved')} value={summary.by_status?.resolved || 0} />
          <StatCard icon="alertTriangle" label={t('cases.critical')} value={summary.by_priority?.critical || 0} variant="error" />
        </div>
      )}

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <DCard title={t('cases.allCases')} noPad>
            {loading ? (
              <div style={{ padding: 16 }}><SkeletonRow cols={4} /><SkeletonRow cols={4} /><SkeletonRow cols={4} /></div>
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
                      <tr key={c.id || c._id} onClick={() => setSelected(c)} style={{ borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer', background: (selected?.id || selected?._id) === (c.id || c._id) ? 'var(--surface-hover)' : 'transparent' }}>
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

        {selected && (
          <CaseConversation
            caseId={selected.id || selected._id}
            onClose={() => setSelected(null)}
            statusVariant={statusVariant}
            priorityVariant={priorityVariant}
          />
        )}
      </div>
    </div>
  );
}

// ── Panneau conversation d'un dossier ───────────────────────────────────────────
function CaseConversation({ caseId, onClose, statusVariant, priorityVariant }) {
  const { t } = useTranslation();
  const toast = useToast();
  const [summary, setSummary] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState('');
  const [sending, setSending] = useState(false);
  const threadRef = useRef(null);

  async function load() {
    setLoading(true);
    try {
      const [sumRes, msgRes] = await Promise.allSettled([
        authFetch(`/api/v1/cases/${caseId}/summary`).then(r => r.ok ? r.json() : null),
        authFetch(`/api/v1/cases/${caseId}/messages?limit=200`).then(r => r.ok ? r.json() : null),
      ]);
      setSummary(sumRes.status === 'fulfilled' ? sumRes.value : null);
      setMessages(msgRes.status === 'fulfilled' && msgRes.value ? (msgRes.value.messages || []) : []);
    } catch {
      // Keep the panel visible even if loading fails.
    }
    setLoading(false);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { void Promise.resolve().then(load); }, [caseId]);

  useEffect(() => {
    if (threadRef.current) threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [messages]);

  const sendReply = async () => {
    if (!reply.trim()) return;
    setSending(true);
    const content = reply.trim();
    setReply('');
    try {
      const res = await authFetch(`/api/v1/cases/${caseId}/converse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      if (res.ok) {
        const turn = await res.json();
        setMessages(prev => [...prev, turn.user_message, turn.assistant_message].filter(Boolean));
        if (turn.context) setSummary(prev => prev ? { ...prev, context: turn.context } : prev);
      } else {
        toast.error(t('cases.createError'));
        setReply(content);
      }
    } catch {
      toast.error(t('cases.createError'));
      setReply(content);
    }
    setSending(false);
  };

  const ctx = summary?.context || {};

  return (
    <div style={{ width: 400, flexShrink: 0 }}>
      <DCard noPad>
        {/* En-tête */}
        <div style={{ padding: '16px 18px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-heading)', lineHeight: 1.3 }}>{summary?.title || '…'}</div>
            <button onClick={onClose} aria-label="Close" style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 2, display: 'flex', flexShrink: 0 }}>
              <DIcon name="x" size={16} />
            </button>
          </div>
          {summary && (
            <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
              <Badge variant={statusVariant(summary.status)}>{summary.status}</Badge>
              <Badge variant={priorityVariant(summary.priority)}>{summary.priority}</Badge>
              {ctx.matter_type && <Badge variant="info">{ctx.matter_type}</Badge>}
            </div>
          )}
        </div>

        {loading ? (
          <div style={{ padding: 16 }}><SkeletonRow cols={1} /><SkeletonRow cols={1} /></div>
        ) : (
          <>
            {/* Contexte extrait */}
            {(ctx.next_question || ctx.facts_known?.length > 0 || ctx.facts_missing?.length > 0) && (
              <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-hover)' }}>
                {ctx.next_question && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--gold-dark)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>{t('cases.nextQuestion')}</div>
                    <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.5 }}>{ctx.next_question}</div>
                  </div>
                )}
                {ctx.facts_known?.length > 0 && (
                  <div style={{ marginBottom: ctx.facts_missing?.length > 0 ? 10 : 0 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, marginBottom: 4 }}>{t('cases.knownFacts')} ({ctx.facts_known.length})</div>
                    {ctx.facts_known.map((f, i) => <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '2px 0' }}>• {f}</div>)}
                  </div>
                )}
                {ctx.facts_missing?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--warning)', marginBottom: 4 }}>{t('cases.missingFacts')} ({ctx.facts_missing.length})</div>
                    {ctx.facts_missing.map((f, i) => <div key={i} style={{ fontSize: 12, color: 'var(--text-muted)', padding: '2px 0' }}>• {f}</div>)}
                  </div>
                )}
              </div>
            )}

            {/* Fil de messages */}
            <div ref={threadRef} style={{ maxHeight: 360, overflowY: 'auto', padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {messages.length === 0 ? (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', padding: '12px 0' }}>{t('cases.noMessages')}</div>
              ) : messages.map((m, i) => (
                <div key={m.id || i} style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
                  <div style={{
                    padding: '9px 12px', borderRadius: 12, fontSize: 13, lineHeight: 1.5,
                    background: m.role === 'user' ? 'var(--navy)' : 'var(--surface-active)',
                    color: m.role === 'user' ? '#fff' : 'var(--text)',
                    borderBottomRightRadius: m.role === 'user' ? 3 : 12,
                    borderBottomLeftRadius: m.role === 'user' ? 12 : 3,
                    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  }}>{m.content}</div>
                </div>
              ))}
            </div>

            {/* Saisie réponse */}
            <div style={{ display: 'flex', gap: 8, padding: '12px 14px', borderTop: '1px solid var(--border)' }}>
              <input
                value={reply}
                onChange={e => setReply(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendReply(); } }}
                placeholder={t('cases.askPlaceholder')}
                disabled={sending}
                style={{ flex: 1, minWidth: 0, padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'var(--surface)', color: 'var(--text)', outline: 'none' }}
              />
              <DButton size="sm" icon="send" onClick={sendReply} disabled={sending || !reply.trim()}>
                {sending ? '…' : t('common.send')}
              </DButton>
            </div>
          </>
        )}
      </DCard>
    </div>
  );
}
