def her2ProteinAssay(lower, spacelower, aberrentTests, aberrentReasons):
    print("her2/ new protein assay")
    print(lower)
    testStarts = []
    testEnds = []
    testType = 'her2/neu protein assay (ihc)'
    testTech = 'ihc'
    opener = re.finditer('her2/ neu protein assay \(ihc\)', lower)
    for start in opener:
        testStart = start.start()
        fullTest = lower[testStart:]
        fullTestEnd = re.search('pathologist\|', fullTest)
        testStarts.append(testStart)
        try:
            testEnds.append(testStart + fullTestEnd.start())
        except Exception as e:
            testEnds.append(testStart + len(fullTest))
            aberrentTests.append(spacelower)
            lower = lower + "ABERRENT"
            aberrentReasons.append('pending')
            reportedDate = 'pending'
            continue
        try:
            fullTest = fullTest[:fullTestEnd.start() + len('pathologist')]
        except Exception as e:
            aberrentTests.append(spacelower)
            lower = lower + "ABERRENT"
            aberrentReasons.append('no pathologist')
            continue
        if 'date ordered:' in fullTest:
            orderedDate = re.search('date ordered: ', fullTest)
            orderedDateEnd = re.search('date reported: ', fullTest)
            orderedDate = fullTest[orderedDate.start() + len("date ordered: "): orderedDateEnd.start()].strip()
            reportedDate = re.search('date reported: ', fullTest)
            try:
                reportedDateEnd = re.search('\|', fullTest[reportedDate.start():])
            except Exception as e:
                aberrentTests.append(spacelower)
                lower = lower + "ABERRENT"
                aberrentReasons.append('pending')
                reportedDate = 'pending'
                continue
            try:
                reportedDate = fullTest[reportedDate.start() + len("date reported: "): reportedDate.start() + reportedDateEnd.start()].strip()
            except Exception as e:
                aberrentTests.append(spacelower)
                lower = lower + "ABERRENT"
                aberrentReasons.append('pending')
                reportedDate = 'pending'
                continue
            if 'pending' in reportedDate:
                aberrentTests.append(spacelower)
                lower = lower + "ABERRENT"
                aberrentReasons.append('pending')
                reportedDate = 'pending'
                continue
            pathologist = re.search('out\*\*\*\|', fullTest)
            pathologist = fullTest[pathologist.start() + len('out***|'):].strip()

        else:
            orderedDate = ''
            reportedDate = ''
        if 'pending' in reportedDate:
            reportedDate = 'pending'
        if reportedDate.strip() == 'pending':
            aberrentTests.append(spacelower)
            lower = lower + "ABERRENT"
            aberrentReasons.append('pending')
            continue
        # Now let's find all the samples:
        samples = re.finditer('\|[a-z]\.\s', fullTest)
        for sample in samples:
            sampleText = fullTest[sample.end():]
            try:
                sampleEnd = sampleText.index(': ')
            except Exception as e:
                aberrentTests.append(fullTest)
                lower = lower + "ABERRENT"
                continue
            # We'll pull out the location of the sample here
            sampleLocation = sampleText[:sampleEnd]
            sampleText = sampleText[sampleEnd + 2:]
            # Now we separate the two types!
            if 'ki-67' in sampleText:
                sampleTextStart = sampleText.index('mib1')
                sampleTextEnd = sampleText.index('|||')
                sampleText = sampleText[sampleTextStart:sampleTextEnd]
                sampleText = sampleText.replace('|', ' ')
            else:
                try:
                    sampleTextStart = sampleText.index('interpretation: ')
                except Exception as e:
                    sampleTextStart = 0
                try:
                    sampleTextEnd = sampleText.index('results: ')
                except Exception as e:
                    if 'protein.' in sampleText:
                        sampleTextEnd = sampleText.index('protein.') + len('protein.')
                    else:
                        print(fullTest)
                        aberrentTests.append(fullTest)
                        lower = lower + "ABERRENT"
                        continue
                sampleText = sampleText[sampleTextStart:sampleTextEnd]
                sampleText = sampleText.replace('|', ' ')
            linesOfTest = sampleText.split('|')
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
                # input()
                for index, row in results.iterrows():
                    bioResult = ', '.join(row['Biomarker'])
                    conResult = ', '.join(row['Concept'])
                    numResult = ', '.join(row['Numeric'])
                    qualResult = ', '.join(row['Qualifier'])
                    # one possible row is a blank biomarker with intensity and a qualifier - those are associated with an ER or a PR
                    if 'intensity' in conResult:
                        intensityList.append(conResult)
                    if '% tumor cells' in numResult:
                        numResult = numResult[:numResult.index('tumor cells')] + numResult[numResult.index('tumor cells') + len('tumor cells'):]
                        percentageTumorCellList.append(numResult)
                    if 'immunostain' in conResult:
                        testMethodList.append('immunostain')
                    if 'ki67' in bioResult:
                        biomarkerNameList.append('KI-67')
                    if 'mib1' in bioResult:
                        cloneList.append('mib1')
                    if 'overexpression' in conResult:
                        overexpressionList.append(qualResult)
                        overexpressionValueList.append(numResult)
                        biomarkerNameList.append(bioResult)
                    alterationStatusList.append(qualResult)

    while len(firstNameList) < find_max_list(allList):
        standardAppends(firstName, middleName, lastName, MRN, dob, accession, testType, sampleLocation, pathologist, orderedDate, reportedDate, fullTest)
    squareUp()
    # Now we're going to snip all those tests out of the overall report!
    sampleLocation = ''
    testStarts.reverse()
    testEnds.reverse()
    for h in range(0, len(testStarts)):
        lower = lower[:testStarts[h]] + lower[testEnds[h]:]