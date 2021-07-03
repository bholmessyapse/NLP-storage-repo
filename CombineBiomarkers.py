import pandas as pd
import numpy as np
import random
# For regex
import re
import copy
from collections import Counter
from uuid import uuid5, UUID

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', -1)

weirdBio = []
weirdCon = []
weirdNum = []
weirdQua = []
weirdText = []
weirdPatient = []

# These are the columns we need to send out, in order.
reportIdList, patientIdList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList, probeNumberCellsList, averageSignalList, signalRatioList, \
    alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionNumberList, testTextList, testNameList, platformList, sampleLocationList, \
    pathologistList, dateOrderedList, dateReportedList, copyNumberList, alleleFrequencyList, percentReadsList, immuneCellStainPresentList, strandOrientationList, clinicalSignificanceList, \
    allelicStateList, exonsList, proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList, tumorProportionScoreList, combinedPositiveScoreList, fullTextList, datasourcetypeList,\
    copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList, tumorMutationBurdenScoreList, tumorMutationBurdenUnitList, icdCodeList, ericaList, pricaList,\
    copyNumberRatioComparisonGeneList, copyNumberRatioComparisonGeneSignalList, sourcenameList, suborgList, geneList, proteinList, otherAnalyteList,\
    variantNameList = ([] for i in range(57))

# These are the temporary versions we use per report
tempreportIdList, temppatientIdList, tempcloneList, tempintensityList, temppercentTumorCellsList, tempallredScoreList, tempprobeList, tempprobeNumberCellsList, \
  tempaverageSignalList, tempsignalRatioList, tempalterationList, tempalterationStatusList, tempfirstNameList, tempmiddleNameList, templastNameList, tempmrnList, tempdobList, \
  tempaccessionNumberList, temptestTextList, temptestNameList, tempplatformList, tempsampleLocationList, temppathologistList, tempdateOrderedList, tempdateReportedList, tempcopyNumberList, \
  tempalleleFrequencyList, temppercentReadsList, tempimmuneCellStainPresentList, tempstrandOrientationList, tempclinicalSignificanceList, tempallelicStateList, tempexonsList, \
  tempproteinIdList, tempaminoAcidChangeList, tempcodingIdList, tempcodingChangeList, temptumorProportionScoreList, tempcombinedPositiveScoreList, tempfullTextList, tempdatasourcetypeList,\
  tempcopyNumberRatioList, templog2CopyNumberRatioList, tempcellFreeDnaPercentList, temptumorMutationBurdenScoreList, temptumorMutationBurdenUnitList, tempicdCodeList, tempericaList, \
  temppricaList, tempcopyNumberRatioComparisonGeneList, tempcopyNumberRatioComparisonGeneSignalList, tempsourcenameList, tempSuborgList,\
    tempgeneList, tempproteinList, tempotherAnalyteList, tempvariantNameList = ([] for j in range(57))

# It's also helpful to have a list of those lists, that we can iterate through.
allTempLists = [tempreportIdList, temppatientIdList, tempcloneList, tempintensityList, temppercentTumorCellsList, tempallredScoreList, tempprobeList,
                tempprobeNumberCellsList, tempaverageSignalList, tempsignalRatioList, tempalterationList, tempalterationStatusList, tempfirstNameList, tempmiddleNameList, templastNameList,
                tempmrnList, tempdobList, tempaccessionNumberList, temptestTextList, temptestNameList, temppercentReadsList, tempimmuneCellStainPresentList, tempstrandOrientationList,
                tempclinicalSignificanceList, tempallelicStateList, tempexonsList, tempproteinIdList, tempaminoAcidChangeList, tempcodingIdList, tempcodingChangeList,
                temptumorProportionScoreList, tempcombinedPositiveScoreList, tempalleleFrequencyList, tempcopyNumberRatioList, templog2CopyNumberRatioList, tempcellFreeDnaPercentList,
                temptumorMutationBurdenScoreList, temptumorMutationBurdenUnitList, tempicdCodeList, tempericaList, temppricaList, tempplatformList, tempsampleLocationList,
                temppathologistList, tempdateOrderedList, tempdateReportedList, tempcopyNumberList, tempfullTextList, tempdatasourcetypeList, tempcopyNumberRatioComparisonGeneList,
                tempcopyNumberRatioComparisonGeneSignalList, tempsourcenameList, tempSuborgList, tempgeneList, tempproteinList, tempotherAnalyteList, tempvariantNameList]

allLists = [reportIdList, patientIdList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList,
                probeNumberCellsList, averageSignalList, signalRatioList, alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList,
                mrnList, dobList, accessionNumberList, testTextList, testNameList, percentReadsList, immuneCellStainPresentList, strandOrientationList,
                clinicalSignificanceList, allelicStateList, exonsList, proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList,
                tumorProportionScoreList, combinedPositiveScoreList, alleleFrequencyList, copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList,
                tumorMutationBurdenScoreList, tumorMutationBurdenUnitList, icdCodeList, ericaList, pricaList, platformList, sampleLocationList,
                pathologistList, dateOrderedList, dateReportedList, copyNumberList, fullTextList, datasourcetypeList, copyNumberRatioComparisonGeneList,
                copyNumberRatioComparisonGeneSignalList, sourcenameList, suborgList, geneList, proteinList, otherAnalyteList, variantNameList]

# These rows are invariant between rows in a test, and should be added every time we add a new row
def standardAppends(fReportId, fPatientId, fFirstName, fMiddleName, fLastName, fMRN, fDOB, fAccession, fTestText, fTestName, fFullText, fSampleLocation, fPathologist, fDateOrdered,
                    fDateReported, fICDCode, fDatasourcetype, fsource, fsuborg):
    tempreportIdList.append(fReportId)
    temppatientIdList.append(fPatientId)
    tempfirstNameList.append(fFirstName)
    tempmiddleNameList.append(fMiddleName)
    templastNameList.append(fLastName)
    tempmrnList.append(fMRN)
    tempdobList.append(fDOB)
    tempaccessionNumberList.append(fAccession)
    temptestTextList.append(fTestText)
    temptestNameList.append(fTestName)
    tempfullTextList.append(fFullText)
    tempsampleLocationList.append(fSampleLocation)
    temppathologistList.append(fPathologist)
    tempdateOrderedList.append(fDateOrdered)
    tempdateReportedList.append(fDateReported)
    tempicdCodeList.append(fICDCode)
    tempdatasourcetypeList.append(fDatasourcetype)
    tempsourcenameList.append(fsource)
    tempSuborgList.append(fsuborg)

