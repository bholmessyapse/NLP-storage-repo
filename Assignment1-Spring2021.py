#########
#
#   Assignment 1
#   Information Retrieval
#   Ben Holmes
#   Spring 2021
#
#########

#Imports
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
import numpy as np
import math
from scipy.spatial.distance import cosine
import random

########
# This section should be un-commented and run if it's the
# first time the code is being run on this system, or
# if you're in an environment that otherwise doesn't contain the
# stopwords and wordnet from nltk!
#
try:
    list(stopwords.words('english'))
except:
    nltk.download('stopwords')
    nltk.download('wordnet')

######
# Booleans - these control how the program runs. Explanations above each, set it to how you'd like it to run.
######

# Make this TRUE if you want to see the changes to the document as you progress, or FALSE for just the final answer
seeProgress = False

# Make this TRUE if you want to lemmatize the text, or FALSE if not.
lemmatizingOn = True

# Turn this value to 'True' if you want more documents (this assumes that any terms without logical operators between them are 'ors'
# and turn it to 'False' if you want higher quality documents (this assumes that any terms without logical operators between them are 'ands'
permissivity = True

# To conveniently hold both parts of this assignment in one file, I've got boolean triggers for turning on one part or another.
# part 1 constructs the index from provided documents, part 2 does the query
runPart1 = False
runPart2 = True

# This dictates the top number of documents we return
topDocs = 20

# The base path for where we're writing files to, and where the cran files are.
# Replace path according to your working directory structure
basePath = '/Users/bholmes/Desktop/Assign/Assignment 1/'
path = basePath + 'cran/cran.all.1400'

######
# Pre-sets. These structures are important for processing
######

# This is for the query that we will run on the corpus
queryHolder = []

# This holds the query text
queryText = ''

# This is a copy of the query with only keywords
queryKeywords = []

# This is the dictionary for the entire corpus
termDictionary = [['', 0]]

# This contains a holder for a word and associated docId list for one term
wordDocidDict = [['', 0]]

# Holds the list of documents
docsHolder = []

totalWords = 0

# Proccess docs for index building
def indexBuilder(thisDocument, ID):

    # We'll hold a set of words for every document
    wordsInCorpus = set()
    # from each doc, append words into raw words list
    terms = thisDocument.split()
    for word in terms:
        if word != ' . ' and word != '.':
            wordsInCorpus.add(word.replace(',', '').replace(';', '').replace(':', '').replace(' . ', ''))

    # We're using the stopwords from the nltk corpus
    stopWords = list(stopwords.words('english'))
    textMinusStopwords = [w for w in list(wordsInCorpus) if not w in stopWords]
    # This stopwords doesn't remove periods. I want them gone
    textMinusStopwords = [w for w in list(textMinusStopwords) if not w in ['.']]
    if seeProgress:
        print('INITIAL DOC')
        print(thisDocument)
        print('\n')
        print('AFTER REMOVING STOPWORDS')
        print(textMinusStopwords)
        print('\n')

    # If Lemmatizing is on, this lemmatizes the text. We're using the WordNet Lemmatizer, for ease of use.
    if lemmatizingOn:
        lemmadWords = []
        lemmatizer = WordNetLemmatizer()
        for word in textMinusStopwords:
            lemmadWords.append(lemmatizer.lemmatize(word))
        if seeProgress:
            print('AFTER LEMMATIZING')
            print(lemmadWords)
            print('\n')
        # Remove punctuation
        lemmadWords =  list(filter(None, lemmadWords))
        finalList = lemmadWords

    else:
        finalList = textMinusStopwords

    # Now let's find which words from the term dictionary appear in this document, and let's further
    # flag any duplicates! This means that for every word in our final list (lemma'd or not), we'll
    # go through the term dictionary. Since it starts out empty, our first act will be to add all the terms from
    # the first document. From then on, we'll add new terms one by one, adding their doc id to list.
    # If we encounter a word we have already added from a document, we mark it a duplicate and move on!
    foundTerm = False
    foundDup = False
    for word in finalList:
        for termInDic in termDictionary:
            # If we find this word in the dictionary...
            if termInDic[0] == word:
                foundTerm = True
                # If this word already has this docId associated with it, it's a duplicate!
                for x in termInDic[1:]:
                    if x == ID:
                        foundDup = True
                        break
                # If the term wasn't a duplicate, add the doc id
                if not foundDup:
                    termInDic.append(ID)
                if foundDup:
                    foundDup = False
        # If we didn't find this term anywhere else in the dictionary, append it + the docId!
        if(not foundTerm):
            termDictionary.append([word, ID])
        if(foundTerm):
            foundTerm = False

