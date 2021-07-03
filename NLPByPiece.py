import pandas as pd
import numpy as np
# For regex
import re
import gc
from datetime import datetime
from NumWords import text2int
from MetaMapForLots import metamapstringoutput
from random import random
from random import seed
import random

# This is for matching misspelled section headers.
# You should ALSO make sure 'python-levenshtein' is installed.
import regex

# Right, so we'll process these reports in chunks. Henry Ford tends to give us reports in a very standardized
# format, so we'll process the bits we can with pattern matching, then put the rest through metamap or something.

# Tally ho
df = pd.read_csv("~/Desktop/DeleteMeSoon/combined.csv", low_memory=False)
# df = pd.read_csv("~/Desktop/DeleteMeSoon/MASample.csv", low_memory=False)

# The list of tests we're pulling from
panelTests = ['Lung Adenocarcinoma Panel', 'Hematolymphoid Sequencing Panel (51 genes)',
                'TruSeq 48 Gene Cancer Panel', 'Lymphoid neoplasm panel', 'Colorectal Cancer Panel',
                'Hematolymphoid Sequencing Panel (54 genes)', 'Melanoma Panel', 'JAK2 Mutational Analysis',
                'Gastrointestinal Stromal Tumors (GIST) Panel', 'Myelodysplastic Syndrome (MDS) Panel',
                'Molecular Pathology and Genomic Test', 'BRAF Gene Mutation Analysis',
                'Myeloproliferative Neoplasm (MPN) Panel', 'EGFR TKI Sensitivity and Resistance Panel',
                'De novo AML panel', 'Molecular Studies Report', 'KRAS Gene Mutation Analysis',
                'FLT3, AML', 'NPM1 Mutational Analysis', 'Custom Hereditary Cancer Risk Test',
                'IDH1 Mutation Detection Assay', 'BRCA1/2 Sequencing and Common Deletions / Duplications']

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
DOBs = df['DOB']
genders = df['gender']
# ### The date, too, is best pulled from the path report
testOrderDates = pd.to_datetime(df['testOrderDate'], format='%Y%m%d%M%S')

# We'll want to save a list per every result for all the structured fields, along with the parts of the result that
# we get from the panels.
reportIdList, sourceList, healthOrgList, MRNList, firstNameList, middleNameList, lastNameList, jrSrList, DOBList, genderList, \
        testTypeList, testReportedDateList, testApproveList, geneList, locationList, transcriptList, cdnaList, proteinList,\
        dpList, exonList, alleleFrequencyList, labelList, aminoAcidRangeList, icdCodeList, accessionList, \
        physicianList, takenList, statusList, fullTestList, specimenCodeList, specimenTypeList, pdfLinkList, pathologistList, orderedDateList = ([] for i in range(34))

# This extra one is for saving gene/exon coding regions from reports.
geneTestedList = []
exonTestedList = []
aminoAcidTestedList = []

# THIS IS FOR FINDING REPORTS
biomarkersForPhizer = []
biomarkerTestsForPhizer = []

# We want to filter out duplicates
reportIdsSoFar = []

# For catching all the kinds
allSectionLists = []

namesAndSources = set()
allSources = set()

# DELETE - for results panel.
fishResultsWholeText = []
fishResultsSectionPullOut = []
fishResultsNonBioInfo = []
fishResultsOnlyBio = []
fishResultsBio1 = []
fishResultsBio2 = []
fishResultsMetaMap = []
fishResultsReportId = []
fishResultsHealthOrg = []
fishResultsFirstName = []
fishResultsMiddleName = []
fishResultsLastName = []
fishResultsTestType = []
fishResultsSource = []
fishResultsPhysician = []
fishResultsDOB = []
fishResultsMRN = []
fishResultsAccession = []
fishResultsGender = []
fishResultstestReportedDate = []
fishResultsSampleCollectionDate = []

fishTestTypes = []

fishCounter = 0

## DELETE - FOR SAMPLING
listOfReportIds = []
listOfReportNots = []

sampleReportIdList = []
sampleHealthOrgList = []
sampleFirstNameList = []
sampleMiddleNameList = []
sampleLastNameList = []
sampleJrSrNameList = []
sampleTestTypeList = []
sampleSourceList = []
samplePhysicianList = []
sampleDOBList = []
sampleMRNList = []
sampleAccessionList = []
sampleGenderList = []
sampleTestReportedDateList = []
sampleTakenList = []
sampleGeneList = []
sampleLocationList = []
sampleTranscriptList = []
sampleCdnaList = []
sampleProteinList = []
sampleAminoAcidList = []
sampleAlleleList = []
sampleDPList = []
sampleExonList = []
sampleLabelList = []
sampleICDList = []
sampleStatusList = []
sampleSpecimenCodeList = []
sampleSpecimenTypeList = []
sampleFullTextList = []
lungnumber = 200
truseqnumber = 27
brcaTests = []
nonoList = [20193450055706,20192070125429,20192140096907,20192180136131,20192200114162,20191910120849,20191930116697,20191930124437,
            20192490127512,5600009257587,20192540101703,20192550104028,20192560102455,20192590044351,20192610087396,20192610093655,5600009337119,20192660115769,20192680068773,
            20193440152412,20193440153140,20191970144977,20191980117076,20192000110737,20192000113856,20192040145720,20192040146199,5600008902040,20193370120776,20193020142720,
            20192960096086,20193300109963,20193300139454,20193330078060,20193080146859,20192970095028,20192470131046,20192530130260,20192550102530,20192880084235,20191990119278,
            20192040136473,20193510054156,20193120096492,20193250090913,20193250144266,20193500154908,20192400107266,20192700062520,20192740111500,5600009465805,20192340077799,
            5600006647536,5600006634561,5600006574720,5600006682637,5600006835479,5600006774516,5600007662611,5600007566834,5600007612830,5600007635672,5600005741001,5600005766897,
            5600005706299,5600005755232,5600005826302,5600005703886,5600005448139,5600006992032,5600006879979,5600005862130,5600005915416,5600005961733,5600006040034,5600006035955,
            5600006066916,5600006012611,5600006034321,5600006040569,5600005987991,5600007168858,5600006421133,5600007278874,5600007384108,5600007384099,5600007411565,5600007269437,
            5600006132410]



