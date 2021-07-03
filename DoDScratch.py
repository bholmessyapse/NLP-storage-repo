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

# forDate columns
# NOTE: optional_use_data_12 has 'JV, MQ, SE, MA'
# 'last_name_1a', 'first_name_1b', 'middle_initial_1c', 'SSN_2', 'DOB_month_3a', 'DOB_day_3b', 'DOB_year_3c', 'fathers_surname_4', 'age_at_death_unit_5a', 'age_at_death_number_units_5b',
# 'sex_6', 'race_7', 'marital_status_8', 'state_of_residence_9', 'state_of_birth_10', 'control_number_11', 'optional_use_data_12', 'blank_field_13', 'state_of_death_14', 'year_of_death_14A',
# 'state_of_death_CODE_15', 'alias_indicator_16', 'death_certificate_num_17', 'DOD_month_18a', 'DOD_day_18b', 'DOD_year_18c', 'first_name_19a', 'middle_initial_19b', 'last_name_19c',
# 'fathers_surname_20', 'last_name_21', 'SSN_22', 'DOB_month_23a', 'DOB_day_23b', 'DOB_year_23c', 'age_at_death_24', 'sex_25', 'race_26', 'marital_status_27', 'state_of_residence_28',
# 'state_of_birth_29', 'blank_field_30', 'exact_match_indicator_31', 'matching_sequence_32', 'num_possible_NDI_record_33', 'PROBABILISTIC_SCORE_34', 'CLASS_CODE_35', 'STATUS_CODE_36'

# Sensitivity Sheet Columns:
#'control Id', 'patient', 'SEER date of death', 'SEER deceased status', 'MA Date of Death', 'MA Deceased Status', 'Tumor Registry Date Of Death', 'Tumor Registry Deceased Status',
# 'EMR Date of Death', 'EMR Flag for Death', 'EMR Deceased Status', 'Datavant Date of Death', 'Datavant Deceased Status', 'Preliminary Syapse Rolled Up View of Deceased Status',
# 'Preliminary Syapse Rolled Up View of Date of Death', 'NDI Match Or Not', 'NDI DoD', 'NDI % Match', 'NDI Status Code', 'NDI Gold Standard Vital Status \n(Derived from columns I and J)',
# '1. SEER vs. NDI', '2. Datavant vs. NDI', '4. Manual Abstraction vs. NDI', '5. EMR vs. NDI', '6. Hospital Registries vs. NDI', '7. Rolled up Syapse View vs. NDI',
# '1. SEER DoD Agreement', '2. Datavant DoD Agreement', '4. Manual Abstraction DoD Agreement', '5. EMR DoD Agreement', '6. Hospital Registries DoD Agreement',
# '7. Rolled up Syapse View DoD Agreement', 'Deceased according to MA', 'Deceased According to a non-MA source', 'Only Deceased in MA', '1. MA vs. SEER', '2. MA vs. Datavant Rollup',
# '5. MA vs. EMR data sampled from Jeeves', '6. MA vs. Hospital tumor registry data', 'Date of Death from HS Source', 'Date of Death from Third Party Source'

# Data Sent To NDI Columns

#'syapse_source', 'syapse_source_dod', 'ndi_lastname', 'ndi_firstname', 'ndi_middleinitial', 'ndi_ssn', 'ndi_monthofbirth', 'ndi_dayofbirth', 'ndi_yearofbirth', 'ndi_fathersurname',
#'ndi_ageunitsatdeath', 'ndi_ageatdeath', 'ndi_code_sex', 'ndi_code_race', 'ndi_code_maritalstatus', 'ndi_code_addressstate', 'ndi_stateofbirth', 'ndi_controlid', 'ndi_diagnosissource',
# 'ndi_diagnosisyear', 'ndi_optional'],

# This is a brief story about Syapse's data that was sent to NDI:

