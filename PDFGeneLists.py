import pdftotext
# Import libraries
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import re
import pdfplumber
import textract
import pdftotext


getNewTexts = True

mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Neogenomics/'
pdfs = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.pdf' in f]

fnum = 0

brokens = []

if getNewTexts:
    for pdf in pdfs:
        print(str(fnum), ' of ' , str(len(pdfs)))
        fnum = fnum + 1

        if os.path.isfile(mypath + pdf.replace('.pdf', '_out_text_SAMPLE.txt')):
            print('found one!')
            print(pdf)
            continue

        results = ''
        num = 0
        try:
            with pdfplumber.open(mypath + pdf) as pd:
                    for first_page in pd.pages:
                        num = num + 1
                        print('page ', num, ' of ', len(pd.pages))
                        #first_page = first_page.dedupe_chars()
                        first_page = first_page.extract_text()
                        results = results + ' ' + first_page
            output = results
        except:
            print("HAD A WEIRD ONE AT")
            print(pdf)
            output = ''

        outfile = mypath + pdf[:-4] + "_out_text_SAMPLE.txt"
        f = open(outfile, "a")
        f.write(output)
        f.close()

for x in brokens:
    print(x)