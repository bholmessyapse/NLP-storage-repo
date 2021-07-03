# Import libraries
from os import listdir
from os.path import isfile, join
import pandas as pd
import itertools
from zipfile import ZipFile
import random

firstNames = []
middleNames = []
lastNames = []
jrSrs = []
testTexts = []
fullTexts = []
birthDates = []
testTypes = []
testReceivedDates = []
testOrderedDates = []
testDateTypes = []
diagnoses = []
primaries = []
specimenTypes = []
specimenSites = []
problems = []
sources = []
fileNames = []
mrns = []
docIds = []
datasourceTypes = []
accessionNumbers = []

# These are for genes and labels - indeterminates, wild types, etc.
geneList = []
exonList = []
variantList = []
platformList = []
typeList = []
callList = []

negGeneList = []
negExonList = []
negPlatformList = []
negTypeList = []
negCallList = []

# For finding Tempus files with no gene lists
tempusNoLists = []
tempusNoListDates = []

# Split up the ingest if desired
getCaris = False
getFMI = True
getTempus = False
getGuardant = False
getNeogenomics = False
getInvitae = False

sampleName = "/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/FMISample.csv"
zipName = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/FMISample.zip'

# To see the files go by
countFiles = True

# For finding the rightmost value
def listRightIndex(alist, value):
    return len(alist) - alist[-1::-1].index(value) -1


def standardAppends():
    firstNames.append(firstName)
    middleNames.append(middleName)
    lastNames.append(lastName)
    jrSrs.append(srJr)
    testTexts.append(testText)
    fullTexts.append('')
    birthDates.append(birthdate)
    diagnoses.append(diagnosis)
    primaries.append(primary)
    specimenSites.append(specimenSite)
    specimenTypes.append(specimenType)
    sources.append(source)
    fileNames.append(filename)
    testReceivedDates.append(received)
    testOrderedDates.append(ordered)
    testDateTypes.append(dateType)
    testTypes.append(testType)
    mrns.append(mrn)
    docIds.append(docId)
    datasourceTypes.append(datasource)
    accessionNumbers.append(accession)

if getCaris:
    # Caris doesn't seem to send test types in their reports?
    testType = ''
    # or MRNs
    mrn = ''
    mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Caris/'
    txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]
    fnum = 0
    brokens = []
    for txt in txts:
        if countFiles:
            print(fnum, ' of ', len(txts))
        fnum = fnum + 1
        file = mypath + txt
        file = open(file, mode='r')
        all_of_it = file.read()
        file.close()

        source = 'Caris'
        filename = txt[:-20]

        ######
        # Let's get the test recieved date
        #####
        all_of_it = all_of_it.replace('Specimen Recieved:', 'Specimen Received:')
        if 'Completion of Testing:' in all_of_it:
            space = all_of_it[all_of_it.index('Completion of Testing:') + len('Completion of Testing:'):]
            space = space[:space.index('\n')]
            if '   ' in space:
                space = space[:space.index('   ')]
            space = space.strip()
            space = space
            received = space
            dateType = 'Testing Completed'
        elif 'Specimen Received:' in all_of_it:
            space = all_of_it[all_of_it.index('Specimen Received:') + len('Specimen Received:'):]
            space = space[:space.index('\n')]
            if '   ' in space:
                space = space[:space.index('   ')]
            space = space.strip()
            space = space
            dateType = 'Specimen Recieved'
            received = space
        elif 'FINAL REPORT - ' in all_of_it:
            space = all_of_it[all_of_it.index('FINAL REPORT - ') + len('FINAL REPORT - '):]
            space = space[:space.index('\n')]
            received = space
            dateType = 'Final Report Date'
        else:
            print(all_of_it)
            input()
        #####
        # First, for identification, we get the name
        #####
        if 'Name:' in all_of_it:
            section = all_of_it[all_of_it.index('Name:') + len('Name:'):]
            section = section[:section.index('       ')].strip()

        elif 'ORDERED BY' in all_of_it:
            section = all_of_it[all_of_it.index('ORDERED BY') + len('ORDERED BY'):]
            section = section[:section.index('Primary Tumor Site')].strip()

        lastName = section.split(',')[0].strip()
        firstName = section.split(',')[1].strip()
        if len(firstName.split()) > 1:
            middleName = firstName.split()[1].strip()
            firstName = firstName.split()[0].strip()
        else:
            middleName = ''
        if len(lastName.split()) > 1 and ('jr' in lastName.lower() or 'sr' in lastName.lower() or lastName.lower().split()[1].replace('i', '') == ''):
            srJr = lastName.split()[1].strip()
            lastName = lastName.split()[0].strip()
        else:
            srJr = ''
        firstName = firstName.replace(' ', '')
        middleName = middleName.replace(' ', '')
        lastName = lastName.replace(' ', '')
        srJr = srJr.replace(' ', '')


        #####
        # Next let's find the date of birth
        #####
        if 'date of birth:' in all_of_it.lower():
            section = all_of_it[all_of_it.lower().index('date of birth:') + len('date of birth:'):]
            section = section[:section.index('         ')].strip()
        elif 'birthdate:' in all_of_it.lower():
            section = all_of_it[all_of_it.lower().index('birthdate:') + len('birthdate:'):]
            section = section[:section.index('         ')].strip()
        birthdate = section

        #####
        # Next, let's get the diagnosis
        #####
        if 'Diagnosis:' in all_of_it:
            section = all_of_it[all_of_it.index('Diagnosis:') + len('Diagnosis:'):]
            section = section[:section.index('         ')].strip()
            # This is a workaround for some wonky formatting. Lots more of this if we start extracting in earnest!
            if section.endswith(',') or section.endswith('with'):
                oldSection = section
                section = all_of_it[all_of_it.index('Diagnosis:') + len('Diagnosis:'):]
                section = section[:section.index('\n\n')].strip()
                bitToRemove = section[section.index(oldSection) + len(oldSection):section.index('\n')]
                section = section.replace(bitToRemove, '')
                section = section.split('\n')
                for sectionB in range(0, len(section)):
                    if section[sectionB].replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace(' ', '').isnumeric():
                        section[sectionB] = ''
                    if section[sectionB].replace(' ', '').replace('USA', '') == '':
                        section[sectionB] = ''
                section = list(filter(None, section))
                sectionKeep = section[0] + ' ' + section[-1]
                section = sectionKeep
            if '                     ' in section:
                section = section[:section.index('                     ')]
            if '.' in section:
                section = section[:section.index('.') + len('.')]
            while '  ' in section:
                section = section.replace('  ', ' ')

            diagnosis = section

        else:
            diagnosis = 'Not Given'

        #####
        # Finally, let's get the primary site
        #####
        if 'Primary Tumor Site:' in all_of_it:
            section = all_of_it[all_of_it.index('Primary Tumor Site:') + len('Primary Tumor Site:'):]
            section = section[:section.index('         ')].strip()
            if section.endswith('of'):
                origSection = section
                if 'Date of Birth:' not in all_of_it:
                    startSection = 'Case Number:'
                else:
                    startSection = 'Date of Birth:'
                section = all_of_it[all_of_it.index(startSection) + len(startSection):]
                section = section[:section.index('\n')].strip()
                while '  ' in section:
                    section = section.replace('  ', ' ')
                if section.split()[1].endswith(','):
                    newsection = ''
                    start = 1
                    while (not section.split()[start][0].isupper() or section.split()[start].isupper()):
                        newsection = newsection + ' ' + section.split()[start]
                        start = start + 1
                    section = origSection + ' ' + newsection.strip()
                else:
                    section = section.split()[1]
                section = origSection + ' ' + section
            primary = section

        else:
            primary = 'Not Given'

        #####
        # Extra-Finally, let's get the specimen site
        #####

        if 'Specimen Site: ' in all_of_it:
            section = all_of_it[all_of_it.index('Specimen Site: ') + len('Specimen Site: '):]
            section = section[:section.index('   ')]
            if section.endswith('and') or section.endswith('subcutaneous'):
                specimenLine = 0
                split = all_of_it.split('\n')
                while 'Specimen Site:' not in split[specimenLine]:
                    specimenLine = specimenLine + 1
                specimenLine = specimenLine + 1
                nextRow = split[specimenLine]
                nextRow = nextRow.split('               ')
                nextRow = list(filter(None, nextRow))
                if len(nextRow) == 1:
                    sectionTop = split[specimenLine-1].split('   ')
                    sectionBottom = split[specimenLine+1].split('   ')
                    sectionTop = list(filter(None, sectionTop))
                    sectionBottom = list(filter(None, sectionBottom))
                    section = sectionTop[0] + ' ' + sectionBottom[0]
                    while '  ' in section:
                        section = section.replace('  ', ' ')
                    if 'Specimen Site: ' in section:
                        section = section[section.index('Specimen Site: ') + len('Specimen Site: '):]
                else:
                    nextRow = nextRow[1]
                    section = section + ' ' + nextRow
                while '  ' in section:
                    section = section.replace('  ', ' ')
            if 'Specimen ID' in section:
                section = section[:section.index('Specimen ID')]
            #print(section)

        else:
            specimenSite = 'Not Given'
            #print(all_of_it)
            #input()
        specimenSite = section
        # Specimen Type is not given in caris
        specimenType = 'Not Given'

        # Lookin' for LOH
        if 'GENOMIC LOSS OF HETEROZYGOSITY' in all_of_it:
            section = all_of_it[all_of_it.index('GENOMIC LOSS OF HETEROZYGOSITY'):]
            section = section[:section.index('Genomic Loss of Heterozygosity Analysis:')]
            origSection = section
            section = section.split('\n')
            section = list(filter(None, section))
            section = section[-1]
            while '  ' in section:
                section = section.replace('  ', ' ')
            section = section[section.index('(LOH)') + len('(LOH)'):].strip()
            if len(section.split()) == 1:
                section = section
            else:
                section = section.split()[2]
            if section == 'performed' or section == 'Indeterminate':
                section = 'Test not performed'
            LOH = section
            geneList.append('LOH')
            exonList.append('{}')
            variantList.append('')
            platformList.append('LOH')
            typeList.append('LOH')
            callList.append(LOH)
            standardAppends()

        # Now let's find the rest of the stuff in the appendix:
        # We'll start with tumor mutational burden / total mutational load!
        totalLoads = ['TOTAL MUTATIONAL LOAD', 'TUMOR MUTATIONAL BURDEN']
        ends = ['TMB', 'Interpretation:', 'TOTAL', 'MICROSATELLITE', 'TML']
        while any(load in all_of_it for load in totalLoads):
            for l in range(0, len(totalLoads)):
                wholeSection = ''
                if totalLoads[l] in all_of_it:
                    start = totalLoads[l]
                    wholeSection = all_of_it[all_of_it.index(start):]
                    section = all_of_it[all_of_it.index(start) + len(start):]
                    endIndex = 99999999
                    for end in ends:
                        if end in section:
                            if section.index(end) < endIndex:
                                endIndex = section.index(end)
                    section = section[:endIndex]
                    wholeSection = wholeSection[:len(end) + endIndex]
                    # Now let's split it up
                    section = section.split('\n')
                    section = list(filter(None, section))
                    for sec in range(0, len(section)):
                        while '  ' in section[sec]:
                            section[sec] = section[sec].replace('  ', ' ')

                    if 'Result:' in section[0]:
                        mutationNumber = section[0][section[0].index('Megabase: ') + len('Megabase: '):section[0].index('Result:')].strip()
                        mutationCall = section[0][section[0].index('Result:') + len('Result: '):].strip()
                    elif 'Megabase Result' in section[0]:
                        if 'Indeterminate' in section[1]:
                            mutationNumber = ''
                            mutationCall = 'Untested - Indeterminate'
                        else:
                            mutationNumber = section[1].strip().split()[0]
                            mutationCall = section[1].strip().split()[1]
                    elif 'Megabase (Mb)' in section[0]:
                        mutationNumber = section[1].strip().split()[1]
                        mutationCall = section[1].strip().split()[0]
                    geneList.append('TMB')
                    exonList.append('{}')
                    variantList.append('')
                    platformList.append('NGS')
                    typeList.append('TMB')
                    callList.append(mutationCall)
                    standardAppends()
                all_of_it = all_of_it.replace(wholeSection, '')


        # Now let's move to microsatellite instability
        micros = ['MICROSATELLITE INSTABILITY ANALYSIS', 'MICROSATELLITE INSTABILITY (MSI) BY NEXT-GENERATION SEQUENCING']
        ends = ['Microsatellite Instability', 'GENES']
        while any(ms in all_of_it for ms in micros):
            for l in range(0, len(micros)):
                wholeSection = ''
                if micros[l] in all_of_it:
                    start = micros[l]
                    wholeSection = all_of_it[all_of_it.index(start):]
                    section = all_of_it[all_of_it.index(start) + len(start):]
                    endIndex = 99999999
                    for end in ends:
                        if end in section:
                            if section.index(end) < endIndex:
                                endIndex = section.index(end)
                    section = section[:endIndex]
                    wholeSection = wholeSection[:len(end) + endIndex]
                    section = section.split('\n')
                    section = list(filter(None, section))
                    if 'Result:' in section[0]:
                        MSI = section[0].split()[-1]
                    else:
                        MSI = section[1].split()[-1]
                    geneList.append("MSI")
                    exonList.append('{}')
                    variantList.append('')
                    platformList.append('MSI')
                    typeList.append('MSI')
                    callList.append(MSI)
                    standardAppends()
                all_of_it = all_of_it.replace(wholeSection, '')

        # CISH is here
        while 'AM PLIFICATION BY CHROMOG ENIC IN SITU HYBRIDIZATION (CISH)' in all_of_it:
            section = all_of_it[all_of_it.index('AM PLIFICATION BY CHROMOG ENIC IN SITU HYBRIDIZATION (CISH)'):]
            section = section[:section.index(' Reference')]
            origSection = section
            section = section.split('\n')
            for x in range(0, len(section)):
                while '  ' in section[x]:
                    section[x] = section[x].replace('  ', ' ')
                if 'nuc ish' in section[x]:
                    amplified = section[x-1]
                    geneList.append(amplified.strip())
                    exonList.append('{}')
                    variantList.append('')
                    platformList.append('CISH')
                    typeList.append('Amplification')
                    callList.append('yes')
                    standardAppends()
            all_of_it = all_of_it.replace(origSection, '')

        # There are a number of sections with one gene per line. Let's get that


        # This section is unique - it's not a gene list, it's a table with a whole series of pieces of information in it about the genes found
        # I figure that we can do a full dive and pull out everything in here later if necessary? But since the positives should already
        # be coming through, if I just get the gene list for positive alterations, we can go back later and compare.
        while 'GENES TESTED WITH ALTERATIONS' in all_of_it:
            wholeSection = section = all_of_it[all_of_it.index('GENES TESTED WITH ALTERATIONS'):]
            section = all_of_it[all_of_it.index('GENES TESTED WITH ALTERATIONS') + len('GENES TESTED WITH ALTERATIONS'):]
            endingPos = 9999999999999
            sectionEndings = ['GENES TESTED', 'PATIENT']
            for ending in sectionEndings:
                if ending in section:
                    if section.index(ending) < endingPos:
                        endingPos = section.index(ending)
            section = section[:endingPos]
            wholeSection = wholeSection[:endingPos]
            origSection = section
            section = section.split('\n')

            indentForGene = 0
            for line in section:
                if 'Gene' in line and indentForGene == 0:
                    while line.startswith(' '):
                        indentForGene = indentForGene + 1
                        line = line[1:]
                    continue
                lineIndent = 0
                while line.startswith(' '):
                    line = line[1:]
                    lineIndent = lineIndent + 1
                if abs(indentForGene - lineIndent) <= 5 and indentForGene != 0 and lineIndent > 1 and line != '':
                    while '  ' in line:
                        line = line.replace('  ', ' ')
                    section = list(filter(None, section))
                    gene = line.split()[0]
                    if gene not in ['Gene', 'Genes']:
                        geneList.append(gene)
                        exonList.append('{}')
                        variantList.append('')
                        platformList.append('NGS')
                        typeList.append('Gene tested with alteration')
                        if 'Variant of Uncertain Significance' in line:
                            callList.append('VUS')
                        else:
                            callList.append('Positive')
                        standardAppends()
            all_of_it = all_of_it.replace(wholeSection, '')

        # Rearrangement by FISH:
        while 'REARRANGEMENT BY FLUORESCENCE IN SITU HYBRIDIZATION (FISH)' in all_of_it:
            section = all_of_it[all_of_it.index('REARRANGEMENT BY FLUORESCENCE IN SITU HYBRIDIZATION (FISH)'):]
            section = section[:section.index('Electronic')]
            origSection = section
            section = section.split('\n')
            section = list(filter(None, section))
            for x in range(0, len(section)):
                while '  ' in section[x]:
                    section[x] = section[x].replace('  ', ' ')
                if 'Reference' in section[x]:
                    bit = section[x-1]
                    b = x-1
                    while 'Detected' not in bit and 'QNS' not in bit and 'Negative' not in bit and 'See Below' not in bit and \
                            'Positive' not in bit and 'Other' not in bit and 'Test not performed' not in bit:
                        b = b - 1
                        bit = section[b]
                    if 'Positive' in bit:
                        call = 'Positive'
                    elif 'Test not performed' in bit:
                        call = 'TNP'
                    elif 'Other' in bit:
                        call = 'Other'
                    elif 'QNS' in bit:
                        call = 'QNS'
                    elif 'Negative' in bit:
                        call = 'Negative, explicit'
                    # Get aberrent comments
                    elif 'See Below' in bit:
                        call = all_of_it[all_of_it.index('Comments on FISH Analysis'):]
                        # Sometimes we jsut need the next line
                        if 'comments.' not in call:
                            call = call[call.index('\n')+1:]
                            call = call[call.index('\n')+1:]
                            call = call[:call.index('\n')]
                        else:
                            call = call[call.index('comments.') + len('comments.'):]
                            call = call[:call.index('\n')].strip()
                    else:
                        call = bit[:bit.index('Detected') + len('Detected')].strip()
                    gene = section[x-1].split()[-1].replace('ish(', '').replace(')','')
                    if 'x' in gene:
                        gene = gene[:gene.index('x')]
                    geneList.append(gene)
                    exonList.append('{}')
                    variantList.append('')
                    platformList.append('FISH')
                    typeList.append('Rearrangement')
                    callList.append(call)
                    standardAppends()
            all_of_it = all_of_it.replace(origSection, '')

        # We'll get the PD-L1s here
        while any(pd in all_of_it for pd in ['PD-L1 TUMOR CELL STAINING', 'PD-L1 COMBINED POSITIVE SCORE', 'PD-L1 TUMOR PROPORTION SCORE (TPS)', 'PD-L1 IMMUNE CELL (IC) SCORE']):
            for pdl in ['PD-L1 TUMOR CELL STAINING', 'PD-L1 COMBINED POSITIVE SCORE', 'PD-L1 TUMOR PROPORTION SCORE (TPS)', 'PD-L1 IMMUNE CELL (IC) SCORE']:
                if pdl in all_of_it:
                    section = all_of_it[all_of_it.index(pdl):]
                    if 'Scoring' not in section:
                        if 'Utilizing' in section:
                            section = section[:section.index('Utilizing')]
                        elif 'CPS:' in section:
                            section = section[:section.index('CPS:')]
                        elif 'Clones' in section:
                            section = section[:section.index('Clones')]
                        else:
                            section = section[:section.index('IC scoring')]
                    else:
                        section = section[:section.index('Scoring')]
                    origSection = section
                    all_of_it = all_of_it.replace(origSection, '')
                    section = section.split('\n')
                    section = list(filter(None, section))
                    for x in range(1, len(section)):
                        if 'PD-L1' in section[x] and len(section[x].split('   ')) > 1:
                            bit = section[x].split('   ')
                            for b in bit:
                                if 'PD-L1' in b:
                                    geneList.append(b.strip())
                                    exonList.append('{}')
                                    variantList.append('')
                                    platformList.append('FISH')
                                    typeList.append('PD-L1')
                                    callList.append(pdl)
                                    standardAppends()
                            continue

        # Clones. Easy to get!
        while 'Clones used:' in all_of_it:
            section = all_of_it[all_of_it.index('Clones used:'):]
            section = section[:section.index('.\n')]
            all_of_it = all_of_it.replace(section, '')
            section = section[len('Clones used: '):]
            for clone in section.split(','):
                geneList.append(clone)
                exonList.append('{}')
                variantList.append('')
                platformList.append('Clone')
                typeList.append('Clone Used')
                callList.append('Clone used')
                standardAppends()

        # This is a low-number assay, but let's get it
        while 'Her-2 IHC: Gastroesophageal Cancer (Biopsy/FNA)' in all_of_it:
            section = all_of_it[all_of_it.index('Her-2 IHC: Gastroesophageal Cancer (Biopsy/FNA)'):]
            section = section[:section.index('\n\n\n')]
            fullSection = section
            section = section.split('\n')
            section = list(filter(None, section))
            for sec in section:
                if sec == '.':
                    section.remove(sec)
            section = section[-1]
            while section.startswith(' '):
                section = section[1:]
            geneList.append('Her-2 FNA IHC')
            exonList.append('{}')
            variantList.append('')
            platformList.append('IHC')
            typeList.append('FNA')
            callList.append(section.split('   ')[0].replace('|', '-'))
            standardAppends()
            all_of_it = all_of_it.replace(fullSection, '')

        # Put this one off for too long - protein expression by IHC babeee
        all_of_it = all_of_it.replace('PROTEIN EXPRESSION BY IMMUNOHISTOCHEMISTRY (IHC)', 'Protein Expression by Immunohistochemistry (IHC)')
        while 'Protein Expression by Immunohistochemistry (IHC)' in all_of_it:
            section = all_of_it[all_of_it.index('Protein Expression by Immunohistochemistry (IHC)'):]
            wholeSection = section
            if 'Scoring' not in section:
                ends = ['Comments', 'IHC Methods', 'immunohistochemistry', 'IHC was', 'IHC stains', 'failed', 'Appropriate staining', 'The sarcoma', 'Utilizing',
                        'PD-L1 TUMOR', 'PD-L1 COMBINED', 'RESULT', 'This case']
                if not any(end in section for end in ends):
                    print(section)
                    print("HERE")
                    input()
                    continue
                endIndex = 999999999999
                for end in ends:
                    if end in section:
                        if section.index(end) < endIndex:
                            endIndex = section.index(end)
                section = section[:endIndex]
            else:
                section = section[:section.index('Scoring')]
            otherEnds = ['PD-L1 Tumor Cell', 'PD-L1 Tumor Proportion', 'PD-L1 Combined', 'PD-L1 COMBINED', 'PD-L1 TUMOR', 'CPS:']
            for end in otherEnds:
                if end in section:
                    section = section[:section.index(end)]
            all_of_it = all_of_it.replace(section, '')
            if '(0, 1+, 2+, 3+)' not in section:
                continue
            else:
                section = section[section.index('(0, 1+, 2+, 3+)') + len('(0, 1+, 2+, 3+)'):]
            if 'Electronic Signature' in section:
                section = section[:section.index('Electronic Signature')]
            section = section.split('\n')
            section = list(filter(None, section))
            for sec in section:
                while sec.startswith(' '):
                    sec = sec[1:]
                sec = sec.split('     ')
                sec = list(filter(None, sec))
                if len(sec) > 1:
                    if len(sec) < 4:
                        print(sec)
                        print(section)
                        continue
                    geneList.append(sec[0].strip())
                    exonList.append('{}')
                    variantList.append('')
                    platformList.append('IHC')
                    typeList.append('Protein IHC')
                    callList.append(sec[3].strip())
                    standardAppends()

        # Finally, these tests are just brute lists.
        all_of_it = all_of_it.replace('*', '')
        sectionStarts = ['GENES TESTED WITH NO MUTATIONS DETECTED', 'GENES TESTED WITH INDETERMINATE RESULTS BY TUMOR DNA SEQUENCING', 'GENES WITH INDETERMINATE CNA RESULTS',
                         'GENES TESTED WITH NO AMPLIFICATION DETECTED', 'GENES TESTED WITH UNEVALUATED AMPLIFICATION',
                         'GENES TESTED WITH INDETERMINATE GENE FUNCTION OR TRANSCRIPT VARIANT RESULTS', 'GENES TESTED WITH INDETERMINATE RESULTS',
                         'Genes Tested with Intermediate CNA Results by Tumor DNA Sequencing']
        sectionEnds = ['COMPLETE', 'Additional', 'PATIENT:', 'Electronic', 'For', 'Sequencing', 'GENES', 'The', '¶', 'CNA', 'Genes', 'CNA', 'IN SITU', 'South', 'Comments']
        typeOList = ['No mutations detected', 'Indeterminate mutation result', 'Indetermiante CNA result', 'No Amplification', 'Unevaluated Amplification',
                    'Untested Gene - Indeterminate', 'Untested Gene - Indeterminate', 'Untested CNA - Intermediate']
        while any(section in all_of_it for section in sectionStarts):
            for sectionStarter in range(0, len(sectionStarts)):
                if sectionStarts[sectionStarter] in all_of_it:
                    start = sectionStarts[sectionStarter]
                    type = typeOList[sectionStarter]
                    # We take out the name of the section for analysis, but we leave it in to delete the section
                    section = all_of_it[all_of_it.index(start) + len(start):]
                    wholeSection = all_of_it[all_of_it.index(start):]
                    endIndex = 999999999999
                    for end in sectionEnds:
                        if end in section:
                            if section.index(end) < endIndex:
                                endIndex = section.index(end)
                    section = section[:endIndex]
                    wholeSection = wholeSection[:endIndex + len(start)]
                    # Now we remove that section from the main report
                    all_of_it = all_of_it.replace(wholeSection, '')
                    section = section.replace('\n', ' ')
                    while '  ' in section:
                        section = section.replace('  ', ' ')
                    section = section.strip()
                    section = section.split()
                    while section[0] in ['BY', 'TUMOR', 'DNA', 'SEQUENCING']:
                        section = section[1:]
                    for gene in section:
                        if gene[0].isupper() and gene[1].islower() and gene not in ['Androgen', 'Receptor', 'Her2/Neu', 'Neu)', 'Tertiary', 'Mutation']:
                            print(section)
                            print(gene)
                            print(txt)
                            input()
                        if gene.startswith('(') or gene in ['Receptor', 'Neu)', 'Tertiary', 'Mutation']:
                            geneList[-1] = geneList[-1] + ' ' + gene
                        else:
                            geneList.append(gene)
                            exonList.append('{}')
                            variantList.append('')
                            platformList.append('NGS')
                            if len(type.split()) == 3 and type.split()[2] == 'result':
                                typeList.append(type.split()[1])
                                callList.append(type.split()[0])
                            elif type == 'No mutations detected':
                                typeList.append('Mutation')
                                callList.append('Negative, explicit')
                            elif type == 'No Amplification':
                                typeList.append('Amplification')
                                callList.append('Negative, explicit')
                            elif type == 'Unevaluated Amplification':
                                typeList.append('Amplification')
                                callList.append('Unevaluated')
                            elif type == 'Untested Gene - Indeterminate':
                                typeList.append('Mutation')
                                callList.append('Untested - Indeterminate')
                            elif type == 'Untested CNA - Intermediate':
                                typeList.append('CNA')
                                callList.append('Untested - Intermediate')
                            elif type == 'VUS Mutation':
                                typeList.append('Gene tested with alteration')
                                callList.append('VUS')
                            else:
                                print(type)
                                input()
                            standardAppends()


























