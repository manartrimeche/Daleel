# -*- coding: utf-8 -*-
"""Generate corrected Figure 1.3 — Diagramme de cas d'utilisation général."""
from PIL import Image, ImageDraw, ImageFont
import os, math

W, H = 2400, 1800
bg = (255, 255, 255)
img = Image.new("RGB", (W, H), bg)
draw = ImageDraw.Draw(img)

# Fonts
try:
    font_title = ImageFont.truetype("arial.ttf", 28)
    font_actor = ImageFont.truetype("arialbd.ttf", 22)
    font_uc = ImageFont.truetype("arial.ttf", 18)
    font_pkg = ImageFont.truetype("arialbd.ttf", 20)
    font_small = ImageFont.truetype("arial.ttf", 15)
except:
    font_title = ImageFont.load_default()
    font_actor = font_title
    font_uc = font_title
    font_pkg = font_title
    font_small = font_title

# Colors
C_BORDER = (60, 60, 60)
C_ACTOR = (50, 50, 50)
C_UC_FILL = (230, 245, 255)
C_UC_BORDER = (70, 130, 180)
C_PKG_BORDER = (100, 100, 100)
C_LINE = (100, 100, 100)
C_SYSTEM = (245, 245, 250)
C_TITLE = (30, 30, 80)

