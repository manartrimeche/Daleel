const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "C:\\Users\\RSCH\\Daleel";
const CAP = path.join(ROOT, "captures");
const OUT = path.join(ROOT, "presentation", "Soutenance_Daleel_15min_demo.pptx");
const DEMO_GIF = path.join(ROOT, "presentation", "demo_daleel.gif");
const DEMO_COVER = path.join(ROOT, "presentation", "demo_daleel_cover.png");
const DEMO_WEBM = path.join(ROOT, "presentation", "demo_daleel.webm");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_16x9";
pptx.author = "Manar Trimeche";
pptx.company = "Ecole Polytechnique de Sousse - Didax IT";
pptx.subject = "Soutenance PFE Daleel";
pptx.title = "Daleel - Soutenance PFE";
pptx.lang = "fr-FR";
pptx.theme = {
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  lang: "fr-FR",
};

const W = 13.333;
const H = 7.5;
const NAVY = "232946";
const NAVY2 = "2E3654";
const GOLD = "D4A437";
const GOLD2 = "F4E8C8";
const WHITE = "FFFFFF";
const ICE = "F5F7FB";
const INK = "1E2433";
const MUTED = "626D83";
const GREEN = "1F9D6B";
const RED = "C0392B";
let slideNo = 0;

function addSlide(bg = WHITE) {
  const s = pptx.addSlide();
  s.background = { color: bg };
  slideNo += 1;
  return s;
}

function foot(s, dark = false) {
  s.addText("Daleel - Soutenance PFE", {
    x: 0.55, y: 7.05, w: 4.2, h: 0.22, margin: 0,
    fontFace: "Calibri", fontSize: 8.5, color: dark ? "AEB6CE" : MUTED,
  });
  s.addText(String(slideNo), {
    x: 12.55, y: 7.05, w: 0.3, h: 0.22, margin: 0,
    fontFace: "Calibri", fontSize: 8.5, color: dark ? "AEB6CE" : MUTED, align: "right",
  });
}

function title(s, section, text) {
  s.addText(section.toUpperCase(), {
    x: 0.65, y: 0.38, w: 11.8, h: 0.25, margin: 0,
    fontFace: "Calibri", fontSize: 9.5, bold: true, color: GOLD, charSpacing: 1.6,
  });
  s.addText(text, {
    x: 0.65, y: 0.72, w: 11.8, h: 0.55, margin: 0,
    fontFace: "Cambria", fontSize: 26, bold: true, color: NAVY,
  });
}

function card(s, x, y, w, h, fill = ICE, line = "E1E6F0") {
  s.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: fill },
    line: { color: line, width: 0.7 },
    shadow: { type: "outer", color: "1A1A2E", opacity: 0.14, blur: 2, angle: 45, distance: 1 },
  });
}

function bulletList(s, items, x, y, w, h, opts = {}) {
  s.addText(items.map((t, i) => ({
    text: t,
    options: {
      bullet: { type: "ul" },
      breakLine: i < items.length - 1,
      paraSpaceAfterPt: opts.space || 8,
    },
  })), {
    x, y, w, h, margin: 0.04,
    fontFace: "Calibri", fontSize: opts.size || 15,
    color: opts.color || INK,
    fit: "shrink",
    breakLine: false,
  });
}

function chip(s, text, x, y, w, color = NAVY, fill = GOLD2) {
  s.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.34, rectRadius: 0.08,
    fill: { color: fill },
    line: { color: fill },
  });
  s.addText(text, {
    x, y: y + 0.07, w, h: 0.18, margin: 0,
    fontFace: "Calibri", fontSize: 9.5, bold: true,
    color, align: "center",
  });
}

function image(s, file, x, y, w, h) {
  s.addImage({ path: path.join(CAP, file), x, y, w, h, sizing: { type: "contain", x, y, w, h } });
}

function notes(s, text) {
  s.addNotes(text);
}