z = 0
line = 0

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

# For skipping reports
skipBool = False
skipNum = 163275
start = 0

# Every line of df['result'] is another unstructured report.
for reportLine in df['result']:

    if skipBool:
        if start < skipNum:
            start = start + 1
            line = line + 1
            continue

    if line % 100 == 0:
        print(str(line), ' of ', str(len(df['result'])))

    # If we don't handle space removal before, here's the place to do it.
    for i in range(0, len(reportLine)):
        reportLine[i] = reportLine[i].strip()

    # The hospital that did the report
    source = reportLine[0]

    namesAndSources.add(str(firstNames[line]) + " " + str(lastNames[line]) + " " + source)

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
    DOB = DOBs[line]
    try:
        date_time_obj = datetime.strptime(DOB, '%Y%m%d')
    except:
        pass
    try:
        date_time_obj = datetime.strptime(DOB, '%Y-%m-%d')
    except:
        pass
    DOB = date_time_obj.strftime('%m/%d/%Y')
    gender = genders[line]

    line = line + 1
    allSources.add(source)

    # Activate me to select a particular report!
#    if reportId != 5600005448320:
#        continue
#    else:
#        print('GIT IT')

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
        if testType.endswith('.'):
            testType = testType[:-1]

    # We're going to join the list together into a string, which we reserve the right to separate later. The
    # newline characters are preserved as pipes, in case that's useful.
    pathReport = '|'.join(reportLine)
    pathReportFull = '\n'.join(reportLine)
    pathReport = re.sub(' +', ' ', pathReport)
    pathReport = pathReport.lower()

    #if testType not in panelTests and not (testType.lower() == 'surgical pathology report' and (regex.findall('(?:gene exon / amino acid){s<=2}', \
    #                            pathReport) or regex.findall('(?:gene target region){s<=2}', pathReport))):
    #    print('dropped a ', testType)
    #    continue

    if 'brca' in pathReport:
        brcaTests.append(pathReportFull)

    # This is our marker to show that there is no panel result - if that's true, we'll have to add a blank
    # amino acid range for every marker we find.
    noPanel = False

    # This is the 'fast lane' to a variety of figures we might be interested in
    if reportIds[z] not in reportIdsSoFar:
        reportIdsSoFar.append(reportIds[z])
    z = z+1

    # This is where we get the date reported and MRN.
    reportedIndex = pathReport.index("reported:")
    date = pathReport[reportedIndex + 9:reportedIndex + 20].replace("|", '').replace("p", '').replace('r', '')
    date = date.strip()
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
    except:
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


     #Let's find the pathologist on the case - there can be multiple "***electronically signed out***s"
    foundim = False
    pathReportSplit =  pathReport.split("|")
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

    # We can go back and undo this step if we need to - I'm representing the entire
    # path report as one long string here, so I can divide it by sections. I'm not
    # using free spaces to represent new sections, because this isn't reliable. It
    # sometimes works, sometimes not.
    pathReport = pathReport.replace('|', ' ')

    # Also there are a few spelling mistakes that I don't want to miss
    pathReport = pathReport.replace('eoxn', 'exon')

    # THIS IS FOR FINDING REPORT TYPES
    #if 'akt1' in pathReport:
    #    biomarkersForPhizer.append('akt1')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'brca1' in pathReport:
    #    biomarkersForPhizer.append('brca1')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'brca2' in pathReport:
    #    biomarkersForPhizer.append('brca21')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'erbb21' in pathReport:
    #    biomarkersForPhizer.append('erbb21')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'her2' in pathReport:
    #    biomarkersForPhizer.append('her2')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'esr1' in pathReport:
    #    biomarkersForPhizer.append('esr1')
    #    biomarkerTestsForPhizer.append(testType)
    #if ' er ' in pathReport:
    #    biomarkersForPhizer.append('er')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'pd-l1' in pathReport:
    #    biomarkersForPhizer.append('pd-l1')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'pd-1' in pathReport:
    #    biomarkersForPhizer.append('pd-1')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'pgr' in pathReport:
    #    biomarkersForPhizer.append('pgr')
    #    biomarkerTestsForPhizer.append(testType)
    #if ' pr ' in pathReport:
    #    biomarkersForPhizer.append('pr')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'pms2' in pathReport:
    #    biomarkersForPhizer.append('pms2')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'pik3c1' in pathReport:
    #    biomarkersForPhizer.append('pik3c1')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'pten' in pathReport:
    #    biomarkersForPhizer.append('pten')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'tp53' in pathReport:
    #    biomarkersForPhizer.append('tp53')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'tmb' in pathReport:
    #    biomarkersForPhizer.append('tmb')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'msi' in pathReport:
    #    biomarkersForPhizer.append('msi')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'tumor mutational burden' in pathReport or 'tumor mutation burden' in pathReport:
    #    biomarkersForPhizer.append('tmb')
    #    biomarkerTestsForPhizer.append(testType)
    #if 'microsatellite instability' in pathReport:
    #    biomarkersForPhizer.append('msi')
    #    biomarkerTestsForPhizer.append(testType)


    # We're standardizing headers for pulling out later.
    if 'med: rec.' in pathReport:
        pathReport = pathReport.replace('med: rec.', 'med. rec.')

    # These are ICD codes. Easy to pull out!

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
        icdC = ', '.join(icdC)

    # If there's a reason the test failed, we want it - we ALSO don't want to do anything else.
    if ('not performed' in pathReport.replace('|', ' ') or 'quality matrix failed' in pathReport.replace('|', ' ')
        or 'quantity not sufficient for pcr analysis' in pathReport.replace('|', ' ') or 'cancelled at the request of the care provider.'\
            in pathReport.replace('|', '')) and testType in panelTests:
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

    equivocalGenes = []
    equivocalExons = []
    equivocalLocations = []
    gene = ''
    exon = []
    # First, and, hopefully, easiest, is we're gonna pull out the equivocal results.
    equiText = regex.findall('(?:content  gene exon\b){s<=2}', pathReport)
    if 'content. gene exon' in pathReport:
        equiText = regex.findall('(?:content. gene exon\b){s<=2}', pathReport)
    if 'content.  gene exon' in pathReport:
        equiText = regex.findall('(?:content.  gene exon\b){s<=2}', pathReport)
    if 'excluded in these regions.  gene exon' in pathReport:
        equiText = regex.findall('(?:excluded in these regions.  gene exon\b){s<=2}', pathReport)
    if 'excluded in these regions.  gene exon / (aa)' in pathReport:
        equiText = regex.findall('(?:excluded in these regions.  gene exon / (aa)\b){s<=2}', pathReport)
    if 'low coverage areas: gene exon' in pathReport:
        equiText = regex.findall('(?:low coverage areas: gene exon\b){s<=2}', pathReport)
    if equiText:
        equiPos = [m.start() for m in regex.finditer('(?:content  gene exon\b){s<=2}', pathReport)]
        if 'content. gene exon' in pathReport:
            equiPos = [m.start() for m in regex.finditer('(?:content. gene exon\b){s<=2}', pathReport)]
        if 'content.  gene exon' in pathReport:
            equiPos = [m.start() for m in regex.finditer('(?:content.  gene exon\b){s<=2}', pathReport)]
        if 'excluded in these regions.  gene exon' in pathReport:
            equiPos = [m.start() for m in regex.finditer('(?:excluded in these regions.  gene exon\b){s<=2}', pathReport)]
        if 'excluded in these regions.  gene exon / (aa)' in pathReport:
            equiPos = [m.start() for m in regex.finditer('(?:excluded in these regions.  gene exon / (aa)\b){s<=2}', pathReport)]
        if 'low coverage areas: gene exon' in pathReport:
            equiPos = [m.start() for m in regex.finditer('(?:low coverage areas: gene exon\b){s<=2}', pathReport)]
        equiPath = pathReport[equiPos[0]:]
        equiPath = equiPath.replace(';', ',')
        equiEnd = [m.start() for m in regex.finditer('(?:results-comments\b){s<=2}', equiPath)]
        equiPath = equiPath[:equiEnd[0]]
        equiList = equiPath.split()
        while "" in equiList:
            equiList.remove("")
        while equiList:
            # Some combination of these (and frequently all of them in order) are going to start us off!
            while equiList[0] in ['content', 'content.', 'gene', 'exon', '/', '(aa)', '(aa', 'excluded', 'in', 'these', 'regions', 'regions.']:
                if len(equiList) == 1:
                    equiList = []
                    break
                else:
                    equiList = equiList[1:]

            # If there's nothing there, it's over
            if not equiList:
                break

            # The gene is the first token
            gene = equiList[0]
            equiList = equiList[1:]

            # If there's nothing there, it's over
            if not equiList:
                break

            # It can be a list of exons, space-delimited or not. It can be 2, 3 , 2,3 , or 2+3. It can say
            # [gene] full to indicate that the entire gene is equivocal
            if equiList[0].replace(',', '').replace('+', '').replace('-', '').replace(';', '').isnumeric() \
                    or equiList[0] in ['full', 'partial'] \
                    or equiList[0] in [',', '+', '(aa', '(dp:', 'all', 'exon', 'exons', 'all', 'and', '(partial)', '(aa)', '/', '-', '(all'] \
                    or ('(' in equiList[0] and ')' in equiList[0]):
                while equiList[0].replace(',', '').replace('+', '').replace('-', '').replace(';', '').isnumeric() \
                        or equiList[0] in ['full', 'partial'] \
                        or equiList[0] in [',', '+', '(aa', '(dp:', 'all', 'exon', 'exons', 'all', 'and', '(partial)', '(aa)', '/', '-', '(all'] or \
                        ('(' in equiList[0] and ')' in equiList[0]):
                    if equiList[0].replace(',', '').replace('+', '').replace('-', '').isnumeric():
                        if equiList[0].endswith(','):
                            equiList[0] = equiList[0][:-1]
                        if '+' in equiList[0]:
                            exons = equiList[0].split()
                            equiList[0].split() == ''
                            for x in equiList[0]:
                                equiList[0] = equiList[0] + str(x) + ','
                            equiList[0] = equiList[0].replace('+', ',')
                        if ';' in equiList[0]:
                            equiList[0] = equiList[0].replace(';', ',')
                        if '-' in equiList[0]:
                            lower = equiList[0].split('-')[0]
                            upper = equiList[0].split('-')[1]
                            equiList[0] = ''
                            for x in range(int(lower), int(upper)+1):
                                equiList[0] = equiList[0] + str(x) + ','
                        if ',' in equiList[0]:
                            exons = equiList[0].split(',')
                            for ex in exons:
                                if ex and ex not in exons:
                                    exon.append(ex)
                        else:
                            exon.append(equiList[0])

                    # Sometimes after we're done putting in exons, we get AA ranges. If that's the case, we want to
                    # replace the exons with the AA list.
                    if len(equiList) > 1:
                        if equiList[1] in ['(aa', '(aa:']:
                            exon = []
                            equiList = equiList[1:]
                            equiList = equiList[1:]
                            while ')' not in equiList[0]:
                                if equiList[0].replace('-', '').replace(',', '').isnumeric():
                                    exon.append(equiList[0].replace('-', '').replace(',', ''))
                                    equiList = equiList[1:]
                                else:
                                    equiList = equiList[1:]
                            if equiList[0].replace('-', '').replace(')', '').isnumeric():
                                exon.append(equiList[0].replace(')', ''))

                    # We don't want to capture the dp
                    if equiList[0] in ['(dp:', '(dp']:
                        while ')' not in equiList[0]:
                            equiList = equiList[1:]

                    # This specific situation came up a lot? Don't know why. It would be '(aa cdkn2a'
                    if equiList[0] == '(aa' and equiList[1] == 'cdkn2a':
                        pass
                    elif equiList[0] in ['(aa', '(dp:']:
                        while ')' not in equiList[0]:
                            equiList = equiList[1:]

                    # For these two, we want to go until the second-to-last-token, since we always advance at the end
                    if len(equiList) > 2:
                        if equiList[0] == 'all' and equiList[1] in ['targeted', 'sequenced', 'exons'] and equiList[2] in ['exons', 'targeted', 'sequenced']:
                            exon.append('all exons targeted')
                            equiList = equiList[1:]
                            equiList = equiList[1:]
                        if equiList[0] == '(all' and equiList[3] == 'regions)':
                            equiList = equiList[1:]
                            equiList = equiList[1:]
                            equiList = equiList[1:]

                    if equiList[0] in ['full', 'partial', 'all']:
                        exon.append(equiList[0])

                    # if equiList[0] in ['exon', 'exons', 'and', '(partial)', '(aa)', '/', '-']:
                    #    equiList = equiList[1:]

                    if '(' in equiList[0] and ')' in equiList[0]:
                        equiList = equiList[1:]

                    # Here we advance tokens
                    equiList = equiList[1:]

                    for ex in range(0, len(exon)):
                        exon[ex] = str(exon[ex])

                    if not equiList:
                        break
                equivocalGenes.append(gene)
                equivocalExons.append(','.join(exon))
                gene = ''
                exon = []
                if not equiList:
                    break
            else:
                # print("BREAKING2")
                # print(equiList)
                # print(pathReport)
                # print('')
                equiList = []
                break

