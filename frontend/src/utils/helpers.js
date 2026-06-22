import DOMPurify from 'dompurify';

export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

export function isArabic(text) {
  return /[؀-ۿ]/.test(text);
}

// Direction d'affichage : RTL uniquement si l'arabe domine (évite de basculer
// toute une réponse FR/EN à droite à cause de quelques références en arabe).
export function isRtlText(text) {
  const ar = (String(text).match(/[؀-ۿ]/g) || []).length;
  const lat = (String(text).match(/[A-Za-zÀ-ÿ]/g) || []).length;
  return ar > lat;
}

export function detectMessageLanguage(text) {
  if (isArabic(text)) return 'ar';
  const lower = (text || '').toLowerCase();
  const frenchMarkers = ['quelle', 'quelles', 'quel', 'quels', 'comment', 'pourquoi', 'dans', 'pour', 'avec', 'selon', 'droit', 'loi', 'article', 'société', 'societe', 'contrat', 'obligation'];
  if (/[àâäéèêëïîôùûüÿçœæ]/i.test(text)) return 'fr';
  if (frenchMarkers.filter(w => lower.includes(w)).length >= 2) return 'fr';
  return 'en';
}

export function getAdaptiveRetrievalSettings(text) {
  const trimmed = (text || '').trim();
  const words = trimmed.split(/\s+/).filter(Boolean).length;
  const hasQuestionChain = /[؟?].*[؟?]|\b(et|ou|puis|ensuite|ainsi que|و|ثم|أو)\b/i.test(trimmed);
  const hasArticleMention = /(article|الفصل|فصل)\s*\d+/i.test(trimmed);
  let topK = 6, temperature = 0.2;
  if (words >= 18 || hasQuestionChain || hasArticleMention) { topK = 10; temperature = 0.15; }
  if (words <= 6 && !hasArticleMention) { topK = 5; temperature = 0.2; }
  return { topK, temperature };
}

export function renderMarkdown(text) {
  let html = text
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
  html = html.replace(/(<li>.*?<\/li>)/gs, match => {
    if (!match.startsWith('<ul>')) return '<ul>' + match + '</ul>';
    return match;
  });
  html = html.replace(/<\/ul>\s*<ul>/g, '');
  return DOMPurify.sanitize('<p>' + html + '</p>');
}

export function stripMarkdown(text) {
  return String(text || '')
    .replace(/\r\n/g, '\n')
    .replace(/```[^\n]*\n?([\s\S]*?)```/g, '$1')
    .replace(/^ {0,3}#{1,6}\s+/gm, '')
    .replace(/^ {0,3}>\s?/gm, '')
    .replace(/^ {0,3}[-*_]{3,}\s*$/gm, '')
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\[([^\]]+)\]\[[^\]]+\]/g, '$1')
    .replace(/^ {0,3}[-*+]\s+/gm, '')
    .replace(/^ {0,3}\d+[.)]\s+/gm, '')
    .replace(/^\s*\[[ xX]\]\s+/gm, '')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*([^*\n]+)\*\*/g, '$1')
    .replace(/__([^_\n]+)__/g, '$1')
    .replace(/\*([^*\n]+)\*/g, '$1')
    .replace(/_([^_\n]+)_/g, '$1')
    .replace(/~~([^~\n]+)~~/g, '$1')
    .replace(/^\s*\|(.+)\|\s*$/gm, '$1')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' o';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko';
  return (bytes / (1024 * 1024)).toFixed(1) + ' Mo';
}

export function getTime() {
  return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
