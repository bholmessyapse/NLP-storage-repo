import pandas as pd
import numpy as np
# For regex
import re
import gc
from NumWords import text2int
from MetaMapForLots import metamapstringoutput
from random import random
from random import seed
import random

# Right, so we'll process these reports in chunks. Henry Ford tends to give us reports in a very standardized
# format, so we'll process the bits we can with pattern matching, then put the rest through metamap or something.

# This boolean is for debugging.
# Enter the accession of the report you want to check
# If debug is true, we'll skip all tests except the one with the accession # given
# if flipOn is true, we'll skip all tests until we get to the one with the accession #, and do all the ones after that
# Always have SkipTest set to true - that's changed in code
# If upTo is on, we'll go up to the numberToSkip of reports.
debug = False
flipOn = False
skipTest = True
reportIdToCheck = 5600010001005

upTo = False
skipNum = False
numberToSkip = 4897
numCounter = 0

# Tally ho
df = pd.read_csv("~/Desktop/DeleteMeSoon/combined.csv", low_memory=False)

# We'll first split the report by line break.
df['result'] = df['result'].apply(lambda p: p.split("\n"))

# These are the parts of the report that we pulled out from the rest of the HL7 message
reportIds = df['ReportId']
# ### Source we can better pull out from the unstructured part of the path report
# sources = df['Source']
# ## Healthcare Organization is the first line always, so that's easy to get
# healthOrgs = df['healthOrg']
# ### MRN we likewise need to pull from the path report
# MRNs = df['MRN']
firstNames = df['firstName']
middleNames = df['middleName']
lastNames = df['lastName']
DOBs = pd.to_datetime(df['DOB'], format='%Y-%m-%d')
genders = df['gender']
# ### The date, too, is best pulled from the path report
testOrderDates = pd.to_datetime(df['testOrderDate'], format='%Y%m%d%M%S')


# This is what I've been using to pick selected test types
brcaTests = []

# We'll want to save a list per every result for all the structured fields, along with the parts of the result that
# we get from the panels.
reportIdList, sourceList, healthOrgList, MRNList, firstNameList, middleNameList, lastNameList, jrSrList, DOBList, genderList, \
        testTypeList, testReportedDateList, testApproveList, geneList, locationList, transcriptList, cdnaList, proteinList,\
        dpList, exonList, alleleFrequencyList, labelList, aminoAcidRangeList, icdCodeList, accessionList, \
        physicianList, takenList, statusList, fullTestList, specimenCodeList, specimenTypeList, pdfLinkList, pathologistList = ([] for i in range(33))


# Ok, here are some biomarker-and-test-specific ones. We're starting with an easy one, ER/PR from surgical path reports
geneList = []
assayList = []
assayPercentPositiveList = []
intensityList = []
assayResultList = []
allredScoreList = []


# This extra one is for saving gene/exon coding regions from reports.
geneTestedList = []
exonTestedList = []
aminoAcidTestedList = []


# We'll go through line by line
line = 0

# For the impatient, an iterator number
testNum = 0
# Tests that don't fit the mold
aberrantTests = []
aberrantMRNs = []
aberrantFirstNames = []
aberrantLastNames = []
aberrantDOBs = []
aberrantReason = []

# We have a file detailing where the PDFs from the HF path reports are. There SHOULD be a path report for every accession and record id. Let's check.
pdfRecordId = []
pdfAccession = []
with open("/Users/bholmes/Desktop/DeleteMeSoon/listOfPdfs.txt") as pdfNameFile:
    lines = pdfNameFile.readlines()
    for lineT in lines:
        lineT = lineT.split()
        for bit in lineT:
            bit = bit.split("_")
            pdfRecordId.append(bit[0])
            pdfAccession.append(bit[1])

