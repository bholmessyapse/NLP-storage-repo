import pandas as pd
# For regex
import re
import os
from subprocess import call
import json

from MetaMapForLots import metamapstringoutput
from collections import Counter

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# Now beginning the sorting out!
pathReports = pd.read_csv("/Users/bholmes/Desktop/DeleteMeSoon/MSMDR Narratives/PathReports.csv", low_memory=False)

testTypes = []
reports = []

# List of info captured for the database. We'll do the secondary mapping right in-function. Maybe move it out later?
firstNameList = []
middleNameList = []
lastNameList = []
mrnList = []
dobList = []
accessionList = []
testTextList = []
fullTextList = []
testTypeList = []
testTechList = []
sampleLocationList = []
pathologistList = []
dateOrderedList = []
icdList = []
dateReportedList = []

# These are for tags
matchedWordsList = []
candidateScoreList = []
candidateMatchedList = []
candidatePreferredList = []
semTypesList = []
negatedList = []
sourcesList = []
tagsList = []

# There are three here - named, derived, and general
testGroupList = []


# This is for making sure the lists never get smaller - only for debugging!
storedLen = 0

unknownTests = []
aberrentTests = []
aberrentReasons = []
wrongwayTests = []
extraTests = []
failedTests = []
failedReasons = []

erprNames = ['estrogen receptor', 'progesterone receptor', ' er:', ' pr:', 'er/pr', 'estrogen/progesterone', 'esr1', ' esr', ' pgr']

