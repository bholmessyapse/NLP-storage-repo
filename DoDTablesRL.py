import pandas as pd
import numpy as np
# For regex
from datetime import datetime
from lifelines import KaplanMeierFitter
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.evaluate import mcnemar

patientsMinusPSJH = pd.read_csv("/Users/bholmes/Desktop/NDI/SquareAllPatients/patientsMinusPSJHExpanded.csv", low_memory=False)
# The UPDATED DoD 5-category Data was produced by Daniel and myself - it's a benchmark for the patients who came back from NDI (not the ones that had no match!)
#sensitivitySheet = pd.read_csv("/Users/bholmes/Desktop/NDI/SquareAllPatients/sheetsWithNoDups.csv", low_memory=False)
sensitivitySheet = pd.read_csv("/Users/bholmes/Desktop/NDI/SquareAllPatients/finalSheet2.csv", low_memory=False)
sensitivitySheet = sensitivitySheet.drop_duplicates()
sensitivitySheet = sensitivitySheet.reset_index(drop=True)

# This drops the patients who have a date of death past the allowed date
sensitivitySheet = sensitivitySheet[sensitivitySheet['Datavant Deceased Status'].notna()]
sensitivitySheet = sensitivitySheet.reset_index(drop=True)

# The metastatic IDs are a list of control IDs for metastatic patients - this comes from RStudio.
allMetastaticIds = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/allMetastaticIds.csv", low_memory=False)
# The ForDate file is a list of all the patients that NDI sent back that they were able to match.
featureFrame = syapseData = pd.read_csv("/Users/bholmes/Desktop/NDI/FromScratch/ForDate.txt", sep='|', low_memory=False)

raceSexAge = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/RaceSexAgeNonMetriq.csv", low_memory=False)
tumorType = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/TumorType.csv", low_memory=False)

patientIdToRecordId = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/patientIdToRecordId.csv", low_memory=False)
patientIdToRecordId = patientIdToRecordId.drop_duplicates()
patientIdToRecordId = patientIdToRecordId.reset_index(drop=True)

allPatientInfo = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/AllPatientInfo.csv", low_memory=False)
allPatientInfo = allPatientInfo.drop(columns=['Unnamed: 0'])

allPatientInfo['ndi_code_race'] = allPatientInfo['ndi_code_race'].map({0: "Asian/Pacific Islander", 1: "White", 2: "Black or African American", 3: "American Indian or Alaska Native", 9: "Unknown"})
allPatientInfo['ndi_code_sex'] = allPatientInfo['ndi_code_sex'].map({1: "Male", 2: "Female", 9: "Unknown"})
allPatientInfo['yearOfDeath'] = allPatientInfo['ndi_yearofbirth'] + allPatientInfo['ndi_ageatdeath']
allPatientInfo = allPatientInfo.rename(columns={"ndi_code_sex": "sex", "ndi_code_race": "race", "ndi_diagnosisyear": "diagnosisyear", "ndi_yearofbirth": "yearofbirth", "ndi_ageatdeath": "ageatdeath"})
allPatientInfo = allPatientInfo.sort_values(['ndi_controlid', 'diagnosisyear'])
allPatientInfo = allPatientInfo.drop_duplicates(subset=['ndi_controlid'], keep='last')
allPatientInfo = allPatientInfo.reset_index(drop=True)

# Now let's get income level by zip - 'patientid' and 'postalcode' are what we want from the patient one
addressInfo = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/Zips.csv", low_memory=False)
addressInfo.sort_values(by=['patientid'], inplace=True)
addressInfo = addressInfo.drop_duplicates(subset='patientid', keep='first')
zipIncome = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/income_by_zip.tsv", sep="\t", low_memory=False)
addressInfo['postalcode'] = addressInfo['postalcode'].astype('str')
zipIncome['Zip'] = zipIncome['Zip'].astype('str')
zipIncome['Median'] = zipIncome['Median'].str.replace(',','')
zipIncome['Median'] = zipIncome['Median'].astype('int')


def remove_dash(x):
    x = x.split('-')
    x = x[0]
    return x
addressInfo['postalcode'] = addressInfo['postalcode'].apply(remove_dash)

addressInfo = addressInfo.merge(zipIncome, left_on='postalcode', right_on='Zip', how='left')
addressInfo['patientid'] = addressInfo['patientid'].str.replace('-', '')

#print(addressInfo[['postalcode', 'Zip', 'Median', 'Pop']])

######################################################################
# One of the things we're gonna do is take out MA from the waterfall
# We'll need the status, and the time difference in days
notCountingMAStatus = []
notCountingMADate = []
NDIDeceasedDoD = []

sensitivitySheet = sensitivitySheet.reset_index()