def normalStandardAppends():
    standardAppends(row['reportId'], row['patientId'], row['firstName'], row['middleName'], row['lastName'], row['mrn'], row['dob'], row['accession'], row['testText'], row['testType'],
                    row['fullText'], row['sampleLocation'], row['pathologist'], row['dateOrdered'], row['dateReported'], row['icdCode'], datasourcetype, sourcename, suborg)

# Find the longest list
def find_max_list(list):
    list_len = [len(i) for i in list]
    return max(list_len)

# Make sure everybody is as long as the longest list.
def squareUp():
    maxSize = find_max_list(allTempLists)
    for lis in allTempLists:
        if lis != tempalterationList:
            while len(lis) < maxSize:
                lis.append('')
        if lis == tempalterationList:
            while len(lis) < maxSize:
                if len(tempalterationList) == 0:
                    lis.append('')
                else:
                    lis.append(tempalterationList[-1])

doERPR = True
doHer2 = True
doPDL1 = True
doBRCA = True
doCRC = False
doGuardant = False

rowNum = 0

# Let's do Her2
rowNum = 0
if doHer2:
    sourcename = 'hfhs'
    suborg = 'Henry Ford Health System'
    pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/May2021/MayBreastData.csv", low_memory=False)
    # No nulls needed
    Her2Reports = pathReports.replace(np.nan, '', regex=True)
    datasourcetype = 'Narrative'

    # I put this check in to make sure results always come in the same order
    gene1sig = False
    gene2sig = False
    genesratio = False
    lastTag = ''

    oldId = ''

    # This is for inserting probe names
    compId = ''
    probeHold = ''
    probeHoldNum = 0

    for index, row in Her2Reports.iterrows():

        # If biomarker is null, skip
        if row['biomarker'] == '':
            continue

        # These are for result overviews, like 'if the ratio is >2 then..."
        if any(x in row['numeric'] for x in ['>', '<']) and ('ratio' in row['concept'] or 'signal' in row['concept']):
            continue

        # This is for test information, and is discarded for now.
        if any(x in row['testText'] for x in ['signals was changed from', 'centromere signals is #']):
            continue

        if 'nuclear' in row['qualifier']:
            continue

        if 'studies' in row['concept']:
            continue

        # This is an extra result we don't need
        if row['qualifier'] in ['consistent with result, equivocal', 'weak, positive, equivocal', 'negative, equivocal', 'strong, equivocal', 'equivocal, negative']:
            row['qualifier'] = 'equivocal'

        # We don't need microsatellite
        if row['qualifier'] in ['negative, microsatellite stable', 'negative, unstable', 'negative, detected', 'negative, average', 'negative, together, consistent with result',
                                'average, strong, negative']:
            row['qualifier'] = 'negative'

        if row['qualifier'] in ['slightly, different', 'strong, positive, strong positive']:
            row['qualifier'] = 'positive'

        # Concatenated results should be negative
        if row['qualifier'] in ['positive, negative', 'strong, positive, negative', 'nuclear, negative, absent']:
            row['qualifier'] = 'negative'

        # This indicates they're talking about the test
        if row['qualifier'] in['negative, equivocal, positive', 'usually', 'consistent with result', 'consistent with result, negative', 'positive, negative absent']:
            continue

        # we're not doing hema hema, man
        if row['firstName'] == 'hema' and row['lastName'] == 'hema':
            continue

        # This kind of normalization I'm ok with
        if row['concept'] == 'expression, immunohistochemistry':
            row['concept'] = 'expression'
        if row['concept'] in ['immunohistochemistry, stain', 'immunostain, stain']:
            row['concept'] = 'stain'

        # We square up with every new report
        if oldId != '' and row['reportId'] != oldId:
            squareUp()
            oldId = row['reportId']

        # I'm expecting that the ratio tags will all come in a row. So if the qualifier doesn't have ratio or average, and we don't
        # have all three parts, we're in trouble.
        # The ONE exception to this is if we've got 'cen7' as our other variable - then we'll have to do a mapping about it.
        elif 'average' not in row['qualifier'] and 'ratio' not in row['qualifier'] and (genesratio or gene1sig or gene2sig):
            badReports = Her2Reports[Her2Reports['reportId'] == lastTag]
            if 'cen7' in ' '.join(badReports['testText']):
                tempcopyNumberRatioComparisonGeneList.append('cen7')
                sigRat = badReports[badReports['concept'] == 'signal, ratio']
                tempcopyNumberRatioComparisonGeneSignalList.append(list(sigRat['numeric'])[0])
                normalStandardAppends()
                squareUp()
                gene2sig = False
                gene1sig = False
                genesratio = False
                lastTag = ''

            elif gene1sig and gene2sig:
                badReports = Her2Reports[Her2Reports['reportId'] == lastTag]
                tempcopyNumberRatioComparisonGeneList.append('centromere 17')
                tempcopyNumberRatioList.append(str(float(tempaverageSignalList[-1]) / float(tempcopyNumberRatioComparisonGeneSignalList[-1])))
                normalStandardAppends()
                squareUp()
                gene2sig = False
                gene1sig = False
                genesratio = False
                lastTag = ''

            else:
                print("OUT OF ORDER")
                badReports = Her2Reports[Her2Reports['reportId'] == lastTag]
                print(genesratio)
                print(gene1sig)
                print(gene2sig)
                print(badReports)
                print(row['biomarker'], row['concept'], row['numeric'], row['qualifier'])
                input()

        elif row['reportId'] != lastTag and lastTag != '' and (genesratio or gene1sig or gene2sig):
            print("NEW TEST?!")
            input()

        # compId is the identifier for the report id associated with the probe that we're holding onto. Any subsequent rows
        # will also get this probe value! We've already gone back and given it to previous records in this report.
        if compId == row['reportId']:
            tempprobeList.append(probeHold)
            tempprobeNumberCellsList.append(probeHoldNum)
        elif compId != '':
            compId = ''
            probeHold = ''
            probeHoldNum = 0

        # Set it on row 1
        if oldId == '':
            oldId = row['reportId']

        if any(x in row['qualifier'] for x in ['pending']) or any(y in row['testText'] for y in ['will be reported', 'reported as an addendum', 'are reported under',
                                                                                                 'from the outside report', 'testing is deferred']):
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her-2', 'her 2', 'her2/neu']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempvariantNameList.append(bio)
                    tempotherAnalyteList.append('')
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('pending')
                    tempplatformList.append('ihc')
                    normalStandardAppends()
                    squareUp()


        elif any(x in row['testText'] for x in ['no tumor cells present', 'insufficient for', 'insufficient cells', 'insufficient tumor cells', 'no tumor is present',
                                                'no tissue is present', 'quantity not sufficient', 'insufficient amount']):
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her-2', 'her 2', 'her2/neu']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('qns')
                    tempplatformList.append('ihc')
                    normalStandardAppends()
                    squareUp()

        elif any(x in row['testText'] for x in ['see attached', 'see other test', 'see addendum', 'performed on addendum', 'please see addenda', 'please see the', 'please see her2',
                                                'please see results below', 'please see procedure', 'please see separate', 'specimen was sent out for', 'please refer to']):
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her-2', 'her 2', 'her2/neu']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('results in separate report')
                    tempplatformList.append('ihc')
                    normalStandardAppends()
                    squareUp()

        elif any(x in row['testText'] for x in ['cannot be performed', 'failure of test:', 'unable to obtain results']):
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her-2', 'her 2', 'her2/neu']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('test could not be performed')
                    tempplatformList.append('ihc')
                    normalStandardAppends()
                    squareUp()

        elif any(x in row['testText'] for x in ['cancelled at the request of the care provider']):
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her-2', 'her 2', 'her2/neu']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('test could not be performed')
                    tempplatformList.append('ihc')
                    normalStandardAppends()
                    squareUp()

        # There are three parts - a cen17 signal, a her2 signal, and a cen17/her2 ratio
        elif row['biomarker'] in ['centromere, centromere 17'] and row['qualifier'] == 'ratio' and row['concept'] == 'signal' and row['numeric'] != '':
            if not genesratio:
                if not gene1sig and not gene2sig and not genesratio:
                    squareUp()
                genesratio = True
                lastTag = row['reportId']
                if gene1sig and gene2sig and genesratio:
                    lastTag = ''
                tempcopyNumberRatioComparisonGeneList.append('centromere 17')
                tempcopyNumberRatioList.append(row['numeric'])

        elif row['biomarker'] in ['her2', 'her-2', 'her 2'] and row['qualifier'] == 'ratio' and row['numeric'] != '':
            if not genesratio:
                if not gene1sig and not gene2sig and not genesratio:
                    squareUp()
                genesratio = True
                lastTag = row['reportId']
                if gene1sig and gene2sig and genesratio:
                    lastTag = ''
                tempcopyNumberRatioComparisonGeneList.append('centromere 17')
                tempcopyNumberRatioList.append(row['numeric'])

        elif row['biomarker'] in ['her2', 'her-2', 'her 2'] and row['qualifier'] in 'average' and row['numeric'] != '':
            if not gene1sig and not gene2sig and not genesratio:
                squareUp()
            gene1sig = True
            lastTag = row['reportId']
            tempproteinList.append(row['biomarker'])
            tempgeneList.append('')
            tempotherAnalyteList.append('')
            tempvariantNameList.append(row['biomarker'])
            tempaverageSignalList.append(row['numeric'])
            tempalterationList.append('ihc signal')
            tempplatformList.append('ihc')

        elif row['biomarker'] in ['centromere, centromere 17', 'centromere 17'] and row['qualifier'] == 'average' and row['numeric'] != '':
            if not gene1sig and not gene2sig and not genesratio:
                squareUp()
            gene2sig = True
            lastTag = row['reportId']
            tempcopyNumberRatioComparisonGeneSignalList.append(row['numeric'])

        elif 'centromere' in row['biomarker'] and 'ratio' in row['concept'] and row['numeric'] != '':
            if not gene1sig and not gene2sig and not genesratio:
                squareUp()
            genesratio = True
            lastTag = row['reportId']
            tempcopyNumberRatioComparisonGeneSignalList.append(row['numeric'])

        elif 'overexpression' in row['concept']:
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her 2', 'her-2', 'her2/neu']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('overexpression')
                    tempalterationStatusList.append(row['qualifier'])
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '+' in num:
                            tempintensityList.append(num)
            normalStandardAppends()

        elif 'nuc ish' in row['biomarker']:
            compId = row['reportId']
            for bio in row['biomarker'].split(', '):
                if 'nuc ish' in bio:
                    probeHold = bio
            for num in row['numeric']:
                if num.isnumeric():
                    probeHoldNum = row['numeric']
            indList = len(tempproteinList) - 1
            while len(tempreportIdList) > len(tempprobeList):
                tempprobeList.append([])
                tempprobeNumberCellsList.append([])
            while tempreportIdList[indList] == compId:
                tempprobeList[indList] = probeHold
                tempprobeNumberCellsList[indList] = probeHoldNum
                indList = indList - 1

        elif any(x in row['concept'] for x in ['amplification', 'duplication', 'aneuploidy']):
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her 2', 'her-2', 'her2/neu', 'chromosome 17']:
                    if bio == 'chromosome 17':
                        tempotherAnalyteList.append(bio)
                        tempgeneList.append('')
                        tempproteinList.append('')
                        tempvariantNameList.append(bio)
                    else:
                        tempproteinList.append('her2')
                        tempvariantNameList.append('her2')
                        tempgeneList.append('')
                        tempotherAnalyteList.append('')
                    tempalterationList.append(row['concept'])
                    tempalterationStatusList.append(row['qualifier'])
                    tempplatformList.append('ihc')
                    normalStandardAppends()
                    squareUp()

        elif any(x in row['qualifier'] for x in ['negative', 'positive', 'equivocal']):
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her 2', 'her-2', 'her2/neu']:
                    tempproteinList.append('her2')
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append('her2')

                    if row['concept'] not in ['foci'] and row['concept'] != '':
                        tempalterationList.append(row['concept'])
                    else:
                        tempalterationList.append('expression')
                    tempalterationStatusList.append(row['qualifier'])
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '+' in num:
                            tempintensityList.append(num)
                    normalStandardAppends()
                    squareUp()

        elif row['concept'] in ['loss', 'expression', 'stain']:
            for bio in row['biomarker'].split(', '):
                if bio in ['her2', 'her 2', 'her-2', 'her2/neu']:
                    tempproteinList.append('her2')
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append('her2')
                    tempalterationList.append(row['concept'])
                    tempalterationStatusList.append(row['qualifier'])
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '+' in num:
                            tempintensityList.append(num)
                    normalStandardAppends()
                    squareUp()

        # Irrelevent
        elif not any(x in row['biomarker'] for x in ['her2', 'her-2', 'her 2', 'her2/neu']) or row['mrn'] in ['63455080'] or row['concept'] in ['nucleus, ratio']\
                or (row['concept'] in ['ratio', 'ratio, signal'] and row['numeric'] == '') or any(x in row['qualifier'] for x in ['consistent with result', 'similar']):
            continue

        else:
            weirdBio.append(row['biomarker'])
            weirdCon.append(row['concept'])
            weirdNum.append(row['numeric'])
            weirdQua.append(row['qualifier'])
            weirdText.append(row['fullText'])
            weirdPatient.append(row['patientId'])

        # Once we have all three pieces of information for the signal, append!
        if gene1sig and gene2sig and genesratio:
            normalStandardAppends()
            squareUp()
            genesratio = False
            gene1sig = False
            gene2sig = False

