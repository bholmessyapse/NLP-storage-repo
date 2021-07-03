import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput
import string
# Remove non-ascii characters
def unweird(stringA):
    return re.sub(r'[^\x00-\x7f]',r'', stringA)

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# Now beginning the sorting out!
pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/March2020HFHS.csv", low_memory=False)

# Delete later, this is for finding reports that were triggering a weird condition
reportsToCheck = []

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


# This is for making sure the lists never get smaller - only for debugging!
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
extraStrings = []
failedTests = []
failedReasons = []

erprNames = ['estrogen receptor', 'progesterone receptor', ' er:', ' pr:', 'er/pr', 'estrogen/progesterone', 'esr1', ' esr', ' pgr']

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
#for x in range(124800, 125000):
#    try:
    if x % 100 == 0:
        print(x, ' of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    # This to jump to a report
    # if reportId != "5d359c40-4e59-4c2f-a215-2b9c72157f51":
    #     continue
    lower = str(pathReports['description'][x]).lower()
    lower = unweird(lower)
    lower = re.sub(' +', ' ', lower)
    lower = lower.replace('but', '. .')
    lower = lower.replace('|er ', '|estrogen receptor ').replace(' er ', ' estrogen receptor ').replace('|pr ', '|progesterone receptor ').replace(' pr ', ' progesterone reeceptor ')
    lower = lower.replace('er/pr', 'estrogen receptor and progesterone receptor')
    splitReport = lower.split('\n')
    # These reports are truncated and don't contain info - NONE have 'ER' or 'PR'
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
    if any(substring in lower for substring in erprNames):

        # We want to remove all 'test description's, and 'analyte specific reagent's  because they can contain the strings of the biomarkers we're looking for, and they don't matter!
        # Pull these out later if you want the test descriptions!
        while 'test description:' in lower:
            firstInstance = re.search(r"test description:", lower)
            testDescription = lower[firstInstance.start():]
            paragraphBreak = re.search('\n\n', testDescription)
            testDesString = lower[firstInstance.start():firstInstance.start() + paragraphBreak.start()]
            lower = '\n'.join(lower.split(testDesString))
        while 'analyte specific reagent (asr) disclaimer:' in lower:
            firstInstance = re.search(r"analyte specific reagent \(asr\) disclaimer:", lower)
            testDescription = lower[firstInstance.start():]
            paragraphBreak = re.search('\n\n', testDescription)
            testDesString = lower[firstInstance.start():firstInstance.start() + paragraphBreak.start()]
            lower = '\n'.join(lower.split(testDesString))

        # Alright, now we're gonna get them.
        barlower = lower.replace('\n', '|').replace('her-2', 'her2').replace('over expression', 'overexpression').replace('\\\\r\\\\', '').replace('),', '). .')
        spacelower = lower
        lower = lower.replace('\n', '|').replace('her-2', 'her2').replace('over expression', 'overexpression').replace('\\\\r\\\\', '').replace('),', '). .')

        # I'm shifting this from an 'if' to a 'while', so that if there's any errors, we only delete the one section in question, instead of the whole test.
        while 'estrogen and progesterone receptor assay' in lower:
            resetDerived()
            print('estrogen and progesterone receptor assay')
            testStarts = []
            testEnds = []
            testType = 'estrogen and progesterone receptor assay'
            testTech = 'ihc'

            testIndex = lower.index('estrogen and progesterone receptor assay')
            fullTest = lower[testIndex:]
            lower = lower[testIndex + len('estrogen and progesterone receptor assay'):]

            # These tests are badly formed, and I don't know what to do with them
            if 'ventana ultraview dab detection kit:' in fullTest:
                extraTests.append(lower.replace('|', '\n'))
                exStrings = []
                for subz in erprNames:
                    if subz in lower:
                        exStrings.append(subz)
                exStrings = ', '.join(exStrings)
                extraStrings.append(exStrings)
                continue
            if 'pathologist|' in fullTest:
                fullTestEnd = fullTest.index('pathologist|')
                fullTest = fullTest[:fullTestEnd + len('pathologist')]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:testIndex] + lower[testIndex+len('estrogen and progesterone receptor assay'):]
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
                    lower = lower[:testIndex] + lower[testIndex + len('estrogen and progesterone receptor assay'):]
                    continue
                try:
                    reportedDate = fullTest[reportedDate.start() + len("date reported: "): reportedDate.start() + reportedDateEnd.start()].strip()
                except Exception as e:
                    aberrentTests.append(fullTest)
                    aberrentReasons.append('dates missing')
                    lower = lower[:testIndex] + lower[testIndex + len('estrogen and progesterone receptor assay'):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('er')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:testIndex] + lower[testIndex + len('estrogen and progesterone receptor assay'):]

                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pr')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:testIndex] + lower[testIndex + len('estrogen and progesterone receptor assay'):]

                    continue
                if 'out***' in fullTest:
                    pathologist = re.search('out\*\*\*\|', fullTest)
                    pathologist = fullTest[pathologist.start() + len('out***|'):].strip()
                else:
                    reportsToCheck.append(reportId)
                    #input()
                    continue
            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:

            # Experimental - let's see if we can find things like ' b ' and replace them with ' b. '
            potentialSpots = re.findall('\s[b-j]\s', fullTest)
            for spot in potentialSpots:
                fullTest = fullTest.replace(spot, spot[:-1] + '. ')

            samples = re.finditer('\|[a-z]\.\s', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                if 'test results' in sampleText:
                    sampleEnd = sampleText.index('test results')
                    sampleLocation = sampleText[:sampleEnd]
                    sampleText = sampleText[sampleEnd + len('test results'):]
                elif sampleText.split()[0] == 'test':
                    sampleLocation = ''
                    sampleText = sampleText[3:]
                else:
                    try:
                        sampleEnd = sampleText.index(': ')
                        # We'll pull out the location of the sample here
                        sampleLocation = sampleText[:sampleEnd]
                        sampleText = sampleText[sampleEnd + 2:]
                    except Exception as e:
                        continue

                print(sampleLocation)
                print(sampleText)
                print(fullTest)
                sampleTextStart = 0
                if 'estrogen receptor|' in sampleText:
                    sampleTextStart = sampleText.index('estrogen receptor|')
                if 'progesterone receptor' in sampleText:
                    sampleText = sampleText.replace('progesterone receptor', '. . progesterone receptor')
                    sampleText = sampleText.replace('estrogen receptor and . . progesterone receptor', '. . estrogen receptor and progesterone receptor')
                elif ' er ' in sampleText:
                    sampleTextStart = sampleText.index(' er ')
                if 'allred score: %' in sampleText:
                    sampleTextEnd = sampleText.index('allred score: %')
                    sampleText = sampleText[sampleTextStart: sampleTextEnd]
                if 'allred score' in sampleText:
                    sampleText = sampleText.replace('allred score', '. . allred score')
                elif 'intensity score' in sampleText:
                    sampleTextEnd = sampleText.index('intensity score')
                    sampleText = sampleText[sampleTextStart: sampleTextEnd]
                else:
                    sampleText = sampleText
                sampleText = sampleText.replace('||', ' . . ').replace('|', ' ').replace('er/pr', '').replace('however,', '')
                sampleText = sampleText.replace('for estrogen receptors,', 'for estrogen receptors.').replace('for progesterone receptors,', 'for progesterone receptors.')

                while '(proportion score' in sampleText:
                    proportionPart = sampleText[sampleText.index('(proportion score'):]
                    if ')' in proportionPart:
                        proportionEnd = proportionPart.index(')') + 2
                        sampleText = sampleText[:sampleText.index('(proportion score')] + sampleText[sampleText.index('(proportion score') + proportionEnd:] + ' . . '
                    else:
                        sampleText = sampleText[:sampleText.index('(proportion score')]

                while '/8 ' in sampleText:
                    sampleText = sampleText.replace('/8 ', '/8. . ')

                sampleText = sampleText.replace('/8.', '/8 .')

                while sampleText.endswith('.') or sampleText.endswith(' '):
                    sampleText = sampleText[:-1]

                sampleText = sampleText + '. '

                if 'test results:' in sampleText:
                    subsample = re.search('\s[a-z]\.\s', sampleText)
                    if subsample is None:
                        subsample = re.search('test results:', sampleText)
                    sampleText = sampleText[:subsample.start()]

                # This and the previous are spliiting up the a. and b. samples
                subsample = re.search('\s[a-z]\.\s', sampleText)
                if subsample is not None:
                    sampleText = sampleText[:subsample.start()]

                # We need to strip out extra commentary about negativitiy/positivity
                if 'immunocytochemical assay (erica):' in sampleText and 'percent positive:' in sampleText:
                    partBeforeErica = sampleText[:sampleText.index('immunocytochemical assay (erica):') + len('immunocytochemical assay (erica):')]
                    partAfterErica = sampleText[sampleText.index('percent positive:'):]
                    partInBetween = sampleText[sampleText.index('immunocytochemical assay (erica):') + len('immunocytochemical assay (erica):'):sampleText.index('percent positive:')]
                    if 'positive' in partInBetween and 'negative' in partInBetween:
                        partInBetween = ' positive, negative '
                    elif 'positive' in partInBetween:
                        partInBetween = ' positive '
                    elif 'negative' in partInBetween:
                        partInBetween = ' negative '
                    sampleText = partBeforeErica + partInBetween + partAfterErica

                if 'immunocytochemical assay (prica):' in sampleText and 'percent positive:' in sampleText:
                    partBeforePrica = sampleText[:sampleText.index('immunocytochemical assay (prica):') + len('immunocytochemical assay (prica):')]
                    partAfterPrica = sampleText[sampleText.rfind('percent positive:'):]
                    partInBetween = sampleText[sampleText.index('immunocytochemical assay (prica):') + len('immunocytochemical assay (prica):'):sampleText.rfind('percent positive:')]
                    if 'positive' in partInBetween and 'negative' in partInBetween:
                        partInBetween = ' positive, negative '
                    elif 'positive' in partInBetween:
                        partInBetween = ' positive '
                    elif 'negative' in partInBetween:
                        partInBetween = ' negative '
                    sampleText = partBeforePrica + partInBetween + partAfterPrica

                # And we're eliminating anything after the final receptor score
                sampleText = sampleText[:sampleText.rfind('8 ) . . ')]

                if 'note:' in sampleText:
                    print(sampleText)
                    partAfterNote = sampleText[sampleText.index('note:'):]
                    if 'allred' in partAfterNote:
                        sampleText = sampleText[:sampleText.index('note:')] + sampleText[sampleText.index('note:') + partAfterNote.index('allred'):]
                    else:
                        sampleText = sampleText[:sampleText.index('note:')]

                linesOfTest = sampleText.split('|')
                for lot in linesOfTest:
                    lot = lot + "\n"
                    while lot.startswith('.') or lot.startswith(' '):
                        lot = lot[1:]
                    if lot == '' or len(lot.strip()) == 0:
                        continue
                    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                    with open(file, 'w') as filetowrite:
                        filetowrite.write(lot)
                    results = metamapstringoutput()
                    # Turn this on to print results
                    # printResults()
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # print(lot)
                    # input()
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

        # Now we'll look by section: let's start with pathological diagnosis
        if 'pathological diagnosis' in lower:
            # We'll use these for concatenating sections later
            addedForward = False
            addedBackward = False
            addToEnd = False

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
                    if any(substring in lower for substring in erprNames):
                        aberrentTests.append(lower)
                        aberrentReasons.append('no signout')
                        print('aberrant')
                        ##input()
                    continue
            if any(substring in section for substring in erprNames):
                section = section.split('|')
                section = list(filter(None, section))
                fullTest = section
                testTech = ''
                for sec in range(0, len(section)):
                    section[sec] = ' ' + section[sec]
                    if addedForward == True:
                        addedForward = False
                        continue
                    if any(substring in section[sec] for substring in erprNames):
                        addedForward = False
                        addedBackward = False
                        if addToEnd:
                            continue
                        bit = section[sec]
                        if 'provided immunohistochemical staining' in section[sec]:
                            addToEnd = True
                            for nextSec in range(sec + 1, len(section)):
                                bit = bit + ' ' + section[nextSec]
                            bit = bit.replace('while', ' . . ').replace('cells.', 'cells. .')
                            # print(bit)
                            # print('here!')
                            # input()
                        if 'negative' not in section[sec] and 'positive' not in section[sec] and 'equivocal' not in section[sec] and sec > 0:
                            if 'negative' in section[sec - 1] or 'positive' in section[sec - 1] or 'equivocal' in section[sec - 1]:
                                addedBackward = True
                                bit = section[sec - 1] + ' ' + bit
                        if not section[sec].endswith('.') and not section[sec].endswith('results:') and sec < len(section) - 1:
                            if '. ' in section[sec + 1][2:]:
                                addedForward = True
                                bit = bit + ' ' + section[sec + 1]
                        if '(' in section[sec] and ')' not in section[sec] and not addedForward:
                            bit = bit + ' ' + section[sec + 1]

                        if ' % of tumor cells' in bit and not addedForward and len(section) - 1 > sec:
                            bit = bit + ' ' + section[sec + 1]
                            if len(section)-1 > sec + 1:
                                bit = bit + ' ' + section[sec + 2]
                        # Now that we've got all the possible bits, screen out the sentences with er/pr
                        bitsplit = bit.split('. ')
                        bit = ''
                        for b in bitsplit:
                            b = ' ' + b
                            if any(substring in b for substring in erprNames):
                                bit = bit + ' ' + b
                        if 'pending' not in bit and 'in progress' not in bit and 'will be reported' not in bit and 'will be performed' not in section[
                            sec] and 'please do' not in bit and 'criteria for' not in bit\
                                and 'are ordered' not in bit  and 'gene copy' not in bit \
                                and 'template' not in bit and 'formalin fixed' not in bit and 'are reported' not in bit \
                                and 'were characterized' not in bit and 'immunohistochemical staining for her2/neu is interpreted as' not in bit \
                                and 'will follow' not in bit:
                            bit = bit.replace(' - ', ' . . ').replace('immunohistochemical', 'ihc').replace('er:', 'er').replace('pr:', 'pr').replace(');', ').')
                            if ') and' in bit:
                                bit = bit.replace(') and', '). . and')
                            if '+) ' in bit:
                                bit = bit.replace('+) ', '+) . . ')
                            if ') ' in bit:
                                bit = bit.replace(') ', ') . . ')
                            if 'negative,' in bit:
                                bit = bit.replace('negative,', 'negative. . ')
                            if 'positive,' in bit:
                                bit = bit.replace('positive,', 'positive. .')
                            # Experimental - let's see if we can find things like ' b ' and replace them with ' b. '
                            potentialSpots = re.findall('\s[b-j]\s', bit)
                            for spot in potentialSpots:
                                bit = bit.replace(spot, spot[:-1] + '. ')
                            bit = re.sub('\|[a-z]\.\s', '|', bit)
                            bit = re.sub('\s[a-z]\.\s', '|', bit)
                            while bit.startswith('.') or bit.startswith(' '):
                                bit = bit[1:]
                            linesOfTest = bit.split('|')
                            for lot in linesOfTest:
                                lot = lot + "\n"
                                while lot.startswith('.') or lot.startswith(' '):
                                    lot = lot[1:]
                                if lot == '' or len(lot.strip()) == 0:
                                    continue
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
                                for index, row in results.iterrows():
                                    bioResult = ', '.join(row['Biomarker'])
                                    conResult = ', '.join(row['Concept'])
                                    numResult = ', '.join(row['Numeric'])
                                    qualResult = ', '.join(row['Qualifier'])
                                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType + ' - pathological diagnosis', sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode,
                                                    reportId,
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


        # Now we'll look by section: let's start with procedures
        if 'procedures/addenda' in lower:
            # We'll use these for concatenating sections later
            addedForward = False
            addedBackward = False

            resetDerived()
            print("gettin' into procedures")
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
                    section = section[:section.index('|||')]
                    testEnds.append(section.index('|||'))
                except:
                    if any(substring in lower for substring in erprNames):
                        aberrentTests.append(lower)
                        aberrentReasons.append('no signout')
                        print('aberrant')
                        ##input()
                    continue
            if any(substring in section for substring in erprNames):
                fullTest = section
                testTech = ''
                section = section.split('|')
                section = list(filter(None, section))
                for sec in range(0, len(section)):
                    if addedForward:
                        addedForward = False
                        continue
                    section[sec] = ' ' + section[sec]
                    if any(substring in section[sec] for substring in erprNames):
                        bit = section[sec]
                        addedForward = False
                        addedBackward = False
                        if 'negative' not in section[sec] and 'positive' not in section[sec] and 'equivocal' not in section[sec] and sec > 0:
                            if 'negative' in section[sec - 1] or 'positive' in section[sec - 1] or 'equivocal' in section[sec - 1]:
                                addedBackward = True
                                bit = section[sec - 1] + ' ' + bit
                            elif sec < len( section) - 1:
                                if 'negative' in section[sec + 1] or 'positive' in section[sec + 1] or 'equivocal' in section[sec + 1]:
                                    addedForward = True
                                    bit = bit + ' ' +  section[sec + 1]
                        if not section[sec].endswith('.') and not section[sec].endswith('results:') and sec < len(section) - 1 and not addedForward:
                            if '. ' in section[sec + 1][2:]:
                                addedForward = True
                                bit = bit + ' ' + section[sec + 1]
                        if '(' in section[sec] and ')' not in section[sec] and not addedForward:
                            bit = bit + ' ' + section[sec + 1]
                        if ' % of tumor cells' in bit and not addedForward and len(section) - 1 > sec:
                            bit = bit + ' ' + section[sec + 1]
                            if len(section)-1 > sec + 1:
                                bit = bit + ' ' + section[sec + 2]                        # Now that we've got all the possible bits, screen out the sentences with er/pr
                        bitsplit = bit.split('.')
                        bit = ''
                        for b in bitsplit:
                            if any(substring in b for substring in erprNames):
                                bit = bit + ' ' + b
                        if 'pending' not in bit and 'in progress' not in bit and 'will be reported' not in bit and 'will be performed' not in section[
                            sec] and 'please do' not in bit and 'criteria for' not in bit\
                                and 'are ordered' not in bit  and 'gene copy' not in bit \
                                and 'template' not in bit and 'formalin fixed' not in bit and 'are reported' not in bit \
                                and 'were characterized' not in bit and 'immunohistochemical staining for her2/neu is interpreted as' not in bit \
                                and 'will follow' not in bit:
                            bit = bit.replace(' - ', ' . . ').replace('immunohistochemical', 'ihc').replace('er:', 'er').replace('pr:', 'pr').replace(');', ').')
                            if '+)' in bit:
                                bit = bit.replace('+)', '+) . .')
                            elif ') ' in bit:
                                bit = bit.replace(') ', ') . . ')
                            if 'negative,' in bit:
                                bit = bit.replace('negative,', 'negative. . ')
                            if 'positive,' in bit:
                                bit = bit.replace('positive,', 'positive. . ')

                            # Experimental - let's see if we can find things like ' b ' and replace them with ' b. '
                            potentialSpots = re.findall('\s[b-j]\s', bit)
                            for spot in potentialSpots:
                                bit = bit.replace(spot, spot[:-1] + '. ')

                            bit = re.sub('\|[a-z]\.\s', '|', bit)
                            bit = re.sub('\s[a-z]\.\s', '|', bit)

                            while bit.startswith('.') or bit.startswith(' '):
                                bit = bit[1:]

                            linesOfTest = bit.split('|')
                            for lot in linesOfTest:
                                lot = lot + "\n"
                                while lot.startswith('.') or lot.startswith(' '):
                                    lot = lot[1:]
                                if lot == '' or len(lot.strip()) == 0:
                                    continue
                                file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
                                with open(file, 'w') as filetowrite:
                                    filetowrite.write(lot)
                                results = metamapstringoutput()
                                # Turn this on to print results
                                # print(bit)
                                # printResults()
                                # input()
                                # Turn this on to look at the whole test
                                # print(spacelower)
                                # #input()
                                for index, row in results.iterrows():
                                    print("PROCEDURES/ADDENDA")
                                    bioResult = ', '.join(row['Biomarker'])
                                    conResult = ', '.join(row['Concept'])
                                    numResult = row['Numeric']
                                    qualResult = ', '.join(row['Qualifier'])
                                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType + ' - procedures', sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode,
                                                    reportId,
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

        if any(substring in lower for substring in erprNames):
            extraTests.append(lower.replace('|',"\n"))
            exStrings = []
            for subz in erprNames:
                if subz in lower:
                    exStrings.append(subz)
            exStrings = ', '.join(exStrings)
            extraStrings.append(exStrings)
            print(lower)



wrongTests = pd.DataFrame(list(zip(extraTests, extraStrings)), columns=['text', 'biomarker strings in report'])
wrongTests.to_csv("~/Desktop/LatestNLP/Unstructured Results/ExtrasOfERPR.csv", index=False)

wrongwayTest = pd.DataFrame(list(zip(wrongwayTests, wrongwayReasons)), columns=['test', 'reason'])
wrongwayTest.to_csv("~/Desktop/LatestNLP/Unstructured Results/MalformedOfERPR.csv", index=False)

aberrentTest = pd.DataFrame(list(zip(aberrentTests, aberrentReasons)), columns=['test', 'reason'])
aberrentTest.to_csv("~/Desktop/LatestNLP/Unstructured Results/ErrorsOfERPR.csv", index=False)

failed = pd.DataFrame(list(zip(failedTests, failedReasons)), columns=['text', 'reason'])
failed.to_csv("~/Desktop/LatestNLP/Unstructured Results/FailedOfERPR.csv", index=False)

rawResults = pd.DataFrame(list(zip(biomarkerResultList, conceptResultList, numericResultList, qualifierResultList,
                                   firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionList, testTypeList, sampleLocationList,
                                   pathologistList, dateOrderedList, dateReportedList, testTextList, fullTextList, icdCodeList, patientIdList, reportIdList)),
                          columns=['biomarker', 'concept', 'numeric', 'qualifier', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accession', 'testType',
                                   'sampleLocation', 'pathologist', 'dateOrdered', 'dateReported', 'testText', 'fullText', 'icdCode', 'patientId', 'reportId'])

rawResults = rawResults.applymap(lambda x: ','.join(x) if isinstance(x, list) else x)

rawResults = rawResults.drop_duplicates()
rawResults = rawResults.reset_index()

rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/RawOfERPR.csv", index=False)

print("ALSO CHECK THESE")
print(reportsToCheck)