function splitTitleBody(s, heading, body, x, y, w, h, color = NAVY) {
  s.addText(heading, {
    x, y, w, h: 0.35, margin: 0,
    fontFace: "Cambria", fontSize: 15.5, bold: true, color,
  });
  s.addText(body, {
    x, y: y + 0.48, w, h: h - 0.48, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: MUTED,
    fit: "shrink",
  });
}

// 1
{
  const s = addSlide(NAVY);
  s.addShape(pptx.ShapeType.arc, { x: -1.1, y: 4.6, w: 4, h: 4, line: { color: NAVY2, transparency: 100 }, fill: { color: NAVY2 } });
  s.addText("DALEEL", {
    x: 0.7, y: 1.1, w: 12, h: 0.75, margin: 0,
    fontFace: "Cambria", fontSize: 46, bold: true, color: WHITE, charSpacing: 5,
  });
  s.addText("Plateforme integree d'assistance juridique et de conformite reglementaire fondee sur l'intelligence artificielle", {
    x: 0.72, y: 2.08, w: 10.2, h: 0.7, margin: 0,
    fontFace: "Calibri", fontSize: 19, color: "D9DEF0",
  });
  s.addShape(pptx.ShapeType.line, { x: 0.72, y: 3.12, w: 3.1, h: 0, line: { color: GOLD, width: 2 } });
  s.addText("Projet de Fin d'Etudes - Soutenance", {
    x: 0.72, y: 3.42, w: 6.8, h: 0.35, margin: 0,
    fontFace: "Calibri", fontSize: 14.5, bold: true, color: GOLD,
  });
  s.addText("Manar Trimeche\nEncadrant academique : Dr Nizar Omheni\nEncadrant professionnel : M. Raouf Bouneb\nEcole Polytechnique de Sousse - Didax IT - 2025/2026", {
    x: 0.72, y: 4.25, w: 8.5, h: 1.0, margin: 0,
    fontFace: "Calibri", fontSize: 13, color: "AEB6CE", breakLine: false,
  });
  foot(s, true);
  notes(s, "Bonjour, je vais vous presenter mon projet de fin d'etudes intitule Daleel. Daleel signifie le guide. L'objectif est de faciliter l'acces a l'information juridique tunisienne et d'aider les organisations a suivre leurs obligations de conformite. Annoncer que la presentation dure 15 minutes avec une courte demonstration integree.");
}

// 2
{
  const s = addSlide();
  title(s, "Plan", "Deroulement de la soutenance");
  const rows = [
    ["01", "Contexte et problematique", "Pourquoi le besoin existe"],
    ["02", "Solution proposee", "RAG juridique + Compliance Ops"],
    ["03", "Conception et realisation", "Architecture, pipeline, modules"],
    ["04", "Demo, qualite et bilan", "Interfaces, tests, limites, perspectives"],
  ];
  rows.forEach((r, i) => {
    const y = 1.55 + i * 1.12;
    card(s, 0.95, y, 11.45, 0.82, i === 2 ? GOLD2 : ICE);
    s.addText(r[0], { x: 1.2, y: y + 0.16, w: 0.65, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 22, bold: true, color: i === 2 ? GOLD : NAVY });
    s.addText(r[1], { x: 2.05, y: y + 0.14, w: 4.3, h: 0.25, margin: 0, fontFace: "Calibri", fontSize: 14.5, bold: true, color: NAVY });
    s.addText(r[2], { x: 2.05, y: y + 0.47, w: 8.5, h: 0.22, margin: 0, fontFace: "Calibri", fontSize: 11.2, color: MUTED });
  });
  foot(s);
  notes(s, "Presenter le fil directeur : on part du besoin metier, puis la solution, puis l'architecture et les modules realises, avant de passer a la demonstration et au bilan.");
}

