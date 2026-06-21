from PIL import Image

im = Image.open(r"C:\Users\RSCH\Daleel\captures\fig_1_1_crisp_dm.png")
w, h = im.size
print("taille:", w, h)
# Agrandir x2 pour lisibilite
big = im.resize((w * 2, h * 2), Image.LANCZOS)
big.save(r"C:\Users\RSCH\Daleel\_tmp_crisp_big.png")
# Quadrant bas-gauche (Évaluation) et bas (Modélisation)
im.crop((0, int(h * 0.5), int(w * 0.55), h)).resize((int(w * 1.3), int(h * 0.65)), Image.LANCZOS).save(r"C:\Users\RSCH\Daleel\_tmp_crisp_eval.png")
