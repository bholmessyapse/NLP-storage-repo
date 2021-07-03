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

doLung = True

######################
######################
######################
if doLung:
    # We'll move to the next biggest - ER/PR
    LungReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/Lung/TestRawOfLung.csv", low_memory=False)

    # No nulls needed
    LungReports = LungReports.replace(np.nan, '', regex=True)

    # We'll want to ingest these one report at a time. First we'll get a list of all test ids
    reports = LungReports['reportId'].unique()

    # For each report...
    for report in reports:
        # Clear all the temp lists
        for tl in allTempLists:
            tl.clear()

        reportColumns = LungReports[LungReports['reportId'] == report]
        reportColumns.reset_index()

        # thisReportId is for when we have multiple rows important - like, if we want to keep the probe name constant
        thisReportId = ''
        thisProbe = ''
        thisProbeNumber = ''

        # Right. Here's the deal. To Facilitate a quick load of this stuff,
        # we're gonna take it row by row and leave the hard stuff for later
        # less go
        for index, row in reportColumns.iterrows():

            # We'll rename her2/neu
            if row['biomarker'] == 'her2, neu' or (row['biomarker'] == 'her2' and 'her2-neu' in row['testText']):
                row['biomarker'] = 'her2-neu'
            if row['biomarker'] == 'her-2 neu, her2/neu':
                row['biomarker'] = 'her2/neu'
            # and estrogen receptor
            if 'estrogen receptor' in row['biomarker']:
                row['biomarker'] = row['biomarker'].replace('estrogen receptor', 'er').replace('(anaplastic lymphoma kinase)-1, ', '')
            # and e-cadherin
            if 'e, cadherin' in row['biomarker']:
                row['biomarker'] = row['biomarker'].replace('e, cadherin', 'e-cadherin')

            # 'receptors' shouldn't be there
            row['biomarker'] = row['biomarker'].replace('receptors, ', '').replace('receptors', '').replace(', ae 1', '').replace(', her2/neu staining', '')
            row['concept'] = row['concept'].replace('mutations, copy number alteration', 'mutation, copy number alteration')

            # These results are set to 'expression'
            row['concept'] = row['concept'].replace('immunohistochemistry, normal, expression', 'expression').replace('normal, expression', 'expression')

            # we don't want 'assessment'
            row['concept'] = row['concept'].replace('assessment, ', '')

            # 'negative, detected' gets normalized to negative
            row['qualifier'] = row['qualifier'].replace('negative, detected', 'negative')
            row['qualifier'] = row['qualifier'].replace('positive, detected', 'positive')

            # 'results pending' is 'pending'
            row['qualifier'] = row['qualifier'].replace('results pending', 'pending')

            text = row['testText'].replace('\n', ' ').replace('over expression', 'overexpression')
            # Normalize the text please
            text = text.strip()

            # Blank out the held fields if this is a new report
            if row['reportId'] != thisReportId:
                thisProbe = ''
                thisReportId = ''
                thisProbeNumber = ''


            # These are 'fakeout' results - we just pass them
            if row['biomarker'].strip() in ['normal results', 'test', 'amp']:
                continue

            # Pending results here
            if 'pending' in row['qualifier'] or any(x in text for x in ['will be reported as an addenda', 'will be reported as addenda', 'will be performed']):
                tempvariantNameList.append(row['biomarker'])
                tempalterationList.append(row['concept'])
                tempalterationStatusList.append('pending')
                normalStandardAppends()

            elif 'overexpression' in row['concept']:
                tempvariantNameList.append(row['biomarker'])
                tempalterationList.append('overexpression')
                tempintensityList.append(row['numeric'])
                tempalterationStatusList.append(row['qualifier'])
                tempplatformList.append('ihc')
                normalStandardAppends()

            # Assuming here that this always comes in groups
            elif row['qualifier'] == 'probe used':
                thisReportId = row['reportId']
                thisProbe = row['biomarker']
                thisProbeNumber = row['numeric']
                normalStandardAppends()

            elif row['concept'] in ['amplification', 'signal']:
                tempvariantNameList.append(row['biomarker'])
                tempalterationList.append(row['concept'])
                if 'average' in row['qualifier']:
                    tempaverageSignalList.append(row['numeric'])
                elif 'ratio' in row['qualifier']:
                    tempsignalRatioList.append(row['numeric'])
                else:
                    tempalterationStatusList.append(row['qualifier'])
                if thisProbe != '':
                    tempprobeList.append(thisProbe)
                    tempprobeNumberCellsList.append(thisProbeNumber)
                tempplatformList.append('ihc')
                normalStandardAppends()

            elif row['concept'] in ['expression', 'mutation']:
                for bio in row['biomarker'].split(', '):
                    tempvariantNameList.append(bio)
                    tempalterationList.append(row['concept'])
                    tempalterationStatusList.append(row['qualifier'])
                    tempplatformList.append('ihc')
                    normalStandardAppends()

            # These have multiple concept results for each biomarker - split them all out!
            elif row['concept'] in ['mutation, copy number alteration']:
                for bio in row['biomarker'].split(', '):
                    for con in row['concept'].split(', '):
                        tempvariantNameList.append(bio)
                        tempalterationList.append(con)
                        tempalterationStatusList.append(row['qualifier'])
                        tempplatformList.append('ihc')
                        normalStandardAppends()

            # This is overall intensity as an ihc result
            elif row['concept'] in ['immunohistochemistry']:
                for bio in row['biomarker'].split(', '):
                    tempvariantNameList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append(row['qualifier'])
                    tempintensityList.append(row['numeric'])
                    tempplatformList.append('ihc')
                    normalStandardAppends()

            # Now let's get MS
            elif 'microsatellite' in row['biomarker']:
                tempalterationList.append('MSI')
                if 'unstable' in row['qualifier']:
                    tempalterationStatusList.append('MS-Unstable')
                elif 'stable' in row['qualifier']:
                    tempalterationStatusList.append('MS-Stable')
                elif 'high' in row['qualifier']:
                    tempalterationStatusList.append('MS-High')
                elif row['qualifier'] in ['positive', 'consistent with result']:
                    tempalterationStatusList.append('MS-Unstable')
                elif row['qualifier'] in ['negative']:
                    tempalterationStatusList.append('MS-Stable')
                else:
                    weirdBio.append(row['biomarker'])
                    weirdCon.append(row['concept'])
                    weirdNum.append(row['numeric'])
                    weirdQua.append(row['qualifier'])
                    weirdText.append(row['testText'])
                tempplatformList.append('ihc')
                normalStandardAppends()

            elif row['qualifier'] in ['test not performed']:
                tempvariantNameList.append(row['biomarker'])
                tempalterationStatusList.append(row['qualifier'])
                normalStandardAppends()

            else:
                weirdBio.append(row['biomarker'])
                weirdCon.append(row['concept'])
                weirdNum.append(row['numeric'])
                weirdQua.append(row['qualifier'])
                weirdText.append(row['testText'])


            squareUp()

            stanLen = len(allTempLists[0])
            for a in range(1, len(allTempLists)):
                if len(allTempLists[a]) != stanLen:
                    print(a)
                    print('here!')
                    input()

        for z in range(0, len(allLists)):
            allLists[z] = allLists[z] + allTempLists[z]


# That's that, let's combine results

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

print(len(fullTextList))
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



rawResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/MolecularBiomarkersLung.csv", index=False, na_rep='')

rawReports.to_csv("~/Desktop/LatestNLP/Unstructured Results/ReportsProcessedLung.csv", index=False)

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