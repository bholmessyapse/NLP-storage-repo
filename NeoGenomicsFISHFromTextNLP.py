import pandas as pd
# For regex
import re
import math
from MetaMapForLots import metamapstringoutput
from metamapLoader import metamapStarter
from metamapLoader import metamapCloser
from os import listdir
from os.path import isfile, join
import pandas as pd
import random
from zipfile import ZipFile

countFiles = True

# Start up metamap - we'll close after we're done!
metamapStarter()

fileNames = []
testTypes = []
mrns = []
firstNames = []
middleNames = []
lastNames = []
srsJrs = []
accessionNumbers = []
dobs = []
specimenTypes = []
specimenSites = []
diagnoses = []
datesRecieved = []
dateTypes = []
finalResults = []
finalProbes = []
biomarkerList = []
conceptList = []
numericList = []
qualifierList = []

mypath = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/NeoFish/'
txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]
fnum = 0
brokens = []
for txt in txts:
    if countFiles:
        print(fnum, ' of ', len(txts))
    if fnum > 50:
        break
    fnum = fnum + 1
    file = mypath + txt
    file = open(file, mode='r')
    all_of_it = file.read()
    file.close()
    # I'm assuming this is a typo, pending Dr. Berry
    all_of_it = all_of_it.replace('PGFRA', 'PDGFRA').replace('PDGFRa', 'PDGFRA').replace('PDGFRb', 'PDGFRB').replace('CEN 17', 'CEN17')

    source = 'Neogenomics'
    filename = txt.replace('_out_text_SAMPLE.txt', '.pdf')

    # Test Type should be first two lines
    testType = ' '.join(all_of_it.split('\n')[0:2]).strip()

    # Let's get MRN
    if 'MRN:' in all_of_it:
        section = all_of_it[all_of_it.index('MRN:') + len('MRN:'):]
        section = section[1:]
        if section.index('\n') < section.index(' '):
            section = section[:section.index('\n')]
        else:
            section = section[:section.index(' ')]
        mrn = section.strip()
    if not mrn.isnumeric():
        mrn = 'Not Given'

    # And accession
    section = all_of_it[all_of_it.index('CaseNo:'):]
    section = section[:section.index('\n')]
    section = section[section.index('/ ') + 2:]
    accession = section

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
            if lastName.split()[1].lower().replace('.', '') in ['jr', 'sr'] or lastName.split()[1].replace('I', '').replace('lll', '') == '':
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
        if 'M.D' in specimenSite or 'Dr.' in specimenSite or ' DO' in specimenSite or ' MD' in specimenSite or ' Md' in specimenSite or 'D.O.' in specimenSite:
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
            if section.endswith(',') or all_of_it[all_of_it.index(section) + len(section) + 1: all_of_it.index(section) + len(section) + 10].isupper():
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

        # Now, for results

        # Results are all the results from the interp section
        # Probes are all the probes from the Probe Set Details section
        # Matched Probes matches the probe with the results
        results = []
        probes = []
        matchedProbes = []
        gotResults = False
        # There are two major types: tests with "Interpretation:" and tests without. Let's do interpretation first!
        if 'Interpretation:' in all_of_it:
            gotResults = True
            interpSection = all_of_it[all_of_it.index('Interpretation:'):]
            interpSection = interpSection.split('\n')
            lsIndex = 1
            # We keep going until we get a long paragraph. I HOPE this always works!
            while len(interpSection[lsIndex]) < 50 and 'Number of Observers' not in interpSection[lsIndex] and 'The FISH study' not in interpSection[lsIndex]:
                result = interpSection[lsIndex]
                while '  ' in result:
                    result = result.replace('  ', ' ')
                if '):' in result and '): ' not in result:
                    result = result.replace('):', '): ')
                # Gains(5, 9, 15) should be split into three
                if 'Gains(' in result:
                    if '):' in result:
                        endResult = result[result.index('):') + 2:]
                        endResult = endResult.strip()
                        middleResult = result[result.index('(')+1:]
                        middleResult = middleResult[:middleResult.index(')')]
                        for res in middleResult.split(','):
                            results.append('Gain(' + res.strip() + '): ' + endResult.strip())
                else:
                    results.append(result.replace('CEN 17', 'CEN17'))
                lsIndex = lsIndex + 1
            # Non-standard interp section:
            if results == []:
                interpSection = all_of_it[all_of_it.index('Interpretation:') + len('Interpretation:\n'):]
                interpSection = interpSection[:interpSection.index('.\n')].replace('\n', ' ')
                if ', however, ' in interpSection:
                    interpSection = interpSection.split(', however, ')
                if 'probes' in interpSection:
                    if 'Normal results' in interpSection:
                        interpSection = interpSection[interpSection.index('for the ') + len('for the '):interpSection.index('probes')].replace('and', '')
                        interpSectionSp = interpSection.split(', ')
                        interpSection = []
                        for i in interpSectionSp:
                            interpSection.append('probe ' + i.strip() + ': normal results')
                if 'The average (mean)' in interpSection:
                    interpSection = interpSection.replace('The average (mean)', '*').replace('CEN 17', 'CEN17')
                    interpSection = interpSection.replace('Ratio', '*')
                    interpSection = interpSection.split('*')
                    interpSection = interpSection[1:]
                    for i in range(0, len(interpSection)):
                        if 'divided by' not in interpSection[i]:
                            interpSection[i] = 'average ' + interpSection[i][interpSection[i].index(', ') + 2:]
                        else:
                            if 'HER2' in interpSection[i] and 'CEN17' in interpSection[i]:
                                endString = 'Along with'
                                if 'Along with' not in interpSection[i]:
                                    endString = 'Reference Ranges:'
                                    if 'Reference Ranges:' not in interpSection[i]:
                                        endString = 'none'
                                if endString != 'none':
                                    interpSection[i] = interpSection[i][:interpSection[i].index(endString)]
                                    interpSection[i] = 'ratio of HER2 to Cen17 ' + interpSection[i][interpSection[i].index('='):]

                if isinstance(interpSection, list):
                    for bt in interpSection:
                        results.append(bt)


        elif '\nResults: ' in all_of_it:
            allSplit = all_of_it.split('\n')
            linInd = 0
            while 'Results: ' not in allSplit[linInd]:
                linInd = linInd + 1
            results.append(allSplit[linInd])
            gotResults = True

        hasNuc = False
        if 'Probe Set Detail:' in all_of_it:
            hasNuc = True
            section = all_of_it[all_of_it.index('Probe Set Detail:'):]
            if 'Assessment of' in section:
                section = section[:section.index('Assessment of')]
            section = section.split('\n')
            lsIndex = 1
            # First we try to catch 'nuc ish' probes. Most useful!
            if 'nuc ish' in ' '.join(section):
                sectionEnders = ['Comments:', 'Nuclei Scored:']
                while not any(x in section[lsIndex] for x in sectionEnders):
                    # These tokens indicate page breaks
                    if any(y in section[lsIndex] for y in ['©', 'Patient', 'CaseNo:']):
                        lsIndex = lsIndex + 1
                        continue
                    if 'nuc ish' in section[lsIndex]:
                        probes.append(section[lsIndex])
                    elif len(probes) > 0:
                        if probes[-1].endswith(','):
                            probes[-1] = probes[-1] + section[lsIndex]
                    #else:
                    #    print(section[lsIndex])
                    #    print(probes)
                    #    print(section)
                    #    input()
                    lsIndex = lsIndex + 1
            # Catching probes used elsewhere
            if 'was performed and reported separately' in all_of_it:
                allSplit = all_of_it.split('\n')
                for line in allSplit:
                    if 'was performed and reported separately' in line:
                        probes.append(line)

            # These might be first-line probes, too
            if probes == []:
                lsIndex = 1
                sectionEnders = ['Comments:', 'Nuclei Scored:']
                while not any(x in section[lsIndex] for x in sectionEnders) and lsIndex < len(section)-1:
                    line = section[lsIndex]
                    stop = False
                    if line.split()[0].endswith(':'):
                        probes.append(line.split()[0][:-1])
                        stop = True
                    if len(line.split()) > 1 and not stop:
                        if line.split()[1].endswith(':'):
                            probes.append(line.split()[0] + ' ' + line.split()[1][:-1])
                            stop = True
                    if len(line.split()) > 2 and not stop:
                        if line.split()[2].endswith(':'):
                            probes.append(line.split()[0] + ' ' + line.split()[1] + ' ' + line.split()[2][:-1])
                    if len(line.split()) > 3 and not stop:
                        if line.split()[3].endswith(':'):
                            probes.append(line.split()[0] + ' ' + line.split()[1] + ' ' + line.split()[2] + ' ' + line.split()[3][:-1])


                    lsIndex = lsIndex + 1

            if probes == []:
                print(all_of_it)
                input()

        # Next up - see if you can get the probe names from the scoring method!
        # We'll maybe add in later
        elif 'Probe set Scoring method' in all_of_it:
            allSplit = all_of_it.split('\n')
            linInd = 0
            while 'Probe set Scoring method' not in allSplit[linInd]:
                linInd = linInd + 1
            linInd = linInd + 1
            while any(y in allSplit[linInd] for y in ['©', 'Patient', 'CaseNo:']):
                linInd = linInd + 1
            line = allSplit[linInd]
            endBits = ['Manual', 'Computer', 'Not Scored']
            if any(x in line for x in endBits):
                for y in endBits:
                    if y in line:
                        line = line[:line.index(y)]
            line = line.split(',')
            for l in line:
                if l not in ['HER2 Breast']:
                    probes.append(l.strip())
                    hasNuc = True

        if hasNuc:
            if len(results) == 1 and len(probes) == 1:
                matchedProbes.append(probes[0])
            elif 'Results:' in ' '.join(results):
                result = results[0]
                results = []
                if 'See Below' in result:
                    resultSection = all_of_it[all_of_it.index('Probe Set Detail:\n') + len('Probe Set Detail:\n'):]
                    resultSection = resultSection[:resultSection.index('Nuclei')]
                    if 'Comments' in resultSection:
                        resultSection = resultSection[:resultSection.index('Comments')]
                    resultSection = resultSection.split('.\n')
                    for rs in resultSection:
                        if ': ' not in rs:
                            continue
                        backupProbe = rs[:rs.index(':')]
                        rs = rs[rs.index(': ') + 2:]
                        rs = rs.replace('\n', ' ')
                        if 'following a' in rs:
                            rs = rs[:rs.index('following a')]
                        if 'article:' not in rs and 'et al.' not in rs:
                            results.append(rs)
                            probeType = ''
                            for word in rs.split():
                                if word.isupper() and word not in ['A', 'NEGATIVE']:
                                    probeType = word
                                    if '/' in probeType:
                                        probeType = probeType[:probeType.index('/')]
                            foundProbe = False
                            for prob in probes:
                                if probeType in prob:
                                    matchedProbes.append(prob)
                                    foundProbe = True
                            if not foundProbe:
                                matchedProbes.append(backupProbe)

                else:
                    for pr in probes:
                        results.append(result)
                        matchedProbes.append(pr)


            else:
                for result in results:
                    geneResult = result.split()[0]
                    if geneResult.endswith(':'):
                        geneResult = geneResult[:-1]
                    if 'Panel' in geneResult:
                        continue
                    if 't(' in geneResult:
                        # Sometimes we mis-write t(11;14) like t(11:14)
                        geneResult = geneResult.replace(':', ';')
                        if '/' in geneResult:
                            geneResult = geneResult.split('/')
                        else:
                            geneResult = [geneResult]

                    elif geneResult in ['Monosomy', 'Trisomy', 'Tetrasomy', 'Average', 'Co-deletion']:
                        geneResult = result.split()[1]
                        if geneResult.endswith(':'):
                            geneResult = geneResult[:-1]
                        geneResult = [geneResult]

                    elif geneResult in ['POSITIVE', 'NEGATIVE', 'EQUIVOCAL']:
                        geneResult = [' '.join(results)]

                    elif any(x in geneResult for x in ['Del', 'inv', 'Dup', 'Gain']):
                        geneResult = [geneResult]

                    elif not geneResult[0:3].isupper() and not geneResult.replace('p', '').replace('q', '').isnumeric() and not geneResult in ['A']:
                        if geneResult == 'probe':
                            geneResult = result.split()[1]
                            if ';' in geneResult:
                                geneResult = geneResult.split(';')[0]
                            if geneResult.endswith(':'):
                                geneResult = geneResult[:-1]
                        elif any(x.isupper() for x in result.split()):
                            for y in result.split():
                                if y.isupper() and not y in ['A', 'DETECTED', 'NOT', 'FISH'] and '=' not in y:
                                    geneResult = y
                        elif 'Normal results seen for the' in result and 'probe set' in result:
                            print(probes)
                            input()
                            results = []
                            for item in probes:
                                results.append('Normal Results for ' + item)
                                matchedProbes.append(item)

                    else:
                        while '(' in geneResult:
                            geneResult = geneResult[:geneResult.index('(')] + geneResult[geneResult.index(')')+1:]
                        if '/' in geneResult or '(' in geneResult:
                            geneResult = geneResult.split('/')
                        else:
                            geneResult = [geneResult]

                    totalMatch = False
                    matchInd = 0
                    while not totalMatch:
                        unitMatch = True
                        for bit in geneResult:
                            # We want the locations masked by these prefixes
                            bit = bit.replace('inv(', '').replace('Del(', '').replace('t(', '').replace(')','').replace('Dup(', '').replace('Grain(', '')
                            # Weird casting here
                            bit = bit.replace('ALK1', 'ALK')
                            # Just want the chrosome
                            if bit.split()[0] in ['POSITIVE', 'NEGATIVE', 'EQUIVOCAL']:
                                bit = bit.split()[-1]
                            # t(3;3) should just be (3) for 3p or 3q
                            if ';' in bit:
                                if bit.split(';')[0] == bit.split(';')[1]:
                                    bit = bit.split(';')[0]
                            if 'p' in bit and bit.replace('p', '').isnumeric():
                                bit = bit.split('p')[0]
                            if 'q' in bit and bit.replace('q', '').isnumeric():
                                bit = bit.split('q')[0]
                            # If we still have a '(', it's a split like Del(17p)(TP53)
                            if bit.isnumeric():
                                # We need to cover "13q" "13p" "+13" "Chromosome 13" "Chromosomes 13 and 14" and "Chromosomes 14 & 13"
                                if bit + 'p' not in probes[matchInd] and bit + 'q' not in probes[matchInd] and '+' + bit not in probes[matchInd] and \
                                    'Chromosome ' + bit not in probes[matchInd] and 'Chromosomes ' + bit not in probes[matchInd] and '& ' + bit not in probes[matchInd]:
                                    unitMatch = False
                            # This is for stuff like Del(18p)(TP53)
                            elif '(' in bit:
                                bit = bit.split('(')
                                if bit[0] not in probes[matchInd] and bit[1] not in probes[matchInd]:
                                    unitMatch = False
                            # This is for stuff like Del(13q)/-13
                            elif '/' in bit:
                                bit = bit.split('/')
                                bit = bit[0].replace('p', '').replace('q', '').replace('-', '')
                                if bit + 'p' not in probes[matchInd] and bit + 'q' not in probes[matchInd] and '+' + bit not in probes[matchInd] and \
                                    'Chromosome ' + bit not in probes[matchInd] and 'Chromosomes ' + bit not in probes[matchInd] and '& ' + bit not in probes[matchInd]:
                                    unitMatch = False
                            else:
                                if bit not in probes[matchInd]:
                                    unitMatch = False
                        if unitMatch:
                            totalMatch = True
                            matchedProbes.append(probes[matchInd])
                        matchInd = matchInd + 1

                        if matchInd == len(probes) and not totalMatch:
                            totalMatch = True
                            matchedProbes.append('')
                            #print(all_of_it)
                            #print('FAILURE OF')
                            #print(bit)
                            #print(probes)
                            #print(probes[matchInd])
                            #input()

        else:
            #print(all_of_it)
            #input()
            for entry in results:
                matchedProbes.append('')

        if 'Normal results seen for the' in all_of_it and 'probe set' in all_of_it:
            if results == []:
                for item in probes:
                    results.append('Normal Results: ' + item)
                    if item.isnumeric():
                        if '+' + item in all_of_it:
                            matchedProbes.append('+' + item)
                        else:
                            print(item)
                            print(filename)
                            print('probe with plus not in!')
                            input()
                    else:
                        matchedProbes.append(item)
            else:
                print(results)
                print(matchedProbes)
                input()

        reserveWord = 'None'
        for i in range(0, len(results)):
            file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
            if '(See Below)' in results[i]:
                results[i] = results[i].replace('(See Below', '')
            if 'ProbeSet:' in results[i]:
                results[i] = results[i].replace('ProbeSet:', matchedProbes[i])
            toScan = results[i]
            if 'Del(' in toScan or 'inv(' in toScan or 'dup(' in toScan:
                if ')(' in toScan:
                    if 'Del(' in toScan:
                        toScan = toScan.replace(')(', ') Del(')
                    if 'inv(' in toScan:
                        toScan = toScan.replace(')(', ') inv(')
                    if 'dup(' in toScan:
                        toScan = toScan.replace(')(', ') dup(')
            if 'Results: ' in toScan and 'Normal Results: ' not in toScan:
                toScan = matchedProbes[i] + ' ' + toScan
            toScan = toScan.replace('Gain(', 'Gain of Chromosome ')
            toScan = toScan.replace(' Results show', ' . . Results show').replace(' Mean number', ' . . Mean number').replace(' and a ', ' and an ').replace('with average', '. . average').replace('mean', 'average')
            with open(file, 'w') as filetowrite:
                filetowrite.write(results[i])
            mmAnswer = metamapstringoutput()


            for index, row in mmAnswer.iterrows():
                if 'Normal Results: ' in toScan:
                    bioResult = toScan[toScan.index('Normal Results: ') + len('Normal Results: '):]
                    if bioResult.replace('+', '').isnumeric():
                        bioResult = 'Chromosome ' + bioResult
                    conResult = 'expression'
                    numResult = ''
                    qualResult = 'Normal'
                else:
                    bioResult = ', '.join(row['Biomarker'])
                    conResult = ', '.join(row['Concept'])
                    numResult = ', '.join(list(dict.fromkeys(row['Numeric'])))
                    qualResult = ', '.join(row['Qualifier'])
                biomarkerList.append(bioResult)
                conceptList.append(conResult)
                numericList.append(numResult)
                qualifierList.append(qualResult)
                fileNames.append(filename)
                testTypes.append(testType)
                mrns.append(mrn)
                firstNames.append(firstName)
                middleNames.append(middleName)
                lastNames.append(lastName)
                srsJrs.append(srJr)
                accessionNumbers.append(accession)
                dobs.append(birthdate)
                specimenTypes.append(specimenType)
                specimenSites.append(specimenSite)
                diagnoses.append(diagnosis)
                datesRecieved.append(received)
                dateTypes.append(dateType)
                finalResults.append(results[i])
                finalProbes.append(matchedProbes[i])

                for ix in [fileNames, testTypes, mrns, firstNames, middleNames, lastNames, srsJrs, accessionNumbers, dobs, specimenTypes, specimenSites, diagnoses, datesRecieved, dateTypes, finalResults, finalProbes, biomarkerList, conceptList, numericList, qualifierList]:
                    if len(ix) < len(fileNames):
                        print('PROBLEM WITH LEN!')
                        input()