sampleNum = 0
# Every line of df['result'] is another unstructured report.
for reportLine in df['result']:

    # If we don't handle space removal before, here's the place to do it.
    for i in range(0, len(reportLine)):
        reportLine[i] = reportLine[i].strip()

    # The hospital that did the report
    source = reportLine[0]

    firstName = firstNames[line]
    middleName = middleNames[line]
    lastName = lastNames[line]
    if pd.isnull(firstName):
        firstName = ''
    if pd.isnull(lastName):
        lastName = ''
    if pd.isnull(middleName):
        middleName = ''

    if len(firstName.split()) == 2:
        middleName = firstName.split()[1]
        firstName = firstName.split()[0]

    if len(lastName.split()) == 2:
        if lastName.split()[1].lower() == 'jr' or lastName.split()[1].lower() == 'jr.' or lastName.split()[1].lower() == 'junior':
            jrSr = "JR"
            lastName = lastName.split()[0]
    elif len(lastName.split()) == 2:
        if lastName.split()[1].lower() == 'sr' or lastName.split()[1].lower() == 'sr.' or lastName.split()[1].lower() == 'senior':
            jrSr = 'SR'
            lastName = lastName.split()[0]
    elif len(middleName.split()) == 2:
        if 'jr' in middleName.split()[1].lower() or 'junior' in middleName.split()[1].lower():
            middleName = middleName.split()[0]
            jrSr = 'JR'
    elif len(middleName.split()) == 2:
        if 'sr' in middleName.split()[1].lower() or 'senior' in middleName.split()[1].lower():
            middleName = middleName.split()[0]
            jrSr = 'SR'
    else:
        jrSr = ''
    reportId = reportIds[line]
    DOB = DOBs[line].date()
    gender = genders[line]

    line = line + 1

    # One thing that (FOR NOW) is always consistent among HF reports is that the test type
    # shows up RIGHT before the patient information. Using this, I can find the name of the test type.
    # A more stable way to find this would probably be to do some CNNing. This is implemented, but let's
    # try to not use it for now.
    #
    # Ok check on that, if the report is amended then I need to further map it. Can't guarantee that this won't
    # eventually fail, but until we get a comprehensive list of all the tests, I can't search for those.
    index = [idx for idx, s in enumerate(reportLine) if 'Patient Name:' in s][0]
    indexTT = index-1
    testType = reportLine[indexTT]
    while testType == '' or 'amended' in testType.lower():
        indexTT = indexTT-1
        testType = reportLine[indexTT].strip()

    # We're going to join the list together into a string, which we reserve the right to separate later. The
    # newline characters are preserved as pipes, in case that's useful.
    pathReport = '|'.join(reportLine)
    pathReportFull = '\n'.join(reportLine)
    pathReport = re.sub(' +', ' ', pathReport)
    pathReport = pathReport.lower()

    # These are ICD codes. Easy to pull out!
    if 'icd code(s)' in pathReport:
        if 'billing fee' in pathReport:
            icdC = pathReport[pathReport.index("icd code(s):") + len('icd code(s):'):pathReport.index('billing fee')] \
                .replace('however', '.').replace('less than', '<').replace('more than', '>').replace('|','').strip().split()
        elif 'clia' in pathReport:
            icdC = pathReport[pathReport.index("icd code(s):") + len('icd code(s):'):pathReport.index('clia')] \
                .replace('however', '.').replace('less than', '<').replace('more than', '>').replace('|','').strip().split()
        else:
            icdC = pathReport[pathReport.index("icd code(s):") + len('icd code(s):'):pathReport.index('==')] \
                .replace('however', '.').replace('less than', '<').replace('more than', '>').replace('|','').strip().split()
        icdC = list(dict.fromkeys(icdC))
        icdC = ', '.join(icdC)
        icdC = icdC.replace('|', ' ').replace(':,', ':').strip()
    else:
        icdC = ""

    # This is where we get the date reported and MRN.
    reportedIndex = pathReport.index("reported:")
    date = pathReport[reportedIndex + 9:reportedIndex + 20].replace("|", '').replace("p", '')
    date = date.strip()
    mrnIndex = pathReport.index("rec.:")
    MRN = pathReport[mrnIndex + 5:mrnIndex + 14]

    # This is where we get the signout date - sometimes it's not different than the reported date
    try:
        receivedIndex = pathReport.index("received:")
        received = pathReport[receivedIndex + 9:receivedIndex+20].replace('|', '').replace('p', '')
        received = received.strip()
    except:
        received = date

    # Let's find the pathologist on the case - there can be multiple "***electronically signed out***s"
    foundim = False
    pathReportSplit = pathReport.split("|")
    for lineo in range(0, len(pathReportSplit)):
        if '***electronically' in pathReportSplit[lineo]:
            if '=' not in pathReportSplit[lineo + 1] and pathReportSplit[lineo + 1] != '':
                pathologist = pathReportSplit[lineo+1].strip()
                foundim = True
                continue
    if not foundim:
        try:
            personSection = pathReport.index('***electronically signed out by')
            personBit = pathReport[personSection + 32:]
            endBit = personBit.index('*')
            pathologist = pathReport[personSection + 32: personSection + 32 + endBit].strip()
        except:
            try:
                personSection = pathReport.index('pathologist:')
                personBit = pathReport[personSection + 12:]
                endBit = personBit.index('|')
                pathologist = pathReport[personSection + 12: personSection + 12 + endBit].strip()
            except:
                print(pathReportFull)
                input()

    # Let's get the sample Id, if they have it
    specimenCode = []
    specimenType = []
    if 'operation/specimen' in pathReport:
        reportedIndex = pathReport.index("operation/specimen")
        postReportedBreak = pathReport[reportedIndex + 19:].index("||")
        reportedArray = pathReport[reportedIndex + 19: (reportedIndex + 19) + postReportedBreak]
        # Reported array should be all the specimens, broken up by '|'. So let's get an array of each
        reportedArray = reportedArray.replace('|', ' ')
        for specimen in re.split(r'[^0-9]:', reportedArray)[1:]:
            specimen.strip()
            specList = specimen.split(',')
            if len(specList) == 1:
                specList = specimen.split(';')
            if len(specList) == 1:
                specList = specimen.split(') ')
                if len(specList) == 2:
                    specList[0] = specList[0] + ')'
            specimenCd = ''
            specimenTp = ''
            for spec in specList:
                spec = spec.strip()
                if spec == '':
                    continue
                if '-' in spec and ' - ' not in spec and 'biopsy' not in spec:
                    if ':' in spec.split()[0] and not spec.split()[0][0].isnumeric():
                        spec = spec[3:]
                    # Some samples are listed as "bone marrow [sample id]". Let's fix.
                    if 'bone marrow' in spec:
                        spec = spec.replace('bone marrow ', '')
                        specimenTp = specimenTp + ' ' + 'bone marrow'
                    specimenCd = specimenCd + ' ' + spec
                else:
                    if len(specimenCode) == len(specimenType) and len(specimenCode) > 0:
                        if specimenType[-1] == 'bone marrow':
                            continue
                    if ':' in spec.split()[0] and not spec.split()[0][0].isnumeric():
                        spec = spec[3:]
                    specimenTp = specimenTp + ' ' + spec
            specimenCode.append(specimenCd.strip())
            specimenType.append(specimenTp.strip())
        specimenCode = ','.join(specimenCode)
        specimenType = ','.join(specimenType)
        if 'bone marrow aspirate' in specimenType:
            specimenType = 'bone marrow aspirate'
        elif 'bone marrow smear' in specimenType:
            specimenType = 'bone marrow smear'
        elif 'bone marrow' in specimenType:
            specimenType = 'bone marrow'
        elif 'tissue' in specimenType:
            specimenType = 'tissue'
        elif 'blood' in specimenType:
            specimenType = 'blood'
        elif 'excision biopsy' in specimenType:
            specimenType = 'tissue'
        elif 'biopsy' in specimenType:
            specimenType = 'tissue'
        elif '[]' in specimenType:
            specimenType = 'Blood'
        else:
            specimenType = 'Blood'

    # Let's get accession and physician aaaand date collected just for fun - accession is going to be the "report id"
    reportedIndex = pathReport.index("accession #:")
    accessionBit = pathReport[reportedIndex + 12:]
    postAccessionBreak = accessionBit.index("|")
    accession = pathReport[reportedIndex + 12: reportedIndex + 12 + postAccessionBreak].strip()

    # Here 'were getting the PDF link
    if str(reportId) in pdfRecordId:
        pdfLink = "s3://syapse-ephemeral/PDFs/" + str(reportId) + "_" + accession + "_pdf.pdf"
    else:
        pdfLink = "s3://syapse-ephemeral/PDFs/" + str(reportId) + "_" + accession + "_txt.txt"

    reportedIndex = pathReport.index("physician(s):")
    physicianBit = pathReport[reportedIndex + 13:]
    postPhysicianBreak = physicianBit.index("|")
    physician = pathReport[reportedIndex + 13: reportedIndex + 13 + postPhysicianBreak].strip()

    if 'taken:' not in pathReport:
        if 'collected:' in pathReport:
            reportedIndex = pathReport.index('collected:')
            takenBit = pathReport[reportedIndex + 10:]
            postTakenBreak = takenBit.index("|")
            taken = pathReport[reportedIndex + 10: reportedIndex + 10 + postTakenBreak].strip()
        elif 'autopsy date:' in pathReport:
            reportedIndex = pathReport.index('autopsy date:')
            takenBit = pathReport[reportedIndex + 13:]
            postTakenBreak = takenBit.index("|")
            taken = pathReport[reportedIndex + 13: reportedIndex + 13 + postTakenBreak].strip()
        else:
            taken = ''
    else:
        reportedIndex = pathReport.index("taken:")
        takenBit = pathReport[reportedIndex + 6:]
        postTakenBreak = takenBit.index("|")
        taken = pathReport[reportedIndex + 6: reportedIndex + 6 + postTakenBreak].strip()

    if 'status:' not in pathReportFull:
        status = ''
    else:
        reportedIndex = pathReport.index("status:")
        statusBit = pathReport[reportedIndex + 7:]
        postStatusBreak = statusBit.index("|")
        status = pathReport[reportedIndex + 7: reportedIndex + 7 + postStatusBreak].strip()

    # And we'll pull out the healthcareOrg here
    healthOrg = pathReport.split('|')[0]

    ###############################
    #  AND NOW WE BEGIN THE NLP!! #
    ###############################

    # Here we're getting the single largest chunk of ER/PR assays - the 'Estrogen and Progesterone Receptor Assay's from surgical pathology reports
    if testType == 'Surgical Pathology Report':

        if debug and skipTest:
            if reportId != reportIdToCheck:
                print('movin on')
                continue
            else:
                if flipOn:
                    skipTest = False
                print("HERE!")
                input()

        # This will isolate the estrogen and progesterone assay
        if "estrogen and progesterone receptor assay" in pathReport:
            # This skips tests for us if we're doing that
            if skipNum and numCounter < numberToSkip:
                print('movin on')
                numCounter = numCounter + 1
                continue
            if upTo:
                if numCounter > numberToSkip:
                    break
                numCounter = numCounter + 1
            sampleNum = sampleNum + 1
            # It's nice to know how many tests have passed
            print("*****************************")
            print("TEST NUMBER " + str(testNum))
            testNum = testNum + 1
            print("*****************************")
            # This is so I can tell if skipped tests have pending dates
            if 'pending' in pathReport:
                print("PENDING")
            testIndex = pathReport.index('estrogen and progesterone receptor assay')
            testPart = pathReport[testIndex:]
            try:
                endIndex = testPart.index('***electronically')
            # This usually means it's pending. Don't add?
            except:
                aberrantTests.append(pathReportFull)
                aberrantFirstNames.append(firstName)
                aberrantLastNames.append(lastName)
                aberrantMRNs.append(MRN)
                aberrantDOBs.append(DOB)
                aberrantReason.append("No ***electronically")
                continue
            testPart = pathReport[testIndex+41:testIndex+endIndex]
            testType = "estrogen and progesterone receptor assay"

            # These tests will individually report their date ordered and reported
            if 'date ordered:' in testPart:
                date = testPart[testPart.index('date ordered:')+ 13: testPart.index('date repo')].strip()
            if 'date reported:' in testPart:
                received = testPart[testPart.index('date reported:')+ 14: testPart.index('||')].strip()
                # If the results are pending, we can skip 'em
                if received == 'pending' or 'pending' in received:
                    aberrantTests.append(pathReportFull)
                    aberrantFirstNames.append(firstName)
                    aberrantLastNames.append(lastName)
                    aberrantMRNs.append(MRN)
                    aberrantDOBs.append(DOB)
                    aberrantReason.append("Pending")
                    continue

            # And will also have their own pathologist
            postTestArea = pathReport[testIndex+endIndex:]
            nextLineIndex = postTestArea.index('*|')
            nextLine = postTestArea[nextLineIndex+2:]
            endOfNextLineIndex = nextLine.index('|')
            pathologist = postTestArea[nextLineIndex+2:nextLineIndex+2+endOfNextLineIndex]

            indices = []
            # Some of these have tests done on multiple samples. They'll be divided up like A. [sample type] [test] B. [sample type] etc.
            if '|a:' in testPart and '|a.' in testPart:
                if testPart.index('a:') < testPart.index('a.'):
                    indices = re.finditer(r'\|\w\:', testPart)
                else:
                    indices = re.finditer(r'\|\w\.', testPart)
            elif '|a:' in testPart and '|a.' not in testPart:
                indices = re.finditer(r'\|\w\:', testPart)
            elif '|a:' not in testPart and '|a.' in testPart:
                indices = re.finditer(r'\|\w\.', testPart)
            elif 'results: a.' in testPart:
                indices = re.finditer(r'\b\w\.', testPart)
            else:
                indices = [0]

            testStarts = []
            for m in indices:
                if m == 0:
                    testStarts.append(m)
                else:
                    testStarts.append(m.start())
            testStarts.append(len(testPart))

            # If there aren't individual tests, we'll take the whole section in one chunk
            if len(testStarts) == 1:
                testStarts = []
                testStarts.append(-3)
                testStarts.append(endIndex)

            # Let's look at each individual test
            for startIndex in range(0, len(testStarts)-1):
                subTest = testPart[testStarts[startIndex]+3:testStarts[startIndex+1]]
                # These tests are biopsy tests, so the sample will end with the word "biopsy"
                if 'biopsy' in subTest:
                    biopsyIndex = subTest.index('biopsy') + 6
                    specimenType = subTest[0:biopsyIndex].strip()
                    specimenCode = ''
                else:
                    specimenType = ''
                    specimenCode = ''

                # They'll start with 'test results:' and, if the allred score % definitinos are around, will end with those
                try:
                    testStartIndex = subTest.index('estrogen receptor')
                except:
                    print(subTest)
                    print(pathReportFull)
                    aberrantTests.append(pathReportFull)
                    aberrantFirstNames.append(firstName)
                    aberrantLastNames.append(lastName)
                    aberrantMRNs.append(MRN)
                    aberrantDOBs.append(DOB)
                    aberrantReason.append("No estrogen receptor")
                    continue
                # 'please note' is for exceptions to the normal flow
                try:
                    testEndIndex = subTest.index('please note')
                except:
                    try:
                        testEndIndex = subTest.index('allred score: % staining score')
                        indTest = subTest[testStartIndex: testEndIndex]
                    except:
                        try:
                            testEndIndex = subTest.index('test description:')
                            indTest = subTest[testStartIndex: testEndIndex]
                        except:
                            indTest = subTest[testStartIndex:]

                # Now let's do some manipulation to give metamap the cleanest possible text
                # First, let's try to remove the notes
                if 'note:' in indTest:
                    partPostNote = indTest[indTest.index('note:'):]
                    endOfNote = partPostNote.index('||') + indTest.index('note:')
                    firstPart = indTest[0:indTest.index('note:')]
                    secondPart = indTest[endOfNote:]
                    indTest = firstPart + '|' + secondPart

                indTest = indTest.split('|')
                print("HERE'S A TEST")
                print(indTest)
                for line in range(0, len(indTest)):
                    indTest[line] = indTest[line].replace(':', ' ')
                    if '(erica):' in indTest[line] or 'percent positive' in indTest[line] or 'intensity' in indTest[line] or '(prica):' in indTest[line]:
                        indTest[line] = indTest[line] + '.'
                    # We want to eliminate (by percentage) or (by allred score)
                    if '(prica)' in indTest[line] or '(erica)' in indTest[line]:
                        if 'by' in indTest[line]:
                            indTest[line] = indTest[line][:indTest[line].index('by')]
                        if ' in ' in indTest[line]:
                            indTest[line] = indTest[line][:indTest[line].index(' in ')]
                        if ' pr ' in indTest[line]:
                            indTest[line] = indTest[line][:indTest[line].index(' pr ')]
                        if ' er ' in indTest[line]:
                            indTest[line] = indTest[line][:indTest[line].index(' er ')]
                    if 'erica' not in indTest[line] and 'prica' not in indTest[line] and 'percent positive' not in indTest[line] and 'intensity' not in indTest[line] and 'estrogen' not in indTest[line]\
                        and 'progesterone' not in indTest[line]:
                        indTest[line] = ''
                    if 'estrogen receptor score' in indTest[line]:
                        # Sometimes the reports are malformed with like receptor:3-
                        for strn in indTest[line].split():
                            if '-' in strn and '/' not in strn  :
                                indTest[line] = indTest[line].replace(strn, '')
                        indTest[line] = indTest[line].replace('estrogen receptor score', 'estrogen receptor allred score')
                        # This is to replace 3-4 with 3 to 4
                        indTest[line] = indTest[line].replace('-', ' to ')
                        try:
                            startOfParen = indTest[line].index('(')
                        except:
                            startOfParen = len(indTest[line])
                        indTest[line] = indTest[line][:startOfParen]
                        indTest[line] = indTest[line].strip() + '.'
                    if 'progesterone receptor score' in indTest[line]:
                        # Sometimes the reports are malformed with like receptor:3-
                        for strn in indTest[line].split():
                            if '-' in strn and '/' not in strn:
                                indTest[line] = indTest[line].replace(strn, '')
                        indTest[line] = indTest[line].replace('progesterone receptor score', 'progesterone receptor allred score')
                        indTest[line] = indTest[line].replace('-', ' to ')
                        try:
                            startOfParen = indTest[line].index('(')
                        except:
                            startOfParen = len(indTest[line])
                        indTest[line] = indTest[line][:startOfParen]
                        indTest[line] = indTest[line].strip() + '.'
                    if 'intensity' in indTest[line]:
                        indTest[line] = indTest[line] + "|"
                    if 'pr allred score' in indTest[line]:
                        indTest[line] = indTest[line].replace('er/pr allred score', '')
                indTest = ' '.join(indTest)

                # At this point, we can split them and expect good results from metamap out of each of the
                linesOfTest = indTest.split('|')
                print("HERE'S THE WHOLE")
                print(pathReportFull)
                for lot in linesOfTest:
                    lot = lot + "\n"
                    if lot == '' or len(lot.strip()) == 0:
                        continue
                    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                    with open(file, 'w') as filetowrite:
                        filetowrite.write(lot)
                    print(lot)
                    print(len(lot))
                    print(len(lot.strip()))
                    results = metamapstringoutput()
                    print("AND THE RESULTS")
                    print(results)
                    print(lot)
                    input()

                    # And here, we're going to analyze those results!
                    for index, row in results.iterrows():
                        # one possible row is a blank biomarker with intensity and a qualifier - those are associated with an ER or a PR
                        if 'intensity' in row['Concept']:
                            if row['Qualifier'] == []:
                                intensityList.append('None')
                            elif 'qns' in row['Qualifier']:
                                intensityList.append('qns')
                            elif len(row['Qualifier']) == 2:
                                intensityList.append(str(row['Qualifier'][0]) + ' to ' + str(row['Qualifier'][1]))
                            else:
                                intensityList.append(str(row['Qualifier'][0]))
                        # Another possible row is the ER or PR
                        if row['Biomarker'] == ['estrogen receptor'] and 'erica' in row['Concept']:
                            geneList.append('ER')
                            if('negative' in row['Qualifier']):
                                assayResultList.append('negative')
                            elif 'qns' in row['Qualifier'][0]:
                                row['Qualifier'][0] = 'qns'
                            elif(len(row['Qualifier'][0].split(',')) == 2):
                                assayResultList.append(row['Qualifier'][0] + ' to ' + row['Qualifier'][1])
                            else:
                                assayResultList.append(row['Qualifier'][0])
                            firstNameList.append(firstName)
                            middleNameList.append(middleName)
                            lastNameList.append(lastName)
                            jrSrList.append(jrSr)
                            reportIdList.append(reportId)
                            healthOrgList.append(healthOrg)
                            testTypeList.append(testType)
                            sourceList.append(source)
                            MRNList.append(MRN)
                            DOBList.append(DOB)
                            genderList.append(gender)
                            testReportedDateList.append(date)
                            testApproveList.append(received)
                            icdCodeList.append(icdC)
                            accessionList.append(accession)
                            physicianList.append(physician)
                            takenList.append(taken)
                            statusList.append(status)
                            specimenCodeList.append(specimenCode)
                            specimenTypeList.append(specimenType)
                            pdfLinkList.append(pdfLink)
                            pathologistList.append(pathologist)
                            # Sometimes there are NO allred or intensity scores
                            if 'allred' not in ' '.join(linesOfTest):
                                allredScoreList.append('not given')
                            # And sometimes there's not either estrogen or progesterone, but there IS the other
                            elif 'estrogen receptor score' not in pathReport:
                                allredScoreList.append('not given')
                            if 'intensity' not in ' '.join(linesOfTest):
                                intensityList.append('not given')
                            # We also want to check if ER (which comes first) doesn't have intensity
                            elif 'progesterone receptor|' in pathReport:
                                if 'intensity' not in pathReport[pathReport.index('(erica)'):pathReport.index('progesterone receptor|')]:
                                    intensityList.append('not given')
                            else:
                                if 'intensity' not in pathReport[pathReport.index('(erica)'):pathReport.index('test description')]:
                                    intensityList.append('not given')
                        if row['Biomarker'] == ['progesterone receptor'] and 'prica' in row['Concept']:
                            geneList.append('PR')
                            if 'negative' in row['Qualifier']:
                                assayResultList.append('negative')
                            elif(len(row['Qualifier']) == 2):
                                assayResultList.append(row['Qualifier'][0] + ' to ' + row['Qualifier'][0][1])
                            else:
                                assayResultList.append(row['Qualifier'][0])
                            firstNameList.append(firstName)
                            middleNameList.append(middleName)
                            lastNameList.append(lastName)
                            jrSrList.append(jrSr)
                            reportIdList.append(reportId)
                            healthOrgList.append(healthOrg)
                            testTypeList.append(testType)
                            sourceList.append(source)
                            MRNList.append(MRN)
                            DOBList.append(DOB)
                            genderList.append(gender)
                            testReportedDateList.append(date)
                            testApproveList.append(received)
                            icdCodeList.append(icdC)
                            accessionList.append(accession)
                            physicianList.append(physician)
                            takenList.append(taken)
                            statusList.append(status)
                            specimenCodeList.append(specimenCode)
                            specimenTypeList.append(specimenType)
                            pdfLinkList.append(pdfLink)
                            pathologistList.append(pathologist)
                            # This is the part of the test after 'progesterone'
                            postProg = pathReport[pathReport.index('progesterone receptor|'):]
                            # sometimes we don't have any allred or intensity scores
                            if 'allred' not in ' '.join(linesOfTest):
                                allredScoreList.append('not given')
                            # And sometimes there's not either estrogen or progesterone, but there IS the other
                            elif 'progesterone receptor score' not in pathReport:
                                allredScoreList.append('not given')
                            if 'intensity' not in ' '.join(linesOfTest):
                                intensityList.append('not given')
                            else:
                                if 'er/pr allred score:' in pathReport:
                                    if 'intensity' not in pathReport[pathReport.index('progesterone receptor|'):pathReport.index('progesterone receptor|') + postProg.index('er/pr allred score')]:
                                        intensityList.append('not given')
                                elif 'test description' in postProg:
                                    if 'intensity' not in pathReport[pathReport.index('progesterone receptor|'):pathReport.index('progesterone receptor|') + postProg.index('test description')]:
                                        intensityList.append('not given')
                                elif 'intensity' not in pathReport[pathReport.index('progesterone receptor|'):pathReport.index('progesterone receptor|') + postProg.index('***el')]:
                                    intensityList.append('not given')
                                else:
                                    print("INTENSITY")
                                    print(pathReport)
                        if 'erica' in row['Concept'] or 'prica' in row['Concept']:
                            if 'erica' in row['Concept']:
                                assayList.append('erica')
                            elif 'prica' in row['Concept']:
                                assayList.append('prica')
                            if row['Qualifier'] == ['qns']:
                                assayPercentPositiveList.append('qns')
                            elif row['Numeric'] == []:
                                assayPercentPositiveList.append('unspecified')
                            else:
                                assayPercentPositiveList.append(row['Numeric'][0])
                        if row['Concept'] == ['allred score']:
                            if row['Numeric'] == []:
                                allredScoreList.append('unspecified')
                            else:
                                if len(row['Numeric']) == 2:
                                    allredScoreList.append(row['Numeric'][0] + '-' + row['Numeric'][1])
                                else:
                                    allredScoreList.append(row['Numeric'][0])

        # Now let's try Her-2/ neu Protein Assay (IHC)
        #if 'her-2/ neu protein assay (ihc)' in pathReport:
        #    testIndex = pathReport.index('her-2/ neu protein assay (ihc)')
        #    testPart = pathReport[testIndex:]
        #    try:
        #        endIndex = testPart.index('***electronically')
        #    # This usually means it's pending. Don't add?
        #    except:
        #        aberrantTests.append(pathReportFull)
        #        continue
        #    testPart = pathReport[testIndex+31:testIndex+endIndex]
        #    testType = "estrogen and progesterone receptor assay"
        #    #print(testPart)
        #    #input()



        sampleLen = len(firstNameList)
        for listo in [firstNameList, lastNameList, middleNameList, jrSrList, reportIdList, healthOrgList, testTypeList, sourceList, MRNList, DOBList, genderList,
    testReportedDateList, testApproveList, icdCodeList, accessionList, physicianList, takenList, statusList, specimenCodeList,
    specimenTypeList, pdfLinkList, pathologistList, geneList, assayList, assayPercentPositiveList, intensityList, assayResultList,
    allredScoreList]:
            if len(listo) != sampleLen:
                print("PROBLEM'S HERE")
                print(reportId)
                print(geneList)
                print(assayList)
                print(assayPercentPositiveList)
                print(intensityList)
                print(allredScoreList)
                print(assayResultList)
                print(len(listo))
                print(sampleLen)
                print(listo)
                print(pathReportFull)
                print(results)
                print(lot)
                input()

