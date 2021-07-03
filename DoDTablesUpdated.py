import pandas as pd
import numpy as np
# For regex
import re
import regex
import NumWords
import os
import json
from NumWords import text2int
import math
from sklearn import tree
from collections import Counter
from datetime import datetime
from lifelines import KaplanMeierFitter
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.evaluate import mcnemar

# So, what we're gonna do here is: Ok actually scrap that. We're gonna produce a copy of the 'ol 5-source with the new non-matching data


nonMatchingPatients = pd.read_csv("/Users/bholmes/Desktop/NDI/FinalPatients/PatientsNotMatchedByNDIWithoutPSJH.csv", low_memory=False)

controlIds = []
patients = []
seerDoDs = []
seerDeceasedStatuses = []
MADoDs = []
MADeceasedStatuses = []
TRDoDs = []
TRDeceasedStatuses = []
EMRDoDs = []
EMRDeceasedStatuses = []
DatavantDoDs = []
DatavantDeceasedStatuses = []

patientCounter = 88696
gotEMR = False
gotMA = False
gotTR = False
for x in range(0, len(nonMatchingPatients['controlIds'])):
    if nonMatchingPatients['controlIds'][x] not in controlIds:
        if len(seerDoDs) != len(controlIds):
            seerDoDs.append('')
            seerDeceasedStatuses.append('NA')
        if len(MADoDs) != len(controlIds):
            MADoDs.append('')
            MADeceasedStatuses.append('NA')
        if len(TRDoDs) != len(controlIds):
            TRDoDs.append('')
            TRDeceasedStatuses.append('NA')
        if len(EMRDoDs) != len(controlIds):
            EMRDoDs.append('0')
            EMRDeceasedStatuses.append('ALIVE')
        if len(DatavantDoDs) != len(controlIds):
            DatavantDoDs.append('')
            DatavantDeceasedStatuses.append('ALIVE')
        controlIds.append(nonMatchingPatients['controlIds'][x])
        patients.append(patientCounter)
        patientCounter = patientCounter + 1
        gotEMR = False
        gotMA = False
        gotTR = False
    if nonMatchingPatients['sourceschema'][x] == 'ma' and not gotMA:
        MADeceasedStatuses.append(nonMatchingPatients['isdeceased'][x])
        MADoDs.append(nonMatchingPatients['deceaseddate'][x])
        gotMA = True
    elif nonMatchingPatients['sourceschema'][x] == 'pma_metriq' and not gotTR:
        TRDeceasedStatuses.append(nonMatchingPatients['isdeceased'][x])
        TRDoDs.append(nonMatchingPatients['deceaseddate'][x])
        gotTR = True
    elif not gotEMR:
        EMRDeceasedStatuses.append(nonMatchingPatients['isdeceased'][x])
        EMRDoDs.append(nonMatchingPatients['deceaseddate'][x])
        gotEMR = True

newFrame = pd.DataFrame(list(zip(controlIds, patients, seerDoDs, seerDeceasedStatuses, MADoDs, MADeceasedStatuses, TRDoDs, TRDeceasedStatuses, EMRDoDs, EMRDeceasedStatuses, DatavantDoDs, DatavantDeceasedStatuses)),
                                                            columns=['control Id', 'patient', 'SEER DoD', 'SEER Deceased Status', 'MA DoD', 'MA DeceasedStatus', 'TR DoD', 'TR Deceased Status',
                                                                     'EMR DoD', 'EMR Deceased Status', 'Datavant DoD', 'Datavant Deceased Status'])

newFrame.to_csv("~/Desktop/NDI/FinalPatients/Unmatched5-category.csv", index=False)