def enterQuery():
    global queryHolder
    global queryText
    queryInput = input('Please input your query:')
    querySplit = queryInput.lower().split()

    # Let's now lemmatize the query, if we're doing lemmatizing
    if lemmatizingOn:
        lemmatizer = WordNetLemmatizer()
        for word in querySplit:
            queryHolder.append(lemmatizer.lemmatize(word))
    else:
        for word in querySplit:
            queryHolder.append(word)

    getTermsAndDocIds()
    docsList = getDocListWithLogical()
    return docsList

# This returns the term and associated docIds for a word.
# They're in the form ['word', 1, 3, 4....]
def getTermsAndDocIds():
    global termDictionary
    global wordDocidDict
    wordDocidDict=[]
    for word in queryHolder:
        if word in termDictionary:
            wordDocidDict.append([word, termDictionary[word]])

# This gets the doc ids containing the query, taking into account the logical operations that
# we might have
def getDocListWithLogical():
    # When we pull the keywords from the query, we'll hold them here
    global queryKeywords
    global queryHolder
    global permissivity

    if len(queryHolder) == 0:
        print("EMPTY QUERY - PLEASE RE-ENTER")
        quit()

    # We don't permit logicals first or last!
    if queryHolder[0] in ['and', 'or', 'not'] or queryHolder[-1] in ['and', 'or', 'not']:
        print("BADLY FORMED QUERY, PLEASE RE-WRITE IN THE FORM OF [term logical term logical term [etc.]]")
        quit()

    # Now what we do is iterate through the list. If we've in 'permissive' mode, every stretch of terms without
    # an 'and' 'or' or 'not' (logical) between them are considered to be or'd together. If permissive is off,
    # all those terms are 'anded', (i.e. we take either the union or intersection).
    # These sub-lists are then combined as through the logicals in the list.
    # so 'airplane boat and car' would be
    #   (airplane OR boat) and (car)
    #   or
    #   (airplane AND boat) and (car)
    # We take the first bit of keywords before the first logical operator ('and', 'or', 'not') and perform the appropriate logical operation
    # on all the sub-terms.
    # Then we save that list, perform logical operations on the next chunk of sub-terms, and then combine those two cumulative doc ids from the
    # two sub-terms.
    # This is then saved as the whole rolling list, and the next chunk is taken.
    # So to illustrate, if permissive is on:
    # boat car plane and cat dog not car
    # is evaluated like this:
    # (boat OR car OR plane) is gotten first. This sub-list of docIds we'll call Chunk1
    # then (cat OR dog) is gotten. We'll call those docids Chunk2
    # Then (chunk1 AND chunk2) is gotten. We'll call that list Chunk3
    # Then (car) is gotten - we'll call that list Chunk4
    # Finally, (chunk3 NOT chunk4) is gotten. We'll call that Chunk5
    # Chunk5 is our final output.
    subList1 = []
    subList2 = []
    logicalHolder = ''
    firstTerm = True
    firstAdd = True
    totalList = []
    while len(queryHolder) > 0:
        if queryHolder[0] not in ['and', 'or', 'not']:
            queryKeywords.append(queryHolder[0])
        # If we haven't encountered a logical yet, we keep adding terms to our first sub-expression
        if queryHolder[0] not in ['and', 'or', 'not'] and firstTerm:
            subList1.append(queryHolder[0])
            queryHolder = queryHolder[1:]
        # Otherwise, if we encounter a logical and we don't have term 2, know that we have more terms to come, so we hold
        # the logical and keep going
        elif queryHolder[0] in ['and', 'or', 'not'] and firstTerm:
            logicalHolder = queryHolder[0]
            queryHolder = queryHolder[1:]
            firstTerm = False
        # otherwise, if it's not a logical, we append to the second sub-expression
        elif queryHolder[0] not in ['and', 'or', 'not'] and not firstTerm:
            subList2.append(queryHolder[0])
            queryHolder = queryHolder[1:]
        # Otherwise, we need to stop and calculate first
        else:
            permissivity = True
            # If this is the first chunk:
            if firstAdd:
                firstAdd = False
                nextLogicalHolder = queryHolder[0]
                queryHolder = queryHolder[1:]
                # For the 'or' permissive, it's any document that has any term in the sublists
                if permissivity:
                    rollingCount = []
                    rollingCount2 = []
                    for wrd in wordDocidDict:
                        if wrd[0] == subList1[0]:
                            for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                rollingCount.append(doc)
                    subList1 = subList1[1:]
                    while len(subList1) > 0:
                        newTerm = []
                        for wrd in wordDocidDict:
                            if wrd[0] == subList1[0]:
                                for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                    newTerm.append(doc)
                        rollingCount = logicalOr(rollingCount, newTerm)
                        subList1 = subList1[1:]
                    ### Now we take the second list
                    for wrd in wordDocidDict:
                        if wrd[0] == subList2[0]:
                            for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                rollingCount2.append(doc)
                    subList1 = subList2[1:]
                    while len(subList2) > 0:
                        newTerm = []
                        for wrd in wordDocidDict:
                            if wrd[0] == subList2[0]:
                                for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                    newTerm.append(doc)
                        rollingCount2 = logicalOr(rollingCount2, newTerm)
                        subList2 = subList2[1:]

                # For the 'and' permissive, it's any document that has any term in the sublists
                else:
                    rollingCount = []
                    rollingCount2 = []
                    for wrd in wordDocidDict:
                        if wrd[0] == subList1[0]:
                            for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                rollingCount.append(doc)
                    subList1 = subList1[1:]
                    while len(subList1) > 0:
                        newTerm = []
                        for wrd in wordDocidDict:
                            if wrd[0] == subList1[0]:
                                for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                    newTerm.append(doc)
                        rollingCount = logicalAnd(rollingCount, newTerm)
                        subList1 = subList1[1:]
                    ### Now we take the second list
                    for wrd in wordDocidDict:
                        if wrd[0] == subList2[0]:
                            for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                rollingCount2.append(doc)
                    subList1 = subList2[1:]
                    while len(subList2) > 0:
                        newTerm = []
                        for wrd in wordDocidDict:
                            if wrd[0] == subList2[0]:
                                for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                    newTerm.append(doc)
                        rollingCount2 = logicalAnd(rollingCount2, newTerm)
                        subList2 = subList2[1:]
            else:
                subList1 = totalList
                logicalHolder = nextLogicalHolder
                nextLogicalHolder = queryHolder[0]
                queryHolder = queryHolder[1:]
                # For the 'or' permissive, it's any document that has any term in the sublists
                if permissivity:
                    rollingCount2 = []
                    # Just the second list now
                    for wrd in wordDocidDict:
                        if wrd[0] == subList2[0]:
                            for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                rollingCount2.append(doc)
                    subList1 = subList2[1:]
                    while len(subList2) > 0:
                        newTerm = []
                        for wrd in wordDocidDict:
                            if wrd[0] == subList2[0]:
                                for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                    newTerm.append(doc)
                        rollingCount2 = logicalOr(rollingCount2, newTerm)
                        subList2 = subList2[1:]

                # For the 'and' permissive, it's any document that has any term in the sublists
                else:
                    rollingCount2 = []
                    ### Now we take the second list
                    for wrd in wordDocidDict:
                        if wrd[0] == subList2[0]:
                            for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                rollingCount2.append(doc)
                    subList1 = subList2[1:]
                    while len(subList2) > 0:
                        newTerm = []
                        for wrd in wordDocidDict:
                            if wrd[0] == subList2[0]:
                                for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                                    newTerm.append(doc)
                        rollingCount2 = logicalAnd(rollingCount2, newTerm)
                        subList2 = subList2[1:]
                        rollingCount = subList1

            if logicalHolder == 'and':
                totalList = logicalAnd(rollingCount, rollingCount2)
            elif logicalHolder == 'or':
                totalList = logicalOr(rollingCount, rollingCount2)
            elif logicalHolder == 'not':
                totalList = logicalNot(rollingCount, rollingCount2)
            subList1 = []
            subList2 = []

    # At this point, we're all done but the last comparison!
    if not firstAdd:
        subList1 = totalList
    if firstAdd:
        logicalHolder = logicalHolder
        # For the 'or' permissive, it's any document that has any term in the sublists
        if permissivity:
            rollingCount = []
            rollingCount2 = []
            for wrd in wordDocidDict:
                if wrd[0] == subList1[0]:
                    for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                        rollingCount.append(doc)
            subList1 = subList1[1:]
            while len(subList1) > 0:
                newTerm = []
                for wrd in wordDocidDict:
                    if wrd[0] == subList1[0]:
                        for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                            newTerm.append(doc)
                rollingCount = logicalOr(rollingCount, newTerm)
                subList1 = subList1[1:]
            ### Now we take the second list
            for wrd in wordDocidDict:
                if subList2 == []:
                    rollingCount2 = []
                    logicalHolder = 'or'
                else:
                    if wrd[0] == subList2[0]:
                        for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                            rollingCount2.append(doc)
            subList1 = subList2[1:]
            while len(subList2) > 0:
                newTerm = []
                for wrd in wordDocidDict:
                    if wrd[0] == subList2[0]:
                        for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                            newTerm.append(doc)
                rollingCount2 = logicalOr(rollingCount2, newTerm)
                subList2 = subList2[1:]

        # For the 'and' permissive, it's any document that has any term in the sublists
        else:
            rollingCount = []
            rollingCount2 = []
            for wrd in wordDocidDict:
                if wrd[0] == subList1[0]:
                    for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                        rollingCount.append(doc)
            subList1 = subList1[1:]
            while len(subList1) > 0:
                newTerm = []
                for wrd in wordDocidDict:
                    if wrd[0] == subList1[0]:
                        for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                            newTerm.append(doc)
                rollingCount = logicalAnd(rollingCount, newTerm)
                subList1 = subList1[1:]
            ### Now we take the second list
            for wrd in wordDocidDict:
                if wrd[0] == subList2[0]:
                    for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                        rollingCount2.append(doc)
            subList1 = subList2[1:]
            while len(subList2) > 0:
                newTerm = []
                for wrd in wordDocidDict:
                    if wrd[0] == subList2[0]:
                        for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                            newTerm.append(doc)
                rollingCount2 = logicalAnd(rollingCount2, newTerm)
                subList2 = subList2[1:]

        if logicalHolder == 'and':
            totalList = logicalAnd(rollingCount, rollingCount2)
        elif logicalHolder == 'or':
            totalList = logicalOr(rollingCount, rollingCount2)
        elif logicalHolder == 'not':
            totalList = logicalNot(rollingCount, rollingCount2)

    else:
        logicalHolder = nextLogicalHolder
        # For the 'or' permissive, it's any document that has any term in the sublists
        if permissivity:
            rollingCount2 = []
            # Just the second list now
            for wrd in wordDocidDict:
                if wrd[0] == subList2[0]:
                    for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                        rollingCount2.append(doc)
            subList1 = subList2[1:]
            while len(subList2) > 0:
                newTerm = []
                for wrd in wordDocidDict:
                    if wrd[0] == subList2[0]:
                        for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                            newTerm.append(doc)
                rollingCount2 = logicalOr(rollingCount2, newTerm)
                subList2 = subList2[1:]

        # For the 'and' permissive, it's any document that has any term in the sublists
        else:
            rollingCount2 = []
            ### Now we take the second list
            for wrd in wordDocidDict:
                if wrd[0] == subList2[0]:
                    for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                        rollingCount2.append(doc)
            subList1 = subList2[1:]
            while len(subList2) > 0:
                newTerm = []
                for wrd in wordDocidDict:
                    if wrd[0] == subList2[0]:
                        for doc in wordDocidDict[wordDocidDict.index(wrd)][1:][0]:
                            newTerm.append(doc)
                rollingCount2 = logicalAnd(rollingCount2, newTerm)
                subList2 = subList2[1:]
                rollingCount = subList1
                if logicalHolder == 'and':
                    totalList = logicalAnd(rollingCount, rollingCount2)
                elif logicalHolder == 'or':
                    totalList = logicalOr(rollingCount, rollingCount2)
                elif logicalHolder == 'not':
                    totalList = logicalNot(rollingCount, rollingCount2)
                    totalList = totalList
    return totalList