# This is the data sent from NDI back to Syapse
ndiData = pd.read_csv("/Users/bholmes/Desktop/NDI/FromScratch/ForDate.txt", sep='|', low_memory=False)
ndiMatchData = pd.read_csv("/Users/bholmes/Desktop/NDI/FromScratch/Matched-Parsed.txt", sep='\t', low_memory=False)

# Un-comment this to see the number of unique control Ids found
#controlIdsCombined = ndiData['control_number_11']
#controlIdsMatched = ndiMatchData['control_number_11']
#print(len(set(controlIdsCombined)))
#print(len(set(controlIdsMatched)))
#input()

# This is the data that Syapse sent to NDI
syapseData = pd.read_csv("/Users/bholmes/Desktop/NDI/SquareAllPatients/DataSentToNDI.csv", low_memory=False)

###################################
# I'm going to assume that a combination of name, birthday, and state of birth are unique.
# When we take the length of the unique values in 'uniqueperson', we go from 131120 down to 104557.
# That means 31362 people we sent to NDI were duplicates. However, some of them have different control IDs.
# This is because, I assume, some people had multiple MRNs
###################################

# Un-comment this section to do the first part over!

#syapseData['uniquePerson'] = syapseData['ndi_lastname'] + syapseData['ndi_firstname'] + syapseData['ndi_monthofbirth'].astype(str) + syapseData['ndi_dayofbirth'].astype(str) + syapseData['ndi_yearofbirth'].astype(str)

#print(len(syapseData['uniquePerson']))
#syapseDataUniques = syapseData['uniquePerson'].unique()
#print(len(syapseDataUniques))
#syapseData = syapseData.drop('uniquePerson', 1)

# Un-comment this to get a csv file with the names and DOBs of all the patients.
pd.options.mode.chained_assignment = None
syapseDataIDs = syapseData[['ndi_lastname', 'ndi_firstname', 'ndi_monthofbirth', 'ndi_yearofbirth', 'ndi_dayofbirth']]
syapseDataIDs['ndi_lastname'] = syapseDataIDs['ndi_lastname'].str.lower()
syapseDataIDs['ndi_firstname'] = syapseDataIDs['ndi_firstname'].str.lower()
syapseDataIDs = syapseDataIDs.drop_duplicates()
syapseDataIDs = syapseDataIDs.reset_index(drop=True)
syapseDataIDs.to_csv("~/Desktop/NDI/AllRecordsAllPatients/1) SyapseToNDI.csv", index=False)

# Now we'd like to associate whatever information we can with these patients. We're going to grab a number of fields, grouping them all together with one unique patient.

#'syapse_source', 'syapse_source_dod', 'ndi_lastname', 'ndi_firstname', 'ndi_middleinitial', 'ndi_ssn', 'ndi_monthofbirth', 'ndi_dayofbirth', 'ndi_yearofbirth', 'ndi_fathersurname',
#'ndi_ageunitsatdeath', 'ndi_ageatdeath', 'ndi_code_sex', 'ndi_code_race', 'ndi_code_maritalstatus', 'ndi_code_addressstate', 'ndi_stateofbirth', 'ndi_controlid', 'ndi_diagnosissource',
# 'ndi_diagnosisyear', 'ndi_optional'],

#sources = []
#sexes = []
#races = []
#controlids = []

#for x in range(0, len(syapseDataIDs['ndi_lastname'])):
#    print(x)
#    tempsources = []
#    tempsexes = []
#    tempraces = []
#    tempcontrolids = []
#    subsetOfLarger = syapseData[(syapseData['ndi_firstname'].str.lower() == syapseDataIDs['ndi_firstname'][x]) &
#                                (syapseData['ndi_lastname'].str.lower() == syapseDataIDs['ndi_lastname'][x]) &
#                                (syapseData['ndi_monthofbirth'] == syapseDataIDs['ndi_monthofbirth'][x]) &
#                                (syapseData['ndi_yearofbirth'] == syapseDataIDs['ndi_yearofbirth'][x])]
#    tempsources = list(set(subsetOfLarger['syapse_source'].tolist()))
#    tempsexes = list(set(subsetOfLarger['ndi_code_sex'].tolist()))
#    tempraces = list(set(subsetOfLarger['ndi_code_race'].tolist()))
#    tempcontrolids  = list(set(subsetOfLarger['ndi_controlid'].tolist()))
#    sources.append(tempsources)
#    sexes.append(tempsexes)
#    races.append(tempraces)
#    controlids.append(tempcontrolids)