if getFMI:
    mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/FMI/'
    txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]
    fnum = 0
    brokens = []
    num = 1
    # No MRNs from FMI
    mrn = ''
    for txt in txts:
        txtNames = ["fmi_file.f7b2dee4-4616-4f9a-9676-8fa272f54d26",
                    "fmi_file.c909377f-fef0-49d5-92f9-52b8db0dad98",
                    "TRF136486.02f8971f-e1c4-416a-9481-7aaba163b9bd",
                    "QRF049489.af7c7441-89e4-4edd-b5ae-7c3fd1921a3e",
                    "QRF048483.1e062feb-9586-466b-b0af-55e43de1abcb",
                    "fmi_file.ed2b9090-6285-4792-991d-43caf3941647",
                    "fmi_file.dc1d28d2-5642-40cf-bbde-6332d0724d57",
                    "fmi_file.d7e30826-3aaa-488b-b37c-f1b173066fad",
                    "fmi_file.d6bac8e4-bcaf-4244-a45c-820cdf330e89",
                    "fmi_file.d05e0b0b-c923-479f-a4b8-45f9ccb6a7da",
                    "fmi_file.b3f34b26-71d4-47ce-a5cc-63dac9406b04",
                    "fmi_file.a7b5a908-eb2c-42d4-8d55-2ae3a0a3b887",
                    "TRF324799.ff9dbefe-9850-40c5-bb74-c49a8dc4f4ae",
                    "TRF323991.50e0452c-8965-4783-89b4-212282674555",
                    "TRF322133.d9935631-3f77-47ef-a2a1-293bdfa06808",
                    "TRF268949.b44d918f-add4-4ddd-9858-c6b9c24ce548",
                    "TRF242784.bac4836e-f37a-40dd-8838-2b9324b9277d",
                    "fmi_file.833546c0-e1e4-4d30-8242-fcf6b7c41c27",
                    "fmi_file.6b613e12-fd73-4257-8251-6654e4dabfe3",
                    "fmi_file.545a3042-d460-400e-ae87-2268bb6e00f7",
                    "fmi_file.536facb4-fc60-44d4-9798-c90454e51cde",
                    "fmi_file.3e92797b-1a1a-4e4c-9606-e3395795921b",
                    "fmi_file.39c6736a-595a-48c6-8bd9-eb936a4d3022",
                    "fmi_file.2d9656d7-ed40-44f5-9123-8200b04b85d1",
                    "fmi_file.2b449fa0-8fe0-4e95-a7c4-20f0b04a341f",
                    "fmi_file.14270e3a-7721-4636-9666-d47de5648a5a",
                    "fmi_file.11f8ebe3-beb5-407a-b18a-feefcf6ab5ed",
                    "fmi_file.0133741b-ca28-4706-b26b-a33d51c71963",
                    "QRF043068.52f089bb-139c-419e-afd6-c006bf9e7eee",
                    "QRF040084.9dd1034e-b079-4cf0-a356-7e4af1cdb53f",
                    "QRF036513.e14274fd-35ae-4c70-9db3-669a57052ba3",
                    "fmi_file.9ed62f9a-6283-4a3a-b633-1d331ef2ea18",
                    "fmi_file.9ab79950-be2f-435d-a675-4de2e80906c8",
                    "fmi_file.5d9b1461-d489-4aeb-9e72-e508506de99d",
                    "fmi_file.4b1dfb07-d063-4f42-af79-095054aecf22",
                    "fmi_file.020134e3-5a24-4e7c-98ed-aecad03e28a2",
                    "fmi_file.9f758274-bd7c-4f83-92c7-78becccceb84",
                    "fmi_file.097534d2-2336-4a59-91cf-5e60da05a058",
                    "fmi_file.f8ffc97d-5c66-4453-a30a-5782069b5554",
                    "fmi_file.f5d9794b-0c3b-4f46-8ce2-8d7f7d3632e0",
                    "fmi_file.c8beed2d-7901-4ad6-b00e-c03d07dd1e1b",
                    "fmi_file.c077966f-e923-4347-a9c3-3c05044b5388",
                    "fmi_file.b71ae296-53e4-4855-ae51-da655cd59e1c",
                    "fmi_file.b4c4f2c0-7c84-479a-8a99-a074d151dace",
                    "fmi_file.a361c90b-44c3-4122-b02f-47a145ea0564",
                    "TRF405013.b1dabcd9-4104-4234-bbb3-f9044bb763af",
                    "TRF103820.aad82dac-8603-4dec-8e35-2014fcb8d483",
                    "QRF156032.0b32de73-87a5-4d7b-9891-7b19108e44de",
                    "QRF132980.447f7bea-8e90-4077-a802-fbf83c6aaffa",
                    "QRF125745.21607c9b-8bb9-478d-b41a-6cb687e99a04",
                    "QRF112631.b18d317c-b9df-4942-be21-a3b167cd7118",
                    "QRF110835.4a577aa1-50e5-4646-8586-73a0db341054",
                    "QRF101016.59afb0bb-d007-4013-b8b8-face4223db00",
                    "QRF076852.1fe8894d-804c-4b2b-8efc-8afae9af6e8d",
                    "QRF070276.be8b95f1-eeaf-43b3-a969-c321c71e2f3b",
                    "ORD-0991801-01.7d8b748e-ce67-4e58-8bf2-78ea4f1e7dd0",
                    "ORD-0980541-01.235f37af-e800-45b9-908a-8166a9ac2473",
                    "ORD-0939862-01.0e04869f-b6cf-4bbe-b7de-3e009e40c388",
                    "ORD-0898417-01.70857fe3-f2fb-441a-bbf6-f0cf1f6e1096",
                    "ORD-0867169-01.daf30056-5c19-47a0-830c-da54c508ee4c",
                    "ORD-0830899-01.e475c8f2-a193-4c1f-a95f-49a014141f33",
                    "ORD-0821851-01.74fe62b9-b6f1-4916-bf43-404e5f7ce8e9",
                    "ORD-0643162-01.bab62e5c-9e1d-4074-a118-b0dde28a81ff",
                    "ORD-0636741-01.97c3c420-8408-4f7d-879b-e4dab3d7050e",
                    "fmi_file.966eef6a-5246-4f43-a455-6143fd2fa943",
                    "fmi_file.96530131-35ea-451c-ba6b-8b0d45de7f8c",
                    "fmi_file.844cf425-b2d6-4e79-b444-db576446fa35",
                    "fmi_file.618b660c-9cba-4661-bcad-b79cf4e28686",
                    "fmi_file.5a368766-4f52-4ea7-ac04-6f16e3d82586",
                    "fmi_file.5165ddff-8379-4ac8-b7dc-76f159e3397c",
                    "fmi_file.4d2e4152-d65a-4fcf-8301-b6b01e952751",
                    "fmi_file.42bb0c7e-7e17-4481-83f4-3d996cce342a",
                    "fmi_file.29da9616-50b0-4c27-b656-8e7c762d97a2",
                    "fmi_file.28160058-7725-4a7f-90ab-a0a5ccad3b1c",
                    "fmi_file.208d5242-6e91-4d01-a0a0-401e73206ecb",
                    "fmi_file.13a3d56e-8a01-443d-bc1c-49ec9c1384f5",
                    "fmi_file.1115424f-1ec4-4869-94ad-9633c43f45e8"]
        #if not any(x in txt for x in txtNames):
        #    continue
        #if not 'QRF125745.21607c9b-8bb9-478d-b41a-6cb687e99a04' in txt:
        #    continue
        truncdGenes = []
        if countFiles:
            print(str(num), ' of ', str(len(txts)))
        num = num + 1
        file = mypath + txt
        file = open(file, mode='r')
        all_of_it = file.read()
        file.close()

        source = 'FMI'
        filename = txt[:-20]
        received = ''
        dateType = ''

        # We only want to add these once
        addedMSI = False
        addedTMB = False

        # This indicates a blank test. Add it to a list of mangled tests for later?
        if len(all_of_it.split('\n')) < 2:
            continue

        testNames = ['FoundationOne CDx', 'FoundationACT', 'FoundationOne™', 'FoundationOne Liquid', 'FoundationOne Heme', 'FoundationOne®']
        if not any(tn in all_of_it for tn in testNames):
            print(all_of_it)
            input()
        else:
            for tn in ['FoundationOne CDx', 'FoundationACT', 'FoundationOne™', 'FoundationOne Liquid', 'FoundationOne Heme', 'FoundationOne®']:
                if tn in all_of_it:
                    testType = tn

        # Getting doc id
        docId = txt.replace('fmi_file.', '').replace('_out_text_SAMPLE.txt', '')
        datasource = 'PDF'

        # Let's get the accession
        if 'FMI Case #' in all_of_it:
            accession = all_of_it[all_of_it.index('FMI Case #') + len('FMI Case #') + 1:]
            accession = accession[:accession.index(' ')]

        elif any(x in all_of_it for x in ['QRF#', 'TRF#', 'CRF#']):
            for y in ['QRF#', 'TRF#', 'CRF#']:
                if y in all_of_it:
                    tag = y
            accession = all_of_it[all_of_it.index(tag) + len(tag) + 1:]
            accession = accession[:accession.index('\n')]
        elif 'ORDERED TEST #' in all_of_it:
            accession = all_of_it[all_of_it.index('ORDERED TEST #') + len('ORDERED TEST #') + 1:]
            accession = accession[:accession.index('\n')]
        else:
            print(all_of_it)
            input()

        # Getting test date
        if 'REPORT DATE' in all_of_it:
            dateLine = 0
            split = all_of_it.split('\n')
            while 'REPORT DATE' not in split[dateLine]:
                dateLine = dateLine + 1
            lineWithDate = split[dateLine + 1]
            lwdSplit = lineWithDate.split()
            lwdBit = 0
            while not lwdSplit[lwdBit].isnumeric():
                lineWithDate = lineWithDate.replace(lwdSplit[lwdBit], '')
                lwdBit = lwdBit + 1
            lineWithDate = lineWithDate.strip()
            received = lineWithDate
            dateType = 'Report Date'
        elif 'Patient Name Report Date Tumor Type' in all_of_it:
            space = all_of_it.split('\n')[1]
            space = ' '.join(space.split()[2:5])
            received = space
            dateType = 'Report Date'
            start = 2
            end = 5
            while not received.split()[-1].isnumeric():
                space = all_of_it.split('\n')[1]
                space = ' '.join(space.split()[start:end])
                received = space
                dateType = 'Report Date'
                start = start + 1
                end = end + 1
        elif 'Patient Name Report Date' in all_of_it:
            spaceLine = 0
            while 'Patient Name Report Date' not in all_of_it.split('\n')[spaceLine]:
                spaceLine = spaceLine + 1
            space = all_of_it.split('\n')[spaceLine + 1]
            space = space.split()
            while not space[-1].isnumeric():
                space = space[:-1]
            space = ' '.join(space[-3:])
            received = space
            dateType = 'Report Date'

        elif 'SPECIMEN RECEIVED' in all_of_it:
            space = all_of_it[all_of_it.index('SPECIMEN RECEIVED') + len('SPECIMEN RECEIVED'):]
            space = space[:space.index('\n')]
            received = space.strip()
            dateType = 'Speciment Received'

        elif 'page 1 of' in all_of_it:
            pageLine = 0
            while 'page 1 of' not in all_of_it.split('\n')[pageLine]:
                pageLine = pageLine + 1
            section = all_of_it[all_of_it.index(all_of_it.split('\n')[pageLine]) + len(all_of_it.split('\n')[pageLine]):]
            reportLine = 0
            section = section[section.index('Report Date'):]
            section = section[section.index('\n')+1:]
            section = section[:section.index('\n')]
            section = section.split()
            while not section[0].isnumeric():
                section = section[1:]
            section = ' '.join(section[0:3])
            received = section
            dateType = 'Report Date'
        else:
            print(all_of_it)
            input()
        while received.startswith(',') or received.startswith(' '):
            received = received[1:]

        # Getting test date
        if 'DATE OF COLLECTION' in all_of_it:
            ordered = all_of_it[all_of_it.index('DATE OF COLLECTION') + len('DATE OF COLLECTION '):]
            ordered = ordered[:ordered.index('\n')]
        elif 'Date of Collection' in all_of_it:
            ordered = all_of_it[all_of_it.index('Date of Collection') + len('Date of Collection '):]
            ordered = ordered[:ordered.index('\n')]
        elif 'DDAATTEE  OOFF  CCOOLLLLEECCTTIIOONN' in all_of_it:
            ordered = all_of_it[all_of_it.index('DDAATTEE  OOFF  CCOOLLLLEECCTTIIOONN') + len('DDAATTEE  OOFF  CCOOLLLLEECCTTIIOONN'):]
            ordered = ordered[:ordered.index('\n')]
        else:
            print(all_of_it)
            input()

        # Getting name here
        if 'NAME' in all_of_it:
            section = all_of_it[all_of_it.index('NAME') + len('NAME'):]
            section = section[:section.index('\n')]
            name = ' '.join(section.split()[0:2])
            if name.split()[1].replace('I', '').replace('V', '') == '' or name.endswith(','):
                name = ' '.join(section.split()[0:3])
        elif 'PATIENT TUMOR TYPE' in all_of_it.split('\n')[0]:
            section = all_of_it.split('\n')[1]
            name = ' '.join(section.split()[0:2])
            if name.split()[1].replace('I', '').replace('V', '') == '' or name.endswith(','):
                name = ' '.join(section.split()[0:3])
        else:
            split = all_of_it.split('\n')
            lineNum = 0
            # There can be a variable number of lines where the patient name is, but it's always below the line that says 'Patient'
            while 'Patient' not in split[lineNum]:
                lineNum = lineNum + 1
            lineNum = lineNum + 1

            section = split[lineNum]
            name = ' '.join(section.split()[0:2])
            if name.split()[1].replace('I', '').replace('V', '') == '' or name.endswith(','):
                name = ' '.join(section.split()[0:3])

        nameSplit = name.split()
        nameSplit = list(filter(None, nameSplit))
        if len(nameSplit) == 3:
            if nameSplit[1].endswith(','):
                if nameSplit[1].lower() in ['jr', 'sr'] or nameSplit[1].lower().replace('i', '') == '':
                    firstName = nameSplit[2]
                    lastName = nameSplit[0]
                    srJr = nameSplit[1].replace(',', '')
                    middleName = ''
                else:
                    firstName = nameSplit[2]
                    lastName = nameSplit[0] + ' ' + nameSplit[1].replace(',', '')
                    srJr = ''
            else:
                firstName = nameSplit[0]
                if nameSplit[1].lower().replace('.', '') in ['jr', 'sr'] or nameSplit[1].lower().replace('i', '') == '':
                    srJr = ''
                middleName = nameSplit[1]
                lastName = nameSplit[2]
        elif len(nameSplit) == 2:
            if nameSplit[0].endswith(','):
                lastName = nameSplit[0].replace(',', '')
                firstName = nameSplit[1]
                srJr = ''
                middleName = ''
            else:
                firstName = nameSplit[0]
                lastName = nameSplit[0]
                srJr = ''
                middleName = ''
        else:
            print(nameSplit)
            input()

        # Now let's get DOB!
        if 'date of birth' in all_of_it.lower():
            section = all_of_it[all_of_it.lower().index('date of birth') + len('date of birth'):]
            section = section[:section.index('\n')].strip()
            section = ' '.join(section.split()[0:3])
        elif 'DDAATTEE  OOFF  BBIIRRTTHH' in all_of_it:
            section = all_of_it[all_of_it.index('DDAATTEE  OOFF  BBIIRRTTHH') + len('DDAATTEE  OOFF  BBIIRRTTHH'):]
            section = section[:section.index('\n')]
        else:
            print(all_of_it)
            input()
        birthdate = section
        if not birthdate.split()[0].isnumeric():
            lineNum = 0
            while 'Date of Birth' not in all_of_it.split('\n')[lineNum]:
                lineNum = lineNum + 1
            birthdate = all_of_it.split('\n')[lineNum - 1] + ' ' + all_of_it.split('\n')[lineNum + 1]
        if not birthdate.split()[0].isnumeric():
            print(birthdate)
            input()


        # Now let's get diagnosis
        all_of_it = all_of_it.replace('DDIISSEEAASSEE', 'DISEASE')
        if 'TUMOR TYPE:' in all_of_it:
            section = all_of_it[all_of_it.index('TUMOR TYPE:') + len('TUMOR TYPE:'):].split('\n')
            if 'PATIENT RESULTS' in section[1] and len(section[1].replace('PATIENT RESULTS', '')) < 2 and '†' not in section[1]:
                sectionStart = section[0].strip()
                section = sectionStart + ' ' + section[2].strip()
            elif section[1].isupper() and '†' not in section[1]:
                sectionStart = section[0].strip()
                section = sectionStart + ' ' + section[1].replace('PATIENT RESULTS ', '').strip()
            else:
                section = section[0].strip()
        elif 'DISEASE' in all_of_it:
            startLine = 0
            while 'DISEASE' not in all_of_it.split('\n')[startLine]:
                startLine = startLine + 1
            section = all_of_it[all_of_it.index('DISEASE') + len('DISEASE'):]
            if 'ORDERING' in section:
                if section.index('ORDERING') < section.index('\n'):
                    endText = 'ORDERING'
                else:
                    endText = '\n'
            else:
                endText = '\n'
            section = section[:section.index(endText)].strip()
            if all_of_it.split('\n')[startLine+1].split()[0].islower() and not any(x in all_of_it.split('\n')[startLine+1] for x in ['dduuee', 'ssttaatt']):
                line = all_of_it.split('\n')[startLine+1]
                pos = 0
                while line.split()[pos].islower():
                    section = section + ' ' + line.split()[pos]
                    pos = pos + 1
            if ')' in all_of_it.split('\n')[startLine+1].split()[0]:
                section = section + ' ' + all_of_it.split('\n')[startLine+1].split()[0]
        for x in ['oonn', 'failed', 'MMii', 'MMSS', 'detection', 'processing', 'signatures', 'ssaa', 'iinnc', 'number', 'SSee']:
            if x in section:
                section = section[:section.index(x)]

        diagnosis = section

        # Finally, the site
        all_of_it = all_of_it.replace('SSPPEECCIIMMEENN  SSIITTEE', 'SPECIMENT SITE').replace('SPECIMENT SITE', 'SPECIMEN SITE')
        if 'SPECIMEN SITE' in all_of_it:
            section = all_of_it[all_of_it.index('SPECIMEN SITE') + len('SPECIMEN SITE'):]
            section = section[:section.index('\n')].strip()
        elif 'Specimen Site' in all_of_it:
            section = all_of_it[all_of_it.index('Specimen Site') + len('Specimen Site'):]
            section = section[:section.index('\n')].strip()
            if section == '':
                x = 0
                while 'Specimen Site' not in all_of_it.split('\n')[x]:
                    x = x + 1
                section = all_of_it.split('\n')[x-1] + ' ' + all_of_it.split('\n')[x+1]
        else:
            section = 'Not Given'
        wordSpot = 0
        foundOne = False
        for x in range(0, len(section.split())):
            if not ((section.split()[x][0].isupper() and section.split()[x][1:].islower()) or (section.split()[x].islower()) or (')' in section.split()[x] and '(' in section.split()[x])):
                if not foundOne:
                    foundOne = True
                    wordSpot = x
        if wordSpot != 0:
            section = ' '.join(section.split()[0:wordSpot])
        ends = ['Genomic', 'For']
        for x in ends:
            if x in section:
                section = section[:section.index(x)]
        section = section.strip()
        specimenSite = section

        # Now we're getting the type if available
        if 'Specimen Type' in all_of_it:
            section = all_of_it[all_of_it.index('Specimen Type') + len('Specimen Type'):]
            section = section[:section.index('\n')].strip()
        elif 'SPECIMEN TYPE' in all_of_it:
            section = all_of_it[all_of_it.index('SPECIMEN TYPE') + len('SPECIMEN TYPE'):]
            section = section[:section.index('\n')].strip()
        elif 'SSPPEECCIIMMEENN  TTYYPPEE' in all_of_it:
            section = all_of_it[all_of_it.index('SSPPEECCIIMMEENN  TTYYPPEE') + len('SSPPEECCIIMMEENN  TTYYPPEE'):]
            section = section[:section.index('\n')].strip()
        else:
            section = 'Not Given'
            print(all_of_it)
            input()
        wordSpot = 0
        foundOne = False
        for x in range(0, len(section.split())):
            if not ((section.split()[x][0].isupper() and section.split()[x][1:].islower()) or (section.split()[x].islower()) or (')' in section.split()[x] and '(' in section.split()[x])):
                if not foundOne:
                    foundOne = True
                    wordSpot = x
        if wordSpot != 0:
            section = ' '.join(section.split()[0:wordSpot])
        specimenType = section

        primary = 'Not Given'
        sectionStarts = [#'AADDDDIITTIIOONNAALL  AASSSSAAYYSS::  FFOORR  TTHHEE  DDEETTEECCTTIIOONN  OOFF  SSEELLEECCTT  CCAANNCCEERR  BBIIOOMMAARRKKEERRSS',
                         'DNA Gene List: For the Detection of Select Rearrangements',
                         'DNA Gene List: For the Detection Select Rearrangements',
                         'DNA Gene List: Select Exonic Sequence for the Detection of Base Substitutions, Insertions/Deletions, and Copy Number Alterations',
                         'DNA Gene List: Entire Coding Sequence for the Detection of Base Substitutions, Insertion/Deletions, and Copy Number Alterations',
                         'DNA Gene List: Entire Exonic Sequence for the Detection of Base Substitutions, Insertions/Deletions, and Copy Number Alterations',
                         'Hematological Malignancy DNA Gene List: Select Rearrangements',
                         'Hematological Malignancy RNA Gene List: Select Rearrangements',
                         'Hematological Malignancy DNA Gene List: Entire Coding Sequence (Base Substitutions, Indels, Copy Number Alterations)',
                         'RNA Gene List: For the Detection of Select Gene Fusions',
                         'Select Rearrangements',
                         'DDNNAA  GGEENNEE  LLIISSTT::  EENNTTIIRREE  CCOODDIINNGG  SSEEQQUUEENNCCEE  FFOORR  TTHHEE  DDEETTEECCTTIIOONN  OOFF  BBAASSEE  SSUUBBSSTTIITTUUTTIIOONNSS,,  IINNSSEERRTTIIOONN//DDEELLEETTIIOONNSS,,\nAANNDD  CCOOPPYY  NNUUMMBBEERR  AALLTTEERRAATTIIOONNSS',
                         'DDNNAA  GGEENNEE  LLIISSTT::  FFOORR  TTHHEE  DDEETTEECCTTIIOONN  OOFF  SSEELLEECCTT  RREEAARRRRAANNGGEEMMEENNTTSS',
                         'DDNNAA  GGEENNEE  LLIISSTT::  SSEELLEECCTT  EEXXOONNIICC  SSEEQQUUEENNCCEE  OOFF  TTHHEE  DDEETTEECCTTIIOONN  OOFF  BBAASSEE  SSUUBBSSTTIITTUUTTIIOONNSS,,  IINNSSEERRTTIIOONNSS//\nDDEELLEETTIIOONNSS,,  AANNDD  CCOOPPYY  NNUUMMBBEERR  AALLTTEERRAATTIIOONNSS',
                         'DDNNAA  GGEENNEE  LLIISSTT::  EENNTTIIRREE  CCOODDIINNGG  SSEEQQUUEENNCCEE  FFOORR  TTHHEE  DDEETTEECCTTIIOONN  OOFF  BBAASSEE  SSUUBBSSTTIITTUUTTIIOONNSS,,  IINNSSEERRTTIIOONN//\nDDEELLEETTIIOONNSS,,  AANNDD  CCOOPPYY  NNUUMMBBEERR  AALLTTEERRAATTIIOONNSS',
                         'DDNNAA  GGEENNEE  LLIISSTT::  EENNTTIIRREE  CCOODDIINNGG  SSEEQQUUEENNCCEE  FFOORR  TTHHEE  DDEETTEECCTTIIOONN  OOFF  BBAASSEE  SSUUBBSSTTIITTUUTTIIOONNSS,,  IINNSSEERRTTIIOONN//DDEELLEETTIIOONNSS,,  AANNDD  CCOOPPYY  NNUUMMBBEERR\nAALLTTEERRAATTIIOONNSS',
                         'HHEEMMAATTOOLLOOGGIICCAALL  MMAALLIIGGNNAANNCCYY  DDNNAA  GGEENNEE  LLIISSTT::  EENNTTIIRREE  CCOODDIINNGG  SSEEQQUUEENNCCEE  FFOORR  TTHHEE  DDEETTEECCTTIIOONN  OOFF  BBAASSEE\nSSUUBBSSTTIITTUUTTIIOONNSS,,  IINNSSEERRTTIIOONN//DDEELLEETTIIOONNSS,,  AANNDD  CCOOPPYY  NNUUMMBBEERR  AALLTTEERRAATTIIOONNSS',
                         'HHEEMMAATTOOLLOOGGIICCAALL  MMAALLIIGGNNAANNCCYY  RRNNAA  GGEENNEE  LLIISSTT::  FFOORR  TTHHEE  DDEETTEECCTTIIOONN  OOFF  SSEELLEECCTT  RREEAARRRRAANNGGEEMMEENNTTSS',
                         'Reportable Alterations Identified†',
                         'reflect new knowledge about cancer biology.',
                         'captured with\nincreased sensitivity.'
                         ]
        negExon = [#'Not Given',
                   'Not Given', 'Not Given', 'Select', 'Entire', 'Entire', 'Not Given', 'Not Given', 'Entire', 'Not Given', 'Not Given', 'Entire', 'Not Given', 'Select', 'Entire', 'Entire', 'Entire', 'Not Given', 'Not Given', 'Not Given', 'Select']
        negPlatforms = [#'MSI/TMB',
                        'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS']
        negType = [#'MIS/TMB',
                   'DNA Rearrangement', 'DNA Rearrangement', 'DNA Sub/Indel/CNA', 'DNA Sub/Indel/CNA', 'DNA Sub/Indel/CNA', 'DNA Rearrangement', 'RNA Rearrangement', 'DNA Sub/Indel/CNA', 'RNA Fusions', 'DNA Rearrangement', 'DNA Sub/Indel/CNA', 'DNA Rearrangement', 'DNA Sub/Indel/CNA', 'DNA Sub/Indel/CNA', 'DNA Sub/Indel/CNA',  'DNA Sub/Indel/CNA', 'RNA Rearrangement', 'DNA Sub/Indel/CNA', 'DNA Sub/Indel/CNA', 'Complete']
        negCall = [#'MSI/TMB',
                   'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, inferred', 'Negative, Explicit', 'Negative, inferred', 'Negative, inferred']

        negGeneList = []
        negExonList = []
        negTypeList = []
        negPlatformList = []
        negCallList = []

        posGeneList = []
        vusGeneList = []

        posGeneTs = []
        posTypes = []
        vusTypes = []

        sectionEnds = ['DDNNAA', 'DNA Gene', '*Note:', 'For more', 'See professional',  'about cancer biology.', '*TERC', 'Electronically', 'DNA Gene', 'Additional Assays',
                       'AADDDDIITTIIOONNAALL  AASSSSAAYYSS::', 'Hematological', 'HHEEMMAATTOOLLOOGGIICCAALL', 'nnoo  rreeppoorrttaabbllee', 'Additional Disease-relevant',
                       '†  For', 'II Reduced', 'clinical trial', 'QQUUAALLIIFFIIEEDD  AALLTTEERRAATTIIOONN', 'For additional', 'As new', 'INDICATIONS']

        # This is a liquid test - I NEED TO GET THIS READ BETTER
        if not any(x in all_of_it for x in sectionStarts):
            continue
        if 'Liquid CDx' in all_of_it or any(f in txt for f in
                                            ['TRF320296.d3930afd-f0df-4cbb-91ed-4cd61e42decd', '5e849c7f-e1ad-4765-81f9-09a936b70a81', 'fmi_file.402a8a0b-a5de-4db2-8af6-465cb5b1313b',
                                             '516c28f0-721e-42c2-b80b-b557b7753c34']):
            continue

        while any(x in all_of_it for x in sectionStarts):
            for x in sectionStarts:
                if x in all_of_it:
                    index = sectionStarts.index(x)
                    wholeSection = all_of_it[all_of_it.index(x):]
                    section = all_of_it[all_of_it.index(x) + len(x):]
                    endPos = 999999999999
                    if not any(y in section for y in sectionEnds):
                        print(all_of_it)
                        input()
                    endChoice = ''
                    for z in sectionEnds:
                        if z in section:
                            if section.index(z) < endPos:
                                endPos = section.index(z)
                                endChoice = z
                    section = section[:endPos]
                    if endChoice == 'clinical trial':
                        if section.split()[-1].isnumeric():
                            section = ' '.join(section.split()[:-1])
                    wholeSection = wholeSection[:endPos+len(x)]
                    all_of_it = all_of_it.replace(wholeSection, '')
                    exons = ''
                    if len(section.split()) > 0:
                        if len(section.split()[0]) > 3:
                            if section.split()[0][0] == section.split()[0][1] and section.split()[0][2] == section.split()[0][3]:
                                for word in section.split():
                                    if len(word) > 3:
                                        if word[0] == word[1] and word[2] == word[3]:
                                            newWord = word
                                            evenWord = []
                                            oddWord = []
                                            for i in range(0, len(newWord)):
                                                if i % 2:
                                                    evenWord.append(newWord[i])
                                                else:
                                                    oddWord.append(newWord[i])
                                            newWord = ''.join(oddWord)
                                            section = section.replace(word, newWord)
                                while '  ' in section:
                                    section = section.replace('  ', ' ')
                    section = section.replace(' (Coding Exons ', ', (Coding_Exons_')
                    hasExons = False
                    sameLineParens = False
                    if not any(v.startswith('(') for v in section.split('\n')):
                        sameLineParens = True
                    if 'Exon' in section:
                        hasExons = True
                        section = section.replace('Exons', 'Exon')
                        genes = ''
                        exons = ''
                        for line in section.split('\n'):
                            if 'Exon' in line.replace('Coding_Exon', ''):
                                line = line.split('Exon ')
                                for lp in range(0, len(line)):
                                    line[lp] = line[lp].replace(', ', ',')
                                    if line[lp].endswith(','):
                                        line[lp] = line[lp] + ' '
                                line = 'Exon '.join(line)
                                exons = exons + ' ' + line
                            # Dealing with mutli-line exons here
                            elif line.replace(' ','').replace(',', '').replace('-', '').replace('(Coding_Exon_', '').replace(')', '').isnumeric():
                                line = line.replace('(Coding_Exon_', '(coding_exon_')
                                toAdd = line.split()
                                exons = exons.split()
                                for expos in range(0, len(toAdd)):
                                    added = False
                                    for exopos in range(0, len(exons)):
                                        if exons[exopos].endswith(',') and not added:
                                            added = True
                                            exons[exopos] = exons[exopos] + toAdd[expos]
                                exons = ' '.join(exons)
                            else:
                                genes = genes + ' ' + line
                        exons = exons.replace(' (', ' Exon (')
                        exons = exons.split('Exon')[1:]
                        for ex in range(0, len(exons)):
                            exons[ex] = exons[ex].strip()
                            exons[ex] = exons[ex].replace(' ', ',').replace(',,', ',').replace('er,', 'er ')
                            if exons[ex].endswith(','):
                                exons[ex] = exons[ex][:-1]
                        genes = genes.replace(' (', '_(').split()
                        genes = list(filter(None, genes))
                    else:
                        genes = section.split()
                        genes = list(filter(None, genes))
                    for a in range(0, len(genes)):
                        while genes[a].endswith('*'):
                            genes[a] = genes[a][:-1]
                        if genes[a] not in ['Microsatellite', 'Status', '(MS)', 'Tumor', 'Mutational', 'Burden', '(TMB)']:
                            if ('(' in genes[a] and genes[a].startswith('(')) or (genes[a] in ['or']) or (')' in genes[a] and not genes[a].startswith('(') and not '_' in genes[a] and genes[a].endswith(')')):
                                if hasExons or sameLineParens:
                                    negGeneList[-1] = negGeneList[-1] + ' ' + genes[a]

                                else:
                                    parens = ['(FAM123B)', '(EMSY)', '(C17orf39)', '(MYST3)', '(promoter', 'only)', '(MYCL1)', '(MLL)', '(MLL3)', '(MLL2)', '(WTX)', '(MYST3)', '(C11orf30)', '(GID4)']
                                    assoGenes = ['AMER1', 'C11orf30', 'GID4', 'KAT6A', 'TERT', 'TERT (promoter', 'MYCL', 'KMT2A', 'KMT2C', 'KMT2D', 'FAM123B', 'KAT6A', 'EMSY', 'C17orf30']
                                    if genes[a] not in negGeneList:
                                        if genes[a].startswith('(') or genes[a].endswith(')'):
                                            if genes[a] in parens:
                                                for k in range(0, len(parens)):
                                                    if parens[k] == genes[a]:
                                                        if assoGenes[k] in negGeneList:
                                                            negGeneList[negGeneList.index(assoGenes[k])] = negGeneList[negGeneList.index(assoGenes[k])] + ' ' + genes[a]
                                                continue
                                            else:
                                                print(txt)
                                                print("GOT ONE THAT'S WEIRD")
                                                print(genes[a])
                                                print(negGeneList)
                                                input()
                            else:
                                if genes[a] not in negGeneList:
                                    negGeneList.append(genes[a])
                                    if exons == '':
                                        negExonList.append(negExon[index])
                                    else:
                                        negExonList.append(exons[a])
                                    negCallList.append(negCall[index])
                                    negPlatformList.append(negPlatforms[index])
                                    negTypeList.append(negType[index])
                                else:
                                    negTypeList[negGeneList.index(genes[a])] = negTypeList[negGeneList.index(genes[a])] + ', ' + negType[index]
                                    if exons != '':
                                        negExonList[negGeneList.index(genes[a])] = negExonList[negGeneList.index(genes[a])] + ', ' + exons[genes.index(genes[a])]
                                    else:
                                        negExonList[negGeneList.index(genes[a])] = negExonList[negGeneList.index(genes[a])] + ', ' + negExon[index]

        for part in range(0, len(negGeneList)):
            if '_' in negGeneList[part]:
                negGeneList[part] = negGeneList[part].replace('_', ' ')

        # Now let's get the positives!
        positivesStarts = ['MEDICAL RECORD',
                           'GENOMIC FINDINGS WITH NO REPORTABLE THERAPEUTIC OR CLINICAL TRIAL OPTIONS',
                           'MMiiccrroossaatteelllliittee  ssttaattuuss',
                           'TTuummoorr  MMuuttaattiioonnaall  BBuurrddeenn',
                           'Genomic Alterations Identified†',
                           'Genomic Alteration Identified†',
                           'GGEENNOOMMIICC  FFIINNDDIINNGGSS MMAAFF  %%',
                           'OOTTHHEERR  AALLTTEERRAATTIIOONNSS  &&  BBIIOOMMAARRKKEERRSS  IIDDEENNTTIIFFIIEEDD',
                           'GENE ALTERATIONS WITH NO REPORTABLE THERAPEUTIC OR CLINICAL TRIALS OPTIONS',
                           'GGEENNOOMMIICC  FFIINNDDIINNGGSS',
                           'Interpretive content on this page and subsequent Biomarker Findings',
                           'PPAATTIIEENNTT',
                           'GENOMIC FINDINGS DETECTED',
                           ]
        positivesEnds = ['Electronically', 'PPAATTIIEENNTT', 'Genomic Alterations', 'THERAPEUTIC IMPLICATIONS', 'For more comprehensive', 'PPOOTTEENNTTIIAALL', 'AALLTTEERRAATTIIOONN',
                         'GENE ALTERATIONS WITH', 'the agents listed', 'Refer to', 'patients with', 'Increased', 'Patient may', 'nnoo  rreeppoorrttaabbllee', 'DISEASE',
                         'AARREEAASS  OOFF', 'Additional Disease-relevant Genes with No', 'AAPPPPRROOVVEEDD  IINNDDIICCAATTIIOONNSS', 'clinical trial ', '†For a',
                         'OOTTHHEERR  AALLTTEERRAATTIIOONNSS', 'wwiitthh  CClliinniiccaall  BBeenneeffiitt', '§ Refer to']

        posPlatforms = ['NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS', 'NGS']
        posCall = ['Positive', 'Positive', 'MS', 'TMB', 'Positive', 'Positive', 'Positive', 'Positive', 'Positive']

        all_of_it = all_of_it.replace('Mutation Burden', 'Mutational Burden')
        positiveBits = []
        anyBits = []
        # This marker is for reports where the gene name and the variants are pushed together
        smushedSection = False
        while any(x in all_of_it for x in positivesStarts):
            for y in positivesStarts:
                if y in all_of_it:
                    section = all_of_it[all_of_it.index(y):]
                    origSection = section
                    endPos = 9999999999999
                    for z in positivesEnds:
                        if z in section and z not in y and y not in z:
                            if section.index(z) < endPos:
                                endPos = section.index(z)

                    if y == 'Interpretive content on this page and subsequent Biomarker Findings' and lastName == 'Ostergaard':
                        endPos = section.index('SPECIMEN RECEIVED')

                    section = section[:endPos]
                    newSection = ''
                    # IN THIS BIT, I pull out the positive results and their findings
                    sectionCopy = section
                    for word in sectionCopy.split():
                        if len(word) > 3:
                            if word[0] == word[1] and word[2] == word[3]:
                                newWord = word
                                evenWord = []
                                oddWord = []
                                for i in range(0, len(newWord)):
                                    if i % 2:
                                        evenWord.append(newWord[i])
                                    else:
                                        oddWord.append(newWord[i])
                                newWord = ''.join(oddWord)
                                sectionCopy = sectionCopy.replace(word, newWord + ' ')
                    if ('Microsatellite' in sectionCopy and not any(x in sectionCopy for x in ['Interpretive content'])) or 'GENOMIC FINDINGS WITH NO REPORTABLE' in sectionCopy\
                            or ('GENOMIC FINDINGS DETECTED') in sectionCopy or 'Identified†' in sectionCopy or 'MEDICAL RECORD' in sectionCopy or 'For a complete list' in sectionCopy:
                        positiveBits.append(sectionCopy)

                    anyBits.append(sectionCopy)

                    newSection = section.replace('\n', ' ')
                    for word in section.replace('\n', ' ').split():
                        if len(word) > 3:
                            if word[0] == word[1] and word[2] == word[3]:
                                newWord = word
                                evenWord = []
                                oddWord = []
                                for i in range(0, len(newWord)):
                                    if i % 2:
                                        evenWord.append(newWord[i])
                                    else:
                                        oddWord.append(newWord[i])
                                newWord = ''.join(oddWord)
                                newSection = newSection.replace(word, newWord)

                    newSection = newSection.replace('  --', ' ')
                    while '  ' in newSection:
                        newSection = newSection.replace('  ', ' ')

                    # This is to catch a weirdly-formatted table that shows up on page 1
                    if 'no reportable alterations' in newSection:
                        newSection = newSection[:newSection.index('no reportable alterations')]

                    if 'MS-' in newSection and not addedMSI:
                        ms = newSection[newSection.index('MS-'):]
                        if ' ' in ms:
                            ms = ms[:ms.index(' ')]
                        ms = ms.replace('§', '')
                        addedMSI = True

                    if 'Microsatelite status' in newSection and 'Canot Be Determined' in newSection and not addedMSI:
                        ms = 'Cannot Be Determined'
                        addedMSI = True

                    if 'Mutational Burden ' in newSection.replace('-', ' ') and not addedTMB:
                        if '/Mb' not in newSection:
                            if 'Canot Be Determined' in newSection:
                                tmb = 'Cannot be Determined'
                                addedTMB = True
                        else:
                            tmb = newSection.replace('-',' ')[newSection.replace('-',' ').index('Mutational Burden ') + len('Mutational Burden '):newSection.replace('-',' ').index('/Mb') + len('/Mb')]
                            tmb = tmb.replace('§', '')
                            addedTMB = True
                    if 'Muts/Mb' in newSection and not addedTMB:
                        for word in range(0, len(newSection.split())):
                            if newSection.split()[word] == 'Muts/Mb':
                                tmb = newSection.split()[word-1] + ' ' + 'Muts/Mb'
                                addedTMB = True
                                break

                    if 'MSI Status Undetermined' in newSection and not addedMSI:
                        ms = 'MSI-Undetermined'
                        addedMSI = True
                    all_of_it = all_of_it.replace(section, '')

                    # Taking out medication information
                    for word in newSection.split():
                        if word.replace(')', '').endswith(('nib', 'mab', 'mus', '®', 'rif', 'bix')):
                            newSection = newSection.replace(word, '')
                    while '  ' in newSection:
                        newSection = newSection.replace('  ', ' ')
                    # Occasionally we get results like 'KRAS/NRAS x'
                    if '/' in newSection:
                        if 'CDKN2A/B' in newSection and 'CDKN2A/B ' not in newSection:
                            newSection = newSection.replace('CDKN2A/B', 'CDKN2A/B ')
                        if 'CDKN2A/B' in newSection:
                            newSection = newSection.replace('CDKN2A/B', 'CDKN2A/CDKN2B')
                        for word in newSection.split():
                            if '/' in word and word in newSection.split():
                                if word.split('/')[0] in negGeneList and word.split('/')[1] in negGeneList:
                                    thisSec = newSection.split()[newSection.split().index(word):]
                                    if len(thisSec) == 1:
                                        break
                                    endInd = 1
                                    while thisSec[endInd] not in negGeneList and thisSec[endInd] not in ['Tumor', 'Microsatellite', 'For']:
                                        if endInd == len(thisSec) - 1:
                                            break
                                        endInd = endInd + 1
                                    wholeSec = ' '.join(thisSec[:endInd])
                                    bit1 = word.split('/')[0] + ' ' + ' '.join(thisSec[1:endInd])
                                    bit2 = word.split('/')[1] + ' ' + ' '.join(thisSec[1:endInd])
                                    newSection = newSection.replace(wholeSec, bit1 + ' ' + bit2)
                    if 'Microsatelite status' in newSection or 'Microsatellite status' in newSection or 'GENOMIC FINDINGS DETECTED' in newSection or 'Identified†' in newSection or 'MEDICAL RECORD' in newSection or 'OTHER ALTERATIONS' in newSection:
                        for gen in range(0, len(negGeneList)):
                            origGene = negGeneList[gen]
                            gene = negGeneList[gen].replace('(', '').replace(')', '')
                            gene = gene.split()
                            added = False
                            for g in gene:
                                if g[0] == g[1]:
                                    g = ''.join(ch for ch, _ in itertools.groupby(g))
                                if (' ' + g + ' ' in newSection or '\n' + g + ' ' in newSection) and not added and origGene not in posGeneList and g not in ['Loss', 'of', 'Heterozygosity (LOH)', 'score', 'status', 'and', 'or']:
                                    posGeneList.append(origGene)
                        # It might be that we have results smushed together
                        if posGeneList == []:
                            for word in newSection.split():
                                if word[0].isupper() or '*' in word:
                                    biggestOne = ''
                                    # We also want to make sure we don't add two genes, for "ATR" and "ATRX" if the real gene is atrx, for instance
                                    for genn in negGeneList:
                                        if word.startswith(genn) and len(genn) > len(biggestOne):
                                            biggestOne = genn
                                    if biggestOne != '':
                                        posGeneList.append(biggestOne)
                            if len(posGeneList) > 0:
                                smushedSection = True
        for i in range(0, len(positiveBits)):
            positiveBits[i] = positiveBits[i].replace('\n', ' ')
        wholePositive = '\n'.join(positiveBits)
        while '  ' in wholePositive:
            wholePositive = wholePositive.replace('  ', ' ')
        # Un-split genes
        wholePositive = wholePositive.replace('los ', 'loss ')
        if smushedSection:
            for word in wholePositive.split():
                for gene in posGeneList:
                    if word.startswith(gene) and word != gene:
                        wholePositive = wholePositive.replace(word, gene + ' ' + word[len(gene):])

        # Taking out medication information
        for word in wholePositive.split():
            if word.replace(')', '').endswith(('nib', 'mab', 'mus', '®', 'rif', 'bix')):
                wholePositive = wholePositive.replace(word, '')
        # Occasionally we get results like 'KRAS/NRAS x'
        wholePositive = wholePositive.replace('\n', ' ')
        while '  ' in wholePositive:
            wholePositive = wholePositive.replace('  ', ' ')
        if 'CDKN2A/B' in wholePositive:
            wholePositive = wholePositive.replace('CDKN2A/B', 'CDKN2A/CDKN2B')
        if '/' in wholePositive:
            for word in wholePositive.split():
                if '/' in word:
                    if word.split('/')[0] in negGeneList and word.split('/')[1] in negGeneList:
                        thisSec = wholePositive.split()[wholePositive.split().index(word):]
                        endInd = 1
                        while thisSec[endInd] not in negGeneList and thisSec[endInd] not in ['Tumor', 'Microsatellite', 'For']:
                            if endInd == len(thisSec) - 1:
                                break
                            endInd = endInd + 1
                        wholeSec = ' '.join(thisSec[:endInd])
                        bit1 = word.split('/')[0] + ' ' + ' '.join(thisSec[1:endInd])
                        bit2 = word.split('/')[1] + ' ' + ' '.join(thisSec[1:endInd])
                        wholePositive = wholePositive.replace(wholeSec, bit1 + ' ' + bit2)
        while '  ' in wholePositive:
            wholePositive = wholePositive.replace('  ', ' ')
        wholePositive = wholePositive.replace('\n', ' ').split()

        # This section is to pull out the VUSs
        if 'the future.' in all_of_it:
            fullSection = []
            if 'VARIANTS OF UNKOWN SIGNIFICANCE' not in all_of_it:
                section = all_of_it[all_of_it.index('the future.') + len('the future.'):]
                section = section[:section.index('Electronically')]
                sectionEnders = ['The content', 'For more', 'To set', '†An', 'For additional']
                while any(nd in section for nd in sectionEnders):
                    for ndr in sectionEnders:
                        if ndr in section:
                            section = section[:section.index(ndr)]
            else:
                while 'VARIANTS OF UNKNOWN SIGNIFICANCE' in all_of_it:
                    section = all_of_it[all_of_it.index('VARIANTS OF UNKNOWN SIGNIFICANCE'):]
                    section = section[:section.index('Electronically')]
                    sectionEnders = ['The content', 'For more', 'To set', '†An', 'For additional']
    
                    while any(nd in section for nd in sectionEnders):
                        for ndr in sectionEnders:
                            if ndr in section:
                                section = section[:section.index(ndr)]
                    adder = section
                    if 'the future.' in adder:
                        adder = adder[adder.index('the future.') + len('the future.'):]
                    if 'SIGNIFICANCE' in adder:
                        adder = adder[adder.index('SIGNIFICANCE') + len('SIGNIFICANCE'):]
                    adder = adder.strip()
    
                    if adder != '':
                        fullSection.append(adder)
                    all_of_it = all_of_it.replace(section, '')
                section = '\n'.join(fullSection)
            # Tests that are mangled sometimes start like this
            if 'ThElecet' in section:
                section = section[:section.index('ThElecet')]

            if 'CDKN2A rearrangement' in section:
                section = section.replace('CDKN2A rearrangement', 'CDKN2A_rearrangement')

            # Let's see if we need to delete intermediates
            vusSection = section.split('\n')
            vusName = vusSection.copy()
            newVusSection = []
            newVusTypes = []

            # Ok, let's try this again
            vusName = list(filter(None, vusSection))

            for line in range(0, len(vusName)):
                if vusName[line] == 'amplification':
                    for word in vusName[line-1].split():
                        if word.endswith(',') and word.count(',') == 1:
                            vusName[line-1] = vusName[line-1].replace(word, word + ' ' + 'amplification')
                            vusName[line] = ''
                            break
            vusName = list(filter(None, vusName))

            activeGenes = []
            activeTypes = []
            for line in vusName:
                # We might have duplication of letters. Let's deal with it here.
                if len(line.split()) > 0:
                    firstGene = line.split()[0]
                    if len(firstGene) > 3:
                        if firstGene[0] == firstGene[1] and firstGene[2] == firstGene[3]:
                            for word in line.split():
                                newWord = word
                                evenWord = []
                                oddWord = []
                                for i in range(0, len(newWord)):
                                    if i % 2:
                                        evenWord.append(newWord[i])
                                    else:
                                        oddWord.append(newWord[i])
                                newWord = ''.join(oddWord)
                                line = line.replace(word, newWord)
                # Lil' Normalization
                if ' and ' in line:
                    # Sometimes the 'and' goes to a new line. If we could fill all the open slots on the active gene
                    # list by assuming we had [x] and (newline) and then on the next line [y], let's do that
                    if len(line.replace(' and', '_and ').split()) == len(activeGenes) - len(activeTypes):
                        line = line.replace(' and ', '_and ')
                    else:
                        beforeToken = line.split()[line.split().index('and')-1]
                        afterToken = line.split()[line.split().index('and')+1]
                        # I THINK this indicates that the next line has a del in it
                        if beforeToken.endswith('del') and not afterToken.endswith('del'):
                            line = line.replace(' and ', '_and ')
                            if len(line.split()) > len(activeGenes):
                                for word in range(0, len(line.split())):
                                    if 'and' in line.split()[word]:
                                        line = line.replace(line.split()[word-1] + ' ',line.split()[word-1] + '_')
                                        break
                        else:
                            line = line.replace(' and ', '_and_')
                if ' splice site ' in line:
                    nextToken = line.split()[line.split().index('site')+1]
                    if '>' in nextToken or '-' in nextToken or '+' in nextToken:
                        line = line.replace(' splice site ', ' splice_site_')
                    else:
                        line = line.replace(' splice site ', ' splice_site, ')
                elif 'splice site ' in line:
                    nextToken = line.split()[line.split().index('site')+1]
                    if '>' in nextToken or '-' in nextToken or '+' in nextToken:
                        line = line.replace('splice site ', 'splice_site_')
                    else:
                        line = line.replace('splice site ', 'splice_site, ')
                elif 'splice site' in line:
                    line = line.replace('splice site', 'splice_site,')
                elif 'promoter ' in line:
                    nextToken = line.split()[line.split().index('promoter')+1]
                    if '>' in nextToken or '-' in nextToken or '+' in nextToken:
                        line = line.replace('promoter ', 'promoter_')
                    else:
                        line = line.replace('promoter ', 'promoter, ')


                while ' (' in line:
                    line = line.replace(' (', '(')
                thisLine = line.split()
                thisLineCopy = thisLine.copy()

                # Can't hurt to be specific, right? We want to add this to splice sites
                if ('>' in ' '.join(thisLine)  or '+' in ' '.join(thisLine)) and 'splice_site' not in ' '.join(thisLine) and any(tr.endswith('site,') for tr in activeTypes):
                    toAdd = ''
                    for bit in range(0, len(thisLine)):
                        if '>' in thisLine[bit] or '+' in thisLine[bit]:
                            toAdd = thisLine[bit]
                    if any(b.endswith('site,') for b in activeTypes):
                        for bt in range(0, len(activeTypes)):
                            if activeTypes[bt].endswith('site,'):
                                activeTypes[bt] = activeTypes[bt].replace('site,', 'site_' + toAdd)
                                break
                        thisLine.remove(toAdd)
                elif ('>' in ' '.join(thisLine) or '+' in ' '.join(thisLine)) and 'splice_site' not in ' '.join(thisLine) and any(tr.endswith('-') for tr in activeTypes):
                    toAdd = ''
                    for bit in range(0, len(thisLine)):
                        if '>' in thisLine[bit] or '+' in thisLine[bit]:
                            toAdd = thisLine[bit]
                    if any(b.endswith('-') for b in activeTypes):
                        for bt in range(0, len(activeTypes)):
                            if activeTypes[bt].endswith('-'):
                                activeTypes[bt] = activeTypes[bt].replace('-', '-' + toAdd)
                                break
                        thisLine.remove(toAdd)


                if any(x in thisLine for x in ['Microsatellite', 'status', 'Tumor', 'Mutation', 'MS-Stable', 'MSI-Unknown', 'TMB-Unknown', 'Burden', 'Muts/Mb', 'TMB-Intermediate;',
                                               'TMB-Low;']):
                    for x in ['Microsatellite', 'status', 'Tumor', 'Mutation', 'MS-Stable', 'MSI-Unknown', 'TMB-Unknown', 'Burden', 'Muts/Mb', 'TMB-Intermediate;',
                              'TMB-Low;']:
                        if x in line:
                            thisLine.remove(x)
                if any(('.' in x and x.replace('.', '').isnumeric()) for x in thisLine):
                    for x in thisLine:
                        if '.' in x and x.replace('.', '').isnumeric():
                            thisLine.remove(str(x))

                # Stuff like 'a', no thanks.
                removalQueue = []
                for x in thisLine:
                    if any(yr.endswith('_and') for yr in activeTypes):
                        added = False
                        for yr in range(0, len(activeTypes)):
                            if activeTypes[yr].endswith('_and') and not added:
                                added = True
                                activeTypes[yr] = activeTypes[yr] + '_' + x
                                if x in thisLine:
                                    removalQueue.append(x)

                    if len(x) == 1:
                        if x in ['n'] and 'amplificatio' in ' '.join(activeTypes):
                            for bit in range(0, len(activeTypes)):
                                if 'amplificatio' in activeTypes[bit] and 'amplification' not in activeTypes[bit]:
                                    activeTypes[bit] = activeTypes[bit].replace('amplificatio', 'amplification')
                                    if x in thisLine:
                                        removalQueue.append(x)
                        elif x in ['o'] and 'amplificati' in ' '.join(activeTypes):
                            for bit in range(0, len(activeTypes)):
                                if 'amplificati' in activeTypes[bit] and 'amplification' not in activeTypes[bit]:
                                    activeTypes[bit] = activeTypes[bit].replace('amplificati', 'amplification')
                                    if x in thisLine:
                                        removalQueue.append(x)
                        else:
                            if x in thisLine:
                                removalQueue.append(x)

                    # I'm going to ASSUME the longest string is the one that  got cut off
                    if x in ['del']:
                        max_len = -1
                        for ele in activeTypes:
                            if len(ele) > max_len:
                                max_len = len(ele)
                                res = ele
                        activeTypes[activeTypes.index(res)] = activeTypes[activeTypes.index(res)] + x

                    if len(x) == 2:
                        if x == 'el' and any(r.endswith('d') for r in activeTypes):
                            for bit in range(0, len(activeTypes)):
                                if activeTypes[bit].endswith('d'):
                                    activeTypes[bit] = activeTypes[bit] + 'el'
                            if x in thisLine:
                                removalQueue.append(x)
                        elif x == 'on' and any(r.endswith('cati') for r in activeTypes):
                            for bit in range(0, len(activeTypes)):
                                if activeTypes[bit].endswith('cati'):
                                    activeTypes[bit] = activeTypes[bit] + 'on'
                            if x in thisLine:
                                removalQueue.append(x)
                        # This is a gene
                        elif x in ['AR', 'FH', 'PC']:
                            pass
                        else:
                            if x in thisLine:
                                removalQueue.append(x)

                for x in removalQueue:
                    if x in thisLine:
                        thisLine.remove(x)

                while len(thisLine) > 0:
                    bit = thisLine[0]
                    if bit == 'CCARDD1111':
                        bit = 'CCAARRDD1111'
                    if bit == 'ARIIDD11AA':
                        bit = 'AARRIIDD11AA'
                    if bit == 'BCORLL11':
                        bit = 'BBCCOORRLL11'
                    if bit == 'BBARDD11':
                        bit = 'BBAARRDD11'
                    if bit == 'PCLLOO':
                        bit = 'PPCCLLOO'
                    if bit == 'MYCLL11':
                        bit = 'MMYYCCLL11'
                    if bit == 'ARFFRRPP11':
                        bit = 'AARRFFRRPP11'
                    if bit == 'ARAAFF':
                        bit = 'AARRAAFF'
                    if bit in ['BBCCOORRLL11', 'AARRIIDD11AA', 'CCAARRDD1111', 'BBAARRDD11', 'PPCCLLOO', 'MMYYCCLL11', 'AARRFFRRPP11', 'AARRAAFF']:
                        evenWord = []
                        oddWord = []
                        for i in range(0, len(bit)):
                            if i % 2:
                                evenWord.append(bit[i])
                            else:
                                oddWord.append(bit[i])
                        bit = ''.join(oddWord)
                        thisLine[0] = ''.join(oddWord)
                    if '(' in bit:
                        bit = bit.replace('(', ' (')

                    # Let's concat stuff if it's commas - AND if we have commas already
                    if any(prev.endswith(',') for prev in activeTypes):
                        if bit.endswith(',') and not thisLine[-1] == bit:
                            if thisLine[thisLine.index(bit)+1].endswith(',') or len(thisLine) == 2:
                                thisLine[thisLine.index(bit):thisLine.index(bit) + 2] = [''.join(thisLine[thisLine.index(bit):thisLine.index(bit) + 2])]
                                bit = thisLine[0]

                    # is only the very last number duplicated?
                    if bit[-1] == bit[-2]:
                        if bit[:-1] in negGeneList:
                            thisLine[thisLine.index(bit)] = bit[:-1]
                            bit = bit[:-1]

                    # Does it mess things up to handle commas here? Assuming no gene will have a ','
                    if bit.endswith(',') and len(thisLine) > 1:
                        if thisLine[thisLine.index(bit)+1].endswith(','):
                            newBit = bit + thisLine[thisLine.index(bit)+1]
                            thisLine.remove(thisLine[thisLine.index(bit)+1])
                            thisLine.remove(bit)
                            bit = newBit
                            thisLine.insert(0, bit)
                            # Extremely short next bits can squeeze in
                            if len(thisLine) > 1:
                                if len(thisLine[1]) <= 3:
                                    newBit = bit + thisLine[thisLine.index(bit) + 1]
                                    thisLine.remove(thisLine[thisLine.index(bit) + 1])
                                    thisLine.remove(bit)
                                    bit = newBit
                                    thisLine.insert(0, bit)
                        else:
                            if 'splice_site' not in bit and bit.count(',') < 2:
                                newBit = bit + thisLine[thisLine.index(bit)+1]
                                thisLine.remove(thisLine[thisLine.index(bit)+1])
                                thisLine.remove(bit)
                                bit = newBit
                                thisLine.insert(0, bit)

                    # Some genes don't show up on the list???
                    if (bit in ' '.join(negGeneList) or bit in ['RAD51L3', 'RAD51L1', 'PDCD1 (PD-1)', 'WHSC1 (MMSET)', 'MAP3K1', 'MYST3', 'MLL2', 'MLL3', 'MLL', 'PMS2', 'SYK',
                                                               'CDKN2A/B', 'MYCL1', 'C17ORF39', 'DIS3', 'MAP3K13', 'FAM123B', 'C17orf39', 'MAP2K2 (MEK2)', 'EWSR1',
                                                                'RUNX1T1', 'NSD1'] \
                            or ('C11ORF30' in bit and 'C11orf30' in ' '.join(negGeneList)))\
                            and bit not in ['A2T', 'L7R']:
                        activeGenes.append(bit.replace(' (', '('))
                        thisLine.remove(bit.replace(' (', '('))
                    elif bit in ['site'] and any(b.endswith('splice') for b in activeTypes):
                        for b in activeTypes:
                            if b.endswith('splice'):
                                activeTypes[activeTypes.index(b)] = activeTypes[activeTypes.index(b)] + '_site'
                                thisLine.remove(bit)
                                break
                    # If we have any open comma slots, put it in! (Unless we have an open gene slot?)
                    elif any(open.endswith(',') and open not in ['splice_site,'] and not open.count(',') % 2 == 0 for open in activeTypes) and not bit.endswith(',') and (len(activeGenes) <= len(activeTypes) or len(thisLine) == 1):
                        firstCom = 0
                        while not activeTypes[firstCom].endswith(','):
                            firstCom = firstCom + 1
                        activeTypes[firstCom] = activeTypes[firstCom] + bit
                        thisLine.remove(bit)
                    elif any(oper.endswith(',') and oper not in ['splice_site,'] and oper.count(',') % 2 == 0 and oper.split(',')[0] + ',' not in thisLineCopy for oper in activeTypes) and bit.count(',') == 2:
                        for oper in activeTypes:
                            if oper.endswith(',') and oper not in ['splice_site,'] and oper.count(',') % 2 == 0 and oper.split(',')[0] + ',' not in thisLineCopy:
                                activeTypes[activeTypes.index(oper)] = activeTypes[activeTypes.index(oper)] + bit
                                thisLine.remove(bit)
                    elif any(oper.endswith(',') and oper not in ['splice_site,'] and oper.count(',') % 2 == 0 and oper.split(',')[0] + ',' not in thisLineCopy for oper in activeTypes) and bit.count(',') == 1 and ',' not in ' '.join(thisLine[1:]):
                        for oper in activeTypes:
                            if oper.endswith(',') and oper not in ['splice_site,'] and oper.count(',') % 2 == 0 and oper.split(',')[0] + ',' not in thisLineCopy:
                                activeTypes[activeTypes.index(oper)] = activeTypes[activeTypes.index(oper)] + bit
                                thisLine.remove(bit)

                    elif len(activeTypes) < len(activeGenes):
                        activeTypes.append(bit)
                        thisLine.remove(bit.replace(' (', '('))
                    else:
                        # We will frequently have two commas
                        if sum(1 for i in activeTypes if i.endswith(',')) == 2 and len(thisLine) == 1:
                            firstInd = 0
                            while not activeTypes[firstInd].endswith(','):
                                firstInd = firstInd + 1
                            activeTypes[firstInd:firstInd+2] = [''.join(activeTypes[firstInd:firstInd+2])]
                            if len(thisLine) == 1:
                                activeTypes.append(thisLine[0])
                                thisLine.remove(thisLine[0])
                        if len(thisLine) == 1:
                            if any(x.endswith(',') for x in activeTypes):
                                for type in range(0, len(activeTypes)):
                                    if activeTypes[type].endswith(','):
                                        activeTypes[type] = activeTypes[type] + thisLine[0]
                                        thisLine.remove(thisLine[0])

                            elif thisLine[0] == 'and':
                                activeTypes[-1] = activeTypes[-1] + ','
                                thisLine = []

                            # If it truly is just a dangling thing, just delete it
                            elif len(activeGenes) == len(activeTypes):
                                thisLine = []

                            else:
                                if thisLine[0] not in ['MS-Stable', 'Burden', 'TMB-Intermediate;'] and 'Muts/Mb' not in thisLine[0]:
                                    print('deleting')
                                    print(thisLine)
                                    print(filename)
                                    input()
                                thisLine = []
                        elif len(thisLine) == 0:
                            pass
                        elif ',' in ' '.join(thisLine):
                            if any(end in ' '.join(thisLine) for end in ['©', 'All rights reserved']):
                                thisLine = []
                                continue
                            # Last chance for a concat
                            # We will frequently have two commas
                            if sum(1 for i in activeTypes if i.endswith(',')) == 2:
                                firstInd = 0
                                while not activeTypes[firstInd].endswith(','):
                                    firstInd = firstInd + 1
                                activeTypes[firstInd:firstInd + 2] = [''.join(activeTypes[firstInd:firstInd + 2])]
                            # For the somewhat awkward case where we have to finish up adding a type to a new plant, then add a double.
                            if not thisLine[0].endswith(',') and any(t.endswith(',') for t in activeTypes):
                                activeTypes.append(thisLine[0])
                                thisLine.remove(thisLine[0])
                                #if thisLine[0].endswith(','):
                                #    thisLine = (''.join(thisLine[0:2]))
                            # For the opposite situation, where we add the commas first
                            if thisLine[0].endswith(','):
                                if any(b.endswith(',') for b in activeTypes):
                                    for b in activeTypes:
                                        if b.endswith(','):
                                            activeTypes[activeTypes.index(b)] = activeTypes[activeTypes.index(b)] + thisLine[0]
                                            thisLine = thisLine[1:]
                                            break
                                else:
                                    print('huh')
                                    print(activeTypes)
                                    input()

                            else:
                                # These are dangly lines that don't have anything interesting
                                if not any(bt.endswith(',') for bt in activeTypes):
                                    thisLine = []
                                else:
                                    print(thisLine)
                                    print(filename)
                                    input()

                        elif not(any(bt in ' '.join(negGeneList) for bt in thisLine)) and len(activeGenes) == len(activeTypes):
                            if any(type.endswith('and') for type in activeTypes):
                                for type in activeTypes:
                                    if type.endswith('and'):
                                        activeTypes[activeTypes.index(type)] = activeTypes[activeTypes.index(type)].replace('_', ',')
                                        type = type.replace('_', ',')
                                        activeTypes[activeTypes.index(type)] = activeTypes[activeTypes.index(type)] + ',' + ','.join(thisLine)
                                        thisLine = ''
                            elif bit.startswith('Q') and any(at.endswith('Q') for at in activeTypes):
                                for at in activeTypes:
                                    if at.endswith('Q'):
                                        activeTypes[activeTypes.index(at)] = activeTypes[activeTypes.index(at)] + bit
                                        thisLine.remove(bit)
                                        break

                            elif ',' not in bit and any(b.endswith(',') for b in activeTypes):
                                for at in activeTypes:
                                    if at.endswith(','):
                                        activeTypes[activeTypes.index(at)] = activeTypes[activeTypes.index(at)] + bit
                                        thisLine.remove(bit)
                                        break

                            else:
                                print('deleting')
                                print(thisLine)
                                print(activeGenes)
                                print(activeTypes)
                                print(filename)
                                print(negGeneList)
                                #input()
                                thisLine = []
                        elif len(activeGenes) == len(activeTypes):
                            thisLine = thisLine[1:]

                        else:
                            print(thisLine)
                            print(filename)
                            print(negGeneList)
                            print(activeGenes)
                            print(activeTypes)
                            print(len(activeGenes))
                            print(len(activeTypes))
                            input()
            newVusSection.append(' '.join(activeGenes))
            newVusTypes.append(' '.join(activeTypes))

            section = '\n'.join(newVusSection)
            types = '\n'.join(newVusTypes)

            vusSection = section.replace('\n', ' ')
            types = types.replace('\n', ' ')

            section = []
            while vusSection.startswith(' '):
                vusSection = vusSection[1:]

            # Now take out errors in the types
            if ' and ' in types or ', ' in types:
                types = types.replace(' and ', '_and_').replace(', ', ',')

            if '  (' in vusSection:
                vusSection = vusSection.replace('  (', '(')

            if len(vusSection.split()) != len(types.split()):
                print(vusSection, len(vusSection.split()))
                print(types, len(types.split()))
                print(filename)
                if len(vusSection.split()) < len(types.split()):
                    for z in range(0, len(vusSection.split())):
                        print(vusSection.split()[z], ' - ', types.split()[z])
                else:
                    for z in range(0, len(types.split())):
                        print(vusSection.split()[z], ' - ', types.split()[z])

                input()

            for word in vusSection.split():
                if word in ' '.join(negGeneList):
                    section.append(word)
                if 'Microsatellite' in word:
                    section.append('MSI')
                if 'Burden' in word:
                    section.append('TMB')

            newVusSection = newVusSection[0].split()
            newVusTypes = newVusTypes[0].split()

            # Now let's add 'em all as VUS
            for word in range(0, len(newVusSection)):
                if newVusSection[word].isnumeric() and vusGeneList[-1] == 'TMB':
                    callList[-1] = str(word) + ' muts/mb'
                else:
                    if '(' in newVusSection[word] and ' (' not in newVusSection[word]:
                        newVusSection[word] = newVusSection[word].replace('(', ' (')

                    vusGeneList.append(newVusSection[word])
                    geneList.append(newVusSection[word])
                    truncdGenes.append(newVusSection[word])
                    exonList.append('{}')
                    variantList.append('')
                    platformList.append('NGS')
                    typeChecker = newVusTypes[newVusSection.index(newVusSection[word])]
                    typeChecker = typeChecker.replace('_and_', ',').split(',')
                    type = ''
                    for t in typeChecker:
                        if any(x in t for x in ['ins', 'del']):
                            type = type + ', Indel'
                        elif any(x in t for x in ['amplification']):
                            type = type + ', CNA'
                        elif t in ['rearrangement']:
                            type = type + ', rearrangement'
                        elif (t[0].isalpha() and t[-1].isalpha()) or any(x in t for x in ['*', '>']):
                            type = type + ', Sub'
                        elif any(x in t for x in ['equivocal']):
                            type = type + ', equivocal'
                        else:
                            type = type + ', Sub'
                    while type.startswith(',') or type.startswith(' '):
                        type = type[1:]
                    type = ', '.join(list(set(type.split(', '))))
                    vusTypes.append(type)
                    typeList.append(type)
                    callList.append('VUS')
                    testText = vusSection
                    fullText = all_of_it
                    standardAppends()
        else:
            if 'Failed report' not in all_of_it:
                print(txt)
        if addedMSI:
            geneList.append('MSI')
            truncdGenes.append('MSI')
            exonList.append('{}')
            variantList.append('')
            platformList.append('NGS')
            typeList.append('MSI')
            callList.append(ms.replace('MSI-', ''))
            standardAppends()
            ms = ''
        if addedTMB:
            geneList.append('TMB')
            truncdGenes.append('TMB')
            exonList.append('{}')
            variantList.append('')
            platformList.append('NGS')
            typeList.append('TMB')
            callList.append(tmb)
            standardAppends()
            tmb = ''

        geneAddedList = []
        for neg in range(0, len(negGeneList)):
            isWildtype = False
            gene = negGeneList[neg]
            genType = ''
            if negGeneList[neg] in posGeneList:
                if negGeneList[neg] == 'TERC (promoter only)':
                    negGeneList[neg] = 'TERT (promoter only)'
                    negGeneList[negGeneList.index('TERT')] = 'TERC'
                if '(' in negGeneList[neg]:
                    trial1 = negGeneList[neg][:negGeneList[neg].index('(')].strip()
                    trial2 = negGeneList[neg][negGeneList[neg].index('(') + 1:].replace(')', '').strip()
                    genes = [trial1, trial2]
                else:
                    genes = [negGeneList[neg]]

                typeClue = []
                shortGeneSkip = False
                for gene in genes:
                    if gene == '':
                        continue
                    # If we have anything smushed together "NRASWildtype" for instance, this should fix it.
                    for pGene in posGeneList:
                        for word in range(0, len(wholePositive)):
                            if wholePositive[word].startswith(pGene) and not wholePositive[word] == pGene:
                                wholePositive[word] = wholePositive[word+1].replace(pGene, '')
                                wholePositive.insert(word, pGene)
                    # This is not a result - this is talking about therapies
                    if any(x in wholePositive for x in ['anti-' + gene, 'Anti-' + gene, '"' + gene + '",']):
                        for y in ['anti-' + gene, 'Anti-' + gene, '"' + gene + '",']:
                            while y in wholePositive:
                                wholePositive[wholePositive.index(y)] = ''
                    while gene in ' '.join(wholePositive) and not shortGeneSkip:
                        # If the gene is in the text but not a unique field...
                        if gene not in wholePositive:
                            # Our short genes like 'AR', yeah, they're probably in other words
                            if len(gene) <= 3:
                                if not any(x.startswith(gene) for x in wholePositive):
                                    shortGeneSkip = True
                                    break
                            newWholePositive = []
                            wpInd = 0
                            while gene not in wholePositive[wpInd]:
                                newWholePositive.append(wholePositive[wpInd])
                                wpInd = wpInd + 1
                            if gene + '-' in wholePositive[wpInd]:
                                newWholePositive.append(gene)
                                newWholePositive.append(wholePositive[wpInd].split('-')[1])
                                newWholePositive = newWholePositive + wholePositive[wpInd + 1:]
                                wholePositive = newWholePositive
                            # Sure, sometimes we just put parentheses around the gene.
                            elif '(' + gene + ')' in wholePositive:
                                wholePositive[wholePositive.index('(' + gene + ')')] = gene
                            # And sometimes two hyphens
                            elif '--' + gene in wholePositive:
                                wholePositive[wholePositive.index('--' + gene)] = gene
                            elif 'and' + gene + 'exon' in wholePositive:
                                wholePositive[wholePositive.index('and' + gene + 'exon')] = gene
                            elif gene + '1' in wholePositive:
                                gene = gene + '1'
                            # This is mushed together 'anEGFR mutation'
                            elif 'An' + gene in wholePositive:
                                wholePositive[wholePositive.index('An' + gene)] = gene
                            elif any((pos.startswith(gene) and pos != gene) for pos in wholePositive):
                                wpInd = 0
                                newWholePositive = []
                                while gene not in wholePositive[wpInd]:
                                    newWholePositive.append(wholePositive[wpInd])
                                    wpInd = wpInd + 1
                                newWholePositive.append(gene)
                                newWholePositive.append(wholePositive[wpInd].split(gene)[1])
                                newWholePositive = newWholePositive + wholePositive[wpInd + 1:]
                                wholePositive = newWholePositive
                            elif '(' + gene + ')' in wholePositive[wpInd]:
                                newWholePositive.append(gene)
                                newWholePositive.append(wholePositive[wpInd].split(gene + ')')[1])
                                newWholePositive = newWholePositive + wholePositive[wpInd + 1:]
                                wholePositive = newWholePositive
                            else:
                                print(txt)
                                print(wholePositive)
                                print(gene)
                                input()
                        section = wholePositive[wholePositive.index(gene):]
                        sectionStart = wholePositive.index(gene)
                        secInd = 1
                        while section[secInd] not in ' '.join(negGeneList) and section[secInd] not in ['Therapies', 'therapies', 'Tumor', 'Microsatellite', 'GENOMIC', 'MEDICAL', 'alteration'] and \
                                not section[secInd].endswith(('nib', 'mab', 'mus', '®', 'rif')):
                            if secInd == len(section) - 1 :
                                break
                            secInd = secInd + 1
                        wholePositive1 = wholePositive[:sectionStart]
                        wholePositive2 = wholePositive[sectionStart + secInd:]
                        wholePositive = wholePositive1 + wholePositive2
                        section = section[1:secInd]
                        section = ' '.join(section)
                        typeClue.append(section)
                if negGeneList[neg] not in geneAddedList:
                    geneAddedList.append(negGeneList[neg])
                    type = []
                    for item in typeClue:
                        if item in [' ', '']:
                            continue
                        if 'promoter' in item:
                            geneAddedList[-1] = geneAddedList[-1] + ' ' + 'promoter'
                            negGeneList[neg] = negGeneList[neg] + ' ' + 'promoter'
                        if any(x in item for x in ['amplification', 'loss']):
                            type.append('CNA')
                        elif any(x in item for x in ['del', 'ins', 'duplication']):
                            type.append('Indel')
                        elif any(x in item for x in ['wildtype', 'wild type']):
                            type = ['wildtype']
                        elif any(x in item for x in ['rearrangement']) or ('NM_' in item and '-' in item):
                            type.append('DNA Rearrangement')
                        elif any(x in item for x in ['fusion']):
                            type.append('Fusion')
                        elif any(x in item for x in ['equivocal']):
                            type.append('Equivocal')
                        else:
                            type.append('Sub')
                        if 'splice site' in item:
                            type.append('splice site')
                    types = list(set(type))
                    for type in types:
                        genType = genType + ', ' + type
                    while genType.startswith((',', ' ')):
                        genType = genType[1:]
                    if genType != 'wildtype':
                        geneList.append(negGeneList[neg])
                        truncdGenes.append(''.join(sorted(set(negGeneList[neg]), key=negGeneList[neg].index)))
                        exonList.append('{}')
                        variantList.append('')
                        platformList.append(negPlatformList[neg])
                        # Occasionally, we get a split gene that doesn't pick up the alteration for both parts
                        if negGeneList[neg] in ['CDKN2B'] and genType == '' and geneList[-2] in ['CDKN2A']:
                            typeList.append(typeList[-2])
                        else:
                            typeList.append(genType)
                        callList.append('Positive')
                        standardAppends()
                    if genType == 'wildtype':
                        isWildtype = True

            if negGeneList[neg] in vusGeneList:
                ind = vusGeneList.index(negGeneList[neg])
                types = vusTypes[ind]
                for typ in types.split(', '):
                    genType = genType + ', ' + typ
                while genType.startswith(',') or genType.startswith(' '):
                    genType = genType[1:]
                genType = ', '.join(list(set(genType.split(', '))))

            genType = genType.split(', ')
            genType = list(filter(None, genType))
            negTypes = negTypeList[neg].split(', ')
            negExons = negExonList[neg].split(', ')
            # So genType are all the things that we've found
            # and negTypes are all the types that this gene has
            countr = 0
            for type in negTypes:
                if type == 'DNA Sub/Indel/CNA':
                    final = ['Sub', 'Indel', 'CNA']
                    for bit in genType:
                        if bit in final:
                            final.remove(bit)
                    negTypeList[neg] = '/'.join(final)
                    type = '/'.join(final)
                if type == 'DNA Rearrangement' and 'Fusion' in genType:
                    continue
                geneList.append(negGeneList[neg])
                truncdGenes.append(''.join(sorted(set(negGeneList[neg]), key=negGeneList[neg].index)))
                if '{' in negExons[countr]:
                    exonList.append(negExons[countr])
                else:
                    exonList.append('{' + negExons[countr] + '}')
                countr = countr + 1
                variantList.append('')
                platformList.append(negPlatformList[neg])
                typeList.append(type)
                if isWildtype:
                    callList.append('Negative, Explicit')
                else:
                    callList.append('Negative, Inferred')
                standardAppends()

