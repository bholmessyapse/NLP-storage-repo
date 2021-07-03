import pandas as pd
import numpy as np
# import operator
import re
from subprocess import call
import itertools
import os
import json
import sys
import csv
from NumWords import text2int
from collections import Counter

# Tally ho
df = pd.read_csv("~/Desktop/DeleteMeSoon/FullTests/FullTests.csv", low_memory=False)

biomarkerTestMRNs = []
biomarkerTestTypes = []
biomarkerTestDates = []

num = 0
type1 = 0
type2 = 0
type3 = 0
type4 = 0
type5 = 0
type6 = 0
type7 = 0
type8 = 0
type9 = 0
type10 = 0
type11 = 0
type12 = 0
type13 = 0
type14 = 0


for report in df['description']:
    print("report number " + str(num))
    num = num + 1
    if report in ['Outside Films', 'Ordered by an unspecified provider.', 'This exam has not been interpreted by a physician.'] or report.isnumeric() or \
        'The imaging of the surgical specimen was reviewed.' in report:
        continue
    # These are the standard that I'm used to
    try:
        mrnIndex = report.index("Rec.:")
        # The MRN is easy to get
        MRN = report[mrnIndex + 5:mrnIndex + 14].strip()
        type1 = type1 + 1
        # We'll get the test type here
        reportLines = report.split('\n')
        while ("" in reportLines):
            reportLines.remove("")
        index = [idx for idx, s in enumerate(reportLines) if 'Patient Name:' in s][0]
        indexTT = index - 1
        testType = reportLines[indexTT].strip()
        while testType == '' or 'amended' in testType.lower():
            indexTT = indexTT - 1
            testType = reportLines[indexTT].strip()
            if testType.endswith('.'):
                testType = testType[:-1].strip()
        if testType.endswith('.'):
            testType = testType[:-1].strip()
        # Now the test date
        pathReport = '|'.join(reportLines).lower()
        reportedIndex = pathReport.index("reported:")
        date = pathReport[reportedIndex + 9:reportedIndex + 20].replace("|", '').replace("p", '').replace('r', '')
        date = date.strip()

        biomarkerTestMRNs.append(MRN)
        biomarkerTestTypes.append(testType)
        biomarkerTestDates.append(date)


    except:
        # These are the ones with no patient name - they seem to be imaging
        try:
            mrnIndex = report.index("Patient MRN:")
            MRN = report[mrnIndex+13:mrnIndex+21].strip()
            type2 = type2 + 1
            #print(MRN)
            #print(report)
        except:
            try:
                # Ok, I'm thinking ALL the rest of these are imaging
                procedureIndex = report.index('PROCEDURE:')
                procedurePart = report[procedureIndex:]
                procedureEndIndex = procedurePart.index('\n\n')
                procedure = report[procedureIndex + 11: procedureIndex + procedureEndIndex]
                type3 = type3 + 1
                #print(procedure)
                #print(report)
                #input()
            except:
                try:
                    dateTimePresent = report.index('Consent given by:')
                    procedureLines = report.split('\n')
                    procedure = procedureLines[1]
                    type4 = type4 + 1
                    #print(procedure)
                except:
                    try:
                        imagesIndex = report.index('Images are stored in PACS.')
                        type5 = type5 + 1
                    except:
                        try:
                            FR = report.index('FINAL REPORT')
                            procedureLines = report.split('\n')
                            procedure = procedureLines[1]
                            type6 = type6 + 1
                            #print(procedure)
                        except:
                            try:
                                fr = report.index('Comparison:')
                                procedure = report[:report.index('\n\n')].replace('\n', '')
                                type7 = type7 + 1
                                #print(procedure)
                            except:
                                try:
                                    fr = report.index('Date/Time: ')
                                    procedureLines = report.split('\n')
                                    procedure = procedureLines[2]
                                    type8 = type8 + 1
                                    #print(procedure)
                                except:
                                    try:
                                        fr = report.index('Wire localization procedure:')
                                        procedure = report.split('\n')[0]
                                        type9 = type9 + 1
                                        #print(procedure)
                                    except:
                                        try:
                                            # This one has name, mrn, DOB, and test info
                                            fr = report.index('Requesting Physician:')
                                            MRN = report[report.index('MRN:')+4:report.index('DOB:')].strip()
                                            type10 = type10 + 1
                                            #print(MRN)
                                        except:
                                            try:
                                                # This one has some CT imaging - history, etc.
                                                fr = report.index('Requesting Physician:')
                                                ed = report.index('Exam Description')
                                                lineInQuestion = report[report.index('PACS Acc #')+10:]
                                                endOfSection = lineInQuestion.index('\n\n')
                                                section = lineInQuestion[:endOfSection]
                                                sectionSplit = section.split()
                                                result = ''
                                                for sec in sectionSplit:
                                                    if not sec.replace('/', '').replace(':','').isnumeric() and sec != '':
                                                        result = result + ' ' + sec
                                                result = result.strip()
                                                type11 = type11 + 1
                                                #print(result)
                                            except:
                                                try:
                                                    # This has information about the exam - it's imaging
                                                    fr = report.index('EXAMINATION:')+12
                                                    result = report[fr:report.index('\n\n')].strip()
                                                    type12 = type12 + 1
                                                    #print(result)
                                                except:
                                                    try:
                                                        # These are for mammogram screenings
                                                        fr = report.index('CLINICAL INDICATIONS:')
                                                        result = report.split('\n')[0]
                                                        type13 = type13 + 1
                                                        #print(result)
                                                    except:
                                                        try:
                                                            # These appear to be for imaging
                                                            fr = report.index('TECHNIQUE:')
                                                            result = report.split('\n')[0]
                                                            type14 = type14 + 1
                                                            #print(result)
                                                        except:
                                                            pass
                                                            #print("HERE!")
                                                            #print(report)
                                                            #input()



testsAndMRNS = pd.DataFrame(list(zip(biomarkerTestMRNs, biomarkerTestTypes, biomarkerTestDates)), columns=['MRN', 'Test Type', 'Test Date'])
testsAndMRNS.to_csv("~/Desktop/DeleteMeSoon/FullListOfTestsAndMRNs.csv", index=False)

print(Counter(biomarkerTestTypes))