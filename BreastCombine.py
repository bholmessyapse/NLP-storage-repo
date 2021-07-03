import pandas as pd
import numpy as np
import random
# For regex
import re
import copy
from collections import Counter
from uuid import uuid4

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', -1)

weirdBio = []
weirdCon = []
weirdNum = []
weirdQua = []
weirdText = []

# These are the columns we need to send out, in order.
reportIdList, patientIdList, variantNameList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList, probeNumberCellsList, averageSignalList, signalRatioList, \
    alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionNumberList, testTextList, testNameList, platformList, sampleLocationList, \
    pathologistList, dateOrderedList, dateReportedList, copyNumberList, alleleFrequencyList, percentReadsList, immuneCellStainPresentList, strandOrientationList, clinicalSignificanceList, \
    allelicStateList, exonsList, proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList, tumorProportionScoreList, combinedPositiveScoreList, fullTextList,\
    copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList, tumorMutationBurdenScoreList, tumorMutationBurdenUnitList, icdCodeList, ericaList, pricaList = ([] for i in range(49))

# These are the temporary versions we use per report
tempreportIdList, temppatientIdList, tempvariantNameList, tempcloneList, tempintensityList, temppercentTumorCellsList, tempallredScoreList, tempprobeList, tempprobeNumberCellsList, \
  tempaverageSignalList, tempsignalRatioList, tempalterationList, tempalterationStatusList, tempfirstNameList, tempmiddleNameList, templastNameList, tempmrnList, tempdobList, \
  tempaccessionNumberList, temptestTextList, temptestNameList, tempplatformList, tempsampleLocationList, temppathologistList, tempdateOrderedList, tempdateReportedList, tempcopyNumberList, \
  tempalleleFrequencyList, temppercentReadsList, tempimmuneCellStainPresentList, tempstrandOrientationList, tempclinicalSignificanceList, tempallelicStateList, tempexonsList, \
  tempproteinIdList, tempaminoAcidChangeList, tempcodingIdList, tempcodingChangeList, temptumorProportionScoreList, tempcombinedPositiveScoreList, tempfullTextList,\
  tempcopyNumberRatioList, templog2CopyNumberRatioList, tempcellFreeDnaPercentList, temptumorMutationBurdenScoreList, temptumorMutationBurdenUnitList, tempicdCodeList, tempericaList, \
  temppricaList = ([] for j in range(49))

# It's also helpful to have a list of those lists, that we can iterate through.
allTempLists = [tempreportIdList, temppatientIdList, tempvariantNameList, tempcloneList, tempintensityList, temppercentTumorCellsList, tempallredScoreList, tempprobeList,
                tempprobeNumberCellsList, tempaverageSignalList, tempsignalRatioList, tempalterationList, tempalterationStatusList, tempfirstNameList, tempmiddleNameList, templastNameList,
                tempmrnList, tempdobList, tempaccessionNumberList, temptestTextList, temptestNameList, temppercentReadsList, tempimmuneCellStainPresentList, tempstrandOrientationList,
                tempclinicalSignificanceList, tempallelicStateList, tempexonsList, tempproteinIdList, tempaminoAcidChangeList, tempcodingIdList, tempcodingChangeList,
                temptumorProportionScoreList, tempcombinedPositiveScoreList, tempalleleFrequencyList, tempcopyNumberRatioList, templog2CopyNumberRatioList, tempcellFreeDnaPercentList,
                temptumorMutationBurdenScoreList, temptumorMutationBurdenUnitList, tempicdCodeList, tempericaList, temppricaList, tempplatformList, tempsampleLocationList,
                temppathologistList, tempdateOrderedList, tempdateReportedList, tempcopyNumberList, tempfullTextList]

allLists = [reportIdList, patientIdList, variantNameList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList,
                probeNumberCellsList, averageSignalList, signalRatioList, alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList,
                mrnList, dobList, accessionNumberList, testTextList, testNameList, percentReadsList, immuneCellStainPresentList, strandOrientationList,
                clinicalSignificanceList, allelicStateList, exonsList, proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList,
                tumorProportionScoreList, combinedPositiveScoreList, alleleFrequencyList, copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList,
                tumorMutationBurdenScoreList, tumorMutationBurdenUnitList, icdCodeList, ericaList, pricaList, platformList, sampleLocationList,
                pathologistList, dateOrderedList, dateReportedList, copyNumberList, fullTextList]

# These rows are invariant between rows in a test, and should be added every time we add a new row
def standardAppends(fReportId, fPatientId, fFirstName, fMiddleName, fLastName, fMRN, fDOB, fAccession, fTestText, fTestName, fFullText, fSampleLocation, fPathologist, fDateOrdered,
                    fDateReported, fICDCode):
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

def normalStandardAppends():
    standardAppends(row['reportId'], row['patientId'], row['firstName'], row['middleName'], row['lastName'], row['mrn'], row['dob'], row['accession'], row['testText'], row['testType'],
                    row['fullText'], row['sampleLocation'], row['pathologist'], row['dateOrdered'], row['dateReported'], row['icdCode'])

# Find the longest list
def find_max_list(list):
    list_len = [len(i) for i in list]
    return max(list_len)

# Make sure everybody is as long as the longest list.
def squareUp():
    maxSize = find_max_list(allTempLists)
    for lis in allTempLists:
        if lis != tempvariantNameList:
            while len(lis) < maxSize:
                lis.append('')
        if lis == tempvariantNameList:
            while len(lis) < maxSize:
                if len(tempvariantNameList) == 0:
                    lis.append('')
                else:
                    lis.append(tempvariantNameList[-1])

doERPR = True
doHer2 = True
doPDL1 = True
doBRCA = True
doCRC = False


