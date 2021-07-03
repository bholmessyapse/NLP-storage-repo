import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput
from metamapLoader import metamapStarter
from metamapLoader import metamapCloser
from collections import Counter


# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# If false, this writes files. If true, it doesn't
testing = False

# Now beginning the sorting out! This points to the most recent file
pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/March2020HFHS.csv", low_memory=False)

# This is for tests that ended up with one of our biomarkers that didn't get parsed out somehow
testsToCheckList = []
testsToCheckTypeList = []

# This is for tests that I can't pull anything from
noContentSections = []

panelsTests = []

# This is for testing the addendum bits checked
addendumPiece = []

addendumLeftovers = []
addendumLeftoverIds = []
removedSections = []

processedSections = []
processedBits = []
noSectionsList = []

# Here's our regex. We want to find any biomarker name (include aliases if you think they will show up!)
# with whitespace or punctuation around it (so we want er/pr, :her2, her2:, etc.
regexp = re.compile(r'(?<=[ .\\\/,?!:\-;\n])(braf|kras|nras|hras|ntrk|msi|mss|tmb|tumor mutational burden|mlh1|msh2|msh6|pms2|apc|bmpr1a|epcam|grem1|mutyh|myh|smad4|skt11|lkb1)[ .\\\/,?!:\-;\r\n]')

# Putting this up front for ease of finding. Once we have our section extracted, we'll give it here.
# Moving all the formatting outside this call.
def extractBiom(text, testtype, pathol, dr, do):
    ttype = testtype
    pathologist = pathol
    reportedDate = dr
    orderedDate = do
    section = text
    addResults(section)

# Takes metamap output and adds it to the final results!
def addResults(reso):
    reso = reso.strip()
    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
    with open(file, 'w') as filetowrite:
        filetowrite.write(reso)
    if reso != '':
        res = metamapstringoutput()
        # print(results)
        # lot = section
        # Turn this on to print results
        # printResults()
        # input()
        # Turn this on to look at the whole test
        # print(spacelower)
        # print(lowerOrig)
        # print(reso)
        # print(res)
        # input()
        for index, row in res.iterrows():
            bioResult = ', '.join(row['Biomarker'])
            conResult = ', '.join(row['Concept'])
            numResult = ', '.join(row['Numeric'])
            qualResult = ', '.join(row['Qualifier'])
            standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, reso, lowerOrig, icdCode, reportId,
                            patientId)
            biomarkerResultList.append(bioResult)
            conceptResultList.append(conResult)
            numericResultList.append(numResult)
            qualifierResultList.append(qualResult)

# We don't get these results from metamap - they're pulled from the test at the beginning. This is the method to append them to the
# relevant lists.
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
    # print(fullTest)
    # print(results)
    # print(lot)
    print(orderedDate)
    print(reportedDate)
    print(sampleLocation)
    print(testType)
    # print(testTech)
    print(pathologist)


