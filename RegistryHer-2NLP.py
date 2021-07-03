import nltk
import json
import pandas as pd
import re
from subprocess import call
import itertools
import os
import sys
import csv
from MetaMapForLots import metamapstringoutput

pd.set_option("display.max_rows", None, "display.max_columns", None)

# Now beginning the sorting out!
pathReports1 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/AdventAllRegistry.csv", low_memory=False)
pathReports2 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/AmitaAllRegistry.csv", low_memory=False)
pathReports3 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/AsenscionAllRegistry.csv", low_memory=False)
pathReports4 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/AuroraAllRegistry.csv", low_memory=False)
pathReports5 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/HfhsAllRegistry.csv", low_memory=False)

pathReports = pd.concat([pathReports1, pathReports2, pathReports3, pathReports4, pathReports5], axis=0)
pathReports = pathReports.reset_index()

textList = []
bowList = []
tagsList = []
normList = []
reportIdList = []
patientIdList = []
primarySiteList = []

# Now let's do metamap on it
os.chdir('/Users/bholmes/public_mm')
call(["bin/skrmedpostctl", "start"])
# call(["bin/wsdserverctl", "start"])

# This is to count how many instances of genes we find
geneMatchedFrequency = dict()

#for x in range(0, len(pathReports['textdxproclabtests'])):
for x in range(0, 50000):
    # These lists go into making the dataframe containing the tags for each report.
    matchedWordsList = []
    candidateScoreList = []
    candidateMatchedList = []
    candidatePreferredList = []
    semTypesList = []
    negatedList = []
    sourcesList = []

    # This is specifically for gene or amino acid tags
    geneMatchedWordsList = []
    geneMatchedNormalizedList = []

    # We'll pull out the data as usual from each test - probably won't keep it all
    if x % 100 == 0:
        print(x, ' of ', len(pathReports['textdxproclabtests']))
    lower = str(pathReports['textdxproclabtests'][x]).lower()
    try:
        reportIdList.append(pathReports['id'][x].lower())
    except:
        print(pathReports['id'][x])
        input()
    patientIdList.append(pathReports['patientidnumber'][x])
    primarySiteList.append(str(pathReports['textprimarysitetitle'][x]).lower())
    textList.append(lower)

    # Now let's get a Bag of Words. We'll sentence Tokenize, and remove punctuation
    corpus = nltk.sent_tokenize(lower)

    if ' her' in lower:
        file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
        lower = ' '.join(lower.split('\n'))
        lower = lower.encode("ascii", "ignore")
        lower = lower.decode()
        lower = lower + "\n"
        with open(file, 'w') as filetowrite:
            filetowrite.write(lower)

        results = metamapstringoutput()
        print(results)
        print(lower)
        input()
        for index, row in results.iterrows():
            bioResult = ', '.join(row['Biomarker'])
            conResult = ', '.join(row['Concept'])
            numResult = ', '.join(row['Numeric'])
            qualResult = ', '.join(row['Qualifier'])

    normDF = pd.DataFrame(list(zip(geneMatchedWordsList, geneMatchedNormalizedList)), columns=['Matched Words', 'Normalized Words'])
    normDF = normDF.drop_duplicates()
    normDF = normDF.reset_index(drop=True)
    normList.append(normDF)

    tagsDF = pd.DataFrame(list(zip(matchedWordsList, semTypesList, sourcesList, candidateMatchedList, candidatePreferredList, candidateScoreList,
                                   negatedList)), columns=['MatchedWords', 'SemTypes', 'Sources', 'CandidateMatched', 'CandidatePreferred', 'CandidateScore', 'Negatives'])
    tagsDF = tagsDF.drop_duplicates()
    tagsDF = tagsDF.reset_index(drop=True)
    tagsList.append(tagsDF)

call(["bin/skrmedpostctl", "stop"])
# call(["bin/wsdserverctl", "stop"])

# write dict to file
exDict = pd.DataFrame(geneMatchedFrequency.items(), columns=['Gene', '# occurrences'])

exDict.to_csv("~/Desktop/LatestNLP/Registry/RegistryFreq.csv", index=False)

resultDF = pd.DataFrame(list(zip(textList, normList, bowList, tagsList, reportIdList, patientIdList, primarySiteList)), columns=['original text', 'genes', 'Bag of Words', 'tags', 'report id', 'patient id', 'primary site'])

resultDF.to_csv("~/Desktop/LatestNLP/Registry/RegistryBOWAndTags.csv", index=False)