######################
######################
######################
if doERPR:
    # We'll move to the next biggest - ER/PR
    ERPRReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/ER:PR/RawOfERPR.csv", low_memory=False)

    # No nulls needed
    ERPRReports = ERPRReports.replace(np.nan, '', regex=True)

    # We'll want to ingest these one report at a time. First we'll get a list of all test ids
    reports = ERPRReports['reportId'].unique()

    # For each report...
    for report in reports:
        # Clear all the temp lists
        for tl in allTempLists:
            tl.clear()

        reportColumns = ERPRReports[ERPRReports['reportId'] == report]
        reportColumns.reset_index()

        for index, row in reportColumns.iterrows():
            # This is for iteration
            isTouched = False

            if row['biomarker'] == 'pr, estrogen receptor':
                row['biomarker'] = 'progesterone receptor'
            if row['biomarker'] == 'pr':
                row['biomarker'] = 'progesterone receptor'
            if row['biomarker'] == 'estrogen' or row['biomarker'] == 'er':
                row['biomarker'] = 'estrogen receptor'

            # rows with no content I think we want to pass on
            if row['concept'] == 'immunostain' and row['qualifier'] == 'tested' and row['numeric'] == '':
                continue


            if row['numeric'].isnumeric():
                if int(row['numeric']) > 3:
                    row['numeric'] = row['numeric'] + '%'

            # sometimes we get [100, 100%] and we just want the %
            if row['concept'] == '' and len(row['numeric'].split(',')) == 2:
                if row['numeric'].split(',')[0] == row['numeric'].split(',')[1].strip().replace('%',''):
                    row['numeric'] = row['numeric'].split(',')[1]
            # This is for "80-90%, 80%
            if 'intensity' in row['concept'] and len(row['numeric'].split(',')) == 3:
                if '-' in row['numeric'].split(',')[0]:
                    row['numeric'] = row['numeric'].split(',')
                    row['numeric'] = row['numeric'][0] + ',' + row['numeric'][2]
                elif '<' in row['numeric'].split(',')[0]:
                    row['numeric'] = row['numeric'].split(',')
                    row['numeric'] = row['numeric'][0] + ',' + row['numeric'][1]
                elif '%' in row['numeric'].split(',')[0] and '%' in row['numeric'].split(',')[2]:
                    row['numeric'] = row['numeric'].split(',')
                    row['numeric'] = row['numeric'][0] + ',' + row['numeric'][1]
            elif 'intensity' in row['concept'] and len(row['numeric'].split(',')) == 2:
                if '-' in row['numeric'].split(',')[0] and '%' in row['numeric'].split(',')[0] and '%' in row['numeric'].split(',')[1]:
                    row['numeric'] = row['numeric'].split(',')[0]

            # This is to remove 'allred score' from rows where it doesn't belong
            if 'allred score' in row['concept'] and row['concept'] != 'allred score':
                row['concept'] = row['concept'].replace('allred score, ', '')

            if 'estrogen receptor' in row['biomarker']:
                if len(tempvariantNameList) == 0:
                    tempvariantNameList.append('ER')
                    normalStandardAppends()
                # Sometimes we get duplicate data for allred!
                elif '/8' in row['numeric'] and len(tempallredScoreList) > 0 and tempvariantNameList[-1] == 'ER' and row['testText'] == temptestTextList[-1]:
                    if tempallredScoreList[-1] == row['numeric']:
                        continue
                elif '%' in row['numeric'] and len(temppercentTumorCellsList) > 0 and tempvariantNameList[-1] == 'ER' and row['testText'] == temptestTextList[-1]:
                    if temppercentTumorCellsList[-1] == row['numeric']:
                        continue
                elif row['testText'] != temptestTextList[-1]:
                    squareUp()
                    tempvariantNameList.append('ER')
                    normalStandardAppends()
                elif tempvariantNameList[-1] != 'ER':
                    squareUp()
                    tempvariantNameList.append('ER')
                    normalStandardAppends()
                elif len(tempalterationList) > 0 and len(tempallredScoreList) > 0:
                    if tempalterationList[-1] != '' and row['concept'] != '' and tempallredScoreList[-1] == '':
                        squareUp()
                        tempvariantNameList.append('ER')
                        normalStandardAppends()
                # Sometimes we don't catch a '%' where we should
                if row['concept'] == '' and row['numeric'].isnumeric():
                    row['numeric'] = row['numeric'] + '%'
                    tempallredScoreList.append(row['numeric'])
                if 'allred score' in row['concept'] or ('intensity' in row['concept'] and '/8' in ''.join(row['numeric']) and len(row['numeric'].split(',')) == 1):
                    isTouched = True
                    for num in row['numeric'].split(','):
                        if '/8' in num:
                            if len(tempallredScoreList) < len(tempvariantNameList) or row['testText'] != temptestTextList[-1]:
                                tempallredScoreList.append(num)
                        elif '%' in num:
                            if len(temppercentTumorCellsList) < len(tempvariantNameList) or row['testText'] != temptestTextList[-1]:
                                temppercentTumorCellsList.append(num)
                        else:
                            if len(tempintensityList) < len(tempvariantNameList) or row['testText'] != temptestTextList[-1]:
                                tempintensityList.append(num)
                if 'erica' in row['concept']:
                    isTouched = True
                    temptestNameList[-1] = temptestNameList[-1] + ' - erica'
                    tempalterationList.append('presence')
                    if row['qualifier'] in ['strong', 'weak', 'moderate', 'intermediate']:
                        tempintensityList.append(row['qualifier'])
                    else:
                        tempalterationStatusList.append(row['qualifier'])
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' in num:
                                if len(temppercentTumorCellsList) < len(variantNameList):
                                    temppercentTumorCellsList.append(num)
                            else:
                                if len(tempintensityList) == len(tempvariantNameList):
                                    tempintensityList[-1] = tempintensityList[-1] + ', ' + num
                                else:
                                    tempintensityList.append(num)
                    else:
                        if '%' in row['numeric']:
                            if len(temppercentTumorCellsList) < len(variantNameList):
                                temppercentTumorCellsList.append(row['numeric'])
                        else:
                            if len(tempintensityList) == len(tempvariantNameList):
                                tempintensityList[-1] = tempintensityList[-1] + ', ' + row['numeric']
                            else:
                                tempintensityList.append(row['numeric'])
                if row['concept'] == 'intensity':
                    isTouched = True
                    tempalterationStatusList.append(row['qualifier'])
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' in num:
                                temppercentTumorCellsList.append(num)
                            elif '/' in num:
                                tempallredScoreList.append(num)
                            else:
                                tempintensityList.append(num)
                    else:
                        if '%' in row['numeric']:
                            temppercentTumorCellsList.append(row['numeric'])
                        elif '/' in row['numeric']:
                            tempallredScoreList.append(row['numeric'])
                        else:
                            tempintensityList.append(row['numeric'])
                if row['qualifier'] == 'tested' and row['numeric'] == '' and row['concept' == ''] and 'ER' not in tempvariantNameList:
                    isTouched = True
                    tempalterationList.append('testing')
                    tempalterationStatusList.append('status: incomplete')
                if row['concept'] == 'immunostain':
                    isTouched = True
                    tempalterationList.append('immunostain')
                    tempalterationStatusList.append(row['qualifier'])
                if row['concept'] == 'immunohistochemistry' or row['concept'] == 'ihc':
                    isTouched = True
                    tempalterationList.append('immunohistochemistry')
                    tempalterationStatusList.append(row['qualifier'])
                    for num in row['numeric'].split(','):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        else:
                            tempintensityList.append(num)
                if ('positive' in ''.join(row['qualifier']) or 'negative' in ''.join(row['qualifier']) or 'equivocal' in ''.join(row['qualifier'])) and row['concept'] == '' and row['numeric'] == '':
                    isTouched = True
                    tempalterationList.append('presence')
                    tempalterationStatusList.append(row['qualifier'])
                if ('positive' in ''.join(row['qualifier']) or 'negative' in ''.join(row['qualifier']) or 'equivocal' in ''.join(row['qualifier'])) and row['concept'] == '' and row['numeric'] != '':
                    isTouched = True
                    tempalterationStatusList.append(row['qualifier'])
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' in num:
                                temppercentTumorCellsList.append(num)
                            elif '/' in num:
                                tempallredScoreList.append(num)
                            else:
                                tempintensityList.append(num)
                    else:
                        if '%' in row['numeric']:
                            temppercentTumorCellsList.append(row['numeric'])
                        elif '/' in row['numeric']:
                            tempallredScoreList.append(row['numeric'])
                        else:
                            tempintensityList.append(row['numeric'])
                # Last chance to catch allred score
                if row['concept'] == '' and '/8' in row['numeric'] and not isTouched:
                    tempallredScoreList.append(row['numeric'])

            if 'progesterone receptor' in row['biomarker']:
                if len(tempvariantNameList) == 0:
                    tempvariantNameList.append('PR')
                    normalStandardAppends()
                # Sometimes we get duplicate data for allred!
                elif '/8' in row['numeric'] and len(tempallredScoreList) > 0 and tempvariantNameList[-1] == 'PR' and row['testText'] == temptestTextList[-1]:
                    if tempallredScoreList[-1] == row['numeric']:
                        continue
                elif '%' in row['numeric'] and len(tempallredScoreList) > len(tempintensityList) and 'intensity' in row['concept']:
                    if tempvariantNameList[-1] != 'progesterone receptor':
                        normalStandardAppends()
                    pass
                elif '%' in row['numeric'] and len(temppercentTumorCellsList) > 0 and tempvariantNameList[-1] == 'PR' and row['testText'] == temptestTextList[-1]:
                    if temppercentTumorCellsList[-1] == row['numeric']:
                        continue
                elif row['testText'] != temptestTextList[-1]:
                    squareUp()
                    tempvariantNameList.append('PR')
                    normalStandardAppends()
                elif tempvariantNameList[-1] != 'PR':
                    squareUp()
                    tempvariantNameList.append('PR')
                    normalStandardAppends()
                elif len(tempalterationList) == 0 or len(tempallredScoreList) == 0:
                    squareUp()
                    tempvariantNameList.append('PR')
                    normalStandardAppends()
                elif tempalterationList[-1] != '' and row['concept'] != '' and tempallredScoreList[-1] == '':
                    squareUp()
                    tempvariantNameList.append('PR')
                    normalStandardAppends()
                # Sometimes we don't catch a '%' where we should
                if row['concept'] == '' and row['numeric'].isnumeric():
                    row['numeric'] = row['numeric'] + '%'
                    tempallredScoreList.append(row['numeric'])
                if 'allred score' in row['concept'] or ('intensity' in row['concept'] and '/8' in ''.join(row['numeric']) and len(row['numeric'].split(',')) == 1):
                    isTouched = True
                    for num in row['numeric'].split(','):
                        if '/8' in num:
                            if len(tempallredScoreList) < len(tempvariantNameList) or row['testText'] != temptestTextList[-1]:
                                tempallredScoreList.append(num)
                        elif '%' in num:
                            if len(temppercentTumorCellsList) < len(tempvariantNameList) or row['testText'] != temptestTextList[-1]:
                                temppercentTumorCellsList.append(num)
                        else:
                            if len(tempintensityList) < len(tempvariantNameList) or row['testText'] != temptestTextList[-1]:
                                tempintensityList.append(num)
                if 'prica' in row['concept']:
                    temptestNameList[-1] = temptestNameList[-1] + ' - prica'
                    tempalterationList.append('presence')
                    if row['qualifier'] in ['strong', 'weak', 'moderate', 'intermediate']:
                        tempintensityList.append(row['qualifier'])
                    else:
                        tempalterationStatusList.append(row['qualifier'])
                    isTouched = True
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' in num:
                                temppercentTumorCellsList.append(num)
                            elif '/' in num:
                                tempallredScoreList.append(num)
                            else:
                                if len(tempintensityList) == len(tempvariantNameList):
                                    tempintensityList[-1] = tempintensityList[-1] + ', ' + num
                                else:
                                    tempintensityList.append(num)
                    else:
                        if '%' in row['numeric']:
                            temppercentTumorCellsList.append(row['numeric'])
                        elif '/' in row['numeric']:
                            tempallredScoreList.append(num)
                        else:
                            if len(tempintensityList) == len(tempvariantNameList):
                                tempintensityList[-1] = tempintensityList[-1] + ', ' + num
                            else:
                                tempintensityList.append(num)
                if row['concept'] == 'intensity':
                    isTouched = True
                    tempalterationStatusList.append(row['qualifier'])
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' in num:
                                temppercentTumorCellsList.append(num)
                            elif '/' in num:
                                tempallredScoreList.append(num)
                            else:
                                tempintensityList.append(num)
                    else:
                        if '%' in row['numeric']:
                            temppercentTumorCellsList.append(row['numeric'])
                        elif '/' in row['numeric']:
                            tempallredScoreList.append(row['numeric'])
                        else:
                            tempintensityList.append(row['numeric'])
                if row['qualifier'] == 'tested' and row['numeric'] == '' and row['concept' == ''] and 'PR' not in tempvariantNameList:
                    isTouched = True
                    tempalterationList.append('testing')
                    tempalterationStatusList.append('status: incomplete')
                if row['concept'] == 'immunostain':
                    isTouched = True
                    tempalterationList.append('immunostain')
                    tempalterationStatusList.append(row['qualifier'])
                if row['concept'] == 'immunohistochemistry' or row['concept'] == 'ihc':
                    isTouched = True
                    tempalterationList.append('immunohistochemistry')
                    tempalterationStatusList.append(row['qualifier'])
                    for num in row['numeric'].split(','):
                        if '%' in num:
                            temppercentTumorCellsList.append(num)
                        else:
                            tempintensityList.append(num)
                if ('positive' in ''.join(row['qualifier']) or 'negative' in ''.join(row['qualifier']) or 'equivocal' in ''.join(row['qualifier'])) and row['concept'] == '' and row['numeric'] == '':
                    isTouched = True
                    tempalterationList.append('presence')
                    tempalterationStatusList.append(row['qualifier'])
                if ('positive' in ''.join(row['qualifier']) or 'negative' in ''.join(row['qualifier']) or 'equivocal' in ''.join(row['qualifier'])) and row['concept'] == '' and row['numeric'] != '':
                    isTouched = True
                    tempalterationStatusList.append(row['qualifier'])
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' in num:
                                temppercentTumorCellsList.append(num)
                            elif '/' in num:
                                tempallredScoreList.append(num)
                            else:
                                tempintensityList.append(num)
                    else:
                        if '%' in row['numeric']:
                            temppercentTumorCellsList.append(row['numeric'])
                        elif '/' in row['numeric']:
                            tempallredScoreList.append(row['numeric'])
                        else:
                            tempintensityList.append(row['numeric'])
                # Last chance to catch allred score
                if row['concept'] == '' and '/8' in row['numeric'] and not isTouched:
                    tempallredScoreList.append(row['numeric'])

            # These rows are supplemental for some other rows discussing intensity
            if row['biomarker'] == '' and row['concept'] == 'intensity':
                if 'estrogen receptor' in reportColumns['biomarker'][index + 1] or 'er' in reportColumns['biomarker'][index + 1].lower():
                    if len(tempvariantNameList) == 0:
                        tempvariantNameList.append('PR')
                    else:
                        if tempvariantNameList[-1] != 'PR':
                            squareUp()
                            tempvariantNameList.append('PR')
                if 'progesterone receptor' in reportColumns['biomarker'][index + 1] or 'pr' in reportColumns['biomarker'][index + 1].lower():
                    if len(tempvariantNameList) == 0:
                        squareUp()
                        tempvariantNameList.append('PR')
                    else:
                        if tempvariantNameList[-1] != 'PR':
                            squareUp()
                            tempvariantNameList.append('PR')
                isTouched = True
                normalStandardAppends()
                row['qualifier'] = row['qualifier'].replace('average, ', '')
                tempintensityList.append(row['qualifier'])

            if row['qualifier'] == 'pending':
                isTouched = True
                normalStandardAppends()
                if 'er' in row['biomarker'] or 'estrogen receptor' in row['biomarker']:
                    tempvariantNameList.append('ER')
                elif 'pr' in row['biomarker'] or 'progesterone receptor' in row['biomarker']:
                    tempvariantNameList.append('PR')
                tempalterationList.append('test')
                tempalterationStatusList.append('pending')

            if row['reportId'] == '4f76f2e3-b8e5-455b-94f5-7950d911f1a6':
                print(row['biomarker'])
                print(row['concept'])
                print(row['numeric'])
                print(row['qualifier'])
                print(row['testText'])
                print(tempallredScoreList)
                print(tempvariantNameList)
                print(tempalterationStatusList)
                #input()

        squareUp()

        for z in range(0, len(allLists)):
            allLists[z] = allLists[z] + allTempLists[z]

        if not isTouched:
            weirdBio.append(row['biomarker'])
            weirdCon.append(row['concept'])
            weirdNum.append(row['numeric'])
            weirdQua.append(row['qualifier'])
            weirdText.append(row['fullText'])

