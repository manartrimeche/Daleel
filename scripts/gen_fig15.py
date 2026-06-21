# -*- coding: utf-8 -*-
"""Generate Figure 1.5 — Cas d'utilisation : assistant juridique IA et Legal RAG."""
from PIL import Image, ImageDraw, ImageFont
import math

def load_fonts():
    sizes = {}
    try:
        sizes["title"] = ImageFont.truetype("arialbd.ttf", 32)
        sizes["pkg"] = ImageFont.truetype("arialbd.ttf", 22)
        sizes["actor"] = ImageFont.truetype("arialbd.ttf", 20)
        sizes["uc"] = ImageFont.truetype("arial.ttf", 17)
        sizes["note"] = ImageFont.truetype("arial.ttf", 15)
    except:
        f = ImageFont.load_default()
        for k in ["title","pkg","actor","uc","note"]:
            sizes[k] = f
    return sizes

FONTS = load_fonts()

BG = (255, 255, 255)
C_ACTOR = (40, 40, 40)
C_UC_FILL = (222, 240, 255)
C_UC_BORDER = (60, 120, 180)
C_PKG_BG = (248, 248, 255)
C_PKG_BORDER = (80, 80, 120)
C_PKG_TAB = (230, 230, 248)
C_LINE = (120, 120, 140)
C_SYS_BG = (252, 252, 255)
C_SYS_BORDER = (100, 100, 140)
C_TITLE = (20, 20, 70)


def draw_actor(d, x, y, name):
    r = 14
    d.ellipse([x-r, y, x+r, y+2*r], outline=C_ACTOR, width=2)
    d.line([x, y+2*r, x, y+2*r+40], fill=C_ACTOR, width=2)
    d.line([x-22, y+2*r+16, x+22, y+2*r+16], fill=C_ACTOR, width=2)
    d.line([x, y+2*r+40, x-20, y+2*r+65], fill=C_ACTOR, width=2)
    d.line([x, y+2*r+40, x+20, y+2*r+65], fill=C_ACTOR, width=2)
    lines = name.split("\n")
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=FONTS["actor"])
        d.text((x - tw/2, y+2*r+70 + i*22), line, fill=C_ACTOR, font=FONTS["actor"])