# This is where we take incoming sections and extract the results from them.
def processSection(text, testtype, pathol, dr, do):
    gotSomething = False
    text = text + '\n*endAdd*'
    text = text.replace('her-2', 'her2').replace('over expression', 'overexpression')
    # Keep going as long as there's any biomarkers of interest in this section
    while regexp.search(text):
        foundResult = False
        # Here, we're ingesting a section (or the whole test) that has one of the biomarkers of interest in it.
        # We'll want to break it into as many component parts as possible, and from there, decide how
        # to segment it. Segments with biomarkers of interest will be extracted.

        # interpretation should be the last one - last port of call
        subsectionheaders = ['microscopic description', 'interpretation: ', 'her2 fish results:', '\ncomments\n', 'nuc ish', 'er/pr, her2-neu', 'negative - ', 'ancillary studies',
                             'results-comments', 'the ratio of her2 ', 'scored for each probe.', 'result:\n', 'immunohistochemistry (performed', 'molecular genetic studies: performed',
                             'omim genes with a copy number loss at ', 'omim genes with a copy number gain at ', 'representative tumor block', '\nfollowing results:\n',
                             'resection:', 'her2 testing', 'pathologic stage classification', 'microsatellite stable', 'a limited panel of immunostains was performed',
                             'testing performed on case number:', 'cytogenetic impression:', 'immunohistochemistry microsatellite instability panel']

        subsectionenders = ['diagnosis of malignancy', 'results: ', '*endAdd*', 'a her2 to chromosome 17', 'checklist: breast', 'results-comments', 'icd code(s):', 'has been documentedx`',
                            '\ncomment\n', 'immunostaining for mmr protein expression was performed', 'test description:', 'testing performed on rna', 'sections of tumor',
                            'billing fee code(s)', 'analyte specific reagent (asr) disclaimer', 'slides from', 'these findings indicate', 'scoring criteria:', 'reference normal result:',
                            'sample adequate for analysis:', 'her2 fish results:', 'whether patients', 'the number of her2', 'her2 her2', 'the t(14;16) igh-maf', 'due to the results',
                            'this test was developed', 'the results suggest', 'likely results', 'normal result:', 'test performed on', 'differential diagnostic', 'was previously performed',
                            'omim genes with a copy number gain at', "genes (5'-3')", 'immunostains are performed', 'kras g12c ', 'kras hotspot mutations', 'kras codon 12 mutations',
                            'the tumor appears', 'two different results were noted ', 'checklist', 'molecular genetic studies: performed', 'notes:\n'
                            ]

        # Let's do any necessary text munging
        if ('\na)' in text and '\nb)' in text and '\na) ' not in text):
            for a in re.findall(r'\n[a-z]\)\S', text):
                lastChar = a[-1]
                text = text.replace(a, a[:-1] + ' ' + lastChar)
        # Remove common test names
        text = text.replace('microsatellite instability testing by immunohistochemistry', '')
        # Take out explanatory sections
        if 'submitted immunostains for' in text:
            if 'following results' not in text:
                if 'following\nresults:' in text:
                    text = text.replace('following\nresults:', 'following results:')
            if 'following results:' in text:
                text = text[text.index('following results:') + len('following results:'):]
            if '\n\n' in text:
                text = text[:text.index('\n\n')]
        # Let's look at removing some sections
        removalSectionStarts = ['analyte specific reagent (asr) disclaimer', 'testing description:', 'caution:', 'fda comment:', 'this is a somatic', 'test description:',
                                'type of service:', 'report comments \n']
        removalSectionEnds = ['testing.', 'caution:', 'fda comment:', 'criteria.', 'icd code(s)', 'antibody result', '***electronically', '*endAdd*', 'disclaimer:']
        if any(section in text for section in removalSectionStarts):
            for section in removalSectionStarts:
                if section in text:
                    removeSection = text[text.index(section):]
                    endPos = 9999999999
                    endChoice = ''
                    for endSec in removalSectionEnds:
                        if endSec in removeSection and removeSection.index(endSec) + len(endSec) < endPos and endSec not in section:
                            endPos = removeSection.index(endSec) + len(endSec)
                            endChoice = endSec
                    removeSection = removeSection[:endPos]
                    text = text.replace(removeSection, ' [removed section pt 1] ')
                    removedSections.append(removeSection)

        # Some titles can be split by newlines. Let's make sure that doesn't happen!
        if 'scored for each probe' in text.replace('\n', ' '):
            if 'scored for each probe' not in text:
                print(text)
                input()

        ##################
        # Sometimes we send JUST the results.
        ##################
        if not any(subs in text for subs in subsectionheaders):
            goodSec = ''
            goodSplit = []
            # if we start with 'comment', we want to go until there's a new number I THINK
            if text.strip().startswith('comment:'):
                if re.search("\n\s?([0-9]|[a-z])\.\s+", text):
                    text = text[re.search("\n\s?([0-9]|[a-z])\.\s+", text).start():]
                elif re.search("\n\s?([0-9]|[a-z])\.\)*", text):
                    text = text[re.search("\n\s?([0-9]|[a-z])\.\)*", text).start():]
            # These are paragraph-separated (and period-separated) sentences
            if '% of nuclei have' in text:
                goodSec = text[:text.index('slides from')]
                gotSomething = True
                extractBiom(goodSec, testtype, pathol, dr, do)
                text = text.replace(text, ' [removed section pt 2] ')
            # We strip out 'caution' too
            if 'caution:' in text:
                removeBit = text[text.index('caution:'):]
                if '\n\n' in removeBit:
                    removeBit = removeBit[:removeBit.index('\n\n')]
                text = text.replace(removeBit, ' [removed section pt 3] ')
            goodSec = ''
            # We're going to have the whole text in a list to begin with.
            # If we can split it by letter, or period, or newline, we'll do that.
            goodSplit = [text]
            # Let's first look for '1.' or 'a.'
            if re.search("\n\s?([0-9]|[a-z])\.\s+", text):
                goodSplit = []
                goodSec = re.split("\n\s?([0-9]|[a-z])\.\s+", text)
                for bit in goodSec:
                    if regexp.search(bit):
                        goodSplit.append(bit)
            # Let's also look for 'a)'
            for bit in goodSplit:
                if re.search("\n\s?([0-9]|[a-z])\.\)*", bit):
                    newSplit = []
                    for item in goodSplit:
                        if item != bit:
                            newSplit.append(item)
                        else:
                            goodSec = re.split("\n\s?([0-9]|[a-z])\)\s+", bit)
                            for gs in goodSec:
                                if regexp.search(gs):
                                    newSplit.append(gs)
                    goodSplit = newSplit
            # Now let's... try paragraph separation? Not sure
            for bit in goodSplit:
                if '\n\n' in goodSplit:
                    print(bit)
                    print('has paragraph!')
                    input()
            # Here let's see if we can split by period - if not, we'll split by line
            for bit in goodSplit:
                sampleBit = bit.replace('dr.', '').replace('. \n', '').replace('.\n', '')
                if len(sampleBit.split('.')) > 3:
                    newSplit = []
                    for item in goodSplit:
                        if item != bit:
                            newSplit.append(item)
                        else:
                            goodSec = bit.replace('dr.', 'dr').split('.')
                            for gs in goodSec:
                                gs = ' ' + gs
                                if regexp.search(gs) and not any(x in gs for x in ['test description']):
                                    newSplit.append(gs)
                                    text = text.replace(gs, ' [removed section pt 4] ')
                                else:
                                    text = text.replace(gs, ' [removed section pt 5] ')
                    goodSplit = newSplit
                # Couldn't split by period, let's go by line
                else:
                    newSplit = []
                    for item in goodSplit:
                        if item != bit:
                            newSplit.append(item)
                        else:
                            goodSec = bit.split('\n')
                            toAdd = ''
                            for gs in goodSec:
                                gs = ' ' + gs
                                pdl1Markers = ['tps', 'tumor proportion score', 'cps', 'combined positive score']
                                if regexp.search(gs) and not any(x in gs for x in ['test description', 'molecular pathology and genomic']):
                                    # Sometimes we split up pd-l1 and the results
                                    if 'pd-l1' in gs and not any(y in gs for y in pdl1Markers) and any(z in bit for z in pdl1Markers):
                                        gs = gs[gs.index('pd-l1'):]
                                        toAdd = gs
                                    elif any(y in gs for y in pdl1Markers) and toAdd != '':
                                        gs = toAdd + ' : ' + gs
                                        toAdd = ''
                                    if toAdd == '':
                                        newSplit.append(gs)
                                        text = text.replace(gs, ' [removed section pt 6] ')
                                else:
                                    text = text.replace(gs, ' [removed section pt 7] ')
                    goodSplit = newSplit
            for item in goodSplit:
                if regexp.search(item):
                    gotSomething = True
                    extractBiom(item, testtype, pathol, dr, do)
                    text = text.replace(item, ' [removed section pt 8] ')


        # At this point, we should only have sections left that will either have NO mention
        # of the biomarkers, or will have BIOMARKER RESULTS.
        while any(subs in text for subs in subsectionheaders):
            for sub in subsectionheaders:
                endr = '*endAdd*'
                if sub in text:
                    potentialSection = text[text.index(sub):]
                    if not any(subE in potentialSection for subE in subsectionenders):
                        print(potentialSection)
                        print(text)
                        print('NO ENDER FOR SECTION!')
                        subsectionpos = len(potentialSection)
                    else:
                        endOne = ''
                        subsectionpos = 999999999
                        for endr in subsectionenders:
                            if endr != sub and endr not in sub:
                                if endr in potentialSection:
                                    if potentialSection.index(endr) < subsectionpos:
                                        subsectionpos = potentialSection.index(endr)
                                        endOne = endr
                    potentialSection = potentialSection[:subsectionpos]
                    # here, our potential section does not have any biomarkers of interest in it
                    if not regexp.search(potentialSection) and 'microsatellite' not in potentialSection:
                        text = text.replace(potentialSection, '\n')
                    # Here, it DOES, and we want to extract them.
                    else:
                        goodSec = potentialSection
                        # This one is a reference
                        if sub in goodSec and sub in ['microsatellite stable']:
                            if '(j natl cancer' in goodSec:
                                text = text.replace(potentialSection, ' [removed section pt 9] ')
                                goodSec = ''
                        if sub in goodSec and sub not in ['nuc ish', 'er/pr, her2-neu', '\nnegative - ', 'microsatellite stable', 'the ratio of her2 ']:
                            goodSec = goodSec.replace(sub, ' [removed section pt 10] ')
                        # These sections are newline-delimited
                        if sub in ['\ncomments\n', 'nuc ish', 'er/pr, her2-neu', 'resection:', 'pathologic stage classification', 'her2 fish results:', 'the ratio of her2 ',
                                   'microsatellite stable', ' testing performed on case number:', 'ancillary studies', 'immunohistochemistry microsatellite instability panel',
                                   '\nfollowing results:\n']:
                            goodSplit = goodSec.split('\n')
                            goodSec = ''
                            for gs in goodSplit:
                                if regexp.search(gs) or 'nuc ish' in gs or 'centromere' in gs:
                                    goodSec = goodSec + ' . . ' + gs
                        # special newline-deliniation
                        if 'consistent with' in goodSec and 'microsatellite instability' in goodSec:
                            goodSec = goodSec[goodSec.index('microsatellite instability'):]
                            goodSplit = goodSec.split('\n')
                            goodSec = ''
                            for gs in goodSplit:
                                if regexp.search(gs) or 'nuc ish' in gs:
                                    goodSec = goodSec + ' . . ' + gs
                        # These sections are period-delimited
                        if sub in ['microscopic description', 'a limited panel of immunostains was performed', 'cytogenetic impression:', 'result:\n', 'representative tumor block']:
                            goodSec = goodSec.replace('\n', ' ')
                            goodSplit = goodSec.split('.')
                            goodSec = ''
                            for gs in goodSplit:
                                if regexp.search(gs) or 'nuc ish' in gs and not any(no in gs for no in ['on separate slides']):
                                    goodSec = goodSec + ' . . ' + gs
                        # Special are period-delimited
                        if sub in ['results-comments'] and goodSec.endswith('.') and len(goodSec.split('.')) > 3:
                            goodSec = goodSec.replace('\n', ' ')
                            goodSplit = goodSec.split('.')
                            goodSec = ''
                            for gs in goodSplit:
                                if regexp.search(gs) or 'nuc ish' in gs and not any(no in gs for no in ['on separate slides', 'has been associated']):
                                    goodSec = goodSec + ' . . ' + gs
                        # hyphen-delineated
                        if sub in ['immunohistochemistry (performed', 'molecular genetic studies: performed']:
                            goodSplit = goodSec.split('\n - ')
                            goodSec = ''
                            adder = ''
                            # We want to combine items if they're like "test:" "result"
                            for gs in range(0, len(goodSplit)):
                                if goodSplit[gs].strip().endswith(':'):
                                    adder = goodSplit[gs]
                                    goodSplit[gs] = ''
                                elif adder != '':
                                    goodSplit[gs] = adder + ' ' + goodSplit[gs]
                                    adder = ''
                            for gs in goodSplit:
                                gs = ' ' + gs
                                # Sometimes they just list tests with no results. Delete
                                if gs.strip().endswith(':'):
                                    gs = ''
                                if regexp.search(gs) or 'nuc ish' in gs and not any(no in gs for no in ['on separate slides']):
                                    goodSec = goodSec + ' . . ' + gs
                        # Special comma-delimited
                        if sub in ['omim genes with a copy number gain at', 'omim genes with a copy number loss at']:
                            location = goodSec[:goodSec.index(':')].strip(0)
                            goodSec = goodSec[goodSec.index(':') + 1].strip()
                            goodSplit = goodSec.split(',')
                            goodSec = ''
                            for gs in goodSplit:
                                if regexp.search(gs):
                                    if sub == 'omim genes with a copy number loss at':
                                        gs = 'copy number loss at ' + location
                                    else:
                                        gs = 'copy number gain at ' + location
                                    goodSec = goodSec + ' . . ' + gs

                        # These sections are letter) delimited
                        if sub in ['scored for each probe.']:
                            goodSplit = re.split('\n[a-z]\)', goodSec)
                            goodSec = ''
                            for gs in goodSplit:
                                if regexp.search(gs):
                                    goodSec = goodSec + ' . . ' + gs.replace('\n', ' ')

                        gotSomething = True
                        # Make any substitutions here
                        goodSec = goodSec.replace('present\n', 'present . . ')
                        goodSec = goodSec.replace('signals;', 'signals . . ')
                        if endr in ['her2 her2']:
                            goodSec = 'her2 ' + goodSec
                        goodSec = goodSec.strip()
                        # If we have a long section, let's find out about it
                        if len(goodSec.split()) > 150:
                            print(text)
                            print(goodSec)
                            print('lets be sure here')
                            input()
                        extractBiom(goodSec, testtype, pathol, dr, do)
                        text = text.replace(potentialSection, ' [removed section pt 11] ')

        if not gotSomething:
            noContentSections.append(text)
        if regexp.search(text):
            addendumLeftovers.append(text)
            addendumLeftoverIds.append(reportId)
            for x in ['braf', 'kras', 'nras', 'hras','ntrk','msi','mss','tmb','tumor mutational burden',
                      'mlh1','msh2','msh6','pms2','apc','bmpr1a','epcam','grem1','mutyh','myh','smad4','skt11','lkb1']:
                text = text.replace(x, ' [removed section pt 12] ')