######################
######################
######################
if doBRCA:
    # We'll start with BRCA
    BRCAReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/BRCA/RawOfBRCA.csv", low_memory=False)

    # No nulls needed
    BRCAReports = BRCAReports.replace(np.nan, '', regex=True)

    # We'll want to ingest these one report at a time. First we'll get a list of all test ids
    reports = BRCAReports['reportId'].unique()

    # For each report...
    for report in reports:
        # Clear all the temp lists
        for tl in allTempLists:
            tl.clear()

        reportColumns = BRCAReports[BRCAReports['reportId'] == report]
        reportColumns.reset_index()

        # If we have a ratio of values, we'll find it.
        ratio = ''
        for index, row in reportColumns.iterrows():
            # This is for iteration
            isTouched = False

            if 'unsuccessful' in row['qualifier'] or 'qns' in row['qualifier'] or 'test not performed' in row['qualifier']:
                isTouched = True
                normalStandardAppends()
                tempvariantNameList.append('Test Failed')
                tempalterationStatusList.append(row['qualifier'])

            if 'cancelled by care provider' in row['qualifier']:
                isTouched = True
                tempvariantNameList.append('Test Failed')
                tempalterationStatusList.append('Cancelled by Care Provider')
                normalStandardAppends()

            if 'results in other report' in row['qualifier']:
                isTouched = True
                tempvariantNameList.append('Test Not Done')
                tempalterationStatusList.append('Results in Other Report')
                normalStandardAppends()

            if 'sent to other lab for testing' in row['qualifier']:
                isTouched = True
                tempvariantNameList.append('Test Not Done')
                tempalterationStatusList.append('Sent to Other Lab')
                normalStandardAppends()

            if 'normal results' in row['qualifier']:
                isTouched = True
                normalStandardAppends()
                tempvariantNameList.append(row['biomarker'])
                tempalterationList.append('deletions')
                tempalterationStatusList.append('negative')
                normalStandardAppends()
                tempvariantNameList.append(row['biomarker'])
                tempalterationList.append('duplications')
                tempalterationStatusList.append('negative')
                normalStandardAppends()
                tempvariantNameList.append(row['biomarker'])
                tempalterationList.append('mutations')
                tempalterationStatusList.append('negative')

            if len(row['biomarker'].split(',')) > 1 and 'brca' in row['biomarker']:
                isTouched = True
                normalStandardAppends()
                tempalterationList.append('mutation')
                for entry in row['biomarker'].split(','):
                    entry = entry.strip()
                    if 'brca' in entry:
                        tempvariantNameList.append(entry)
                    elif 'p.' in entry:
                        tempproteinIdList.append(entry)
                    elif 'c.' in entry:
                        tempcodingChangeList.append(entry)
                row['qualifier'] = row['qualifier'].split(',')
                row['qualifier'] = list(map(str.strip, row['qualifier']))
                row['qualifier'] = list(set(row['qualifier']))
                tempalterationStatusList.append(', '.join(row['qualifier']))

            squareUp()

        for z in range(0, len(allLists)):
            allLists[z] = allLists[z] + allTempLists[z]

        if not isTouched:
            weirdBio.append(row['biomarker'])
            weirdCon.append(row['concept'])
            weirdNum.append(row['numeric'])
            weirdQua.append(row['qualifier'])
            weirdText.append(row['fullText'])

