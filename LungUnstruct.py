import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput
from metamapLoader import metamapStarter
from metamapLoader import metamapCloser
from collections import Counter
from UnstructuredTextSectionProcess import processSection

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# Now beginning the sorting out! This points to the most recent file
pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/March2020HFHS.csv", low_memory=False)

# This is for tests that ended up with one of our biomarkers that didn't get parsed out somehow
testsToCheckList = []
testsToCheckTypeList = []

panelsTests = []

# This is for testing the addendum bits checked
addendumPiece = []


# This is for tests that I can't pull anything from
noContentSections = []
noContentSectionIds = []
addendumLeftovers = []
addendumLeftoverIds = []
removedSections = []
removedSectionIds = []

processedSections = []
processedBits = []
noSectionsList = []

# Here's our regex. We want to find any biomarker name (include aliases if you think they will show up!)
# with whitespace or punctuation around it (so we want er/pr, :her2, her2:, etc.
regexp = re.compile(r'(?<=[ .\\\/,?!:\-;\n])(alk|braf|cdk4|cdk6|egfr|egfrviii|fgfr1|fgfr2|fgfr3|fgfr4|her2|hras|kras|met|microsatellite|msi|nras|ntrk1|ntrk2|ntrk3|pd-1|pd-l1|ret|ros1|stk11|tumor mutational|tmb|mlh1|pms2|msh2|msh6|apc|bmpr1a|epcam|grem1|mutyh|myh|smad4|skt11|lkb1)[ .\\\/,?!:\-;\r\n]')

# Putting this up front for ease of finding. Once we have our section extracted, we'll give it here.
# Moving all the formatting outside this call.
def extractBiom(text, testtype, pathol, dr, do):
    # Just a rew replacements
    ttype = testtype
    pathologist = pathol
    reportedDate = dr
    orderedDate = do
    section = text
    addResults(section, ttype, pathologist, dr, do)

# Takes metamap output and adds it to the final results!
def addResults(reso, testype, pathol, dater, dateo):
    reso = reso.strip()
    while '[removed' in reso:
        pullSec = reso[reso.index('[removed'):]
        pullSec = pullSec[:pullSec.index(']') + 1]
        reso = reso.replace(pullSec, ' ')
    reso = reso.replace('*endAdd*', '')
    resoOrig = reso
    reso = reso.replace('(see notes below)', '')
    reso = reso.replace('msi  ms-stable ', 'msi  ms-stable . .').replace('10 muts/mb ', '10 muts/mb . . ').replace(' raising the', '. . raising the').replace('pd-1', 'pd1')
    if '(see' in reso:
        reso = reso[:reso.index('(see')]
    if 'on a separately' in reso and 'antibodies against alk' in reso:
        reso = reso[reso.index('):') + 1:]
        reso = 'alk ' + reso
        reso = reso[:reso.index(';')]
    # Sometimes we have longer paragraphs that we need to cut off when they start talking about the meaning of results
    if any(endSent in reso for endSent in ['is a common', 'has been']) and len(reso.split()) > 1:
        resoSplit = reso.split('. ')
        reso = ''
        stopAdding = False
        for r in resoSplit:
            if any(endSent in r for endSent in ['is a common', 'has been']):
                stopAdding = True
            if not stopAdding:
                reso = reso + '. ' + r


    # A few late additions
    # These changes make it so that long chains of results are split up
    reso = reso.replace('\n', ' ').replace('and retained', '. . retained').replace('and normal', '. . normal').replace('and do not', '. . negative').replace('fgfr3-igh t(4;14):', '')
    reso = reso.replace('with loss', '. . loss').replace('and retained', '. . retained').replace('and positive', '. . and positive').replace('and negative', '. . and negative')
    resos = reso.split('. .')
    for reso in resos:
        file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
        with open(file, 'w') as filetowrite:
            filetowrite.write(reso)
        if reso.strip() != '':
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
                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testype, sampleLocation, pathol, dateo, dater, resoOrig, lowerOrig, icdCode, reportId,
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

# If false, this writes files. If true, it doesn't
testing = True

