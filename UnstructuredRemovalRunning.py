import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput
from metamapLoader import metamapStarter
from metamapLoader import metamapCloser
from UnstructuredTextSectionProcess import processSection

# Here we store specific tests that we need to be more carefully parsed
from UnstructuredSpecificTests import estrogenProgesteroneTest, estrogenImmunocyto

noBios = []

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# Now beginning the sorting out! This points to the most recent file
pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/May2020HFHS.csv", sep = '\t', low_memory=False)

# This is for tests that ended up with one of our biomarkers that didn't get parsed out somehow
testsToCheckList = []
testsToCheckTypeList = []

panelsTests = []

# This is for testing the addendum bits checked
addendumPiece = []

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
panelSections = []
panelSectionIds = []

processedSections = []
processedBits = []
noSectionsList = []

# These are tests that appear to have no sample associated with them
noSampleTests = []
noSampleIds = []

# These are sections we're excluding for being from previous studies, or if they're speculative
excludedSections = []
excludedReasons = []
excludedIds = []

# Putting this up front for ease of finding. Once we have our section extracted, we'll give it here.
# Moving all the formatting outside this call.
def extractBiom(text, testtype, pathol, dr, do, samLoc):
    # Just a rew replacements
    ttype = testtype
    pathologist = pathol
    reportedDate = dr
    orderedDate = do
    section = text
    sampleLocation = samLoc
    addResults(section, ttype, pathologist, dr, do, sampleLocation)

# Takes metamap output and adds it to the final results!
def addResults(reso, testype, pathol, dater, dateo, sampleLoc):
    reso = reso.strip()
    reso = reso.replace('*endAdd*', '')
    resoOrig = reso
    reso = reso.replace('(see notes below)', '')
    if 'addendum: addendum' in testype:
        testype = testype.replace('addendum: addendum', 'addendum')
    # This corrects if we have multiple tests chained together - like "fish test: sish test"
    if testype.count(':') > 1:
        testypesplit = testype.split(':')
        newtestype = testypesplit[0] + ':' + testypesplit[-1]
    # The point of this next bit is - if we add any new divisions (by adding in '. . 's, we also want to duplicate the appropriate location!
    changeLocs = []
    if any(x in reso for x in ['msi  ms-stable', 'muts/mb', ' raising the', ' but', 'and retained', 'and normal', 'and do not', 'with loss', 'and positive', 'and negative']):
        resplit = reso.split(' . . ')
        locsplit = sampleLoc.split(' . . ')
        changeLocs = []
        for r in range(0, len(resplit)):
            changeLocs.append(locsplit[r])
            while any(x in resplit[r] for x in ['msi  ms-stable', 'muts/mb', ' raising the', ' but', 'and retained', 'and normal', 'and do not', 'with loss', 'and positive', 'and negative']):
                for y in ['msi  ms-stable', 'muts/mb', ' raising the', ' but', 'and retained', 'and normal', 'and do not', 'with loss', 'and positive', 'and negative']:
                    if y in resplit[r]:
                        changeLocs.append(locsplit[r])
                        resplit[r] = resplit[r].replace(y, '', 1)
    if changeLocs != []:
        for bit in changeLocs:
            sampleLoc = sampleLoc.replace(bit + ' . . ', bit + ' . . ' + bit + ' . . ', 1)
    reso = reso.replace('msi  ms-stable ', 'msi  ms-stable . .').replace('muts/mb ', 'muts/mb . . ').replace(' raising the', '. . raising the').replace('pd-1', 'pd1')
    reso = reso.replace(' but ', ' . . ')
    # We want '>=1', not '>= 1', and we need it to be separated from previous words
    if '>=' in reso and ' >=' not in reso or '<=' in reso and ' <=' not in reso:
        reso = reso.replace('>=', ' >=').replace('<=', ' <=')
    if '>= ' in reso or '<= ' in reso:
        reso = reso.replace('>= ', '>=').replace('<= ', '<=')
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
    reso = reso.replace('with loss', '. . loss').replace('and positive', '. . positive').replace('and negative', '. . negative')
    resos = reso.split(' . . ')
    locs = sampleLoc.split(' . . ')

    if len(locs) == 1 and len(resos) != 1:
        while len(locs) < len(resos):
            locs.append(locs[0])
    for reso in resos:
        if reso in ['', ' ']:
            resos.remove(reso)
            continue
        resInd = resos.index(reso)
        thisLocation = locs[resInd].strip()
        file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
        with open(file, 'w') as filetowrite:
            filetowrite.write(reso)
        if reso.strip() != '':
            try:
                res = metamapstringoutput()
            except:
                testsToCheckList.append(lowerOrig)
                testsToCheckTypeList.append(testType)
                break
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
                if bioResult == '':
                    noBios.append(reso)
                conResult = ', '.join(row['Concept'])
                numResult = ', '.join(row['Numeric'])
                qualResult = ', '.join(row['Qualifier'])
                standardAppends(firstName, middleName, lastName, MRN, dob, accession, testype, thisLocation, pathol, dateo, dater, resoOrig, lowerOrig, icdCode, reportId,
                                patientId)
                biomarkerResultList.append(bioResult)
                conceptResultList.append(conResult)
                numericResultList.append(numResult)
                qualifierResultList.append(qualResult)
                # Make sure our lists are even
                lists = [biomarkerResultList, conceptResultList, numericResultList, qualifierResultList,
                                   firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionList, testTypeList, sampleLocationList,
                                   pathologistList, dateOrderedList, dateReportedList, testTextList, fullTextList, icdCodeList, patientIdList, reportIdList]
                it = iter(lists)
                the_len = len(next(it))
                if not all(len(l) == the_len for l in it):
                    print('not all lists have same length!')
                    #input()
                else:
                    print("LENGTH IS", len(biomarkerResultList))

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
testing = False