for x in range(0, len(sensitivitySheet)):
    if sensitivitySheet['SEER deceased status'][x] == "DEAD" or sensitivitySheet['Datavant Deceased Status'][x] == "DEAD" or sensitivitySheet['Tumor Registry Deceased Status'][x] == "DEAD" or \
        sensitivitySheet['EMR Deceased Status'][x] == "DEAD":
        notCountingMAStatus.append('Dead')
    else:
        notCountingMAStatus.append('Alive')
    if sensitivitySheet['Tumor Registry Date Of Death'][x] and sensitivitySheet['Tumor Registry Date Of Death'][x] is not np.nan:
        notCountingMADate.append(sensitivitySheet['Tumor Registry Date Of Death'][x])
    elif sensitivitySheet['SEER date of death'][x] and sensitivitySheet['SEER date of death'][x] is not np.nan:
        notCountingMADate.append(sensitivitySheet['SEER date of death'][x])
    elif sensitivitySheet['EMR Date of Death'][x] and sensitivitySheet['EMR Date of Death'][x] is not np.nan:
        notCountingMADate.append(sensitivitySheet['EMR Date of Death'][x])
    elif sensitivitySheet['Datavant Date of Death'][x] and sensitivitySheet['Datavant Date of Death'][x] is not np.nan:
        notCountingMADate.append(sensitivitySheet['Datavant Date of Death'][x])
    else:
        notCountingMADate.append('0')
    if sensitivitySheet['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Dead' and sensitivitySheet['NDI DoD'][x]:
        NDIDeceasedDoD.append(sensitivitySheet['NDI DoD'][x])
    else:
        NDIDeceasedDoD.append('0')

notCountingMADateDiff = []
notCountingMAVsNDI = []

    # Now change the date formats and get their difference + the status difference
for x in range(0, len(notCountingMADate)):
    if notCountingMADate[x] == '0':
        pass
    else:
        if '-' in notCountingMADate[x]:
            date = datetime.strptime(notCountingMADate[x], '%Y-%m-%d')
            notCountingMADate[x] = date
        elif '/' in notCountingMADate[x]:
            date = datetime.strptime(notCountingMADate[x], '%m/%d/%Y')
            notCountingMADate[x] = date
    if NDIDeceasedDoD[x] == '0':
        pass
    else:
        if '-' in NDIDeceasedDoD[x]:
            date = datetime.strptime(NDIDeceasedDoD[x], '%Y-%m-%d')
            NDIDeceasedDoD[x] = date
        elif '/' in NDIDeceasedDoD[x]:
            date = datetime.strptime(NDIDeceasedDoD[x], '%m/%d/%Y')
            NDIDeceasedDoD[x] = date
    if notCountingMADate[x] != '0' and NDIDeceasedDoD[x] != '0':
        notCountingMADateDiff.append(abs((notCountingMADate[x] - NDIDeceasedDoD[x]).days))
    else:
        notCountingMADateDiff.append(np.nan)
    if sensitivitySheet['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Dead' and notCountingMAStatus[x] == 'Dead':
        notCountingMAVsNDI.append('TP')
    elif sensitivitySheet['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Dead' and notCountingMAStatus[x] == 'Alive':
        notCountingMAVsNDI.append('FN')
    elif sensitivitySheet['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Alive' and notCountingMAStatus[x] == 'Alive':
        notCountingMAVsNDI.append('TN')
    elif sensitivitySheet['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Alive' and notCountingMAStatus[x] == 'Dead':
        notCountingMAVsNDI.append('FP')
    else:
        print(sensitivitySheet['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x])
        print(notCountingMAStatus[x])
        print(x)
        input()

sensitivitySheet['Rolled Up Syapse View Without MA Date Diff'] = notCountingMADateDiff
sensitivitySheet['Rolled Up Syapse View Without MA Vs NDI'] = notCountingMAVsNDI

# Now let's get the survival time for KM curves

sensitivitySheet = pd.merge(sensitivitySheet, allPatientInfo, left_on='control Id', right_on='ndi_controlid', how='left')

yearsSurvival = []
conditionOrNot = []
for x in range(0, len(sensitivitySheet)):
    if sensitivitySheet['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Alive':
        # Filter out ones we can't find matches for
        if not 2020 - sensitivitySheet['diagnosisyear'][x] > 0:
            yearsSurvival.append(999)
            conditionOrNot.append(999)
            continue
        else:
            yearsSurvival.append(2020 - sensitivitySheet['diagnosisyear'][x])
        conditionOrNot.append(0)
    else:
        if '-' in sensitivitySheet['NDI DoD'][x]:
            date = datetime.strptime(sensitivitySheet['NDI DoD'][x], '%Y-%m-%d').year
        else:
            date = datetime.strptime(sensitivitySheet['NDI DoD'][x], '%m/%d/%Y').year
        numberSurvived = date - sensitivitySheet['diagnosisyear'][x]
        if numberSurvived < 0:
            numberSurvived = 0
        yearsSurvival.append(numberSurvived)
        #print(numberSurvived)
        conditionOrNot.append(1)

sensitivitySheet['conditionOrNot'] = conditionOrNot
sensitivitySheet['yearsSurvival'] = yearsSurvival

sensitivitySheet = sensitivitySheet[sensitivitySheet['conditionOrNot'] != 999]

#
#====================================================================================
# OK! First let's get patients minus the ones from PSJH - this will be our baseline going forwards
sensitivityMinusPSJH = sensitivitySheet[(sensitivitySheet['control Id'].isin(patientsMinusPSJH['patient_id']))]
sensitivityMinusPSJH = sensitivityMinusPSJH.drop_duplicates()
sensitivityMinusPSJH = sensitivityMinusPSJH.reset_index(drop=True)


# Leaving this part in so I know how I got the datavant IDs later!
patientIdToRecordId = patientIdToRecordId.drop_duplicates()
patientIdToRecordId = patientIdToRecordId.reset_index(drop=True)
sensitivityMinusPSJH = pd.merge(sensitivityMinusPSJH, patientIdToRecordId, how='left', left_on='control Id', right_on='patient_id')
#sensitivityJustIds = sensitivityMinusPSJHDatavant['recordid']
#sensitivityJustIds = sensitivityJustIds.drop_duplicates()
#sensitivityJustIds.to_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/DatavantPatientIds.csv", index=False)

# But now we've got the SOURCE of datavant, so let's get that
datavantIds = pd.read_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/DatavantSource.csv", low_memory=False)
datavantIds = datavantIds.drop_duplicates()
datavantIds = datavantIds.reset_index(drop=True)
sensitivityMinusPSJH = sensitivityMinusPSJH.merge(datavantIds, left_on='recordid', right_on='id', how='left')


#datavantSource = datavantSource.reset_index(drop=True)
#datavantSource['syapse id'] = datavantSource['syapse id'].str.replace('-','')
#datavantSource = datavantSource.merge(patientIdToRecordId, left_on='syapse id', right_on='recordid', how='left')

SSAvsNdi = []
SSADoD = []
ObitVsNdi = []
ObitDoD = []
SSAActualDoD = []
ObitActualDoD = []
neitherVsNdi = []
neitherDoD = []
neitherActualDoD = []

sensitivityMinusPSJH = sensitivityMinusPSJH.drop(columns=['Unnamed: 0'])
sensitivityMinusPSJH = sensitivityMinusPSJH.drop_duplicates()
sensitivityMinusPSJH = sensitivityMinusPSJH.reset_index(drop=True)

for x in range(0, len(sensitivityMinusPSJH['datasourcetype'])):
    neither = True
    if sensitivityMinusPSJH['datasourcetype'][x] is not np.nan:
        if 'OBIT' in sensitivityMinusPSJH['datasourcetype'][x]:
            ObitVsNdi.append(sensitivityMinusPSJH['2. Datavant vs. NDI'][x])
            ObitDoD.append(sensitivityMinusPSJH['2. Datavant DoD Agreement'][x])
            ObitActualDoD.append(sensitivityMinusPSJH['Datavant Date of Death'][x])
            neither = False
        else:
            if sensitivityMinusPSJH['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Alive':
                ObitVsNdi.append('TN')
                ObitDoD.append(np.nan)
                ObitActualDoD.append(np.nan)
            elif sensitivityMinusPSJH['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Dead':
                ObitVsNdi.append('FN')
                ObitDoD.append(np.nan)
                ObitActualDoD.append(np.nan)
        if 'SSA' in sensitivityMinusPSJH['datasourcetype'][x]:
            SSAvsNdi.append(sensitivityMinusPSJH['2. Datavant vs. NDI'][x])
            SSADoD.append(sensitivityMinusPSJH['2. Datavant DoD Agreement'][x])
            SSAActualDoD.append(sensitivityMinusPSJH['Datavant Date of Death'][x])
            neither = False
        else:
            if sensitivityMinusPSJH['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Alive':
                SSAvsNdi.append('TN')
                SSADoD.append(np.nan)
                SSAActualDoD.append(np.nan)
            elif sensitivityMinusPSJH['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Dead':
                SSAvsNdi.append('FN')
                SSADoD.append(np.nan)
                SSAActualDoD.append(np.nan)

        if neither:
            neitherVsNdi.append(sensitivityMinusPSJH['2. Datavant vs. NDI'][x])
            neitherDoD.append(sensitivityMinusPSJH['2. Datavant DoD Agreement'][x])
            neitherActualDoD.append(sensitivityMinusPSJH['Datavant Date of Death'][x])
        else:
            neitherVsNdi.append(np.nan)
            neitherDoD.append(np.nan)
            neitherActualDoD.append(np.nan)
    else:
        if sensitivityMinusPSJH['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Alive':
            SSAvsNdi.append('TN')
            SSADoD.append(np.nan)
            SSAActualDoD.append(np.nan)
            ObitVsNdi.append('TN')
            ObitDoD.append(np.nan)
            ObitActualDoD.append(np.nan)
        elif sensitivityMinusPSJH['NDI Gold Standard Vital Status \n(Derived from columns I and J)'][x] == 'Dead':
            SSAvsNdi.append('FN')
            SSADoD.append(np.nan)
            SSAActualDoD.append(np.nan)
            ObitVsNdi.append('FN')
            ObitDoD.append(np.nan)
            ObitActualDoD.append(np.nan)

        neitherVsNdi.append(np.nan)
        neitherDoD.append(np.nan)
        neitherActualDoD.append(np.nan)

sensitivityMinusPSJH['2a. Obit vs. NDI'] = ObitVsNdi
sensitivityMinusPSJH['2a. Obit DoD Agreement'] = ObitDoD
sensitivityMinusPSJH['2b. SSA vs. NDI'] = SSAvsNdi
sensitivityMinusPSJH['2b. SSA DoD Agreement'] = SSADoD
sensitivityMinusPSJH['Obit Date of Death'] = ObitActualDoD
sensitivityMinusPSJH['SSA Date of Death'] = SSAActualDoD

# Now let's work on metastatic vs not patients
listOfMetastaticIds = allMetastaticIds['x']
sensitivityOfMetastatic = sensitivityMinusPSJH[sensitivityMinusPSJH['control Id'].isin(listOfMetastaticIds)]
sensitivityOfNonMetastatic = sensitivityMinusPSJH[~sensitivityMinusPSJH['control Id'].isin(listOfMetastaticIds)]

# Now for race/sex/age - race first
#featureFrameWithDemos = featureFrame.merge(raceSexAge, left_on='control_number_11', right_on='ndi_controlid', how='left')
featureFrameIds = featureFrame[['control_number_11', 'PROBABILISTIC_SCORE_34']]
featureFrameSorted = featureFrameIds.sort_values(by=['PROBABILISTIC_SCORE_34'])
featureFrameSorted = featureFrameSorted.drop_duplicates(subset='control_number_11', keep="last")
featureFrameSorted.reset_index(drop=True)
sensitivityMinusPSJH = sensitivityMinusPSJH.merge(featureFrameSorted, left_on='control Id', right_on='control_number_11', how='left')
sensitivityMinusPSJH = sensitivityMinusPSJH.drop_duplicates()
sensitivityMinusPSJH = sensitivityMinusPSJH.reset_index(drop=True)

sensitivityOfWhitePatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['race'] == 'White')]
sensitivityOfBlackPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['race'] == 'Black or African American')]

sensitivityOfAsianPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['race'] == 'Asian/Pacific Islander')]
sensitivityOfFirstNationParents = sensitivityMinusPSJH[(sensitivityMinusPSJH['race'] == 'American Indian or Alaska Native')]
sensitivityOfUnknownPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['race'] == 'Unknown')]

sensitivityOfWhitePatients.to_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/WhiteP.csv", index=False)
sensitivityOfBlackPatients.to_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/BlackP.csv", index=False)

sensitivityOfKnownPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['PROBABILISTIC_SCORE_34'] >= 28)]
sensitivityLowerCutoff = sensitivityMinusPSJH
sensitivityLowerCutoff.drop_duplicates()
sensitivityLowerCutoff = sensitivityLowerCutoff.reset_index(drop=True)

#sensitivityLowerCutoff = sensitivityMinusPSJH[(sensitivityMinusPSJH['race'] != 'Unknown') & (sensitivityMinusPSJH['sex'] != 'Unknown')]
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'FP'), '1. SEER vs. NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'FP'),'2. Datavant vs. NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['2a. Obit vs. NDI'] == 'FP'),'2a. Obit vs. NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['2b. SSA vs. NDI'] == 'FP'),'2b. SSA vs. NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['4. Manual Abstraction vs. NDI'] == 'FP'),'4. Manual Abstraction vs. NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'FP'),'5. EMR vs. NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'FP'),'6. Hospital Registries vs. NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['7. Rolled up Syapse View vs. NDI'] == 'FP'),'7. Rolled up Syapse View vs. NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['Rolled Up Syapse View Without MA Vs NDI'] == 'FP'),'Rolled Up Syapse View Without MA Vs NDI'] = 'TP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'TN'), '1. SEER vs. NDI'] = 'FN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'TN'),'2. Datavant vs. NDI'] = 'FN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['2a. Obit vs. NDI'] == 'TN'),'2a. Obit vs. NDI'] = 'FN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['2b. SSA vs. NDI'] == 'TN'),'2b. SSA vs. NDI'] = 'FN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['4. Manual Abstraction vs. NDI'] == 'TN'),'4. Manual Abstraction vs. NDI'] = 'FN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'TN'),'5. EMR vs. NDI'] = 'FN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'TN'),'6. Hospital Registries vs. NDI'] = 'FN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['7. Rolled up Syapse View vs. NDI'] == 'TN'),'7. Rolled up Syapse View vs. NDI'] = 'FN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] >= 27) & (sensitivityLowerCutoff['Rolled Up Syapse View Without MA Vs NDI'] == 'TN'),'Rolled Up Syapse View Without MA Vs NDI'] = 'FN'

sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'TP'), '1. SEER vs. NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'TP'),'2. Datavant vs. NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['2a. Obit vs. NDI'] == 'TP'),'2a. Obit vs. NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['2b. SSA vs. NDI'] == 'TP'),'2b. SSA vs. NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['4. Manual Abstraction vs. NDI'] == 'TP'),'4. Manual Abstraction vs. NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'TP'),'5. EMR vs. NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'TP'),'6. Hospital Registries vs. NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['7. Rolled up Syapse View vs. NDI'] == 'TP'),'7. Rolled up Syapse View vs. NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['Rolled Up Syapse View Without MA Vs NDI'] == 'TP'),'Rolled Up Syapse View Without MA Vs NDI'] = 'FP'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'FN'), '1. SEER vs. NDI'] = 'TN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'FN'),'2. Datavant vs. NDI'] = 'TN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['2a. Obit vs. NDI'] == 'FN'),'2a. Obit vs. NDI'] = 'TN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['2b. SSA vs. NDI'] == 'FN'),'2b. SSA vs. NDI'] = 'TN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['4. Manual Abstraction vs. NDI'] == 'FN'),'4. Manual Abstraction vs. NDI'] = 'TN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'FN'),'5. EMR vs. NDI'] = 'TN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'FN'),'6. Hospital Registries vs. NDI'] = 'TN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['7. Rolled up Syapse View vs. NDI'] == 'FN'),'7. Rolled up Syapse View vs. NDI'] = 'TN'
sensitivityLowerCutoff.loc[(sensitivityLowerCutoff['PROBABILISTIC_SCORE_34'] < 27) & (sensitivityLowerCutoff['Rolled Up Syapse View Without MA Vs NDI'] == 'FN'),'Rolled Up Syapse View Without MA Vs NDI'] = 'TN'


# Then sex
sensitivityOfMalePatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['sex'] == 'Male')]
sensitivityOfFemalePatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['sex'] == 'Female')]
sensitivityOfGenderMissingPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['sex'] == 'Unknown')]

