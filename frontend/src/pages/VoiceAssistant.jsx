import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import DIcon from '../components/DIcon';
import { authFetch } from '../utils/auth';

const STATES = { IDLE: 'idle', LISTENING: 'listening', PROCESSING: 'processing', RESPONDING: 'responding', ERROR: 'error' };

const BAR_COUNT = 24;
const BAR_COLORS = ['#B8935A', '#c9a76b', '#d4b87c', '#B8935A', '#a8834a'];

function AudioEqualizer({ state, audioPlaying }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const barsRef = useRef(Array.from({ length: BAR_COUNT }, () => 0));

  const active = state === STATES.RESPONDING && audioPlaying;
  const listening = state === STATES.LISTENING;
  const processing = state === STATES.PROCESSING;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener('resize', resize);

    const draw = () => {
      const w = canvas.getBoundingClientRect().width;
      const h = canvas.getBoundingClientRect().height;
      const centerY = h / 2;
      const barW = Math.max(3, (w / BAR_COUNT) * 0.55);
      const gap = w / BAR_COUNT;

      ctx.clearRect(0, 0, w, h);

      for (let i = 0; i < BAR_COUNT; i++) {
        let target;
        if (active) {
          const wave = Math.sin(Date.now() * 0.004 + i * 0.6) * 0.5 + 0.5;
          const wave2 = Math.sin(Date.now() * 0.007 + i * 0.9) * 0.3 + 0.5;
          target = (wave * wave2) * (h * 0.38) + h * 0.04;
        } else if (listening) {
          target = (Math.sin(Date.now() * 0.003 + i * 0.5) * 0.3 + 0.35) * h * 0.2;
        } else if (processing) {
          const pulse = Math.sin(Date.now() * 0.005 + i * 0.3) * 0.5 + 0.5;
          target = pulse * h * 0.12 + 2;
        } else {
          target = 3;
        }

        barsRef.current[i] += (target - barsRef.current[i]) * 0.18;
        const barH = barsRef.current[i];
        const x = gap * i + (gap - barW) / 2;
        const color = BAR_COLORS[i % BAR_COLORS.length];

        const alpha = active ? 0.9 : listening ? 0.5 : processing ? 0.35 : 0.15;
        ctx.fillStyle = color;
        ctx.globalAlpha = alpha;

        // Top bar (mirrored)
        const radius = Math.min(barW / 2, 3);
        ctx.beginPath();
        ctx.roundRect(x, centerY - barH, barW, barH, [radius, radius, 0, 0]);
        ctx.fill();
        // Bottom bar (mirrored)
        ctx.beginPath();
        ctx.roundRect(x, centerY, barW, barH, [0, 0, radius, radius]);
        ctx.fill();

        // Glow effect when active
        if (active && barH > h * 0.1) {
          ctx.globalAlpha = 0.15;
          ctx.shadowColor = color;
          ctx.shadowBlur = 8;
          ctx.beginPath();
          ctx.roundRect(x, centerY - barH, barW, barH * 2, radius);
          ctx.fill();
          ctx.shadowBlur = 0;
        }

        ctx.globalAlpha = 1;
      }

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [active, listening, processing]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: '100%', maxWidth: 360, height: 120,
        opacity: state === STATES.IDLE ? 0.3 : 1,
        transition: 'opacity 0.4s ease',
      }}
    />
  );
}