# Let's make sure we add ihc signal ratio to the call it comes from. The way this goes is, there will be one row
# with all our signal information, and another with 'nuc ish' in the test text. We want to merge those, when
# the signal information comes first.
if doHer2:
    deleteRows = []
    averageSig = []
    compSig = []
    compAvg = []
    comprecId = []
    for x in range(0, len(tempvariantNameList)):
        # We're assuming that the ihc signal always comes first
        # Error out if not
        if tempcopyNumberRatioComparisonGeneSignalList[x] != '':
            comprecId.append(tempreportIdList[x])
            averageSig.append(tempaverageSignalList[x])
            compSig.append(tempcopyNumberRatioComparisonGeneList[x])
            compAvg.append(tempcopyNumberRatioComparisonGeneSignalList[x])
            deleteRows.append(x)
        # And that we always want to add it to a row with 'nuc ish' in it
        # If 'nuc ish' comes before we have these signals, then it's for
        # some other set of values.
        elif 'nuc ish' in temptestTextList[x]:
            if comprecId == '' or averageSig == []:
                continue
            else:
                tempaverageSignalList[x] = averageSig.pop()
                tempcopyNumberRatioComparisonGeneList[x] = compSig.pop()
                tempcopyNumberRatioComparisonGeneSignalList[x] = compAvg.pop()

    # Now we've merged all the rows, let's delete the ones with redundant information, from last to first.
    deleteRows.reverse()
    for delRow in deleteRows:
        for listz in allTempLists:
            del listz[delRow]