resultDF = pd.DataFrame(list(zip(finalResults, finalProbes, biomarkerList, conceptList, numericList, qualifierList, testTypes, mrns, firstNames, middleNames, lastNames, srsJrs, accessionNumbers, dobs, specimenTypes, specimenSites, diagnoses, datesRecieved, dateTypes, fileNames)),
                        columns=['Result', 'Probe Used', 'Biomarker', 'Concept', 'Numeric', 'Qualifier', 'Test Type', 'MRN', 'First Name', 'Middle Name', 'Last Name', "Jr/Sr", 'Accession #', 'DOB', 'Specimen Type', 'Specimen Site',
                                 'Reason for Referral', 'Date Revieved', 'Date Type', 'File Name'])

resultDF = resultDF.drop_duplicates()
resultDF = resultDF.reset_index()

#resultDF.to_csv("/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/NeoFishResults.csv", index=False)

# Here, we're going to get a sample by every test type
sampleName = "/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/NeoFishResults.csv"
zipName = '/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/NeoFishSample.zip'

testTypes = list(set(resultDF['Test Type']))
listOfRandomsByType = []

allFiles = list(set(fileNames))
for tt in testTypes:
    testTypeSamp = resultDF.loc[resultDF['Test Type'] == tt]
    allFiles = list(set(testTypeSamp['File Name']))
    if len(allFiles) > 10:
        numberOf = 10
    else:
        numberOf = len(allFiles)
    randomReports = random.sample(allFiles, numberOf)
    randomRes = resultDF[resultDF['File Name'].isin(randomReports)]
    listOfRandomsByType.append(randomRes)

sampledByType = pd.concat(listOfRandomsByType)

sampledByType.to_csv(sampleName, index=False)

zipObj = ZipFile(zipName, 'w')

for x in list(set(sampledByType['File Name'])):
    file = mypath + x
    arcname = '/' + x
    zipObj.write(file, arcname)
zipObj.close

metamapCloser()