# Title
draw.text((W//2 - 350, 15), "Diagramme de cas d'utilisation général — Daleel", fill=C_TITLE, font=font_title)

# System boundary
SX, SY, SW, SH = 380, 60, 1650, 1700
draw.rectangle([SX, SY, SX+SW, SY+SH], outline=C_PKG_BORDER, width=2, fill=C_SYSTEM)
draw.text((SX + 10, SY + 5), "« système » Daleel", fill=C_PKG_BORDER, font=font_pkg)

# --- Draw actor ---
def draw_actor(x, y, name):
    # Head
    draw.ellipse([x-12, y, x+12, y+24], outline=C_ACTOR, width=2)
    # Body
    draw.line([x, y+24, x, y+60], fill=C_ACTOR, width=2)
    # Arms
    draw.line([x-20, y+38, x+20, y+38], fill=C_ACTOR, width=2)
    # Legs
    draw.line([x, y+60, x-18, y+85], fill=C_ACTOR, width=2)
    draw.line([x, y+60, x+18, y+85], fill=C_ACTOR, width=2)
    # Name
    tw = draw.textlength(name, font=font_actor)
    draw.text((x - tw//2, y+90), name, fill=C_ACTOR, font=font_actor)

# --- Draw use case ellipse ---
def draw_uc(cx, cy, text, w=260, h=48):
    draw.ellipse([cx-w//2, cy-h//2, cx+w//2, cy+h//2], outline=C_UC_BORDER, width=2, fill=C_UC_FILL)
    lines = text.split("\n")
    total_h = len(lines) * 20
    start_y = cy - total_h//2
    for i, line in enumerate(lines):
        tw = draw.textlength(line, font=font_uc)
        draw.text((cx - tw//2, start_y + i*20), line, fill=(30, 30, 30), font=font_uc)
    return (cx, cy)

# --- Draw line ---
def draw_link(x1, y1, x2, y2, dashed=False):
    if dashed:
        # dashed line
        length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        dash_len = 10
        steps = int(length / dash_len)
        for i in range(0, steps, 2):
            t1 = i / steps
            t2 = min((i+1) / steps, 1.0)
            draw.line([
                x1 + (x2-x1)*t1, y1 + (y2-y1)*t1,
                x1 + (x2-x1)*t2, y1 + (y2-y1)*t2
            ], fill=C_LINE, width=1)
    else:
        draw.line([x1, y1, x2, y2], fill=C_LINE, width=1)

# --- Draw package ---
def draw_package(x, y, w, h, title):
    draw.rectangle([x, y, x+w, y+h], outline=C_PKG_BORDER, width=2)
    tab_w = draw.textlength(title, font=font_pkg) + 16
    draw.rectangle([x, y, x+tab_w, y+28], outline=C_PKG_BORDER, width=2, fill=(235, 235, 245))
    draw.text((x+8, y+4), title, fill=C_PKG_BORDER, font=font_pkg)

# ═══════ ACTORS ═══════
actors = {
    "Visiteur":    (120, 200),
    "Membre":      (120, 600),
    "Owner":       (120, 1050),
    "Super Admin": (120, 1500),
    "Agent\nSystème": (2280, 400),
}

for name, (ax, ay) in actors.items():
    real_name = name.replace("\n", " ")
    draw_actor(ax, ay, real_name)

# ═══════ PACKAGES & USE CASES ═══════

# --- Package: Authentification ---
draw_package(420, 90, 540, 280, "Authentification")
uc_auth = [
    (690, 140, "S'inscrire"),
    (690, 190, "Se connecter"),
    (690, 240, "Réinitialiser mot de passe"),
    (690, 290, "Vérifier email / OTP"),
    (690, 340, "Se déconnecter"),
]
for cx, cy, t in uc_auth:
    draw_uc(cx, cy, t, w=280, h=38)

# --- Package: Assistant juridique IA ---
draw_package(1020, 90, 580, 280, "Assistant juridique IA")
uc_rag = [
    (1310, 140, "Poser une question juridique"),
    (1310, 190, "Activer l'agent autonome"),
    (1310, 240, "Questionner un document"),
    (1310, 290, "Utiliser la voix"),
    (1310, 340, "Gérer les conversations"),
]
for cx, cy, t in uc_rag:
    draw_uc(cx, cy, t, w=290, h=38)

# --- Package: Gestion documentaire ---
draw_package(420, 400, 540, 200, "Gestion documentaire")
uc_doc = [
    (690, 450, "Téléverser un document"),
    (690, 500, "Consulter les documents"),
    (690, 550, "Extraire les exigences"),
]
for cx, cy, t in uc_doc:
    draw_uc(cx, cy, t, w=280, h=38)

# --- Package: Gestion législative ---
draw_package(1020, 400, 580, 250, "Gestion législative")
uc_leg = [
    (1310, 450, "Gérer les lois et articles"),
    (1310, 500, "Gérer les amendements"),
    (1310, 550, "Veille juridique automatique"),
    (1310, 600, "Affecter textes à une entreprise"),
]
for cx, cy, t in uc_leg:
    draw_uc(cx, cy, t, w=310, h=38)

# --- Package: Exigences réglementaires ---
draw_package(420, 640, 540, 200, "Exigences réglementaires")
uc_exig = [
    (690, 690, "Consulter les exigences applicables"),
    (690, 740, "Évaluer l'applicabilité"),
    (690, 790, "Gérer les exigences (Owner)"),
]
for cx, cy, t in uc_exig:
    draw_uc(cx, cy, t, w=320, h=38)

# --- Package: Conformité & dossiers ---
draw_package(420, 870, 740, 340, "Conformité et dossiers de non-conformité")
uc_conf = [
    (750, 920, "Créer un dossier de non-conformité"),
    (750, 970, "Gérer constats et actions correctives"),
    (750, 1020, "Gérer les preuves"),
    (750, 1070, "Lancer l'orchestration ASK/CLARIFY/ACT/REVIEW"),
    (750, 1120, "Consulter tableau de bord BI"),
    (750, 1170, "Déléguer la conformité à un membre"),
]
for cx, cy, t in uc_conf:
    draw_uc(cx, cy, t, w=370, h=38)

# --- Package: Administration plateforme ---
draw_package(420, 1240, 740, 290, "Administration de la plateforme")
uc_admin = [
    (750, 1290, "Gérer les organisations"),
    (750, 1340, "Gérer les utilisateurs"),
    (750, 1390, "Approuver/Rejeter les inscriptions"),
    (750, 1440, "Gérer adhésions et paiements"),
    (750, 1490, "Consulter statistiques agrégées"),
]
for cx, cy, t in uc_admin:
    draw_uc(cx, cy, t, w=340, h=38)

# --- Package: Notifications ---
draw_package(1250, 680, 420, 150, "Notifications")
uc_notif = [
    (1460, 730, "Recevoir des notifications"),
    (1460, 780, "Notifier le Super Admin"),
]
for cx, cy, t in uc_notif:
    draw_uc(cx, cy, t, w=280, h=38)

# ═══════ LINKS ═══════

# Visiteur -> Auth
for cx, cy, t in uc_auth[:2]:  # s'inscrire, se connecter
    draw_link(145, 250, cx - 130, cy)

# Membre -> Auth (se connecter, déconnecter)
draw_link(145, 650, uc_auth[1][0]-130, uc_auth[1][1])
# Membre -> RAG
for cx, cy, t in uc_rag[:4]:
    draw_link(145, 650, cx - 140, cy)
# Membre -> Notifications
draw_link(145, 650, 1460-130, 730)

# Owner -> Documents
for cx, cy, t in uc_doc:
    draw_link(145, 1100, cx - 130, cy)
# Owner -> Exigences
for cx, cy, t in uc_exig:
    draw_link(145, 1100, cx - 150, cy)
# Owner -> Conformité (tout)
for cx, cy, t in uc_conf:
    draw_link(145, 1100, cx - 180, cy)
# Owner -> RAG (aussi accès)
draw_link(145, 1100, uc_rag[0][0]-140, uc_rag[0][1])
# Owner -> Notifications
draw_link(145, 1100, 1460-130, 730)
draw_link(145, 1100, 1460-130, 780)

# Super Admin -> Admin (tout)
for cx, cy, t in uc_admin:
    draw_link(145, 1550, cx - 160, cy)
# Super Admin -> Gestion législative
for cx, cy, t in uc_leg[:2]:
    draw_link(145, 1550, cx - 150, cy)
# Super Admin -> Consulter tableau de bord BI
draw_link(145, 1550, uc_conf[4][0]-180, uc_conf[4][1])
# Super Admin -> Consulter stats agrégées
draw_link(145, 1550, uc_admin[4][0]-160, uc_admin[4][1])

# Agent Système -> Veille juridique automatique
draw_link(2260, 450, uc_leg[2][0]+150, uc_leg[2][1])

# ═══════ LEGEND ═══════
lx, ly = 1650, 1550
draw.rectangle([lx, ly, lx+380, ly+180], outline=C_PKG_BORDER, width=1, fill=(252,252,255))
draw.text((lx+10, ly+5), "Légende des rôles", fill=C_TITLE, font=font_pkg)
legend = [
    "Visiteur : consulte, s'inscrit",
    "Membre : interroge le système",
    "Owner : gère sa conformité + exigences",
    "Super Admin : administre la plateforme",
    "Agent Système : veille juridique auto",
]
for i, txt in enumerate(legend):
    draw.text((lx+15, ly+35 + i*28), txt, fill=C_ACTOR, font=font_small)

out = r"C:\Users\RSCH\Downloads\fig_1_3_corrige.png"
img.save(out, dpi=(300, 300))
print(f"Saved: {out}")
