# -*- coding: utf-8 -*-
import sys
import pdfplumber

path = r'C:\Users\RSCH\Downloads\Memoire Pfe_Manar Trimeche.pdf'
term = sys.argv[1]

pdf = pdfplumber.open(path)
for i in range(len(pdf.pages)):
    text = pdf.pages[i].extract_text() or ""
    if term in text:
        idx = text.find(term)
        snippet = text[max(0, idx-80):idx+120]
        print("PAGE {}: ...{}...".format(i + 1, snippet.replace(chr(10), " ")))
pdf.close()
