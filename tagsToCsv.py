import pandas as pd
import numpy as np
# For regex
import re
import gc
from NumWords import text2int
from MetaMapForLots import metamapstringoutput

df = pd.read_csv("~/Desktop/DeleteMeSoon/TagsToRows/ALK.csv", low_memory=False)

geneNameList = []
probeNameList = []
rearrangementNameList = []
chromosomeList = []
percentNucleiList = []
numberOfCellsList = []
numberOfCopiesList = []
variantNameList = []
normalList = []
labelList = []

wholeTextList = []
pulledOutList = []
testPatientInfoList = []
biomarkerSectionList = []
tagsList = []

for i in range(0, len(df['tags'])):
    lines = str(df['tags'][i])
    if '|' not in lines:
        lines = 'ALK | | | no test info'
    lines = lines.split('\n')
    for line in lines:
        thisLine = line.split('|')
        if thisLine == ['']:
            continue
        if 'alk' in thisLine[0]:
            geneNameList.append('ALK')
        if '2p23' in thisLine[0]:
            probeNameList.append('2p23')
        if 'chromosome 2' in thisLine[0]:
            chromosomeList.append('2')
        nums = thisLine[2].split(',')
        for num in nums:
            if 'nuclei' in num:
                percentNucleiList.append(num.split()[0])
            if 'cop' in num:
                numberOfCopiesList.append(' '.join(num.split()[:-1]))
            if '/' in num:
                numberOfCellsList.append(num)
        labelList.append(thisLine[3])
        if 'nuc ish' in thisLine[0]:
            rearrangementNameList.append(thisLine[0])
        variantNameList.append(thisLine[1])
        if 'normal' in thisLine[0]:
            normalList.append("True")

        while len(geneNameList) < len(labelList):
            geneNameList.append('')

        while len(probeNameList) < len(labelList):
            probeNameList.append('')

        while len(rearrangementNameList) < len(labelList):
            rearrangementNameList.append('')

        while len(chromosomeList) < len(labelList):
            chromosomeList.append('')

        while len(percentNucleiList) < len(labelList):
            percentNucleiList.append("")

        while len(numberOfCopiesList) < len(labelList):
            numberOfCopiesList.append('')

        while len(numberOfCellsList) < len(labelList):
            numberOfCellsList.append('')

        while len(variantNameList) < len(labelList):
            variantNameList.append('')

        while len(normalList) < len(labelList):
            normalList.append('')
        wholeTextList.append(df['whole test'][i])
        pulledOutList.append(df['pulled-out sections'][i])
        testPatientInfoList.append(df['test/patient info'][i])
        biomarkerSectionList.append(df['just biomarker'][i])
        tagsList.append(df['tags'][i])


panelsDataFrame = pd.DataFrame(list(zip(wholeTextList, pulledOutList, testPatientInfoList, biomarkerSectionList, tagsList,
    geneNameList, probeNameList, rearrangementNameList, chromosomeList, percentNucleiList, numberOfCellsList, numberOfCopiesList, variantNameList, normalList, labelList)),
                                                            columns=['whole test', 'pulled-out sections', 'test/patient info', 'biomarker section', 'tags',
                                                                'gene', 'probe', 'rearrangement name', 'chromosome', '% nuclei', '# cells', '# copies', 'variant', 'normal results', 'label'])


panelsDataFrame.to_csv("~/Desktop/DeleteMeSoon/TagsToRows/ALKResult.csv", index=False)