# Let's do ER/PR
rowNum = 0
if doERPR:
    sourcename = 'hfhs'
    suborg = 'Henry Ford Health System'
    pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/May2021/MayBreastData.csv", low_memory=False)
    # No nulls needed
    ERPRReports = pathReports.replace(np.nan, '', regex=True)
    datasourcetype = 'Narrative'

    for index, row in ERPRReports.iterrows():
        rowNum = rowNum + 1
        # If biomarker is null, skip
        if row['biomarker'] == '':
            continue

        # These things mean it's a sample it's caught
        if 'f' in row['numeric']:
            row['numeric'] = ''

        if '/' in row['numeric'] and '/8' not in row['numeric'] and '/0' not in row['numeric'] and len(row['numeric'].split()) == 1:
            row['numeric'] = ''

        if 'nuclear' in row['qualifier']:
            continue

        # Concatenated results should be negative
        if row['qualifier'] in ['positive, negative', 'negative, nuclear, negative positive negative negative', 'negative, together, consistent with result',
                                'negative, consistent with result']:
            row['qualifier'] = 'negative'

        if any(x in row['qualifier'] for x in ['pending']) or any(y in row['testText'] for y in ['will be reported', 'reported as an addendum', 'are reported under',
                                                                                                 'from the outside report']):
            for bio in row['biomarker'].split(', '):
                if bio in ['estrogen receptor', 'er', 'progesterone receptor', 'pr']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('pending')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['no tumor cells present', 'insufficient for']):
            for bio in row['biomarker'].split(', '):
                if bio in ['estrogen receptor', 'er', 'progesterone receptor', 'pr']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('qns')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['see attached', 'see other test', 'see addendum', 'performed on addendum']):
            for bio in row['biomarker'].split(', '):
                if bio in ['estrogen receptor', 'er', 'progesterone receptor', 'pr']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('results in separate report')
                    tempplatformList.append('ihc')
                    normalStandardAppends()


        # For your allred scores
        elif ('erica' in row['concept'] or 'prica' in row['concept']) and (row['biomarker'] in ['estrogen receptor', 'er'] or row['biomarker'] in ['progesterone receptor', 'pr']):
            for bio in row['biomarker'].split(', '):
                if bio in ['estrogen receptor', 'er']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('erica')
                    if '<1' in row['numeric']:
                        tempalterationStatusList.append('negative')
                    else:
                        tempalterationStatusList.append('positive')
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        elif '/8' in num or '/0' in num:
                            tempallredScoreList.append(num)
                        elif num.isnumeric() or '+' in num:
                            if '+' in num:
                                tempintensityList.append(num)
                            else:
                                tempintensityList.append(str(num) + '+')
                    normalStandardAppends()
                if bio in ['progesterone receptor', 'pr']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('prica')
                    if '<1' in row['numeric']:
                        tempalterationStatusList.append('negative')
                    else:
                        tempalterationStatusList.append('positive')
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        elif '/8' in num or '/0' in num:
                            tempallredScoreList.append(num)
                        elif num.isnumeric() or '+' in num:
                            if '+' in num:
                                tempintensityList.append(num)
                            else:
                                tempintensityList.append(str(num) + '+')
                    normalStandardAppends()
        elif ('allred score' in row['concept']) and (row['biomarker'] in ['estrogen receptor', 'er'] or row['biomarker'] in ['progesterone receptor', 'pr']):
            for bio in row['biomarker'].split(', '):
                if bio in ['estrogen receptor', 'er']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('erica')
                    if '<1' in row['numeric'] or '0%' in row['numeric']:
                        tempalterationStatusList.append('negative')
                    else:
                        tempalterationStatusList.append('positive')
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        elif '/8' in num or '/0' in num:
                            tempallredScoreList.append(num)
                        elif num.isnumeric() or '+' in num:
                            if '+' in num:
                                tempintensityList.append(num)
                            else:
                                tempintensityList.append(str(num) + '+')
                    normalStandardAppends()
                if bio in ['progesterone receptor', 'pr']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('prica')
                    if '<1' in row['numeric'] or '0%' in row['numeric']:
                        tempalterationStatusList.append('negative')
                    else:
                        tempalterationStatusList.append('positive')
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        elif '/8' in num or '/0' in num:
                            tempallredScoreList.append(num)
                        elif num.isnumeric() or '+' in num:
                            if '+' in num:
                                tempintensityList.append(num)
                            else:
                                tempintensityList.append(str(num) + '+')
                    normalStandardAppends()
        elif ('positive' in row['qualifier'] and 'negtive' not in row['qualifier']) or ('negative' in row['qualifier'] and 'positive' not in row['qualifier']):
            for bio in row['biomarker'].split(', '):
                if bio in ['estrogen receptor', 'er', 'progesterone receptor', 'pr']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append(row['qualifier'])
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        elif '/8' in num or '/0' in num:
                            tempallredScoreList.append(num)
                        elif num.isnumeric() or '+' in num:
                            if '+' in num:
                                tempintensityList.append(num)
                            else:
                                tempintensityList.append(str(num) + '+')
                    normalStandardAppends()

        elif any(x in row['qualifier'] for x in ['weak', 'approximately', 'patchy', 'present', 'moderate', 'subset', 'intermediate', 'strong', 'equivocal']):
            for bio in row['biomarker'].split(', '):
                if bio in ['estrogen receptor', 'er', 'progesterone receptor', 'pr']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append(row['qualifier'])
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        elif '/8' in num or '/0' in num:
                            tempallredScoreList.append(num)
                        elif num.isnumeric() or '+' in num:
                            if '+' in num:
                                tempintensityList.append(num)
                            else:
                                tempintensityList.append(str(num) + '+')
                    normalStandardAppends()

        elif any(x in row['concept'] for x in ['intensity', 'stain', 'expression']):
            for bio in row['biomarker'].split(', '):
                if bio in ['estrogen receptor', 'er', 'progesterone receptor', 'pr']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append(row['qualifier'])
                    tempplatformList.append('ihc')
                    for num in row['numeric'].split(', '):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        elif '/8' in num or '/0' in num:
                            tempallredScoreList.append(num)
                        elif num.isnumeric() or '+' in num:
                            if '+' in num:
                                tempintensityList.append(num)
                            else:
                                tempintensityList.append(str(num) + '+')
                    normalStandardAppends()



        # Irrelevent results
        elif not any(x in ' ' + row['biomarker'].replace('primary', '').replace('procedure', '') for x in [' er', ' pr', 'estrogen receptor', 'progesterone receptor']) \
                or row['qualifier'] in ['not specific']:
            continue
        else:
            weirdBio.append(row['biomarker'])
            weirdCon.append(row['concept'])
            weirdNum.append(row['numeric'])
            weirdQua.append(row['qualifier'])
            weirdText.append(row['fullText'])
            weirdPatient.append(row['patientId'])

        squareUp()

