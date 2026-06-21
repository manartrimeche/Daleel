# -*- coding: utf-8 -*-
"""Generate corrected Figures 3.4 and 3.5 — MCD without FK, with verb associations."""
from PIL import Image, ImageDraw, ImageFont
import math

def load_fonts():
    sizes = {}
    try:
        sizes["title"] = ImageFont.truetype("arialbd.ttf", 28)
        sizes["class_name"] = ImageFont.truetype("arialbd.ttf", 18)
        sizes["attr"] = ImageFont.truetype("arial.ttf", 14)
        sizes["assoc"] = ImageFont.truetype("ariali.ttf", 15)
        sizes["card"] = ImageFont.truetype("arialbd.ttf", 14)
        sizes["note"] = ImageFont.truetype("arial.ttf", 13)
    except:
        f = ImageFont.load_default()
        for k in sizes:
            sizes[k] = f
    return sizes

FONTS = load_fonts()

BG = (255, 255, 255)
C_CLASS_HEAD = (50, 80, 140)
C_CLASS_HEAD_TEXT = (255, 255, 255)
C_CLASS_BODY = (245, 248, 255)
C_CLASS_BORDER = (70, 100, 160)
C_ASSOC_DIAMOND = (255, 240, 210)
C_ASSOC_BORDER = (180, 140, 60)
C_ASSOC_TEXT = (120, 80, 20)
C_LINE = (100, 100, 120)
C_TITLE = (20, 20, 70)
C_CARD = (180, 60, 60)


