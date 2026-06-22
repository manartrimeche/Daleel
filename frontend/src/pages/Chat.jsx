import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import DIcon from '../components/DIcon';
import { Badge, DButton, useToast } from '../components/UI';
import { authFetch } from '../utils/auth';
import { isArabic, isRtlText, detectMessageLanguage, getAdaptiveRetrievalSettings, stripMarkdown, formatFileSize, getTime } from '../utils/helpers';

const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'webp'];
const CONTRACT_EXTENSIONS = ['pdf', 'docx', 'doc'];
const HISTORY_ACTION_MENU_WIDTH = 150;
const HISTORY_ACTION_MENU_HEIGHT = 78;
const HISTORY_ACTION_MENU_GAP = 8;

const scoreColors = {
  excellent: { bg: 'var(--score-excellent-bg)', text: 'var(--score-excellent)', ring: 'var(--score-excellent)' },
  bon: { bg: 'var(--score-bon-bg)', text: 'var(--score-bon)', ring: 'var(--score-bon)' },
  attention: { bg: 'var(--score-attention-bg)', text: 'var(--score-attention)', ring: 'var(--score-attention)' },
  critique: { bg: 'var(--score-critique-bg)', text: 'var(--score-critique)', ring: 'var(--score-critique)' },
};

const severityColors = {
  critical: { bg: 'var(--severity-critical-bg)', text: 'var(--severity-critical)', border: 'var(--severity-critical)' },
  major: { bg: 'var(--severity-major-bg)', text: 'var(--severity-major)', border: 'var(--severity-major)' },
  minor: { bg: 'var(--severity-minor-bg)', text: 'var(--severity-minor)', border: 'var(--severity-minor)' },
};

function getSourceDisplayTitle(source, fallback) {
  const title = source?.document_title || source?.title || source?.filename || fallback;
  return String(title || fallback).trim() || fallback;
}

function normalizeSectionTitle(text) {
  return String(text || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/^[^\p{L}\p{N}]+/u, '')
    .trim()
    .toLowerCase();
}

function isBotSectionTitle(line) {
  const trimmed = String(line || '').trim();
  if (!trimmed || trimmed.length > 90) return false;
  if (/\[Source\s+\d+\]/i.test(trimmed)) return false;

  const normalized = normalizeSectionTitle(trimmed);
  const words = normalized.split(/\s+/).filter(Boolean);
  const hasSentenceEnding = /[.;,]$/.test(trimmed);
  const startsWithIcon = /^[^\p{L}\p{N}\s]/u.test(trimmed);
  const sectionKeywords = [
    'a retenir',
    'analyse',
    'application pratique',
    'articles',
    'base legale',
    'cadre juridique',
    'ce que',
    'conclusion',
    'conditions',
    'conseil',
    'conseils',
    'demarches',
    'delais',
    'diagnostic',
    'dispositions',
    'documents',
    'en pratique',
    'etapes',
    'exemples',
    'limites',
    'obligations',
    'plan daction',
    'points',
    'preuves',
    'procedure',
    'recommandation',
    'recommandations',
    'reponse courte',
    'resume',
    'risques',
    'sanctions',
    'sources',
    'synthese',
    'verification',
  ];

  return (
    sectionKeywords.some(keyword => normalized.startsWith(keyword)) ||
    (startsWithIcon && words.length <= 10 && !hasSentenceEnding) ||
    (words.length <= 6 && !hasSentenceEnding && /^[A-ZÀ-ÖØ-Þ]/.test(trimmed))
  );
}

function isBotLegalReferenceTitle(line) {
  const trimmed = String(line || '').trim();
  if (!trimmed || trimmed.length > 140) return false;
  if (/\[Source\s+\d+\]/i.test(trimmed)) return false;

  const normalized = normalizeSectionTitle(trimmed);
  return /^(article|art)\s+\d+([^\d].*)?$/.test(normalized) ||
    /^(loi|loi organique|decret|decret-loi|arrete|circulaire)\b/.test(normalized);
}

function renderLineWithSourceTitles(line, sources, keyPrefix) {
  const sourcePattern = /\[Source\s+(\d+)\]/gi;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = sourcePattern.exec(line)) !== null) {
    const sourceIndex = Number(match[1]) - 1;
    const source = sources[sourceIndex];

    if (!source) continue;

    if (match.index > lastIndex) {
      parts.push(line.slice(lastIndex, match.index));
    }

    const fallback = match[0];
    const title = getSourceDisplayTitle(source, fallback);
    parts.push(
      <span
        key={`${keyPrefix}-${match.index}-${match[1]}`}
        title={fallback}
        style={{
          display: 'inline-flex',
          maxWidth: '100%',
          verticalAlign: 'baseline',
          padding: '1px 7px',
          borderRadius: 999,
          background: 'var(--gold-bg)',
          border: '1px solid var(--gold-10)',
          color: 'var(--gold-dark)',
          fontSize: 13.5,
          fontWeight: 800,
          lineHeight: 1.35,
          overflowWrap: 'anywhere',
          whiteSpace: 'normal',
        }}
      >
        {title}
      </span>
    );
    lastIndex = sourcePattern.lastIndex;
  }

  if (lastIndex === 0) return line;
  if (lastIndex < line.length) parts.push(line.slice(lastIndex));
  return parts;
}

function renderBotTextWithSourceTitles(text, sources = []) {
  const plainText = stripMarkdown(text);
  const lines = plainText.split('\n').filter(line => !isBotLegalReferenceTitle(line));

  return lines.flatMap((line, index) => {
    const renderedLine = renderLineWithSourceTitles(line, sources, `line-${index}`);
    const content = isBotSectionTitle(line) ? (
      <span
        key={`section-title-${index}`}
        style={{
          display: 'block',
          margin: index === 0 ? '0 0 4px' : '10px 0 4px',
          color: 'var(--text)',
          fontSize: 15.5,
          fontWeight: 800,
          lineHeight: 1.45,
        }}
      >
        {renderedLine}
      </span>
    ) : renderedLine;

    return index < lines.length - 1 ? [content, '\n'] : [content];
  });
}

