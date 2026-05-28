import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import DIcon from '../components/DIcon';
import { Badge } from '../components/UI';
import { authFetch } from '../utils/auth';
import { isArabic, detectMessageLanguage, getAdaptiveRetrievalSettings, renderMarkdown, formatFileSize, getTime } from '../utils/helpers';

const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'webp'];
const CONTRACT_EXTENSIONS = ['pdf', 'docx', 'doc'];

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
        <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '8px 12px', background: '#e8f5e9', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <DIcon name="check" size={14} style={{ color: '#2e7d32' }} />
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
                background: c.importance === 'mandatory' ? '#ffebee' : '#fff3e0',
                borderLeft: `3px solid ${c.importance === 'mandatory' ? '#f44336' : '#ff9800'}`,
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
        <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '8px 12px', background: '#e8f5e9', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <DIcon name="check" size={14} style={{ color: '#2e7d32' }} />
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
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  const [history, setHistory] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showWelcome, setShowWelcome] = useState(true);
  const [conversationId, setConversationId] = useState(null);

  const chatRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const conversationHistory = useRef([]);
  const locale = i18n.language === 'ar' ? 'ar-TN' : i18n.language === 'en' ? 'en-US' : 'fr-FR';

  const isContractFile = attachedFile && CONTRACT_EXTENSIONS.includes(
    attachedFile.name.split('.').pop().toLowerCase()
  );

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

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

  const loadConversation = async (entry) => {
    setShowWelcome(false);

    if (entry.conversation_id) {
      setConversationId(entry.conversation_id);
      try {
        const res = await authFetch(`/api/v1/chat-history/conversation/${entry.conversation_id}`);
        if (res.ok) {
          const data = await res.json();
          const msgs = data.messages || [];
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
          setMessages(uiMessages);
          return;
        }
      } catch {
        // fallback below
      }
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
    conversationHistory.current = [];
    setConversationId(null);
    setMessages([]);
    setShowWelcome(true);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      alert(t('chat.unsupportedFormat'));
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      alert(t('chat.fileTooLarge'));
      return;
    }
    setAttachedFile(file);
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
      const jwt = localStorage.getItem('daleel_access_token');
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

        const headers = {};
        if (jwt) headers['Authorization'] = 'Bearer ' + jwt;
        response = await fetch('/api/v1/ask-with-document', { method: 'POST', headers, body: formData });
      } else {
        const headers = { 'Content-Type': 'application/json' };
        if (jwt) headers['Authorization'] = 'Bearer ' + jwt;
        response = await fetch('/api/v1/ask-agentic', {
          method: 'POST',
          headers,
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
      setMessages(prev => [...prev, { role: 'bot', text: `${t('chat.connectionError')} ${err.message}`, sources: [], time: getTime() }]);
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
      const jwt = localStorage.getItem('daleel_access_token');
      const formData = new FormData();
      formData.append('file', savedFile);
      formData.append('action', action);
      formData.append('response_language', i18n.language || 'fr');
      formData.append('conversation_id', activeConvId);

      const headers = {};
      if (jwt) headers['Authorization'] = 'Bearer ' + jwt;

      const response = await fetch('/api/v1/chat-contract-analysis', {
        method: 'POST', headers, body: formData,
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
        text: `${t('chat.connectionError')} ${err.message}`,
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
      alert(t('chat.micNotAccessible'));
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
          <button onClick={newChat} style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-md)', background: 'var(--navy)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, border: 'none' }}>
            <DIcon name="plus" size={16} /> {t('chat.newConversation')}
          </button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px' }}>
          {history.length === 0 ? (
            <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>{t('chat.noConversation')}</div>
          ) : history.map((entry, i) => (
            <div key={entry.conversation_id || i} onClick={() => loadConversation(entry)}
              style={{
                padding: '10px 12px', borderRadius: 'var(--radius-md)', cursor: 'pointer', marginBottom: 4,
                transition: 'background .12s', border: '1px solid transparent',
                background: conversationId && entry.conversation_id === conversationId ? 'var(--surface-hover)' : 'transparent',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
              onMouseLeave={e => { if (!(conversationId && entry.conversation_id === conversationId)) { e.currentTarget.style.background = 'transparent'; } e.currentTarget.style.borderColor = 'transparent'; }}>
              <div style={{ fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{(entry.question || '').slice(0, 60)}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>{new Date(entry.created_at).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })}</span>
                {entry.message_count > 1 && (
                  <span style={{ background: 'var(--gold-bg)', color: 'var(--gold)', padding: '1px 6px', borderRadius: 10, fontSize: 10, fontWeight: 600 }}>
                    {entry.message_count} msgs
                  </span>
                )}
              </div>
            </div>
          ))}
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
                  <button key={i} onClick={() => { setInput(s); }} style={{ padding: '12px 16px', borderRadius: 'var(--radius-md)', background: 'var(--surface)', border: '1px solid var(--border)', cursor: 'pointer', fontSize: 12, color: 'var(--text-secondary)', textAlign: 'left', lineHeight: 1.4, transition: 'all .15s' }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--gold)'; e.currentTarget.style.color = 'var(--text)'; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}>
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
                  {/* Contract analysis rich message */}
                  {msg.contractAnalysis ? (
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
                      direction: isArabic(msg.text) ? 'rtl' : 'ltr',
                    }}
                      dangerouslySetInnerHTML={msg.role === 'bot' ? { __html: renderMarkdown(msg.text) } : undefined}
                    >
                      {msg.role === 'user' ? msg.text : undefined}
                    </div>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>{t('chat.sources')} ({msg.sources.length})</div>
                      {msg.sources.map((s, j) => (
                        <div key={j} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', borderRadius: 6, background: 'var(--surface)', border: '1px solid var(--border-subtle)', marginBottom: 4, fontSize: 12 }}>
                          <DIcon name="fileText" size={14} style={{ color: 'var(--gold)' }} />
                          <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.filename}</span>
                          <Badge variant="gold">{Math.round(s.relevance_score * 100)}%</Badge>
                        </div>
                      ))}
                    </div>
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
              <button onClick={() => setAttachedFile(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2 }}>
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
                    style={{
                      padding: '6px 12px', borderRadius: 20,
                      background: 'var(--surface)', border: '1px solid var(--border)',
                      color: 'var(--text-secondary)', fontSize: 11, fontWeight: 500,
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      display: 'flex', alignItems: 'center', gap: 5,
                      transition: 'all .15s',
                      opacity: isLoading ? 0.5 : 1,
                    }}
                    onMouseEnter={e => { if (!isLoading) { e.currentTarget.style.borderColor = 'var(--gold)'; e.currentTarget.style.color = 'var(--gold)'; e.currentTarget.style.background = 'var(--gold-bg)'; } }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.background = 'var(--surface)'; }}
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
              <button onClick={() => fileInputRef.current?.click()} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '8px 4px', flexShrink: 0 }}>
                <DIcon name="paperclip" size={18} />
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
              <button onClick={startRecording} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '8px 4px', flexShrink: 0 }}>
                <DIcon name="mic" size={18} />
              </button>
              <button onClick={sendMessage} disabled={isLoading || !input.trim()} style={{ width: 36, height: 36, borderRadius: 8, background: input.trim() ? 'var(--navy)' : 'var(--surface-active)', color: input.trim() ? '#fff' : 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: input.trim() ? 'pointer' : 'default', border: 'none', flexShrink: 0, transition: 'all .15s' }}>
                <DIcon name="send" size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
