import pandas as pd
from os import listdir
from os.path import isfile, join
# For regex
import re
import math
from MetaMapForLots import metamapstringoutput
from metamapLoader import metamapStarter
from metamapLoader import metamapCloser

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# This one is now to get FISH specific tests from the regular neo

newPath = mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/NeoFish/'

countFiles = True

mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Neogenomics/'
txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]
fnum = 0
brokens = []
for txt in txts:
    fnum = fnum + 1
    file = mypath + txt
    file = open(file, mode='r')
    all_of_it = file.read()
    file.close()
    with open("/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/NeoFish/" + txt.replace('_out_text_SAMPLE', ''), "a+") as f:
        f.write(all_of_it)