biomarkersTested = ['ki-67', 'ki67', 'ki 67', 'mib1', 'mib-1', 'mib 1']

expandedString = ''
for biom in biomarkersTested:
    expandedString = expandedString + biom + '|'
expandedString = expandedString[:-1]

reString = r'((?<=[ .\\\/,?!:\-;\n\(])|^)(' + expandedString + r')([ .\\\/,?!:\-;\r\n\+)]|$)'

# Here's our regex. We want to find any biomarker name (include aliases if you think they will show up!)
# with whitespace or punctuation around it (so we want er/pr, :her2, her2:, etc.
regexp = re.compile(reString)

# If we only want a sub-range for testing, un-comment here
#for x in range(0, 100000):
for x in range(0, len(pathReports['patientid'])):
    if x % 100 == 0:
        print(x, ' out of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    # If we want a specific report, add its' id in here
    #if '0094138C-6BC4-4326-AA10-B40B30B80EE0' not in reportId and '0094138C-6BC4-4326-AA10-B40B30B80EE0' not in patientId:
    #    continue
    #if '84692fa3-de93-47ce-9920-c2f9a567b835' not in str(reportId):
    #    continue
    #if '1dd46eef-9ccc-4a9c-9367-b3b0118f504a' not in str(patientId):
    #    continue
    # Preprocess the reports. All to lower, no plusses
    lower = str(pathReports['description'][x]).lower()
    lower = re.sub(' +', ' ', lower)
    splitReport = lower.split('\n')
    #print(lower)
    #input()
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
        section = lower[lower.index('reported:') + len('reported:'):]
        section = section[:section.index('\n')]
        dateReported = section
        reportedDate = dateReported.strip()
    else:
        dateReported = ''
        reportedDate = ''
    if 'ordered:' in lower:
        section = lower[lower.index('ordered:') + len('ordered:'):]
        section = section[:section.index('\n')]
        dateOrdered = section
        if 'date' in dateOrdered:
            dateOrdered = dateOrdered[:dateOrdered.index('date')]
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

    # We don't want to do some tests - adding this back in for ones we TRULY don't want to do
    if testType in ['autopsy report', 'factor v (leiden)', 'cystic fibrosis testing', 'spinal muscular atrophy', 'autopsy - anatomic preliminary report']:
        lower = ''
        continue

    # Let's see if we can get the specimen type:
    if any(x in lower for x in ['operation/specimen: ', 'operation/specimen ', 'type of specimen:', 'site of biopsy:', 'sample type:', 'dna analysis for:']):
        for x in ['operation/specimen: ', 'operation/specimen ', 'type of specimen:', 'site of biopsy:', 'sample type:', 'dna analysis for:']:
            if x in lower:
                ender = x
                break
        section = lower.index(ender)
        section = lower[section + len(ender):]
        if 'pathological diagnosis:' in section:
            section = section[:section.index('pathological')]
        elif '\n' not in section:
            section = section
        else:
            section = section[:section.index('\n')]
        section = section.strip()
        sampleLocation = section
    else:
        # The names listed below have tiny, truncated reports.
        if not any(x in lower for x in ['patient name: wheeler, deborah m.', 'patient name: soulliere, jessica', 'patient name: hurley, michael',
                                        'patient name: pauze, sherry']):
            sampleLocation = ''
            noSampleTests.append(lower)
            noSampleIds.append(reportId)

    # Here, we eliminate common non-test sources of the biomarkers
    lower = lower.replace('well as prominent braf and pdgfa mutations.', '')
    lower = lower.replace('msi: 81301, g0452', '').replace('alk-fish-m:', '').replace('msi-m:', '').replace('her2-sish: 88377', '').replace('egfrviii: 81403', '')
    lower = lower.replace('her2-fish: 88377', '')
    lower = lower.replace('apc machine', '')

    # Here are some common alternate spellings
    lower = lower.replace('mlh-1', 'mlh1').replace('egfr-viii', 'egfrviii').replace('egfr viii', 'egfrviii')
    lower = lower.replace('microsatellite status', 'msi ')
    lower = lower.replace('each \nprobe', 'each probe')
    lower = lower.replace('er/pr/her2', 'er and pr and her2').replace('er/pr', 'er and pr')
    lower = lower.replace('fgfr1/2/3/4', 'fgfr1, fgfr2, fgfr3, fgfr4').replace('ntrk1/2/3', 'ntrk1, ntrk2, ntrk3')
    lower = lower.replace(' cps ', 'combined positive score')

    # Just makes it easier to find this section later
    if 'following\nresults:' in lower:
        lower = lower.replace('following\nresults:', 'following results:')

    # We want to keep looking in the reports as long as we find the biomarker of interest somewhere!
    while regexp.search(lower):
        ################################
        ################################
        ################################
        # Let's remove panels and always non-test-related bits here. Also PROBABLY clinical history
        ################################
        ################################
        ################################
        removalBits = ['gene exon / amino acid (aa) coverage annotation transcript',
                       'gene location transcript cdna protein dp exon af interpretation',
                       'location transcript cdna',
                       'cdna protein dp exon af interpretation',
                       'gene location transcript cdna protein dp exon af label',
                       'gene variant exon cdna change chr genomic coordinates coverage allele fraction',
                       'gene transcript exons direction type',
                       'gene transcript exons direction',
                       'gene accession exon assay type direction',
                       'gene variant prediction cdna change chr genomic coordinates coverage allele',
                       'gene location',
                       'gene cdna protein',
                       'gene exon / (aa)',
                       'fusions category reads unique molecules breakpoints',
                       'genes ss reads %reads breakpoint',
                       'gene exon / amino acid (aa) coverage',
                       'gene target region (exon)',
                       'genomic findings detected fda-approved therapeutic options',
                       'genes unique start sites reads %of reads breakpoint category',
                       'mutations in 48 genes',
                       'references:',
                       'genes (5\'-3\') category reads unique molecules breakpoints',
                       'assay targets',
                       'gene chr genomic coordinates transcript cdna change protein change exon depth',
                       'gene location transcript cdna protein dp exon',
                       'gene location transcript cdna',
                       'list of target genes',
                       'variant of unknown significance gene location transcript cdna',
                       'pathogenic variant gene location transcript cdna protein dp',
                       'positive for the following coding variants:',
                       'clinical history',
                       'gene exons',
                       'due to superficial nature',
                       '#cells cytogenetic findings interpretation'
                       ]
        while any(x in lower for x in removalBits):
            if reportId not in panelsTests:
                panelsTests.append(reportId)
            # These are the strings that might potentially end a panel section. Find the one that's the closest to the start string, and go until you hit that.
            for y in removalBits:
                sectionEnders = ['disclaimer', '***ele', 'interpretation: ', 'specific mutations', 'target details', 'comment:', 'note:', 'results-comments', 'pathological diagnosis',
                                 'these longitudinal', 'fluorescent in situ hybridization (fish)', '\ncomment\n', 'this hereditary']
                if y in lower:
                    section = lower[lower.index(y):]
                    endBit = 99999999999
                    if not any(z in section for z in sectionEnders):
                        sectionEnders = [section.split()[-1]]
                    for bit in sectionEnders:
                        if bit in section:
                            if section.index(bit) < endBit:
                                endBit = section.index(bit)
                    section = section[:endBit]
            # If it's a panel, note that. Otherwise it goes in the general 'removed sections' bin
            if y in ['gene exon / amino acid (aa) coverage annotation transcript', 'gene location transcript cdna protein dp exon af interpretation',
                     'cdna protein dp exon af interpretation', 'gene location transcript cdna protein dp exon af label', 'gene location', 'gene exon / (aa)',
                     'gene variant exon cdna change chr genomic coordinates coverage allele fraction', 'gene transcript exons direction', 'genes ss reads %reads breakpoint',
                     'gene exon / amino acid (aa) coverage', 'gene target region (exon)', 'genes unique start sites reads %of reads breakpoint category', 'mutations in 48 genes',
                     'assay targets', 'gene chr genomic coordinates transcript cdna change protein change exon depth', 'gene location transcript cdna protein dp exon',
                     'gene location transcript cdna', 'list of target genes', 'gene transcript exons direction type', 'variant of unknown significance gene location transcript cdna',
                     'pathogenic variant gene location transcript cdna protein dp', 'positive for the following coding variants:', 'gene exons', 'gene cdna protein']:
                panelSections.append(section)
                panelSectionIds.append(reportId)
            else:
                removedSections.append(section)
                removedSectionIds.append(reportId)
            lower = lower.replace(section, '')

        # Special removal
        if 'section 1: potentially actionable genomic alterations' in lower:
            sec = lower[lower.index('section 1: potentially actionable genomic alterations'):]
            if '5. predicted' in sec:
                sec = sec[:sec.index('5. predicted') + len('5. predicted')]
            if 'comprehensive solid tumor panel' in sec:
                sec = sec[:sec.index('comprehensive solid tumor panel') + len('comprehensive solid tumor panel')]
            lower = lower.replace(sec, '')
            removedSections.append(sec)
            removedSectionIds.append(reportId)

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
        equalsLine = 0
        if len(indices) > 1:
            # We also want the first or main part!
            indices.insert(0, 0)
            addendumTestType = testType + ' - addendum'
            # We're gonna loop through these in reverse order, so that deleting an earlier one doesn't change the
            # index of a later one
            indices = reversed(indices)
            pathoForNextSection = []
            # We want to get the separate dates for each addendum, along with their full text.
            for ind in indices:
                # We're setting these by default to be what the main test's are.
                addendumOrdered = orderedDate
                addendumReported = reportedDate
                addendumPathologist = pathologist

                # Piecing off the index here.
                lowerBit = lower[ind:]
                lowerBitOrig = lowerBit
                lowerSplit = lowerBit.split('\n')
                lowerSplit = lowerSplit[1:]
                lowerSplit = list(filter(None, lowerSplit))
                pathoNextHolder = []
                # We end with "****electronically signed out***" followed by the pathologist. Let's snip him out.
                while any(x in lowerSplit[0] for x in ['pathologist', 'consultant', ' md', 'm.d.', 'phd', ',md']) or lowerSplit[0].replace(' ', '') == '':
                    if lowerSplit[0].replace(' ', '') != '':
                        pathoNextHolder.append(lowerSplit[0])
                    lowerSplit = lowerSplit[1:]

                # We set the pathologist based on this
                foundPatho = False
                if len(pathoForNextSection) > 1:
                    for x in pathoForNextSection:
                        if any(y in x for y in ['pathologist', 'consultant', ' md', 'm.d.', 'phd', ',md']):
                            addendumPathologist = x
                            foundPatho = True
                            break
                if not foundPatho:
                    addendumPathologist = ''

                # We'll add him in for double-checking purposes
                addendum = lowerSplit + pathoForNextSection
                # Now load this pathologist into the chamber, and reset the holder
                pathoForNextSection = pathoNextHolder
                pathoNextHolder = []
                addendum = '\n'.join(lowerSplit)
                addendum = addendum.strip()

                if regexp.search(addendum):
                    # If we have multiple dates, we probably want to split that up, right?
                    if len(re.findall('date ordered: ', addendum)) > 1:
                        if 'date reported: pending' not in addendum:
                            print("MULTI DATE SITUATION!")
                            print(addendum)
                            input()
                        for line in range(0, len(addendum.split('\n'))):
                            firstTest = False
                            if 'date reported: pending' in addendum.split('\n')[line]:
                                test1 = '\n'.join(addendum.split('\n')[:line+1])
                                test2 = '\n'.join(addendum.split('\n')[line+1:])
                                test1Ordered = test1[test1.index('date ordered: ') + len('date ordered: '):]
                                test1Ordered = test1Ordered[:test1Ordered.index('date')]
                                extractBiom('results pending', addendumTestType + ': ' + test1.split('\n')[0], addendumPathologist, 'pending', test1Ordered, sampleLocation)

                                addendum = test2
                                break

                    # This is where we end up when there's only one test in this addendum, thank goodness.
                    if 'date ordered:' in addendum:
                        addendumOrdered = addendum[addendum.index('date ordered: ') + len('date ordered: '): addendum.index('date reported')].strip()
                        addendumReported = addendum[addendum.index('date reported: ') + len('date reported: '):].strip()
                        try:
                            addendumReported = addendumReported[:addendumReported.index('\n')].strip()
                        except:
                            addendumReported = addendumReported.strip()

                    # These kind of aren't addenda at this point, but they ARE separate parts of the test, and we'll scan them separately.
                    else:
                        #print(lowerOrig)
                        #print('--------')
                        #print(addendum)
                        #print("NO DATE?!")
                        #print('-------')
                        #input()
                        addendumOrdered = orderedDate
                        addendumReported = reportedDate
                # If there is NOT a biomarker, don't BOTHER.
                else:
                    # Now delete the addendum
                    lower = lower.replace(lowerBitOrig, '')
                    continue
                # Otherwise... well, still delete it, but keep going.
                lower = lower.replace(lowerBitOrig, '')

                # Are there any specific tests in this addendum?
                if any(x in addendum for x in ['estrogen and progesterone receptor assay', 'estrogen receptor immunocytochemical assay:']):
                    if 'addendum:' in addendumTestType:
                        addendumTestType = testType[:addendumTestType.index('addendum') + len('addendum  ')]
                    if 'estrogen and progesterone receptor assay' in addendum:
                        addendumTestType = addendumTestType + ': estrogen and progesterone receptor assay'
                    else:
                        addendumTestType = addendumTestType + ' : estrogen and progesterone immunocytochemical assay'
                    if 'estrogen and progesterone receptor assay' in addendum:
                        returnString, addendumNew = estrogenProgesteroneTest(addendum)
                        addendum = addendumNew
                        addS = sampleLocation.replace('\n', ' ')
                        while len(addS.split('. .')) < len(returnString.split('. .')):
                            addS = addS + ' . . ' + sampleLocation.replace('\n', ' ')
                        extractBiom(returnString, addendumTestType, addendumPathologist, addendumReported, addendumOrdered, addS)
                        addendum = ''
                    elif 'estrogen receptor immunocytochemical assay:' in addendum:
                        print(addendum)
                        print('IMMUNOCYTOCHEMICAL STOP POINT')
                        input()

                # Let's make sure we're in the right place
                starter = ''
                if len(addendum.split('\n')) < 5:
                    ender = len(addendum.split('\n'))
                else:
                    ender = 5
                for line in range(0, ender):
                    if 'procedures/addenda' in addendum.split('\n')[line] or '=============' in addendum.split('\n')[line]:
                        starter = line

                if isinstance(starter, int):
                    addendum = '\n'.join(addendum.split('\n')[starter+1:])

                # We may want to look further for the 'real' addendum, if the first part is just saying it's an addendum
                if regexp.search(addendum):
                    if addendum.split('\n')[0] in ['amendments']:
                        lineSt = 0
                        foundProc = False
                        while not foundProc and lineSt < 10:
                            lineSt = lineSt + 1
                            if 'procedures/addenda' in addendum.split('\n')[lineSt]:
                                foundProc = True
                        if foundProc:
                            addendum = '\n'.join(addendum.split('\n')[lineSt+1:])
                # Now if not, scan this section, if it has a gene of interest
                if addendum.strip() == '':
                    continue
                # Sometimes the first line is a name. We want to skip
                while (len(addendum.split('\n')[0].split()) == 2 and not any(x in addendum.split('\n')[0] for x
                                    in ['description', 'cytometry', 'material', 'specimen', 'results', 'stains', 'consultation'])) or \
                    any(y in addendum.split('\n')[0] for y in ['phd', ' md ', 'm.d.', 'azx']):
                    print('SKIPPING LINE')
                    print(addendum.split('\n')[0])
                    addendum = '\n'.join(addendum.split('\n')[1:])
                # These are first lines that should be skipped
                while addendum.split('\n')[0] in ['', 'results reviewed', 'status:signed out', ' '] or any(x in addendum.split('\n')[0] for x in ['date ordered']):
                    addendum = '\n'.join(addendum.split('\n')[1:])
                # If the addendum starts with a sample name, let's call it 'sample analysis
                if re.search(r'^[a-z][\.:] ',addendum.split('\n')[0]):
                    addSplit = addendum.split('\n')
                    addSplit.insert(0, 'sample analysis')
                    addendum = '\n'.join(addSplit)
                    print(addendum)
                    print('HERE THE NEW')
                    input()
                # These are names of addenda tests
                if addendum.split('\n')[0] not in ['her-2/ neu gene amplification (fish) assay', 'her-2/ neu protein assay (ihc)', 'gross description', 'immunofluorescence',
                                                   'addendum', 'pcr for egfr variant iii mutation', 'her-2/ neu (sish) gene amplification assay', 'molecular pathology and genomic test',
                                                   'microsatellite instability testing (msi)', 'immunohistology', 'intra-operative consultation', 'mlh1 promoter methylation detection',
                                                   'outside pathology reports.', 'immunocytochemical stains', 'flow cytometry', 'pd-l1', 'icd-9(s):', 'interpretation', 'material examined',
                                                   'specimen description', 'ebv chromogenic in-situ hybridization assay', 'amendments', 'special stains', 'pcr, tissue identity',
                                                   'gestational disease profile', 'histochemistry', 'fusion panel - solid tumor (50 genes)', 'fluorescent in-situ hybridization assay',
                                                   'fusion panel - sarcoma (26 genes)', 'result:', 'ig kappa-lambda by cish', 'braf gene mutation analysis', 'cytogenetics result, fish',
                                                   'b cell gene rearrangement', 'cytogenetics results (hfah)', 'pcr for epidermal growth factor receptor',
                                                   'cytogenetics result, not specified', 'pathology and laboratory medicine',
                                                   'alk gene rearrangement (fish) assay', 'egfr tki sensitivity and resistance panel'] \
                                                and 'amendments for' not in addendum.split('\n')[0]:
                    print(lowerOrig)
                    print('--------------------------')
                    print(addendum)
                    print('---------------------------')
                    print('NEW ADDENDUM FIRST LINE')
                    print(addendum.split('\n')[0])
                    input()
                if 'addendum:' in addendumTestType:
                    addendumTestType = testType[:addendumTestType.index('addendum') + len('addendum  ')]
                addendumTestType = addendumTestType + ': ' + addendum.split('\n')[0]
                # This indicates that we have the main test
                if 'pathology and laboratory medicine' in addendum.split('\n')[0]:
                    addendumTestType = testTypeOrig
                addendum = '\n'.join(addendum.split('\n')[1:])
                toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                    processSection(addendum, addendumTestType, addendumPathologist, addendumReported, addendumOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                try:
                    extractBiom(toExtract, addendumTestType, addendumPathologist, addendumReported, addendumOrdered, specificSampleLoc)
                except:
                    print(lowerSplit)
                    #input()
                noContentSections = noContentSections + noConSec
                noContentSectionIds = noContentSectionIds + noConSecId
                removedSections = removedSections + remSec
                removedSectionIds = removedSectionIds + remSecId
                addendumLeftovers = addendumLeftovers + addLefSec
                addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                excludedSections = excludedSections + excludedS
                excludedReasons = excludedReasons + excludedR
                excludedIds = excludedIds + excludedI

        # Sometimes we'll have a procedures section without multiple 'electronically signed out's
        elif 'procedures/addenda' in lower:
            if not any(x in lower for x in ['era result (clone ']):
                print(lower)
                print('got a rogue procedures!')
                addendumTestType = 'addendum'
                #input()
            while 'procedures/addenda' in lower:
                addendum = lower[lower.index('procedures/addenda'):]
                if '***electronically' not in addendum:
                    if '*** end' not in addendum:
                        addendum = addendum
                    else:
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
                if 'pathologist\n' in addendum:
                    addSplit = addendum.split('\n')
                    for line in addSplit:
                        if 'pathologist\n' in line:
                            addendumPathologist = line
                else:
                    addendumPathologist = pathologist
                # Now delete the addendum
                lower = lower.replace(addendum, '')

                # Are there any specific tests in this addendum? Delete that bit from the addendum if so
                if any(x in addendum for x in ['estrogen and progesterone receptor assay', 'estrogen receptor immunocytochemical assay:']):
                    if 'addendum:' in addendumTestType:
                        addendumTestType = testType[:addendumTestType.index('addendum') + len('addendum  ')]
                    addendumTestType = addendumTestType + ' ' + 'estrogen and progesterone receptor assay'
                    if 'estrogen and progesterone receptor assay' in addendum:
                        returnString, addendumNew = estrogenProgesteroneTest(addendum)
                        addendum = addendumNew
                        extractBiom(returnString, addendumTestType, addendumPathologist, addendumReported, addendumOrdered, sampleLocation)
                    elif 'estrogen receptor immunocytochemical assay:' in addendum:
                        removedSections.append(addendum)
                        removedSectionIds.append(reportId)

                # Now scan this section, if it has a gene of interest
                if regexp.search(addendum):
                    addendumTestType = testType + ' - addendum'
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                        processSection(addendum, addendumTestType, addendumPathologist, addendumReported, addendumOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                    extractBiom(toExtract, addendumTestType, addendumPathologist, addendumReported, addendumOrdered, specificSampleLoc)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                    excludedSections = excludedSections + excludedS
                    excludedReasons = excludedReasons + excludedR
                    excludedIds = excludedIds + excludedI

        ####################################
        ####################################
        ####################################
        # Otherwise, now that we've handled the procedures/addenda, we should just have the main test.
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
                if 'pathologist' in line and ',' in line:
                    pathologist = line[:line.index(',')]
        else:
            pathologist = lowSplit[endLine + 1]
            pathologist = pathologist[0:pathologist.rfind(',')]
        if 'date reported:' in lower:
            dateReported = lower[lower.index('date reported:') + len('date reported:'):]
            dateReported = dateReported[:dateReported.index('\n')]
            reportedDate = dateReported.strip()
        elif 'reported:' in lower:
            dateReported = lower[lower.index('reported:') + len('reported:'):]
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
        elif 'taken:' in lower:
            dateOrdered = lower[lower.index('taken:') + len('taken:'):]
            dateOrdered = dateOrdered[:dateOrdered.index('\n')]
            orderedDate = dateOrdered.strip()
        elif 'received:' in lower:
            dateOrdered = lower[lower.index('received:') + len('received:'):]
            dateOrdered = dateOrdered[:dateOrdered.index('\n')]
            orderedDate = dateOrdered.strip()

        else:
            orderedDate = ''

        # First, we'll pull out the good stuff
        if testType in ['molecular pathology and genomic test'] and 'immunohistochemistry for mmr proteins:' in lower:
            results = lower[lower.index('immunohistochemistry for mmr proteins:'):]
            results = results[:results.index('results-comments')]
            if 'immunohistochemistry for mmr proteins:' in results:
                resultsOrig = results
                results = results[results.index('immunohistochemistry for mmr proteins:') + len('immunohistochemistry for mmr proteins:'):].strip()
            if regexp.search(section):
                toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                    processSection(section, testType + ' - immunohistochemistry for mmr proteins:', pathologist, dateReported, dateOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                extractBiom(toExtract, testType + ' - immunohistochemistry for mmr proteins:', pathologist, dateReported, dateOrdered, specificSampleLoc)
                noContentSections = noContentSections + noConSec
                noContentSectionIds = noContentSectionIds + noConSecId
                removedSections = removedSections + remSec
                removedSectionIds = removedSectionIds + remSecId
                addendumLeftovers = addendumLeftovers + addLefSec
                addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                excludedSections = excludedSections + excludedS
                excludedReasons = excludedReasons + excludedR
                excludedIds = excludedIds + excludedI

            lower = lower.replace(resultsOrig, '')

        # Are there any specific tests in this addendum?
        if any(x in lower for x in ['estrogen and progesterone receptor assay']):
            if testType != 'estrogen and progesterone receptor assay':
                testType = testType + ' - estrogen and progesterone receptor assay'
            if 'estrogen and progesterone receptor assay' in lower:
                returnString, lowerNew = estrogenProgesteroneTest(lower)
                lower = lowerNew
                extractBiom(returnString, testType, pathologist, dateOrdered, dateReported, sampleLocation)

        if 'brca1/2 sequencing' in testType:
            if 'pathogenic mutation(s): none detected' in lower and 'variant(s) of unknown significance: none detected' in lower and 'gross deletion(s)/duplication(s): none detected' in lower:
                returnString = 'brca1 no pathogenic mutations . . brca2 no pathogenic mutations . . brca1 no deletions or duplications . . brca2 no deletions or duplications'
                extractBiom(returnString, testType, pathologist, dateOrdered, dateReported, sampleLocation)
            if 'no pathogenic mutations, variants of unknown significance' in lower:
                returnString = 'brca1 no pathogenic mutations . . brca2 no pathogenic mutations . . brca1 no deletions or duplications . . brca2 no deletions or duplications'
                extractBiom(returnString, testType, pathologist, dateOrdered, dateReported, sampleLocation)
                # This is a piece of test info to remove
                if 'disclaimer' in lower:
                    remSection = lower[lower.index('no pathogenic mutations'):lower.index('disclaimer')]
                    lower = lower.replace(remSection, '')
            if 'brca1 and brca2' in lower:
                remSec = lower[lower.index('brca1 and brca2'):]
                if 'disclaimer' in remSec:
                    remSec = remSec[:remSec.index('disclaimer')]
                    lower = lower.replace(remSec, '')

        if 'cytogenetic impression:' in lower and 'this array profile is' not in lower:
            if 'interpretation' in lower:
                results = lower[lower.index('cytogenetic impression:'):lower.index('interpretation')]
            else:
                results = lower[lower.index('cytogenetic impression:'):]
            lower = lower.replace(results, '')
            # We don't want the summary of what the results mean
            if 'overall, these' in results:
                results = results[:results.index('overall, these')]
            # Let's do some splitting-up work
            results = results[len('cytogenetic impression:'):].replace('\n', ' ').strip().replace('and negative', '. . negative').replace('and positive', '. . positive').replace('. ', '. . ')
            results = results.replace('results are abnormal and indicate', 'results are abnormal . . ').replace(' but ', '. .').replace('and gains', '. . gains').replace(' including', ' . . including').replace('fusion, ', 'fusion . . ')
            results = results.replace('regions and', 'regions . . ')
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
            if 'a her2 to chromosome' in results:
                results = results[:results.index('a her2 to chromosome')]
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
            if regexp.search(results):
                #print(results)
                tSampleLoc = sampleLocation
                while len(results.split('. . ')) > len(tSampleLoc.split(' . . ')):
                    tSampleLoc = tSampleLoc + ' . . ' + sampleLocation
                results = re.sub(r'(?<=[^\s])\. \. ', ' . . ', results)
                extractBiom(results, testType, pathologist, dateReported, dateOrdered, tSampleLoc)

        if 'immunohistochemistry microsatellite instability panel' in lower:
            results = lower[lower.index('immunohistochemistry microsatellite instability panel'):lower.index('scoring criteria: ')]
            lower = lower.replace(results, '')
            if regexp.search(section):
                toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                    processSection(section, testType + ' - immunohistochemistry microsatellite instability panel', pathologist, dateReported, dateOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                extractBiom(toExtract, testType + ' - immunohistochemistry microsatellite instability panel', pathologist, dateReported, dateOrdered, specificSampleLoc)
                noContentSections = noContentSections + noConSec
                noContentSectionIds = noContentSectionIds + noConSecId
                removedSections = removedSections + remSec
                removedSectionIds = removedSectionIds + remSecId
                addendumLeftovers = addendumLeftovers + addLefSec
                addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                excludedSections = excludedSections + excludedS
                excludedReasons = excludedReasons + excludedR
                excludedIds = excludedIds + excludedI


        if 'no clinically significant coding variants' in lower:
            section = lower[lower.index('no clinically significant coding variants'):]
            if 'tested' not in section:
                section = section[:section.index('regions')]
            else:
                section = section[:section.index('tested')]
            lower = lower.replace(section, ' [removed section pt 20] ')
            section = section.replace('\n', ' ')
            #print(section)
            print('extract site 2')
            #input()
            extractBiom(section, testType, pathologist, dateReported, dateOrdered, sampleLocation)

        # Finally, this is another place to find this
        if 'colorectal adenocarcinoma her-2/neu summary' in lower:
            section = lower[lower.index('colorectal adenocarcinoma her-2/neu summary'):]
            sectionWhole = section[:section.index('tissue studied:')]
            section = section[section.index('interpretation: ') + len('interpretation: '):]
            section = 'her2 ' + section[:section.index('her2 her2')].strip()
            lower = lower.replace(sectionWhole, ' [removed section pt 20] ')
            print('extract site 3')
            extractBiom(section, testType + ' - colorectal adenocarcinoma panel', pathologist, dateReported, dateOrdered, sampleLocation)

        # If this is panel results, just test the whole thing
        if any(x in lower for x in ['results\nnegative', 'no pathogenic mutations,', 'results\npositive', 'no additional pathogenic', 'no other pathogenic', 'results\nvous']):
            toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                processSection(lower, testType, pathologist, dateReported, dateOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
            extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered, specificSampleLoc)
            noContentSections = noContentSections + noConSec
            noContentSectionIds = noContentSectionIds + noConSecId
            removedSections = removedSections + remSec
            removedSectionIds = removedSectionIds + remSecId
            addendumLeftovers = addendumLeftovers + addLefSec
            addendumLeftoverIds = addendumLeftoverIds + addLefSecId
            excludedSections = excludedSections + excludedS
            excludedReasons = excludedReasons + excludedR
            excludedIds = excludedIds + excludedI
            lower = ''

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
            if testType not in ['factor v (leiden)', 'microsatellite instability testing (msi)', 'autopsy report', 'autopsy - anatomic preliminary report',
                                'comprehensive solid tumor cancer panel (170 genes)'] and regexp.search(lower) and (firstName != 'hema' and lastName != 'hema'):
                #print(lower)
                print('couldnt find section in whole!')
                noSectionsList.append(lower)

        for x in sections:
            while x in lower:
                sectionEnders = ['results-comments', 'icd code(s)', 'comment\n', '***electronically', 'section 2:', 'technical note:', '*** end', 'methods', 'analyte specific',
                                 'loss of nuclear expression of', 'scoring criteria:', 'disclaimer', 'previous signout', 'the metastatic dimension', 'targeted therapy',
                                 'operative diagnoses', 'clinical interpretation:', '\nresults:', 'her2 her2 ihc']
                section = lower[lower.index(x) + len(x):]
                sectionWhole = lower[lower.index(x):]
                if not any(sec in section for sec in sectionEnders):
                    #print(sectionWhole)
                    print('COULDNT FIND END!\n')
                    #input()
                    #print(lowerOrig)
                    #input()
                endPos = 9999999999
                for m in sectionEnders:
                    if m in section and not ('refer to the ' + m) in section.replace('\n', ' ') and m not in x and section.index(m) > 0:
                        if section.index(m) < endPos:
                            endPos = section.index(m)
                section = section[:endPos]
                sectionWhole = sectionWhole[:endPos + len(x)]
                section = section.replace('pdl1', 'pd-l1')
                # Here, we're pulling out pd-l1 results
                if x in ['results-comments'] and 'pd-l1' in section and 'control cell line' in section:
                    section = ''
                if 'pd-l1' in section and ('tumor proportion score' in section or 'combined positive score' in section or 'tps' in section or 'cps' in section) and \
                        not any(t in section for t in ['control cell line', 'this assay has been fda approved']):
                    # PD-L1 in 'results-comments' seems like always just a description of the test
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
                            if len(secSplit[line].split()) > 1:
                                if secSplit[line].split()[0] in ['cps', 'tps'] and '-' in secSplit[line].split()[1] or '>' in secSplit[line].split()[1] or '>' in secSplit[line].split()[1]:
                                    secSplit[line] = '. .'
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
                            if 'pd-l1 (22c3) expression' in lowerOrig and 'pd-l1 (28-8) expression' in lowerOrig:
                                print(lowerOrig)
                                print("DOUBLE TROUBLE IN PD-L1?!")
                                #input()
                            elif 'pd-l1 (22c3) expression' in lowerOrig:
                                resultBit = '22c3 ' + resultBit
                            elif 'pd-l1 (28-8) expression' in lowerOrig:
                                resultBit = '28-8 ' + resultBit
                        # These are addenda to the results that we want to cut
                        if 'note:' in resultBit:
                            resultBit = resultBit[:resultBit.index('note:')]
                        if '[tps' in resultBit:
                            resultBit = resultBit[:resultBit.index('[tps')]
                        if 'tps >' in resultBit:
                            resultBit = resultBit[:resultBit.index('tps >')]
                        pdExp = re.compile(r'\((?!(?:pd|2|cp))')
                        if pdExp.search(resultBit):
                            resultBit = resultBit[:pdExp.search(resultBit).start()]
                        extractBiom(resultBit, testType, pathologist, dateReported, dateOrdered, sampleLocation)
                        lower = lower.replace(section, '')
                        section = ''
                if 'note:' in section:
                    lilSection = section[:section.index('note')].strip()
                    # This is a common, small section
                    if len(lilSection.split('\n')) == 2:
                        section = lilSection.replace('\n', ' ')
                # Turns out metamap doesn't handle long lists gracefully if not detected
                if '\nnone \n' in section:
                    section = section[section.index('none '):].strip().replace('detected', 'not detected')
                if 'comment:' in section and not any(x in section for x in ['pathogenic mutations, variants', 'pathogenic mutations or variants']):
                    section = section[section.index('comment:'):]
                # We want the whole panel
                if any(x in section for x in ['results\nnegative', 'results\npositive', 'panel includes']):
                    section = lower
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered, specificSampleLoc)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                    excludedSections = excludedSections + excludedS
                    excludedReasons = excludedReasons + excludedR
                    excludedIds = excludedIds + excludedI

                lower = lower.replace(sectionWhole, '')

        # We might have some small thing to send
        if regexp.search(lower):
            if lower[regexp.search(lower).start():].startswith('microsatellite stable'):
                if '***elec' in lower:
                    section = lower[regexp.search(lower).start():][:lower[regexp.search(lower).start():].index('***elec')]
                else:
                    section = lower[regexp.search(lower).start():]
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered, specificSampleLoc)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                    excludedSections = excludedSections + excludedS
                    excludedReasons = excludedReasons + excludedR
                    excludedIds = excludedIds + excludedI

                lower = lower.replace(section, '')
            if 'pd-l1' in lower and 'tumor proportion score:' in lower:
                if 'test: ' in lower:
                    lower = lower[lower.index('test: ') + len('test: '):]
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered, specificSampleLoc)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                    excludedSections = excludedSections + excludedS
                    excludedReasons = excludedReasons + excludedR
                    excludedIds = excludedIds + excludedI

                lower = lower.replace(lower, '')
            if 'submitted immunostains for' in lower:
                lower = lower[lower.index('showed the following results:'):]
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered, specificSampleLoc)
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                    excludedSections = excludedSections + excludedS
                    excludedReasons = excludedReasons + excludedR
                    excludedIds = excludedIds + excludedI

                lower = lower.replace(lower, '')

        # Last chance for a slow dance, here
        if regexp.search(lower):
            foundSection = False
            skip = False
            if '\ndna analysis for:' in lower:
                section = lowerOrig[lowerOrig.index('dna analysis for:'):]
                if 'disclaimer: ' not in section:
                    if 'report comments' not in section:
                        section = section
                    else:
                        section = section[:section.index('report comments')]
                else:
                    section = section[:section.index('disclaimer: ')]
                foundSection = True
                skip = True
            if '\ncomment' in lower and '***electro' in lower and not skip:
                section = lower[lower.index('\ncomment'):]
                if '***electro' in section:
                    section = section[:section.index('***electro')]
                    foundSection = True
            if '\nresults' in lower and not skip:
                section = lower[lower.index('\nresults'):]
                if '***electro' in section:
                    section = section[:section.index('***electro')]
                    foundSection = True
            if 'operation/specimen' in lower and 'checklist:' in lower and not skip:
                section = lower[lower.index('checklist:'):]
                if 'checklist:' in section:
                    section = section[:section.index('checklist:')]
                    foundSection = True
            if foundSection:
                if regexp.search(section):
                    toExtract, noConSec, noConSecId, remSec, remSecId, addLefSec, addLefSecId, specificSampleLoc, excludedS, excludedR, excludedI = \
                        processSection(section, testType, pathologist, dateReported, dateOrdered, regexp, reportId, biomarkersTested, sampleLocation, lowerOrig)
                    extractBiom(toExtract, testType, pathologist, dateReported, dateOrdered, specificSampleLoc)
                    lower = lower.replace(section, '')
                    noContentSections = noContentSections + noConSec
                    noContentSectionIds = noContentSectionIds + noConSecId
                    removedSections = removedSections + remSec
                    removedSectionIds = removedSectionIds + remSecId
                    addendumLeftovers = addendumLeftovers + addLefSec
                    addendumLeftoverIds = addendumLeftoverIds + addLefSecId
                    excludedSections = excludedSections + excludedS
                    excludedReasons = excludedReasons + excludedR
                    excludedIds = excludedIds + excludedI

        # Finally, let's remove any genes from the rest of the report!
        if regexp.search(lower):
            testsToCheckList.append(lower)
            testsToCheckTypeList.append(testType)
            for x in biomarkersTested:
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
panelResults = pd.DataFrame(list(zip(panelSections, panelSectionIds)), columns = ['panels', 'report Id'])
noSampleTests = pd.DataFrame(list(zip(noSampleTests, noSampleIds)), columns=['tests','ids'])
excludedSectionsResults = pd.DataFrame(list(zip(excludedSections, excludedReasons, excludedIds)), columns=['Excluded Sections', 'Reasons', 'Ids'])


if not testing:
    rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/TestRaw2.csv", index=False)
    removedResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/TestRemoved2.csv", index=False)
    failResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/TesttestsWithNoSectionsToRemove2.csv", index=False)
    addendumLeftoverResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/TestleftoverBitOfPulledOutSections2.csv", index=False)
    noContentResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/TestSectionsWithNoContent2.csv", index=False)
    panelResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/Panels2.csv", index=False)
    noSampleTests.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/ShortTests2.csv")
    excludedSectionsResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/ExcludedSections2.csv")

#addendumNoGos = pd.DataFrame(list(zip(noContentSections)), columns=['unscanned'])

#addendumNoGos.to_csv("~/Desktop/LatestNLP/Unstructured Results/pulledOutSectionsUnableToScan.csv")

for bio in noBios:
    print(bio)