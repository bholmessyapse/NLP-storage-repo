import nltk
import json
import pandas as pd
import re
from subprocess import call
import itertools
import os
import sys
import csv

pd.set_option("display.max_rows", None, "display.max_columns", None)

# Now beginning the sorting out!
pathReports1 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/AdventAllRegistry.csv", low_memory=False)
pathReports2 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/AmitaAllRegistry.csv", low_memory=False)
pathReports3 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/AsenscionAllRegistry.csv", low_memory=False)
pathReports4 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/AuroraAllRegistry.csv", low_memory=False)
pathReports5 = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Registry/Source Files/HfhsAllRegistry.csv", low_memory=False)

pathReports = pd.concat([pathReports1, pathReports2, pathReports3, pathReports4, pathReports5], axis=0)
pathReports = pathReports.reset_index()

pathReports = pathReports.sample(frac=1).reset_index(drop=True)

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
for x in range(0, 10000):
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

    # This uses metamap to create an output file based on the input file.
    try:
        os.system("bin/metamap --JSONf 2 -Q 0 --prune 20 --negex --nomap NoMapFile /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                  "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
    except:
        continue

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
                    if 'gngm' in mappingCandidate['SemTypes'] or 'aapp' in mappingCandidate['SemTypes']:
                        geneMatchedWordsList.append(' '.join(mappingCandidate['MatchedWords']))
                        geneMatchedNormalizedList.append(mappingCandidate['CandidatePreferred'])
                        for word in mappingCandidate['MatchedWords']:
                            word = word + '_matched to_' + mappingCandidate['CandidatePreferred']
                            if word in geneMatchedFrequency:
                                geneMatchedFrequency[word] += 1
                            else:
                                geneMatchedFrequency[word] = 1
                    else:
                        geneMatchedWordsList.append('')
                        geneMatchedNormalizedList.append('')


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
exDict[['input text', 'matched tag']] = exDict.Gene.str.split("_matched to_", expand=True)
del exDict['Gene']

exDict.to_csv("~/Desktop/LatestNLP/Registry/RegistryFreq.csv", index=False)

resultDF = pd.DataFrame(list(zip(textList, normList, bowList, tagsList, reportIdList, patientIdList, primarySiteList)), columns=['original text', 'genes', 'Bag of Words', 'tags', 'report id', 'patient id', 'primary site'])

resultDF.to_csv("~/Desktop/LatestNLP/Registry/RegistryBOWAndTags.csv", index=False)