// 3
{
  const s = addSlide();
  title(s, "Contexte", "Une information juridique difficile a exploiter");
  const items = [
    ["Volume", "Codes, lois, decrets, circulaires et textes modificatifs."],
    ["Formats", "PDF, Word, images scannees, OCR parfois necessaire."],
    ["Langues", "Francais, arabe et parfois anglais dans le meme environnement."],
    ["Evolution", "Versions, amendements, abrogations et nouveaux articles."],
  ];
  items.forEach((it, i) => {
    const x = 0.75 + (i % 2) * 6.05;
    const y = 1.65 + Math.floor(i / 2) * 1.8;
    card(s, x, y, 5.5, 1.25);
    chip(s, it[0], x + 0.25, y + 0.22, 1.2);
    s.addText(it[1], { x: x + 0.25, y: y + 0.68, w: 4.9, h: 0.35, margin: 0, fontFace: "Calibri", fontSize: 13.2, color: INK, fit: "shrink" });
  });
  s.addText("Resultat : la recherche manuelle est lente, incomplete et difficile a tracer.", {
    x: 1.15, y: 5.55, w: 11, h: 0.36, margin: 0,
    fontFace: "Cambria", fontSize: 18, bold: true, color: NAVY, align: "center",
  });
  foot(s);
  notes(s, "Expliquer le constat de depart : dans le domaine juridique, l'information est volumineuse et changeante. Les documents ne sont pas toujours propres ou numeriques. Le probleme n'est donc pas seulement de chercher un mot-cle, mais de retrouver le bon contexte, dans la bonne version, et de garder la trace de la source.");
}

// 4
{
  const s = addSlide();
  title(s, "Problematique", "Trouver vite, repondre juste, prouver la source");
  card(s, 0.85, 1.55, 11.65, 1.55, NAVY, NAVY);
  s.addText("Comment concevoir une plateforme d'assistance juridique qui fournit des reponses pertinentes, tracables et exploitables dans le contexte reglementaire tunisien ?", {
    x: 1.15, y: 1.88, w: 11.05, h: 0.72, margin: 0,
    fontFace: "Cambria", fontSize: 20, bold: true, color: WHITE, align: "center", fit: "shrink",
  });
  const enjeux = [
    "Pertinence : retrouver le bon passage, pas seulement le bon document.",
    "Fiabilite : limiter les hallucinations grace aux sources.",
    "Tracabilite : citer les textes et garder l'audit des decisions.",
    "Action : transformer l'information en exigences et actions de conformite.",
  ];
  bulletList(s, enjeux, 1.2, 3.7, 10.9, 1.6, { size: 15.5, space: 10 });
  foot(s);
  notes(s, "Formuler clairement la problematique. Insister sur les quatre criteres qui guident le projet : pertinence, fiabilite, tracabilite et passage a l'action. Dire que Daleel ne remplace pas le juriste ; il l'assiste avec une information sourcée.");
}

// 5
{
  const s = addSlide();
  title(s, "Objectifs", "Transformer des documents juridiques en outil d'aide a la decision");
  const cols = [
    ["Centraliser", "Regrouper les documents juridiques et les donnees de conformite."],
    ["Extraire", "Lire automatiquement PDF, DOCX, TXT, images et documents scannes."],
    ["Indexer", "Decouper, vectoriser et rechercher semantiquement les passages."],
    ["Repondre", "Generer une reponse multilingue fondee sur les sources."],
    ["Piloter", "Suivre exigences, actions, preuves, exceptions et audit."],
  ];
  cols.forEach((c, i) => {
    const x = 0.55 + i * 2.55;
    card(s, x, 1.7, 2.25, 3.65, i === 2 ? GOLD2 : ICE);
    s.addText(String(i + 1).padStart(2, "0"), { x: x + 0.2, y: 1.95, w: 0.65, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 20, bold: true, color: GOLD });
    s.addText(c[0], { x: x + 0.2, y: 2.55, w: 1.85, h: 0.38, margin: 0, fontFace: "Cambria", fontSize: 15.5, bold: true, color: NAVY });
    s.addText(c[1], { x: x + 0.2, y: 3.1, w: 1.85, h: 1.45, margin: 0, fontFace: "Calibri", fontSize: 11.2, color: MUTED, fit: "shrink" });
  });
  foot(s);
  notes(s, "Presenter les objectifs comme une chaine : centraliser, extraire, indexer, repondre et piloter. L'idee forte est de passer d'une base documentaire passive a un outil d'aide a la decision.");
}