if getTempus:
    mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Tempus/'
    txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]
    fnum = 0
    brokens = []
    # No MRN from Tempus
    mrn = ''
    for txt in txts:
        if countFiles:
            print(fnum, ' of ', len(txts))
        fnum = fnum + 1
        file = mypath + txt
        file = open(file, mode='r')
        all_of_it = file.read()
        file.close()

        # This is a sample file
        if 'Shesgot' in all_of_it or all_of_it == '':
            continue

        testNames = ['xT', 'xF', 'Tempus Clinical Sequencing Report', 'IHC\n', 'Panel of 595 genes', 'Panel of 1714 genes']
        if not any(tn in all_of_it for tn in testNames):
            if 'IHC' in all_of_it:
                testType = 'Tempus IHC Report'
            else:
                print(all_of_it)
                print(txt)
                input()
        else:
            for tn in testNames:
                if tn in all_of_it:
                    if tn == '| IHC ':
                        tn = 'IHC'
                    testType = tn

        # Let's get the date of test!
        if 'Received' in all_of_it:
            space = all_of_it[all_of_it.index('Received') + len('Received'):]
            space = space[:space.index('\n')]
            if '   ' in space:
                space = space[:space.index('   ')]
            space = space.strip()
            while space.startswith(':') or space.startswith(' '):
                space = space[1:]
            received = space
            dateType = 'Date Received'
        else:
            print(all_of_it)
            input()

        source = 'Tempus'
        filename = txt[:-20]

        all_of_it = all_of_it.split('\n')
        all_of_it = list(filter(None, all_of_it))
        all_of_it = '\n'.join(all_of_it)

        #####
        # First, for identification, we get the name
        #####
        if 'Name   ' in all_of_it:
            section = all_of_it[all_of_it.index('Name   ') + len('Name   '):]
            section = section[:section.index('Physician')]
            nameBit = section.strip()
        elif not all_of_it.startswith('Diagnosis'):
            section = all_of_it.split('\n')[0]
            section = section[:section.index('    ')]
            nameBit = section
            split = all_of_it.split('\n')
            nameLine = 1
            while split[nameLine][0] == ' ':
                nameLine = nameLine + 1
            if not nameBit.endswith('-'):
                nameBit = nameBit + ' '
            nameBit = nameBit + all_of_it.split('\n')[nameLine].split('   ')[0]
        else:
            nameLine = 1
            while all_of_it.split('\n')[nameLine][0] == ' ':
                nameLine = nameLine + 1
            nameBit = all_of_it.split('\n')[nameLine].split('   ')[0]

        if 'EMR' in nameBit:
            nameBit = nameBit[:nameBit.index('EMR')]
        nameBit = nameBit.split()
        if len(nameBit) == 1:
            name = nameBit[0]
            nameLine = 0
            while name not in all_of_it.split('\n')[nameLine]:
                nameLine = nameLine + 1
            line = all_of_it.split('\n')[nameLine+1]
            while line.startswith(' '):
                line = line[1:]
            nameBit.append(line.split(' ')[0])
        if nameBit[-1] in ['Jr.', 'Jr', 'Sr.', 'Sr'] or nameBit[-1].replace('I','').replace('i','') == '':
            srJr = nameBit[-1]
            nameBit = nameBit[:-1]
        else:
            srJr = ''
        if len(nameBit) > 2:
            lastName = nameBit[-1]
            nameBit = nameBit[:-1]
            firstName = nameBit[0]
            nameBit = nameBit[1:]
            middleName = ' '.join(nameBit)
        else:
            firstName = nameBit[0]
            lastName = nameBit[1]
            middleName = ''
            srJr = ''

        #####
        # Now for the birthday
        #####
        all_of_it = all_of_it.replace('Date Of Birth', 'Date of Birth')
        if 'Date of Birth' in all_of_it:
            section = all_of_it[all_of_it.index('Date of Birth'):]
            section = section.split('\n')
            birthdate = section[1]
            if 'Diagnosis' in birthdate:
                birthdate = section[0]
                while '  ' in birthdate:
                    birthdate = birthdate.replace('  ', ' ')
                birthdate = birthdate.split()[3]
            if birthdate.startswith(' '):
                birthdate = section[0]
                if birthdate == 'Date of Birth':
                    section = section[1:]
                    while section[0].startswith(' '):
                        section = section[1:]
                else:
                    while '  ' in birthdate:
                        birthdate = birthdate.replace('  ', ' ')
                    birthdate = birthdate.split()[3]
            if birthdate == '':
                section = section[1:]
                while section[0].startswith(' ') or section[0] == '':
                    section = section[1:]
                birthdate = section[0]

        else:
            print(all_of_it)
            input()
        if len(birthdate.split()) > 1:
            birthdate = birthdate.split()[0]

        ####
        # Now Diagnosis and Site
        ####
        if 'Tumor specimen:' in all_of_it:
            tumorLine = 0
            split = all_of_it.split('\n')
            while 'Tumor specimen:' not in split[tumorLine]:
                tumorLine = tumorLine + 1
            tumorLine = tumorLine + 1
            primary = split[tumorLine]
            while primary[0] == ' ':
                tumorLine = tumorLine + 1
                primary = split[tumorLine]
        elif 'Tumor Specimen: ' in all_of_it:
            primary = all_of_it[all_of_it.index('Tumor Specimen: ') + len('Tumor Specimen: '):]
            primary = primary[:primary.index('\n')]
        elif 'cfDNA specimen:' in all_of_it:
            tumorLine = 0
            split = all_of_it.split('\n')
            while 'cfDNA specimen:' not in split[tumorLine]:
                tumorLine = tumorLine + 1
            primary = split[tumorLine + 1]
        elif 'Heme specimen:' in all_of_it:
            tumorLine = 0
            split = all_of_it.split('\n')
            while 'Heme specimen:' not in split[tumorLine]:
                tumorLine = tumorLine + 1
            primary = split[tumorLine + 1]
        elif any(test in all_of_it for test in ['xF 77 Genes', 'xF 105 Genes']):
            for testo in ['xF 77 Genes', 'xF 105 Genes']:
                if testo in all_of_it:
                    thisTest = testo
            testLine = 0
            while thisTest not in all_of_it.split('\n')[testLine]:
                testLine = testLine + 1
            primary = all_of_it.split()[testLine + 1].split('   ')[0]
            if primary == '':
                primary = all_of_it.split()[testLine + 2].split('   ')[0]
        elif 'Specimens' in all_of_it:
            primary = ''
            bit = all_of_it[:all_of_it.index('Accession No.')]
            split = all_of_it.split('\n')
            for line in split:
                lineSplit = line.split('    ')
                lineSplit = list(filter(None, lineSplit))
                if 'Collected:' in lineSplit[-1] or 'Received:' in lineSplit[-1]:
                    if len(lineSplit) > 1:
                        if 'Physician' not in lineSplit:
                            primary = primary + ' ' + lineSplit[-2]
                        else:
                            primary = primary + ';'
                    else:
                        primary = primary + ';'
            while '  ' in primary:
                primary = primary.replace('  ', ' ')
            primary = primary.strip()

        if '   ' in primary:
            primary = primary[:primary.index('   ')]

        # Finally, the diagnosis
        if all_of_it.startswith('Diagnosis'):
            diagLine = 1
            split = all_of_it.split('\n')
            while split[diagLine][0] == ' ':
                diagLine = diagLine + 1
            splitLine =split[diagLine].split('   ')
            splitLine = list(filter(None, splitLine))
            while len(splitLine) == 1:
                diagLine = diagLine + 1
                splitLine = split[diagLine].split('   ')
                splitLine = list(filter(None, splitLine))
            diagnosis = splitLine[1]
            dobLine = 0
            while 'Date of Birth' not in split[dobLine]:
                dobLine = dobLine + 1
            if split[dobLine-1].startswith(' '):
                splitLine = split[dobLine-1].split('   ')
                splitLine = list(filter(None, splitLine))
                if splitLine[0].strip() not in ['xF', 'IHC', 'xT']:
                    diagnosis = diagnosis + ' ' + splitLine[0].strip()
            diagnosis = diagnosis.strip()
            while '  ' in diagnosis:
                diagnosis = diagnosis.replace('  ', ' ')

            # Troubleshooting
            if diagnosis[0].islower():
                diagnosis = ''
                section = all_of_it[all_of_it.index('Diagnosis'):all_of_it.index('Date of Birth')]
                section = section.split('\n')
                section = section[1:]
                # Let's get the alignment
                sectionLine = section[0].split(' ')
                indent = 0
                while sectionLine[indent] == '':
                    indent = indent + 1
                lineIndent = indent
                while sectionLine[lineIndent] != '':
                    diagnosis = diagnosis + ' ' + sectionLine[lineIndent]
                    lineIndent = lineIndent + 1
                    if lineIndent == len(sectionLine):
                        sectionLine.append('')
                for line in range(2,len(section)):
                    start = 0
                    sectionLine = section[line].split(' ')
                    begwords = []
                    if '' in sectionLine:
                        while sectionLine[start] != '':
                            begwords.append(sectionLine[start])
                            start = start + 1
                        sectionLine = section[line]
                        for word in begwords:
                            sectionLine = sectionLine.replace(word, ' ' * len(word))
                    sectionLine = section[line].split(' ')
                    if len(sectionLine) > indent:
                        if sectionLine[indent] != '':
                            lineIndent = indent
                            while sectionLine[lineIndent] != '':
                                diagnosis = diagnosis + ' ' + sectionLine[lineIndent]
                                lineIndent = lineIndent + 1
                                if lineIndent == len(sectionLine):
                                    sectionLine.append('')
                diagnosis = diagnosis.strip()

            if 'G E N' in diagnosis or 'Q UA N' in diagnosis:
                diagnosis = ''
                section = all_of_it[all_of_it.index('Accession'):all_of_it.index('Date of Birth')]
                section = section.split('\n')
                section = section[1:]
                # Let's get the alignment
                sectionLine = section[0].split(' ')
                indent = 0
                while sectionLine[indent] == '':
                    indent = indent + 1
                lineIndent = indent
                while sectionLine[lineIndent] != '':
                    diagnosis = diagnosis + ' ' + sectionLine[lineIndent]
                    lineIndent = lineIndent + 1
                for line in range(2,len(section)):
                    start = 0
                    sectionLine = section[line].split(' ')
                    begwords = []
                    if '' in sectionLine:
                        while sectionLine[start] != '':
                            begwords.append(sectionLine[start])
                            start = start + 1
                        sectionLine = section[line]
                        for word in begwords:
                            sectionLine = sectionLine.replace(word, ' ' * len(word))
                    sectionLine = section[line].split(' ')
                    if len(sectionLine) > indent:
                        if sectionLine[indent] != '':
                            lineIndent = indent
                            while sectionLine[lineIndent] != '':
                                diagnosis = diagnosis + ' ' + sectionLine[lineIndent]
                                lineIndent = lineIndent + 1
                                if lineIndent == len(sectionLine):
                                    sectionLine.append('')
                diagnosis = diagnosis.strip()

        elif 'Diagnosis' in all_of_it.split('\n')[0]:
            diagLine = 1
            split = all_of_it.split('\n')
            while split[diagLine][0] == ' ':
                diagLine = diagLine + 1
            splitLine = split[diagLine].split('   ')
            splitLine = list(filter(None, splitLine))
            while len(splitLine) < 2:
                diagLine = diagLine - 1
                splitLine = split[diagLine].split('   ')
                splitLine = list(filter(None, splitLine))
            if '\n' + splitLine[0] in all_of_it:
                diagnosis = splitLine[1].strip()
            else:
                diagnosis = splitLine[0].strip()
            dobLine = 0
        elif 'Diagnosis' in all_of_it:
            section = all_of_it[all_of_it.index('Diagnosis'):]
            if '(IHC)' in section:
                section = section[:section.index('(IHC)')]
            else:
                section = section[:section.index('Results')]

            numOfLines = len(section.split('\n'))

            # First word isn't necessarially spaced right
            lineSplit = section.split('\n')[0].split(' ')
            lineSplit = list(filter(None, lineSplit))
            if len(lineSplit) > 1:
                diagnosis = lineSplit[1]
            else:
                diagLine = 0
                splitLines = all_of_it.split('\n')
                while 'Diagnosis' not in splitLines[diagLine]:
                    diagLine = diagLine + 1
                diagOne = splitLines[diagLine-1]
                diagTwo = splitLines[diagLine+1]
                while diagOne.startswith(' '):
                    diagOne = diagOne[1:]
                while diagTwo.startswith(' '):
                    diagTwo = diagTwo[1:]
                diagnosis = diagOne.split()[0] + ' ' + diagTwo.split()[0]

            # But from then on, they'll have the same spacing
            firstGoodSpace = 1
            lineSplit = section.split('\n')[firstGoodSpace].split(' ')
            testLine = list(filter(None, lineSplit))
            while testLine[0] in ['Estimated']:
                firstGoodSpace = firstGoodSpace + 1
                lineSplit = section.split('\n')[firstGoodSpace].split(' ')
                testLine = list(filter(None, lineSplit))
            spacing = 0
            while lineSplit[spacing] == '':
                spacing = spacing + 1
            firstSpace = spacing
            while lineSplit[spacing] != '' and spacing < len(lineSplit):
                diagnosis = diagnosis + ' ' + lineSplit[spacing]
                spacing = spacing + 1
                if spacing == len(lineSplit):
                    lineSplit.append('')

            for ln in range(firstGoodSpace + 1, numOfLines):
                lineSplit = section.split('\n')[ln].split(' ')
                spacing = firstSpace
                if len(lineSplit) > spacing:
                    while lineSplit[spacing] != '':
                        diagnosis = diagnosis + ' ' + lineSplit[spacing]
                        spacing = spacing + 1
                        if spacing == len(lineSplit):
                            lineSplit.append('')

        while '  ' in diagnosis:
            diagnosis = diagnosis.replace('  ', ' ')
        diagnosis = diagnosis.replace('- ', '-').replace('ﬀ', 'ff')
        for ender in ['NUMBER', 'Henry', 'Variant', 'Blood']:
            if ender in diagnosis:
                diagnosis = diagnosis[:diagnosis.index(ender)]

        if 'TL-' in diagnosis:
            for word in diagnosis.split():
                if 'TL-' in word:
                    diagnosis = diagnosis.replace(word + ' ', '')

        if 'Normal Specimen: ' in all_of_it:
            section = all_of_it[all_of_it.index('Normal Specimen: ') + len('Normal Specimen: '):]
            section = section[:section.index('\n')]
        elif 'Normal specimen: ' in all_of_it:
            section = all_of_it[all_of_it.index('Normal specimen: '):]
            section = section.split('\n')
            section = section[1]
            section = section.split('        ')
            section = section[0]
        else:
            section = 'Not Given'
        specimenType = section

        # Let's adjust a little
        specimenSite = primary
        primary = 'Not Given'

        listStarts = ['Gene List', 'Gene Rearrangements Found by DNA Sequencing', 'Germline Genes', 'RNA Fusion Analysis']

        listEnds = ['Gene Rearrangements Found by DNA Sequencing', 'Germline Genes', 'RNA Fusion Analysis', 'Tempus Disclaimer']

        negTypes = ['Mutation', 'Rearrangement', 'Germline', 'RNA Fusion']

        negPlatforms = ['NGS', 'NGS', 'NGS', 'RNA Fusion']

        # Why don't we find lists, if we dont'?
        if not any(x in all_of_it for x in listStarts):
            if 'PD-L 1 EXPRESSION' in all_of_it or 'P D - L1   E X PR E S S I O N' in all_of_it:
                type = 'PD-L1 test'
                #tempusNoLists.append('PD-L1')
                #tempusNoListDates.append(received)
            elif 'Panel of 595 genes' in all_of_it:
                type = '595-gene panel'
                tempusNoLists.append('595')
                tempusNoListDates.append(received)
                if '2020' in received:
                    print(txt)
                    input()
            elif 'for PD-L1 Expression' in all_of_it:
                type = 'PD-L1 test'
                #tempusNoLists.append('PD-L1')
                #tempusNoListDates.append(received)
            elif 'Panel of 1714 genes' in all_of_it:
                type = '1714-gene panel'
                tempusNoLists.append('1714-Panel')
                tempusNoListDates.append(received)
                if '2020' in received:
                    print(txt)
                    input()
            elif 'xE' in all_of_it:
                type = 'Tempus xE'
                tempusNoLists.append('xE')
                tempusNoListDates.append(received)
            elif 'xF' in all_of_it:
                type = 'Tempus xF'
                tempusNoLists.append('xF')
                tempusNoListDates.append(received)
                if '2020' in received:
                    print(txt)
                    input()
            elif 'xT' in all_of_it:
                type = 'Tempus xT'
                tempusNoLists.append('xT')
                tempusNoListDates.append(received)
                if '2020' in received:
                    print(txt)
                    input()
            elif 'For the complete gene list, see the Tempus website.' in all_of_it or 'Please see the Tempus website for a complete' in all_of_it:
                print(all_of_it)
                input()
                type = 'Website Referral'
                tempusNoLists.append('Site Referral')
                tempusNoListDates.append(received)
            geneList.append('No Provided Gene List')
            exonList.append('{}')
            variantList.append('')
            platformList.append('')
            typeList.append(type)
            callList.append('')
            standardAppends()

        # For holding our negatives
        negGeneList = []
        negExonList = []
        negPlatformList = []
        negTypeList = []
        negCallList = []

        # For holding our positives
        posGeneList = []
        posExonList = []
        posPlatformList = []
        posTypeList = []
        posCallList = []

        while any(x in all_of_it for x in listStarts):
            for test in listStarts:
                if test in all_of_it:
                    negIndex = listStarts.index(test)
                    wholeSection = all_of_it[all_of_it.index(test):]
                    section = all_of_it[all_of_it.index(test) + len(test):]
                    endIndex = 999999999
                    for end in listEnds:
                        if end in section and test not in end:
                            if section.index(end) < endIndex:
                                endIndex = section.index(end)
                    section = section[:endIndex]
                    wholeSection = wholeSection[:endIndex + len(test)]
                    origSection = wholeSection
                    while 'Electronically' in section:
                        snip = section[section.index('Electronically'):]
                        if '(continued)' not in snip:
                            pass
                        else:
                            snip = snip[:snip.index('(continued)') + len('(continued)')]
                        section = section.replace(snip, '')
                        while '  ' in section:
                            section = section.replace('  ', ' ')
                    sectionSplit = section.split('\n')
                    section = ''
                    for sec in sectionSplit:
                        if len(sec) == 3 and '-' in sec:
                            pass
                        else:
                            section = section + ' ' + sec
                    if 'Copy Number' in section:
                        section = section[:section.index('Copy')]
                    section = section.replace('   ', ', ')
                    section = section.strip()

                    all_of_it = all_of_it.replace(origSection, '')
                    for word in section.split(','):
                        word = word.strip()
                        if len(word.split()) > 1 and '(' not in word and 'BIOCARE' not in word:
                            if '- ' in word:
                                wordNew = word.replace('- ', '-')
                                section = section.replace(word, wordNew)
                            else:
                                wordNew = word.replace(' ', ', ')
                                section = section.replace(word, wordNew)

                    while section.startswith(',') or section.startswith(' '):
                        section = section[1:]
                    while section.endswith(',') or section.endswith(' '):
                        section = section[:-1]
                    for bit in section.split(','):
                        negGeneList.append(bit.strip())
                        negExonList.append('Not Given')
                        negPlatformList.append(negPlatforms[negIndex])
                        negTypeList.append(negTypes[negIndex])
                        negCallList.append('Negative, inferred')

        # We can now pull out the positives
        posStarts = ['Somatic - Biologically Relevant',
                     'Germline - Pathogenic / Likely Pathogenic',
                     'IM M UN OTHERA PY M A RKERS',
                     'VA RIA N TS OF UN KN OWN SIGN IFICA N CE',
                     'L OW COV ERA GE REGION S',
                     'SOM A TIC V A RIA N T DETA IL S - BIOL OGICA L L Y REL EV A N T\n',
                     'DN A M ISM A TCH REPA IR PROTEIN EXPRESSION',
                     'D N A   M I S M AT C H   R E PA I R    PRO T E I N   E X PR E S S I O N']

        posEnds = ['Somatic - Biologically Relevant',
                        'Germline - Pathogenic / Likely Pathogenic',
                        'IM M UN OTHERA PY M A RKERS',
                        'VA RIA N TS OF UN KN OWN SIGN IFICA N CE',
                        'L OW COV ERA GE REGION S',
                        'SOM A TIC V A RIA N T DETA IL S - BIOL OGICA L L Y REL EV A N T\n',
                        'CL IN ICA L HISTORY', 'Assay Description',
                   'SOM A TIC V A RIA N T DETA IL S - POTEN TIA L L Y A CTION A BL E',
                    ]

        posPlatforms = ['NGS', 'NGS', 'Not Given', 'NGS', 'NGS', 'NGS', 'DNA Mismatch Repair', 'DNA Mismatch Repair']
        posTypes = ['Somatic Mutation', 'Germline Mutation', 'Immunotherapy marker', 'Mutation', 'Not Given', 'Mutation', 'DNA Mismatch Repair', 'DNA Mismatch Repair']
        posCalls = ['Positive - Biologically Relevant', 'Positive- Pathogenic / Likely  Pathogenic', 'Positive', 'VUS', 'Equivocal - Low Coverage', 'Positive - Biologically Relevant', 'Positive - DNA Mismatch', 'Positive - DNA Mismatch']

        if not any(pos in all_of_it for pos in posStarts):
            if 'The requested assay could not be completed due to insuﬃcient quantity and/or':
                geneList.append('Test Not Done')
                exonList.append('{}')
                variantList.append('')
                platformList.append('')
                typeList.append('QNS/Test not Done')
                callList.append('')
                standardAppends()

        for neg in range(0, len(negGeneList)):
            negGeneList[neg] = negGeneList[neg].strip()

        while any(pos in all_of_it for pos in posStarts):
            for pos in posStarts:
                if pos in all_of_it:
                    posIndex = posStarts.index(pos)
                    posSection = all_of_it[all_of_it.index(pos):]
                    endIndex = 999999999999
                    for end in posEnds:
                        if end in posSection and pos not in end:
                            if posSection.index(end) < endIndex:
                                endIndex = posSection.index(end)
                    posSection = posSection[:endIndex]
                    all_of_it = all_of_it.replace(posSection, '')
                    for gen in range(0, len(negGeneList)):
                        geneType = ''
                        origGene = negGeneList[gen].strip()
                        origGeneCopy = origGene.split()[0]
                        gene = negGeneList[gen].replace('(', '').replace(')', '')
                        gene = gene.split()
                        added = False
                        for g in gene:
                            if (' ' + g in posSection or '\n' + g in posSection) and not added and origGene not in posGeneList and g not in ['Loss', 'of', 'Heterozygosity (LOH)', 'score', 'status', 'and']:
                                if pos == 'VA RIA N TS OF UN KN OWN SIGN IFICA N CE':
                                    if 'Germline' in posSection:
                                        somaticPart = posSection[:posSection.index('Germline')]
                                        germlinePart = posSection[posSection.index('Germline'):]
                                        if origGeneCopy in somaticPart:
                                            geneType = '- Somatic'
                                        elif origGeneCopy in germlinePart:
                                            geneType = '- Germline'
                                        else:
                                            print(origGeneCopy)
                                            print(posSection)
                                            input()
                                added = True
                                posGeneList.append(origGene.strip())
                                posExonList.append('')
                                posPlatformList.append(posPlatforms[posIndex])
                                if geneType != '':
                                    posTypeList.append(posTypes[posIndex] + geneType)
                                else:
                                    posTypeList.append(posTypes[posIndex])
                                posCallList.append(posCalls[posIndex])

        for gen in range(0, len(negGeneList)):
            origGene = negGeneList[gen].strip()
            if origGene not in posGeneList:
                geneList.append(origGene)
                exonList.append('{}')
                variantList.append('')
                platformList.append(negPlatformList[gen])
                typeList.append(negTypeList[gen])
                callList.append(negCallList[gen])
                standardAppends()
            else:
                geneList.append(origGene)
                posIndex = posGeneList.index(origGene)
                exonList.append('{}')
                variantList.append('')
                platformList.append(posPlatformList[posIndex])
                typeList.append(posTypeList[posIndex])
                callList.append(posCallList[posIndex])
                standardAppends()