# Then age
sensitivityMinusPSJH['age'] = sensitivityMinusPSJH['yearofbirth'].apply(lambda x: 2020-x)
sensitivityMinusPSJH['age'] = sensitivityMinusPSJH['age'].astype('int')
sensitivityOfBelow30Patients = sensitivityMinusPSJH[(sensitivityMinusPSJH['age'] < 30)]
sensitivityOf30to60 = sensitivityMinusPSJH[(sensitivityMinusPSJH['age'] >= 30) & (sensitivityMinusPSJH['age'] < 60)]
sensitivityOfOver60Patients = sensitivityMinusPSJH[(sensitivityMinusPSJH['age'] >= 60)]

# Un-comment for review
#sensitivityMinusPSJH.to_csv("/Users/bholmes/Desktop/NDI/GoogleSheets/InputToFinder.csv", index=False)

# We're getting tumor type - that means we need tumors by control ID
tumorType['patientid'] = tumorType['patientid'].str.replace('-', '')
tumorsById = tumorType.merge(patientIdToRecordId, left_on='patientid', right_on='recordid', how='left')
#print(Counter(tumorsById['tumortype']))
#print(tumorsById.columns)
#input()
NSCLCHistologies = ["Verrucous carcinoma, NOS", "Papillary squamous cell carcinoma", "Papillary squamous cell carcinoma, non-invasive", "Squamous carcinoma", "Squamous cell carcinoma, NOS", "Squamous cell carcinoma NOS", "Squamous cell carcinoma", "Squamous cell carcinoma, metastatic, NOS", "Squamous cell carcinoma, keratinizing, NOS", "Invasive squamous cell carcinoma, keratinizing", "Squamous cell carcinoma, large cell, keratinizing", "Squamous cell carcinoma, nonkeratinizing, NOS", "Squamous cell carcinoma, large cell, nonkeratinizing, NOS", "Squamous cell carcinoma, large cell", "Squamous cell carcinoma, small cell, nonkeratinizing", "Invasive squamous cell carcinoma, non-keratinizing", "Squamous cell carcinoma, adenoid", "Squamous cell carcinoma, pseudoglandular", "Squamous cell carcinoma, microinvasive", "Squamous cell carcinoma with horn formation", "Basaloid squamous cell carcinoma", "Invasive squamous cell carcinoma, basaloid", "Squamous cell carcinoma, clear cell type", "Adenocarcinoma, NOS", "Adenocarcinoma NOS", "Adenocarcinoma", "Adenocarcinoma, metastatic, NOS", "Scirrhous adenocarcinoma", "Superficial spreading adenocarcinoma", "Adenocarcinoma, intestinal type", "Adenocarcinoma intestinal type", "Basal cell adenocarcinoma", "Solid carcinoma, NOS", "Solid carcinoma NOS", "Bronchiolo-alveolar adenocarcinoma, NOS", "Bronchiolo-alveolar carcinoma, NOS", "Bronchiolar adenocarcinoma", "Bronchiolar carcinoma", "Alveolar adenocarcinoma", "Bronchiolo-alveolar carcinoma, non-mucinous", "Bronchiolo-alveolar carcinoma non-mucinous", "Bronchiolo-alveolar carcinoma, mucinous", "Bronchio-alveolar carcinoma, mucinous", "Bronchiolo-alveolar carcinoma, mixed mucinous and non-mucinous", "Bronchio-alveolar carcinoma, mixed mucinous and non-mucinous", "Bronchiolo-alveolar carcinoma, indeterminate type", "Bronchiolo-alveolar carcinoma; type II pneumocyte", "Adenocarcinoma with mixed subtypes", "Adenocarcinoma combined with other types of carcinoma ", "Minimally invasive adenocarcinoma, Nonmucinous", "Minimally invasive adenocarcinoma, Mucinous", "Papillary adenocarcinoma, NOS", "Papillary adenocarcinoma NOS", "Micropapillary carcinoma, NOS", "Clear cell adenocarcinoma, NOS ", "Clear cell carcinoma", "Mixed cell adenocarcinoma", "Fetal adenocarcinoma", "Mucinous cystadenocarcinoma, NOS", "Colloid adenocarcinoma", "Mucinous adenocarcinoma", "Mucous adenocarcinoma", "Mucinous carcinoma", "Mucin-producing adenocarcinoma", "Mucin-secreting adenocarcinoma", "Signet ring cell carcinoma", "Signet ring cell adenocarcinoma", "Adenocarcinoma with squamous metaplasia", "Adenocarcinoma with cartilaginous and osseous metaplasia", "Adenocarcinoma with cartilaginous metaplasia", "Adenocarcinoma with spindle cell metaplasia", "Adenocarcinoma with neuroendocrine differentiation", "Carcinoma with neuroendocrine differentiation", "Hepatoid adenocarcinoma ", "Mixed invasive mucinous and non-mucinous adenocarcinoma", "Oxyphilic adenocarcinoma", "Oncocytic adenocarcinoma", "Acinar cell carcinoma", "Acinar adenocarcinoma ", "Acinar carcinoma", "Invasive adenocarcinoma, predominant subtype cannot be determined (explain)", "Adenosquamous carcinoma", "Mixed adenocarcinoma and squamous cell carcinoma", "Large cell carcinoma, NOS", "Large cell carcinoma NOS", "Large cell neuroendocrine carcinoma", "Combined large cell neuroendocrine carcinoma (LCNEC and other non-small cell component)", "Large cell carcinoma with rhabdoid phenotype", "Basaloid carcinoma ", "Pleomorphic carcinoma ", "Giant cell and spindle cell carcinoma", "Giant cell carcinoma", "Spindle cell carcinoma, NOS", "Squamous cell carcinoma, spindle cell", "Squamous cell carcinoma, sarcomatoid", "Pseudosarcomatous carcinoma", "Sarcomatoid carcinoma", "Carcinoma with osteoclast-like giant cells", "Pulmonary blastoma", "Malignant tumor, giant cell type", "Malignant tumor, spindle cell type ", "Carcinosarcoma, NOS", "NUT carcinoma", "Lymphoepithelial carcinoma ", "Malignant tumor, clear cell type ", "Non-small cell carcinoma"]
SCLCHistologies = ["Small cell carcinoma", "Oat cell carcinoma", "Combined small cell carcinoma"]

#tumortype has the tumors we want. patient_id has the control id
sensitivityOfLungCancerPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(tumorsById[tumorsById['tumortype'] == 'Respiratory: Lung and bronchus']['patient_id']))]
sensitivityOfNSCLCLungCancer = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(tumorsById[(tumorsById['tumortype'] == 'Respiratory: Lung and bronchus') & (tumorType['histology'].isin(NSCLCHistologies))]['patient_id']))]
sensitivityOfSCLCLungCancer = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(tumorsById[(tumorsById['tumortype'] == 'Respiratory: Lung and bronchus') & (tumorType['histology'].isin(SCLCHistologies))]['patient_id']))]
sensitivityOfAMLPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(tumorsById[tumorsById['tumortype'] == 'Leukemia: Acute myeloid leukemia']['patient_id']))]
sensitivityOfAllCRCPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(tumorsById[tumorsById['tumortype'] == 'GI: Colon']['patient_id']))]
sensitivityOfAllBreastPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(tumorsById[tumorsById['tumortype'] == 'Breast']['patient_id']))]
sensitivityOfMetastaticBreastPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(tumorsById[(tumorsById['tumortype'] == 'Breast') & (sensitivityMinusPSJH['control Id'].isin(listOfMetastaticIds))]['patient_id']))]
sensitivityOfAdvancedCRCPatients = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(tumorsById[(tumorsById['tumortype'] == 'GI: Colon') & (sensitivityMinusPSJH['control Id'].isin(listOfMetastaticIds))]['patient_id']))]