totalTests = 0
karyocount = 0
for x in range(0, len(pathReports['description'])):
#for x in range(0, 100):
#    try:
    if x % 100 == 0:
        print(x, ' of ', len(pathReports['description']))
    lower = pathReports['description'][x].lower()
    lower = re.sub(' +', ' ', lower)
    splitReport = lower.split('\n')
    # These reports are truncated and don't contain info - NONE have 'her 2' or 'her2' or 'her-2'
    if 'patient name:' not in lower:
        wrongwayTests.append(lower)
        continue
    # We'll pull out the MRN
    try:
        mrnIndex = lower.index("rec.:")
    except Exception as e:
        # There's only one kind without a rec.:, and it's a regadenoson pharmacological stress myocardial perfusion study
        aberrentTests.append(lower)
        aberrentReasons.append('no MRN')
        continue
    MRN = lower[mrnIndex + 5:mrnIndex + 14].strip()
    # And icd code...
    try:
        icdIndex = lower.index('icd code(s):') + len('icd code(s):')
        icdPart = lower[icdIndex:].replace('\n', ' ')
        icdPart = icdPart[:icdPart.index('billing fee')]
    except:
        icdPart = ''
    icdCode = icdPart.strip()
    icdLists = re.findall('\s[a-z]\:\s', icdCode)
    for icd in icdLists:
        icdCode = icdCode.replace(icd, ' ')
    icdCode = ', '.join(list(dict.fromkeys(icdCode.split())))
    icdList.append(icdCode)

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
    firstNameList.append(firstName)
    lastNameList.append(lastName)
    middleNameList.append(middleName)
    # And the accession
    accession = lower[endName + len('accession #:'):mrnIndex - 5].strip()
    # And the DOB
    dobindex = lower.index('dob:')
    enddod = lower.index('(age')
    dob = lower[dobindex + 4:enddod].strip()
    dobList.append(dob)
    index = [idx for idx, s in enumerate(splitReport) if 'patient name:' in s][0]
    indexTT = index - 1
    testType = splitReport[indexTT]
    # Pull out test type
    try:
        mrnIndex = lower.index("rec.:")
    except Exception as e:
        # There's only one kind without a rec.:, and it's a regadenoson pharmacological stress myocardial perfusion study
        wrongwayTests.append(lower)
        continue
    MRN = lower[mrnIndex + 5:mrnIndex + 14].strip()
    mrnList.append(MRN)

    while testType == '' or 'amended' in testType.lower() or testType.lower().replace('-', '') == '':
        indexTT = indexTT - 1
        testType = splitReport[indexTT].strip()
        if testType.endswith('.'):
            testType = testType[:-1]
    testTypeOrig = testType
    reportedDate = ''
    if 'reported:' in lower:
        reportedDate = lower[lower.index('reported: ') + len('reported: '):]
        reportedDate = reportedDate[:reportedDate.index('\n')]
    dateReportedList.append(reportedDate)


    if testType in ['surgical pathology report', 'gynecological cytopathology report', 'non-gynecological cytopathology report', 'hematopathology report',
                    'fine needle aspiration cytopathology report', 'cytogenetics result, fish', 'consultation report', 'molecular pathology and genomic test']:
        testGroup = 'general test'
    else:
        testGroup = 'named test'

    if testType in 'surgical pathology report':
        if 'procedures/addenda' in lower:
            lowerproc = lower.index('procedures/addenda')
            lower = lower[lowerproc:]
            if 'gross description' in lower:
                lower = lower[:lower.index('gross description')]
            # The first test list has SPECIFIC tests, the second has more general ones
            testList = ['estrogen and progesterone receptor assay', 'immunostain for h. pylori', 'gastroesophageal biopsy her-2/neu summary', 'her-2/ neu protein assay (ihc)',
                        'b cell gene rearrangement', 'outside pathology reports.', 'flow cytometry', 'pcr for egfr variant iii mutation', 'stone analysis', 'special stains',
                        'immunostain for helicobacter pylori', 'gms special stain', 'her-2/ neu gene amplification (fish) assay', 'amyloid protein identification',
                        'afb and gms', 'non-specific direct immunofluorescence', 'amyloid typing', 'fusion panel - sarcoma (26 genes)',
                        'polypectomy', 'cd10 and bcl6 stains', 'electron microscopy', 'ig kappa-lambda by cish', 't cell gene rearrangement', 'mgmt promoter methylation',
                        'histochemical staining for fungal organisms', 'ebv chromogenic in-situ hybridization assay', 'immunostains for cmv and hsv',
                        'gestational disease profile', 'ventana ultraview', 'perls iron stain', 'her-2/ neu (sish) gene amplification assay', 'fusion panel - solid tumor (50 genes)',
                        'microsatellite instability testing (msi)', 'cytokeratin ae1/ae3 immunohistochemical stain', 'loss of heterozygosity 1p, 19q assay (loh)', 'gram stain',
                        'mucicarcimin stain', 'braf gene mutation analysis', 'pd-l1 expression', 'colorectal adenocarcinoma her-2/neu summary', 'trichrome special stain',
                        'congo red special stain', 'igg and igg4 staining', 'u of m sendout results (hfah)', 'alk gene rearrangement (fish) assay', 'pcr, tissue identity',
                        'truseq 48 gene cancer panel', 'gastrointestinal stromal tumors (gist) panel', 'melanoma panel', 'colorectal cancer panel', 'idh1 mutation detection assay',
                        'cytogenetics result, not specified', 'pd-l1.', 'comprehensive solid tumor cancer panel (170 genes)', 'cytogenetics result, chromosome analysis']

            backupList = ['immunohistochemical staining', 'histochemistry', 'immunohistology',  'immunohistochemistry', 'incisional biopsy', 'immunofluorescence', 'immunostain',
                          'histochemical stains', 'immunohistochemical studies', 'molecular pathology and genomic test', 'fluorescent in-situ hybridization assay', 'unknown procedure']
            if any(typeT in lower for typeT in testList):
                testType = ''
                for test in testList:
                    if test in lower:
                        testType = testType + "SPR - " + test + ', '
                        testGroup = 'derived test'
            elif ('pas' in lower and ('fungal' in lower or 'fungus' in lower)) or ('pas: negative' in lower) or ('pas: positive' in lower):
                testType = testType + 'SPR - pas test for fungus, '
                testGroup = 'derived test'
            elif ('gms' in lower and ('fungal' in lower or 'fungus' in lower)) or "grocott's methenamine silver stain" in lower:
                testType = testType + 'SPR - gms test for fungus, '
                testGroup = 'derived test'
            elif any(typeT in lower for typeT in backupList):
                testType = ''
                for test in backupList:
                    if test in lower:
                        if 'analyte specific reagent (asr) disclaimer' in lower:
                            lower = lower[:lower.index('analyte specific reagent (asr) disclaimer')]
                        testType = testType + "SPR - " + test + ', '
                        testGroup = 'derived test'
                        print(lower)

                        ####
                        # If we found one of the lower words here, we'll want to get all the metamap tags!
                        ####
                        file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                        lower = lower.replace('\n', ' ')
                        lower = lower.strip()
                        lower = lower.encode("ascii", "ignore")
                        lower = lower.decode()
                        lower = lower + "\n"
                        with open(file, 'w') as filetowrite:
                            filetowrite.write(lower)
                        # Now let's do metamap on it
                        os.chdir('/Users/bholmes/public_mm')
                        call(["bin/skrmedpostctl", "start"])
                        call(["bin/wsdserverctl", "start"])

                        # This uses metamap to create an output file based on the input file.
                        try:
                            os.system("bin/metamap --JSONf 2 -Q 0 --prune 20 --negex --nomap NoMapFile /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                                      "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
                        except:
                            continue

                        call(["bin/skrmedpostctl", "stop"])
                        call(["bin/wsdserverctl", "stop"])

                        with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
                            data = json.load(json_file)

                        # These are for tags
                        tempmatchedWordsList = []
                        tempcandidateScoreList = []
                        tempcandidateMatchedList = []
                        tempcandidatePreferredList = []
                        tempsemTypesList = []
                        tempnegatedList = []
                        tempsourcesList = []
                        temptagsList = []
                        tempTestText = []

                        # We go by utterance -> phrase -> mapping -> mappingCandidates
                        for utt in range(0, len(data['AllDocuments'][0]['Document']['Utterances'])):
                            utterance = data['AllDocuments'][0]['Document']['Utterances'][utt]
                            for phrasePos in range(0, len(utterance['Phrases'])):
                                phrase = utterance['Phrases'][phrasePos]
                                for mappingPos in range(0, len(phrase['Mappings'])):
                                    mapping = phrase['Mappings'][mappingPos]
                                    for mappingCandidatePos in range(0, len(mapping['MappingCandidates'])):
                                        mappingCandidate = mapping['MappingCandidates'][mappingCandidatePos]
                                        tempmatchedWordsList.append(' '.join(mappingCandidate['MatchedWords']))
                                        tempcandidateScoreList.append(mappingCandidate['CandidateScore'])
                                        tempcandidateMatchedList.append(mappingCandidate['CandidateMatched'])
                                        tempcandidatePreferredList.append(mappingCandidate['CandidatePreferred'])
                                        tempsemTypesList.append(' '.join(mappingCandidate['SemTypes']))
                                        tempnegatedList.append(' '.join(mappingCandidate['Negated']))
                                        tempsourcesList.append(' '.join(mappingCandidate['Sources']))

                        matchedWordsList.append(tempmatchedWordsList)
                        candidateScoreList.append(tempcandidateScoreList)
                        candidateMatchedList.append(tempcandidateMatchedList)
                        candidatePreferredList.append(tempcandidatePreferredList)
                        semTypesList.append(tempsemTypesList)
                        negatedList.append(tempnegatedList)
                        sourcesList.append(tempsourcesList)
                        testTextList.append(tempTestText)

            else:
                if 'date' not in lower:
                    print(lower)
                    continue
                if lower[lower.index('procedures/addenda') + len('procedures/addenda'): lower.index('date')].strip() != 'addendum':
                    print(lower[lower.index('procedures/addenda') + len('procedures/addenda'): lower.index('date')])
                    input()
                unknownTests.append(lower)
        elif 'pathological diagnosis:' in lower:
            lowerproc = lower.index('pathological diagnosis:')
            lower = lower[lowerproc:]
            if '***elec' in lower:
                lower = lower[:lower.index('***elec')]
            # The first test list has SPECIFIC tests, the second has more general ones
            testList = ['estrogen and progesterone receptor assay', 'immunostain for h. pylori', 'gastroesophageal biopsy her-2/neu summary', 'her-2/ neu protein assay (ihc)',
                        'b cell gene rearrangement', 'outside pathology reports.', 'flow cytometry', 'pcr for egfr variant iii mutation', 'stone analysis', 'special stains',
                        'immunostain for helicobacter pylori', 'gms special stain', 'her-2/ neu gene amplification (fish) assay', 'amyloid protein identification',
                        'afb and gms', 'non-specific direct immunofluorescence', 'amyloid typing', 'fusion panel - sarcoma (26 genes)',
                        'polypectomy', 'cd10 and bcl6 stains', 'electron microscopy', 'ig kappa-lambda by cish', 't cell gene rearrangement', 'mgmt promoter methylation',
                        'histochemical staining for fungal organisms', 'ebv chromogenic in-situ hybridization assay', 'immunostains for cmv and hsv',
                        'gestational disease profile', 'ventana ultraview', 'perls iron stain', 'her-2/ neu (sish) gene amplification assay', 'fusion panel - solid tumor (50 genes)',
                        'microsatellite instability testing (msi)', 'cytokeratin ae1/ae3 immunohistochemical stain', 'loss of heterozygosity 1p, 19q assay (loh)', 'gram stain',
                        'mucicarcimin stain', 'braf gene mutation analysis', 'pd-l1 expression', 'colorectal adenocarcinoma her-2/neu summary', 'trichrome special stain',
                        'congo red special stain', 'igg and igg4 staining', 'u of m sendout results (hfah)', 'alk gene rearrangement (fish) assay', 'pcr, tissue identity',
                        'truseq 48 gene cancer panel', 'gastrointestinal stromal tumors (gist) panel', 'melanoma panel', 'colorectal cancer panel', 'idh1 mutation detection assay',
                        'cytogenetics result, not specified', 'pd-l1.', 'comprehensive solid tumor cancer panel (170 genes)', 'cytogenetics result, chromosome analysis']

            backupList = ['immunohistochemical staining', 'histochemistry', 'immunohistology',  'immunohistochemistry', 'incisional biopsy', 'immunofluorescence', 'immunostain',
                          'histochemical stains', 'immunohistochemical studies', 'molecular pathology and genomic test', 'fluorescent in-situ hybridization assay', 'unknown procedure']
            if any(typeT in lower for typeT in testList):
                testType = ''
                for test in testList:
                    if test in lower:
                        if 'analyte specific reagent (asr) disclaimer' in lower:
                            lower = lower[:lower.index('analyte specific reagent (asr) disclaimer')]
                        testType = testType + "SPR - " + test + ', '
                        testGroup = 'derived test'

                        ####
                        # If we found one of the lower words here, we'll want to get all the metamap tags!
                        ####
                        file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                        lower = lower.replace('\n', ' ')
                        lower = lower.strip()
                        lower = lower.encode("ascii", "ignore")
                        lower = lower.decode()
                        lower = lower + "\n"
                        with open(file, 'w') as filetowrite:
                            filetowrite.write(lower)
                        # Now let's do metamap on it
                        os.chdir('/Users/bholmes/public_mm')
                        call(["bin/skrmedpostctl", "start"])
                        call(["bin/wsdserverctl", "start"])

                        # This uses metamap to create an output file based on the input file.
                        try:
                            os.system("bin/metamap --JSONf 2 -Q 0 --prune 20 --negex --nomap NoMapFile /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                                      "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
                        except:
                            continue

                        call(["bin/skrmedpostctl", "stop"])
                        call(["bin/wsdserverctl", "stop"])

                        with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
                            data = json.load(json_file)

                        # These are for tags
                        tempmatchedWordsList = []
                        tempcandidateScoreList = []
                        tempcandidateMatchedList = []
                        tempcandidatePreferredList = []
                        tempsemTypesList = []
                        tempnegatedList = []
                        tempsourcesList = []
                        temptagsList = []
                        tempTestText = lower

                        # We go by utterance -> phrase -> mapping -> mappingCandidates
                        for utt in range(0, len(data['AllDocuments'][0]['Document']['Utterances'])):
                            utterance = data['AllDocuments'][0]['Document']['Utterances'][utt]
                            for phrasePos in range(0, len(utterance['Phrases'])):
                                phrase = utterance['Phrases'][phrasePos]
                                for mappingPos in range(0, len(phrase['Mappings'])):
                                    mapping = phrase['Mappings'][mappingPos]
                                    for mappingCandidatePos in range(0, len(mapping['MappingCandidates'])):
                                        mappingCandidate = mapping['MappingCandidates'][mappingCandidatePos]
                                        tempmatchedWordsList.append(' '.join(mappingCandidate['MatchedWords']))
                                        tempcandidateScoreList.append(mappingCandidate['CandidateScore'])
                                        tempcandidateMatchedList.append(mappingCandidate['CandidateMatched'])
                                        tempcandidatePreferredList.append(mappingCandidate['CandidatePreferred'])
                                        tempsemTypesList.append(' '.join(mappingCandidate['SemTypes']))
                                        tempnegatedList.append(' '.join(mappingCandidate['Negated']))
                                        tempsourcesList.append(' '.join(mappingCandidate['Sources']))

                        matchedWordsList.append(tempmatchedWordsList)
                        candidateScoreList.append(tempcandidateScoreList)
                        candidateMatchedList.append(tempcandidateMatchedList)
                        candidatePreferredList.append(tempcandidatePreferredList)
                        semTypesList.append(tempsemTypesList)
                        negatedList.append(tempnegatedList)
                        sourcesList.append(tempsourcesList)
                        testTextList.append(tempTestText)

            elif ('pas' in lower and ('fungal' in lower or 'fungus' in lower)) or ('pas: negative' in lower) or ('pas: positive' in lower):
                testType = 'SPR - pas test for fungus'
                testGroup = 'derived test'
            elif ('gms' in lower and ('fungal' in lower or 'fungus' in lower)) or "grocott's methenamine silver stain" in lower:
                testType = 'SPR - gms test for fungus'
                testGroup = 'derived test'
            elif any(typeT in lower for typeT in backupList):
                for test in backupList:
                    if test in lower:
                        testType = "SPR - " + test
                        testGroup = 'derived test'
            else:
                unknownTests.append(lower)

        else:
            print(lower)
            input()

    testTypeList.append(testType)
    testGroupList.append(testGroup)
    for testT in [matchedWordsList, candidateScoreList, candidatePreferredList, candidateMatchedList, semTypesList, negatedList, sourcesList, testTextList]:
        while len(testT) < len(firstNameList):
            testT.append('')

goodTests = pd.DataFrame(list(zip(firstNameList, lastNameList, middleNameList, mrnList, dobList, icdList, testTypeList, testGroupList, dateReportedList, matchedWordsList,
                                  semTypesList, testTextList, candidateMatchedList, candidatePreferredList, candidateScoreList, negatedList, sourcesList)),
                         columns = ["First Name", "Last Name", "Middle Name", "MRN", "DOB", 'ICD Code', "Test Type", "Test Group", "Date Reported", "Matched Words",
                                    "Sematic Types", "Test Text", "Candidate Matched", "Candidate Preferred", "Candidate Score", 'Negated', 'Sources'])
goodTests.to_csv("~/Desktop/DeleteMeSoon/BiomarkersForPhizer/AllTestData/AllUnstructResults.csv", index=False)

print(goodTests['Test Type'].value_counts())

print(len(set(mrnList)))

unknownTests = pd.DataFrame(list(zip(unknownTests)), columns = ['Unknown Tests'])
#unknownTests.to_csv("~/Desktop/DeleteMeSoon/BiomarkersForPhizer/AllTestData/UnknownResults.csv", index=False)