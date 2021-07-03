import pandas as pd
import os
from os import listdir
from os.path import isfile, join
from collections import Counter
# For regex
import re
from MetaMapForLots import metamapstringoutput
from collections import Counter

# Turn this on to display the gene lists as they come
displayLists = False

# Turn this on to display patient info
displayInfo = False

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)


# This is for getting each of the three
getCaris = False
getFMI = False
getTempus = True

#######
# CARIS
#######

if getCaris:
    # Now beginning the sorting out!
    mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/Caris/'
    txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]

    documentNameList = []
    caseNumberList = []
    biomarkerNameList = []
    biomarkerTypeList = []
    siteList = []
    weirdTests = []

    sitesByTest = []

    # So let's roll - crack open these cold ones with the boys
    for txt in txts:
        # Path of the pdf
        TXT_file = mypath + txt
        with open(TXT_file, 'r') as file:
            data = file.read()

        # First, we'll pull some standard info
        if 'Case Number:' in data:
            case = data[data.index('Case Number: ') + len('Case Number: '):]
            case = case[:case.index('Specimen')].strip()
            if '\n' in case:
                case = case[:case.index('\n')]
        else:
            if data.replace(' ','').replace('\n','') == '':
                continue
            case = data[data.index('Specimen #: ') + len('Specimen #: '):]
            case = case[:case.index('\n')].strip()

        # Annoyingly, we have to separate out the site from the name, with no division.
        # The idea is, caris always goes "Lung, lower lobe Brian Anderson" so capital,
        # Then lower-case words, followed by an upper-case name.
        if 'Primary Tumor Site:' not in data:
            if 'CancerNext-Expanded' not in data:
                site = ''
            else:
                site = 'CancerNext sample'
        else:
            site = data[data.index('Primary Tumor Site: ') + len('Primary Tumor Site: '):]
            site = site[:site.index('\n')]
            site = site.split()
            realSite = site[0]
            site = site[1:]
            for s in site:
                if s[0].islower():
                    realSite = realSite + ' ' + s
                elif s.isupper():
                    realSite = realSite + ' ' + s
                else:
                    break
        sitesByTest.append(realSite)

        # We're going to loop through the document, excising any gene lists. We'll find them by their headers.
        noMoreLists = False
        startStrings = ['COMPLETE LIST OF GENES TESTED WITH INDETERMINATE RESULTS BY TUMOR DNA SEQUENCING',
                        'COMPLETE LIST OF GENES TESTED WITH INDETERMINATE RESULTS',
                        'GENES TESTED WITH NO MUTATIONS DETECTED BY TUMOR DNA SEQUENCING ',
                        'GENES TESTED BY TUMOR DNA SEQUENCING WITH INDETERMINATE RESULTS',
                        'GENES TESTED WITH NO MUTATIONS DETECTED',
                        'GENES TESTED WITH NO AMPLIFICATION DETECTED',
                        'GENES TESTED WITH UNEVALUATED AMPLIFICATION DETECTED',
                        'GENES TESTED WITH NO GENE FUSION OR TRANSCRIPT VARIANT DETECTED',
                        'GENES WITH INDETERMINATE CNA RESULTS',
                        'Genes Tested Without Alterations',
                        'GENES TESTED WITH NO RNA ALTERATIONS BY NGS',
                        'Genes Analyzed (77 total):',
                        'GENES TESTED WITH INDETERMINATE GENE FUSION OR TRANSCRIPT VARIANT RESULTS',
                        'GENES TESTED WITH NO MU IONS DETECTED',
                        'Other Findings',
                        'GENES TESTED WITH INDETERMINATE RESULTS BY TUMOR DNA SEQUENCING',
                        'GENES TESTED WITH INDETERMINATE FUSION OR VARIANT TRANSCRIPT RESULTS BY NGS'
                        ]

        endStrings = ['Genes in', 'CNA Methods', 'For Next-Generation', 'The CNV', 'Gene Fusion Methods', 'CNV Methods', 'Comments', 'Electronic Signature', 'Additional',
                      'PATIENT:', 'The CNA', 'GENES TESTED', 'For a', 'COMPLETE LIST', 'The mutations', 'Order Summary:']

        typeStrings = ['Genes - indeterminate result', 'Genes - indeterminate result', 'Genes - no mutation', 'Genes - indeterminate result', 'Genes - no mutation', 'Genes - no amplification',
                       'Genes - unevaluated amplifcation', 'Genes - no gene fusion or transcript variant', 'Genes - indeterminate CNA', 'Genes - no alteration', 'Genes - no RNA alteration',
                       'Genes', 'Genes - indeterminate fusion or transcript variant', 'Genes - no mutation', 'indeterminate due to insufficient MRNA sequencing reads', 'Genes - indeterminate',
                       'Genes - indeterminate fusion or transcript variant']

        # We loop through, finding the first string. If we find NO strings, we're done.
        foundAny = False
        while not noMoreLists:
            didntFindStart = True
            firstStart = 10000000000
            startText = ''
            firstEnd = 10000000000
            for x in range(0, len(startStrings)):
                if startStrings[x] in data.replace('*', ''):
                    didntFindStart = False
                    foundAny = True
                    if data.index(startStrings[x]) < firstStart:
                        firstStart = data.index(startStrings[x])
                        startText = startStrings[x]
                        type = typeStrings[x]
            if didntFindStart:
                if displayLists:
                    print("All done with this one!")
                    print('--------------------------------------------------')
                noMoreLists = True
                if not foundAny:
                    if displayLists:
                        print("NO STRINGS!")
                        print(txt)
                    if 'Appendix 1 of' not in data:
                        weirdTests.append(data)
                        pass
                    else:
                        if displayLists:
                            weirdTests.append(data[data.index('Appendix 1 of '):])

            else:
                listBit = data[firstStart:]
                geneBit = data[firstStart + len(startText):]
                for y in endStrings:
                    if y in geneBit:
                        if geneBit.index(y) < firstEnd:
                            firstEnd = geneBit.index(y)
                listBit = listBit[:firstEnd + len(startText)]
                geneBit = geneBit[:firstEnd]
                geneBit = geneBit.replace('\n', ' ').strip()
                while geneBit.endswith(('"', '*')):
                    geneBit = geneBit[:-1]
                while '  ' in geneBit:
                    geneBit = geneBit.replace('  ', ' ')
                # Now geneBit is just a space-separated list of genes.
                # Parenthases in these lists is like CD274 (PD-L1), where we want to merge those two strings
                # Tert § means 'tert promoter region not tested'
                # Fusion not detected -and- Variant Transcript Not Detected are signs to incorporate
                if displayLists:
                    print(geneBit)
                    print(txt)
                    print(type)
                    print(startText)
                    print('--------------------------------------------------')
                    #print(listBit)
                    #print("HERE!")
                geneBit = geneBit.split(' ')
                for gene in geneBit:
                    if gene.startswith('('):
                        biomarkerNameList[-1] = biomarkerNameList[-1] + ' ' + gene
                        continue
                    if gene == 'Fusion':
                        type = 'Fusion not detected'
                        continue
                    if gene == 'Variant':
                        type = 'Variant Transcript not detected'
                        continue
                    if gene in ['not', 'detected', 'Not', 'Detected', 'Transcript'] and type in ['Fusion not detected', 'Variant Transcript not detected']:
                        continue
                    documentNameList.append(txt)
                    caseNumberList.append(case)
                    biomarkerNameList.append(gene)
                    biomarkerTypeList.append(type)
                    siteList.append(realSite)
                data = data.replace(listBit, '')


    resultsFrame = pd.DataFrame(list(zip(documentNameList, caseNumberList, siteList, biomarkerNameList, biomarkerTypeList)),
                                   columns=['document name', 'case number', 'primary site', 'biomarker', 'type'])

    resultsFrame.to_csv('/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/CarisResults.csv', index=False)

    weirdFrame = pd.DataFrame(list(zip(weirdTests)), columns=['text'])

    weirdFrame.to_csv('/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/CarisAberrantResults.csv', index=False)

    for entry, value in Counter(siteList).items():
        print(entry, ': ', value)


#######
# Tempus
#######
