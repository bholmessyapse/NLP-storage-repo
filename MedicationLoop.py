from metamapLoader import metamapStarter
from metamapLoader import metamapCloser
from MetamapMedication import metamapstringoutput
import pandas as pd

# Start up metamap - we'll close after we're done!
metamapStarter()

pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/Medications/MedNames.csv", low_memory=False)

names = []
synonyms = []
cuis = []

totalNum = len(pathReports['Modified drug_name'])
num = 0
for name in pathReports['Modified drug_name']:
    print('***************')
    print(num, ' of ', totalNum)
    num = num + 1
    thisCUI, thisName, thisSynonym = metamapstringoutput(name)

    # This indicates that we couldn't find a synonym
    if thisName == '':
        thisName = name
    names.append(thisName)
    synonyms.append(thisSynonym)
    cuis.append(thisCUI)


rawResults = pd.DataFrame(list(zip(names, synonyms, cuis)), columns=['matched name', 'normalized name', 'cui'])

rawResults.to_csv("/Users/bholmes/Desktop/LatestNLP/Medications/MedNameCUIResults.csv", index=False)

metamapCloser()