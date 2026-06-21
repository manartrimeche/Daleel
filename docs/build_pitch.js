const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

// ---------- Brand palette (marketing) ----------
const NAVY = "10203F", NAVY2 = "1A2E54", NAVY3 = "2C4068";
const TEAL = "0E9488", TEALL = "16B5A6", TEALD = "0B6F6A";
const GOLD = "D4A82A", GOLDL = "E8C24E";
const INK = "16233B", MUTED = "5B6B82", LINE = "E4E9F0";
const WHITE = "FFFFFF", MIST = "F4F8FA", TEALT = "EAF6F4", GOLDT = "FBF3DC";
const CAP = "C:/Users/RSCH/Daleel/captures/";

async function iconPng(IconComponent, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(IconComponent, { color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
const sh = () => ({ type: "outer", color: "000000", blur: 9, offset: 3, angle: 90, opacity: 0.18 });
const shG = () => ({ type: "outer", color: "0E9488", blur: 12, offset: 4, angle: 90, opacity: 0.25 });

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Daleel";
  pres.title = "Daleel — Pitch";

  const I = {
    scaleG: await iconPng(fa.FaBalanceScale, "#" + GOLD, 256),
    bolt: await iconPng(fa.FaBolt, "#FFFFFF", 256),
    shield: await iconPng(fa.FaShieldAlt, "#FFFFFF", 256),
    check: await iconPng(fa.FaCheckDouble, "#FFFFFF", 256),
    globe: await iconPng(fa.FaGlobe, "#FFFFFF", 256),
    lock: await iconPng(fa.FaLock, "#FFFFFF", 256),
    search: await iconPng(fa.FaCommentDots, "#FFFFFF", 256),
    tasks: await iconPng(fa.FaClipboardCheck, "#FFFFFF", 256),
    arrow: await iconPng(fa.FaArrowRight, "#" + GOLD, 256),
    quote: await iconPng(fa.FaRobot, "#FFFFFF", 256),
    // light-bg teal icons for "pour qui"
    gavel: await iconPng(fa.FaGavel, "#" + TEAL, 256),
    building: await iconPng(fa.FaBuilding, "#" + TEAL, 256),
    userTie: await iconPng(fa.FaUserTie, "#" + TEAL, 256),
    briefcase: await iconPng(fa.FaBriefcase, "#" + TEAL, 256),
    clock: await iconPng(fa.FaClock, "#" + TEAL, 256),
    language: await iconPng(fa.FaLanguage, "#" + TEAL, 256),
    fileAlt: await iconPng(fa.FaFileAlt, "#" + TEAL, 256),
    sync: await iconPng(fa.FaSyncAlt, "#" + TEAL, 256),
    server: await iconPng(fa.FaServer, "#FFFFFF", 256),
    cloud: await iconPng(fa.FaCloudUploadAlt, "#FFFFFF", 256),
    languageW: await iconPng(fa.FaLanguage, "#FFFFFF", 256),
    fileAltW: await iconPng(fa.FaFileAlt, "#FFFFFF", 256),
  };

  // ---------- helpers ----------
  function pill(slide, x, y, w, h, fill, line) {
    const ln = (line && line !== "none") ? { color: line, width: 1 } : { type: "none" };
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: ln, rectRadius: 0.1, shadow: sh() });
  }
  function kicker(slide, txt, color, x, y) {
    slide.addText(txt.toUpperCase(), { x: x || 0.7, y: y || 0.5, w: 8.6, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 13, bold: true, color: color || GOLD, charSpacing: 3 });
  }
  function shot(slide, file, ow, oh, x, y, maxW, maxH) {
    const ar = ow / oh; let w = maxW, h = w / ar; if (h > maxH) { h = maxH; w = h * ar; }
    const cx = x + (maxW - w) / 2, cy = y + (maxH - h) / 2;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx - 0.08, y: cy - 0.08, w: w + 0.16, h: h + 0.16, fill: { color: WHITE }, line: { color: LINE, width: 1 }, rectRadius: 0.06, shadow: sh() });
    slide.addImage({ path: CAP + file, x: cx, y: cy, w, h });
  }
  function circleIcon(slide, icon, x, y, d, fill) {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill } });
    slide.addImage({ data: icon, x: x + d * 0.28, y: y + d * 0.28, w: d * 0.44, h: d * 0.44 });
  }
  const notes = (slide, t) => slide.addNotes(t);

  // ============================================================
  // 1 — HERO
  // ============================================================
  let s = pres.addSlide(); s.background = { color: NAVY };
  s.addShape(pres.shapes.OVAL, { x: 6.8, y: -2.2, w: 6.2, h: 6.2, fill: { color: NAVY2 } });
  s.addShape(pres.shapes.OVAL, { x: 8.7, y: 3.6, w: 3.0, h: 3.0, fill: { color: NAVY2 } });
  circleIcon(s, I.scaleG, 0.7, 0.6, 1.0, NAVY2);
  s.addShape(pres.shapes.OVAL, { x: 0.7, y: 0.6, w: 1.0, h: 1.0, fill: { type: "none" }, line: { color: GOLD, width: 1.5 } });
  s.addText("DALEEL  ·  دليل", { x: 0.72, y: 2.05, w: 8, h: 0.4, margin: 0, fontFace: "Calibri", fontSize: 15, bold: true, color: GOLD, charSpacing: 4 });
  s.addText("Le droit tunisien,\nà portée de question.", { x: 0.66, y: 2.4, w: 8.2, h: 1.6, margin: 0, fontFace: "Cambria", fontSize: 44, bold: true, color: WHITE, lineSpacingMultiple: 0.98 });
  s.addText("L'assistant juridique intelligent qui répond, cite ses sources, et pilote votre conformité.", { x: 0.72, y: 4.25, w: 7.6, h: 0.6, margin: 0, fontFace: "Calibri", fontSize: 16, color: "C4D0E2" });
  s.addText("by Didax IT", { x: 0.72, y: 5.0, w: 4, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 11, italic: true, color: "7E8DA6" });
  notes(s, "Daleel — « le guide » en arabe. Notre promesse : rendre le droit tunisien aussi simple qu'une question. Vous demandez, Daleel répond en citant la loi, et vous accompagne jusqu'à l'action conforme.");

  // ============================================================
  // 2 — THE PAIN
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Le constat", GOLD);
  s.addText("Trouver la bonne réponse juridique\nprend des heures — et reste risqué.", { x: 0.7, y: 0.85, w: 8.6, h: 1.2, margin: 0, fontFace: "Cambria", fontSize: 28, bold: true, color: NAVY, lineSpacingMultiple: 0.98 });
  const pains = [
    [I.fileAlt, "Des textes éparpillés", "Codes, lois, décrets, circulaires… dans des dizaines de PDF."],
    [I.language, "Un casse-tête multilingue", "Arabe et français, parfois sans équivalence — et des scans illisibles."],
    [I.sync, "Un droit qui change", "Amendements, abrogations : difficile de savoir ce qui s'applique vraiment."],
    [I.clock, "Du temps perdu, un risque réel", "Et une simple erreur d'interprétation peut coûter cher."],
  ];
  pains.forEach((p, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.7 + col * 4.45, y = 2.35 + row * 1.32, w = 4.2, h = 1.18;
    pill(s, x, y, w, h, MIST, LINE);
    circleIcon(s, p[0], x + 0.25, y + 0.3, 0.58, TEALT);
    s.addText(p[1], { x: x + 1.05, y: y + 0.2, w: w - 1.2, h: 0.35, margin: 0, fontFace: "Calibri", fontSize: 14.5, bold: true, color: NAVY });
    s.addText(p[2], { x: x + 1.05, y: y + 0.56, w: w - 1.2, h: 0.5, margin: 0, fontFace: "Calibri", fontSize: 11, color: MUTED, lineSpacingMultiple: 0.98 });
  });
  notes(s, "Posons le décor. Aujourd'hui, chercher une réponse juridique, c'est fouiller des dizaines de PDF, jongler entre l'arabe et le français, deviner quel texte est toujours en vigueur. C'est long, et une erreur peut coûter cher.");

  // ============================================================
  // 3 — MEET DALEEL
  // ============================================================
  s = pres.addSlide(); s.background = { color: NAVY };
  s.addShape(pres.shapes.OVAL, { x: -1.8, y: 3.2, w: 4.5, h: 4.5, fill: { color: NAVY2 } });
  kicker(s, "La solution", GOLD, 0.7, 0.7);
  s.addText("Et si vous posiez simplement\nla question ?", { x: 0.7, y: 1.05, w: 5.1, h: 1.5, margin: 0, fontFace: "Cambria", fontSize: 30, bold: true, color: WHITE, lineSpacingMultiple: 0.98 });
  s.addText("Daleel comprend votre question en arabe, français ou anglais — et répond en citant les articles de loi exacts. Plus de recherche interminable : une réponse claire, sourcée, en quelques secondes.", { x: 0.72, y: 2.75, w: 5.0, h: 1.6, margin: 0, fontFace: "Calibri", fontSize: 15, color: "C4D0E2", lineSpacingMultiple: 1.18 });
  s.addText("« Posez la question. Daleel cite la loi. »", { x: 0.72, y: 4.45, w: 5.0, h: 0.5, margin: 0, fontFace: "Cambria", fontSize: 16, bold: true, italic: true, color: GOLD });
  shot(s, "fig_4_1_chat_reponse.png", 1637, 842, 6.0, 1.2, 3.6, 3.9);
  notes(s, "Et si tout cela disparaissait ? Avec Daleel, vous posez votre question en langage naturel — dans la langue de votre choix — et vous obtenez une réponse claire qui cite les articles exacts. En quelques secondes.");

  // ============================================================
  // 4 — 3 STEPS
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Comment ça marche", GOLD);
  s.addText("Aussi simple que 1 · 2 · 3", { x: 0.7, y: 0.85, w: 8.6, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 28, bold: true, color: NAVY });
  const steps = [
    [I.search, "1", "Demandez", "Posez votre question en arabe, français ou anglais — à l'écrit ou à la voix."],
    [I.quote, "2", "Daleel cite la loi", "Une réponse structurée, avec les articles exacts en sources cliquables."],
    [I.tasks, "3", "Agissez", "Transformez la réponse en exigences, actions et suivi de conformité."],
  ];
  steps.forEach((st, i) => {
    const x = 0.7 + i * 2.97, w = 2.7, y = 1.85, h = 3.1;
    pill(s, x, y, w, h, MIST, LINE);
    circleIcon(s, st[0], x + w / 2 - 0.45, y + 0.4, 0.9, TEAL);
    s.addText(st[1], { x: x + w / 2 + 0.18, y: y + 0.32, w: 0.5, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 20, bold: true, color: GOLD });
    s.addText(st[2], { x, y: y + 1.5, w, h: 0.45, margin: 0, align: "center", fontFace: "Cambria", fontSize: 19, bold: true, color: NAVY });
    s.addText(st[3], { x: x + 0.25, y: y + 2.0, w: w - 0.5, h: 0.95, margin: 0, align: "center", fontFace: "Calibri", fontSize: 11.5, color: MUTED, lineSpacingMultiple: 1.05 });
    if (i < 2) s.addImage({ data: I.arrow, x: x + w + 0.04, y: y + 1.2, w: 0.32, h: 0.32 });
  });
  notes(s, "L'expérience tient en trois temps : vous demandez, Daleel cite la loi, et vous passez à l'action. Aucune compétence technique requise.");

  // ============================================================
  // 5 — BENEFITS
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Vos bénéfices", GOLD);
  s.addText("Pourquoi Daleel change tout", { x: 0.7, y: 0.85, w: 8.6, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 28, bold: true, color: NAVY });
  const benefits = [
    [I.bolt, "Instantané", "Des heures de recherche réduites à quelques secondes.", TEAL],
    [I.check, "Fiable & sourcé", "Chaque réponse cite la loi. Zéro réponse inventée.", GOLD],
    [I.globe, "Multilingue", "Arabe, français, anglais — jusqu'au dialecte tunisien.", TEAL],
    [I.lock, "Confidentiel", "100 % sur vos serveurs. Vos données ne sortent jamais.", GOLD],
  ];
  benefits.forEach((b, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.7 + col * 4.45, y = 1.75 + row * 1.65, w = 4.2, h = 1.5;
    pill(s, x, y, w, h, i % 2 ? GOLDT : TEALT, "none");
    circleIcon(s, b[0], x + 0.28, y + 0.46, 0.62, b[3]);
    s.addText(b[1], { x: x + 1.12, y: y + 0.24, w: w - 1.3, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 18, bold: true, color: NAVY });
    s.addText(b[2], { x: x + 1.12, y: y + 0.72, w: w - 1.3, h: 0.6, margin: 0, fontFace: "Calibri", fontSize: 11.5, color: INK, lineSpacingMultiple: 1.02 });
  });
  notes(s, "Quatre bénéfices qui font la différence : c'est instantané, c'est fiable parce que chaque réponse cite la loi, c'est multilingue jusqu'au dialecte, et c'est confidentiel — tout tourne chez vous.");

  // ============================================================
  // 6 — TWO SOLUTIONS IN ONE
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Une plateforme, deux super-pouvoirs", GOLD);
  s.addText("Comprendre la loi. Piloter la conformité.", { x: 0.7, y: 0.85, w: 8.6, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 27, bold: true, color: NAVY });
  const two = [
    [I.search, "Assistant juridique", TEAL, ["Questions en langage naturel", "Réponses sourcées & traçables", "Recherche dans tout votre corpus", "Analyse de contrats & documents"]],
    [I.shield, "Pilotage de conformité", NAVY, ["Exigences applicables à votre activité", "Actions correctives & échéances", "Preuves, contrôles & exceptions", "Tableau de bord temps réel"]],
  ];
  two.forEach((t, i) => {
    const x = 0.7 + i * 4.45, y = 1.7, w = 4.2, h = 3.45;
    pill(s, x, y, w, h, MIST, LINE);
    circleIcon(s, t[0], x + 0.35, y + 0.38, 0.85, t[2]);
    s.addText(t[1], { x: x + 1.35, y: y + 0.6, w: w - 1.5, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 19, bold: true, color: NAVY });
    s.addText(t[3].map((p) => ({ text: p, options: { bullet: { code: "2713", indent: 16 }, color: INK, breakLine: true, paraSpaceAfter: 10, fontSize: 13, fontFace: "Calibri" } })), { x: x + 0.4, y: y + 1.55, w: w - 0.7, h: 1.7, margin: 0, valign: "top" });
  });
  notes(s, "Daleel, c'est deux produits en un. D'un côté, un assistant juridique qui répond et source. De l'autre, un véritable pilotage de conformité : exigences, actions, preuves, tableau de bord. De la question… à l'action conforme.");

  // ============================================================
  // 7 — IN ACTION
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "En action", GOLD);
  s.addText("Voyez par vous-même", { x: 0.7, y: 0.85, w: 8.6, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 28, bold: true, color: NAVY });
  shot(s, "fig_4_1_chatbot.png", 1917, 912, 0.7, 1.7, 4.35, 2.7);
  shot(s, "fig_4_3_dashboard.png", 1580, 906, 5.25, 1.7, 4.05, 2.7);
  s.addText("Un chatbot qui répond et cite la loi", { x: 0.7, y: 4.55, w: 4.35, h: 0.35, margin: 0, align: "center", fontFace: "Calibri", fontSize: 13, bold: true, color: NAVY });
  s.addText("Un tableau de bord de votre conformité", { x: 5.25, y: 4.55, w: 4.05, h: 0.35, margin: 0, align: "center", fontFace: "Calibri", fontSize: 13, bold: true, color: NAVY });
  notes(s, "Voici Daleel en vrai : à gauche, le chatbot qui dialogue et cite ses sources ; à droite, le tableau de bord qui donne en un coup d'œil votre posture de conformité. Une interface moderne, en arabe comme en français.");

  // ============================================================
  // 8 — DIFFERENTIATION
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Ce qui nous rend uniques", GOLD);
  s.addText("La seule plateforme pensée\npour le contexte tunisien.", { x: 0.7, y: 0.82, w: 8.6, h: 1.1, margin: 0, fontFace: "Cambria", fontSize: 26, bold: true, color: NAVY, lineSpacingMultiple: 0.97 });
  const uniq = [
    [I.languageW, "Native en arabe & derja", "Là où les solutions internationales s'arrêtent à l'anglais."],
    [I.fileAltW, "Spécialiste du droit tunisien", "2 565 articles déjà indexés — codes du travail, sociétés, données…"],
    [I.lock, "100 % on-premise", "Aucune donnée envoyée dans le cloud. Souveraineté totale."],
    [I.quote, "Agent IA autonome", "Raisonne, croise les sources, et reste transparent sur son cheminement."],
  ];
  uniq.forEach((u, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.7 + col * 4.45, y = 2.2 + row * 1.45, w = 4.2, h = 1.28;
    pill(s, x, y, w, h, MIST, LINE);
    circleIcon(s, u[0] === I.quote || u[0] === I.lock ? u[0] : u[0], x + 0.26, y + 0.34, 0.58, NAVY);
    s.addText(u[1], { x: x + 1.05, y: y + 0.22, w: w - 1.2, h: 0.38, margin: 0, fontFace: "Calibri", fontSize: 14, bold: true, color: NAVY });
    s.addText(u[2], { x: x + 1.05, y: y + 0.6, w: w - 1.2, h: 0.55, margin: 0, fontFace: "Calibri", fontSize: 11, color: MUTED, lineSpacingMultiple: 0.98 });
  });
  notes(s, "Pourquoi Daleel et pas un autre ? Parce que c'est la seule solution native en arabe et en derja, spécialiste du droit tunisien, qui tourne entièrement chez vous, et qui embarque un véritable agent IA autonome et transparent.");

  // ============================================================
  // 9 — NUMBERS
  // ============================================================
  s = pres.addSlide(); s.background = { color: NAVY };
  s.addShape(pres.shapes.OVAL, { x: 7.3, y: -2.0, w: 5.5, h: 5.5, fill: { color: NAVY2 } });
  kicker(s, "En chiffres", GOLD, 0.7, 0.6);
  s.addText("Des résultats concrets", { x: 0.7, y: 0.95, w: 8.6, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 28, bold: true, color: WHITE });
  const nums = [["2 565", "articles de loi indexés"], ["3", "langues (ar · fr · en)"], ["+40 %", "de précision de recherche*"], ["100 %", "on-premise & confidentiel"]];
  nums.forEach((n, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.7 + col * 4.45, y = 1.95 + row * 1.55, w = 4.2, h = 1.35;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: NAVY2 }, line: { color: NAVY3, width: 1 }, rectRadius: 0.1 });
    s.addText(n[0], { x: x + 0.3, y: y + 0.18, w: w - 0.6, h: 0.7, margin: 0, fontFace: "Cambria", fontSize: 40, bold: true, color: i % 2 ? GOLDL : TEALL });
    s.addText(n[1], { x: x + 0.32, y: y + 0.92, w: w - 0.6, h: 0.35, margin: 0, fontFace: "Calibri", fontSize: 12.5, color: "C4D0E2" });
  });
  s.addText("* gain mesuré sur la recherche après spécialisation du moteur IA au droit tunisien.", { x: 0.7, y: 5.05, w: 8.6, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 9.5, italic: true, color: "7E8DA6" });
  notes(s, "Quelques chiffres : plus de 2 500 articles déjà indexés, trois langues, une précision de recherche améliorée de 40 % grâce à notre moteur spécialisé, et une solution 100 % on-premise.");

  // ============================================================
  // 10 — FOR WHOM
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Pour qui", GOLD);
  s.addText("Pensé pour ceux qui vivent du droit", { x: 0.7, y: 0.85, w: 8.6, h: 0.6, margin: 0, fontFace: "Cambria", fontSize: 27, bold: true, color: NAVY });
  const who = [
    [I.gavel, "Cabinets d'avocats", "Recherche & analyse accélérées"],
    [I.building, "Directions juridiques", "Réponses fiables à grande échelle"],
    [I.userTie, "Responsables conformité", "Pilotage et preuves centralisés"],
    [I.briefcase, "PME & ESN", "L'expertise juridique accessible"],
  ];
  who.forEach((w0, i) => {
    const x = 0.7 + i * 2.21, ww = 2.0, y = 1.85, h = 2.9;
    pill(s, x, y, ww, h, MIST, LINE);
    circleIcon(s, w0[0], x + ww / 2 - 0.42, y + 0.4, 0.84, TEALT);
    s.addText(w0[1], { x: x + 0.1, y: y + 1.45, w: ww - 0.2, h: 0.7, margin: 0, align: "center", fontFace: "Cambria", fontSize: 15.5, bold: true, color: NAVY, lineSpacingMultiple: 0.95 });
    s.addText(w0[2], { x: x + 0.15, y: y + 2.15, w: ww - 0.3, h: 0.65, margin: 0, align: "center", fontFace: "Calibri", fontSize: 10.5, color: MUTED, lineSpacingMultiple: 1.0 });
  });
  notes(s, "À qui s'adresse Daleel ? Aux cabinets d'avocats, aux directions juridiques, aux responsables conformité, et aux PME qui n'ont pas les moyens d'un service juridique complet. Tous gagnent du temps et de la fiabilité.");

  // ============================================================
  // 11 — TRUST / SECURITY
  // ============================================================
  s = pres.addSlide(); s.background = { color: WHITE };
  kicker(s, "Confiance & souveraineté", GOLD);
  s.addText("Vos données ne sortent jamais\nde chez vous.", { x: 0.7, y: 0.85, w: 5.2, h: 1.2, margin: 0, fontFace: "Cambria", fontSize: 27, bold: true, color: NAVY, lineSpacingMultiple: 0.98 });
  const trust = [
    [I.server, "Déploiement on-premise", "Daleel tourne sur votre infrastructure, derrière votre pare-feu."],
    [I.lock, "Zéro fuite de données", "Aucun appel à un service cloud externe. Confidentialité totale."],
    [I.check, "Maîtrise & transparence", "Sources vérifiables, raisonnement traçable, technologie ouverte."],
  ];
  trust.forEach((t, i) => {
    const y = 2.3 + i * 0.95;
    circleIcon(s, t[0], 0.72, y, 0.6, NAVY);
    s.addText(t[1], { x: 1.5, y: y - 0.02, w: 4.4, h: 0.35, margin: 0, fontFace: "Calibri", fontSize: 14.5, bold: true, color: NAVY });
    s.addText(t[2], { x: 1.5, y: y + 0.32, w: 4.4, h: 0.5, margin: 0, fontFace: "Calibri", fontSize: 11, color: MUTED, lineSpacingMultiple: 0.98 });
  });
  // right visual block
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.35, y: 1.55, w: 3.0, h: 3.6, fill: { color: NAVY }, rectRadius: 0.1, shadow: sh() });
  circleIcon(s, I.lock, 6.35 + 1.5 - 0.55, 2.15, 1.1, NAVY2);
  s.addShape(pres.shapes.OVAL, { x: 6.35 + 1.5 - 0.55, y: 2.15, w: 1.1, h: 1.1, fill: { type: "none" }, line: { color: GOLD, width: 1.5 } });
  s.addText("Souveraineté\nnumérique", { x: 6.5, y: 3.45, w: 2.7, h: 0.8, margin: 0, align: "center", fontFace: "Cambria", fontSize: 19, bold: true, color: WHITE, lineSpacingMultiple: 0.95 });
  s.addText("100 % de vos données restent chez vous.", { x: 6.5, y: 4.3, w: 2.7, h: 0.6, margin: 0, align: "center", fontFace: "Calibri", fontSize: 11, color: "C4D0E2" });
  notes(s, "Un argument décisif, surtout pour des données juridiques sensibles : Daleel est 100 % on-premise. Rien ne part dans le cloud. Vous gardez la maîtrise totale de vos données — c'est de la souveraineté numérique.");

  // ============================================================
  // 12 — CTA
  // ============================================================
  s = pres.addSlide(); s.background = { color: NAVY };
  s.addShape(pres.shapes.OVAL, { x: 6.7, y: -2.4, w: 6.5, h: 6.5, fill: { color: NAVY2 } });
  s.addShape(pres.shapes.OVAL, { x: -1.6, y: 3.6, w: 3.6, h: 3.6, fill: { color: NAVY2 } });
  circleIcon(s, I.scaleG, 0.7, 0.7, 0.9, NAVY2);
  s.addShape(pres.shapes.OVAL, { x: 0.7, y: 0.7, w: 0.9, h: 0.9, fill: { type: "none" }, line: { color: GOLD, width: 1.5 } });
  s.addText("Prêt à transformer\nvotre quotidien juridique ?", { x: 0.7, y: 1.9, w: 8.4, h: 1.5, margin: 0, fontFace: "Cambria", fontSize: 34, bold: true, color: WHITE, lineSpacingMultiple: 0.98 });
  s.addText("Découvrez Daleel en démonstration — et posez-lui votre première question.", { x: 0.72, y: 3.45, w: 8, h: 0.5, margin: 0, fontFace: "Calibri", fontSize: 15, color: "C4D0E2" });
  // CTA button
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.72, y: 4.2, w: 2.95, h: 0.72, fill: { color: GOLD }, rectRadius: 0.1, shadow: shG() });
  s.addText("Demander une démo", { x: 0.72, y: 4.2, w: 2.95, h: 0.72, margin: 0, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 15, bold: true, color: NAVY });
  s.addText("contact@didax-it.tn   ·   www.daleel.tn", { x: 3.95, y: 4.2, w: 5.2, h: 0.72, margin: 0, valign: "middle", fontFace: "Calibri", fontSize: 13, color: "C4D0E2" });
  s.addText("Daleel — votre guide juridique intelligent.", { x: 0.72, y: 5.05, w: 8, h: 0.3, margin: 0, fontFace: "Cambria", fontSize: 12, italic: true, bold: true, color: GOLD });
  notes(s, "La question n'est plus de savoir si l'IA va transformer le métier juridique, mais quand vous allez en profiter. Demandez une démo, et posez à Daleel votre première vraie question. Merci !");

  await pres.writeFile({ fileName: "C:/Users/RSCH/Daleel/docs/Daleel_Pitch_Marketing.pptx" });
  console.log("OK written");
})().catch((e) => { console.error(e); process.exit(1); });
