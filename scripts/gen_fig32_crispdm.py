from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "captures" / "fig_3_2_flux_rag.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["arialbd.ttf" if bold else "arial.ttf", "segoeuib.ttf" if bold else "segoeui.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def draw_wrapped(draw, text, box, fnt, fill="#344054", max_chars=52, line_gap=8):
    x1, y1, x2, _ = box
    y = y1
    for line in wrap(text, max_chars):
        draw.text((x1, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def rounded(draw, box, fill, outline, radius=24, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def main():
    width, height = 2200, 1480
    img = Image.new("RGB", (width, height), "#f8fbff")
    draw = ImageDraw.Draw(img)

    title_f = font(48, True)
    subtitle_f = font(25)
    header_f = font(25, True)
    phase_f = font(22, True)
    body_f = font(22)
    small_f = font(18)

    draw.text((90, 60), "Figure 3.2 - Lecture CRISP-DM du traitement d'une requête Daleel", font=title_f, fill="#101828")
    draw.text(
        (92, 124),
        "Une vue simplifiée qui relie le besoin utilisateur, les données, la modélisation, l'évaluation et la restitution.",
        font=subtitle_f,
        fill="#475467",
    )

    # Top context band.
    rounded(draw, (90, 195, 2110, 330), "#e0f2fe", "#38bdf8", radius=28, width=3)
    draw.text((130, 228), "Point de départ", font=header_f, fill="#075985")
    draw.text(
        (390, 226),
        "L'utilisateur pose une question juridique en langage naturel. Le système doit fournir une réponse claire, sourcée et exploitable.",
        font=body_f,
        fill="#0f172a",
    )

    columns = [
        ("Phase CRISP-DM", 110, 430, 395),
        ("Rôle dans Daleel", 415, 430, 980),
        ("Ce que cela apporte", 1000, 430, 2090),
    ]
    header_y = 390
    for label, x1, _, x2 in columns:
        rounded(draw, (x1, header_y, x2, header_y + 68), "#101828", "#101828", radius=14, width=1)
        tw = draw.textbbox((0, 0), label, font=header_f)[2]
        draw.text((x1 + (x2 - x1 - tw) / 2, header_y + 18), label, font=header_f, fill="#ffffff")

    rows = [
        (
            "1. Compréhension du métier",
            "Identifier le besoin réel : accéder rapidement à une information juridique fiable.",
            "La requête est interprétée selon le contexte métier : domaine juridique, langue, intention et type de réponse attendue.",
            "#eef4ff",
            "#4f46e5",
        ),
        (
            "2. Compréhension des données",
            "Mobiliser le corpus juridique disponible : lois, codes, amendements et documents internes.",
            "Le système sait quelles sources peuvent répondre à la question et conserve la traçabilité des références.",
            "#ecfeff",
            "#0891b2",
        ),
        (
            "3. Préparation des données",
            "Nettoyer, segmenter, indexer et vectoriser les textes avant la recherche.",
            "Les documents bruts deviennent des unités exploitables : chunks, embeddings, métadonnées et index FAISS.",
            "#f0fdf4",
            "#16a34a",
        ),
        (
            "4. Modélisation",
            "Combiner recherche hybride, reranking, enrichissement KG Light et génération par LLM.",
            "La réponse est construite à partir des passages les plus pertinents, pas seulement depuis la mémoire du modèle.",
            "#fff7ed",
            "#ea580c",
        ),
        (
            "5. Évaluation",
            "Vérifier les sources, les citations, les références d'articles et la cohérence linguistique.",
            "La garde-qualité réduit les hallucinations et bloque les réponses non suffisamment justifiées.",
            "#fefce8",
            "#ca8a04",
        ),
        (
            "6. Déploiement",
            "Retourner la réponse dans l'interface avec les sources et le journal de raisonnement.",
            "L'utilisateur obtient une réponse lisible, traçable et directement exploitable dans son travail.",
            "#fdf2f8",
            "#db2777",
        ),
    ]

    y = 480
    row_h = 118
    for phase, role, benefit, fill, stroke in rows:
        rounded(draw, (110, y, 2090, y + row_h), fill, stroke, radius=18, width=3)
        draw.line((395, y, 395, y + row_h), fill="#d0d5dd", width=2)
        draw.line((980, y, 980, y + row_h), fill="#d0d5dd", width=2)
        draw_wrapped(draw, phase, (135, y + 26, 370, y + row_h), phase_f, fill="#101828", max_chars=23, line_gap=6)
        draw_wrapped(draw, role, (430, y + 24, 940, y + row_h), body_f, fill="#344054", max_chars=43, line_gap=6)
        draw_wrapped(draw, benefit, (1018, y + 24, 2050, y + row_h), body_f, fill="#344054", max_chars=86, line_gap=6)
        y += row_h + 22

    # Bottom result band.
    rounded(draw, (90, 1372, 2110, 1445), "#ffffff", "#d0d5dd", radius=18, width=2)
    draw.text((130, 1394), "À retenir :", font=header_f, fill="#101828")
    draw.text(
        (310, 1396),
        "la figure ne décrit pas tous les appels techniques ; elle explique comment Daleel transforme une question en résultat validé selon la logique CRISP-DM.",
        font=small_f,
        fill="#475467",
    )

    img.save(OUT)


if __name__ == "__main__":
    main()