# Let's do PD-L1
rowNum = 0
if doPDL1:
    sourcename = 'hfhs'
    suborg = 'Henry Ford Health System'
    pathReports = pd.read_csv('/Users/bholmes/Desktop/LatestNLP/Unstructured Results/May2021/MayBreastData.csv', low_memory=False)
    # No nulls needed
    PDL1Reports = pathReports.replace(np.nan, '', regex=True)
    datasourcetype = 'Narrative'

    for index, row in PDL1Reports.iterrows():
        rowNum = rowNum + 1

        # If biomarker is null, skip
        if row['biomarker'] == '':
            continue

        if row['concept'] == '' and 'tps' in row['testText']:
            row['concept'] = 'tumor proportion score'

        # Concatenated results should be negative
        if row['qualifier'] in ['positive, negative']:
            row['qualifier'] = 'negative'

        if any(x in row['qualifier'] for x in ['pending']) or any(y in row['testText'] for y in ['will be reported', 'reported as an addendum', 'are reported under',
                                                                                                 'from the outside report', 'testing is deferred']):
            for bio in row['biomarker'].split(', '):
                if bio in ['pd-l1', 'pdl1', 'pd l1']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('pending')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['no tumor cells present', 'insufficient for', 'insufficient cells', 'insufficient tumor cells', 'no tumor is present',
                                                'no tissue is present', 'quantity not sufficient', 'insufficient amount']):
            for bio in row['biomarker'].split(', '):
                if bio in ['pd-l1', 'pdl1', 'pd l1']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('qns')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['see attached', 'see other test', 'see addendum', 'performed on addendum', 'please see addenda', 'please see the', 'please see her2',
                                                'please see results below', 'please see procedure', 'please see separate']):
            for bio in row['biomarker'].split(', '):
                if bio in ['pd-l1', 'pdl1', 'pd l1']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('results in separate report')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['cannot be performed', 'failure of test:', 'unable to obtain results']):
            for bio in row['biomarker'].split(', '):
                if bio in ['pd-l1', 'pdl1', 'pd l1']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('test could not be performed')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        # The most common one will be tumor proportion score or combined positive score
        elif row['concept'] == 'tumor proportion score':
            if row['numeric'] == '':
                continue
            for bio in row['biomarker'].split(', '):
                if 'clone' in bio:
                    tempcloneList.append(bio)
                elif bio in ['pd-l1', 'pdl1', 'pd l1']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
            tempalterationList.append(row['concept'])
            tempalterationStatusList.append(row['qualifier'])
            for num in row['numeric'].split(', '):
                if num.replace('%', '').replace('<', '').isnumeric():
                    temptumorProportionScoreList.append(num)
                elif '-' not in num:
                    temppercentTumorCellsList.append(num)
            normalStandardAppends()


        # The most common one will be tumor proportion score or combined positive score
        elif row['concept'] in ['combined positive score', 'combined positive score, expression']:
            if row['numeric'] == '':
                continue
            if row['concept'] == 'combined positive score, expression':
                row['concept'] = 'combined positive score'
                if row['qualifier'] == 'positive, negative':
                    row['qualifier'] = 'negative'
            for bio in row['biomarker'].split(', '):
                if 'clone' in bio:
                    tempcloneList.append(bio)
                elif bio in ['pd-l1', 'pdl1', 'pd l1']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
            tempalterationList.append(row['concept'])
            tempalterationStatusList.append(row['qualifier'])
            for num in row['numeric'].split(', '):
                if num.replace('>', '').replace('=', '').replace('<', '').isnumeric():
                    tempcombinedPositiveScoreList.append(num)
                elif '-' not in num:
                    temppercentTumorCellsList.append(num)
            normalStandardAppends()

        elif row['concept'] in ['expression', 'low expression', 'immunostain, stain'] and not any(x in row['testText'] for x in ['combined positive score', 'cps', 'tps', 'tumor proportion score']):
            for bio in row['biomarker'].split(', '):
                if 'clone' in bio:
                    tempcloneList.append(bio)
                elif bio in ['pd-l1', 'pdl1', 'pd l1']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
            tempalterationList.append(row['concept'])
            tempalterationStatusList.append(row['qualifier'])
            for num in row['numeric'].split(', '):
                if num.replace('%', '').replace('<', '').isnumeric():
                    temppercentTumorCellsList.append(num)
            normalStandardAppends()

        elif row['concept'] == 'expression' and 'combined positive score' in row['testText']:
            continue
        elif 'clone' in row['biomarker'] and row['numeric'] == '':
            continue
        elif 'pd-l1 (22c3) expression by immunohistochemistry: \n- combined positive' in row['fullText'] and row['numeric'] == '':
            continue
        elif any(x in row['testText'] for x in ['is a qualitative immunohistochemical ']):
            continue

        # Irrelevent
        elif not any(x in row['biomarker'] for x in ['pd-l1', 'pdl1', 'pd l1']) or row['testText'] == '22c3':
            continue


        else:
            weirdBio.append(row['biomarker'])
            weirdCon.append(row['concept'])
            weirdNum.append(row['numeric'])
            weirdQua.append(row['qualifier'])
            weirdText.append(row['fullText'])
            weirdPatient.append(row['patientId'])

        squareUp()

