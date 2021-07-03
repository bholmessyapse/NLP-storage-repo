import pandas as pd
import time
import os
import json
import sys
import datetime

# We'll be pulling both JSON files and text-based files. Both are formatted
# in the HL7 format. JSON files are obviously a little easier to parse, so we'll
# start with those.
os.chdir(r"/Users/bholmes/Desktop/DeleteMeSoon/orus/JSON/hl7json/")
listOfFiles = os.listdir('.')

# This is just a maker to get a list of the tests. Not important for the pipeline!
alltests = set()

# All these lists are the pieces of information we're able to pull from the report. The "result" is the unstructured
# text blob.
sourceList, healthOrgList, reportIdList, MRNList, firstNameList, lastNameList, middleNameList, DOBList, genderList, \
testTypeList, resultList, orderedDateList = ([] for i in range(12))

isLargeSample = False

for sampleJSON in listOfFiles:

    # We'll get a new one of these variables for each report.
    source, healthOrg, reportId, MRN, firstName, lastName, middleName, DOB, gender, testType, result, \
    orderedDate = ("" for i in range(12))

    with open(sampleJSON) as json_file:
        #print(sampleJSON)
        data = json.load(json_file)
        # I'm assuming that there is only ever one patient per report. This is to tell me if that's ever false.
        if len(data['patient_identification']) != 1:
            print("THE ASSUMPTION WAS WRONG, THERE CAN BE MORE THAN ONE PATIENT")
            input("")
        # Now we start pulling information. Because it's in JSON format, it's easy to find.
        firstName = data['patient_identification'][0]['patient_name']['name_first']
        lastName = data['patient_identification'][0]['patient_name']['name_last']

        # Names are probably difficult to get just right, and might have a low return on investment.
        # If we're getting MRN, don't worry about name TOO much. This should get everybody though.
        try:
            middleName = data['patient_identification'][0]['patient_name']['name_middle']
        except:
            middleName = ""
        if len(' '.split(firstName)) == 2:
            middleName = ' '.split(firstName)[1]
            firstName = ' '.split(firstName)[0]

        gender = data['patient_identification'][0]['administrative_sex']['identifier']
        mrn = data['patient_identification'][0]['patient_identifier_list']['id_number']
        DOB = data['patient_identification'][0]['date_time_of_birth']
        # Kind of making the decision that hour/minute/second doesn't matter for DOB. Could be wrong? Probably not.
        # Something to possibly revisit.
        DOBobj = datetime.datetime.strptime(DOB, '%Y-%m-%dT%H:%M:%S.%fZ')
        new_format = "%Y-%m-%d"
        DOB = DOBobj.strftime(new_format)
        source = data['message_header'][0]['receiving_facility']
        healthOrg = data['message_header'][0]['sending_facility']
        reportId = data['message_header'][0]['message_control_id']
        testType = data['observation_request'][0]['universal_service_identifier']['text']

        if reportId == '5600009894810':
            print(reportId)

        for i in range(0, len(data['observation_result'])):
            result = ""
            # There are two kinds of results - one in which there are a number of observations together
            # with units, and another in which there is one large observation. We're interested in the large
            # observations for now. Come back and look at the individual ones later?
            try:
                result = result + data['observation_result'][i]['observation_identifier']['original_text'] + " - "
                result = result + data['observation_result'][i]['observation_value'] + " "
                result = result + data['observation_result'][i]['units']['alternate_identifier']
            except:
                result = data['observation_result'][i]['observation_value']
                isLargeSample = True

        if isLargeSample:
            isLargeSample = False
            sourceList.append(source)
            healthOrgList.append(healthOrg)
            reportIdList.append(reportId)
            MRNList.append(MRN)
            firstNameList.append(firstName)
            middleNameList.append(middleName)
            lastNameList.append(lastName)
            DOBList.append(DOB)
            genderList.append(gender)
            testTypeList.append(testType)
            resultList.append(result)
            orderedDateList.append(orderedDate)


############## TIME FOR TEXT-BASED ####################

# Now it's time to get the text-based files. There are fewer of them, but each contains lots of reports!
os.chdir(r"/Users/bholmes/Desktop/DeleteMeSoon/orus/Text")
listOfFiles = os.listdir('.')

for hl7file in listOfFiles:
    # So we've got a bunch of HL7 messages all mushed together. It's our job to sort them out!
    # The 'errors='ignore'' flag has to be set for this to work. Might be worth investigating why?
    with open(hl7file, "r", encoding="UTF-8", errors='ignore') as hl7:
        print(hl7file)
        # First, we'll make sure that there's one row per line.
        hl7 = hl7.read()
        lines = hl7.split("\n")

        # We'll get a new one of these variables for each report.
        source, healthOrg, reportId, MRN, firstName, lastName, middleName, DOB, gender, testType, result, \
        orderedDate = ("" for i in range(12))
        isObs = False
        coPathReport = False

        # The way these files go, each line has a code that indicates what kind of informaiton is stored on the line.
        # A line with patient information will start with "PID".
        # There will be many lines with "OBX", for observation result. We want to pull information from each line
        # as it comes in, and keep a running tally of all the OBX lines, concatenating them when they're over.
        for line in lines:

            # HL7 lines are pipe-delimited
            thisLine = line.split("|")

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
            # Note that this testType gets overridden by what we pull out of the un-structured report.
            elif thisLine[0] == "OBR":
                testType = ' '.join(thisLine[15].split('^')).replace('^', ' ').replace('&', '->')

            # This is the observation result itself
            elif thisLine[0] == "OBX":
                if "PDFReport" not in thisLine[3]:
                    result = result + thisLine[5].strip() + "\n"

            # This indicates that we're entering an observation phase. There will be some number of OBX lines
            # after this one.
            if thisLine[0] == 'OBX' and isObs == False:
                isObs = True

            # The 'OBX' line is the last piece of the record that we want to record. This indicates that, for our
            # purposes, the record is finished, and we can push the results to a new line of the dataframe.
            if thisLine[0] != 'OBX' and isObs is True:
                isObs = False
                # Also, we only want coPath results. Again, maybe something to change later!
                if coPathReport is True:
                    coPathReport = False
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
                source, healthOrg, reportId, MRN, firstName, lastName, middleName, DOB, gender, testType, result, \
                orderedDate = ("" for i in range(12))


unformedDataFrame = pd.DataFrame(list(zip(reportIdList, sourceList, healthOrgList, MRNList, firstNameList,
                                          middleNameList, lastNameList, DOBList, genderList, testTypeList,
                                          orderedDateList, resultList)),
                                                            columns=['ReportId', 'Source', 'healthOrg', 'MRN',
                                                                 'firstName', 'middleName', 'lastName', 'DOB',
                                                                 'gender', 'testType', 'testOrderDate', 'result'])


export_csv = unformedDataFrame.to_csv ('~/Desktop/DeleteMeSoon/LungAdenocarcinomaText2.csv', index=False)