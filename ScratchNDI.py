import pandas as pd
import numpy
# For regex
import re
import regex
import NumWords
import os
import json
from NumWords import text2int
import math
from sklearn import tree

# This is to shuffle up the reports for testing.
from random import shuffle

# This is for matching misspelled section headers.
# You should ALSO make sure 'python-levenshtein' is installed.
import regex

# For statistics
from collections import Counter

#featureFrame = syapseData = pd.read_csv("/Users/bholmes/Desktop/NDI/FromScratch/ForDate.txt", sep='|', low_memory=False)

allTests = pd.read_csv("/Users/bholmes/Desktop/DeleteMeSoon/PanelsUpdatedFull.csv", low_memory=False)

filesOnS3 = []

missingrecordId = []
missingAsenscion = []
missingTest = []

fileNames = []

with open("/Users/bholmes/Desktop/DeleteMeSoon/s3Files.txt", 'r') as s3Files:
    lines = s3Files.readlines()
    for line in lines:
        filesOnS3.append(line.split()[-1])

for index, row in allTests.iterrows():
    if (str(row['hl7 record id']) + '_' + row['reportId'].upper() + '_txt.txt') not in filesOnS3:
        missingrecordId.append(row['hl7 record id'])
        missingAsenscion.append(row['reportId'])
        missingTest.append(row['full text'])
        print('added ' + str(row['hl7 record id']))

numWrit = 0
for pos in range(0, len(missingrecordId)):
    if str(missingrecordId[pos]) + '_' + missingAsenscion[pos].upper() + "_txt.txt" not in fileNames:
        fileNames.append(str(missingrecordId[pos]) + '_' + missingAsenscion[pos].upper() + "_txt.txt")
        fileName = "/Users/bholmes/Desktop/DeleteMeSoon/Missing/" + str(missingrecordId[pos]) + '_' + missingAsenscion[pos].upper() + "_txt.txt"
        with open(fileName, 'w') as out_file:
            out_file.write(missingTest[pos])
        numWrit = numWrit + 1
        print('wrote ' + str(numWrit) + "!")
