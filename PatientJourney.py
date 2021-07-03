import pandas as pd
import numpy as np
import random
import statsmodels.api as sm
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import urllib, json
import math
from itertools import product


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

# here are the columns
#['body_site_name', 'classification_name', 'distant_metastasis_name',
#       'pat_id', 'stage_group_name', 'stage_id', 'icd9_code', 'icd10_code',
#       'enc_start', 'facility', 'prim_enc_prov_id', 'display_name',
#       'plan_start_date', 'treatment_goal_name']


#print(df.groupby(['stage_group_name','display_name']).size().reset_index().rename(columns={0:'count'}))
#input()
#print(df['enc_start'].unique())
#input()
########

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

dfAll = pd.concat([df1, df2, df3, df4, df5, df6, df7])

dfAll['stage_group_name'] = dfAll['stage_group_name'].fillna('stage not given')
dfAll['display_name'] = dfAll['display_name'].fillna('medication not given')

dfAllStageMeds = dfAll[['stage_group_name', 'display_name']]
dfAllStageMeds.drop_duplicates()
dfAllStageMeds.to_csv("~/Desktop/Hackathon/StageAndMeds.csv", index=False)
print("HERE!")
input()

for x in list(product(dfAll['stage_group_name'], dfAll['display_name'])):
    print(x)
input()

# How many encounters in total?
# print(dfAll['encounter_number'].unique())
# [0,1,2,3] -  4! That's quite a number

# Here, we'll get all the initial stages
# print(dfAll[dfAll['encounter_number'] == 0]['stage_group_name'].unique())
# ['Stage IV' 'Stage IIIA' 'Stage III' 'Stage I' nan 'Stage IIIC' 'Stage IB1' 'Stage IIB']

#################
### GETTING FIRST ENCOUNTER
#################
# We're grouping by patient id, encounter number, and stage_group_name, because we want all of those to be singles.
dfAll = (dfAll.groupby(['pat_id', 'encounter_number', 'stage_group_name'], as_index=False).agg(lambda x: x.sum() if np.issubdtype(x.dtype, np.number) else ', '.join(x)))

print(dfAll.head())
input()

firstStage = dfAll[dfAll['encounter_number'] == 0]['stage_group_name']
firstStage = list(firstStage)
# Now let's get all the medications from the initial stages
firstMedications = dfAll[dfAll['encounter_number'] == 0]['display_name']
firstMedications = list(firstMedications)

firstStageLabels = list(set(firstStage))
firstMedicationLabels = list(set(firstMedications))

firstLabels = firstStageLabels + firstMedicationLabels

sources = []
sinks = []
numbers = []
patientIds = []

for stage in firstStageLabels:
    for medication in firstMedicationLabels:
        thisCount = list(dfAll[(dfAll['encounter_number'] == 0) & (dfAll['stage_group_name'] == stage)]['display_name']).count(medication)
        sources.append(firstLabels.index(stage))
        sinks.append(firstLabels.index(medication))
        numbers.append(thisCount)
        if len (dfAll[(dfAll['encounter_number'] == 0) & (dfAll['stage_group_name'] == stage) & (dfAll['display_name']== medication)]) > 0:
            patientIds.append(list(dfAll[(dfAll['encounter_number'] == 0) & (dfAll['stage_group_name'] == stage) & (dfAll['display_name']== medication)]['pat_id'])[0])
        else:
            patientIds.append('')

color = []

for m in range(0, len(firstMedicationLabels)):
    firstMedicationLabels[m] = firstMedicationLabels[m][0:20] + '...'

firstLabels = firstStageLabels + firstMedicationLabels

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

realSources = []
realSinks = []
realNumbers = []
realPatientIds = []
for num in range(0, len(numbers)):
    if numbers[num] != 0:
        realSources.append(sources[num])
        realSinks.append(sinks[num])
        realNumbers.append(numbers[num])
        realPatientIds.append(patientIds[num])

sources = realSources
sinks = realSinks
numbers = realNumbers
patientIds = realPatientIds

