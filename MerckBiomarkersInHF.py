import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput
from collections import Counter

# Display everything
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 150)

# Now beginning the sorting out!
pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/Jan2020Narratives.csv", low_memory=False)
#pathReports = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020-1.csv", low_memory=False)

# Use this to divide up new reports
#df = pd.read_csv("/Users/bholmes/Desktop/LatestNLP/MSMDRO_Narratives/Jan2020Narratives.csv", low_memory=False)
#truncated1 = df.iloc[:1000000]
#truncated2 = df.iloc[1000001:2000000]
#truncated3 = df.iloc[2000001:3000000]
#truncated4 = df.iloc[3000001:4000000]
#truncated5 = df.iloc[4000001:5000000]
#truncated6 = df.iloc[5000001:]
#truncated1.to_csv("~/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020-1.csv", index=False)
#truncated2.to_csv("~/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020-2.csv", index=False)
#truncated3.to_csv("~/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020-3.csv", index=False)
#truncated4.to_csv("~/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020-4.csv", index=False)
#truncated5.to_csv("~/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020-5.csv", index=False)
#truncated6.to_csv("~/Desktop/LatestNLP/MSMDRO_Narratives/TruncatedJan2020-6.csv", index=False)
#print("LOADED!")
#input()

#print(pathReports.columns)
#input()

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

# To avoid typing this out every time for every test, we'll define a method here.
def standardAppends(fname, mname, lname, mrnf, dobf, acc, ttype, sloc, path, dorder, dreport, ttext, ftext, ficd, frid, fpid):
    firstNameList.append(fname)
    middleNameList.append(mname)
    lastNameList.append(lname)
    mrnList.append(mrnf)
    dobList.append(dobf)
    accessionList.append(acc)
    testTypeList.append(ttype)
    sampleLocationList.append(sloc)
    pathologistList.append(path)
    dateOrderedList.append(dorder)
    dateReportedList.append(dreport)
    testTextList.append(ttext)
    fullTextList.append(ftext)
    icdCodeList.append(ficd)
    reportIdList.append(frid)
    patientIdList.append(fpid)

# These values are specific per test. We don't want to persist one sample location between samples. So reset!
def resetDerived():
    global pathologist
    global orderedDate
    global reportedDate
    global sampleLocation
    pathologist = ''
    orderedDate = ''
    reportedDate = ''
    sampleLocation = ''

# Also to avoid re-printing this for each test
def printResults():
    print("THE RESULTS")
    print(firstName)
    print(lastName)
    print(accession)
    print(lower)
    #print(fullTest)
    #print(results)
    #print(lot)
    print(orderedDate)
    print(reportedDate)
    print(sampleLocation)
    print(testType)
    #print(testTech)
    print(pathologist)

tests = []

# Data is the section that has the data
# Reasons is where it's pulled from
# Full is the full report text
alkData = []
alkReasons = []
alkFull = []
for x in range(0, len(pathReports['description'])):
#for x in range(0, 10000):
#    try:
    #if x % 100 == 0:
        #print(x, ' of ', len(pathReports['description']))
    patientId = pathReports['patientid'][x]
    reportId = pathReports['id'][x]
    # if reportId != '25be56ef-b1a0-4181-8382-3cec8f718d26':
    #     continue
    lower = str(pathReports['description'][x]).lower()
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
    while '\n\n' in lower:
        lower = lower.replace('\n\n', '\n')
    lowerOrig = lower

    # First, we're going to test to see if 'alk' is really 'alkaline phosphotase'
    lower = lower.replace('alk phos', '')
    # Now let's take out names
    lower = lower.replace('dr.alk', 'dr. alk')
    # And let's remove icd codes
    lower = lower.replace('alk-fish-m', '')

    #if 'gene target region' in lower:
    #    lower = lower[:lower.index('gene target region')]
    if 'c61' in lower:
        if 'arid1a ' in lower or 'atrx' in lower or ' atm ' in lower:
            print(patientId)