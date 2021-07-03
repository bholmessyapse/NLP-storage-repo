# Import libraries
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import re

# Turn this on to turn all PDFs into TXTs
getNewTexts = False

# Turn this on to get biomarkers from TXTs
getBiomarkers = True

mypath = '/Users/bholmes/Desktop/DeleteMeSoon/BiomarkersForGuardant/PDFs/'
pdfs = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.pdf' in f]

if getNewTexts:
    for pdf in pdfs:

        # Path of the pdf
        PDF_file = mypath + pdf
        # Part #1 : Converting PDF to images
        # Store all the pages of the PDF in a variable
        pages = convert_from_path(PDF_file, 500)

        # Counter to store images of each page of PDF to image
        image_counter = 1

        # Iterate through all the pages stored above
        for page in pages:
            # Declaring filename for each page of PDF as PNG
            # For each page, filename will be:
            # PDF page n -> page_n.png
            filename = mypath + "/page_" + str(image_counter) + ".png"

            # Save the image of the page in system
            page.save(filename, 'PNG')

            # Increment the counter to update filename
            image_counter = image_counter + 1

        # Part #2 - Recognizing text from the images using OCR
        # Variable to get count of total number of pages
        filelimit = image_counter - 1

        # Creating a text file to write the output
        outfile = mypath + pdf[:-4] + "_out_text.txt"

        # Open the file in append mode so that
        # All contents of all images are added to the same file
        f = open(outfile, "a")

        # Iterate from 1 to total number of pages
        for i in range(1, filelimit + 1):
            # Set filename to recognize text from
            # page_n.png
            filename = mypath + "page_" + str(i) + ".png"

            # Recognize the text as string in image using pytesserct
            text = str(((pytesseract.image_to_string(Image.open(filename)))))

            # The recognized text is stored in variable text
            # Any string processing may be applied on text
            # Here, basic formatting has been done:
            # In many PDFs, at line ending, if a word can't
            # be written fully, a 'hyphen' is added.
            # The rest of the word is written in the next line
            text = text.replace('-\n', '')

            # Finally, write the processed text to the file.
            f.write(text)

        # Close the file after writing all the text.
        f.close()

        delpath = '/Users/bholmes/Desktop/DeleteMeSoon/BiomarkersForGuardant/PDFs/'
        pngs = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.png' in f]
        for png in pngs:
            fileToDel = mypath + png
            os.remove(fileToDel)

# These will hold our results
bigfirstNameList = []
biglastNameList = []
bigdocNumberList = []
bigtestNameList = []
bigdiagnosisList = []
bigmrnList = []
bigdobList = []
biggenderList = []
bigdiagnosisList = []
bigtestNumberList = []
bigphysicianList = []
bigreportDateList = []
bigreceiptDateList = []
bigcollectionDateList = []
bigaccountList = []
bigspecimenList = []
bigaddresssList = []
bigstatusList = []
biggeneList = []
bigvariantList = []
biglabelList = []
bigpercentcfDNAList = []
biglastTestpercentcfDNAList = []
bigplasmaCopyNumberList = []

# Since test information is the same for each variant in a test, rather than append it all each time, we'll
# just have a function that does that
def addNormals():
    firstNameList.append(firstName)
    lastNameList.append(lastName)
    docNumberList.append(docNumber)
    testNameList.append(testName)
    diagnosisList.append(diagnosis)
    mrnList.append(MRN)
    dobList.append(DOB)
    genderList.append(gender)
    testNumberList.append(testNumber)
    physicianList.append(physician)
    accountList.append(account)
    specimenList.append(specimen)
    addresssList.append(address)
    statusList.append(status)
    reportDateList.append(reportDate)
    collectionDateList.append(collectionDate)
    receiptDateList.append(receiptDate)

# This is to make sure all lists are the same length
def squareUp():
    for list in [geneList, variantList, percentcfDNAList, lastTestpercentcfDNAList, labelList, plasmaCopyNumberList]:
        while len(list) < len(firstNameList):
            list.append('')

def addToTotal():
    bigfirstNameList.extend(firstNameList)
    biglastNameList.extend(lastNameList)
    bigdocNumberList.extend(docNumberList)
    bigtestNameList.extend(testNameList)
    bigdiagnosisList.extend(diagnosisList)
    bigmrnList.extend(mrnList)
    bigdobList.extend(dobList)
    biggenderList.extend(genderList)
    bigtestNumberList.extend(testNumberList)
    bigphysicianList.extend(physicianList)
    bigreportDateList.extend(reportDateList)
    bigreceiptDateList.extend(receiptDateList)
    bigcollectionDateList.extend(collectionDateList)
    bigaccountList.extend(accountList)
    bigspecimenList.extend(specimenList)
    bigaddresssList.extend(addresssList)
    bigstatusList.extend(statusList)
    biggeneList.extend(geneList)
    bigvariantList.extend(variantList)
    biglabelList.extend(labelList)
    bigpercentcfDNAList.extend(percentcfDNAList)
    biglastTestpercentcfDNAList.extend(lastTestpercentcfDNAList)
    bigplasmaCopyNumberList.extend(plasmaCopyNumberList)

