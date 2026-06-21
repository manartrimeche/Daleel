# -*- coding: utf-8 -*-
"""Generate merged Figure 1.3+1.4 — Diagramme de cas d'utilisation général (v2)."""
from PIL import Image, ImageDraw, ImageFont
import math

def load_fonts():
    sizes = {}
    try:
        sizes["title"] = ImageFont.truetype("arialbd.ttf", 28)
        sizes["pkg"] = ImageFont.truetype("arialbd.ttf", 20)
        sizes["actor"] = ImageFont.truetype("arialbd.ttf", 18)
        sizes["uc"] = ImageFont.truetype("arial.ttf", 15)
        sizes["note"] = ImageFont.truetype("arial.ttf", 13)
    except:
        f = ImageFont.load_default()
        for k in sizes:
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
    r = 12
    d.ellipse([x-r, y, x+r, y+2*r], outline=C_ACTOR, width=2)
    d.line([x, y+2*r, x, y+2*r+35], fill=C_ACTOR, width=2)
    d.line([x-18, y+2*r+14, x+18, y+2*r+14], fill=C_ACTOR, width=2)
    d.line([x, y+2*r+35, x-16, y+2*r+55], fill=C_ACTOR, width=2)
    d.line([x, y+2*r+35, x+16, y+2*r+55], fill=C_ACTOR, width=2)
    lines = name.split("\n")
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=FONTS["actor"])
        d.text((x - tw/2, y+2*r+60 + i*20), line, fill=C_ACTOR, font=FONTS["actor"])