if getNeogenomics:
    mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Neogenomics/'
    txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]
    fnum = 0
    brokens = []
    for txt in txts:
        if countFiles:
            print(fnum, ' of ', len(txts))
        fnum = fnum + 1
        file = mypath + txt
        file = open(file, mode='r')
        all_of_it = file.read()
        file.close()

        # We're skipping a few file types:
        disregardTests = ['Flow Cytometry Analysis', 'SRSF2 Mutation Analysis', 'Oncology Chromosome Analysis', 'Androgen Receptor Mutation Analysis']
        if any(x in all_of_it for x in disregardTests):
            continue

        # I'm assuming this is a typo, pending Dr. Berry
        all_of_it = all_of_it.replace('PGFRA', 'PDGFRA').replace('PDGFRa', 'PDGFRA')

        source = 'Neogenomics'
        filename = txt[:-20]

        testNames = ['Gastric Tumor Profile', 'Lung Profile', 'Next-Gen Myeloid Disorders Profile', 'Lung Tumor Profile', 'NeoTYPE™ Breast Tumor Panel',
                     'NeoTYPE™ Head & Neck Tumor Panel', 'Colorectal Tumor Profile', 'Liver/Biliary Tumor Profile', 'Discovery Profile', 'NeoTYPE™ Lung Tumor FISH Panel',
                     'MDS/CMML Profile', 'Head & Neck Tumor Profile', 'AML Favorable-Risk Profile', 'Pancreas Tumor Profile', 'CLL Prognostic Profile', 'Other Solid Tumor Profile',
                     'Breast Tumor Profile', 'Brain Tumor Profile', 'AML Prognostic Profile', 'Esophageal Profile', 'NeoTYPE™ Other Solid Tumor Panel', 'NeoTYPE™ Gastric Tumor Panel',
                     'Melanoma Profile', 'NeoTYPE™ Colorectal Tumor Panel', 'Lymphoma Profile', 'Precision Profile for Solid Tumors', 'HRD+ Profile', 'MPN Profile', 'GI Predictive Profile',
                     'Endometrial Tumor Profile', 'GIST and Soft Tissue Tumor Profile', 'GIST Profile', 'NeoTYPE™ Pancreas Tumor Panel', 'NeoTYPE™ Melanoma FISH Panel', 'Ovarian Profile',
                     'NeoTYPE™ Endometrial Tumor Panel', 'EGFR T790M - Liquid Biopsy', 'NeoTYPE™ Esophageal Tumor Panel', 'NeoTYPE™ Liver/Biliary Tumor Panel', 'Thyroid Profile',
                     'Esophageal Tumor Profile', 'NeoTYPE™ Thyroid Panel', 'Ovarian Tumor Profile', 'NeoTYPE™ GI Predictive FISH Panel', 'NeoTYPE™ GIST and Soft Tissue Tumor Panel',
                     'NeoTYPE™ Myeloid Disorders Profile', 'Cervical Tumor Profile']
        if not any(tn in all_of_it for tn in testNames):
            print(all_of_it)
            print(txt)
            input()
        else:
            for tn in testNames:
                if tn in all_of_it:
                    if tn.endswith('Profile'):
                        tn = 'NeoTYPE™ Analysis ' + tn
                    testType = tn

        # Let's get MRN
        if 'MRN:' in all_of_it:
            section = all_of_it[all_of_it.index('MRN:') + len('MRN:'):]
            section = section[1:]
            if section.index('\n') < section.index(' '):
                section = section[:section.index('\n')]
            else:
                section = section[:section.index(' ')]
            mrn = section.strip()
        else:
            print(all_of_it)
            print('no mrn - neo')
            input()

        # First up is the name
        if 'Patient Name: ' in all_of_it:
            section = all_of_it[all_of_it.index('Patient Name: ') + len('Patient Name: '):]
            section = section[:section.index('\n')]
            if 'Ordering' in section:
                section = section[:section.index('Ordering')]
            section = section.split(', ')
            if len(section) < 2:
                section = section[0].split()
            lastName = section[0]
            firstName = section[1]
            middleName = ''
            srJr = ''
            if len(lastName.split()) > 1:
                if lastName.split()[1].lower().replace('.','') in ['jr', 'sr'] or lastName.split()[1].replace('I', '').replace('lll', '') == '':
                    srJr = lastName.split()[1]
                    lastName = lastName.split()[0]
            if len(firstName.split()) > 1:
                middleName = firstName.split()[1]
                firstName = firstName.split()[0]

        # Next, birthdate
        if 'Patient DOB / Sex:' in all_of_it:
            section = all_of_it[all_of_it.index('Patient DOB / Sex:') + len('Patient DOB / Sex:'):]
            section = section[:section.index('\n')]
            section = section.split(' / ')
            birthdate = section[0]
            birthdate = birthdate.strip()

        # Next, specimen type
        if 'Specimen Type:' in all_of_it:
            section = all_of_it[all_of_it.index('Specimen Type: ') + len('Specimen Type: '):]
            endPoint = 9999999999999
            for ending in ['Accession', 'Treating', 'Physician', 'APRN', 'Collection', '\n', 'MD']:
                if ending in section:
                    if section.index(ending) < endPoint:
                        endPoint = section.index(ending)
            section = section[:endPoint]
            section = section.strip()
            for ending in ['Tissue ', 'Marrow ', 'Node ']:
                if ending in section:
                    section = section[:section.index(ending) + len(ending)]
            section = section.strip()
            if section.endswith('Flow-'):
                section = section + 'Suspension'
            specimenType = section

        if 'Body Site: ' in all_of_it:
            specimenSite = all_of_it[all_of_it.index('Body Site: ') + len('Body Site: '):]
            endPos = 9999999
            for x in ['Collection', 'Received', '\n']:
                if x in specimenSite:
                    if specimenSite.index(x) < endPos:
                        endPos = specimenSite.index(x)
            specimenSite = specimenSite[:endPos]
            endPos = 9999999
            for x in ['Accession']:
                if x in specimenSite:
                    if specimenSite.index(x) < endPos:
                        endPos = specimenSite.index(x)
            specimenSite = specimenSite[:endPos]
            specimenSite = specimenSite.strip()
            # Sometimes this leaves the physician appended on the end - let's remove it
            if 'Ordering Physician' in all_of_it:
                physcianCheck = all_of_it[all_of_it.index('Ordering Physician'):all_of_it.index('Specimen Type')]
                siteWords = specimenSite.split()
                for word in range(0, len(siteWords)):
                    if siteWords[word] in physcianCheck:
                        siteWords[word] = ''
                siteWords = list(filter(None, siteWords))
                specimenSite = ' '.join(siteWords)

        else:
            specimenSite = 'Not Given'

        # Here we're just sorting out names from the specimen sites. They're hard to get out!
        if 'M.D' in specimenSite or 'Dr.' in specimenSite or 'DO' in specimenSite or 'MD' in specimenSite or 'Md' in specimenSite or 'D.O.' in specimenSite:
            specimenSite = specimenSite.split()
            if len(specimenSite) < 4:
                specimenSite = ' '.join(specimenSite[:-2])
            else:
                specimenSite = ' '.join(specimenSite[:-3])
            if specimenSite.endswith(','):
                specimenSite = specimenSite.split()
                specimenSite = ' '.join(specimenSite[:-1])
            if len(specimenSite.split()) > 1:
                if specimenSite.split()[-1][0].isupper() and specimenSite.split()[-2][0].islower():
                    specimenSite = specimenSite.split()
                    specimenSite = ' '.join(specimenSite[:-1])
        if specimenSite.split()[0].isupper() and not specimenSite.isupper() and len(specimenSite.replace(',', ' ').split()[0]) > 3:
            endPart = 0
            while specimenSite.split()[endPart].isupper():
                endPart = endPart + 1
            specimenSite = ' '.join(specimenSite.split()[0:endPart])

        # Sometimes there's a word that stops it
        for x in ['Pathologist']:
            if x in specimenSite:
                specimenSite = specimenSite[:specimenSite.index(x)]
        while '  ' in specimenSite:
            specimenSite = specimenSite.replace('  ', ' ')

        primary = 'Not Given'

        # Neo doesn't give diagnosis
        if 'Reason for Referral:' in all_of_it:
            section = all_of_it[all_of_it.index('Reason for Referral:') + len('Reason for Referral:'):]
            section = section[:section.index('\n')]
            if section.endswith(','):
                diagLine = 0
                testSplit = all_of_it.split('\n')
                while 'Reason for Referral:' not in testSplit[diagLine]:
                    diagLine = diagLine + 1
                nextLine = testSplit[diagLine + 1].split('   ')[0]
                section = section + ' ' + nextLine
            diagnosis = section

        # Now let's get the report date
        if 'Report Date: ' in all_of_it:
            section = all_of_it[all_of_it.index('Report Date: ') + len('Report Date: '):]
            section = section[:section.index('\n')]
            section = section.split()
            section = section[0]
            received = section
            dateType = 'Report Date'
        elif 'Received Date: ' in all_of_it:
            section = all_of_it[all_of_it.index('Received Date: ') + len('Received Date: '):]
            section = section[:section.index('\n')]
            section = section.split()
            section = section[0]
            received = section
            dateType = 'Received Date'

        # NOW we get the gene list!
        starts = []
        lists = []

        startStrings = ['Variants of Unknown Clinical Significance\n',
                        'Genes Evaluated (by molecular analysis unless otherwise noted)',
                        'select exons of the genes listed unless another method is noted.',
                        'select exons of the genes listed.',
                        'listed unless another method is noted.',
                        'unless another method is noted.',
                        'Biomarkers Evaluated (by molecular analysis unless otherwise noted)',
                        'sequencing of select exons of the genes\nlisted.',
                        'The genes sequenced\nare',
                        'Probe Set Detail',
                        'The genes sequenced are ',
                        'The genes evaluated are ',
                        'genes evaluated are',
                        'Molecular Testing Detail',
                        'FISH Testing Detail',
                        'Test Results ISCN Data',
                        'Histology Testing Detail',
                        'Overall Summary', #this is where we'll find stuff about 'test not performed
                        'Biomarker/Assay Results',
                        'Interpretation',
                        'Results Summary / Diagnostic & Prognostic Implications',
                        'Test Result',
                        'Results Summary\n'
                        ]
        if not any(x in all_of_it for x in startStrings):
            print(all_of_it)
            print(txt)
            input()
        while any(x in all_of_it for x in startStrings):
            for x in startStrings:
                if x in all_of_it:
                    starter = x
                    endStrings = ['References', 'Methodology', '©', 'Comments:', 'Electronic Signature',
                                  '\nClinical', 'Results Summary', 'FISH Testing Detail', 'Histology Testing Detail',
                                  'Test orders', 'Variants of Unknown Clinical Significance\n', 'Therapeutic Implications',
                                  'References', 'Test Description', 'See full list', 'Biomarker/Assay Results', 'Nuclei Scored',
                                  'Biomarker/Assay']
                    fullSection = all_of_it[all_of_it.index(x):]
                    section = all_of_it[all_of_it.index(x) + len(x):]
                    if not any(y in section.replace(starter, '') for y in endStrings):
                        print('here')
                        print(section)
                        print(txt)
                        input()
                    endPos = 9999999999999
                    for y in endStrings:
                        if y in section and y != x and y not in x:
                            if section.index(y) < endPos:
                                endPos = section.index(y)
                    section = section[:endPos]
                    fullSection = fullSection[:endPos+len(x)]
                    while section.startswith(':') or section.startswith('\n') or section.startswith(' '):
                        section = section[1:]
                    #print(all_of_it)
                    all_of_it = all_of_it.replace(fullSection, '')
                    if starter.endswith(' '):
                        starter = starter.strip()
                    starts.append(starter)
                    lists.append(section.strip())
                    #print(starts[-1])
                    #print('------')
                    #print(lists[-1])
                    #print(txt)
                    #print(len(lists))
        #print("END OF TEST")
        #print('=================')

        # This is a split section. Let's re-combine
        for start in range(0, len(starts)):
            if starts[start] == 'Test Results ISCN Data':
                starts[start] = 'FISH Testing Detail'

        # Let's combine sections with the same header
        if len(list(set(starts))) < len(starts):
            newStarts = []
            newLists = []
            for item in list(set(starts)):
                newStarts.append(item)
                comb = ''
                for bit in range(0, len(starts)):
                    if item == starts[bit]:
                        comb = comb + '\n' + lists[bit]
                newLists.append(comb)
            starts = newStarts
            lists = newLists

        # So, now, at this point we have to do the interpretation.
        # Our first port of call is if there's a list of the biomarkers. I'll want to see the
        # tests that don't have one of these bad boys.

        # We're storing all the platforms, results, and biomarker names
        fullPlatforms = []
        fullResults = []
        fullBioms = []
        fullBioNames = []
        fullExons = []
        fullTypes = []
        hasSeperators = False

        # First, let's see if this is the kind of test that has comma-separated 'biomarker' sections or not.
        # Otherwise, it's ugly to separate!
        if 'Biomarkers Evaluated (by molecular analysis unless otherwise noted)' in starts:
            fullIndex = starts.index('Biomarkers Evaluated (by molecular analysis unless otherwise noted)')
            lists[fullIndex] = lists[fullIndex].replace('\n', ' ')
            if ',' in lists[fullIndex]:
                hasSeperators = True

        altStarts = ['The genes sequenced are', 'select exons of the genes listed unless another method is noted.', 'select exons of the genes listed.',
                     'listed unless another method is noted.', 'sequencing of select exons of the genes\nlisted.', 'unless another method is noted.',
                     'The genes evaluated are', 'Genes Evaluated (by molecular analysis unless otherwise noted)', 'The genes sequenced\nare',
                     'genes evaluated are']

        if any(alt in starts for alt in altStarts) and not hasSeperators:
            for alt in altStarts:
                if alt in starts:
                    starter = alt
                    break
            fullIndex = starts.index(starter)
            lists[fullIndex] = lists[fullIndex].replace('\n', ' ').replace(' and', ',').replace('.', ',').replace('Other methods: ', '')
            while any(furtherStart in lists[fullIndex] for furtherStart in altStarts):
                whole = lists[fullIndex]
                for fs in altStarts:
                    if fs in whole:
                        whole = whole[whole.index(fs) + len(fs):]
                lists[fullIndex] = whole
            lists[fullIndex] = lists[fullIndex].strip()
            if ',' in lists[fullIndex]:
                fullBioms = lists[fullIndex].split(',')
            else:
                fullBioms = lists[fullIndex].split()
            fullBioms = list(filter(None, fullBioms))
            # In the non-comma-separated ones, sometimes we have to figure out how to put FISH together with the right token
            disregardFish = False

            for biom in range(0, len(fullBioms)):
                fullBioms[biom] = fullBioms[biom].strip()
                removeExtras = fullBioms[biom].split()
                extrasCopy = fullBioms[biom].split()

                if fullBioms[biom] in ['FISH'] and not disregardFish:
                    fullPlatforms[-1] = fullBioms[biom]
                    continue

                if fullBioms[biom] in ['FISH'] and disregardFish:
                    disregardFish = False
                    continue

                if fullBioms[biom] in ['Tumor']:
                    fullBioms[biom] = 'TMB'
                    removeExtras = fullBioms[biom].split()
                    extrasCopy = fullBioms[biom].split()

                if fullBioms[biom] in ['amp']:
                    fullBioNames[-1] = fullBioNames[-1] + ' ' + fullBioms[biom]
                    fullPlatforms[-1] = 'FISH'
                    continue

                if fullBioms[biom] in ['Analysis', '22c3', '22C3', 'FDA', '(KEYTRUDA®)', 'only)', 'Mutation', 'Mutational', 'Burden']:
                    continue

                # Sometimes we have "NB FISH"
                if fullBioms[biom] in ['NB']:
                    fullBioNames[-1] = fullBioNames[-1] + ' ' + fullBioms[biom]
                    fullPlatforms[-1] = 'FISH'
                    disregardFish = True
                    continue

                for re in range(0, len(removeExtras)):
                    if removeExtras[re] in ['Deletion', 'Exon', 'FISH', 'IHC'] or removeExtras[re].replace('-', '').replace('+', '').isnumeric():
                        removeExtras[re] = ''
                removeExtras = list(filter(None, removeExtras))
                if len(removeExtras) > 1:
                    if removeExtras[1].isupper():
                        removeExtras = removeExtras[-1]
                        fullBioms[biom] = removeExtras
                else:
                    fullBioms[biom] = ' '.join(extrasCopy)
                if 'Exon' in fullBioms[biom]:
                    addToExon = ''
                    split = fullBioms[biom].split()
                    for item in split:
                        if item.replace('-', '').isnumeric():
                            fullBioms[biom] = fullBioms[biom].replace(item, '')
                            addToExon = addToExon + ', ' + item
                        if item.replace('+', '').isnumeric():
                            fullBioms[biom] = fullBioms[biom].replace(item, '')
                            addToExon = item.replace('+', ', ')
                        elif 'Exon' in item:
                            fullBioms[biom] = fullBioms[biom].replace(item, '')
                    while addToExon.startswith(',') or addToExon.startswith(' '):
                        addToExon = addToExon[1:]
                    addToExon = addToExon.strip()
                    fullExons.append(addToExon)
                    while '  ' in fullBioms[biom]:
                        fullBioms[biom] = fullBioms[biom].replace('  ', ' ')
                else:
                    fullExons.append('')
                if 'FISH' in fullBioms[biom]:
                    fullBioNames.append(fullBioms[biom].replace(' FISH', ''))
                    fullPlatforms.append('FISH')
                elif 'IHC' in fullBioms[biom]:
                    fullBioNames.append(fullBioms[biom].replace(' IHC', ''))
                    fullPlatforms.append('IHC')
                elif fullBioms[biom].startswith('('):
                    # The parenthases get ALL out of wack without separators, and
                    # I don't think they're important. I'll add them back in if they are
                    if hasSeperators:
                        fullBioNames[-1] = fullBioNames[-1] + ' ' + fullBioms[biom]
                    fullExons = fullExons[:-1]
                elif any(x in fullBioms[biom] for x in ['Deletion', 'Amplification']):
                    fullBioNames.append(fullBioms[biom].split()[0])
                    fullPlatforms.append('FISH')
                elif any(x in fullBioms[biom] for x in ['Methylation']):
                    fullBioNames.append(fullBioms[biom].split()[0])
                    fullPlatforms.append('Bisulfate DNA PCR')

                else:
                    fullBioNames.append(fullBioms[biom])
                    fullPlatforms.append('NGS')

        elif 'Biomarkers Evaluated (by molecular analysis unless otherwise noted)' in starts:
            fullIndex = starts.index('Biomarkers Evaluated (by molecular analysis unless otherwise noted)')
            lists[fullIndex] = lists[fullIndex].replace('\n', ' ')
            commas = False
            if ',' in lists[fullIndex]:
                fullBioms = lists[fullIndex].split(',')
                commas = True
            else:
                fullBioms = lists[fullIndex].split()
            for biom in range(0, len(fullBioms)):
                noGos = ['NB', 'FISH', 'Deletion', '(KEYTRUDA®)', 'Analysis', 'for', 'NSCLC',]
                notNGS = False
                fullBioms[biom] = fullBioms[biom].strip()
                if '\n' in fullBioms[biom]:
                    fullBioms[biom] = fullBioms[biom].replace('\n', '')
                # If we're seeing something about exons, we know to add that to the previous one
                if 'Exon' in fullBioms[biom]:
                    if not commas:
                        fullExons[-1] = 'ADD ME'
                        notNGS = True
                else:
                    if not fullBioms[biom].replace('-','').replace('+', '').replace(',','').strip().isnumeric():
                        if fullBioms[biom] not in noGos:
                            fullExons.append('')
                # If this actually IS the exon, go and add it where it's needed
                if fullBioms[biom].replace('-','').replace('+', '').replace(',','').strip().isnumeric():
                    add = fullExons.index('ADD ME')
                    fullExons[add] = fullBioms[biom]
                    notNGS = True
                # Otherwise, if something is called out as being like 'MET FISH' that's the platform
                if ' FISH' in fullBioms[biom]:
                    fullBioms[biom] = fullBioms[biom].replace(' FISH', '')
                    fullPlatforms.append('FISH')
                # We sometimes get like PDGFRA AMP and don't want it
                elif ' amp' in fullBioms[biom]:
                    fullBioms[biom] = fullBioms[biom].replace(' amp', '')
                    fullPlatforms.append('FISH')
                # And MSI and TMB are otherwise obvious exceptions
                elif fullBioms[biom] in ['Microsatellite Instability', 'MSI']:
                    fullPlatforms.append('NGS')
                elif ('Tumor' in fullBioms[biom] and 'Burden' in fullBioms[biom]):
                    fullPlatforms.append('NGS')
                # Pan-TRK and PD-L1 are otherwise added in as IHC
                elif fullBioms[biom] in ['Pan-TRK'] or 'PD-L1' in fullBioms[biom]:
                    fullPlatforms.append('IHC')
                elif 'Methylation' in fullBioms[biom]:
                    fullPlatforms.append('Bisulfate DNA PCR')
                elif notNGS:
                    notNGS = False
                else:
                    if fullBioms[biom] not in noGos:
                        fullPlatforms.append('NGS')

                if 'Exon' not in fullBioms[biom] and not fullBioms[biom].replace('-', '').replace('+', '').strip().isnumeric() and fullBioms[biom] not in noGos:
                    fullBioNames.append(fullBioms[biom])
                else:
                    if hasSeperators:
                        if 'Exon' in fullBioms[biom]:
                            fullBioNames.append(fullBioms[biom].split('Exon')[0].strip())
                            otherPart = fullBioms[biom].split('Exon')[1].strip()
                            if len(otherPart.split()) > 1:
                                fullExons.append(otherPart.split()[0])
                                fullBioNames[-1] = fullBioNames[-1] + ' ' + ' '.join(otherPart.split()[1:])
                            else:
                                fullExons.append(otherPart)

        elif 'Probe Set Detail' in starts and 'Interpretation' not in starts:
            fullIndex = starts.index('Probe Set Detail')
            results = lists[fullIndex]
            results = results.split('\n')
            if 'Results: Negative' in all_of_it:
                for res in results:
                    if ':' not in res:
                        continue
                    section = res[:res.index(':')]
                    fullBioNames.append(section)
                    fullPlatforms.append('FISH')
                    fullResults.append('Negative, inferred')
                    fullTypes.append('FISH')
                    fullExons.append('')

        # Only got the probe set and the interpretation
        elif 'Probe Set Detail' in starts and 'Interpretation' in starts:
            fullIndex = starts.index('Interpretation')
            results = lists[fullIndex]
            results = results.split('\n')
            for res in range(0, len(results)):
                if 'This study' in results[res] or 'All the' in results[res] or ':' not in results[res] or 'Average' in results[res]:
                    if len(fullResults) != 0:
                        break
                    else:
                        continue
                fullBioNames.append(results[res].split()[0])
                fullPlatforms.append('FISH')
                fullTypes.append(results[res][:results[res].index(':')].replace(results[res].split()[0] + ' ', ''))
                fullResults.append(results[res][results[res].index(':')+1:].strip().replace('(See Below)', ''))
                fullExons.append('')

        # Only fish results
        elif 'FISH Testing Detail' in starts and 'Histology Testing Detail' in starts:
            resSec = starts.index('FISH Testing Detail')
            results = lists[resSec]
            results = results.split('\n')
            results = results[1:]
            for line in results:
                if ('FISH' not in line and ' by ' not in line) or 'nuc ish' not in line:
                    continue
                if 'FISH' in line:
                    if 'Amplification' in line[:line.index('FISH')].strip():
                        fullTypes.append('Amplification')
                        fullBioNames.append(line[:line.index('FISH')].replace('Amplification', '').strip())
                    elif 'Deletion' in line[:line.index('FISH')].strip():
                        fullTypes.append('Deletion')
                        fullBioNames.append(line[:line.index('FISH')].replace('Amplification', '').strip())
                    else:
                        fullTypes.append('')
                        fullBioNames.append(line[:line.index('FISH')].strip())
                    fullResults.append(line[line.index('FISH') + len('FISH'): line.index('nuc ish')].strip())
                    fullPlatforms.append('FISH')
                    fullExons.append('')
                elif ' by ' in line:
                    if 'Amplification' in line[:line.index(' by ')].strip():
                        fullTypes.append('Amplification')
                        fullBioNames.append(line[:line.index(' by ')].replace('Amplification', '').strip())
                    elif 'Deletion' in line[:line.index(' by ')].strip():
                        fullTypes.append('Deletion')
                        fullBioNames.append(line[:line.index(' by ')].replace('Amplification', '').strip())
                    else:
                        fullBioNames.append(line[:line.index(' by ')].strip())
                    fullResults.append(line[line.index(' by ') + len(' by '): line.index('nuc ish')].strip())
                    fullPlatforms.append('FISH')
                    fullExons.append('')
            # Now histology
            resSec = starts.index('Histology Testing Detail')
            results = lists[resSec]
            results = results.split('\n')
            results = results[1:]
            if 'PD-L1' in results[0]:
                fullBioNames.append(' '.join(results[0].split()[:-1]))
                fullResults.append(results[0].split()[-1])
                fullPlatforms.append('IHC')
                fullExons.append('')
            else:
                print(results)
                print('aberrent results')
                input()

        # Unknown Test Type
        else:
            print('unknown test typeZ')
            print(starts)
            print(txt)
            #input()

        # At this point, we should have
        # fullBiomList, fullExonList, fullPlatformList all filled in and the same length
        # Rather than append the rest of the lists one by one, let's fill them with empties and get indices
        for x in range(0, len(fullBioNames)):
            if len(fullResults) < len(fullBioNames):
                fullResults.append('')
            if len(fullTypes) < len(fullBioNames):
                fullTypes.append('')

        # Alternate headers where MSI/TMB might be hiding
        alternateStarts = ['Biomarker/Assay Results']

        # I'm assuming they should then have a 'molecular testing detail' with the positive results
        # This contains our NGS results, MSI, and TMB
        if 'Molecular Testing Detail' in starts:
            resultsIndex = starts.index('Molecular Testing Detail')
            results = lists[resultsIndex]
            for biom in range(0, len(fullBioNames)):
                # Let's handle the one special case first, actually. Bisfulate
                if fullPlatforms[biom] == 'Bisulfate DNA PCR':
                    foundIt = False
                    tempName = fullBioNames[biom].split()[0]
                    if tempName in results and 'Methylation' in results:
                        foundIt = True
                        section = results[results.index('Methylation') + len('Methylation'):]
                        section = section.strip()
                        if '\n' in section:
                            section = section[:section.index('\n')]
                        if 'QNS' in section:
                            fullResults[biom] = 'QNS'
                        elif 'TNP' in section:
                            fullResults[biom] = 'Test Not Performed'
                        else:
                            if 'Detected' not in section:
                                print(section)
                                input()
                            section = section[:section.index('Detected') + len('Detected')]
                            fullResults[biom] = section.strip()
                    if 'Biomarker/Assay Results' in starts and not foundIt:
                        results = lists[starts.index('Biomarker/Assay Results')]
                        if tempName + ' Methylation' in results:
                            foundIt = True
                            section = results[results.index(tempName + ' Methylation') + len(tempName + ' Methylation'):]
                            if 'Detected' in section:
                                section = section[:section.index('Detected') + len('Detected')]
                            elif 'QNS' in section:
                                section = 'QNS'
                        else:
                            lines = results.split('\n')
                            for line in lines:
                                if tempName in line and 'Methylation' in line:
                                    foundIt = True
                                    section = results[results.index(' Methylation') + len(' Methylation'):]
                                    if 'Detected' in section:
                                        section = section[:section.index('Detected') + len('Detected')]
                                    elif 'QNS' in section:
                                        section = 'QNS'
                        fullResults[biom] = section.strip()
                    if 'Test Result' in starts and not foundIt:
                        results = lists[starts.index('Test Result')]
                        if tempName in results and 'Methylation' in results:
                            foundIt = True
                            section = results[results.index('Methylation') + len('Methylation'):]
                            section = section.strip()
                            section = section[:section.index('Detected') + len('Detected')]
                            fullResults[biom] = section.strip()
                    # Last ditch
                    if 'Overall Summary' in starts and not foundIt:
                        results = lists[starts.index('Overall Summary')]
                        if 'methylation' in results:
                            foundIt = True
                            results = results.split('\n')
                            for line in results:
                                if 'methylation' in line:
                                    if 'There is no evidence' in line or 'Not detected' in line or 'Not Detected' in line:
                                        fullResults[biom] = 'Explicit Negative'
                                    elif 'Detected.' in line:
                                        fullResults[biom] = 'Positive'
                                    else:
                                        print(line)
                                        input()
                    if 'Results Summary / Diagnostic & Prognostic Implications' in starts and not foundIt:
                        results = lists[starts.index('Results Summary / Diagnostic & Prognostic Implications')]
                        if 'methylation' in results:
                            foundIt = True
                            results = results.split('\n')
                            for line in results:
                                if 'methylation' in line:
                                    if 'There is no evidence' in line or 'Not detected' in line or 'Not Detected' in line:
                                        fullResults[biom] = 'Explicit Negative'
                                    elif 'Detected.' in line:
                                        fullResults[biom] = 'Positive'
                                    else:
                                        print(line)
                                        input()
                    if 'Interpretation' in starts and not foundIt:
                        results = lists[starts.index('Interpretation')]
                        if 'methylation' in results:
                            foundIt = True
                            results = results.split('\n')
                            for line in results:
                                if 'methylation' in line:
                                    if 'There is no evidence' in line or 'Not detected' in line or 'Not Detected' in line:
                                        fullResults[biom] = 'Explicit Negative'
                                    elif 'Detected.' in line:
                                        fullResults[biom] = 'Positive'
                                    else:
                                        print(line)
                                        input()

                    if not foundIt:
                        fullResults[biom] = 'Not Given'
                        print("NO METHYLATION RESULTS?")
                        print(tempName)
                        print(results)
                        print(txt)
                    if fullResults[biom] == '':
                        fullResults[biom] = 'Not Given'
                        print(results)
                        print('***')
                        print(section)
                        print(fullBioNames[biom])
                        print(txt)
                        input()
                    else:
                        fullResults[biom] = fullResults[biom].strip()

                # First case is NGS genes - look for them showing up as 'Not Detected' or not showing up at all. Otherwise, they're positive!
                if fullPlatforms[biom] == 'NGS':
                    resultsIndex = starts.index('Molecular Testing Detail')
                    results = lists[resultsIndex]
                    if fullBioNames[biom] in results or fullBioNames[biom].split()[0] in results:
                        if len(fullBioNames[biom].split()) > 1:
                            if fullBioNames[biom].split()[0] in results and not fullBioNames[biom] in results:
                                name = fullBioNames[biom].split()[0]
                            else:
                                name = fullBioNames[biom]
                        else:
                            name = fullBioNames[biom]
                        bit = results[results.index(name):results.index(name)+40]
                        if 'Not Dete' in bit:
                            fullResults[biom] = 'Negative, inferred'
                        else:
                            fullResults[biom] = 'Positive'

                    else:
                        fullResults[biom] = 'Negative, inferred'

                # Next up is MSI/TMB
                elif fullPlatforms[biom] == 'MSI':
                    # Type should be MSI
                    fullTypes[biom] = 'MSI'
                    haventFound = True
                    msiResults = ''
                    if 'Microsatellite Instability MSI -' in results:
                        section = results[results.index('Microsatellite Instability MSI - ') + len('Microsatellite Instability MSI - '):]
                        if '(MSS)' not in section:
                            section = section.split()[0]
                        else:
                            section = section[:section.index('(MSS)')]
                        fullResults[biom] = section.strip()
                        haventFound = False
                    # Sometimes it just says 'TNP' for text not performed
                    elif 'Microsatellite Instability TNP -' in results:
                        fullResults[biom] = 'Test not performed'
                    # Sometimes it says "Microsatellite Instability MSI-Stable
                    elif 'Microsatellite Instability' in results:
                        section = results[results.index('Microsatellite Instability') + len('Microsatellite Instability'):]
                        if '\n' in section:
                            section = section[:section.index('\n')]
                        if '(MSS)' in section:
                            section = section[:section.index('(MSS)')]
                        print(section)
                        sectionS = section.split()
                        endInd = 999999
                        for word in sectionS:
                            if word.isupper() and section.index(word) < endInd:
                                endInd = section.index(word)
                        section = section[:endInd].strip()
                        fullResults[biom] = section

                    else:
                        haventFound = True
                    # First, we'll look in 'Biomarker/Assay Results'
                    if 'Biomarker/Assay Results' in starts and haventFound:
                        msiResultsIndex = starts.index('Biomarker/Assay Results')
                        msiResults = lists[msiResultsIndex]
                        if 'Microsatellite Instability' in msiResults:
                            section = msiResults[msiResults.index('Microsatellite Instability ') + len('Microsatellite Instability '):]
                            if '\n' in section:
                                section = section[:section.index('\n')]
                            fullResults[biom] = section.strip()
                            haventFound = False
                    # Then in 'Results Summary / Diagnostic & Prognostic Implications'
                    if 'Results Summary / Diagnostic & Prognostic Implications' in starts and haventFound:
                        msiResultsIndex = starts.index('Results Summary / Diagnostic & Prognostic Implications')
                        msiResults = lists[msiResultsIndex]
                        if '(MSI-' in msiResults:
                            section = msiResults[msiResults.index('(MSI-'):]
                            section = section[:section.index('.')]
                            section = section.replace('(MSI-', '').replace(')', '').strip()
                            fullResults[biom] = section.strip()
                            haventFound = False

                    # Finally, kind of a hail mary - this can just be anywhere in the report
                    elif 'Microsatellite instability was not performed' in msiResults and haventFound:
                        fullResults[biom]  = ('Not Performed')
                        haventFound = False
                    elif 'There is no evidence of microsatellite instability.' in msiResults and haventFound:
                        fullResults[biom]  = ('Explicit Negative')
                        haventFound = False

                    # Turn this on to find reports that don't have MSI turned on anywhere
                    if haventFound:
                        #print(results)
                        #print(fullBioNames)
                        print('NO MSI?')
                        print(txt)
                        #input()
                    else:
                        if 'Tumor' in fullResults[biom]:
                            fullResults[biom] = fullResults[biom][:fullResults[biom].index('Tumor')]

                if fullPlatforms[biom] == 'TMB':
                    fullTypes[biom] = 'NGS'
                    if 'Tumor Mutation Burden Result' in results:
                        section = results[results.index('Tumor Mutation Burden Result') + len('Tumor Mutation Burden Result'):]
                        if '\n' in section:
                            section = section[:section.index('\n')]
                        fullResults[biom] = section.strip()
                    else:
                        if 'Biomarker/Assay Results' in starts:
                            tmbResultsIndex = starts.index('Biomarker/Assay Results')
                            tmbResults = lists[tmbResultsIndex]
                            if 'Tumor Mutation Burden Result' in tmbResults:
                                section = tmbResults[tmbResults.index('Tumor Mutation Burden Result ') + len('Tumor Mutation Burden Result '):]
                                if '\n' in section:
                                    section = section[:section.index('\n')]
                                fullResults[biom] = section.strip()
                            # Another place to look for TMB
                            elif 'Results Summary / Diagnostic & Prognostic Implications' in starts:
                                secIndex = starts.index('Results Summary / Diagnostic & Prognostic Implications')
                                section = lists[secIndex]
                                section = section[section.index('- TUMOR MUTATION BURDEN (TMB):') + len('- TUMOR MUTATION BURDEN (TMB):'):]
                                section = section[:section.index('. ')]
                                fullResults[biom] = section.strip()
                            # Turn this on to see missed TMBs
                            else:
                                #print(results)
                                #print(fullBioNames)
                                #print(starts)
                                print(txt)
                                print('NO TMB1?')
                                fullResults[biom] = 'Not Given'
                                #input()
                        else:
                            #print(results)
                            #print(fullBioNames)
                            #print(starts)
                            print('NO TMB2?')
                            fullResults[biom] = 'Not Given'
                            #input()

        # Let's now try to get any VUSs
        if 'Variants of Unknown Clinical Significance\n' in starts:
            secIndex = starts.index('Variants of Unknown Clinical Significance\n')
            results = lists[secIndex]
            for gene in range(0, len(fullBioNames)):
                if fullBioNames[gene] in results:
                    fullResults[gene] = 'VUS'

        # There are two more parts: FISH and Histology
        if 'FISH Testing Detail' in starts:
            temp = ''
            resultsIndex = starts.index('FISH Testing Detail')
            results = lists[resultsIndex]

            results = results.replace(' Amplification by', ' by').replace(' Rearrangement by', ' by').replace('PDGFRa', 'PDGFRA')
            # Let's look for results that weren't in the original gene list
            fishLines = results.split('\n')
            fishLines = fishLines[1:]
            for line in fishLines:
                if ('FISH' not in line and ' by ' not in line) or 'nuc ish' not in line:
                    continue
                # First, let's loop through and see if we need to add anything this is for biomarkers that we don't have in our list yet
                # - sometimes, biomarkers are mentioned only here
                if 'FISH' in line:
                    line = line.replace(' by ', ' ')
                    if line[:line.index('FISH')].strip().replace('Non-Breast', 'NB') not in fullBioNames and line[:line.index('FISH')].replace(' Non-Breast', '').replace(' Amplification', '').replace(' Deletion', '').strip() not in fullBioNames:
                        fullTypes.append('')
                        fullBioNames.append(line[:line.index('FISH')].replace('Amplification', '').strip())
                        fullPlatforms.append('FISH')
                        fullExons.append('')
                        fullResults.append('')
                elif ' by ' in line:
                    if 'FISH' not in line:
                        line = line.replace(' by ', ' FISH ')
                    if line[:line.index('FISH')].strip().replace('Non-Breast', 'NB') not in fullBioNames and line[:line.index('FISH')].strip().replace(' Non-Breast', '') not in fullBioNames:
                        fullTypes.append('')
                        fullBioNames.append(line[:line.index('FISH')].replace('Amplification', '').strip())
                        fullPlatforms.append('FISH')
                        fullExons.append('')
                        fullResults.append('')
            # Now let's get the biomarkers that we already know about
            for biom in range(0, len(fullBioNames)):
                if fullPlatforms[biom] == 'FISH':
                    # We might want 'amp' out of the results
                    if 'amp' in fullBioNames[biom]:
                        tempName = fullBioNames[biom]
                        fullBioNames[biom] = fullBioNames[biom].replace(' amp', '')
                    # We switch pretty freely between 'non-breast' and 'NB' for HER2
                    if 'HER2 Non-Breast' in results:
                        if fullBioNames[biom] == 'HER2':
                            temp = 'HER2'
                            fullBioNames[biom] = 'HER2 NB'
                    if fullBioNames[biom].replace('NB', 'Non-Breast') + ' FISH' in results \
                        or fullBioNames[biom].replace('NB', 'Non-Breast') + ' by FISH' in results \
                        or fullBioNames[biom].replace('NB', 'Non-Breast') + ' by ' in results:
                        results = results.replace(' by FISH', ' FISH')
                        results = results.replace(' by ', ' FISH ')
                        if ' by' in fullBioNames[biom]:
                            fullBioNames[biom] = fullBioNames[biom].replace(' by', '')
                        section = results[results.index(fullBioNames[biom].replace('NB', 'Non-Breast') + ' FISH') + len(fullBioNames[biom].replace('NB', 'Non-Breast') + ' FISH '):]
                        if 'nuc' in section:
                            section = section[:section.index('nuc')]
                        elif '\n' in section:
                            section = section[:section.index('\n')]
                        elif '(' in section:
                            section = section[:section.index('(')]
                        else:
                            if ' ' in section:
                                section = section[:section.index(' ')]
                        fullResults[biom] = section
                        if temp != '':
                            fullBioNames[biom] = temp
                    elif 'Overall Summary' in starts:
                        if fullBioNames[biom] == 'HER2 NB':
                            fullBioNames[biom] = 'HER2'
                        startIndex = starts.index('Overall Summary')
                        section = lists[startIndex]
                        if 'FISH studies' in section:
                            section = section.split('-')
                            thisBit = ''
                            for x in section:
                                if 'FISH studies' in x:
                                    thisBit = x
                                    break
                            thisBit = thisBit.split(',')
                            if fullBioNames[biom] in ' '.join(thisBit):
                                onDeck = ''
                                for bt in thisBit:
                                    bt = bt.replace('\n', '')
                                    if 'no evidence' in bt or 'negative results' in bt:
                                        onDeck = 'Negative, inferred'
                                    else:
                                        onDeck = 'Positive'
                                    if fullBioNames[biom] in bt:
                                        fullResults[biom] = onDeck
                                        if 'amplification' in bt:
                                            fullTypes[biom] = 'amplification'
                                        elif 'deletion' in bt:
                                            fullTypes[biom] = 'deletion'
                                        else:
                                            fullTypes[biom] = ''
                        else:
                            fullResults[biom] = 'Not Given'
                            print(fullBioNames[biom])
                            print('NO FISH RESULTS2?')
                            #print(fullBioNames)
                            #print(results)
                            print(txt)
                            #print(starts)
                            #if fullBioNames[biom] not in ['PDGFRA', 'CLL', 'CLL Analysis']:
                            #    input()
                    # We might also fine some results in the 'results summary' section
                    elif 'Results Summary\n' in starts:
                        if fullBioNames[biom] == 'HER2 NB':
                            fullBioNames[biom] = 'HER2'
                            startInd = starts.index('Results Summary\n')
                            section = lists[startInd]
                            if 'Pertinent Negatives' in section:
                                section = section[section.index('Pertinent Negatives'):]
                                if fullBioNames[biom] in section:
                                    fullResults[biom] = 'Explicit Negative'
                            else:
                                fullResults[biom] = 'Not Given'
                                print(fullBioNames[biom])
                                print('NO FISH RESULTS3?')
                                # print(fullBioNames)
                                # print(results)
                                print(txt)
                                # print(starts)
                                #if fullBioNames[biom] not in ['PDGFRA', 'CLL', 'CLL Analysis']:
                                #    input()
                    # Last Chance
                    elif 'Results Summary / Diagnostic & Prognostic Implications' in starts:
                        section = lists[starts.index('Results Summary / Diagnostic & Prognostic Implications')]
                        if 'Disease Relevant Genes with No' in section:
                            section = section[section.index('Disease Relevant Genes with No'):]
                            if 'See' in section:
                                section = section[:section.index('See')]
                            if 'Therapeutic Implications' in section:
                                section = section[:section.index('Therapeutic Implications')]
                            if fullBioNames[biom] in section:
                                fullResults[biom] = 'Explicit Negative'
                        else:
                            fullResults[biom] = 'Not Given'
                            print('NO FISH RESULTS4?')
                            print(fullBioNames[biom])
                            # print(fullBioNames)
                            # print(results)
                            print(txt)
                            # print(starts)
                            #if fullBioNames[biom] not in ['CLL', 'CLL Analysis']:
                            #    input()

                    else:
                        fullResults[biom] = 'Not Given'
                        print('NO FISH RESULTS?')
                        print(fullBioNames[biom])
                        #print(fullBioNames)
                        #print(results)
                        print(txt)
                        print(starts)
                        #if fullBioNames[biom] not in ['CLL', 'CLL Analysis']:
                        #    input()


        if 'Histology Testing Detail' in starts:
            resultsIndex = starts.index('Histology Testing Detail')
            results = lists[resultsIndex]
            for biom in range(0, len(fullBioNames)):
                if fullPlatforms[biom] == 'IHC':
                    if 'TRK' in fullBioNames[biom]:
                        if 'Pan-TRK' in results:
                            if 'PD-L1' in results:
                                section = results[results.index('Pan-TRK') + len('Pan-Trk'):results.index('PD-L1')]
                            else:
                                section = results[results.index('Pan-TRK') + len('Pan-Trk'):]
                            fullResults[biom] = section.strip()
                        # Another place to look for Pan-TRK
                        elif 'Results Summary / Diagnostic & Prognostic Implications' in starts:
                            summaryInd = starts.index('Results Summary / Diagnostic & Prognostic Implications')
                            trkPart = lists[summaryInd]
                            if 'Pan-TRK by IHC:' in trkPart:
                                section =  trkPart[trkPart.index('Pan-TRK by IHC:'):]
                                section = section[:section.index('.')]
                                fullResults[biom] = section
                            # Turn on to find missing Pan-TRK
                            else:
                                #print(section)
                                print('NO PAN-TRK2?')
                                #print(fullBioNames)
                                #print(txt)
                                #input()

                        elif 'Results Summary' in starts:
                            summaryInd = starts.index('Results Summary')
                            trkPart = lists[summaryInd]
                            if 'Pan-TRK:' in trkPart:
                                section = trkPart[trkPart.index('Pan-TRK:'):]
                                section = section[:section.index('\n')]
                                fullResults[biom] = section
                            else:
                                #print(section)
                                print('NO PAN-TRK23')
                                #print(fullBioNames)
                                #print(txt)
                                #input()
                        else:
                            #print(section)
                            print('NO PAN-TRK?')
                            #print(fullBioNames)
                            #print(txt)
                            #input()

                    # Now let's look for PD-L1
                    elif 'PD-L1' in fullBioNames[biom]:
                        joinedLists = ' '.join(lists)
                        while '  ' in joinedLists:
                            joinedLists = joinedLists.replace('  ', ' ')
                        if 'PD-L1' in results:
                            if 'CPS' in results:
                                if '(PD' not in results:
                                    if '(No' in results:
                                        section = results[results.index('PD-L1'):results.index('(No')]
                                else:
                                    section = results[results.index('PD-L1'):results.index('(PD')]
                                if 'CPS' in section:
                                    section = section[section.index('CPS'):]
                                fullResults[biom] = section.strip()

                            elif 'for NSCLC' in results:
                                section = results[results.index('for NSCLC') + len('for NSCLC'):]
                                if '\n' in section:
                                    section = section[:section.index('\n')]
                                if section.strip() == '':
                                    section = results[results.index('FDA') + len('FDA'):]
                                    section = section[:section.index('\n')]
                                fullResults[biom] = section.strip()

                            elif 'for TNBC (Breast) IC' in results:
                                section = results[results.index('for TNBC (Breast) IC') + len('for TNBC (Breast) IC'):]
                                if '\n' in section:
                                    section = section[:section.index('\n')]
                                fullResults[biom] = section.strip()

                            elif 'FDA' in results:
                                section = results[results.index('FDA') + len('FDA'):]
                                if '\n' in section:
                                    section = section[:section.index('\n')]
                                fullResults[biom] = section.strip()

                        # Other things that PD-L1 might be!
                        elif 'PD-L1 is expressed' in joinedLists:
                            fullResults[biom] = 'Positive'
                        elif 'PD-L1 22C3 by IHC: Please see separate report.' in joinedLists or 'PD-L1 22C3 by IHC: See separate report' in joinedLists:
                            fullResults[biom] = 'Results in separate report'
                        elif 'PD-L1 is highly expressed' in joinedLists:
                            fullResults[biom] = 'Positive'
                        elif 'PD-L1 is not expressed' in joinedLists:
                            fullResults[biom] = 'Explicit Negative'
                        elif 'PD-L1 22C3 by IHC: Please refer to separate report' in joinedLists:
                            fullResults[biom] = 'Results in separate report'
                        elif 'Please refer to previous report for the PD-L1 IHC results' in joinedLists:
                            fullResults[biom] = 'Results in separate report'
                        elif 'Test Result' in starts:
                            secIndex = starts.index('Test Result')
                            section = lists[secIndex]
                            if 'PD-L1' in section:
                                if 'CPS' in section:
                                    if '(PD' not in section:
                                        section = section[section.index('PD-L1'):section.index('(No')]
                                    else:
                                        section = section[section.index('PD-L1'):section.index('(PD')]
                                    section = section[section.index('CPS'):]
                                    fullResults[biom] = section.strip()
                                elif 'for NSCLC' in section:
                                    section = section[section.index('for NSCLC') + len('for NSCLC'):]
                                    if '\n' in section:
                                        section = section[:section.index('\n')]
                                    fullResults[biom] = section.strip()
                                elif 'for TNBC (Breast) IC' in section:
                                    section = section[section.index('for TNBC (Breast) IC') + len('for TNBC (Breast) IC'):]
                                    if '\n' in section:
                                        section = section[:section.index('\n')]
                                    fullResults[biom] = section.strip()

                        else:
                            #print(section)
                            print('NO PD-L1?')
                            print(txt)
                            #print(fullBioNames)
                            #input()

        # Make sure we actually did the test
        explanatorySections = ['Overall Summary', 'Interpretation', 'Results Summary / Diagnostic & Prognostic Implications']
        doneIt = False
        if any(sec in starts for sec in explanatorySections):
            for sec in explanatorySections:
                if sec in starts and not doneIt:
                    resultsIndex = starts.index(sec)
                    results = lists[resultsIndex]
                    results = results.replace('\n', ' ')
                    if 'insufficient or no tumor' in results.lower() or 'an insufficient quantity' in results.lower() or 'the quantity of dna is suboptimal' in results.lower():
                        doneIt = True
                        for biom in range(0, len(fullBioNames)):
                            fullResults[biom] = 'QNS'
                    if 'NEXT GENERATION SEQUENCING' in results:
                        section = results[results.index('NEXT GENERATION SEQUENCING'):]
                        if 'Quantity not sufficient (QNS)' in section:
                            for rgb in range(0, len(fullBioNames)):
                                if fullPlatforms[rgb] == 'NGS':
                                    fullResults[rgb] = 'QNS'
                        elif 'No pathogenic mutations' in section:
                            for rgb in range(0, len(fullBioNames)):
                                if fullPlatforms[rgb] == 'NGS':
                                    fullResults[rgb] = 'Negative, inferred'
                        if 'Variants of unknown clinical significance' in section:
                            section = section[section.index('Variants of unknown clinical significance'):]
                            if '.' in section:
                                section = section[:section.index('.')]
                            for rgb in range(0, len(fullBioNames)):
                                if fullPlatforms[rgb] == 'NGS' and fullBioNames[rgb] in section:
                                    fullResults[rgb] = 'VUS'
                    else:
                        for rg in range(0, len(fullBioNames)):
                            if fullResults[rg] == '':
                                fullResults[rg] = 'Negative, inferred'

        # If we have any exons to split and represent correctly, let's do it here!
        for x in range(0, len(fullBioNames)):
            if fullExons[x] != '':
                exons = fullExons[x].split(',')
                exons = list(filter(None, exons))
                for ex in range(0, len(exons)):
                    if '-' in exons[ex]:
                        lower = int(exons[ex].split('-')[0])
                        upper = int(exons[ex].split('-')[1])
                        rang = range(lower, upper+1)
                        replacement = ''
                        for number in rang:
                            replacement = replacement + ', ' + str(number)
                        while replacement.startswith(',') or replacement.startswith(' '):
                            replacement = replacement[1:]
                        exons[ex] = replacement
                fullExons[x] = '{' + ','.join(exons) + "}"

            # Now let's add on all the fields we found!
            geneList.append(fullBioNames[x])
            exonList.append('{' + fullExons[x] + '}')
            variantList.append('')
            platformList.append(fullPlatforms[x])
            if len(fullTypes) != 0:
                typeList.append(fullTypes[0])
            else:
                typeList.append(fullPlatforms[x])
            callList.append(fullResults[x])
            standardAppends()