# We're keeping parallel lists for all the fields that will make up the resulting CSV.
# After every report is processed, all of these must be the same length. We'll fill in
# any blanks as necessary.
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

# These will hold the metamap 5-tuple. We'll move column mapping to another function!
# Time results list haven't been used in this set of HF reports. Kept here for addition later!
biomarkerResultList = []
conceptResultList = []
numericResultList = []
qualifierResultList = []
timeResultList = []

# Wrongway tests are those ones that aren't even path reports - distinguised by not having 'patient name' as a field.
# I'm EXPECTING that I will have filtered all of these out by now
wrongwayTests = []
wrongwayReasons = []

# We expect the path reports file to have three fields: 'description', which is the test text, 'patientid' and 'id', which is the report id

# Start up metamap - we'll close after we're done!
metamapStarter()

# If we only want a sub-range for testing, un-comment here
#for x in range(700, 10000):
for x in range(0, len(pathReports['patientid'])):
    if x % 100 == 0:
        print(x, ' out of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    # If we want a specific report, add its' id in here
    # if '45C7421D-CD01-4737-833E-3C49A7DE957A' not in reportId:
    #   continue
    # Preprocess the reports. All to lower, no plusses
    lower = str(pathReports['description'][x]).lower()
    lower = re.sub(' +', ' ', lower)
    splitReport = lower.split('\n')
    # These reports are truncated and don't contain info - NONE have the biomarker of interest
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

    # Let's try to get a pathologist
    if 'staff pathologist' in lower:
        lowerLines = lower.split('\n')
        pathoLine = 0
        while 'staff pathologist' not in lowerLines[pathoLine]:
            pathoLine = pathoLine + 1
        line = lowerLines[pathoLine]
        if 'senior' not in line:
            if 'sr.' not in line:
                line = lowerLines[pathoLine - 1]
                line = line[line.index('dr.'):]
            else:
                pathologist = line[:line.index('sr.')]
        else:
            pathologist = line[:line.index('senior')]
    else:
        pathologist = ''

    if 'reported:' in lower:
        section = lower[lower.index('reported:'):]
        section = lower[:lower.index('\n')]
        dateReported = section
        reportedDate = dateReported.strip()
    else:
        dateReported = ''
        reportedDate = ''
    if 'ordered:' in lower:
        section = lower[lower.index('ordered:'):]
        section = lower[:lower.index('\n')]
        dateOrdered = section
        orderedDate = dateOrdered.strip()
    else:
        dateOrdered = ''
        orderedDate = ''

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
    while '\n\n' in lower:
        lower = lower.replace('\n\n', '\n')
    lowerOrig = lower

    # Let's see if we can get the specimen type:
    if 'operation/specimen: ' in lower:
        section = lower.index('operation/specimen: ')
        section = lower[section + len('operation/specimen: '):]
        if 'pathological diagnosis:' in section:
            section = section[:section.index('pathological')]
        section = section.strip()
        sampleLocation = section
    else:
        sampleLocation = ''

    # Here, we eliminate common non-test sources of the biomarkers
    lower = lower.replace('well as prominent braf and pdgfa mutations.', '')
    lower = lower.replace('msi: 81301, g0452', '').replace('alk-fish-m:', '').replace('msi-m:', '').replace('her2-sish: 88377', '').replace('egfrviii: 81403', '')
    lower = lower.replace('her2-fish: 88377', '')
    lower = lower.replace('apc machine', '')


    # Here are some common alternate spellings
    lower = lower.replace('mlh-1', 'mlh1')
    lower = lower.replace('microsatellite status', 'msi ')
    lower = lower.replace('each \nprobe', 'each probe')
    lower = lower.replace('expressed', 'expression')
    lower = lower.replace('er/pr/her2', 'er and pr and her2').replace('er/pr', 'er and pr')
    # lower = lower.replace('tumor mutational burden', 'tmb')

    # We want to keep looking in the reports as long as we find the biomarker of interest somewhere!
    while regexp.search(lower):
        ################################
        ################################
        ################################
        # Let's remove panels and references here. Also PROBABLY clinical history
        ################################
        ################################
        ################################
        removalBits = ['gene exon / amino acid (aa) coverage annotation transcript',
                       'gene location transcript cdna protein dp exon af interpretation',
                       'cdna protein dp exon af interpretation',
                       'gene location transcript cdna protein dp exon af label',
                       'gene variant exon cdna change chr genomic coordinates coverage allele fraction',
                       'gene transcript exons direction',
                       'gene location',
                       'gene exon / amino acid (aa) coverage',
                       'gene target region (exon)',
                       'genomic findings detected fda-approved therapeutic options',
                       'genes unique start sites reads %of reads breakpoint category',
                       'mutations in 48 genes',
                       'references:',
                       'assay targets',
                       'gene chr genomic coordinates transcript cdna change protein change exon depth',
                       'gene location transcript cdna protein dp exon',
                       'gene location transcript cdna',
                       'list of target genes',
                       'gene transcript exons direction type',
                       'variant of unknown significance gene location transcript cdna',
                       'pathogenic variant gene location transcript cdna protein dp',
                       'positive for the following coding variants:',
                       'gene exons']
        while any(x in lower for x in removalBits):
            if reportId not in panelsTests:
                panelsTests.append(reportId)
            # These are the strings that might potentially end a panel section. Find the one that's the closest to the start string, and go until you hit that.
            for y in removalBits:
                sectionEnders = ['disclaimer', '***ele', 'interpretation: ', 'specific mutations', 'target details', 'comment:', 'note:']
                if y in lower:
                    section = lower[lower.index(y):]
                    endBit = 99999999999
                    if not any(z in section for z in sectionEnders):
                        print(section)
                        print('NO SECTION END!')
                        input()
                    for bit in sectionEnders:
                        if bit in section:
                            if section.index(bit) < endBit:
                                endBit = section.index(bit)
                    section = section[:endBit]
            lower = lower.replace(section, '')

        ####################################
        ####################################
        ####################################
        ############# Here's where we handle specific tests
        ####################################
        ####################################
        ####################################

        ############################
        ############################
        ############################
        # at this point, we're done with the specific tests. The NEXT step is eliminating panels. Those show up in the semi-structured
        # removal, so there's no point in having them in!
        ############################
        ############################
        ############################

        ####
        # Let's handle all addenda first
        # We're tackling these separately because they might have different dates or pathologists!
        # Specifically, this is any test with multiple '***electronically signed out**** marks
        # OR ones with a 'procedures/addenda' section.
        ####
        indices = [m.start() for m in re.finditer('\*\*\*electronically', lower)]
        if len(indices) > 1:
            addendumTestType = testType + ' - addendum'
            # We're gonna loop through these in reverse order, so that deleting an earlier one doesn't change the
            # index of a later one
            indices = reversed(indices)
            # We want to get the separate dates for each addendum, along with their full text.
            for ind in indices:
                # We're setting these by default to be what the main test's are.
                addendumOrdered = dateOrdered
                addendumReported = dateReported
                addendumPathologist = pathologist
                # Piecing off the index here.
                lowerBit = lower[ind:]
                lowerSplit = lowerBit.split('\n')
                foundDate = False
                equalsLine = 9999999999999
                # We frequently find a line of '==========' that's the start of the addendum.
                # We'll scan for it, and start one line below
                # Also, we're looking for separate 'date ordered' markers
                if len(lowerSplit) < 20:
                    end = len(lowerSplit)
                else:
                    end = 20
                # Here we look for the equals line and the found date
                for bit in range(0, end):
                    # If we find the end of the section, do not go on.
                    if '***elec' in lowerSplit[bit] and bit > 3:
                        break
                    if '===========' in lowerSplit[bit]:
                        equalsLine = bit
                    if 'date ordered:' in lowerSplit[bit]:
                        foundDate = True
                # If we found the date, we can safely call this an addendum.
                if foundDate:
                    if equalsLine < end:
                        addendum = lowerBit[lowerBit.index(lowerSplit[equalsLine+1]):]
                        if '***electronically' not in addendum:
                            if '*** end' not in addendum:
                                addendum = addendum
                            else:
                                addendum = addendum[:addendum.index('*** end')]
                        else:
                            addendum = addendum[:addendum.index('***electronically')]
                    else:
                        addendum = lowerBit
                        addendum = addendum[addendum.index('out***') + len('out***'):]
                        if 'procedures/addenda' in addendum:
                            addendum = addendum[addendum.index('procedures/addenda'):]
                        if '***electronically' not in addendum:
                            if '*** end' not in addendum:
                                addendum = addendum
                            else:
                                addendum = addendum[:addendum.index('*** end')]
                        else:
                            addendum = addendum[:addendum.index('***electronically')]
                    addendum = addendum.strip()
                    if len(addendum.split('\n')) == 1:
                        addendum = ''

                        continue
                    # Sometimes the date is a line above the equals line. For some reason.
                    if 'date reported' not in addendum:
                        if 'date reported' in lowerSplit[equalsLine-1]:
                            dateline = lowerSplit[equalsLine-1]
                            addendumOrdered = dateline[dateline.index('date ordered: ') + len('date ordered: '): dateline.index('date reported')].strip()
                            addendumReported = dateline[dateline.index('date reported: ') + len('date reported: '):].strip()
                        else:
                            print(addendum)
                    else:
                        addendumOrdered = addendum[addendum.index('date ordered: ') + len('date ordered: '): addendum.index('date reported')].strip()
                        addendumReported = addendum[addendum.index('date reported: ') + len('date reported: '):].strip()
                    try:
                        addendumReported = addendumReported[:addendumReported.index('\n')].strip()
                    except:
                        addendumReported = addendumReported.strip()
                # These kind of aren't addenda at this point, but they ARE separate parts of the test, and we'll scan them separately.
                else:
                    # This is to catch any actual procedures/addenda that don't have a separate date ordered.
                    if 'procedures/addenda' in lowerBit and not any(x in lowerBit for x in ['procedures/addenda,', 'procedures/addenda)', 'procedures/addenda.']):
                        print(lowerBit)
                        input()
                    addendum = lowerBit
                    if equalsLine < end:
                        addendum = lowerBit[lowerBit.index(lowerSplit[equalsLine+1]):]
                    addendumOrdered = dateOrdered
                    addendumReported = dateReported
                # Let's see if we can get a new pathologist for this
                if 'pathologist' in addendum:
                    addSplit = addendum.split('\n')
                    pathIn = 0
                    while 'pathologist' not in addSplit[pathIn]:
                        pathIn = pathIn + 1
                    if ',' not in addSplit[pathIn]:
                        if ';' in addSplit[pathIn]:
                            if 'sub' not in addSplit[pathIn]:
                                addendumPathologist = pathologist
                            else:
                                addendumPathologist = addSplit[pathIn][addSplit[pathIn].index(';') + 1:addSplit[pathIn].index('sub')]
                    else:
                        addendumPathologist = addSplit[pathIn][:addSplit[pathIn].index(',')]
                else:
                    addendumPathologist = pathologist
                # Now delete the addendum
                lower = lower.replace(addendum, '')
                # Now scan this section, if it has a gene of interest
                if regexp.search(addendum):
                    processSection(addendum, addendumTestType, addendumPathologist, addendumReported, addendumOrdered)
        # Sometimes we'll have a procedures section without multiple 'electronically signed out's
        elif 'procedures/addenda' in lower:
            while 'procedures/addenda' in lower:
                addendum = lower[lower.index('procedures/addenda'):]
                if '***electronically' not in addendum:
                    addendum = addendum[:addendum.index('*** end')]
                else:
                    addendum = addendum[:addendum.index('***electronically')]
                if 'date ordered:' in addendum:
                    addendumOrdered = addendum[addendum.index('date ordered: ') + len('date ordered: '): addendum.index('date reported')].strip()
                    addendumReported = addendum[addendum.index('date reported: ') + len('date reported: '):].strip()
                    addendumReported = addendumReported[:addendumReported.index('\n')].strip()
                else:
                    addendumOrdered = dateOrdered
                    addendumReported = dateReported
                # Now delete the addendum
                lower = lower.replace(addendum, '')
                # Now scan this section, if it has a gene of interest
                if regexp.search(addendum):
                    processSection(addendum, addendumTestType, addendumPathologist, addendumReported, addendumOrdered)

        ####################################
        ####################################
        ####################################
        # Otherwise, now that we've handled the procedures/addenda, we're left with the normals
        # We'll start by grabbing the pathologist and dates
        ####################################
        ####################################
        ####################################
        if '\n***electronically signed out***\n' not in lower:
            lower = lower.replace('***electronically signed out***', '\n***electronically signed out***\n')
        lowSplit = lower.split('\n')
        lowSplit = list(filter(None, lowSplit))
        endIndex = 0
        if '***elec' not in lower:
            endIndex = len(lowSplit)
        else:
            while '***elec' not in lowSplit[endIndex]:
                endIndex = endIndex + 1
            endLine = endIndex
        testType = testTypeOrig
        if 'pathologist' not in lower:
            pathologist = ''
        elif endIndex == len(lowSplit):
            for line in lowSplit:
                if 'pathologist' in line:
                    pathologist = line[:line.index(',')]
        else:
            pathologist = lowSplit[endLine + 1]
            pathologist = pathologist[0:pathologist.rfind(',')]
        if 'date reported:' in lower:
            dateReported = lower[lower.index('date reported:') + len('date reported:'):]
            dateReported = dateReported[:dateReported.index('\n')]
            reportedDate = dateReported.strip()
        else:
            reportedDate = ''
        if 'date ordered:' in lower:
            dateOrdered = lower[lower.index('date ordered:') + len('date ordered:'):]
            if 'date rep' in dateOrdered:
                dateOrdered = dateOrdered[:dateOrdered.index('date rep')]
            else:
                dateOrdered = dateOrdered[:dateOrdered.index('\n')]
            orderedDate = dateOrdered.strip()
        else:
            orderedDate = ''

        # We don't want to do some tests
        if testType in ['comprehensive solid tumor cancer panel (170 genes)', 'factor v (leiden)', 'hereditary breast/ovarian cancer-related gene sequence analysis (20 genes)']:
            lower = ''
            continue

        # First, we'll pull out the good stuff
        if testType in ['molecular pathology and genomic test'] and 'immunohistochemistry for mmr proteins:' in lower:
            results = lower[lower.index('immunohistochemistry for mmr proteins:'):]
            results = results[:results.index('results-comments')]
            if 'immunohistochemistry for mmr proteins:' in results:
                resultsOrig = results
                results = results[results.index('immunohistochemistry for mmr proteins:') + len('immunohistochemistry for mmr proteins:'):].strip()
            if regexp.search(section):
                processSection(results, testType + ' - immunohistochemistry for mmr proteins:', pathologist, dateReported, dateOrdered)
            lower = lower.replace(resultsOrig, '')

        if 'cytogenetic impression:' in lower:
            results = lower[lower.index('cytogenetic impression:'):lower.index('interpretation')]
            lower = lower.replace(results, '')
            results = results[len('cytogenetic impression:'):].replace('\n', ' ').strip().replace('and negative', '. . negative').replace('and positive', '. . positive')
            if 'fusion of' in results:
                results = results[:results.index('fusion of')]
            if 'this finding' in results:
                results = results[:results.index('this finding')]
            extractBiom(results, testType, pathologist, dateReported, dateOrdered)

        if 'immunohistochemistry microsatellite instability panel' in lower:
            results = lower[lower.index('immunohistochemistry microsatellite instability panel'):lower.index('scoring criteria: ')]
            lower = lower.replace(results, '')
            if regexp.search(section):
                print(results)
                input()
                processSection(results, testType + ' - immunohistochemistry microsatellite instability panel', pathologist, dateReported, dateOrdered)

        if 'no clinically significant coding variants' in lower:
            section = lower[lower.index('no clinically significant coding variants'):]
            if 'tested' not in section:
                section = section[:section.index('regions')]
            else:
                section = section[:section.index('tested')]
            lower = lower.replace(section, ' [removed section pt 20] ')
            extractBiom(section, testType, pathologist, dateReported, dateOrdered)

        # Finally, this is another place to find this
        if 'colorectal adenocarcinoma her-2/neu summary' in lower:
            section = lower[lower.index('colorectal adenocarcinoma her-2/neu summary'):]
            sectionWhole = section[:section.index('tissue studied:')]
            section = section[section.index('interpretation: ') + len('interpretation: '):]
            section = 'her2 ' + section[:section.index('her2 her2')]
            lower = lower.replace(sectionWhole, ' [removed section pt 20] ')
            extractBiom(section, testType + ' - colorectal adenocarcinoma panel', pathologist, dateReported, dateOrdered)

        # If that cleared the biomarkers, look no further
        if not regexp.search(lower):
            continue

        # Otherwise, time to dig into section headers
        lower = lower.replace('\ncomment \n', '\ncomment\n')
        # Now let's see if there is any info in other sections!
        sections = ['diagnostic interpretation:', 'are as follows:\n', 'microscopic description', 'microscopic:\n', 'specimen description\n',
                    'pathological diagnosis:', '\ncomment\n', 'clinical history', 'final cytopathological diagnosis', '\naddendum diagnosis\n',
                    'tier 1 / 2', 'results-comments', 'clinical panel', 'interpretation', 'outside institution and is reported as follows:',
                    'predicted copy number alterations', 'biopsied at']

        if not any(bit in lower for bit in sections):
            if testType not in ['factor v (leiden)', 'microsatellite instability testing (msi)', 'autopsy report', 'hereditary breast/ovarian cancer-related gene sequence analysis (20 genes)',
                                'comprehensive solid tumor cancer panel (170 genes)'] and regexp.search(lower) and (firstName != 'hema' and lastName != 'hema'):
                print(lower)
                print('couldnt find section in whole!')
                noSectionsList.append(lower)
                lower = ''

        for x in sections:
            while x in lower:
                sectionEnders = ['results-comments', 'icd code(s)', 'comment\n', '***electronically', 'section 2:', 'technical note:', '*** end', 'methods', 'analyte specific',
                                 'loss of nuclear expression of', 'scoring criteria:', 'disclaimer', 'previous signout', 'the metastatic dimension', 'targeted therapy',
                                 'operative diagnoses']
                section = lower[lower.index(x) + len(x):]
                sectionWhole = lower[lower.index(x):]
                if not any(sec in section for sec in sectionEnders):
                    print(sectionWhole)
                    print(x)
                    print('COULDNT FIND END!')
                endPos = 9999999999
                for m in sectionEnders:
                    if m in section and m not in x and section.index(m) > 0:
                        if section.index(m) < endPos:
                            endPos = section.index(m)
                if 'pd-l1' in section and ('tumor proportion score' in section or 'combined positive score' in section):
                    if 'test: ' in section:
                        section = section[section.index('test: ') + len('test: '):]
                    if not section.strip().startswith('control'):
                        resultBit = ''
                        secSplit = section.split('\n')
                        line = 0
                        if secSplit[line] == '':
                            line = 1
                        while 'pd-l1' in secSplit[line]:
                            if '); pd-l1' in secSplit[line]:
                                secSplit[line] = secSplit[line][secSplit[line].index('); pd-l1') + 3:]
                            if 'tumor proportion score' in secSplit[line] or 'combined positive score' in secSplit[line]:
                                secSplit[line] = secSplit[line] + ' . . '
                            resultBit = resultBit + ' ' + secSplit[line]
                            line = line + 1
                        extractBiom(resultBit, testType, pathologist, dateReported, dateOrdered)
                        lower = lower.replace(lower, '')
                section = section[:endPos]
                sectionWhole = sectionWhole[:endPos + len(x)]
                if 'note:' in section:
                    section = section[:section.index('note')].strip()
                    # This is a common, small section
                    if len(section.split('\n')) == 2:
                        section = section.replace('\n', ' ')
                # Turns out metamap doesn't handle long lists gracefully if not detected
                if '\nnone \n' in section:
                    section = section[section.index('none '):].strip().replace('detected', 'not detected')
                if regexp.search(section):
                    processSection(section, testType, pathologist, dateReported, dateOrdered)
                lower = lower.replace(sectionWhole, '')

        # We might have some small thing to send
        if regexp.search(lower):
            if lower[regexp.search(lower).start():].startswith('microsatellite stable'):
                section = lower[regexp.search(lower).start():][:lower[regexp.search(lower).start():].index('***elec')]
                processSection(section, testType, pathologist, dateReported, dateOrdered)
                lower = lower.replace(section, '')
            if 'pd-l1' in lower and 'tumor proportion score:' in lower:
                if 'test: ' in lower:
                    lower = lower[lower.index('test: ') + len('test: '):]
                print(lower)
                input()
                processSection(lower, testType, pathologist, dateReported, dateOrdered)
                lower = lower.replace(lower, '')
            if 'submitted immunostains for' in lower:
                lower = lower[lower.index('following results:') + len('following results:'):]
                processSection(lower, testType, pathologist, dateReported, dateOrdered)
                lower = lower.replace(lower, '')

        # Finally, let's remove any genes from the rest of the report!
        if regexp.search(lower):
            # print(lower)
            # print(testType)
            # print(firstName)
            # print('couldnt find nothin')
            # print(lower[regexp.search(lower).start():])
            # print(testType)
            # print('#########')
            # input()
            testsToCheckList.append(lower)
            testsToCheckTypeList.append(testType)
            for x in ['braf','kras','nras','hras','ntrk','msi','mss','tmb','tumor mutational burden','mlh1',
                      'msh2','msh6','pms2','apc','bmpr1a','epcam','grem1','mutyh','myh','smad4','skt11','lkb1']:
                lower = lower.replace(x, '')


# Close metamap!
metamapCloser()

rawResults = pd.DataFrame(list(zip(biomarkerResultList, conceptResultList, numericResultList, qualifierResultList,
                                   firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionList, testTypeList, sampleLocationList,
                                   pathologistList, dateOrderedList, dateReportedList, testTextList, fullTextList, icdCodeList, patientIdList, reportIdList)),
                          columns=['biomarker', 'concept', 'numeric', 'qualifier', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accession', 'testType',
                                   'sampleLocation', 'pathologist', 'dateOrdered', 'dateReported', 'testText', 'fullText', 'icdCode', 'patientId', 'reportId'])

rawResults = rawResults.applymap(lambda x: ','.join(x) if isinstance(x, list) else x)

rawResults = rawResults.drop_duplicates()
rawResults = rawResults.reset_index()

failResults = pd.DataFrame(list(zip(testsToCheckTypeList, testsToCheckList)), columns=['Type', 'Text'])
addendumLeftoverResults = pd.DataFrame(list(zip(addendumLeftovers, addendumLeftoverIds)), columns=['addendum leftovers', 'report Ids'])
removedResults = pd.DataFrame(list(zip(removedSections)), columns=['removed sections'])

if not testing:
    rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/RawOCRC.csv", index=False)
    removedResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/RemovedOfCRC.csv", index=False)
    failResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/testsWithNoSectionsToRemoveCRC.csv", index=False)
    addendumLeftoverResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/leftoverBitOfPulledOutSectionsCRC.csv", index=False)

addendumNoGos = pd.DataFrame(list(zip(noContentSections)), columns=['unscanned'])

addendumNoGos.to_csv("~/Desktop/LatestNLP/Unstructured Results/pulledOutSectionsUnableToScanCRC.csv")
