import pandas as pd
import numpy as np
# For regex
import re
from datetime import datetime
import string
import os

# This is for matching misspelled section headers.
import regex

# Let's append tests that don't seem to work well
brokenTests = []
brokenTestReasons = []

#let's also get tests we're not picking up
panelsDropped = []
panelIdsDropped = []

# Right, so we'll process these reports in chunks. Henry Ford tends to give us reports in a very standardized
# format, so we'll process the bits we can with pattern matching, then put the rest through metamap or something.

# This function looks for a more specific test type, given the index of the test we're starting at
# Let's see if we can find a more specific test type
def findSpecificTest(indexSt, testName):
    if testName == 'molecular pathology and genomic test':
        if ' a: ' in pathReport or '\na: ' in pathReport:
            if ' a: ' in pathReport:
                bit = pathReport[pathReport.index(' a: ') + len(' a: '):]
            else:
                bit = pathReport[pathReport.index('\na: ') + len('\na: '):]
        elif 'procedures/addenda' in pathReport:
            if 'procedures/addenda' in pathReport:
                bit = pathReport[pathReport.index('procedures/addenda') + len('procedures/addenda'):]
                bit = bit[:bit.index('date')]
                return bit.strip()
        else:
            panelChoices = ['fusion sarcoma panel', 'truseq amplicon cancer panel']
            if any(panel in pathReport for panel in panelChoices):
                for pc in panelChoices:
                    if pc in pathReport:
                        return pc
            else:
                return 'molecular pathology and genomic test'
                print(pathReportOrig)
                print('didnt have a:!')
                input()

        if ' b: ' in pathReport or '\nb: ' in pathReport:
            print(pathReport)
            print('review for b!')
            input()
        bit = bit[:bit.index('=')]
        bit = bit.strip()
        while '\n' in bit:
            bit = bit.replace('\n', '')
        while '  ' in bit:
            bit = bit.replace('  ', ' ')
        if ',' in bit:
            bit = bit[bit.index(',') + 1:].strip()
        elif ';' in bit:
            bit = bit[bit.index(';') + 1:].strip()
        bit = bit.replace('\t', ' ')
        return bit
    elif testName in['surgical pathology report', 'molecular studies report']:
        if 'procedures/addenda' in pathReport:
            bit = pathReport[pathReport.index('procedures/addenda') + len('procedures/addenda'):]
            bit = bit[:bit.index('date')]
            return bit.strip()
        elif 'pathologist' in pathReport and 'date' in pathReport[pathReport.index('pathologist'):]:
            bit = pathReport[pathReport.index('pathologist') + len('pathologist'):]
            bit = bit[:bit.index('date')]
            return bit.strip()
        else:
            print('surg path r')
            print(pathReportOrig)
            print('')
            print(pathReport)
            #input()
    elif testName in ['hematopathology report']:
        if 'pathologist' in pathReport:
            pathLocations = [zm.start() for zm in re.finditer('pathologist', pathReport)]
            finalLoc = 0
            for pl in pathLocations:
                if pl > finalLoc and pl < indexSt:
                    finalLoc = pl
            bit = pathReport[finalLoc + len('pathologist'):]
            bit = bit[:bit.index('date')]
            return bit.strip()
        else:
            print(pathReportOrig)
            print('no patho in hemo!')
            return pathReport
            #input()
    else:
        print(testName)
        print('other')
        print(pathReportOrig)
        print(pathReport[indexSt:])
        input()


# Tally ho
df = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/May2020HFHS.csv", sep = '\t', low_memory=False)
#df = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020.csv", low_memory=False)
# Use this to truncate huge files for quicker testing
#truncated = df.iloc[5000000:]
#truncated.to_csv("~/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020.csv", index=False)
#print("LOADED!")
#input()

# The list of tests we're pulling from
panelTests = ['lung adenocarcinoma panel', 'hematolymphoid sequencing panel (51 genes)', 'rapid flt3 mutation assesment',
              'truseq 48 gene cancer panel', 'lymphoid neoplasm panel', 'colorectal cancer panel', 'q rt-pcr, aml-m3, pml/rara t(15;17)',
              'hematolymphoid sequencing panel (54 genes)', 'melanoma panel', 'jak2 mutational analysis',
              'gastrointestinal stromal tumors (gist) panel', 'myelodysplastic syndrome (mds) panel',
              'molecular pathology and genomic test', 'braf gene mutation analysis', 'myd88 mutational analysis',
              'myeloproliferative neoplasm (mpn) panel', 'egfr tki sensitivity and resistance panel',
              'de novo aml panel', 'molecular studies report', 'kras gene mutation analysis', 'calr (calreticulin) mutations',
              'flt3, aml', 'npm1 mutational analysis', 'custom hereditary cancer risk test', 'tp53 mutational analysis',
              'idh1 mutation detection assay', 'brca1/2 sequencing and common deletions / duplications', 'glioma solid tumor sequencing panel']


# These are 'generic' tests, that probably have a more specific test name in them
genericTests = ['molecular pathology and genomic test', 'molecular studies report', 'surgical pathology report', 'hematopathology report']

# This extra one is for saving gene/exon coding regions from reports.
geneTestedList = []
exonTestedList = []
aminoAcidTestedList = []

# This list is to double-check and see how many tests with panels aren't getting represented
testsWithPanelsList = []

# We'll want to save a list per every result for all the structured fields, along with the parts of the result that
# we get from the panels.
reportIdList, sourceList, healthOrgList, MRNList, firstNameList, middleNameList, lastNameList, jrSrList, DOBList, genderList, \
        testTypeList, testReportedDateList, testApproveList, geneList, locationList, transcriptList, cdnaList, proteinList,\
        dpList, exonList, alleleFrequencyList, labelList, aminoAcidRangeList, icdCodeList, accessionList, \
        physicianList, takenList, statusList, fullTestList, specimenCodeList, specimenTypeList, pdfLinkList, pathologistList, orderedDateList = ([] for i in range(34))


# This is for the variant panel 'fusions'
fusionreportIdList, fusionsourceList, fusionhealthOrgList, fusionMRNList, fusionfirstNameList, fusionmiddleNameList, fusionlastNameList, fusionjrSrList, fusionDOBList, fusiongenderList, \
        fusiontestTypeList, fusiontestReportedDateList, fusiontestApproveList, fusionList, fusioncategoryList, fusionreadsList, fusionuniqueMolList, fusionStartSitesList, fusionbreakpointsList, \
        fusionicdCodeList, fusionaccessionList, fusionphysicianList, fusiontakenList, fusionstatusList, fusionfullTestList, fusionspecimenCodeList, fusionspecimenTypeList, \
        fusionpdfLinkList, fusionpathologistList, fusionorderedDateList, fusiondirectionList, fusionexonList, fusiontranscriptList, fusionlabelList = ([] for i in range(34))