for bit in numbers:
    number = random.randint(0, len(possColors)-1)
    while possColors[number] in color:
        number = random.randint(0, len(possColors)-1)
    color.append(possColors[number])

#################
### GETTING SECOND ENCOUNTER
#################

secondStage = dfAll[dfAll['encounter_number'] == 1]['stage_group_name']
secondStage = list(secondStage)
secondStageLabels = list(set(secondStage))
secondStageLabels.append('No Further Appt.')

origLabels = firstLabels
firstLabels = firstLabels + secondStageLabels

sources2 = sinks
sinks2 = []
numbers2 = []

x = 0
for id in patientIds:
    idOfStage2 = dfAll[(dfAll['encounter_number'] == 1) & (dfAll['pat_id'] == id)]['stage_group_name']
    if len(list(idOfStage2)) > 0:
        sinks2.append(list(idOfStage2)[0])
        numbers2.append(1)
        color.append(color[x])
    else:
        sinks2.append('No Further Appt.')
        numbers2.append(1)
        color.append('white')
    x = x + 1

sinks2num = []
for x in sinks2:
    sinks2num.append(len(origLabels) + secondStageLabels.index(x))
sinks2 = sinks2num

sinks = sinks + sinks2
sources = sources + sources2
numbers = numbers + numbers2

# Now for the next medication:
sources3 = sinks2
sinks3 = []
numbers3 = []

x = 0
for id in patientIds:
    idOfMed2 = dfAll[(dfAll['encounter_number'] == 1) & (dfAll['pat_id'] == id)]['display_name']
    if len(list(idOfMed2)) > 0:
        meds = ' '.join(list(idOfMed2))[0:20]
        sinks3.append(meds)
        numbers3.append(1)
        color.append(color[x])
    else:
        sinks3.append('No Further Meds.')
        numbers3.append(1)
        color.append('white')
    x = x + 1

secondMedications = dfAll[dfAll['encounter_number'] == 1]['display_name']
secondMedications = list(secondMedications)
for x in range(0, len(secondMedications)):
    secondMedications[x] = secondMedications[x][0:20]
secondMedications.append('No Further Meds.')

origLabels = firstLabels
firstLabels = firstLabels + secondMedications

sinks3num = []
for x in sinks3:
    sinks3num.append(len(origLabels) + secondMedications.index(x))
sinks3 = sinks3num

sinks = sinks + sinks3
sources = sources + sources3
numbers = numbers + numbers3


#################
### GETTING SECOND ENCOUNTER
#################

thirdStage = dfAll[dfAll['encounter_number'] == 2]['stage_group_name']
thirdStage = list(thirdStage)
thirdStageLabels = list(set(thirdStage))
thirdStageLabels.append('No Further Appt.')

origLabels = firstLabels
firstLabels = firstLabels + thirdStageLabels

sources4 = sinks3
sinks4 = []
numbers4 = []

x = 0
for id in patientIds:
    idOfStage3 = dfAll[(dfAll['encounter_number'] == 2) & (dfAll['pat_id'] == id)]['stage_group_name']
    if len(list(idOfStage3)) > 0:
        sinks4.append(list(idOfStage3)[0])
        numbers4.append(1)
        color.append(color[x])
    else:
        sinks4.append('No Further Appt.')
        numbers4.append(1)
        color.append('white')
    x = x + 1

sinks4num = []
for x in sinks4:
    sinks4num.append(len(origLabels) + thirdStageLabels.index(x))
sinks4 = sinks4num

sinks = sinks + sinks4
sources = sources + sources4
numbers = numbers + numbers4


####################

fig = go.Figure(data=[go.Sankey(
    node = dict(
      pad = 15,
      thickness = 20,
      line = dict(color = "black", width = 0.5),
      label = firstLabels,
      color = color
    ),
    link = dict(
      source = sources, # indices correspond to labels, eg A1, A2, A2, B1, ...
      target = sinks,
      line=dict(color="black", width=0.5),
      value = numbers,
      color = color
  ))])

fig.update_layout(title_text="Breast Cancer Patient Journey", font_size=10)
fig.show()