if getBiomarkers:
    txts = [f for f in listdir(mypath) if isfile(join(mypath, f)) and '.txt' in f]

    for file in txts:
        # The test info
        firstNameList = []
        lastNameList = []
        docNumberList = []
        testNameList = []
        diagnosisList = []
        mrnList = []
        dobList = []
        genderList = []
        diagnosisList = []
        testNumberList = []
        physicianList = []
        reportDateList = []
        receiptDateList = []
        collectionDateList = []
        accountList = []
        specimenList = []
        addresssList = []
        statusList = []

        # The test results
        geneList = []
        variantList = []
        labelList = []
        percentcfDNAList = []
        lastTestpercentcfDNAList = []
        plasmaCopyNumberList = []

        txt = open(mypath + file, mode='r')
        reportText = txt.read()
        reportText = reportText.replace('GUARDANT (369°', 'GUARDANT 360').replace('CSUARDANT', 'GUARDANT').replace('GUARDANT360)', 'GUARDANT 360').replace('360CDx:', '360 CDx')\
            .replace('360°','360')
        txt.close()

        # Pull out the name
        thisBit = reportText[:reportText.index(' (')]
        firstName = thisBit.split(',')[1].strip()
        lastName = thisBit.split(',')[0].strip()

        # Pull out the doc id
        thisBit = reportText[reportText.index('(')+1:reportText.index(')')]
        docNumber = str(thisBit)
        # Misreading letter as numbers
        if docNumber.startswith('4'):
            docNumber = re.sub('4', 'A', docNumber, 1)


        # Pull out test name
        thisBit = reportText[reportText.index(')')+1:reportText.index('\n')]
        testName = thisBit.strip()

        # Pull out the MRN
        thisBit = reportText[reportText.index('Patient MRN:') + len('Patient MRN:'):]
        thisBit = thisBit[:thisBit.index('|')]
        MRN = thisBit.strip()

        # Pull out the DOB
        thisBit = reportText[reportText.index('DOB:') + len('DOB:'):]
        thisBit = thisBit[:thisBit.index('|')]
        DOB = thisBit.strip()

        # Pull out the gender
        thisBit = reportText[reportText.index('Gender:') + len('Gender:'):]
        thisBit = thisBit[:thisBit.index('\n')]
        gender = thisBit.strip()

        # Pull out the diagnosis
        thisBit = reportText[reportText.index('Diagnosis:') + len('Diagnosis:'):]
        thisBit = thisBit[:thisBit.index('|')]
        diagnosis = thisBit.strip()

        # Pull out the test number
        thisBit = reportText[reportText.index('Test Number') + len('Test Number'):]
        thisBit = thisBit[:thisBit.index('\n')].strip()
        testNumber = thisBit.split()[0]

        # Pull out the status
        thisBit = reportText[reportText.index('Status:') + len('Status:'):]
        thisBit = thisBit[:thisBit.index('\n')].strip()
        status = thisBit.split()[0]

        # Pull out the report date and physician
        thisBit = reportText[reportText.index('Report Date:') + len('Report Date:'):]
        thisBit = thisBit[:thisBit.index('\n')].strip()
        reportDate = thisBit.split()[0]
        physician = thisBit.split()[1:]
        if len(physician) > 1:
            physician = physician[0] + ' ' + physician[1]
        else:
            physician = ' '.join(physician)
        if physician == '':
            thisBit = reportText[reportText.index('PHYSICIAN') + len('PHYSICIAN'):]
            thisBit = thisBit[:thisBit.index('Account:')].strip()
            physician = thisBit

        # Pull out the receipt date
        thisBit = reportText[reportText.index('Receipt Date:') + len('Receipt Date:'):]
        thisBit = thisBit[:thisBit.index('\n')].strip()
        receiptDate = thisBit.split()[0]

        # Pull out the account
        thisBit = reportText[reportText.index('Account:') + len('Account:'):]
        thisBit = thisBit[:thisBit.index('\n')].strip()
        account = thisBit.strip()

        # Pull out the collection date
        thisBit = reportText[reportText.index('Collection Date:') + len('Collection Date:'):]
        thisBit = thisBit[:thisBit.index('\n')].strip()
        collectionDate = thisBit.split()[0]
        if len(thisBit.split()) > 1:
            account = account + ' ' +  ' '.join(thisBit.split()[1:])
            account = account.replace(' | ', ' ')

        # Pull out specimen
        thisBit = reportText[reportText.index('Specimen:') + len('Specimen:'):]
        if 'Address:' not in thisBit:
            thisBit = thisBit[:thisBit.index('\n')].strip()
        else:
            thisBit = thisBit[:thisBit.index('Address:')].strip()
        specimen = thisBit.strip()
        if '\n' in specimen:
            specimen = specimen[:specimen.index('\n')].strip()

        # Pull out address
        thisBit = reportText[reportText.index('Address:') + len('Address:'):]
        if 'Status:' not in thisBit:
            thisBit = thisBit[:thisBit.index('Ph:')].strip()
        elif thisBit.index('Ph:') < thisBit.index('Status:'):
            thisBit = thisBit[:thisBit.index('Ph:')].strip()
        else:
            thisBit = thisBit[:thisBit.index('Status:')].strip()
        if 'Specimen:' in thisBit:
            specBit = thisBit[thisBit.index('Specimen:'):]
            specBit = specBit[:specBit.index('\n')]
            thisBit = thisBit.replace(specBit, '')
        thisBit = thisBit.replace('\n', ' ').replace(' , ', ', ')
        while '  ' in thisBit:
            thisBit = thisBit.replace('  ', ' ')
        while thisBit.endswith(','):
            thisBit = thisBit[:-1]
        address = thisBit

        # Pull out MSI
        if 'Microsatellite status:' not in reportText:
            thisBit = reportText[reportText.index('MSI-High'):]
        else:
            thisBit = reportText[reportText.index('Microsatellite status:') + len('Microsatellite status:'):]
        thisBit = thisBit[:thisBit.index('\n')].strip()
        if 'NOT DETECTED' not in thisBit:
            thisBit = 'MSI-High DETECTED'
        while thisBit.endswith('.'):
            thisBit = thisBit[:-1]
        msi = thisBit
        msi = msi.replace('MSI-High', '').strip()
        addNormals()
        geneList.append('MSI')
        variantList.append('MSI-High')
        labelList.append(msi)
        squareUp()

        # Now for the gene list
        # 'Amp Alteration Trend' means there's more than one test
        if 'Alteration % cfDNA or Amp Alteration Trend' not in reportText:
            thisBit = reportText[reportText.index('% cfDNA or Amp') + len('% cfDNA or Amp'):]
            thisBit = thisBit[:thisBit.index('The table')].strip()
            thisBit = thisBit.split('\n')
            # Right, that's got us the list of genes, alterations, and allele frequencies.
            for pos in range(0, len(thisBit)):
                result = thisBit[pos]
                result = result.split()
                # We might have a blank line
                if result == []:
                    continue
                # Sometimes we get amplification labels on the next row
                if result[0] in ['High', 'Medium', 'Low']:
                    if variantList[-1] == 'Amplification':
                        labelList[-1] = result[0]
                    continue
                # Sometimes the plasma copy number is on the next line (it's either 'Plasma copy number' or 'Amplifications not graphed above Plasma copy number')
                if result[0] == 'Plasma':
                    if plasmaCopyNumberList[-1] == '':
                        plasmaCopyNumberList[-1] = result[-1]
                    else:
                        plasmaCopyNumberList.append(result[-1])
                    continue
                elif len(result) > 5:
                    if result[4] == 'Plasma':
                        if plasmaCopyNumberList[-1] == '':
                            plasmaCopyNumberList[-1] = result[-1]
                        else:
                            plasmaCopyNumberList.append(result[-1])
                        continue
                # Sometimes a vous is on the next line
                if result[0] == 'Variant' and 'Significance' in result:
                    labelList[-1] = 'VUS'
                    continue
                # This might be the end of the page
                if (result[0] == 'A' and result[1] == 'more') or result[0] in ['GUARDANT', 'DOB:', 'Detected', '%', 'Amplifications', 'Tumor', 'portal.guardanthealth.com', 'Alteration']\
                        or 'GUARDANT' in result[0]:
                    continue
                addNormals()
                geneList.append(result[0])
                variantList.append(result[1].replace('|', 'I'))
                if 'Amplification' in result[1]:
                    if len(result) < 3:
                        labelList.append('Detected')
                    else:
                        labelList.append(result[2])
                else:
                    percentcfDNAList.append(result[2])
                    if 'Unknown' in result or 'Uncertain' in result:
                        labelList.append('VUS')
                    elif 'Synonymous' in result:
                        labelList.append('Synonymous Alteration')
                    else:
                        labelList.append('Pathogenic')
                squareUp()

        # This is what we see if there was more than one test
        if 'Alteration % cfDNA or Amp Alteration Trend' in reportText:
            thisBit = reportText[reportText.index('Alteration % cfDNA or Amp Alteration Trend') + len('Alteration % cfDNA or Amp Alteration Trend'):]
            thisBit = thisBit[:thisBit.index('The table')].strip()
            thisBit = thisBit.split('\n')
            # These rows have the graphs showing before and after, so they can be a bit confusing.
            # In general, if there are more than 2 items, it's probably the gene + variant (unless it's a VOUS gene, in which case it might be the
            # past percentage)
            for bit in range(0, len(thisBit)):
                if len(thisBit[bit].split()) > 2:
                    if thisBit[bit].split()[0] in ['GUARDANT', 'portal.guardanthealth.com', 'DOB:', 'Tumor', 'Alteration']:
                        continue
                    if '%' in thisBit[bit].split()[0] and 'Significance' in thisBit[bit]:
                        lastTestpercentcfDNAList.append(thisBit[bit].split()[0])
                        continue
                    thisLine = thisBit[bit].split()
                    if thisLine[1] == 'Splice':
                        thisLine[1:4] = [' '.join(thisLine[1:4])]
                    if thisLine[1].startswith('('):
                        thisLine[0:2] = [' '.join(thisLine[0:2])]
                    addNormals()
                    geneList.append(thisLine[0])
                    variantList.append(thisLine[1])
                    percentcfDNAList.append(thisLine[2])
                    if 'Variant' in thisBit[bit] and 'Uncertain' in thisBit[bit]:
                        labelList.append('VUS')
                    else:
                        labelList.append('Pathogenic')
                else:
                    if '%' not in thisBit[bit]:
                        continue
                    if len(thisBit[bit].split()) > 1:
                        lastTestpercentcfDNAList.append(thisBit[bit].split()[0])
                    else:
                        lastTestpercentcfDNAList.append(thisBit[bit])
                    squareUp()

        # Now let's get the main list
        if 'genes as indicated below.' in reportText:
            thisBit = reportText[reportText.index('genes as indicated below') + len('genes as indicated below'):]
            thisBit = thisBit[:thisBit.index('Guardant')]
            thisBit = thisBit.replace(' * ', ' ').replace('#', '').replace('+', '').replace('~', '').replace('°', '').replace('®', '').strip()
            thisBit = thisBit.split()
            for bit in range(0, len(thisBit)):
                if thisBit[bit].isnumeric() or thisBit[bit] in ['.', '*', '?', 'T', 't', '©', 'Q', 'Tt', 't2']:
                    continue
                else:
                    if thisBit[bit] not in geneList:
                        addNormals()
                        if '?' in thisBit[bit]:
                            thisBit[bit] = thisBit[bit].replace('?', '1')
                        geneList.append(thisBit[bit])
                        labelList.append('No Variant Found')
                        squareUp()
        addToTotal()


