import pandas as pd
import numpy as np
# For regex

# Input dataframe contains columns with comparison values of our various sources vs NDI.
# These can take on four values: TP, FP, TN, FN for True and False Positives and Negatives
# There are also columns with the difference in days of dates of death - these can be from 0 and up - columns are ints.
inputDataFrame = pd.read_csv("~/patientFileForDoDWhitePatients.csv", low_memory=False)
standardDataFrame = pd.read_csv("~/patientFileForDoDAllPatients.csv")

# There are also dataframes containing only a subset of patients
# These include dfs with patients split up by:
# - Tumor type (Any Lung Cancer, NSCLC, SCLC, AML, All CRC, Advanced CRC, All Breast cancer, Metastatic Breast Cancer, Unknown)
# - Race (White, Black or African American, Asian / Pacific Islander, American Indian / Alaskan Native, Unknown)
# - Age (0-30, 30-60, 60 and up, Unknown)
# - Sex (Male, Female, Unknown)
# - SES (as determined by patient zip code: 0-30K, 30-60K, 60-100K, 100-185K, >185K, Unknown)
# - Metastatic Status (Metastatic, Non-Metastatic)

# We want to go column by column comparing the positive/negative status and the date agreement for our various sources.
positivesValues = ['1. SEER vs. NDI', '2. Datavant vs. NDI', '2a. Obit vs. NDI', '2b. SSA vs. NDI', '4. Manual Abstraction vs. NDI', '5. EMR vs. NDI', '6. Hospital Registries vs. NDI', '7. Rolled up Syapse View vs. NDI', 'Rolled Up Syapse View Without MA Vs NDI']
datesValues = ['1. SEER DoD Agreement', '2. Datavant DoD Agreement', '2a. Obit DoD Agreement', '2b. SSA DoD Agreement', '4. Manual Abstraction DoD Agreement', '5. EMR DoD Agreement', '6. Hospital Registries DoD Agreement',
               '7. Rolled up Syapse View DoD Agreement', 'Rolled Up Syapse View Without MA Date Diff']

for x in range(0, len(positivesValues)):
    # Total number is the overall # of patients
    # Class number is the # of patients in this 'class', AKA the group under review
    totalNumber = len(standardDataFrame.index)
    classNumber = len(inputDataFrame.index)

    # Our input data frame will be the one we get values from
    columnPos = positivesValues[x]
    columnDates = datesValues[x]
    print(columnPos)
    TP = len(inputDataFrame[inputDataFrame[columnPos] == 'TP'])
    TN = len(inputDataFrame[inputDataFrame[columnPos] == 'TN'])
    FP = len(inputDataFrame[inputDataFrame[columnPos] == 'FP'])
    FN = len(inputDataFrame[inputDataFrame[columnPos] == 'FN'])

    print('overall # -', (TP + TN + FP + FN))
    if totalNumber > 0 and classNumber > 0:
        print('percent coverage - all patients', ((TP + TN + FP + FN) / totalNumber))
        print('percent coverage - this subgroup', ((TP + TN + FP + FN) / classNumber))

    print('tp - ', str(TP))
    print('fp - ', str(FP))
    print('tn - ', str(TN))
    print('fn - ', str(FN))

    # This is to handle situations with very low patient numbers:
    # We'll to avoid dividing by 0, we'll set 0 numbers to just be very small - this will still show up as 0s
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

    print('Sensitivity - ' + str(TP / (TP + FN)))
    print('Specificity - ' + str(TN / (FP + TN)))
    print('PPV - ' + str(TP / (TP + FP)))
    print('NPV - ' + str(TN / (TN + FN)))

    # Find the number off by zero days - we're also only interested in ones where the patient is in fact deceased
    # FP will mean NDI doesn't have a DoD
    # FN will mean Syapse doesn't have a DoD
    # TN will mean neither has a DoD
    numWithExact = len(inputDataFrame[(inputDataFrame[columnDates] == 0) & (inputDataFrame[columnPos] == 'TP')]) + len(
        inputDataFrame[(inputDataFrame[columnDates].isna()) & (inputDataFrame[columnPos] == 'TP')])

    print('% within 1 day - ' + str((numWithExact + len(inputDataFrame[(inputDataFrame[columnDates] == 1) & (inputDataFrame[columnPos] == 'TP')])) / TP))
    print('# within 0 day - ' + str(numWithExact))
    print('# within 1 day - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] == 1) & (inputDataFrame[columnPos] == 'TP')])))
    print('% within 1 day - ' + str(len(inputDataFrame[inputDataFrame[columnDates] == 1]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
    print('# within 7 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 7) & (inputDataFrame[columnDates] > 1) & (inputDataFrame[columnPos] == 'TP')])))
    print('% within 7 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 7) & (inputDataFrame[columnDates] > 1)]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
    print('# within 15 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 15) & (inputDataFrame[columnDates] > 7) & (inputDataFrame[columnPos] == 'TP')])))
    print('% within 15 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 15) & (inputDataFrame[columnDates] > 7)]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
    print('# within 30 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 30) & (inputDataFrame[columnDates] > 15) & (inputDataFrame[columnPos] == 'TP')])))
    print('% within 30 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] <= 30) & (inputDataFrame[columnDates] > 15)]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
    print('# past 30 days - ' + str(len(inputDataFrame[(inputDataFrame[columnDates] > 30) & (inputDataFrame[columnPos] == 'TP')])))
    print('% past 30 days - ' + str(len(inputDataFrame[inputDataFrame[columnDates] > 30]) / len(inputDataFrame[inputDataFrame[columnDates].notna()])))
    # input()
    print('')
    print('')
    print('###############################')

    print('PPV - ' + str(TP/(TP+FP)))
    print('NPV - ' + str(TN/(TN+FN)))

    from mlxtend.evaluate import mcnemar
    tb_b = np.array([[TP, FP],
                     [FN, TN]])
    chi2, p = mcnemar(ary=tb_b, corrected=True)
    print(chi2)
