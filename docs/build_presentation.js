const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

// ---------- Palette ("Daleel = le guide") ----------
const NAVY  = "14213D"; // dominant dark
const NAVY2 = "1C2E52";
const TEAL  = "0E8388";
const TEALL = "14B8A6";
const GOLD  = "C9A227";
const INK   = "1E293B";
const MUTED = "64748B";
const LIGHT = "F1F5F9";
const TINT  = "F4F7FA";
const WHITE = "FFFFFF";

const CAP = "C:/Users/RSCH/Daleel/captures/";

// ---------- Icon helper ----------
async function iconPng(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
function shadow() {
  return { type: "outer", color: "000000", blur: 8, offset: 3, angle: 90, opacity: 0.18 };
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625
  pres.author = "Manar Trimeche";
  pres.title = "Daleel — Présentation de l'application";

  const W = 10, H = 5.625;

  // Pre-render icons
  const icScale   = await iconPng(fa.FaBalanceScale, "#" + GOLD, 256);
  const icSearch  = await iconPng(fa.FaSearch, "#FFFFFF", 256);
  const icShield  = await iconPng(fa.FaShieldAlt, "#FFFFFF", 256);
  const icLayers  = await iconPng(fa.FaLayerGroup, "#" + TEAL, 256);
  const icGlobe   = await iconPng(fa.FaGlobe, "#" + TEAL, 256);
  const icFile    = await iconPng(fa.FaFileAlt, "#" + TEAL, 256);
  const icHistory = await iconPng(fa.FaHistory, "#" + TEAL, 256);
  const icTasks   = await iconPng(fa.FaTasks, "#" + TEAL, 256);
  const icRobot   = await iconPng(fa.FaRobot, "#" + GOLD, 256);
  const icCheck   = await iconPng(fa.FaCheckCircle, "#" + TEAL, 256);
  const icComment = await iconPng(fa.FaComments, "#FFFFFF", 256);
  const icChart   = await iconPng(fa.FaChartLine, "#FFFFFF", 256);
  const icMic     = await iconPng(fa.FaMicrophone, "#" + TEAL, 256);
  const icLink    = await iconPng(fa.FaLink, "#" + TEAL, 256);
  const icLang    = await iconPng(fa.FaLanguage, "#" + TEAL, 256);
  const icUpload  = await iconPng(fa.FaCloudUploadAlt, "#" + TEAL, 256);

  // ---------- helpers ----------
  function kicker(slide, txt) {
    slide.addText(txt.toUpperCase(), {
      x: 0.6, y: 0.42, w: 8.8, h: 0.3, margin: 0,
      fontFace: "Calibri", fontSize: 12, bold: true, color: GOLD, charSpacing: 2,
    });
  }
  function title(slide, txt) {
    slide.addText(txt, {
      x: 0.6, y: 0.7, w: 8.8, h: 0.75, margin: 0,
      fontFace: "Cambria", fontSize: 30, bold: true, color: NAVY,
    });
  }
  // framed screenshot with white backing + shadow, contained
  function shot(slide, file, ow, oh, x, y, maxW, maxH) {
    const ar = ow / oh;
    let w = maxW, h = w / ar;
    if (h > maxH) { h = maxH; w = h * ar; }
    const cx = x + (maxW - w) / 2;
    const cy = y + (maxH - h) / 2;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: cx - 0.08, y: cy - 0.08, w: w + 0.16, h: h + 0.16,
      fill: { color: WHITE }, line: { color: "E2E8F0", width: 1 },
      rectRadius: 0.06, shadow: shadow(),
    });
    slide.addImage({ path: CAP + file, x: cx, y: cy, w, h });
  }
  function iconRow(slide, icon, head, body, x, y, w) {
    slide.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color: TINT } });
    slide.addImage({ data: icon, x: x + 0.12, y: y + 0.12, w: 0.26, h: 0.26 });
    slide.addText(head, {
      x: x + 0.68, y: y - 0.04, w: w - 0.68, h: 0.32, margin: 0,
      fontFace: "Calibri", fontSize: 15, bold: true, color: INK,
    });
    slide.addText(body, {
      x: x + 0.68, y: y + 0.26, w: w - 0.68, h: 0.5, margin: 0,
      fontFace: "Calibri", fontSize: 11.5, color: MUTED, lineSpacingMultiple: 0.98,
    });
  }
  function bullets(slide, items, x, y, w, h) {
    slide.addText(
      items.map((it, i) => ({
        text: it,
        options: { bullet: { code: "2022", indent: 14 }, color: INK, breakLine: true,
          paraSpaceAfter: 8, fontSize: 13.5, fontFace: "Calibri" },
      })),
      { x, y, w, h, margin: 0, valign: "top" }
    );
  }

  // ============================================================
  // SLIDE 1 — TITLE
  // ============================================================
  let s = pres.addSlide();
  s.background = { color: NAVY };
  // subtle motif circles
  s.addShape(pres.shapes.OVAL, { x: 7.7, y: -1.4, w: 4.2, h: 4.2, fill: { color: NAVY2 } });
  s.addShape(pres.shapes.OVAL, { x: 9.0, y: 3.6, w: 2.6, h: 2.6, fill: { color: NAVY2 } });
  s.addShape(pres.shapes.OVAL, { x: 0.6, y: 0.55, w: 0.95, h: 0.95, fill: { color: NAVY2 }, line: { color: GOLD, width: 1.25 } });
  s.addImage({ data: icScale, x: 0.83, y: 0.78, w: 0.49, h: 0.49 });
  s.addText("دليل  ·  DALEEL", {
    x: 0.6, y: 1.95, w: 8.8, h: 0.4, margin: 0,
    fontFace: "Calibri", fontSize: 16, bold: true, color: GOLD, charSpacing: 4,
  });
  s.addText("Daleel", {
    x: 0.55, y: 2.3, w: 8.8, h: 1.1, margin: 0,
    fontFace: "Cambria", fontSize: 64, bold: true, color: WHITE,
  });
  s.addText("Plateforme intelligente de recherche juridique et de suivi de conformité", {
    x: 0.6, y: 3.45, w: 8.2, h: 0.6, margin: 0,
    fontFace: "Calibri", fontSize: 18, color: "CBD5E1",
  });
  s.addText([
    { text: "Manar Trimeche", options: { bold: true, color: WHITE, fontSize: 13, breakLine: true } },
    { text: "École Polytechnique de Sousse  ·  Encadrant : Dr. Nizar Omheni  ·  Didax IT", options: { color: "94A3B8", fontSize: 11.5 } },
  ], { x: 0.6, y: 4.7, w: 8.8, h: 0.6, margin: 0, lineSpacingMultiple: 1.1 });

  // ============================================================
  // SLIDE 2 — DALEEL EN BREF
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Vue d'ensemble");
  title(s, "Daleel en bref");
  s.addText(
    "Daleel (دليل, « le guide ») est une application web qui aide à exploiter le corpus juridique " +
    "tunisien grâce à l'intelligence artificielle. L'utilisateur interroge les textes de loi en langage " +
    "naturel et reçoit des réponses fondées sur des sources vérifiables, puis pilote tout son cycle " +
    "de conformité réglementaire — de la veille juridique jusqu'à l'action corrective.",
    { x: 0.6, y: 1.55, w: 5.05, h: 2.0, margin: 0, fontFace: "Calibri", fontSize: 14.5, color: INK, lineSpacingMultiple: 1.15, valign: "top" }
  );
  s.addText("Multilingue arabe · français · anglais", {
    x: 0.6, y: 3.55, w: 5.05, h: 0.4, margin: 0, italic: true, fontFace: "Calibri", fontSize: 13, color: TEAL, bold: true,
  });
  // stat cards 2x2 on right
  const stats = [
    ["170+", "points d'accès API"],
    ["41", "services métier"],
    ["38", "collections MongoDB"],
    ["34", "composants d'interface"],
  ];
  const sx = 6.0, sy = 1.55, cw = 1.72, ch = 1.62, gap = 0.22;
  stats.forEach((st, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = sx + col * (cw + gap), y = sy + row * (ch + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: ch, fill: { color: TINT }, line: { color: "E2E8F0", width: 1 }, rectRadius: 0.08, shadow: shadow() });
    s.addText(st[0], { x, y: y + 0.22, w: cw, h: 0.7, margin: 0, align: "center", fontFace: "Cambria", fontSize: 38, bold: true, color: TEAL });
    s.addText(st[1], { x: x + 0.1, y: y + 0.95, w: cw - 0.2, h: 0.55, margin: 0, align: "center", fontFace: "Calibri", fontSize: 11.5, color: MUTED });
  });

  // ============================================================
  // SLIDE 3 — POURQUOI DALEEL (besoin)
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Le besoin");
  title(s, "Pourquoi Daleel ?");
  s.addText("L'information juridique tunisienne est vaste, fragmentée et difficile à exploiter.", {
    x: 0.6, y: 1.5, w: 8.8, h: 0.4, margin: 0, fontFace: "Calibri", fontSize: 14, italic: true, color: MUTED,
  });
  const needs = [
    [icFile,   "Volume & fragmentation", "Codes, lois, décrets et circulaires dispersés, en formats hétérogènes (PDF, DOCX, scans)."],
    [icGlobe,  "Corpus multilingue",     "Textes en arabe et en français, sans correspondance terme à terme entre les versions."],
    [icLayers, "Documents scannés",      "Une partie des textes arabes n'existe qu'en images — exploitation directe impossible sans OCR."],
    [icHistory,"Textes évolutifs",       "Amendements : ajout, remplacement, modification, abrogation — il faut tracer chaque version."],
    [icTasks,  "Conformité non outillée", "Aucun outil ne relie les textes applicables au pilotage opérationnel de la conformité."],
  ];
  let ny = 2.05;
  needs.forEach((n, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    if (i === 4) { iconRow(s, n[0], n[1], n[2], 0.6, ny + row * 1.0, 8.8); return; }
    iconRow(s, n[0], n[1], n[2], 0.6 + col * 4.55, ny + row * 1.0, 4.35);
  });

  // ============================================================
  // SLIDE 4 — UNE PLATEFORME, DEUX VOLETS
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "La solution");
  title(s, "Une plateforme, deux volets");
  const cards = [
    { ic: icSearch, t: "Legal RAG", st: "Recherche juridique intelligente",
      pts: ["Recherche hybride multilingue (vecteurs FAISS + lexical)", "Reranking par cross-encoder + routage par domaine", "Réponses synthétisées et sourcées par un LLM local", "Agent autonome ReAct à 12 outils", "Garde-qualité anti-hallucination"] },
    { ic: icShield, t: "Compliance Operations", st: "Pilotage opérationnel de la conformité",
      pts: ["Dossiers de non-conformité & constats notés", "Exigences applicables par profil d'entreprise", "Actions correctives, preuves & contrôles", "Registre d'exceptions & audit traçable", "Tableau de bord de la posture de conformité"] },
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + i * 4.55, y = 1.6, w = 4.35, h = 3.55;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: i === 0 ? TINT : "F4FAF9" }, line: { color: "E2E8F0", width: 1 }, rectRadius: 0.08, shadow: shadow() });
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.3, w: 0.7, h: 0.7, fill: { color: i === 0 ? TEAL : NAVY } });
    s.addImage({ data: c.ic, x: x + 0.48, y: y + 0.48, w: 0.34, h: 0.34 });
    s.addText(c.t, { x: x + 1.15, y: y + 0.32, w: w - 1.3, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 20, bold: true, color: NAVY });
    s.addText(c.st, { x: x + 1.15, y: y + 0.74, w: w - 1.3, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 11.5, italic: true, color: MUTED });
    s.addText(
      c.pts.map((p) => ({ text: p, options: { bullet: { code: "2022", indent: 12 }, color: INK, breakLine: true, paraSpaceAfter: 7, fontSize: 12, fontFace: "Calibri" } })),
      { x: x + 0.35, y: y + 1.25, w: w - 0.6, h: 2.1, margin: 0, valign: "top" }
    );
  });

  // ============================================================
  // Content+screenshot slides factory
  // ============================================================
  function shotSlide(opts) {
    const sl = pres.addSlide(); sl.background = { color: WHITE };
    kicker(sl, opts.kicker);
    title(sl, opts.title);
    bullets(sl, opts.bullets, 0.6, 1.7, 4.0, 3.4);
    shot(sl, opts.file, opts.ow, opts.oh, 4.8, 1.55, 4.65, 3.55);
    if (opts.note) {
      sl.addText(opts.note, { x: 4.8, y: 5.12, w: 4.65, h: 0.32, margin: 0, align: "center", fontFace: "Calibri", fontSize: 10, italic: true, color: MUTED });
    }
    return sl;
  }

  // SLIDE 5 — Chatbot
  shotSlide({
    kicker: "Interface 1 · Utilisateur final",
    title: "Le chatbot conversationnel",
    bullets: [
      "Questions en langage naturel — arabe, français, anglais",
      "Saisie vocale et transcription intégrées",
      "Réponses sourcées avec références cliquables",
      "Conversation continue pour approfondir un sujet",
      "Bouton de feedback 👍/👎 pour l'amélioration continue",
    ],
    file: "fig_4_1_chatbot.png", ow: 1917, oh: 912,
    note: "Interface du chatbot conversationnel multilingue",
  });

  // SLIDE 6 — Réponse sourcée + garde-qualité
  shotSlide({
    kicker: "Confiance & traçabilité",
    title: "Réponse sourcée, sans hallucination",
    bullets: [
      "Chaque [Source N] ouvre le passage exact du texte de loi",
      "Garde-qualité en 4 couches après génération",
      "Badge vert (acceptée) · orange (réécrite) · rouge (rejetée)",
      "Citations fabriquées et références inventées neutralisées",
      "Réponse rendue dans la langue de la question",
    ],
    file: "fig_4_1_chat_reponse.png", ow: 1637, oh: 842,
    note: "Réponse avec sources vérifiables et contrôle qualité",
  });

  // SLIDE 7 — Agent autonome
  shotSlide({
    kicker: "Raisonnement avancé",
    title: "L'agent autonome ReAct",
    bullets: [
      "12 outils spécialisés (recherche, articles, conformité…)",
      "Raisonnement itératif sur les questions complexes",
      "Croise plusieurs sources avant de répondre",
      "Journal de raisonnement transparent et consultable",
      "Garde-fous : budget d'itérations et délai maximal",
    ],
    file: "fig_4_2_agent_tool_log.png", ow: 1646, oh: 772,
    note: "Journal des outils invoqués par l'agent",
  });

  // SLIDE 8 — Multilingue / arabe / derja
  shotSlide({
    kicker: "Adapté au contexte tunisien",
    title: "Multilingue, jusqu'au derja",
    bullets: [
      "Interface entièrement bilingue, RTL pour l'arabe",
      "Compréhension de l'arabe juridique et du dialecte",
      "OCR spécialisé pour les textes arabes scannés",
      "Normalisation Unicode dédiée à l'arabe",
      "Recherche translingue arabe ⇄ français",
    ],
    file: "fig_4_3_derja.png", ow: 1617, oh: 838,
    note: "Prise en charge de l'arabe et du dialecte tunisien",
  });

  // SLIDE 9 — Panneau admin
  shotSlide({
    kicker: "Interface 2 · Administration",
    title: "Gestion du corpus & ingestion",
    bullets: [
      "Import de documents PDF, DOCX, TXT et images",
      "Suivi du pipeline : extrait → nettoyé → segmenté → indexé",
      "Détection et application des amendements",
      "Gestion multi-tenant : organisations, utilisateurs, rôles",
      "Profils d'entreprise pour évaluer l'applicabilité",
    ],
    file: "fig_4_2_admin_documents.png", ow: 1587, oh: 673,
    note: "Panneau d'administration — gestion documentaire",
  });

  // SLIDE 10 — Dashboard BI
  shotSlide({
    kicker: "Pilotage conformité",
    title: "Tableau de bord de conformité",
    bullets: [
      "Score global de conformité en temps réel",
      "Dossiers actifs et constats critiques ouverts",
      "Courbes d'évolution sur 12 mois",
      "Heatmap domaine × organisation (zones à risque)",
      "Top des actions critiques en retard",
    ],
    file: "fig_4_3_dashboard.png", ow: 1580, oh: 906,
    note: "Tableau de bord BI de la posture de conformité",
  });

  // ============================================================
  // SLIDE 11 — RÉSULTATS (native chart)
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Résultats mesurés");
  title(s, "Recherche plus précise après fine-tuning");
  s.addText(
    "Modèle d'embeddings spécialisé sur le corpus juridique tunisien, évalué sur 30 requêtes de référence. " +
    "Gains nets sur la précision des premiers résultats — décisifs pour la qualité des réponses RAG.",
    { x: 0.6, y: 1.5, w: 8.8, h: 0.6, margin: 0, fontFace: "Calibri", fontSize: 13, color: MUTED, lineSpacingMultiple: 1.1 }
  );
  s.addChart(pres.charts.BAR, [
    { name: "Baseline (mpnet)", labels: ["Recall@1", "Recall@5", "MRR@10", "nDCG@5"], values: [0.33, 0.53, 0.42, 0.43] },
    { name: "Daleel (fine-tuné)", labels: ["Recall@1", "Recall@5", "MRR@10", "nDCG@5"], values: [0.47, 0.70, 0.57, 0.59] },
  ], {
    x: 0.6, y: 2.25, w: 6.0, h: 3.05, barDir: "col",
    chartColors: ["AEB8C2", TEAL],
    chartArea: { fill: { color: WHITE } },
    catAxisLabelColor: MUTED, catAxisLabelFontFace: "Calibri", catAxisLabelFontSize: 11,
    valAxisLabelColor: MUTED, valAxisHidden: false, valAxisMaxVal: 0.8, valAxisMinVal: 0,
    valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK,
    dataLabelFontFace: "Calibri", dataLabelFontSize: 9, dataLabelFormatCode: "0.00",
    showLegend: true, legendPos: "b", legendColor: INK, legendFontFace: "Calibri", legendFontSize: 11,
  });
  // highlight callouts on the right
  const gains = [["+40 %", "Recall@1"], ["+34 %", "MRR@10"], ["+37 %", "nDCG@5"]];
  gains.forEach((g, i) => {
    const y = 2.35 + i * 0.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.0, y, w: 2.4, h: 0.82, fill: { color: TINT }, line: { color: "E2E8F0", width: 1 }, rectRadius: 0.07, shadow: shadow() });
    s.addText(g[0], { x: 7.0, y: y + 0.08, w: 1.0, h: 0.66, margin: 0, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 24, bold: true, color: GOLD });
    s.addText([{ text: "de gain sur", options: { fontSize: 10, color: MUTED, breakLine: true } }, { text: g[1], options: { fontSize: 13, bold: true, color: INK } }],
      { x: 8.0, y: y + 0.06, w: 1.35, h: 0.7, margin: 0, valign: "middle", fontFace: "Calibri" });
  });

  // ============================================================
  // SLIDE 12 — CONCLUSION (dark)
  // ============================================================
  s = pres.addSlide(); s.background = { color: NAVY };
  s.addShape(pres.shapes.OVAL, { x: -1.3, y: 3.4, w: 4.0, h: 4.0, fill: { color: NAVY2 } });
  s.addText("EN RÉSUMÉ", { x: 0.6, y: 0.6, w: 8, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: GOLD, charSpacing: 2 });
  s.addText("De la recherche juridique au pilotage de la conformité", {
    x: 0.6, y: 0.95, w: 8.8, h: 0.9, margin: 0, fontFace: "Cambria", fontSize: 26, bold: true, color: WHITE,
  });
  // 4-step journey
  const steps = [["1", "Importer", "déposer les textes de loi"], ["2", "Interroger", "poser une question en langage naturel"], ["3", "Comprendre", "réponse claire et sourcée"], ["4", "Piloter", "exigences, actions, conformité"]];
  steps.forEach((st, i) => {
    const x = 0.6 + i * 2.27, y = 2.25, w = 2.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.55, fill: { color: NAVY2 }, line: { color: "33446B", width: 1 }, rectRadius: 0.08 });
    s.addShape(pres.shapes.OVAL, { x: x + 0.18, y: y + 0.2, w: 0.5, h: 0.5, fill: { color: GOLD } });
    s.addText(st[0], { x: x + 0.18, y: y + 0.2, w: 0.5, h: 0.5, margin: 0, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 20, bold: true, color: NAVY });
    s.addText(st[1], { x: x + 0.78, y: y + 0.26, w: w - 0.85, h: 0.4, margin: 0, fontFace: "Calibri", fontSize: 14, bold: true, color: WHITE });
    s.addText(st[2], { x: x + 0.2, y: y + 0.82, w: w - 0.35, h: 0.6, margin: 0, fontFace: "Calibri", fontSize: 11, color: "9FB0CC", lineSpacingMultiple: 0.98 });
  });
  s.addText(
    "Daleel rend l'information juridique tunisienne plus accessible, plus fiable et mieux organisée — " +
    "en assistant l'expert, jamais en le remplaçant.",
    { x: 0.6, y: 4.2, w: 8.8, h: 0.6, margin: 0, fontFace: "Calibri", fontSize: 14, italic: true, color: "CBD5E1", lineSpacingMultiple: 1.1 }
  );
  s.addText("Merci de votre attention.", { x: 0.6, y: 4.95, w: 8.8, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 16, bold: true, color: GOLD });

  await pres.writeFile({ fileName: "C:/Users/RSCH/Daleel/docs/Presentation_Application_Daleel.pptx" });
  console.log("OK written");
})().catch((e) => { console.error(e); process.exit(1); });