# We're getting median income and postal code too
addressWithId = addressInfo.merge(patientIdToRecordId, left_on='patientid', right_on='recordid', how='left')
sensitivityOfNAPost = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(addressWithId[addressWithId['Median'].isnull()]['patient_id']))]
sensitivityOfBelow30k = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(addressWithId[addressWithId['Median'] < 30000]['patient_id']))]
sensitivityOf30to60K = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(addressWithId[(addressWithId['Median'] >= 30000) & (addressWithId['Median'] < 60000)]['patient_id']))]
sensitivityOf60to100K = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(addressWithId[(addressWithId['Median'] >= 60000) & (addressWithId['Median'] < 100000)]['patient_id']))]
sensitivityOf100to185K = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(addressWithId[(addressWithId['Median'] >= 100000) & (addressWithId['Median'] < 185000)]['patient_id']))]
sensitivityOf185kUp = sensitivityMinusPSJH[(sensitivityMinusPSJH['control Id'].isin(addressWithId[(addressWithId['Median'] >= 185000)]['patient_id']))]

# And some lower cutoff subgroups
sensitivityLowerCutoff['age'] = sensitivityLowerCutoff['yearofbirth'].apply(lambda x: 2020-x)
sensitivityLowerCutoff['age'] = sensitivityLowerCutoff['age'].astype('int')
sensitivityOfMetastaticLower = sensitivityLowerCutoff[sensitivityLowerCutoff['control Id'].isin(listOfMetastaticIds)]
sensitivityOfWhiteLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['race'] == 'White')]
sensitivityOfBlackLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['race'] == 'Black or African American')]
sensitivityOfAsianLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['race'] == 'Asian/Pacific Islander')]
sensitivityOfFirstNationLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['race'] == 'American Indian or Alaska Native')]
sensitivityOfUnknownLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['race'] == 'Unknown')]
sensitivityOfMaleLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['sex'] == 'Male')]
sensitivityOfFemaleLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['sex'] == 'Female')]
sensitivityOfGenderMissingLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['sex'] == 'Unknown')]
sensitivityOfBelow30Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] < 30)]
sensitivityOf30to60Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 30) & (sensitivityLowerCutoff['age'] < 60)]

sensitivityOf10Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] < 10)]
sensitivityOf10to20Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 10) & (sensitivityLowerCutoff['age'] < 20)]
sensitivityOf20to30Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 20) & (sensitivityLowerCutoff['age'] < 30)]
sensitivityOf30to40Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 30) & (sensitivityLowerCutoff['age'] < 40)]
sensitivityOf40to50Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 40) & (sensitivityLowerCutoff['age'] < 50)]
sensitivityOf50to60Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 50) & (sensitivityLowerCutoff['age'] < 60)]
sensitivityOf60to70Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 60) & (sensitivityLowerCutoff['age'] < 70)]
sensitivityOf70to80Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 70) & (sensitivityLowerCutoff['age'] < 80)]
sensitivityOf80to90Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 80) & (sensitivityLowerCutoff['age'] < 90)]
sensitivityOf90to100Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 90) & (sensitivityLowerCutoff['age'] < 100)]
sensitivityOf100Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 100)]

addressWithId.sort_values(by=['Median'], inplace=True)
addressWithId.drop_duplicates(subset='patient_id', keep="first")
addressWithId.reset_index()

sensitivityOfOver60Lower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 60)]
sensitivityOfNonMetastaticLower = sensitivityLowerCutoff[~sensitivityLowerCutoff['control Id'].isin(listOfMetastaticIds)]
sensitivityOfNAPostLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(addressWithId[addressWithId['Median'].isnull()]['patient_id']))]
sensitivityOfBelow30kLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(addressWithId[addressWithId['Median'] < 30000]['patient_id']))]
sensitivityOf30to60KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(addressWithId[(addressWithId['Median'] >= 30000) & (addressWithId['Median'] < 60000)]['patient_id']))]
sensitivityOf60to100KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(addressWithId[(addressWithId['Median'] >= 60000) & (addressWithId['Median'] < 100000)]['patient_id']))]
sensitivityOf100to185KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(addressWithId[(addressWithId['Median'] >= 100000) & (addressWithId['Median'] < 185000)]['patient_id']))]
sensitivityOf185kUpLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(addressWithId[(addressWithId['Median'] >= 185000)]['patient_id']))]


sensitivityOf10KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] < 10000)]
sensitivityOf10to20KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 10000) & (sensitivityLowerCutoff['age'] < 20000)]
sensitivityOf20to30KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 20000) & (sensitivityLowerCutoff['age'] < 30000)]
sensitivityOf30to40KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 30000) & (sensitivityLowerCutoff['age'] < 40000)]
sensitivityOf40to50KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 40000) & (sensitivityLowerCutoff['age'] < 50000)]
sensitivityOf50to60KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 50000) & (sensitivityLowerCutoff['age'] < 60000)]
sensitivityOf60to70KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 60000) & (sensitivityLowerCutoff['age'] < 70000)]
sensitivityOf70to80KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 70000) & (sensitivityLowerCutoff['age'] < 80000)]
sensitivityOf80to90KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 80000) & (sensitivityLowerCutoff['age'] < 90000)]
sensitivityOf90to100KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 90000) & (sensitivityLowerCutoff['age'] < 100000)]
sensitivityOf100KLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 100000)]

sensitivityOfLungCancerLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(tumorsById[tumorsById['tumortype'] == 'Respiratory: Lung and bronchus']['patient_id']))]
sensitivityOfNSCLCLungCancerLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(tumorsById[(tumorsById['tumortype'] == 'Respiratory: Lung and bronchus') & (tumorType['histology'].isin(NSCLCHistologies))]['patient_id']))]
sensitivityOfSCLCLungCancerLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(tumorsById[(tumorsById['tumortype'] == 'Respiratory: Lung and bronchus') & (tumorType['histology'].isin(SCLCHistologies))]['patient_id']))]
sensitivityOfAMLPatientsLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(tumorsById[tumorsById['tumortype'] == 'Leukemia: Acute myeloid leukemia']['patient_id']))]
sensitivityOfAllCRCLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(tumorsById[tumorsById['tumortype'] == 'GI: Colon']['patient_id']))]
sensitivityOfAllBreastLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(tumorsById[tumorsById['tumortype'] == 'Breast']['patient_id']))]
sensitivityOfMetastaticBreastLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(tumorsById[(tumorsById['tumortype'] == 'Breast') & (sensitivityLowerCutoff['control Id'].isin(listOfMetastaticIds))]['patient_id']))]
sensitivityOfAdvancedCRCLower = sensitivityLowerCutoff[(sensitivityLowerCutoff['control Id'].isin(tumorsById[(tumorsById['tumortype'] == 'GI: Colon') & (sensitivityLowerCutoff['control Id'].isin(listOfMetastaticIds))]['patient_id']))]

