import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# Now beginning the sorting out!
pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/March2020HFHS.csv", low_memory=False)

testTypes = []
reports = []

# This is for making sure the lists never get smaller - only for debugging!
storedLen = 0

allTestTypes = []

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
dateReportedList = []
icdCodeList = []
patientIdList = []
reportIdList = []

# These will hold the metamap 4-tuple. We'll move column mapping to another function!
biomarkerResultList = []
conceptResultList = []
numericResultList = []
qualifierResultList = []

# Wrongway tests are those ones that aren't even path reports - distinguised by not having 'patient name' as a field.
# Aberrent tests are those that don't follow expected patterns. We're expecting formatting that we're not finding.
# Failed tests are ones that break either the NLP or this script entirely. The original run (of the 350k tests) will have 0 of these. Keep new ones for analysis!
# Extra tests are those that still have the biomarker in question in the report text by the end.
aberrentTests = []
aberrentReasons = []
wrongwayTests = []
wrongwayReasons = []
extraTests = []
failedTests = []
failedReasons = []

# To avoid typing this out every time for every test, we'll define a method here.
def standardAppends(fname, mname, lname, mrnf, dobf, acc, ttype, sloc, path, dorder, dreport, ttext, ftext, ficd, frid, fpid):
    firstNameList.append(fname)
    middleNameList.append(mname)
    lastNameList.append(lname)
    mrnList.append(mrnf)
    dobList.append(dobf)
    accessionList.append(acc)
    testTypeList.append(ttype)
    sampleLocationList.append(sloc)
    pathologistList.append(path)
    dateOrderedList.append(dorder)
    dateReportedList.append(dreport)
    testTextList.append(ttext)
    fullTextList.append(ftext)
    icdCodeList.append(ficd)
    reportIdList.append(frid)
    patientIdList.append(fpid)

# These values are specific per test. We don't want to persist one sample location between samples. So reset!
def resetDerived():
    global pathologist
    global orderedDate
    global reportedDate
    global sampleLocation
    pathologist = ''
    orderedDate = ''
    reportedDate = ''
    sampleLocation = ''

# Also to avoid re-printing this for each test
def printResults():
    print("THE RESULTS")
    print(firstName)
    print(lastName)
    print(accession)
    print(lower)
    print(fullTest)
    print(results)
    print(lot)
    print(orderedDate)
    print(reportedDate)
    print(sampleLocation)
    print(testType)
    print(testTech)
    print(pathologist)

brcaNames = ['brca1/2 sequencing and full deletions /|duplications only',
             'brca1/2 sequencing and full deletions / duplications|only',
             'brca1/2 sequencing and common deletions /|duplications only',
             'brca1/2 sequencing and common deletions / duplications|only']


