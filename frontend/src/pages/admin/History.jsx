import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { DCard, EmptyState } from '../../components/UI';
import { authFetch } from '../../utils/auth';

const PAGE_SIZE = 25;

export default function History() {
  const { t, i18n } = useTranslation();
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  async function loadHistory() {
    setLoading(true);
    try {
      const res = await authFetch(`/api/v1/chat-history?scope=organization&skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`);
      if (res.ok) {
        const data = await res.json();
        setEntries(data.entries || []);
        setTotal(data.total || 0);
      }
    } catch {
      // History errors are represented by the current empty/list state.
    }
    setLoading(false);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { void Promise.resolve().then(loadHistory); }, [page]);

  return (
    <div style={{ padding: '28px 32px', maxWidth: 1200 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('history.companyTitle')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>{t('history.conversations', { count: total })}</p>

      <DCard noPad>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>{t('common.loading')}</div>
        ) : entries.length === 0 ? (
          <EmptyState icon="clock" title={t('history.noHistory')} desc={t('history.noHistoryDesc')} />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['user', 'question', 'answer', 'sources', 'date'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t(`history.cols.${h}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {entries.map((e, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 500, whiteSpace: 'nowrap' }}>{e.user_name || '-'}</td>
                    <td style={{ padding: '12px 16px', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.question}</td>
                    <td style={{ padding: '12px 16px', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>{(e.answer || '').slice(0, 120)}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{e.sources_count || 0}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 12, whiteSpace: 'nowrap' }}>{new Date(e.created_at).toLocaleDateString(locale, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {total > PAGE_SIZE && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: 16, borderTop: '1px solid var(--border)' }}>
            <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} style={{ padding: '6px 14px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, cursor: 'pointer' }}>{t('common.previous')}</button>
            <span style={{ padding: '6px 14px', fontSize: 12, color: 'var(--text-secondary)' }}>{t('common.pageSimple', { current: page + 1 })}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={(page + 1) * PAGE_SIZE >= total} style={{ padding: '6px 14px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, cursor: 'pointer' }}>{t('common.next')}</button>
          </div>
        )}
      </DCard>
    </div>
  );
}
