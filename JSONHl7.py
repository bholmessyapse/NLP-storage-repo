import pandas as pd
import time
import os
import json
import sys
import datetime

os.chdir(r"/Users/bholmes/Desktop/DeleteMeSoon/orus/JSON/hl7json/")
listOfFiles = os.listdir('.')

alltests = set()

sourceList = list()
source = ""
healthOrgList = list()
healthOrg = ""
reportIdList = list()
reportId = ""
MRNList = list()
MRN = ""
firstNameList = list()
firstName = ""
lastNameList = list()
lastName = ""
middleNameList = list()
middleName = ""
DOBList = list()
DOB = ""
genderList = list()
gender = ""
testTypeList = list()
testType = ""
resultList = list()
result = ""
orderedDateList = list()
orderedDate = ""

isLargeSample = False

for sampleJSON in listOfFiles:
    with open(sampleJSON) as json_file:
        print(sampleJSON)
        data = json.load(json_file)
        if len(data['patient_identification']) != 1:
            print("THE ASSUMPTION WAS WRONG, THERE CAN BE MORE THAN ONE PATIENT")
        firstName = data['patient_identification'][0]['patient_name']['name_first']
        lastName = data['patient_identification'][0]['patient_name']['name_last']

        # Names are probably difficult to get just right, and might have a low return on investment.
        # If we're getting MRN, don't worry about name TOO much.
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
        DOBobj = datetime.datetime.strptime(DOB, '%Y-%m-%dT%H:%M:%S.%fZ')
        new_format = "%Y-%m-%d"
        DOB = DOBobj.strftime(new_format)
        source = data['message_header'][0]['receiving_facility']
        healthOrg = data['message_header'][0]['sending_facility']
        reportId = data['message_header'][0]['message_control_id']
        testType = data['observation_request'][0]['universal_service_identifier']['text']


        for i in range(0, len(data['observation_result'])):
            result = ""
            # There are two kinds of results - one in which there are a number of observations together
            # with units, and another in which there is one large observation. We'll try to get the
            # individual units of the list, and, failing
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
        result = ""
        orderedDate = ""


unformedDataFrame = pd.DataFrame(list(zip(reportIdList, sourceList, healthOrgList, MRNList, firstNameList,
                                          middleNameList, lastNameList, DOBList, genderList, testTypeList,
                                          orderedDateList, resultList)),
                                                            columns=['ReportId', 'Source', 'healthOrg', 'MRN',
                                                                 'firstName', 'middleName', 'lastName', 'DOB',
                                                                 'gender', 'testType', 'testOrderDate', 'result'])


#export_csv = unformedDataFrame.to_csv ('~/Desktop/DeleteMeSoon/LungAdenocarcinomaJson.csv', index=False)