function SourceList({ sources = [], t }) {
  const [open, setOpen] = useState(false);
  if (!Array.isArray(sources) || sources.length === 0) return null;
  const visibleSources = sources.slice(0, 6);

  return (
    <div
      style={{
        marginTop: 8,
        padding: 0,
        borderRadius: 10,
        overflow: 'hidden',
        border: open ? '1px solid rgba(184,147,90,0.24)' : 'none',
      }}
    >
      <button
        type="button"
        onClick={() => setOpen(value => !value)}
        aria-expanded={open}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 7,
          minHeight: 30,
          padding: '6px 10px',
          borderRadius: 999,
          background: open ? 'var(--gold-bg)' : 'var(--surface)',
          border: '1px solid rgba(184,147,90,0.28)',
          color: 'var(--gold-dark)',
          fontSize: 11,
          fontWeight: 800,
          cursor: 'pointer',
          boxShadow: open ? 'none' : '0 4px 10px rgba(27,43,66,0.06)',
        }}
      >
        <DIcon name="bookmark" size={13} />
        {t('chat.sources')}
        <span style={{ color: 'var(--text-secondary)', fontWeight: 700 }}>
          {sources.length}
        </span>
        <DIcon name="chevronDown" size={13} style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform .15s ease' }} />
      </button>

      {open && (
        <div
          style={{
            marginTop: 7,
            padding: '9px 10px',
            borderRadius: 10,
            background: 'var(--gold-bg)',
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
          }}
        >
        {visibleSources.map((source, index) => {
          const title = getSourceDisplayTitle(source, `Source ${index + 1}`);
          const meta = [
            source.section,
            source.page_number ? `p. ${source.page_number}` : null,
            source.language,
          ].filter(Boolean).join(' · ');

          return (
            <div
              key={`${source.document_id || title}-${index}`}
              style={{
                display: 'grid',
                gridTemplateColumns: '22px minmax(0, 1fr)',
                gap: 8,
                alignItems: 'start',
                minWidth: 0,
              }}
            >
              <span
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 6,
                  background: 'rgba(184,147,90,0.18)',
                  color: 'var(--gold-dark)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 11,
                  fontWeight: 800,
                  flexShrink: 0,
                }}
              >
                {index + 1}
              </span>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)', lineHeight: 1.25, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {title}
                </div>
                {meta && (
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {meta}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {sources.length > visibleSources.length && (
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', paddingLeft: 30 }}>
            +{sources.length - visibleSources.length}
          </div>
        )}
        </div>
      )}
    </div>
  );
}

function ScoreRing({ score, category, size = 90 }) {
  const colors = scoreColors[category] || scoreColors.attention;
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={7} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={colors.ring} strokeWidth={7}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease-out' }} />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontSize: size * 0.28, fontWeight: 800, color: colors.text, lineHeight: 1 }}>{score}</span>
        <span style={{ fontSize: 9, color: colors.text, fontWeight: 600 }}>/100</span>
      </div>
    </div>
  );
}

const critColors = {
  Critique:   { bg: '#FFC7CE', text: '#9C0006', border: '#F4A5AE' },
  Importante: { bg: '#FFEB9C', text: '#9C6500', border: '#F0D060' },
  Secondaire: { bg: '#C6EFCE', text: '#006100', border: '#8ED09E' },
};
const typeIcons = { Obligation: 'shieldCheck', Sanction: 'alertTriangle', Condition: 'filter', Interdiction: 'x' };

function ExigencesMessage({ data, t, onExport }) {
  const [expanded, setExpanded] = useState(null);
  if (!data || !data.exigences) return null;
  const { document_name, exigences, by_type, by_level, total } = data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: '100%' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Badge variant="gold">{document_name}</Badge>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{total} {t('chat.exigences.total')}</span>
      </div>

      {/* Level summary pills */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {Object.entries(by_level || {}).map(([level, count]) => {
          const c = critColors[level] || critColors.Secondaire;
          return count > 0 ? (
            <span key={level} style={{ padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: c.bg, color: c.text, border: `1px solid ${c.border}` }}>
              {level} : {count}
            </span>
          ) : null;
        })}
      </div>

      {/* Type breakdown */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {Object.entries(by_type || {}).map(([type, count]) => (
          <span key={type} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 6, fontSize: 11, background: 'var(--surface-active)', color: 'var(--text-secondary)' }}>
            <DIcon name={typeIcons[type] || 'file'} size={12} />
            {type} ({count})
          </span>
        ))}
      </div>

      {/* Exigences table */}
      <div style={{ overflowX: 'auto', borderRadius: 8, border: '1px solid var(--border)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ background: 'var(--navy)', color: '#fff' }}>
              <th style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 600, fontSize: 11 }}>{t('chat.exigences.article')}</th>
              <th style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 600, fontSize: 11 }}>{t('chat.exigences.type')}</th>
              <th style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 600, fontSize: 11, minWidth: 200 }}>{t('chat.exigences.text')}</th>
              <th style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600, fontSize: 11 }}>{t('chat.exigences.criticality')}</th>
              <th style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600, fontSize: 11 }}>{t('chat.exigences.score')}</th>
            </tr>
          </thead>
          <tbody>
            {exigences.slice(0, expanded ? 999 : 10).map((e, i) => {
              const c = critColors[e.level] || {};
              return (
                <tr key={i} style={{ background: c.bg || 'transparent', borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 10px', fontWeight: 500, whiteSpace: 'nowrap', color: c.text || 'var(--text)' }}>{e.article || '-'}</td>
                  <td style={{ padding: '8px 10px', whiteSpace: 'nowrap' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: c.text || 'var(--text-secondary)' }}>
                      <DIcon name={typeIcons[e.type] || 'file'} size={12} />
                      {e.type}
                    </span>
                  </td>
                  <td style={{ padding: '8px 10px', color: c.text || 'var(--text)', lineHeight: 1.4, maxWidth: 350 }}>{e.text?.length > 150 ? e.text.slice(0, 150) + '...' : e.text}</td>
                  <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                    <span style={{ padding: '2px 10px', borderRadius: 12, fontSize: 11, fontWeight: 700, background: c.bg, color: c.text, border: `1px solid ${c.border || 'transparent'}` }}>
                      {e.level}
                    </span>
                  </td>
                  <td style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 700, fontFamily: 'var(--font-mono)', color: c.text || 'var(--text)' }}>{e.score}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Show more / less */}
      {exigences.length > 10 && (
        <button
          onClick={() => setExpanded(!expanded)}
          style={{ alignSelf: 'center', padding: '6px 16px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface)', cursor: 'pointer', fontSize: 12, color: 'var(--text-secondary)' }}
        >
          {expanded ? t('chat.exigences.showLess') : t('chat.exigences.showAll', { count: exigences.length })}
        </button>
      )}

      {/* Export button */}
      {onExport && (
        <button
          onClick={onExport}
          style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 8, border: '1px solid var(--gold)', background: 'var(--gold-bg)', cursor: 'pointer', fontSize: 12, fontWeight: 600, color: 'var(--gold)' }}
        >
          <DIcon name="download" size={14} />
          {t('chat.exigences.exportExcel')}
        </button>
      )}
    </div>
  );
}