totalTests = 0
for x in range(0, len(pathReports['description'])):
#for x in range(0, 1000):
#    try:
    if x % 100 == 0:
        print(x, ' of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    lower = str(pathReports['description'][x]).lower()
    lower = re.sub(' +', ' ', lower)
    splitReport = lower.split('\n')
    # These reports are truncated and don't contain info - NONE have 'her 2' or 'her2' or 'her-2'
    if 'patient name:' not in lower:
        wrongwayTests.append(lower)
        wrongwayReasons.append('no Patient')
        continue
    # We'll pull out the MRN
    try:
        mrnIndex = lower.index("rec.:")
    except Exception as e:
        # There's only one kind without a rec.:, and it's a regadenoson pharmacological stress myocardial perfusion study
        wrongwayTests.append(lower)
        wrongwayReasons.append('no MRN')
        continue
    MRN = lower[mrnIndex + 5:mrnIndex + 14].strip()
    # And the ICD codes - we'll also delete anything that's like a: b:
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

    # We're going to look for anything in 'erprNames', since there are a lot of things these can be called
    if 'brca' in lower:
        # We want to remove all 'test description's, and 'analyte specific reagent's  because they can contain the strings of the biomarkers we're looking for, and they don't matter!
        # Pull these out later if you want the test descriptions!
        while 'test description:' in lower:
            firstInstance = re.search(r"test description:", lower)
            testDescription = lower[firstInstance.start():]
            paragraphBreak = re.search('\n\n', testDescription)
            testDesString = lower[firstInstance.start():firstInstance.start() + paragraphBreak.start()]
            lower = '\n'.join(lower.split(testDesString))

        # Alright, now we're gonna get them.
        barlower = lower.replace('\n', '|').replace('over expression', 'overexpression')
        spacelower = lower.replace('\n', ' ').replace('over expression', 'overexpression')
        lower = lower.replace('\n', '|').replace('over expression', 'overexpression')
        lower = lower.replace(' c. ', ' c.').replace(' p. ', ' p.')
        lower = lower.replace('vous', 'variant of uncertain significance')

        # I'm shifting this from an 'if' to a 'while', so that if there's any errors, we only delete the one section in question, instead of the whole test.
        while any(substring in lower for substring in brcaNames):

            lowestIndex = 10000000
            testName = ''
            for v in brcaNames:
                if v in lower:
                    index = lower.index(v)
                    if index < lowestIndex:
                        lowestIndex = index
                        testName = v
                        testType = testName.replace('|', ' ')

            # Now we proceed
            resetDerived()
            testStarts = []
            testEnds = []
            testType = testName
            testTech = 'pcr'

            testIndex = lower.index(testName)
            fullTest = lower[testIndex-12:]
            if 'pathologist|' in fullTest:
                fullTestEnd = fullTest.index('pathologist|')
                fullTest = fullTest[:fullTestEnd + len('pathologist')]
            elif 'md, s' in fullTest:
                fullTestEnd = fullTest.index('md, s')
                fullTest = fullTest[:fullTestEnd + len('md, s')]
            elif 'phd' in fullTest:
                fullTestEnd = fullTest.index('phd')
                fullTest = fullTest[:fullTestEnd + len('phd')]
            elif 'p.h.d.' in fullTest:
                fullTestEnd = fullTest.index('p.h.d.')
                fullTest = fullTest[:fullTestEnd + len('p.h.d.')]
            elif ', m|' in fullTest:
                fullTestEnd = fullTest.index(', m|')
                fullTest = fullTest[:fullTestEnd + len(', m|')]
            elif 'rdb' in fullTest:
                fullTestEnd = fullTest.index('rdb')
                fullTest = fullTest[:fullTestEnd + len('rdb')]
            else:
                print(lower)
                print("ABERRENT!")
                input()
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:testIndex] + lower[testIndex+len(testName):]
                continue
            testStarts.append(testIndex)
            testEnds.append(testIndex + fullTestEnd)

            if 'date ordered:' in fullTest:
                orderedDate = re.search('date ordered: ', fullTest)
                orderedDateEnd = re.search('date reported: ', fullTest)
                orderedDate = fullTest[orderedDate.start() + len("date ordered: "): orderedDateEnd.start()].strip()
                reportedDate = re.search('date reported: ', fullTest)
                try:
                    reportedDateEnd = re.search('\|', fullTest[reportedDate.start():])
                except Exception as e:
                    aberrentTests.append(fullTest)
                    aberrentReasons.append('dates missing')
                    lower = lower[:testIndex] + lower[testIndex + len(testName):]
                    continue
                try:
                    reportedDate = fullTest[reportedDate.start() + len("date reported: "): reportedDate.start() + reportedDateEnd.start()].strip()
                except Exception as e:
                    aberrentTests.append(fullTest)
                    aberrentReasons.append('dates missing')
                    lower = lower[:testIndex] + lower[testIndex + len(testName):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('brca1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')

                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('brca2')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')

                    lower = lower[:testIndex] + lower[testIndex + len(testName):]
                    continue
                pathologist = re.search('out\*\*\*\|', fullTest)
                pathologist = fullTest[pathologist.start() + len('out***|'):].strip()
                testEnds.append(pathologist.start())

            else:
                orderedDate = ''
                reportedDate = ''
            testSplit = fullTest.split('|')
            pathologist = testSplit[-1]

            # Now let's find all the samples:
            samples = re.finditer('\s[a-z]\:\s', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                sampleLocation = sampleText.index('||')
                sampleLocation = sampleText[sampleText.index(','):sampleLocation].replace('|', ' ')
                while sampleLocation.startswith(','):
                    sampleLocation = sampleLocation[1:]
                sampleLocation = sampleLocation.strip()

                # Some tests have "interpretation: diagnostic interpretation:" let's just cut to the chase and grab the second one if there
                if 'diagnostic interpretation:|' in sampleText:
                    sampleText = sampleText[sampleText.index('diagnostic interpretation') + len('diagnostic interpretation'):]

                # There's a whole forest of 'interpretations' 'results' and other headers
                elif 'results|' in sampleText:
                    sampleText = sampleText[sampleText.index('results|') + len('results|'):]
                    if 'interpretation' in sampleText and (sampleText.startswith('|pathogenic') or sampleText.startswith('pathogenic')):
                        sampleText = sampleText[sampleText.index('interpretation') + len('interpretation'):]

                elif 'interpretation' in sampleText:
                    sampleText = sampleText[sampleText.index('interpretation') + len('interpretation'):]


                # Here we're dealing with the (many) brca reports that have been put off, and the reasons captured in results-comments or report comments
                if 'see results-comments' in sampleText or 'see reference lab' in sampleText:
                    while 'results-comments' in sampleText:
                        sampleText = sampleText[sampleText.index('results-comments') + len('results-comments'):]
                    while 'report comments' in sampleText:
                        sampleText = sampleText[sampleText.index('report comments') + len('report comments'):]
                elif 'see report comments' in sampleText:
                    while 'report comments' in sampleText:
                        sampleText = sampleText[sampleText.index('report comments') + len('report comments'):]

                sampleText = sampleText.strip()
                if sampleText.startswith(':'):
                    sampleText = sampleText[1:]
                while sampleText.startswith('|'):
                    sampleText = sampleText[1:]

                if 'positive for' in sampleText:
                    try:
                        sampleText = sampleText[:sampleText.index(')||') + 1]
                    except:
                        sampleText = sampleText[:sampleText.index('variant gene')]
                else:
                    sampleText = sampleText.replace('||gene', '|gene')
                    sampleText = sampleText[:sampleText.index('||')]

                # sometimes the test name sneaks through
                if 'duplications assays:' in sampleText:
                    sampleText = sampleText[sampleText.index('duplications assays:') + len('duplications assays:'):]

                sampleText = sampleText.replace('|', ' ').strip()
                testType = testType.replace('|', ' ').strip()

                if '(see below for variant of unknown significance)' in sampleText:
                    sampleBit2 = spacelower[spacelower.index('variant of unknown significance gene location transcript cdna protein dp exon af interpretation') +
                                            len('variant of unknown significance gene location transcript cdna protein dp exon af interpretation'):]
                    sampleBit2 = sampleBit2[:sampleBit2.index('note:')]
                    sampleBit2 = sampleBit2.strip()
                    sampleText = sampleText + '|' + sampleBit2

                # At this point, if 'brca' doesn't show up at all in the sample text, it's probably because there were no results. Let's parse out why!
                if 'brca' not in sampleText:
                    if 'this order has been cancelled at the request of the care provider' in sampleText:
                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId, patientId)
                        biomarkerResultList.append('brca1')
                        conceptResultList.append('')
                        numericResultList.append('')
                        qualifierResultList.append('cancelled by care provider')

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId, patientId)
                        biomarkerResultList.append('brca2')
                        conceptResultList.append('')
                        numericResultList.append('')
                        qualifierResultList.append('cancelled by care provider')
                        continue
                    if 'no pathogenic mutations, variants of unknown significance or gross deletion' in sampleText:
                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId, patientId)
                        biomarkerResultList.append('brca1')
                        conceptResultList.append('')
                        numericResultList.append('')
                        qualifierResultList.append('normal results')

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId, patientId)
                        biomarkerResultList.append('brca2')
                        conceptResultList.append('')
                        numericResultList.append('')
                        qualifierResultList.append('normal results')
                        continue
                    if 'please refer to case number' in sampleText:
                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId, patientId)
                        biomarkerResultList.append('brca1')
                        conceptResultList.append('')
                        numericResultList.append('')
                        qualifierResultList.append('results in other report')

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId, patientId)
                        biomarkerResultList.append('brca2')
                        conceptResultList.append('')
                        numericResultList.append('')
                        qualifierResultList.append('results in other report')
                        continue
                    if 'specimen was sent out' in sampleText:
                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId, patientId)
                        biomarkerResultList.append('brca1')
                        conceptResultList.append('')
                        numericResultList.append('')
                        qualifierResultList.append('sent to other lab for testing')

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId, patientId)
                        biomarkerResultList.append('brca2')
                        conceptResultList.append('')
                        numericResultList.append('')
                        qualifierResultList.append('sent to other lab for testing')
                        continue
                sampleSplit = sampleText.split('. ')
                sampleText = ''
                for sam in sampleSplit:
                    if 'brca' in sam:
                        sampleText = sampleText + sam
                linesOfTest = sampleText.split('|')
                for lot in linesOfTest:
                    lot = lot + "\n"
                    lot = lot.replace('(','').replace(')','')
                    # We want to separate out negative results
                    lot = lot.replace('no additional', '. . no additional')
                    if lot == '' or len(lot.strip()) == 0:
                        continue
                    # print(lot)
                    # input()
                    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                    with open(file, 'w') as filetowrite:
                        filetowrite.write(lot)
                    results = metamapstringoutput()
                    # Turn this on to print results
                    # printResults()
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # input()
                    bioList = []
                    conList = []
                    numList = []
                    qualList = []
                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(row['Numeric'])
                        qualResult = ', '.join(row['Qualifier'])
                        if ('p.' in bioResult or 'c.' in bioResult or 'missense' in bioResult) and 'brca' not in bioResult:
                            bioList[-1] = bioList[-1] + ', ' + bioResult
                            conList[-1] = conList[-1] + ', ' + conResult
                            numList[-1] = numList[-1] + ', ' + numResult
                            qualList[-1] = qualList[-1] + ', ' + qualResult
                        else:
                            bioList.append(bioResult)
                            conList.append(conResult)
                            numList.append(numResult)
                            qualList.append(qualResult)

                    for u in range(0, len(bioList)):
                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                        biomarkerResultList.append(bioList[u])
                        conceptResultList.append(conList[u])
                        numericResultList.append(numList[u])
                        qualifierResultList.append(qualList[u])

            # Now we're going to snip all those tests out of the overall report!
            sampleLocation = ''
            testStarts.reverse()
            testEnds.reverse()
            #print(testStarts)
            #print(testEnds)
            #print(lower)
            #input()
            for h in range(0, len(testStarts)):
                lower = lower[:testStarts[h]] + lower[testEnds[h]:]

            if 'brca' in lower:
                extraTests.append(lower)


