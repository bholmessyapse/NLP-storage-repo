import pandas as pd
import numpy as np


# Righto mates, cheerio whatever let's roll on this LUNG/CRC BIOMARKERS WOO

# Gonna see if I can collapse these all atta end, but for now, let's do all separate, eh?


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
    copyNumberRatioComparisonGeneList, copyNumberRatioComparisonGeneSignalList, sourcenameList, suborgList, geneList, proteinList, otherAnalyteList = ([] for i in range(56))

# These are the temporary versions we use per report
tempreportIdList, temppatientIdList, tempcloneList, tempintensityList, temppercentTumorCellsList, tempallredScoreList, tempprobeList, tempprobeNumberCellsList, \
  tempaverageSignalList, tempsignalRatioList, tempalterationList, tempalterationStatusList, tempfirstNameList, tempmiddleNameList, templastNameList, tempmrnList, tempdobList, \
  tempaccessionNumberList, temptestTextList, temptestNameList, tempplatformList, tempsampleLocationList, temppathologistList, tempdateOrderedList, tempdateReportedList, tempcopyNumberList, \
  tempalleleFrequencyList, temppercentReadsList, tempimmuneCellStainPresentList, tempstrandOrientationList, tempclinicalSignificanceList, tempallelicStateList, tempexonsList, \
  tempproteinIdList, tempaminoAcidChangeList, tempcodingIdList, tempcodingChangeList, temptumorProportionScoreList, tempcombinedPositiveScoreList, tempfullTextList, tempdatasourcetypeList,\
  tempcopyNumberRatioList, templog2CopyNumberRatioList, tempcellFreeDnaPercentList, temptumorMutationBurdenScoreList, temptumorMutationBurdenUnitList, tempicdCodeList, tempericaList, \
  temppricaList, tempcopyNumberRatioComparisonGeneList, tempcopyNumberRatioComparisonGeneSignalList, tempsourcenameList, tempSuborgList,\
    tempgeneList, tempproteinList, tempotherAnalyteList= ([] for j in range(56))

# It's also helpful to have a list of those lists, that we can iterate through.
allTempLists = [tempreportIdList, temppatientIdList, tempcloneList, tempintensityList, temppercentTumorCellsList, tempallredScoreList, tempprobeList,
                tempprobeNumberCellsList, tempaverageSignalList, tempsignalRatioList, tempalterationList, tempalterationStatusList, tempfirstNameList, tempmiddleNameList, templastNameList,
                tempmrnList, tempdobList, tempaccessionNumberList, temptestTextList, temptestNameList, temppercentReadsList, tempimmuneCellStainPresentList, tempstrandOrientationList,
                tempclinicalSignificanceList, tempallelicStateList, tempexonsList, tempproteinIdList, tempaminoAcidChangeList, tempcodingIdList, tempcodingChangeList,
                temptumorProportionScoreList, tempcombinedPositiveScoreList, tempalleleFrequencyList, tempcopyNumberRatioList, templog2CopyNumberRatioList, tempcellFreeDnaPercentList,
                temptumorMutationBurdenScoreList, temptumorMutationBurdenUnitList, tempicdCodeList, tempericaList, temppricaList, tempplatformList, tempsampleLocationList,
                temppathologistList, tempdateOrderedList, tempdateReportedList, tempcopyNumberList, tempfullTextList, tempdatasourcetypeList, tempcopyNumberRatioComparisonGeneList,
                tempcopyNumberRatioComparisonGeneSignalList, tempsourcenameList, tempSuborgList, tempgeneList, tempproteinList, tempotherAnalyteList]

allLists = [reportIdList, patientIdList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList,
                probeNumberCellsList, averageSignalList, signalRatioList, alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList,
                mrnList, dobList, accessionNumberList, testTextList, testNameList, percentReadsList, immuneCellStainPresentList, strandOrientationList,
                clinicalSignificanceList, allelicStateList, exonsList, proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList,
                tumorProportionScoreList, combinedPositiveScoreList, alleleFrequencyList, copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList,
                tumorMutationBurdenScoreList, tumorMutationBurdenUnitList, icdCodeList, ericaList, pricaList, platformList, sampleLocationList,
                pathologistList, dateOrderedList, dateReportedList, copyNumberList, fullTextList, datasourcetypeList, copyNumberRatioComparisonGeneList,
                copyNumberRatioComparisonGeneSignalList, sourcenameList, suborgList, geneList, proteinList, otherAnalyteList]

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


doHer2 = True
doPDL1 = True
doMLH = True

