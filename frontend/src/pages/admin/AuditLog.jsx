import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { DCard, DButton, EmptyState, SkeletonRow, Badge, FilterChip } from '../../components/UI';
import { authFetch } from '../../utils/auth';

const PAGE_SIZE = 25;

// Types d'événements émis par audit_service.py (trail append-only).
const EVENT_TYPES = [
  'document_classified',
  'amendment_extracted',
  'amendment_applied',
  'version_superseded',
  'article_repealed',
  'recalculation_done',
];

// Mappe chaque type d'événement vers une variante de Badge.
const EVENT_VARIANT = {
  document_classified: 'info',
  amendment_extracted: 'info',
  amendment_applied: 'gold',
  version_superseded: 'warning',
  article_repealed: 'error',
  recalculation_done: 'success',
};

export default function AuditLog() {
  const { t, i18n } = useTranslation();
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [eventType, setEventType] = useState('');
  const [loading, setLoading] = useState(true);
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  async function loadLogs() {
    setLoading(true);
    try {
      const params = new URLSearchParams({ skip: String(page * PAGE_SIZE), limit: String(PAGE_SIZE) });
      if (eventType) params.set('event_type', eventType);
      const res = await authFetch(`/api/v1/audit-logs?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
        setTotal(data.total || 0);
      }
    } catch {
      // Les erreurs de chargement sont reflétées par l'état liste/vide courant.
    }
    setLoading(false);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { void Promise.resolve().then(loadLogs); }, [page, eventType]);

  const onFilter = (value) => {
    setEventType(value);
    setPage(0);
  };

  const eventLabel = (type) => t(`audit.events.${type}`, { defaultValue: type });

  return (
    <div style={{ padding: '44px 32px 28px', maxWidth: 1200 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('audit.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>{t('audit.subtitle', { count: total })}</p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
        <FilterChip label={t('audit.allEvents')} active={eventType === ''} onClick={() => onFilter('')} />
        {EVENT_TYPES.map(type => (
          <FilterChip key={type} label={eventLabel(type)} active={eventType === type} onClick={() => onFilter(type)} />
        ))}
      </div>

      <DCard noPad>
        {loading ? (
          <div style={{ padding: 16 }}><SkeletonRow cols={5} /><SkeletonRow cols={5} /><SkeletonRow cols={5} /></div>
        ) : logs.length === 0 ? (
          <EmptyState icon="archive" title={t('audit.noLogs')} desc={t('audit.noLogsDesc')} />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['date', 'event', 'actor', 'reference', 'proof', 'confidence'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t(`audit.cols.${h}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 12, whiteSpace: 'nowrap' }}>{new Date(log.created_at).toLocaleDateString(locale, { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
                    <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                      <Badge variant={EVENT_VARIANT[log.event_type] || 'neutral'}>{eventLabel(log.event_type)}</Badge>
                    </td>
                    <td style={{ padding: '12px 16px', fontWeight: 500, whiteSpace: 'nowrap' }}>{log.actor || 'system'}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{log.legal_reference || '-'}</td>
                    <td style={{ padding: '12px 16px', maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-muted)' }} title={log.proof_extract || ''}>{log.proof_extract || '-'}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{Math.round((log.confidence ?? 1) * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {total > PAGE_SIZE && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: 16, borderTop: '1px solid var(--border)' }}>
            <DButton variant="ghost" size="sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>{t('common.previous')}</DButton>
            <span style={{ padding: '6px 14px', fontSize: 12, color: 'var(--text-secondary)' }}>{t('common.pageSimple', { current: page + 1 })}</span>
            <DButton variant="ghost" size="sm" onClick={() => setPage(p => p + 1)} disabled={(page + 1) * PAGE_SIZE >= total}>{t('common.next')}</DButton>
          </div>
        )}
      </DCard>
    </div>
  );
}