# Now Invitae. Why haven't I split this up yet?

if getInvitae:
    mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Invitae/'
    txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]
    fnum = 0
    brokens = []
    for txt in txts:
        if countFiles:
            print(fnum, ' of ', len(txts))
        fnum = fnum + 1
        file = mypath + txt
        file = open(file, mode='r')
        all_of_it = file.read()
        file.close()

        source = 'Invitae'
        filename = txt[:-20]

        testNames = ['Invitae Common Hereditary Cancers Panel', 'Invitae BRCA1 and BRCA2 STAT Panel', 'Invitae Arrhythmia Comprehensive Panel', 'Invitae Breast and Gyn Cancers Panel',
                     'Invitae Breast Cancer STAT Panel', 'Invitae Multi-Cancer Panel', 'Sequence analysis of', 'Sequence analysis and deletion/duplication testing of',
                     'Primary Panel (CF, SMA)', 'Invitae Singleton NIPS']
        if not any(tn in all_of_it for tn in testNames):
            print(all_of_it)
            input()
        else:
            for tn in testNames:
                if tn in all_of_it:
                    if tn.endswith(' of'):
                        tn = tn.replace(' of', '')
                    testType = tn
                    break
        # Let's get MRN
        if 'MRN:' in all_of_it:
            section = all_of_it[all_of_it.index('MRN:') + len('MRN:'):]
            section = section[1:]
            if section.index('\n') < section.index(' '):
                section = section[:section.index('\n')]
            else:
                section = section[:section.index(' ')]
            mrn = section
            if mrn.isalpha():
                mrn = ''
        else:
            print(all_of_it)
            input()

        ######
        # Let's get the test received date
        #####
        if 'Report date:' in all_of_it:
            section = all_of_it[all_of_it.index('Report date:') + len('Report date:'):]
            section = section[:section.index('\n')].strip()
            received = section
            dateType = 'Report Date'
        else:
            print(all_of_it)
            input()

        ######
        # Now Name
        #####
        if 'Patient name:' in all_of_it:
            section = all_of_it[all_of_it.index('Patient name:') + len('Patient name:'):]
            section = section[:section.index('Sample type')].strip()
            section = section.split()
            if len(section) == 2:
                firstName = section[0]
                middleName = ''
                lastName = section[1]
                srJr = ''
            elif len(section) == 3:
                if section[-1].lower().replace('.','') in ['jr', 'sr'] or section[-1].lower().replace('i', '') == '':
                    firstName = section[0]
                    middleName = ''
                    lastName = section[1].replace(',', '')
                    srJr = section[2]
                else:
                    firstName = section[0]
                    middleName = section[1]
                    lastName = section[2]
                    srJr = ''
            elif len(section) == 4:
                firstName = section[0]
                middleName = section[1]
                lastName = section[2].replace(',', '')
                srJr = section[3]
        else:
            print(all_of_it)
            input()

        ######
        # Now DOB
        #####
        if 'DOB:' in all_of_it:
            section = all_of_it[all_of_it.index('DOB:') + len('DOB:'):]
            section = section[:section.index('Sample')].strip()
            birthdate = section

        # Diagnosis is not given
        diagnosis = 'Not Given'

        # Primary site is not given
        primary = 'Not Given'

        # Sample type is here at least
        if 'Sample type:' in all_of_it:
            section = all_of_it[all_of_it.index('Sample type:') + len('Sample type:'):]
            section = section[:section.index('Report')].strip()
            specimenType = section

        # Sample site seems to be liquid for these
        if specimenType in ['Saliva', 'Blood', 'Plasma', 'Assisted Saliva']:
            specimenSite = 'Liquid'
        elif specimenType in ['Buccal Swab']:
            specimenSite = 'Swab'
        else:
            print(specimenType)
            input()

        endingStrings = ['Laboratory Director']

        negGenes = []
        posGenes = []
        vusGenes = []

        # Ok, that's all the info. Now for the genes!
        while 'GENE TRANSCRIPT' in all_of_it:
            if 'GENE TRANSCRIPT GENE TRANSCRIPT' in all_of_it:
                sectionStart = 'GENE TRANSCRIPT GENE TRANSCRIPT'
            else:
                sectionStart = 'GENE TRANSCRIPT'
            section = all_of_it[all_of_it.index(sectionStart):]
            if not any(end in section for end in endingStrings):
                print(all_of_it)
                input()
            endIndex = 9999999999
            for end in endingStrings:
                if end in section:
                    if section.index(end) < endIndex:
                        endIndex = section.index(end)
            section = section[:endIndex]
            all_of_it = all_of_it.replace(section, '')
            # Ok, that's the gene list. Let's get 'em
            section = section.replace('\n', ' ').replace('*', '')
            section = section.split()
            for token in section:
                if token.startswith('NM_') or token.replace('.', '').isnumeric() or token in ['GENE', 'TRANSCRIPT']:
                    continue
                elif token.startswith('('):
                    negGenes[-1] = negGenes[-1] + ' ' + token
                else:
                    negGenes.append(token)

        # Now we gotta get the positives

        posEnds = ['Additional Variant', 'GENE VARIANT']
        while 'RESULT: POSITIVE' in all_of_it:
            section = all_of_it[all_of_it.index('RESULT: POSITIVE'):]
            if not any(end in section for end in posEnds):
                print(all_of_it)
                input()
            endIndex = 9999999999
            for end in posEnds:
                if end in section:
                    if section.index(end) < endIndex:
                        endIndex = section.index(end)
            section = section[:endIndex]
            all_of_it = all_of_it.replace(section, '')
            for gene in negGenes:
                if gene in section:
                    negGenes.remove(gene)
                    posGenes.append(gene)

        vusEnds = ['About this test']

        while 'Additional Variant(s) of Uncertain Significance identified.' in all_of_it:
            section = all_of_it[all_of_it.index('Additional Variant(s) of Uncertain Significance identified.'):]
            if not any(end in section for end in vusEnds):
                print(all_of_it)
                print('no vus ends!')
                input()
            endIndex = 9999999999
            for end in vusEnds:
                if end in section:
                    if section.index(end) < endIndex:
                        endIndex = section.index(end)
            section = section[:endIndex]
            all_of_it = all_of_it.replace(section, '')
            for gene in negGenes:
                if gene in section:
                    negGenes.remove(gene)
                    vusGenes.append(gene)

        for gene in negGenes:
            geneList.append(gene)
            exonList.append('{}')
            variantList.append('')
            platformList.append('NGS')
            typeList.append('Mutation')
            callList.append('Negative, inferred')
            standardAppends()

        for gene in posGenes:
            geneList.append(gene)
            exonList.append('{}')
            variantList.append('')
            platformList.append('NGS')
            typeList.append('Mutation')
            callList.append('Positive')
            standardAppends()

        for gene in vusGenes:
            geneList.append(gene)
            exonList.append('{}')
            variantList.append('')
            platformList.append('NGS')
            typeList.append('Mutation')
            callList.append('VUS')
            standardAppends()
















