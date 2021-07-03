import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput
from collections import Counter

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

pmsCount = 0

# Now beginning the sorting out!
pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/March2020HFHS.csv", low_memory=False)

# This is for tests that ended up with 'alk' that didn't get parsed out somehow
nothingList = []

# This is for tests with no section headings
noSectionsList = []

# Putting this up front for ease of finding. Once we have our section extracted, we'll give it here.
def extractBiom(text, testtype, pathol, dr, do):
    ttype = testtype
    pathologist = pathol
    reportedDate = dr
    orderedDate = do
    # This particular test is tough to pull out. We'll have to munge it specifically
    if 'an immunohistochemical stain with antibodies against alk (anaplastic lymphoma kinase)-1 is prepared' in text.replace('\n', ' '):
        section = text.index('antibodies against alk (anaplastic lymphoma kinase)-1')
        sectionOrig = text[section:]
        sectionOrig = sectionOrig[:sectionOrig.index('results-comments')]
        section = sectionOrig[sectionOrig.index('time of sign out): ') + len('time of sign out):'):]
        section = 'alk is ' + section.replace('\n', ' ')
    # If we have a small piece broken off, that's probably safe to give.
    elif len(text.split('\n')) == 1:
        section = text
    else:
        section = text.replace('\n', ' ')
        print(section)
        print('GOT A FRESH ONE!')
    addResults(section)



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

regexp = re.compile(r'(?<![^ .\\\/,?!-;])alk(?![^ .\\\/,?!-;\r\n])')


# Takes metamap output and adds it to the final results!
def addResults(reso):
    file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
    with open(file, 'w') as filetowrite:
        filetowrite.write(reso)
    try:
        res = metamapstringoutput()
    except:
        print(lower)
        print(reso)
        print('couldnt run it!')
        input()
    # print(results)
    lot = section
    # Turn this on to print results
    #printResults()
    #input()
    # Turn this on to look at the whole test
    # print(spacelower)
    # print(lot)
    # input()
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
    # print(fullTest)
    # print(results)
    # print(lot)
    print(orderedDate)
    print(reportedDate)
    print(sampleLocation)
    print(testType)
    # print(testTech)
    print(pathologist)