if doBRCA:
    sourcename = 'hfhs'
    suborg = 'Henry Ford Health System'
    pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/May2021/MayBreastData.csv", low_memory=False)
    # No nulls needed
    BRCAreports = pathReports.replace(np.nan, '', regex=True)
    datasourcetype = 'Narrative'

    for index, row in BRCAreports.iterrows():

        if any(x in row['qualifier'] for x in ['pending']) or any(y in row['testText'] for y in ['will be reported', 'reported as an addendum', 'are reported under',
                                                                                                 'from the outside report', 'testing is deferred']):
            for bio in row['biomarker'].split(', '):
                if bio in ['brca1', 'brca2']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('pending')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['no tumor cells present', 'insufficient for', 'insufficient cells', 'insufficient tumor cells', 'no tumor is present',
                                                'no tissue is present', 'quantity not sufficient', 'insufficient amount']):
            for bio in row['biomarker'].split(', '):
                if bio in ['brca1', 'brca2']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('qns')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['see attached', 'see other test', 'see addendum', 'performed on addendum', 'please see addenda', 'please see the', 'please see her2',
                                                'please see results below', 'please see procedure', 'please see separate', 'specimen was sent out for', 'please refer to']):
            for bio in row['biomarker'].split(', '):
                if bio in ['brca1', 'brca2']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('results in separate report')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['cannot be performed', 'failure of test:', 'unable to obtain results']):
            for bio in row['biomarker'].split(', '):
                if bio in ['brca1', 'brca2']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('test could not be performed')
                    tempplatformList.append('ihc')
                    normalStandardAppends()

        elif any(x in row['testText'] for x in ['cancelled at the request of the care provider']):
            for bio in row['biomarker'].split(', '):
                if bio in ['brca1', 'brca2']:
                    tempproteinList.append(bio)
                    tempgeneList.append('')
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append('test could not be performed')
                    tempplatformList.append('ihc')
                    normalStandardAppends()


        elif row['qualifier'] == 'normal results':
            if 'pathogenic mutations' in row['testText']:
                row['concept'] = row['concept'] + ', ' + 'pathogenic mutations'
            if 'variants of unknown significance' in row['testText']:
                row['concept'] = row['concept'] + ', ' + 'vus mutations'
            if 'gross deletion(s)/duplication(s)' in row['testText']:
                row['concept'] = row['concept'] + ', ' + 'deletions, duplications'
            while row['concept'].startswith(',') or row['concept'].startswith(' '):
                row['concept'] = row['concept'][1:]
            for bio in row['biomarker'].split(', '):
                if bio in ['brca1', 'brca2']:
                    tempproteinList.append('')
                    tempgeneList.append(bio)
                    tempotherAnalyteList.append('')
                    tempvariantNameList.append(bio)
            tempalterationList.append(row['concept'])
            tempalterationStatusList.append('negative')
            tempplatformList.append('ngs')
            normalStandardAppends()

        elif ('positive' in row['qualifier'] and 'pathogenic' in row['qualifier']) or ('detected' in row['qualifier'] and 'pathogenic' in row['qualifier']):
            if 'brca1' in row['biomarker'] or 'brca2' in row['biomarker']:
                for bio in row['biomarker'].split(','):
                    bio = bio.strip()
                    if not bio.endswith('tt'):
                        if bio in ['brca1', 'brca2']:
                            tempproteinList.append('')
                            tempgeneList.append(bio)
                            tempotherAnalyteList.append('')
                            tempvariantNameList.append(bio)
                        if bio.startswith('c.'):
                            tempcodingIdList.append(bio)
                        if bio.startswith('p.'):
                            tempproteinIdList.append(bio)
                tempalterationList.append('mutation')
                tempalterationStatusList.append('positive, pathogenic')
                tempplatformList.append('ngs')
                normalStandardAppends()

        elif row['qualifier'] in ['negative']:
            for bio in row['biomarker'].split(', '):
                if not bio.endswith('tt'):
                    if bio in ['brca1', 'brca2']:
                        tempproteinList.append('')
                        tempgeneList.append(bio)
                        tempotherAnalyteList.append('')
                        tempvariantNameList.append(bio)
                    if bio.startswith('c.'):
                        tempcodingIdList.append(bio)
                    if bio.startswith('p.'):
                        tempproteinIdList.append(bio)
            tempalterationList.append('mutation')
            tempalterationStatusList.append('negative')
            tempplatformList.append('ngs')
            normalStandardAppends()

        elif 'uncertain significance' in row['qualifier'] or 'unknown significance' in row['qualifier']:
            for bio in row['biomarker'].split(', '):
                if not bio.endswith('tt'):
                    if bio in ['brca1', 'brca2']:
                        tempproteinList.append('')
                        tempgeneList.append(bio)
                        tempotherAnalyteList.append('')
                        tempvariantNameList.append(bio)
                    if bio.startswith('c.'):
                        tempcodingIdList.append(bio)
                    if bio.startswith('p.'):
                        tempproteinIdList.append(bio)
            tempalterationList.append('mutation')
            tempalterationStatusList.append('vous')
            tempplatformList.append('ngs')
            normalStandardAppends()


        elif row['qualifier'] in ['negative, detected'] and 'c.' in row['testText']:
            continue

        # Irrelevent
        elif not any(x in row['biomarker'] for x in ['brca1', 'brca2']):
            continue


        else:
            weirdBio.append(row['biomarker'])
            weirdCon.append(row['concept'])
            weirdNum.append(row['numeric'])
            weirdQua.append(row['qualifier'])
            weirdText.append(row['fullText'])
            weirdPatient.append(row['patientId'])

        squareUp()



