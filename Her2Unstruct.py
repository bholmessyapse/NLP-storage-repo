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

# Use this to truncate huge files for quicker testing
#pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020.csv", low_memory=False)
#truncated = pathReports.iloc[5000000:]
#truncated.to_csv("~/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020.csv", index=False)
#print("LOADED!")
#input()

# The lists for the file
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


storedLen = 0
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

for x in range(0, len(pathReports['description'])):
#for x in range(0, 10000):
#    try:
    if x % 100 == 0:
        print(x, ' of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    # if reportId != '25be56ef-b1a0-4181-8382-3cec8f718d26':
    #     continue
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

    if 'her2' in lower or 'her-2' in lower or 'her 2' in lower:

        # We want to remove all 'test description's, because they can contain the strings of the biomarkers we're looking for, and they don't matter!
        # Pull these out later if you want the test descriptions!
        while 'test description:' in lower:
            firstInstance = re.search(r"test description:", lower)
            testDescription = lower[firstInstance.start():]
            paragraphBreak = re.search('\n\n', testDescription)
            testDesString = lower[firstInstance.start():firstInstance.start() + paragraphBreak.start()]
            lower = '\n'.join(lower.split(testDesString))

        # Alright, now we're gonna get them.
        barlower = lower.replace('\n', '|').replace('her-2', 'her2').replace('over expression', 'overexpression')
        spacelower = lower
        lower = lower.replace('\n', '|').replace('her-2', 'her2').replace('over expression', 'overexpression')

        # I'm shifting this from an 'if' to a 'while', so that if there's any errors, we only delete the one section in question, instead of the whole test.
        while 'her2/ neu protein assay (ihc)' in lower:
            resetDerived()
            print("her2/ new protein assay")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            testType = 'her2/neu protein assay (ihc)'
            testTech = 'ihc'
            opener = lower.index('her2/ neu protein assay (ihc)')

            fullTest = lower[opener:]
            if 'pathologist|' in fullTest:
                fullTestEnd = fullTest.index('pathologist|')
                fullTest = fullTest[:fullTestEnd + len('pathologist')]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener+len('her2/neu protein assay (ihc)'):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len('her2/neu protein assay (ihc)'):]
                    continue
                try:
                    reportedDate = fullTest[reportedDate.start() + len("date reported: "): reportedDate.start() + reportedDateEnd.start()].strip()
                except Exception as e:
                    aberrentTests.append(fullTest)
                    aberrentReasons.append('dates missing')
                    lower = lower[:opener] + lower[opener + len('her2/neu protein assay (ihc)'):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('her2')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len('her2/neu protein assay (ihc)'):]
                    continue
                pathologist = re.search('out\*\*\*\|', fullTest)
                pathologist = fullTest[pathologist.start() + len('out***|'):].strip()


            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('\|[a-z]\.\s', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                try:
                    sampleEnd = sampleText.index(': ')
                except Exception as e:
                    continue
                # We'll pull out the location of the sample here
                sampleLocation = sampleText[:sampleEnd]
                sampleText = sampleText[sampleEnd + 2:]
                # Now we separate the two types!
                if 'ki-67' in sampleText:
                    sampleTextStart = sampleText.index('mib1')
                    sampleTextEnd = sampleText.index('|||')
                    sampleText = sampleText[sampleTextStart:sampleTextEnd]
                    sampleText = sampleText.replace('|', ' ')
                else:
                    try:
                        sampleTextStart = sampleText.index('interpretation: ')
                    except Exception as e:
                        sampleTextStart = 0
                    try:
                        sampleTextEnd = sampleText.index('results: ')
                    except Exception as e:
                        if 'protein.' in sampleText:
                            sampleTextEnd = sampleText.index('protein.') + len('protein.')
                        else:
                            aberrentTests.append('sampleText')
                            aberrentReasons.append('no results')
                            continue
                    sampleText = sampleText[sampleTextStart:sampleTextEnd]
                    sampleText = sampleText.replace('|', ' ')
                linesOfTest = sampleText.split('|')
                for lot in linesOfTest:
                    lot = lot + "\n"
                    if lot == '' or len(lot.strip()) == 0:
                        continue
                    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                    with open(file, 'w') as filetowrite:
                        filetowrite.write(lot)
                    results = metamapstringoutput()
                    # Turn this on to print results
                    #printResults()
                    #input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()
                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(row['Numeric'])
                        qualResult = ', '.join(row['Qualifier'])

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                        biomarkerResultList.append(bioResult)
                        conceptResultList.append(conResult)
                        numericResultList.append(numResult)
                        qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            sampleLocation = ''
            testStarts.reverse()
            testEnds.reverse()
            for h in range(0, len(testStarts)):
                lower = lower[:testStarts[h]] + lower[testEnds[h]:]

        while 'her2/ neu gene amplification (fish) assay' in lower:
            resetDerived()
            print("her2/ neu gene amplification (fish) assay")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            testType = 'her2/neu gene amplification (fish) assay'
            testTech = 'fish'
            opener = lower.index('her2/ neu gene amplification (fish) assay')
            testStart = opener
            fullTest = lower[testStart:]
            if 'pathologist|' in fullTest:
                fullTestEnd = fullTest.index('pathologist|')
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len('her2/ neu gene amplification (fish) assay'):]
                continue
            testStarts.append(testStart)
            testEnds.append(testStart + fullTestEnd)
            fullTest = fullTest[:fullTestEnd + len('pathologist')]
            if 'date ordered:' in fullTest:
                if 'date reported:' in fullTest:
                    orderedDate = re.search('date ordered:', fullTest)
                    reportedDateText = 'date reported:'
                    orderedDateEnd = re.search('date reported:', fullTest)
                    reportedDate = re.search('date reported:', fullTest)
                elif 'status:' in fullTest:
                    orderedDate = re.search('date ordered:', fullTest)
                    reportedDateText = 'status:'
                    orderedDateEnd = re.search('status:', fullTest)
                    reportedDate = re.search('status:', fullTest)
                reportedDateEnd = re.search('\|', fullTest[reportedDate.start():])
                try:
                    orderedDate = fullTest[orderedDate.start() + len('date ordered:'): orderedDateEnd.start()].strip()
                    reportedDate = fullTest[reportedDate.end(): reportedDate.start() + reportedDateEnd.start()].strip()
                    while orderedDate.endswith('|'):
                        orderedDate = orderedDate[:-1]
                    while reportedDate.endswith(':') or reportedDate.endswith('|'):
                        reportedDate = reportedDate[:-1]
                except:
                    aberrentTests.append(fullTest)
                    aberrentReasons.append('no date')
                    lower = lower.replace('her2/neu gene amplification (fish) assay', '')
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('her2')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len('her2/ neu gene amplification (fish) assay'):]
                    continue
                pathologist = re.search('out\*\*\*\|', fullTest)
                pathologist = fullTest[pathologist.start() + len('out***|'):].strip()

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('\|[a-z]:\s', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                try:
                    sampleEnd = sampleText.index('|nuc')
                except Exception as e:
                    continue
                # We'll pull out the location of the sample here
                sampleLocation = sampleText[:sampleEnd]
                sampleText = sampleText[sampleEnd + 2:]
                # Now we separate the two types!
                if 'the results' not in sampleText:
                    sampleTextStart = sampleText.index('nuc')
                    try:
                        sampleTextEnd = sampleText.index('a her2 to')
                    except Exception as e:
                        sampleTextEnd = sampleText.index('her2 to chromosome')
                    sampleText = sampleText[sampleTextStart:sampleTextEnd].replace('results-comments', '')
                    sampleText = sampleText.replace('per asco/cap guidelines, the average her2', '')
                    sampleText = sampleText.replace('signal falls in the equivocal range (>4 and <6).', '')
                    sampleText = sampleText.replace('the number of her2', '')
                    sampleText = sampleText.replace('signals per cell is >4 and <6 signals.', '')
                    if 'see comment' in sampleText:
                        firstBit = sampleText[:sampleText.index('see comment')]
                        secondBit = sampleText[sampleText.index('her2 duplication'):]
                        sampleText = firstBit + ' ' + secondBit
                    elif 'comment:' in sampleText:
                        firstBit = sampleText[:sampleText.index('comment:')]
                        secondBit = sampleText[sampleText.index('her2 duplication'):]
                        sampleText = firstBit + ' ' + secondBit

                else:
                    if 'nuc' not in sampleText:
                        print("NO NUC")
                        #input()
                        continue
                    sampleTextStart = sampleText.index('nuc')
                    sampleTextEnd = sampleText.index('the results')
                    sampleText1 = sampleText[sampleTextStart:sampleTextEnd].replace('results-comments', '')
                    sampleTextStart2 = sampleText.index('the ratio of')
                    sampleTextEnd2 = sampleText.index('a her2 to')
                    sampleText2 = sampleText[sampleTextStart2:sampleTextEnd2].replace('results-comments', '').strip()
                    sampleText = sampleText1 + ' ' + sampleText2
                    sampleText = sampleText.replace('per asco/cap guidelines, the average her2', '')
                    sampleText = sampleText.replace('signal falls in the equivocal range (>4 and <6).', '')
                    sampleText = sampleText.replace('the number of her2', '')
                    sampleText = sampleText.replace('signals per cell is >4 and <6 signals.', '')
                    if 'see comment' in sampleText:
                        firstBit = sampleText[:sampleText.index('see comment')]
                        secondBit = sampleText[sampleText.index('her2 duplication'):]
                        sampleText = firstBit + ' ' + secondBit
                    elif 'comment:' in sampleText:
                        firstBit = sampleText[:sampleText.index('comment:')]
                        secondBit = sampleText[sampleText.index('her2 duplication'):]
                        sampleText = firstBit + ' ' + secondBit

                sampleText = sampleText.replace('|', ' . ')
                sampleText = sampleText.replace(' . chromosome 17', ' . . chromosome 17')
                sampleText = sampleText.replace(' . aneuploidy of', ' . . aneuploidy of')
                linesOfTest = sampleText.split('|')
                for lot in linesOfTest:
                    lot = lot + "\n"
                    if lot == '' or len(lot.strip()) == 0:
                        continue
                    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                    with open(file, 'w') as filetowrite:
                        filetowrite.write(lot)
                    results = metamapstringoutput()
                    # Turn this on to print results
                    # printResults()
                    # #input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()
                    ratioGenes = []
                    signalRatio = ''
                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(row['Numeric'])
                        qualResult = ', '.join(row['Qualifier'])

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                        biomarkerResultList.append(bioResult)
                        conceptResultList.append(conResult)
                        numericResultList.append(numResult)
                        qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            sampleLocation = ''
            testStarts.reverse()
            testEnds.reverse()
            for r in range(0, len(testStarts)):
                lower = lower[:testStarts[r]] + lower[testEnds[r]:]

        while 'her2/ neu (sish) gene amplification assay' in lower:
            resetDerived()
            print("her2/ neu gene amplification (sish) assay")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            testType = 'her2/ neu (sish) gene amplification assay'
            testTech = 'sish'
            opener = lower.index('her2/ neu (sish) gene amplification assay')
            testStart = opener
            fullTest = lower[testStart:]
            if 'pathologist|' in fullTest:
                fullTestEnd = re.search('pathologist\|', fullTest)
                testStarts.append(testStart)
                testEnds.append(testStart + fullTestEnd.start())
            else:
                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                patientId)
                biomarkerResultList.append('her2')
                conceptResultList.append('')
                numericResultList.append('')
                qualifierResultList.append('pending')

                ###
                # TEMP
                ###
                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                patientId)
                biomarkerResultList.append('her2')
                conceptResultList.append('')
                numericResultList.append('')
                qualifierResultList.append('pending')
                lower = lower[:opener] + lower[opener + len('her2/ neu (sish) gene amplification assay'):]
                continue
            fullTest = fullTest[:fullTestEnd.start() + len('pathologist')]
            if 'date ordered:' in fullTest:
                if 'date reported:' in fullTest:
                    orderedDate = re.search('date ordered:', fullTest)
                    reportedDateText = 'date reported:'
                    orderedDateEnd = re.search('date reported:', fullTest)
                    reportedDate = re.search('date reported:', fullTest)
                elif 'status:' in fullTest:
                    orderedDate = re.search('date ordered:', fullTest)
                    reportedDateText = 'status:'
                    orderedDateEnd = re.search('status:', fullTest)
                    reportedDate = re.search('status:', fullTest)
                reportedDateEnd = re.search('\|', fullTest[reportedDate.start():])
                try:
                    orderedDate = fullTest[orderedDate.start() + len('date ordered:'): orderedDateEnd.start()].strip()
                    reportedDate = fullTest[reportedDate.end(): reportedDate.start() + reportedDateEnd.start()].strip()
                    while orderedDate.endswith('|'):
                        orderedDate = orderedDate[:-1]
                    while reportedDate.endswith(':') or reportedDate.endswith('|'):
                        reportedDate = reportedDate[:-1]
                except:
                    aberrentTests.append(fullTest)
                    aberrentReasons.append('no date')
                    lower = lower[:opener] + lower[opener + len('her2/ neu (sish) gene amplification assay'):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('her2')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len('her2/ neu (sish) gene amplification assay'):]
                    continue
                pathologist = re.search('out\*\*\*\|', fullTest)
                pathologist = fullTest[pathologist.start() + len('out***|'):].strip()

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('\|[a-z]:\s', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                try:
                    sampleEnd = sampleText.index(')|')
                except Exception as e:
                    continue
                # We'll pull out the location of the sample here
                sampleLocation = sampleText[:sampleEnd] + ')'
                sampleText = sampleText[sampleEnd + 2:]
                # Now we separate the two types!
                if 'the results' not in sampleText:
                    if 'nuc' not in sampleText:
                        aberrentTests.append(sampleText)
                        aberrentReasons.append('no nuc')
                        continue
                    sampleTextStart = sampleText.index('nuc')
                    try:
                        sampleTextEnd = sampleText.index('a her2 to')
                    except Exception as e:
                        try:
                            sampleTextEnd = sampleText.index('her2 to chromosome')
                        except Exception as e:
                            sampleTextEnd = sampleText.index('results-comments')
                    sampleText = sampleText[sampleTextStart:sampleTextEnd].replace('results-comments', '')
                    sampleText = sampleText.replace('per asco/cap guidelines, the average her2', '')
                    sampleText = sampleText.replace('signal falls in the equivocal range (>4 and <6).', '')
                    sampleText = sampleText.replace('the number of her2', '')
                    sampleText = sampleText.replace('signals per cell is >4 and <6 signals.', '')
                    if 'see comment' in sampleText:
                        firstBit = sampleText[:sampleText.index('see comment')]
                        secondBit = sampleText[sampleText.index('her2 duplication'):]
                        sampleText = firstBit + ' ' + secondBit
                    elif 'comment:' in sampleText:
                        firstBit = sampleText[:sampleText.index('comment:')]
                        secondBit = sampleText[sampleText.index('her2 duplication'):]
                        sampleText = firstBit + ' ' + secondBit

                else:
                    if 'nuc' not in sampleText:
                        aberrentTests.append(sampleText)
                        aberrentReasons.append('no nuc')
                        continue
                    sampleTextStart = sampleText.index('nuc')
                    sampleTextEnd = sampleText.index('the results')
                    sampleText1 = sampleText[sampleTextStart:sampleTextEnd].replace('results-comments', '')
                    sampleTextStart2 = sampleText.index('the ratio of')
                    sampleTextEnd2 = sampleText.index('a her2 to')
                    sampleText2 = sampleText[sampleTextStart2:sampleTextEnd2].replace('results-comments', '').strip()
                    sampleText = sampleText1 + ' ' + sampleText2
                    sampleText = sampleText.replace('per asco/cap guidelines, the average her2', '')
                    sampleText = sampleText.replace('signal falls in the equivocal range (>4 and <6).', '')
                    sampleText = sampleText.replace('the number of her2', '')
                    sampleText = sampleText.replace('signals per cell is >4 and <6 signals.', '')
                    if 'see comment' in sampleText:
                        firstBit = sampleText[:sampleText.index('see comment')]
                        secondBit = sampleText[sampleText.index('her2 duplication'):]
                        sampleText = firstBit + ' ' + secondBit
                    elif 'comment:' in sampleText:
                        firstBit = sampleText[:sampleText.index('comment:')]
                        secondBit = sampleText[sampleText.index('her2 duplication'):]
                        sampleText = firstBit + ' ' + secondBit

                sampleText = sampleText.replace('|', ' . ')
                sampleText = sampleText.replace(' . chromosome 17', ' . . chromosome 17')
                sampleText = sampleText.replace(' . aneuploidy of', ' . . aneuploidy of')
                linesOfTest = sampleText.split('|')
                for lot in linesOfTest:
                    lot = lot + "\n"
                    if lot == '' or len(lot.strip()) == 0:
                        continue
                    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                    with open(file, 'w') as filetowrite:
                        filetowrite.write(lot)
                    results = metamapstringoutput()
                    # Turn this on to print results
                    # printResults()
                    # #input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()
                    ratioGenes = []
                    signalRatio = ''
                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(row['Numeric'])
                        qualResult = ', '.join(row['Qualifier'])

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                        biomarkerResultList.append(bioResult)
                        conceptResultList.append(conResult)
                        numericResultList.append(numResult)
                        qualifierResultList.append(qualResult)
            # Now we're going to snip all those tests out of the overall report!
            sampleLocation = ''
            testStarts.reverse()
            testEnds.reverse()
            if len(testStarts) == len(testEnds):
                for r in range(0, len(testStarts)):
                    lower = lower[:testStarts[r]] + lower[testEnds[r]:]

        while 'gastroesophageal biopsy her2/neu summary' in lower:
            resetDerived()
            #input()
            testStarts = []
            testEnds = []
            testType = 'gastroesophageal biopsy her2/neu summary'
            testTech = 'ihc'
            testStart = lower.index('gastroesophageal biopsy her2/neu summary')
            # We're pulling out the full segment here so we can get the pathologist and dates
            # I'm assuming that the sample is the one that contains this summary in it!
            samples = re.finditer(' [a-z]:\s', lower)
            sampleSize = sum(1 for _ in re.finditer(' [a-z]:\s', lower))
            if sampleSize > 0:
                sampStart = 0
                # We want the latest sample that's before the start of our test
                for sam in samples:
                    if sampStart < sam.end() < testStart:
                        sampStart = sam.end()
                sampleLocation = lower[sampStart:]
                sampleLocation = sampleLocation[:sampleLocation.index('|')]
                fullTest = lower[testStart - 100:]
            else:
                # If we can't find any samples, we'll just go from the start of the test
                fullTest = lower
                sampStart = lower.index('gastroesophageal biopsy her2/neu summary') + len('gastroesophageal biopsy her2/neu summary')
            fullTestEnd = re.search('pathologist\|', fullTest)
            testStarts.append(testStart)
            testEnds.append(testStart + fullTestEnd.start())
            fullTest = fullTest[:fullTestEnd.start() + len('pathologist')]
            if 'date ordered:' in fullTest:
                orderedDate = re.search('date ordered: ', fullTest)
                orderedDateEnd = re.search('date reported: ', fullTest)
                orderedDate = fullTest[orderedDate.start() + len("date ordered: "): orderedDateEnd.start()].strip()
                reportedDate = re.search('date reported: ', fullTest)
                reportedDateEnd = re.search('\|', fullTest[reportedDate.start():])
                reportedDate = fullTest[reportedDate.start() + len("date reported: "): reportedDate.start() + reportedDateEnd.start()].strip()
            else:
                orderedDate = ''
                reportedDate = ''
            # We'll also pull out the name of the pathologist
            signOut = re.search('out\*?', fullTest)
            signOutEnd = re.search('pathologist', fullTest[signOut.start():])
            pathologist = fullTest[signOut.start() + len('out***|'):].strip()

            # Just a little normalization
            testPart = lower[testStart:]
            testEnd = re.search('\)', testPart)
            testEnd = testEnd.start()
            testPart = testPart[len('gastroesophageal biopsy her2/neu summary '):testEnd + 1]
            testPart = testPart.strip()
            testPart = testPart.replace('|interpretation:', 'interpretation: her2').replace('greater than ', '>').replace('less than', '<')
            testPart = testPart.replace('|', ' ')
            linesOfTest = testPart.split('|')
            for lot in linesOfTest:
                lot = lot + "\n"
                if lot == '' or len(lot.strip()) == 0:
                    continue
                file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                with open(file, 'w') as filetowrite:
                    filetowrite.write(lot)
                results = metamapstringoutput()
                # Turn this on to print results
                # printResults()
                # #input()
                # Turn this on to look at the whole test
                # print(spacelower)
                # #input()
                for index, row in results.iterrows():
                    bioResult = ', '.join(row['Biomarker'])
                    conResult = ', '.join(row['Concept'])
                    numResult = ', '.join(row['Numeric'])
                    qualResult = ', '.join(row['Qualifier'])

                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append(bioResult)
                    conceptResultList.append(conResult)
                    numericResultList.append(numResult)
                    qualifierResultList.append(qualResult)
                    bioResult = ''
                    conResult = ''
                    numResult = ''
                    qualResult = ''

            # Now we're going to snip all those tests out of the overall report!
            testStarts.reverse()
            testEnds.reverse()
            for w in range(0, len(testStarts)):
                lower = lower[:testStarts[w]] + lower[testEnds[w]:]

        while 'her2 (results' in lower:
            resetDerived()
            print("her2 (results")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            # Get the next ':'
            testPart = lower.index('her2 (results')
            testPart = lower[testPart:]
            while testPart.index('|') < testPart.index(':'):
                ind = testPart.index('|')
                testPart = testPart[:ind] + ' ' + testPart[ind + 1:]
            testPart = testPart[:testPart.index('|')]
            testStarts.append(lower.index('her2 (results'))
            testEnds.append(lower.index('her2 (results') + len(testPart))
            testType = testTypeOrig
            testTech = ''
            testStart = re.search('her2 \(results', lower)
            # We're pulling out the full segment here so we can get the pathologist and dates
            testStart = testStart.start()
            # I'm assuming that the sample is the one that contains this summary in it!
            samples = re.finditer(' [a-z]:\s', lower)
            sampStart = 0
            # We want the latest sample that's before the start of our test
            for sam in samples:
                if sam.end() > sampStart and sam.end() < testStart:
                    sampStart = sam.end()
            sampleLocation = lower[sampStart:]
            sampleLocation = sampleLocation[:sampleLocation.index('|')]
            testPart = 'her2 ' + testPart[testPart.index(':') + 1:]
            linesOfTest = testPart.split('|')

            for lot in linesOfTest:
                lot = lot + "\n"
                if lot == '' or len(lot.strip()) == 0:
                    continue
                file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                with open(file, 'w') as filetowrite:
                    filetowrite.write(lot)
                results = metamapstringoutput()
                # Turn this on to print results
                # printResults()
                # #input()
                # Turn this on to look at the whole test
                # print(spacelower)
                # #input()
                for index, row in results.iterrows():
                    bioResult = ', '.join(row['Biomarker'])
                    conResult = ', '.join(row['Concept'])
                    numResult = ', '.join(row['Numeric'])
                    qualResult = ', '.join(row['Qualifier'])

                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append(bioResult)
                    conceptResultList.append(conResult)
                    numericResultList.append(numResult)
                    qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            # Now remove that title from the report!
            lower = lower[:lower.index('her2 (results')] + lower[lower.index('her2 (results')+len('her2 (results'):]

        while 'submitted her2 immunostain' in lower:
            resetDerived()
            print("submitted her2 immunostain")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            # Get the next ':'
            testPart = lower.index('submitted her2 immunostain')
            testPart = lower[testPart:]
            testPart = testPart[:testPart.index('staff pathologist') + len('staff pathologist')]
            pathologist = re.search('out\*\*\*\|', fullTest)
            pathologist = fullTest[pathologist.start() + len('out***|'):].strip()
            testType = testTypeOrig
            testStarts.append(lower.index('submitted her2 immunostain'))
            testEnds.append(lower.index('submitted her2 immunostain') + + len(testPart))
            testTech = ''
            testStart = re.search('submitted her2 immunostain', lower)
            # We're pulling out the full segment here so we can get the pathologist and dates
            testStart = testStart.start()
            # I'm assuming that the sample is the one that contains this summary in it!
            samples = re.finditer(' [a-z]:\s', lower)
            sampStart = 0
            # We want the latest sample that's before the start of our test
            for sam in samples:
                if sam.end() > sampStart and sam.end() < testStart:
                    sampStart = sam.end()
            sampleLocation = lower[sampStart:]
            sampleLocation = sampleLocation[:sampleLocation.index('|')]
            testPart = testPart[:testPart.index('|')]
            linesOfTest = testPart.split('|')

            for lot in linesOfTest:
                lot = lot + "\n"
                if lot == '' or len(lot.strip()) == 0:
                    continue
                file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                with open(file, 'w') as filetowrite:
                    filetowrite.write(lot)
                results = metamapstringoutput()
                # Turn this on to print results
                # printResults()
                # #input()
                # Turn this on to look at the whole test
                # print(spacelower)
                # #input()
                for index, row in results.iterrows():
                    bioResult = ', '.join(row['Biomarker'])
                    conResult = ', '.join(row['Concept'])
                    numResult = ', '.join(row['Numeric'])
                    qualResult = ', '.join(row['Qualifier'])

                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append(bioResult)
                    conceptResultList.append(conResult)
                    numericResultList.append(numResult)
                    qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            # Now remove that title from the report!
            lower = lower[:lower.index('submitted her2 immunostain')] + lower[lower.index('submitted her2 immunostain')+len('submitted her2 immunostain'):]


        while 'in situ hybridization (fish or cish) for her2' in lower:
            resetDerived()
            print("in situ hybridization (fish or cish)")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            # Get the next ':'
            testPart = lower.index('in situ hybridization (fish or cish) for her2') + len('in situ hybridization (fish or cish) for her2')
            testPart = lower[testPart:]
            testPart = testPart[:testPart.index('(')]
            pathologist = ''
            testType = testTypeOrig
            testStarts.append(lower.index('in situ hybridization (fish or cish) for her2'))
            testEnds.append(lower.index('in situ hybridization (fish or cish) for her2') + len('in situ hybridization (fish or cish) for her2') + len(testPart))
            testTech = 'fish or cish'
            testStart = re.search('in situ hybridization \(fish or cish\) for her2', lower)
            # We're pulling out the full segment here so we can get the pathologist and dates
            testStart = testStart.start()
            # I'm assuming that the sample is the one that contains this summary in it!
            samples = re.finditer(' [a-z]:\s', lower)
            sampStart = 0
            # We want the latest sample that's before the start of our test
            for sam in samples:
                if sam.end() > sampStart and sam.end() < testStart:
                    sampStart = sam.end()
            sampleLocation = lower[sampStart:]
            sampleLocation = sampleLocation[:sampleLocation.index('|')]
            testPart = 'her2' + testPart
            testPart = testPart.replace('amplified', 'amplification')
            linesOfTest = testPart.split('|')
            for index, row in results.iterrows():
                bioResult = ', '.join(row['Biomarker'])
                conResult = ', '.join(row['Concept'])
                numResult = ', '.join(row['Numeric'])
                qualResult = ', '.join(row['Qualifier'])

                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                patientId)
                biomarkerResultList.append(bioResult)
                conceptResultList.append(conResult)
                numericResultList.append(numResult)
                qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            # Now remove that title from the report!
            lower = lower[:lower.index('in situ hybridization (fish or cish) for her2')] + lower[lower.index('in situ hybridization (fish or cish) for her2')+len('in situ hybridization (fish or cish) for her2'):]

        while 'her2/neu is negative (' in lower or 'her2/neu is positive (' in lower or 'her2/neu is equivocal (' in lower:
            resetDerived()
            print("HER2 IS A THING PAREN")
            testStarts = []
            testEnds = []
            testPart = lower.index('her2/neu is')
            testStarts.append(testPart)
            testPart = lower[testPart:]
            if 'staff pathologist' not in testPart:
                testPart = testPart[:testPart.index('||') + len('||')]
            else:
                testPart = testPart[:testPart.index('staff pathologist') + len('staff pathologist')]
            testEnds.append(lower.index('her2/neu is') + len(testPart))
            fullTest = testPart
            sampleText = testPart
            pathologist = re.search('out\*\*\*\|', testPart)
            if not pathologist:
                pathologist = ''
            else:
                pathologist = testPart[pathologist.start() + len('out***|'):].strip()
                pathologist = pathologist.split('|')
                realPathologist = ''
                for p in pathologist:
                    if 'pathologist' in p:
                        pathologist2 = p
                pathologist = p
            testPart = testPart[testPart.index('is ') + len('is '):testPart.index('(')]
            sampleLocation = ''
            testType = 'Clinical History'
            testTech = ''
            orderedDate = ''
            reportedDate = ''
            standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                            patientId)
            biomarkerResultList.append('her2')
            conceptResultList.append('presence')
            numericResultList.append('')
            qualifierResultList.append(testPart)

            ###
            # TEMP
            ###
            standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                            patientId)
            biomarkerResultList.append('her2')
            conceptResultList.append('presence')
            numericResultList.append('')
            qualifierResultList.append(testPart)

            # Now we're going to snip all those tests out of the overall report!
            testStarts.reverse()
            testEnds.reverse()
            for d in range(0, len(testStarts)):
                lower = lower[:testStarts[d]] + lower[testEnds[d]:]

        while 'her2/neu is negative ' in lower or 'her2/neu is positive ' in lower or 'her2/neu is equivocal ' in lower:
            resetDerived()
            print("HER2 IS A THING NO PAREN")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            testPart = lower.index('her2/neu is')
            testStarts.append(testPart)
            testPart = lower[testPart:]
            testPart = testPart[:testPart.index('staff pathologist') + len('staff pathologist')]
            testEnds.append(lower.index('her2/neu is') + len(testPart))
            fullTest = testPart
            if 'out***' in testPart:
                pathologist = re.search('out\*\*\*\|', testPart)
                pathologist = testPart[pathologist.start() + len('out***|'):].strip()
            else:
                testSplit = testPart.split('|')
                for ts in testSplit:
                    if 'staff pathologist' in ts:
                        pathologist = ts
            testPart = testPart[testPart.index('is ') + len('is '):testPart.index('|')]

            sampleLocation = ''
            testType = testTypeOrig
            testTech = ''
            orderedDate = ''
            reportedDate = ''
            linesOfTest = testPart.split('|')
            for lot in linesOfTest:
                lot = lot + "\n"
                if lot == '' or len(lot.strip()) == 0:
                    continue
                file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                with open(file, 'w') as filetowrite:
                    filetowrite.write(lot)
                results = metamapstringoutput()
                # Turn this on to print results
                # printResults()
                # #input()
                # Turn this on to look at the whole test
                # print(spacelower)
                # #input()
                for index, row in results.iterrows():
                    bioResult = ', '.join(row['Biomarker'])
                    conResult = ', '.join(row['Concept'])
                    numResult = ', '.join(row['Numeric'])
                    qualResult = ', '.join(row['Qualifier'])

                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append(bioResult)
                    conceptResultList.append(conResult)
                    numericResultList.append(numResult)
                    qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            # Now remove that title from the report!
            lower = lower[:lower.index('her2/neu is')] + lower[lower.index('her2/neu is')+len('her2/neu is'):]

        while 'her2/neu expression status:' in lower:
            resetDerived()
            print('HER2/NEU EXPRESSION STATUS:')
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            testPart = lower.index('her2/neu expression status:')
            testStarts.append(testPart)
            testPart = lower[testPart:]
            testPart = testPart[:testPart.index('staff pathologist') + len('staff pathologist')]
            fullTest = testPart
            sampleText = testPart
            if 'out***' in testPart:
                pathologist = re.search('out\*\*\*\|', testPart)
                testText = 'out***|'
            elif 'signed out by' in testPart:
                pathologist = re.search('signed out by', testPart)
                testText = 'signed out by'
            pathologist = testPart[pathologist.start() + len(testText):].strip()
            pathologist = pathologist.replace('|', ' ')
            if '***' in pathologist:
                pathologist = pathologist[:pathologist.index('***')]
            testPart = testPart[testPart.index('status: ') + len('status: '):testPart.index('|')]
            testEnds.append(lower.index('her2/neu expression status:') + len('her2/neu expression status:') + len(testPart))
            sampleLocation = ''
            testType = 'Additional Findings'
            testTech = ''
            orderedDate = ''
            reportedDate = ''
            if testPart in ['positive', 'negative', 'equivocal', 'pending']:
                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                patientId)
                biomarkerResultList.append('her2')
                conceptResultList.append('presence')
                numericResultList.append('')
                qualifierResultList.append(testPart)
                ###
                # TEMP
                ###
                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                patientId)
                biomarkerResultList.append('her2')
                conceptResultList.append('presence')
                numericResultList.append('')
                qualifierResultList.append(testPart)
            else:
                testPart = 'her2 ' + testPart
                linesOfTest = testPart.split('|')
                for lot in linesOfTest:
                    lot = lot + "\n"
                    if lot == '' or len(lot.strip()) == 0:
                        continue
                    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                    with open(file, 'w') as filetowrite:
                        filetowrite.write(lot)
                    results = metamapstringoutput()
                    # Turn this on to print results
                    # printResults()
                    # #input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()
                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(row['Numeric'])
                        qualResult = ', '.join(row['Qualifier'])

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                        biomarkerResultList.append(bioResult)
                        conceptResultList.append(conResult)
                        numericResultList.append(numResult)
                        qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            # Now remove that title from the report!
            lower = lower[:lower.index('her2/neu expression status:')] + lower[lower.index('her2/neu expression status:')+len('her2/neu expression status:'):]

        while 'her2 ihc:' in lower or ('|her2:' in lower and 'ratio of|her2:' not in lower) or 'her2-neu:' in lower:
            resetDerived()
            print("her2 ihc")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            if 'her2 ihc:' in lower and '|her2:' in lower:
                if lower.index('her2 ihc:') < lower.index('|her2:'):
                    startText = 'her2 ihc:'
                else:
                    startText = '|her2:'
            elif 'her2 ihc:' in lower:
                startText = 'her2 ihc:'
            elif 'her2-neu:' in lower:
                startText = 'her2-neu:'
            else:
                startText = '|her2:'
            testPart = lower.index(startText)
            testStarts.append(testPart)
            testPart = lower[testPart:]
            if 'pathologist' not in testPart:
                aberrentTests.append(testPart)
                lower = lower + "ABERRENT"
                aberrentReasons.append('no pathologist')
                lower = lower.replace(startText, '')
                continue
            testPart = testPart[:testPart.index('staff pathologist') + len('staff pathologist')]
            try:
                testEnds.append(lower.index(startText) + len(testPart))
            except:
                aberrentTests.append(lower)
                lower = lower + "ABERRENT"
                aberrentReasons.append('no pathologist')
                lower = lower.replace('startText', '')
                continue
            fullTest = testPart
            pathologist = re.search('out\*\*\*\|', testPart)
            pathologist = testPart[pathologist.start() + len('out***|'):].strip()
            testPart = testPart[testPart.index(':') + len(':'):]
            testPart = testPart[:testPart.index('|')].strip()
            sampleLocation = ''
            testType = ''
            testTech = 'ihc'
            orderedDate = ''
            reportedDate = ''
            if testPart == 'pending':
                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                patientId)
                biomarkerResultList.append('her2')
                conceptResultList.append('')
                numericResultList.append('')
                qualifierResultList.append('pending')

            elif ';' in testPart:
                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                patientId)
                biomarkerResultList.append('her2')
                conceptResultList.append('presence')
                numericResultList.append('')
                qualifierResultList.append(testPart)
            else:
                testPart = 'her2 ' + testPart
                linesOfTest = testPart.split('|')
                for lot in linesOfTest:
                    lot = lot + "\n"
                    if lot == '' or len(lot.strip()) == 0:
                        continue
                    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                    with open(file, 'w') as filetowrite:
                        filetowrite.write(lot)
                    results = metamapstringoutput()
                    # Turn this on to print results
                    # printResults()
                    # #input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()
                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(row['Numeric'])
                        qualResult = ', '.join(row['Qualifier'])

                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                        biomarkerResultList.append(bioResult)
                        conceptResultList.append(conResult)
                        numericResultList.append(numResult)
                        qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            # Now remove that title from the report!
            lower = lower[:lower.index(startText)] + lower[lower.index(startText)+len(startText):]

        # Now we'll look by section: let's start with pathological diagnosis
        if 'pathological diagnosis' in lower:
            resetDerived()
            print("gettin' into patho")
            print(lower)
            #input()
            testStarts = []
            testEnds = []
            sectionStart = lower.index('pathological diagnosis')
            section = lower[sectionStart:]
            testStarts.append(sectionStart)
            try:
                testEnds.append(sectionStart + section.index('***elec'))
                section = section[:section.index('***elec')]
            except:
                try:
                    section = section[:section.index('|||')]
                    testEnds.append(section.index('|||'))
                except:
                    if 'her2' in lower or 'her-2' in lower or 'her 2' in lower:
                        aberrentTests.append(lower)
                        aberrentReasons.append('no signout')
                        print('aberrant')
                        ##input()
                    continue
            if 'her2' in section or 'her-2' in section or ' her 2' in section:
                section = section.split('|')
                section = list(filter(None, section))
                for sec in range(0, len(section)):
                    if 'her2' in section[sec] or 'her-2' in section[sec] or ' her 2' in section[sec]:
                        bit = section[sec]
                        if 'negative' not in section[sec] and 'positive' not in section[sec] and 'equivocal' not in section[sec] and sec > 0:
                            if 'negative' in section[sec - 1] or 'positive' in section[sec - 1] or 'equivocal' in section[sec - 1]:
                                bit = section[sec - 1] + ' ' + bit
                        if not section[sec].endswith('.') and sec < len(section) - 1:
                            if '.' in section[sec + 1]:
                                bit = bit + ' ' + section[sec + 1]
                        if '(' in section[sec] and ')' not in section[sec]:
                            bit = bit + ' ' + section[sec + 1]
                        if 'pending' not in bit and 'in progress' not in bit and 'will be reported' not in bit and 'will be performed' not in section[
                            sec] and 'please do' not in bit and 'criteria for' not in bit\
                                and 'are ordered' not in bit  and 'gene copy' not in bit \
                                and 'template' not in bit and 'formalin fixed' not in bit and 'are reported' not in bit \
                                and 'were characterized' not in bit and 'immunohistochemical staining for her2/neu is interpreted as' not in bit \
                                and 'will follow' not in bit:
                            bit = bit.replace(' - ', ' . ').replace('immunohistochemical', 'ihc')
                            linesOfTest = bit.split('|')
                            for lot in linesOfTest:
                                lot = lot + "\n"
                                if lot == '' or len(lot.strip()) == 0:
                                    continue
                                file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                                with open(file, 'w') as filetowrite:
                                    filetowrite.write(lot)
                                results = metamapstringoutput()
                                # Turn this on to print results
                                # printResults()
                                # #input()
                                # Turn this on to look at the whole test
                                # print(spacelower)
                                # #input()
                                for index, row in results.iterrows():
                                    bioResult = ', '.join(row['Biomarker'])
                                    conResult = ', '.join(row['Concept'])
                                    numResult = ', '.join(row['Numeric'])
                                    qualResult = ', '.join(row['Qualifier'])

                                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                                patientId)
                                    biomarkerResultList.append(bioResult)
                                    conceptResultList.append(conResult)
                                    numericResultList.append(numResult)
                                    qualifierResultList.append(qualResult)

                # Now we're going to snip all those tests out of the overall report!
                testStarts.reverse()
                testEnds.reverse()
                if len(testStarts) == len(testEnds):
                    for c in range(0, len(testStarts)):
                        lower = lower[:testStarts[c]] + lower[testEnds[c]:]

        # Next it seems like 'procedures/addenda' is the place to be
        if 'procedures/addenda' in lower:
            resetDerived()
            sectionStarts = []
            sectionEnds = []
            testStarts = []
            testEnds = []
            sectionStart = lower.index('procedures/addenda')
            section = lower[sectionStart:]
            testStarts.append(sectionStart)
            try:
                testEnds.append(sectionStart + section.index('***elec'))
                section = section[:section.index('***elec')]
            except:
                try:
                    testEnds.append(section.index('|||'))
                    section = section[:section.index('|||')]
                except:
                    if 'her2' in lower or 'her-2' in lower or 'her 2' in lower:
                        aberrentTests.append(lower)
                        aberrentReasons.append('no signout')
                        print('aberrant')
                        ##input()
                    continue
            if 'her2' in section or 'her-2' in section or ' her 2' in section:
                if 'estrogen receptor' in section:
                    print(section)
                    print(lower)
                    #input()
                section = section.split('|')
                section = list(filter(None, section))
                for sec in range(0, len(section)):
                    if 'her2' in section[sec] or 'her-2' in section[sec] or ' her 2' in section[sec]:
                        bit = section[sec]
                        if 'negative' not in section[sec] and 'positive' not in section[sec] and 'equivocal' not in section[sec] and sec > 0:
                            if 'negative' in section[sec - 1] or 'positive' in section[sec - 1] or 'equivocal' in section[sec - 1]:
                                bit = section[sec - 1] + ' ' + bit
                        if not section[sec].endswith('.') and sec < len(section) - 1:
                            if '.' in section[sec + 1]:
                                bit = bit + ' ' + section[sec + 1]
                            if '(' in section[sec] and ')' not in section[sec]:
                                bit = bit + ' ' + section[sec + 1]
                        if 'pending' not in bit and 'in progress' not in bit and 'will be reported' not in bit and 'will be performed' not in section[
                            sec] and 'please do' not in bit \
                                and 'are ordered' not in bit and 'criteria for' not in bit and 'gene copy' not in bit \
                                and 'template' not in bit and 'formalin fixed' not in bit and 'are reported' not in bit \
                                and 'were characterized' not in bit and 'immunohistochemical staining for her2/neu is interpreted as' not in bit \
                                and 'will follow' not in bit:
                            bit = bit.replace(' - ', ' . ').replace('immunohistochemical', 'ihc')
                            linesOfTest = bit.split('|')
                            for lot in linesOfTest:
                                lot = lot + "\n"
                                if lot == '' or len(lot.strip()) == 0:
                                    continue
                                file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                                with open(file, 'w') as filetowrite:
                                    filetowrite.write(lot)
                                results = metamapstringoutput()
                                # Turn this on to print results
                                # printResults()
                                # #input()
                                # Turn this on to look at the whole test
                                # print(spacelower)
                                # #input()
                                for index, row in results.iterrows():
                                    bioResult = ', '.join(row['Biomarker'])
                                    conResult = ', '.join(row['Concept'])
                                    numResult = ', '.join(row['Numeric'])
                                    qualResult = ', '.join(row['Qualifier'])

                                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                                    patientId)
                                    biomarkerResultList.append(bioResult)
                                    conceptResultList.append(conResult)
                                    numericResultList.append(numResult)
                                    qualifierResultList.append(qualResult)

            # Now we're going to snip all those tests out of the overall report!
            testStarts.reverse()
            testEnds.reverse()
            if len(testStarts) == len(testEnds):
                for c in range(0, len(testStarts)):
                    lower = lower[:testStarts[c]] + lower[testEnds[c]:]



        lower = lower.replace('a her2/neu immunohistochemical study is pending', '').replace('template for reporting results of her2', ''). \
            replace('her2 immunohistochemical|stain is performed on this specimen', '').replace('(her2 gene copy|', '').replace('er/pr, her2-neu and mib-1 immunostains will be', ''). \
            replace('her2 and mib-1 are in progress', '').replace('her2 is pending', '').replace('her2-neu immunostains will be reported as an addendum.', ''). \
            replace('her2-neu immunostain will be reported as an addendum.', '').replace('her2-fish: 88377','').replace('her2-sish: 88377','')

        if 'her2' in lower or 'her-2' in lower or ' her 2' in lower:
            extraTests.append(lower)
            print(lower)
            #input()
            ##input()
    # except Exception as e:
    #    failedTests.append(lower)
    #    failedReasons.append(e)
    #    continue

