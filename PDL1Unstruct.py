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

throwaways = []

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
#for x in range(150100, len(pathReports['description'])):
#    try:
    if x % 100 == 0:
        print(x, ' of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    # if reportId != 'd0e05353-530d-4b02-a768-fb96593d9843':
    #       continue
    lower = str(pathReports['description'][x]).lower()
    lower = re.sub(' +', ' ', lower)
    # Here we're removing certain unhelpful strings
    lower = lower.replace('\\\\t\\\\', '')
    # We never want an '=' without a space after it
    regexp = re.compile('=[0-9]+')
    if regexp.search(lower):
        lower = re.sub('(=)([0-9]+)', '\\1 \\2', lower)

    # This is a billing code
    lower = lower.replace('pdl1-m', '')
    # This is a treatment regimen
    lower = lower.replace('anti-pd-l1', '')
    # MAYBE INVESTIGATE?
    # This spelling error happens a lot(?)
    lower = lower.replace(' l1(22c3):', 'pd-l1(22c3):')
    # This is an ICD code and who cares
    lower = lower.replace('pdl1: 88360', '')
    # Let's make sure the tests are in order!
    lower = lower.replace('pd-l1 (28-8), pd-l1 (22c3), molecular', 'pd-l1 (22c3, 28-8), molecular')
    # Why not just put in the hyphen here
    lower = lower.replace('pdl1', 'pd-l1')
    # This one sometimes ends up in brackets
    lower = lower.replace('[sp142]', '(sp142)')
    # Bad spacing
    lower = lower.replace('pd-l1 (22c3) , m', 'pd-l1 (22c3), m')
    # No losing the .m.d. to spacing
    lower = lower.replace('|m.d.', 'm.d.')

    splitReport = lower.split('\n')
    # These reports are truncated and don't contain info - NONE have pd-l1
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

    # We're going to look for anything in 'pd-l1', since there are a lot of things these can be called
    if 'pd-l1' in lower or 'pdl1' in lower or 'pd l1' in lower:
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
        enterlower = lower
        spacelower = lower.replace('\n', ' ')
        lower = lower.replace('\n', '|').replace('over expression', 'overexpression')
        lower = lower.replace('|| pd-l1.||||', '')
        lower = lower.replace('pd-l1|(22c3)', 'pd-l1 (22c3)')
        lower = lower.replace('pd-l1|(28-8)', 'pd-l1 (28-8)')

        ###########
        ###########
        ###########
        if 'pd-l1 22c3, pd-l1 28-8; molecular pathology and genomic test' in spacelower or 'pd-l1(22c3 28-8)molecular pathology and genomic test' in spacelower \
                or 'pd-l1 (22c3 and 28-8); molecular pathology and genomic test' in spacelower or 'pd-l1 (22c3, 28-8), molecular pathology and genomic test' in spacelower \
                or 'pd-l1(22c3,28-8), molecular pathology and genomic test' in spacelower or 'pd-l1(22c328-8) molecular pathology and genomic test' in spacelower or \
                'pd-l1 (22c3 and 28-8)' in spacelower or 'pd-l1 (22c3) and (28-8), m' in spacelower:
            # Let's do some transforms to already recognized test formats rather than add in extra conditions!
            lower = lower.replace('pd-l1 (22c3 and 28-8); molecular', 'pd-l1(22c3 28-8)molecular')
            spacelower = spacelower.replace('pd-l1 (22c3 and 28-8); molecular', 'pd-l1(22c3 28-8)molecular')

            lower = lower.replace('pd-l1 (22c3, 28-8), molecular', 'pd-l1(22c3 28-8)molecular')
            spacelower = spacelower.replace('pd-l1 (22c3, 28-8), molecular', 'pd-l1(22c3 28-8)molecular')

            lower = lower.replace('pd-l1(22c3,28-8), molecular', 'pd-l1(22c3 28-8)molecular')
            spacelower = spacelower.replace('pd-l1(22c3,28-8), molecular', 'pd-l1(22c3 28-8)molecular')

            lower = lower.replace('pd-l1(22c328-8) molecular', 'pd-l1(22c3 28-8)molecular')
            spacelower = spacelower.replace('pd-l1(22c328-8) molecular', 'pd-l1(22c3 28-8)molecular')

            lower = lower.replace('pd-l1 (22c3) and (28-8), m', 'pd-l1(22c3 28-8)m')
            spacelower = spacelower.replace('pd-l1 (22c3) and (28-8), m', 'pd-l1(22c3 28-8)m')

            if 'pd-l1(22c3 28-8)molecular pathology and genomic test' in spacelower and 'pd-l1 22c3, pd-l1 28-8; molecular pathology and genomic test' in spacelower:
                if spacelower.index('pd-l1 22c3, pd-l1 28-8; molecular pathology and genomic test') < spacelower.index('pd-l1(22c3 28-8)molecular pathology and genomic test'):
                    intro = 'pd-l1 22c3'
                else:
                    intro = 'pd-l1(22c3'
            elif 'pd-l1(22c3 28-8)molecular pathology and genomic test' in spacelower:
                intro = 'pd-l1(22c3'
            elif 'pd-l1 (22c3 and 28-8)' in spacelower:
                intro = 'pd-l1 (22c3'
            else:
                intro = 'pd-l1 22c3'

            resetDerived()
            print("pd-l1 22c3, pd-l1 28-8; molecular pathology and genomic test")
            # input()
            testStarts = []
            testEnds = []
            testType = 'pd-l1 22c3, pd-l1 28-8'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener:]
            if 'pathologist|' in fullTest:
                fullTestEnd = fullTest.index('pathologist|')
                fullTest = fullTest[:fullTestEnd + len('pathologist')]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                pathologist = re.search('out\*\*\*\|', fullTest)
                pathologist = fullTest[pathologist.start() + len('out***|'):].strip()

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            if 'results-comments' in fullTest:
                fullTest = fullTest[:fullTest.index('results-comments')]
            if '|a.' in fullTest:
                samples = re.finditer('\|[a-z]\.\s', fullTest)
            else:
                # samples = re.finditer('\|[1-9]\.\s', fullTest)
                samples = re.finditer('interpretation', fullTest)
            for sample in samples:
                # 22c3 is the first sample
                sampleText = fullTest[sample.end():]
                # This stops us from taking a truncated version of things
                if '22c3' not in sampleText:
                    lower = lower.replace(sampleText, '')
                    continue
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                # I've found that pd-l1(22c328-8) means just 22c3. Odd!
                sampleText = sampleText.replace('pd-l1(22c328-8', 'pd-l1(22c3')
                sampleText = sampleText.replace('pd-l1(22c3)', 'pd-l1 (22c3)').replace('pd-l1(28-8)', 'pd-l1 (28-8)')
                sampleText = sampleText.replace('pd-l1 ihc 22c3 pharmdx assay', 'pd-l1 (22c3)').replace('pd-l1 ihc 28-8 pharmdx assay', 'pd-l1 (28-8)')
                sampleText = sampleText.replace(' 22c3 pharmdx assay:', 'pd-l1 (22c3)').replace(' 28-8 pharmdx assay:', 'pd-l1 (28-8)')
                print(sampleText)
                try:
                    sampleStart = sampleText.index('pd-l1 (22c3)')
                except:
                    try:
                        sampleStart = sampleText.index('pd-l1 22c3')
                    except:
                        try:
                            sampleStart = sampleText.index('|22c3|')
                        except:
                            sampleStart = 999
                try:
                    sampleEnd = sampleText.index(']')
                except:
                    try:
                        sampleEnd = sampleText.index(')||')
                    except:
                        sampleEnd = sampleText.index('|| ')
                if sampleStart == 999:
                    sample1 = ''
                else:
                    sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                try:
                    sampleStart = sampleText.index('pd-l1 28-8')
                except:
                    try:
                        sampleStart = sampleText.index('pd-l1 (28-8)')
                    except:
                        try:
                            sampleStart = sampleText.index('|28-8|')
                        except:
                            sampleStart = 999
                if sampleStart == 999:
                    sample2Text = ''
                else:
                    sample2Text = sampleText[sampleStart:]
                    try:
                        sampleEnd = sample2Text.index(']')
                    except:
                        sampleEnd = sample2Text.index('|||')
                    sample2 = sample2Text[:sampleEnd]
                sample2 = sample2.replace('|', ' ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')

            for sam in [sample1, sample2]:
                linesOfTest = [sam]
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
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
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if any(x in spacelower for x in ['pd-l1(22c3); molecular pathology and genomic test', 'pd-l1 (22c3), molecular pathology', 'pd-l1 (22c3); molecular pathology',
                                         'pd-l1(22c3), molecular pathology and genomic test', 'pd-l1(22c3) molecular pathology and genomic test',
                                         'pd-l1 (22c3) molecular pathology and genomic test']):
            resetDerived()
            spacelower = spacelower.replace('pd-l1(22c3) molecular pathology and genomic test', 'pd-l1(22c3); molecular pathology and genomic test')
            spacelower = spacelower.replace('pd-l1 (22c3) molecular pathology and genomic test', 'pd-l1 (22c3); molecular pathology and genomic test')
            if ('pd-l1(22c3); molecular pathology and genomic test' in spacelower or 'pd-l1(22c3), molecular pathology and genomic test' in spacelower) \
                    and ('pd-l1 (22c3); molecular pathology' in spacelower or 'pd-l1 (22c3), molecular pathology' in spacelower):
                if spacelower.index('pd-l1(22c3)') < spacelower.index('pd-l1 (22c3)'):
                    intro = 'pd-l1(22c3)'
                else:
                    intro = 'pd-l1 (22c3)'
            elif 'pd-l1(22c3); molecular pathology and genomic test' in spacelower or 'pd-l1(22c3), molecular pathology and genomic test' in spacelower:
                intro = 'pd-l1(22c3)'
            else:
                intro = 'pd-l1 (22c3)'
            testStarts = []
            testEnds = []
            testType = 'pd-l1 22c3'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener:]
            if 'pathologist|' in fullTest:
                fullTestEnd = fullTest.index('pathologist|')
                fullTest = fullTest[:fullTestEnd + len('pathologist')]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                pathologist = re.search('out\*\*\*\|', fullTest)
                pathologist = fullTest[pathologist.start() + len('out***|'):].strip()

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('\|[a-z]\.\s', fullTest)
            sample1 = ''
            for sample in samples:
                # 22c3 is the first sample
                sampleText = fullTest[sample.end():]
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                sampleStart = sampleText.index(intro)
                try:
                    sampleEnd = sampleText.index(']')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            if sample1 == '':
                start = fullTest.index('interpretation') + len('interpretation')
                sample1 = fullTest[start:start + fullTest.index('|||')]

            for sam in [sample1]:
                linesOfTest = [sam]
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
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
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if any(x in spacelower for x in ['pd-l1 (22c3) expression by immunohistochemistry']):
            resetDerived()
            if 'pd-l1 (22c3) expression by immunohistochemistry' in spacelower:
                intro = 'pd-l1 (22c3)'
            print("pd-l1(22c3); expression by immunohistochemistry")
            print(lower)
            # input()
            testStarts = []
            testEnds = []
            testType = 'pd-l1 22c3'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener - 40:]
            if 'pathologist|' in fullTest:
                fullTestEnd = fullTest.index('pathologist|')
                fullTest = fullTest[:fullTestEnd + len('pathologist')]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                pathologist = re.search('out\*\*\*\|', fullTest)
                pathologist = fullTest[pathologist.start() + len('out***|'):].strip()

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            if '|a: ' in fullTest:
                samples = re.finditer('\|[a-z]\:\s', fullTest)
            else:
                samples = re.finditer('\s[a-z]\:\s', fullTest)
            for sample in samples:
                # 22c3 is the first sample
                sampleText = fullTest[sample.end():]
                if 'interpretation' not in sampleText:
                    print('no interp')
                    sample1 = ''
                    continue
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                sampleStart = sampleText.index('interpretation')
                try:
                    sampleEnd = sampleText.index(']')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            for sam in [sample1]:
                linesOfTest = [sam]
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
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
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if any(x in spacelower for x in ['pd-l1 (28-8) expression by immunohistochemistry']):
            resetDerived()
            if 'pd-l1 (28-8) expression by immunohistochemistry' in spacelower:
                intro = 'pd-l1 (28-8)'
            print("pd-l1(28-8); expression by immunohistochemistry")
            print(lower)
            # input()
            testStarts = []
            testEnds = []
            testType = 'pd-l1 28-8'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener - 40:]
            if 'pathologist|' in fullTest:
                fullTestEnd = fullTest.index('pathologist|')
                fullTest = fullTest[:fullTestEnd + len('pathologist')]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                pathologist = re.search('out\*\*\*\|', fullTest)
                pathologist = fullTest[pathologist.start() + len('out***|'):].strip()

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            if '|a: ' in fullTest:
                samples = re.finditer('\|[a-z]\:\s', fullTest)
            else:
                samples = re.finditer('\s[a-z]\:\s', fullTest)
            for sample in samples:
                # 28-8 is the first sample
                sampleText = fullTest[sample.end():]
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                if 'interpretation' not in sampleText:
                    print('no interp')
                    sample1 = ''
                    continue
                sampleStart = sampleText.index('interpretation')
                try:
                    sampleEnd = sampleText.index(']')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            for sam in [sample1]:
                linesOfTest = [sam]
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
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
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if any(x in spacelower for x in ['pd-l1 immunohistochemistry (ihc) analysis (ventana sp142)']):
            resetDerived()
            if 'sp142)' in spacelower:
                intro = 'sp142)'
            print("pd-l1 immunohistochemistry (ihc) analysis (ventana sp142)")
            print(lower)
            # input()
            testStarts = []
            testEnds = []
            testType = 'pd-l1 ventana sp142'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener - 80:]
            print(fullTest)
            # input()
            if '***ele' in fullTest:
                fullTestEnd = fullTest.index('***ele')
                fullTest = fullTest[:fullTestEnd]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                for bt in fullTest.split('|'):
                    if 'pathologist' in bt or ' phd' in bt or ' m.d.' in bt:
                        pathologist = bt

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('interpretation', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                sampleStart = sampleText.index(intro)
                try:
                    sampleEnd = sampleText.index('(proportion')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' . ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            for sam in [sample1]:
                linesOfTest = [sam]
                # print(linesOfTest)
                # input()
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
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
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if any(x in spacelower for x in ['pd-l1 (sp142), molecular', 'pd-l1(sp142), molecular', 'pd-l1 (sp142)', 'pd-l1(sp142)']):
            resetDerived()
            if 'sp142)' in spacelower:
                intro = 'sp142)'
            print("pd-l1 immunohistochemistry (ihc) analysis (ventana sp142)")
            print(lower)
            # input()
            testStarts = []
            testEnds = []
            testType = 'pd-l1 ventana sp142'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener - 80:]
            if '***ele' in fullTest:
                fullTestEnd = fullTest.index('***ele')
                fullTest = fullTest[:fullTestEnd]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                for bt in fullTest.split('|'):
                    if 'pathologist' in bt or ' phd' in bt or ' m.d.' in bt:
                        pathologist = bt

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('interpretation\|', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                sampleStart = 0
                try:
                    sampleEnd = sampleText.index('(proportion')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' . ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            for sam in [sample1]:
                linesOfTest = [sam]
                # print(linesOfTest)
                # input()
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
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
                lower = lower[:testStarts[r] - 10] + lower[testEnds[r] - 10:]
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if 'molecular pathology and genomic test: |her-2, pd-l1 22c3, mmr (msi)|' in lower:
            resetDerived()
            if 'molecular pathology and genomic test:  her-2, pd-l1 22c3, mmr (msi)' in spacelower:
                intro = 'her-2, pd-l1 22c3, mmr (msi)'
            print('her-2, pd-l1 22c3, mmr (msi)')
            print(lower)
            # input()
            testStarts = []
            testEnds = []
            testType = 'her-2, pd-l1 22c3, mmr (msi)'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener - 80:]
            if '***ele' in fullTest:
                fullTestEnd = fullTest.index('***ele')
                fullTest = fullTest[:fullTestEnd]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                for bt in fullTest.split('|'):
                    if 'pathologist' in bt or ' phd' in bt or ' m.d.' in bt:
                        pathologist = bt

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('interpretation', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                sampleStart = 0
                try:
                    sampleEnd = sampleText.index('(proportion')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' . ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            for sam in [sample1]:
                linesOfTest = [sam]
                # print(linesOfTest)
                # input()
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
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
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if '|pd-l1|date ordered:' in lower:
            resetDerived()
            intro = 'pd-l1|date ordered:'
            print('pd-l1')
            print(lower)
            # input()
            testStarts = []
            testEnds = []
            testType = 'pd-l1'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener:]
            if '***ele' in fullTest:
                fullTestEnd = fullTest.index('***ele')
                fullTest = fullTest[:fullTestEnd]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                for bt in fullTest.split('|'):
                    if 'pathologist' in bt or ' phd' in bt or ' m.d.' in bt:
                        pathologist = bt

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('combined positive', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                sampleStart = 0
                try:
                    sampleEnd = sampleText.index('control')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' . ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            for sam in [sample1]:
                linesOfTest = [sam]
                # print(linesOfTest)
                # input()
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
                        qualResult = ', '.join(row['Qualifier'])
                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
                        biomarkerResultList.append(bioResult)
                        conceptResultList.append(conResult)
                        numericResultList.append(numResult)
                        qualifierResultList.append(qualResult)
            sampleLocation = ''
            testStarts.reverse()
            testEnds.reverse()
            for r in range(0, len(testStarts)):
                lower = lower[:testStarts[r]] + lower[testEnds[r]:]
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if 'pd-l1 immunohistochemistry (ihc) analysis (dako 22c3 pharmdx)' in lower:
            resetDerived()
            if 'pd-l1 immunohistochemistry (ihc) analysis (dako 22c3 pharmdx)' in spacelower:
                intro = 'pd-l1 immunohistochemistry (ihc) analysis (dako 22c3 pharmdx)'
            print('pd-l1 immunohistochemistry (ihc) analysis (dako 22c3 pharmdx)')
            print(lower)
            # input()
            testStarts = []
            testEnds = []
            testType = 'pd-l1 dako 22c3'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener - 80:]
            if '***ele' in fullTest:
                fullTestEnd = fullTest.index('***ele')
                fullTest = fullTest[:fullTestEnd]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                pathologist = ''
                for bt in fullTest.split('|'):
                    if 'pathologist' in bt or ' phd' in bt or ' m.d.' in bt:
                        pathologist = bt

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('pd-l1 immunohistochemistry', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.end():]
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                sampleStart = 0
                try:
                    sampleEnd = sampleText.index('tps companion')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' . ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            for sam in [sample1]:
                linesOfTest = [sam]
                # print(linesOfTest)
                # input()
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
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
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        if 'pd-l1 22c3 fda (keytruda)' in lower:
            resetDerived()
            if 'pd-l1 22c3 fda (keytruda)' in spacelower:
                intro = 'pd-l1 22c3 fda (keytruda)'
            print('pd-l1 22c3 fda (keytruda)')
            print(lower)
            # input()
            testStarts = []
            testEnds = []
            testType = 'pd-l1 22c3 (keytruda)'
            testTech = 'ihc'
            opener = lower.index(intro)
            fullTest = lower[opener - 80:]
            if '***ele' in fullTest:
                fullTestEnd = fullTest.index('***ele')
                fullTest = fullTest[:fullTestEnd]
            else:
                aberrentTests.append(fullTest)
                aberrentReasons.append('no pathologist')
                lower = lower[:opener] + lower[opener + len(intro):]
                continue
            testStarts.append(opener)
            testEnds.append(opener + fullTestEnd)
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
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                if 'pending' in reportedDate:
                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, sampleText, lower, icdCode, reportId,
                                    patientId)
                    biomarkerResultList.append('pd-l1')
                    conceptResultList.append('')
                    numericResultList.append('')
                    qualifierResultList.append('pending')
                    lower = lower[:opener] + lower[opener + len(intro):]
                    continue
                pathologist = ''
                for bt in fullTest.split('|'):
                    if 'pathologist' in bt or ' phd' in bt or 'm.d.' in bt:
                        pathologist = bt

            else:
                orderedDate = ''
                reportedDate = ''
            # Now let's find all the samples:
            samples = re.finditer('pd-l1 22c3 fda \(keytruda\) for nsclc:', fullTest)
            for sample in samples:
                sampleText = fullTest[sample.start():]
                sampleText = sampleText.replace('pdl1', 'pd-l1')
                sampleStart = sampleText.index('pd-l1 22c3 fda')
                try:
                    sampleEnd = sampleText.index('tps companion')
                except:
                    sampleEnd = sampleText.index('|||')
                sample1 = sampleText[sampleStart:sampleEnd]
                # Now let's do some pre-processing:
                sample1 = sample1.replace('|', ' . ').replace('[', '. . ').replace(' d ', ' >').replace(' % ', '% ').replace('tps', 'tumor proportion score').replace('cps', 'combined positive score').replace('(cps)', '').replace(')=', ') = ')
                if ';' in sample1:
                    sample1 = sample1[sample1.index(';')+1:]

            for sam in [sample1]:
                linesOfTest = [sam]
                # print(linesOfTest)
                # input()
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
                    # input()
                    # Turn this on to look at the whole test
                    # print(spacelower)
                    # #input()

                    for index, row in results.iterrows():
                        bioResult = ', '.join(row['Biomarker'])
                        conResult = ', '.join(row['Concept'])
                        numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
                        qualResult = ', '.join(row['Qualifier'])
                        ######
                        # TEMP
                        ######
                        biomarkerResultList.append(bioResult)
                        conceptResultList.append(conResult)
                        numericResultList.append(numResult)
                        qualifierResultList.append(qualResult)
                        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode, reportId,
                                    patientId)
            # Now we're going to snip all those tests out of the overall report!
            sampleLocation = ''
            testStarts.reverse()
            testEnds.reverse()
            for r in range(0, len(testStarts)):
                lower = lower[:testStarts[r]] + lower[testEnds[r]:]
                spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        # Next it seems like 'procedures/addenda' is the place to be
        if 'procedures/addenda' in lower and ('pd-l1' in lower or 'pdl1' in lower or 'pd l1' in lower):
            resetDerived()
            sectionStarts = []
            sectionEnds = []
            testStarts = []
            testEnds = []
            testTech = ''
            testType = testType + ' - procedures/addenda'
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
                    if 'pdl1' in lower or 'pd-l1' in lower or 'pd l1' in lower:
                        aberrentTests.append(lower)
                        aberrentReasons.append('no signout')
                        print('aberrant')
                        ##input()
                    continue
            if 'pdl1' in section or 'pd-l1' in section or 'pd l1' in section:
                if 'results-comments' in section:
                    keep = section[:section.index('results-comments')]
                    throw = section[section.index('results-comments'):]
                    section = keep
                    if 'external slide review' in throw:
                        section = section + ' ' + throw
                    throwaways.append(throw)
                section = section.split('|')
                section = list(filter(None, section))
                for sec in section:
                    if 'pathologist' in sec or ' phd' in sec or 'm.d.' in sec or 'm.d' in sec:
                        pathologist = sec
                addedForward = False
                for sec in range(0, len(section)):
                    if addedForward:
                        addedForward = False
                        continue
                    if 'pdl1' in section[sec] or 'pd-l1' in section[sec] or 'pd l1' in section[sec] or 'tumor proportion score' in section[sec] or 'combined positive score' in section[sec]:
                        bit = section[sec]
                        # if 'negative' not in section[sec] and 'positive' not in section[sec] and 'equivocal' not in section[sec] and sec > 0:
                        #    if 'negative' in section[sec - 1] or 'positive' in section[sec - 1] or 'equivocal' in section[sec - 1]:
                        #        bit = section[sec - 1] + ' ' + bit
                        if not section[sec].endswith('.') and sec < len(section) - 1:
                            if '.' in section[sec + 1]:
                                addedForward = True
                                bit = bit + ' ' + section[sec + 1]
                            if '(' in section[sec] and ')' not in section[sec] and not addedForward:
                                addedForward = True
                                bit = bit + ' ' + section[sec + 1]
                        if 'pending' not in bit and 'in progress' not in bit and 'will be reported' not in bit and 'will be performed' not in section[
                            sec] and 'please do' not in bit \
                                and 'are ordered' not in bit and 'criteria for' not in bit and 'gene copy' not in bit \
                                and 'template' not in bit and 'formalin fixed' not in bit and 'are reported' not in bit \
                                and 'were characterized' not in bit and 'will follow' not in bit:
                            bit = bit.replace(' - ', ' . ').replace('immunohistochemical', 'ihc')
                            linesOfTest = bit.split('|')
                            for lot in linesOfTest:
                                fullTest = section
                                lot = lot + "\n"
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
                                # #input()
                                for index, row in results.iterrows():
                                    print("PROCEDURES/ADDENDA")
                                    bioResult = ', '.join(row['Biomarker'])
                                    conResult = ', '.join(row['Concept'])
                                    numResult = row['Numeric']
                                    qualResult = ', '.join(row['Qualifier'])
                                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode,
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
                    spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        # Next it seems like 'comment:' is the place to be
        if 'comment' in lower.replace('results-comments', '') and ('pd-l1' in lower or 'pdl1' in lower or 'pd l1' in lower):
            resetDerived()
            sectionStarts = []
            sectionEnds = []
            testStarts = []
            testEnds = []
            testTech = ''
            testType = testType + ' - comment'
            sectionStart = lower.index('comment')
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
                    if 'pdl1' in lower or 'pd-l1' in lower or 'pd l1' in lower:
                        aberrentTests.append(lower)
                        aberrentReasons.append('no signout')
                        print('aberrant')
                        ##input()
                    continue
            if 'pdl1' in section or 'pd-l1' in section or 'pd l1' in section:
                section = section.split('|')
                section = list(filter(None, section))
                addedForward = False
                for sec in section:
                    if 'pathologist' in sec or ' phd' in sec or 'm.d.' in sec:
                        pathologist = sec
                for sec in range(0, len(section)):
                    if addedForward:
                        addedForward = False
                        continue
                    if 'pdl1' in section[sec] or 'pd-l1' in section[sec] or 'pd l1' in section[sec]:
                        bit = section[sec]
                        # if 'negative' not in section[sec] and 'positive' not in section[sec] and 'equivocal' not in section[sec] and sec > 0:
                        #    if 'negative' in section[sec - 1] or 'positive' in section[sec - 1] or 'equivocal' in section[sec - 1]:
                        #        bit = section[sec - 1] + ' ' + bit
                        if not section[sec].endswith('.') and sec < len(section) - 1:
                            if '.' in section[sec + 1]:
                                addedForward = True
                                bit = bit + ' ' + section[sec + 1]
                            if '(' in section[sec] and ')' not in section[sec] and not addedForward:
                                addedForward = True
                                bit = bit + ' ' + section[sec + 1]
                            if section[sec].endswith(':') and not addedForward:
                                addedForward = True
                                bit = bit + ' ' + section[sec + 1]
                        if 'pending' not in bit and 'in progress' not in bit and 'will be reported' not in bit and 'will be performed' not in section[
                            sec] and 'please do' not in bit \
                                and 'are ordered' not in bit and 'criteria for' not in bit and 'gene copy' not in bit \
                                and 'template' not in bit and 'formalin fixed' not in bit and 'are reported' not in bit \
                                and 'were characterized' not in bit and 'will follow' not in bit:
                            bit = bit.replace(' - ', ' . ').replace('immunohistochemical', 'ihc')
                            linesOfTest = bit.split('|')
                            for lot in linesOfTest:
                                fullTest = section
                                lot = lot + "\n"
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
                                # #input()
                                for index, row in results.iterrows():
                                    print("Comments")
                                    bioResult = ', '.join(row['Biomarker'])
                                    conResult = ', '.join(row['Concept'])
                                    numResult = row['Numeric']
                                    qualResult = ', '.join(row['Qualifier'])
                                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode,
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
                    spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        # Next it seems like 'clinical history' is the place to be
        while 'clinical history' in lower and ('pd-l1' in lower or 'pdl1' in lower or 'pd l1' in lower):
            resetDerived()
            sectionStarts = []
            sectionEnds = []
            testStarts = []
            testEnds = []
            testTech = ''
            testType = testType + ' - clinical history'
            sectionStart = lower.index('clinical history')
            section = lower[sectionStart:]
            testStarts.append(sectionStart)
            try:
                testEnds.append(sectionStart + section.index('icd code(s)'))
                section = section[:section.index('icd code(s)')]
            except:
                try:
                    testEnds.append(section.index('||| '))
                    section = section[:section.index('||| ')]
                except:
                    if 'pdl1' in lower or 'pd-l1' in lower or 'pd l1' in lower:
                        print(lower)
                        aberrentTests.append(lower)
                        aberrentReasons.append('no signout')
                        print('aberrant')
                        lower = lower[:sectionStart] + lower[sectionStart + 10:]
                        ##input()
                    continue
            # If there are multiple 'clinical histories' and this one doesn't have pd-l1, move on
            if 'pdl1' not in section and 'pd-l1' not in section and 'pd l1' not in section:
                lower = lower.replace(section, '')
                continue

            if 'pdl1' in section or 'pd-l1' in section or 'pd l1' in section:
                section = section.split('|')
                section = list(filter(None, section))
                for sec in section:
                    if 'pathologist' in sec or ' phd' in sec or 'm.d.' in sec:
                        pathologist = sec
                for sec in range(0, len(section)):
                    if 'pdl1' in section[sec] or 'pd-l1' in section[sec] or 'pd l1' in section[sec]:
                        bit = section[sec]
                        if not section[sec].endswith('.') and sec < len(section) - 1:
                            if '.' in section[sec + 1]:
                                bit = bit + ' ' + section[sec + 1]
                            if '(' in section[sec] and ')' not in section[sec]:
                                bit = bit + ' ' + section[sec + 1]
                        if 'pending' not in bit and 'in progress' not in bit and 'will be reported' not in bit and 'will be performed' not in section[
                            sec] and 'please do' not in bit \
                                and 'are ordered' not in bit and 'criteria for' not in bit and 'gene copy' not in bit \
                                and 'template' not in bit and 'formalin fixed' not in bit and 'are reported' not in bit \
                                and 'were characterized' not in bit and 'will follow' not in bit:
                            bit = bit.replace(' - ', ' . ').replace('immunohistochemical', 'ihc').replace('immunohistochemistry', 'ihc')
                            linesOfTest = bit.split('|')
                            for lot in linesOfTest:
                                fullTest = section
                                lot = lot + "\n"
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
                                # #input()
                                for index, row in results.iterrows():
                                    print("DIAGNOSIS")
                                    bioResult = ', '.join(row['Biomarker'])
                                    conResult = ', '.join(row['Concept'])
                                    numResult = row['Numeric']
                                    qualResult = ', '.join(row['Qualifier'])
                                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode,
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
                    spacelower = lower.replace('\n', ' ')

        ###########
        ###########
        ###########
        # Next it seems like 'addendum diagnosis' is the place to be
        while 'addendum diagnosis' in lower and ('pd-l1' in lower or 'pdl1' in lower or 'pd l1' in lower):
            resetDerived()
            sectionStarts = []
            sectionEnds = []
            testStarts = []
            testEnds = []
            testTech = ''
            testType = testType + ' - addendum diagnosis'
            sectionStart = lower.index('addendum diagnosis')
            section = lower[sectionStart:]
            testStarts.append(sectionStart)
            try:
                testEnds.append(sectionStart + section.index('***elec'))
                section = section[:section.index('***elec')]
            except:
                try:
                    testEnds.append(section.index('||| '))
                    section = section[:section.index('||| ')]
                except:
                    if 'pdl1' in lower or 'pd-l1' in lower or 'pd l1' in lower:
                        aberrentTests.append(lower)
                        aberrentReasons.append('no signout')
                        print('aberrant')
                        ##input()
                    continue
            # If there are multiple 'clinical histories' and this one doesn't have pd-l1, move on
            if 'pdl1' not in section and 'pd-l1' not in section and 'pd l1' not in section:
                lower = lower.replace(section, '')
                continue

            if 'pdl1' in section or 'pd-l1' in section or 'pd l1' in section:
                section = section.split('|')
                section = list(filter(None, section))
                for sec in section:
                    if 'pathologist' in sec or ' phd' in sec or 'm.d.' in sec:
                        pathologist = sec
                for sec in range(0, len(section)):
                    if 'pdl1' in section[sec] or 'pd-l1' in section[sec] or 'pd l1' in section[sec]:
                        bit = section[sec]
                        if not section[sec].endswith('.') and sec < len(section) - 1:
                            if '.' in section[sec + 1]:
                                bit = bit + ' ' + section[sec + 1]
                            if '(' in section[sec] and ')' not in section[sec]:
                                bit = bit + ' ' + section[sec + 1]
                        if 'pending' not in bit and 'in progress' not in bit and 'will be reported' not in bit and 'will be performed' not in section[
                            sec] and 'please do' not in bit \
                                and 'are ordered' not in bit and 'criteria for' not in bit and 'gene copy' not in bit \
                                and 'template' not in bit and 'formalin fixed' not in bit and 'are reported' not in bit \
                                and 'were characterized' not in bit and 'will follow' not in bit:
                            bit = bit.replace(' - ', ' . ').replace('immunohistochemical', 'ihc').replace('immunohistochemistry', 'ihc')
                            linesOfTest = bit.split('|')
                            for lot in linesOfTest:
                                fullTest = section
                                lot = lot + "\n"
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
                                # #input()
                                for index, row in results.iterrows():
                                    print("ADDENDUM DIAGNOSIS")
                                    bioResult = ', '.join(row['Biomarker'])
                                    conResult = ', '.join(row['Concept'])
                                    numResult = row['Numeric']
                                    qualResult = ', '.join(row['Qualifier'])
                                    standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, lot, lower, icdCode,
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
                    spacelower = lower.replace('\n', ' ')

        if 'pd-l1' in lower or 'pdl1' in lower or 'pd l1' in lower:
            extraTests.append(lower)
        for listo in [biomarkerResultList, conceptResultList, numericResultList, qualifierResultList,
                                   firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionList, testTypeList, sampleLocationList,
                                   pathologistList, dateOrderedList, dateReportedList, testTextList, fullTextList, icdCodeList, patientIdList, reportIdList]:
            if len(listo) != len(firstNameList):
                print("HERE!")
                print(listo)
                print(firstNameList)
                input()