######################
######################
######################
if doPDL1:
    # We'll start with PD-L1
    PDL1Reports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/PD-L1/RawOfPDL1.csv", low_memory=False)

    # No nulls needed
    PDL1Reports = PDL1Reports.replace(np.nan, '', regex=True)

    # We'll want to ingest these one report at a time. First we'll get a list of all test ids
    reports = PDL1Reports['reportId'].unique()

    # For each report...
    for report in reports:
        # Clear all the temp lists
        for tl in allTempLists:
            tl.clear()

        reportColumns = PDL1Reports[PDL1Reports['reportId'] == report]
        reportColumns.reset_index()

        # If we have a ratio of values, we'll find it.
        ratio = ''
        for index, row in reportColumns.iterrows():
            # This is for iteration
            isTouched = False

            if 'unsuccessful' in row['qualifier'] or 'qns' in row['qualifier'] or 'test not performed' in row['qualifier']:
                isTouched = True
                tempvariantNameList.append('Test Failed')
                normalStandardAppends()
                tempalterationStatusList.append(row['qualifier'])

            if 'sp142' in row['biomarker'] and row['concept'] == '' and len(tempvariantNameList) == 0:
                isTouched = True
                normalStandardAppends()
                tempvariantNameList.append('PD-L1')
                tempcloneList.append('sp142 clone')
                if row['numeric'] == '':
                    if 'd1%' in row['testText']:
                        temppercentTumorCellsList.append('<1%')
                else:
                    temppercentTumorCellsList.append(row['numeric'])
                tempalterationList.append('expression')
                tempalterationStatusList.append(row['qualifier'])

            if 'pd-l1' in row['biomarker'] and ('expression' in row['concept'] or 'proportion score' in row['concept'] or 'intensity' in row['concept'] or 'ihc' in row['concept']
                                                or 'intensity' in row['concept']):
                isTouched = True

                if '[' in row['numeric']:
                    row['numeric'] = row['numeric'].replace("[", '').replace(']', '').replace("'", '')

                if len(tempvariantNameList) == 0:
                    tempvariantNameList.append('PD-L1')
                    normalStandardAppends()
                    for item in row['biomarker'].split(','):
                        if 'clone' in item:
                            tempcloneList.append(item)

                elif 'clone' in row['biomarker'] and len(tempcloneList) < len(tempvariantNameList):
                    for item in row['biomarker'].split(','):
                        if 'clone' in item:
                            tempcloneList.append(item)

                elif 'clone' in row['biomarker'] and len(tempcloneList) == len(tempvariantNameList) and len(tempcloneList) > 0:
                    tempvariantNameList.append('PD-L1')
                    normalStandardAppends()
                    for item in row['biomarker'].split(','):
                        if 'clone' in item:
                            tempcloneList.append(item)

                for item in row['concept'].split(','):
                    if 'expression' in item and (len(tempalterationList) == 0 or tempalterationList[-1] != 'expression'):
                        tempalterationList.append('expression')
                        tempalterationStatusList.append(row['qualifier'])
                    elif ('ihc' in item or 'immunohistochemistry' in item or 'intensity' in item) and 'expression' not in row['concept'] and (
                            len(tempalterationList) == 0 or tempalterationList[-1] != 'expression'):
                        tempalterationList.append('expression')
                        tempalterationStatusList.append(row['qualifier'])

                for item in row['numeric'].split(','):
                    if 'tumor positive' in item and len(temppercentTumorCellsList) < len(tempvariantNameList):
                        temppercentTumorCellsList.append(item.split()[0])
                    elif '%' in item and '-' not in item and 'tumor positive' not in row['numeric'] and ('>' in item or '<' in item) and len(temptumorProportionScoreList) < len(tempvariantNameList):
                        temptumorProportionScoreList.append(item)
                    elif '%' in item and '-' not in item and 'tumor positive' not in row['numeric'] and len(temptumorProportionScoreList) < len(tempvariantNameList):
                        temptumorProportionScoreList.append(item)
                        if len(temppercentTumorCellsList) < len(tempvariantNameList):
                            temppercentTumorCellsList.append(item)

                if 'no pd-l1 expression' in row['testText'] and len(temppercentTumorCellsList) < len(tempvariantNameList):
                    temppercentTumorCellsList.append('0%')

        squareUp()

        for z in range(0, len(allLists)):
            allLists[z] = allLists[z] + allTempLists[z]

        if not isTouched:
            weirdBio.append(row['biomarker'])
            weirdCon.append(row['concept'])
            weirdNum.append(row['numeric'])
            weirdQua.append(row['qualifier'])
            weirdText.append(row['fullText'])