# Data is the section that has the data
# Reasons is where it's pulled from
# Full is the full report text
alkData = []
alkReasons = []
alkFull = []
for x in range(0, len(pathReports['description'])):
    # for x in range(0, 10000):
    if x % 100 == 0:
        print(x, ' out of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    # if reportId != '25be56ef-b1a0-4181-8382-3cec8f718d26':
    #     continue
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

    # First, we're going to test to see if 'alk' is really 'alkaline phosphotase'
    lower = lower.replace('alk phos', '')
    # Now let's take out names
    lower = lower.replace('dr.alk', 'dr. alk')
    # And let's remove icd codes
    lower = lower.replace('alk-fish-m', '')

    # We've found ALK, now let's get the results!
    while regexp.search(lower):

        # Let's remove panels and references here. Also PROBABLY clinical history
        lower = lower.replace('alk + lung adenocarcinoma panel', '')
        removalBits = ['gene exon / amino acid (aa) coverage annotation transcript',
                       'gene location transcript cdna protein dp exon af interpretation',
                       'gene location transcript cdna protein dp exon af label',
                       'gene variant exon cdna change chr genomic coordinates coverage allele fraction',
                       'gene transcript exons direction',
                       'gene exon / amino acid (aa) coverage',
                       'genomic findings detected fda-approved therapeutic options',
                       'genes unique start sites reads %of reads breakpoint category',
                       'mutations in 48 genes',
                       'references:',
                       'assay targets',
                       'gene chr genomic coordinates transcript cdna change protein change exon depth',
                       'list of target genes']
        while any(x in lower for x in removalBits):
            for y in removalBits:
                sectionEnders = ['disclaimer', '***ele', 'interpretation: ', 'specific mutations', 'target details']
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

        ####
        # Let's handle all addenda first
        ####

        # Sometimes we don't properly note addenda - let's note it here
        indices = [m.start() for m in re.finditer('\*\*\*electronically', lower)]
        if len(indices) > 1:
            addBit = 0
            for x in indices:
                offset = (len('procedures/addenda ') * addBit)
                lowerBit = lower[x + offset:]
                lowerBitOrig = lowerBit
                lowerBitSplit = lowerBit.split('\n')
                if 'date reported:' in lowerBitSplit[3]:
                    lowerBitSplit.insert(2, 'procedures/addenda')
                    lowerBit = '\n'.join(lowerBitSplit)
                    addBit = addBit + 1
                elif 'date reported:' in lowerBitSplit[4]:
                    lowerBitSplit.insert(3, 'procedures/addenda')
                    lowerBit = '\n'.join(lowerBitSplit)
                    addBit = addBit + 1
                else:
                    pass

                lower = lower.replace(lowerBitOrig, lowerBit)

        indices = [m.start() for m in re.finditer('==========(=+)', lower)]
        for x in indices:
            lowerBit = lower[x:]
            if '***elec' not in lowerBit:
                break
            lowerBit = lowerBit[:lowerBit.index('***elec')]
            # Here, we're looking for a section divider that 1) has a new reported date, and 2) doesn't have a proper 'procedures/addenda' tag
            if 'date reported:' in lowerBit and 'procedures/addenda' not in lowerBit:
                lowerBitSplit = lowerBit.split('\n')
                lowerBitSplit.insert(1, 'procedures/addenda')
                lowerBit = '\n'.join(lowerBitSplit)
                print(lowerBit)
                print('######################')
                print(lower)
                input()

        while 'procedures/addenda' in lower:
            addendum = lower[lower.index('procedures/addenda'):]
            addSplit = addendum.split('\n')
            if '***electronically' in addendum:
                elecBit = 0
                while '***electronically' not in addSplit[elecBit]:
                    elecBit = elecBit + 1
                endSplit = elecBit
                addendum = '\n'.join(addSplit[0:endSplit + 2])
                addendumOrig = addendum
                patho = addSplit[endSplit + 1]
                testType = addSplit[1] + ' - addendum'
                addSplit = addendum.split('\n')
                endLine = elecBit
                pathologist = addSplit[endLine + 1]
                pathologist = pathologist[0:pathologist.rfind(',')]
            else:
                addendum = '\n'.join(addSplit)
                addendumOrig = addendum
                pathologist = ''
            if 'date reported:' in addendum:
                dateReported = addendum[addendum.index('date reported:') + len('date reported:'):]
                dateReported = dateReported[:dateReported.index('\n')]
                reportedDate = dateReported.strip()
            else:
                reportedDate = ''
            if 'date ordered:' in addendum:
                dateOrdered = addendum[addendum.index('date ordered:') + len('date ordered:'):]
                if 'date rep' in dateOrdered:
                    dateOrdered = dateOrdered[:dateOrdered.index('date rep')]
                else:
                    dateOrdered = dateOrdered[:dateOrdered.index('\n')]
                orderedDate = dateOrdered.strip()
            else:
                orderedDate = ''
            # Now let's split up the various addenda.
            if 'addendum diagnosis' in addendum:
                finalResult = ''
                addendum = addendum[addendum.index('addendum diagnosis')]
                addendum = addendum.split('.')
                for x in addendum:
                    if regexp.search(x):
                        finalResult = finalResult + ' ' + x
                finalResult = x.strip()
                addendum = finalResult
            if 'interpretation' in addendum:
                if 'interpretation:' in addendum:
                    addendum = addendum[:addendum.index('interpretation:')]
                elif 'results-comments' in addendum:
                    addendum = addendum[:addendum.index('results-comments')]
                # This is a weird outside path report
                if 'alk1, ihc w/interp' in addendum:
                    addendum = addendum.replace('detected', 'detected. .')
                finalResult = ''
                addendum = addendum.split('.')
                for x in addendum:
                    if regexp.search(x):
                        finalResult = finalResult + ' ' + x
                finalResult = x.strip()
                addendum = finalResult
            if 'microscopic description' in addendum:
                addendum = addendum.replace(' - ', '.')
                addendum = addendum[:addendum.index('icd code(s):')]
                addendum = addendum.split
                addendum = addendum.split('.')
                for x in addendum:
                    if regexp.search(x):
                        finalResult = finalResult + ' ' + x
                finalResult = x.strip()
                addendum = finalResult
            else:
                finalBit = ''
                addendumWhole = addendum
                addendum = addendum.split('.')
                for x in addendum:
                    # if there is 1. and 2., make sure we remove that final number
                    if regexp.search(x):
                        if x[-1].isnumeric() and len(addendumWhole) > addendumWhole.index(x) + len(x):
                            if addendumWhole[addendumWhole.index(x) + len(x):][0] == '.':
                                x = x[:-1]
                        finalResult = finalResult + ' ' + x
                finalResult = x.strip()
                addendum = finalResult

            # That's that.
            # If alk's in it, let's get it!
            if regexp.search(addendum):
                extractBiom(addendum, testType, pathologist, reportedDate, orderedDate)
            lower = lower.replace(addendumOrig, '')

        # If we don't have alk, let's end
        if not regexp.search(lower):
            continue

        # Otherwise, now that we've handled the procedures/addenda, we're left with the normals
        # We'll start by grabbing the pathologist and dates
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

        # First, we'll pull out the good stuff
        if testType == 'alk gene rearrangement (fish) assay' or testType == 'fluorescent in-situ hybridization assay' or testType == 'cytogenetics result, fish.':
            if testType == 'alk gene rearrangement (fish) assay':
                section = lower[lower.index('alk gene rearrangement (fish) assay'):]
            else:
                section = lower[lower.index('interpretation\n'):]
            if 'alk fish assay (molecular)' in lower:
                lower = lower.replace('alk fish assay (molecular)', '')
            if '***electronically signed out***' not in section:
                section = section[:section.index('icd code')]
            else:
                section = section[:section.index('***electronically signed out***')]
            if 'karyotype: ' in lower:
                secFISH = lower[lower.index('karyotype: ') + len('karyotype: '):]
                sectionSplit = secFISH.split('\n')
                secIndex = 0
                while 'least two hundred interphase cells were scored. ' not in sectionSplit[secIndex]:
                    secIndex = secIndex + 1
                probe = sectionSplit[secIndex+1]
                results = secFISH[:secFISH.index('cytogenetic')]
                results = results.replace('\n', ' ')
                extractBiom(results, testType, pathologist, reportedDate, orderedDate)
            elif 'nuc ish' in lower:
                sectionSplit = lower.split('\n')
                indexNum = 0
                while 'nuc ish' not in sectionSplit[indexNum]:
                    indexNum = indexNum + 1
                probe = sectionSplit[indexNum]
                secFISH = lower[lower.index('nuc ish'):]
                secFISH = secFISH[secFISH.index('results-comments') + len('results-comments'):secFISH.index('slides from')].replace('\n', ' ')
                results = secFISH
                extractBiom(results, testType, pathologist, reportedDate, orderedDate)

            lower = lower.replace(section, '')

        if testType in ['lung cancer fusion panel'] and 'interpretation\n' in lower:
            results = lower[lower.index('interpretation\n') + len('interpretation\n'):]
            resultsOrig = lower[lower.index('interpretation\n'):]
            if 'note:' not in results:
                if 'results-comments' in results:
                    results = results[:results.index('results-comments')]
                    resultsOrig = resultsOrig[:resultsOrig.index('results-comments')]
                elif 'disclaimer:' in results:
                    results = results[:results.index('disclaimer:')]
                    resultsOrig = resultsOrig[:resultsOrig.index('disclaimer:')]

            else:
                results = results[:results.index('note:')]
                resultsOrig = resultsOrig[:resultsOrig.index('note:')]
            addendum = results.split('.')
            finalResult = ''
            for x in addendum:
                # if there is 1. and 2., make sure we remove that final number
                if regexp.search(x):
                    if x[-1].isnumeric():
                        print('whole')
                        print(addendumWhole)
                        print('x')
                        print(x)
                        if addendumWhole[addendumWhole.index(x) + len(x):][0] == '.':
                            x = x[:-1]
                    finalResult = finalResult + ' ' + x
            finalResult = x.strip()
            results = finalResult
            lower = lower.replace(resultsOrig, '')
            results = results.replace('\n', ' ')
            if results.replace(' ','').replace('\n','') == '':
                continue
            if results.startswith('diagnostic interpretation: '):
                results = results[len('diagnostic interpretation: '):]
            extractBiom(results, testType, pathologist, reportedDate, orderedDate)

        # If that cleared the ALK, look no further
        if not regexp.search(lower):
            continue
        lower = lower.replace('\ncomment \n', '\ncomment\n')
        # Now let's see if there is any info in other sections!
        sections = ['diagnostic interpretation:', 'microscopic description', 'microscopic:\n', 'specimen description\n',
                    'pathological diagnosis:', '\ncomment\n', 'clinical history', 'final cytopathological diagnosis', '\naddendum diagnosis\n',
                    'tier 1 / 2']
        if not any(bit in lower for bit in sections):
            print(lower)
            print('couldnt find section in whole!')
            noSectionsList.append(lower)

        for x in sections:
            while x in lower:
                sectionEnders = ['results-comments', 'icd code(s)', 'comment\n', '***electronically', 'section 2:', 'technical note:', '*** end']
                section = lower[lower.index(x) + len(x):]
                sectionWhole = lower[lower.index(x):]
                if not any(sec in section for sec in sectionEnders):
                    print(sectionWhole)
                    print(x)
                    print('COULDNT FIND END!')
                endPos = 9999999999
                for m in sectionEnders:
                    if m in section and x not in m and section.index(m) > 0:
                        if section.index(m) < endPos:
                            endPos = section.index(m)
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
                # Let's split up some sections by sentence!
                if x in ['microscopic description', 'microscopic:\n', 'clinical history', 'final cytopathological diagnosis', '\naddendum diagnosis\n', 'integrated diagnosis']:
                    finalBit = ''
                    section = section.replace('- ', '. ')
                    section = section.replace('\n', ' ').split('.')
                    for sec in section:
                        if regexp.search(sec):
                            finalBit = finalBit + ' ' + sec
                    finalBit = finalBit.strip()
                    section = finalBit
                # The diagnostic interpretation is sometimes split by numbers.
                elif x in ['diagnostic interpretation:'] and '1. ' in section:
                    if 'interpretation:' in section:
                        section = section[:section.index('interpretation:')]
                    section = section.replace('\n', ' ')
                    finalBit = ''
                    section = section.split('.')
                    for sec in section:
                        if regexp.search(sec):
                            finalBit = finalBit + ' ' + sec
                    finalBit = finalBit.strip()
                    section = finalBit
                # Some are split by 1) 2)
                elif x in ['\ncomment\n']:
                    finalBit = ''
                    if '1)' in section:
                        section = section.replace('\n', ' ').split(')')
                        for sec in section:
                            if regexp.search(sec):
                                finalBit = finalBit + ' ' + sec
                    else:
                        section = section.replace('\n', ' ').split('.')
                        for sec in section:
                            if regexp.search(sec):
                                finalBit = finalBit + ' ' + sec

                    finalBit = finalBit.strip()
                    section = finalBit
                # Others are all one
                elif x in ['tier 1 / 2']:
                    section = section.replace('\n', ' ')
                    finalBit = ''
                    section = section.split('.')
                    for sec in section:
                        if regexp.search(sec):
                            finalBit = finalBit + ' ' + sec
                    finalBit = finalBit.strip()
                    section = finalBit
                    if 'variant interpretation' in section:
                        section = section[:section.index('variant interpretation')]
                    if "genes (5'-3" in section:
                        section = section[:section.index("genes (5'-3")]
                    if 'fusions reads' in section:
                        section = section[:section.index("fusions reads")]
                    print(section)
                    print('tier 1 / 2 HERE')
                # Others just don't have good punctuation
                elif x in ['pathological diagnosis:', 'specimen description\n']:
                    finalBit = ''
                    if '- ' in section:
                        section = section.replace('\n', ' ').split('- ')
                    else:
                        section = section.split('\n')
                    for sec in section:
                        if regexp.search(sec):
                            finalBit = finalBit + ' ' + sec
                    finalBit = finalBit.strip()
                    section = finalBit
                if regexp.search(section):
                    if ') and negative' in section:
                        section = section.replace(') and negative', '. . negative')
                    elif '); negative' in section:
                        section = section.replace('); negative', ') . . negative')
                    # If this is a long paragraph, let's just get the ALKs
                    if len(section.split('. ')) > 3:
                        finalResult = ''
                        section = section.split('.')
                        for xy in section:
                            if regexp.search(xy):
                                finalResult = finalResult + ' ' + xy
                        finalResult = finalResult.strip()
                        section = finalResult
                    if len(section.split(': ')) > 3:
                        finalResult = ''
                        section = section.split(':')
                        for xy in section:
                            if regexp.search(xy):
                                finalResult = finalResult + ' ' + xy
                        finalResult = finalResult.strip()
                        section = finalResult



                    extractBiom(section, testType, pathologist, reportedDate, orderedDate)
                lower = lower.replace(sectionWhole, '')

        if regexp.search(lower):
            print(lower)
            print(testType)
            print('couldnt find nothin')
            nothingList.append(lower)
            lower = lower.replace('alk', '')



wrongTests = pd.DataFrame(list(zip(list(testTextList))), columns=['text'])
wrongTests.to_csv("~/Desktop/LatestNLP/Unstructured Results/AllALKStrings.csv", index=False)

rawResults = pd.DataFrame(list(zip(biomarkerResultList, conceptResultList, numericResultList, qualifierResultList,
                                   firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionList, testTypeList, sampleLocationList,
                                    pathologistList, dateOrderedList, dateReportedList, testTextList, fullTextList, icdCodeList, patientIdList, reportIdList)),
                             columns=['biomarker', 'concept', 'numeric', 'qualifier', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accession', 'testType',
                                   'sampleLocation', 'pathologist', 'dateOrdered', 'dateReported', 'testText', 'fullText', 'icdCode', 'patientId', 'reportId'])

rawResults = rawResults.applymap(lambda x: ','.join(x) if isinstance(x, list) else x)

rawResults = rawResults.drop_duplicates()
rawResults = rawResults.reset_index()

rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/RawOfAlk.csv", index=False)