for listo in [firstNameList, lastNameList, middleNameList, jrSrList, reportIdList, healthOrgList, testTypeList, sourceList, MRNList, DOBList, genderList,
    testReportedDateList, testApproveList, icdCodeList, accessionList, physicianList, takenList, statusList, specimenCodeList,
    specimenTypeList, pdfLinkList, pathologistList, geneList, assayList, assayPercentPositiveList, intensityList, assayResultList,
    allredScoreList]:
    print(len(listo))

erPrSurpath = pd.DataFrame(list(zip(
    firstNameList, lastNameList, middleNameList, jrSrList, reportIdList, healthOrgList, testTypeList, sourceList, MRNList, DOBList, genderList,
    testReportedDateList, testApproveList, icdCodeList, accessionList, physicianList, takenList, statusList, specimenCodeList,
    specimenTypeList, pdfLinkList, pathologistList, geneList, assayList, assayPercentPositiveList, intensityList, assayResultList,
    allredScoreList)), columns=['firstName', 'lastName', 'middleName', 'jrSr', 'reportId', 'healthOrg', 'testType', 'source', 'MRN', 'DOB', 'gender',
                                'testReportedDate', 'testApprovedDate', 'icdCode', 'accession', 'physician', 'taken', 'status', 'specimenCode',
                                'specimenType', 'pdfLink', 'pathologist', 'gene', 'assay', 'assayPercentPositive', 'intensity', 'assayResult', 'allredScore'])

wrongTests = pd.DataFrame(list(zip(aberrantTests, aberrantFirstNames, aberrantLastNames, aberrantDOBs, aberrantMRNs, aberrantReason)),
                          columns=['weird tests', 'first name', 'last name', 'dob', 'mrn', 'reasons'])

erPrSurpath.to_csv("~/Desktop/DeleteMeSoon/BiomarkersForPhizer/ERPRTests.csv",index=False)
wrongTests.to_csv("~/Desktop/DeleteMeSoon/BiomarkersForPhizer/ERPRTestsSurgicalPathDiffro.csv",index=False)