####
# Here we capture variants of equivocal genes - these are in low numbers, and are basically one-offs.
####

    if 'neoplastic cell content  genes:' in pathReport or 'neoplastic cell content. genes:' or\
            'low neoplastic cell content  gene' in pathReport or 'these genes. genes:' in pathReport or\
            'low neoplastic cell content. gene' in pathReport or 'neoplastic cell content genes:' in pathReport\
            or 'low neoplastic cell content.  gene' in pathReport:
        # Some have the REGION (we'll extract the exon)
        includesRegion = False
        # Some have amino acids (we'll extract those)
        includesAminoAcids = False
        # Some have gene (exon 3,4)
        includesMultiExons = False
        # Some have genes AND amino acides like: braf 2 (1-12)
        includesExonsAndAminoAcids = False
        equiText = regex.findall('(?:neoplastic cell content  genes:\b){s<=2}', pathReport)
        if not equiText:
            equiText = regex.findall('(?:neoplastic cell content  gene:\b){s<=2}', pathReport)
        if not equiText:
            equiText = regex.findall('(?:neoplastic cell content. genes:\b){s<=2}', pathReport)
        if not equiText:
            equiText = regex.findall('(?:neoplastic cell content  gene\b){s<=2}', pathReport)
        if not equiText:
            equiText = regex.findall('(?:neoplastic cell content. gene\b){s<=2}', pathReport)
        if not equiText:
            equiText = regex.findall('(?:these genes. genes:\b){s<=2}', pathReport)
        if not equiText:
            equiText = regex.findall('(?:neoplastic cell content genes:\b){s<=2}', pathReport)
        if not equiText:
            equiText = regex.findall('(?:neoplastic cell content.  gene:\b){s<=2}', pathReport)
        if equiText:
            equiPos = [m.start() for m in regex.finditer('(?:neoplastic cell content  genes:\b){s<=2}', pathReport)]
            if not equiPos:
                equiPos = [m.start() for m in regex.finditer('(?:neoplastic cell content  gene:\b){s<=2}', pathReport)]
            if not equiPos:
                equiPos = [m.start() for m in regex.finditer('(?:neoplastic cell content. genes:\b){s<=2}', pathReport)]
            if not equiPos:
                equiPos = [m.start() for m in regex.finditer('(?:neoplastic cell content  gene\b){s<=2}', pathReport)]
            if not equiPos:
                equiPos = [m.start() for m in regex.finditer('(?:neoplastic cell content. gene\b){s<=2}', pathReport)]
            if not equiPos:
                equiPos = [m.start() for m in regex.finditer('(?:neoplastic cell content.  gene\b){s<=2}', pathReport)]
            if not equiPos:
                equiPos = [m.start() for m in regex.finditer('(?:these genes. genes:\b){s<=2}', pathReport)]
            if not equiPos:
                equiPos = [m.start() for m in regex.finditer('(?:neoplastic cell content genes:\b){s<=2}', pathReport)]
            equiPath = pathReport[equiPos[0]:]
            equiEnd = [m.start() for m in regex.finditer('(?:results-comments\b){s<=2}', equiPath)]
            equiPath = equiPath[:equiEnd[0]]
            # I THINK we always want to split these!
            equiPath2 = re.sub(r'(?<=[,])(?=[^\s])', r' ', equiPath)
            equiPath = equiPath2
            equiList = equiPath.split()
            while '/' in equiList:
                equiList.remove('/')
            while "" in equiList:
                equiList.remove("")
            while equiList:
                # Some combination of these (and frequently all of them in order) are going to start us off!
                while equiList[0] in ['neoplastic', 'cell', 'content', 'content.', 'genes:', 'gene', 'these', 'genes.', 'gene:']:
                    if len(equiList) == 1:
                        equiList = []
                        break
                    else:
                        equiList = equiList[1:]

                if not equiList:
                    break

                if equiList[0] == 'exon' or equiList[0] == 'section':
                    break
                if equiList[0] == 'regions':
                    includesRegion = True
                    equiList = equiList[1:]
                    if equiList[0] == 'of':
                        includesRegion = False
                        equiList = equiList[1:]
                if equiList[0] == 'amino':
                    includesAminoAcids = True
                    equiList = equiList[1:]
                    equiList = equiList[1:]
                if equiList[0] == '(aa)':
                    includesExonsAndAminoAcids = True
                    equiList = equiList[1:]
                if len(equiList) > 1:
                    if equiList[1] == '(exon':
                        includesMultiExons = True

                if not equiList:
                    break

                # Handle the special cases
                if includesRegion:
                    if len(equiList[0].split('.')) < 2:
                        break
                    # if it has a region, it'll be like egfr4.chr7.55241677.55241708_tile_1.1
                    # We don't want the number, we ONLY want
                    genePart = equiList[0].split('.')[0]
                    if '_' in genePart:
                        genePart = genePart.split('_')[0]
                    else:
                        while genePart[-1].isdigit():
                            genePart = genePart[:-1]
                    equivocalGenes.append(genePart)
                    equivocalExons.append('')
                    locationPart = equiList[0].split('.')[1].replace('chr', '') + ":" + equiList[0].split('.')[2] + '-' + equiList[0].split('.')[3]
                    locationPart = locationPart.split("_")[0]
                    equivocalLocations.append(locationPart)
                    #equivocalExons.append(equiList[0].split('.')[1].replace('chr', ''))
                elif includesExonsAndAminoAcids:
                    equivocalGenes.append(equiList[0])
                    equiList = equiList[1:]
                    # Anything outside of parenthases is an exon, like nras 2 (1-19)
                    while '(' not in equiList[0] and equiList:
                        equiList = equiList[1:]
                    # We might have a few ranges to capture, here. The last one will have no comma
                    while ')' not in equiList[0] or ',' in equiList[0]:
                        if ')' in equiList[0]:
                            exon.append(equiList[0].replace(',', '').replace('(', '').replace(')', ''))
                        else:
                            equiList = equiList[1:]
                        if ')' in equiList[0] and ',' not in equiList[0]:
                            exon.append(equiList[0].replace(',', '').replace('(', '').replace(')', ''))
                            equivocalExons.append(','.join(exon))
                elif includesAminoAcids:
                    exon = []
                    equivocalGenes.append(equiList[0])
                    equiList = equiList[1:]
                    # While this token and the next are both ranges, append them.
                    if len(equiList) > 1:
                        while len(equiList) > 1 and equiList[1].replace('-', '').replace(',', '').isnumeric()\
                                and equiList[0].replace('-', '').replace(',', '').isnumeric():
                            exon.append(equiList[0].replace(',', ''))
                            equiList = equiList[1:]
                    # Once that's done, append the current range if it's numeric
                    if equiList[0].replace('-', '').replace(',', '').isnumeric():
                        exon.append(equiList[0])
                    equivocalExons.append(','.join(exon))
                elif includesMultiExons:
                    exon = []
                    equivocalGenes.append(equiList[0])
                    equiList = equiList[1:]
                    equiList = equiList[1:]
                    while equiList[0].replace(',', '').isnumeric():
                        exon.append(equiList[0].replace(',', ''))
                        equiList = equiList[1:]
                    if equiList[0].replace(')', '').isnumeric():
                        exon.append(equiList[0].replace(')', ''))
                    equivocalExons.append(','.join(exon))

                # This might happen with a region or amino acids path report
                if not equiList:
                    break

                if equiList[0] in ['few', 'gene', 'and', '(part', 'of', 'gene)', '(part)']:
                    equiList = equiList[1:]
                    continue

                # This might happen with a region or amino acids path report
                if not equiList:
                    break

                if equiList[0] in ['by', 'c.']:
                    break

                if not includesMultiExons and not includesAminoAcids and not includesRegion:
                    if len(equiList) > 1 and 'exon' in equiList[1] and '(' not in equiList[1]:
                        equivocalGenes.append(equiList[0])
                        equiList = equiList[1:]
                        equiList = equiList[1:]
                        equivocalExons.append(equiList[0].replace(')', '').replace(',', ''))
                    else:
                        equivocalGenes.append(equiList[0].replace(',', ''))
                        equivocalExons.append('full')
                equiList = equiList[1:]

    # The panels typically come with a list of the genes/exons that are covered. I'm assuming that all HF panels
    # start with "gene exon / amino acid (aa) coverage" and end with "disclaimers:". Worth investigating!
    if testType in panelTests or (testType.lower() == 'surgical pathology report' and (regex.findall('(?:gene exon / amino acid){s<=2}', \
                                pathReport) or regex.findall('(?:gene target region){s<=2}', pathReport))):
        geneTestedList = []
        exonTestedList = []
        aminoAcidTestedList = []
        aminoAcidTestedChunk = []
        geneTestedChunk = []
        exonTestedChunk = []
        coverageText = regex.findall('(?:gene exon / amino acid){s<=2}', pathReport)
        coveragePos = [m.start() for m in regex.finditer('(?:gene exon / amino acid){s<=2}', pathReport)]
        for pos in coveragePos:
            # We want the next token which is 1) farther than the start token, and 2) closest to it
            nearestPos = len(pathReport)
            for x in ['tp53 is not', 'disclaimers:', 'fusion assay:', '2. immunohistochemistry', 'this test', 'this result', 'idh2 testing was',
                      'flt3 itd detection', 'calreticulin mutations', 'the isocitrate', 'somatic',
                      'hematolymphoid', 'detection', 'was performed']:
                place = [m.start() for m in regex.finditer('(?:' + x + '){s<=2}', pathReport)]
                if place and pos:
                    for pl in place:
                        if pos < pl < nearestPos:
                            coverageEndPos = place
                            nearestPos = pl
            if coverageText:
                coverageSplit = pathReport[pos + len('gene exon / amino acid (aa) coverage'):nearestPos].split()
                # If we don't handle space removal before, here's the place to do it.
                for i in range(0, len(coverageSplit)):
                    coverageSplit[i] = coverageSplit[i].strip()
                geneTestedChunk = []
                exonTestedChunk = []
                aminoAcidTestedChunk = []
                # Now we've split it into chunks, let's take it in the following way: First, a gene name, then, the exons,
                # finally, the exact amino acids. We're being thorough, so we'll get the exons AND the amino acids.
                while coverageSplit:
                    # This is a sign that we're done with this section.
                    if len(coverageSplit) > 1:
                        if coverageSplit[1] == 'immunohistochemistry':
                            coverageSplit = []
                            break

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
                    if not coverageSplit[0].isnumeric():
                        geneTestedChunk.append(coverageSplit[0])
                        coverageSplit = coverageSplit[1:]
                        # Now coverageSplit[0] is 'exons'
                        coverageSplit = coverageSplit[1:]
                    if len(coverageSplit) > 1:
                        while '(' not in coverageSplit[0]:
                            if len(coverageSplit) > 1:
                                if coverageSplit[1] in ['exons', 'exon']:
                                    break
                            # Sometimes it's 'and'.
                            if 'and' in coverageSplit[0]:
                                coverageSplit = coverageSplit[1:]
                            # I'm dealing with ranges here. I'm NOT dealing with ranges for amino acids.
                            exonBit = coverageSplit[0].replace(',', '')
                            if '-' in exonBit:
                                if exonBit.endswith('-'):
                                    coverageSplit = coverageSplit[1:]
                                    exonBit = exonBit + coverageSplit[0]
                                for x in range(int(exonBit.split('-')[0]), int(exonBit.split('-')[1])+1):
                                    exonTestedChunk.append(x)
                            else:
                                exonTestedChunk.append(int(coverageSplit[0].replace(',', '')))
                            coverageSplit = coverageSplit[1:]
                            if not coverageSplit:
                                break
                    # This is for if we end with an exon without an amino acid
                    if len(coverageSplit) == 1 and '(' not in coverageSplit[0]:
                        exonBit = coverageSplit[0].replace(',', '')
                        exonTestedChunk.append(int(exonBit))
                        coverageSplit = coverageSplit[1:]

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
                    if geneTestedChunk == 'note:':
                        geneTestedChunk = []
                        exonTestedChunk = []
                        aminoAcidTestedChunk = []
                        continue
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
                for x in ['tp53 is not', 'note:', 'disclaimers:', 'fusion assay:', '2. immunohistochemistry', 'this test', 'this result', 'idh2 testing was',
                          'flt3 itd detection', 'calreticulin mutations', 'the isocitrate']:
                    place = [m.start() for m in regex.finditer('(?:' + x + '){s<=1}', pathReport[pos:])]
                    if place and pos:
                        if place[0] > 0 and place[0] < nearestPos:
                            coverageEndPos = place
                            nearestPos = place[0]
                            coverageSplit = pathReport[pos + len('gene target region(exon)'):pos + nearestPos]
                            if '(aa' in coverageSplit and '(aa ' not in coverageSplit:
                                coverageSplit = coverageSplit.replace('(aa', '(aa ')
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
                    if coverageSplit[0] == 'this' and coverageSplit[1] == 'test':
                        coverageSplit = []
                        break
                    if coverageSplit[0] in ['hematolymphoid', 'somatic']:
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
                                coverageSplit[0] in ['full', '(partial)', 'and'] or 'partial' in coverageSplit[0] or 'exon' in coverageSplit[0] or coverageSplit[0] == '(aa':
                            # Sometimes it's 'full (all gene coding regions)'
                            if coverageSplit[0] == 'full' and coverageSplit[1] == '(all':
                                exonTestedChunk.append(coverageSplit[0].replace(',', '').replace('+', ''))
                                while ')' not in coverageSplit[0]:
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

                    if 'this' in geneTestedChunk:
                        print(coverageSplit)
                        print(pathReport)
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
        elif not coverageText:
            noPanel = True

    # Now to get the results from this test!

    # First we need to get all instances of the header. The first three fields have been constant in
    # basically the panels I've seen from HF.
    panelText = regex.findall('(?:gene location transcript\b){s<=2}', pathReport)
    panelPos = [m.start() for m in regex.finditer('(?:gene location transcript\b){s<=2}', pathReport)]
    panelEnds = []

    # I've also only seen panels end with 'label' or 'interpretation'. This section picks out the rest of the
    # label until we run into one of those two keywords.
    panelEndText = ""
    fullPanel = ""

    # This is where we separate out the tests with semi-structured panels
    if panelText:

        # There might be many different semi-structured sections!
        for panelStart in panelPos:
            # At this point, 'panelText' is 'gene location transcript'. Let's get the end of the panel
            # which is either 'label' or 'interpretation'
            restOfReport = pathReport[panelStart+len(panelText):panelStart+len(panelText) + 100]
            # It'll either be 'label' or 'interpretation'
            panelEndText = regex.findall('(?:label\b){s<=1}', restOfReport)
            panelEndPos = [m.start() for m in regex.finditer('(?:label\b){s<=1}', restOfReport)]
            if not panelEndText:
                panelEndText = regex.findall('(?:interpreation\b){s<=1}', restOfReport)
                panelEndPos = [m.start() for m in regex.finditer('(?:interpreation\b){s<=1}', restOfReport)]
            if not panelEndText:
                panelEndText = regex.findall('(?:interpretation\b){s<=8}', restOfReport)
                panelEndPos = [m.start() for m in regex.finditer('(?:interpretation\b){s<=8}', restOfReport)]
            fullPanel = pathReport[panelStart:panelStart+len(panelText)+panelEndPos[0] + len(panelEndText[0])]
            sectionList.append(fullPanel)
            sectionPos.append(panelStart)
            panelEnds.append(panelEndPos[0])

    elif testType in panelTests and noPanel:
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
                    if fullPanelBroken[j+1] == '%':
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

                # Yet another pipe-delimiting problem. Sometimes there's a semi-colon with a space gap in cdna or protein.
                while thisSection[3].endswith(';'):
                    thisSection[3:5] = [' '.join(thisSection[3:5])]
                while thisSection[4].endswith(';'):
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

                # Sometimes there's an exta field by the protein - we took out the addition because it was redundant information: like V600E after p.val600ely
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
                    pass
                    #aminoAcidRangeList.append('')

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
    if (testType in panelTests or testType.lower() == 'surgical pathology report') and (regex.findall('(?:positive result cannot be ruled out.){s<=2}', pathReport) \
            or regex.findall('(?:false positive cannot be ruled out.){s<=2}', pathReport)):
        hasExtras = False
        posEquivSt = [m.start() for m in regex.finditer('(?:positive result cannot be ruled out.){s<=2}', pathReport)]
        phrase = 'positive result cannot be ruled out.'
        if not posEquivSt:
            posEquivSt = [m.start() for m in regex.finditer('(?:false positive cannot be ruled out.){s<=2}', pathReport)]
            phrase = 'false positive cannot be ruled out.'
        posChunk = pathReport[posEquivSt[0] + len(phrase):]
        posEquivStop = [m.start() for m in regex.finditer(r'(\d{1,}\))', posChunk)]
        posEquiStopVariant = [m.start() for m in regex.finditer('(?:results-comments){s<=2}', posChunk)]
        if posEquiStopVariant and posEquivStop:
            if posEquiStopVariant[0] < posEquivStop[0]:
                posEquivStop = posEquiStopVariant
        if not posEquivStop and posEquiStopVariant:
            posEquivStop = posEquiStopVariant
        posChunk = posChunk[:posEquivStop[0]].strip()
        if 'it is noted' in posChunk:
            posChunk = posChunk[posChunk.find('.')+1:]
        if 'clinical correlation' in posChunk:
            print(posChunk)
            print("CC")
            posChunk = ''
        if 'dp exon af label' in posChunk:
            hasExtras = True
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
        if posSplit[0] == '':
            posSplit = posSplit[1:]
        for equiv in posSplit:
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
            testType.lower() == 'surgical pathology report' and (regex.findall('(?:gene exon / amino acid){s<=2}', \
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
                    for x in range(0, len(usedGenes)):
                        if aminoacidChunk[i]:
                            if geneChunk[i] == usedGenes[x] and usedLowerRange[x] < aminoacidChunk[i] < usedHigherRange[x] and not foundMatch:
                                aminoAcidRangeList.append(usedFullRange[x])
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
            geneList.append(geneName)
            if len(equivocalLocations) > 0:
                if equivocalLocations[gene]:
                    locationList.append(equivocalLocations[gene])
            else:
                locationList.append('')
            transcriptList.append('')
            cdnaList.append('')
            alleleFrequencyList.append('')
            dpList.append('')
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
            # Assuming that AA ranges have a '-', exons don't, and proteins have letters
            for geneBit in equivocalExons[gene].split(','):
                if not geneBit.replace('-', '').isnumeric() or geneBit == 'full':
                    equiProts.append(geneBit)
                elif '-' in geneBit:
                    equiAAs.append(geneBit)
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

        #if 'cannot be excluded' in pathReport:
        #    if equivocalGenes == []:
        #        print(pathReport)
        #        print('')
        equivocalExons = []
        equivocalGenes = []

    if testType in panelTests:
        print(pathReportFull)
        input()

    if not len(geneList) == len(exonList) == len(proteinList) == len(aminoAcidRangeList) == len(labelList):
        print(len(geneList))
        print(len(exonList))
        print(len(proteinList))
        print(len(aminoAcidRangeList))
        print(len(labelList))
        print('')
        print(geneList[-200:])
        #print(exonList)
        #print(proteinList)
        print(aminoAcidRangeList[-200:])
        print(labelList[-200:])
        print(pathReport)
        print('')
        print(geneChunk)
        print(geneTestedList)
        print(exonTestedList)
        print(aminoAcidTestedList)
        print(aminoacidChunk)
        print(testType)
        input()

    aminoAcidTestedList = []

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
                and (proteinList[pos] != '' and proteinList[pos-1] == ''):
            proteinList[pos-1] = proteinList[pos]
            aminoAcidRangeList[pos] = aminoAcidRangeList[pos-1]
        elif geneList[pos] == geneList[pos - 1] and reportIdList[pos] == reportIdList[pos - 1] and (aminoAcidRangeList[pos-1] == '' and aminoAcidRangeList[pos] != '') \
                and (proteinList[pos - 1] != '' and proteinList[pos] == ''):
            proteinList[pos] = proteinList[pos - 1]
            aminoAcidRangeList[pos - 1] = aminoAcidRangeList[pos]
    # This one's for fixing BRAF tests:
    if testTypeList[pos] == 'BRAF Gene Mutation Analysis' and 'negative - no coding variants detected in the targeted regions tested' in fullTestList[pos]:
        geneList[pos] = 'braf'
        labelList[pos] = 'negative'
        statusList[pos] = 'normal'
        aminoAcidRangeList[pos] = '439-472, 581-606'
        proteinList[pos] = ''
    # This is for clearing up anything that's not '.p' if there's a '.c'
    if cdnaList[pos].startswith('c.') and not proteinList[pos].startswith('p.'):
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


# No duplicate rows!
#panelsDataFrame = panelsDataFrame.drop_duplicates()

panelsDataFrame = panelsDataFrame.drop(panelsDataFrame[(panelsDataFrame['gene'] == '') & (panelsDataFrame['location'] != '') & (panelsDataFrame['transcript'] != '')].index)
panelsDataFrame = panelsDataFrame.drop(panelsDataFrame[(panelsDataFrame['label'] == 'no variant found') & (panelsDataFrame['amino acid range'] == '') & (panelsDataFrame['exon'] == '')].index)
fullPanelsDataFrame = fullPanelsDataFrame.drop(fullPanelsDataFrame[(fullPanelsDataFrame['gene'] == '') & (fullPanelsDataFrame['location'] != '') & (fullPanelsDataFrame['transcript'] != '')].index)
fullPanelsDataFrame = fullPanelsDataFrame.drop(fullPanelsDataFrame[(fullPanelsDataFrame['label'] == 'no variant found') & (fullPanelsDataFrame['amino acid range'] == '') & (fullPanelsDataFrame['exon'] == '')].index)
panelsDataFrame.to_csv("~/Desktop/DeleteMeSoon/PanelsUpdated.csv", index=False)
fullPanelsDataFrame.to_csv("~/Desktop/DeleteMeSoon/PanelsUpdatedFull.csv", index=False)
df = pd.read_csv("~/Desktop/DeleteMeSoon/PanelsUpdated.csv", low_memory=False)
df = df.drop_duplicates(keep='first')
df.to_csv("~/Desktop/DeleteMeSoon/PanelsUpdated2.csv", index=False)


testTypesDataFrame = pd.DataFrame(list(zip(biomarkersForPhizer, biomarkerTestsForPhizer)),
                                                            columns=['biomarker', 'test'])

testTypesDataFrame = testTypesDataFrame.drop_duplicates()
#testTypesDataFrame.to_csv("~/Desktop/DeleteMeSoon/PhizerTestTypesAndBiomarkers.csv", index=False)
