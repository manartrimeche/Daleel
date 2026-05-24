import pdfplumber
with pdfplumber.open(r"C:\Users\RSCH\Downloads\KHLIJ-Eya-version-1.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            print(f"=== PAGE {i+1} ===")
            print(text)
            print()