def draw_class(d, x, y, name, attributes, w=200):
    """Draw a UML class box (MCD entity). Returns (cx, cy, w, h)."""
    head_h = 30
    attr_h = len(attributes) * 20 + 10
    h = head_h + attr_h

    # Header
    d.rectangle([x, y, x+w, y+head_h], outline=C_CLASS_BORDER, width=2, fill=C_CLASS_HEAD)
    tw = d.textlength(name, font=FONTS["class_name"])
    d.text((x + (w-tw)//2, y+5), name, fill=C_CLASS_HEAD_TEXT, font=FONTS["class_name"])

    # Body
    d.rectangle([x, y+head_h, x+w, y+h], outline=C_CLASS_BORDER, width=2, fill=C_CLASS_BODY)
    for i, attr in enumerate(attributes):
        prefix = ""
        if i == 0:
            prefix = "# "  # primary key indicator
        d.text((x+10, y+head_h+5+i*20), prefix + attr, fill=(40, 40, 40), font=FONTS["attr"])

    cx = x + w // 2
    cy = y + h // 2
    return (cx, cy, w, h, x, y)


def draw_diamond(d, cx, cy, text, w=140, h=50):
    """Draw a diamond (MCD association)."""
    points = [(cx, cy-h//2), (cx+w//2, cy), (cx, cy+h//2), (cx-w//2, cy)]
    d.polygon(points, outline=C_ASSOC_BORDER, fill=C_ASSOC_DIAMOND)
    tw = d.textlength(text, font=FONTS["assoc"])
    d.text((cx - tw//2, cy-8), text, fill=C_ASSOC_TEXT, font=FONTS["assoc"])
    return (cx, cy)


def draw_line(d, x1, y1, x2, y2):
    d.line([x1, y1, x2, y2], fill=C_LINE, width=2)


def draw_card(d, x, y, text):
    """Draw cardinality label."""
    d.text((x, y), text, fill=C_CARD, font=FONTS["card"])


# ═══════════════════════════════════════════════════════════════
# FIGURE 3.4 — MCD hiérarchie juridique
# ═══════════════════════════════════════════════════════════════

def gen_fig34():
    W, H = 1800, 1100
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    t = "Figure 3.4 — Modèle conceptuel de la hiérarchie juridique"
    tw = d.textlength(t, font=FONTS["title"])
    d.text(((W-tw)//2, 15), t, fill=C_TITLE, font=FONTS["title"])

    # ── Classes ──

    loi = draw_class(d, 50, 80, "Loi", [
        "id", "code", "nom_complet",
        "date_promulgation", "langue",
        "statut", "description",
    ], w=210)

    article = draw_class(d, 50, 420, "Article", [
        "id", "article_key",
        "article_number",
        "article_heading",
        "hierarchy",
    ], w=210)

    version = draw_class(d, 450, 420, "ArticleVersion", [
        "id", "version_number",
        "text", "status",
        "language", "is_current",
        "is_base_version",
        "effective_date",
    ], w=230)

    exigence = draw_class(d, 900, 420, "Exigence", [
        "id", "text",
        "exigence_type",
        "page_number",
        "confidence",
    ], w=210)

    action = draw_class(d, 900, 80, "Action", [
        "id", "modalite",
        "action_precise",
        "conditions", "preuve",
        "confidence",
    ], w=210)

    criticality = draw_class(d, 1350, 80, "ActionCriticality", [
        "id", "level", "score",
        "factors", "computed_at",
        "computed_by",
    ], w=220)

    amendment = draw_class(d, 450, 780, "AmendmentOperation", [
        "id", "operation_type",
        "description",
        "effective_date",
    ], w=230)

    dependency = draw_class(d, 1350, 420, "ActionDependency", [
        "id", "dependency_type",
        "reason",
    ], w=220)

    # ── Associations (diamonds with verbs) ──

    # Loi --contenir--> Article
    dcx, dcy = 155, 340
    draw_diamond(d, dcx, dcy, "contenir", w=130, h=44)
    draw_line(d, loi[0], loi[1]+loi[3]//2, dcx, dcy-22)
    draw_line(d, dcx, dcy+22, article[0], article[1]-article[3]//2)
    draw_card(d, dcx+70, dcy-35, "1,1")
    draw_card(d, dcx+70, dcy+20, "1,N")

    # Article --posséder--> ArticleVersion
    dcx2, dcy2 = 340, 500
    draw_diamond(d, dcx2, dcy2, "posséder", w=130, h=44)
    draw_line(d, article[4]+article[2], article[1], dcx2-65, dcy2)
    draw_line(d, dcx2+65, dcy2, version[4], version[1])
    draw_card(d, dcx2-65, dcy2-30, "1,1")
    draw_card(d, dcx2+45, dcy2-30, "1,N")

    # ArticleVersion --engendrer--> Exigence
    dcx3, dcy3 = 770, 500
    draw_diamond(d, dcx3, dcy3, "engendrer", w=140, h=44)
    draw_line(d, version[4]+version[2], version[1], dcx3-70, dcy3)
    draw_line(d, dcx3+70, dcy3, exigence[4], exigence[1])
    draw_card(d, dcx3-70, dcy3-30, "1,1")
    draw_card(d, dcx3+50, dcy3-30, "0,N")

    # Exigence --nécessiter--> Action
    dcx4, dcy4 = 1005, 330
    draw_diamond(d, dcx4, dcy4, "nécessiter", w=140, h=44)
    draw_line(d, exigence[0], exigence[1]-exigence[3]//2, dcx4, dcy4+22)
    draw_line(d, dcx4, dcy4-22, action[0], action[1]+action[3]//2)
    draw_card(d, dcx4+75, dcy4+10, "1,1")
    draw_card(d, dcx4+75, dcy4-30, "0,N")

    # Action --recevoir--> ActionCriticality
    dcx5, dcy5 = 1230, 180
    draw_diamond(d, dcx5, dcy5, "recevoir", w=130, h=44)
    draw_line(d, action[4]+action[2], action[1], dcx5-65, dcy5)
    draw_line(d, dcx5+65, dcy5, criticality[4], criticality[1])
    draw_card(d, dcx5-65, dcy5-30, "1,1")
    draw_card(d, dcx5+45, dcy5-30, "0,1")

    # Action --dépendre de--> Action (via ActionDependency)
    dcx6, dcy6 = 1230, 500
    draw_diamond(d, dcx6, dcy6, "dépendre de", w=140, h=44)
    draw_line(d, action[0]+action[2]//2, action[1]+action[3]//2, dcx6, dcy6-22)
    draw_line(d, dcx6+70, dcy6, dependency[4], dependency[1])
    draw_card(d, dcx6-20, dcy6-40, "0,N")
    draw_card(d, dcx6+50, dcy6-30, "0,N")

    # AmendmentOperation --modifier--> ArticleVersion
    dcx7, dcy7 = 565, 700
    draw_diamond(d, dcx7, dcy7, "modifier", w=130, h=44)
    draw_line(d, version[0], version[1]+version[3]//2, dcx7, dcy7-22)
    draw_line(d, dcx7, dcy7+22, amendment[0], amendment[1]-amendment[3]//2)
    draw_card(d, dcx7+70, dcy7-35, "1,1")
    draw_card(d, dcx7+70, dcy7+20, "0,N")

    out = r"C:\Users\RSCH\Downloads\fig_3_4_corrige.png"
    img.save(out, dpi=(300, 300))
    print(f"OK: {out}")


# ═══════════════════════════════════════════════════════════════
# FIGURE 3.5 — MCD cycle de conformité
# ═══════════════════════════════════════════════════════════════

def gen_fig35():
    W, H = 1800, 1100
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    t = "Figure 3.5 — Modèle conceptuel du cycle de conformité"
    tw = d.textlength(t, font=FONTS["title"])
    d.text(((W-tw)//2, 15), t, fill=C_TITLE, font=FONTS["title"])

    # ── Classes ──

    case = draw_class(d, 50, 80, "ComplianceCase", [
        "id", "title", "status",
        "description", "created_at",
    ], w=220)

    msg = draw_class(d, 50, 420, "CaseMessage", [
        "id", "role", "content",
        "created_at",
    ], w=200)

    doc = draw_class(d, 350, 420, "CaseDocument", [
        "id", "filename",
        "document_type",
        "analysis_status",
    ], w=210)

    finding = draw_class(d, 650, 80, "CaseFinding", [
        "id", "title",
        "description", "severity",
        "confidence",
    ], w=210)

    case_action = draw_class(d, 650, 420, "CaseAction", [
        "id", "title",
        "description", "priority",
        "status", "due_date",
    ], w=210)

    assessment = draw_class(d, 1100, 80, "ComplianceAssessment", [
        "id", "score",
        "coverage_rate",
        "assessed_at",
    ], w=240)

    control = draw_class(d, 1100, 420, "Control", [
        "id", "title",
        "control_type", "frequency",
        "automation", "status",
    ], w=220)

    evidence = draw_class(d, 1450, 420, "ControlEvidence", [
        "id", "evidence_type",
        "description", "status",
    ], w=220)

    exception = draw_class(d, 1450, 80, "ExceptionRegister", [
        "id", "reason",
        "approved_by",
        "expiry_date",
    ], w=220)

    link = draw_class(d, 1100, 750, "RequirementControlLink", [
        "id", "status",
        "linked_at",
    ], w=240)

    # ── Associations ──

    # ComplianceCase --contenir--> CaseMessage
    dcx, dcy = 160, 320
    draw_diamond(d, dcx, dcy, "contenir", w=120, h=40)
    draw_line(d, case[0], case[1]+case[3]//2, dcx, dcy-20)
    draw_line(d, dcx, dcy+20, msg[0], msg[1]-msg[3]//2)
    draw_card(d, dcx+65, dcy-28, "1,1")
    draw_card(d, dcx+65, dcy+12, "0,N")

    # ComplianceCase --joindre--> CaseDocument
    dcx2, dcy2 = 350, 320
    draw_diamond(d, dcx2, dcy2, "joindre", w=110, h=40)
    draw_line(d, case[4]+case[2], case[1]+case[3]//2-10, dcx2, dcy2-20)
    draw_line(d, dcx2, dcy2+20, doc[0], doc[1]-doc[3]//2)
    draw_card(d, dcx2+60, dcy2-28, "1,1")
    draw_card(d, dcx2+60, dcy2+12, "0,N")

    # ComplianceCase --produire--> CaseFinding
    dcx3, dcy3 = 430, 150
    draw_diamond(d, dcx3, dcy3, "produire", w=120, h=40)
    draw_line(d, case[4]+case[2], case[1], dcx3-60, dcy3)
    draw_line(d, dcx3+60, dcy3, finding[4], finding[1])
    draw_card(d, dcx3-60, dcy3-25, "1,1")
    draw_card(d, dcx3+40, dcy3-25, "0,N")

    # CaseFinding --déclencher--> CaseAction
    dcx4, dcy4 = 755, 330
    draw_diamond(d, dcx4, dcy4, "déclencher", w=130, h=40)
    draw_line(d, finding[0], finding[1]+finding[3]//2, dcx4, dcy4-20)
    draw_line(d, dcx4, dcy4+20, case_action[0], case_action[1]-case_action[3]//2)
    draw_card(d, dcx4+70, dcy4-28, "1,1")
    draw_card(d, dcx4+70, dcy4+12, "0,N")

    # ComplianceCase --évaluer par--> ComplianceAssessment
    dcx5, dcy5 = 870, 120
    draw_diamond(d, dcx5, dcy5, "évaluer par", w=130, h=40)
    draw_line(d, finding[4]+finding[2], finding[1], dcx5-65, dcy5)
    draw_line(d, dcx5+65, dcy5, assessment[4], assessment[1])
    draw_card(d, dcx5-65, dcy5-25, "1,1")
    draw_card(d, dcx5+45, dcy5-25, "0,N")

    # Control --attester par--> ControlEvidence
    dcx6, dcy6 = 1380, 500
    draw_diamond(d, dcx6, dcy6, "attester par", w=130, h=40)
    draw_line(d, control[4]+control[2], control[1], dcx6-65, dcy6)
    draw_line(d, dcx6+65, dcy6, evidence[4], evidence[1])
    draw_card(d, dcx6-65, dcy6-25, "1,1")
    draw_card(d, dcx6+45, dcy6-25, "0,N")

    # Control --couvrir--> Exigence (via RequirementControlLink)
    dcx7, dcy7 = 1210, 650
    draw_diamond(d, dcx7, dcy7, "couvrir", w=110, h=40)
    draw_line(d, control[0], control[1]+control[3]//2, dcx7, dcy7-20)
    draw_line(d, dcx7, dcy7+20, link[0], link[1]-link[3]//2)
    draw_card(d, dcx7+60, dcy7-28, "0,N")
    draw_card(d, dcx7+60, dcy7+12, "0,N")

    # Control --enregistrer exception--> ExceptionRegister
    dcx8, dcy8 = 1380, 250
    draw_diamond(d, dcx8, dcy8, "enregistrer", w=130, h=40)
    draw_line(d, control[0], control[1]-control[3]//2, dcx8, dcy8+20)
    draw_line(d, dcx8+65, dcy8, exception[4], exception[1]+20)
    draw_card(d, dcx8-20, dcy8+22, "1,1")
    draw_card(d, dcx8+45, dcy8-25, "0,N")

    out = r"C:\Users\RSCH\Downloads\fig_3_5_corrige.png"
    img.save(out, dpi=(300, 300))
    print(f"OK: {out}")


if __name__ == "__main__":
    gen_fig34()
    gen_fig35()
    print("Done.")