#   for x in range(0, 20000):
#   for x in range(422300, len(df)):
for x in range(0, len(df['description'])):
    #     try:
    if x % 100 == 0:
        print(x, ' of ', len(df['description']))
    patientId = df['patientid'][x]
    reportId = df['id'][x]

    # DEBUGGIN'
    # Make this true if you want to save the results
    saveResults = True

    debug = False
    checkMeEnd = False

    if 'ecedfd0a-b01f-4ec8-9fff-37e2ae37cc53' not in str(reportId):
        continue

    lower = str(df['description'][x]).lower()
    lower = re.sub(' +', ' ', lower)
    origLower = lower
    if debug:
        print(origLower)
        input()
    splitReport = lower.split('\n')

    # We want to filter out duplicates
    reportIdsSoFar = []

    # For catching all the kinds
    allSectionLists = []

    namesAndSources = set()
    allSources = set()

    lower = lower.split('\n')
    for l in range(0, len(lower)):
        lower[l] = lower[l].strip()

    pathReport = '|'.join(lower)
    pathReportFull = '\n'.join(lower)
    pathReport = re.sub(' +', ' ', pathReport)
    pathReport = pathReport.lower()

    # This is our marker to show that there is no panel result - if that's true, we'll have to add a blank
    # amino acid range for every marker we find.
    noPanel = False

    # This is the 'fast lane' to a variety of figures we might be interested in
    if reportId not in reportIdsSoFar:
        reportIdsSoFar.append(reportId)

    # This is where we get the date reported and MRN.
    # if we don't have 'reported', it's one of those regnadson assays
    if 'reported:' not in pathReport:
        continue
    reportedIndex = pathReport.index("reported:")
    date = pathReport[reportedIndex + 9:reportedIndex + 20].replace("|", '').replace("p", '').replace('r', '')
    date = date.strip()
    # This is a fish test - maybe good for pulling out for non-panels, but not useful here
    if 'rec.:' not in pathReport:
        continue
    mrnIndex = pathReport.index("rec.:")
    MRN = pathReport[mrnIndex + 5:mrnIndex + 14]
    # This means the date is 'pending'
    if 'ending' in date:
        date = ''

    # This is where we get the signout date - sometimes it's not different than the reported date
    try:
        receivedIndex = pathReport.index("received:")
        received = pathReport[receivedIndex + 9:receivedIndex+20].replace('|', '').replace('p', '').replace('r', '')
        received = received.strip()
        if not received.replace('/', '').isnumeric():
            received = date
    except:
        received = date

    try:
        received = datetime.strptime(received, '%m/%d/%Y')
        received = received.strftime('%m/%d/%Y')
    except Exception as E:
        if not received == '':
            print(pathReportFull)
            print(received)
            input()

    if received < date:
        received = date

    try:
        date = datetime.strptime(date, '%m/%d/%Y')
        date = date.strftime('%m/%d/%Y')
    except:
        if not date == '':
            print(pathReportFull)
            print(date)
            input()

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
                pathologist = 'Not Given'

    # Let's get the sample Id, if they have it
    specimenCode = []
    specimenType = []
    if 'operation/specimen' in pathReport:
        reportedIndex = pathReport.index("operation/specimen")
        if '||' not in pathReport[reportedIndex + 19:]:
            brokenTests.append(origLower)
            brokenTestReasons.append('no good operation/specimen')
            continue
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

    pdfLink = "s3://syapse-prod-nlp-sqa/" + str(reportId).upper() + "_" + accession.upper() + "_txt.txt"

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

    if taken != '':
        taken = datetime.strptime(taken, '%m/%d/%Y')
        taken = taken.strftime('%m/%d/%Y')


    if 'date ordered:' in pathReport:
        testOrderedIndex = pathReport.index('date ordered:')
        ordered = pathReport[testOrderedIndex + 13:testOrderedIndex+24].replace('|','').replace('s','').strip()
        if not ordered[-1].isnumeric():
            ordered = ordered[:-1].strip()
        try:
            ordered = datetime.strptime(ordered, '%m/%d/%Y')
            ordered = ordered.strftime('%m/%d/%Y')
        except:
            ordered = taken

    else:
        # Default to collected date
        ordered = taken


    if 'status:' not in pathReportFull:
        status = ''
    else:
        reportedIndex = pathReport.index("status:")
        statusBit = pathReport[reportedIndex + 7:]
        postStatusBreak = statusBit.index("|")
        status = pathReport[reportedIndex + 7: reportedIndex + 7 + postStatusBreak].strip()

    # And we'll pull out the healthcareOrg here
    healthOrg = pathReport.split('|')[0]

    nameIndex = pathReportFull.index('name:')
    endName = pathReportFull.index('accession')
    nameBit = pathReportFull[nameIndex + 5: endName]
    firstName = nameBit.split(',')[1].strip()
    lastName = nameBit.split(',', )[0].strip()
    middleName = ''
    if len(firstName.split()) == 2:
        middleName = firstName.split()[1]
        firstName = firstName.split()[0]
    if len(lastName.split()) == 2:
        if lastName.split()[1].lower() == 'jr' or lastName.split()[1].lower() == 'jr.' or lastName.split()[1].lower() == 'junior':
            jrSr = "Jr"
            lastName = lastName.split()[0]
    elif len(lastName.split()) == 2:
        if lastName.split()[1].lower() == 'sr' or lastName.split()[1].lower() == 'sr.' or lastName.split()[1].lower() == 'senior':
            jrSr = 'Sr'
            lastName = lastName.split()[0]
    elif len(middleName.split()) == 2:
        if 'jr' in middleName.split()[1].lower() or 'junior' in middleName.split()[1].lower():
            middleName = middleName.split()[0]
            jrSr = 'Jr'
    elif len(middleName.split()) == 2:
        if 'sr' in middleName.split()[1].lower() or 'senior' in middleName.split()[1].lower():
            middleName = middleName.split()[0]
            jrSr = 'Sr'
    else:
        jrSr = ''
    firstName = string.capwords(firstName)
    middleName = string.capwords(middleName)
    lastName = string.capwords(lastName)

    # This is our marker to show that there is no panel result - if that's true, we'll have to add a blank
    # amino acid range for every marker we find.
    noPanel = False

    pdfLink = "s3://syapse-prod-nlp-sqa/" + str(reportId).upper() + "_" + accession.upper() + "_txt.txt"

    # We can go back and undo this step if we need to - I'm representing the entire
    # path report as one long string here, so I can divide it by sections. I'm not
    # using free spaces to represent new sections, because this isn't reliable. It
    # sometimes works, sometimes not.
    pathReport = pathReport.replace('|', ' ')

    # Also there are a few spelling mistakes that I don't want to miss
    pathReport = pathReport.replace('eoxn', 'exon').replace('genetranscript', 'gene transcript').replace('interpretations', 'interpretation').replace('inerpretations', 'interpretation')
    pathReportOrig = pathReport

    sections = [
        # Paperwork
        '***electronically signed out***',
        'icd code(s):',
        'billing fee code(s):',
        'clia signout facility:',
        'physician(s):',
        'client:',  # This is the lab that wanted the report, I think
        'date ordered:',
        'date reported:',

        # Patient/Test Info
        'patient name:',
        'accession #',
        'received:',
        'clinical history',
        'diagnostic sensitivity',
        'technical sensitivitiy',
        'gene exon / amino acid (aa) coverage',
        'pathological diagnosis:',
        'microdissection',
        'disclaimers',
        'test performed:',
        'referring physician(s):',
        'date ordered',
        'reason for testing:',
        'report reviewed and signed:',
        'dna analysis for:',
        'indication for testing:',
        'methods:',
        'site of biopsy:',
        'addendum diagnosis',
        'addendum comment',
        'procedures/addenda',
        'comment:',
        'comment*:',
        'vous:',

        # Cytogenics
        'band resolution:',
        'cells analyzed/counted:',
        'images/karyograms:',

        # Information about the specimen
        'operation/specimen:',
        'gross description',
        'status',
        'sample type:',
        'karyotype:',
        'date sample obtained:',
        'date sample received',
        'lab accession number:',
        'type of specimen:',

        # Results
        'positive for the following',
        'we were not able to',
        'note',
        'results-comments',
        'results',
        'report comments',
        'dna quality',
        'mean amplicon depth',
        '% uniformity of coverage',
        'laboratory notes',
        'braf-m',
        'diagnostic interpretation',
        'clinical panel',  # This one seems to be important
        'cytogenic impression',
        'impression',
        'summary of cytogenetic analysis:',
        'interpretation:',
        'genotype',
        'phenotype',
        'enzyme activity',
        'variant classification:',
        'variant type:',
        'pathogenic mutation(s):',
        'variant(s) of unknown significance:',
        'gross deletion(s)/duplication(s):',
        'gene:',
        'variant:',
        'zygosity:',
        'final cytopathological diagnosis',

        # Autopsy fields
        'post mortem hours:',
        'authorized by',
        'relationship to patient',
        'reason for autopsy',
        'medical examiner',
        'autopsy restrictions',
        'anatomic preliminary diagnosis'
    ]

    if 'icd code(s)' in pathReport:
        if 'billing fee' in pathReport:
            icdC = pathReport[pathReport.index("icd code(s):") + len('icd code(s):'):pathReport.index('billing fee')] \
                .replace('however', '.').replace('less than', '<').replace('more than', '>').strip().split()
        elif 'clia' in pathReport:
            icdC = pathReport[pathReport.index("icd code(s):") + len('icd code(s):'):pathReport.index('clia')] \
                .replace('however', '.').replace('less than', '<').replace('more than', '>').strip().split()
        else:
            icdC = pathReport[pathReport.index("icd code(s):") + len('icd code(s):'):pathReport.index('==')] \
                .replace('however', '.').replace('less than', '<').replace('more than', '>').strip().split()
        icdC = list(dict.fromkeys(icdC))
        for i in range(len(icdC)-1, -1, -1):
            if icdC[i].endswith(':'):
                icdC.remove(icdC[i])
        icdC = ', '.join(icdC)

    dobindex = pathReportFull.index('dob:')
    enddod = pathReportFull.index('(age')
    DOB = pathReportFull[dobindex + 4:enddod].strip()
    index = [idx for idx, s in enumerate(pathReportSplit) if 'patient name:' in s][0]
    indexTT = index - 1
    testType = pathReportSplit[indexTT]
    testTypeOrig = pathReportSplit[indexTT]
    # Pull out test type
    while testType == '' or 'amended' in testType.lower() or testType.lower().replace('-', '') == '':
        indexTT = indexTT - 1
        testType = pathReportSplit[indexTT].strip()
        if testType.endswith('.'):
            testType = testType[:-1]

    source = healthOrg

    # Let's just see here
    if 'gene location transcript' in pathReport and testType not in panelTests and testType not in genericTests:
        print(pathReportFull)
        print(testType)
        print("NEW TEST TYPE???")
        print(reportId)
        checkMe = False
        input()
    elif 'gene location transcript' in pathReport and testType in panelTests:
        #print('REGULAR TEST TYPE')
        #print(testType)
        pass
    elif 'gene location transcript' not in pathReport and 'gene exon / amino acid (aa) coverage' not in pathReport and 'gene target region (exon):' not in pathReport and testType in panelTests:
        if testType not in ['surgical pathology report', 'molecular pathology and genomic test', 'myeloproliferative neoplasm (mpn) panel', 'molecular studies report',
                            'jak2 mutational analysis', 'idh1 mutation detection assay', 'brca1/2 sequencing and common deletions / duplications']:
            checkMe = False
            #print(pathReportFull)
            if debug:
                print('location 1')
            geneList.append('')
            locationList.append('')
            transcriptList.append('')
            cdnaList.append('')
            proteinList.append('')
            aminoAcidRangeList.append('')
            alleleFrequencyList.append('')
            dpList.append('')
            exonList.append('')
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
            orderedDateList.append(ordered)
            testApproveList.append(received)
            icdCodeList.append(icdC)
            accessionList.append(accession)
            physicianList.append(physician)
            takenList.append(taken)
            statusList.append("Panel Test has no tables")
            specimenCodeList.append(specimenCode)
            specimenTypeList.append(specimenType)
            pdfLinkList.append(pdfLink)
            pathologistList.append(pathologist)
            fullTestList.append(pathReportFull)
            if 'insufficient amount' in pathReport.replace('|', ' ') or 'quantity not sufficient' in pathReport.replace('|', ' '):
                labelList.append("QNS")
            elif 'no tumor containing blocks available' in pathReport.replace('|', ' '):
                labelList.append("No tumor in sample")
            elif 'patient financial responsibility not accepted' in pathReport.replace('|', ' '):
                labelList.append('Patient Finance Problem')
            elif 'not diagnostic of tumor/carcinoma' in pathReport.replace('|', ' '):
                labelList.append('Specimen rejected: not diagnostic')
            elif 'not a patient specimen' in pathReport.replace('|', ' '):
                labelList.append('Testing, not patient specimen')
            elif 'testing not performed per policy.' in pathReport.replace('|', ' '):
                labelList.append('Not performed per policy - no additional information')
            elif 'the quality matrix failed' in pathReport.replace('|', ' '):
                labelList.append("Poor DNA Quality")
            elif 'cancelled at the request of the care provider.' in pathReport.replace('|', ' '):
                labelList.append('Cancelled by care provider')
            else:
                labelList.append('Testing Cancelled')
            continue
            #input()

    genderBit = pathReportFull.index('gender:')
    genderBit = pathReportFull[genderBit:]
    genderBit = genderBit[len('gender:'):genderBit.index('\n')]
    gender = genderBit.strip()

    allReportsLoc = [m.start() for m in re.finditer('\*\*\*electronically', pathReport)]
    allReportsLoc.insert(0, 0)
    allReportsLoc.insert(len(allReportsLoc), len(pathReport))
    foundAnything = False
    for portBit in range(0, len(allReportsLoc)-1):
        pathReport = pathReportOrig[allReportsLoc[portBit]:allReportsLoc[portBit + 1]].strip()
        pathReportSplit = pathReport.split('\n')
        if 'procedures/addenda' in pathReport:
            pathReport = pathReport[pathReport.index('procedures/addenda'):]
        # If there's a reason the test failed, we want it - we ALSO don't want to do anything else.
        if ('not performed' in pathReport.replace('|', ' ') or 'quality matrix failed' in pathReport.replace('|', ' ')
            or 'quantity not sufficient for pcr analysis' in pathReport.replace('|', ' ') or 'cancelled at the request of the care provider.'\
                in pathReport.replace('|', '')) and testType in panelTests:
            if debug:
                print('location 2')
            geneList.append('')
            locationList.append('')
            transcriptList.append('')
            cdnaList.append('')
            proteinList.append('')
            aminoAcidRangeList.append('')
            alleleFrequencyList.append('')
            dpList.append('')
            exonList.append('')
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
            orderedDateList.append(ordered)
            testApproveList.append(received)
            icdCodeList.append(icdC)
            accessionList.append(accession)
            physicianList.append(physician)
            takenList.append(taken)
            statusList.append("Not Done")
            specimenCodeList.append(specimenCode)
            specimenTypeList.append(specimenType)
            pdfLinkList.append(pdfLink)
            pathologistList.append(pathologist)
            fullTestList.append(pathReportFull)
            if 'insufficient amount' in pathReport.replace('|', ' ') or 'quantity not sufficient' in pathReport.replace('|', ' '):
                labelList.append("QNS")
            elif 'no tumor containing blocks available' in pathReport.replace('|', ' '):
                labelList.append("No tumor in sample")
            elif 'patient financial responsibility not accepted' in pathReport.replace('|', ' '):
                labelList.append('Patient Finance Problem')
            elif 'not diagnostic of tumor/carcinoma' in pathReport.replace('|', ' '):
                labelList.append('Specimen rejected: not diagnostic')
            elif 'not a patient specimen' in pathReport.replace('|', ' '):
                labelList.append('Testing, not patient specimen')
            elif 'testing not performed per policy.' in pathReport.replace('|', ' '):
                labelList.append('Not performed per policy - no additional information')
            elif 'the quality matrix failed' in pathReport.replace('|', ' '):
                labelList.append("Poor DNA Quality")
            elif 'cancelled at the request of the care provider.' in pathReport.replace('|', ' '):
                labelList.append('Cancelled by care provider')
            else:
                labelList.append('Testing Cancelled')
            continue

        # These will hold the names and positions in the report of all the section headers
        sectionList = []
        sectionPos = []

        # This stores the semi-structured panel section for deletion later
        semiStructuredSection = ''

        # ###### STRUCTURED TEXT PULL-OUTS ##########

        # In this section, we'll look at structured results.
        # 'gene location transcript cdna protein dp exon af label'
        # 'gene location transcript cdna protein dp exon vaf interpretation',
        # 'gene exon' - this one is for low coverage!
        # 'gene chr genomic coordinates'

        equivocalGenes = []
        equivocalExons = []
        equivocalLocations = []
        gene = ''
        exon = []


        # HERE YO
        equiText = ''
        equiPos = ''
        pathReport = pathReport.replace('(dna quality: suboptimal: results should be interpreted with caution.) ', '')
        if 'gene exon / (aa)' in pathReport:
            equiText = regex.findall('(?:gene exon / (aa)\b){s<=2}', pathReport)
        if 'cell content  gene' in pathReport:
            equiText = regex.findall('(?:cell content  gene\b){s<=2}', pathReport)
        if 'content. gene' in pathReport:
            equiText = regex.findall('(?:cell content. gene\b){s<=2}', pathReport)
        if 'content.  gene' in pathReport:
            equiText = regex.findall('(?:cell content.  gene\b){s<=2}', pathReport)
        if 'content  gene exon' in pathReport:
            equiText = regex.findall('(?:content  gene exon\b){s<=2}', pathReport)
        if 'content  gene:' in pathReport:
            equiText = regex.findall('(?:content  gene:\b){s<=2}', pathReport)
        if 'content  genes:' in pathReport:
            equiText = regex.findall('(?:content  genes:\b){s<=2}', pathReport)
        if 'content genes:' in pathReport:
            equiText = regex.findall('(?:content genes:\b){s<=2}', pathReport)
        if 'content. gene exon' in pathReport:
            equiText = regex.findall('(?:content. gene exon\b){s<=2}', pathReport)
        if 'content.  gene exon' in pathReport:
            equiText = regex.findall('(?:content.  gene exon\b){s<=2}', pathReport)
        if 'coverage: gene:' in pathReport:
            equiText = regex.findall('(?:coverage: gene:\b){s<=2}', pathReport)
        if 'feasible.  gene' in pathReport:
            equiText = regex.findall('(?:feasible.  gene\b){s<=2}', pathReport)
        if 'content.  gene:' in pathReport:
            equiText = regex.findall('(?:content.  gene:\b){s<=2}', pathReport)
        if 'excluded in these regions.  gene exon' in pathReport:
            equiText = regex.findall('(?:excluded in these regions.  gene exon\b){s<=2}', pathReport)
        if 'excluded in these regions.  gene exon / (aa)' in pathReport:
            equiText = regex.findall('(?:excluded in these regions.  gene exon / (aa)\b){s<=2}', pathReport)
        if 'low coverage areas: gene exon' in pathReport:
            equiText = regex.findall('(?:low coverage areas: gene exon\b){s<=2}', pathReport)
        if 'following regions showed coverage of less than 500x:' in pathReport:
            equiText = regex.findall('(?:following regions showed coverage of less than 500x:\b){s<=2}', pathReport)
        if 'separately.  gene exon' in pathReport:
            equiText = regex.findall('(?:separately.  gene exon\b){s<=2}', pathReport)
        if 'low coverage regions: gene exon' in pathReport:
            equiText = regex.findall('(?:low coverage regions: gene exon\b){s<=2}', pathReport)
        if 'gene low coverage regions' in pathReport:
            equiText = regex.findall('(?:gene low coverage regions\b){s<=2}', pathReport)
        if 'clinical and laboratory data.  gene' in pathReport:
            equiText = regex.findall('(?:clinical and laboratory data.  gene\b){s<=2}', pathReport)
        if 'cell content.  brain' in pathReport:
            equiText = regex.findall('(?:cell content.  brain\b){s<=2}', pathReport)
        if equiText:
            equiPos = [m.start() for m in regex.finditer('(?:content  gene exon\b){s<=2}', pathReport)]
            if 'cell content.  brain' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:cell content.  brain\b){s<=2}', pathReport)]
            if 'clinical and laboratory data.  gene' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:clinical and laboratory data.  gene\b){s<=2}', pathReport)]
            if 'low coverage regions: gene exon' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:low coverage regions: gene exon\b){s<=2}', pathReport)]
            if 'gene exon / (aa)' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:gene exon / (aa)\b){s<=2}', pathReport)]
            if 'separately.  gene exon' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:separately.  gene exon\b){s<=2}', pathReport)]
            if 'gene exon / (aa)' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:gene exon / (aa)\b){s<=2}', pathReport)]
            if 'cell content  gene ' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:cell content  gene\b){s<=2}', pathReport)]
            if 'content. gene' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:content. gene\b){s<=2}', pathReport)]
            if 'content.  gene' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:content.  gene\b){s<=2}', pathReport)]
            if 'content.  gene:' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:content.  gene:\b){s<=2}', pathReport)]
            if 'content. gene exon' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:content. gene exon\b){s<=2}', pathReport)]
            if 'coverage: gene:' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:coverage: gene:\b){s<=2}', pathReport)]
            if 'content.  gene exon' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:content.  gene exon\b){s<=2}', pathReport)]
            if 'content.  gene' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:content.  gene\b){s<=2}', pathReport)]
            if 'feasible.  gene' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:feasible.  gene\b){s<=2}', pathReport)]
            if 'cell content  gene:' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:cell content  gene:\b){s<=2}', pathReport)]
            if 'cell content  genes:' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:cell content  genes:\b){s<=2}', pathReport)]
            if 'cell content genes:' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:cell content genes:\b){s<=2}', pathReport)]
            if 'excluded in these regions.  gene exon' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:excluded in these regions.  gene exon\b){s<=2}', pathReport)]
            if 'excluded in these regions.  gene exon / (aa)' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:excluded in these regions.  gene exon / (aa)\b){s<=2}', pathReport)]
            if 'low coverage areas: gene exon' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:low coverage areas: gene exon\b){s<=2}', pathReport)]
            if '500x: gene exon / (aa)' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:500x: gene exon / (aa)\b){s<=2}', pathReport)]
            if '500x:  gene exon / (aa)' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:500x:  gene exon / (aa)\b){s<=2}', pathReport)]
            if '500x:  gene exon' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:500x:  gene exon\b){s<=2}', pathReport)]
            if 'gene low coverage regions' in pathReport:
                equiPos = [m.start() for m in regex.finditer('(?:gene low coverage regions\b){s<=2}', pathReport)]

            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(equiPos[0], testType)
                panelTests.append(testType)

            equiPath = pathReport[equiPos[0]:]
            equiPath = equiPath.replace(';', ',')
            equiEnd = [m.start() for m in regex.finditer('(?:results-comments\b){s<=2}', equiPath)]
            if 'results-comments' in equiPath:
                earliest = equiPath.index('results-comments')
            else:
                earliest = len(equiPath)
            if 'gene location transcript' in equiPath:
                equiEnd = [equiPath.index('gene location transcript')]
                earliest = equiEnd[0]
            if 'this custom cancer' in equiPath:
                equiEnd = [equiPath.index('this custom cancer')]
                earliest = equiEnd[0]
            if 'sample for' in equiPath:
                if equiPath.index('sample for') < earliest:
                    equiEnd = [m.start() for m in regex.finditer('(?:sample for\b){s<=2}', equiPath)]
                    earliest = equiEnd[0]
            if 'note:' in equiPath:
                if equiPath.index('note:') < earliest:
                    equiEnd = [m.start() for m in regex.finditer('(?:note:\b){s<=2}', equiPath)]
                    earliest = equiEnd[0]
            if ' b. ' in equiPath:
                if equiPath.index(' b. ') < earliest:
                    equiEnd = [equiPath.index(' b. ')]
                    earliest = equiEnd[0]
            if ' c. ' in equiPath:
                if equiPath.index(' c. ') < earliest:
                    equiEnd = [equiPath.index(' c. ')]
                    earliest = equiEnd[0]
            if 'flt3-itd analysis' in equiPath:
                if equiPath.index('flt3-itd analysis') < earliest:
                    equiEnd = [equiPath.index('flt3-itd analysis')]
                    earliest = equiEnd[0]
            if 'alk and ros1 by fish' in equiPath:
                if equiPath.index('alk and ros1 by fish') < earliest:
                    equiEnd = [equiPath.index('alk and ros1 by fish')]
                    earliest = equiEnd[0]
            if 'comment:' in equiPath:
                if equiPath.index('comment:') < earliest:
                    equiEnd = [equiPath.index('comment:')]
                    earliest = equiEnd[0]
            if 'if clinically indicated' in equiPath:
                if equiPath.index('if clinically indicated') < earliest:
                    equiEnd = [equiPath.index('if clinically indicated')]
                    earliest = equiEnd[0]
            if 'findings were communicated' in equiPath:
                if equiPath.index('findings were communicated') < earliest:
                    equiEnd = [equiPath.index('findings were communicated')]
                    earliest = equiEnd[0]
            if '4).this' in equiPath:
                if equiPath.index('4).') < earliest:
                    equiEnd = [equiPath.index('4).')]
                    earliest = equiEnd[0]
            if 'a false negative' in equiPath:
                if equiPath.index('a false negative') < earliest:
                    equiEnd = [m.start() for m in regex.finditer('(?:a false negative\b){s<=2}', equiPath)]
                    earliest = equiEnd[0]
            if 'diagnostic interpretation' in equiPath:
                if equiPath.index('diagnostic interpretation') < earliest:
                    equiEnd = [equiPath.index('diagnostic interpretation')]
                    earliest = equiEnd[0]
            if 'section 1:' in equiPath:
                if equiPath.index('section 1:') < earliest:
                    equiEnd = [equiPath.index('section 1:')]
                    earliest = equiEnd[0]
            if '(including' in equiPath:
                if equiPath.index('(including') < earliest:
                    equiEnd = [equiPath.index('(including')]
                    earliest = equiEnd[0]
            if 'negative mutation' in equiPath:
                if equiPath.index('negative mutation') < earliest:
                    equiEnd = [equiPath.index('negative mutation')]
                    earliest = equiEnd[0]
            if 'negative - mutation' in equiPath:
                if equiPath.index('negative - mutation') < earliest:
                    equiEnd = [equiPath.index('negative - mutation')]
                    earliest = equiEnd[0]
            if 'this hereditary' in equiPath:
                if equiPath.index('this hereditary') < earliest:
                    equiEnd = [equiPath.index('this hereditary')]
                    earliest = equiEnd[0]
            if 'limitations:' in equiPath:
                if equiPath.index('limitations:') < earliest:
                    equiEnd = [m.start() for m in regex.finditer('(?:limitations:\b){s<=2}', equiPath)]
                    earliest = equiEnd[0]
            if 'hereditary breast' in equiPath:
                if equiPath.index('hereditary breast') < earliest:
                    equiEnd = [m.start() for m in regex.finditer('(?:hereditary breast\b){s<=2}', equiPath)]
                    earliest = equiEnd[0]
            if 'hereditary colorectal' in equiPath:
                if equiPath.index('hereditary colorectal') < earliest:
                    equiEnd = [m.start() for m in regex.finditer('(?:hereditary colorectal\b){s<=2}', equiPath)]
                    earliest = equiEnd[0]
            if 'inherited genetic' in equiPath:
                if equiPath.index('inherited genetic') < earliest:
                    equiEnd = [m.start() for m in regex.finditer('(?:inherited genetic\b){s<=2}', equiPath)]
                    earliest = equiEnd[0]
            if 'breast cancer' in equiPath:
                if equiPath.index('breast cancer') < earliest:
                    equiEnd = [m.start() for m in regex.finditer('(?:breast cancer\b){s<=2}', equiPath)]
                    earliest = equiEnd[0]


            if len(equiEnd) == 0:
                equiEnd = [equiPath.index('   ')]
            equiPath = equiPath[:equiEnd[0]]
            equiPath = equiPath.replace('+', ' ')
            equiPath = equiPath.replace('and', ' ')

            # If any string '(aa' is smashed up against another, add a space
            if re.search('\S\(aa', equiPath):
                re.sub('(\S)\(aa', r'\1 (aa', equiPath)

            equiList = equiPath.split()

            # Let's remove tokens we never want
            while '/' in equiList:
                equiList.remove('/')
            while '-' in equiList:
                equiList.remove('-')
            while ':' in equiList:
                equiList.remove(':')

            exonOrAa = ''
            hasDp = False
            hasCov = False
            fullBit = ' '.join(equiList)

            # Let's start out by getting to the front of the list
            while equiList[0] in['content', 'gene', 'exon', '(aa)', '500x:', 'cell', 'gene:', 'coverage:', 'few', 'regions',
                                 '(aa', 'of', 'genes:', 'content.', '(exon', 'exons', 'depth', 'coverage', 'genes', 'feasible.', 'aa',
                                 'amino', 'acid', 'separately.', 'acids', 'excluded', 'in', 'these', 'regions.', 'low', 'coverage', 'regions:', 'areas:',
                                 'clinical', 'laboratory', 'data.', 'transcript', 'metastasis', 'brain', 'lung', 'primary'] and len(equiList) > 1:
                if equiList[0] in ['exon', '(exon', 'exons']:
                    exonOrAa = 'exons'
                if equiList[0] in ['depth']:
                    hasDp = True
                equiList = equiList[1:]

            while len(equiList) > 1:
                if (equiList[0].startswith('hs') or equiList[0].startswith('(hs')) and '-' in equiList[0]:
                    equiList = equiList[1:]

                if (equiList[0].startswith('(a') and equiList[0].endswith(':')) or (equiList[0].startswith('a') and equiList[0].endswith('):')):
                    equiList = equiList[1:]

                # For jak2 exon 12 (coverage = 480)
                while (equiList[0].startswith('(coverage')) or equiList[0] == '=' or (equiList[0].replace(')', '').isnumeric() and ')' in equiList[0]):
                    equiList = equiList[1:]
                    if len(equiList) == 0:
                        break

                if len(equiList) == 0:
                    break

                if equiList[0] not in ['genes.', 'exon', '(part)', 'exons', '(part', 'of', 'gene)', ')', '(aa)', '(aa', 'depth', 'coverage', 'feasible.', 'aa', 'x',
                                       'amino', 'acid', 'separately.', 'acids', 'excluded', 'in', 'these', 'regions.', 'low', 'regions', 'for', 'gene', 'areas:', 'transcript', 'aa',
                                       '(coverage)', 'metastasis', 'brain', 'primary', 'lung']:
                    # Assuming gene name will be first
                    equivocalGenes.append(equiList[0].replace(',',''))
                    equiList = equiList[1:]

                if equiList[0] in ['genes.', '(part)', '(part', 'of', 'gene)', ')', '(aa)', '(aa', 'coverage', 'x', 'separately.', 'low', 'regions', 'for', 'gene', 'brain',
                                   'metastasis', 'primary', 'lung']:
                    if len(equiList) == 1:
                        equiList[0] = 'x'
                    else:
                        equiList = equiList[1:]

                # This clues us that exons are to follow
                if equiList[0] in ['exon', 'exons', '(exon']:
                    exonOrAa = 'exons'
                    equiList = equiList[1:]

                # This lets us know AAs are coming. NOT UNIVERSAL
                if equiList[0] in ['aa']:
                    exonOrAa = 'aa'
                    equiList = equiList[1:]

                if equiList[0] in ['(coverage)']:
                    hasCov = True
                    equiList = equiList[1:]

                goOn = True
                toAdd = ''

                ###
                # Now let's find the results
                ###
                while len(equiList) > 0 and goOn:
                    # don't want transcripts
                    if equiList[0].startswith('nm_'):
                        equiList[0] = 'x'
                    # For depth of read, sometimes we get an x on the end
                    if equiList[0].endswith('x') and hasDp:
                        equiList[0] = 'x'
                        if len(equiList) > 1:
                            equiList = equiList[1:]
                    # We sometimes get protein info
                    if equiList[0].startswith('p.') or equiList[0].startswith('(p.'):
                        equiList[0] = 'x'
                    # Sometimes it's in parentheses: we'll delete those
                    if equiList[0] in ['(depth', '(dp:']:
                        while ')' not in equiList[0]:
                            equiList = equiList[1:]
                        equiList[0] = 'x'
                    # Just numbers or 'full' or 'partial'
                    if equiList[0].replace(')','').isnumeric() or (equiList[0].replace('.','').isnumeric() and equiList[0].endswith('.')) \
                            or equiList[0] in ['full', 'partial', 'all', 'multiple', 'promoter', 'target', 'regions']:
                        if equiList[0].endswith('.'):
                            equiList[0] = equiList[0].replace('.', ',')
                        if len(equiList) == 1:
                            toAdd = toAdd + ',' + equiList[0].replace(')', '')
                            if len(equiList) > 1:
                                if (exonOrAa == 'exons' or exonOrAa == '') and '(' in equiList[1]:
                                    exonOrAa = 'aa'
                            equiList = equiList[1:]
                            if hasDp:
                                equiList = equiList[1:]
                        elif equiList[0] == 'partial':
                            #equivocalGenes[-1] = equivocalGenes[-1] + ' ' + 'partial'
                            toAdd = toAdd + ',' + equiList[0].replace(')', '')
                            equiList = equiList[1:]
                        elif equiList[0] == 'promoter':
                            toAdd = toAdd + ' ' + 'promoter'
                            equiList = equiList[1:]
                        elif equiList[0] == 'multiple':
                            if len(equiList) > 1:
                                if equiList[1] == 'regions':
                                    toAdd = toAdd + ',' + 'multiple regions'
                                    equiList = equiList[1:]
                                    equiList = equiList[1:]
                                else:
                                    toAdd = toAdd + ',' + 'multiple'
                                    equiList = equiList[1:]
                        elif equiList[1] not in ['targeted', 'exons']:
                            toAdd = toAdd + ',' + equiList[0].replace(')', '')
                            if len(equiList) > 1:
                                if (exonOrAa == 'exons' or exonOrAa == '') and '(' in equiList[1]:
                                    exonOrAa = 'aa'
                                elif ('exon (aa)' in fullBit) and '-' in equiList[1] and not equiList[0].endswith(','):
                                    exonOrAa = 'aa'
                            equiList = equiList[1:]
                            if hasDp:
                                equiList = equiList[1:]

                            if hasCov and '(' in equiList[0] and ')' in equiList[0]:
                                equiList = equiList[1:]
                                equiList = equiList[1:]
                        # all targeted exons
                        elif equiList[1] in ['targeted', 'exons']:
                            toAdd = toAdd + ',' + equiList[0] + ' ' + equiList[1] + ' ' + equiList[2]
                            equiList = equiList[1:]
                            equiList = equiList[1:]
                            equiList = equiList[1:]
                    # (partial)
                    elif equiList[0] == '(partial)':
                        toAdd = toAdd + ' ' + equiList[0]
                        equiList = equiList[1:]
                    # (all gene coding regions)
                    elif equiList[0] == '(all':
                        if equiList[1] == 'gene' and equiList[2] == 'coding' and equiList[3] == 'regions)':
                            toAdd = toAdd + ' ' + '(all gene coding regions)'
                            equiList = equiList[1:]
                            equiList = equiList[1:]
                            equiList = equiList[1:]
                            equiList = equiList[1:]

                    # if it's '2,3'
                    elif equiList[0].replace(',', '').replace(')','').isnumeric():
                        if not equiList[0].endswith(','):
                            for item in equiList[0].split(','):
                                toAdd = toAdd + ',' + item.replace(')','')
                            equiList = equiList[1:]
                        else:
                            equiList[0] = equiList[0][:-1]
                            for item in equiList[0].split(','):
                                toAdd = toAdd + ',' + item.replace(')','')
                            equiList = equiList[1:]
                    # if it's 2-3
                    elif equiList[0].replace('-', '').replace(',', '').replace('(','').replace(')','').isnumeric():
                        if exonOrAa == 'exons':
                            if ',' in equiList[0][:-1]:
                                if equiList[0].endswith(','):
                                    equiList[0] = equiList[0][:-1]
                                for bit in equiList[0].split(','):
                                    bit = bit.strip()
                                    if '-' in bit:
                                        lower = bit.split('-')[0].replace('(','')
                                        upper = bit.split('-')[1].replace(')','').replace(',','')
                                        for zx in range(int(lower), int(upper)+1):
                                            toAdd = toAdd + ',' + str(zx)
                                    else:
                                        toAdd = toAdd + ',' + bit
                                equiList = equiList[1:]
                                if len(equiList) > 0:
                                    if equiList[0] in ['(aa']:
                                        exonOrAa = 'aa'

                            else:
                                lower = equiList[0].split('-')[0].replace('(','')
                                upper = equiList[0].split('-')[1].replace(')','').replace(',','')
                                for zx in range(int(lower), int(upper)+1):
                                    toAdd = toAdd + ',' + str(zx)
                                equiList = equiList[1:]
                                if len(equiList) > 0:
                                    if equiList[0] in ['(aa']:
                                        exonOrAa = 'aa'
                        elif exonOrAa == 'aa' or exonOrAa == '':
                            toAdd = toAdd + ',' + equiList[0].replace(',', '').replace('(','').replace(')','')
                            if len(equiList) > 1:
                                if '(' not in equiList[1] and ')' not in equiList[1] and 'exon' in fullBit and ')' not in equiList[0] and ('-' not in equiList[0]):
                                    exonOrAa = 'exons'
                            equiList = equiList[1:]
                            if len(equivocalGenes) == len(equivocalExons) and len(equivocalGenes) > 0:
                                if equivocalExons[-1] != '':
                                    equivocalExons[-1] = equivocalExons[-1] + toAdd
                                    toAdd = ''

                    # For gene names stuck with a comma (egfr,alk)
                    elif ',' in equiList[0] and not equiList[0].endswith(',') and not equiList[0].split(',')[0].isnumeric() and not equiList[0].split(',')[1].isnumeric():
                        equivocalGenes.append(equiList[0].split(',')[0])
                        equivocalGenes.append(equiList[0].split(',')[1])
                        equiList = equiList[1:]

                    else:
                        goOn = False
                while toAdd.startswith(',') or toAdd.startswith(' '):
                    toAdd = toAdd[1:]
                if toAdd != '':
                    equivocalExons.append(toAdd)

            # There might be one final entry
            if len(equiList) == 1:
                if equiList[0] not in [')', '(aa)', 'x']:
                    equivocalGenes.append(equiList[0].replace(',',''))

        while len(equivocalExons) < len(equivocalGenes):
            equivocalExons.append('')

        if testType not in panelTests and testType != 'surgical pathology report' and testType != 'calr (calreticulin) mutations' and (regex.findall('(?:gene exon / amino acid){s<=2}', \
                                    pathReport) or regex.findall('(?:gene target region){s<=2}', pathReport) or regex.findall('(?:gene exon transcript){s<=2}', pathReport))\
                or regex.findall('(?:fusions category reads){s<=2}', pathReport):
            panelsDropped.append(pathReport)
            panelIdsDropped.append(reportId)

        # The panels typically come with a list of the genes/exons that are covered. I'm assuming that all HF panels
        # start with "gene exon / amino acid (aa) coverage" and end with "disclaimers:". Worth investigating!
        if testType in panelTests or (regex.findall('(?:gene exon / amino acid){s<=2}', pathReport) or regex.findall('(?:gene target region){s<=2}', pathReport) or 
                                      regex.findall('(?:fusions category){s<=2}', pathReport)) or regex.findall('(?:gene variant tier){s<=2}', pathReport) or \
                regex.findall('(?:gene variant prediction){s<=2}', pathReport) or regex.findall('(?:gene transcript exons direction){s<=2}', pathReport):
            testsWithPanelsList.append(reportId)
            geneTestedList = []
            exonTestedList = []
            aminoAcidTestedList = []
            aminoAcidTestedChunk = []
            geneTestedChunk = []
            exonTestedChunk = []
            coverageText = regex.findall('(?:gene exon / amino acid){s<=2}', pathReport)
            coveragePos = [m.start() for m in regex.finditer('(?:gene exon / amino acid){s<=2}', pathReport)]
            for pos in coveragePos:
                # Let's see if we can't get a more specific name
                if testType in genericTests:
                    testType = findSpecificTest(pos, testType)
                    panelTests.append(testType)
                # We want the next token which is 1) farther than the start token, and 2) closest to it
                nearestPos = len(pathReport)
                pathSection = pathReport[pos:]
                for v in ['tp53 is not', 'disclaimers:', 'fusion assay:', '2. immunohistochemistry', 'this test', 'this result', 'idh2 testing was',
                          'flt3 itd detection', 'calreticulin mutations', 'the isocitrate', 'somatic', 'ret is an',
                          'hematolymphoid', 'detection', 'was performed', 'genes targeted', '/*note', '*note:']:
                    if v in pathSection:
                        if pathSection.index(v) < nearestPos:
                            nearestPos = pathSection.index(v)
                if coverageText:
                    coverageSplit = pathSection[len('gene exon / amino acid (aa) coverage'):nearestPos].replace('*', '').strip().split()
                    # If we don't handle space removal before, here's the place to do it.
                    newList = []
                    #findMe
                    for i in range(0, len(coverageSplit)):
                        # sometimes you get "nm_2034alk" - this split the alk from that
                        if 'nm_' not in coverageSplit[i]:
                            newList.append(coverageSplit[i].strip())
                        elif coverageSplit[i].replace('nm_', '').isnumeric():
                            newList.append(coverageSplit[i].strip())
                        else:
                            m = re.search(r"[^0-9\.]", coverageSplit[i][3:])
                            newList.append(coverageSplit[i][:m.start()+3].strip())
                            newList.append(coverageSplit[i][m.start()+3:].strip())
                    coverageSplit = newList
                    newList = []
                    geneTestedChunk = []
                    exonTestedChunk = []
                    aminoAcidTestedChunk = []
                    if len(coverageSplit) == 0:
                        break
                    while coverageSplit[0] in ['annotation', 'transcript']:
                        coverageSplit = coverageSplit[1:]
                    # Now we've split it into chunks, let's take it in the following way: First, a gene name, then, the exons,
                    # finally, the exact amino acids. We're being thorough, so we'll get the exons AND the amino acids.
                    while coverageSplit:
                        while '' in coverageSplit:
                            coverageSplit.remove('')
                        if 'nm_' in ' '.join(coverageSplit):
                            for item in coverageSplit:
                                if 'nm_' in item:
                                    coverageSplit.remove(item)
                        # This is a sign that we're done with this section.
                        if len(coverageSplit) > 1:
                            if coverageSplit[1] == 'immunohistochemistry':
                                coverageSplit = []
                                break
                        # This is all for 'including p.600E variant'
                        if coverageSplit[0] in ['including', 'variant', '(see', 'comment)', 'annotation', 'transcript']:
                            coverageSplit = coverageSplit[1:]
                        if coverageSplit[0].startswith('p.'):
                            exonTestedChunk.append(coverageSplit)
                            coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                        # Sometimes we'll get something like '- only insertions less than 25bp in length are detected'
                        if coverageSplit[0] == '-':
                            while coverageSplit[1] != 'exon':
                                coverageSplit = coverageSplit[1:]
                        # Sometimes there will be a second 'gene exon / amino acid (aa) coverage'
                        if coverageSplit[0] == 'gene' and coverageSplit[1] == 'exon':
                            coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                        # And SOMETIMES there will be multiple gene/exon breaks.
                        if coverageSplit[0].isnumeric():
                            geneTestedChunk.append(geneTestedList[-1][0])
                        # Sometimes we get gene exons (amino acids) exons (amino acids)
                        if coverageSplit[0] in ['exon', 'exons']:
                            geneTestedChunk.append(geneTestedList[-1][0])
                            coverageSplit = coverageSplit[1:]
                        # Sometimes it reads 'investigational panel'
                        if coverageSplit[0] == 'investigational':
                            coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                            if coverageSplit[0] == 'gene':
                                coverageSplit = coverageSplit[1:]
                                coverageSplit = coverageSplit[1:]
                                coverageSplit = coverageSplit[1:]
                                coverageSplit = coverageSplit[1:]
                                coverageSplit = coverageSplit[1:]
                                coverageSplit = coverageSplit[1:]
                                coverageSplit = coverageSplit[1:]
                        if not coverageSplit[0].replace(',', '').replace('-','').isnumeric():
                            geneTestedChunk.append(coverageSplit[0])
                            coverageSplit = coverageSplit[1:]
                            # Some genes are two words. Also tert promoter tends to have a comma after it?
                            if coverageSplit[0].replace(',', '') in ['promoter']:
                                geneTestedChunk[-1] = geneTestedChunk[-1] + ' ' + coverageSplit[0].replace(',', '')
                                coverageSplit = coverageSplit[1:]
                            if coverageSplit[0] not in ['full', 'exons', 'exon']:
                                print(coverageSplit)
                                input()
                            # Now coverageSplit[0] is 'exons'
                            if coverageSplit[0] in ['exons', 'exon']:
                                coverageSplit = coverageSplit[1:]
                            elif coverageSplit[0] in ['full']:
                                if len(coverageSplit) > 1:
                                    if coverageSplit[1] in ['coding']:
                                        exonTestedChunk.append('full coding region')
                                        coverageSplit = coverageSplit[1:]
                                        coverageSplit = coverageSplit[1:]
                                        coverageSplit = coverageSplit[1:]
                                    else:
                                        exonTestedChunk.append('full')
                                        coverageSplit = coverageSplit[1:]
                                else:
                                    exonTestedChunk.append('full')
                                    coverageSplit = coverageSplit[1:]

                        if len(coverageSplit) > 1 and '(' in ' '.join(coverageSplit).replace('(partial', ''):
                            while '(' not in coverageSplit[0] or coverageSplit[0] == '(partial':
                                if coverageSplit[0] in ['(partial', 'coverage)']:
                                    exonTestedChunk[-1] = str(exonTestedChunk[-1]) + ' ' + coverageSplit[0]
                                    coverageSplit = coverageSplit[1:]
                                if len(coverageSplit) > 1:
                                    if coverageSplit[1] in ['exons', 'exon']:
                                        print('unexpected exons')
                                        input()
                                        break
                                # Sometimes it's 'and'
                                if 'and' in coverageSplit[0]:
                                    coverageSplit = coverageSplit[1:]
                                # I'm dealing with ranges here. I'm NOT dealing with ranges for amino acids.
                                exonBit = coverageSplit[0].replace(',', '')
                                if '-' in exonBit:
                                    if exonBit.endswith('-'):
                                        coverageSplit = coverageSplit[1:]
                                        exonBit = exonBit + coverageSplit[0]
                                    for a in range(int(exonBit.split('-')[0]), int(exonBit.split('-')[1])+1):
                                        exonTestedChunk.append(a)
                                elif ',' in exonBit:
                                    while ',' in exonBit:
                                        exonTestedChunk.append(exonBit.replace(',',''))
                                        coverageSplit = coverageSplit[1:]
                                        exonBit = coverageSplit[0]
                                    exonTestedChunk.append(exonBit)
                                else:
                                    exonTestedChunk.append(int(coverageSplit[0].replace(',', '')))
                                coverageSplit = coverageSplit[1:]
                                if not coverageSplit:
                                    break
                        # We might not have AAs at all
                        elif len(coverageSplit) > 1 and '(' not in ' '.join(coverageSplit).replace('(partial', ''):
                            while coverageSplit[0].replace(',','').replace('-','').isnumeric() or coverageSplit[0] in ['(partial', 'coverage)']:
                                if '-' in coverageSplit[0]:
                                    for a in range(int(coverageSplit[0].split('-')[0]), int(coverageSplit[0].split('-')[1].replace(',','')) + 1):
                                        exonTestedChunk.append(a)
                                    coverageSplit = coverageSplit[1:]
                                elif coverageSplit[0] in ['(partial', 'coverage)']:
                                    exonTestedChunk[-1] = str(exonTestedChunk[-1]) + ' ' + coverageSplit[0]
                                    coverageSplit = coverageSplit[1:]
                                else:
                                    exonTestedChunk.append(coverageSplit[0].replace(',',''))
                                    coverageSplit = coverageSplit[1:]
                                if len(coverageSplit) == 0:
                                    break

                        # This is for if we end with an exon without an amino acid
                        elif len(coverageSplit) == 1 and '(' not in coverageSplit[0]:
                            exonBit = coverageSplit[0].replace(',', '')
                            newExonBit = ''
                            if '-' in exonBit:
                                for num in range(int(exonBit.split('-')[0]),int(exonBit.split('-')[1])+1):
                                    exonTestedChunk.append(num)
                            else:
                                exonTestedChunk.append(int(exonBit))
                            coverageSplit = coverageSplit[1:]
                        else:
                            if not coverageSplit:
                                continue
                            if coverageSplit[0].isnumeric():
                                exonTestedChunk.append(int(coverageSplit[0]))
                            coverageSplit = coverageSplit[1:]
                            pass

                        # Now in the parenthases, it's usually '(aa
                        if not coverageSplit:
                            continue
                        if 'aa' in coverageSplit[0]:
                            if coverageSplit[0] == '(aa':
                                coverageSplit = coverageSplit[1:]
                            else:
                                coverageSplit[0] = coverageSplit[0][3:]
                            # Now it's the amino acids
                            while ')' not in coverageSplit[0]:
                                # This is accounting for if there are no spaces between the AA ranges
                                if coverageSplit[0].endswith(','):
                                    aminoAcid = coverageSplit[0][:-1]
                                else:
                                    aminoAcid = coverageSplit[0]
                                aminoAcid = aminoAcid.split(',')
                                for aa in aminoAcid:
                                    aminoAcidTestedChunk.append(aa)
                                coverageSplit = coverageSplit[1:]
                            # Now it's the last amino acid
                            aminoAcid = coverageSplit[0].replace(')', '')
                            aminoAcid = aminoAcid.split(',')
                            for aa in aminoAcid:
                                aminoAcidTestedChunk.append(aa)
                            coverageSplit = coverageSplit[1:]
                        # If it isn't '(aa' - sometimes it's (variant)
                        elif ')' in coverageSplit[0]:
                            aminoAcidTestedChunk.append(coverageSplit[0].replace('(', '').replace(')', ''))
                            coverageSplit = coverageSplit[1:]
                        # Now it's either the next thing, the end, OR it's 'including'
                        if coverageSplit:
                            if coverageSplit[0] == 'including':
                                coverageSplit = coverageSplit[1:]
                                # now it's the variant name. IF THERE'S MORE THAN ONE CHANGE IT HERE!
                                aminoAcidTestedChunk.append(coverageSplit[0])
                                coverageSplit = coverageSplit[2:]
                        if 'this' in geneTestedChunk:
                            print(coverageSplit)
                            print(pathReport)
                            print(reportId)
                        if geneTestedChunk == 'note:':
                            geneTestedChunk = []
                            exonTestedChunk = []
                            aminoAcidTestedChunk = []
                            continue
                        if debug:
                            print('list append 1')
                        foundAnything = True
                        geneTestedList.append(geneTestedChunk)
                        geneTestedChunk = []
                        exonTestedList.append(exonTestedChunk)
                        exonTestedChunk = []
                        aminoAcidTestedList.append(aminoAcidTestedChunk)
                        aminoAcidTestedChunk = []
                    if geneTestedChunk:
                        foundAnything = True
                        if debug:
                            print('list append 1a')
                        geneTestedList.append(geneTestedChunk)
                        geneTestedChunk = []
                        exonTestedList.append(exonTestedChunk)
                        exonTestedChunk = []
                        aminoAcidTestedList.append(aminoAcidTestedChunk)
                        aminoAcidTestedChunk = []



            if not coverageText and regex.findall('(?:gene target region){s<=2}', pathReport):
                coveragePos = [m.start() for m in regex.finditer('(?:gene target region){s<=2}', pathReport)]
                for pos in coveragePos:
                    # This is here so we don't consider situations with "gene target region gene target region" which I've seen
                    if 'gene target region' in pathReport[pos+len('gene target region'):pos+len('gene target region')+30]:
                        continue
                    nearestPos = len(pathReport[pos:])
                    for h in ['tp53 is not', 'note:', 'disclaimers:', 'fusion assay:', '2. immunohistochemistry', 'this test', 'this result', 'idh2 testing was',
                                  'flt3 itd detection', 'calreticulin mutations', 'the isocitrate']:
                        place = [m.start() for m in regex.finditer('(?:' + h + '){s<=1}', pathReport[pos:])]
                        if place and pos:
                            if place[0] > 0 and place[0] < nearestPos:
                                coverageEndPos = place
                                nearestPos = place[0]
                                coverageSplit = pathReport[pos + len('gene target region(exon)'):pos + nearestPos]
                                if '(aa' in coverageSplit and '(aa ' not in coverageSplit:
                                    coverageSplit = coverageSplit.replace('(aa', '(aa ')
                                coverageSplit = coverageSplit.replace(' - ', '-')
                                coverageSplit = coverageSplit.split()
                        else:
                            pass
                    # If we don't handle space removal before, here's the place to do it.
                    for i in range(0, len(coverageSplit)):
                        coverageSplit[i] = coverageSplit[i].strip()
                    geneTestedChunk = []
                    exonTestedChunk = []
                    aminoAcidTestedChunk = []
                    while coverageSplit:
                        # Signs that we're done
                        if len(coverageSplit) > 1:
                            if coverageSplit[1] == 'immunohistochemistry':
                                coverageSplit = []
                                break
                        if coverageSplit[0] in ['(all']:
                            while ')' not in coverageSplit[0]:
                                coverageSplit = coverageSplit[1:]
                            coverageSplit = coverageSplit[1:]
                            if coverageSplit == []:
                                continue
                        if coverageSplit[0] == 'this' and coverageSplit[1] == 'test':
                            coverageSplit = []
                            break
                        if coverageSplit[0] in ['hematolymphoid', 'somatic', 'assay', 'kinase', 'proto-oncogene']:
                            coverageSplit = []
                            break
                        # Sometimes there's a space in the start - this pushes us past the beginning
                        if '):' in coverageSplit[0]:
                            coverageSplit = coverageSplit[1:]
                        geneTestedChunk.append(coverageSplit[0])
                        if 'exon' in coverageSplit[0]:
                            print("EXON")
                            print(coverageSplit)
                            print(pathReport)
                            print(geneTestedChunk)
                        coverageSplit = coverageSplit[1:]
                        if not coverageSplit:
                            break
                        # Sometimes there's some clarification that we don't need.
                        if ')' in coverageSplit[0] and 'partial' not in coverageSplit[0]:
                            coverageSplit = coverageSplit[1:]
                        # Now it can be 'exon' or 'exons'
                        if coverageSplit:
                            if coverageSplit[0] in ['exon', 'exons']:
                                coverageSplit = coverageSplit[1:]
                        if len(coverageSplit) > 1:
                            isAAList = False
                            while coverageSplit[0].replace(',', '').replace('-', '').replace('+', '').replace(')','').isnumeric() or coverageSplit[0] == '+' or\
                                    coverageSplit[0] in ['full', '(partial)', 'and'] or 'partial' in coverageSplit[0] \
                                    or 'exon' in coverageSplit[0] or coverageSplit[0] == '(aa':
                                # Sometimes it's 'full (all gene coding regions)'
                                if coverageSplit[0] == 'full' and coverageSplit[1] == '(all':
                                    exonTestedChunk.append(coverageSplit[0].replace(',', '').replace('+', ''))
                                    while ')' not in coverageSplit[0]:
                                        coverageSplit = coverageSplit[1:]
                                    coverageSplit = coverageSplit[1:]
                                elif coverageSplit[0] == 'full' and coverageSplit[1] == 'coding':
                                    exonTestedChunk.append(coverageSplit[0] + ' ' + coverageSplit[1] + ' ' + coverageSplit[2])
                                    coverageSplit = coverageSplit[1:]
                                    coverageSplit = coverageSplit[1:]
                                    coverageSplit = coverageSplit[1:]
                                elif coverageSplit[0].replace(',', '').replace('-', '').replace('+', '').replace(')','').isnumeric() or coverageSplit[0] in ['full', 'partial']\
                                        or coverageSplit[0] == 'exon':
                                    for bit in coverageSplit[0].split('+'):
                                        # Here we're pulling apart "2,3,4,5"
                                        if len(bit.split(',')) > 1 and not isAAList:
                                            for b in bit.split(','):
                                                if b:
                                                    exonTestedChunk.append(b)
                                        elif '-' in bit:
                                            if isAAList:
                                                aaBit = bit.replace(',', '')
                                                if ')' in aaBit:
                                                    isAAList = False
                                                    aaBit = aaBit.replace(')', '')
                                                aminoAcidTestedChunk.append(aaBit)
                                            else:
                                                exonBit = bit.replace(',', '')
                                                for o in range(int(exonBit.split('-')[0]), int(exonBit.split('-')[1]) + 1):
                                                    exonTestedChunk.append(o)
                                        elif '+' in bit:
                                            exonBit = bit.replace(',', '')
                                            for o in exonBit.split('+'):
                                                exonTestedChunk.append(int(o))
                                        else:
                                            if coverageSplit[0] == 'full':
                                                if coverageSplit[1] != '(all':
                                                    exonTestedChunk.append(bit.replace(',', ''))
                                            else:
                                                exonTestedChunk.append(bit.replace(',', ''))
                                    coverageSplit = coverageSplit[1:]
                                elif coverageSplit[0] in ['(all']:
                                    while ')' not in coverageSplit[0]:
                                        coverageSplit = coverageSplit[1:]
                                    coverageSplit = coverageSplit[1:]
                                elif coverageSplit[0] in ['+', 'and']:
                                    coverageSplit = coverageSplit[1:]
                                elif coverageSplit[0] == '(partial)':
                                    exonTestedChunk[-1] = exonTestedChunk[-1] + coverageSplit[0]
                                    coverageSplit = coverageSplit[1:]
                                elif '(partial)' in coverageSplit[0]:
                                    exonTestedChunk.append(coverageSplit[0])
                                    coverageSplit = coverageSplit[1:]
                                # If it's like exon12
                                elif 'exon' in coverageSplit[0] and coverageSplit[0] != 'exon':
                                    exonTestedChunk.append(coverageSplit[0].replace('exon', ''))
                                    coverageSplit = coverageSplit[1:]
                                elif coverageSplit[0] == '(aa':
                                    isAAList = True
                                    coverageSplit = coverageSplit[1:]
                                # else:
                                #    exonTestedChunk.append(coverageSplit[0].replace(',', '').replace('+',''))
                                # coverageSplit = coverageSplit[1:]

                                if not coverageSplit:
                                    break
                        else:
                            if coverageSplit:
                                exonTestedChunk.append(coverageSplit[0])
                            coverageSplit = []
                        foundAnything = True
                        if debug:
                            print('list append 2')
                        geneTestedList.append(geneTestedChunk)
                        geneTestedChunk = []
                        if aminoAcidTestedChunk != []:
                            aminoAcidTestedList.append(aminoAcidTestedChunk)
                            exonTestedList.append([])
                            aminoAcidTestedChunk = []
                        else:
                            exonTestedChunk = list(dict.fromkeys(exonTestedChunk))
                            exonTestedList.append(exonTestedChunk)
                            aminoAcidTestedList.append([])
                            exonTestedChunk = []
            elif not coverageText and 'list of target genes' not in pathReport:
                noPanel = True

        # Now to get the results from this test!
        repeatTest = pathReport
        genes = []
        tiers = []
        cdnas = []
        locations = []
        dps = []
        afs = []
        transcripts = []
        while 'gene variant tier cdna change chr genomic coordinates coverage allele fraction transcript' in repeatTest:
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('gene variant tier cdna change chr genomic coordinates coverage allele fraction transcript'), testType)
                panelTests.append(testType)
            repeatTest = repeatTest[repeatTest.index('gene variant tier cdna change chr genomic coordinates coverage allele fraction transcript')
                                    + len('gene variant tier cdna change chr genomic coordinates coverage allele fraction transcript'):]
            thisTest = repeatTest[:repeatTest.index('interpretation')]
            if 'notes:' in thisTest:
                thisTest = thisTest[:thisTest.index('notes:')]
            panelSplit = thisTest.split()
            gene = ''
            while len(panelSplit) > 1:
                while not panelSplit[0].isnumeric():
                    gene = gene + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                gene = gene.strip()
                genes.append(gene)
                tier = 'tier ' + panelSplit[0]
                tiers.append(tier)
                panelSplit = panelSplit[1:]
                cdna = panelSplit[0]
                cdnas.append(cdna)
                panelSplit = panelSplit[1:]
                location = panelSplit[0] + ':' + panelSplit[1]
                locations.append(location)
                panelSplit = panelSplit[1:]
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                dps.append(dp)
                panelSplit = panelSplit[1:]
                af = panelSplit[0]
                afs.append(af)
                panelSplit = panelSplit[1:]
                transcript = panelSplit[0]
                transcripts.append(transcript)
                panelSplit = panelSplit[1:]

        for gp in range(0, len(genes)):
            foundAnything = True
            if debug:
                print('location 3')
            geneList.append(genes[gp])
            geneChunk.append(gene[gp])
            exonList.append('')
            exonChunk.append('')
            locationList.append(locations[gp])
            transcriptList.append(transcripts[gp])
            cdnaList.append(cdnas[gp])
            proteinList.append('')
            aminoAcidRangeList.append('')
            aminoacidChunk.append('')
            dpList.append(dps[gp])
            alleleFrequencyList.append(afs[gp])
            labelList.append(tiers[gp])
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
            orderedDateList.append(ordered)
            testApproveList.append(received)
            icdCodeList.append(icdC)
            accessionList.append(accession)
            physicianList.append(physician)
            takenList.append(taken)
            if not status:
                statusList.append("normal")
            else:
                statusList.append(status)
            specimenCodeList.append(specimenCode)
            specimenTypeList.append(specimenType)
            pdfLinkList.append(pdfLink)
            pathologistList.append(pathologist)
            fullTestList.append(pathReportFull)


        # Now to get the results from this test!
        repeatTest = pathReport
        while 'interpretation gene cdna protein dp exon af label' in repeatTest:
            geneChunk = []
            exonChunk = []
            aminoacidChunk = []
            label = ''
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('interpretation gene cdna protein dp exon af label'), testType)
                panelTests.append(testType)

            repeatTest = repeatTest[repeatTest.index('interpretation gene cdna protein dp exon af label')  + len('interpretation gene cdna protein dp exon af label'):]
            endStrings = ['mutation of']
            endIndex = 99999999
            for x in endStrings:
                if x in repeatTest:
                    if repeatTest.index(x) < endIndex:
                        endIndex = repeatTest.index(x)
            thisTest = repeatTest[:endIndex]
            panelSplit = thisTest.split()
            while len(panelSplit) > 0:
                if panelSplit[0] in ['notes:']:
                    break
                gene = panelSplit[0]
                panelSplit = panelSplit[1:]
                if not '[' in panelSplit[0]:
                    print(panelSplit)
                    print('ERROR HERE POS 1')
                    input()
                panelSplit = panelSplit[1:]
                cdna = panelSplit[0]
                panelSplit = panelSplit[1:]
                protein = panelSplit[0]
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                panelSplit = panelSplit[1:]
                exon = panelSplit[0]
                panelSplit = panelSplit[1:]
                af = panelSplit[0]
                panelSplit = panelSplit[1:]
                label = ''
                while panelSplit[0] in ['pathogenic', 'likely', 'non-pathogenic', 'nonpathogenic', 'variant', 'of', 'uncertain', 'significance']:
                    label = label + ' ' + panelSplit[0]
                    if len(panelSplit) == 1:
                        panelSplit = panelSplit[1:]
                        break
                    panelSplit = panelSplit[1:]
                label = label.strip()
                if debug:
                    print('location 4')
                foundAnything = True
                geneList.append(gene)
                geneChunk.append(gene)
                locationList.append('')
                transcriptList.append('')
                cdnaList.append(cdna)
                proteinList.append(protein)
                aminoAcidRangeList.append('')
                alleleFrequencyList.append(af)
                dpList.append(dp)
                exonList.append(exon)
                labelList.append(label)
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
                orderedDateList.append(ordered)
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
                fullTestList.append(pathReportFull)
                label = ''

        # Now to get the results from this test!
        repeatTest = pathReport
        while 'genes (5\'-3\') category reads unique molecules breakpoints' in repeatTest:
            label = ''
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('genes (5\'-3\') category reads unique molecules breakpoints'), testType)
                panelTests.append(testType)
            repeatTest = repeatTest[repeatTest.index('genes (5\'-3\') category reads unique molecules breakpoints')
                                    + len('genes (5\'-3\') category reads unique molecules breakpoints'):]
            endStrings = ['interpretation', 'annotation transcripts:', 'exon annotation']
            endPos = 99999
            for x in endStrings:
                if x in repeatTest:
                    if repeatTest.index(x) < endPos:
                        endPos = repeatTest.index(x)
            thisTest = repeatTest[:endPos]
            thisTest = thisTest.strip()
            panelSplit = thisTest.split()
            if '(' in panelSplit[0]:
                panelSplit = panelSplit[1:]
            while len(panelSplit) > 0:
                fusion = panelSplit[0]
                panelSplit = panelSplit[1:]
                if '(ex' not in panelSplit[0]:
                    print(thisTest)
                    print(panelSplit)
                    print("FUSION PANEL ERROR 1")
                    input()
                panelSplit = panelSplit[1:]
                exon = panelSplit[0].replace(')', '')
                panelSplit = panelSplit[1:]
                # This is -
                panelSplit = panelSplit[1:]
                fusion = fusion + ', ' + panelSplit[0]
                panelSplit = panelSplit[1:]
                panelSplit = panelSplit[1:]
                exon = exon + ', ' + panelSplit[0].replace(')', '')
                panelSplit = panelSplit[1:]
                category = ''
                while not panelSplit[0].isnumeric():
                    category = category + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                category = category.strip()
                dp = panelSplit[0]
                panelSplit = panelSplit[1:]
                dp = dp + ', ' + panelSplit[0]
                panelSplit = panelSplit[1:]
                uniqueMolecule = ''
                if '(' not in panelSplit[0] and ('(' in panelSplit[1] or '-' in panelSplit[1]):
                    uniqueMolecule = uniqueMolecule + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                while '(' in panelSplit[0] or ':' in panelSplit[0] or panelSplit[0] in ['(multiple', 'additional', 'breakpoints)']:
                    uniqueMolecule = uniqueMolecule + ' ' + panelSplit[0]
                    if len(panelSplit) == 1:
                        panelSplit = panelSplit[1:]
                        break
                    panelSplit = panelSplit[1:]
                uniqueMolecule = uniqueMolecule.strip()
                
                fusionreportIdList.append(reportId)
                fusionsourceList.append(source)
                fusionhealthOrgList.append(healthOrg)
                fusionMRNList.append(MRN)
                fusionfirstNameList.append(firstName)
                fusionmiddleNameList.append(middleName)
                fusionlastNameList.append(lastName)
                fusionjrSrList.append(jrSr)
                fusionDOBList.append(DOB)
                fusiongenderList.append(gender)
                fusiontestTypeList.append(testType)
                fusiontestReportedDateList.append(date)
                fusionorderedDateList.append(ordered)
                fusiontestApproveList.append(received)
                fusionList.append(fusion)
                foundAnything = True
                fusionexonList.append(exon)
                fusiondirectionList.append('3\'-5\'')
                fusiontranscriptList.append('')
                fusioncategoryList.append(category)
                fusionreadsList.append(dp)
                fusionuniqueMolList.append(uniqueMolecule)
                fusionStartSitesList.append('')
                fusionbreakpointsList.append('')
                fusionicdCodeList.append(icdC)
                fusionaccessionList.append(accession)
                fusionphysicianList.append(physician)
                fusiontakenList.append(taken)
                fusionstatusList.append(status)
                fusionfullTestList.append(pathReportFull)
                fusionspecimenCodeList.append(specimenCode)
                fusionspecimenTypeList.append(specimenType)
                fusionpdfLinkList.append(reportId)
                fusionpathologistList.append(pathologist)
                fusionorderedDateList.append(ordered)
                fusionlabelList.append('result')

        # Now to get the results from this test!
        repeatTest = pathReport
        while 'genes unique start sites reads %of reads breakpoint category' in repeatTest:
            label = ''
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('genes unique start sites reads %of reads breakpoint category'), testType)
                panelTests.append(testType)
            repeatTest = repeatTest[repeatTest.index('genes unique start sites reads %of reads breakpoint category')
                                    + len('genes unique start sites reads %of reads breakpoint category'):]

            endStrings = ['comment', '2).', 'the fusion has been']
            if not any(x in repeatTest for x in endStrings):
                print('no end for fusion')
                input()
            endPos = 999999
            for x in endStrings:
                if x in repeatTest:
                    if repeatTest.index(x) < endPos:
                        endPos = repeatTest.index(x)
            thisTest = repeatTest[:endPos]
            thisTest = thisTest.strip()
            panelSplit = thisTest.split()
            while len(panelSplit) > 0:
                if panelSplit[1] == 'f':
                    fusion = panelSplit[0] + '-'
                    panelSplit = panelSplit[1:]
                    # Next is f
                    panelSplit = panelSplit[1:]
                    fusion = fusion + panelSplit[0]
                else:
                    fusion = panelSplit[0]
                panelSplit = panelSplit[1:]
                dp = panelSplit[0] + ', '
                panelSplit = panelSplit[1:]
                dp = dp + panelSplit[0]
                panelSplit = panelSplit[1:]
                # This is % reads
                panelSplit = panelSplit[1:]
                uniqueMolecule = panelSplit[0]
                panelSplit = panelSplit[1:]
                if ':' in panelSplit[0] or ')' in panelSplit[0]:
                    print('ERROR FUSION PT 2')
                    print(panelSplit)
                    print(thisTest)
                    input()
                category = panelSplit[0]
                panelSplit = panelSplit[1:]
                fusionreportIdList.append(reportId)
                fusionsourceList.append(source)
                fusionhealthOrgList.append(healthOrg)
                fusionMRNList.append(MRN)
                fusionfirstNameList.append(firstName)
                fusionmiddleNameList.append(middleName)
                fusionlastNameList.append(lastName)
                fusionjrSrList.append(jrSr)
                fusionDOBList.append(DOB)
                fusiongenderList.append(gender)
                fusiontestTypeList.append(testType)
                fusiontestReportedDateList.append(date)
                fusionorderedDateList.append(ordered)
                fusiontestApproveList.append(received)
                fusionList.append(fusion)
                foundAnything = True
                fusionexonList.append('')
                fusiondirectionList.append('')
                fusiontranscriptList.append('')
                fusioncategoryList.append(category)
                fusionreadsList.append(dp)
                fusionuniqueMolList.append(uniqueMolecule)
                fusionStartSitesList.append('')
                fusionbreakpointsList.append('')
                fusionicdCodeList.append(icdC)
                fusionaccessionList.append(accession)
                fusionphysicianList.append(physician)
                fusiontakenList.append(taken)
                fusionstatusList.append(status)
                fusionfullTestList.append(pathReportFull)
                fusionspecimenCodeList.append(specimenCode)
                fusionspecimenTypeList.append(specimenType)
                fusionpdfLinkList.append(reportId)
                fusionpathologistList.append(pathologist)
                fusionorderedDateList.append(ordered)
                fusionlabelList.append('result')

        # Now to get the results from this test!
        repeatTest = pathReport
        while 'variant of unknown significance gene location transcript cdna protein dp exon af interpretation' in repeatTest:
            geneChunk = []
            exonChunk = []
            aminoacidChunk = []
            label = ''
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('variant of unknown significance gene location transcript cdna protein dp exon af interpretation'), testType)
                panelTests.append(testType)
            repeatTest = repeatTest[repeatTest.index('variant of unknown significance gene location transcript cdna protein dp exon af interpretation')
                                    + len('variant of unknown significance gene location transcript cdna protein dp exon af interpretation'):]
            endStrings = ['note:', 'comment:']
            if not any(x in repeatTest for x in endStrings):
                print(repeatTest)
                print('no end!')
                input()
            endPos = 99999
            for x in endStrings:
                if x in repeatTest:
                    if repeatTest.index(x) < endPos:
                        endPos = repeatTest.index(x)
            thisTest = repeatTest[:endPos]
            thisTest = thisTest.strip()
            thisTest = thisTest.replace('unknow ', 'unknown ')
            panelSplit = thisTest.split()
            while len(panelSplit) > 0:
                gene = panelSplit[0]
                panelSplit = panelSplit[1:]
                if ':' not in panelSplit[0]:
                    print("ERROR VUS POS 1")
                    print(panelSplit)
                    print(repeatTest)
                    input()
                location = panelSplit[0]
                panelSplit = panelSplit[1:]
                transcript = panelSplit[0]
                panelSplit = panelSplit[1:]
                cdna = panelSplit[0]
                panelSplit = panelSplit[1:]
                protein = panelSplit[0]
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                panelSplit = panelSplit[1:]
                exon = panelSplit[0]
                panelSplit = panelSplit[1:]
                af = panelSplit[0]
                panelSplit = panelSplit[1:]
                label = ''
                while panelSplit[0] in ['variant', 'of', 'unknown', 'significance', 'pathogenic', 'likely']:
                    label = label + ' ' + panelSplit[0]
                    if len(panelSplit) == 1:
                        panelSplit = panelSplit[1:]
                        break
                    panelSplit = panelSplit[1:]
                label = label.strip()
                if debug:
                    print('location 5')
                foundAnything = True
                geneList.append(gene)
                geneChunk.append(gene)
                locationList.append(location)
                transcriptList.append(transcript)
                cdnaList.append(cdna)
                proteinList.append(protein)
                aminoAcidRangeList.append('')
                alleleFrequencyList.append(af)
                dpList.append(dp)
                exonList.append(exon)
                labelList.append(label)
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
                orderedDateList.append(ordered)
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
                fullTestList.append(pathReportFull)
                label = ''

        while 'pathogenic variant gene location transcript cdna protein dp exon af interpretation' in repeatTest:
            geneChunk = []
            exonChunk = []
            aminoacidChunk = []
            label = ''
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('pathogenic variant gene location transcript cdna protein dp exon af interpretation'), testType)
                panelTests.append(testType)
            repeatTest = repeatTest[repeatTest.index('pathogenic variant gene location transcript cdna protein dp exon af interpretation')
                                    + len('pathogenic variant gene location transcript cdna protein dp exon af interpretation'):]
            endStrings = ['variants of', 'no coding', 'positive for', 'comment:', 'exon 19 deletions', 'variant of', 'the a146t']
            if not any(x in repeatTest for x in endStrings):
                print(repeatTest)
                input()
            else:
                endPos = 9999999
                for x in endStrings:
                    if x in repeatTest:
                        if repeatTest.index(x) < endPos:
                            endPos = repeatTest.index(x)
                thisTest = repeatTest[:endPos]
            thisTest = thisTest.strip()
            panelSplit = thisTest.split()
            while len(panelSplit) > 0:
                gene = panelSplit[0]
                panelSplit = panelSplit[1:]
                if ':' not in panelSplit[0]:
                    print("ERROR PATHO POS 1")
                    print(panelSplit)
                    print(thisTest)
                    input()
                location = panelSplit[0]
                panelSplit = panelSplit[1:]
                transcript = panelSplit[0]
                panelSplit = panelSplit[1:]
                cdna = panelSplit[0]
                panelSplit = panelSplit[1:]
                protein = panelSplit[0]
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                panelSplit = panelSplit[1:]
                exon = panelSplit[0]
                panelSplit = panelSplit[1:]
                af = panelSplit[0]
                panelSplit = panelSplit[1:]
                while panelSplit[0] in ['pathogenic', 'likely', 'positive']:
                    label = label + ' ' + panelSplit[0]
                    if len(panelSplit) == 1:
                        panelSplit = panelSplit[1:]
                        break
                    panelSplit = panelSplit[1:]
                label = label.strip()
                if debug:
                    print('location 6')
                foundAnything = True
                geneList.append(gene)
                geneChunk.append(gene)
                locationList.append(location)
                transcriptList.append(transcript)
                cdnaList.append(cdna)
                proteinList.append(protein)
                aminoAcidRangeList.append('')
                alleleFrequencyList.append(af)
                dpList.append(dp)
                exonList.append(exon)
                labelList.append(label)
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
                orderedDateList.append(ordered)
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
                fullTestList.append(pathReportFull)
                label = ''

        # More for the gene list here
        if 'detection of gene fusions / splicing variants:' in repeatTest:
            section = repeatTest[repeatTest.index('detection of gene fusions / splicing variants:') + len('detection of gene fusions / splicing variants:'):]
            section = section.strip()
            if 'detection of' not in section:
                print('NO DETECTION OF')
                print(section)
                section = section[:section.index('disclaimers:')]
            else:
                section = section[:section.index('detection of')]
            if 'comprehensive solid' in section:
                section = section[:section.index('comprehensive solid')]
            for bit in section.split(', '):
                if debug:
                    print('location 7')
                foundAnything = True
                geneList.append(bit.strip())
                locationList.append('')
                transcriptList.append('')
                cdnaList.append('')
                proteinList.append('')
                aminoAcidRangeList.append('')
                alleleFrequencyList.append('')
                dpList.append('')
                exonList.append('')
                labelList.append('Tested for fusion \ splicing variant')
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
                orderedDateList.append(ordered)
                testApproveList.append(received)
                icdCodeList.append(icdC)
                accessionList.append(accession)
                physicianList.append(physician)
                takenList.append(taken)
                statusList.append("Tested")
                specimenCodeList.append(specimenCode)
                specimenTypeList.append(specimenType)
                pdfLinkList.append(pdfLink)
                pathologistList.append(pathologist)
                fullTestList.append(pathReportFull)

        elif 'list of target genes detection of gene fusions:' in repeatTest:
            section = repeatTest[repeatTest.index('list of target genes detection of gene fusions:') + len('list of target genes detection of gene fusions:'):]
            section = section.strip()
            if 'detection of' not in section:
                print('NO DETECTION OF')
                print(section)
                section = section[:section.index('disclaimers:')]
            else:
                section = section[:section.index('detection of')]
            if 'comprehensive solid' in section:
                section = section[:section.index('comprehensive solid')]
            for bit in section.split(', '):
                if debug:
                    print('location 8')
                foundAnything = True
                geneList.append(bit.strip())
                locationList.append('')
                transcriptList.append('')
                cdnaList.append('')
                proteinList.append('')
                aminoAcidRangeList.append('')
                alleleFrequencyList.append('')
                dpList.append('')
                exonList.append('')
                labelList.append('Tested for fusion')
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
                orderedDateList.append(ordered)
                testApproveList.append(received)
                icdCodeList.append(icdC)
                accessionList.append(accession)
                physicianList.append(physician)
                takenList.append(taken)
                statusList.append("Tested")
                specimenCodeList.append(specimenCode)
                specimenTypeList.append(specimenType)
                pdfLinkList.append(pdfLink)
                pathologistList.append(pathologist)
                fullTestList.append(pathReportFull)
        if 'detection of snvs / indels/ cnvs:' in repeatTest:
            section = repeatTest[repeatTest.index('detection of snvs / indels/ cnvs:') + len('detection of snvs / indels/ cnvs:'):]
            section = section.strip()
            if 'detection of' not in section:
                section = section[:section.index('disclaimers:')]
            else:
                section = section[:section.index('detection of')]
            if 'comprehensive solid' in section:
                section = section[:section.index('comprehensive solid')]
            for bit in section.split(', '):
                if debug:
                    print('location 9')
                foundAnything = True
                geneList.append(bit.strip())
                locationList.append('')
                transcriptList.append('')
                cdnaList.append('')
                proteinList.append('')
                aminoAcidRangeList.append('')
                alleleFrequencyList.append('')
                dpList.append('')
                exonList.append('')
                labelList.append('Tested for snv/indel/cnv')
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
                orderedDateList.append(ordered)
                testApproveList.append(received)
                icdCodeList.append(icdC)
                accessionList.append(accession)
                physicianList.append(physician)
                takenList.append(taken)
                statusList.append("Tested")
                specimenCodeList.append(specimenCode)
                specimenTypeList.append(specimenType)
                pdfLinkList.append(pdfLink)
                pathologistList.append(pathologist)
                fullTestList.append(pathReportFull)

        elif 'detection of snvs / indels:' in repeatTest:
            section = repeatTest[repeatTest.index('detection of snvs / indels:') + len('detection of snvs / indels:'):]
            section = section.strip()
            if 'detection of' not in section:
                section = section[:section.index('disclaimers:')]
            else:
                section = section[:section.index('detection of')]
            if 'comprehensive solid' in section:
                section = section[:section.index('comprehensive solid')]
            for bit in section.split(', '):
                if debug:
                    print('location 10')
                foundAnything = True
                geneList.append(bit.strip())
                locationList.append('')
                transcriptList.append('')
                cdnaList.append('')
                proteinList.append('')
                aminoAcidRangeList.append('')
                alleleFrequencyList.append('')
                dpList.append('')
                exonList.append('')
                labelList.append('Tested for snv/indel')
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
                orderedDateList.append(ordered)
                testApproveList.append(received)
                icdCodeList.append(icdC)
                accessionList.append(accession)
                physicianList.append(physician)
                takenList.append(taken)
                statusList.append("Tested")
                specimenCodeList.append(specimenCode)
                specimenTypeList.append(specimenType)
                pdfLinkList.append(pdfLink)
                pathologistList.append(pathologist)
                fullTestList.append(pathReportFull)
        if 'detection of amplifications / cnvs' in repeatTest:
            section = repeatTest[repeatTest.index('detection of amplifications / cnvs:') + len('detection of amplifications / cnvs:'):]
            section = section.strip()
            if 'detection of' not in section:
                section = section[:section.index('disclaimers:')]
            else:
                section = section[:section.index('detection of')]
            if 'comprehensive solid' in section:
                section = section[:section.index('comprehensive solid')]
            if 'this assay simultaneously' in section:
                section = section[:section.index('this assay simultaneously')]
            for bit in section.split(', '):
                if debug:
                    print('location 11')
                foundAnything = True
                geneList.append(bit.strip())
                locationList.append('')
                transcriptList.append('')
                cdnaList.append('')
                proteinList.append('')
                aminoAcidRangeList.append('')
                alleleFrequencyList.append('')
                dpList.append('')
                exonList.append('')
                labelList.append('Tested for snv/amplification')
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
                orderedDateList.append(ordered)
                testApproveList.append(received)
                icdCodeList.append(icdC)
                accessionList.append(accession)
                physicianList.append(physician)
                takenList.append(taken)
                statusList.append("Tested")
                specimenCodeList.append(specimenCode)
                specimenTypeList.append(specimenType)
                pdfLinkList.append(pdfLink)
                pathologistList.append(pathologist)
                fullTestList.append(pathReportFull)
        if 'detection of dna mutations:' in repeatTest:
            section = repeatTest[repeatTest.index('detection of dna mutations:') + len('detection of dna mutations:'):]
            section = section.strip()
            if 'detection of' not in section:
                section = section[:section.index('disclaimers:')]
            else:
                section = section[:section.index('detection of')]
            if 'comprehensive solid' in section:
                section = section[:section.index('comprehensive solid')]
            for bit in section.split(', '):
                if debug:
                    print('location 12')
                foundAnything = True
                geneList.append(bit.strip())
                locationList.append('')
                transcriptList.append('')
                cdnaList.append('')
                proteinList.append('')
                aminoAcidRangeList.append('')
                alleleFrequencyList.append('')
                dpList.append('')
                exonList.append('')
                labelList.append('Tested for mutation')
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
                orderedDateList.append(ordered)
                testApproveList.append(received)
                icdCodeList.append(icdC)
                accessionList.append(accession)
                physicianList.append(physician)
                takenList.append(taken)
                statusList.append("Tested")
                specimenCodeList.append(specimenCode)
                specimenTypeList.append(specimenType)
                pdfLinkList.append(pdfLink)
                pathologistList.append(pathologist)
                fullTestList.append(pathReportFull)

        # Now to get the results from this test!
        repeatTest = pathReport
        while 'genes ss reads %reads breakpoint' in repeatTest:
            label = ''
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('genes ss reads %reads breakpoint'), testType)
                panelTests.append(testType)
            repeatTest = repeatTest[repeatTest.index('genes ss reads %reads breakpoint')
                                    + len('genes ss reads %reads breakpoint'):]
            thisTest = repeatTest[:repeatTest.index('unless')]
            thisTest = thisTest.strip()
            panelSplit = thisTest.split()
            hasCategory = False
            if panelSplit[0] == 'category':
                hasCategory = True
                panelSplit = panelSplit[1:]
            while len(panelSplit) > 0:
                if panelSplit[0] in ['comment:']:
                    break
                #print(panelSplit)
                fusion = panelSplit[0]
                panelSplit = panelSplit[1:]
                # This is just 'f'
                fusion = fusion + '-'
                panelSplit = panelSplit[1:]
                fusion = fusion + panelSplit[0]
                # So fusion is 'gene - gene' now we move on to dp
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                dp = dp + ', '
                panelSplit = panelSplit[1:]
                dp = dp + panelSplit[0]
                panelSplit = panelSplit[1:]
                # This is percent reads
                panelSplit = panelSplit[1:]
                uniqueMolecule = panelSplit[0]
                panelSplit = panelSplit[1:]
                category = ''
                if hasCategory:
                    category = panelSplit[0]
                    panelSplit = panelSplit[1:]

                fusionreportIdList.append(reportId)
                fusionsourceList.append(source)
                fusionhealthOrgList.append(healthOrg)
                fusionMRNList.append(MRN)
                fusionfirstNameList.append(firstName)
                fusionmiddleNameList.append(middleName)
                fusionlastNameList.append(lastName)
                fusionjrSrList.append(jrSr)
                fusionDOBList.append(DOB)
                fusiongenderList.append(gender)
                fusiontestTypeList.append(testType)
                fusiontestReportedDateList.append(date)
                fusionorderedDateList.append(ordered)
                fusiontestApproveList.append(received)
                fusionList.append(fusion)
                foundAnything = True
                fusionexonList.append('')
                fusiondirectionList.append('')
                fusiontranscriptList.append('')
                fusioncategoryList.append(category)
                fusionreadsList.append(dp)
                fusionuniqueMolList.append(uniqueMolecule)
                fusionStartSitesList.append('')
                fusionbreakpointsList.append('')
                fusionicdCodeList.append(icdC)
                fusionaccessionList.append(accession)
                fusionphysicianList.append(physician)
                fusiontakenList.append(taken)
                fusionstatusList.append(status)
                fusionfullTestList.append(pathReportFull)
                fusionspecimenCodeList.append(specimenCode)
                fusionspecimenTypeList.append(specimenType)
                fusionpdfLinkList.append(reportId)
                fusionpathologistList.append(pathologist)
                fusionorderedDateList.append(ordered)
                fusionlabelList.append('result')



        # Now to get the results from this test!
        repeatTest = pathReport
        while 'gene variant exon cdna change chr genomic coordinates coverage allele fraction transcript interpretation' in repeatTest:
            geneChunk = []
            exonChunk = []
            aminoacidChunk = []
            label = ''
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('gene variant exon cdna change chr genomic coordinates coverage allele fraction transcript interpretation'), testType)
                panelTests.append(testType)
            repeatTest = repeatTest[repeatTest.index('gene variant exon cdna change chr genomic coordinates coverage allele fraction transcript interpretation')
                                    + len('gene variant exon cdna change chr genomic coordinates coverage allele fraction transcript interpretation'):]
            thisTest = repeatTest[:repeatTest.index('interpretation')]
            panelSplit = thisTest.split()
            while len(panelSplit) > 1:
                print(panelSplit)
                gene = panelSplit[0]
                panelSplit = panelSplit[1:]
                protein = panelSplit[0]
                panelSplit = panelSplit[1:]
                exon = panelSplit[0]
                panelSplit = panelSplit[1:]
                cdna = panelSplit[0]
                panelSplit = panelSplit[1:]
                # This is the chromosome
                panelSplit = panelSplit[1:]
                # This is the genomic coordinates
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                panelSplit = panelSplit[1:]
                af = panelSplit[0]
                panelSplit = panelSplit[1:]
                transcript = panelSplit[0]
                panelSplit = panelSplit[1:]
                while panelSplit[0] in ['pathogenic', 'likely', 'non-pathogenic', 'nonpathogenic', 'variant', 'of', 'uncertain', 'significance']:
                    label = label + ' ' + panelSplit[0]
                    if len(panelSplit) == 1:
                        panelSplit = panelSplit[1:]
                        break
                    panelSplit = panelSplit[1:]
                label = label.strip()
                if debug:
                    print('location 13')
                foundAnything = True
                geneList.append(gene)
                geneChunk.append(gene)
                locationList.append('')
                transcriptList.append(transcript)
                cdnaList.append(cdna)
                proteinList.append(protein)
                aminoAcidRangeList.append('')
                alleleFrequencyList.append(af)
                dpList.append(dp)
                exonList.append(exon)
                labelList.append(label)
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
                orderedDateList.append(ordered)
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
                fullTestList.append(pathReportFull)
                label = ''

        # Now to get the results from this test!
        repeatTest = pathReport
        while 'gene variant prediction cdna change chr genomic coordinates coverage allele' in repeatTest:
            geneChunk = []
            exonChunk = []
            aminoacidChunk = []
            label = ''
            # Let's see if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('gene variant prediction cdna change chr genomic coordinates coverage allele fraction transcript'), testType)
                panelTests.append(testType)
            repeatTest = repeatTest[repeatTest.index('gene variant prediction cdna change chr genomic coordinates coverage allele fraction transcript')
                                    + len('gene variant prediction cdna change chr genomic coordinates coverage allele fraction transcript'):]
            if 'interpretation' in repeatTest:
                thisTest = repeatTest[:repeatTest.index('interpretation')]
            panelSplit = thisTest.split()
            while len(panelSplit) > 0:
                if panelSplit[0] in ['notes:']:
                    break
                gene = panelSplit[0]
                panelSplit = panelSplit[1:]
                if not panelSplit[0].startswith('p.'):
                    toAdd = panelSplit[0]
                    while not panelSplit[1].startswith('c.'):
                        toAdd = toAdd + ' ' + panelSplit[1]
                        panelSplit = panelSplit[1:]
                    panelSplit = panelSplit[1:]
                    protein = str(toAdd)
                else:
                    protein = panelSplit[0]
                    panelSplit = panelSplit[1:]
                while 'c.' not in panelSplit[0]:
                    label = label + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                while label.startswith(' '):
                    label = label[1:]
                cdna = panelSplit[0]
                panelSplit = panelSplit[1:]
                location = panelSplit[0] + ':' + panelSplit[1]
                panelSplit = panelSplit[1:]
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                panelSplit = panelSplit[1:]
                af = panelSplit[0]
                panelSplit = panelSplit[1:]
                transcript = panelSplit[0]
                panelSplit = panelSplit[1:]
                if debug:
                    print('location 14')
                foundAnything = True
                geneList.append(gene)
                geneChunk.append(gene)
                locationList.append(location)
                transcriptList.append(transcript)
                cdnaList.append(cdna)
                proteinList.append(protein)
                aminoAcidRangeList.append('')
                alleleFrequencyList.append(af)
                dpList.append(dp)
                exonList.append('')
                exonChunk.append('')
                labelList.append(label)
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
                orderedDateList.append(ordered)
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
                fullTestList.append(pathReportFull)
                label = ''

        repeatTest = pathReport
        fusions = []
        while 'fusions category reads' in repeatTest:
            fusions = []
            categories = []
            reads = []
            uniMols = []
            startSites = []
            breakpoints = []
            label = ''
            if 'fusions category reads unique molecules breakpoints' in pathReport:
                repeatTest = repeatTest[repeatTest.index('fusions category reads unique molecules breakpoints')
                                        + len('fusions category reads unique molecules breakpoints'):]
                repeatTest = repeatTest.strip()
                # See if we can't get a more specific name
                if testType in genericTests:
                    testType = findSpecificTest(repeatTest.index('fusions category reads unique molecules breakpoints'), testType)
                    panelTests.append(testType)
                if 'comment:' in repeatTest:
                    if repeatTest.index('comment:') < repeatTest.index('interpretation'):
                        thisTest = repeatTest[:repeatTest.index('comment:')]
                    else:
                        thisTest = repeatTest[:repeatTest.index('interpretation')]
                else:
                    thisTest = repeatTest[:repeatTest.index('interpretation')]
                panelSplit = thisTest.split()
                fusion = ''
                fusion = panelSplit[0]
                panelSplit = panelSplit[1:]
                oneTime = False
                while panelSplit[0].startswith('(') or panelSplit[0] == '-' or panelSplit[0].endswith(')') or oneTime:
                    if oneTime:
                        oneTime = False
                    if panelSplit[0] == '-':
                        oneTime = True
                    fusion = fusion + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                fusions.append(fusion)
                category = ''
                while not panelSplit[0].isnumeric():
                    category = category + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                category = category.strip()
                categories.append(category)
                reads.append(panelSplit[0])
                panelSplit = panelSplit[1:]
                uniMols.append(panelSplit[0])
                panelSplit = panelSplit[1:]
                breakpt = ''
                goOn = True
                while goOn:
                    if ':' in panelSplit[0] and panelSplit[0].endswith(')'):
                        breakpt = breakpt + panelSplit[0] + ', '
                        panelSplit = panelSplit[1:]
                        if len(panelSplit) < 1:
                            goOn = False
                    elif len(panelSplit) > 1:
                        if ':' in panelSplit[1] and panelSplit[1].replace(',', '').endswith(')'):
                            breakpt = breakpt + panelSplit[0] + ' ' + panelSplit[1].replace(',', '') + ', '
                            panelSplit = panelSplit[2:]
                            if len(panelSplit) < 1:
                                goOn = False
                        else:
                            goOn = False
                    else:
                        goOn = False
                while breakpt.endswith(',') or breakpt.endswith(' '):
                    breakpt = breakpt[:-1]
                breakpoints.append(breakpt)
                startSites.append('')
            elif 'fusions category reads start sites breakpoints' in pathReport:
                # See if we can't get a more specific name
                if testType in genericTests:
                    testType = findSpecificTest(repeatTest.index('fusions category reads start sites breakpoints'), testType)
                    panelTests.append(testType)
                repeatTest = repeatTest[repeatTest.index('fusions category reads start sites breakpoints')
                                        + len('fusions category reads start sites breakpoints'):]
                repeatTest = repeatTest.strip()
                thisTest = repeatTest[:repeatTest.index('interpretation')]
                panelSplit = thisTest.split()
                while len(panelSplit) > 0:
                    fusion = ''
                    fusion = panelSplit[0]
                    panelSplit = panelSplit[1:]
                    oneTime = False
                    while panelSplit[0].startswith('(') or panelSplit[0] == '-' or panelSplit[0].endswith(')') or oneTime:
                        if oneTime:
                            oneTime = False
                        if panelSplit[0] == '-':
                            oneTime = True
                        fusion = fusion + ' ' + panelSplit[0]
                        panelSplit = panelSplit[1:]
                    fusions.append(fusion)
                    category = ''
                    while not panelSplit[0].isnumeric():
                        category = category + ' ' + panelSplit[0]
                        panelSplit = panelSplit[1:]
                    category = category.strip()
                    categories.append(category)
                    reads.append(panelSplit[0])
                    panelSplit = panelSplit[1:]
                    startSite = ''
                    while panelSplit[0].isnumeric():
                        startSite = startSite + ', ' + panelSplit[0]
                        panelSplit = panelSplit[1:]
                    while startSite.startswith(',') or startSite.startswith(' '):
                        startSite = startSite[1:]
                    startSites.append(startSite)
                    breakpt = ''
                    goOn = True
                    while goOn:
                        if ':' in panelSplit[0] and panelSplit[0].endswith(')'):
                            breakpt = breakpt + panelSplit[0] + ', '
                            panelSplit = panelSplit[1:]
                            if len(panelSplit) < 1:
                                goOn = False
                        elif len(panelSplit) > 1:
                            if ':' in panelSplit[1] and panelSplit[1].replace(',', '').endswith(')'):
                                breakpt = breakpt + panelSplit[0] + ' ' + panelSplit[1].replace(',', '') + ', '
                                panelSplit = panelSplit[2:]
                                if len(panelSplit) < 1:
                                    goOn = False
                        else:
                            goOn = False
                    while breakpt.endswith(',') or breakpt.endswith(' '):
                        breakpt = breakpt[:-1]
                    breakpoints.append(breakpt)
                    uniMols.append('')
            else:
                print(pathReportFull)
                input()

        for fusPos in range(0, len(fusions)):
            fusionreportIdList.append(reportId)
            fusionsourceList.append(source)
            fusionhealthOrgList.append(healthOrg)
            fusionMRNList.append(MRN)
            fusionfirstNameList.append(firstName)
            fusionmiddleNameList.append(middleName)
            fusionlastNameList.append(lastName)
            fusionjrSrList.append(jrSr)
            fusionDOBList.append(DOB)
            fusiongenderList.append(gender)
            fusiontestTypeList.append(testType)
            fusiontestReportedDateList.append(date)
            fusionorderedDateList.append(ordered)
            fusiontestApproveList.append(received)
            fusionList.append(fusions[fusPos])
            foundAnything = True
            fusionexonList.append('')
            fusiondirectionList.append('')
            fusiontranscriptList.append('')
            fusioncategoryList.append(categories[fusPos])
            fusionreadsList.append(reads[fusPos])
            fusionuniqueMolList.append(uniMols[fusPos])
            fusionStartSitesList.append(startSites[fusPos])
            fusionbreakpointsList.append(breakpoints[fusPos])
            fusionicdCodeList.append(icdC)
            fusionaccessionList.append(accession)
            fusionphysicianList.append(physician)
            fusiontakenList.append(taken)
            fusionstatusList.append(status)
            fusionfullTestList.append(pathReportFull)
            fusionspecimenCodeList.append(specimenCode)
            fusionspecimenTypeList.append(specimenType)
            fusionpdfLinkList.append(reportId)
            fusionpathologistList.append(pathologist)
            fusionorderedDateList.append(ordered)
            fusionlabelList.append('result')

        if 'gene variant cdna change chr genomic coordinates coverage allele fraction transcript prediction' in pathReport:
            geneChunk = []
            exonChunk = []
            aminoacidChunk = []
            panelTest = pathReport.index('gene variant cdna change chr genomic coordinates coverage allele fraction transcript prediction')
            panelTest = pathReport[panelTest + len('gene variant cdna change chr genomic coordinates coverage allele fraction transcript prediction'):]
            panelTest = panelTest[:panelTest.index('interpretation:')].strip()
            panelSplit = panelTest.split()
            # See if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(pathReport.index('gene variant cdna change chr genomic coordinates coverage allele fraction transcript prediction'), testType)
                panelTests.append(testType)
            while len(panelSplit) > 0:
                gene = panelSplit[0]
                exon = ''
                protein = ''
                panelSplit = panelSplit[1:]
                if panelSplit[0] in ['splice', 'promoter', 'p.(?)']:
                    while 'c.' not in panelSplit[1]:
                        protein = protein + ' ' + panelSplit[0]
                        panelSplit = panelSplit[1:]
                    protein = protein + ' ' + panelSplit[0]
                    protein = protein.strip()
                else:
                    protein = panelSplit[0]
                panelSplit = panelSplit[1:]
                cdna = panelSplit[0]
                panelSplit = panelSplit[1:]
                location = panelSplit[0] + ':' + panelSplit[1]
                panelSplit = panelSplit[1:]
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                panelSplit = panelSplit[1:]
                af = panelSplit[0]
                panelSplit = panelSplit[1:]
                transcript = panelSplit[0]
                panelSplit = panelSplit[1:]
                if panelSplit[0] in ['likely']:
                    label = panelSplit[0] + ' ' + panelSplit[1]
                    panelSplit = panelSplit[1:]
                    panelSplit = panelSplit[1:]
                else:
                    label = panelSplit[0]
                    panelSplit = panelSplit[1:]
                    if debug:
                        print('location 15')
                foundAnything = True
                geneList.append(gene)
                geneChunk.append(gene)
                locationList.append(location)
                transcriptList.append(transcript)
                cdnaList.append(cdna)
                proteinList.append(protein)
                aminoAcidRangeList.append('')
                alleleFrequencyList.append(af)
                dpList.append(dp)
                exonList.append(exon)
                exonChunk.append(exon)
                labelList.append(label)
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
                orderedDateList.append(ordered)
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
                fullTestList.append(pathReportFull)

        repeatTest = pathReport
        while 'gene transcript exons direction type' in repeatTest:
            testTypeHere = testType
            # See if we can't get a more specific name
            if testType in genericTests:
                testType = findSpecificTest(repeatTest.index('gene transcript exons direction type'), testType)
                panelTests.append(testType)
            if 'procedures/addenda' in repeatTest:
                panelStart = repeatTest.index('gene transcript exons direction type')
                findSection = repeatTest
                goOn = True
                while 'procedures/addenda' in findSection and goOn:
                    if findSection.index('gene transcript exons direction type') < findSection.index('procedures/addenda'):
                        goOn = False
                    else:
                        findSection = findSection[findSection.index('procedures/addenda') + len('procedures/addenda'):]
                findSection = findSection[:findSection.index('date')].strip()
                testTypeHere = testType + ' - ' + findSection
            elif 'panel' in repeatTest:
                panelStart = repeatTest.index('gene transcript exons direction type')
                findSection = repeatTest
                goOn = True
                if 'pathologist' in findSection:
                    while 'pathologist' in findSection and goOn:
                        if findSection.index('gene transcript exons direction type') < findSection.index('pathologist'):
                            goOn = False
                        else:
                            findSection = findSection[findSection.index('pathologist') + len('pathologist'):]
                    if 'date' not in findSection:
                        findSection = findSection[:findSection.index('disclaimer')].strip()

                    else:
                        findSection = findSection[:findSection.index('date')].strip()
                    if len(findSection) < 100:
                        testTypeHere = testType + ' - ' + findSection
                else:
                    letterPos = [m.start() for m in regex.finditer('( [a-zA-Z]\. )', findSection)]
                    name = ''
                    if len(letterPos) > 0:
                        for let in range(0, len(letterPos)):
                            if len(letterPos) - 1 > let:
                                if letterPos[let+1] < findSection.index('gene transcript exons direction type'):
                                    continue
                                else:
                                    if 'panel' in findSection[letterPos[let]:letterPos[let]+30]:
                                        sectionBit = findSection[letterPos[let] + 4: ]
                                        if '=' in sectionBit:
                                            if sectionBit.index('=') < sectionBit.index(':'):
                                                name = sectionBit[:sectionBit.index('=')]
                                            else:
                                                name = sectionBit[:sectionBit.index(':')]
                                        else:
                                            name = sectionBit[:sectionBit.index(':')]
                            else:
                                if 'panel' in findSection[letterPos[let]:letterPos[let] + 30]:
                                    sectionBit = findSection[letterPos[let] + 4:]
                                    if '=' in sectionBit:
                                        if sectionBit.index('=') < sectionBit.index(':'):
                                            name = sectionBit[:sectionBit.index('=')]
                                        else:
                                            name = sectionBit[:sectionBit.index(':')]
                                    else:
                                        name = sectionBit[:sectionBit.index(':')]

                        if name != '':
                            testTypeHere = testTypeHere + ' - ' + name
                    else:
                        letterPos = [m.start() for m in regex.finditer('( \([a-zA-Z][0-9]\)\, )', findSection)]
                        for let in range(0, len(letterPos)):
                            if len(letterPos) - 1 > let:
                                if letterPos[let+1] < findSection.index('gene transcript exons direction type'):
                                    continue
                                else:
                                    if 'panel' in findSection[letterPos[let]:letterPos[let]+30]:
                                        sectionBit = findSection[letterPos[let] + 6: ]
                                        if sectionBit.index('=') < sectionBit.index(':'):
                                            name = sectionBit[:sectionBit.index('=')]
                                        else:
                                            name = sectionBit[:sectionBit.index(':')]
                            else:
                                if 'panel' in findSection[letterPos[let]:letterPos[let] + 30]:
                                    sectionBit = findSection[letterPos[let] + 6:]
                                    if sectionBit.index('=') < sectionBit.index(':'):
                                        name = sectionBit[:sectionBit.index('=')]
                                    else:
                                        name = sectionBit[:sectionBit.index(':')]
                        if name != '':
                            testTypeHere = testTypeHere + ' - ' + name

            geneChunk = []
            exonChunk = []
            panelTest = pathReport.index('gene transcript exons direction type')
            panelTest = pathReport[panelTest + len('gene transcript exons direction type'):]
            panelTest = panelTest[:panelTest.index('disclaimer:')].strip()
            panelSplit = panelTest.split()
            while len(panelSplit) > 0:
                gene = panelSplit[0]
                panelSplit = panelSplit[1:]
                transcript = panelSplit[0]
                panelSplit = panelSplit[1:]
                exon = []
                while "'" not in panelSplit[0] and 'n/a' not in panelSplit[0]:
                    if '(' in panelSplit[0]:
                        toAdd = panelSplit[0]
                        panelSplit = panelSplit[1:]
                        while ')' not in panelSplit[0]:
                            toAdd = toAdd + ' ' + panelSplit[0]
                            panelSplit = panelSplit[1:]
                        toAdd = toAdd + ' ' + panelSplit[0].replace(',','')
                        panelSplit = panelSplit[1:]
                        exon.append(toAdd)
                    else:
                        exon.append(panelSplit[0].replace(',', ''))
                        panelSplit = panelSplit[1:]
                exon = ', '.join(exon)
                direction = panelSplit[0]
                panelSplit = panelSplit[1:]
                type = panelSplit[0]
                panelSplit = panelSplit[1:]
                fusionList.append(gene)
                foundAnything = True
                fusionexonList.append(exon)
                fusiontranscriptList.append(transcript)
                fusionStartSitesList.append('')
                fusiondirectionList.append(direction)
                fusioncategoryList.append(type)
                fusionreportIdList.append(reportId)
                fusionsourceList.append(source)
                fusionhealthOrgList.append(healthOrg)
                fusionMRNList.append(MRN)
                fusionfirstNameList.append(firstName)
                fusionmiddleNameList.append(middleName)
                fusionlastNameList.append(lastName)
                fusionjrSrList.append(jrSr)
                fusionDOBList.append(DOB)
                fusiongenderList.append(gender)
                fusiontestTypeList.append(testTypeHere)
                fusiontestReportedDateList.append(date)
                fusionorderedDateList.append(ordered)
                fusiontestApproveList.append(received)
                fusionreadsList.append('')
                fusionuniqueMolList.append('')
                fusionStartSitesList.append('')
                fusionbreakpointsList.append('')
                fusionicdCodeList.append(icdC)
                fusionaccessionList.append(accession)
                fusionphysicianList.append(physician)
                fusiontakenList.append(taken)
                fusionstatusList.append(status)
                fusionfullTestList.append(pathReportFull)
                fusionspecimenCodeList.append(specimenCode)
                fusionspecimenTypeList.append(specimenType)
                fusionpdfLinkList.append(reportId)
                fusionpathologistList.append(pathologist)
                fusionorderedDateList.append(ordered)
                fusionlabelList.append('test target')
            repeatTest = repeatTest[repeatTest.index('gene transcript exons direction type') + len('gene transcript exons direction type'):]

        if 'gene chr genomic coordinates transcript cdna change protein change exon depth of coverage' in pathReport:
            noInterp = False
            if not 'gene chr genomic coordinates transcript cdna change protein change exon depth of coverage allele fraction interpretation' in pathReport:
                noInterp = True
            geneChunk = []
            exonChunk = []
            aminoacidChunk = []
            if noInterp:
                pathReport = pathReport.replace('depth of coverage % allele', 'depth of coverage allele')
                panelTest = pathReport.index('gene chr genomic coordinates transcript cdna change protein change exon depth of coverage allele fraction')
                panelTest = pathReport[panelTest + len('gene chr genomic coordinates transcript cdna change protein change exon depth of coverage allele fraction'):]
                # See if we can't get a more specific name
                if testType in genericTests:
                    testType = findSpecificTest(pathReport.index('gene chr genomic coordinates transcript cdna change protein change exon depth of coverage allele fraction'), testType)
                    panelTests.append(testType)
                if 'interpretation:' in panelTest:
                    panelTest = panelTest[:panelTest.index('interpretation:')].strip()
                if 'variant' in panelTest:
                    panelTest = panelTest[:panelTest.index('variant')].strip()
                if 'note:' in panelTest:
                    panelTest = panelTest[:panelTest.index('note:')].strip()
                if 'predicted' in panelTest:
                    panelTest = panelTest[:panelTest.index('predicted')].strip()
                if '2. ' in panelTest:
                    panelTest = panelTest[:panelTest.index('2. ')].strip()
            else:
                panelTest = pathReport.index('gene chr genomic coordinates transcript cdna change protein change exon depth of coverage allele fraction interpretation')
                panelTest = pathReport[panelTest + len('gene chr genomic coordinates transcript cdna change protein change exon depth of coverage allele fraction interpretation'):]
                if 'interpretation:' in panelTest:
                    panelTest = panelTest[:panelTest.index('interpretation:')].strip()
            if 'comment:' in panelTest:
                panelTest = panelTest[:panelTest.index('comment:')].strip()
            if 'note:' in panelTest:
                panelTest = panelTest[:panelTest.index('note:')].strip()
            if 'predicted' in panelTest:
                panelTest = panelTest[:panelTest.index('predicted')].strip()
            if 'gene' in panelTest:
                panelTest = panelTest[:panelTest.index('gene')].strip()
            if ' %' in panelTest:
                panelTest = panelTest.replace(' %', '%')
            if panelTest.startswith('(%)'):
                panelTest = panelTest.replace('(%)', '')
            if panelTest.startswith('%'):
                panelTest = panelTest.replace('%', '')


            panelSplit = panelTest.split()
            while len(panelSplit) > 0:
                # Sometimes we get like '2. variant of unknown significance (tier 3)
                if panelSplit[0].replace('.','').isnumeric() and panelSplit[0].endswith('.'):
                    while ')' not in panelSplit[0]:
                        panelSplit = panelSplit[1:]
                    panelSplit = panelSplit[1:]
                if panelSplit[0] in ['interpretation', 'variant']:
                    panelSplit = panelSplit[1:]
                if len(panelSplit) == 0:
                    break
                protein = ''
                if panelSplit[0].startswith('*'):
                    panelSplit = []
                # Sometimes they say [gene] lies within the active site
                if 'lies within' in ' '.join(panelSplit):
                    if '%' not in panelSplit:
                        panelSplit = []
                    else:
                        if ' '.join(panelSplit).index('lies within') < ' '.join(panelSplit).index('%'):
                            panelSplit = []
                # Sometimes we get [gene] mutations are used in the diagnosis of...
                if len(panelSplit) > 1:
                    if panelSplit[1] == 'mutations':
                        panelSplit = []
                if panelSplit == []:
                    break
                #print(panelSplit)
                gene = panelSplit[0]
                panelSplit = panelSplit[1:]
                location = panelSplit[0] + ':' + panelSplit[1]
                panelSplit = panelSplit[1:]
                panelSplit = panelSplit[1:]
                transcript = panelSplit[0]
                panelSplit = panelSplit[1:]
                cdna = panelSplit[0]
                panelSplit = panelSplit[1:]
                if cdna == 'c.' and not panelSplit[0].startswith('p.'):
                    cdna = cdna + panelSplit[0]
                    panelSplit = panelSplit[1:]
                if panelSplit[0].replace(',','') in ['p.(?)']:
                    panelSplit[0] = panelSplit[0].replace(',','')
                    protein = protein + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                    if panelSplit[0] in ['splice', 'site', 'deletion']:
                        while panelSplit[0] in ['splice', 'site', 'deletion']:
                            protein = protein + ' ' + panelSplit[0]
                            panelSplit = panelSplit[1:]
                            protein = protein.strip()
                    elif ')' in ' '.join(panelSplit):
                        while ')' not in panelSplit[0]:
                            protein = protein + ' ' + panelSplit[0]
                            panelSplit = panelSplit[1:]
                        protein = protein + ' ' + panelSplit[0]
                        panelSplit = panelSplit[1:]
                        protein = protein.strip()
                elif panelSplit[0] in ['promoter', 'splice']:
                    protein = panelSplit[0]
                    panelSplit = panelSplit[1:]
                    protein = protein + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                    if panelSplit[0] in ['mutation']:
                        protein = protein + ' ' + panelSplit[0]
                        panelSplit = panelSplit[1:]
                elif panelSplit[0] == 'exon':
                    while not panelSplit[0].isnumeric():
                        protein = protein + ' ' + panelSplit[0]
                        panelSplit = panelSplit[1:]
                    protein = protein.strip()
                elif panelSplit[0].isnumeric():
                    protein = ''
                else:
                    protein = panelSplit[0]
                    panelSplit = panelSplit[1:]
                if panelSplit[0] in ['splicing']:
                    protein = protein + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                if panelSplit[0].endswith(')') and '(' in protein:
                    protein = protein + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                exon = panelSplit[0]
                panelSplit = panelSplit[1:]
                dp = panelSplit[0]
                panelSplit = panelSplit[1:]
                if panelSplit[0] in ['(low)']:
                    dp = dp + ' ' + panelSplit[0]
                    panelSplit = panelSplit[1:]
                af = panelSplit[0]
                panelSplit = panelSplit[1:]
                if noInterp:
                    label = ''
                else:
                    if panelSplit[0] in ['likely', 'see']:
                        label = panelSplit[0] + ' ' + panelSplit[1]
                        panelSplit = panelSplit[1:]
                        panelSplit = panelSplit[1:]
                    else:
                        label = panelSplit[0]
                        panelSplit = panelSplit[1:]
                if len(panelSplit) > 0:
                    if panelSplit[0].replace('.', '').isnumeric() and panelSplit[0].endswith('.'):
                        panelSplit = []
                    elif panelSplit[0].startswith('*') and panelSplit[0].replace('*','') in geneChunk:
                        panelSplit = []
                if debug:
                    print('location 16')
                foundAnything = True
                geneList.append(gene)
                geneChunk.append(gene)
                locationList.append(location)
                transcriptList.append(transcript)
                cdnaList.append(cdna)
                proteinList.append(protein)
                aminoAcidRangeList.append('')
                alleleFrequencyList.append(af)
                dpList.append(dp)
                exonList.append(exon)
                exonChunk.append(exon)
                labelList.append(label)
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
                orderedDateList.append(ordered)
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
                fullTestList.append(pathReportFull)

        # First we need to get all instances of the header. The first three fields have been constant in
        # basically the panels I've seen from HF.
        panelPos = [m.start() for m in regex.finditer('(?:gene location transcript\b){s<=2}', pathReport)]
        panelText = regex.findall('(?:gene location transcript\b){s<=2}', pathReport)
        panelEnds = []

        # I've also only seen panels end with 'label' or 'interpretation'. This section picks out the rest of the
        # label until we run into one of those two keywords.
        panelEndText = ""
        fullPanel = ""

        # This is where we separate out the tests with semi-structured panels
        if panelText:

            # There might be many different semi-structured sections!
            for panelStart in panelPos:
                if testType in ['surgical pathology report']:
                    upToPanel = pathReport[:panelStart]
                    print(upToPanel)
                # At this point, 'panelText' is 'gene location transcript'. Let's get the end of the panel
                # which is either 'label' or 'interpretation'
                restOfReport = pathReport[panelStart+len(panelText):panelStart+len(panelText) + 100]
                # It'll either be 'label' or 'interpretation'
                panelEndText = regex.findall('(?:label\b){s<=1}', restOfReport)
                panelEndPos = [m.start() for m in regex.finditer('(?:label\b){s<=1}', restOfReport)]
                if not panelEndText:
                    panelEndText = regex.findall('(?:interpreation\b){s<=6}', restOfReport)
                    panelEndPos = [m.start() for m in regex.finditer('(?:interpreation\b){s<=6}', restOfReport)]
                if not panelEndText:
                    panelEndText = regex.findall('(?:interpretation\b){s<=1}', restOfReport)
                    panelEndPos = [m.start() for m in regex.finditer('(?:interpretation\b){s<=8}', restOfReport)]
                if not panelEndText:
                    print(restOfReport)
                    panelEndPos = [restOfReport.index(' af ')]
                    panelEndText = [' af ']
                fullPanel = pathReport[panelStart:panelStart+len(panelText)+panelEndPos[0] + len(panelEndText[0])]
                sectionList.append(fullPanel)
                sectionPos.append(panelStart)
                panelEnds.append(panelEndPos[0])

        elif testType in panelTests and not foundAnything and portBit == len(allReportsLoc)-2:
            if debug:
                print('location 17')
            foundAnything = True
            geneList.append('')
            locationList.append('')
            transcriptList.append('')
            cdnaList.append('')
            proteinList.append('')
            aminoAcidRangeList.append('')
            alleleFrequencyList.append('')
            dpList.append('')
            exonList.append('')
            labelList.append('Test passed to NLP')
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
            orderedDateList.append(ordered)
            testApproveList.append(received)
            icdCodeList.append(icdC)
            accessionList.append(accession)
            physicianList.append(physician)
            takenList.append(taken)
            statusList.append("No Panel Results")
            specimenCodeList.append(specimenCode)
            specimenTypeList.append(specimenType)
            pdfLinkList.append(pdfLink)
            pathologistList.append(pathologist)
            fullTestList.append(pathReportFull)

        # Now we push the panel onto the list of sections, and add the position.
        for section in sections:
            if section in pathReport:
                sectionPositions = [m.start() for m in re.finditer(re.escape(section), pathReport)]
                for pos in sectionPositions:
                    sectionList.append(section)
                    sectionPos.append(pos)
        sectionList = [x for _, x in sorted(zip(sectionPos, sectionList))]
        sectionPos = sorted(sectionPos)

        if 'gene location' in pathReport and not fullPanel:
            print("A SEMI-STRUCTURED PATH REPORT DIDN'T FOLLOW THE PATTERN!")
            print(pathReport)
            input()

        geneChunk = []
        exonChunk = []
        aminoacidChunk = []

        for section in range(0, len(sectionList)):
            if 'gene location' in sectionList[section]:
                position = section
                # See if we can't get a more specific name
                if testType in genericTests:
                    testType = findSpecificTest(sectionPos[position], testType)
                    panelTests.append(testType)
                thisSection = pathReport[sectionPos[position] + len(sectionList[section]):sectionPos[position+1]].split()
                # This eliminates interior extra spaces
                thisSection = [x for x in thisSection if x]

                # We're going to remove the semi-structured list later from the report.
                semiStructuredSection = pathReport[sectionPos[position]: sectionPos[position+1]]

                # We'll make sure every record has the same number of rows. This means adding some blanks.
                addExon = False
                exon = ""
                addVaf = False
                addDp = False
                noCdna = False
                noProtein = False

                # Sometimes, for whatever reason, the allele frequency is represented INSIDE the table. We'll capture it
                # here.
                hiddenAF = ''

                # Let's split up the panel, just like we'll split each line up. Instead of referencing by number,
                # let's get the location by name. Improves readability.
                fullPanelBroken = fullPanel.split()
                # Sometimes "AF" is named "Allele Frequency"
                if 'allele' in fullPanelBroken:
                    del fullPanelBroken[fullPanelBroken.index('allele')+1]
                    fullPanelBroken[fullPanelBroken.index('allele')] = 'vaf%'

                if 'cdna' not in fullPanelBroken:
                    noCdna = True
                    fullPanelBroken.insert(3, 'cdna')

                if 'protein' not in fullPanelBroken:
                    noProtein = True
                    fullPanelBroken.insert(4, 'protein')

                # These are the maybes
                # Do we need to add exon?
                if 'exon' not in fullPanelBroken:
                    addExon = True

                # What about vaf?
                vaf = ''
                for j in range(0, len(fullPanelBroken)-1):
                    if 'af' in fullPanelBroken[j]:
                        vaf = j
                        if fullPanelBroken[j+1] in ('%', '(%)'):
                            del fullPanelBroken[j+1]
                if not vaf:
                    addVaf = True

                # We need to make sure that 'label' or 'interpretation' are the last things in the panel
                if 'label' in fullPanelBroken:
                    label = fullPanelBroken.index('label')
                    del fullPanelBroken[label+1:]
                else:
                    for i in range(0, len(fullPanelBroken)):
                        if regex.findall('(?:interpretation\b){e<7}', fullPanelBroken[i]):
                            label = i
                            del fullPanelBroken[label+1:]
                            break

                # So now we have the indices for our dataframe. Let's make sure the data fits it
                # ###### Now to eliminate any discrepencies.
                while len(thisSection) >= len(fullPanelBroken):

                    # Sometimes they just write in variants of unknown significance. Sometimes 'see comment'
                    if thisSection[0] == 'variants':
                        del thisSection[0:4]
                    if thisSection[0] == 'see':
                        del(thisSection[0:2])

                    # Occasionally we see a gene name duplicated, like 'braf braf'
                    if thisSection[0] == thisSection[1]:
                        thisSection = thisSection[1:]

                    # Sometimes after the gene we see '(see comment)'
                    if 'see' in thisSection[1] and 'comment' in thisSection[2]:
                        del thisSection[1:3]

                    # Occasionally, the first column is not a gene name
                    if 'nm_' in thisSection[0]:
                        if thisSection[0].replace('nm_', '').replace('.', '').isnumeric():
                            thisSection.insert(0, '')
                            thisSection.insert(0, '')
                    if thisSection[0].replace(':', '').isnumeric():
                        thisSection.insert(0, '')

                    # Asterisks show up in a few places. We might want them in the protein or cdna sections, but
                    # sometimes they show up as notes on the genes or label. We might pull those out later, but for now
                    # We'll just delete them. I'll go back to find them later!
                    if thisSection[1] == '*':
                        thisSection.remove(thisSection[1])
                    while thisSection[0].endswith('*'):
                        thisSection[0] = thisSection[0][:-1]
                    if '*' in thisSection[len(fullPanelBroken)-1]:
                        thisSection[len(fullPanelBroken)-1] = thisSection[len(fullPanelBroken)-1].replace('*', '')

                    # Sometimes the 'location' is exon + a name. PIPE DELIMIT. Sometimes it's even weirder, having
                    # the allele frequency INSIDE the table??? Sometimes the exon is in the name!
                    if 'exon' in thisSection[1]:
                        if thisSection[3] == 'allele' and thisSection[4] == 'frequency':
                            if thisSection[6] == '%':
                                del thisSection[6]
                            if '%' not in thisSection[5]:
                                thisSection[5] = thisSection[5] + '%'
                            hiddenAF = thisSection[5]
                            del thisSection[1:6]
                        else:
                            exon = thisSection[2].replace(')', '')
                            del thisSection[1:3]

                    # I've seen the location be 19:13054621; 19:13054688
                    if thisSection[1].endswith(';') and ':' in thisSection[2]:
                        thisSection[1:3] = [''.join(thisSection[1:3])]

                    # Sometimes the gene also has some brackets. Dunno. PIPE DELIMIT PLEASE. Talk to Cheryl or Alyssa about
                    # if we really need these!
                    if thisSection[1].startswith('[') and thisSection[1].endswith(']'):
                        thisSection[0:2] = [' '.join(thisSection[0:2])]

                    # Sometimes the cdna will have some parentheses after it
                    if '(' in thisSection[4]:
                        if 'p.(' in thisSection[4]:
                            thisSection[4] = thisSection[4].replace('(','').replace(')','')
                        # I don't THINK this condition gets used, but it's what was here before!
                        else:
                            del thisSection[4]

                    # Sometimes there's just straight-up a gap that needs fixed
                    if not thisSection[4].startswith('p.') and thisSection[5].startswith('p.'):
                        thisSection[3:5] = [' '.join(thisSection[3:5])]

                    # Yet another pipe-delimiting problem. Sometimes there's a semi-colon with a space gap in cdna or protein.
                    while thisSection[3].endswith(';'):
                        thisSection[3:5] = [' '.join(thisSection[3:5])]
                    while thisSection[4].endswith(';'):
                        thisSection[4:6] = [' '.join(thisSection[4:6])]

                    # Another protein splitting problem
                    if not thisSection[5].replace('.','').replace('%','').isnumeric() and thisSection[6].replace('.','').replace('%','').isnumeric():
                        thisSection[4:6] = [' '.join(thisSection[4:6])]

                    # Sometimes the protein is 'p.? (splice site)'
                    if thisSection[5].startswith('(') and thisSection[6].endswith(')'):
                        thisSection[4:7] = [' '.join(thisSection[4:7])]
                    # or sometimes p.(cys1464_ile2002 delinspheproprothr)
                    elif '(' in thisSection[4] and not thisSection[4].endswith(')') and thisSection[5].endswith('('):
                        thisSection[4:6] = [' '.join(thisSection[4:6])]


                    # This one is just odd. Happened once, hopefully not again. split between the del and the r.
                    # I'm also guarding against future times when the del might be in the protein. Furthermore,
                    # sometimes the protein site is called 'splice site' or 'splicing region' or 'splice site variant'
                    if thisSection[3].endswith('del') and not thisSection[4].startswith('p.'):
                        thisSection[3:5] = [''.join(thisSection[3:5])]
                    if thisSection[4].endswith('del') and not thisSection[5].replace('.', '').isdigit():
                        thisSection[4:6] = [''.join(thisSection[4:6])]
                    if thisSection[4] == 'variant':
                        thisSection[3:5] = [''.join(thisSection[3:5])]
                    # I've also seen this where there are sometimes not fields for 'protein'
                    if thisSection[4] in ['splice', '?splice'] and thisSection[5] == 'site' and thisSection[6] == 'variant':
                        thisSection[4:7] = [' '.join(thisSection[4:7])]
                    if thisSection[4] == 'not' or thisSection[4] in ['splice', '?splice', 'splicing', '?truncating', 'truncating']:
                        thisSection[4] = thisSection[4]
                        thisSection[4:6] = [' '.join(thisSection[4:6])]

                    # If we're lacking a protein or CDNA, insert it here
                    if noCdna:
                        thisSection.insert(3, '')
                    # Sometimes they might call the protein a splice site variant, EVEN THOUGH they don't say that
                    # protein is a field.
                    if noProtein:
                        if 'splice' not in thisSection[4]:
                            thisSection.insert(4, '')

                    # Sometimes we won't have a protein field.
                    if thisSection[3].startswith('c.') and thisSection[4].replace('.', '').isdigit():
                        thisSection.insert(4, '')

                    # Sometimes there's an extra field by the protein - we took out the addition because it was redundant information: like V600E after p.val600ely
                    if thisSection[5].startswith('('):
                        #thisSection[4] = thisSection[4] + " " + thisSection[5]
                        del thisSection[5]

                    # cdna or protein can be "see comment"
                    if thisSection[4] == 'see':
                        thisSection[4:6] = [' '.join(thisSection[4:6])]
                    if thisSection[5] == 'see':
                        thisSection[5:7] = [' '.join(thisSection[5:7])]

                    # I'm assuming that this is just a loss of precision. We COULD impute it to be 0, but, we don't know, so
                    # just leaving out the decimal seems truer-to-life. This is for depth of read.
                    if not addDp:
                        if thisSection[5].endswith('.'):
                            thisSection[5] = thisSection[5].rstrip('.')

                    # If the AF doesn't have a percent, add one on. Don't worry about trying to match loose ones, just delete
                    # them.
                    if not addVaf:
                        if '%' not in thisSection[vaf]:
                            thisSection[vaf] = thisSection[vaf] + '%'
                        # This takes out the percentage signs if there's a space between AF # and %
                        if thisSection[vaf + 1] == '%':
                            thisSection.pop(vaf + 1)

                    # Occasionally, they decide to call the label 'variant of unknown significance' instead of vous. PLEASE
                    # pipe delimit, people.
                    if 'variant' in thisSection[len(fullPanelBroken)-1]:
                        if thisSection[len(fullPanelBroken)] == 'of':
                            thisSection[len(fullPanelBroken)-1] = 'vous'
                            del thisSection[len(fullPanelBroken):len(fullPanelBroken)+3]

                    # Since we're splitting by spaces, we'll smush the likelies together. THIS is why you pipe-delimit,
                    # darn it!
                    if thisSection[len(fullPanelBroken)-1] == "likely" or thisSection[len(fullPanelBroken)-1] == \
                            'pathogenic/likely' or thisSection[len(fullPanelBroken)-1] == 'see' or \
                            thisSection[len(fullPanelBroken)-1] == 'very':
                        thisSection[len(fullPanelBroken)-1:len(fullPanelBroken)+1] = [' '.join(thisSection[len(fullPanelBroken)-1:len(fullPanelBroken)+1])]
                    if len(thisSection) > len(fullPanelBroken):
                        if 'likely' in thisSection[len(fullPanelBroken)]:
                            thisSection[len(fullPanelBroken)-1:len(fullPanelBroken)+2] = [' '.join(thisSection[len(fullPanelBroken)-1:len(fullPanelBroken)+2])]

                    # We'll want to come back to this, since there are comments about the results here
                    if len(thisSection) > len(fullPanelBroken):
                        if '(comment' in thisSection[len(fullPanelBroken)]:
                            del thisSection[len(fullPanelBroken):len(fullPanelBroken)+2]
                        if '(see' in thisSection[len(fullPanelBroken)]:
                            del thisSection[len(fullPanelBroken):len(fullPanelBroken)+2]

                    # Might be an asterisk or period in the final section. Remove it. OR the first one!
                    if '*' in thisSection[len(fullPanelBroken) - 1]:
                        thisSection[len(fullPanelBroken)-1] = thisSection[len(fullPanelBroken)-1].replace('*', '')
                    if '.' in thisSection[len(fullPanelBroken) - 1]:
                        thisSection[len(fullPanelBroken)-1] = thisSection[len(fullPanelBroken)-1].replace('.', '')
                    if ',' in thisSection[len(fullPanelBroken) - 1]:
                        thisSection[len(fullPanelBroken)-1] = thisSection[len(fullPanelBroken)-1].replace(',', '')
                    if '*' in thisSection[0]:
                        thisSection[0] = thisSection[0].replace('*', '')
                    thisSection[0] = thisSection[0].strip()

                    # Looks like sometimes we don't split the c. and p. correctly?
                    if 'p.' in thisSection[3] and thisSection[4] == '':
                        thisSection[4] = thisSection[3].split()[1]
                        thisSection[3] = thisSection[3].split()[0]
                    elif 'p.' in thisSection[3] and '(' in thisSection[4] and ')' in thisSection[4]:
                        thisSection[4] = thisSection[3].split()[1] + thisSection[4]
                        thisSection[3] = thisSection[3].split()[0]
                    # Sometimes the protein is "?splice site variant"
                    if '?splice' in thisSection[4] or '?truncating':
                        thisSection[4] = thisSection[4].replace('?splice', 'splice').replace('?truncating', 'truncating')

                    # Here's where we add to the lists.
                    genAdd = thisSection[0]
                    if len(genAdd.split()) == 2:
                        if genAdd.split()[1].replace('[','').replace(']','').isnumeric() and '[' in genAdd.split()[1]:
                            genAdd = genAdd.split()[0]
                        if genAdd.endswith('.') or genAdd.endswith(','):
                            genAdd = genAdd[:-1]
                    # If we have a location but no gene name, just move on.
                    if len(thisSection[1]) == 0 and len(genAdd) > 0:
                        continue
                    if debug:
                        print('location 18')
                    foundAnything = True
                    geneList.append(genAdd)
                    # This is the test-specific list of genes
                    geneChunk.append(genAdd)
                    locationList.append(thisSection[1].replace(',', ''))
                    transcriptList.append(thisSection[2])
                    cdnaList.append(thisSection[3])
                    proteinList.append(thisSection[4])
                    # This is for the test-specific list of proteins(amino acids)
                    allAcids = re.findall(r'\d+', thisSection[4])
                    res = list(map(int, allAcids))
                    if res:
                        justAminoAcid = res[0]
                        aminoacidChunk.append(justAminoAcid)
                    else:
                        aminoacidChunk.append('')
                    if addDp:
                        dpList.append('')
                    else:
                        dpList.append(thisSection[fullPanelBroken.index('dp')])
                    if addVaf:
                        alleleFrequencyList.append('')
                    else:
                        alleleFrequencyList.append(thisSection[vaf])
                    if addExon:
                        if exon:
                            if '-' in exon:
                                firstNum = exon.split('-')[0]
                                secondNum = exon.split('-')[1]
                                exon = ','.join(range(firstNum, secondNum+1))
                            exonList.append(exon)
                            exon = ''
                        else:
                            exonList.append('')
                    else:
                        exon = thisSection[fullPanelBroken.index('exon')]
                        if '-' in exon:
                            firstNum = exon.split('-')[0]
                            secondNum = exon.split('-')[1]
                            exon = ','.join(range(firstNum, secondNum + 1))
                        exonList.append(exon)
                    # This is the test-specific list of exons
                    if addExon:
                        exonChunk.append('')
                    else:
                        exonChunk.append(thisSection[fullPanelBroken.index('exon')])
                    # Check to see if the result is equivocal first!
                    # MAYBE REMOVE IF BREAKS - I'm thinking we SHOULD add in positive results (BUT NOT NEGATIVE) if the exon was equivocal!
                    exonWasEqui = False
                    #if thisSection[0] in equivocalGenes:
                    #    equiIndex = equivocalGenes.index(thisSection[0])
                    #    exon = equivocalExons[equiIndex]
                    #    exonEq = exon.split(',')
                    #    for eeq in exonEq:
                    #        if '-' not in eeq:
                    #            if (eeq == exonList[-1] or eeq in ['full', 'all exons targeted']) and not exonWasEqui:
                    #                labelList.append('equivocal')
                    #                exonWasEqui = True
                    #        else:
                    #            lower = eeq.split('-')[0]
                    #            upper = eeq.split('-')[1]
                    #            if int(justAminoAcid) < int(upper) and justAminoAcid > int(lower):
                    #                labelList.append('equivocal')
                    #                exonWasEqui = True

                    if not exonWasEqui:
                        labelList.append(thisSection[len(fullPanelBroken)-1])
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
                    orderedDateList.append(ordered)
                    testApproveList.append(received)
                    icdCodeList.append(icdC)
                    accessionList.append(accession)
                    physicianList.append(physician)
                    takenList.append(taken)
                    if not status:
                        statusList.append("normal")
                    else:
                        statusList.append(status)
                    specimenCodeList.append(specimenCode)
                    specimenTypeList.append(specimenType)
                    pdfLinkList.append(pdfLink)
                    pathologistList.append(pathologist)
                    fullTestList.append(pathReportFull)

                    # We'll add the amino acid range later, when we check it against the panels (unless there's no
                    # gene panel list, then we add it here.)
                    if noPanel:
                        #aminoAcidRangeList.append('')
                        pass
                    endToken = thisSection[len(fullPanelBroken) - 1]
                    if not regex.findall('(?:vous){e<=2}', endToken) and not regex.findall('(?:pathogenic){e<=2}', endToken) \
                            and endToken != 'uncertain' and endToken != 'see comment' and 'class_' not in endToken:
                        if 'nm_' in thisSection:
                            print(thisSection)
                        thisSection = []

                    # From here, we take the next chunk. Since we've normalized the above chunk, it will always be
                    # the length of the panel.
                    if len(thisSection) == len(fullPanelBroken):
                        thisSection = []
                    else:
                        if 'nm_' in ' '.join(thisSection[len(fullPanelBroken):]):
                            thisSection = thisSection[len(fullPanelBroken):]
                        else:
                            thisSection = []

        # NOW's the time to pull out the positive equivocals, too!
        if (testType in panelTests or 'surgical pathology report' in testType.lower()) and (regex.findall('(?:positive result cannot be ruled out.){s<=2}', pathReport) \
                or regex.findall('(?:false positive cannot be ruled out.){s<=2}', pathReport)) and (not regex.findall('(?: technically a false positive result cannot be ruled out.){s<=2}', pathReport)):
            hasExtras = False
            posEquivSt = [m.start() for m in regex.finditer('(?:positive result cannot be ruled out.){s<=2}', pathReport)]
            phrase = 'positive result cannot be ruled out.'
            if not posEquivSt:
                posEquivSt = [m.start() for m in regex.finditer('(?:false positive cannot be ruled out.){s<=2}', pathReport)]
                phrase = 'false positive cannot be ruled out.'
            posChunk = pathReport[posEquivSt[0] + len(phrase):]
            posEquivStop = [m.start() for m in regex.finditer(r'(\s\d{1,}[\).]\s)', posChunk)]
            posEquiStopVariant = [m.start() for m in regex.finditer('(?:results-comments){s<=2}', posChunk)]
            if posEquiStopVariant and posEquivStop:
                if posEquiStopVariant[0] < posEquivStop[0]:
                    posEquivStop = posEquiStopVariant
            if not posEquivStop and posEquiStopVariant:
                posEquivStop = posEquiStopVariant
            if 'correlation with' in posChunk:
                posChunk = posChunk[:posChunk.index('correlation with')]
            if '1).' in posChunk:
                if posChunk.index('1).') < posChunk.index('results-comments'):
                    posChunk = posChunk[posChunk.index('1).'):]
                    posChunk = posChunk[:posChunk.index('  ')]
            else:
                posChunk = posChunk[:posEquivStop[0]].strip()
            if '2).' in posChunk:
                posChunk = posChunk[:posChunk.index('2).')]
            if '3).' in posChunk:
                posChunk = posChunk[:posChunk.index('3).')]
            if posChunk.startswith('clinical and'):
                posChunk = ''
            if 'it is noted' in posChunk:
                posChunk = posChunk[posChunk.find('.')+1:]
            if 'clinical correlation' in posChunk:
                print(posChunk)
                print("CC")
                posChunk = ''
            if 'dp exon af label' in posChunk:
                hasExtras = True
            if '1).' in posChunk:
                posSplit = posChunk.split()
                while len(posSplit) > 1:
                    if posSplit[0] in ['unless']:
                        break
                    posSplit = posSplit[1:]
                    if posSplit[0] in ['unless']:
                        break
                    geneName = posSplit[0]
                    posSplit = posSplit[1:]
                    cdnaName = posSplit[0].replace('(', '')[:-1]
                    posSplit = posSplit[1:]
                    proteinName = posSplit[0][:-1]
                    posSplit = posSplit[1:]
                    posSplit = posSplit[1:]
                    dpName = posSplit[0][:-1]
                    posSplit = posSplit[1:]
                    posSplit = posSplit[1:]
                    while '%' not in posSplit[0]:
                        posSplit = posSplit[1:]
                    afName = posSplit[0][:-1].replace(')', '')
                    posSplit = posSplit[1:]
                    if len(posSplit) > 0:
                        if posSplit[0].endswith('.') and not posSplit[0].endswith(').'):
                            posSplit = posSplit[1:]

                    if debug:
                        print('location 19')
                    foundAnything = True
                    geneList.append(geneName)
                    geneChunk.append(geneName)
                    exonList.append('')
                    exonChunk.append('')
                    locationList.append('')
                    transcriptList.append('')
                    cdnaList.append(cdnaName)
                    proteinList.append(proteinName)
                    aminoacidChunk.append('')
                    dpList.append(dpName)
                    alleleFrequencyList.append(afName)
                    labelList.append("equivocal - low AF")
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
                    orderedDateList.append(ordered)
                    testApproveList.append(received)
                    icdCodeList.append(icdC)
                    accessionList.append(accession)
                    physicianList.append(physician)
                    takenList.append(taken)
                    if not status:
                        statusList.append("normal")
                    else:
                        statusList.append(status)
                    specimenCodeList.append(specimenCode)
                    specimenTypeList.append(specimenType)
                    pdfLinkList.append(pdfLink)
                    pathologistList.append(pathologist)
                    fullTestList.append(pathReportFull)
                    cdnaName = ''
                    proteinName = ''
                    dpName = ''
                    afName = ''
                posChunk = ''

            if 'gene location' in posChunk:
                posChunk = posChunk[posChunk.find('label') + 6:]
                posChunk = posChunk.split()
                for word in range(0, len(posChunk)):
                    if ('patho' in posChunk[word] or 'vous' in posChunk[word]) and word < len(posChunk)-1:
                        posChunk[word] = posChunk[word] + '-'
                posChunk = ' '.join(posChunk)

            multipleCsPs = False
            if '-' in posChunk:
                posSplit = posChunk.split('-')
            else:
                posChunk = posChunk.split()
                if len(posChunk) > 0:
                    if posChunk[0] == 'low':
                        posChunk = []
                for word in range(0, len(posChunk)):
                    if (' af' in ' ' + posChunk[word]) and word < len(posChunk)-2:
                        posChunk[word+1] = posChunk[word+1] + '-'
                    if word < len(posChunk) - 3:
                        if 'c.' in posChunk[word] and 'c.' in posChunk[word+2]:
                            multipleCsPs = True
                posChunk = ' '.join(posChunk)
            posSplit = posChunk.split('-')
            geneName = ''
            locationName = ''
            transcriptName = ''
            exonName = ''
            cdnaName = ''
            proteinName = ''
            dpName = ''
            afName = ''
            labelName = ''
            if posSplit[0] == '' or posSplit[0] == ' ':
                posSplit = posSplit[1:]
            for equiv in posSplit:
                print(posSplit)
                indSplit = equiv.split()
                if 'c.' in indSplit[0]:
                    geneName = ''
                else:
                    geneName = indSplit[0].replace(':', '')
                    indSplit = indSplit[1:]
                if multipleCsPs:
                    while len(indSplit) >= 1:
                        if 'nm_' in indSplit[0]:
                            transcriptName = indSplit[0].replace(',', '')
                            indSplit = indSplit[1:]
                        if 'c.' in indSplit[0]:
                            cdnaName = indSplit[0].replace(',', '')
                            indSplit = indSplit[1:]
                        if 'p.' in indSplit[0] and hasExtras:
                            proteinName = indSplit[0].replace(';', '')
                            indSplit = indSplit[1:]
                            dpName = indSplit[0].replace(',', '')
                            indSplit = indSplit[1:]
                            exonName = indSplit[0].replace(',', '')
                            indSplit = indSplit[1:]
                            afName = indSplit[0].replace(',', '')
                            indSplit = indSplit[1:]
                            labelName = indSplit[0].replace(',', '')
                            indSplit = indSplit[1:]
                            if len(geneName.split()) == 2:
                                if geneName.split()[1].replace('[', '').replace(']', '').isnumeric() and '[' in geneName.split()[1]:
                                    geneName = geneName.split()[0]
                                if geneName.endswith('.') or geneName.endswith(','):
                                    geneName = geneName[:-1]
                            if debug:
                                print('location 20')
                            foundAnything = True
                            geneList.append(geneName)
                            geneChunk.append(geneName)
                            if '-' in exonName:
                                firstNum = exonName.split('-')[0]
                                secondNum = exonName.split('-')[1]
                                exonName = ','.join(range(firstNum, secondNum + 1))
                            exonList.append(exonName)
                            exonChunk.append(exonName)
                            locationList.append(locationName.replace(',', ''))
                            transcriptList.append(transcriptName)
                            cdnaList.append(cdnaName)
                            proteinList.append(proteinName)
                            aminoacidChunk.append('')
                            dpList.append(dpName)
                            alleleFrequencyList.append(afName)
                            labelList.append("equivocal - low AF")
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
                            orderedDateList.append(ordered)
                            testApproveList.append(received)
                            icdCodeList.append(icdC)
                            accessionList.append(accession)
                            physicianList.append(physician)
                            takenList.append(taken)
                            if not status:
                                statusList.append("normal")
                            else:
                                statusList.append(status)
                            specimenCodeList.append(specimenCode)
                            specimenTypeList.append(specimenType)
                            pdfLinkList.append(pdfLink)
                            pathologistList.append(pathologist)
                            fullTestList.append(pathReportFull)
                            cdnaName = ''
                            proteinName = ''
                            dpName = ''
                            afName = ''
                            indSplit = indSplit[1:]
                        if 'p.' in indSplit[0] and not hasExtras:
                            proteinName = indSplit[0].replace(';', '')
                            if len(geneName.split()) == 2:
                                if geneName.split()[1].replace('[', '').replace(']', '').isnumeric() and '[' in geneName.split()[1]:
                                    geneName = geneName.split()[0]
                                if geneName.endswith('.') or geneName.endswith(','):
                                    geneName = geneName[:-1]
                            if debug:
                                print('location 21')
                            foundAnything = True
                            geneList.append(geneName)
                            geneChunk.append(geneName)
                            if '-' in exonName:
                                firstNum = exonName.split('-')[0]
                                secondNum = exonName.split('-')[1]
                                exonName = ','.join(range(firstNum, secondNum + 1))
                            exonList.append(exonName)
                            exonChunk.append(exonName)
                            locationList.append(locationName.replace(',', ''))
                            transcriptList.append(transcriptName)
                            cdnaList.append(cdnaName)
                            proteinList.append(proteinName)
                            aminoacidChunk.append('')
                            dpList.append(dpName)
                            alleleFrequencyList.append(afName)
                            labelList.append("equivocal - low AF")
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
                            orderedDateList.append(ordered)
                            testApproveList.append(received)
                            icdCodeList.append(icdC)
                            accessionList.append(accession)
                            physicianList.append(physician)
                            takenList.append(taken)
                            if not status:
                                statusList.append("normal")
                            else:
                                statusList.append(status)
                            specimenCodeList.append(specimenCode)
                            specimenTypeList.append(specimenType)
                            pdfLinkList.append(pdfLink)
                            pathologistList.append(pathologist)
                            fullTestList.append(pathReportFull)
                            cdnaName = ''
                            proteinName = ''
                            dpName = ''
                            afName = ''
                            indSplit = indSplit[1:]
                    continue
                if indSplit[0] == '':
                    indSplit = indSplit[1:]
                if indSplit[0].replace(':', '').isnumeric and ':' in indSplit[0]:
                    locationName = indSplit[0]
                    indSplit = indSplit[1:]
                if 'nm_' in indSplit[0]:
                    transcriptName = indSplit[0]
                    indSplit = indSplit[0]
                if 'exon' in indSplit[0]:
                    if indSplit[0] == 'exon':
                        indSplit = indSplit[1:]
                    exonName = indSplit[0].replace(';', '').replace(',', '').replace(':', '')
                    indSplit = indSplit[1:]
                if 'c.' in indSplit[0]:
                    cdnaName = indSplit[0].replace(';', '').replace(',', '')
                    indSplit = indSplit[1:]
                if 'p.' in indSplit[0]:
                    proteinName = indSplit[0].replace(';', '').replace(',', '')
                    indSplit = indSplit[1:]
                    # In the long form ones, dp and af come after protein
                    if indSplit[0].isnumeric() and int(indSplit[0]) > 100:
                        dpName = indSplit[0]
                        indSplit = indSplit[1:]
                    if indSplit[0].isnumeric():
                        exonName = indSplit[0]
                        indSplit = indSplit[1:]
                    if '%' in indSplit[0]:
                        afName = indSplit[0]
                        indSplit = indSplit[1:]
                    if 'path' in indSplit[0] or 'vous' in indSplit[0]:
                        labelName = indSplit[0].replace('-', '')
                if 'dp' in indSplit[0]:
                    if indSplit[0].replace('(', '').replace(')', '') in ['dp:', 'dp']:
                        indSplit = indSplit[1:]
                    indSplit[0] = indSplit[0].replace('dp:', '').replace(';', '').replace(',', '').replace('(', '').replace(')', '')
                    indSplit[0] = indSplit[0].strip()
                    dpName = indSplit[0]
                    indSplit = indSplit[1:]
                if 'af' in indSplit[0]:
                    if indSplit[0] in ['af:', 'af']:
                        indSplit = indSplit[1:]
                    indSplit[0] = indSplit[0].replace('af:', '').replace(';', '').replace(',', '').replace('(', '').replace(')', '')
                    indSplit[0] = indSplit[0].strip()
                    afName = indSplit[0]
                    if len(geneName.split()) == 2:
                        if geneName.split()[1].replace('[', '').replace(']', '').isnumeric() and '[' in geneName.split()[1]:
                            geneName = geneName.split()[0]
                        if geneName.endswith('.') or geneName.endswith(','):
                            geneName = geneName[:-1]
                if debug:
                    print('location 22')
                foundAnything = True
                # Sometimes they say 'the following variant was found'
                if geneName == '':
                    firstBit = lower[:lower.index(equiv)]
                    firstBit = ' '.join(firstBit)
                    firstInd = firstBit.rfind('the following')
                    firstBit = firstBit[firstInd:]
                    firstBit = firstBit.split()
                    firstInd = firstBit.index('following')
                    geneName = firstBit[firstInd+1]
                    if firstBit[firstInd+2] == 'exon':
                        exonName = firstBit[firstInd+3]
                geneList.append(geneName)
                geneChunk.append(geneName)
                if '-' in exonName:
                    firstNum = exonName.split('-')[0]
                    secondNum = exonName.split('-')[1]
                    exonName = ','.join(range(firstNum, secondNum + 1))
                exonList.append(exonName)
                exonChunk.append(exonName)
                locationList.append(locationName.replace(',', ''))
                transcriptList.append(transcriptName)
                cdnaList.append(cdnaName)
                proteinList.append(proteinName)
                aminoacidChunk.append('')
                dpList.append(dpName)
                alleleFrequencyList.append(afName)
                labelList.append("Equivocal - low AF")
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
                orderedDateList.append(ordered)
                testApproveList.append(received)
                icdCodeList.append(icdC)
                accessionList.append(accession)
                physicianList.append(physician)
                takenList.append(taken)
                if not status:
                    statusList.append("normal")
                else:
                    statusList.append(status)
                specimenCodeList.append(specimenCode)
                specimenTypeList.append(specimenType)
                pdfLinkList.append(pdfLink)
                pathologistList.append(pathologist)
                fullTestList.append(pathReportFull)
                geneName = ''
                locationName = ''
                transcriptName = ''
                exonName = ''
                cdnaName = ''
                proteinName = ''
                dpName = ''
                afName = ''
                labelName = ''

        # At this point, 'geneChunk' is a list of the specific gene variants found in the test. 'exonChunk' is a list
        # of the associated exons. They are the same length.
        # geneTestedList is a list of lists, every sub-list of length one, with all the genes tested for IN THIS
        # REPORT.
        # exonTestedList is a list of lists, every sub-list can be any length, but the list of lists is the same
        # length as geneTestedList. I'm NOT dealing with Amino Acids at this point.
        # I'm going to subtract every pair of exons/genes that we find from the geneTestedList and exonTestedList.
        # anything left at the end will be given a 'negative' result.
        if testType in panelTests or (
                ('surgical pathology report' in testType.lower() or 'hematopathology report' in testType.lower()) and (regex.findall('(?:gene exon / amino acid){s<=2}', \
                                                                                   pathReport) or regex.findall('(?:gene target region){s<=2}', pathReport))):
            # There are two situations - either we get just the exons, or we have exons + amino acids.
            # If we have the amino acids, then we'll list those under 'no results', removing any that we found
            # a positive result in. If we only have exons, we'll do it with that.
            if aminoAcidTestedList:
                usedGenes = []
                usedLowerRange = []
                usedHigherRange = []
                usedFullRange = []
                for i in range(0, len(geneChunk)):
                    foundMatch = False
                    geneChunk[i] = geneChunk[i].replace(',','').replace('.','')
                    for j in range(0, len(geneTestedList)):
                        aminoAcidRangesToDelete = []
                        # Sometimes there might be actually be a situation where there are a mixture of amino acids and exons. If that's so, record the exons here.
                        if len(aminoAcidTestedList[j]) == 0:
                            for ex in exonTestedList[j]:
                                # There seem to be some ranges getting caught in here!
                                if '-' in str(ex):
                                    lower = int(ex.split('-')[0])
                                    upper = int(ex.split('-')[1])
                                    exonTestedList[j].remove(ex)
                                    for num in range(lower, upper + 1):
                                        exonTestedList[j].append(str(num))

                            if exonChunk[i] and geneChunk[i] == geneTestedList[j][0]:
                                if str(exonChunk[i]) in exonTestedList[j]:
                                    if len(exonTestedList[j]) == 1:
                                        exonTestedList[j] = ['blank']
                                        geneTestedList[j] = ['blank']
                                    else:
                                        exonTestedList[j].remove(str(exonChunk[i]))
                        for k in range(0, len(aminoAcidTestedList[j])):
                            if aminoAcidTestedList[j][k].replace('-','').isnumeric():
                                aaLower = int(aminoAcidTestedList[j][k].split('-')[0])
                                aaHigher = int(aminoAcidTestedList[j][k].split('-')[1])
                                if (aminoacidChunk[i]) and geneChunk[i] == geneTestedList[j][0]:
                                    if aaLower < int(aminoacidChunk[i]) < aaHigher:
                                        aminoAcidRangesToDelete.append(aminoAcidTestedList[j][k])
                                        # If we have TWO ranges that fit for one place, then don't add both. Concatenate.
                                        if not foundMatch:
                                            aminoAcidRangeList.append(aminoAcidTestedList[j][k])
                                        else:
                                            if not aminoAcidRangeList[-1] == aminoAcidTestedList[j][k]:
                                                aminoAcidRangeList[-1] = aminoAcidRangeList[-1] + ' , ' + aminoAcidTestedList[j][k]
                                        # Add this gene and the higher and lower range to the list. We'll need them if
                                        # there are any other variants in this range!
                                        usedGenes.append(geneChunk[i])
                                        usedLowerRange.append(aaLower)
                                        usedHigherRange.append(aaHigher)
                                        usedFullRange.append(aminoAcidTestedList[j][k])
                                        foundMatch = True
                        for rangeD in aminoAcidRangesToDelete:
                            aminoAcidTestedList[j].remove(rangeD)
                    # Last-Ditch effort: maybe we've already used this upper/lower range?
                    if not foundMatch:
                        for vb in range(0, len(usedGenes)):
                            if aminoacidChunk[i]:
                                if geneChunk[i] == usedGenes[vb] and usedLowerRange[vb] < aminoacidChunk[i] < usedHigherRange[vb] and not foundMatch:
                                    aminoAcidRangeList.append(usedFullRange[vb])
                                    foundMatch = True

                    # At this point we've got nothin'
                    if not foundMatch:
                        aminoAcidRangeList.append('')


            else:
                for i in range(0, len(geneChunk)):
                    # If there's no amino acid ranges stored, we need to add an extra 'no' for every positive result
                    aminoAcidRangeList.append('')
                    for j in range(0, len(geneTestedList)):
                        for ex in exonTestedList[j]:
                            # There seem to be some ranges getting caught in here!
                            if '-' in str(ex):
                                lower = int(ex.split('-')[0])
                                upper = int(ex.split('-')[1])
                                exonTestedList[j].remove(ex)
                                for num in range(lower, upper+1):
                                    exonTestedList[j].append(str(num))

                        if exonChunk[i] and geneChunk[i] == geneTestedList[j][0]:
                            if str(exonChunk[i]) in exonTestedList[j]:
                                if len(exonTestedList[j]) == 1:
                                    exonTestedList[j] = ['blank']
                                    geneTestedList[j] = ['blank']
                                else:
                                    exonTestedList[j].remove(str(exonChunk[i]))


            # Now at this point, we've gotten all the genes/exons we had handled, so time to add all the negatives to
            # the results!
            for place in range(0, len(geneTestedList)):
                if geneTestedList[place][0] != 'blank':
                    if aminoAcidTestedList:
                        # We might occasionally get some situations where there are some exons and some amino acids - handle it here
                        if aminoAcidTestedList[place] == []:
                            if geneTestedList[place][0] in equivocalGenes or geneTestedList[place] == equivocalGenes:
                                equiIndex = equivocalGenes.index(geneTestedList[place][0])
                                equiExons = equivocalExons[equiIndex]
                                equis = equiExons.split(',')
                                for eexon in equiExons.split(','):
                                    negExons = []
                                    for negexon in range(0, len(exonTestedList[place])):
                                        negExons.append(str(exonTestedList[place][negexon]))
                                    if negExons:
                                        for negativeExon in negExons:
                                            if negativeExon == eexon or eexon in ['all exons targeted', 'full']:
                                                # If a certain exon is both negative AND equivocal, we want to remove it
                                                negExons.remove(negativeExon)
                                if negExons:
                                    exonTestedList[place] = negExons
                                else:
                                    exonTestedList[place] = []
                            if exonTestedList[place] == []:
                                continue
                            geneName = geneTestedList[place][0]
                            if len(geneName.split()) == 2:
                                if geneName.split()[1].replace('[', '').replace(']', '').isnumeric() and '[' in geneName.split()[1]:
                                    geneName = geneName.split()[0]
                                if geneName.endswith('.') or geneName.endswith(','):
                                    geneName = geneName[:-1]
                            if debug:
                                print('location 23')
                            foundAnything = True
                            geneList.append(geneName)
                            locationList.append('')
                            transcriptList.append('')
                            cdnaList.append('')
                            proteinList.append('')
                            alleleFrequencyList.append('')
                            dpList.append('')
                            for exon in range(0, len(exonTestedList[place])):
                                exonTestedList[place][exon] = str(exonTestedList[place][exon])
                                # If the exons are like "1-11" handle that here
                                if '-' in exonTestedList[place][exon]:
                                    firstNum = int(exonTestedList[place][exon].split('-')[0])
                                    secondNum = int(exonTestedList[place][exon].split('-')[1])
                                    exonTestedList[place][exon] = ', '.join(set(str(v) for v in range(firstNum, secondNum + 1)))
                                exonTestedList[place][exon] = exonTestedList[place][exon].replace('+', ', ')
                            exonList.append(', '.join(list(set(exonTestedList[place]))))
                            labelList.append('no variant found')
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
                            orderedDateList.append(ordered)
                            testApproveList.append(received)
                            aminoAcidRangeList.append('')
                            icdCodeList.append(icdC)
                            accessionList.append(accession)
                            physicianList.append(physician)
                            takenList.append(taken)
                            if not status:
                                statusList.append("normal")
                            else:
                                statusList.append(status)
                            fullTestList.append(pathReportFull)
                            specimenCodeList.append(specimenCode)
                            specimenTypeList.append(specimenType)
                            pdfLinkList.append(pdfLink)
                            pathologistList.append(pathologist)
                            continue

                        if geneTestedList[place][0] in equivocalGenes:
                            equiIndex = equivocalGenes.index(geneTestedList[place][0])
                            equiAAs = equivocalExons[equiIndex]
                            equiAAs = equiAAs.replace('+', ', ')
                            for AA in equiAAs.split(','):
                                negativeAAs = aminoAcidTestedList[place]
                                for negativeAA in negativeAAs:
                                    if AA == negativeAA or AA in ['all exons targeted', 'full']:
                                        negativeAAs.remove(negativeAA)
                                aminoAcidTestedList[place] = negativeAAs
                        # If every result was equivocal, just continue.
                        if not aminoAcidTestedList:
                            continue
                        geneName = geneTestedList[place][0]
                        if len(geneName.split()) == 2:
                            if geneName.split()[1].replace('[', '').replace(']', '').isnumeric() and '[' in geneName.split()[1]:
                                geneName = geneName.split()[0]
                            if geneName.endswith('.') or geneName.endswith(','):
                                geneName = geneName[:-1]
                        if debug:
                            print('location 24')
                        foundAnything = True
                        geneList.append(geneName)
                        locationList.append('')
                        transcriptList.append('')
                        cdnaList.append('')
                        notFoundProteins = []
                        notFoundAminoAcids = []
                        # We sometimes capture stuff like "T790A". Let's put them in the protein column!
                        # NOTE: IT WAS REQUESTED ON CLIN-1181 TO NOT INCLUDE PROTEINS
                        for candidateAA in aminoAcidTestedList[place]:
                            if not candidateAA.replace('-', '').isnumeric():
                                notFoundProteins.append(candidateAA)
                                notFoundAminoAcids.append(candidateAA)
                            else:
                                notFoundAminoAcids.append(candidateAA)
                        if notFoundProteins:
                            #proteinList.append(', '.join(notFoundProteins))
                            proteinList.append('')
                        else:
                            proteinList.append('')
                        if notFoundAminoAcids:
                            aminoAcidRangeList.append(', '.join(notFoundAminoAcids))
                        else:
                            aminoAcidRangeList.append('')
                        alleleFrequencyList.append('')
                        dpList.append('')
                        exonList.append('')
                        labelList.append('no variant found')
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
                        orderedDateList.append(ordered)
                        testApproveList.append(received)
                        icdCodeList.append(icdC)
                        accessionList.append(accession)
                        physicianList.append(physician)
                        takenList.append(taken)
                        if not status:
                            statusList.append("normal")
                        else:
                            statusList.append(status)
                        fullTestList.append(pathReportFull)
                        specimenCodeList.append(specimenCode)
                        specimenTypeList.append(specimenType)
                        pdfLinkList.append(pdfLink)
                        pathologistList.append(pathologist)
                    else:
                        if geneTestedList[place][0] in equivocalGenes or geneTestedList[place] == equivocalGenes:
                            equiIndex = equivocalGenes.index(geneTestedList[place][0])
                            equiExons = equivocalExons[equiIndex]
                            equis = equiExons.split(',')
                            for eexon in equiExons.split(','):
                                negExons = []
                                for negexon in range(0, len(exonTestedList[place])):
                                    negExons.append(str(exonTestedList[place][negexon]))
                                if negExons:
                                    for negativeExon in negExons:
                                        if negativeExon == eexon or eexon in ['all exons targeted', 'full']:
                                            # If a certain exon is both negative AND equivocal, we want to remove it
                                            negExons.remove(negativeExon)
                            if negExons:
                                exonTestedList[place] = negExons
                            else:
                                exonTestedList[place] = []
                        if exonTestedList[place] == []:
                            continue
                        geneName = geneTestedList[place][0]
                        if len(geneName.split()) == 2:
                            if geneName.split()[1].replace('[', '').replace(']', '').isnumeric() and '[' in geneName.split()[1]:
                                geneName = geneName.split()[0]
                            if geneName.endswith('.') or geneName.endswith(','):
                                geneName = geneName[:-1]
                        if debug:
                            print('location 25')
                        foundAnything = True
                        geneList.append(geneName)
                        locationList.append('')
                        transcriptList.append('')
                        cdnaList.append('')
                        proteinList.append('')
                        alleleFrequencyList.append('')
                        dpList.append('')
                        for exon in range(0, len(exonTestedList[place])):
                            exonTestedList[place][exon] = str(exonTestedList[place][exon])
                            # If the exons are like "1-11" handle that here
                            if '-' in exonTestedList[place][exon]:
                                firstNum = int(exonTestedList[place][exon].split('-')[0])
                                secondNum = int(exonTestedList[place][exon].split('-')[1])
                                exonTestedList[place][exon] = ', '.join(set(str(v) for v in range(firstNum, secondNum+1)))
                            exonTestedList[place][exon] = exonTestedList[place][exon].replace('+', ', ')
                        exonList.append(', '.join(list(set(exonTestedList[place]))))
                        labelList.append('no variant found')
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
                        orderedDateList.append(ordered)
                        testApproveList.append(received)
                        aminoAcidRangeList.append('')
                        icdCodeList.append(icdC)
                        accessionList.append(accession)
                        physicianList.append(physician)
                        takenList.append(taken)
                        if not status:
                            statusList.append("normal")
                        else:
                            statusList.append(status)
                        fullTestList.append(pathReportFull)
                        specimenCodeList.append(specimenCode)
                        specimenTypeList.append(specimenType)
                        pdfLinkList.append(pdfLink)
                        pathologistList.append(pathologist)
            for gene in range(0, len(equivocalGenes)):
                geneName = equivocalGenes[gene]
                if len(geneName.split()) == 2:
                    if geneName.split()[1].replace('[', '').replace(']', '').isnumeric() and '[' in geneName.split()[1]:
                        geneName = geneName.split()[0]
                    if geneName.endswith('.') or geneName.endswith(','):
                        geneName = geneName[:-1]
                if debug:
                    print('location 26')
                foundAnything = True
                geneList.append(geneName)
                if len(equivocalLocations) > 0:
                    if equivocalLocations[gene]:
                        locationList.append(equivocalLocations[gene])
                else:
                    locationList.append('')
                transcriptList.append('')
                cdnaList.append('')
                alleleFrequencyList.append('')
                labelList.append('equivocal - low DP')
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
                orderedDateList.append(ordered)
                testApproveList.append(received)
                icdCodeList.append(icdC)
                accessionList.append(accession)
                physicianList.append(physician)
                takenList.append(taken)
                if not status:
                    statusList.append("normal")
                else:
                    statusList.append(status)
                fullTestList.append(pathReportFull)
                specimenCodeList.append(specimenCode)
                specimenTypeList.append(specimenType)
                pdfLinkList.append(pdfLink)
                pathologistList.append(pathologist)
                equiExons = []
                equiAAs = []
                equiProts = []
                equiDPs = []
                # Assuming that AA ranges have a '-', exons don't, and proteins have letters
                for geneBit in equivocalExons[gene].split(','):
                    geneBit = geneBit.strip()
                    if not (geneBit.replace('-', '').replace(',', '').replace(' ','').isnumeric() or geneBit in ['full', 'multiple regions'] or geneBit.endswith('x')):
                        equiProts.append(geneBit)
                    elif '-' in geneBit:
                        equiAAs.append(geneBit)
                    elif geneBit.endswith('x'):
                        geneBit = geneBit[:-1]
                        equiDPs.append(geneBit)
                    else:
                        equiExons.append(geneBit)
                if equiAAs:
                    aminoAcidRangeList.append(','.join(equiAAs))
                else:
                    aminoAcidRangeList.append('')
                if equiExons:
                    exonList.append(','.join(equiExons))
                else:
                    exonList.append('')
                if equiProts:
                    proteinList.append(','.join(equiProts))
                else:
                    proteinList.append('')
                if equiDPs:
                    dpList.append(','.join(equiDPs))
                else:
                    dpList.append('')

            #if 'cannot be excluded' in pathReport:
            #    if equivocalGenes == []:
            #        print(pathReport)
            #        print('')
            equivocalExons = []
            equivocalGenes = []

        #if testType in panelTests:
        #    print(pathReportFull)
        #    input()
        if checkMeEnd:

            print(geneList)
            print(exonList)
            print(proteinList[-100:])
            print(aminoAcidRangeList[-20:])
            print(labelList[-20:])
            print(testTypeList[-20:])
            #print(testsWithPanelsList[-1])
            input()
        if not len(geneList) == len(exonList) == len(proteinList) == len(aminoAcidRangeList) == len(labelList):
            print(len(geneList))
            print(len(exonList))
            print(len(proteinList))
            print(len(aminoAcidRangeList))
            print(len(labelList))
            print('')
            print(geneList[-200:])
            print(exonList[-200:])
            print(proteinList[-200:])
            print(aminoAcidRangeList[-200:])
            print(labelList[-200:])
            print(pathReport)
            print('')
            print(geneChunk)
            print(exonChunk)
            print(aminoAcidTestedChunk)
            print(geneTestedList)
            print(exonTestedList)
            print(aminoAcidTestedList)
            print(aminoacidChunk)
            input()
        aminoAcidTestedList = []
        aminoAcidChunk = []
        # print(x)

