import pandas as pd
import numpy as np
import random
import statsmodels.api as sm
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import urllib, json
import math

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', -1)


# Let's import our patients
df1 = pd.read_csv("~/Desktop/Hackathon/patient_2.csv", low_memory=False)
df2 = pd.read_csv("~/Desktop/Hackathon/patient_3.csv", low_memory=False)
df3 = pd.read_csv("~/Desktop/Hackathon/patient_4.csv", low_memory=False)
df4 = pd.read_csv("~/Desktop/Hackathon/patient_5.csv", low_memory=False)
df5 = pd.read_csv("~/Desktop/Hackathon/patient_new_1.csv", low_memory=False)
df6 = pd.read_csv("~/Desktop/Hackathon/patient_new2.csv", low_memory=False)
df7 = pd.read_csv("~/Desktop/Hackathon/patient_new3.csv", low_memory=False)

"""
# here are the columns
#['body_site_name', 'classification_name', 'distant_metastasis_name',
#       'pat_id', 'stage_group_name', 'stage_id', 'icd9_code', 'icd10_code',
#       'enc_start', 'facility', 'prim_enc_prov_id', 'display_name',
#       'plan_start_date', 'treatment_goal_name']

# Here's working individually
# The date is formatted like 2018-02-02T13:38:40:000-06:00
# I'm deleting everything after the '-'
# I'm stripping out the time here. We would NOT want to do that in a full implementation!

df1['enc_start'] = df1['enc_start'].apply(lambda x: x[:x.rfind('T')])
df1['enc_start'] = pd.to_datetime(df1['enc_start'], format='%Y-%m-%d')
df1['enc_start'] = df1['enc_start'].dt.normalize()
df1 = df1.sort_values(by="enc_start")
df1 = df1.reset_index()


# We're assigning encounter numbers here - first encounter is 0, second is 1, so on
patientDates = list(df1['enc_start'].unique())
encounterNumber = []
for index, row in df1.iterrows():
    encounter = patientDates.index(row['enc_start'])
    encounterNumber.append(encounter)
df1['encounter_number'] = encounterNumber

df1['encounter_gap'] = ''

# We're also going to get the time between encounters
encounterTime = [0]
if len(list(set(encounterNumber))) > 1:
    encounterNum = list(set(encounterNumber))
    lastEncounter = list(df1[df1['encounter_number'] == encounterNum[0]]['enc_start'])[0]
    for x in range(1, len(list(set(encounterNumber)))):
        date = list(df1[df1['encounter_number'] == encounterNum[x]]['enc_start'])[0]
        dateDiff = (date - lastEncounter).days / 7
        encounterTime.append(dateDiff)

for x in range(0, len(encounterTime)):
    df1.loc[df1['encounter_number'] == x, 'encounter_gap'] = encounterTime[x]

df2['enc_start'] = df2['enc_start'].apply(lambda x: x[:x.rfind('T')])
df2['enc_start'] = pd.to_datetime(df2['enc_start'], format='%Y-%m-%d')
df2['enc_start'] = df2['enc_start'].dt.normalize()
df2 = df2.sort_values(by="enc_start")
df2 = df2.reset_index()

# We're assigning encounter numbers here - first encounter is 0, second is 1, so on
patientDates = list(df2['enc_start'].unique())
encounterNumber = []
for index, row in df2.iterrows():
    encounter = patientDates.index(row['enc_start'])
    encounterNumber.append(encounter)
df2['encounter_number'] = encounterNumber

df2['encounter_gap'] = ''
# We're also going to get the time between encounters
encounterTime = [0]
if len(list(set(encounterNumber))) > 1:
    encounterNum = list(set(encounterNumber))
    lastEncounter = list(df2[df2['encounter_number'] == encounterNum[0]]['enc_start'])[0]
    for x in range(1, len(list(set(encounterNumber)))):
        date = list(df2[df2['encounter_number'] == encounterNum[x]]['enc_start'])[0]
        dateDiff = (date - lastEncounter).days / 7
        encounterTime.append(dateDiff)

for x in range(0, len(encounterTime)):
    df2.loc[df2['encounter_number'] == x, 'encounter_gap'] = encounterTime[x]

df3['enc_start'] = df3['enc_start'].apply(lambda x: x[:x.rfind('T')])
df3['enc_start'] = pd.to_datetime(df3['enc_start'], format='%Y-%m-%d')
df3['enc_start'] = df3['enc_start'].dt.normalize()
df3 = df3.sort_values(by="enc_start")
df3 = df3.reset_index()

# We're assigning encounter numbers here - first encounter is 0, second is 1, so on
patientDates = list(df3['enc_start'].unique())
encounterNumber = []
for index, row in df3.iterrows():
    encounter = patientDates.index(row['enc_start'])
    encounterNumber.append(encounter)
df3['encounter_number'] = encounterNumber
df3['encounter_gap'] = ''
# We're also going to get the time between encounters
encounterTime = [0]
if len(list(set(encounterNumber))) > 1:
    encounterNum = list(set(encounterNumber))
    lastEncounter = list(df3[df3['encounter_number'] == encounterNum[0]]['enc_start'])[0]
    for x in range(1, len(list(set(encounterNumber)))):
        date = list(df3[df3['encounter_number'] == encounterNum[x]]['enc_start'])[0]
        dateDiff = (date - lastEncounter).days / 7
        encounterTime.append(dateDiff)

for x in range(0, len(encounterTime)):
    df3.loc[df3['encounter_number'] == x, 'encounter_gap'] = encounterTime[x]

df4['enc_start'] = df4['enc_start'].apply(lambda x: x[:x.rfind('T')])
df4['enc_start'] = pd.to_datetime(df4['enc_start'], format='%Y-%m-%d')
df4['enc_start'] = df4['enc_start'].dt.normalize()
df4 = df4.sort_values(by="enc_start")
df4 = df4.reset_index()

# We're assigning encounter numbers here - first encounter is 0, second is 1, so on
patientDates = list(df4['enc_start'].unique())
encounterNumber = []
for index, row in df4.iterrows():
    encounter = patientDates.index(row['enc_start'])
    encounterNumber.append(encounter)
df4['encounter_number'] = encounterNumber
df4['encounter_gap'] = ''
# We're also going to get the time between encounters
encounterTime = [0]
if len(list(set(encounterNumber))) > 1:
    encounterNum = list(set(encounterNumber))
    lastEncounter = list(df4[df4['encounter_number'] == encounterNum[0]]['enc_start'])[0]
    for x in range(1, len(list(set(encounterNumber)))):
        date = list(df4[df4['encounter_number'] == encounterNum[x]]['enc_start'])[0]
        dateDiff = (date - lastEncounter).days / 7
        encounterTime.append(dateDiff)

for x in range(0, len(encounterTime)):
    df4.loc[df4['encounter_number'] == x, 'encounter_gap'] = encounterTime[x]

df5['enc_start'] = df5['enc_start'].apply(lambda x: x[:x.rfind('T')])
df5['enc_start'] = pd.to_datetime(df5['enc_start'], format='%Y-%m-%d')
df5['enc_start'] = df5['enc_start'].dt.normalize()
df5 = df5.sort_values(by="enc_start")
df5 = df5.reset_index()

# We're assigning encounter numbers here - first encounter is 0, second is 1, so on
patientDates = list(df5['enc_start'].unique())
encounterNumber = []
for index, row in df5.iterrows():
    encounter = patientDates.index(row['enc_start'])
    encounterNumber.append(encounter)
df5['encounter_number'] = encounterNumber
df5['encounter_gap'] = ''
# We're also going to get the time between encounters
encounterTime = [0]
if len(list(set(encounterNumber))) > 1:
    encounterNum = list(set(encounterNumber))
    lastEncounter = list(df5[df5['encounter_number'] == encounterNum[0]]['enc_start'])[0]
    for x in range(1, len(list(set(encounterNumber)))):
        date = list(df5[df5['encounter_number'] == encounterNum[x]]['enc_start'])[0]
        dateDiff = (date - lastEncounter).days / 7
        encounterTime.append(dateDiff)

for x in range(0, len(encounterTime)):
    df5.loc[df5['encounter_number'] == x, 'encounter_gap'] = encounterTime[x]

df6['enc_start'] = df6['enc_start'].apply(lambda x: x[:x.rfind('T')])
df6['enc_start'] = pd.to_datetime(df6['enc_start'], format='%Y-%m-%d')
df6['enc_start'] = df6['enc_start'].dt.normalize()
df6 = df6.sort_values(by="enc_start")
df6 = df6.reset_index()

# We're assigning encounter numbers here - first encounter is 0, second is 1, so on
patientDates = list(df6['enc_start'].unique())
encounterNumber = []
for index, row in df6.iterrows():
    encounter = patientDates.index(row['enc_start'])
    encounterNumber.append(encounter)
df6['encounter_number'] = encounterNumber
df6['encounter_gap'] = ''
# We're also going to get the time between encounters
encounterTime = [0]
if len(list(set(encounterNumber))) > 1:
    encounterNum = list(set(encounterNumber))
    lastEncounter = list(df6[df6['encounter_number'] == encounterNum[0]]['enc_start'])[0]
    for x in range(1, len(list(set(encounterNumber)))):
        date = list(df6[df6['encounter_number'] == encounterNum[x]]['enc_start'])[0]
        dateDiff = (date - lastEncounter).days / 7
        encounterTime.append(dateDiff)

for x in range(0, len(encounterTime)):
    df6.loc[df6['encounter_number'] == x, 'encounter_gap'] = encounterTime[x]

df7['enc_start'] = df7['enc_start'].apply(lambda x: x[:x.rfind('T')])
df7['enc_start'] = pd.to_datetime(df7['enc_start'], format='%Y-%m-%d')
df7['enc_start'] = df7['enc_start'].dt.normalize()
df7 = df7.sort_values(by="enc_start")
df7 = df7.reset_index()

# We're assigning encounter numbers here - first encounter is 0, second is 1, so on
patientDates = list(df7['enc_start'].unique())
encounterNumber = []
for index, row in df7.iterrows():
    encounter = patientDates.index(row['enc_start'])
    encounterNumber.append(encounter)
df7['encounter_number'] = encounterNumber
df7['encounter_gap'] = ''
# We're also going to get the time between encounters
encounterTime = [0]
if len(list(set(encounterNumber))) > 1:
    encounterNum = list(set(encounterNumber))
    lastEncounter = list(df7[df7['encounter_number'] == encounterNum[0]]['enc_start'])[0]
    for x in range(1, len(list(set(encounterNumber)))):
        date = list(df7[df7['encounter_number'] == encounterNum[x]]['enc_start'])[0]
        dateDiff = (date - lastEncounter).days / 7
        encounterTime.append(dateDiff)

for x in range(0, len(encounterTime)):
    df7.loc[df7['encounter_number'] == x, 'encounter_gap'] = encounterTime[x]

dfAll = pd.concat([df1, df2, df3, df4, df5, df6, df7])

dfAll['stage_group_name'] = dfAll['stage_group_name'].fillna('stage not given')
dfAll['display_name'] = dfAll['display_name'].fillna('medication not given')

sources = []
sinks = []
numbers = []
firstLabels = []
spacing = []
spacingY = []

df1sources = []
df1sinks = []
df1numbers = []
df1firstLabels = []
df1spacing = []
df1spacingY = []
yBase = 0

df1['stage_group_name'] = df1['stage_group_name'].fillna('stage not given')
df1['display_name'] = df1['display_name'].fillna('medication not given')
baseNum = 0
startDate = list(set(df1[df1['encounter_number'] == 0]['enc_start']))[0]
for x in list(set(df1['encounter_number'])):
    stage = ', '.join(list(set(df1[df1['encounter_number'] == x]['stage_group_name'])))
    medication = ', '.join(list(set(df1[df1['encounter_number'] == x]['display_name'])))[0:30] + '...'
    encounterGap = list(set(df1[df1['encounter_number'] == x]['encounter_gap']))[0]
    df1firstLabels.append(stage)
    df1firstLabels.append(medication)
    df1spacing.append(encounterGap)

df1firstLabels.append('last record')

today = date.today()
finalDiff = (today - startDate).days / 7
df1spacing.append(finalDiff)

for x in range(0, len(df1firstLabels) -1 ):
    df1sources.append(baseNum + x)
    df1numbers.append(1)
for x in range(1, len(df1firstLabels)):
    df1sinks.append(baseNum + x)
    df1numbers.append(1)

baseNum = baseNum + len(df1firstLabels)
df1spacingReal = []
for x in range(0, len(df1spacing) - 1 ):
    df1spacingReal.append(df1spacing[x])
    df1spacingReal.append(df1spacing[x] + 0.1)
df1spacingReal.append(df1spacing[-1])
df1spacing = df1spacingReal

for x in range(0, len(df1firstLabels)):
    df1spacingY.append(yBase)
yBase = yBase + 0.1

sources = sources + df1sources
sinks = sinks + df1sinks
numbers = numbers + df1numbers
spacing = spacing + df1spacing
firstLabels = firstLabels + df1firstLabels
spacingY = spacingY + df1spacingY

df4sources = []
df4sinks = []
df4numbers = []
df4firstLabels = []
df4spacing = []
df4spacingY = []

df4['stage_group_name'] = df4['stage_group_name'].fillna('stage not given')
df4['display_name'] = df4['display_name'].fillna('medication not given')
startDate = list(set(df4[df4['encounter_number'] == 0]['enc_start']))[0]
for x in list(set(df4['encounter_number'])):
    stage = ', '.join(list(set(df4[df4['encounter_number'] == x]['stage_group_name'])))
    medication = ', '.join(list(set(df4[df4['encounter_number'] == x]['display_name'])))[0:30] + '...'
    encounterGap = list(set(df4[df4['encounter_number'] == x]['encounter_gap']))[0]
    df4firstLabels.append(stage)
    df4firstLabels.append(medication)
    df4spacing.append(encounterGap)

df4firstLabels.append('last record')

today = date.today()
finalDiff = (today - startDate).days / 7
df4spacing.append(finalDiff)

for x in range(0, len(df4firstLabels) -1 ):
    df4sources.append(baseNum + x)
    df4numbers.append(1)
for x in range(1, len(df4firstLabels)):
    df4sinks.append(baseNum + x)
    df4numbers.append(1)

baseNum = baseNum + len(df4firstLabels)
df4spacingReal = []
for x in range(0, len(df4spacing) - 1 ):
    df4spacingReal.append(df4spacing[x])
    df4spacingReal.append(df4spacing[x] + 0.1)
df4spacingReal.append(df4spacing[-1])
df4spacing = df4spacingReal

for x in range(0, len(df4firstLabels)):
    df4spacingY.append(yBase)
yBase = yBase + 0.1


yBase = yBase + 0.2

sources = sources + df4sources
sinks = sinks + df4sinks
numbers = numbers + df4numbers
spacing = spacing + df4spacing
firstLabels = firstLabels + df4firstLabels
spacingY = spacingY + df4spacingY

df5sources = []
df5sinks = []
df5numbers = []
df5firstLabels = []
df5spacing = []
df5spacingY = []

df5['stage_group_name'] = df5['stage_group_name'].fillna('stage not given')
df5['display_name'] = df5['display_name'].fillna('medication not given')
startDate = list(set(df5[df5['encounter_number'] == 0]['enc_start']))[0]
for x in list(set(df5['encounter_number'])):
    stage = ', '.join(list(set(df5[df5['encounter_number'] == x]['stage_group_name'])))
    medication = ', '.join(list(set(df5[df5['encounter_number'] == x]['display_name'])))[0:30] + '...'
    encounterGap = list(set(df5[df5['encounter_number'] == x]['encounter_gap']))[0]
    df5firstLabels.append(stage)
    df5firstLabels.append(medication)
    df5spacing.append(encounterGap)

df5firstLabels.append('last record')

today = date.today()
finalDiff = (today - startDate).days / 7
df5spacing.append(finalDiff)

for x in range(0, len(df5firstLabels) -1 ):
    df5sources.append(baseNum + x)
    df5numbers.append(1)
for x in range(1, len(df5firstLabels)):
    df5sinks.append(baseNum + x)
    df5numbers.append(1)

baseNum = baseNum + len(df5firstLabels)
df5spacingReal = []
for x in range(0, len(df5spacing) - 1 ):
    df5spacingReal.append(df5spacing[x])
    df5spacingReal.append(df5spacing[x] + 0.1)
df5spacingReal.append(df5spacing[-1])
df5spacing = df5spacingReal

for x in range(0, len(df5firstLabels)):
    df5spacingY.append(yBase)
yBase = yBase + 0.1

sources = sources + df5sources
sinks = sinks + df5sinks
numbers = numbers + df5numbers
spacing = spacing + df5spacing
firstLabels = firstLabels + df5firstLabels
spacingY = spacingY + df5spacingY

df6sources = []
df6sinks = []
df6numbers = []
df6firstLabels = []
df6spacing = []
df6spacingY = []

df6['stage_group_name'] = df6['stage_group_name'].fillna('stage not given')
df6['display_name'] = df6['display_name'].fillna('medication not given')
startDate = list(set(df6[df6['encounter_number'] == 0]['enc_start']))[0]
for x in list(set(df6['encounter_number'])):
    stage = ', '.join(list(set(df6[df6['encounter_number'] == x]['stage_group_name'])))
    medication = ', '.join(list(set(df6[df6['encounter_number'] == x]['display_name'])))[0:30] + '...'
    encounterGap = list(set(df6[df6['encounter_number'] == x]['encounter_gap']))[0]
    df6firstLabels.append(stage)
    df6firstLabels.append(medication)
    df6spacing.append(encounterGap)

df6firstLabels.append('last record')

today = date.today()
finalDiff = (today - startDate).days / 7
df6spacing.append(finalDiff)

for x in range(0, len(df6firstLabels) - 1):
    df6sources.append(baseNum + x)
    df6numbers.append(1)
for x in range(1, len(df6firstLabels)):
    df6sinks.append(baseNum + x)
    df6numbers.append(1)

baseNum = baseNum + len(df6firstLabels)
df6spacingReal = []
for x in range(0, len(df6spacing) - 1):
    df6spacingReal.append(df6spacing[x])
    df6spacingReal.append(df6spacing[x] + 0.1)
df6spacingReal.append(df6spacing[-1])
df6spacing = df6spacingReal

for x in range(0, len(df6firstLabels)):
    df6spacingY.append(yBase)
yBase = yBase + 0.1


sources = sources + df6sources
sinks = sinks + df6sinks
numbers = numbers + df6numbers
spacing = spacing + df6spacing
firstLabels = firstLabels + df6firstLabels
spacingY = spacingY + df6spacingY

df7sources = []
df7sinks = []
df7numbers = []
df7firstLabels = []
df7spacing = []
df7spacingY = []

df7['stage_group_name'] = df7['stage_group_name'].fillna('stage not given')
df7['display_name'] = df7['display_name'].fillna('medication not given')
startDate = list(set(df7[df7['encounter_number'] == 0]['enc_start']))[0]
for x in list(set(df7['encounter_number'])):
    stage = ', '.join(list(set(df7[df7['encounter_number'] == x]['stage_group_name'])))
    medication = ', '.join(list(set(df7[df7['encounter_number'] == x]['display_name'])))[0:30] + '...'
    encounterGap = list(set(df7[df7['encounter_number'] == x]['encounter_gap']))[0]
    df7firstLabels.append(stage)
    df7firstLabels.append(medication)
    df7spacing.append(encounterGap)

df7firstLabels.append('last record')

today = date.today()
finalDiff = (today - startDate).days / 7
df7spacing.append(finalDiff)

for x in range(0, len(df7firstLabels) - 1):
    df7sources.append(baseNum + x)
    df7numbers.append(1)
for x in range(1, len(df7firstLabels)):
    df7sinks.append(baseNum + x)
    df7numbers.append(1)

baseNum = baseNum + len(df7firstLabels)
df7spacingReal = []
for x in range(0, len(df7spacing) - 1):
    df7spacingReal.append(df7spacing[x])
    df7spacingReal.append(df7spacing[x] + 0.1)
df7spacingReal.append(df7spacing[-1])
df7spacing = df7spacingReal

for x in range(0, len(df7firstLabels)):
    df7spacingY.append(yBase)
yBase = yBase + 0.1


sources = sources + df7sources
sinks = sinks + df7sinks
numbers = numbers + df7numbers
spacing = spacing + df7spacing
firstLabels = firstLabels + df7firstLabels
spacingY = spacingY + df7spacingY

df2sources = []
df2sinks = []
df2numbers = []
df2firstLabels = []
df2spacing = []
df2spacingY = []

df2['stage_group_name'] = df2['stage_group_name'].fillna('stage not given')
df2['display_name'] = df2['display_name'].fillna('medication not given')
startDate = list(set(df2[df2['encounter_number'] == 0]['enc_start']))[0]
for x in list(set(df2['encounter_number'])):
    stage = ', '.join(list(set(df2[df2['encounter_number'] == x]['stage_group_name'])))
    medication = ', '.join(list(set(df2[df2['encounter_number'] == x]['display_name'])))[0:30] + '...'
    encounterGap = list(set(df2[df2['encounter_number'] == x]['encounter_gap']))[0]
    df2firstLabels.append(stage)
    df2firstLabels.append(medication)
    df2spacing.append(encounterGap)

df2firstLabels.append('last record')

today = date.today()
finalDiff = (today - startDate).days / 7
df2spacing.append(finalDiff)

for x in range(0, len(df2firstLabels) - 1):
    df2sources.append(baseNum + x)
    df2numbers.append(1)
for x in range(1, len(df2firstLabels)):
    df2sinks.append(baseNum + x)
    df2numbers.append(1)

baseNum = baseNum + len(df2firstLabels)
df2spacingReal = []
for x in range(0, len(df2spacing) - 1):
    df2spacingReal.append(df2spacing[x])
    df2spacingReal.append(df2spacing[x] + 0.1)
df2spacingReal.append(df2spacing[-1])
df2spacing = df2spacingReal

for x in range(0, len(df2firstLabels)):
    df2spacingY.append(yBase)
yBase = yBase + 0.1


sources = sources + df2sources
sinks = sinks + df2sinks
numbers = numbers + df2numbers
spacing = spacing + df2spacing
firstLabels = firstLabels + df2firstLabels
spacingY = spacingY + df2spacingY

df3sources = []
df3sinks = []
df3numbers = []
df3firstLabels = []
df3spacing = []
df3spacingY = []

df3['stage_group_name'] = df3['stage_group_name'].fillna('stage not given')
df3['display_name'] = df3['display_name'].fillna('medication not given')
startDate = list(set(df3[df3['encounter_number'] == 0]['enc_start']))[0]
for x in list(set(df3['encounter_number'])):
    stage = ', '.join(list(set(df3[df3['encounter_number'] == x]['stage_group_name'])))
    medication = ', '.join(list(set(df3[df3['encounter_number'] == x]['display_name'])))[0:30] + '...'
    encounterGap = list(set(df3[df3['encounter_number'] == x]['encounter_gap']))[0]
    df3firstLabels.append(stage)
    df3firstLabels.append(medication)
    df3spacing.append(encounterGap)

df3firstLabels.append('last record')

today = date.today()
finalDiff = (today - startDate).days / 7
df3spacing.append(finalDiff)

for x in range(0, len(df3firstLabels) - 1):
    df3sources.append(baseNum + x)
    df3numbers.append(1)
for x in range(1, len(df3firstLabels)):
    df3sinks.append(baseNum + x)
    df3numbers.append(1)

baseNum = baseNum + len(df3firstLabels)
df3spacingReal = []
for x in range(0, len(df3spacing) - 1):
    df3spacingReal.append(df3spacing[x])
    df3spacingReal.append(df3spacing[x] + 0.1)
df3spacingReal.append(df3spacing[-1])
df3spacing = df3spacingReal

for x in range(0, len(df3firstLabels)):
    df3spacingY.append(yBase)
yBase = yBase + 0.1


sources = sources + df3sources
sinks = sinks + df3sinks
numbers = numbers + df3numbers
spacing = spacing + df3spacing
firstLabels = firstLabels + df3firstLabels
spacingY = spacingY + df3spacingY

maxSpacing = max(spacing)
for item in range(0, len(spacing)):
    spacing[item] = spacing[item]/maxSpacing


color = []

possColors = ["aliceblue", "antiquewhite", "aqua", "aquamarine", "azure", "beige", "bisque", "black", "blanchedalmond", "blue", "blueviolet", "brown", "burlywood", "cadetblue",
              "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgrey", "darkgreen",
              "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred", "darksalmon", "darkseagreen", "darkslateblue", "darkslategray", "darkslategrey",
              "darkturquoise", "darkviolet", "deeppink", "deepskyblue", "dimgray", "dimgrey", "dodgerblue", "firebrick", "floralwhite", "forestgreen", "fuchsia", "gainsboro", "ghostwhite",
              "gold", "goldenrod", "gray", "grey", "green", "greenyellow", "honeydew", "hotpink", "indianred", "indigo", "ivory", "khaki", "lavender", "lavenderblush", "lawngreen",
              "lemonchiffon", "lightblue", "lightcoral", "lightcyan", "lightgoldenrodyellow", "lightgray", "lightgrey", "lightgreen", "lightpink", "lightsalmon", "lightseagreen",
              "lightskyblue", "lightslategray", "lightslategrey", "lightsteelblue", "lightyellow", "lime", "limegreen", "linen", "magenta", "maroon", "mediumaquamarine", "mediumblue",
              "mediumorchid", "mediumpurple", "mediumseagreen", "mediumslateblue", "mediumspringgreen", "mediumturquoise", "mediumvioletred", "midnightblue", "mintcream", "mistyrose",
              "moccasin", "navajowhite", "navy", "oldlace", "olive", "olivedrab", "orange", "orangered", "orchid", "palegoldenrod", "palegreen", "paleturquoise", "palevioletred",
              "papayawhip", "peachpuff", "peru", "pink", "plum", "powderblue", "purple", "red", "rosybrown", "royalblue", "rebeccapurple", "saddlebrown", "salmon", "sandybrown",
              "seagreen", "seashell", "sienna", "silver", "skyblue", "slateblue", "slategray", "slategrey", "snow", "springgreen", "steelblue", "tan", "teal", "thistle", "tomato",
              "turquoise", "violet", "wheat", "white", "whitesmoke", "yellow", "yellowgreen"]

number = random.randint(0, len(possColors) - 1)
while possColors[number] in color:
    number = random.randint(0, len(possColors) - 1)
col = possColors[number]

for entry in firstLabels:
    if entry != 'last record':
        color.append(col)
    else:
        color.append(col)
        color.append(col)
        number = random.randint(0, len(possColors) - 1)
        while possColors[number] in color:
            number = random.randint(0, len(possColors) - 1)
        col = possColors[number]

fig = go.Figure(data=[go.Sankey(
    arrangement= "freeform",
    node = dict(
      pad = 10,
      line = dict(color = "black", width = 0.5),
      label = firstLabels,
      color = "black",
      x = spacing,
      y = [0,0,0,0,0,0,0,0,0,0,0,0,0]
    ),
    link = dict(
      source = sources, # indices correspond to labels, eg A1, A2, A2, B1, ...
      target = sinks,
      line=dict(color="black", width=0.5),
      value = numbers,
      color = color,
  ))])

fig.update_layout(title_text="Breast Cancer Patient Journey", font_size=10, autosize=True)
fig.show()
"""