seerOld = sensitivityOfOver60Patients.loc[sensitivityOfOver60Patients['1. SEER vs. NDI'].notnull()]
seerYoung = sensitivityOf30to60[sensitivityOf30to60['1. SEER vs. NDI'].notnull()]

sensitivityOf30to60KLower.loc[(sensitivityOf30to60KLower['Rolled Up Syapse View Without MA Vs NDI'] == 'FN') & (sensitivityOf30to60KLower['PROBABILISTIC_SCORE_34'] < 29), 'Rolled Up Syapse View Without MA Vs NDI'] = 'TN'
sensitivityOf30to40KLower.loc[(sensitivityOf30to40KLower['Rolled Up Syapse View Without MA Vs NDI'] == 'FN') & (sensitivityOf30to40KLower['PROBABILISTIC_SCORE_34'] < 29), 'Rolled Up Syapse View Without MA Vs NDI'] = 'TN'
sensitivityOf40to50KLower.loc[(sensitivityOf40to50KLower['Rolled Up Syapse View Without MA Vs NDI'] == 'FN') & (sensitivityOf40to50KLower['PROBABILISTIC_SCORE_34'] < 29), 'Rolled Up Syapse View Without MA Vs NDI'] = 'TN'
sensitivityOf50to60KLower.loc[(sensitivityOf50to60KLower['Rolled Up Syapse View Without MA Vs NDI'] == 'FN') & (sensitivityOf50to60KLower['PROBABILISTIC_SCORE_34'] < 29), 'Rolled Up Syapse View Without MA Vs NDI'] = 'TN'

#print(len((sensitivityLowerCutoff[(sensitivityLowerCutoff['age'] >= 30) & (sensitivityLowerCutoff['age'] < 60)])))
#print(seerOld['sex'].value_counts())
#print(seerYoung['sex'].value_counts())
#print(seerOld['1. SEER vs. NDI'].value_counts())
#print(seerYoung['1. SEER vs. NDI'].value_counts())

#print(seerOld['race'].value_counts())
#print(seerYoung['race'].value_counts())
#input()

#######
# Here's where we get the values!
######
# These are the columns we'll be interested in
positivesValues = ['1. SEER vs. NDI', '2. Datavant vs. NDI', '2a. Obit vs. NDI', '2b. SSA vs. NDI', '4. Manual Abstraction vs. NDI', '5. EMR vs. NDI', '6. Hospital Registries vs. NDI', '7. Rolled up Syapse View vs. NDI', 'Rolled Up Syapse View Without MA Vs NDI']
graphValues = ['SEER date of death', 'Datavant Date of Death', 'Obit Date of Death', 'SSA Date of Death', 'MA Date of Death', 'EMR Date of Death', 'Tumor Registry Date Of Death', 'Preliminary Syapse Rolled Up View of Date of Death', 'Rolled Up Syapse View Without MA Vs NDI']


datesValues = ['1. SEER DoD Agreement', '2. Datavant DoD Agreement', '2a. Obit DoD Agreement', '2b. SSA DoD Agreement', '4. Manual Abstraction DoD Agreement', '5. EMR DoD Agreement', '6. Hospital Registries DoD Agreement',
               '7. Rolled up Syapse View DoD Agreement', 'Rolled Up Syapse View Without MA Date Diff']

# Set the input dataframe here
idf = [sensitivityLowerCutoff, sensitivityOfWhiteLower, sensitivityOfBlackLower, sensitivityOfAsianLower, sensitivityOfFirstNationLower, sensitivityOfUnknownLower, sensitivityOfMaleLower,
                  sensitivityOfFemaleLower, sensitivityOfGenderMissingLower, sensitivityOfBelow30Lower, sensitivityOf30to60Lower, sensitivityOfOver60Lower, sensitivityOfMetastaticLower,
                  sensitivityOfNonMetastaticLower, sensitivityOfBelow30kLower, sensitivityOf30to60KLower, sensitivityOf60to100KLower, sensitivityOf100to185KLower,
                  sensitivityOf185kUpLower]

names = ['Overall', 'White', 'Black', 'Asian', 'American Indian', 'Unknown Race', 'Male', 'Female', 'Unknown Gender', 'Younger than 30', '30-60', '60 and older', 'Metastatic',
         'non-Metastatic', 'Less than 30k', '30-60k', '60-100k', '100-185k', 'Over 185k']

#idf = [sensitivityOf10Lower, sensitivityOf10to20Lower, sensitivityOf20to30Lower, sensitivityOf30to40Lower, sensitivityOf40to50Lower, sensitivityOf50to60Lower, sensitivityOf60to70Lower,
#       sensitivityOf70to80Lower, sensitivityOf80to90Lower, sensitivityOf90to100Lower, sensitivityOf100Lower, sensitivityOf10KLower, sensitivityOf10to20KLower, sensitivityOf20to30KLower, sensitivityOf30to40KLower, sensitivityOf40to50KLower, sensitivityOf50to60KLower, sensitivityOf60to70KLower,
#       sensitivityOf70to80KLower, sensitivityOf80to90KLower, sensitivityOf90to100KLower, sensitivityOf100KLower]

#names = ['Under 10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100', 'over 100', 'under 10k', '10k-20k', '20k-30k', '30k-40k', '40k-50k', '50k-60k',
#         '60k-70k', '70k-80k', '80k-90k', '90k-100k', 'above 100k']

#idf = [sensitivityOfLungCancerLower, sensitivityOfNSCLCLungCancerLower, sensitivityOfSCLCLungCancerLower, sensitivityOfAMLPatientsLower, sensitivityOfAllCRCLower,
#       sensitivityOfAllBreastLower, sensitivityOfMetastaticBreastLower, sensitivityOfAdvancedCRCLower]
#names = ['Lung', 'NSCLC Lung', 'SCLC Lung', 'AML', 'All CRC', 'All Breast', 'Metastatic Breast', 'Advanced CRC']

#idf = [sensitivityOfBelow30kLower, sensitivityOf30to60KLower, sensitivityOf60to100KLower, sensitivityOf100to185KLower, sensitivityOf185kUpLower]
#names = ['below 30', '30-60', '60-100', '100-185', '185 over']

#idf = [sensitivityLowerCutoff]
#names = ['overall']

namesPos = 0