listOfPs = []
listOfCs = []
# If we have any post-hoc stuff to do, do it here
for pos in range(0, len(reportIdList)):
    if geneList[pos].endswith(',') or geneList[pos].endswith('.') or geneList[pos].endswith('*'):
        geneList[pos] = geneList[pos][:-1]
    # First, remove any rows that are just lists
    if ''.join(specimenTypeList[pos]).replace(',', '') == '':
        specimenTypeList[pos] = ''
    if ''.join(specimenCodeList[pos]).replace(',', '') == '':
        specimenCodeList[pos] = ''
    if ''.join(proteinList[pos]).replace(',','') == '':
        proteinList[pos] = ''
    # Eliminate duplicates in exon
    if len(exonList[pos]) > 1:
        exonL = exonList[pos].split(',')
        while "" in exonL:
            exonL.remove("")
        exonList[pos] = ', '.join(list(dict.fromkeys(exonL)))
    # This handles if they have the p. and c. in a list
    if ';' in cdnaList[pos] and ';' in proteinList[pos]:
        listOfPs = proteinList[pos].replace('p.[', '').replace(']','').split(';')
        listOfCs = cdnaList[pos].replace('c.[', '').replace(']', '').split(';')
        cdnaList[pos] = 'c.' + listOfCs[0]
        proteinList[pos] = 'p.' + listOfPs[0]
    elif ';' in cdnaList[pos] and ';' not in proteinList[pos]:
        listOfCs = cdnaList[pos].replace('c.[', '').replace(']', '').split(';')
        cdnaList[pos] = 'c.' + listOfCs[0]
        listOfPs = []
        for y in range(0, len(listOfCs)):
            listOfPs.append(proteinList[pos])
    # Sometimes there's a weird separation in the locations. We'll make two duplicate rows and eliminate them later
    if pos < len(reportIdList):
        if locationList[pos].endswith(':'):
            if locationList[pos+1].isnumeric():
                locationList[pos] = locationList[pos] + locationList[pos+1]
                locationList[pos+1] = locationList[pos]
    # This one's for the protein/amino acid separations
    if pos > 0:
        if geneList[pos] == geneList[pos-1] and reportIdList[pos] == reportIdList[pos-1] and (aminoAcidRangeList[pos] == '' and aminoAcidRangeList[pos-1] != '')\
                and (proteinList[pos] != '' and proteinList[pos-1] == '') and labelList[pos] == labelList[pos-1]:
            proteinList[pos-1] = proteinList[pos]
            aminoAcidRangeList[pos] = aminoAcidRangeList[pos-1]
        elif geneList[pos] == geneList[pos - 1] and reportIdList[pos] == reportIdList[pos - 1] and (aminoAcidRangeList[pos-1] == '' and aminoAcidRangeList[pos] != '') \
                and (proteinList[pos - 1] != '' and proteinList[pos] == '') and labelList[pos] == labelList[pos-1]:
            proteinList[pos] = proteinList[pos - 1]
            aminoAcidRangeList[pos - 1] = aminoAcidRangeList[pos]
    # This one's for fixing BRAF tests:
    if testTypeList[pos] == 'BRAF Gene Mutation Analysis' and 'negative - no coding variants detected in the targeted regions tested' in fullTestList[pos]:
        geneList[pos] = 'braf'
        labelList[pos] = 'negative'
        statusList[pos] = 'normal'
        aminoAcidRangeList[pos] = '439-472, 581-606'
        proteinList[pos] = ''
    if len(exonList[pos]) > 0 and 'equivocal' in labelList[pos]:
        exons = exonList[pos].split(',')
        goodExons = exons.copy()
        for ex in exons:
            goodExons.remove(ex)
            goodExons.append(ex.strip())
        exons = goodExons
        AAs = aminoAcidRangeList[pos]
        AAs = AAs.split(',')
        goodAAs = AAs.copy()
        for AA in AAs:
            goodAAs.remove(AA)
            goodAAs.append(AA.strip())
        for ex in exons:
            if ex.isnumeric():
                if int(ex) > 100:
                    exons.remove(ex)
                    AAs.append(ex)
        while '' in AAs:
            AAs.remove('')
        exonList[pos] = ', '.join(exons)
        aminoAcidRangeList[pos] = ', '.join(AAs)

    # This is for clearing up anything that's not '.p' if there's a '.c'
    if cdnaList[pos].startswith('c.') and not proteinList[pos].startswith('p.') and not proteinList[pos].startswith('promoter'):
        proteinList[pos] = ''
    # This is for adding any missing values for the sample type
    if specimenTypeList[pos] == '':
        specimenTypeList[pos] = 'tissue'
    # Eliminate parenthases from proteins
    if '(' in proteinList[pos]:
        proteinList[pos] = proteinList[pos].replace('(','').replace(')','')
    # Sometimes there are multiple rows with 'variant not found's
    if pos > 1:
        if reportIdList[pos] == reportIdList[pos-1] and geneList[pos] == geneList[pos-1] and labelList[pos] == 'no variant found' and labelList[pos-1] == 'no variant found':
            if aminoAcidRangeList[pos] != '':
                aminoAcidRangeList[pos-1] = str(aminoAcidRangeList[pos-1]) + ', ' + str(aminoAcidRangeList[pos])
                aminoAcidRangeList[pos] = aminoAcidRangeList[pos-1]
            if exonList[pos] != '' and exonList[pos-1] != '':
                exonList[pos-1] = str(exonList[pos-1]) + ', ' + str(exonList[pos])
                exonList[pos] = exonList[pos-1]
    # There is some gene mapping to do
    if geneList[pos] == 'usaf1':
        geneList[pos] = "u2af1"
    if geneList[pos] == 'etv6/tel':
        geneList[pos] = 'etv6'
    if geneList[pos] == 'tp536' or geneList[pos] == 'tp5366':
        geneList[pos] = 'tp53'
    if geneList[pos] == 'cdkn2a1':
        geneList[pos] = 'cdkn2a'
    if geneList[pos] == 'ezhe':
        geneList[pos] = 'ezh2'
    if geneList[pos] == 'nras1':
        geneList[pos] = 'nras'
    if geneList[pos] == 'smad':
        geneList[pos] = 'smad4'
    if geneList[pos] == 're':
        geneList[pos] = 'ret'
    # If we have any situations where there's no gene but a location, then delete that row. We'll do it by making it a duplicate
    if pos < len(reportIdList)-1:
        if geneList[pos] == '' and (locationList[pos] != '' or transcriptList[pos] != '' or geneList[pos] != ''  or cdnaList[pos] != '' or proteinList[pos] != ''):
            geneList[pos] = geneList[pos + 1]
            locationList[pos] = locationList[pos + 1]
            transcriptList[pos] = transcriptList[pos + 1]
            cdnaList[pos] = cdnaList[pos + 1]
            proteinList[pos] = proteinList[pos + 1]
            aminoAcidRangeList[pos] = aminoAcidRangeList[pos + 1]
            alleleFrequencyList[pos] = alleleFrequencyList[pos + 1]
            dpList[pos] = dpList[pos + 1]
            exonList[pos] = exonList[pos + 1]
            firstNameList[pos] = firstNameList[pos + 1]
            middleNameList[pos] = middleNameList[pos + 1]
            lastNameList[pos] = lastNameList[pos + 1]
            jrSrList[pos] = jrSrList[pos + 1]
            reportIdList[pos] = reportIdList[pos + 1]
            healthOrgList[pos] = healthOrgList[pos + 1]
            testTypeList[pos] = testTypeList[pos + 1]
            sourceList[pos] = sourceList[pos + 1]
            MRNList[pos] = MRNList[pos + 1]
            DOBList[pos] = DOBList[pos + 1]
            genderList[pos] = genderList[pos + 1]
            testReportedDateList[pos] = testReportedDateList[pos + 1]
            testApproveList[pos] = testApproveList[pos + 1]
            icdCodeList[pos] = icdCodeList[pos + 1]
            accessionList[pos] = accessionList[pos + 1]
            physicianList[pos] = physicianList[pos + 1]
            takenList[pos] = takenList[pos + 1]
            statusList[pos] = statusList[pos + 1]
            specimenCodeList[pos] = specimenCodeList[pos + 1]
            specimenTypeList[pos] = specimenTypeList[pos + 1]
            pdfLinkList[pos] = pdfLinkList[pos + 1]
            pathologistList[pos] = pathologistList[pos + 1]
            fullTestList[pos] = fullTestList[pos + 1]
            labelList[pos] = labelList[pos + 1]
        else:
            if geneList[pos] == '' and (locationList[pos] != '' or transcriptList[pos] != '' or geneList[pos] != '' or cdnaList[pos] != '' or proteinList[pos] != ''):
                geneList[pos] = geneList[pos - 1]
                locationList[pos] = locationList[pos - 1]
                transcriptList[pos] = transcriptList[pos - 1]
                cdnaList[pos] = cdnaList[pos - 1]
                proteinList[pos] = proteinList[pos - 1]
                aminoAcidRangeList[pos] = aminoAcidRangeList[pos - 1]
                alleleFrequencyList[pos] = alleleFrequencyList[pos - 1]
                dpList[pos] = dpList[pos - 1]
                exonList[pos] = exonList[pos - 1]
                firstNameList[pos] = firstNameList[pos - 1]
                middleNameList[pos] = middleNameList[pos - 1]
                lastNameList[pos] = lastNameList[pos - 1]
                jrSrList[pos] = jrSrList[pos - 1]
                reportIdList[pos] = reportIdList[pos - 1]
                healthOrgList[pos] = healthOrgList[pos - 1]
                testTypeList[pos] = testTypeList[pos - 1]
                sourceList[pos] = sourceList[pos - 1]
                MRNList[pos] = MRNList[pos - 1]
                DOBList[pos] = DOBList[pos - 1]
                genderList[pos] = genderList[pos - 1]
                testReportedDateList[pos] = testReportedDateList[pos - 1]
                testApproveList[pos] = testApproveList[pos - 1]
                icdCodeList[pos] = icdCodeList[pos - 1]
                accessionList[pos] = accessionList[pos - 1]
                physicianList[pos] = physicianList[pos - 1]
                takenList[pos] = takenList[pos - 1]
                statusList[pos] = statusList[pos - 1]
                specimenCodeList[pos] = specimenCodeList[pos - 1]
                specimenTypeList[pos] = specimenTypeList[pos - 1]
                pdfLinkList[pos] = pdfLinkList[pos - 1]
                pathologistList[pos] = pathologistList[pos - 1]
                fullTestList[pos] = fullTestList[pos - 1]
                labelList[pos] = labelList[pos - 1]

