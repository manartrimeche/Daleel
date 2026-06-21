# -*- coding: utf-8 -*-
"""Generate 3 corrected UML use case diagrams for PFE report."""
from PIL import Image, ImageDraw, ImageFont
import math

# ═══════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════

def load_fonts():
    sizes = {}
    try:
        sizes["title"] = ImageFont.truetype("arialbd.ttf", 32)
        sizes["pkg"] = ImageFont.truetype("arialbd.ttf", 22)
        sizes["actor"] = ImageFont.truetype("arialbd.ttf", 20)
        sizes["uc"] = ImageFont.truetype("arial.ttf", 17)
        sizes["note"] = ImageFont.truetype("arial.ttf", 15)
        sizes["legend"] = ImageFont.truetype("arial.ttf", 16)
        sizes["legend_title"] = ImageFont.truetype("arialbd.ttf", 18)
    except:
        f = ImageFont.load_default()
        for k in ["title","pkg","actor","uc","note","legend","legend_title"]:
            sizes[k] = f
    return sizes

FONTS = load_fonts()

# Colors
BG = (255, 255, 255)
C_BORDER = (60, 60, 60)
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
C_NOTE_BG = (255, 255, 220)
C_NOTE_BORDER = (200, 200, 150)


def draw_actor(draw, x, y, name, font=None):
    if font is None:
        font = FONTS["actor"]
    r = 14
    draw.ellipse([x-r, y, x+r, y+2*r], outline=C_ACTOR, width=2)
    draw.line([x, y+2*r, x, y+2*r+40], fill=C_ACTOR, width=2)
    draw.line([x-22, y+2*r+16, x+22, y+2*r+16], fill=C_ACTOR, width=2)
    draw.line([x, y+2*r+40, x-20, y+2*r+65], fill=C_ACTOR, width=2)
    draw.line([x, y+2*r+40, x+20, y+2*r+65], fill=C_ACTOR, width=2)
    lines = name.split("\n")
    for i, line in enumerate(lines):
        tw = draw.textlength(line, font=font)
        draw.text((x - tw/2, y+2*r+70 + i*22), line, fill=C_ACTOR, font=font)
    return (x, y + r + 20)  # center of body