if getGuardant:
    countFiles = True
    mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Guardant/'
    txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]
    fnum = 0
    brokens = []
    for txt in txts:
        if countFiles:
            print(fnum, ' of ', len(txts))
        fnum = fnum + 1
        file = mypath + txt
        file = open(file, mode='r')
        all_of_it = file.read()
        file.close()

        source = 'Guardant'
        filename = txt[:-20]
        fullText = all_of_it
        # Let's get MRN
        if 'Patient MRN:' in all_of_it:
            section = all_of_it[all_of_it.index('Patient MRN:') + len('Patient MRN:'):]
            section = section[:section.index('|')]
            mrn = section.strip()
        else:
            mrn = ''
        docId = all_of_it.split('\n')[0][all_of_it.split('\n')[0].index('(')+1:all_of_it.split('\n')[0].index(')')]
        datasource = 'pdf'
        #####
        # First, name
        #####
        testNames = ['Guardant360']
        if not any(tn in all_of_it for tn in testNames):
            print(all_of_it)
            input()
        else:
            for tn in testNames:
                if tn in all_of_it:
                    testType = tn

        split = all_of_it.split('\n')
        section = split[0]
        section = section[:section.index('(')].strip()
        firstName = section[section.index(', ')+ 2:]
        rest = section[:section.index(',')]
        if len(rest.split()) == 1:
            lastName = rest.strip()
            middleName = ''
            srJr = ''
        elif len(rest.split()) == 2:
            if rest.split()[-1].lower() in ['jr', 'sr'] or rest.split()[-1].lower().replace('i', '') == '':
                lastName = rest.split()[0]
                srJr = rest.split()[1]
                middleName = ''
            else:
                lastName = rest.split()[1]
                middleName = rest.split()[0]
                middleName = ''
        else:
            print(rest)
            input()

        ###
        # Now DOB
        ###
        if 'DOB:' in all_of_it:
            section = all_of_it[all_of_it.index('DOB:') + len('DOB:'):]
            section = section[:section.index('|')]
            section = section.strip()
            birthdate = section
        else:
            print(all_of_it)
            print('NO DOB')

        ###
        # Now Diagnosis
        ###
        if 'Diagnosis:' in all_of_it:
            section = all_of_it[all_of_it.index('Diagnosis:') + len('Diagnosis:'):]
            section = section[:section.index('|')]
            section = section.strip()
            if section == '':
                section = 'Not Given'
            diagnosis = section
        else:
            print(all_of_it)
            print('no diagnosis!')
            input()


        ###
        # Primary is not given
        ###
        primary = ''

        ###
        # Now specimen type
        ###
        if 'Specimen:' in all_of_it:
            section = all_of_it[all_of_it.index('Specimen:') + len('Specimen:'):]
            section = section[:section.index('|')]
            section = section.strip()
            sectionSplit = section.split()
            word = ''
            wordBit = 0
            while not sectionSplit[wordBit].replace(',','').isnumeric() and not sectionSplit[wordBit].endswith(',') and not sectionSplit[wordBit].endswith(':'):
                wordBit = wordBit + 1
            word = sectionSplit[wordBit]
            section = section[:section.index(word)]
            specimenSite = section.strip()
        else:
            print(all_of_it)
            print('no specimen!')
            input()

        ####
        # We'll infer the type from the location
        ###

        if specimenSite in ['Blood']:
            specimenType = 'Liquid'

        else:
            print(specimenSite)
            print('unknown specimen type!')
            input()

        ####
        # Now the date
        ####

        if 'Report Date:' in all_of_it:
            section = all_of_it[all_of_it.index('Report Date: '):]
            section = section[:section.index('\n')]
            section = section.split()
            section = section[2]

            received = section
            dateType = 'Report Date'

        else:
            print(all_of_it)
            print('No report date!')
            input()

        if 'Collection Date:' in all_of_it:
            section = all_of_it[all_of_it.index('Collection Date: ') + len('Collection Date: '):]
            section = section.split()
            ordered = section[0]

        negGeneList = []
        negExonList = []
        negPlatformList = []
        negTypeList = []
        negCallList = []

        posGeneList = []
        posExonList = []
        posPlatformList = []
        posTypeList = []
        posCallList = []

        # OK, now for the results
        if 'genes as indicated below.' not in all_of_it:
            if 'Status: CANCELLED' in all_of_it:
                geneList.append('Cancelled Test')
                platformList.append('Cancelled')
                exonList.append('{}')
                variantList.append('')
                typeList.append('Cancelled')
                callList.append('Cancelled')
                standardAppends()
            else:
                print(all_of_it)
                input()

        else:
            section = all_of_it[all_of_it.index('genes as indicated below.') + len('genes as indicated below.'):]
            endStrings = ['Guardant360 reports', 'About the Test']
            endPos = 9999999999
            if not any(end in section for end in endStrings):
                print(all_of_it)
                print('weird end!')
                input()
            for end in endStrings:
                if end in section:
                    if section.index(end) < endPos:
                        endPos = section.index(end)
            section = section[:endPos]
            if 'single nucleotide variants and splice site mutations in all clinically relevant exons' not in all_of_it.lower():
                print('not snvs and splice sites in all!')
                input()
            testText = 'Genes Tested:\n' + section
            section = section.replace('\n', ' ')
            section = section.strip()
            while '  ' in section:
                section = section.replace('  ', ' ')
            section = section.replace(' #', '#').replace(' Ω', 'Ω').replace(' †', '†').replace(' ‡', '‡')
            section = section.split()
            for gene in section:
                listOfVariants = ['SNV', 'Splice Site Mutation']
                listOfTypes = ['Mutation', 'Mutation']
                if 'Ω' in gene:
                    listOfVariants.append('Indel')
                    listOfTypes.append('Mutation')
                if '#' in gene:
                    listOfVariants.append('Fusion')
                    listOfTypes.append('Fusion')
                if '‡' in gene:
                    listOfVariants.append('Promoter Region Alteration')
                    listOfTypes.append('Mutation')
                if '†' in gene:
                    listOfVariants.append('Amplification')
                    listOfTypes.append('CNA')
                wholeGene = gene
                for y in range(0, len(listOfVariants)):
                    negGeneList.append(gene.replace('#', '').replace('Ω', '').replace('†', '').replace('‡', '').replace('&', '').replace('§', ''))
                    negExonList.append('')
                    negPlatformList.append('NGS')
                    negCallList.append('Inferred Negative - ' + listOfVariants[y])
                    negTypeList.append(listOfTypes[y])

            # Now pull out the positives
            if 'Alteration % cfDNA or Amp' in all_of_it:
                section = all_of_it[all_of_it.index('Alteration % cfDNA or Amp')+ len('Alteration % cfDNA or Amp'):]
                section = section[:section.index('The table above')].replace('§', '')

                # This means that there's a page break in the results.
                while 'a more detailed' in section.lower():
                    sectionPart1 = section.lower()[:section.lower().index('a more detailed')]
                    sectionPart2 = section[section.index('Alteration % cfDNA or Amp') + len('Alteration % cfDNA or Amp'):]
                    section = sectionPart1 + sectionPart2
                    if '\n\n' in section: section = section.replace('\n\n', '\n')
                    section = section.strip()
                testText = testText + '\n Test results: \n' + section
                section = section.split('\n')
                section = list(filter(None, section))

                for line in section:
                    adder = ''
                    line = line.strip()
                    line = line.split()
                    if not line[0].isupper():
                        if line[0] in['Plasma', 'Amplifications', 'Significance', 'Alteration', 'alteration', 'significance', 'amplifications']:
                            continue
                        elif line[0] in ['(Exon', '(exon']:
                            exon = line[1]
                            posExonList[-1] = line[1]
                            posTypeList[-1] = line[2].replace(')', '')
                            continue
                    wholeGene = line[0]
                    if 'promoter' in ' '.join(line).lower():
                        wholeGene = wholeGene + ' ‡'
                    elif 'fusion' in ' '.join(line).lower():
                        wholeGene = wholeGene + ' #'
                    elif 'amplification' in ' '.join(line).lower():
                        wholeGene = wholeGene + ' †'
                    elif 'ins' in ' '.join(line).lower() or 'del' in ' '.join(line).lower():
                        wholeGene = wholeGene + ' Ω'
                    elif 'splice' in ' '.join(line).lower():
                        wholeGene = wholeGene + '&'
                    posGeneList.append(wholeGene)
                    posExonList.append('')
                    posPlatformList.append('NGS')
                    if '%' in line[-1]:
                        line = line[:-1]
                    if line[1] in ['(HER2)', '(her2)']:
                        line[0:2] = [' '.join(line[0 : 2])]
                    if len(line) > 3:
                        if 'variant of unknown' in ' '.join(line).lower() or 'variant of uncertain' in ' '.join(line).lower():
                            adder = 'VUS'
                        elif line[1] in ['Amplification', 'amplification']:
                            adder = line[1]
                        else:
                            if '(+' not in ' '.join(line[3:]) and '%' not in ' '.join(line[3:]):
                                adder = ' '.join(line[3:])
                        posTypeList.append(adder)
                    elif len(line) > 1:
                        if line[1] in ['Amplification']:
                            posTypeList.append(line[1])
                        else:
                            posTypeList.append('Mutation')
                    if posTypeList[-1] in ['Synonymous Alteration', 'synonymous alteration']:
                        posCallList.append('Clinically Negative - SNV')
                    else:
                        if 'Ω' in wholeGene:
                            posCallList.append('Positive - indel')
                        elif '#' in wholeGene:
                            posCallList.append('Positive - fusion')
                        elif '‡' in wholeGene:
                            posCallList.append('Positive - promoter region')
                        elif '†' in wholeGene:
                            posCallList.append('Positive - amplification')
                        elif '&' in wholeGene:
                            posCallList.append('Positive - splice site alteration')
                        else:
                            posCallList.append('Positive - SNV')

            else:
                if "No tumor-related somatic alterations were detected in this patient's sample." in all_of_it:
                    pass
                else:
                    print(all_of_it)
                    print('weird negative test')
                    input()

            # To make sure we catch EVERYTHING, we split up all fusion genes into their component parts
            compList = []
            for x in range(0, len(posGeneList)):
                if '#' in posGeneList[x]:
                    fusion = posGeneList[x].split()[0].split('-')
                    compList.append(fusion[0] + ' #')
                    compList.append(fusion[1] + ' #')
                else:
                    compList.append(posGeneList[x])

            for x in range(0, len(posGeneList)):
                if len(posGeneList) != len(posTypeList):
                    print('\n'.join(section))
                    print('\n'.join(posGeneList))
                    input()
                geneList.append(posGeneList[x].replace('#', '').replace('Ω', '').replace('†', '').replace('‡', '').replace('§', '').replace('&', '').strip())
                exonList.append('{' + posExonList[x] + '}')
                variantList.append('')
                typeList.append(posTypeList[x])
                platformList.append(posPlatformList[x])
                callList.append(posCallList[x])
                standardAppends()

            # We do the join to get both genes in a fusion!
            for x in range(0, len(negGeneList)):
                # We'll add back in the signifiers. Just for comparison
                if negCallList[x] == 'Inferred Negative - Indels':
                    negGeneList[x] = negGeneList[x] + ' Ω'
                elif negCallList[x] == 'Inferred Negative - Fusions':
                    negGeneList[x] = negGeneList[x] + ' #'
                elif negCallList[x] == 'Inferred Negative - Promoter Region Alterations':
                    negGeneList[x] = negGeneList[x] + ' ‡'
                elif negCallList[x] == 'Inferred Negative - Amplifications':
                    negGeneList[x] = negGeneList[x] + ' †'
                elif negCallList[x] == 'Inferred Negative - Splice Site Mutations':
                    negGeneList[x] = negGeneList[x] + ' &'
                if negGeneList[x] not in compList:
                    if '-' not in negGeneList[x]:
                        geneList.append(negGeneList[x].replace('#', '').replace('Ω', '').replace('†', '').replace('‡', '').replace('§', '').replace('&', '').strip())
                        exonList.append('{' + negExonList[x] + '}')
                        variantList.append('')
                        typeList.append(negTypeList[x])
                        platformList.append(negPlatformList[x])
                        callList.append(negCallList[x])
                        standardAppends()
                    elif negGeneList[x].split('-')[1] + '-' + negGeneList[x].split('-')[0] not in compList:
                        geneList.append(negGeneList[x].replace('#', '').replace('Ω', '').replace('†', '').replace('‡', '').replace('§', '').replace('&', '').strip())
                        exonList.append('{' + negExonList[x] + '}')
                        variantList.append('')
                        typeList.append(negTypeList[x])
                        platformList.append(negPlatformList[x])
                        callList.append(negCallList[x])
                        standardAppends()

            # Finally, let's find MSI
            if 'Microsatellite status:' in all_of_it:
                section = all_of_it[all_of_it.index('Microsatellite status:') + len('Microsatellite status:'):]
                section = section[:section.index('\n')]
                section = section.strip()
                if 'MSI-High' not in section:
                    print(section)
                    print('not msi high')
                    input()
                else:
                    section = section[section.index('MSI-High') + len('MSI-High'):]
                    section = section.strip()
                    geneList.append('MSI-High')
                    exonList.append('{}')
                    variantList.append('')
                    platformList.append('NGS')
                    typeList.append('MSI')
                    callList.append(section)
                    standardAppends()

