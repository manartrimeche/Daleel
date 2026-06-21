# -*- coding: utf-8 -*-
import sys
import pdfplumber

path = r'C:\Users\RSCH\Downloads\Memoire Pfe_Manar Trimeche.pdf'
start = int(sys.argv[1])
end = int(sys.argv[2])
full = len(sys.argv) > 3 and sys.argv[3] == "full"

pdf = pdfplumber.open(path)
for i in range(start - 1, min(end, len(pdf.pages))):
    text = pdf.pages[i].extract_text()
    if text:
        print("==== PAGE {} ====".format(i + 1))
        print(text if full else text[:900])
        print("")
pdf.close()
