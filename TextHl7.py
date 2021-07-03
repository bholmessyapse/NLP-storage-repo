import pandas as pd
import time
import os

os.chdir(r"/Users/bholmes/Desktop/DeleteMeSoon/orus/text")
listOfFiles = os.listdir('.')

# We're going to make a dataframe out of a bunch of HL7 reports. Fortunately, they DO have a consistent formatting.
# This means we can pull them apart in a structured way!

# This fully-formed dataframe is the eventual goal. It's NOT what we've got for now. In order to get it,
# we'll have to parse the HL7 files (that bit is done) and then do NLP on the parsed ones (not done).
# This is the windmill!
fullyFormedDataframe = pd.DataFrame(columns=['ReportId', 'Source', 'FirstName', 'LastName', 'MiddleName',
                                           'HealthcareOrganization', 'Gender', 'TestName', 'BiomarkerTested',
                                           'MRN', 'Address', 'DOB', 'TestOrderedDate', 'HGNCSymbol'])

# This is where I'm keeping all the sync'd HL7 files. We should put this on cloud9 and make it so we can do this
# on all the files going forward maybe? This is just more labor-intensive.
sourceList = list()
healthOrgList = list()
reportIdList = list()
MRNList = list()
firstNameList = list()
lastNameList = list()
middleNameList = list()
DOBList = list()
genderList = list()
testTypeList = list()
resultList = list()
orderedDateList = list()

allTests = set()

for hl7file in listOfFiles:
    print(hl7file)
    # So we've got a bunch of HL7 messages all mushed together. It's our job to sort them out!
    with open(hl7file, "r", encoding="UTF-8", errors='ignore') as hl7:
        # First, we'll make sure that there's one row per line.
        hl7 = hl7.read()
        lines = hl7.split("\n")

        source = ""
        healthOrg = ""
        reportId = ""
        MRN = ""
        firstName = ""
        lastName = ""
        middleName = ""
        DOB = ""
        gender = ""
        testType = ""
        result = ""
        orderedDate = ""
        isObs = False
        coPathReport = False

        # Each line has some information.
        for line in lines:

            # HL7 lines are pipe-delimited
            thisLine = line.split("|")

            # The 'OBX' line is the last piece of the record that we want to record. We set
            # 'isObs' true on the first OBX record. When it STOPS being an OBX record, we want to
            # clear out everything and push the results to the list.
            if thisLine[0] != 'OBX' and isObs is True:
                isObs = False

                if coPathReport is True:
                    coPathReport = False
                    # CHANGE THIS PART OUT TO SELECT WHICH REPORTS WE TAKE SUCKA
                    # if "Lung Adenocarcinoma Panel" in result:
                    if result != "":
                        sourceList.append(source)
                        healthOrgList.append(healthOrg)
                        reportIdList.append(reportId)
                        MRNList.append(MRN)
                        firstNameList.append(firstName)
                        middleNameList .append(middleName)
                        lastNameList.append(lastName)
                        DOBList.append(DOB)
                        genderList.append(gender)
                        testTypeList.append(testType)
                        resultList.append(result)
                        orderedDateList.append(orderedDate)
                result = ""
                source = ""
                healthOrg = ""
                reportId = ""
                MRN = ""
                firstName = ""
                middleName = ""
                lastName = ""
                DOB = ""
                gender = ""
                testType = ""
                orderedDate = ""

            # This indicates that we're entering an observation phase.
            if thisLine[0] == 'OBX' and isObs == False:
                isObs = True

            # The first thing we'll see in a message is the "MSH" label. This is how we know we've got a new
            # message incoming.
            # https://corepointhealth.com/resource-center/hl7-resources/hl7-msh-message-header/
            # We can get some information about the sending institution and the reportId
            if thisLine[0] == 'MSH':
                source = thisLine[3]
                reportId = thisLine[9]
                if 'CoPath' in thisLine[2]:
                    coPathReport = True


            # There might be an "SFT" version next. We DO NOT CARE. This is a software thing.
            # https://hl7-definition.caristix.com/v2/HL7v2.6/Segments/SFT

            # The PID is next. This gives us some information about the patient.
            # https://corepointhealth.com/resource-center/hl7-resources/hl7-pid-segment/
            elif thisLine[0] == 'PID':
                MRN = thisLine[3].split('^')[0]
                lastName = thisLine[5].split('^')[0]
                firstName = thisLine[5].split('^')[1]
                if len(thisLine[5].split('^')) > 2:
                    middleName = thisLine[5].split('^')[2]
                if len(thisLine[5].split('^')) == 2 or thisLine[5].split('^')[2] == "":
                    middleName = ""
                else:
                    middleName = thisLine[5].split('^')[2]
                DOB = thisLine[7]
                gender = thisLine[8]

            # Next we might see some information about the patient intake, in PV1. We don't care
            # about it for now.
            # https://corepointhealth.com/resource-center/hl7-resources/hl7-pv1-patient-visit-information-segment/

            # Then there might be a bit about the next of kin. Not recovered for now.
            # https://corepointhealth.com/resource-center/hl7-resources/hl7-nk1-next-kinassociate-parties/

            # Next might be a bit of common order information - it's got the date the request was put out
            # for now https://hl7-definition.caristix.com/v2/HL7v2.6/Segments/ORC
            elif thisLine[0] == "ORC":
                orderedDate = thisLine[9]

            # Next might be information about the order. We can get the test type here
            # https://corepointhealth.com/resource-center/hl7-resources/hl7-obr-segment/
            elif thisLine[0] == "OBR":
                testType = ' '.join(thisLine[15].split('^')).replace('^', ' ').replace('&', '->')

            # This is the observation result itself
            elif thisLine[0] == "OBX":
                if "PDFReport" not in thisLine[3]:
                    result = result + thisLine[5].strip() + "\n"


unformedDataFrame = pd.DataFrame(list(zip(reportIdList, sourceList, healthOrgList, MRNList, firstNameList,
                                          middleNameList, lastNameList, DOBList, genderList, testTypeList,
                                          orderedDateList, resultList)),
                                                            columns=['ReportId', 'Source', 'healthOrg', 'MRN',
                                                                 'firstName', 'middleName', 'lastName', 'DOB',
                                                                 'gender', 'testType', 'testOrderDate', 'result'])


export_csv = unformedDataFrame.to_csv ('~/Desktop/DeleteMeSoon/LungAdenocarcinomaText.csv', index=False)

#for record in unformedDataFrame['testType']:
#    if ',' in record:
#        print(record.split(',')[1])
#    elif ';' in record:
#        print(record.split(';')[1])

#print(testTypeList)