# This is to split up any c.s and p.s with multiple entries. Bizarre.
if listOfPs:
    for x in (1, len(listOfPs)-1):
        geneList.append(geneList[pos])
        locationList.append(locationList[pos])
        transcriptList.append(transcriptList[pos])
        cdnaList.append('c.' + listOfCs[x].strip())
        proteinList.append('p.' + listOfPs[x].strip())
        aminoAcidRangeList.append(aminoAcidRangeList[pos])
        alleleFrequencyList.append(alleleFrequencyList[pos])
        dpList.append(dpList[pos])
        exonList.append(exonList[pos])
        firstNameList.append(firstNameList[pos])
        middleNameList.append(middleNameList[pos])
        lastNameList.append(lastNameList[pos])
        jrSrList.append(jrSrList[pos])
        reportIdList.append(reportIdList[pos])
        healthOrgList.append(healthOrgList[pos])
        testTypeList.append(testTypeList[pos])
        sourceList.append(sourceList[pos])
        MRNList.append(MRNList[pos])
        DOBList.append(DOBList[pos])
        genderList.append(genderList[pos])
        testReportedDateList.append(testReportedDateList[pos])
        testApproveList.append(testApproveList[pos])
        icdCodeList.append(icdCodeList[pos])
        accessionList.append(accessionList[pos])
        physicianList.append(physicianList[pos])
        takenList.append(takenList[pos])
        statusList.append(statusList[pos])
        specimenCodeList.append(specimenCodeList[pos])
        specimenTypeList.append(specimenTypeList[pos])
        pdfLinkList.append(pdfLinkList[pos])
        pathologistList.append(pathologistList[pos])
        fullTestList.append(fullTestList[pos])
        labelList.append(labelList[pos])