// 6
{
  const s = addSlide();
  title(s, "Solution", "Deux volets complementaires");
  card(s, 0.85, 1.55, 5.65, 3.95, NAVY, NAVY);
  s.addText("RAG juridique", { x: 1.2, y: 1.9, w: 4.95, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 22, bold: true, color: GOLD });
  bulletList(s, [
    "Questions en langage naturel",
    "Recherche semantique dans le corpus",
    "Generation de reponses avec sources",
    "Controle qualite anti-hallucination",
  ], 1.25, 2.65, 4.7, 1.75, { size: 14, color: "E8EDF5" });
  card(s, 6.85, 1.55, 5.65, 3.95, GOLD2, GOLD2);
  s.addText("Compliance Ops", { x: 7.2, y: 1.9, w: 4.95, h: 0.4, margin: 0, fontFace: "Cambria", fontSize: 22, bold: true, color: NAVY });
  bulletList(s, [
    "Profils d'entreprise et applicabilite",
    "Exigences, constats et actions",
    "Preuves, controles et exceptions",
    "Roadmap et tableaux de bord",
  ], 7.25, 2.65, 4.7, 1.75, { size: 14, color: INK });
  s.addText("Message cle : assister l'expert juridique, pas le remplacer.", {
    x: 1.2, y: 6.0, w: 10.9, h: 0.35, margin: 0,
    fontFace: "Cambria", fontSize: 18, bold: true, color: NAVY, align: "center",
  });
  foot(s);
  notes(s, "Presenter Daleel comme une plateforme a deux volets. Le premier volet repond aux questions a partir des textes. Le second transforme les informations en elements suivables de conformite. Bien preciser que l'expert reste decisionnaire.");
}

// 7
{
  const s = addSlide();
  title(s, "Architecture", "Une architecture modulaire et extensible");
  image(s, "fig_3_1_architecture.png", 0.65, 1.45, 7.35, 4.75);
  card(s, 8.35, 1.5, 4.15, 4.65);
  splitTitleBody(s, "Couches principales", "Frontend React/Vite\nAPI FastAPI\nServices metier\nTraitement documentaire\nMongoDB + FAISS\nLLM local via Ollama", 8.75, 1.85, 3.45, 2.35);
  splitTitleBody(s, "Choix d'ingenierie", "Separation claire des responsabilites, execution locale possible, et evolution par modules.", 8.75, 4.45, 3.45, 0.85, GOLD);
  foot(s);
  notes(s, "Decrire l'architecture sans entrer dans toutes les classes. Cote utilisateur, React. Cote serveur, FastAPI expose les endpoints. Les services metier gerent la recherche, les documents, la conformite et les cas. MongoDB stocke les donnees structurees, FAISS gere la recherche vectorielle, et Ollama permet une generation locale.");
}

// 8
{
  const s = addSlide();
  title(s, "Pipeline RAG", "Du document brut a la reponse sourcee");
  const steps = [
    ["Upload", "PDF, DOCX, TXT, images"],
    ["Extraction/OCR", "texte natif ou document scanne"],
    ["Nettoyage", "normalisation et segmentation"],
    ["Embeddings", "representation semantique multilingue"],
    ["FAISS", "recherche vectorielle et reranking"],
    ["LLM", "reponse claire avec sources"],
  ];
  steps.forEach((st, i) => {
    const x = 0.5 + i * 2.08;
    card(s, x, 1.65, 1.82, 2.35, i === 5 ? NAVY : ICE, i === 5 ? NAVY : "E1E6F0");
    s.addText(String(i + 1), { x: x + 0.16, y: 1.9, w: 0.35, h: 0.3, margin: 0, fontFace: "Cambria", fontSize: 18, bold: true, color: i === 5 ? GOLD : GOLD });
    s.addText(st[0], { x: x + 0.16, y: 2.48, w: 1.45, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 13, bold: true, color: i === 5 ? WHITE : NAVY });
    s.addText(st[1], { x: x + 0.16, y: 2.92, w: 1.45, h: 0.75, margin: 0, fontFace: "Calibri", fontSize: 10.2, color: i === 5 ? "D9DEF0" : MUTED, fit: "shrink" });
    if (i < steps.length - 1) s.addText(">", { x: x + 1.85, y: 2.55, w: 0.25, h: 0.3, margin: 0, fontFace: "Calibri", fontSize: 18, bold: true, color: GOLD });
  });
  image(s, "fig_3_2_flux_rag.png", 2.35, 4.35, 8.65, 1.6);
  foot(s);
  notes(s, "Expliquer le parcours d'un document. Le point important : le LLM ne repond pas seul ; il s'appuie sur les passages retrouves. Cela reduit les hallucinations et donne a l'utilisateur des sources verifiables.");
}