function ContractAnalysisMessage({ data, t }) {
  const { action, analysis: a } = data;
  if (!a) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: '100%' }}>
      {/* Header: type + parties */}
      {a.contract_type_label && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <Badge variant="gold">{a.contract_type_label}</Badge>
          {(a.parties || []).length > 0 && (
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {a.parties.join(' — ')}
            </span>
          )}
        </div>
      )}

      {/* Summary */}
      {a.summary && (
        <div style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)' }}>
          {a.summary}
        </div>
      )}

      {/* Score (full analysis only) */}
      {action === 'full' && a.score != null && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 16, padding: 14,
          borderRadius: 10, background: scoreColors[a.score_category]?.bg || 'var(--surface)',
          border: `1px solid ${scoreColors[a.score_category]?.ring || 'var(--border)'}20`,
        }}>
          <ScoreRing score={a.score} category={a.score_category} />
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: scoreColors[a.score_category]?.text }}>
              {t(`contractChat.score`)}: {a.score}/100
            </div>
            <Badge variant={a.score_category === 'excellent' ? 'success' : a.score_category === 'bon' ? 'info' : a.score_category === 'attention' ? 'warning' : 'error'}
              style={{ marginTop: 4 }}>
              {t(`contractChat.${a.score_category}`)}
            </Badge>
            {a.score_breakdown && (
              <div style={{ display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
                {a.findings_summary && (
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {a.findings_summary.total} {t('contractChat.findings').toLowerCase()}
                  </span>
                )}
                {a.missing_clauses && (
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {a.missing_clauses.length} {t('contractChat.missingClauses').toLowerCase()}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Findings (risks) */}
      {(action === 'risks' || action === 'full') && a.findings && a.findings.length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <DIcon name="alertTriangle" size={14} style={{ color: 'var(--error)' }} />
            {t('contractChat.findings')} ({a.findings_summary?.total || a.findings.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {a.findings.map((f, i) => {
              const sc = severityColors[f.severity] || severityColors.minor;
              return (
                <div key={f.id || i} style={{
                  padding: '10px 12px', borderRadius: 8,
                  background: sc.bg, borderLeft: `3px solid ${sc.border}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <Badge variant={f.severity === 'critical' ? 'error' : f.severity === 'major' ? 'warning' : 'gold'} style={{ fontSize: 10 }}>
                      {t(`contractChat.severity.${f.severity}`)}
                    </Badge>
                    <span style={{ fontSize: 12, fontWeight: 700, color: sc.text }}>{f.title}</span>
                  </div>
                  <div style={{ fontSize: 12, lineHeight: 1.5, color: 'var(--text-secondary)' }}>{f.description}</div>
                  {f.recommendation && (
                    <div style={{ fontSize: 11, marginTop: 6, padding: '6px 8px', borderRadius: 6, background: 'rgba(184,147,90,0.1)', color: 'var(--gold-dark)' }}>
                      <DIcon name="sparkle" size={11} style={{ marginRight: 4 }} />
                      {f.recommendation}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
      {(action === 'risks' || action === 'full') && a.findings && a.findings.length === 0 && (
        <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '8px 12px', background: 'var(--success-bg)', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <DIcon name="check" size={14} style={{ color: 'var(--success)' }} />
          {t('contractChat.noFindings')}
        </div>
      )}

      {/* Missing clauses */}
      {(action === 'missing_clauses' || action === 'full') && a.missing_clauses && a.missing_clauses.length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <DIcon name="search" size={14} style={{ color: 'var(--gold)' }} />
            {t('contractChat.missingClauses')} ({a.missing_clauses.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {a.missing_clauses.map((c, i) => (
              <div key={c.id || i} style={{
                padding: '10px 12px', borderRadius: 8,
                background: c.importance === 'mandatory' ? 'var(--error-bg)' : 'var(--warning-bg)',
                borderLeft: `3px solid ${c.importance === 'mandatory' ? 'var(--error)' : 'var(--warning)'}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <Badge variant={c.importance === 'mandatory' ? 'error' : 'warning'} style={{ fontSize: 10 }}>
                    {t(`contractChat.importance.${c.importance}`)}
                  </Badge>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)' }}>{c.clause_name}</span>
                </div>
                {c.legal_basis && (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>
                    <DIcon name="bookmark" size={11} style={{ marginRight: 3 }} /> {c.legal_basis}
                  </div>
                )}
                {c.risk_if_missing && (
                  <div style={{ fontSize: 12, lineHeight: 1.5, color: 'var(--text-secondary)' }}>
                    {c.risk_if_missing}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      {(action === 'missing_clauses' || action === 'full') && a.missing_clauses && a.missing_clauses.length === 0 && (
        <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '8px 12px', background: 'var(--success-bg)', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <DIcon name="check" size={14} style={{ color: 'var(--success)' }} />
          {t('contractChat.noMissing')}
        </div>
      )}

      {/* Recommendations */}
      {(action === 'recommendations' || action === 'full') && a.recommendations && a.recommendations.length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <DIcon name="sparkle" size={14} style={{ color: 'var(--gold)' }} />
            {t('contractChat.recommendations')} ({a.recommendations.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {a.recommendations.map((r, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: 8,
                padding: '8px 10px', borderRadius: 8, background: 'var(--gold-bg)',
              }}>
                <span style={{
                  width: 20, height: 20, borderRadius: '50%', background: 'var(--gold)',
                  color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 10, fontWeight: 800, flexShrink: 0, marginTop: 1,
                }}>{i + 1}</span>
                <span style={{ fontSize: 12, lineHeight: 1.5, color: 'var(--text)' }}>{r}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Chat() {
  const { t, i18n } = useTranslation();
  const toast = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  const [history, setHistory] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showWelcome, setShowWelcome] = useState(true);
  const [conversationId, setConversationId] = useState(null);
  const [openMenuId, setOpenMenuId] = useState(null);
  const [menuPosition, setMenuPosition] = useState(null);
  const [renamingId, setRenamingId] = useState(null);
  const [renameDraft, setRenameDraft] = useState('');
  const [showDocPicker, setShowDocPicker] = useState(false);
  const [docList, setDocList] = useState([]);
  const [loadingExigences, setLoadingExigences] = useState(false);

  const chatRef = useRef(null);
  const historyScrollRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const conversationHistory = useRef([]);
  const skipRenameBlurRef = useRef(false);
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';
  const requestedConversationId = searchParams.get('conversation');
  const requestedScope = searchParams.get('scope') === 'organization' ? 'organization' : 'personal';

  const isContractFile = attachedFile && CONTRACT_EXTENSIONS.includes(
    attachedFile.name.split('.').pop().toLowerCase()
  );

  const getChatErrorMessage = (err) => {
    if (err?.message === 'Session expired') return t('chat.sessionExpired');
    return `${t('chat.connectionError')} ${err?.message || t('chat.processingError')}`;
  };

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (requestedConversationId && requestedConversationId !== conversationId) {
      loadConversationById(requestedConversationId, requestedScope);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestedConversationId, requestedScope]);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    if (!openMenuId) return;
    const close = () => {
      setOpenMenuId(null);
      setMenuPosition(null);
    };
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [openMenuId]);

  const loadHistory = async () => {
    try {
      const res = await authFetch('/api/v1/chat-history?limit=30');
      if (res.ok) {
        const data = await res.json();
        setHistory(data.entries || []);
      }
    } catch {
      // optional
    }
  };

  const conversationTitle = (entry) => entry.conversation_title || entry.title || entry.question || t('chat.untitledConversation');

  const buildConversationMessages = (msgs) => {
    conversationHistory.current = [];
    const uiMessages = [];
    for (const m of msgs) {
      const time = m.created_at
        ? new Date(m.created_at).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })
        : '';
      uiMessages.push({ role: 'user', text: m.question, time });
      uiMessages.push({ role: 'bot', text: m.answer, sources: [], time });
      conversationHistory.current.push(
        { role: 'user', content: m.question },
        { role: 'assistant', content: m.answer },
      );
    }
    if (conversationHistory.current.length > 20) {
      conversationHistory.current = conversationHistory.current.slice(-20);
    }
    return uiMessages;
  };

  const loadConversationById = async (id, scope = 'personal') => {
    if (!id) return false;
    setShowWelcome(false);
    setConversationId(id);
    try {
      const suffix = scope === 'organization' ? '?scope=organization' : '';
      const res = await authFetch(`/api/v1/chat-history/conversation/${encodeURIComponent(id)}${suffix}`);
      if (res.ok) {
        const data = await res.json();
        const msgs = data.messages || [];
        setMessages(buildConversationMessages(msgs));
        return true;
      }
    } catch {
      // Keep the current chat state if the conversation cannot be loaded.
    }
    return false;
  };

  const loadConversation = async (entry) => {
    setOpenMenuId(null);
    setMenuPosition(null);
    setShowWelcome(false);

    if (entry.conversation_id) {
      setSearchParams({ conversation: entry.conversation_id });
      const loaded = await loadConversationById(entry.conversation_id);
      if (loaded) return;
    }

    setConversationId(null);
    conversationHistory.current = [
      { role: 'user', content: entry.question },
      { role: 'assistant', content: entry.answer },
    ];
    setMessages([
      { role: 'user', text: entry.question, time: new Date(entry.created_at).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' }) },
      { role: 'bot', text: entry.answer, sources: [], time: new Date(entry.created_at).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' }) },
    ]);
  };

  const newChat = () => {
    setOpenMenuId(null);
    setMenuPosition(null);
    conversationHistory.current = [];
    setConversationId(null);
    setMessages([]);
    setShowWelcome(true);
    setSearchParams({});
  };

  const toggleConversationMenu = (entry, event) => {
    event.stopPropagation();
    if (openMenuId === entry.conversation_id) {
      setOpenMenuId(null);
      setMenuPosition(null);
      return;
    }

    const buttonRect = event.currentTarget.getBoundingClientRect();
    const spaceBelow = window.innerHeight - buttonRect.bottom;
    const openUp = spaceBelow < HISTORY_ACTION_MENU_HEIGHT + HISTORY_ACTION_MENU_GAP && buttonRect.top > spaceBelow;
    const top = openUp
      ? Math.max(HISTORY_ACTION_MENU_GAP, buttonRect.top - HISTORY_ACTION_MENU_HEIGHT - HISTORY_ACTION_MENU_GAP)
      : Math.min(
        window.innerHeight - HISTORY_ACTION_MENU_HEIGHT - HISTORY_ACTION_MENU_GAP,
        buttonRect.bottom + HISTORY_ACTION_MENU_GAP,
      );
    const left = Math.min(
      window.innerWidth - HISTORY_ACTION_MENU_WIDTH - HISTORY_ACTION_MENU_GAP,
      Math.max(HISTORY_ACTION_MENU_GAP, buttonRect.right - HISTORY_ACTION_MENU_WIDTH),
    );

    setMenuPosition({ top, left });
    setOpenMenuId(entry.conversation_id);
  };

  const archiveConversation = async (entry) => {
    if (!entry.conversation_id) return;
    setOpenMenuId(null);
    setMenuPosition(null);
    const res = await authFetch(`/api/v1/chat-history/conversation/${encodeURIComponent(entry.conversation_id)}/archive`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ archived: true }),
    });
    if (res.ok) {
      await loadHistory();
      if (conversationId === entry.conversation_id) newChat();
    }
  };

  const renameConversation = (entry) => {
    if (!entry.conversation_id) return;
    setOpenMenuId(null);
    setMenuPosition(null);
    skipRenameBlurRef.current = false;
    setRenameDraft(conversationTitle(entry));
    setRenamingId(entry.conversation_id);
  };

  const cancelRename = () => {
    skipRenameBlurRef.current = true;
    setRenamingId(null);
    setRenameDraft('');
  };

  const commitRename = async (entry) => {
    if (skipRenameBlurRef.current) {
      skipRenameBlurRef.current = false;
      return;
    }
    const title = renameDraft.trim();
    const current = conversationTitle(entry);
    setRenamingId(null);
    if (!title || title === current) return;
    const res = await authFetch(`/api/v1/chat-history/conversation/${encodeURIComponent(entry.conversation_id)}/rename`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title.slice(0, 120) }),
    });
    if (res.ok) loadHistory();
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      toast.error(t('chat.unsupportedFormat'));
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      toast.error(t('chat.fileTooLarge'));
      return;
    }
    setAttachedFile(file);
  };

  // ── Exigences picker ──

  const openExigencesPicker = async () => {
    try {
      const res = await authFetch('/api/v1/documents?skip=0&limit=50');
      if (res.ok) {
        const data = await res.json();
        const docs = (Array.isArray(data) ? data : data.documents || []).filter(d => d.status === 'ready');
        setDocList(docs);
        setShowDocPicker(true);
      }
    } catch { /* ignore */ }
  };

  const loadExigences = async (doc) => {
    setShowDocPicker(false);
    setLoadingExigences(true);
    setShowWelcome(false);

    setMessages(prev => [...prev, {
      role: 'user',
      text: `📋 ${t('chat.exigences.requestPrefix')} « ${doc.filename} »`,
      time: getTime(),
    }]);

    try {
      const res = await authFetch(`/api/v1/documents/${doc.id}/exigences`);
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();

      // Compute criticality for display (inline, using the type as proxy)
      const typeLabels = { obligation: 'Obligation', sanction: 'Sanction', condition: 'Condition', prohibition: 'Interdiction' };
      const baseScores = { sanction: 0.85, interdiction: 0.70, obligation: 0.65, condition: 0.35 };
      const levelOf = (s) => s >= 0.75 ? 'Critique' : s >= 0.50 ? 'Importante' : 'Secondaire';

      const exigences = (data.exigences || []).map(e => {
        const score = baseScores[e.exigence_type] || 0.50;
        return {
          article: e.article_reference || '',
          type: typeLabels[e.exigence_type] || e.exigence_type,
          text: e.text,
          confidence: e.confidence_score,
          score: score,
          level: levelOf(score),
        };
      });

      const byLevel = { Critique: 0, Importante: 0, Secondaire: 0 };
      const byType = {};
      exigences.forEach(e => {
        byLevel[e.level] = (byLevel[e.level] || 0) + 1;
        byType[e.type] = (byType[e.type] || 0) + 1;
      });

      setMessages(prev => [...prev, {
        role: 'bot',
        text: '',
        time: getTime(),
        exigencesData: {
          document_id: doc.id,
          document_name: doc.filename,
          exigences,
          by_type: byType,
          by_level: byLevel,
          total: exigences.length,
        },
      }]);
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: t('chat.exigences.error'), time: getTime() }]);
    }
    setLoadingExigences(false);
  };

  const handleExportFromChat = async (docId) => {
    try {
      const res = await authFetch(`/api/v1/documents/${docId}/exigences/export?format=xlsx`);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `exigences_${docId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(t('documents.exportSuccess'));
    } catch {
      toast.error(t('documents.exportError'));
    }
  };

  const matchExigences = async (queryText) => {
    const text = queryText || input.trim();
    if (!text || loadingExigences) return;

    setLoadingExigences(true);
    setShowWelcome(false);
    setInput('');

    setMessages(prev => [...prev, {
      role: 'user',
      text: `🔍 ${t('chat.exigences.matchPrefix')} « ${text.length > 80 ? text.slice(0, 80) + '...' : text} »`,
      time: getTime(),
    }]);

    try {
      const res = await authFetch('/api/v1/exigences/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, top_k: 15 }),
      });
      if (!res.ok) throw new Error('Match failed');
      const data = await res.json();

      const byLevel = { Critique: 0, Importante: 0, Secondaire: 0 };
      const byType = {};
      const exigences = (data.exigences || []).map(e => {
        const lvl = e.criticality_level || 'Secondaire';
        byLevel[lvl] = (byLevel[lvl] || 0) + 1;
        byType[e.type] = (byType[e.type] || 0) + 1;
        return {
          article: e.article,
          type: e.type,
          text: e.text,
          confidence: e.relevance_score,
          score: e.criticality_score,
          level: e.criticality_level,
        };
      });

      if (exigences.length === 0) {
        setMessages(prev => [...prev, { role: 'bot', text: t('chat.exigences.noMatch'), time: getTime() }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'bot',
          text: '',
          time: getTime(),
          exigencesData: {
            document_name: t('chat.exigences.matchResults'),
            exigences,
            by_type: byType,
            by_level: byLevel,
            total: exigences.length,
          },
        }]);
      }
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: t('chat.exigences.error'), time: getTime() }]);
    }
    setLoadingExigences(false);
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const retrieval = getAdaptiveRetrievalSettings(text);
    const responseLanguage = detectMessageLanguage(text);
    const hasFile = !!attachedFile;
    const savedFile = attachedFile;

    let activeConvId = conversationId;
    if (!activeConvId) {
      activeConvId = crypto.randomUUID();
      setConversationId(activeConvId);
    }

    setIsLoading(true);
    setInput('');
    setShowWelcome(false);
    setAttachedFile(null);

    const userMsg = hasFile ? `\u{1F4CE} ${savedFile.name}\n${text}` : text;
    setMessages(prev => [...prev, { role: 'user', text: userMsg, time: getTime() }]);

    try {
      let response;

      if (hasFile) {
        const formData = new FormData();
        formData.append('file', savedFile);
        formData.append('question', text);
        formData.append('top_k', retrieval.topK);
        formData.append('temperature', retrieval.temperature);
        if (responseLanguage) formData.append('response_language', responseLanguage);
        if (conversationHistory.current.length > 0) formData.append('history', JSON.stringify(conversationHistory.current));
        formData.append('conversation_id', activeConvId);

        response = await authFetch('/api/v1/ask-with-document', { method: 'POST', body: formData });
      } else {
        response = await authFetch('/api/v1/ask-auto', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: text, top_k: retrieval.topK, temperature: retrieval.temperature, response_language: responseLanguage, history: conversationHistory.current, conversation_id: activeConvId }),
        });
      }

      const data = await response.json();
      if (response.ok) {
        setMessages(prev => [...prev, { role: 'bot', text: data.answer, sources: data.sources || [], time: getTime() }]);
        conversationHistory.current.push({ role: 'user', content: text }, { role: 'assistant', content: data.answer });
        if (conversationHistory.current.length > 20) conversationHistory.current = conversationHistory.current.slice(-20);
        loadHistory();
      } else {
        setMessages(prev => [...prev, { role: 'bot', text: data?.detail || t('chat.processingError'), sources: [], time: getTime() }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', text: getChatErrorMessage(err), sources: [], time: getTime() }]);
    }
    setIsLoading(false);
    inputRef.current?.focus();
  };

  const sendContractAction = async (action) => {
    if (!attachedFile || isLoading) return;
    const savedFile = attachedFile;

    let activeConvId = conversationId;
    if (!activeConvId) {
      activeConvId = crypto.randomUUID();
      setConversationId(activeConvId);
    }

    setIsLoading(true);
    setShowWelcome(false);
    setAttachedFile(null);

    const actionLabels = {
      summary: t('contractChat.actionSummary'),
      risks: t('contractChat.actionRisks'),
      missing_clauses: t('contractChat.actionMissing'),
      recommendations: t('contractChat.actionRecommendations'),
      full: t('contractChat.actionFull'),
    };

    const userMsg = `\u{1F4CE} ${savedFile.name}\n${actionLabels[action] || action}`;
    setMessages(prev => [...prev, { role: 'user', text: userMsg, time: getTime() }]);

    try {
      const formData = new FormData();
      formData.append('file', savedFile);
      formData.append('action', action);
      formData.append('response_language', i18n.language || 'fr');
      formData.append('conversation_id', activeConvId);

      const response = await authFetch('/api/v1/chat-contract-analysis', {
        method: 'POST', body: formData,
      });

      const data = await response.json();
      if (response.ok) {
        setMessages(prev => [...prev, {
          role: 'bot',
          text: '',
          sources: [],
          time: getTime(),
          contractAnalysis: data,
        }]);
        loadHistory();
      } else {
        setMessages(prev => [...prev, {
          role: 'bot',
          text: data?.detail || t('chat.processingError'),
          sources: [],
          time: getTime(),
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: getChatErrorMessage(err),
        sources: [],
        time: getTime(),
      }]);
    }
    setIsLoading(false);
    inputRef.current?.focus();
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const opts = MediaRecorder.isTypeSupported('audio/webm') ? { mimeType: 'audio/webm' } : {};
      const recorder = new MediaRecorder(stream, opts);
      chunksRef.current = [];
      streamRef.current = stream;
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setRecordingTime(0);
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
    } catch {
      toast.error(t('chat.micNotAccessible'));
    }
  };

  const stopRecordingCleanup = () => {
    clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecording(false);
    setRecordingTime(0);
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.ondataavailable = null;
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }
    stopRecordingCleanup();
  };

  const sendRecording = () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') return;
    const recorder = mediaRecorderRef.current;
    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
      stopRecordingCleanup();
      if (blob.size) await processVoice(blob);
    };
    recorder.stop();
  };

  const formatRecTime = (sec) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const processVoice = async (audioBlob) => {
    setShowWelcome(false);
    setMessages(prev => [...prev, { role: 'user', text: t('chat.voiceMessage'), time: getTime() }]);
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      const res = await authFetch('/api/v1/voice/ask', { method: 'POST', body: formData });
      const data = await res.json();
      setMessages(prev => {
        const updated = [...prev];
        const lastUser = updated.findLastIndex(m => m.role === 'user');
        if (lastUser >= 0) updated[lastUser].text = data.transcription || updated[lastUser].text;
        return [...updated, { role: 'bot', text: data.answer, sources: data.sources || [], time: getTime() }];
      });
      if (data.audio_base64) {
        const bytes = atob(data.audio_base64);
        const arr = new Uint8Array(bytes.length);
        for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
        const url = URL.createObjectURL(new Blob([arr], { type: data.audio_content_type }));
        const audio = new Audio(url);
        audio.play().catch(() => {});
        audio.onended = () => URL.revokeObjectURL(url);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', text: t('chat.voiceError') + ' ' + err.message, sources: [], time: getTime() }]);
    }
    setIsLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const suggestions = [
    t('chat.suggestion1'),
    t('chat.suggestion2'),
    t('chat.suggestion3'),
    t('chat.suggestion4'),
  ];

  const contractActions = [
    { key: 'summary', icon: 'fileText', label: t('contractChat.actionSummary') },
    { key: 'risks', icon: 'alertTriangle', label: t('contractChat.actionRisks') },
    { key: 'missing_clauses', icon: 'search', label: t('contractChat.actionMissing') },
    { key: 'recommendations', icon: 'sparkle', label: t('contractChat.actionRecommendations') },
    { key: 'full', icon: 'layers', label: t('contractChat.actionFull') },
  ];

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ width: 260, background: 'var(--surface)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border)' }}>
          <DButton icon="plus" onClick={newChat} style={{ width: '100%', justifyContent: 'center' }}>
            {t('chat.newConversation')}
          </DButton>
          {conversationId && (
            <div style={{ marginTop: 10, padding: '9px 10px', borderRadius: 8, background: 'var(--gold-bg)', border: '1px solid var(--gold-10)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <DIcon name="messageCircle" size={15} style={{ color: 'var(--gold)' }} />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--gold-dark)' }}>{t('chat.currentConversation')}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t('chat.savedAndContinuable')}</div>
              </div>
            </div>
          )}
        </div>
        <div style={{ padding: '12px 12px 6px', fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
          {t('chat.recentConversations')}
        </div>
        <div ref={historyScrollRef} style={{ flex: 1, overflowY: 'auto', padding: '0 12px 8px' }}>
          {history.length === 0 ? (
            <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>{t('chat.noConversation')}</div>
          ) : history.map((entry, i) => {
            const isRenaming = renamingId && renamingId === entry.conversation_id;
            return (
            <div key={entry.conversation_id || i} onClick={() => { if (!isRenaming) loadConversation(entry); }}
              style={{
                position: 'relative',
                padding: '11px 12px', borderRadius: 9, cursor: isRenaming ? 'default' : 'pointer', marginBottom: 7,
                transition: 'all .12s', border: conversationId && entry.conversation_id === conversationId ? '1px solid var(--gold-10)' : '1px solid var(--border-subtle)',
                background: conversationId && entry.conversation_id === conversationId ? 'var(--gold-bg)' : 'var(--surface)',
                boxShadow: conversationId && entry.conversation_id === conversationId ? 'var(--shadow-sm)' : 'none',
              }}
              className={isRenaming ? '' : 'hover-bg'}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {isRenaming ? (
                  <div style={{ flex: 1, minWidth: 0, position: 'relative' }}>
                    <input
                      autoFocus
                      value={renameDraft}
                      maxLength={120}
                      onChange={(e) => setRenameDraft(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      onFocus={(e) => e.currentTarget.select()}
                      onBlur={() => commitRename(entry)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') { e.preventDefault(); e.currentTarget.blur(); }
                        else if (e.key === 'Escape') { e.preventDefault(); cancelRename(); }
                      }}
                      style={{ width: '100%', fontSize: 13, fontWeight: 500, border: '1px solid var(--gold)', borderRadius: 6, padding: '4px 8px', background: 'var(--surface)', color: 'var(--text)', outline: 'none', fontFamily: 'inherit' }}
                    />
                    {renameDraft.length > 100 && (
                      <span style={{ position: 'absolute', right: 6, bottom: -14, fontSize: 10, color: renameDraft.length >= 120 ? 'var(--error)' : 'var(--text-muted)' }}>
                        {renameDraft.length}/120
                      </span>
                    )}
                  </div>
                ) : (
                  <div style={{ flex: 1, minWidth: 0, fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{conversationTitle(entry).slice(0, 60)}</div>
                )}
                {entry.conversation_id && !isRenaming && (
                  <button
                    type="button"
                    onClick={(e) => toggleConversationMenu(entry, e)}
                    aria-label={t('chat.moreActions')}
                    style={{ width: 26, height: 26, borderRadius: 6, border: 'none', background: openMenuId === entry.conversation_id ? 'var(--surface-active)' : 'transparent', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}
                  >
                    <DIcon name="moreHorizontal" size={16} />
                  </button>
                )}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 5, display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                <span>{new Date(entry.created_at).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })}</span>
                {entry.message_count > 1 && (
                  <span style={{ background: 'var(--gold-bg)', color: 'var(--gold)', padding: '1px 6px', borderRadius: 10, fontSize: 10, fontWeight: 600 }}>
                    {entry.message_count} msgs
                  </span>
                )}
              </div>
            </div>
            );
          })}
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '14px 24px', borderBottom: '1px solid var(--border)', background: 'var(--surface)', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: 'var(--radius-md)', background: 'var(--gold-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold)', overflow: 'hidden' }}>
            <img src="/daleel-mark-light.png?v=20260526" alt="" aria-hidden="true" style={{ width: 27, height: 26, objectFit: 'contain', display: 'block' }} />
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, fontFamily: 'var(--font-heading)' }}>{t('chat.assistantTitle')}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t('chat.assistantSubtitle')}</div>
          </div>
        </div>

        <div ref={chatRef} style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
          {showWelcome ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center' }}>
              <div style={{ width: 64, height: 64, borderRadius: 16, background: 'var(--gold-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20, overflow: 'hidden' }}>
                <img src="/daleel-mark-light.png?v=20260526" alt="" aria-hidden="true" style={{ width: 48, height: 46, objectFit: 'contain', display: 'block' }} />
              </div>
              <h2 style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 8 }}>{t('chat.welcomeTitle')}</h2>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 480, marginBottom: 32, lineHeight: 1.6 }}>
                {t('chat.welcomeDesc')}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, maxWidth: 520, width: '100%' }}>
                {suggestions.map((s, i) => (
                  <button key={i} onClick={() => { setInput(s); }} className="hover-border-gold" style={{ padding: '12px 16px', borderRadius: 'var(--radius-md)', background: 'var(--surface)', border: '1px solid var(--border)', cursor: 'pointer', fontSize: 12, color: 'var(--text-secondary)', textAlign: 'left', lineHeight: 1.4 }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 20, flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
                <div style={{ width: 34, height: 34, borderRadius: '50%', background: msg.role === 'user' ? 'var(--navy)' : 'var(--gold-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: msg.role === 'user' ? '#fff' : 'var(--gold)', fontSize: 14 }}>
                  {msg.role === 'user' ? <DIcon name="user" size={16} /> : <img src="/daleel-mark-light.png?v=20260526" alt="" aria-hidden="true" style={{ width: 22, height: 21, objectFit: 'contain', display: 'block' }} />}
                </div>
                <div style={{ maxWidth: '70%', minWidth: 0 }}>
                  {/* Exigences rich message */}
                  {msg.exigencesData ? (
                    <div style={{
                      padding: '14px 16px', borderRadius: 12,
                      background: 'var(--surface)', border: '1px solid var(--border)',
                      fontSize: 13, lineHeight: 1.6,
                    }}>
                      <ExigencesMessage
                        data={msg.exigencesData}
                        t={t}
                        onExport={() => handleExportFromChat(msg.exigencesData.document_id)}
                      />
                    </div>
                  ) : msg.contractAnalysis ? (
                    <div style={{
                      padding: '14px 16px', borderRadius: 12,
                      background: 'var(--surface)', border: '1px solid var(--border)',
                      fontSize: 13, lineHeight: 1.6,
                    }}>
                      <ContractAnalysisMessage data={msg.contractAnalysis} t={t} />
                    </div>
                  ) : (
                    <div style={{
                      padding: '12px 16px', borderRadius: 12,
                      background: msg.role === 'user' ? 'var(--navy)' : 'var(--surface)',
                      color: msg.role === 'user' ? '#fff' : 'var(--text)',
                      border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                      fontSize: 13, lineHeight: 1.6,
                      direction: isRtlText(msg.text) ? 'rtl' : 'ltr',
                      whiteSpace: 'pre-wrap',
                      overflowWrap: 'anywhere',
                    }}
                  >
                      {msg.role === 'bot' ? renderBotTextWithSourceTitles(msg.text, msg.sources) : msg.text}
                    </div>
                  )}
                  {msg.role === 'bot' && !msg.exigencesData && !msg.contractAnalysis && (
                    <SourceList sources={msg.sources} t={t} />
                  )}
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, textAlign: msg.role === 'user' ? 'right' : 'left' }}>{msg.time}</div>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
              <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'var(--gold-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold)' }}>
                <img src="/daleel-mark-light.png?v=20260526" alt="" aria-hidden="true" style={{ width: 22, height: 21, objectFit: 'contain', display: 'block' }} />
              </div>
              <div style={{ padding: '12px 16px', borderRadius: 12, background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: 13 }}>
                <span style={{ animation: 'pulse 1.5s infinite' }}>{t('chat.analyzing')}</span>
              </div>
            </div>
          )}
        </div>

        {/* Attached file + contract action buttons */}
        {attachedFile && (
          <div style={{ padding: '8px 24px', background: 'var(--surface)', borderTop: '1px solid var(--border)' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 12px', borderRadius: 'var(--radius-md)', background: 'var(--gold-bg)', fontSize: 12 }}>
              <DIcon name="fileText" size={14} style={{ color: 'var(--gold)' }} />
              <span style={{ fontWeight: 500 }}>{attachedFile.name}</span>
              <span style={{ color: 'var(--text-muted)' }}>{formatFileSize(attachedFile.size)}</span>
              <button onClick={() => setAttachedFile(null)} aria-label={t('common.delete')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2 }}>
                <DIcon name="x" size={14} />
              </button>
            </div>

            {/* Contract analysis quick actions */}
            {isContractFile && (
              <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                {contractActions.map(a => (
                  <button
                    key={a.key}
                    onClick={() => sendContractAction(a.key)}
                    disabled={isLoading}
                    className="hover-gold-chip"
                    style={{
                      padding: '6px 12px', borderRadius: 20,
                      background: 'var(--surface)', border: '1px solid var(--border)',
                      color: 'var(--text-secondary)', fontSize: 11, fontWeight: 500,
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      display: 'flex', alignItems: 'center', gap: 5,
                      opacity: isLoading ? 0.5 : 1,
                    }}
                  >
                    <DIcon name={a.icon} size={13} />
                    {a.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
          {isRecording ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'var(--error-bg)', borderRadius: 12, border: '1px solid var(--error)', padding: '8px 8px 8px 16px', animation: 'fadeIn .2s' }}>
              <button onClick={cancelRecording} title={t('common.delete')} style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(185,28,28,0.1)', color: 'var(--error)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(185,28,28,0.2)', cursor: 'pointer', flexShrink: 0, transition: 'all .15s' }}>
                <DIcon name="trash" size={16} />
              </button>
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--error)', animation: 'pulse 1.2s infinite', flexShrink: 0 }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--error)', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>{formatRecTime(recordingTime)}</span>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{t('chat.recording')}</span>
              </div>
              <button onClick={sendRecording} title={t('common.send')} style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--navy)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', border: 'none', cursor: 'pointer', flexShrink: 0, transition: 'all .15s' }}>
                <DIcon name="send" size={16} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, background: 'var(--bg)', borderRadius: 12, border: '1px solid var(--border)', padding: '4px 4px 4px 16px' }}>
              <input type="file" ref={fileInputRef} onChange={handleFileSelect} accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg,.webp" style={{ display: 'none' }} />
              <button onClick={() => fileInputRef.current?.click()} aria-label={t('chat.attachFile')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '8px 4px', flexShrink: 0 }}>
                <DIcon name="paperclip" size={18} />
              </button>
              <button onClick={openExigencesPicker} disabled={loadingExigences} aria-label={t('chat.exigences.button')} title={t('chat.exigences.button')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: loadingExigences ? 'var(--gold)' : 'var(--text-muted)', padding: '8px 4px', flexShrink: 0, transition: 'color .15s' }}>
                <DIcon name="shieldCheck" size={18} />
              </button>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t('chat.placeholder')}
                rows={1}
                style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', fontSize: 13, resize: 'none', padding: '8px 0', fontFamily: 'var(--font-body)', color: 'var(--text)', lineHeight: 1.5, maxHeight: 120, direction: isArabic(input) ? 'rtl' : 'ltr' }}
              />
              <button onClick={startRecording} aria-label={t('chat.recording')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '8px 4px', flexShrink: 0 }}>
                <DIcon name="mic" size={18} />
              </button>
              {input.trim() && (
                <button onClick={() => matchExigences()} disabled={loadingExigences} title={t('chat.exigences.matchButton')} style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--gold-bg)', color: 'var(--gold)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', border: '1px solid var(--gold)', flexShrink: 0, transition: 'all .15s' }}>
                  <DIcon name="search" size={16} />
                </button>
              )}
              <button onClick={sendMessage} disabled={isLoading || !input.trim()} aria-label={t('common.send')} style={{ width: 36, height: 36, borderRadius: 8, background: input.trim() ? 'var(--navy)' : 'var(--surface-active)', color: input.trim() ? '#fff' : 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: input.trim() ? 'pointer' : 'default', border: 'none', flexShrink: 0, transition: 'all .15s' }}>
                <DIcon name="send" size={16} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Document picker modal for exigences */}
      {showDocPicker && (
        <div onClick={() => setShowDocPicker(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div onClick={e => e.stopPropagation()} style={{ background: 'var(--surface)', borderRadius: 16, padding: 24, minWidth: 360, maxWidth: 500, maxHeight: '70vh', overflowY: 'auto', boxShadow: '0 20px 40px rgba(0,0,0,0.2)', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <DIcon name="shieldCheck" size={20} style={{ color: 'var(--gold)' }} />
              <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>{t('chat.exigences.pickDocument')}</h3>
            </div>
            {docList.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t('chat.exigences.noDocs')}</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {docList.map(doc => (
                  <button
                    key={doc.id}
                    onClick={() => loadExigences(doc)}
                    style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg)', cursor: 'pointer', textAlign: 'left', transition: 'all .15s' }}
                    className="hover-bg"
                  >
                    <DIcon name="fileText" size={18} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.filename}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{doc.total_pages} pages · {doc.language || '?'}</div>
                    </div>
                    <DIcon name="chevronRight" size={16} style={{ color: 'var(--text-muted)' }} />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      {openMenuId && menuPosition && (() => {
        const entry = history.find((item) => item.conversation_id === openMenuId);
        if (!entry) return null;
        const actionStyle = {
          width: '100%',
          minHeight: 34,
          padding: '8px 10px',
          border: 'none',
          background: 'var(--surface)',
          color: 'var(--text)',
          opacity: 1,
          visibility: 'visible',
          fontSize: 12,
          lineHeight: 1.2,
          textAlign: 'left',
          cursor: 'pointer',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-start',
          gap: 8,
        };
        return (
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ position: 'fixed', top: menuPosition.top, left: menuPosition.left, zIndex: 1200, width: HISTORY_ACTION_MENU_WIDTH, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, boxShadow: '0 14px 34px rgba(27,43,66,0.16)', padding: 4 }}
          >
            <button type="button" onClick={() => renameConversation(entry)} className="hover-bg-active" style={actionStyle}>
              <DIcon name="edit" size={14} />
              <span>{t('chat.rename')}</span>
            </button>
            <button type="button" onClick={() => archiveConversation(entry)} className="hover-bg-active" style={actionStyle}>
              <DIcon name="archive" size={14} />
              <span>{t('chat.archive')}</span>
            </button>
          </div>
        );
      })()}
    </div>
  );
}
