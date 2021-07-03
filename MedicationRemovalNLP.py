import pandas as pd
import numpy as np
# For regex
import re
import regex
import NumWords
import os
import json
from NumWords import text2int
import math
from sklearn import tree
from collections import Counter
from datetime import datetime
from lifelines import KaplanMeierFitter
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.evaluate import mcnemar
from MetaMapForLots import metamapstringoutput


# Now beginning the sorting out!
pathReports = pd.read_csv("/Users/bholmes/Desktop/DeleteMeSoon/Josh/RegTreatment.bsv", sep='|', low_memory=False)

print(pathReports.columns)
#input()

chemoResults = []
hormoneResults = []
brmResults = []
chemoText = []
hormoneText = []
brmText = []
for x in range(0, len(pathReports['rxTextChemo'])):
    if type(pathReports['rxTextChemo'][x]) == str:
        if 'none' != pathReports['rxTextChemo'][x].lower():
            lot = pathReports['rxTextChemo'][x]
            lot = lot.lower()
            lot = lot.replace('ctx', 'cyclophosphamide').replace('hrt', 'hormone therapy').replace('ht', 'hrt').replace('tx', 'therapy')
            lot = lot + '.'
            lot = lot + '\n'
            file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
            with open(file, 'w') as filetowrite:
                filetowrite.write(lot)
            print(lot)
            try:
                results = metamapstringoutput()
            except:
                continue
            print("AND THE RESULTS")
            print(results)
            resultArray = []
            for index, row in results.iterrows():
                addMe = False
                res = ' '.join(row['Biomarker'])
                if ''.join(row['Concept']) in ['contraindicated', 'refused']:
                    res = res + ", " + ''.join(row['Concept'])
                    addMe = True
                elif ''.join(row['Qualifier']) in ['negative']:
                    res = res + ", " + ''.join(row['Qualifier'])
                    addMe = True
                resultArray.append(res)
            result = ', '.join(resultArray)
            if addMe:
                chemoResults.append(result)
                chemoText.append(lot)
            else:
                chemoResults.append('')
                chemoText.append(pathReports['rxTextChemo'][x])
        else:
            chemoResults.append('')
            chemoText.append(pathReports['rxTextChemo'][x])
    else:
        chemoResults.append('')
        chemoText.append(pathReports['rxTextChemo'][x])

    if type(pathReports['rxTextHormone'][x]) == str:
        if 'none' not in pathReports['rxTextHormone'][x].lower():
            lot = pathReports['rxTextHormone'][x]
            lot = lot.lower()
            lot = lot.replace('ctx', 'cyclophosphamide').replace('hrt', 'hormone therapy').replace('ht', 'hrt').replace('tx', 'therapy')
            lot = lot + '.'
            lot = lot + '\n'
            file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
            with open(file, 'w') as filetowrite:
                filetowrite.write(lot)
            print(lot)
            results = metamapstringoutput()
            print("AND THE RESULTS")
            resultArray = []
            for index, row in results.iterrows():
                addMe = False
                res = ' '.join(row['Biomarker'])
                if ''.join(row['Concept']) in ['contraindicated', 'refused']:
                    res = res + ", " + ''.join(row['Concept'])
                    addMe = True
                elif ''.join(row['Qualifier']) in ['negative']:
                    res = res + ", " + ''.join(row['Qualifier'])
                    addMe = True
                resultArray.append(res)
            result = ', '.join(resultArray)
            if addMe:
                hormoneResults.append(result)
                hormoneText.append(lot)
            else:
                hormoneResults.append('')
                hormoneText.append(pathReports['rxTextHormone'][x])
        else:
            hormoneResults.append('')
            hormoneText.append(pathReports['rxTextHormone'][x])
    else:
        hormoneResults.append('')
        hormoneText.append(pathReports['rxTextHormone'][x])

    if type(pathReports['rxTextBrm'][x]) == str:
        if 'none' not in pathReports['rxTextBrm'][x].lower():
            lot = pathReports['rxTextBrm'][x]
            lot = lot.lower()
            lot = lot.replace('ctx', 'cyclophosphamide').replace('hrt', 'hormone therapy').replace('ht', 'hrt').replace('tx', 'therapy')
            lot = lot + '.'
            lot = lot + '\n'
            file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
            with open(file, 'w') as filetowrite:
                filetowrite.write(lot)
            print(lot)
            results = metamapstringoutput()
            print("AND THE RESULTS")
            print(results)
            resultArray = []
            for index, row in results.iterrows():
                addMe = False
                res = ' '.join(row['Biomarker'])
                if ''.join(row['Concept']) in ['contraindicated', 'refused']:
                    res = res + ", " + ''.join(row['Concept'])
                    addMe = True
                elif ''.join(row['Qualifier']) in ['negative']:
                    res = res + ", " + ''.join(row['Qualifier'])
                    addMe = True
                resultArray.append(res)
            result = ', '.join(resultArray)
            if addMe:
                brmResults.append(result)
                brmText.append(lot)
            else:
                brmResults.append('')
                brmText.append(pathReports['rxTextBrm'][x])
        else:
            brmResults.append('')
            brmText.append(pathReports['rxTextBrm'][x])
    else:
        brmResults.append('')
        brmText.append(pathReports['rxTextBrm'][x])

print(len(chemoResults))
print(len(chemoText))
print(len(hormoneResults))
print(len(hormoneText))
print(len(brmResults))
print(len(brmText))

chemoResults = pd.DataFrame(list(zip(chemoResults, chemoText, hormoneResults, hormoneText, brmResults, brmText)), columns=['chemo results', 'chemo text', 'hormone results', 'hormone text', 'brm results', 'brm text'])
chemoResults.to_csv('/Users/bholmes/Desktop/DeleteMeSoon/Josh/ChemoResults.csv')