# ['Stage IV' 'Stage IIIA' 'Stage III' 'Stage I' nan 'Stage IIIC' 'Stage IB1' 'Stage IIB']

color = []


firstRunLabelsStage = ["Stage I", "Stage IB1", "Stage IIA", "Stage III", "Stage IIIA", "Stage IIIC", "Stage IV", "Stage IVB", "Stage Not Given"]
firstRunMedications = ['ZOLEDRONIC ACID', 'PALBOCICLIB', 'PROTEIN-BOUND PACLITAXEL', 'CISPLATIN', 'FOLFIRINOX', 'DOXORUBICIN', 'DENOSUMAB (XGEVA)', 'OLAPARIB',
                       'DOSE DENSE AC', 'EVEROLIMUS', 'RiTUXimab', 'LEUPROLIDE ACETATE', 'PALBOCICLIB (IBRANCE)', 'medication not given', 'CEFTRIAXONE',
                       'Fulvestrant', 'ONC IV HYDRATION', 'IVIG']

firstRunLabels = firstRunLabelsStage + firstRunMedications

secondRunLabels = ['Stage I', 'Stage IB1', 'Stage IIA', 'Stage III', 'Stage IIIA', 'Stage IIIC', 'Stage IV', 'Stage IVB', 'Stage Not Given', 'ZOLEDRONIC ACID', 'PALBOCICLIB', 'PROTEIN-BOUND PACLITAXEL', 'CISPLATIN', 'FOLFIRINOX', 'DOXORUBICIN', 'DENOSUMAB (XGEVA)', 'OLAPARIB', 'DOSE DENSE AC', 'EVEROLIMUS', 'RiTUXimab', 'LEUPROLIDE ACETATE', 'PALBOCICLIB (IBRANCE)', 'medication not given', 'CEFTRIAXONE', 'Fulvestrant', 'ONC IV HYDRATION', 'IVIG']
thirdRunLabels = ['Stage I', 'Stage IB1', 'Stage IIA', 'Stage III', 'Stage IIIA', 'Stage IIIC', 'Stage IV', 'Stage IVB', 'Stage Not Given', 'ZOLEDRONIC ACID', 'PALBOCICLIB', 'PROTEIN-BOUND PACLITAXEL', 'CISPLATIN', 'FOLFIRINOX', 'DOXORUBICIN', 'DENOSUMAB (XGEVA)', 'OLAPARIB', 'DOSE DENSE AC', 'EVEROLIMUS', 'RiTUXimab', 'LEUPROLIDE ACETATE', 'PALBOCICLIB (IBRANCE)', 'medication not given', 'CEFTRIAXONE', 'Fulvestrant', 'ONC IV HYDRATION', 'IVIG']
fourthRunLabels = ['Stage I', 'Stage IB1', 'Stage IIA', 'Stage III', 'Stage IIIA', 'Stage IIIC', 'Stage IV', 'Stage IVB', 'Stage Not Given', 'ZOLEDRONIC ACID', 'PALBOCICLIB', 'PROTEIN-BOUND PACLITAXEL', 'CISPLATIN', 'FOLFIRINOX', 'DOXORUBICIN', 'DENOSUMAB (XGEVA)', 'OLAPARIB', 'DOSE DENSE AC', 'EVEROLIMUS', 'RiTUXimab', 'LEUPROLIDE ACETATE', 'PALBOCICLIB (IBRANCE)', 'medication not given', 'CEFTRIAXONE', 'Fulvestrant', 'ONC IV HYDRATION', 'IVIG']

