from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(r"C:\Users\RSCH\Daleel")
CAPTURES = ROOT / "captures"
OUT = ROOT / "presentation" / "demo_daleel.gif"
THUMB = ROOT / "presentation" / "demo_daleel_cover.png"

W, H = 1280, 720
NAVY = (35, 41, 70)
GOLD = (212, 164, 55)
WHITE = (255, 255, 255)
ICE = (246, 248, 252)
MUTED = (92, 103, 125)


SCENES = [
    ("fig_4_1_chatbot.png", "1. Question juridique", "L'utilisateur pose une question en langage naturel."),
    ("fig_4_1_chat_reponse.png", "2. Reponse sourcee", "Daleel repond avec contexte, sources et garde-qualite."),
    ("fig_4_2_admin_documents.png", "3. Gestion documentaire", "Le corpus est importe, traite et indexe."),
    ("fig_4_3_dashboard.png", "4. Pilotage conformite", "Les indicateurs aident a prioriser les actions."),
    ("fig_4_2_agent_tool_log.png", "5. Tracabilite", "Les appels d'outils rendent le raisonnement auditable."),
]


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


TITLE_FONT = font(38, True)
BODY_FONT = font(24)
SMALL_FONT = font(19, True)


def fit_image(img, box_w, box_h):
    img = img.convert("RGB")
    ratio = min(box_w / img.width, box_h / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    return img.resize((nw, nh), Image.LANCZOS)


def rounded_panel(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def make_frame(filename, title, subtitle, index):
    bg = Image.new("RGB", (W, H), ICE)
    draw = ImageDraw.Draw(bg)

    draw.rectangle((0, 0, W, 92), fill=NAVY)
    draw.text((52, 24), "Daleel - demonstration", font=TITLE_FONT, fill=WHITE)
    draw.rounded_rectangle((1030, 24, 1228, 64), radius=20, fill=GOLD)
    draw.text((1060, 34), "PFE 2025-2026", font=SMALL_FONT, fill=NAVY)

    source = Image.open(CAPTURES / filename)
    shot = fit_image(source, 1160, 500)
    x = (W - shot.width) // 2
    y = 120

    shadow = Image.new("RGBA", (shot.width + 28, shot.height + 28), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((14, 14, shot.width + 14, shot.height + 14), radius=22, fill=(0, 0, 0, 72))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    bg.paste(shadow.convert("RGB"), (x - 14, y - 10), shadow)

    rounded_panel(draw, (x - 2, y - 2, x + shot.width + 2, y + shot.height + 2), 20, WHITE, (220, 226, 238), 2)
    bg.paste(shot, (x, y))

    draw.rounded_rectangle((70, 625, 1210, 690), radius=18, fill=WHITE, outline=(225, 230, 240), width=2)
    draw.ellipse((94, 641, 126, 673), fill=GOLD)
    draw.text((104, 645), str(index + 1), font=SMALL_FONT, fill=NAVY)
    draw.text((148, 635), title, font=BODY_FONT, fill=NAVY)
    draw.text((148, 664), subtitle, font=font(18), fill=MUTED)
    return bg


def main():
    frames = [make_frame(*scene, index=i) for i, scene in enumerate(SCENES)]
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=[2300, 2600, 2300, 2300, 2500],
        loop=0,
        optimize=True,
    )
    frames[0].save(THUMB)
    print(f"OK - demo generated: {OUT}")
    print(f"OK - cover generated: {THUMB}")


if __name__ == "__main__":
    main()