######################
######################
######################
if doHer2:
    # We'll start with Her2
    Her2Reports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/HER-2/RawOfHer2.csv", low_memory=False)

    # No nulls needed
    Her2Reports = Her2Reports.replace(np.nan, '', regex=True)

    # We'll want to ingest these one report at a time. First we'll get a list of all test ids
    reports = Her2Reports['reportId'].unique()

    # For each report...
    for report in reports:
        # Clear all the temp lists
        for tl in allTempLists:
            tl.clear()

        reportColumns = Her2Reports[Her2Reports['reportId'] == report]
        reportColumns.reset_index()

        # If we have a ratio of values, we'll find it.
        ratio = ''
        for index, row in reportColumns.iterrows():
            # This is for iteration
            isTouched = False
            row['biomarker'] = row['biomarker'].replace('her 2', 'her-2').replace('her2', 'her-2')
            # if 'equivocal' in row['testText'] and 'equivocal' not in row['qualifier'] and 'pending' not in row['qualifier']:
            #    row['qualifier'] = row['qualifier'] + ' equivocal'
            #    print(row['qualifier'])
            #    input()

            # First, and most obvious, if we have 'her-2', that's a biomarker we want
            if 'her-2' in row['biomarker']:
                # If we run into a row giving us the ratio of her-2 to centromere 17, save it and move to the next row.
                if 'centromere 17' in row['biomarker'] and 'her-2' in row['biomarker'] and 'signal' in row['concept'] and 'tested' in row['qualifier']:
                    isTouched = True
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' not in num:
                                ratio = num
                    else:
                        ratio = row['numeric']
                    continue

                # There are some that just say like "test was ordered"
                if row['numeric'] == '' and (row['qualifier'] == '' or row['qualifier'] == 'tested'):
                    if 'pending' in row['testText']:
                        tempalterationStatusList.append('pending')
                    else:
                        continue

                if row['testText'] == '':
                    row['testText'] = row['fullText']
                normalStandardAppends()
                tempvariantNameList.append('her-2')
                if 'immunohistochemistry' in row['concept'] or 'ihc' in row['concept']:
                    isTouched = True
                    tempplatformList.append('ihc')
                    if row['concept'] == 'immunohistochemistry' or row['concept'] == 'ihc':
                        tempalterationStatusList.append(row['qualifier'])
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '+' in num:
                                tempintensityList.append(num)
                            elif '%' in num:
                                temppercentTumorCellsList.append(num)
                    else:
                        if '+' in row['numeric']:
                            tempintensityList.append(row['numeric'])
                        elif '%' in row['numeric']:
                            temppercentTumorCellsList.append(row['numeric'])
                elif 'fish' in row['concept'] and 'immunostain' not in row['concept']:
                    isTouched = True
                    tempplatformList.append('fish')
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '+' in num:
                                tempintensityList.append(num)
                            elif '%' in num:
                                temppercentTumorCellsList.append(num)
                    else:
                        if '+' in row['numeric']:
                            tempintensityList.append(row['numeric'])
                        elif '%' in row['numeric']:
                            temppercentTumorCellsList.append(row['numeric'])

                if (row['concept'] == '' or (row['concept'] == 'presence' and row['numeric'] == '')) and 'pending' not in row['testText']:
                    isTouched = True
                    tempalterationList.append('presence')
                    tempalterationStatusList.append(row['qualifier'])
                if 'overexpression' in row['concept']:
                    isTouched = True
                    tempalterationList.append('overexpression')
                    tempalterationStatusList.append(row['qualifier'])
                if 'immunostain' in row['concept']:
                    isTouched = True
                    tempalterationList.append('immunostain')
                    tempalterationStatusList.append(row['qualifier'])
                    tempintensityList.append(row['numeric'])
                if 'amplification' in row['concept']:
                    isTouched = True
                    tempalterationList.append('amplification')
                    tempalterationStatusList.append(row['qualifier'])
                if 'duplication' in row['concept']:
                    isTouched = True
                    tempalterationList.append('duplication')
                    tempalterationStatusList.append(row['qualifier'])
                if row['concept'] == 'protein':
                    if 'neu' in row['biomarker']:
                        isTouched = True
                        if ',' in row['numeric']:
                            for num in row['numeric'].split(','):
                                if '%' not in num:
                                    intensityList.append(num)
                                    tempalterationStatusList.append(row['qualifier'])
                        else:
                            intensityList.append(row['numeric'])
                            tempalterationStatusList.append(row['qualifier'])

                if row['concept'] == 'signal' and row['qualifier'] == 'average':
                    isTouched = True
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' not in num:
                                tempaverageSignalList.append(num)
                    else:
                        tempaverageSignalList.append(row['numeric'])
                    if ratio != '':
                        tempsignalRatioList.append(ratio)
                squareUp()

            if 'ki-67' in row['biomarker'] or 'mib1' in row['biomarker'] or 'ki67' in row['biomarker']:
                tempvariantNameList.append('ki-67')
                tempcloneList.append('mib1')
                normalStandardAppends()
                if ',' in row['numeric']:
                    for num in row['numeric'].split(','):
                        if '+' in num:
                            tempintensityList.append(str(num))
                        elif '%' in num:
                            temppercentTumorCellsList.append(num)
                else:
                    if '+' in row['numeric']:
                        tempintensityList.append(str(row['numeric']))
                    elif '%' in row['numeric']:
                        temppercentTumorCellsList.append(row['numeric'])

                if 'overexpression' in row['concept']:
                    isTouched = True
                    tempalterationList.append('overexpression')
                    tempalterationStatusList.append(row['qualifier'])
                elif 'strong' in row['qualifier']:
                    isTouched = True
                    row['qualifier'] = row['qualifier'].replace('strong', '').strip()
                    if row['qualifier'].endswith(','):
                        row['qualifier'] = row['qualifier'][:-1]
                    if len(tempintensityList) == len(tempvariantNameList):
                        tempintensityList[-1] = tempintensityList[-1] + ", strong"
                    else:
                        tempintensityList.append('strong')
                    tempalterationStatusList.append(row['qualifier'])
                squareUp()

            if 'centromere 17' in row['biomarker']:
                tempvariantNameList.append('centromere 17')
                normalStandardAppends()
                if row['concept'] == 'signal' and row['qualifier'] == 'average':
                    isTouched = True
                    if ',' in row['numeric']:
                        for num in row['numeric'].split(','):
                            if '%' not in num:
                                tempaverageSignalList.append(num)
                    else:
                        tempaverageSignalList.append(row['numeric'])
            squareUp()

            if 'nuc ish' in row['biomarker']:
                isTouched = True
                tempvariantNameList.append('Probe Name')
                normalStandardAppends()
                tempprobeList.append(row['biomarker'])
                tempprobeNumberCellsList.append(row['numeric'])
            squareUp()

            # If we have a ratio value saved, we'll go back through the other and add the ratio to both measurements
            if ratio != '':
                for pos in range(0, find_max_list(allTempLists)):

                    if (tempvariantNameList[pos] == 'her-2' or tempvariantNameList[pos] == 'centromere 17') and tempaverageSignalList[pos] != '':
                        tempsignalRatioList[pos] = ratio

        # Sometimes we double up
        for i in range(0, len(tempplatformList)):
            if tempplatformList[i] == 'fish' and i > 0:
                same = True
                for z in range(0, len(allTempLists)):
                    if (allTempLists[z][i] != allTempLists[z][i - 1]) and (allTempLists[z][i] != 'fish'):
                        same = False
                if same:
                    for z in range(0, len(allTempLists)):
                        if allTempLists[z][i] == 'fish':
                            allTempLists[z][i - 1] = 'fish'
        for z in range(0, len(allLists)):
            allLists[z] = allLists[z] + allTempLists[z]

        if not isTouched:
            weirdBio.append(row['biomarker'])
            weirdCon.append(row['concept'])
            weirdNum.append(row['numeric'])
            weirdQua.append(row['qualifier'])
            weirdText.append(row['fullText'])

    #        if not isTouched:
    #            print(row)
    #            input()