def draw_uc(d, cx, cy, text, w=260, h=36):
    d.ellipse([cx-w//2, cy-h//2, cx+w//2, cy+h//2], outline=C_UC_BORDER, width=2, fill=C_UC_FILL)
    lines = text.split("\n")
    line_h = 17
    total = len(lines) * line_h
    sy = cy - total//2
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=FONTS["uc"])
        d.text((cx - tw/2, sy + i*line_h), line, fill=(20, 20, 20), font=FONTS["uc"])
    return (cx, cy)


def draw_package(d, x, y, w, h, title):
    d.rectangle([x, y, x+w, y+h], outline=C_PKG_BORDER, width=2, fill=C_PKG_BG)
    tw = d.textlength(title, font=FONTS["pkg"]) + 16
    d.rectangle([x, y, x+tw, y+26], outline=C_PKG_BORDER, width=2, fill=C_PKG_TAB)
    d.text((x+8, y+3), title, fill=C_PKG_BORDER, font=FONTS["pkg"])


def draw_link(d, x1, y1, x2, y2, dashed=False):
    c = C_LINE
    if dashed:
        length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if length == 0: return
        steps = max(int(length / 10), 1)
        for i in range(0, steps, 2):
            t1 = i / steps
            t2 = min((i+1) / steps, 1.0)
            d.line([x1+(x2-x1)*t1, y1+(y2-y1)*t1, x1+(x2-x1)*t2, y1+(y2-y1)*t2], fill=c, width=1)
    else:
        d.line([x1, y1, x2, y2], fill=c, width=1)


def gen():
    W, H = 2200, 2100
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    t = "Figure 1.3 — Diagramme de cas d'utilisation général de la plateforme Daleel"
    tw = d.textlength(t, font=FONTS["title"])
    d.text(((W-tw)//2, 12), t, fill=C_TITLE, font=FONTS["title"])

    # System box
    SX, SY = 300, 55
    SW, SH = 1600, 2010
    d.rectangle([SX, SY, SX+SW, SY+SH], outline=C_SYS_BORDER, width=3, fill=C_SYS_BG)
    d.text((SX+10, SY+5), "« système » Plateforme Daleel", fill=C_SYS_BORDER, font=FONTS["pkg"])

    AX = 120  # actors X position

    # ═══════════════════════════════════════════
    # ACTEUR 1 : VISITEUR (top)
    # ═══════════════════════════════════════════
    draw_actor(d, AX, 90, "Visiteur")
    a_visit = (AX, 130)

    # Package: Inscription
    px, py = 360, 85
    draw_package(d, px, py, 480, 180, "Inscription")
    ucs_visit = []
    labels = [
        "S'inscrire (compte + organisation)",
        "Vérifier email par jeton",
        "Vérifier téléphone par OTP",
        "Consulter en mode gratuit",
    ]
    for i, lbl in enumerate(labels):
        pos = draw_uc(d, px+240, py+42+i*37, lbl, w=280, h=30)
        ucs_visit.append(pos)

    # Links visiteur
    for uc in ucs_visit:
        draw_link(d, a_visit[0]+20, a_visit[1], uc[0]-140, uc[1])

    # ═══════════════════════════════════════════
    # ACTEUR 2 : MEMBRE
    # ═══════════════════════════════════════════
    draw_actor(d, AX, 400, "Membre")
    a_member = (AX, 440)

    # Package: Authentification
    px2, py2 = 360, 295
    draw_package(d, px2, py2, 480, 110, "Authentification")
    ucs_auth = []
    labels_auth = [
        "Se connecter / Se déconnecter",
        "Réinitialiser son mot de passe",
    ]
    for i, lbl in enumerate(labels_auth):
        pos = draw_uc(d, px2+240, py2+42+i*37, lbl, w=270, h=30)
        ucs_auth.append(pos)

    # Package: Consultation juridique
    px3, py3 = 360, 430
    draw_package(d, px3, py3, 480, 185, "Consultation juridique")
    ucs_consult = []
    labels_consult = [
        "Poser une question juridique",
        "Interroger un document téléversé",
        "Utiliser la voix",
        "Activer l'agent autonome (ReAct)",
    ]
    for i, lbl in enumerate(labels_consult):
        pos = draw_uc(d, px3+240, py3+42+i*37, lbl, w=290, h=30)
        ucs_consult.append(pos)

    # Package: Gestion de conformité (Membre)
    px4, py4 = 360, 640
    draw_package(d, px4, py4, 480, 220, "Gestion de conformité (Membre / Owner)")
    ucs_conf_m = []
    labels_conf_m = [
        "Consulter les exigences applicables",
        "Vérifier la conformité\n(conforme / non conforme)",
        "Fournir les dispositions et preuves",
        "Proposer des actions correctives",
        "Gérer un dossier de non-conformité",
    ]
    for i, lbl in enumerate(labels_conf_m):
        h = 38 if "\n" in lbl else 30
        pos = draw_uc(d, px4+240, py4+40+i*37, lbl, w=300, h=h)
        ucs_conf_m.append(pos)

    # Package: Gestion documentaire
    px4b, py4b = 900, 430
    draw_package(d, px4b, py4b, 450, 110, "Gestion documentaire")
    ucs_doc = []
    labels_doc = [
        "Téléverser un document",
        "Consulter les documents",
    ]
    for i, lbl in enumerate(labels_doc):
        pos = draw_uc(d, px4b+225, py4b+42+i*37, lbl, w=260, h=30)
        ucs_doc.append(pos)

    # Links membre
    for uc in ucs_auth:
        draw_link(d, a_member[0]+20, a_member[1], uc[0]-135, uc[1])
    for uc in ucs_consult:
        draw_link(d, a_member[0]+20, a_member[1], uc[0]-145, uc[1])
    for uc in ucs_conf_m:
        draw_link(d, a_member[0]+20, a_member[1], uc[0]-150, uc[1], dashed=True)
    for uc in ucs_doc:
        draw_link(d, a_member[0]+20, a_member[1], uc[0]-130, uc[1])

    # ═══════════════════════════════════════════
    # ACTEUR 3 : OWNER
    # ═══════════════════════════════════════════
    draw_actor(d, AX, 1000, "Owner")
    a_owner = (AX, 1040)

    # Package: Gestion des membres
    px5, py5 = 360, 900
    draw_package(d, px5, py5, 480, 185, "Gestion des membres (Owner)")
    ucs_membres = []
    labels_membres = [
        "Créer un membre et l'inviter",
        "Faire valider l'inscription\npar le Super Admin",
        "Déléguer la conformité à un membre",
        "Déléguer d'autres tâches\n(contrats, documents)",
    ]
    for i, lbl in enumerate(labels_membres):
        h = 38 if "\n" in lbl else 30
        pos = draw_uc(d, px5+240, py5+40+i*38, lbl, w=300, h=h)
        ucs_membres.append(pos)

    # Package: Pilotage conformité (Owner)
    px6, py6 = 360, 1110
    draw_package(d, px6, py6, 480, 150, "Pilotage de conformité (Owner)")
    ucs_pilot = []
    labels_pilot = [
        "Approuver les actions correctives",
        "Surveiller la clôture des actions",
        "Consulter le tableau de bord BI",
    ]
    for i, lbl in enumerate(labels_pilot):
        pos = draw_uc(d, px6+240, py6+42+i*37, lbl, w=300, h=30)
        ucs_pilot.append(pos)

    # Package: Orchestration
    px6b, py6b = 900, 900
    draw_package(d, px6b, py6b, 450, 110, "Orchestration de cas")
    ucs_orch = []
    labels_orch = [
        "Lancer l'orchestration\nASK / CLARIFY / ACT / REVIEW",
        "Consulter le statut d'orchestration",
    ]
    for i, lbl in enumerate(labels_orch):
        h = 38 if "\n" in lbl else 30
        pos = draw_uc(d, px6b+225, py6b+38+i*40, lbl, w=310, h=h)
        ucs_orch.append(pos)

    # Links Owner
    for uc in ucs_conf_m:
        draw_link(d, a_owner[0]+20, a_owner[1], uc[0]-150, uc[1])
    for uc in ucs_membres:
        draw_link(d, a_owner[0]+20, a_owner[1], uc[0]-150, uc[1])
    for uc in ucs_pilot:
        draw_link(d, a_owner[0]+20, a_owner[1], uc[0]-150, uc[1])
    for uc in ucs_orch:
        draw_link(d, a_owner[0]+20, a_owner[1], uc[0]-155, uc[1])
    # Owner also accesses consultation
    draw_link(d, a_owner[0]+20, a_owner[1], ucs_consult[0][0]-145, ucs_consult[0][1])

    # ═══════════════════════════════════════════
    # ACTEUR 4 : SUPER ADMIN
    # ═══════════════════════════════════════════
    draw_actor(d, AX, 1500, "Super Admin")
    a_sadmin = (AX, 1540)

    # Package: Veille réglementaire et légale
    px7, py7 = 360, 1300
    draw_package(d, px7, py7, 480, 115, "Veille réglementaire et légale")
    ucs_veille = []
    labels_veille = [
        "Chercher et mettre à jour les textes",
        "Classer les textes par catégorie / type",
    ]
    for i, lbl in enumerate(labels_veille):
        pos = draw_uc(d, px7+240, py7+42+i*37, lbl, w=310, h=30)
        ucs_veille.append(pos)

    # Package: Gestion des exigences
    px8, py8 = 360, 1440
    draw_package(d, px8, py8, 480, 115, "Gestion des exigences (Super Admin)")
    ucs_exig = []
    labels_exig = [
        "Extraire / mettre à jour les exigences",
        "Affecter les mises à jour aux organisations",
    ]
    for i, lbl in enumerate(labels_exig):
        pos = draw_uc(d, px8+240, py8+42+i*37, lbl, w=310, h=30)
        ucs_exig.append(pos)

    # Package: Gestion utilisateurs
    px9, py9 = 360, 1580
    draw_package(d, px9, py9, 480, 150, "Gestion des utilisateurs et organisations")
    ucs_users = []
    labels_users = [
        "Gérer les organisations",
        "Gérer les utilisateurs",
        "Gérer les adhésions et paiements",
    ]
    for i, lbl in enumerate(labels_users):
        pos = draw_uc(d, px9+240, py9+42+i*37, lbl, w=290, h=30)
        ucs_users.append(pos)

    # Package: Tableau de bord SA
    px10, py10 = 360, 1755
    draw_package(d, px10, py10, 480, 75, "Supervision plateforme")
    uc_dash_sa = draw_uc(d, px10+240, py10+42, "Consulter le tableau de bord global", w=310, h=30)

    # Package: Notifications (right side)
    px11, py11 = 900, 1300
    draw_package(d, px11, py11, 450, 110, "Notifications")
    ucs_notif = []
    labels_notif = [
        "Recevoir des notifications",
        "Notifier le Super Admin",
    ]
    for i, lbl in enumerate(labels_notif):
        pos = draw_uc(d, px11+225, py11+42+i*37, lbl, w=260, h=30)
        ucs_notif.append(pos)

    # Package: Emails transactionnels (right side)
    px12, py12 = 900, 1440
    draw_package(d, px12, py12, 450, 150, "Emails transactionnels")
    ucs_email = []
    labels_email = [
        "Envoyer email de vérification",
        "Envoyer email de réinitialisation",
        "Notifier approbation / rejet",
    ]
    for i, lbl in enumerate(labels_email):
        pos = draw_uc(d, px12+225, py12+42+i*37, lbl, w=280, h=30)
        ucs_email.append(pos)

    # Package: Historique (right side, middle)
    px13, py13 = 900, 640
    draw_package(d, px13, py13, 450, 110, "Historique et feedback")
    ucs_hist = []
    labels_hist = [
        "Consulter l'historique des conversations",
        "Donner un feedback sur une réponse",
    ]
    for i, lbl in enumerate(labels_hist):
        pos = draw_uc(d, px13+225, py13+42+i*37, lbl, w=300, h=30)
        ucs_hist.append(pos)

    # Links Super Admin
    for uc in ucs_veille:
        draw_link(d, a_sadmin[0]+20, a_sadmin[1], uc[0]-155, uc[1])
    for uc in ucs_exig:
        draw_link(d, a_sadmin[0]+20, a_sadmin[1], uc[0]-155, uc[1])
    for uc in ucs_users:
        draw_link(d, a_sadmin[0]+20, a_sadmin[1], uc[0]-145, uc[1])
    draw_link(d, a_sadmin[0]+20, a_sadmin[1], uc_dash_sa[0]-155, uc_dash_sa[1])
    draw_link(d, a_sadmin[0]+20, a_sadmin[1], ucs_notif[0][0]-130, ucs_notif[0][1])

    # Membre -> Historique
    for uc in ucs_hist:
        draw_link(d, a_member[0]+20, a_member[1], uc[0]-150, uc[1])
    # Owner -> Historique
    draw_link(d, a_owner[0]+20, a_owner[1], ucs_hist[0][0]-150, ucs_hist[0][1])
    # Owner -> Notifications
    draw_link(d, a_owner[0]+20, a_owner[1], ucs_notif[1][0]-130, ucs_notif[1][1])

    # Membre conformité = dashed (accès par délégation du Owner)
    # Already done above with dashed=True

    out = r"C:\Users\RSCH\Downloads\fig_1_3_merged.png"
    img.save(out, dpi=(300, 300))
    print(f"OK: {out}")


if __name__ == "__main__":
    gen()