if saveResults:

    panelsDataFrame = pd.DataFrame(list(zip(reportIdList, accessionList, healthOrgList, firstNameList, middleNameList, lastNameList, jrSrList,
                                                testTypeList, sourceList, physicianList, DOBList, MRNList, genderList, testReportedDateList, takenList, testApproveList, orderedDateList,
                                            pathologistList, geneList, locationList, transcriptList, cdnaList, proteinList, aminoAcidRangeList,
                                            alleleFrequencyList, dpList, exonList, labelList, icdCodeList, statusList, specimenCodeList, specimenTypeList, pdfLinkList)),
                                                                columns=['hl7 record id', 'reportId', 'healthOrg', 'firstName', 'middleName',
                                                                         'lastName', 'Jr/Sr', 'testType', 'source', 'physician', 'DOB', 'MRN',
                                                                         'gender', 'testReportedDate', 'sampleCollectionDate', 'approveDate', 'orderedDate', 'pathologist', 'gene', 'location',
                                                                         'transcript', 'cdna', 'protein', 'amino acid range',
                                                                         'alleleFrequency', 'dp', 'exon', 'label', 'icd code', 'status', 'specimen code', 'specimen type', 'pdf link'])


    fullPanelsDataFrame = pd.DataFrame(list(zip(reportIdList, accessionList, healthOrgList, firstNameList, middleNameList, lastNameList, jrSrList,
                                                testTypeList, sourceList, physicianList, DOBList, MRNList, genderList, testReportedDateList, takenList, testApproveList, orderedDateList,
                                            pathologistList, geneList, locationList, transcriptList, cdnaList, proteinList, aminoAcidRangeList,
                                            alleleFrequencyList, dpList, exonList, labelList, icdCodeList, statusList, specimenCodeList, specimenTypeList, pdfLinkList, fullTestList)),
                                                                columns=['hl7 record id', 'reportId', 'healthOrg', 'firstName', 'middleName',
                                                                         'lastName', 'Jr/Sr', 'testType', 'source', 'physician', 'DOB', 'MRN',
                                                                         'gender', 'testReportedDate', 'sampleCollectionDate', 'approveDate', 'orderedDate', 'pathologist', 'gene', 'location',
                                                                         'transcript', 'cdna', 'protein', 'amino acid range',
                                                                         'alleleFrequency', 'dp', 'exon', 'label', 'icd code', 'status', 'specimen code', 'specimen type', 'pdf link', 'full text'])


    fusionPanelsDataFrame = pd.DataFrame(list(zip(fusionreportIdList, fusionsourceList, fusionhealthOrgList, fusionMRNList, fusionfirstNameList, fusionmiddleNameList, fusionlastNameList, fusionjrSrList, fusionDOBList, fusiongenderList, \
            fusiontestTypeList, fusiontestReportedDateList, fusiontestApproveList, fusionList, fusioncategoryList, fusionreadsList, fusionuniqueMolList, fusionStartSitesList, fusionbreakpointsList, fusiondirectionList, fusionexonList, fusiontranscriptList,\
            fusionicdCodeList, fusionaccessionList, fusionphysicianList, fusiontakenList, fusionstatusList, fusionfullTestList, fusionspecimenCodeList, fusionspecimenTypeList, fusionlabelList, \
            fusionpdfLinkList, fusionpathologistList)), columns=['report Id', 'source', 'healthOrg', 'MRN', 'First Name', 'Middle Name', 'Last Name', 'Jr/Sr', 'DOB', 'gender', 'test type',
                                                                 'reported date', 'sample collection date', 'fusion', 'category', 'reads', 'unique molecules', 'start sites', 'breakpoints', 'direction', 'exons', 'transcript',
                                                                 'icd cdoes', 'accession', 'physician', 'taken', 'status', 'full text', 'specimen code', 'specimen type', 'label', 'pdf', 'pathologist'])

    # No duplicate rows!
    #panelsDataFrame = panelsDataFrame.drop_duplicates()
    panelsDataFrame = panelsDataFrame.drop(panelsDataFrame[(panelsDataFrame['gene'] == '') & (panelsDataFrame['location'] != '') & (panelsDataFrame['transcript'] != '')].index)
    #panelsDataFrame = panelsDataFrame.drop(panelsDataFrame[(panelsDataFrame['label'] == 'no variant found') & (panelsDataFrame['amino acid range'] == '') & (panelsDataFrame['exon'] == '')].index)
    fullPanelsDataFrame = fullPanelsDataFrame.drop(fullPanelsDataFrame[(fullPanelsDataFrame['gene'] == '') & (fullPanelsDataFrame['location'] != '') & (fullPanelsDataFrame['transcript'] != '')].index)
    #fullPanelsDataFrame = fullPanelsDataFrame.drop(fullPanelsDataFrame[(fullPanelsDataFrame['label'] == 'no variant found') & (fullPanelsDataFrame['amino acid range'] == '') & (fullPanelsDataFrame['exon'] == '')].index)
    panelsDataFrame.to_csv("~/Desktop/LatestNLP/Semi-Structured_Results/PanelsUpdated.csv", index=False)
    fullPanelsDataFrame.to_csv("~/Desktop/LatestNLP/Semi-Structured_Results/PanelsUpdatedFull.csv", index=False)
    #df = pd.read_csv("~/Desktop/DeleteMeSoon/PanelsUpdatedFull.csv", low_memory=False)
    df = pd.read_csv("~/Desktop/LatestNLP/Semi-Structured_Results/PanelsUpdatedFull.csv", low_memory=False)
    df = df.drop_duplicates(keep='first')
    df.reset_index()

    os.remove("/Users/bholmes/Desktop/LatestNLP/Semi-Structured_Results/PanelsUpdatedFull.csv")
    os.remove("/Users/bholmes/Desktop/LatestNLP/Semi-Structured_Results/PanelsUpdated.csv")

    df.to_csv("~/Desktop/LatestNLP/Semi-Structured_Results/PanelsResults.csv", index=False)
    fusionPanelsDataFrame.to_csv("~/Desktop/LatestNLP/Semi-Structured_Results/FusionsResults.csv", index=False)

    # Let's also get the dropped tests
    droppedPanels = pd.DataFrame(list(zip(panelsDropped, panelIdsDropped)), columns=['dropped panels', 'dropped panel ids'])
    droppedPanels.to_csv("~/Desktop/LatestNLP/Semi-Structured_Results/DroppedPanels.csv", index=False)

    for i in testsWithPanelsList:
        if i not in reportIdList and i not in fusionreportIdList:
            print(i)
