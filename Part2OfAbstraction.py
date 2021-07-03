import pandas as pd
import numpy as np
# For regex
import re
from MetaMapForLots import metamapstringoutput

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# We're standardizing to this
reportIdList = []
patientIdList = []
variantNameList = []
cloneList = []
intensityList = []
percentTumorCellsList = []
allredScoreList = []
probeList = []
probeNumberCellsList = []
averageSignalList = []
signalRatioList = []
alterationList = []
alterationStatusList = []
firstNameList = []
middleNameList = []
lastNameList = []
mrnList = []
dobList = []
accessionNumberList = []
testTextList = []
testNameList = []
platformList = []
sampleLocationList = []
pathologistList = []
dateOrderedList = []
dateReportedList = []
copyNumberList = []
alleleFrequencyList = []
percentReadsList = []
immuneCellStainPresentList = []
strandOrientationList = []
clinicalSignificanceList = []
allelicStateList = []
exonsList = []
proteinIdList = []
aminoAcidChangeList = []
codingIdList = []
codingChangeList = []
tumorProportionScoreList = []
combinedPositiveScoreList = []
alleleFrequencyList = []
copyNumberRatioList = []
log2CopyNumberRatioList = []
cellFreeDnaPercentList = []
tumorMutationBurdenScoreList = []
tumorMutationBurdenUnitList = []
icdCodeList = []
ericaList = []
pricaList = []

# These are per-test lists
repreportIdList = []
reppatientIdList = []
repvariantNameList = []
repcloneList = []
repintensityList = []
reppercentTumorCellsList = []
repallredScoreList = []
repprobeList = []
repprobeNumberCellsList = []
repaverageSignalList = []
repsignalRatioList = []
repalterationList = []
repalterationStatusList = []
repfirstNameList = []
repmiddleNameList = []
replastNameList = []
repmrnList = []
repdobList = []
repaccessionNumberList = []
reptestTextList = []
reptestNameList = []
repplatformList = []
repsampleLocationList = []
reppathologistList = []
repdateOrderedList = []
repdateReportedList = []
repcopyNumberList = []
repalleleFrequencyList = []
reppercentReadsList = []
repimmuneCellStainPresentList = []
repstrandOrientationList = []
repclinicalSignificanceList = []
repallelicStateList = []
repexonsList = []
repproteinIdList = []
repaminoAcidChangeList = []
repcodingIdList = []
repcodingChangeList = []
reptumorProportionScoreList = []
repcombinedPositiveScoreList = []
repalleleFrequencyList = []
repcopyNumberRatioList = []
replog2CopyNumberRatioList = []
reprepcellFreeDnaPercentList = []
reptumorMutationBurdenScoreList = []
reptumorMutationBurdenUnitList = []
repicdCodeList = []
repericaList = []
reppricaList = []

allLists = [reportIdList, patientIdList, variantNameList, cloneList, intensityList, percentTumorCellsList, allredScoreList, probeList, probeNumberCellsList, averageSignalList,
            signalRatioList, alterationList, alterationStatusList, firstNameList, middleNameList, lastNameList, mrnList, dobList, accessionNumberList, testTextList, testNameList,
            platformList, sampleLocationList, pathologistList, dateOrderedList, dateReportedList, copyNumberList, alleleFrequencyList, percentReadsList, immuneCellStainPresentList,
            strandOrientationList, clinicalSignificanceList, allelicStateList, exonsList, proteinIdList, aminoAcidChangeList, codingIdList, codingChangeList, tumorProportionScoreList,
            combinedPositiveScoreList, alleleFrequencyList, copyNumberRatioList, log2CopyNumberRatioList, cellFreeDnaPercentList, tumorMutationBurdenScoreList, tumorMutationBurdenUnitList,
            icdCodeList, ericaList, pricaList]

# These rows are invariant between rows in a test, and should be added every time we add a new row
def standardAppends(fReportId, fPatientId, fFirstName, fMiddleName, fLastName, fMRN, fDOB, fAccession, fTestText, fTestName, fSampleLocation, fPathologist, fDateOrdered,
                    fDateReported, fICDCode):
    reportIdList.append(fReportId)
    patientIdList.append(fPatientId)
    firstNameList.append(fFirstName)
    middleNameList.append(fMiddleName)
    lastNameList.append(fLastName)
    mrnList.append(fMRN)
    dobList.append(fDOB)
    accessionNumberList.append(fAccession)
    testTextList.append(fTestText)
    testNameList.append(fTestName)
    sampleLocationList.append(fSampleLocation)
    pathologistList.append(fPathologist)
    dateOrderedList.append(fDateOrdered)
    dateReportedList.append(fDateReported)
    icdCodeList.append(fICDCode)