export default function VoiceAssistant() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [state, setState] = useState(STATES.IDLE);
  const [errorMsg, setErrorMsg] = useState('');
  const [audioPlaying, setAudioPlaying] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const audioRef = useRef(null);
  const timerRef = useRef(null);
  const [recordingTime, setRecordingTime] = useState(0);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach(t => t.stop());
      clearInterval(timerRef.current);
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    };
  }, []);

  const cleanup = () => {
    clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    mediaRecorderRef.current = null;
    setRecordingTime(0);
  };

  const startListening = async () => {
    try {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; setAudioPlaying(false); }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const opts = MediaRecorder.isTypeSupported('audio/webm') ? { mimeType: 'audio/webm' } : {};
      const recorder = new MediaRecorder(stream, opts);
      chunksRef.current = [];
      streamRef.current = stream;
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setState(STATES.LISTENING);
      setRecordingTime(0);
      setErrorMsg('');
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
    } catch {
      setErrorMsg(t('voiceAssistant.micError'));
      setState(STATES.ERROR);
    }
  };

  const stopAndSend = () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') return;
    const recorder = mediaRecorderRef.current;
    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
      cleanup();
      if (blob.size > 0) await processVoice(blob);
    };
    recorder.stop();
  };

  const processVoice = async (audioBlob) => {
    setState(STATES.PROCESSING);
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      const res = await authFetch('/api/v1/voice/ask', { method: 'POST', body: formData });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setState(STATES.RESPONDING);

      if (data.audio_base64) {
        const bytes = atob(data.audio_base64);
        const arr = new Uint8Array(bytes.length);
        for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
        const url = URL.createObjectURL(new Blob([arr], { type: data.audio_content_type }));
        const audio = new Audio(url);
        audioRef.current = audio;
        setAudioPlaying(true);
        audio.play().catch(() => {});
        audio.onended = () => {
          URL.revokeObjectURL(url);
          setAudioPlaying(false);
          audioRef.current = null;
          setState(STATES.IDLE);
        };
      } else {
        setState(STATES.IDLE);
      }
    } catch (err) {
      setErrorMsg(err.message);
      setState(STATES.ERROR);
    }
  };

  const handleMicClick = () => {
    if (state === STATES.LISTENING) {
      stopAndSend();
    } else if (state === STATES.RESPONDING && audioPlaying) {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
      setAudioPlaying(false);
      setState(STATES.IDLE);
    } else {
      startListening();
    }
  };

  const formatTime = (sec) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 500,
      background: 'linear-gradient(160deg, #0f1a2e 0%, #1B2B42 40%, #243752 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        padding: '20px 28px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        zIndex: 2,
      }}>
        <button onClick={() => navigate(-1)} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          color: 'rgba(255,255,255,0.5)', fontSize: 13, fontWeight: 500,
          padding: '8px 14px', borderRadius: 8,
          background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)',
          cursor: 'pointer', transition: 'all .15s',
        }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = '#fff'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'rgba(255,255,255,0.5)'; }}
        >
          <DIcon name="arrowLeft" size={16} />
          {t('voiceAssistant.back')}
        </button>
      </div>

      {/* Audio equalizer */}
      <AudioEqualizer state={state} audioPlaying={audioPlaying} />

      {/* Status */}
      <div style={{
        marginTop: 16,
        fontSize: 14, fontWeight: 500,
        color: state === STATES.LISTENING ? 'rgba(0,230,215,0.8)'
          : state === STATES.PROCESSING ? 'rgba(180,100,255,0.7)'
          : state === STATES.ERROR ? 'rgba(255,80,80,0.8)'
          : 'rgba(255,255,255,0.35)',
        fontFamily: 'var(--font-body)',
        minHeight: 24,
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        {state === STATES.IDLE && t('voiceAssistant.pressToTalk')}
        {state === STATES.LISTENING && (
          <>
            {t('voiceAssistant.listening')}
            <span style={{ fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>{formatTime(recordingTime)}</span>
          </>
        )}
        {state === STATES.PROCESSING && t('voiceAssistant.processing')}
        {state === STATES.RESPONDING && audioPlaying && t('voiceAssistant.speaking')}
        {state === STATES.RESPONDING && !audioPlaying && t('voiceAssistant.pressToTalk')}
        {state === STATES.ERROR && (errorMsg || t('voiceAssistant.genericError'))}
      </div>

      {/* Mic button */}
      <button
        onClick={handleMicClick}
        disabled={state === STATES.PROCESSING}
        style={{
          marginTop: 20,
          width: 72, height: 72, borderRadius: '50%',
          background: state === STATES.LISTENING
            ? 'rgba(255,60,60,0.9)'
            : state === STATES.PROCESSING
              ? 'rgba(255,255,255,0.08)'
              : state === STATES.RESPONDING && audioPlaying
                ? 'rgba(255,255,255,0.12)'
                : 'rgba(255,255,255,0.1)',
          border: state === STATES.LISTENING
            ? '2px solid rgba(255,60,60,0.5)'
            : '2px solid rgba(255,255,255,0.1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: state === STATES.PROCESSING ? 'wait' : 'pointer',
          transition: 'all .25s',
        }}
      >
        {state === STATES.PROCESSING ? (
          <div style={{
            width: 24, height: 24, borderRadius: '50%',
            border: '2px solid rgba(255,255,255,0.1)',
            borderTopColor: 'rgba(180,100,255,0.7)',
            animation: 'spin 0.8s linear infinite',
          }} />
        ) : state === STATES.RESPONDING && audioPlaying ? (
          <DIcon name="phoneOff" size={26} style={{ color: 'rgba(255,255,255,0.7)' }} />
        ) : (
          <DIcon name="mic" size={26} style={{ color: state === STATES.LISTENING ? '#fff' : 'rgba(255,255,255,0.6)' }} />
        )}
      </button>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