# AND operator
def logicalAnd(firstTerm, secondTerm):
    tempDocsList = list()
    for x in firstTerm:
        for y in secondTerm:
            # Append only if there's an intersection
            if x == y:
                tempDocsList.append(x)
    return tempDocsList

# OR operator
def logicalOr(firstTerm, secondTerm):
    tempDocsList = list(set(firstTerm + secondTerm))
    return list(set(tempDocsList))

# Not operator
def logicalNot(firstTerm, secondTerm):
    tempDocsList = list()
    for x in firstTerm:
        if x not in secondTerm:
            tempDocsList.append(x)
    return tempDocsList

def loadDocsAndMakeLists(path):
    # Now that we've got the file open, we want to make a list of all the documents. We'll keep two parallel lists: one for the titles,
    # and one for the text
    file = open(path, mode='r')
    cranFile = file.read()
    file.close()

    cranTitles = []
    cranTexts = []

    # The .I is for index, so we'll split on that
    cranFileList = cranFile.split('.I')

    # The first item in the list is blank, so we'll skip it
    cranFileList = cranFileList[1:]

    # Now then - for every item, we'll extract the title (the text between '.T' and '.A'.
    # and the writing - the text between '.W' and the end
    # Also, we want to replace newline characters with spaces.

    for item in cranFileList:
        cranTitles.append(item[item.index('.T\n') + len('.T\n'):item.index('.A\n')].replace('\n', ' '))
        cranTexts.append(item[item.index('.W\n') + len('.W\n'):].replace('\n', ' '))

    return cranTitles, cranTexts