// 9
{
  const s = addSlide();
  title(s, "Modules realises", "De la recherche juridique au pilotage de conformite");
  const modules = [
    "Documents, extraction, chunking et index FAISS",
    "Chatbot juridique multilingue avec sources",
    "Lois, articles, versions et amendements",
    "Exigences applicables et profils d'entreprise",
    "Criticite, actions correctives et roadmap",
    "Case management, preuves, controles et exceptions",
    "Agent ReAct avec journal des outils invoques",
    "Tableaux de bord et exports",
  ];
  bulletList(s, modules, 0.9, 1.55, 5.7, 4.8, { size: 14.2, space: 7 });
  image(s, "fig_3_5_modele_conformite.png", 7.0, 1.7, 5.65, 4.2);
  foot(s);
  notes(s, "Montrer que le projet ne se limite pas a un chatbot. Il couvre l'ingestion documentaire, la recherche, la structuration juridique, la conformite operationnelle, les cas, les preuves et le pilotage.");
}

// 10
{
  const s = addSlide();
  title(s, "Demonstration", "Scenario utilisateur en 2 minutes");
  card(s, 0.75, 1.4, 8.25, 4.9, WHITE);
  if (fs.existsSync(DEMO_WEBM)) {
    const cover = "data:image/png;base64," + fs.readFileSync(DEMO_COVER).toString("base64");
    s.addMedia({ type: "video", path: DEMO_WEBM, cover, x: 0.95, y: 1.62, w: 7.85, h: 4.42 });
  } else {
    s.addImage({ path: DEMO_GIF, x: 0.95, y: 1.62, w: 7.85, h: 4.42, sizing: { type: "contain", x: 0.95, y: 1.62, w: 7.85, h: 4.42 } });
  }
  card(s, 9.35, 1.4, 3.25, 4.9, NAVY, NAVY);
  s.addText("Fil de demo", { x: 9.7, y: 1.75, w: 2.6, h: 0.35, margin: 0, fontFace: "Cambria", fontSize: 17, bold: true, color: GOLD });
  bulletList(s, [
    "poser une question juridique",
    "verifier les sources",
    "ouvrir la gestion documentaire",
    "consulter le dashboard",
    "montrer la tracabilite agent",
  ], 9.75, 2.42, 2.35, 2.4, { size: 12.2, color: "E8EDF5", space: 7 });
  s.addText("La demo video est integree dans le fichier PowerPoint.", {
    x: 9.75, y: 5.35, w: 2.35, h: 0.4, margin: 0,
    fontFace: "Calibri", fontSize: 10.5, italic: true, color: "AEB6CE",
  });
  foot(s);
  notes(s, "Lancer la demonstration ou commenter l'animation. Parcours conseille : poser une question, montrer la reponse sourcee, expliquer l'import documentaire, puis le tableau de bord de conformite et enfin le journal de l'agent. Ne pas depasser deux minutes.");
}