# If we only want a sub-range for testing, un-comment here
#for x in range(0, 10000):
for x in range(0, len(pathReports['patientid'])):
    if x % 100 == 0:
        print(x, ' out of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    # If we want a specific report, add its' id in here
    #if '0094138C-6BC4-4326-AA10-B40B30B80EE0' not in reportId and '0094138C-6BC4-4326-AA10-B40B30B80EE0' not in patientId:
    #    continue
    #if '9DEC66D8-F019-493E-AB54-76FE33228DAD' not in patientId:
    #    continue
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
    lower = lower.replace(' cps ', 'combined positive score')
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
                    print(addendum)
                    input()
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId = \
                        processSection(addendum, addendumTestType, addendumPathologist, addendumReported, addendumOrdered, regexp, reportId)
                    extractBiom(toExtract, addendumTestType, addendumPathologist, addendumReported, addendumOrdered)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId

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
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId = \
                        processSection(addendum, addendumTestType, addendumPathologist, addendumReported, addendumOrdered, regexp, reportId)
                    extractBiom(toExtract, addendumTestType, addendumPathologist, addendumReported, addendumOrdered)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId


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
        if testType in ['comprehensive solid tumor cancer panel (170 genes)', 'factor v (leiden)', 'hereditary multi cancer risk assesment panel (39 genes)',
                        'hereditary breast/ovarian cancer-related gene sequence analysis (20 genes)']:
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
                toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId = \
                    processSection(section, testType + ' - immunohistochemistry for mmr proteins:', pathologist, dateReported, dateOrdered, regexp, reportId)
                extractBiom(toExtract, testType + ' - immunohistochemistry for mmr proteins:', pathologist, dateReported, dateOrdered)
                noContentSections = noContentSections + noConSec
                noContentSectionIds = noContentSectionIds + noConSecId
                removedSections = removedSections + remSec
                removedSectionIds = removedSectionIds + remSecId
                addendumLeftovers = addendumLeftovers + addLefSec
                addendumLeftoverIds = addendumLeftoverIds + addLefSecId

            lower = lower.replace(resultsOrig, '')

        if 'cytogenetic impression:' in lower:
            results = lower[lower.index('cytogenetic impression:'):lower.index('interpretation')]
            lower = lower.replace(results, '')
            # Let's do some splitting-up work
            results = results[len('cytogenetic impression:'):].replace('\n', ' ').strip().replace('and negative', '. . negative').replace('and positive', '. . positive').replace('. ', '. . ')
            results = results.replace('results are abnormal and indicate', 'results are abnormal . . ').replace('but', '. .')
            for ender in ['fusion of', 'this finding', 'summary of', 'examined.', 'in the context', 'this pattern', 'these results']:
                if ender in results:
                    results = results[:results.index(ender)]
            # Sometimes we have to be smart and snip it off
            cutIt = False
            for subResult in results.split('. .'):
                if any(endsign in subResult for endsign in ['has been described']):
                    cutIt = True
                if cutIt:
                    results = results.replace(subResult, '')
            # Here, I want to make sure I put 'chromosome x' before every chromosome if we have like 'chromosomes 4, 5, 6'
            for subResult in results.split('. .'):
                origSR = subResult
                if 'chromosome' in subResult:
                    words = subResult.split()
                    for word in words:
                        if word.replace('.', '').replace(',', '').isnumeric():
                            if 'chromosome ' + word not in subResult:
                                subResult = subResult.replace(word, 'chromosome ' + word)
                results = results.replace(origSR, subResult)
            print(results)
            print('extract site 1')
            extractBiom(results, testType, pathologist, dateReported, dateOrdered)

        if 'immunohistochemistry microsatellite instability panel' in lower:
            results = lower[lower.index('immunohistochemistry microsatellite instability panel'):lower.index('scoring criteria: ')]
            lower = lower.replace(results, '')
            if regexp.search(section):
                toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId = \
                    processSection(section, testType + ' - immunohistochemistry microsatellite instability panel', pathologist, dateReported, dateOrdered, regexp, reportId)
                extractBiom(toExtract, testType + ' - immunohistochemistry microsatellite instability panel', pathologist, dateReported, dateOrdered)
                noContentSections = noContentSections + noConSec
                noContentSectionIds = noContentSectionIds + noConSecId
                removedSections = removedSections + remSec
                removedSectionIds = removedSectionIds + remSecId
                addendumLeftovers = addendumLeftovers + addLefSec
                addendumLeftoverIds = addendumLeftoverIds + addLefSecId

        if 'no clinically significant coding variants' in lower:
            section = lower[lower.index('no clinically significant coding variants'):]
            if 'tested' not in section:
                section = section[:section.index('regions')]
            else:
                section = section[:section.index('tested')]
            lower = lower.replace(section, ' [removed section pt 20] ')
            section = section.replace('\n', ' ')
            print(section)
            print('extract site 2')
            #input()
            extractBiom(section, testType, pathologist, dateReported, dateOrdered)

        # Finally, this is another place to find this
        if 'colorectal adenocarcinoma her-2/neu summary' in lower:
            section = lower[lower.index('colorectal adenocarcinoma her-2/neu summary'):]
            sectionWhole = section[:section.index('tissue studied:')]
            section = section[section.index('interpretation: ') + len('interpretation: '):]
            section = 'her2 ' + section[:section.index('her2 her2')].strip()
            lower = lower.replace(sectionWhole, ' [removed section pt 20] ')
            print(section)
            print('extract site 3')
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
                    'predicted copy number alterations', 'biopsied at', '\nresults: \n']

        if not any(bit in lower for bit in sections):
            if testType not in ['factor v (leiden)', 'microsatellite instability testing (msi)', 'autopsy report',
                                'comprehensive solid tumor cancer panel (170 genes)'] and regexp.search(lower) and (firstName != 'hema' and lastName != 'hema'):
                print(lower)
                print('couldnt find section in whole!')
                noSectionsList.append(lower)
                input()

        for x in sections:
            while x in lower:
                sectionEnders = ['results-comments', 'icd code(s)', 'comment\n', '***electronically', 'section 2:', 'technical note:', '*** end', 'methods', 'analyte specific',
                                 'loss of nuclear expression of', 'scoring criteria:', 'disclaimer', 'previous signout', 'the metastatic dimension', 'targeted therapy',
                                 'operative diagnoses', 'clinical interpretation:', '\nresults:', 'her2 her2 ihc']
                section = lower[lower.index(x) + len(x):]
                sectionWhole = lower[lower.index(x):]
                if not any(sec in section for sec in sectionEnders):
                    print(sectionWhole)
                    print(x)
                    print('COULDNT FIND END!')
                    #input()
                    #print(lowerOrig)
                    #   input()
                endPos = 9999999999
                for m in sectionEnders:
                    if m in section and m not in x and section.index(m) > 0:
                        if section.index(m) < endPos:
                            endPos = section.index(m)
                section = section[:endPos]
                sectionWhole = sectionWhole[:endPos + len(x)]
                section = section.replace('pdl1', 'pd-l1')


                # Here, we're pulling out pd-l1 results
                if 'pd-l1' in section and ('tumor proportion score' in section or 'combined positive score' in section or 'tps' in section or 'cps' in section) and \
                        not any(t in section for t in ['control cell line']):
                    if not section.strip().startswith('control'):
                        section = section.replace('molecular pathology and genomic\n', 'molecular pathology and genomic ').replace('22c3\n', '22c3 ').replace('28-8\n', '28-8 ')
                        for x in ['pd-l1(22c3,28-8), molecular pathology and genomic test:', 'pd-l1(22c3\\t\\28-8) molecular pathology and genomic test:', \
                                  'pd-l1(22c3,28-8), molecular pathology and genomic test:', 'pd-l1 (22c3 \\t\\ 28-8) molecular pathology and genomic test:', \
                                  'pd-l1 (22c3) and (28-8), molecular pathology and genomic test:', 'pd-l1(22c3, 28-8), molecular pathology and genomic test:']:
                            if x in section:
                                section = section[section.index(x) + len(x):]
                        resultBit = ''
                        # Skipping parts of the section, or normalizing the text
                        if 'expression by\n' in section:
                            section = section.replace('expression by\n', 'expression by ')
                        if 'molecular pathology and\n' in section:
                            section = section.replace('molecular pathology and\n', 'molecular pathology and ')
                        if 'clinically indicated.' in section:
                            section = section[section.index('clinically indicated.') + len('clinically indicated.'):]
                        secSplit = section.split('\n')
                        if 'there are no published' in section:
                            if 'correlation is recommended' not in section:
                                section = section[section.index('recommended.') + len('recommended.'):]
                            else:
                                section = section[section.index('correlation is recommended.') + len('correlation is recommended.'):]
                        line = 0
                        if ''.join(secSplit).strip() == '':
                            continue
                        while secSplit[line] in ['', ' ']:
                            line = line + 1
                        while ('pd-l1' in secSplit[line] or 'tps' in secSplit[line] or 'cps' in secSplit[line] \
                               or 'tumor proportion score' in secSplit[line] or 'combined positive score' in secSplit[line] or secSplit[line] == ' '):
                            # Don't need extra punctuation thanks
                            if '. . ' in secSplit[line]:
                                secSplit[line] = secSplit[line].replace('. . ', '')
                            # Sometimes we have a numeric code introducing what the text name is, like (ms-13) pd-l1. Let's dispense with it
                            if any(start + ' pd-l1' in secSplit[line] for start in [');', ',', '.', ')', '):', ';']):
                                for start in [');', ',', '.', ')']:
                                    if start + ' pd-l1' in secSplit[line]:
                                        secSplit[line] = secSplit[line][secSplit[line].index(start) + len(start) + 1:]
                                        if ';' in secSplit[line]:
                                            secSplit[line] = secSplit[line][:secSplit[line].index(';')]
                            if ('tumor proportion score' in secSplit[line] or 'combined positive score' in secSplit[line] or 'tps' in secSplit[line]\
                                or 'cps' in secSplit[line]) and '-' in secSplit[line]:
                                secSplit[line] = secSplit[line] + ' . . '
                            resultBit = resultBit + ' ' + secSplit[line]
                            if line == len(secSplit) - 1:
                                secSplit[line] = ''
                            else:
                                line = line + 1
                        resultBit = resultBit.replace(' d ', ' > ')
                        if '22c3' not in resultBit and '28-8' not in resultBit:
                            if 'pd-l1 (22c3) expression' in lowerOrig:
                                resultBit = '22c3 ' + resultBit
                            elif 'pd-l1 (28-8) expression' in lowerOrig:
                                resultBit = '28-8 ' + resultBit
                        if 'note:' in resultBit:
                            resultBit = resultBit[:resultBit.index('note:')]
                        extractBiom(resultBit, testType, pathologist, dateReported, dateOrdered)
                        print('extract site 4')
                        print(resultBit)
                        lower = lower.replace(lower, '')
                if 'note:' in section:
                    section = section[:section.index('note')].strip()
                    # This is a common, small section
                    if len(section.split('\n')) == 2:
                        section = section.replace('\n', ' ')
                # Turns out metamap doesn't handle long lists gracefully if not detected
                if '\nnone \n' in section:
                    section = section[section.index('none '):].strip().replace('detected', 'not detected')
                if 'comment:' in section:
                    section = section[section.index('comment:'):]
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId

                lower = lower.replace(sectionWhole, '')

        # We might have some small thing to send
        if regexp.search(lower):
            if lower[regexp.search(lower).start():].startswith('microsatellite stable'):
                section = lower[regexp.search(lower).start():][:lower[regexp.search(lower).start():].index('***elec')]
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                lower = lower.replace(section, '')
            if 'pd-l1' in lower and 'tumor proportion score:' in lower:
                if 'test: ' in lower:
                    lower = lower[lower.index('test: ') + len('test: '):]
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                lower = lower.replace(lower, '')
            if 'submitted immunostains for' in lower:
                lower = lower[lower.index('following results:') + len('following results:'):]
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                lower = lower.replace(lower, '')

        # Last chance for a slow dance, here
        if regexp.search(lower):
            foundSection = False
            if '\ncomment' in lower and '***electro' in lower:
                section = lower[lower.index('\ncomment'):]
                if '***electro' in section:
                    section = section[:section.index('***electro')]
                    foundSection = True
            if '\nresults' in lower:
                section = lower[lower.index('\nresults'):]
                if '***electro' in section:
                    section = section[:section.index('***electro')]
                    foundSection = True
            if 'operation/specimen' in lower and 'checklist:' in lower:
                section = lower[lower.index('checklist:'):]
                if 'checklist:' in section:
                    section = section[:section.index('checklist:')]
                    foundSection = True
            if foundSection:
                if regexp.search(section):
                    processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId)
                    lower = lower.replace(section, '')
        # Finally, let's remove any genes from the rest of the report!
        if regexp.search(lower):
            testsToCheckList.append(lower)
            testsToCheckTypeList.append(testType)
            for x in ['alk', 'braf', 'cdk4', 'cdk6', 'egfr', 'fgfr1', 'fgfr2', 'fgfr3', 'fgfr4', 'her2', 'hras', 'kras', 'met', 'tumor mutational burden', 'microsatellite', 'msi',
                          'nras', 'ntrk1', 'ntrk2', 'ntrk3', 'pd-1', 'pd-l1', 'ret', 'ros1', 'stk11', 'tmb', 'mlh1', 'pms2', 'msh2', 'msh6', 'apc', 'bmpr1a', 'epcam', 'grem1',
                      'mutyh', 'myh', 'smad4', 'skt11', 'lkb1']:
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
removedResults = pd.DataFrame(list(zip(removedSections, removedSectionIds)), columns=['removed sections', 'IDs'])
noContentResults = pd.DataFrame(list(zip(noContentSections, noContentSectionIds)), columns=['No content sections', 'IDs'])

if not testing:
    rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/TestRawOfLung.csv", index=False)
    removedResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/TestRemovedOfLung.csv", index=False)
    failResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/TesttestsWithNoSectionsToRemoveOfLung.csv", index=False)
    addendumLeftoverResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/TestleftoverBitOfPulledOutSectionsOfLung.csv", index=False)
    noContentResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/TestSectionsWithNoContentLung.csv", index=False)

#addendumNoGos = pd.DataFrame(list(zip(noContentSections)), columns=['unscanned'])

#addendumNoGos.to_csv("~/Desktop/LatestNLP/Unstructured Results/pulledOutSectionsUnableToScan.csv")
