/* Soutenance PFE — Daleel — Manar Trimeche
 * Génère Soutenance_Daleel_Manar.pptx (16:9, ~22 slides, FR)
 * Style inspiré de la référence : hook → titre → plan-séparateurs → breadcrumbs → stats.
 * Palette Daleel : navy 232946 (dominant) · or D4A437 (accent) · blanc.
 */
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaBalanceScale, FaBuilding, FaExclamationTriangle, FaSearch, FaShieldAlt,
  FaSyncAlt, FaDatabase, FaRobot, FaCogs, FaChartLine, FaRocket, FaCheckCircle,
  FaLightbulb, FaGavel, FaFileAlt, FaLanguage, FaServer, FaUsers, FaLock,
  FaClipboardCheck, FaProjectDiagram, FaQuestionCircle, FaGlobe, FaBolt,
  FaLayerGroup, FaCodeBranch, FaComments, FaTachometerAlt, FaPuzzlePiece,
} = require("react-icons/fa");

const NAVY = "232946";
const NAVY2 = "2E3654";   // navy plus clair (cartes sur fond sombre)
const GOLD = "D4A437";
const GOLDLT = "F4E8C8";
const WHITE = "FFFFFF";
const ICE = "F4F6FB";
const MUTE = "5A6378";
const GREEN = "1F9D6B";
const RED = "C0392B";

const CAP = "C:\\Users\\RSCH\\Daleel\\captures\\";
const W = 10, H = 5.625;

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Comp, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

const sh = () => ({ type: "outer", color: "1A1A2E", blur: 7, offset: 2, angle: 45, opacity: 0.18 });