#syapseDataIDs['sources'] = sources
#syapseDataIDs['races'] = races
#syapseDataIDs['controlids'] = controlids
syapseDataIDs['identifier'] = syapseDataIDs['ndi_firstname'].str.strip() + ' ' + syapseDataIDs['ndi_lastname'].str.strip() + ' ' + syapseDataIDs['ndi_yearofbirth'].astype(str) + ' ' + syapseDataIDs['ndi_monthofbirth'].astype(str)
syapseDataIDs.to_csv("~/Desktop/NDI/AllRecordsAllPatients/1) SyapseToNDI.csv", index=False)
#print("HERE")
#input()


############
# So, using the identifier, I scanned the 'patient' table in the MSMDR. Let's see how many identifiers I missed!
# Answer is like 18k. That's QUITE A NUMBER! They also don't seem to have any entries at all in the MDR.
# Follow-ups necessary.
############

sentToMSMDR = pd.read_csv("~/Desktop/NDI/AllRecordsALlPatients/1) SyapseToNDI.csv")
cameBackFromMSMDR = pd.read_csv("~/Desktop/NDI/AllRecordsAllPatients/2) MSMDR Matches.csv")

missings = sentToMSMDR[~sentToMSMDR['identifier'].isin(cameBackFromMSMDR['identifier'].tolist())]
missings.to_csv("~/Desktop/NDI/AllRecordsAllPatients/3) patientsNotMatchedByName.csv", index=False)


# Un-comment this to get a way to print out the name given a sample controlId
#for id in range(0, len(syapseData['ndi_controlid'])):
#    if syapseData.iloc[id]['ndi_controlid'] == 99650833:
#        print(syapseData.iloc[id]['ndi_firstname'])
#        print(syapseData.iloc[id]['ndi_lastname'])
#        input()

###################################
#
# Here we see something else entirely.
# 52820 of the 120000 unique control IDs sent to NDI came back with no match.
# That means they couldn't find any record of the person at all.
# This has some SERIOUS implications, and should get mixed in RIGHT NOW.
#
###################################

controlIdsSentToNDI = syapseData['ndi_controlid'].unique()
controlIdsSentBack = ndiData['control_number_11'].unique()
unmatchedIds = []

for id in controlIdsSentToNDI:
    if id not in controlIdsSentBack:
        unmatchedIds.append(id)

idsToNdi = []
idsBack = []
for i in syapseData['ndi_controlid']:
    idsToNdi.append(i)
for i in ndiData['control_number_11']:
    idsBack.append(i)

# Now let's grab all the rows of the original that had no match
indices = []
for x in range(0, len(idsToNdi)):
    if idsToNdi[x] not in idsBack:
        indices.append(x)

unmatchedSent = syapseData.iloc[indices]
unmatchedSent = unmatchedSent.drop_duplicates()

unmatchedSearchFields = unmatchedSent[['ndi_lastname', 'ndi_firstname', 'ndi_middleinitial', 'ndi_yearofbirth', 'ndi_monthofbirth', 'ndi_controlid', 'syapse_source_dod', 'ndi_code_sex', 'ndi_code_race']]
unmatchedSearchFields = unmatchedSearchFields.drop_duplicates()
#unmatchedSearchFields.to_csv("~/Desktop/NDI/SquareAllPatients/UnmatchedSentSearchFields.csv", index=False)

#unmatchedSent.to_csv("~/Desktop/NDI/SquareAllPatients/UnmatchedSent.csv", index=False)

#print(unmatchedSent.columns)