firstLabels = firstRunLabels + secondRunLabels + thirdRunLabels + fourthRunLabels + ['no further appointments', 'death']

stageISources = [firstLabels.index('Stage I'), firstLabels.index('Stage I'), firstLabels.index('Stage I'),

                 firstRunLabels.index('IVIG'), firstRunLabels.index('RiTUXimab'), firstLabels.index('medication not given'),
                 firstRunLabels.index('RiTUXimab'), firstRunLabels.index('IVIG'), firstRunLabels.index('IVIG'),

                len(firstRunLabels) + secondRunLabels.index('Stage I'), len(firstRunLabels) + secondRunLabels.index('Stage I'), len(firstRunLabels) + secondRunLabels.index('Stage I'),

                 len(firstRunLabels) + secondRunLabels.index('IVIG'), len(firstRunLabels) + secondRunLabels.index('RiTUXimab'), len(firstRunLabels) + secondRunLabels.index('medication not given'),
                len(firstRunLabels) + secondRunLabels.index('IVIG'), len(firstRunLabels) + secondRunLabels.index('RiTUXimab'),

                 ]

stageISinks = [firstRunLabels.index('IVIG'), firstRunLabels.index('RiTUXimab'), firstLabels.index('medication not given'),

               len(firstRunLabels) + secondRunLabels.index('Stage I'), len(firstRunLabels) + secondRunLabels.index('Stage I'), len(firstRunLabels) + secondRunLabels.index('Stage I'),
               firstLabels.index('no further appointments'), firstLabels.index('no further appointments'), len(firstRunLabels) + secondRunLabels.index('Stage III'),

               len(firstRunLabels) + secondRunLabels.index('IVIG'), len(firstRunLabels) + secondRunLabels.index('RiTUXimab'), len(firstRunLabels) + secondRunLabels.index('medication not given'),

               len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage I'), len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage I'),
               len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage I'),

               firstLabels.index('no further appointments'), firstLabels.index('no further appointments'),
               ]