print(len(list(set(reportIdList))))
#input()

wrongTests = pd.DataFrame(list(zip(extraTests)), columns=['text'])
wrongTests.to_csv("~/Desktop/LatestNLP/Unstructured Results/ExtrasOfHer2.csv", index=False)

wrongwayTest = pd.DataFrame(list(zip(wrongwayTests, wrongwayReasons)), columns=['test', 'reason'])
wrongwayTest.to_csv("~/Desktop/LatestNLP/Unstructured Results/MalformedOfHer2.csv", index=False)

aberrentTest = pd.DataFrame(list(zip(aberrentTests, aberrentReasons)), columns=['test', 'reason'])
aberrentTest.to_csv("~/Desktop/LatestNLP/Unstructured Results/ErrorsOfHer2.csv", index=False)

failed = pd.DataFrame(list(zip(failedTests, failedReasons)), columns=['text', 'reason'])
failed.to_csv("~/Desktop/LatestNLP/Unstructured Results/FailedOfHer2.csv", index=False)

rawResults = pd.DataFrame(list(zip(biomarkerResultList, conceptResultList, numericResultList, qualifierResultList,
                                   firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionList, testTypeList, sampleLocationList,
                                   pathologistList, dateOrderedList, dateReportedList, testTextList, fullTextList, icdCodeList, patientIdList, reportIdList)),
                          columns=['biomarker', 'concept', 'numeric', 'qualifier', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accession', 'testType',
                                   'sampleLocation', 'pathologist', 'dateOrdered', 'dateReported', 'testText', 'fullText', 'icdCode', 'patientId', 'reportId'])
rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/RawOfHer2.csv", index=False)