def draw_uc(draw, cx, cy, text, w=280, h=42):
    draw.ellipse([cx-w//2, cy-h//2, cx+w//2, cy+h//2], outline=C_UC_BORDER, width=2, fill=C_UC_FILL)
    lines = text.split("\n")
    line_h = 19
    total = len(lines) * line_h
    sy = cy - total//2
    for i, line in enumerate(lines):
        tw = draw.textlength(line, font=FONTS["uc"])
        draw.text((cx - tw/2, sy + i*line_h), line, fill=(20, 20, 20), font=FONTS["uc"])
    return (cx, cy)


def draw_package(draw, x, y, w, h, title):
    draw.rectangle([x, y, x+w, y+h], outline=C_PKG_BORDER, width=2, fill=C_PKG_BG)
    tw = draw.textlength(title, font=FONTS["pkg"]) + 20
    draw.rectangle([x, y, x+tw, y+30], outline=C_PKG_BORDER, width=2, fill=C_PKG_TAB)
    draw.text((x+10, y+4), title, fill=C_PKG_BORDER, font=FONTS["pkg"])


def draw_link(draw, x1, y1, x2, y2, dashed=False, color=None):
    c = color or C_LINE
    if dashed:
        length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if length == 0:
            return
        steps = max(int(length / 12), 1)
        for i in range(0, steps, 2):
            t1 = i / steps
            t2 = min((i+1) / steps, 1.0)
            draw.line([x1+(x2-x1)*t1, y1+(y2-y1)*t1, x1+(x2-x1)*t2, y1+(y2-y1)*t2], fill=c, width=1)
    else:
        draw.line([x1, y1, x2, y2], fill=c, width=1)


def draw_note(draw, x, y, lines):
    max_w = max(draw.textlength(l, font=FONTS["note"]) for l in lines)
    h = len(lines) * 18 + 12
    draw.rectangle([x, y, x+max_w+20, y+h], outline=C_NOTE_BORDER, width=1, fill=C_NOTE_BG)
    fold = 12
    draw.polygon([(x+max_w+20-fold, y), (x+max_w+20-fold, y+fold), (x+max_w+20, y+fold)], outline=C_NOTE_BORDER, fill=(245,245,210))
    for i, line in enumerate(lines):
        draw.text((x+10, y+6+i*18), line, fill=(60,60,60), font=FONTS["note"])


# ═══════════════════════════════════════════════════════════════
# FIGURE 1.3 — Diagramme général
# ═══════════════════════════════════════════════════════════════

def gen_fig13():
    W, H = 2200, 2000
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Title
    t = "Figure 1.3 — Diagramme de cas d'utilisation général de la plateforme Daleel"
    tw = d.textlength(t, font=FONTS["title"])
    d.text(((W-tw)//2, 18), t, fill=C_TITLE, font=FONTS["title"])

    # System box
    d.rectangle([340, 70, 1850, 1920], outline=C_SYS_BORDER, width=3, fill=C_SYS_BG)
    d.text((355, 78), "« système » Plateforme Daleel", fill=C_SYS_BORDER, font=FONTS["pkg"])

    # --- ACTORS ---
    AX_L = 140  # left actors X
    AX_R = 2050  # right actors X

    draw_actor(d, AX_L, 100, "Visiteur")
    draw_actor(d, AX_L, 420, "Membre")
    draw_actor(d, AX_L, 900, "Owner")
    draw_actor(d, AX_L, 1550, "Super Admin")

    # actor body centers (for links)
    a_visit = (AX_L, 148)
    a_member = (AX_L, 468)
    a_owner = (AX_L, 948)
    a_sadmin = (AX_L, 1598)

    # --- PACKAGES & USE CASES ---

    # Auth (top-left)
    px, py = 400, 115
    draw_package(d, px, py, 460, 230, "Authentification")
    ucs_auth = []
    labels_auth = ["S'inscrire", "Se connecter", "Réinitialiser mot de passe", "Vérifier email / OTP"]
    for i, lbl in enumerate(labels_auth):
        pos = draw_uc(d, px+230, py+55+i*48, lbl, w=260, h=38)
        ucs_auth.append(pos)

    # Legal RAG (top-right)
    px2, py2 = 920, 115
    draw_package(d, px2, py2, 520, 230, "Assistant juridique IA")
    ucs_rag = []
    labels_rag = ["Poser une question juridique", "Activer l'agent autonome", "Questionner un document", "Utiliser la voix"]
    for i, lbl in enumerate(labels_rag):
        pos = draw_uc(d, px2+260, py2+55+i*48, lbl, w=280, h=38)
        ucs_rag.append(pos)

    # Gestion documentaire
    px3, py3 = 400, 370
    draw_package(d, px3, py3, 460, 180, "Gestion documentaire")
    ucs_doc = []
    labels_doc = ["Téléverser un document", "Consulter les documents", "Extraire les exigences"]
    for i, lbl in enumerate(labels_doc):
        pos = draw_uc(d, px3+230, py3+50+i*46, lbl, w=270, h=36)
        ucs_doc.append(pos)

    # Gestion législative
    px4, py4 = 920, 370
    draw_package(d, px4, py4, 520, 230, "Gestion législative")
    ucs_leg = []
    labels_leg = ["Gérer les lois et articles", "Gérer les amendements", "Affecter textes à une entreprise"]
    for i, lbl in enumerate(labels_leg):
        pos = draw_uc(d, px4+260, py4+50+i*48, lbl, w=310, h=38)
        ucs_leg.append(pos)

    # Exigences réglementaires
    px5, py5 = 400, 575
    draw_package(d, px5, py5, 460, 180, "Exigences réglementaires")
    ucs_exig = []
    labels_exig = ["Consulter exigences applicables", "Évaluer l'applicabilité", "Gérer ses exigences"]
    for i, lbl in enumerate(labels_exig):
        pos = draw_uc(d, px5+230, py5+50+i*46, lbl, w=290, h=36)
        ucs_exig.append(pos)

    # Conformité & dossiers
    px6, py6 = 400, 780
    draw_package(d, px6, py6, 680, 320, "Conformité et dossiers de non-conformité")
    ucs_conf = []
    labels_conf = [
        "Créer un dossier de non-conformité",
        "Gérer constats et actions correctives",
        "Gérer les preuves et contrôles",
        "Lancer l'orchestration\nASK / CLARIFY / ACT / REVIEW",
        "Consulter tableau de bord BI",
        "Déléguer la conformité à un membre",
    ]
    for i, lbl in enumerate(labels_conf):
        h = 48 if "\n" in lbl else 38
        pos = draw_uc(d, px6+340, py6+50+i*46, lbl, w=370, h=h)
        ucs_conf.append(pos)

    # Administration
    px7, py7 = 400, 1130
    draw_package(d, px7, py7, 680, 280, "Administration de la plateforme")
    ucs_admin = []
    labels_admin = [
        "Gérer les organisations",
        "Gérer les utilisateurs",
        "Approuver / Rejeter les inscriptions",
        "Gérer adhésions et paiements",
        "Consulter statistiques agrégées",
    ]
    for i, lbl in enumerate(labels_admin):
        pos = draw_uc(d, px7+340, py7+50+i*46, lbl, w=340, h=38)
        ucs_admin.append(pos)

    # Notifications
    px8, py8 = 1200, 1430
    draw_package(d, px8, py8, 420, 140, "Notifications")
    ucs_notif = []
    labels_notif = ["Recevoir des notifications", "Notifier le Super Admin"]
    for i, lbl in enumerate(labels_notif):
        pos = draw_uc(d, px8+210, py8+45+i*46, lbl, w=280, h=38)
        ucs_notif.append(pos)

    # Gestion conversations
    px9, py9 = 1200, 1600
    draw_package(d, px9, py9, 420, 100, "Historique")
    uc_hist = draw_uc(d, px9+210, py9+55, "Gérer les conversations", w=280, h=38)

    # --- LINKS ---

    # Visiteur -> Auth (s'inscrire, se connecter)
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_auth[0][0]-130, ucs_auth[0][1])
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_auth[1][0]-130, ucs_auth[1][1])

    # Membre -> RAG
    for uc in ucs_rag:
        draw_link(d, a_member[0]+25, a_member[1], uc[0]-140, uc[1])
    # Membre -> Notifications (recevoir)
    draw_link(d, a_member[0]+25, a_member[1], ucs_notif[0][0]-140, ucs_notif[0][1])
    # Membre -> Historique
    draw_link(d, a_member[0]+25, a_member[1], uc_hist[0]-140, uc_hist[1])

    # Owner -> Documents
    for uc in ucs_doc:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-135, uc[1])
    # Owner -> Exigences
    for uc in ucs_exig:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-145, uc[1])
    # Owner -> Conformité (tout le bloc)
    for uc in ucs_conf:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-185, uc[1])
    # Owner -> RAG (aussi)
    draw_link(d, a_owner[0]+25, a_owner[1], ucs_rag[0][0]-140, ucs_rag[0][1])
    # Owner -> Notification (notifier SA)
    draw_link(d, a_owner[0]+25, a_owner[1], ucs_notif[1][0]-140, ucs_notif[1][1])

    # Super Admin -> Admin (tout)
    for uc in ucs_admin:
        draw_link(d, a_sadmin[0]+25, a_sadmin[1], uc[0]-170, uc[1])
    # Super Admin -> Gestion législative (tout)
    for uc in ucs_leg:
        draw_link(d, a_sadmin[0]+25, a_sadmin[1], uc[0]-155, uc[1])
    # Super Admin -> Consulter tableau de bord BI
    draw_link(d, a_sadmin[0]+25, a_sadmin[1], ucs_conf[4][0]-185, ucs_conf[4][1])
    # Super Admin -> Notifications
    draw_link(d, a_sadmin[0]+25, a_sadmin[1], ucs_notif[0][0]-140, ucs_notif[0][1])

    # Agent Système supprimé (perspective, pas implémenté)

    # --- NOTES ---
    # Notes supprimées

    out = r"C:\Users\RSCH\Downloads\fig_1_3_corrige.png"
    img.save(out, dpi=(300, 300))
    print(f"OK: {out}")