if doGuardant:
    guardantReports = pd.read_csv('/Users/bholmes/Desktop/LatestNLP/PDFGeneList/PDFs/FullGuardantResults.csv', low_memory=False)
    datasourcetype = 'PDF'
    # No nulls needed
    guardantReports = guardantReports.replace(np.nan, '', regex=True)
    # We'll want to ingest these one report at a time. First we'll get a list of all test ids
    reports = guardantReports['reportid'].unique()

    # For each report...
    number = 0
    for report in reports:
        # Clear all the temp lists
        for tl in allTempLists:
            tl.clear()
        number = number + 1

        reportColumns = guardantReports[guardantReports['reportid'] == report]
        reportColumns.reset_index()

        for index, row in reportColumns.iterrows():
            isTouched = True
            tempreportIdList.append(row['reportid'])
            temppatientIdList.append('')
            tempproteinList.append('')
            tempgeneList.append(row['Biomarker'])
            tempvariantNameList.append(row['Biomarker'])
            tempotherAnalyteList.append('')
            if row['Type'] == 'VUS':
                tempalterationList.append('Mutation' + ' ' + row['Type'] + ' - ' + row['Call'].split(' - ')[1])
                tempalterationStatusList.append(row['Call'][:row['Call'].index(' - ')])
            elif 'DETECTED' in row['Call'] or 'Cancelled' in row['Call']:
                tempalterationList.append(row['Call'])
                tempalterationList.append(row['Type'])
            else:
                tempalterationList.append(row['Type'] + ' - ' + row['Call'].split(' - ')[1])
                tempalterationStatusList.append(row['Call'][:row['Call'].index(' - ')])
            tempfirstNameList.append(row['First Name'])
            tempmiddleNameList.append(row['Middle Name'])
            templastNameList.append(row['Last Name'])
            tempmrnList.append(row['MRN'])
            tempdobList.append(row['Birthdate'])
            tempaccessionNumberList.append(row['reportid'])
            temptestTextList.append(row['Test Text'])
            tempfullTextList.append(row['Full Text'])
            temptestNameList.append(row['Test Type'])
            tempplatformList.append(row['Platform'])
            tempsampleLocationList.append(row['Specimen Site'])
            temppathologistList.append('')
            tempdateReportedList.append(row['Test Reported Date'])
            tempdateOrderedList.append(row['Test Ordered Date'])
            tempexonsList.append(row['Exons'])
            tempdatasourcetypeList.append(datasourcetype)


            if not isTouched:
                weirdBio.append(row['biomarker'])
                weirdCon.append(row['concept'])
                weirdNum.append(row['numeric'])
                weirdQua.append(row['qualifier'])
                weirdText.append(row['fullText'])
                weirdPatient.append(row['patientId'])

        squareUp()
        for z in range(0, len(allLists)):
            allLists[z] = allLists[z] + allTempLists[z]


if doCRC:
    # We'll start with CRC
    CRCeports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/May2021/TestRaw2.csv", low_memory=False)

    # No nulls needed
    CRCReports = CRCeports.replace(np.nan, '', regex=True)

    # We'll want to ingest these one report at a time. First we'll get a list of all test ids
    reports = CRCReports['reportId'].unique()

    # For each report...
    for report in reports:
        # Clear all the temp lists
        for tl in allTempLists:
            tl.clear()

        reportColumns = CRCReports[CRCReports['reportId'] == report]
        reportColumns.reset_index()

        tempalteration = ''
        # If we have a type of values, we'll find it.
        for index, row in reportColumns.iterrows():
            # This is for iteration
            isTouched = False

            if any(x in row['concept'] for x in ['fusions', 'coding variant', 'copy number variant', 'mutation', 'rearrangement', 'loss', 'expression', 'absense', 'stain',
                                                 'copy number alteration', 'immuonohistochemistry']):
                alt = ''
                for y in ['fusions', 'coding variant', 'copy number variant', 'mutation', 'rearrangement', 'loss', 'expression', 'absense', 'stain', 'copy number alteration',
                          'immunohistochemistry']:
                    if y in row['concept']:
                        alt = alt + ', ' + y
                alt = alt.strip()
                while alt.startswith((',', ' ')):
                    alt = alt[1:]
                while alt.endswith((',', ' ')):
                    alt = alt[:-1]
                tempalteration = alt

            if any(x in row['biomarker'] for x in ['met', 'ret', 'ros1', 'ntrk2', 'ntrk1', 'ntrk3', 'alk', 'pms2', 'msh6', 'msh2', 'mlh1', 'braf', 'kras',' nras', 'erbb2']):
                isTouched = True
                for y in row['biomarker'].split(','):
                    if y.strip() in ['met', 'ret', 'ros1', 'ntrk2', 'ntrk1', 'ntrk3', 'alk', 'pms2', 'msh6', 'msh2', 'mlh1', 'braf', 'kras',' nras', 'erbb2'] and tempalteration != '':
                        normalStandardAppends()
                        tempproteinList.append('')
                        tempgeneList.append(y)
                        tempvariantNameList.append(y)
                        tempotherAnalyteList.append('')
                        tempalterationList.append(tempalteration)
                        tempalterationStatusList.append(row['qualifier'])

            if 'microsatellite instability' in row['biomarker']:
                if any(x in row['qualifier'] for x in ['microsatellite stable', 'pending', 'not applicable', 'unstable', 'test not performed']):
                    for y in ['microsatellite stable', 'pending', 'not applicable', 'unstable', 'test not performed']:
                        if y in row['qualifier']:
                            isTouched = True
                            normalStandardAppends()
                            tempproteinList.append('')
                            tempgeneList.append('')
                            tempvariantNameList.append('microsatellite instability')
                            tempotherAnalyteList.append('microsatellite instabiliity')
                            tempalterationList.append('msi status')
                            tempalterationStatusList.append(y)
                            break
            squareUp()

            for z in range(0, len(allLists)):
                allLists[z] = allLists[z] + allTempLists[z]

            if not isTouched:
                weirdBio.append(row['biomarker'])
                weirdCon.append(row['concept'])
                weirdNum.append(row['numeric'])
                weirdQua.append(row['qualifier'])
                weirdText.append(row['fullText'])
                weirdPatient.append(row['patientId'])