# Here we get the tfidf of a query (or document) given a list of words and the document they came from.
# That would be the query itself for a query, of the text of a document.
def getTFIDF(listOfKeywords, text):
    tfidfs = []
    for keyword in listOfKeywords:
        tf = text.count(keyword)/len(text.split())
        numDocs = len(cranTexts)
        if not keyword in termDictionary:
            numOccurrences = 0
        else:
            numOccurrences = len(termDictionary[keyword])
        idf = math.log(numDocs/(numOccurrences + 1))
        tfidfs.append(tf*idf)
    return tfidfs

# Finally, we rank our documents with cosine similarity
# This takes 1) the vector of our query, and 2) the relevant docs
# We'll caculate the cosine similarity for each!
# We return a list of tuples, sorted by cosine
def getCosineSimilarity(queryTFIFDS, relevantDocs):
    # Our keywords for the query
    global queryKeywords

    tfidfDocList = []
    cosineSimList = []

    # This will get the tf-idf vector for every document
    for doc in relevantDocs:
        docText = cranTexts[doc]
        tfIdfVec = getTFIDF(queryKeywords, docText)
        tfidfDocList.append(tfIdfVec)

    # Now let's get the cosine similarities!
    for tfidf in tfidfDocList:
        cosineSimList.append(1 - cosine(queryTFIFDS, tfidf))

    # We'll zip the lists together by sorting
    zipped_by_cosine = zip(relevantDocs, cosineSimList)
    zipped_by_cosine = sorted(zipped_by_cosine, key = lambda t: t[1], reverse=True)

    return zipped_by_cosine

