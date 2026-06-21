# -*- coding: utf-8 -*-
import sys
import pdfplumber

path = sys.argv[1]
start = int(sys.argv[2])
end = int(sys.argv[3])

pdf = pdfplumber.open(path)
print("TOTAL PAGES:", len(pdf.pages))
for i in range(start - 1, min(end, len(pdf.pages))):
    text = pdf.pages[i].extract_text()
    if text:
        print("==== PAGE {} ====".format(i + 1))
        print(text)
        print("")
pdf.close()