# ═══════════════════════════════════════════════════════════════
# FIGURE 1.4 — Auth et organisations
# ═══════════════════════════════════════════════════════════════

def gen_fig14():
    W, H = 2000, 1500
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    t = "Figure 1.4 — Cas d'utilisation : authentification, organisations et emails transactionnels"
    tw = d.textlength(t, font=FONTS["title"])
    d.text(((W-tw)//2, 15), t, fill=C_TITLE, font=FONTS["title"])

    # System box
    d.rectangle([320, 65, 1680, 1430], outline=C_SYS_BORDER, width=3, fill=C_SYS_BG)
    d.text((335, 73), "« système » Plateforme Daleel", fill=C_SYS_BORDER, font=FONTS["pkg"])

    AX_L = 130
    AX_R = 1850

    draw_actor(d, AX_L, 100, "Visiteur")
    draw_actor(d, AX_L, 440, "Owner")
    draw_actor(d, AX_L, 900, "Super Admin")
    draw_actor(d, AX_R, 500, "Serveur\nEmail")

    a_visit = (AX_L, 148)
    a_owner = (AX_L, 488)
    a_sadmin = (AX_L, 948)
    a_email = (AX_R, 548)

    # --- Auth ---
    draw_package(d, 380, 100, 520, 280, "Authentification")
    ucs_a = []
    for i, lbl in enumerate(["S'inscrire (compte + organisation)",
                              "Se connecter / Se déconnecter",
                              "Vérifier email par jeton",
                              "Vérifier téléphone par OTP",
                              "Réinitialiser mot de passe"]):
        pos = draw_uc(d, 640, 155+i*48, lbl, w=310, h=38)
        ucs_a.append(pos)

    # --- Gestion organisations (Super Admin) ---
    draw_package(d, 380, 410, 520, 330, "Gestion des organisations")
    ucs_org = []
    for i, lbl in enumerate(["Approuver / Rejeter une organisation",
                              "Gérer les utilisateurs",
                              "Renouveler un abonnement",
                              "Gérer adhésions et paiements",
                              "Donner accès aux membres",
                              "Consulter statistiques organisations"]):
        pos = draw_uc(d, 640, 465+i*46, lbl, w=320, h=36)
        ucs_org.append(pos)

    # --- Actions Owner sur son organisation ---
    draw_package(d, 380, 770, 520, 200, "Organisation (Owner)")
    ucs_ow = []
    for i, lbl in enumerate(["Modifier les informations\nde son organisation",
                              "Inviter des membres",
                              "Demander un renouvellement",
                              ]):
        h = 46 if "\n" in lbl else 36
        pos = draw_uc(d, 640, 825+i*48, lbl, w=310, h=h)
        ucs_ow.append(pos)

    # --- Notifications / Emails ---
    draw_package(d, 980, 100, 420, 230, "Emails transactionnels")
    ucs_em = []
    for i, lbl in enumerate(["Envoyer email de vérification",
                              "Envoyer email de réinitialisation",
                              "Notifier le Super Admin\n(modification Owner)",
                              "Notifier approbation / rejet"]):
        h = 44 if "\n" in lbl else 36
        pos = draw_uc(d, 1190, 155+i*50, lbl, w=300, h=h)
        ucs_em.append(pos)

    # --- LINKS ---
    # Visiteur -> Auth
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_a[0][0]-155, ucs_a[0][1])
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_a[2][0]-155, ucs_a[2][1])
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_a[3][0]-155, ucs_a[3][1])
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_a[4][0]-155, ucs_a[4][1])

    # Owner -> Auth (connexion)
    draw_link(d, a_owner[0]+25, a_owner[1], ucs_a[1][0]-155, ucs_a[1][1])
    # Owner -> Son organisation
    for uc in ucs_ow:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-155, uc[1])

    # Super Admin -> Org management
    for uc in ucs_org:
        draw_link(d, a_sadmin[0]+25, a_sadmin[1], uc[0]-160, uc[1])

    # Email server -> Emails
    for uc in ucs_em:
        draw_link(d, a_email[0]-25, a_email[1], uc[0]+150, uc[1])

    # include/extend links (dashed)
    # Auth -> Email (include)
    draw_link(d, ucs_a[0][0]+155, ucs_a[0][1], ucs_em[0][0]-150, ucs_em[0][1], dashed=True)
    draw_link(d, ucs_a[4][0]+155, ucs_a[4][1], ucs_em[1][0]-150, ucs_em[1][1], dashed=True)
    # Owner modif -> Notif SA
    draw_link(d, ucs_ow[0][0]+155, ucs_ow[0][1], ucs_em[2][0]-150, ucs_em[2][1], dashed=True)
    # SA approve -> Notif
    draw_link(d, ucs_org[0][0]+160, ucs_org[0][1], ucs_em[3][0]-150, ucs_em[3][1], dashed=True)

    # Notes
    # Notes supprimées

    out = r"C:\Users\RSCH\Downloads\fig_1_4_corrige.png"
    img.save(out, dpi=(300, 300))
    print(f"OK: {out}")