stageIIISources = [firstRunLabels.index('Stage III'), firstRunLabels.index('Stage III'), firstRunLabels.index('Stage III'), firstRunLabels.index('Stage III'),

                    firstRunLabels.index("ONC IV HYDRATION"), firstRunLabels.index("PROTEIN-BOUND PACLITAXEL"), firstRunLabels.index("FOLFIRINOX"), firstRunLabels.index("medication not given"),
                   firstRunLabels.index('ONC IV HYDRATION'), firstRunLabels.index('ONC IV HYDRATION'),

                   len(firstRunLabels) + secondRunLabels.index('Stage III'), len(firstRunLabels) + secondRunLabels.index('Stage III'),
                   len(firstRunLabels) + secondRunLabels.index('Stage III'), len(firstRunLabels) + secondRunLabels.index('Stage III'),
                   len(firstRunLabels) + secondRunLabels.index('Stage III'),

                   len(firstRunLabels) + secondRunLabels.index("ONC IV HYDRATION"), len(firstRunLabels) + secondRunLabels.index("PROTEIN-BOUND PACLITAXEL"),
                   len(firstRunLabels) + secondRunLabels.index("FOLFIRINOX"), len(firstRunLabels) + secondRunLabels.index("medication not given"),
                   len(firstRunLabels) + secondRunLabels.index("ONC IV HYDRATION"),

                   ]