if doCRC:
    # We'll start with CRC
    CRCeports = pd.read_csv("fileLocation.csv", low_memory=False)

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
                tempalteration = alt

            if any(x in row['biomarker'] for x in ['met', 'ret', 'ros1', 'ntrk2', 'ntrk1', 'ntrk3', 'alk', 'pms2', 'msh6', 'msh2', 'mlh1', 'braf', 'kras',' nras', 'erbb2']):
                isTouched = True
                for y in row['biomarker'].split(','):
                    if y.strip() in ['met', 'ret', 'ros1', 'ntrk2', 'ntrk1', 'ntrk3', 'alk', 'pms2', 'msh6', 'msh2', 'mlh1', 'braf', 'kras',' nras', 'erbb2'] and tempalteration != '':
                        normalStandardAppends()
                        tempvariantNameList.append(y)
                        tempalterationList.append(tempalteration)
                        tempalterationStatusList.append(row['qualifier'])

            if 'microsatellite instability' in row['biomarker']:
                if any(x in row['qualifier'] for x in ['microsatellite stable', 'pending', 'not applicable', 'unstable', 'test not performed']):
                    for y in ['microsatellite stable', 'pending', 'not applicable', 'unstable', 'test not performed']:
                        if y in row['qualifier']:
                            isTouched = True
                            normalStandardAppends()
                            tempvariantNameList.append('microsatellite instability')
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

