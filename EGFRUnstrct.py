import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# Now beginning the sorting out!
pathReports = pd.read_csv("/Users/bholmes/Desktop/DeleteMeSoon/MSMDR Narratives/PathReports.csv", low_memory=False)

# The lists for the file
firstNameList = []
middleNameList = []
lastNameList = []
mrnList = []
dobList = []
accessionList = []
testTextList = []
fullTextList = []
testTypeList = []
testTechList = []
sampleLocationList = []
pathologistList = []
dateOrderedList = []
dateReportedList = []
icdCodeList = []
patientIdList = []
reportIdList = []

# These will hold the metamap 4-tuple. We'll move column mapping to another function!
biomarkerResultList = []
conceptResultList = []
numericResultList = []
qualifierResultList = []


storedLen = 0
# Wrongway tests are those ones that aren't even path reports - distinguised by not having 'patient name' as a field.
# Aberrent tests are those that don't follow expected patterns. We're expecting formatting that we're not finding.
# Failed tests are ones that break either the NLP or this script entirely. The original run (of the 350k tests) will have 0 of these. Keep new ones for analysis!
# Extra tests are those that still have the biomarker in question in the report text by the end.
aberrentTests = []
aberrentReasons = []
wrongwayTests = []
wrongwayReasons = []
extraTests = []
failedTests = []
failedReasons = []

for x in range(0, len(pathReports['description'])):
    if x % 100 == 0:
        print(x, ' of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    lower = pathReports['description'][x].lower()
    lower = re.sub(' +', ' ', lower)
    splitReport = lower.split('\n')
    # These reports are truncated and don't contain info - NONE have 'her 2' or 'her2' or 'her-2'
    if 'patient name:' not in lower:
        wrongwayTests.append(lower)
        wrongwayReasons.append('no Patient')
        continue
    # We'll pull out the MRN
    try:
        mrnIndex = lower.index("rec.:")
    except Exception as e:
        # There's only one kind without a rec.:, and it's a regadenoson pharmacological stress myocardial perfusion study
        wrongwayTests.append(lower)
        wrongwayReasons.append('no MRN')
        continue
    MRN = lower[mrnIndex + 5:mrnIndex + 14].strip()
    # And the ICD codes - we'll also delete anything that's like a: b:
    try:
        icdIndex = lower.index('icd code(s):') + len('icd code(s):')
        icdPart = lower[icdIndex:].replace('\n', ' ')
        icdPart = icdPart[:icdPart.index('billing fee')]
    except:
        icdPart = ''
    icdCode = icdPart.strip()
    icdLists = re.findall('\s[a-z]\:\s', icdCode)
    for icd in icdLists:
        icdCode = icdCode.replace(icd, ' ')
    icdCode = ', '.join(list(dict.fromkeys(icdCode.split())))

    # And the name
    nameIndex = lower.index('name:')
    endName = lower.index('accession')
    nameBit = lower[nameIndex + 5: endName]
    firstName = nameBit.split(',')[1].strip()
    lastName = nameBit.split(',', )[0].strip()
    middleName = ''
    if len(firstName.split()) > 1:
        middleName = firstName.split()[1]
        firstName = firstName.split()[0]
    # And the accession
    accession = lower[endName + len('accession #:'):mrnIndex - 5].strip()
    # And the DOB
    dobindex = lower.index('dob:')
    enddod = lower.index('(age')
    dob = lower[dobindex + 4:enddod].strip()
    index = [idx for idx, s in enumerate(splitReport) if 'patient name:' in s][0]
    indexTT = index - 1
    testType = splitReport[indexTT]
    # Pull out test type
    while testType == '' or 'amended' in testType.lower() or testType.lower().replace('-', '') == '':
        indexTT = indexTT - 1
        testType = splitReport[indexTT].strip()
        if testType.endswith('.'):
            testType = testType[:-1]
    testTypeOrig = testType

    # This is where we get the date reported and MRN.
    reportedIndex = lower.index("reported:")
    date = lower[reportedIndex + 9:reportedIndex + 20].replace("|", '').replace("p", '').replace('r', '')
    date = date.strip()
    # This means the date is 'pending'
    if 'ending' in date:
        date = ''

    if 'procedures/addenda' in lower:
        newBit = lower[lower.index('procedures/addenda'):]
        name = newBit[newBit.index('\n'):]
        name = name.strip()
        name = name[:name.index('\n')]
        if '***elec' in name:
            try:
                newBit = lower[lower.index('procedures/addenda')+5:]
                newBit = newBit[newBit.index('procedures/addenda'):]
                name = newBit[newBit.index('\n'):]
                name = name.strip()
                name = name[:name.index('\n')]
            except:
                pass

        if name == 'addendum':
            try:
                newBit = lower[lower.index('addendum diagnosis'):]
                name = newBit[newBit.index('\n'):]
                name = name.strip()
                name = name[:name.index('\n')]
            except:
                name = testType
        if 'a. ' in name or 'b . ' in name or 'b: ' in name or 'b. ' in name or 'while there' in name or '(see comment)' in name or '':
            name = testType
        if 'h. pylori' in name:
            name = 'h. pylori stain'

    else:
        name = testType

    firstNameList.append(firstName)
    middleNameList.append(middleName)
    lastNameList.append(lastName)
    mrnList.append(MRN)
    icdCodeList.append(icdCode)
    testTypeList.append(name)
    dateReportedList.append(date)


rawResults = pd.DataFrame(list(zip(firstNameList, middleNameList, lastNameList, mrnList, icdCodeList, testTypeList)),
                          columns=['first name', 'middle name', 'last name', 'mrn', 'icd', 'test'])
rawResults.to_csv("~/Desktop/DeleteMeSoon/BiomarkersForPhizer/AllTests.csv", index=False)