for inputDataFrame in idf:
    print(names[namesPos])
    namesPos = namesPos + 1
    print('\n')
    totalNumber = len(sensitivityMinusPSJH)
    classNumber = len(inputDataFrame)

    allDeceased = sensitivityLowerCutoff[sensitivityLowerCutoff['1. SEER vs. NDI'] == 'TP']

    type1 = sensitivityLowerCutoff[
            (
                    (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'TP') & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'TP') |
                    (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'TP') & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'].isnull()) |
                    (sensitivityLowerCutoff['5. EMR vs. NDI'].isnull()) & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'TP')
            ) & \
            (
                    (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'TP') & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'TP') |
                    (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'TP') & (sensitivityLowerCutoff['2. Datavant vs. NDI'].isnull()) |
                    (sensitivityLowerCutoff['1. SEER vs. NDI'].isnull()) & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'TP')
            )
    ]


    type2 = sensitivityLowerCutoff[
            (
                    (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'FN') & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'FN') |
                    (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'FN') & (sensitivityLowerCutoff['2. Datavant vs. NDI'].isnull()) |
                    (sensitivityLowerCutoff['1. SEER vs. NDI'].isnull()) & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'FN') |
                    (sensitivityLowerCutoff['1. SEER vs. NDI'].isnull()) & (sensitivityLowerCutoff['2. Datavant vs. NDI'].isnull())
            ) & \
            ((sensitivityLowerCutoff['5. EMR vs. NDI'] == 'TP') | (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'TP'))]

    type3 = sensitivityLowerCutoff[
            (
                    (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'FN') & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'FN') |
                    (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'FN') & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'].isnull()) |
                    (sensitivityLowerCutoff['5. EMR vs. NDI'].isnull()) & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'FN') |
                    (sensitivityLowerCutoff['5. EMR vs. NDI'].isnull()) & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'].isnull())
            ) & \
            ((sensitivityLowerCutoff['1. SEER vs. NDI'] == 'TP') | (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'TP'))]

    type4 = sensitivityLowerCutoff[
            (
                    (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'FN') & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'FN') |
                    (sensitivityLowerCutoff['5. EMR vs. NDI'] == 'FN') & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'].isnull()) |
                    (sensitivityLowerCutoff['5. EMR vs. NDI'].isnull()) & (sensitivityLowerCutoff['6. Hospital Registries vs. NDI'] == 'FN')
            ) & \
            (
                    (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'FN') & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'FN') |
                    (sensitivityLowerCutoff['1. SEER vs. NDI'] == 'FN') & (sensitivityLowerCutoff['2. Datavant vs. NDI'].isnull()) |
                    (sensitivityLowerCutoff['1. SEER vs. NDI'].isnull()) & (sensitivityLowerCutoff['2. Datavant vs. NDI'] == 'FN')
            )]

    #print(len(type1))
    #print(len(type2))
    #print(len(type3))
    #print(len(type4))
    #input()

    for x in range(0, len(positivesValues)):
        #Our input data frame will be the one we get values from
        columnPos = positivesValues[x]
        columnDates = datesValues[x]
        print(columnPos)
        TP = len(inputDataFrame[inputDataFrame[columnPos] == 'TP'])
        TN = len(inputDataFrame[inputDataFrame[columnPos] == 'TN'])
        FP = len(inputDataFrame[inputDataFrame[columnPos] == 'FP'])
        FN = len(inputDataFrame[inputDataFrame[columnPos] == 'FN'])

        #if columnPos == 'Rolled Up Syapse View Without MA Vs NDI':
        #    FN = 547

        print('overall # -', (TP + TN + FP + FN))
        if totalNumber > 0 and classNumber > 0:
            print('percent coverage - all patients', ((TP + TN + FP + FN)/totalNumber))
            print('percent coverage - this subgroup', ((TP + TN + FP + FN)/classNumber))

        # This is for McNemar's
        tb_b = np.array([[TP, FP],
                         [FN, TN]])
        chi2, p = mcnemar(ary=tb_b, corrected=True)


        print('tp - ', str(TP))
        print('fp - ', str(FP))
        print('tn - ', str(TN))
        print('fn - ', str(FN))

        if TP == 0 and FP == 0:
            FP = 0.00000000000000000000000000001
            TP = 0.00000000000000000000000000001
        if TN == 0 and FN == 0:
            FN = 0.00000000000000000000000000001
            TN = 0.00000000000000000000000000001
        if TP == 0 and FN == 0:
            TP = 0.00000000000000000000000000001
            FN = 0.00000000000000000000000000001
        if TP == 0:
            TP = 0.00000000000000000000000000001


        print('Sensitivity - ' + str(TP/(TP+FN)))
        print('Specificity - ' + str(TN/(FP+TN)))
        print('PPV - ' + str(TP/(TP+FP)))
        print('NPV - ' + str(TN/(TN+FN)))
        oneday = len(inputDataFrame[inputDataFrame[columnDates] == 1])
        numWithExact = len(inputDataFrame[inputDataFrame[columnDates] == 0]) + len(inputDataFrame[(inputDataFrame[columnDates].isna()) & (inputDataFrame[columnPos] == 'TP')])
        print('% within 1 day - ' + str((oneday + numWithExact)/TP))
        #input()

        #print('chi-squared:', chi2)
        #print('p-value:', p)
        #print('PPV - ' + str(TP/(TP+FP)))
        #print('NPV - ' + str(TN/(TN+FN)))

        #numWithExact = len(inputDataFrame[inputDataFrame[columnDates] == 0]) + len(inputDataFrame[(inputDataFrame[columnDates].isna()) & (inputDataFrame[columnPos] == 'TP')])
        #print('# with Exact Agreement - ' + str(numWithExact))
        #try:
        #    print('% with Exact Agreement - ' + str(numWithExact / (len(inputDataFrame[inputDataFrame[columnDates].notna()]) + len(inputDataFrame[(inputDataFrame[columnDates].isna()) & (inputDataFrame[columnPos] == 'TP')]) )))
        #except:
        #    continue

        print('# within 0 day - ' + str(numWithExact))
        print('# within 1 day - ' + str(len(inputDataFrame[inputDataFrame[columnDates] == 1])))
        #print('% within 1 day - ' + str(len(inputDataFrame[inputDataFrame[columnDates] == 1]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
        print('# within 7 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 7) & (inputDataFrame[columnDates] > 1)])))
        #print('% within 7 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 7) & (inputDataFrame[columnDates] > 1)]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
        print('# within 15 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 15) & (inputDataFrame[columnDates] > 7)])))
        #print('% within 15 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 15) & (inputDataFrame[columnDates] > 7)]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
        print('# within 30 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 30) & (inputDataFrame[columnDates] > 15)])))
        #print('% within 30 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 30) & (inputDataFrame[columnDates] > 15)]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
        print('# past 30 days - ' + str(len(inputDataFrame[inputDataFrame[columnDates] > 30])))
        #print('% past 30 days - ' + str(len(inputDataFrame[inputDataFrame[columnDates] > 30]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
        #input()
        print('')
        print('')
        print('###############################')

    #graphValues = ['SEER date of death', 'Datavant Date of Death', 'Obit Date of Death', 'SSA Date of Death', 'MA Date of Death', 'EMR Date of Death', 'Tumor Registry Date Of Death',
     #              'Preliminary Syapse Rolled Up View of Date of Death', 'Rolled Up Syapse View Without MA Vs NDI']

    # And now let's get the KM Curves

    doLastPart = False

    if doLastPart:
        emfOutcomes = inputDataFrame[['EMR Date of Death', 'yearsSurvival', 'conditionOrNot', 'diagnosisyear']]
        #emfOutcomes = emfOutcomes[(inputDataFrame['EMR Date of Death'].notnull())]
        emfOutcomes = emfOutcomes.reset_index(drop=True)
        emfYearsSurvival = []
        emfConditionOrNot = []
        emfOutcomes['EMR Date of Death'] = emfOutcomes['EMR Date of Death'].fillna('-')
        for z in range(0, len(emfOutcomes)):
            if emfOutcomes['EMR Date of Death'][z] == '0' or emfOutcomes['EMR Date of Death'][z] == 0 or emfOutcomes['EMR Date of Death'][z] == '-':
                date = datetime.now().year
                emfConditionOrNot.append(0)
            elif '-' in emfOutcomes['EMR Date of Death'][z]:
                date = datetime.strptime(emfOutcomes['EMR Date of Death'][z], '%Y-%m-%d').year
                emfConditionOrNot.append(1)
            else:
                date = datetime.strptime(emfOutcomes['EMR Date of Death'][z], '%m/%d/%Y').year
                emfConditionOrNot.append(1)
            numberSurvived = date - emfOutcomes['diagnosisyear'][z]
            if numberSurvived <= 0:
                numberSurvived = 0
            if emfConditionOrNot[-1] == 1:
                emfYearsSurvival.append(numberSurvived)
            else:
                emfYearsSurvival.append(numberSurvived)
        emfOutcomes['conditionOrNot'] = emfConditionOrNot
        emfOutcomes['yearsSurvival'] = emfYearsSurvival

        registryOutcomes = inputDataFrame[['Tumor Registry Date Of Death', 'yearsSurvival', 'conditionOrNot', 'diagnosisyear']]
        #registryOutcomes = registryOutcomes[(inputDataFrame['Tumor Registry Date Of Death'].notnull())]
        registryOutcomes = registryOutcomes.reset_index(drop=True)
        registryYearsSurvival = []
        registryConditionOrNot = []
        registryOutcomes['Tumor Registry Date Of Death'] = registryOutcomes['Tumor Registry Date Of Death'].fillna('-')
        for z in range(0, len(registryOutcomes)):
            if registryOutcomes['Tumor Registry Date Of Death'][z] == '0' or registryOutcomes['Tumor Registry Date Of Death'][z] == 0 or registryOutcomes['Tumor Registry Date Of Death'][z] == '-':
                date = datetime.now().year
                registryConditionOrNot.append(0)
            elif '-' in registryOutcomes['Tumor Registry Date Of Death'][z]:
                date = datetime.strptime(registryOutcomes['Tumor Registry Date Of Death'][z], '%Y-%m-%d').year
                registryConditionOrNot.append(1)
            else:
                date = datetime.strptime(registryOutcomes['Tumor Registry Date Of Death'][z], '%m/%d/%Y').year
                registryConditionOrNot.append(1)
            numberSurvived = date - registryOutcomes['diagnosisyear'][z]
            if numberSurvived <= 0:
                numberSurvived = 0
            if registryConditionOrNot[-1] == 1:
                registryYearsSurvival.append(numberSurvived)
            else:
                registryYearsSurvival.append(numberSurvived)
        registryOutcomes['conditionOrNot'] = registryConditionOrNot
        registryOutcomes['yearsSurvival'] = registryYearsSurvival

        rollupOutcomes = inputDataFrame[['Preliminary Syapse Rolled Up View of Date of Death', 'yearsSurvival', 'conditionOrNot', 'diagnosisyear']]
        #rollupOutcomes = rollupOutcomes[(inputDataFrame['Preliminary Syapse Rolled Up View of Date of Death'].notnull())]
        #rollupOutcomes = rollupOutcomes[(inputDataFrame['EMR Date of Death'].notnull())]
        rollupOutcomes = rollupOutcomes.reset_index(drop=True)
        rollupYearsSurvival = []
        rollupConditionOrNot = []
        rollupOutcomes['Preliminary Syapse Rolled Up View of Date of Death'] = rollupOutcomes['Preliminary Syapse Rolled Up View of Date of Death'].fillna('-')
        for z in range(0, len(rollupOutcomes)):
            if rollupOutcomes['Preliminary Syapse Rolled Up View of Date of Death'][z] == '0' or rollupOutcomes['Preliminary Syapse Rolled Up View of Date of Death'][z] == 0 \
                    or rollupOutcomes['Preliminary Syapse Rolled Up View of Date of Death'][z] == '-':
                date = datetime.now().year
                rollupConditionOrNot.append(0)
            elif '-' in rollupOutcomes['Preliminary Syapse Rolled Up View of Date of Death'][z]:
                date = datetime.strptime(rollupOutcomes['Preliminary Syapse Rolled Up View of Date of Death'][z], '%Y-%m-%d').year
                rollupConditionOrNot.append(1)
            else:
                date = datetime.strptime(rollupOutcomes['Preliminary Syapse Rolled Up View of Date of Death'][z], '%m/%d/%Y').year
                rollupConditionOrNot.append(1)
            numberSurvived = date - rollupOutcomes['diagnosisyear'][z]
            if numberSurvived <= 0:
                numberSurvived = 0
            if rollupConditionOrNot[-1] == 1:
                rollupYearsSurvival.append(numberSurvived)
            else:
                rollupYearsSurvival.append(numberSurvived)
        rollupOutcomes['conditionOrNot'] = rollupConditionOrNot
        rollupOutcomes['yearsSurvival'] = rollupYearsSurvival

        #    if graphValues[x] == 'EMR Date of Death' or graphValues[x] == 'Rolled Up Syapse View Without MA Vs NDI' or graphValues[x] == 'Datavant Date of Death':
        #if graphValues[x] == 'Rolled Up Syapse View Without MA Vs NDI':
        if graphValues[x] == 'EMR Date of Death':

            print(emfOutcomes['conditionOrNot'].value_counts())
            print(rollupOutcomes['conditionOrNot'].value_counts())
            print(emfOutcomes['yearsSurvival'].value_counts())
            print(rollupOutcomes['yearsSurvival'].value_counts())
            input()


            kmf = KaplanMeierFitter()
            graphOfInterest = emfOutcomes
            kmf.fit(durations=graphOfInterest.yearsSurvival,
                    event_observed=graphOfInterest.conditionOrNot)

            kmf.plot(label= 'EMR KM Curve')
            plt.title("EMR KM Curve")
            plt.ylabel("Probability the Patient is still alive")
            plt.ylim(0.7, 0.9)
            plt.xlim(0,5)
            plt.show()
            input()

            kmf = KaplanMeierFitter()
            graphOfInterest = rollupOutcomes
            kmf.fit(durations=graphOfInterest.yearsSurvival,
                    event_observed=graphOfInterest.conditionOrNot)

            kmf.event_table
            kmf.plot(label= "Rollup KM Curve")
            plt.title("Rollup KM Curve")
            plt.ylabel("Probability the Patient is still alive")
            plt.ylim(0.7, 0.9)
            plt.xlim(0,5)
            plt.show()
            input()


            kmf = KaplanMeierFitter()
            graphOfInterest = registryOutcomes
            kmf.fit(durations=graphOfInterest.yearsSurvival,
                    event_observed=graphOfInterest.conditionOrNot)

            kmf.event_table
            kmf.plot(label= "Registry KM Curve")
            plt.title("Registry KM Curve")
            plt.ylabel("Probability the Patient is still alive")
            plt.ylim(0.7, 1)
            plt.xlim(0,5)
            plt.show()
            input()


graphOfInterest = inputDataFrame.loc[inputDataFrame['NDI DoD'].notna(),]
#kmf.fit(durations=graphOfInterest.yearsSurvival,
#        event_observed=graphOfInterest.conditionOrNot)
#
#kmf.event_table
#kmf.plot(label= 'NDI DoD')
#plt.title('NDI Date of Death')
#plt.ylabel("Probability the Patient is still alive")
#plt.ylim(0.4, 0.8)
#plt.show()