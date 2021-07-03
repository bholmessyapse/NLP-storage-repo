import pandas as pd
import numpy
import operator
import re


# Right, so we'll process these reports in chunks. Henry Ford tends to give us reports in a very standardized
# format, so we'll process the bits we can with pattern matching, then put the rest through metamap or something.

# Tally ho
df = pd.read_csv("~/Desktop/DeleteMeSoon/LungAdenocarcinomaText.csv", low_memory=False)

# This is the hospital that ordered the test
source = ""
# This is the kind of report this is
testType = ""
# This is a special marker for if we're dealing with an amended report. Dunno what we'll do with it
amendedReport = False
# This is the day the report was done
reported = ""
# This is the physician who oversaw the procedure
physician = ""
# This is the clinical history of the patient
clinicalHistory = ""

allTests = set()

# We're spliiting this into chunks - the report is formatted, which means we can expect discrete chunks to be
# separated by the double line break.
df['line'] = df['result'].apply(lambda x: x.lower().split("\n\n"))

# I'm going to try something a little funny for the start of this. There are going to be a variable number of tokens
# in these reports, but what I need is to carve off the first chunk and keep the rest. So I'm going to call "j" my
# chunk numberer. Position [j] will ALWAYS be the start of "Patient Name", which I think is universal. Let's roll.
for i in range(0, len(df['line'])):
    j = 0
    # Henry Ford ALWAYS includes their contact info first. We'll just take the hospital name.
    source = df['line'][i][0].split("\n")[0]

    # Then the next bit is either the physician or the test type. If physician is first, the test type will be next.
        # There may sometimes be a leading space.
    if 'physician' in df['line'][i][1].split("\n")[0]:
        testType = df['line'][i][2].split("\n")[0]
        j = 3
    else:
        if len(df['line'][i][1].split("\n")) > 1:
            if 'amended' in df['line'][i][1].split("\n")[1]:
                testType = df['line'][i][1].split("\n")[0]
            else:
                testType = df['line'][i][1].split("\n")[1]
            j = 2
        else:
            if "report" in df['line'][i][1].split("\n")[0]:
                testType = df['line'][i][2].split("\n")[0]
                j = 3
            else:
                testType = df['line'][i][1].split("\n")[0]
                j = 2

    # This gets us right to the patient info. After this, we're there.
    if "patient name" not in df['line'][i][j]:
        while "patient name" not in df['line'][i][j]:
            if "amended" in df['line'][i][j]:
                amendedReport = True
            j = j+1

    # Ok, now we'll get when the report was received, and who the presiding physician was.
    patientInfo = df['line'][i][j].replace('\n', ' ')

    # We get two tries to have the reported info, otherwise it's not present.
    if('reported:') not in patientInfo and "autopsy date:" not in patientInfo:
        j = j+1
        patientInfo = df['line'][i][j].replace('\n', ' ')
        if ('reported:') not in patientInfo and "autopsy date:" not in patientInfo:
           reported="Not Reported"
        else:
            patientSplit = patientInfo.split(' ')
            patientLoc = patientSplit.index('reported:')
            reported = patientSplit[patientLoc + 1]
    else:
        patientSplit = patientInfo.split(' ')
        patientLoc = patientSplit.index('reported:')
        reported = patientSplit[patientLoc + 1]

    # Here we pull out the physician. Physician ALWAYS comes after reported date.
    # I'm assuming.
    if 'physician(s):' in df['line'][i][j]:
        physicianSplit = df['line'][i][j].split('\n')
        for value in range(0, len(physicianSplit)):
            if 'physician(s):' in physicianSplit[value]:
                physician = physicianSplit[value].split(':')[1]
    else:
        while 'physician(s):' not in df['line'][i][j]:
            j = j + 1
        physicianSplit = df['line'][i][j].split('\n')
        for value in range(0, len(physicianSplit)):
            if 'physician(s):' in physicianSplit[value]:
                physician = physicianSplit[value].split(':')[1]

    # Now we take the REST of the report. We'll try to capture the various sections below.
    restOfReport = " ".join(df['line'][i][j+1:])

    restOfReport = restOfReport.split("\n")

    # It's a nice visual barrier, but not helpful for our purposes
    # Let's remove the equals sign barriers
    regex = re.compile(r'(==)=+')
    restOfReport = filter(lambda i: not regex.search(i), restOfReport)
    filtered = [i for i in restOfReport if not regex.search(i)]

    # Because I'm joining with pipe, a character that doesn't show up in the reports,
    # I can find lone words.
    filtered = " | ".join(filtered)

    sections = [
        '| clinical history |',
        'operative diagnoses',
        'pathological diagnosis:',
        '| comment |',
        'procedures/addenda',
        'gross description',
        'microscopic description',
        'in-situ hybridization:',
        'icd code(s):',
        'billing fee code(s):',
        'operation/specimen:',
        'clia signout facility:',
        'interpretation |',
        'clinical panel',
        '*** end of report ***',
        '***electronically signed out***',
        'diagnostic interpretation:',
        'disclaimers:',
        'manual microdissection:',
        'dna quality:',
        'mean amplicon depth:',
        'laboratory notes',
        'gene location transcript cdna protein dp exon af label',
        'gene location transcript cdna protein dp exon af interpretation',
        '| results-comments |',
        'cytogenic impression: |',
        'karyotype: |',
        'clonal description |'

    ]

    # Now let's get an ordering - we'll need to drastically expand the number of columns we know about, I bet.
    sectionList = []
    sectionPos = []
    for section in sections:
        if section in filtered:
            sectionList.append(section)
            sectionPos.append(filtered.index(section))
    sectionList = [x for _,x in sorted(zip(sectionPos, sectionList))]
    sectionPos = sorted(sectionPos)


    if 'clinical panel' in sectionList and testType == 'hematolymphoid sequencing panel (51 genes).':
        if 'diagnostic interpretation:' in sectionList:
            position = sectionList.index('diagnostic interpretation:')
            #print(filtered[sectionPos[position]:sectionPos[position+1]])
        else:
            position = sectionList.index('clinical panel')
#            print(filtered[sectionPos[position]:])

    allTests.add(testType)

    if testType == 'microsatellite instability testing (msi).':
        if '| results-comments |' in sectionList:
            #print(sectionList)
            position = sectionList.index('| results-comments |')
            #print(filtered[sectionPos[position]+len('| results-comments |'):])
        else:
            position = sectionList.index('interpretation |')
            print(filtered[sectionPos[position]+len('| results-comments |'):])

#    if 'gene location transcript cdna protein dp exon af label' in sectionList:
#        position = sectionList.index('gene location transcript cdna protein dp exon af label')
#        print(filtered[sectionPos[position]+len('gene location transcript cdna protein dp exon af label'):])
#    elif 'gene location transcript cdna protein dp exon af interpretation' in sectionList:
#        position = sectionList.index('gene location transcript cdna protein dp exon af interpretation')
#        print(filtered[sectionPos[position]+len('gene location transcript cdna protein dp exon af interpretation'):])

#for test in allTests:
#    print(test)