stageIIISinks = [firstRunLabels.index("ONC IV HYDRATION"), firstRunLabels.index("PROTEIN-BOUND PACLITAXEL"), firstRunLabels.index("FOLFIRINOX"), firstRunLabels.index("medication not given"),

                   len(firstRunLabels) + secondRunLabels.index('Stage III'), len(firstRunLabels) + secondRunLabels.index('Stage III'),
                    len(firstRunLabels) + secondRunLabels.index('Stage III'), len(firstRunLabels) + secondRunLabels.index('Stage III'),
                 firstLabels.index('no further appointments'), len(firstRunLabels) + secondRunLabels.index('Stage IV'),

                 len(firstRunLabels) + secondRunLabels.index("ONC IV HYDRATION"), len(firstRunLabels) + secondRunLabels.index("PROTEIN-BOUND PACLITAXEL"),
                 len(firstRunLabels) + secondRunLabels.index("FOLFIRINOX"), len(firstRunLabels) + secondRunLabels.index("medication not given"),
                len(firstRunLabels) + secondRunLabels.index("ONC IV HYDRATION"),

                len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage III'), len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage III'),
                len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage III'), len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage III'),
                len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage III'),
                 ]

stageIVSources = [firstRunLabels.index('Stage IV'), firstRunLabels.index('Stage IV'), firstRunLabels.index('Stage IV'), firstRunLabels.index('Stage IV'), firstRunLabels.index('Stage IV'),

                    firstRunLabels.index("PALBOCICLIB"), firstRunLabels.index("PROTEIN-BOUND PACLITAXEL"), firstRunLabels.index("ZOLEDRONIC ACID"),
                   firstRunLabels.index("DOXORUBICIN"), firstRunLabels.index("medication not given"),
                  firstRunLabels.index('DOXORUBICIN'),

                   len(firstRunLabels) + secondRunLabels.index('Stage IV'), len(firstRunLabels) + secondRunLabels.index('Stage IV'),
                   len(firstRunLabels) + secondRunLabels.index('Stage IV'), len(firstRunLabels) + secondRunLabels.index('Stage IV'), len(firstRunLabels) + secondRunLabels.index('Stage IV'),
                  len(firstRunLabels) + secondRunLabels.index('Stage IV'),

                   len(firstRunLabels) + secondRunLabels.index("PALBOCICLIB"), len(firstRunLabels) + secondRunLabels.index("PROTEIN-BOUND PACLITAXEL"),
                   len(firstRunLabels) + secondRunLabels.index("ZOLEDRONIC ACID"), len(firstRunLabels) + secondRunLabels.index("DOXORUBICIN"),
                  len(firstRunLabels) + secondRunLabels.index("medication not given"), len(firstRunLabels) + secondRunLabels.index("ZOLEDRONIC ACID"),
]

