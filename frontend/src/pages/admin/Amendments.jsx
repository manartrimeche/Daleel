import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import DOMPurify from 'dompurify';
import DIcon from '../../components/DIcon';
import { DCard, Badge, StatCard } from '../../components/UI';
import { authFetch } from '../../utils/auth';

export default function Amendments() {
  const { t } = useTranslation();
  const [step, setStep] = useState('upload');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef();

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await authFetch('/api/v1/documents/upload-amendment', { method: 'POST', body: fd });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        setStep('result');
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || t('amendments.errorProcessing'));
      }
    } catch {
      alert(t('amendments.connectionError'));
    }
    setLoading(false);
  };

  const handleRecalc = async () => {
    if (!result?.document?.loi_id) return;
    setLoading(true);
    try {
      const res = await authFetch(`/api/v1/lois/${result.document.loi_id}/recalculate`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        alert(`Recalcul: ${data.versions_processed || 0} versions, ${data.exigences_extracted || 0} exigences, ${data.actions_extracted || 0} actions`);
      }
    } catch {
      // Recalculation failures keep the uploaded amendment result visible.
    }
    setLoading(false);
  };

  const reset = () => { setStep('upload'); setFile(null); setResult(null); };

  const diff = result?.diff || {};
  const ops = result?.operations || [];

  const opBadge = (type) => {
    const map = { ADD: 'success', REPLACE: 'warning', MODIFY: 'warning', REPEAL: 'error' };
    return <Badge variant={map[type] || 'neutral'}>{type}</Badge>;
  };

  return (
    <div style={{ padding: '28px 32px', maxWidth: 1100 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 4 }}>{t('amendments.title')}</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>{t('amendments.subtitle')}</p>

      {step === 'upload' && (
        <DCard title={t('amendments.importTitle')}>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            {t('amendments.importDesc')}
          </p>

          <div
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={e => { e.preventDefault(); setDragging(false); if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]); }}
            onClick={() => fileRef.current?.click()}
            style={{
              border: `2px dashed ${dragging ? 'var(--gold)' : 'var(--border)'}`,
              borderRadius: 'var(--radius-lg)',
              padding: '32px 24px',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'border-color .2s',
              background: dragging ? 'var(--gold-bg)' : 'transparent',
            }}
          >
            <DIcon name="upload" size={28} style={{ color: 'var(--gold)', marginBottom: 8 }} />
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '8px 0 0' }}
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(t('amendments.dragDrop').replace('<1>', '<span style="color:var(--gold);text-decoration:underline">').replace('</1>', '</span>')) }}
            />
            {file && <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginTop: 8 }}>{file.name}</p>}
            <input ref={fileRef} type="file" accept=".pdf,.docx,.doc,.txt" style={{ display: 'none' }} onChange={e => { if (e.target.files.length) setFile(e.target.files[0]); }} />
          </div>

          <button
            onClick={handleUpload}
            disabled={!file || loading}
            style={{
              marginTop: 16, padding: '10px 20px', borderRadius: 'var(--radius-md)',
              background: file ? 'var(--navy)' : 'var(--surface-active)',
              color: file ? '#fff' : 'var(--text-muted)',
              fontSize: 13, fontWeight: 600, border: 'none', cursor: file ? 'pointer' : 'default',
            }}
          >
            {loading ? t('amendments.processing') : t('amendments.compare')}
          </button>
        </DCard>
      )}

      {step === 'result' && result && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 20 }}>
            <StatCard icon="plus" label={t('amendments.added')} value={diff.added || 0} />
            <StatCard icon="edit" label={t('amendments.modified')} value={diff.modified || 0} variant="warning" />
            <StatCard icon="trash" label={t('amendments.removed')} value={diff.removed || 0} variant="error" />
            <StatCard icon="check" label={t('amendments.unchanged')} value={diff.unchanged || 0} />
            <StatCard icon="bell" label={t('amendments.notified')} value={result.notifications_sent || 0} />
          </div>

          <DCard title={t('amendments.resultTitle')} style={{ marginBottom: 20 }}>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>{result.message}</p>

            {(result.notifications_sent || 0) > 0 && (
              <p style={{ fontSize: 12, color: 'var(--gold)', marginBottom: 8 }}>
                <DIcon name="bell" size={13} style={{ marginRight: 4 }} />
                {t('amendments.notifiedProfiles', { count: result.notifications_sent })}
              </p>
            )}

            {result.old_document_id ? (
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('amendments.oldDocReplaced').replace('<1>', '').replace('</1>', '').replace('{{id}}', result.old_document_id)}</p>
            ) : (
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('amendments.newDocCreated')}</p>
            )}
          </DCard>

          {ops.length > 0 && (
            <DCard title={t('amendments.operations', { count: ops.length })} noPad style={{ marginBottom: 20 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {['operation', 'article', 'details'].map(h => (
                      <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t(`amendments.cols.${h}`)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ops.map((op, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '10px 16px' }}>{opBadge(op.type)}</td>
                      <td style={{ padding: '10px 16px' }}><code style={{ background: 'var(--surface-active)', padding: '1px 6px', borderRadius: 4, fontSize: 12 }}>{op.article_key}</code></td>
                      <td style={{ padding: '10px 16px', fontSize: 12, color: 'var(--text-secondary)' }}>Art. {op.article_number}{op.new_version_id ? ` ${t('amendments.newVersion')}` : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </DCard>
          )}

          <div style={{ display: 'flex', gap: 10 }}>
            {result.document?.loi_id && (
              <button onClick={handleRecalc} disabled={loading} style={{ padding: '10px 18px', borderRadius: 'var(--radius-md)', background: 'var(--navy)', color: '#fff', fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer' }}>
                {loading ? t('amendments.recalculating') : t('amendments.recalculate')}
              </button>
            )}
            <button onClick={reset} style={{ padding: '10px 18px', borderRadius: 'var(--radius-md)', background: 'var(--surface-active)', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600, border: '1px solid var(--border)', cursor: 'pointer' }}>
              {t('amendments.newAmendment')}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