# This just gets a random snippet of the text - this is a very silly way to get it, but it's a
# simple version for now. We take the text, split it by sentence breaks, scramble the sentences,
# then take the first sentence that contains any of the keywords
def getSnippet(text, keywords):
    keywords = list(keywords)
    text = text.split('.')
    random.shuffle(text)
    textLocation = 0
    returnSentence = text[0]
    while not any(kw in returnSentence for kw in keywords):
        textLocation = textLocation + 1
        returnSentence = text[textLocation]
    kwNum = 0
    kw = keywords[kwNum]
    returnSentence = returnSentence.split()
    while kw not in ' '.join(returnSentence):
        kwNum = kwNum + 1
        kw = keywords[kwNum]
    theWord = ''
    for word in returnSentence:
        if kw in word:
            theWord = word
            break
    indexOfWord = returnSentence.index(theWord)
    if indexOfWord < 3:
        startIndex = 0
    else:
        startIndex = indexOfWord - 3
    if len(returnSentence) < startIndex + 3:
        endIndex = len(returnSentence)
    else:
        endIndex = indexOfWord + 3
    returnSentence = ' '.join(returnSentence[startIndex:endIndex])
    if startIndex != 0:
        returnSentence = '...' + returnSentence
    if endIndex != 0:
        returnSentence = returnSentence + '...'
    return returnSentence

