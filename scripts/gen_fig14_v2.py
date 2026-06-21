# -*- coding: utf-8 -*-
"""Generate corrected Figure 1.4 — compact version."""
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
C_NOTE_BG = (255, 255, 220)
C_NOTE_BORDER = (200, 200, 150)


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
    return (x, y + r + 20)


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


def draw_note(d, x, y, lines):
    max_w = max(d.textlength(l, font=FONTS["note"]) for l in lines)
    h = len(lines) * 18 + 12
    d.rectangle([x, y, x+max_w+20, y+h], outline=C_NOTE_BORDER, width=1, fill=C_NOTE_BG)
    fold = 12
    d.polygon([(x+max_w+20-fold, y), (x+max_w+20-fold, y+fold), (x+max_w+20, y+fold)], outline=C_NOTE_BORDER, fill=(245,245,210))
    for i, line in enumerate(lines):
        d.text((x+10, y+6+i*18), line, fill=(60,60,60), font=FONTS["note"])


def draw_include_label(d, x1, y1, x2, y2):
    mx, my = (x1+x2)//2, (y1+y2)//2
    d.text((mx-30, my-16), "«include»", fill=(100,100,140), font=FONTS["note"])


def gen():
    W, H = 2000, 960
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    t = "Figure 1.4 — Cas d'utilisation : authentification, organisations et emails transactionnels"
    tw = d.textlength(t, font=FONTS["title"])
    d.text(((W-tw)//2, 12), t, fill=C_TITLE, font=FONTS["title"])

    # System box — compact
    d.rectangle([310, 58, 1690, 920], outline=C_SYS_BORDER, width=3, fill=C_SYS_BG)
    d.text((325, 64), "« système » Plateforme Daleel", fill=C_SYS_BORDER, font=FONTS["pkg"])

    AX_L = 125
    AX_R = 1860

    draw_actor(d, AX_L, 80, "Visiteur")
    draw_actor(d, AX_L, 380, "Owner")
    draw_actor(d, AX_L, 700, "Super Admin")
    draw_actor(d, AX_R, 300, "Serveur\nEmail")

    a_visit = (AX_L, 128)
    a_owner = (AX_L, 428)
    a_sadmin = (AX_L, 748)
    a_email = (AX_R, 348)

    # --- Auth ---
    draw_package(d, 370, 95, 500, 260, "Authentification")
    ucs_a = []
    labels = [
        "S'inscrire (compte + organisation)",
        "Se connecter / Se déconnecter",
        "Vérifier email par jeton",
        "Vérifier téléphone par OTP",
        "Réinitialiser mot de passe",
    ]
    for i, lbl in enumerate(labels):
        pos = draw_uc(d, 620, 148+i*44, lbl, w=300, h=36)
        ucs_a.append(pos)

    # --- Emails transactionnels ---
    draw_package(d, 950, 95, 430, 220, "Emails transactionnels")
    ucs_em = []
    labels_em = [
        "Envoyer email de vérification",
        "Envoyer email de réinitialisation",
        "Notifier le Super Admin\n(modification Owner)",
        "Notifier approbation / rejet",
    ]
    for i, lbl in enumerate(labels_em):
        h = 44 if "\n" in lbl else 36
        pos = draw_uc(d, 1165, 148+i*48, lbl, w=290, h=h)
        ucs_em.append(pos)

    # --- Gestion organisations (Super Admin) ---
    draw_package(d, 370, 380, 500, 300, "Gestion des organisations (Super Admin)")
    ucs_org = []
    labels_org = [
        "Approuver / Rejeter une organisation",
        "Gérer les utilisateurs",
        "Renouveler un abonnement",
        "Gérer adhésions et paiements",
        "Donner accès aux membres",
        "Consulter statistiques organisations",
    ]
    for i, lbl in enumerate(labels_org):
        pos = draw_uc(d, 620, 432+i*42, lbl, w=310, h=34)
        ucs_org.append(pos)

    # --- Actions Owner sur son org ---
    draw_package(d, 370, 705, 500, 170, "Mon organisation (Owner)")
    ucs_ow = []
    labels_ow = [
        "Modifier les informations\nde son organisation",
        "Inviter des membres",
        "Demander un renouvellement",
    ]
    for i, lbl in enumerate(labels_ow):
        h = 44 if "\n" in lbl else 34
        pos = draw_uc(d, 620, 752+i*42, lbl, w=310, h=h)
        ucs_ow.append(pos)

    # --- LINKS ---

    # Visiteur -> Auth
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_a[0][0]-150, ucs_a[0][1])
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_a[2][0]-150, ucs_a[2][1])
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_a[3][0]-150, ucs_a[3][1])
    draw_link(d, a_visit[0]+25, a_visit[1], ucs_a[4][0]-150, ucs_a[4][1])

    # Owner -> Auth (connexion)
    draw_link(d, a_owner[0]+25, a_owner[1], ucs_a[1][0]-150, ucs_a[1][1])
    # Owner -> Son organisation
    for uc in ucs_ow:
        draw_link(d, a_owner[0]+25, a_owner[1], uc[0]-155, uc[1])

    # Super Admin -> Org management
    for uc in ucs_org:
        draw_link(d, a_sadmin[0]+25, a_sadmin[1], uc[0]-155, uc[1])

    # Email server -> Emails
    for uc in ucs_em:
        draw_link(d, a_email[0]-25, a_email[1], uc[0]+145, uc[1])

    # Include links (dashed) Auth -> Email
    x1, y1 = ucs_a[0][0]+150, ucs_a[0][1]
    x2, y2 = ucs_em[0][0]-145, ucs_em[0][1]
    draw_link(d, x1, y1, x2, y2, dashed=True)
    draw_include_label(d, x1, y1, x2, y2)

    x1, y1 = ucs_a[4][0]+150, ucs_a[4][1]
    x2, y2 = ucs_em[1][0]-145, ucs_em[1][1]
    draw_link(d, x1, y1, x2, y2, dashed=True)
    draw_include_label(d, x1, y1, x2, y2)

    # Owner modif -> Notif SA
    x1, y1 = ucs_ow[0][0]+155, ucs_ow[0][1]
    x2, y2 = ucs_em[2][0]-145, ucs_em[2][1]
    draw_link(d, x1, y1, x2, y2, dashed=True)
    draw_include_label(d, x1, y1, x2, y2)

    # SA approve -> Notif
    x1, y1 = ucs_org[0][0]+155, ucs_org[0][1]
    x2, y2 = ucs_em[3][0]-145, ucs_em[3][1]
    draw_link(d, x1, y1, x2, y2, dashed=True)
    draw_include_label(d, x1, y1, x2, y2)

    # Notes supprimées

    out = r"C:\Users\RSCH\Downloads\fig_1_4_corrige.png"
    img.save(out, dpi=(300, 300))
    print(f"OK: {out}")


if __name__ == "__main__":
    gen()
