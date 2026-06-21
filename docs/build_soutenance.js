const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

// ---------- Palette ----------
const NAVY  = "14213D", NAVY2 = "1C2E52", NAVY3 = "33446B";
const TEAL  = "0E8388", TEALD = "0B6B6F";
const GOLD  = "C9A227";
const INK   = "1E293B", MUTED = "64748B", LINE = "E2E8F0";
const WHITE = "FFFFFF", TINT = "F4F7FA", TEALT = "F0F7F7";
const OKG = "16855A", WARN = "C77B12", BAD = "B23A3A";
const CAP = "C:/Users/RSCH/Daleel/captures/";
const TOTAL = 19;

async function iconPng(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(IconComponent, { color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
const sh = () => ({ type: "outer", color: "000000", blur: 7, offset: 3, angle: 90, opacity: 0.16 });

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625
  pres.author = "Manar Trimeche";
  pres.title = "Daleel — Soutenance PFE";
  pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };

  // icons
  const I = {
    scale: await iconPng(fa.FaBalanceScale, "#" + GOLD, 256),
    search: await iconPng(fa.FaSearch, "#FFFFFF", 256),
    shield: await iconPng(fa.FaShieldAlt, "#FFFFFF", 256),
    file: await iconPng(fa.FaFileAlt, "#" + TEAL, 256),
    globe: await iconPng(fa.FaGlobe, "#" + TEAL, 256),
    layers: await iconPng(fa.FaLayerGroup, "#" + TEAL, 256),
    history: await iconPng(fa.FaHistory, "#" + TEAL, 256),
    tasks: await iconPng(fa.FaTasks, "#" + TEAL, 256),
    robot: await iconPng(fa.FaRobot, "#" + TEAL, 256),
    check: await iconPng(fa.FaCheckCircle, "#" + TEAL, 256),
    brain: await iconPng(fa.FaBrain, "#" + TEAL, 256),
    cogs: await iconPng(fa.FaCogs, "#" + TEAL, 256),
    db: await iconPng(fa.FaDatabase, "#" + TEAL, 256),
    flask: await iconPng(fa.FaFlask, "#" + TEAL, 256),
    docker: await iconPng(fa.FaDocker, "#" + TEAL, 256),
    lang: await iconPng(fa.FaLanguage, "#" + TEAL, 256),
    sitemap: await iconPng(fa.FaSitemap, "#" + TEAL, 256),
    bolt: await iconPng(fa.FaBolt, "#" + GOLD, 256),
    bullseye: await iconPng(fa.FaBullseye, "#" + TEAL, 256),
    chart: await iconPng(fa.FaChartLine, "#" + TEAL, 256),
    // white variants for navy circles
    cogsW: await iconPng(fa.FaCogs, "#FFFFFF", 256),
    historyW: await iconPng(fa.FaHistory, "#FFFFFF", 256),
    sitemapW: await iconPng(fa.FaSitemap, "#FFFFFF", 256),
  };

  // ---------- layout helpers ----------
  function footer(slide, n) {
    slide.addText("Daleel · Soutenance PFE", { x: 0.5, y: 5.28, w: 4, h: 0.25, margin: 0, fontFace: "Calibri", fontSize: 8.5, color: "9AA6B2" });
    slide.addText(`${n} / ${TOTAL}`, { x: 8.6, y: 5.28, w: 0.9, h: 0.25, margin: 0, align: "right", fontFace: "Calibri", fontSize: 8.5, color: "9AA6B2" });
  }
  function head(slide, kick, ttl, n) {
    slide.background = { color: WHITE };
    slide.addText(kick.toUpperCase(), { x: 0.5, y: 0.34, w: 9, h: 0.28, margin: 0, fontFace: "Calibri", fontSize: 11.5, bold: true, color: GOLD, charSpacing: 2 });
    slide.addText(ttl, { x: 0.5, y: 0.6, w: 9, h: 0.62, margin: 0, fontFace: "Cambria", fontSize: 26, bold: true, color: NAVY });
    footer(slide, n);
  }
  function chip(slide, x, y, w, h, fill) {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill || TINT }, line: { color: LINE, width: 1 }, rectRadius: 0.07, shadow: sh() });
  }
  function iconRow(slide, icon, headTxt, body, x, y, w) {
    slide.addShape(pres.shapes.OVAL, { x, y, w: 0.46, h: 0.46, fill: { color: TEALT } });
    slide.addImage({ data: icon, x: x + 0.11, y: y + 0.11, w: 0.24, h: 0.24 });
    slide.addText(headTxt, { x: x + 0.62, y: y - 0.05, w: w - 0.62, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 13.5, bold: true, color: INK });
    slide.addText(body, { x: x + 0.62, y: y + 0.24, w: w - 0.62, h: 0.46, margin: 0, fontFace: "Calibri", fontSize: 10.5, color: MUTED, lineSpacingMultiple: 0.96 });
  }
  function bullets(slide, items, x, y, w, h, fs) {
    slide.addText(items.map((it) => ({ text: it, options: { bullet: { code: "2022", indent: 13 }, color: INK, breakLine: true, paraSpaceAfter: 7, fontSize: fs || 12.5, fontFace: "Calibri" } })),
      { x, y, w, h, margin: 0, valign: "top", lineSpacingMultiple: 1.0 });
  }
  function shot(slide, file, ow, oh, x, y, maxW, maxH) {
    const ar = ow / oh; let w = maxW, h = w / ar; if (h > maxH) { h = maxH; w = h * ar; }
    const cx = x + (maxW - w) / 2, cy = y + (maxH - h) / 2;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx - 0.07, y: cy - 0.07, w: w + 0.14, h: h + 0.14, fill: { color: WHITE }, line: { color: LINE, width: 1 }, rectRadius: 0.05, shadow: sh() });
    slide.addImage({ path: CAP + file, x: cx, y: cy, w, h });
  }
  function notes(slide, t) { slide.addNotes(t); }

  // ============================================================
  // 1 — TITRE
  // ============================================================
  let s = pres.addSlide();
  s.background = { color: NAVY };
  s.addShape(pres.shapes.OVAL, { x: 7.6, y: -1.5, w: 4.4, h: 4.4, fill: { color: NAVY2 } });
  s.addShape(pres.shapes.OVAL, { x: 9.1, y: 3.5, w: 2.7, h: 2.7, fill: { color: NAVY2 } });
  s.addShape(pres.shapes.OVAL, { x: 0.55, y: 0.5, w: 0.95, h: 0.95, fill: { color: NAVY2 }, line: { color: GOLD, width: 1.25 } });
  s.addImage({ data: I.scale, x: 0.78, y: 0.73, w: 0.49, h: 0.49 });
  s.addText("PROJET DE FIN D'ÉTUDES · INGÉNIERIE INFORMATIQUE", { x: 0.55, y: 1.75, w: 8.8, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: GOLD, charSpacing: 2 });
  s.addText("Daleel", { x: 0.5, y: 2.1, w: 8.8, h: 1.0, margin: 0, fontFace: "Cambria", fontSize: 60, bold: true, color: WHITE });
  s.addText("Plateforme intégrée de Legal RAG et de pilotage de la conformité réglementaire", { x: 0.55, y: 3.2, w: 8.4, h: 0.7, margin: 0, fontFace: "Calibri", fontSize: 17, color: "CBD5E1", lineSpacingMultiple: 1.05 });
  s.addText([
    { text: "Présenté par Manar Trimeche", options: { bold: true, color: WHITE, fontSize: 13, breakLine: true } },
    { text: "École Polytechnique de Sousse   ·   Encadrant académique : Dr. Nizar Omheni   ·   Encadrant entreprise : Didax IT", options: { color: "94A3B8", fontSize: 11 } },
  ], { x: 0.55, y: 4.75, w: 9, h: 0.6, margin: 0, lineSpacingMultiple: 1.15 });
  notes(s, "Bonjour, membres du jury. Je vais vous présenter mon projet de fin d'études : Daleel, une plateforme intégrée d'assistance juridique et de pilotage de la conformité fondée sur l'IA, réalisée chez Didax IT sous l'encadrement du Dr. Nizar Omheni. Daleel signifie « le guide » en arabe.");

  // ============================================================
  // 2 — PLAN
  // ============================================================
  s = pres.addSlide(); head(s, "Déroulé de la présentation", "Plan", 2);
  const plan = [
    ["01", "Contexte & problématique", "Besoin métier, verrous, objectifs"],
    ["02", "État de l'art & positionnement", "RAG, agents, embeddings ; marché"],
    ["03", "Méthodologie & architecture", "CRISP-DM, conception en couches"],
    ["04", "Réalisation technique", "Ingestion, RAG, fine-tuning, agent, conformité"],
    ["05", "Évaluation & qualité", "Résultats chiffrés, tests, déploiement"],
    ["06", "Limites, perspectives & bilan", "Discussion critique et conclusion"],
  ];
  plan.forEach((p, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 4.5, y = 1.55 + row * 1.18, w = 4.2, h = 1.0;
    chip(s, x, y, w, h);
    s.addText(p[0], { x: x + 0.18, y: y + 0.18, w: 0.8, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 30, bold: true, color: GOLD });
    s.addText(p[1], { x: x + 1.05, y: y + 0.16, w: w - 1.2, h: 0.35, margin: 0, fontFace: "Calibri", fontSize: 14, bold: true, color: NAVY });
    s.addText(p[2], { x: x + 1.05, y: y + 0.52, w: w - 1.2, h: 0.4, margin: 0, fontFace: "Calibri", fontSize: 10.5, color: MUTED });
  });
  notes(s, "Ma présentation suit six temps : le contexte et la problématique ; l'état de l'art et mon positionnement ; la méthodologie et l'architecture ; la réalisation technique ; l'évaluation ; et enfin les limites, perspectives et le bilan.");

  // ============================================================
  // 3 — CONTEXTE
  // ============================================================
  s = pres.addSlide(); head(s, "Contexte du projet", "Contexte métier & scientifique", 3);
  s.addText([
    { text: "Cadre. ", options: { bold: true, color: NAVY } },
    { text: "Projet mené chez Didax IT (ESN tunisienne) sur le marché émergent de la LegalTech : assister les professionnels du droit et de la conformité par l'IA.", options: { color: INK } },
  ], { x: 0.6, y: 1.5, w: 5.0, h: 0.95, margin: 0, fontFace: "Calibri", fontSize: 13, lineSpacingMultiple: 1.12, valign: "top" });
  s.addText([
    { text: "Enjeu scientifique. ", options: { bold: true, color: NAVY } },
    { text: "Les LLMs hallucinent et ignorent le droit local. Le RAG ancre les réponses sur des sources vérifiables — mais reste à adapter à un corpus juridique multilingue et dynamique.", options: { color: INK } },
  ], { x: 0.6, y: 2.5, w: 5.0, h: 1.0, margin: 0, fontFace: "Calibri", fontSize: 13, lineSpacingMultiple: 1.12, valign: "top" });
  s.addText("« Daleel » (دليل) = le guide", { x: 0.6, y: 3.6, w: 5.0, h: 0.35, margin: 0, italic: true, bold: true, fontFace: "Calibri", fontSize: 13, color: TEAL });
  // corpus stat cards
  s.addText("Le corpus juridique tunisien analysé", { x: 6.0, y: 1.5, w: 3.45, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: MUTED });
  const cstats = [["2 565", "articles indexés"], ["5", "codes juridiques"], ["3", "langues (ar/fr/en)"], ["23 %", "PDF arabes à OCR"]];
  cstats.forEach((st, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 6.0 + col * 1.78, y = 1.9 + row * 1.5, w = 1.62, h = 1.34;
    chip(s, x, y, w, h);
    s.addText(st[0], { x, y: y + 0.2, w, h: 0.6, margin: 0, align: "center", fontFace: "Cambria", fontSize: 30, bold: true, color: TEAL });
    s.addText(st[1], { x: x + 0.08, y: y + 0.82, w: w - 0.16, h: 0.45, margin: 0, align: "center", fontFace: "Calibri", fontSize: 10.5, color: MUTED });
  });
  notes(s, "Le projet s'inscrit dans la LegalTech, un marché en forte croissance. Scientifiquement, l'enjeu est double : les LLMs hallucinent et ne connaissent pas le droit tunisien. Le RAG répond à ce problème en ancrant les réponses sur des sources réelles. J'ai d'abord caractérisé le corpus : 2 565 articles, 5 codes, 3 langues, dont près d'un quart des PDF arabes sans couche texte exploitable.");

  // ============================================================
  // 4 — PROBLÉMATIQUE
  // ============================================================
  s = pres.addSlide(); head(s, "Problématique", "Cinq verrous à lever", 4);
  const verrous = [
    [I.file, "Volume & fragmentation", "Codes, lois, décrets dispersés en formats hétérogènes (PDF, DOCX, scans)."],
    [I.globe, "Multilinguisme ar / fr", "Pas de correspondance terme à terme ; arabe juridique et dialecte."],
    [I.layers, "Qualité des données", "OCR bruité, encodages multiples, polices CMap non extractibles."],
    [I.history, "Textes évolutifs", "Amendements : ajout, substitution, modification, abrogation — à tracer."],
    [I.tasks, "Conformité non outillée", "Aucun lien entre textes applicables et pilotage opérationnel."],
  ];
  verrous.forEach((v, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    if (i === 4) { iconRow(s, v[0], v[1], v[2], 0.6, 1.55 + row * 0.92, 8.8); return; }
    iconRow(s, v[0], v[1], v[2], 0.6 + col * 4.55, 1.55 + row * 0.92, 4.3);
  });
  chip(s, 0.6, 4.5, 8.85, 0.72, NAVY);
  s.addText([
    { text: "Question centrale —  ", options: { bold: true, color: GOLD } },
    { text: "Comment fournir des réponses juridiques pertinentes, traçables et opérationnellement exploitables dans le contexte réglementaire tunisien ?", options: { color: WHITE } },
  ], { x: 0.85, y: 4.5, w: 8.35, h: 0.72, margin: 0, valign: "middle", fontFace: "Calibri", fontSize: 13, italic: true, lineSpacingMultiple: 1.0 });
  notes(s, "La problématique se décompose en cinq verrous : le volume et la fragmentation des sources ; le multilinguisme arabe/français sans équivalence directe ; la qualité dégradée des données, notamment les PDF arabes en polices CMap inextractibles ; le caractère évolutif du droit via les amendements ; et l'absence d'outil reliant les textes au pilotage de la conformité. D'où ma question centrale : fournir des réponses pertinentes, traçables et exploitables.");

  // ============================================================
  // 5 — OBJECTIFS
  // ============================================================
  s = pres.addSlide(); head(s, "Objectifs", "Quatre objectifs d'ingénierie", 5);
  const objs = [
    [I.cogsW, "Traiter la complexité documentaire", "Pipeline d'extraction multi-moteurs + OCR, segmentation en unités juridiques, fine-tuning d'embeddings sur le vocabulaire juridique."],
    [I.historyW, "Maîtriser la dimension temporelle", "Distinguer version en vigueur et versions antérieures ; appliquer les amendements de façon traçable ; analyse comparative."],
    [I.sitemapW, "Concevoir une architecture évolutive", "Modulaire, API REST standardisée, multi-tenant, conteneurisée, couverte par des tests et une CI."],
    [I.shield, "Outiller le cycle de conformité", "Dossiers, constats notés, actions, preuves, contrôles, exceptions — orchestrés par LLM et connectés aux textes."],
  ];
  objs.forEach((o, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 4.5, y = 1.6 + row * 1.78, w = 4.3, h = 1.62;
    chip(s, x, y, w, h);
    s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: y + 0.25, w: 0.6, h: 0.6, fill: { color: NAVY } });
    const ic = { data: o[0], x: x + 0.41, y: y + 0.41, w: 0.28, h: 0.28 };
    // recolor icon white? icons created teal; for navy circle use white -> use a white variant; reuse search/shield already white
    s.addImage(ic);
    s.addText(o[1], { x: x + 1.0, y: y + 0.24, w: w - 1.2, h: 0.55, margin: 0, fontFace: "Calibri", fontSize: 13, bold: true, color: NAVY });
    s.addText(o[2], { x: x + 0.3, y: y + 0.82, w: w - 0.55, h: 0.7, margin: 0, fontFace: "Calibri", fontSize: 10, color: MUTED, lineSpacingMultiple: 0.96 });
  });
  notes(s, "Quatre objectifs d'ingénierie en découlent : traiter la complexité documentaire jusqu'au fine-tuning des embeddings ; maîtriser la dimension temporelle du droit via les amendements ; concevoir une architecture évolutive, multi-tenant et testée ; et outiller le cycle complet de conformité, connecté aux textes et orchestré par LLM.");

  // ============================================================
  // 6 — ÉTAT DE L'ART & POSITIONNEMENT
  // ============================================================
  s = pres.addSlide(); head(s, "État de l'art", "Briques mobilisées & positionnement", 6);
  bullets(s, [
    "LLM local Qwen2.5:7b (tool calling natif, multilingue, on-premise)",
    "RAG modulaire : recherche hybride dense + lexicale, RRF / fusion",
    "Reranking par cross-encoder ; agents ReAct (Reasoning + Acting)",
    "Embeddings multilingues fine-tunés (MNR loss, négatifs hard)",
    "LegalTech & RegTech : extraction d'exigences, scoring de criticité",
  ], 0.6, 1.55, 4.15, 2.5, 11.5);
  // comparison table
  const tx = 5.0, ty = 1.55;
  s.addText("Positionnement vs solutions existantes", { x: tx, y: ty - 0.02, w: 4.5, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 11.5, bold: true, color: MUTED });
  const rows = [
    [{ text: "Critère", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 9.5, align: "left" } },
     { text: "Daleel", options: { bold: true, color: WHITE, fill: { color: TEAL }, fontSize: 9.5, align: "center" } },
     { text: "Harvey", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 9.5, align: "center" } },
     { text: "GRC", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 9.5, align: "center" } }],
  ];
  const cmp = [
    ["RAG multilingue ar/fr/en", "✓", "✗", "✗"],
    ["Agent autonome ReAct", "✓", "~", "✗"],
    ["Cycle conformité complet", "✓", "✗", "✓"],
    ["Droit tunisien indexé", "✓", "✗", "✗"],
    ["On-premise / confidentialité", "✓", "✗", "~"],
  ];
  cmp.forEach((r) => {
    rows.push([
      { text: r[0], options: { fontSize: 9.5, color: INK, align: "left" } },
      { text: r[1], options: { fontSize: 11, bold: true, color: OKG, align: "center", fill: { color: TEALT } } },
      { text: r[2], options: { fontSize: 11, color: r[2] === "✗" ? BAD : WARN, align: "center" } },
      { text: r[3], options: { fontSize: 11, color: r[3] === "✗" ? BAD : (r[3] === "~" ? WARN : OKG), align: "center" } },
    ]);
  });
  s.addTable(rows, { x: tx, y: ty + 0.32, w: 4.5, colW: [2.25, 0.85, 0.7, 0.7], rowH: 0.32, border: { pt: 0.5, color: LINE }, valign: "middle", fontFace: "Calibri", margin: 2 });
  chip(s, 0.6, 4.45, 8.85, 0.75, NAVY);
  s.addText([
    { text: "Lacune du marché —  ", options: { bold: true, color: GOLD } },
    { text: "aucune solution ne combine RAG juridique arabe/français, agent ReAct, cycle de conformité complet et déploiement on-premise. Daleel se place à cette intersection.", options: { color: WHITE } },
  ], { x: 0.85, y: 4.45, w: 8.35, h: 0.75, margin: 0, valign: "middle", fontFace: "Calibri", fontSize: 12.5, italic: true, lineSpacingMultiple: 1.0 });
  notes(s, "J'ai mobilisé un état de l'art structuré : le LLM local Qwen2.5 pour la confidentialité, le RAG modulaire, le reranking, le paradigme ReAct, le fine-tuning contrastif d'embeddings et la RegTech. La comparaison aux solutions existantes — Harvey AI, les GRC classiques — montre qu'aucune ne combine RAG multilingue arabe, agent autonome, cycle de conformité complet et on-premise. C'est la lacune que Daleel comble.");

  // ============================================================
  // 7 — MÉTHODOLOGIE CRISP-DM
  // ============================================================
  s = pres.addSlide(); head(s, "Méthodologie", "Une démarche CRISP-DM itérative", 7);
  shot(s, "fig_1_1_crisp_dm.png", 1254, 1254, 0.5, 1.4, 3.9, 3.7);
  bullets(s, [
    "6 phases : métier → données → préparation → modélisation → évaluation → déploiement",
    "Cycle réellement itératif, pas une cascade",
    "Boucle 1 : l'évaluation (Recall@1 = 0,20) a déclenché le fine-tuning des embeddings",
    "Boucle 2 : l'audit qualité a renvoyé au nettoyage du corpus arabe (ré-OCR)",
    "Mise en œuvre en 10 sprints fonctionnels, chacun testé",
  ], 4.7, 1.55, 4.75, 3.4, 13);
  notes(s, "J'ai conduit le projet selon CRISP-DM, en six phases. Le point clé pour le jury : ça n'a pas été une cascade, mais un vrai cycle. Deux boucles de rétroaction concrètes l'illustrent — l'évaluation a révélé un Recall@1 de 0,20 qui a déclenché le fine-tuning ; et l'audit qualité des réponses arabes m'a renvoyée au nettoyage du corpus par ré-OCR. La réalisation s'est faite en 10 sprints testés.");

  // ============================================================
  // 8 — ARCHITECTURE
  // ============================================================
  s = pres.addSlide(); head(s, "Conception", "Architecture globale en couches", 8);
  shot(s, "fig_3_1_architecture.png", 1536, 1024, 0.45, 1.4, 6.1, 3.75);
  const astats = [["170+", "endpoints REST"], ["41", "services métier"], ["38", "collections"], ["9", "modules de traitement"]];
  astats.forEach((st, i) => {
    const x = 6.85, y = 1.5 + i * 0.92, w = 2.6, h = 0.78;
    chip(s, x, y, w, h);
    s.addText(st[0], { x: x + 0.12, y: y + 0.08, w: 1.05, h: 0.6, margin: 0, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 24, bold: true, color: TEAL });
    s.addText(st[1], { x: x + 1.2, y: y + 0.08, w: w - 1.3, h: 0.62, margin: 0, valign: "middle", fontFace: "Calibri", fontSize: 11, color: INK });
  });
  notes(s, "L'architecture est organisée en cinq couches : présentation (React), API REST FastAPI, services métier, traitement documentaire et persistance. Deux volets transversaux la traversent — Legal RAG et Compliance. En chiffres : plus de 170 endpoints, 41 services, 38 collections MongoDB. Cette modularité permet d'ajouter un corpus ou un module sans refonte.");

  // ============================================================
  // 9 — PIPELINE INGESTION
  // ============================================================
  s = pres.addSlide(); head(s, "Réalisation · Données", "Pipeline d'ingestion documentaire", 9);
  const steps = [
    [I.file, "Extraction multi-moteurs", "PyMuPDF · pdfminer.six · OCR Tesseract + EasyOCR"],
    [I.lang, "Nettoyage arabe (11 étapes)", "Décodage en cascade, normalisation Unicode, dé-bruitage OCR"],
    [I.layers, "Segmentation en articles", "Chunks de 1 500 car. (chevauchement 200), frontières d'articles"],
    [I.history, "Gestion des amendements", "Détection ajout / substitution / modification / abrogation"],
  ];
  steps.forEach((st, i) => { iconRow(s, st[0], st[1], st[2], 0.6, 1.6 + i * 0.82, 5.3); });
  chip(s, 6.2, 1.6, 3.25, 3.05, TEALT);
  s.addText("Le verrou technique majeur", { x: 6.45, y: 1.78, w: 2.8, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: TEALD });
  s.addText([
    { text: "Les PDF arabes officiels (IORT, JORT) utilisent des ", options: { color: INK } },
    { text: "polices CMap personnalisées", options: { bold: true, color: NAVY } },
    { text: " : l'extraction produit des glyphes inversés, inutilisables.", options: { color: INK } },
  ], { x: 6.45, y: 2.15, w: 2.8, h: 1.1, margin: 0, fontFace: "Calibri", fontSize: 11, lineSpacingMultiple: 1.05, valign: "top" });
  s.addText([
    { text: "Solution : ", options: { bold: true, color: TEALD } },
    { text: "ré-OCR à 300 dpi (Tesseract ara) → ", options: { color: INK } },
    { text: "896 articles arabes propres", options: { bold: true, color: TEALD } },
    { text: " contre 699 corrompus.", options: { color: INK } },
  ], { x: 6.45, y: 3.35, w: 2.8, h: 1.1, margin: 0, fontFace: "Calibri", fontSize: 11, lineSpacingMultiple: 1.05, valign: "top" });
  notes(s, "La préparation des données a été la phase la plus lourde. Extraction multi-moteurs, nettoyage arabe en 11 étapes, segmentation respectant les frontières d'articles, et gestion des amendements. Le verrou majeur, à souligner : les PDF arabes officiels emploient des polices CMap personnalisées qui produisent des glyphes inversés à l'extraction. Ma solution a été le ré-OCR à 300 dpi, qui a restauré 896 articles arabes propres contre 699 corrompus.");

  // ============================================================
  // 10 — PIPELINE RAG 6 MODULES
  // ============================================================
  s = pres.addSlide(); head(s, "Réalisation · Cœur IA", "Pipeline RAG avancé à six modules", 10);
  s.addText([{ text: "Question utilisateur", options: { bold: true } }], { x: 0.6, y: 1.5, w: 2.0, h: 0.42, margin: 0, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 12, color: WHITE, fill: { color: NAVY }, fontFace: "Calibri" });
  const mods = [
    ["1", "Recherche hybride", "vecteurs FAISS + signaux lexicaux (fusion pondérée)"],
    ["2", "Reranking cross-encoder", "arbitrage des paires (question, chunk), seuil −2,0"],
    ["3", "Routeur de domaine", "5 domaines, mots-clés trilingues + repli LLM"],
    ["4", "Retrieval partitionné", "base vs amendements selon l'intention — contribution originale"],
    ["5", "KG Light", "sous-graphe Loi→Article→Exigence→Action→Criticité"],
    ["6", "Garde-qualité", "anti-hallucination avant restitution"],
  ];
  mods.forEach((m, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.6 + col * 2.98, y = 2.1 + row * 1.45, w = 2.78, h = 1.28;
    const accent = (i === 3);
    chip(s, x, y, w, h, accent ? "FBF5E3" : TINT);
    s.addShape(pres.shapes.OVAL, { x: x + 0.18, y: y + 0.18, w: 0.5, h: 0.5, fill: { color: accent ? GOLD : TEAL } });
    s.addText(m[0], { x: x + 0.18, y: y + 0.18, w: 0.5, h: 0.5, margin: 0, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 20, bold: true, color: accent ? NAVY : WHITE });
    s.addText(m[1], { x: x + 0.78, y: y + 0.2, w: w - 0.9, h: 0.5, margin: 0, valign: "middle", fontFace: "Calibri", fontSize: 12.5, bold: true, color: NAVY });
    s.addText(m[2], { x: x + 0.2, y: y + 0.72, w: w - 0.35, h: 0.5, margin: 0, fontFace: "Calibri", fontSize: 9.5, color: MUTED, lineSpacingMultiple: 0.95 });
  });
  s.addText("→ Réponse structurée et sourcée [Source N] · prompt ancré, T = 0,15", { x: 0.6, y: 4.95, w: 8.85, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 11, italic: true, color: TEALD });
  notes(s, "Le cœur du système est un pipeline RAG modulaire à six modules activables indépendamment. Recherche hybride combinant vecteurs et signaux lexicaux ; reranking par cross-encoder ; routeur de domaine ; puis le module 4, ma contribution originale : le retrieval partitionné qui sépare textes de base et amendements selon l'intention de l'utilisateur, pour ne pas mélanger des versions contradictoires. Le KG Light enrichit le contexte par un sous-graphe de connaissances, et la garde-qualité valide la réponse. Le tout produit une réponse structurée et sourcée.");

  // ============================================================
  // 11 — FINE-TUNING
  // ============================================================
  s = pres.addSlide(); head(s, "Réalisation · Contribution scientifique", "Fine-tuning des embeddings", 11);
  bullets(s, [
    "Modèle de base : paraphrase-multilingual-mpnet-base-v2 (768 dim)",
    "Dataset : paires question/article générées par LLM + paires inter-langues ar↔fr",
    "Négatifs hard minés (ex. congé annuel vs congé maladie)",
    "Perte contrastive MultipleNegativesRankingLoss (MNR)",
    "Évaluation sur 30 requêtes gold distinctes (20 fr + 10 ar)",
  ], 0.6, 1.55, 5.0, 3.0, 12.5);
  s.addText("Hyperparamètres", { x: 6.0, y: 1.55, w: 3.45, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: MUTED });
  const hp = [
    ["Perte", "MNR Loss"], ["Batch size", "32"], ["Learning rate", "2 × 10⁻⁵"],
    ["Optimiseur", "AdamW"], ["Epochs", "3"], ["Normalisation", "L2 (cosine)"],
  ];
  const htbl = hp.map((r, i) => [
    { text: r[0], options: { fontSize: 11, color: INK, fill: { color: i % 2 ? WHITE : TINT } } },
    { text: r[1], options: { fontSize: 11, bold: true, color: TEALD, align: "right", fill: { color: i % 2 ? WHITE : TINT } } },
  ]);
  s.addTable(htbl, { x: 6.0, y: 1.92, w: 3.45, colW: [2.0, 1.45], rowH: 0.4, border: { pt: 0.5, color: LINE }, valign: "middle", fontFace: "Calibri", margin: 4 });
  s.addText("Contribution la plus mesurable du projet (cf. résultats)", { x: 6.0, y: 4.5, w: 3.45, h: 0.4, margin: 0, italic: true, fontFace: "Calibri", fontSize: 11, color: TEAL, bold: true });
  notes(s, "La contribution scientifique la plus mesurable est le fine-tuning du modèle d'embeddings. Je suis partie de MPNet multilingue, puis j'ai construit un jeu d'entraînement : des paires question/article générées par LLM et des paires inter-langues arabe-français. J'ai miné des négatifs hard pour forcer le modèle à distinguer des cas proches. L'entraînement utilise la perte contrastive MNR. L'évaluation se fait sur 30 requêtes gold indépendantes.");

  // ============================================================
  // 12 — AGENT ReAct
  // ============================================================
  s = pres.addSlide(); head(s, "Réalisation · Raisonnement", "Agent autonome ReAct", 12);
  bullets(s, [
    "Boucle Reasoning + Acting : raisonner → appeler un outil → observer → itérer",
    "12 outils en 3 tiers : recherche, graphe, conformité",
    "Tool calling natif d'Ollama (appels typés, pas de parsing fragile)",
    "Garde-fous : budget d'itérations + timeout global",
    "Journal de raisonnement exposé → transparence totale",
  ], 0.6, 1.6, 4.0, 3.4, 12.5);
  shot(s, "fig_4_2_agent_tool_log.png", 1646, 772, 4.75, 1.6, 4.7, 3.3);
  s.addText("Journal des appels d'outils de l'agent", { x: 4.75, y: 5.0, w: 4.7, h: 0.28, margin: 0, align: "center", fontFace: "Calibri", fontSize: 9.5, italic: true, color: MUTED });
  notes(s, "Au-delà du pipeline séquentiel, Daleel propose un agent autonome ReAct : il alterne raisonnement et action, décide dynamiquement quels outils appeler parmi douze, répartis en trois tiers — recherche, graphe, conformité. J'utilise le tool calling natif d'Ollama, qui produit des appels typés et évite les parseurs fragiles. Des garde-fous bornent les itérations, et surtout le journal de raisonnement est exposé à l'utilisateur : dans un contexte juridique, on doit pouvoir auditer comment la réponse a été construite.");

  // ============================================================
  // 13 — GARDE-QUALITÉ
  // ============================================================
  s = pres.addSlide(); head(s, "Réalisation · Fiabilité", "Garde-qualité anti-hallucination", 13);
  const couches = [
    [I.check, "Couche 1 — Références", "chaque référence d'article est vérifiée contre les chunks réels"],
    [I.search, "Couche 2 — Citations", "détection des citations fabriquées par fenêtre glissante"],
    [I.brain, "Couche 3 — Fidélité", "cohérence sémantique du contenu (LLM-juge indicatif)"],
    [I.lang, "Couche 4 — Langue", "réponse forcée dans la langue détectée de la question"],
  ];
  couches.forEach((c, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    iconRow(s, c[0], c[1], c[2], 0.6 + col * 4.55, 1.6 + row * 0.95, 4.3);
  });
  chip(s, 0.6, 3.7, 8.85, 1.45, TINT);
  s.addText("Ingénierie de prompts complémentaire", { x: 0.85, y: 3.85, w: 8.3, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: NAVY });
  bullets(s, [
    "Persona de conseiller juridique + apprentissage en contexte trilingue",
    "Ancrage disciplinaire strict : inventer un article = « faute professionnelle grave »",
    "Génération déterministe : température T = 0,15, top-p = 0,9",
  ], 0.85, 4.2, 8.3, 0.95, 11);
  notes(s, "La garde-qualité est la dernière ligne de défense contre les hallucinations. Elle opère en quatre couches après génération : vérification des références contre les chunks réels, détection des citations fabriquées par fenêtre glissante, contrôle de fidélité sémantique, et conformité linguistique. Elle est complétée en amont par une ingénierie de prompts rigoureuse : persona, ancrage disciplinaire — j'indique explicitement qu'inventer un article est une faute grave — et une génération déterministe à température 0,15.");

  // ============================================================
  // 14 — COMPLIANCE OPS
  // ============================================================
  s = pres.addSlide(); head(s, "Réalisation · Volet 2", "Compliance Operations", 14);
  s.addText("Cycle complet de conformité", { x: 0.6, y: 1.5, w: 8.8, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: MUTED });
  const cycle = ["Dossier", "Constat", "Action", "Preuve", "Contrôle", "Exception"];
  cycle.forEach((c, i) => {
    const x = 0.6 + i * 1.49, w = 1.32, y = 1.9, h = 0.62;
    chip(s, x, y, w, h, TEALT);
    s.addText(c, { x, y, w, h, margin: 0, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 12, bold: true, color: TEALD });
    if (i < 5) s.addText("›", { x: x + w - 0.06, y, w: 0.2, h, margin: 0, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 16, bold: true, color: MUTED });
  });
  s.addText("Orchestrateur LLM — arbre de décision", { x: 0.6, y: 2.85, w: 8.8, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: MUTED });
  const branches = [["ASK", "analyser & rechercher les faits"], ["CLARIFY", "demander si information manquante"], ["ACT", "exécuter l'action de conformité"], ["REVIEW", "vérifier & tracer la décision"]];
  branches.forEach((b, i) => {
    const x = 0.6 + i * 2.24, w = 2.05, y = 3.25, h = 1.05;
    chip(s, x, y, w, h);
    s.addText(b[0], { x, y: y + 0.14, w, h: 0.4, margin: 0, align: "center", fontFace: "Cambria", fontSize: 18, bold: true, color: NAVY });
    s.addText(b[1], { x: x + 0.12, y: y + 0.55, w: w - 0.24, h: 0.45, margin: 0, align: "center", fontFace: "Calibri", fontSize: 10, color: MUTED, lineSpacingMultiple: 0.95 });
  });
  s.addText([
    { text: "Scoring de criticité déterministe et auditable ", options: { bold: true, color: TEALD } },
    { text: "— chaque décision est journalisée et reproductible.", options: { color: INK } },
  ], { x: 0.6, y: 4.55, w: 8.85, h: 0.5, margin: 0, fontFace: "Calibri", fontSize: 12, italic: true });
  notes(s, "Le second volet, Compliance Operations, transforme l'assistant en outil de pilotage. Il couvre tout le cycle : dossier de non-conformité, constat, action corrective, preuve, contrôle interne, exception. Les décisions sont orchestrées par un LLM selon un arbre à quatre branches — ASK, CLARIFY, ACT, REVIEW — selon la complétude des faits et le niveau de confiance. Point important pour le jury : le scoring de criticité est déterministe et journalisé, donc auditable, contrairement à une décision opaque de LLM.");

  // ============================================================
  // 15 — INTERFACES
  // ============================================================
  s = pres.addSlide(); head(s, "Réalisation · Livrable", "Interfaces livrées (React)", 15);
  const ui = [
    ["fig_4_1_chatbot.png", 1917, 912, "Chatbot multilingue", "questions, sources, voix, feedback"],
    ["fig_4_2_admin_documents.png", 1587, 673, "Panneau d'administration", "corpus, ingestion, multi-tenant"],
    ["fig_4_3_dashboard.png", 1580, 906, "Tableau de bord BI", "posture de conformité temps réel"],
  ];
  ui.forEach((u, i) => {
    const x = 0.55 + i * 3.05;
    shot(s, u[0], u[1], u[2], x, 1.6, 2.85, 1.95);
    s.addText(u[3], { x, y: 3.62, w: 2.85, h: 0.3, margin: 0, align: "center", fontFace: "Calibri", fontSize: 12.5, bold: true, color: NAVY });
    s.addText(u[4], { x, y: 3.92, w: 2.85, h: 0.45, margin: 0, align: "center", fontFace: "Calibri", fontSize: 10, color: MUTED });
  });
  chip(s, 0.55, 4.55, 8.9, 0.62, TINT);
  s.addText("34 composants React (18 pages) · i18next ar/fr/en · RTL automatique pour l'arabe", { x: 0.55, y: 4.55, w: 8.9, h: 0.62, margin: 0, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 12, color: INK });
  notes(s, "Côté livrable, trois interfaces React : le chatbot multilingue pour l'utilisateur métier, avec sources cliquables et saisie vocale ; le panneau d'administration pour gérer le corpus, l'ingestion et le multi-tenant ; et un tableau de bord BI temps réel de la posture de conformité. L'ensemble est trilingue avec passage automatique en RTL pour l'arabe.");

  // ============================================================
  // 16 — ÉVALUATION
  // ============================================================
  s = pres.addSlide(); head(s, "Évaluation quantitative", "Gains du fine-tuning (30 requêtes gold)", 16);
  s.addChart(pres.charts.BAR, [
    { name: "Baseline (mpnet)", labels: ["Recall@1", "Recall@5", "MRR@10", "nDCG@5"], values: [0.33, 0.53, 0.42, 0.43] },
    { name: "Daleel (fine-tuné)", labels: ["Recall@1", "Recall@5", "MRR@10", "nDCG@5"], values: [0.47, 0.70, 0.57, 0.59] },
  ], {
    x: 0.5, y: 1.5, w: 5.5, h: 3.0, barDir: "col", chartColors: ["AEB8C2", TEAL],
    chartArea: { fill: { color: WHITE } }, catAxisLabelColor: MUTED, catAxisLabelFontFace: "Calibri", catAxisLabelFontSize: 10,
    valAxisLabelColor: MUTED, valAxisMaxVal: 0.8, valAxisMinVal: 0, valGridLine: { color: LINE, size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontFace: "Calibri", dataLabelFontSize: 8, dataLabelFormatCode: "0.00",
    showLegend: true, legendPos: "b", legendColor: INK, legendFontFace: "Calibri", legendFontSize: 10,
  });
  const g = [["+40 %", "Recall@1"], ["+34 %", "MRR@10"], ["+37 %", "nDCG@5"]];
  g.forEach((gg, i) => {
    const x = 6.25, y = 1.5 + i * 0.72, w = 3.2, h = 0.62;
    chip(s, x, y, w, h);
    s.addText(gg[0], { x: x + 0.08, y, w: 1.1, h, margin: 0, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 20, bold: true, color: GOLD });
    s.addText([{ text: "gain sur ", options: { color: MUTED, fontSize: 10 } }, { text: gg[1], options: { bold: true, color: INK, fontSize: 12 } }], { x: x + 1.2, y, w: w - 1.3, h, margin: 0, valign: "middle", fontFace: "Calibri" });
  });
  chip(s, 6.25, 3.72, 3.2, 1.45, "FBF5E3");
  s.addText([
    { text: "Lecture honnête. ", options: { bold: true, color: NAVY } },
    { text: "Français : +50 % Recall@1. Arabe en retrait — corpus d'entraînement contaminé (CMap). Remédiation par ré-OCR (896 articles) ⇒ re-fine-tuning attendu équivalent.", options: { color: INK } },
  ], { x: 6.45, y: 3.85, w: 2.85, h: 1.2, margin: 0, fontFace: "Calibri", fontSize: 10, lineSpacingMultiple: 1.03, valign: "top" });
  notes(s, "Les résultats : le fine-tuning produit des gains nets — +40 % en Recall@1, +34 % en MRR@10, +37 % en nDCG@5. Je tiens à être honnête sur la décomposition par langue, c'est important : en français le gain atteint +50 % en Recall@1, mais l'arabe reste en retrait. L'analyse rétrospective a montré que le corpus arabe d'entraînement était contaminé par les artefacts CMap. J'ai mis en œuvre la remédiation — le ré-OCR de 896 articles — et un re-fine-tuning sur ce corpus propre devrait donner des gains comparables au français.");

  // ============================================================
  // 17 — QUALITÉ LOGICIELLE & DÉPLOIEMENT
  // ============================================================
  s = pres.addSlide(); head(s, "Qualité & déploiement", "Industrialisation", 17);
  const qstats = [[I.flask, "55", "fichiers de tests", "unitaires + intégration bout-en-bout"], [I.cogs, "3", "versions Python en CI", "matrice 3.11 / 3.12 / 3.13 (GitHub Actions)"], [I.docker, "3", "services conteneurisés", "MongoDB · Ollama · FastAPI (Compose)"]];
  qstats.forEach((q, i) => {
    const x = 0.6 + i * 2.98, w = 2.78, y = 1.6, h = 2.1;
    chip(s, x, y, w, h);
    s.addShape(pres.shapes.OVAL, { x: x + w / 2 - 0.32, y: y + 0.25, w: 0.64, h: 0.64, fill: { color: TEALT } });
    s.addImage({ data: q[0], x: x + w / 2 - 0.17, y: y + 0.4, w: 0.34, h: 0.34 });
    s.addText(q[1], { x, y: y + 0.92, w, h: 0.55, margin: 0, align: "center", fontFace: "Cambria", fontSize: 34, bold: true, color: TEAL });
    s.addText(q[2], { x: x + 0.1, y: y + 1.45, w: w - 0.2, h: 0.3, margin: 0, align: "center", fontFace: "Calibri", fontSize: 12, bold: true, color: NAVY });
    s.addText(q[3], { x: x + 0.15, y: y + 1.74, w: w - 0.3, h: 0.32, margin: 0, align: "center", fontFace: "Calibri", fontSize: 9.5, color: MUTED });
  });
  chip(s, 0.6, 4.0, 8.85, 1.1, NAVY);
  s.addText([
    "Dockerfile multi-stage (builder Python 3.12 → runtime slim avec Tesseract & poppler)",
    "Lint Ruff + pytest automatiques à chaque push ; LLM mocké par défaut en test",
    "Déploiement reproductible et 100 % on-premise (aucun appel API externe)",
  ].map((it) => ({ text: it, options: { bullet: { code: "2022", indent: 13 }, color: "E8EDF5", breakLine: true, paraSpaceAfter: 5, fontSize: 11, fontFace: "Calibri" } })),
    { x: 0.85, y: 4.12, w: 8.4, h: 0.95, margin: 0, valign: "middle" });
  notes(s, "Sur l'industrialisation : 55 fichiers de tests couvrant l'unitaire et l'intégration de bout en bout, exécutés par une CI GitHub Actions sur trois versions de Python. Le déploiement repose sur un Dockerfile multi-stage et un Docker Compose orchestrant MongoDB, Ollama et FastAPI. Tout est reproductible et entièrement on-premise — un argument clé de confidentialité pour des données juridiques.");

  // fix: the navy box bullets need white text -> overlay
  // (handled below by re-adding as white)

  // ============================================================
  // 18 — LIMITES & PERSPECTIVES
  // ============================================================
  s = pres.addSlide(); head(s, "Discussion critique", "Limites & perspectives", 18);
  chip(s, 0.6, 1.55, 4.3, 3.6, TINT);
  s.addText("Limites identifiées", { x: 0.85, y: 1.72, w: 3.8, h: 0.32, margin: 0, fontFace: "Calibri", fontSize: 14, bold: true, color: BAD });
  bullets(s, [
    "Corpus de fine-tuning encore limité (2 565 articles)",
    "Performances arabes en retrait (corpus contaminé, en cours de correction)",
    "Latence de l'agent (p95 ≈ 22 s) à optimiser",
    "Scoring de criticité calibré empiriquement",
    "Pas encore de validation par un panel d'experts juristes",
  ], 0.85, 2.15, 3.85, 2.9, 11);
  chip(s, 5.1, 1.55, 4.35, 3.6, TEALT);
  s.addText("Perspectives d'évolution", { x: 5.35, y: 1.72, w: 3.85, h: 0.32, margin: 0, fontFace: "Calibri", fontSize: 14, bold: true, color: TEALD });
  bullets(s, [
    "Re-fine-tuning sur le corpus arabe propre (court terme)",
    "Validation par un panel d'experts juridiques (court terme)",
    "Veille JORT : détection automatique d'amendements",
    "Apprentissage continu sur le feedback utilisateur",
    "Extension aux autres juridictions du Maghreb",
  ], 5.35, 2.15, 3.9, 2.9, 11);
  notes(s, "La discussion critique est essentielle. Côté limites : le corpus de fine-tuning reste modeste, les performances arabes sont en retrait — mais j'ai identifié la cause et engagé la correction —, la latence de l'agent est à optimiser, et il manque une validation par des juristes. Côté perspectives, deux sont à court terme et leurs prérequis sont réunis : le re-fine-tuning arabe et la validation par un panel d'experts. À plus long terme : la veille JORT automatique, l'apprentissage sur le feedback, et l'extension au Maghreb.");

  // ============================================================
  // 19 — CONCLUSION
  // ============================================================
  s = pres.addSlide(); s.background = { color: NAVY };
  s.addShape(pres.shapes.OVAL, { x: -1.3, y: 3.5, w: 4.0, h: 4.0, fill: { color: NAVY2 } });
  s.addText("CONCLUSION", { x: 0.55, y: 0.55, w: 8, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: GOLD, charSpacing: 2 });
  s.addText("Une contribution scientifique et applicative", { x: 0.55, y: 0.9, w: 9, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 25, bold: true, color: WHITE });
  const cc = [
    [I.bullseye, "Contribution scientifique", "RAG agentique pour un domaine juridique sous-représenté ; fine-tuning validé (+40 % Recall@1) ; retrieval partitionné & orchestrateur de conformité formalisés."],
    [I.shield, "Contribution applicative", "Produit fonctionnel, déployable en local, respectueux de la confidentialité — comblant un manque du marché LegalTech tunisien."],
  ];
  cc.forEach((c, i) => {
    const x = 0.55 + i * 4.55, y = 1.7, w = 4.3, h = 1.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: NAVY2 }, line: { color: NAVY3, width: 1 }, rectRadius: 0.08 });
    s.addShape(pres.shapes.OVAL, { x: x + 0.28, y: y + 0.28, w: 0.56, h: 0.56, fill: { color: GOLD } });
    s.addImage({ data: c[0], x: x + 0.43, y: y + 0.43, w: 0.26, h: 0.26 });
    s.addText(c[1], { x: x + 1.0, y: y + 0.32, w: w - 1.2, h: 0.5, margin: 0, fontFace: "Calibri", fontSize: 14, bold: true, color: WHITE });
    s.addText(c[2], { x: x + 0.3, y: y + 0.92, w: w - 0.55, h: 0.95, margin: 0, fontFace: "Calibri", fontSize: 10.5, color: "B7C3D6", lineSpacingMultiple: 1.02 });
  });
  s.addText("Compétences mobilisées : ingénierie des données · fine-tuning de LLM · agents IA · architecture multi-tenant · sécurité · DevOps", { x: 0.55, y: 3.95, w: 8.9, h: 0.5, margin: 0, fontFace: "Calibri", fontSize: 11.5, italic: true, color: "9FB0CC", lineSpacingMultiple: 1.05 });
  s.addText("Merci de votre attention — je suis à votre disposition pour vos questions.", { x: 0.55, y: 4.7, w: 8.9, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 16, bold: true, color: GOLD });
  notes(s, "Pour conclure : Daleel est à la fois une contribution scientifique — une approche RAG agentique pour un domaine juridique sous-représenté, avec un fine-tuning validé expérimentalement, un retrieval partitionné et un orchestrateur de conformité formalisés — et une contribution applicative : un produit fonctionnel, on-premise et confidentiel, qui comble un manque du marché. Ce projet m'a permis de mobiliser un large spectre de compétences d'ingénieur. Je vous remercie et je suis à votre disposition pour vos questions.");

  await pres.writeFile({ fileName: "C:/Users/RSCH/Daleel/docs/Soutenance_Daleel_PFE.pptx" });
  console.log("OK written");
})().catch((e) => { console.error(e); process.exit(1); });