for z in range(0, len(allLists)):
    allLists[z] = allLists[z] + allTempLists[z]


reportIdList = allLists[0]
patientIdList = allLists[1]
cloneList = allLists[2]
intensityList = allLists[3]
percentTumorCellsList = allLists[4]
allredScoreList = allLists[5]
probeList = allLists[6]
probeNumberCellsList = allLists[7]
averageSignalList = allLists[8]
signalRatioList = allLists[9]
alterationList = allLists[10]
alterationStatusList = allLists[11]
firstNameList = allLists[12]
middleNameList = allLists[13]
lastNameList = allLists[14]
mrnList = allLists[15]
dobList = allLists[16]
accessionNumberList = allLists[17]
testTextList = allLists[18]
testNameList = allLists[19]
percentReadsList = allLists[20]
immuneCellStainPresentList = allLists[21]
strandOrientationList = allLists[22]
clinicalSignificanceList = allLists[23]
allelicStateList = allLists[24]
exonsList = allLists[25]
proteinIdList = allLists[26]
aminoAcidChangeList = allLists[27]
codingIdList = allLists[28]
codingChangeList = allLists[29]
tumorProportionScoreList = allLists[30]
combinedPositiveScoreList = allLists[31]
alleleFrequencyList = allLists[32]
copyNumberRatioList = allLists[33]
log2CopyNumberRatioList = allLists[34]
cellFreeDnaPercentList = allLists[35]
tumorMutationBurdenScoreList = allLists[36]
tumorMutationBurdenUnitList = allLists[37]
icdCodeList = allLists[38]
ericaList = allLists[39]
pricaList = allLists[40]
platformList = allLists[41]
sampleLocationList = allLists[42]
pathologistList = allLists[43]
dateOrderedList = allLists[44]
dateReportedList = allLists[45]
copyNumberList = allLists[46]
fullTextList = allLists[47]
datasourcetypeList = allLists[48]
copyNumberRatioComparisonGeneList = allLists[49]
copyNumberRatioComparisonGeneSignalList = allLists[50]
sourcenameList = allLists[51]
suborgList = allLists[52]
geneList = allLists[53]
proteinList = allLists[54]
otherAnalyteList = allLists[55]
variantNameList = allLists[56]

testTextList = list(map(str.strip, testTextList))

rawResults = pd.DataFrame(list(zip(reportIdList, patientIdList, variantNameList, proteinList, geneList, otherAnalyteList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList, probeNumberCellsList,
                                   averageSignalList, signalRatioList, alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionNumberList,
                                   testTextList, testNameList, percentReadsList, immuneCellStainPresentList, strandOrientationList, clinicalSignificanceList, allelicStateList, exonsList,
                                   proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList, tumorProportionScoreList, combinedPositiveScoreList, alleleFrequencyList,
                                   copyNumberRatioComparisonGeneList, copyNumberRatioComparisonGeneSignalList,
                                   copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList, tumorMutationBurdenScoreList, tumorMutationBurdenUnitList, icdCodeList,
                                   ericaList, pricaList, platformList, sampleLocationList, pathologistList, dateOrderedList, dateReportedList, copyNumberList, fullTextList, datasourcetypeList,
                                   sourcenameList, suborgList)),
                          columns=['reportId', 'patientId', 'variantName', 'protein', 'gene', 'otherAnalyte', 'clone', 'intensity', 'percentTumorCells', 'allredScore', 'probe', 'probeNumberCells', 'averageSignal',
                                   'signalRatio', 'alteration', 'alterationStatus', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accessionNumber', 'testText', 'testName', 'percentReads',
                                   'immuneCellStainPercent', 'strandOrientation', 'clinicalSignificance', 'allelicState', 'exons', 'proteinId', 'aminoAcidChange', 'codingId',
                                   'codingChange', 'tumorProportionScore', 'combinedPositiveScore', 'alleleFrequency', 'copyNumberRatioComparisonMarker', 'copyNumberRatioComparisonMarkerAverageSignal',
                                   'copyNumberRatio', 'log2CopyNumberRatio', 'cellFreeDnaPercent',
                                   'tumorMutationBurdenScore', 'tumorMutationBurdenUnit', 'icdCode', 'erica', 'prica', 'platform', 'sampleLocation', 'pathologist', 'dateOrdered',
                                   'dateReported', 'copyNumber', 'fullText', 'datasourcetype', 'sourcename', 'suborg'])

rawResults = rawResults.drop_duplicates()
rawResults = rawResults.reset_index()

rawResults = rawResults.replace(r'^\s*$', np.nan, regex=True)
rawResults = rawResults.dropna(subset=['reportId', 'variantName'])

finalResults = rawResults.copy()
del finalResults['fullText']

print(len(rawResults['reportId']))
rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/BreastTest.csv", index=False)