lists = [bigfirstNameList, biglastNameList, bigdocNumberList, bigtestNameList, bigdiagnosisList, bigmrnList, bigdobList, biggenderList, bigdiagnosisList,
                                        bigtestNumberList, bigphysicianList, bigaccountList, bigreportDateList, bigreceiptDateList, bigcollectionDateList, bigspecimenList, bigaddresssList,
                                        bigstatusList, biggeneList, bigvariantList, biglabelList, bigpercentcfDNAList, biglastTestpercentcfDNAList, bigplasmaCopyNumberList]

for l in lists:
    print(l)
    print(len(l))

panelsDataFrame = pd.DataFrame(list(zip(bigfirstNameList, biglastNameList, bigdocNumberList, bigtestNameList, bigdiagnosisList, bigmrnList, bigdobList, biggenderList, bigdiagnosisList,
                                        bigtestNumberList, bigphysicianList, bigaccountList, bigreportDateList, bigreceiptDateList, bigcollectionDateList, bigspecimenList, bigaddresssList,
                                        bigstatusList, biggeneList, bigvariantList, biglabelList, bigpercentcfDNAList, biglastTestpercentcfDNAList, bigplasmaCopyNumberList)),
                               columns=['first name', 'last name', 'doc number', 'test name', 'diagnosis', 'mrn', 'dob', 'gender', 'diagnosis', 'test #',
                                        'physician', 'account', 'report date', 'receipt date', 'collection date', 'specimen', 'address', 'status',
                                        'gene', 'variant', 'label', '% cfDNA', 'previous % cfDNA', 'plasma copy number'])

panelsDataFrame.to_csv("~/Desktop/DeleteMeSoon/BiomarkersForGuardant/GuardantNLPresults.csv", index=False)