def draw_uc(d, cx, cy, text, w=280, h=42):
    d.ellipse([cx-w//2, cy-h//2, cx+w//2, cy+h//2], outline=C_UC_BORDER, width=2, fill=C_UC_FILL)
    lines = text.split("\n")
    line_h = 19
    total = len(lines) * line_h
    sy = cy - total//2
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=FONTS["uc"])
        d.text((cx - tw/2, sy + i*line_h), line, fill=(20, 20, 20), font=FONTS["uc"])
    return (cx, cy)


def draw_package(d, x, y, w, h, title):
    d.rectangle([x, y, x+w, y+h], outline=C_PKG_BORDER, width=2, fill=C_PKG_BG)
    tw = d.textlength(title, font=FONTS["pkg"]) + 20
    d.rectangle([x, y, x+tw, y+30], outline=C_PKG_BORDER, width=2, fill=C_PKG_TAB)
    d.text((x+10, y+4), title, fill=C_PKG_BORDER, font=FONTS["pkg"])


def draw_link(d, x1, y1, x2, y2, dashed=False):
    c = C_LINE
    if dashed:
        length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if length == 0: return
        steps = max(int(length / 12), 1)
        for i in range(0, steps, 2):
            t1 = i / steps
            t2 = min((i+1) / steps, 1.0)
            d.line([x1+(x2-x1)*t1, y1+(y2-y1)*t1, x1+(x2-x1)*t2, y1+(y2-y1)*t2], fill=c, width=1)
    else:
        d.line([x1, y1, x2, y2], fill=c, width=1)


def draw_include_label(d, x1, y1, x2, y2, label="include"):
    mx, my = (x1+x2)//2, (y1+y2)//2
    d.text((mx-30, my-16), f"<<{label}>>", fill=(100,100,140), font=FONTS["note"])


def gen():
    W, H = 1800, 1000
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    t = "Figure 1.5 — Cas d'utilisation : assistant juridique IA et Legal RAG"
    tw = d.textlength(t, font=FONTS["title"])
    d.text(((W-tw)//2, 12), t, fill=C_TITLE, font=FONTS["title"])

    # System box
    d.rectangle([310, 58, 1490, 950], outline=C_SYS_BORDER, width=3, fill=C_SYS_BG)
    d.text((325, 64), "« système » Plateforme Daleel", fill=C_SYS_BORDER, font=FONTS["pkg"])

    AX_L = 130
    AX_R = 1660

    draw_actor(d, AX_L, 150, "Membre")
    draw_actor(d, AX_L, 550, "Owner")
    draw_actor(d, AX_R, 300, "Serveur\nOllama")

    a_member = (AX_L, 198)
    a_owner = (AX_L, 598)
    a_ollama = (AX_R, 348)

    # --- Package: Question-réponse juridique ---
    draw_package(d, 370, 95, 550, 280, "Question-réponse juridique")
    ucs_qa = []
    labels_qa = [
        "Poser une question juridique",
        "Recevoir une réponse sourcée",
        "Activer le mode agentique (ReAct)",
        "Questionner un document téléversé",
        "Consulter les sources citées",
    ]
    for i, lbl in enumerate(labels_qa):
        pos = draw_uc(d, 645, 148+i*46, lbl, w=310, h=36)
        ucs_qa.append(pos)

    # --- Package: Interaction vocale ---
    draw_package(d, 370, 400, 550, 140, "Interaction vocale")
    ucs_voice = []
    labels_voice = [
        "Poser une question par la voix",
        "Écouter la réponse (synthèse vocale)",
    ]
    for i, lbl in enumerate(labels_voice):
        pos = draw_uc(d, 645, 448+i*46, lbl, w=310, h=36)
        ucs_voice.append(pos)

    # --- Package: Historique et conversations ---
    draw_package(d, 370, 565, 550, 180, "Historique et conversations")
    ucs_hist = []
    labels_hist = [
        "Consulter l'historique des conversations",
        "Archiver / Renommer une conversation",
        "Donner un feedback sur une réponse",
    ]
    for i, lbl in enumerate(labels_hist):
        pos = draw_uc(d, 645, 615+i*46, lbl, w=330, h=36)
        ucs_hist.append(pos)

    # --- Package: Pipeline RAG (interne) ---
    draw_package(d, 370, 770, 550, 160, "Pipeline RAG (traitement interne)")
    ucs_rag = []
    labels_rag = [
        "Recherche hybride FAISS + lexicale",
        "Reranking par cross-encoder",
        "Garde-qualité anti-hallucination",
    ]
    for i, lbl in enumerate(labels_rag):
        pos = draw_uc(d, 645, 818+i*44, lbl, w=320, h=36)
        ucs_rag.append(pos)

    # --- LINKS ---

    # Membre -> QA
    for uc in ucs_qa:
        draw_link(d, a_member[0]+25, a_member[1], uc[0]-155, uc[1])
    # Membre -> Voice
    for uc in ucs_voice:
        draw_link(d, a_member[0]+25, a_member[1], uc[0]-155, uc[1])
    # Membre -> Historique
    for uc in ucs_hist:
        draw_link(d, a_member[0]+25, a_member[1], uc[0]-165, uc[1])

    # Owner -> QA (aussi accès)
    for uc in ucs_qa:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-155, uc[1])
    # Owner -> Voice
    for uc in ucs_voice:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-155, uc[1])
    # Owner -> Historique
    for uc in ucs_hist:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-165, uc[1])

    # Ollama -> Pipeline RAG (include from QA)
    for uc in ucs_rag:
        draw_link(d, a_ollama[0]-25, a_ollama[1], uc[0]+160, uc[1])

    # Include: QA -> Pipeline RAG
    draw_link(d, ucs_qa[0][0], ucs_qa[0][1]+18, ucs_rag[0][0], ucs_rag[0][1]-18, dashed=True)
    draw_include_label(d, ucs_qa[0][0]-80, ucs_qa[0][1]+18, ucs_rag[0][0]-80, ucs_rag[0][1]-18)

    # Include: QA agentique -> Pipeline RAG
    draw_link(d, ucs_qa[2][0]+50, ucs_qa[2][1]+18, ucs_rag[0][0]+50, ucs_rag[0][1]-18, dashed=True)

    out = r"C:\Users\RSCH\Downloads\fig_1_5_corrige.png"
    img.save(out, dpi=(300, 300))
    print(f"OK: {out}")


if __name__ == "__main__":
    gen()