async function main() {
  const icons = {};
  const defs = {
    scale: [FaBalanceScale, WHITE], scaleG: [FaBalanceScale, GOLD],
    building: [FaBuilding, WHITE], warn: [FaExclamationTriangle, WHITE],
    search: [FaSearch, WHITE], shield: [FaShieldAlt, WHITE],
    sync: [FaSyncAlt, WHITE], db: [FaDatabase, WHITE], robot: [FaRobot, WHITE],
    cogs: [FaCogs, WHITE], chart: [FaChartLine, WHITE], rocket: [FaRocket, WHITE],
    check: [FaCheckCircle, GREEN], checkW: [FaCheckCircle, WHITE],
    bulb: [FaLightbulb, WHITE], gavel: [FaGavel, WHITE], file: [FaFileAlt, WHITE],
    lang: [FaLanguage, WHITE], server: [FaServer, WHITE], users: [FaUsers, WHITE],
    lock: [FaLock, WHITE], clip: [FaClipboardCheck, WHITE],
    diagram: [FaProjectDiagram, WHITE], q: [FaQuestionCircle, GOLD],
    globe: [FaGlobe, WHITE], bolt: [FaBolt, WHITE], layers: [FaLayerGroup, WHITE],
    branch: [FaCodeBranch, WHITE], comments: [FaComments, WHITE],
    dash: [FaTachometerAlt, WHITE], puzzle: [FaPuzzlePiece, WHITE],
  };
  for (const [k, [C, col]] of Object.entries(defs)) icons[k] = await icon(C, "#" + col);

  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Manar Trimeche";
  pres.title = "Soutenance PFE — Daleel";

  let pageNum = 0;
  function pageNo(s, dark = false) {
    pageNum++;
    s.addText(String(pageNum), {
      x: W - 0.55, y: H - 0.42, w: 0.4, h: 0.3, fontSize: 10,
      color: dark ? "8B93AD" : MUTE, align: "right", fontFace: "Calibri", margin: 0,
    });
  }

  // En-tête des slides de contenu : breadcrumb + titre
  function header(s, crumb, title) {
    s.addText(crumb.toUpperCase(), {
      x: 0.55, y: 0.28, w: 8.8, h: 0.28, fontSize: 10.5, bold: true,
      color: GOLD, charSpacing: 2, fontFace: "Calibri", margin: 0,
    });
    s.addText(title, {
      x: 0.55, y: 0.55, w: 8.9, h: 0.62, fontSize: 27, bold: true,
      color: NAVY, fontFace: "Cambria", margin: 0,
    });
  }

  // Pastille icône ronde
  function dot(s, key, x, y, d, bg) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg } });
    const m = d * 0.26;
    s.addImage({ data: icons[key], x: x + m, y: y + m, w: d - 2 * m, h: d - 2 * m });
  }

  const PLAN = [
    ["01", "Introduction", "Entreprise · Problématique · Solution · CRISP-DM"],
    ["02", "Compréhension métier & données", "Existant · Corpus juridique · Architecture"],
    ["03", "Modélisation & Évaluation", "RAG · Agent ReAct · Fine-tuning · Résultats · Compliance"],
    ["04", "Déploiement & Conclusion", "Interfaces · Production · Réalisations · Perspectives"],
  ];

  // Slide « PLAN » réutilisée comme séparateur (section active mise en avant)
  function planSlide(active) {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    s.addText("PLAN", {
      x: 0.7, y: 0.42, w: 4, h: 0.7, fontSize: 34, bold: true,
      color: WHITE, fontFace: "Cambria", charSpacing: 4, margin: 0,
    });
    dot(s, "scaleG", W - 1.25, 0.42, 0.62, NAVY2);
    const top = 1.45, rh = 0.92, gap = 0.12;
    PLAN.forEach(([num, t, sub], i) => {
      const y = top + i * (rh + gap);
      const on = i === active;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.7, y, w: 8.6, h: rh, rectRadius: 0.07,
        fill: { color: on ? GOLD : NAVY2 },
        shadow: on ? sh() : undefined,
      });
      s.addText(num, {
        x: 0.98, y: y + 0.14, w: 0.75, h: 0.62, fontSize: 26, bold: true,
        color: on ? NAVY : GOLD, fontFace: "Cambria", margin: 0,
      });
      s.addText([
        { text: t, options: { fontSize: 16.5, bold: true, color: on ? NAVY : WHITE, breakLine: true } },
        { text: sub, options: { fontSize: 11, color: on ? "5C4A12" : "AEB6CE" } },
      ], { x: 1.85, y: y + 0.12, w: 7.2, h: 0.7, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    pageNo(s, true);
    return s;
  }

  /* ============ S1 — HOOK ============ */
  {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    s.addText("QUEL PROBLÈME RÉSOLVONS-NOUS ?", {
      x: 0.7, y: 0.55, w: 8.6, h: 0.5, fontSize: 15, bold: true, color: GOLD,
      charSpacing: 3, fontFace: "Calibri", margin: 0,
    });
    s.addText("Un juriste tunisien doit vérifier\nl'applicabilité d'un décret à son entreprise.", {
      x: 0.7, y: 1.15, w: 8.6, h: 1.3, fontSize: 27, bold: true, color: WHITE,
      fontFace: "Cambria", margin: 0,
    });
    const items = [
      ["file", "Des dizaines de PDF à parcourir manuellement"],
      ["sync", "Des versions et amendements à recouper"],
      ["lang", "Deux langues : arabe et français"],
      ["warn", "Des heures de travail — et un risque d'erreur"],
    ];
    items.forEach(([k, t], i) => {
      const y = 2.75 + i * 0.56;
      dot(s, k, 0.78, y, 0.4, NAVY2);
      s.addText(t, {
        x: 1.35, y: y + 0.02, w: 6.6, h: 0.38, fontSize: 14.5, color: "D9DEF0",
        fontFace: "Calibri", margin: 0, valign: "middle",
      });
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 5.7, y: 4.62, w: 3.75, h: 0.62, rectRadius: 0.09, fill: { color: GOLD }, shadow: sh(),
    });
    s.addText("Et si l'IA répondait en quelques secondes ?", {
      x: 5.82, y: 4.66, w: 3.55, h: 0.54, fontSize: 13.5, bold: true, color: NAVY,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
    });
    s.addNotes("Accroche : partir du vécu d'un juriste tunisien. Insister sur le coût en temps et le risque d'erreur du processus manuel. Transition : c'est exactement ce que Daleel résout.");
    pageNo(s, true);
  }

  /* ============ S2 — TITRE ============ */
  {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    dot(s, "scaleG", W / 2 - 0.45, 0.55, 0.9, NAVY2);
    s.addText("DALEEL", {
      x: 0.5, y: 1.5, w: 9, h: 0.85, fontSize: 50, bold: true, color: WHITE,
      fontFace: "Cambria", align: "center", charSpacing: 8, margin: 0,
    });
    s.addText("« دليل » — le guide", {
      x: 0.5, y: 2.32, w: 9, h: 0.4, fontSize: 15, italic: true, color: GOLD,
      fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addText("Plateforme intégrée d'assistance juridique et de conformité réglementaire\nfondée sur l'intelligence artificielle", {
      x: 1, y: 2.8, w: 8, h: 0.75, fontSize: 15.5, color: "D9DEF0",
      fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addShape(pres.shapes.LINE, { x: 3.5, y: 3.78, w: 3, h: 0, line: { color: GOLD, width: 1 } });
    s.addText("Manar Trimeche", {
      x: 0.5, y: 3.95, w: 9, h: 0.42, fontSize: 19, bold: true, color: WHITE,
      fontFace: "Cambria", align: "center", margin: 0,
    });
    s.addText("Encadrant académique : Dr Nizar Omheni     ·     Encadrant professionnel : M. Raouf Bouneb", {
      x: 0.5, y: 4.42, w: 9, h: 0.32, fontSize: 12, color: "AEB6CE",
      fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addText("École Polytechnique de Sousse   ·   Didax IT   ·   2025–2026", {
      x: 0.5, y: 4.78, w: 9, h: 0.32, fontSize: 12, color: GOLD,
      fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addNotes("Se présenter, remercier le jury. Donner le sens du nom Daleel (le guide). Annoncer le double volet : assistance juridique + conformité.");
    pageNo(s, true);
  }

  /* ============ S3 — PLAN (§1 actif) ============ */
  planSlide(0).addNotes("Quatre parties suivant le cycle CRISP-DM : introduction, compréhension métier et données, modélisation et évaluation, déploiement et conclusion.");

  /* ============ S4 — DIDAX IT & CADRE ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Introduction · Entreprise d'accueil", "Didax IT — cadre du projet");
    // Carte entreprise (gauche)
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 1.45, w: 4.3, h: 3.6, rectRadius: 0.08, fill: { color: ICE }, shadow: sh() });
    dot(s, "building", 0.85, 1.75, 0.55, NAVY);
    s.addText("Didax IT", { x: 1.55, y: 1.78, w: 3, h: 0.5, fontSize: 18, bold: true, color: NAVY, fontFace: "Cambria", margin: 0, valign: "middle" });
    s.addText([
      { text: "Société de services IT fondée à Dubaï en 2024", options: { bullet: true, breakLine: true } },
      { text: "Bureau commercial à Dubaï, équipes techniques en Tunisie et en Inde", options: { bullet: true, breakLine: true } },
      { text: "Développement de solutions IA sur mesure, transformation numérique, e-learning", options: { bullet: true } },
    ], { x: 0.85, y: 2.5, w: 3.75, h: 2.4, fontSize: 13, color: "37405C", fontFace: "Calibri", paraSpaceAfter: 8 });
    // Carte cadre (droite)
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.15, y: 1.45, w: 4.3, h: 3.6, rectRadius: 0.08, fill: { color: ICE }, shadow: sh() });
    dot(s, "gavel", 5.45, 1.75, 0.55, GOLD);
    s.addText("Le projet Daleel", { x: 6.15, y: 1.78, w: 3.2, h: 0.5, fontSize: 18, bold: true, color: NAVY, fontFace: "Cambria", margin: 0, valign: "middle" });
    s.addText([
      { text: "Domaine : LegalTech & RegTech", options: { bullet: true, breakLine: true } },
      { text: "Vocation internationale, premier périmètre : droit tunisien", options: { bullet: true, breakLine: true } },
      { text: "Corpus officiel : JORT / IORT, en arabe et en français", options: { bullet: true } },
    ], { x: 5.45, y: 2.5, w: 3.75, h: 2.4, fontSize: 13, color: "37405C", fontFace: "Calibri", paraSpaceAfter: 8 });
    s.addNotes("Présenter Didax IT brièvement (modèle hybride Dubaï/Tunisie). Cadrer le projet : LegalTech à vocation internationale, expérimenté d'abord sur le droit tunisien.");
    pageNo(s);
  }

  /* ============ S5 — PROBLÉMATIQUE ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Introduction · Problématique", "Cinq verrous à lever");
    const cards = [
      ["file", "Volume & fragmentation", "Codes, lois, décrets, circulaires — formats hétérogènes (PDF natifs, scans, DOCX)"],
      ["lang", "Multilinguisme", "Corpus arabe / français sans correspondance directe ; normalisation Unicode arabe"],
      ["layers", "Complexité structurelle", "Livres, titres, chapitres, alinéas ; nuances modales (obligations, sanctions, conditions)"],
      ["warn", "Qualité des sources", "OCR bruité, encodages multiples, bruit éditorial du JORT"],
    ];
    const cw = 4.3, ch = 1.32, gx = 0.6, gy = 0.32;
    cards.forEach(([k, t, d], i) => {
      const x = 0.55 + (i % 2) * (cw + gx);
      const y = 1.42 + Math.floor(i / 2) * (ch + gy);
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: ch, rectRadius: 0.07, fill: { color: ICE }, shadow: sh() });
      dot(s, k, x + 0.18, y + 0.18, 0.46, NAVY);
      s.addText([
        { text: t, options: { fontSize: 13.5, bold: true, color: NAVY, breakLine: true } },
        { text: d, options: { fontSize: 11, color: MUTE } },
      ], { x: x + 0.8, y: y + 0.12, w: cw - 1, h: ch - 0.2, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 4.62, w: 8.9, h: 0.68, rectRadius: 0.07, fill: { color: NAVY }, shadow: sh() });
    s.addText([
      { text: "5e verrou — ", options: { bold: true, color: GOLD } },
      { text: "aucun outil ne relie les textes juridiques au pilotage opérationnel de la conformité", options: { color: WHITE } },
    ], { x: 0.85, y: 4.66, w: 8.4, h: 0.6, fontSize: 13.5, fontFace: "Calibri", margin: 0, valign: "middle" });
    s.addNotes("Insister sur le 5e verrou : le manque fonctionnel majeur n'est pas seulement la recherche, mais le lien texte → exigence → action de conformité. C'est ce qui justifie le double volet de Daleel.");
    pageNo(s);
  }

  /* ============ S6 — SOLUTION : 2 VOLETS ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Introduction · Solution proposée", "Daleel — deux volets intégrés");
    const half = [
      ["search", "Volet « Legal RAG »", NAVY, [
        "Interrogation en langage naturel (ar / fr / en)",
        "Recherche hybride + reranking + retrieval partitionné",
        "Garde anti-hallucination multi-couches",
        "Agent autonome ReAct à 12 outils",
      ]],
      ["shield", "Volet « Compliance Operations »", GOLD, [
        "Exigences réglementaires extraites des textes",
        "Dossiers, constats, actions correctives, preuves",
        "Arbre de décision ASK / CLARIFY / ACT / REVIEW",
        "Tableaux de bord temps réel multi-tenant",
      ]],
    ];
    half.forEach(([k, t, col, items], i) => {
      const x = 0.55 + i * 4.6;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: 4.3, h: 3.15, rectRadius: 0.08, fill: { color: ICE }, shadow: sh() });
      dot(s, k, x + 0.25, y0 = 1.7, 0.52, col);
      s.addText(t, { x: x + 0.95, y: 1.72, w: 3.2, h: 0.5, fontSize: 15.5, bold: true, color: NAVY, fontFace: "Cambria", margin: 0, valign: "middle" });
      s.addText(items.map((tx, j) => ({ text: tx, options: { bullet: true, breakLine: j < items.length - 1 } })),
        { x: x + 0.3, y: 2.42, w: 3.8, h: 2, fontSize: 12, color: "37405C", fontFace: "Calibri", paraSpaceAfter: 7 });
    });
    s.addText([
      { text: "Le lien entre les deux : ", options: { bold: true, color: NAVY } },
      { text: "textes juridiques → exigences → applicabilité → constats → actions → preuves → tableaux de bord", options: { color: MUTE } },
    ], { x: 0.55, y: 4.78, w: 8.9, h: 0.5, fontSize: 12.5, fontFace: "Calibri", align: "center", margin: 0 });
    s.addNotes("Présenter les deux volets et surtout leur chaînage : les exigences réglementaires sont le pont entre la recherche juridique et le pilotage de conformité.");
    pageNo(s);
  }

  /* ============ S7 — CRISP-DM ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Introduction · Méthodologie", "CRISP-DM, appliqué de manière itérative");
    s.addImage({ path: CAP + "fig_1_1_crisp_dm.png", x: 0.45, y: 1.4, w: 4.6, h: 3.8, sizing: { type: "contain", w: 4.6, h: 3.8 } });
    const steps = [
      ["Compréhension métier", "besoins des juristes et responsables conformité"],
      ["Compréhension des données", "corpus JORT/IORT, langues, qualité OCR"],
      ["Préparation", "extraction multi-moteurs, nettoyage arabe, chunks"],
      ["Modélisation", "RAG, agent ReAct, fine-tuning, compliance"],
      ["Évaluation", "Recall@k, MRR, nDCG + 951 tests"],
      ["Déploiement", "Docker Compose, CI/CD GitHub Actions"],
    ];
    steps.forEach(([t, d], i) => {
      const y = 1.42 + i * 0.62;
      s.addShape(pres.shapes.OVAL, { x: 5.25, y: y + 0.05, w: 0.34, h: 0.34, fill: { color: i % 2 ? GOLD : NAVY } });
      s.addText(String(i + 1), { x: 5.25, y: y + 0.05, w: 0.34, h: 0.34, fontSize: 12, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: "Calibri", margin: 0 });
      s.addText([
        { text: t + " — ", options: { bold: true, color: NAVY } },
        { text: d, options: { color: MUTE } },
      ], { x: 5.75, y: y, w: 3.8, h: 0.5, fontSize: 11.5, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addNotes("Exemple d'itération concrète : l'évaluation du modèle d'embeddings de base a révélé un déficit de pertinence → déclenchement du fine-tuning. Les difficultés OCR arabes → renforcement du pipeline de nettoyage.");
    pageNo(s);
  }

  /* ============ S8 — PLAN §2 ============ */
  planSlide(1).addNotes("Deuxième partie : ce qui existe, le corpus, et l'architecture de la solution.");

  /* ============ S9 — POSITIONNEMENT ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Compréhension métier · Solutions existantes", "Un vide entre LegalTech et GRC");
    const rows = [
      [
        { text: "Critère", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
        { text: "Daleel", options: { bold: true, color: NAVY, fill: { color: GOLDLT } } },
        { text: "Harvey AI", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
        { text: "realLaw AI", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
        { text: "GRC (OpenPages…)", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
      ],
      ["RAG juridique sourcé", { text: "✓ + garde-qualité", options: { fill: { color: GOLDLT }, bold: true } }, "✓ propriétaire", "✓ UAE", "✗"],
      ["Pilotage de conformité", { text: "✓ complet", options: { fill: { color: GOLDLT }, bold: true } }, "✗", "✗", "Partiel"],
      ["Droit tunisien (ar/fr)", { text: "✓ 2 565 articles", options: { fill: { color: GOLDLT }, bold: true } }, "✗", "✗", "✗"],
      ["Déploiement on-premise", { text: "✓ Docker", options: { fill: { color: GOLDLT }, bold: true } }, "✗ cloud", "✗ cloud", "Coûteux"],
    ];
    s.addTable(rows, {
      x: 0.55, y: 1.5, w: 8.9, colW: [2.5, 1.8, 1.55, 1.45, 1.6],
      fontSize: 11.5, fontFace: "Calibri", color: "37405C",
      border: { pt: 0.75, color: "D5DAE8" }, align: "center", valign: "middle",
      rowH: 0.52,
    });
    s.addText("Aucune solution ne combine recherche juridique intelligente et conformité opérationnelle pour le droit tunisien.", {
      x: 0.55, y: 4.55, w: 8.9, h: 0.5, fontSize: 13, italic: true, color: NAVY,
      fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addNotes("Harvey AI : anglo-saxon, cloud. realLaw : UAE. Les GRC : pas de moteur juridique intelligent. Daleel occupe l'intersection vide.");
    pageNo(s);
  }

  /* ============ S10 — CORPUS & DÉFIS ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Compréhension des données · Corpus juridique", "2 565 articles, deux langues, mille pièges");
    const stats = [
      ["2 565", "articles indexés", NAVY],
      ["2", "langues : arabe & français", GOLD],
      ["+10 000", "chunks indexables", NAVY],
    ];
    stats.forEach(([n, l, c], i) => {
      const x = 0.55 + i * 3.05;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: 2.85, h: 1.25, rectRadius: 0.08, fill: { color: ICE }, shadow: sh() });
      s.addText(n, { x, y: 1.55, w: 2.85, h: 0.62, fontSize: 30, bold: true, color: c, fontFace: "Cambria", align: "center", margin: 0 });
      s.addText(l, { x, y: 2.2, w: 2.85, h: 0.4, fontSize: 11.5, color: MUTE, fontFace: "Calibri", align: "center", margin: 0 });
    });
    s.addText("Défis observés sur le corpus", { x: 0.55, y: 3.0, w: 8.9, h: 0.4, fontSize: 15, bold: true, color: NAVY, fontFace: "Cambria", margin: 0 });
    const defis = [
      ["Texte arabe mal encodé", "illisible par la machine — à normaliser"],
      ["Documents scannés", "pas de texte sélectionnable — OCR nécessaire"],
      ["Bruit du Journal Officiel", "en-têtes et numéros de page à retirer"],
      ["Mots aux formes variables", "un même terme écrit de plusieurs façons"],
    ];
    defis.forEach(([t, d], i) => {
      const x = 0.55 + (i % 2) * 4.6, y = 3.5 + Math.floor(i / 2) * 0.78;
      dot(s, "warn", x, y, 0.38, GOLD);
      s.addText([
        { text: t + " — ", options: { bold: true, color: NAVY } },
        { text: d, options: { color: MUTE } },
      ], { x: x + 0.52, y: y - 0.04, w: 3.9, h: 0.7, fontSize: 11.5, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addNotes("Ces défis justifient le pipeline d'ingestion en 5 étapes : extraction en cascade (PyMuPDF → pdfminer → OCR Tesseract+EasyOCR), nettoyage arabe en 11 opérations, segmentation hiérarchique, chunks 1500/200, indexation FAISS HNSW.");
    pageNo(s);
  }

  /* ============ S11 — ARCHITECTURE ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Compréhension des données · Vue d'ensemble", "Architecture en cinq couches");
    s.addImage({ path: CAP + "fig_3_1_architecture.png", x: 1.45, y: 1.32, w: 7.1, h: 4.1, sizing: { type: "contain", w: 7.1, h: 4.1 } });
    s.addNotes("Lire de haut en bas : 18 pages React → 9 routeurs FastAPI (170+ endpoints) → 41 services métier → 8 modules de traitement documentaire → MongoDB 38 collections + index FAISS en mémoire. Deux volets transverses : Legal RAG et Compliance.");
    pageNo(s);
  }

  /* ============ S12 — PLAN §3 ============ */
  planSlide(2).addNotes("Cœur technique et scientifique : le pipeline RAG, l'agent, le fine-tuning et ses résultats, puis le volet conformité.");

  /* ============ S13 — PIPELINE RAG ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Modélisation · Pipeline RAG", "Six modules spécialisés, activables indépendamment");
    const mods = [
      ["search", "1 · Recherche hybride", "comprend le sens ET les mots-clés de la question"],
      ["layers", "2 · Reranking", "reclasse pour ne garder que le plus pertinent"],
      ["branch", "3 · Routeur de domaine", "oriente vers le bon domaine juridique"],
      ["sync", "4 · Retrieval partitionné", "ne mélange jamais loi en vigueur et amendements"],
      ["diagram", "5 · Graphe de connaissances", "relie loi → exigence → action → criticité"],
      ["shield", "6 · Garde-qualité", "vérifie chaque source avant de répondre"],
    ];
    const cw = 2.93, chh = 1.62, gx = 0.06, gy = 0.22;
    mods.forEach(([k, t, d], i) => {
      const x = 0.52 + (i % 3) * (cw + gx);
      const y = 1.45 + Math.floor(i / 3) * (chh + gy);
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: chh, rectRadius: 0.07, fill: { color: ICE }, shadow: sh() });
      dot(s, k, x + 0.16, y + 0.16, 0.4, i % 2 ? GOLD : NAVY);
      s.addText(t, { x: x + 0.66, y: y + 0.14, w: cw - 0.8, h: 0.44, fontSize: 12.5, bold: true, color: NAVY, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addText(d, { x: x + 0.18, y: y + 0.68, w: cw - 0.36, h: 0.88, fontSize: 10.5, color: MUTE, fontFace: "Calibri", margin: 0 });
    });
    s.addText("Génération : qwen2.5:7b via Ollama — 100 % local, aucune API externe, confidentialité préservée.", {
      x: 0.55, y: 5.08, w: 8.9, h: 0.36, fontSize: 12, italic: true, color: NAVY, fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addNotes("Souligner la modularité (chaque module activable par configuration) et le choix qwen2.5:7b : multilingue ar/fr/en, function calling natif, licence Apache 2.0, déployable localement — écarte GPT-4 pour la confidentialité. Détail technique si question : recherche hybride = vecteurs FAISS + signaux lexicaux, fusion pondérée 0,56/0,20/0,14/0,10 ; reranking par cross-encoder ms-marco MiniLM avec seuil de rejet (cf. slide annexe).");
    pageNo(s);
  }

  /* ============ S14 — AGENT REACT ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Modélisation · Agent autonome", "ReAct : raisonner, agir, observer, itérer");
    // Boucle (gauche)
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 1.45, w: 4.35, h: 3.6, rectRadius: 0.08, fill: { color: NAVY }, shadow: sh() });
    s.addText("La boucle d'exécution", { x: 0.85, y: 1.62, w: 3.8, h: 0.4, fontSize: 14.5, bold: true, color: GOLD, fontFace: "Cambria", margin: 0 });
    const loop = ["Comprend la question", "Choisit et appelle le bon outil", "Observe le résultat obtenu", "Recommence si nécessaire", "S'arrête et vérifie sa réponse"];
    loop.forEach((t, i) => {
      const y = 2.15 + i * 0.56;
      s.addShape(pres.shapes.OVAL, { x: 0.88, y: y + 0.03, w: 0.32, h: 0.32, fill: { color: GOLD } });
      s.addText(String(i + 1), { x: 0.88, y: y + 0.03, w: 0.32, h: 0.32, fontSize: 11.5, bold: true, color: NAVY, align: "center", valign: "middle", fontFace: "Calibri", margin: 0 });
      s.addText(t, { x: 1.35, y, w: 3.4, h: 0.42, fontSize: 12, color: "D9DEF0", fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    // Stats (droite)
    const st = [
      ["12", "outils à sa disposition", "recherche, lois, exigences, criticité, roadmap…"],
      ["8-15 s", "temps de réponse", "raisonnement complet de bout en bout"],
      ["100 %", "traçable", "chaque étape est journalisée et auditable"],
    ];
    st.forEach(([n, l, d], i) => {
      const y = 1.45 + i * 1.24;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.15, y, w: 4.3, h: 1.1, rectRadius: 0.08, fill: { color: ICE }, shadow: sh() });
      s.addText(n, { x: 5.3, y: y + 0.14, w: 1.35, h: 0.82, fontSize: 26, bold: true, color: GOLD, fontFace: "Cambria", align: "center", valign: "middle", margin: 0 });
      s.addText([
        { text: l, options: { fontSize: 13, bold: true, color: NAVY, breakLine: true } },
        { text: d, options: { fontSize: 10.5, color: MUTE } },
      ], { x: 6.75, y: y + 0.12, w: 2.6, h: 0.88, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addNotes("Contrairement au pipeline RAG séquentiel, l'agent décide dynamiquement quels outils invoquer. Exemple : question sur une PME de 25 salariés → semantic_search, lookup_law, match_exigences, get_criticality, generate_roadmap. Latence médiane 8-15 s. Détail technique si question : appels via le function calling natif d'Ollama, contexte 8 192 tokens, température 0,15, top-p 0,9, garde-fou de budget d'itérations (cf. slide annexe).");
    pageNo(s);
  }

  /* ============ S15 — FINE-TUNING PROTOCOLE ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Modélisation · Fine-tuning des embeddings", "Spécialiser le modèle au droit tunisien");
    // Flow gauche
    const flow = [
      ["db", "487 articles sélectionnés", "les plus propres, sur les 2 565 du corpus"],
      ["comments", "973 paires question–article", "générées par IA, filtrées par cohérence"],
      ["cogs", "Apprentissage spécialisé", "le modèle apprend à rapprocher question et bon article"],
    ];
    flow.forEach(([k, t, d], i) => {
      const y = 1.45 + i * 1.06;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y, w: 4.5, h: 0.92, rectRadius: 0.07, fill: { color: ICE }, shadow: sh() });
      dot(s, k, 0.72, y + 0.16, 0.55, NAVY);
      s.addText([
        { text: t, options: { fontSize: 13, bold: true, color: NAVY, breakLine: true } },
        { text: d, options: { fontSize: 10.5, color: MUTE } },
      ], { x: 1.48, y: y + 0.08, w: 3.45, h: 0.78, fontFace: "Calibri", margin: 0, valign: "middle" });
      if (i < 2) s.addText("▼", { x: 2.6, y: y + 0.9, w: 0.4, h: 0.18, fontSize: 9, color: GOLD, align: "center", margin: 0 });
    });
    // Protocole d'évaluation (droite, encadré or)
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.35, y: 1.45, w: 4.1, h: 3.05, rectRadius: 0.08, fill: { color: NAVY }, shadow: sh() });
    s.addText("Protocole d'évaluation", { x: 5.62, y: 1.62, w: 3.6, h: 0.4, fontSize: 14.5, bold: true, color: GOLD, fontFace: "Cambria", margin: 0 });
    s.addText([
      { text: "50 requêtes gold (30 fr / 20 ar)", options: { bullet: true, bold: true, color: WHITE, breakLine: true } },
      { text: "Zéro fuite : articles jamais vus à l'entraînement", options: { bullet: true, color: "D9DEF0", breakLine: true } },
      { text: "Générées par LLM, relues et validées par le juriste de Didax IT", options: { bullet: true, color: "D9DEF0", breakLine: true } },
      { text: "Métriques : Recall@k, MRR@10, nDCG", options: { bullet: true, color: "D9DEF0" } },
    ], { x: 5.62, y: 2.1, w: 3.6, h: 2.3, fontSize: 12, fontFace: "Calibri", paraSpaceAfter: 7 });
    s.addText("Comparaison équitable : même corpus, mêmes 50 questions, seul le modèle change.", {
      x: 0.55, y: 4.78, w: 8.9, h: 0.4, fontSize: 12, italic: true, color: NAVY, fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addNotes("Point méthodologique fort à défendre : l'évaluation est exempte de fuite par construction — les 50 articles gold n'apparaissent dans aucune paire d'entraînement. Validation humaine par le juriste de l'entreprise. Détail technique si question : modèle de base MPNet multilingue (768 dim), perte contrastive MultipleNegativesRankingLoss, batch 32, learning rate 2e-5, AdamW, 3 epochs, normalisation L2/cosine (cf. slide annexe).");
    pageNo(s);
  }

  /* ============ S16 — RÉSULTATS ⭐ ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Évaluation · Résultats", "Des gains substantiels, sur toutes les métriques");
    s.addImage({ path: CAP + "fig_5_4_finetuning_resultats.png", x: 0.4, y: 1.42, w: 5.9, h: 3.6, sizing: { type: "contain", w: 5.9, h: 3.6 } });
    const res = [
      ["+50 %", "Recall@1 : 0,40 → 0,60", GREEN],
      ["+40 %", "Recall@5 : 0,60 → 0,84", GREEN],
      ["+87 %", "Recall@5 arabe : 0,40 → 0,75", GOLD],
    ];
    res.forEach(([n, l, c], i) => {
      const y = 1.45 + i * 1.18;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.5, y, w: 3, h: 1.02, rectRadius: 0.08, fill: { color: ICE }, shadow: sh() });
      s.addText(n, { x: 6.6, y: y + 0.08, w: 1.3, h: 0.86, fontSize: 24, bold: true, color: c, fontFace: "Cambria", align: "center", valign: "middle", margin: 0 });
      s.addText(l, { x: 7.95, y: y + 0.08, w: 1.5, h: 0.86, fontSize: 11, bold: true, color: NAVY, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addText("L'arabe, pourtant le plus exposé au bruit OCR, enregistre les gains relatifs les plus élevés.", {
      x: 0.55, y: 5.05, w: 8.9, h: 0.4, fontSize: 12.5, italic: true, color: NAVY, fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addNotes("Slide clé. Gains homogènes — pas de sur-apprentissage (Recall@10 progresse aussi, +32%). Message arabe : R@1 +80% (0,25→0,45), R@5 +87%. La spécialisation bénéficie le plus à la langue la moins bien représentée par le modèle générique.");
    pageNo(s);
  }

  /* ============ S17 — COMPLIANCE OPS ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Modélisation · Compliance Operations", "Du texte de loi au plan d'action");
    // 4 branches
    const br = [
      ["ASK", "collecter les faits manquants", NAVY],
      ["CLARIFY", "lever les contradictions", NAVY],
      ["ACT", "constats + plan d'action priorisé", GOLD],
      ["REVIEW", "validation humaine si critique", NAVY],
    ];
    br.forEach(([t, d, c], i) => {
      const x = 0.55 + i * 2.28;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: 2.12, h: 1.18, rectRadius: 0.08, fill: { color: c }, shadow: sh() });
      s.addText(t, { x, y: 1.56, w: 2.12, h: 0.42, fontSize: 16, bold: true, color: c === GOLD ? NAVY : GOLD, fontFace: "Cambria", align: "center", margin: 0 });
      s.addText(d, { x: x + 0.12, y: 1.98, w: 1.88, h: 0.6, fontSize: 10, color: c === GOLD ? "5C4A12" : "D9DEF0", fontFace: "Calibri", align: "center", margin: 0 });
    });
    s.addText("Orchestrateur LLM en 7 phases — chaque décision journalisée dans audit_logs", {
      x: 0.55, y: 2.78, w: 8.9, h: 0.35, fontSize: 11.5, italic: true, color: MUTE, fontFace: "Calibri", align: "center", margin: 0,
    });
    // Criticité
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 3.3, w: 8.9, h: 1.85, rectRadius: 0.08, fill: { color: ICE }, shadow: sh() });
    s.addText("Scoring de criticité déterministe — auditable et reproductible", {
      x: 0.85, y: 3.45, w: 8.3, h: 0.4, fontSize: 14, bold: true, color: NAVY, fontFace: "Cambria", margin: 0,
    });
    const crit = [
      ["Critique", "score ≥ 0,75", RED],
      ["Important", "score ≥ 0,50", GOLD],
      ["Secondaire", "score < 0,50", "8B93AD"],
    ];
    crit.forEach(([t, d, c], i) => {
      const x = 0.95 + i * 2.95;
      s.addShape(pres.shapes.OVAL, { x, y: 4.05, w: 0.3, h: 0.3, fill: { color: c } });
      s.addText([
        { text: t + "  ", options: { bold: true, color: NAVY } },
        { text: d, options: { color: MUTE } },
      ], { x: x + 0.42, y: 4.0, w: 2.4, h: 0.4, fontSize: 12.5, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addText("Score de base selon la modalité juridique (sanction 0,85 · interdiction 0,70 · obligation 0,65) + boosts contextuels (données personnelles +0,15, santé/sécurité +0,12…) — chaque facteur journalisé.", {
      x: 0.85, y: 4.5, w: 8.3, h: 0.6, fontSize: 11, color: MUTE, fontFace: "Calibri", margin: 0,
    });
    s.addNotes("Insister sur le caractère déterministe du scoring : pas de boîte noire, chaque facteur est journalisé dans criticality_reasons — argument d'auditabilité essentiel pour la conformité. La roadmap utilise un tri topologique (criticité + dépendances).");
    pageNo(s);
  }

  /* ============ S18 — PLAN §4 ============ */
  planSlide(3).addNotes("Dernière partie : la plateforme en production, le bilan et les perspectives.");

  /* ============ S19 — INTERFACES & PRODUCTION ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Déploiement · Interfaces & mise en production", "Une plateforme multi-tenant opérationnelle");
    s.addImage({ path: CAP + "fig_4_3_dashboard.png", x: 0.42, y: 1.45, w: 5.55, h: 2.95, sizing: { type: "contain", w: 5.55, h: 2.95 } });
    s.addText("Tableau de bord Owner — score de conformité, couverture, exigences à traiter (i18n ar/fr/en + RTL)", {
      x: 0.42, y: 4.42, w: 5.55, h: 0.55, fontSize: 10.5, italic: true, color: MUTE, fontFace: "Calibri", align: "center", margin: 0,
    });
    const right = [
      ["server", "Docker Compose", "3 services : MongoDB · Ollama · FastAPI"],
      ["checkW", "951 tests · ~50 % couverture", "CI GitHub Actions, Python 3.11→3.13"],
      ["users", "Multi-tenant", "isolation par organisation, vue Super Admin agrégée"],
      ["lock", "SaaS ou on-premise", "souveraineté des données juridiques"],
    ];
    right.forEach(([k, t, d], i) => {
      const y = 1.45 + i * 0.95;
      dot(s, k, 6.25, y, 0.46, i === 1 ? GREEN : NAVY);
      s.addText([
        { text: t, options: { fontSize: 12.5, bold: true, color: NAVY, breakLine: true } },
        { text: d, options: { fontSize: 10.5, color: MUTE } },
      ], { x: 6.85, y: y - 0.05, w: 2.75, h: 0.9, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addNotes("Mentionner la démo possible : chatbot multilingue (y compris derja normalisée), trace de l'agent, dashboards Owner vs Super Admin. La plateforme est en cours de déploiement pour une mise en production effective.");
    pageNo(s);
  }

  /* ============ S19b — DÉMONSTRATION (vidéo à insérer) ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Déploiement · Démonstration", "Daleel en action");
    // Cadre vidéo (gauche) — emplacement pour la vidéo enregistrée
    const vx = 0.55, vy = 1.5, vw = 5.55, vh = 3.12;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: vx, y: vy, w: vw, h: vh, rectRadius: 0.06, fill: { color: NAVY }, line: { color: GOLD, width: 1.25 }, shadow: sh() });
    s.addShape(pres.shapes.OVAL, { x: vx + vw / 2 - 0.45, y: vy + vh / 2 - 0.55, w: 0.9, h: 0.9, fill: { color: GOLD } });
    s.addText("▶", { x: vx + vw / 2 - 0.4, y: vy + vh / 2 - 0.55, w: 0.85, h: 0.9, fontSize: 30, bold: true, color: NAVY, align: "center", valign: "middle", fontFace: "Calibri", margin: 0 });
    s.addText("Vidéo de démonstration", { x: vx, y: vy + vh / 2 + 0.42, w: vw, h: 0.35, fontSize: 13, bold: true, color: WHITE, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText("à insérer dans PowerPoint (Insertion ▸ Vidéo)", { x: vx, y: vy + vh / 2 + 0.74, w: vw, h: 0.3, fontSize: 10, italic: true, color: "AEB6CE", align: "center", fontFace: "Calibri", margin: 0 });
    s.addText("Scénario de démonstration en direct", { x: vx, y: vy + vh + 0.12, w: vw, h: 0.3, fontSize: 10.5, italic: true, color: MUTE, align: "center", fontFace: "Calibri", margin: 0 });
    // Ce que montre la démo (droite)
    s.addText("Le parcours montré", { x: 6.45, y: 1.5, w: 3, h: 0.4, fontSize: 14.5, bold: true, color: NAVY, fontFace: "Cambria", margin: 0 });
    const demo = [
      ["comments", "Question juridique en langage naturel", "en arabe et en français"],
      ["search", "Réponse sourcée en quelques secondes", "chaque article cité et vérifiable"],
      ["robot", "Trace de l'agent ReAct", "les outils appelés, étape par étape"],
      ["dash", "Tableau de bord conformité", "score, couverture, exigences à traiter"],
    ];
    demo.forEach(([k, t, d], i) => {
      const y = 2.0 + i * 0.78;
      dot(s, k, 6.45, y, 0.44, i % 2 ? GOLD : NAVY);
      s.addText([
        { text: t, options: { fontSize: 11.5, bold: true, color: NAVY, breakLine: true } },
        { text: d, options: { fontSize: 10, color: MUTE } },
      ], { x: 7.05, y: y - 0.04, w: 2.55, h: 0.74, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addNotes("Lancer la vidéo de démonstration. Si possible, enchaîner sur une démo live : une vraie question juridique → réponse sourcée → trace de l'agent → dashboard. Garder la démo courte (1 à 2 min) et préparée pour éviter les aléas réseau.");
    pageNo(s);
  }

  /* ============ S19c — AVANT / APRÈS (valeur métier) ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Déploiement · Valeur métier", "Avant / après Daleel");
    // En-têtes de colonnes
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 3.0, y: 1.42, w: 3.05, h: 0.46, rectRadius: 0.06, fill: { color: "EFE3E1" } });
    s.addText("SANS DALEEL", { x: 3.0, y: 1.42, w: 3.05, h: 0.46, fontSize: 12, bold: true, color: RED, align: "center", valign: "middle", charSpacing: 1.5, fontFace: "Calibri", margin: 0 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.2, y: 1.42, w: 3.25, h: 0.46, rectRadius: 0.06, fill: { color: GOLDLT } });
    s.addText("AVEC DALEEL", { x: 6.2, y: 1.42, w: 3.25, h: 0.46, fontSize: 12, bold: true, color: "8A6D1C", align: "center", valign: "middle", charSpacing: 1.5, fontFace: "Calibri", margin: 0 });
    const comp = [
      ["bolt", "Temps de réponse", "Des heures de recherche manuelle", "8 à 15 secondes"],
      ["file", "Traçabilité", "Sources à retrouver à la main", "100 % sourcé & journalisé"],
      ["lang", "Multilinguisme ar / fr", "Recoupement manuel fastidieux", "Unifié automatiquement"],
      ["shield", "Pilotage conformité", "Tableurs épars, déconnectés des textes", "Tableau de bord temps réel"],
    ];
    const ry = 2.04, rh = 0.6, gap = 0.12;
    comp.forEach(([k, dim, av, ap], i) => {
      const y = ry + i * (rh + gap);
      dot(s, k, 0.55, y + 0.07, 0.46, NAVY);
      s.addText(dim, { x: 1.15, y, w: 1.85, h: rh, fontSize: 12, bold: true, color: NAVY, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 3.0, y, w: 3.05, h: rh, rectRadius: 0.05, fill: { color: ICE } });
      s.addText(av, { x: 3.12, y, w: 2.8, h: rh, fontSize: 10.5, color: MUTE, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.2, y, w: 3.25, h: rh, rectRadius: 0.05, fill: { color: GOLDLT } });
      s.addText(ap, { x: 6.32, y, w: 3.0, h: rh, fontSize: 11, bold: true, color: NAVY, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addText("D'un travail de juriste qui se compte en heures à une réponse sourcée et traçable en quelques secondes.", {
      x: 0.55, y: 5.02, w: 8.9, h: 0.4, fontSize: 12, italic: true, color: NAVY, fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addNotes("Slide « valeur ». Insister sur le gain concret pour le métier : temps, traçabilité, conformité. Si tu disposes d'un chiffre réel (heures/dossier, coût juriste), remplace « des heures » par ce chiffre — un gain chiffré est bien plus convaincant. Honnêteté : les valeurs « Avec Daleel » sont mesurées (latence 8-15 s, 100 % des réponses sourcées).");
    pageNo(s);
  }

  /* ============ S20 — RÉALISATIONS ============ */
  {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    s.addText("CONCLUSION · BILAN", {
      x: 0.7, y: 0.42, w: 8, h: 0.3, fontSize: 10.5, bold: true, color: GOLD, charSpacing: 2, fontFace: "Calibri", margin: 0,
    });
    s.addText("Ce qui a été accompli", {
      x: 0.7, y: 0.72, w: 8.6, h: 0.6, fontSize: 27, bold: true, color: WHITE, fontFace: "Cambria", margin: 0,
    });
    const ach = [
      ["search", "Pipeline RAG complet", "6 modules + agent ReAct à 12 outils, 100 % local et traçable"],
      ["chart", "+50 % en Recall@1", "fine-tuning évalué sans fuite sur 50 requêtes gold validées"],
      ["shield", "Cycle de conformité intégré", "exigences → constats → actions → preuves → dashboards"],
      ["rocket", "Prêt pour la production", "Docker, CI/CD, 951 tests — en cours de déploiement effectif"],
    ];
    const cw = 4.35, chh = 1.62, gx = 0.3, gy = 0.28;
    ach.forEach(([k, t, d], i) => {
      const x = 0.6 + (i % 2) * (cw + gx);
      const y = 1.62 + Math.floor(i / 2) * (chh + gy);
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: chh, rectRadius: 0.08, fill: { color: NAVY2 }, shadow: sh() });
      dot(s, k, x + 0.22, y + 0.22, 0.52, GOLD);
      s.addText([
        { text: t, options: { fontSize: 15, bold: true, color: WHITE, breakLine: true } },
        { text: d, options: { fontSize: 11, color: "AEB6CE" } },
      ], { x: x + 0.95, y: y + 0.16, w: cw - 1.15, h: chh - 0.3, fontFace: "Calibri", margin: 0, valign: "middle" });
    });
    s.addNotes("Quatre messages à marteler : un système complet (pas un prototype), des gains mesurés proprement, l'intégration recherche+conformité unique sur le marché, et la mise en production en cours.");
    pageNo(s, true);
  }

  /* ============ S21 — PERSPECTIVES ============ */
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    header(s, "Conclusion · Perspectives", "Trois horizons");
    const hor = [
      ["Court terme", "Consolidation", ["Validation par un panel de praticiens du droit", "Renforcement du corpus arabe + re-fine-tuning", "Étude d'ablation quantitative des modules RAG"], NAVY],
      ["Moyen terme", "Expansion", ["Ouverture aux marchés européen et du Golfe", "Chaque pays = un ajout de corpus, pas une refonte", "Détection automatique d'amendements"], GOLD],
      ["Long terme", "Référence RegTech", ["Intégration ERP / GED", "Génération d'avis juridiques structurés", "Simulation prédictive d'impact réglementaire"], NAVY],
    ];
    hor.forEach(([h, t, items, c], i) => {
      const x = 0.55 + i * 3.05;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: 2.85, h: 3.55, rectRadius: 0.08, fill: { color: i === 1 ? GOLDLT : ICE }, shadow: sh() });
      s.addText(h.toUpperCase(), { x: x + 0.2, y: 1.62, w: 2.45, h: 0.3, fontSize: 10.5, bold: true, color: c === GOLD ? "8A6D1C" : MUTE, charSpacing: 1.5, fontFace: "Calibri", margin: 0 });
      s.addText(t, { x: x + 0.2, y: 1.92, w: 2.45, h: 0.45, fontSize: 17, bold: true, color: NAVY, fontFace: "Cambria", margin: 0 });
      s.addText(items.map((tx, j) => ({ text: tx, options: { bullet: true, breakLine: j < items.length - 1 } })),
        { x: x + 0.2, y: 2.5, w: 2.5, h: 2.3, fontSize: 11, color: "37405C", fontFace: "Calibri", paraSpaceAfter: 8 });
    });
    s.addNotes("Court terme = consolider le produit pour le premier déploiement commercial. Moyen terme = l'axe de croissance principal (Europe, Golfe). Long terme = positionner Daleel comme plateforme RegTech de référence.");
    pageNo(s);
  }

  /* ============ S22 — MERCI ============ */
  {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    dot(s, "scaleG", W / 2 - 0.45, 1.0, 0.9, NAVY2);
    s.addText("Merci pour votre attention", {
      x: 0.5, y: 2.05, w: 9, h: 0.8, fontSize: 38, bold: true, color: WHITE, fontFace: "Cambria", align: "center", margin: 0,
    });
    s.addText("Questions & discussion", {
      x: 0.5, y: 2.95, w: 9, h: 0.45, fontSize: 17, color: GOLD, fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addText("Manar Trimeche  ·  École Polytechnique de Sousse  ·  Didax IT  ·  2025–2026", {
      x: 0.5, y: 4.6, w: 9, h: 0.35, fontSize: 12, color: "AEB6CE", fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addNotes("Remercier le jury. Se tenir prête sur : la fuite de données (0 par construction), le choix qwen vs GPT-4 (confidentialité), les seuils de criticité (déterministes, journalisés), la couverture de tests (~50 %, seuil CI).");
    pageNo(s, true);
  }

  /* ============ SLIDES ANNEXES (réserve pour questions) ============ */
  function annexe(crumb, title, rows, note) {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    s.addText("ANNEXE · " + crumb.toUpperCase(), {
      x: 0.55, y: 0.28, w: 8.8, h: 0.28, fontSize: 10.5, bold: true,
      color: GOLD, charSpacing: 2, fontFace: "Calibri", margin: 0,
    });
    s.addText(title, {
      x: 0.55, y: 0.55, w: 8.9, h: 0.62, fontSize: 25, bold: true,
      color: NAVY, fontFace: "Cambria", margin: 0,
    });
    const body = rows.map(([k, v], i) => ([
      { text: k, options: { fontSize: 12.5, bold: true, color: NAVY, fill: { color: i % 2 ? WHITE : ICE }, align: "left", valign: "middle" } },
      { text: v, options: { fontSize: 12.5, color: "37405C", fill: { color: i % 2 ? WHITE : ICE }, align: "left", valign: "middle" } },
    ]));
    s.addTable(body, {
      x: 0.55, y: 1.45, w: 8.9, colW: [3.1, 5.8], rowH: 0.44,
      border: { pt: 0.5, color: "D5DAE8" }, fontFace: "Calibri", margin: 5,
    });
    if (note) s.addNotes(note);
    pageNo(s);
  }

  annexe("Fine-tuning des embeddings", "Hyperparamètres du fine-tuning", [
    ["Modèle de base", "paraphrase-multilingual-mpnet-base-v2 (768 dimensions)"],
    ["Fonction de perte", "MultipleNegativesRankingLoss (apprentissage contrastif)"],
    ["Données", "973 paires question–article, issues de 487 articles propres"],
    ["Batch size", "32"],
    ["Learning rate", "2 × 10⁻⁵ — optimiseur AdamW"],
    ["Epochs", "3"],
    ["Normalisation", "L2 (similarité cosinus)"],
    ["Évaluation", "50 requêtes gold (30 fr / 20 ar) — zéro fuite, validées par un juriste"],
  ], "Slide de réserve. Tous les hyperparamètres exacts du fine-tuning, à montrer si le jury demande le détail.");

  annexe("Recherche & pipeline RAG", "Paramètres du retrieval", [
    ["Recherche dense", "index FAISS (HNSW) sur embeddings fine-tunés"],
    ["Recherche lexicale", "signaux mots-clés (correspondance exacte de termes)"],
    ["Fusion hybride", "pondération 0,56 dense / 0,20 lexical / 0,14 / 0,10"],
    ["Reranking", "cross-encoder ms-marco MiniLM-L6, avec seuil de rejet"],
    ["Segmentation", "chunks de 1 500 caractères, chevauchement de 200"],
    ["Routeur de domaine", "5 domaines juridiques, repli LLM si ambigu"],
    ["Garde-qualité", "vérif. des références + citations + cohérence de langue"],
  ], "Slide de réserve. Détail du pipeline RAG à 6 modules : pondérations, modèles et seuils exacts.");

  annexe("Génération & agent", "LLM, agent et industrialisation", [
    ["LLM de génération", "qwen2.5:7b via Ollama (licence Apache 2.0, 100 % on-premise)"],
    ["Paramètres", "température 0,15 · top-p 0,9 · contexte 8 192 tokens"],
    ["Function calling", "natif Ollama — appels d'outils typés (pas de parsing fragile)"],
    ["Outils de l'agent", "12 outils en 3 tiers : recherche · graphe · conformité"],
    ["Garde-fous", "budget d'itérations + timeout global"],
    ["Tests", "951 tests collectés · ~50 % de couverture (seuil CI)"],
    ["CI / CD", "GitHub Actions, Python 3.11 → 3.13 · LLM mocké en test"],
    ["Déploiement", "Docker Compose : MongoDB · Ollama · FastAPI"],
  ], "Slide de réserve. Paramètres de génération, architecture de l'agent et industrialisation.");

  await pres.writeFile({ fileName: "C:\\Users\\RSCH\\Daleel\\presentation\\Soutenance_Daleel_Manar.pptx" });
  console.log("OK — Soutenance_Daleel_Manar.pptx générée (" + pageNum + " slides)");
}

main().catch((e) => { console.error(e); process.exit(1); });