stageIVSinks = [firstRunLabels.index("PALBOCICLIB"), firstRunLabels.index("PROTEIN-BOUND PACLITAXEL"), firstRunLabels.index("ZOLEDRONIC ACID"),
                   firstRunLabels.index("DOXORUBICIN"), firstRunLabels.index("medication not given"),

                   len(firstRunLabels) + secondRunLabels.index('Stage IV'), len(firstRunLabels) + secondRunLabels.index('Stage IV'),
                   len(firstRunLabels) + secondRunLabels.index('Stage IV'), len(firstRunLabels) + secondRunLabels.index('Stage IV'), len(firstRunLabels) + secondRunLabels.index('Stage IV'),
                   firstLabels.index('no further appointments'),

                   len(firstRunLabels) + secondRunLabels.index("PALBOCICLIB"), len(firstRunLabels) + secondRunLabels.index("PROTEIN-BOUND PACLITAXEL"),
                   len(firstRunLabels) + secondRunLabels.index("ZOLEDRONIC ACID"), len(firstRunLabels) + secondRunLabels.index("DOXORUBICIN"),
                  len(firstRunLabels) + secondRunLabels.index("medication not given"), len(firstRunLabels) + secondRunLabels.index("ZOLEDRONIC ACID"),

                len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage IV'), len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage IV'),
                len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage IV'), len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage IV'),
                len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage IV'), len(firstRunLabels) + len(secondRunLabels) + thirdRunLabels.index('Stage IV')
                ]