if doMLH:
    rowNum = 0
    sourcename = 'hfhs'
    suborg = 'Henry Ford Health System'
    pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Unstructured Results/May2021/mlh:pms:msh/TestRaw.csv", low_memory=False)
    # No nulls needed
    MLHReports = pathReports.replace(np.nan, '', regex=True)
    datasourcetype = 'Narrative'

    for index, row in MLHReports.iterrows():
        rowNum = rowNum + 1

        # If biomarker is null, skip
        #if row['biomarker'] == '':
        #    continue

        # little normalization
        if row['concept'] in ['loss, stain']:
            row['concept'] = 'loss'

        if row['concept'] == '' and any(x in row['fullText'] for x in ['intact nuclear expression of', 'preserved nuclear expression of', 'normal expression of',
                                                                       'demonstrates immunoreactivity for']):
            row['concept'] = 'expression'
            if row['qualifier'] == 'microsatellite stable':
                row['qualifier'] = 'expression, normal'

        if row['concept'] == '' and any(x in row['testText'] for x in ['and retained expression of']):
            for x in row['biomarker']:
                if x in row['testText']

        # these are discussions of the test
        if row['testText'].startswith(('determine the presence or absence of','immunohistochemical stain for')):
            continue

        # these are discussions of the test
        if any(x in row['biomarker'] for x in ['heritable', 'synaptophysin']):
            continue

        if row['concept'] in ['stain', 'mutation']:
            continue

        if 'methylated' in row['biomarker']:
            row['qualifier'] = row['qualifier'] + ', ' + 'methylated'
            row['biomarker'] = row['biomarker'].replace('methylated', '')
            while row['biomarker'].startswith((' ', ',')):
                row['biomarker'] = row['biomarker'][1:]
            for biomarker in row['biomarker'].split(', '):
                row['biomarker'] = row['biomarker'].replace(biomarker, biomarker + ' promoter')
            row['concept'] = 'expression'

        if row['concept'] in ['expression', 'loss, expression', 'normal, expression', 'loss', 'detected, methylated', 'immunohistochemistry, normal, expression'] and row['numeric'] == '':
            for bio in row['biomarker']:
                if bio.replace(' promoter', '') in ['pms2', 'msh6', 'msh2', 'mlh1']:
                    tempproteinList.append(bio)
                    tempalterationList.append('expression')
                    tempalterationStatusList.append(row['qualifier'])
                    normalStandardAppends()
                    squareUp()


        # Irrelevent
        elif not any(x in row['biomarker'] for x in ['pms2', 'msh6', 'msh2', 'mlh1']):
            continue

        else:
            print(row)
            input()

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

testTextList = list(map(str.strip, testTextList))

rawResults = pd.DataFrame(list(zip(reportIdList, patientIdList, proteinList, geneList, otherAnalyteList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList, probeNumberCellsList,
                                   averageSignalList, signalRatioList, alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionNumberList,
                                   testTextList, testNameList, percentReadsList, immuneCellStainPresentList, strandOrientationList, clinicalSignificanceList, allelicStateList, exonsList,
                                   proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList, tumorProportionScoreList, combinedPositiveScoreList, alleleFrequencyList,
                                   copyNumberRatioComparisonGeneList, copyNumberRatioComparisonGeneSignalList,
                                   copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList, tumorMutationBurdenScoreList, tumorMutationBurdenUnitList, icdCodeList,
                                   ericaList, pricaList, platformList, sampleLocationList, pathologistList, dateOrderedList, dateReportedList, copyNumberList, fullTextList, datasourcetypeList,
                                   sourcenameList, suborgList)),
                          columns=['reportId', 'patientId', 'protein', 'gene', 'otherAnalyte', 'clone', 'intensity', 'percentTumorCells', 'allredScore', 'probe', 'probeNumberCells', 'averageSignal',
                                   'signalRatio', 'alteration', 'alterationStatus', 'firstName', 'middleName', 'lastName', 'mrn', 'dob', 'accessionNumber', 'testText', 'testName', 'percentReads',
                                   'immuneCellStainPercent', 'strandOrientation', 'clinicalSignificance', 'allelicState', 'exons', 'proteinId', 'aminoAcidChange', 'codingId',
                                   'codingChange', 'tumorProportionScore', 'combinedPositiveScore', 'alleleFrequency', 'copyNumberRatioComparisonMarker', 'copyNumberRatioComparisonMarkerAverageSignal',
                                   'copyNumberRatio', 'log2CopyNumberRatio', 'cellFreeDnaPercent',
                                   'tumorMutationBurdenScore', 'tumorMutationBurdenUnit', 'icdCode', 'erica', 'prica', 'platform', 'sampleLocation', 'pathologist', 'dateOrdered',
                                   'dateReported', 'copyNumber', 'fullText', 'datasourcetype', 'sourcename', 'suborg'])

weirdResults = pd.DataFrame(list(zip(weirdBio, weirdCon, weirdNum, weirdQua, weirdText, weirdPatient)), columns=['bio', 'con', 'num', 'qual', 'text', 'patient'])

rawResults = rawResults.drop_duplicates()
rawResults = rawResults.reset_index()

finalResults = rawResults.copy()

testReference = finalResults[["reportId", 'fullText']]
testReference = testReference.drop_duplicates()
testReference = testReference.reset_index()

finalResults.drop('fullText', inplace=True, axis=1)

weirdResults = weirdResults.drop_duplicates()
weirdResults = weirdResults.reset_index()

finalResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/LungCRCBuilding.csv", index=False)
testReference.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/LungCRCTestRef.csv", index=False)
weirdResults.to_csv("~/Desktop/LatestNLP/Unstructured Results/May2021/LungCRCWeird.csv", index=False)