// 11
{
  const s = addSlide();
  title(s, "Qualite et securite", "Preparer le projet a l'industrialisation");
  const stats = [
    ["865", "tests backend valides", "baseline projet documentee"],
    ["60", "fichiers de tests", "unitaires et integration"],
    ["Docker", "deploiement reproductible", "MongoDB, Ollama, FastAPI"],
    ["Local", "confidentialite", "LLM compatible Ollama"],
  ];
  stats.forEach((st, i) => {
    const x = 0.75 + (i % 2) * 6.05;
    const y = 1.65 + Math.floor(i / 2) * 1.65;
    card(s, x, y, 5.5, 1.15, i === 0 ? GOLD2 : ICE);
    s.addText(st[0], { x: x + 0.22, y: y + 0.22, w: 1.3, h: 0.45, margin: 0, fontFace: "Cambria", fontSize: 22, bold: true, color: i === 0 ? GOLD : NAVY });
    s.addText(st[1], { x: x + 1.65, y: y + 0.22, w: 3.4, h: 0.25, margin: 0, fontFace: "Calibri", fontSize: 13, bold: true, color: NAVY });
    s.addText(st[2], { x: x + 1.65, y: y + 0.55, w: 3.4, h: 0.25, margin: 0, fontFace: "Calibri", fontSize: 10.5, color: MUTED });
  });
  bulletList(s, [
    "Authentification, roles, organisations, invitations et notifications.",
    "Rate limiting, CORS configurable, validation des schemas.",
    "CI GitHub Actions, linting, couverture et tests automatises.",
  ], 1.05, 5.25, 11.1, 0.9, { size: 13.5, space: 5 });
  foot(s);
  notes(s, "Insister sur la maturite logicielle : tests, Docker, CI, separation des services, execution locale possible pour proteger les donnees. Dire que la securite production reste une perspective de durcissement mais que les bases sont en place.");
}

// 12
{
  const s = addSlide();
  title(s, "Bilan d'avancement", "Un coeur fonctionnel deja operationnel");
  card(s, 0.85, 1.55, 4.0, 3.7, NAVY, NAVY);
  s.addText("87 %", { x: 1.15, y: 2.2, w: 3.4, h: 0.85, margin: 0, fontFace: "Cambria", fontSize: 54, bold: true, color: GOLD, align: "center" });
  s.addText("avancement global estime", { x: 1.15, y: 3.18, w: 3.4, h: 0.32, margin: 0, fontFace: "Calibri", fontSize: 14, color: WHITE, align: "center" });
  s.addText("Coeur backend, RAG, conformite, interfaces, tests et documentation sont realises.", {
    x: 1.15, y: 3.85, w: 3.4, h: 0.8, margin: 0, fontFace: "Calibri", fontSize: 11.5, color: "D9DEF0", align: "center", fit: "shrink",
  });
  bulletList(s, [
    "Realise : ingestion, recherche, RAG, conformite, case management, dashboard.",
    "En stabilisation : UX frontend, tests bout-en-bout, securite navigateur.",
    "A optimiser : scalabilite vectorielle et latence sur tres grands volumes.",
  ], 5.45, 1.85, 6.8, 2.25, { size: 14.5, space: 9 });
  image(s, "fig_5_4_finetuning_resultats.png", 5.6, 4.25, 6.3, 1.5);
  foot(s);
  notes(s, "Presenter un bilan honnete. Le projet est avance, le coeur fonctionnel est disponible, mais il reste la phase de stabilisation finale. Eviter de dire que tout est parfait : le jury apprecie une lecture critique.");
}

// 13
{
  const s = addSlide();
  title(s, "Limites", "Une lecture critique du projet");
  const limits = [
    ["Validation metier", "besoin d'un panel plus large de juristes et responsables conformite"],
    ["Experience utilisateur", "fluidifier certains parcours et clarifier les etats d'erreur"],
    ["Securite production", "renforcer CSP, sanitization, secrets et monitoring"],
    ["Scalabilite", "optimiser les index et la latence sur de tres grands corpus"],
  ];
  limits.forEach((l, i) => {
    const x = 0.85 + (i % 2) * 5.95;
    const y = 1.65 + Math.floor(i / 2) * 1.65;
    card(s, x, y, 5.35, 1.18, i === 0 ? GOLD2 : ICE);
    splitTitleBody(s, l[0], l[1], x + 0.28, y + 0.22, 4.85, 0.85, i === 0 ? GOLD : NAVY);
  });
  s.addText("Ces limites sont identifiees et traduites en feuille de route.", {
    x: 1.0, y: 5.55, w: 11.3, h: 0.35, margin: 0,
    fontFace: "Cambria", fontSize: 18, bold: true, color: NAVY, align: "center",
  });
  foot(s);
  notes(s, "Expliquer les limites de facon maitrisee : validation par experts, UX, securite production, scalabilite. L'important est de montrer que ces limites sont connues et organisees dans les perspectives.");
}