#for x in [geneList, exonList, platformList, typeList, callList, firstNames]:
#    print(len(x))

#for x in list(set(testTypes)):
#    print(x)
#input()

resultDF = pd.DataFrame(list(zip(geneList, exonList, platformList, typeList, callList, variantList, firstNames, middleNames, lastNames, jrSrs, testTexts, fullTexts,
                                 birthDates, mrns, diagnoses, primaries, specimenTypes, specimenSites, sources, testReceivedDates, testOrderedDates, testTypes, fileNames,
                                 docIds, datasourceTypes, accessionNumbers)),
                        columns=['Biomarker', 'Exons', 'Platform', 'Type', 'Call', 'Variant', 'First Name', 'Middle Name', 'Last Name', 'Jr/Sr', 'Test Text', 'Full Text',
                                 'Birthdate', 'MRN', 'Diagnosis', 'Primary Site', 'Specimen Type', 'Specimen Site', 'Source', 'Test Reported Date', 'Test Ordered Date', 'Test Type', 'Filename',
                                 'reportid', 'datasourcetype', 'Accession #'])

resultDF = resultDF.drop_duplicates()
resultDF = resultDF.sort_values(by=['reportid', 'Call'], ascending=False)
resultDF = resultDF.reset_index()

resultDF.to_csv("/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Results.csv", index=False)