# print(extraTests)

# print(len(list(dict.fromkeys(mrnList))))
# print(list(dict.fromkeys(testTypeList)))
# print(totalTests)

wrongTests = pd.DataFrame(list(zip(extraTests)), columns=['text'])
wrongTests.to_csv("~/Desktop/LatestNLP/Unstructured Results//ExtrasOfPDL1.csv", index=False)

wrongwayTest = pd.DataFrame(list(zip(wrongwayTests, wrongwayReasons)), columns=['test', 'reason'])
wrongwayTest.to_csv("~/Desktop/LatestNLP/Unstructured Results//MalformedOfPDL1.csv", index=False)

aberrentTest = pd.DataFrame(list(zip(aberrentTests, aberrentReasons)), columns = ['test', 'reason'])
aberrentTest.to_csv("~/Desktop/LatestNLP/Unstructured Results//ErrorsOfPDL1.csv", index=False)

failed = pd.DataFrame(list(zip(failedTests, failedReasons)), columns=['text', 'reason'])
failed.to_csv("~/Desktop/LatestNLP/Unstructured Results//FailedOfPDL1.csv", index=False)

rawResults = pd.DataFrame(list(zip(biomarkerResultList, conceptResultList, numericResultList, qualifierResultList,
                                   firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionList, testTypeList, sampleLocationList,
                                   pathologistList, dateOrderedList, dateReportedList, testTextList, fullTextList, icdCodeList, patientIdList, reportIdList)),
                          columns=['biomarker', 'concept', 'numeric', 'qualifier', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accession', 'testType',
                                   'sampleLocation', 'pathologist', 'dateOrdered', 'dateReported', 'testText', 'fullText', 'icdCode', 'patientId', 'reportId'])
rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results//RawOfPDL1.csv", index=False)

for throw in throwaways:
    print(throw)