stageInumbers = [80, 60, 20,
           60, 50, 20, 10, 10, 10,
           60, 50, 20,
           55, 40, 20, 5, 10]

stageIIInumbers = [160, 90, 100, 35,
                  100, 90, 100, 35, 30, 30,
                   130, 90, 100, 35, 10,
                   130, 90, 100, 35, 10,
                  ]

stageIVnumbers = [56, 50, 45, 63, 23,
                  56, 50, 45, 53, 23, 10,
                  56, 50, 45, 53, 23, 30,
                  56, 50, 45, 53, 23, 30,]

stageIlabelColors = ['cornflowerblue', 'hotpink', 'green',
                     'cornflowerblue', 'hotpink', 'green', 'mediumturquoise', 'mediumturquoise', 'lightgoldenrodyellow',
                     'cornflowerblue', 'hotpink', 'green',
                     'cornflowerblue', 'hotpink', 'green', 'mediumturquoise', 'mediumturquoise']

stageIIIlabelColors = ['coral', 'dodgerblue', 'firebrick', 'floralwhite',
                       'coral', 'dodgerblue', 'firebrick', 'floralwhite', 'mediumturquoise', 'crimson',
                       'coral', 'dodgerblue', 'firebrick', 'floralwhite', 'lightgoldenrodyellow',
                       'coral', 'dodgerblue', 'firebrick', 'floralwhite', 'lightgoldenrodyellow', ]