allFiles = list(set(fileNames))
randomReports = random.sample(allFiles, 1)
sampleFiles = resultDF[resultDF['Filename'].isin(randomReports)]

# Here, we're going to get a sample by every test type
testTypes = list(set(resultDF['Test Type']))
listOfRandomsByType = []

for tt in testTypes:
    testTypeSamp = resultDF.loc[resultDF['Test Type'] == tt]
    allFiles = list(set(testTypeSamp['Filename']))
    if len(allFiles) > 77:
        numberOf = 77
    else:
        numberOf = len(allFiles)
    randomReports = random.sample(allFiles, numberOf)
    randomRes = resultDF[resultDF['Filename'].isin(randomReports)]
    listOfRandomsByType.append(randomRes)

sampledByType = pd.concat(listOfRandomsByType)

sampledByType.to_csv(sampleName, index=False)

zipObj = ZipFile(zipName, 'w')

for x in randomReports:
    file = mypath + x + '.pdf'
    arcname = '/' + x + '.pdf'
    zipObj.write(file, arcname)
zipObj.close

#for index, row in resultDF.iterrows():
#    if '0605a958-2686-4499-8c28-dc223dde3ab0' in row['Filename']:
#        print(row['Biomarker'], ' - ', row['Call'], ' - ', row['Type'])