wrongTests = pd.DataFrame(list(zip(extraTests)), columns=['text'])
wrongTests.to_csv("~/Desktop/LatestNLP/Unstructured Results/ExtrasOfBRCA.csv", index=False)

wrongwayTest = pd.DataFrame(list(zip(wrongwayTests, wrongwayReasons)), columns=['test', 'reason'])
wrongwayTest.to_csv("~/Desktop/LatestNLP/Unstructured Results/MalformedOfBRCA.csv", index=False)

aberrentTest = pd.DataFrame(list(zip(aberrentTests, aberrentReasons)), columns=['test', 'reason'])
aberrentTest.to_csv("~/Desktop/LatestNLP/Unstructured Results/ErrorsOfBRCA.csv", index=False)

failed = pd.DataFrame(list(zip(failedTests, failedReasons)), columns=['text', 'reason'])
failed.to_csv("~/Desktop/LatestNLP/Unstructured Results/FailedOfBRCA.csv", index=False)

rawResults = pd.DataFrame(list(zip(biomarkerResultList, conceptResultList, numericResultList, qualifierResultList,
                                   firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionList, testTypeList, sampleLocationList,
                                   pathologistList, dateOrderedList, dateReportedList, testTextList, fullTextList, icdCodeList, patientIdList, reportIdList)),
                          columns=['biomarker', 'concept', 'numeric', 'qualifier', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accession', 'testType',
                                   'sampleLocation', 'pathologist', 'dateOrdered', 'dateReported', 'testText', 'fullText', 'icdCode', 'patientId', 'reportId'])
rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/RawOfBRCA.csv", index=False)