reportIdList = allLists[0]
patientIdList = allLists[1]
variantNameList = allLists[2]
cloneList = allLists[3]
intensityList = allLists[4]
percentTumorCellsList = allLists[5]
allredScoreList = allLists[6]
probeList = allLists[7]
probeNumberCellsList = allLists[8]
averageSignalList = allLists[9]
signalRatioList = allLists[10]
alterationList = allLists[11]
alterationStatusList = allLists[12]
firstNameList = allLists[13]
middleNameList = allLists[14]
lastNameList = allLists[15]
mrnList = allLists[16]
dobList = allLists[17]
accessionNumberList = allLists[18]
testTextList = allLists[19]
testNameList = allLists[20]
percentReadsList = allLists[21]
immuneCellStainPresentList = allLists[22]
strandOrientationList = allLists[23]
clinicalSignificanceList = allLists[24]
allelicStateList = allLists[25]
exonsList = allLists[26]
proteinIdList = allLists[27]
aminoAcidChangeList = allLists[28]
codingIdList = allLists[29]
codingChangeList = allLists[30]
tumorProportionScoreList = allLists[31]
combinedPositiveScoreList = allLists[32]
alleleFrequencyList = allLists[33]
copyNumberRatioList = allLists[34]
log2CopyNumberRatioList = allLists[35]
cellFreeDnaPercentList = allLists[36]
tumorMutationBurdenScoreList = allLists[37]
tumorMutationBurdenUnitList = allLists[38]
icdCodeList = allLists[39]
ericaList = allLists[40]
pricaList = allLists[41]
platformList = allLists[42]
sampleLocationList = allLists[43]
pathologistList = allLists[44]
dateOrderedList = allLists[45]
dateReportedList = allLists[46]
copyNumberList = allLists[47]
fullTextList = allLists[48]