// 14
{
  const s = addSlide();
  title(s, "Perspectives", "Vers une plateforme LegalTech / RegTech extensible");
  const horizons = [
    ["Court terme", "stabiliser la demonstration, renforcer les tests E2E, consolider l'UX"],
    ["Moyen terme", "veille JORT, detection automatique des amendements, feedback utilisateur"],
    ["Long terme", "extension Maghreb/Golfe, integration GED/ERP, avis juridiques structures"],
  ];
  horizons.forEach((h, i) => {
    const x = 0.75 + i * 4.15;
    card(s, x, 1.7, 3.65, 3.8, i === 1 ? GOLD2 : ICE);
    s.addText(h[0].toUpperCase(), { x: x + 0.28, y: 1.95, w: 3.1, h: 0.25, margin: 0, fontFace: "Calibri", fontSize: 9.5, bold: true, color: i === 1 ? GOLD : MUTED, charSpacing: 1.2 });
    s.addText(h[1], { x: x + 0.28, y: 2.55, w: 3.1, h: 1.9, margin: 0, fontFace: "Calibri", fontSize: 14.2, color: INK, fit: "shrink" });
  });
  foot(s);
  notes(s, "Presenter les perspectives par horizon. Court terme : stabilisation. Moyen terme : veille et amendements. Long terme : extension geographique et integrations. Relier cela a l'architecture modulaire presentee plus tot.");
}

// 15
{
  const s = addSlide(NAVY);
  s.addText("Conclusion", {
    x: 0.8, y: 0.75, w: 11.5, h: 0.5, margin: 0,
    fontFace: "Calibri", fontSize: 13, bold: true, color: GOLD, charSpacing: 2,
  });
  s.addText("Daleel rend l'information juridique tunisienne plus accessible, sourcee et exploitable.", {
    x: 0.8, y: 1.48, w: 11.3, h: 1.05, margin: 0,
    fontFace: "Cambria", fontSize: 31, bold: true, color: WHITE, fit: "shrink",
  });
  const msgs = [
    ["Recherche", "retrouver rapidement les passages pertinents"],
    ["Fiabilite", "reponses ancrees dans les documents sources"],
    ["Conformite", "passer du texte juridique aux actions suivables"],
  ];
  msgs.forEach((m, i) => {
    const x = 0.9 + i * 4.05;
    card(s, x, 3.55, 3.45, 1.35, NAVY2, NAVY2);
    s.addText(m[0], { x: x + 0.22, y: 3.82, w: 3.0, h: 0.32, margin: 0, fontFace: "Cambria", fontSize: 16, bold: true, color: GOLD });
    s.addText(m[1], { x: x + 0.22, y: 4.22, w: 3.0, h: 0.42, margin: 0, fontFace: "Calibri", fontSize: 11.2, color: "D9DEF0", fit: "shrink" });
  });
  s.addText("Merci pour votre attention - Questions & discussion", {
    x: 0.8, y: 6.1, w: 11.7, h: 0.45, margin: 0,
    fontFace: "Cambria", fontSize: 22, bold: true, color: GOLD, align: "center",
  });
  foot(s, true);
  notes(s, "Conclure en rappelant l'apport principal : une plateforme qui combine recherche juridique sourcee et pilotage de conformite. Remercier le jury et ouvrir la discussion.");
}

pptx.writeFile({ fileName: OUT }).then(() => {
  console.log(`OK - ${OUT} generated with ${slideNo} slides.`);
});