# ═══════════════════════════════════════════════════════════════
# FIGURE 1.6 — Conformité et dossiers
# ═══════════════════════════════════════════════════════════════

def gen_fig16():
    W, H = 2000, 1120
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    t = "Figure 1.6 — Cas d'utilisation : conformité et dossiers de non-conformité"
    tw = d.textlength(t, font=FONTS["title"])
    d.text(((W-tw)//2, 15), t, fill=C_TITLE, font=FONTS["title"])

    d.rectangle([320, 65, 1680, 1080], outline=C_SYS_BORDER, width=3, fill=C_SYS_BG)
    d.text((335, 73), "« système » Plateforme Daleel", fill=C_SYS_BORDER, font=FONTS["pkg"])

    AX_L = 130

    draw_actor(d, AX_L, 200, "Owner")
    draw_actor(d, AX_L, 750, "Membre\n(délégué)")

    a_owner = (AX_L, 248)
    a_member = (AX_L, 798)

    # --- Dossiers ---
    draw_package(d, 380, 100, 600, 360, "Gestion des dossiers de non-conformité")
    ucs_dos = []
    for i, lbl in enumerate([
        "Créer un dossier de non-conformité",
        "Ajouter des messages / contexte",
        "Joindre et analyser des documents",
        "Générer constats de non-conformité",
        "Créer des actions correctives",
        "Gérer les preuves",
        "Lancer l'orchestration\nASK / CLARIFY / ACT / REVIEW",
    ]):
        h = 46 if "\n" in lbl else 36
        pos = draw_uc(d, 680, 155+i*44, lbl, w=350, h=h)
        ucs_dos.append(pos)

    # --- Conformité globale ---
    draw_package(d, 380, 490, 600, 250, "Pilotage de la conformité")
    ucs_pilot = []
    for i, lbl in enumerate([
        "Évaluer l'applicabilité des exigences",
        "Calculer la posture de conformité",
        "Consulter le tableau de bord BI",
        "Gérer les contrôles internes",
        "Gérer le registre d'exceptions",
    ]):
        pos = draw_uc(d, 680, 545+i*44, lbl, w=350, h=36)
        ucs_pilot.append(pos)

    # --- Délégation ---
    draw_package(d, 380, 770, 600, 140, "Délégation")
    ucs_deleg = []
    for i, lbl in enumerate([
        "Déléguer un rôle conformité à un membre",
        "Révoquer la délégation",
    ]):
        pos = draw_uc(d, 680, 825+i*44, lbl, w=360, h=36)
        ucs_deleg.append(pos)

    # --- Roadmap & export ---
    draw_package(d, 380, 940, 600, 140, "Plan d'action et export")
    ucs_road = []
    for i, lbl in enumerate([
        "Générer un plan d'action priorisé (roadmap)",
        "Exporter les données de conformité",
    ]):
        pos = draw_uc(d, 680, 995+i*44, lbl, w=380, h=36)
        ucs_road.append(pos)

    # --- LINKS ---
    # Owner -> tout
    for uc in ucs_dos:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-175, uc[1])
    for uc in ucs_pilot:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-175, uc[1])
    for uc in ucs_deleg:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-180, uc[1])
    for uc in ucs_road:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-190, uc[1])

    # Membre délégué -> Dossiers + Pilotage (accès délégué)
    for uc in ucs_dos:
        draw_link(d, a_member[0]+25, a_member[1], uc[0]-175, uc[1], dashed=True)
    for uc in ucs_pilot:
        draw_link(d, a_member[0]+25, a_member[1], uc[0]-175, uc[1], dashed=True)
    for uc in ucs_road:
        draw_link(d, a_member[0]+25, a_member[1], uc[0]-190, uc[1], dashed=True)

    # Notes
    # Notes supprimées

    out = r"C:\Users\RSCH\Downloads\fig_1_6_corrige.png"
    img.save(out, dpi=(300, 300))
    print(f"OK: {out}")


# ═══════════════════════════════════════════════════════════════
# GENERATE ALL
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    gen_fig13()
    gen_fig14()
    gen_fig16()
    print("All 3 diagrams generated successfully.")