testTextList = list(map(str.strip, testTextList))

rawResults = pd.DataFrame(list(zip(reportIdList, patientIdList, variantNameList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList, probeNumberCellsList,
                                   averageSignalList, signalRatioList, alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionNumberList,
                                   testTextList, testNameList, percentReadsList, immuneCellStainPresentList, strandOrientationList, clinicalSignificanceList, allelicStateList, exonsList,
                                   proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList, tumorProportionScoreList, combinedPositiveScoreList, alleleFrequencyList,
                                   copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList, tumorMutationBurdenScoreList, tumorMutationBurdenUnitList, icdCodeList,
                                   ericaList, pricaList, platformList, sampleLocationList, pathologistList, dateOrderedList, dateReportedList, copyNumberList, fullTextList)),
                          columns=['reportId', 'patientId', 'variantName', 'clone', 'intensity', 'percentTumorCells', 'allredScore', 'probe', 'probeNumberCells', 'averageSignal',
                                   'signalRatio', 'alteration', 'alterationStatus', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accessionNumber', 'testText', 'testName', 'percentReads',
                                   'immuneCellStainPercent', 'strandOrientation', 'clinicalSignificance', 'allelicState', 'exons', 'proteinId', 'aminoAcidChange', 'codingId',
                                   'codingChange', 'tumorProportionScore', 'combinedPositiveScore', 'alleleFrequency', 'copyNumberRatio', 'log2CopyNumberRatio', 'cellFreeDnaPercent',
                                   'tumorMutationBurdenScore', 'tumorMutationBurdenUnit', 'icdCode', 'erica', 'prica', 'platform', 'sampleLocation', 'pathologist', 'dateOrdered',
                                   'dateReported', 'copyNumber', 'fullText'])

rawResults = rawResults.drop_duplicates()
rawResults = rawResults.reset_index()

finalResults = rawResults.copy()
del finalResults['fullText']



weirdRows = pd.DataFrame(list(zip(weirdBio, weirdCon, weirdNum, weirdQua, weirdText)), columns=['weird bio', 'weird con', 'weird num', 'weird qua', 'weird text'])
weirdRows.to_csv("~/Desktop/LatestNLP/Unstructured Results/weirdRows.csv", index=False)



UsedReports = rawResults[['reportId', 'patientId', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accessionNumber', 'testText', 'testName', 'platform', 'pathologist', 'dateOrdered',
                                   'dateReported']].drop_duplicates()
UsedReports = UsedReports.sort_values(by=['dateReported']).groupby('reportId').first().reset_index()
UsedReports["id"] = [uuid4() for i in range(UsedReports.shape[0])]

rawResults = rawResults.join(UsedReports[['reportId', 'id']].set_index(['reportId']), on = ['reportId'])

#generatedIds = pd.DataFrame.from_dict({"id": listOfReportuuid, "labreportid": listOfUsedReports})
rawReports = rawResults[['id','reportId', 'patientId', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accessionNumber', 'testText', 'testName', 'platform', 'pathologist', 'dateOrdered',
                                   'dateReported']]
rawReports = rawReports.rename(columns={'dateReported': 'reportDate', 'dateOrdered': 'orderDate', 'pathologist': 'orderingProviderName'})

rawReports['testName'] = rawReports['testName'].fillna('')
rawReports['reportDate'] = pd.to_datetime(rawReports['reportDate'], errors='coerce')
rawReports['orderDate'] = pd.to_datetime(rawReports['orderDate'], errors='coerce')
rawReportsGrouped = rawReports.groupby(['reportId']).agg(orderDate = ('orderDate', min), reportDate = ('reportDate', min), testName = ('testName', set), platformTechnologies = ('platform',set), testTexts = ('testText', set))


rawReportsGrouped['platformTechnologies'] = rawReportsGrouped['platformTechnologies'] - set([np.nan])
rawReportsGrouped['platformTechnologies'] = rawReportsGrouped.platformTechnologies.apply(lambda y: str(y) if len(y)!=0 else '')
rawReportsGrouped['testName'] = rawReportsGrouped['testName'] - set([np.nan])
rawReportsGrouped['testName'] = rawReportsGrouped.testName.apply(lambda y: str(y) if len(y)!=0 else '')


rawReportsGrouped['testTexts'] = rawReportsGrouped['testTexts'] - set([np.nan])
rawReportsGrouped['testText'] = rawReportsGrouped.testTexts.apply(lambda y: ":".join(y) if len(y)!=0 else '')
rawReportsGrouped = rawReportsGrouped.drop(columns=['testTexts']).drop_duplicates()


rawReports = rawReports[['id','reportId','patientId', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accessionNumber']].drop_duplicates().join( rawReportsGrouped.reset_index().set_index(['reportId']), on = ['reportId'])
rawReports['datasourceid'] = rawReports['reportId'] + ":" + rawReports['testName'] + ":" + str(rawReports['reportDate'])
rawReports['labreportid'] = rawReports['reportId']
rawReports['labName'] = 'Unknown Lab'
rawResults = rawResults.rename(columns={'id': "molecularreportid"})


rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/MolecularBiomarkersBreast.csv", index=False, na_rep='')

rawReports.to_csv("~/Desktop/LatestNLP/Unstructured Results/ReportsProcessedBreast.csv", index=False)

allFiles = list(set(reportIdList))

randomReports = random.sample(allFiles, 50)

sampleFiles = rawResults[rawResults['reportId'].isin(randomReports)]

listOfUsedReports = []
for index, row in sampleFiles.iterrows():
    id = row['reportId']
    if id not in listOfUsedReports:
        listOfUsedReports.append(id)
        repName = "outputLocation" + id + '.txt'
        text_file = open(repName, "w")
        n = text_file.write(row['fullText'])
        text_file.close()

del sampleFiles['fullText']
sampleFiles.to_csv("sampleLocation.csv", index=False)