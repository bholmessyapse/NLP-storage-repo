import pandas as pd
import numpy as np
# For regex
import re
import regex
import NumWords
import os
import nltk
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
# import operator
from subprocess import call
import itertools
import os
import sys
import csv

pd.set_option("display.max_rows", None, "display.max_columns", None)

# Now beginning the sorting out!
pathReports = pd.read_csv("/Users/bholmes/Desktop/DeleteMeSoon/MSMDR Narratives/PathReports.csv", low_memory=False)

bowList = []
tagsList = []
reportIdList = []
patientIdList = []
testTypeList = []



obs = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/obitSSA.csv", low_memory=False)
print(obs.columns)
input()


#for x in range(0, len(pathReports['description'])):
for x in range(0, 10):
    # These lists go into making the dataframe containing the tags for each report.
    matchedWordsList = []
    candidateScoreList = []
    candidateMatchedList = []
    candidatePreferredList = []
    semTypesList = []
    negatedList = []
    sourcesList = []
    # We'll pull out the data as usual from each test - probably won't keep it all
    if x % 100 == 0:
        print(x, ' of ', len(pathReports['description']))
    lower = pathReports['description'][x].lower()
    lower = re.sub(' +', ' ', lower)
    splitReport = lower.split('\n')
    # We'll pull out the MRN
    try:
        mrnIndex = lower.index("rec.:")
        MRN = lower[mrnIndex + 5:mrnIndex + 14].strip()
    except Exception as e:
        MRN = ''
    # And the name
    nameIndex = lower.index('name:')
    endName = lower.index('accession')
    nameBit = lower[nameIndex + 5: endName]
    firstName = nameBit.split(',')[1].strip()
    lastName = nameBit.split(',', )[0].strip()
    middleName = ''
    if len(firstName.split()) > 1:
        middleName = firstName.split()[1]
        firstName = firstName.split()[0]
    # And the accession
    accession = lower[endName + len('accession #:'):mrnIndex - 5].strip()
    # And the DOB
    dobindex = lower.index('dob:')
    enddod = lower.index('(age')
    dob = lower[dobindex + 4:enddod].strip()
    index = [idx for idx, s in enumerate(splitReport) if 'patient name:' in s][0]
    indexTT = index - 1
    testType = splitReport[indexTT]
    # Pull out test type
    while testType == '' or 'amended' in testType.lower() or testType.lower().replace('-', '') == '':
        indexTT = indexTT - 1
        testType = splitReport[indexTT].strip()
        if testType.endswith('.'):
            testType = testType[:-1]
    testTypeOrig = testType
    testTypeList.append(testType)
    reportIdList.append(pathReports['id'][x])
    patientIdList.append(pathReports['patientid'][x])

    # Now let's get a Bag of Words. We'll sentence Tokenize, and remove punctuation
    corpus = nltk.sent_tokenize(lower)
    for i in range(len(corpus)):
        corpus[i] = re.sub(r'\W', ' ', corpus[i])
        corpus[i] = re.sub(r'\s+', ' ', corpus[i])
    # Now we'll find the word frequencies per sentence
    wordfreq = {}
    for sentence in corpus:
        tokens = nltk.word_tokenize(sentence)
        for token in tokens:
            if token not in wordfreq.keys():
                wordfreq[token] = 1
            else:
                wordfreq[token] += 1

    bowList.append(wordfreq)

    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
    lower = ' '.join(lower.split('\n'))
    lower = lower.encode("ascii", "ignore")
    lower = lower.decode()
    lower = lower + "\n"
    with open(file, 'w') as filetowrite:
        filetowrite.write(lower)
    # Now let's do metamap on it
    os.chdir('/Users/bholmes/public_mm')
    call(["bin/skrmedpostctl", "start"])
    #call(["bin/wsdserverctl", "start"])

    # This uses metamap to create an output file based on the input file.
    try:
        os.system("bin/metamap --JSONf 2 -Q 0 --prune 20 --negex --nomap NoMapFile /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                  "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
    except:
        continue

    call(["bin/skrmedpostctl", "stop"])
    #call(["bin/wsdserverctl", "stop"])

    with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
        data = json.load(json_file)

    # We go by utterance -> phrase -> mapping -> mappingCandidates
    for utt in range(0, len(data['AllDocuments'][0]['Document']['Utterances'])):
        utterance = data['AllDocuments'][0]['Document']['Utterances'][utt]
        for phrasePos in range(0, len(utterance['Phrases'])):
            phrase = utterance['Phrases'][phrasePos]
            for mappingPos in range(0, len(phrase['Mappings'])):
                mapping = phrase['Mappings'][mappingPos]
                for mappingCandidatePos in range(0, len(mapping['MappingCandidates'])):
                    mappingCandidate = mapping['MappingCandidates'][mappingCandidatePos]
                    matchedWordsList.append(' '.join(mappingCandidate['MatchedWords']))
                    candidateScoreList.append(mappingCandidate['CandidateScore'])
                    candidateMatchedList.append(mappingCandidate['CandidateMatched'])
                    candidatePreferredList.append(mappingCandidate['CandidatePreferred'])
                    semTypesList.append(' '.join(mappingCandidate['SemTypes']))
                    negatedList.append(' '.join(mappingCandidate['Negated']))
                    sourcesList.append(' '.join(mappingCandidate['Sources']))


    tagsDF = pd.DataFrame(list(zip(matchedWordsList, semTypesList, sourcesList, candidateMatchedList, candidatePreferredList, candidateScoreList,
                                   negatedList)), columns=['MatchedWords', 'SemTypes', 'Sources', 'CandidateMatched', 'CandidatePreferred', 'CandidateScore', 'Negatived'])
    tagsDF = tagsDF.drop_duplicates()
    tagsDF = tagsDF.reset_index(drop=True)
    tagsList.append(tagsDF)


resultDF = pd.DataFrame(list(zip(bowList, tagsList, reportIdList, patientIdList, testTypeList)))

resultDF.to_csv("~/Desktop/DeleteMeSoon/Artifact/BoWAndTagsForNarratives.csv", index=False)