# This is pretty simple - given a list of docs, we find the title and text of that document, and print it
def selectDoc(listOfDocs):
    if len(listOfDocs) == 0:
        print("SORRY, no documents with that term in the corpus!")
        print('Why not try one of these?')
        print(termDictionary.keys())
        quit()
    print('----------------------')
    print('\n\n\n\n')
    print(len(rankedDocs))
    print("Please select a document from this list of docIds:\n", listOfDocs, '\n')
    selectDoc = input()
    while len(selectDoc) < 1:
        print("\n\n INVALID! Please enter a selection:\n", listOfDocs, '\n')
        selectDoc = input()
    selectDoc = int(selectDoc)
    while selectDoc not in listOfDocs:
        print("\n\n INVALID SELECTION! Please select a document from this list of docIds:\n", listOfDocs, '\n')
        selectDoc = input()

    print("==========================\nThe following document was selected\n==========================\n", cranTitles[selectDoc], '\n------------------------\n', cranTexts[selectDoc].replace('.  ', '.\n'))

#######
# Main run of code below!
#######
if runPart1:

    cranTitles, cranTexts = loadDocsAndMakeLists(path)

    # Now we'll iterate through, and build the inverted index for every file
    docCounter = 0
    for name in cranTexts:
        if seeProgress:
            print(docCounter, ' of ', len(cranTexts))
        indexBuilder(name, docCounter)
        docCounter += 1

    #__Code to create the index file__
    termIndex = {}

    # We're going to save the term dictionary as, well, a dictionary!
    for termInDic in termDictionary:
        termIndex[termInDic[0]] = termInDic[1:]

    # Save the index
    savePath = basePath + '/termDictionary.npy'
    np.save(savePath, termIndex)

    if seeProgress:
        print('Length of terms in corpus: ', len(termDictionary))

if runPart2:
    # Let's load the term index dictionary from part 1
    try:
        termDictionary = np.load(basePath + '/termDictionary.npy', allow_pickle=True).item()
        # Remove the empty key
        termDictionary.pop('', None)

    except:
        "ERROR! You need to run part 1 at least once before running part 2!"
        quit()

    # I imagine that as the size of what we're indexing grows dramatically, we don't want
    # to have to save a local copy of all the docs. Therefore, I'm including the part of the
    # code where we load up the docs and parse them, because this could easily be replaced with
    # other code that grabs them from the internet or something similar
    cranTitles, cranTexts = loadDocsAndMakeLists(path)

    if seeProgress:
        totalWords = 0
        for doc in cranTexts:
            totalWords = totalWords + len(doc.split())
        print('there are ', totalWords, ' total words and', len(termDictionary.keys()), ' unique keys')

        dictLens = []
        dictKeys = []
        for key in termDictionary.keys():
            dictLens.append(len(termDictionary[key]))
            dictKeys.append(key)
        print('Largest number of entries is ', max(dictLens), 'which is', dictKeys[dictLens.index(max(dictLens))], ' and smallest is ', min(dictLens), ' which is ', dictKeys[dictLens.index(min(dictLens))], ' and average is ', sum(dictLens)/len(dictLens))
        input()

    docslist = enterQuery()
    docslist = set(docslist)
    if seeProgress:
        print('Query is: ', queryText)
        print('Relevant Docs: ')
        print(docslist)

    # Let's eliminate any duplicate keywords
    queryKeywords = set(queryKeywords)

    # Now we'll get the tf-idf vector for the query
    querytfidfs = getTFIDF(queryKeywords, ' '.join(queryKeywords))

    #Finally, we'll rank the relevant docs in terms of cosine similarity!
    rankedDocs = getCosineSimilarity(querytfidfs, docslist)

    # We'll return the top x documents, where X is set at the beginning. If we want more documents then there are matches, we'll just return all docs.
    if len(rankedDocs) < topDocs:
        topDocs = len(rankedDocs)

    print('\n')
    print("====================================RANKED RESULTS====================================")
    print("DOC ID\t\t\tSNIPPET FROM TEXT\t\t\tTitle\t\t\tCosine Similarity")
    print('---------------------------------------------------------------------------------\n\n')
    sampleDocs = []
    for num in range(0, topDocs):
        docId = rankedDocs[num][0]
        cosSim = rankedDocs[num][1]
        sampleDocs.append(docId)
        docText = cranTexts[docId]
        snippet = getSnippet(docText, queryKeywords)
        title = cranTitles[docId]
        if len(title) > 100:
            title = title[:100] + '...'
        print(docId, '\t\t\t', snippet, '\t\t\t', title, '\t\t\t', cosSim)

    selectDoc(sampleDocs)