stageIVlabelColors = ['deepskyblue', 'peru', 'peachpuff', 'moccasin', 'rosybrown',
                      'deepskyblue', 'peru', 'peachpuff', 'moccasin', 'rosybrown', 'mediumturquoise',
                      'deepskyblue', 'peru', 'peachpuff', 'moccasin', 'rosybrown', 'crimson',
                      'deepskyblue', 'peru', 'peachpuff', 'moccasin', 'rosybrown', 'crimson']

numbers = stageInumbers + stageIIInumbers + stageIVnumbers
labelColors = stageIlabelColors + stageIIIlabelColors + stageIVlabelColors

sources = stageISources + stageIIISources + stageIVSources
sinks = stageISinks + stageIIISinks + stageIVSinks

possColors = ["aliceblue", "antiquewhite", "aqua", "aquamarine", "azure", "beige", "bisque", "black", "blanchedalmond", "blue", "blueviolet", "brown", "burlywood", "cadetblue",
              "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgrey", "darkgreen",
              "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred", "darksalmon", "darkseagreen", "darkslateblue", "darkslategray", "darkslategrey",
              "darkturquoise", "darkviolet", "deeppink", "deepskyblue", "dimgray", "dimgrey", "dodgerblue", "firebrick", "floralwhite", "forestgreen", "fuchsia", "gainsboro", "ghostwhite",
              "gold", "goldenrod", "gray", "grey", "green", "greenyellow", "honeydew", "hotpink", "indianred", "indigo", "ivory", "khaki", "lavender", "lavenderblush", "lawngreen",
              "lemonchiffon", "lightblue", "lightcoral", "lightcyan", "lightgoldenrodyellow", "lightgray", "lightgrey", "lightgreen", "lightpink", "lightsalmon", "lightseagreen",
              "lightskyblue", "lightslategray", "lightslategrey", "lightsteelblue", "lightyellow", "lime", "limegreen", "linen", "magenta", "maroon", "mediumaquamarine", "mediumblue",
              "mediumorchid", "mediumpurple", "mediumseagreen", "mediumslateblue", "mediumspringgreen", "mediumturquoise", "mediumvioletred", "midnightblue", "mintcream", "mistyrose",
              "moccasin", "navajowhite", "navy", "oldlace", "olive", "olivedrab", "orange", "orangered", "orchid", "palegoldenrod", "palegreen", "paleturquoise", "palevioletred",
              "papayawhip", "peachpuff", "peru", "pink", "plum", "powderblue", "purple", "red", "rosybrown", "royalblue", "rebeccapurple", "saddlebrown", "salmon", "sandybrown",
              "seagreen", "seashell", "sienna", "silver", "skyblue", "slateblue", "slategray", "slategrey", "snow", "springgreen", "steelblue", "tan", "teal", "thistle", "tomato",
              "turquoise", "violet", "wheat", "white", "whitesmoke", "yellow", "yellowgreen"]


fig = go.Figure(data=[go.Sankey(
    arrangement= "freeform",
    node = dict(
      pad = 10,
      line = dict(color = "black", width = 0.5),
      label = firstLabels,
      color = "black",
    ),
    link = dict(
      source = sources, # indices correspond to labels, eg A1, A2, A2, B1, ...
      target = sinks,
      line=dict(color="black", width=0.5),
      value = numbers,
      color = labelColors,
  ))])

fig.update_layout(title_text="Breast Cancer Patient Journey", font_size=10, autosize=True)
fig.show()
