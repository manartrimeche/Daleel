import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import DIcon from '../../components/DIcon';
import { Badge, DCard, DButton, EmptyState, SkeletonRow, useConfirm, useToast } from '../../components/UI';
import { authFetch } from '../../utils/auth';

const PAGE_SIZE = 25;

export default function Documents() {
  const { t } = useTranslation();
  const toast = useToast();
  const confirm = useConfirm();
  const [docs, setDocs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  async function loadDocs() {
    setLoading(true);
    try {
      const res = await authFetch(`/api/v1/documents?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`);
      if (res.ok) {
        const data = await res.json();
        setDocs(Array.isArray(data) ? data : data.documents || []);
        setTotal(data.total || (Array.isArray(data) ? data.length : 0));
      }
    } catch {
      // Document listing errors fall back to the existing table state.
    }
    setLoading(false);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { void Promise.resolve().then(loadDocs); }, [page]);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await authFetch('/api/v1/documents/upload', { method: 'POST', body: formData });
      if (res.ok) loadDocs();
    } catch {
      // Upload failures keep the picker reusable.
    }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleDelete = async (id) => {
    const ok = await confirm(t('documents.deleteConfirm'), { variant: 'danger', confirmLabel: t('common.delete') });
    if (!ok) return;
    try {
      await authFetch(`/api/v1/documents/${id}`, { method: 'DELETE' });
      loadDocs();
    } catch {
      // Delete failures leave the list unchanged.
    }
  };

  const [exportingId, setExportingId] = useState(null);

  const handleExport = async (docId, filename) => {
    setExportingId(docId);
    try {
      const res = await authFetch(`/api/v1/documents/${docId}/exigences/export?format=xlsx`);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const safeName = (filename || docId).replace(/\.[^.]+$/, '');
      a.download = `exigences_${safeName}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(t('documents.exportSuccess'));
    } catch {
      toast.error(t('documents.exportError'));
    }
    setExportingId(null);
  };

  const statusVariant = (s) => ({ indexed: 'success', processing: 'warning', pending: 'warning', error: 'error' }[s] || 'neutral');
  const cols = ['name', 'type', 'language', 'pages', 'chunks', 'status', 'actions'];

  return (
    <div style={{ padding: '44px 32px 28px', maxWidth: 1200 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('documents.title')}</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{t('documents.totalDocs', { count: total })}</p>
        </div>
        <div>
          <input type="file" ref={fileRef} onChange={handleUpload} accept=".pdf,.docx,.txt,.json,.jsonl" style={{ display: 'none' }} />
          <DButton icon="upload" disabled={uploading} onClick={() => fileRef.current?.click()}>
            {uploading ? t('documents.uploading') : t('documents.upload')}
          </DButton>
        </div>
      </div>

      <DCard noPad>
        {loading ? (
          <div style={{ padding: 16 }}><SkeletonRow cols={6} /><SkeletonRow cols={6} /><SkeletonRow cols={6} /></div>
        ) : docs.length === 0 ? (
          <EmptyState icon="fileText" title={t('documents.noDocs')} desc={t('documents.noDocsDesc')} />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {cols.map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{t(`documents.cols.${h}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {docs.map(doc => (
                  <tr key={doc.id || doc._id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 500, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <DIcon name="fileText" size={16} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                        {doc.filename || doc.name}
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px' }}><Badge variant="info">{doc.file_type || doc.type || '-'}</Badge></td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{doc.language || '-'}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{doc.total_pages || doc.pages || '-'}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{doc.total_chunks || doc.chunks || '-'}</td>
                    <td style={{ padding: '12px 16px' }}><Badge variant={statusVariant(doc.status)}>{doc.status || 'inconnu'}</Badge></td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <DButton
                          variant="ghost"
                          size="sm"
                          icon="download"
                          disabled={exportingId === (doc.id || doc._id) || doc.status === 'processing'}
                          onClick={() => handleExport(doc.id || doc._id, doc.filename || doc.name)}
                          aria-label={t('documents.exportExigences')}
                          title={t('documents.exportExigences')}
                        >
                          {exportingId === (doc.id || doc._id) ? t('documents.exporting') : t('documents.exportExigences')}
                        </DButton>
                        <DButton variant="danger" size="sm" icon="trash" onClick={() => handleDelete(doc.id || doc._id)} aria-label={t('common.delete')} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {total > PAGE_SIZE && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: 16, borderTop: '1px solid var(--border)' }}>
            <DButton variant="ghost" size="sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>{t('common.previous')}</DButton>
            <span style={{ padding: '6px 14px', fontSize: 12, color: 'var(--text-secondary)' }}>{t('common.page', { current: page + 1, total: Math.ceil(total / PAGE_SIZE) })}</span>
            <DButton variant="ghost" size="sm" onClick={() => setPage(p => p + 1)} disabled={(page + 1) * PAGE_SIZE >= total}>{t('common.next')}</DButton>
          </div>
        )}
      </DCard>
    </div>
  );
}