# Find the longest list
def find_max_list(list):
    list_len = [len(i) for i in list]
    return max(list_len)

# Make sure everybody is as long as the longest list
def squareUp():
    maxSize = find_max_list(allLists)
    for lis in allLists:
        if lis != variantNameList:
            while len(lis) < maxSize:
                lis.append('')
        if lis == variantNameList:
            while len(lis) < maxSize:
                lis.append(variantNameList[-1])


######################
######################
######################
# We'll start with Her2
Her2Reports = pd.read_csv("/Users/bholmes/Desktop/DeleteMeSoon/BiomarkersForPhizer/RawOfHer2.csv", low_memory=False)


# No nulls needed
Her2Reports = Her2Reports.replace(np.nan, '', regex=True)


currentTestName = ''
testHold = ''
ratioValue = ''
biomsAdded = []

# We'll take one report at a time
reportIds = list(set(Her2Reports['reportId']))

for reportId in reportIds:
    reportRows = Her2Reports[Her2Reports['reportId'] == reportId]
    reportRows = reportRows.reset_index()
    repreportIdList = []
    reppatientIdList = []
    repvariantNameList = []
    repcloneList = []
    repintensityList = []
    reppercentTumorCellsList = []
    repallredScoreList = []
    repprobeList = []
    repprobeNumberCellsList = []
    repaverageSignalList = []
    repsignalRatioList = []
    repalterationList = []
    repalterationStatusList = []
    repfirstNameList = []
    repmiddleNameList = []
    replastNameList = []
    repmrnList = []
    repdobList = []
    repaccessionNumberList = []
    reptestTextList = []
    reptestNameList = []
    repplatformList = []
    repsampleLocationList = []
    reppathologistList = []
    repdateOrderedList = []
    repdateReportedList = []
    repcopyNumberList = []
    repalleleFrequencyList = []
    reppercentReadsList = []
    repimmuneCellStainPresentList = []
    repstrandOrientationList = []
    repclinicalSignificanceList = []
    repallelicStateList = []
    repexonsList = []
    repproteinIdList = []
    repaminoAcidChangeList = []
    repcodingIdList = []
    repcodingChangeList = []
    reptumorProportionScoreList = []
    repcombinedPositiveScoreList = []
    repalleleFrequencyList = []
    repcopyNumberRatioList = []
    replog2CopyNumberRatioList = []
    reprepcellFreeDnaPercentList = []
    reptumorMutationBurdenScoreList = []
    reptumorMutationBurdenUnitList = []
    repicdCodeList = []
    repericaList = []
    reppricaList = []
    ratioValue = ''
    for r in range(0, len(reportRows)):

        if ('her2' in reportRows['biomarker'][r] or 'her-2' in reportRows['biomarker'][r] or 'her 2' in reportRows['biomarker'][r]) and '17' not in reportRows['biomarker'][r]:
            repvariantNameList.append('her-2')
            # One common thing to include is the signal strength
            if 'average' in reportRows['qualifier'][r]:
                for n in reportRows['numeric'][r]:
                    if n.replace('.','').isnumeric():
                        repaverageSignalList.append(n)
                        repalterationList.append('signal strength')
                if ratioValue != '':
                    repsignalRatioList.append(ratioValue)
                    ratioValue = ''

        if 'centromere 17' in reportRows['biomarker'][r] and ('her2' not in reportRows['biomarker'][r] and 'her-2' not in reportRows['biomarker'][r] and 'her 2' not in reportRows['biomarker'][r]):
            repvariantNameList.append('centromere 17')
            if 'average' in reportRows['qualifier'][r]:
                for n in reportRows['numeric'][r]:
                    if n.replace('.','').isnumeric():
                        repaverageSignalList.append(n)
                        repalterationList.append('signal strength')
                if ratioValue != '':
                    repsignalRatioList.append(ratioValue)
                    ratioValue = ''

        if 'chromosome 17' in reportRows['biomarker'][r] and ('aneuploidy' in reportRows['concept'][r] or 'monosomy' in reportRows['concept'][r] or 'deletion' in reportRows['concept'][r]):
            repvariantNameList.append('chromosome 17')
            repaverageSignalList.append(reportRows['concept'][r])
