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

watchGrow = False
alternateVocab = False

indn = 0

# Turn this on to see where everything is getting added
# Current max pos for biomarkers is 137
# Current max pos for qualifiers is 78
# Current max pos for concepts is 60
# Current max pos for numeric is 29
debug = False

# NOTE: MAKE SURE that text coming in has been normalized -
# put through textToInt
# 'less than' to '<'
# 'greater than' to '>'
# Make sure that every period has a space after it, unelss it's p. or c. (OR OTHERS??)
# Replace every 'however' with a '. '
# Replace every 'with' with an 'and'
# Replace 'rearrangment' with 'rearrangement' - SPELL CHECK ONLY THESE WORDS?
# Replace 'chromsome' with 'chromosome' - SPELL CHECK ONLY THESE WORDS?
# Replace ', other than' with ' other than'.
# Replace 'as well as' with 'and'

#####
# FUNCTIONS
#####

# This is saying - if one result is "50% cells" and another is "60% cells", they are the same 'type' of
# result, and it's very unlikely that two identical types of results would be talking about the same
# biomarker.
def numericSimilarty(stringA, stringB):
    stringA = stringA.replace('.', '').replace('to', '').replace('<', '').replace('>' ,'')
    stringB = stringB.replace('.', '').replace('to', '').replace('<', '').replace('>' ,'')
    resultA = ''.join([i for i in stringA if not i.isdigit()]).strip()
    resultB = ''.join([i for i in stringB if not i.isdigit()]).strip()
    if resultA == resultB:
        return True
    elif resultA in ['probe signal', 'probe signals', 'fusion signal', 'fusion signals'] and resultB in ['probe signal', 'probe signals', 'fusion signal', 'fusion signals']:
        return True
    else:
        return False

# Remove non-ascii characters
def unweird(stringA):
    return re.sub(r'[^\x00-\x7f]',r'', stringA)

def metamapstringoutput():
    try:

        # Read the file, and over-write it with the edited version.
        with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput', 'r+') as file:
            data = file.read()
            data = text2int(data)
            data = data.replace('–', '-').replace(' p. ', ' p.').replace('*', 'xstarx').replace('.,', '. ,').replace('>/=', '>=').replace('</=', '<=').replace('and an', '. . an')
            data = data.replace(' percent ', '%')
            data = data.replace('expressed', 'expression')
            encoded_string = data.encode("ascii", "ignore")
            data = encoded_string.decode()

            data = data.replace('immunohistochemistry:', 'immunohistochemistry').replace('microsatelite', 'microsatellite').replace('centromeric', 'centromere').replace('stining', 'staining')

            for word in data.replace('/', ' ').split():
                if 'chr' in word and word.replace('chr', '').isnumeric():
                    numPart = word.replace('chr', '')
                    replace = 'chromosome ' + numPart
                    data = data.replace(word, replace)
            file.seek(0)
            # If we're splitting up multiple reads with a '. .', don't take any of the outside punctuation
            while data.startswith((' ', '.')):
                data = data[1:]
            while data.endswith((' ', '.')):
                data = data[:-1]
            file.write(data.replace('≥', '>').replace('Less', 'less').replace('less than', '<').replace('positive;', 'positive.') \
                       .replace('centromere)', 'cen)').replace('< ', '<').replace('> ', '>').replace('expression by immunohistochemistry', '') + '\n')
            file.truncate()

        if alternateVocab:
            try:
                # This uses metamap to create an output file based on the input file.
                os.system("bin/metamap -Z 2021AA -V USABase --strict_model --JSONf 2 --negex --nomap NoMapFile --prune 30 -Q 0 /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                          "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
                with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
                    data = json.load(json_file)

            except:
                # This uses metamap to create an output file based on the input file.
                os.system("bin/metamap --JSONf 2 --negex --nomap NoMapFile --prune 30 -Q 0 /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                          "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
                with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
                    data = json.load(json_file)

        else:
            # This uses metamap to create an output file based on the input file.
            os.system("bin/metamap --JSONf 2 --negex --nomap NoMapFile --prune 30 -Q 0 /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                      "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
            with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
                data = json.load(json_file)

        ###
        # Ok, time for the the real NLP to begin.
        ###

        # This is for when we're compiling a final list of biomarkers. If we find an 'End' token in the qualifier
        # list, we stop scanning tokens for that utterance.
        # NOTE THE ASSUMPTION HERE, WHICH MAY NOT BE TRUE, that a single biomarker won't have information contained
        # across utterances. This could actually be fixed later, by concatening all the lists together from utterances.
        # That said, an end token really SHOULD mean we dont' do anything!
        endBiomarkerScan = False

        finalBiomarkerResults = []
        finalConceptResults = []
        finalNumericResults = []
        finalQualifierResults = []
        finalTimeResults = []

        if not data['AllDocuments']:
            finalBiomarkerResults = ['No Data']
            finalConceptResults = ['No Data']
            finalNumericResults = ['No Data']
            finalQualifierResults = ['No Data']
            for i in range(0, len(finalBiomarkerResults)):
                print(finalBiomarkerResults[i] + " ; " + finalConceptResults[i] + " ; " + finalNumericResults[i] + " ; " + finalQualifierResults[i])
            sys.exit()

        # Let's take this one at a time, by utterance. I'm scanning over all utterances for now. We've found that multiple
        # utterances can have important information.
        for utt in range(0, len(data['AllDocuments'][0]['Document']['Utterances'])):
            utterance = data['AllDocuments'][0]['Document']['Utterances'][utt]

            # Every utterance is made up of phrases, and we're gonna scan through them looking for particular tokens.
            # biomarkers are the genes/transcripts/etc. , concepts are the whats: amplifications/deletions/rearrangements etc.
            # numerics tell us how many of something there is (% nuclei, # of reads, etc.). Qualifiers tell us how sure
            # we are - results can be positive, negative, possible, approximate, etc.
            conceptList = [[] for z in range(len(utterance['Phrases']))]
            qualifierList = [[] for z in range(len(utterance['Phrases']))]
            numericList = [[] for z in range(len(utterance['Phrases']))]
            linkingList = [[] for z in range(len(utterance['Phrases']))]
            biomarkerList = [[] for z in range(len(utterance['Phrases']))]
            timeList = [[] for z in range(len(utterance['Phrases']))]

            # This only comes up sometimes. It's for giving a concept to a biomarker that's far from it.
            pocketConcept = ''

            # This is a little catch-all to try to find instances where no testing was done.
            if 'testing will not be performed' in utterance['UttText'].lower() or \
                    'fish analysis is not indicated' in utterance['UttText'].lower():
                biomarkerList[0].append('Testing Not Performed')
                linkingList[0].append('end$$$$*')

            # This time, we're keeping separate lists for results. No linking words of course.
            resultsListBiomarker = []
            resultsListConcept = []
            resultsListNumeric = []
            resultsListQualifier = []
            resultsListTime = []

            # ToAdd is a string used when the piece to be added is a large, composite piece. If we need to combine several
            # phrases, for instance. We're initializing it here.
            toAdd = ''

            # The last list is for parts of speech - these right NOW are only looking for adverbs, because those tend
            # to be the qualifier words I'm looking for.
            partOfSpeechList = [[] for z in range(len(utterance['Phrases']))]

            # I'm messing around with this for now, but I THINK if a phrase has 'indicates', we can say that the results are just 'indicated'
            hasIndicated = False
            notIndicated = False

            if 'probe sets' in utterance['UttText'] or 'chromosomes' in utterance['UttText']:
                hasSets = True
                hasSetsOrig = True
            else:
                hasSets = False
                hasSetsOrig = False

            # Now we'll loop through every phrase in the utterance, looking for such tokens.
            for phrasePos in range(0, len(utterance['Phrases'])):

                phrase = utterance['Phrases'][phrasePos]
                # I'm ASSUMING that once we see the word 'indicates', the rest of that phrase is full of maybes
                if 'indicates' in phrase['PhraseText'] or 'indicate' in phrase['PhraseText'] or 'suggest' in phrase['PhraseText'] or 'suggests' in phrase['PhraseText']:
                    hasIndicated = True
                if phrasePos > 1:
                    if 'not' in utterance['Phrases'][phrasePos - 1]['PhraseText']:
                        notIndicated = True

                # One thing we want to catch is if something is happening in 'all loci'
                if 'all loci' in phrase['PhraseText']:
                    if 'all loci' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('all loci')
                        print('added qualifier position 77')

                # This is one we want to capture - when the provider cancels testing
                if 'provider cancelled' in phrase['PhraseText']:
                    linkingList[phrasePos].append('end$$$$are')
                    if 'provider cancelled' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('provider cancelled')
                        if debug:
                            print("added qualifier position 1")
                        biomarkerList[phrasePos].append('test not performed')
                        if debug:
                            print("added biomarker position 1")

                # We don't know this one
                if 'msi-high' in phrase['PhraseText']:
                    if 'msi-high' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('msi-high')
                        print('added qualifier msi-high')

                if 'study is inconclusive' in utterance['UttText']:
                    linkingList[phrasePos].append('end$$$$study')
                    if 'inconclusive' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('inconclusive')
                        if debug:
                            print("added qualifier position 1b")
                        biomarkerList[phrasePos].append('no results')
                        if debug:
                            print("added biomarker position 1b")

                # This is one we want to capture - when the provider cancels testing
                if 'can not be performed' in utterance['UttText'] or 'an attempt was made' in utterance['UttText'] or 'will be repeated using fish' in utterance['UttText']:
                    linkingList[phrasePos].append('end$$$$are')
                    if 'test failed' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('test failed')
                        if debug:
                            print("added qualifier position 1b")
                        biomarkerList[phrasePos].append('test not performed')
                        if debug:
                            print("added biomarker position 1b")

                if 'unable to obtain results' in utterance['UttText']:
                    if 'test failed' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('test failed')
                        if debug:
                            print("added qualifier position 1c")

                if any(pendText in utterance['UttText'] for pendText in ['to follow in an addendum', 'will be reported in an addendum', 'will be reported as an addendum',
                                                                         'are in progress', 'testing will be performed', 'refer to clinical record']):
                    if 'results pending' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('results pending')
                        if debug:
                            print("added qualifier position 1c")

                # THIS IS KIND OF A META-ONE. If we find certain phrases (probe sets, chromosomes) then we'll want to interpret raw numbers we find a certain way.
                if ('probe sets' in utterance['UttText'] or 'chromosomes' in utterance['UttText']) and hasSets == True:
                    hasSets = False
                    for word in utterance['UttText'].split():
                        if word.replace(',', '').replace(';', '').replace('/', '').replace('q', '').isnumeric() or ('(' in word and word[0].isnumeric()):
                            biomarkerList[phrasePos].append('chromosome ' + word.replace(',', ''))
                    print('added probe sets')

                # And once we see a phrase like 'are observed', I THINK that means we want to turn everything before this sentence
                # into 'commonly seen's
                if ('are ' in phrase['PhraseText'] or 'is' in phrase['PhraseText']) and len(utterance['Phrases']) > phrasePos + 1:
                    if 'observed' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                        if 'are' in phrase['PhraseText']:
                            linkingList[phrasePos].append('end$$$$are')
                        elif 'is' in phrase['PhraseText']:
                            linkingList[phrasePos].append('end$$$$is')
                        hasIndicated = False
                        pos = phrasePos
                        while linkingList[pos] != ['.'] and pos > 0:
                            if qualifierList[pos]:
                                qualifierList[pos] = ['commonly seen in tests']
                            pos = pos - 1

                if 'please' in phrase['PhraseText'] and len(utterance['Phrases']) - 1 > phrasePos:
                    if 'see' in utterance['Phrases'][phrasePos + 1]['PhraseText'] or 'refer' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                        if 'no results' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('no results')
                            if debug:
                                print("added biomarker position 2")
                        if 'results in other test' not in qualifierList[phrasePos]:
                            qualifierList[phrasePos].append('results in other test')
                            if debug:
                                print("added qualifier position 2")

                # This is a sign that we've got something normal
                if 'within normal' in phrase['PhraseText']:
                    if 'within normal limits' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('within normal limits')
                        if debug:
                            print("added qualifier position 3")

                # MM doesn't know 'weakly'
                if 'weakly' in phrase['PhraseText']:
                    if 'weak' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('weak')
                        if debug:
                            print('added qualifier position 70')

                # MM doesn't know some CENs
                reString = r'(^|[ \/\\\(\n]+)CEN[0-9]+'
                regexp = re.compile(reString)
                if regexp.search(phrase['PhraseText']):
                    for word in phrase['PhraseText'].split():
                        if regexp.search(word):
                            if word.replace('\\', '').replace('/', '').lower() not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(word.replace('\\', '').replace('/', '').lower())
                                if debug:
                                    print('added biomarker position 135')

                # MM doesn't know maf
                if ' maf ' in ' ' + phrase['PhraseText'].replace('(', ' ').replace(')', ' ').replace('.', ' ').replace('\n', ' ') + ' ':
                    if 'maf' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('maf')
                        if debug:
                            print('added biomarker position 131')

                # MM doesn't know 'expressed'
                if 'expressed' in phrase['PhraseText']:
                    if 'expressed' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('expression')
                        if debug:
                            print('added qualifier position 70b')

                # MM doesn't know 'fh'
                if ' fh ' in ' ' + phrase['PhraseText']:
                    if 'fh' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('fh')
                        print('added biomarker position fh')

                # MM doesn't know ms-stable or ms-high
                if 'ms-' in phrase['PhraseText']:
                    if phrasePos < len(qualifierList) - 1:
                        if 'stable' in utterance['Phrases'][phrasePos + 1]['PhraseText'] or 'high' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                            toAdd = 'ms-' + utterance['Phrases'][phrasePos + 1]['PhraseText']
                            toAdd = toAdd.lower()
                            if toAdd not in qualifierList[phrasePos]:
                                qualifierList[phrasePos].append(toAdd)
                                if debug:
                                    print('added qualifier position 71')

                # This is a measure of TMB
                if 'muts/mb' in phrase['PhraseText']:
                    if 'muts/mb ' not in phrase['PhraseText']:
                        phrase['PhraseText'] = phrase['PhraseText'].replace('muts/mb', 'muts/mb ')
                    if ' muts/mb' not in phrase['PhraseText']:
                        phrase['PhraseText'] = phrase['PhraseText'].replace('muts/mb', ' muts/mb')
                    phraseSplit = phrase['PhraseText'].split()
                    indexO = phraseSplit.index('muts/mb')
                    if phraseSplit[indexO - 1].isnumeric():
                        toAdd = phraseSplit[indexO - 1] + ' ' + phraseSplit[indexO]
                        if toAdd not in numericList[phrasePos]:
                            numericList[phrasePos].append(toAdd)
                            if debug:
                                print('added numeric position 27')

                # And once we see a phrase like 'can occur' or 'is found', or 'has been', I THINK it's over
                if 'can ' in phrase['PhraseText']:
                    if 'occur' in utterance['Phrases'][phrasePos + 1]['PhraseText'] or 'involve' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                        linkingList[phrasePos].append('end$$$$can')
                        pos = phrasePos
                        while linkingList[pos] != ['.'] and pos > 0:
                            qualifierList[pos] = ['medically relevant']
                            pos = pos - 1
                        hasIndicated = False
                if 'is' in phrase['PhraseText'] and len(utterance['Phrases']) > phrasePos + 2:
                    if 'found' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                        linkingList[phrasePos].append('end$$$$is')
                        pos = phrasePos
                        while linkingList[pos] != ['.'] and pos > 0:
                            qualifierList[pos] = ['medically relevant']
                            pos = pos - 1
                        hasIndicated = False
                    elif 'a' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                        if 'common' in utterance['Phrases'][phrasePos + 2]['PhraseText']:
                            linkingList[phrasePos].append('end$$$$is')
                            pos = phrasePos
                            while linkingList[pos] != ['.'] and pos > 0:
                                qualifierList[pos] = ['medically relevant']
                                pos = pos - 1
                            hasIndicated = False
                if 'this test' in phrase['PhraseText'] and len(utterance['Phrases']) < phrasePos + 1:
                    if 'was' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                        linkingList[phrasePos].append('end$$$$this')

                # This one gets its' own category
                if '1 copy' in phrase['PhraseText']:
                    if '1 copy' not in numericList[phrasePos]:
                        numericList[phrasePos].append('1 copy')

                if 'has' in phrase['PhraseText'] and len(utterance['Phrases']) > phrasePos + 2:
                    if 'been' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                        if 'cancelled' in utterance['Phrases'][phrasePos + 2]['PhraseText']:
                            pos = phrasePos
                            biomarkerList[0] = ['test not performed']
                            while linkingList[pos] != ['.'] and pos > 0:
                                qualifierList[pos] = ['order cancelled']
                                pos = pos - 1
                            hasIndicated = False
                        else:
                            linkingList[phrasePos].append('end$$$$has')
                            pos = phrasePos
                            while linkingList[pos] != ['.'] and pos > 0:
                                qualifierList[pos] = ['medically relevant']
                                pos = pos - 1
                            hasIndicated = False
                # This one feels cheaty - maybe change?
                if 'molecular consequence' in phrase['PhraseText'] and len(utterance['Phrases']) > phrasePos + 1:
                    linkingList[phrasePos + 1].append('end$$$$molecular')
                    qualifierList[phrasePos].append('similar molecular consequence (from lit)')
                    if debug:
                        print("added qualifier position 4")

                # Monitor this - why is it + 1. Probably on purpose?
                # This one feels cheaty - maybe change?
                if 'most common' in phrase['PhraseText']:
                    firstWord = phrase['PhraseText'].split()[0]
                    linkingList[phrasePos + 1].append('end$$$$' + firstWord)
                    qualifierList[phrasePos].append('most common')
                    if debug:
                        print("added qualifier position 5")
                # This one feels cheaty - maybe change?
                if 'conventional cytogenetic' in phrase['PhraseText']:
                    if len(linkingList) > phrasePos + 1:
                        linkingList[phrasePos + 1].append('end$$$$conventional')
                    else:
                        linkingList[phrasePos].append('end$$$$conventional')

                # 'Gains' doesn't register like 'gain'. We might want 'multiple gains'
                if 'multiple gains' in phrase['PhraseText']:
                    if 'multiple gains' not in conceptList[phrasePos]:
                        conceptList[phrasePos].append('multiple gains')
                        if debug:
                            print("added concept position 1")

                # metamap does't know what 'unmutated' means
                if 'unmutated' in phrase['PhraseText']:
                    if 'mutation' not in conceptList[phrasePos]:
                        conceptList[phrasePos].append('mutation')
                        if debug:
                            print("added concept position 2")
                    if 'negative' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('negative')
                        if debug:
                            print("added qualifier position 6")

                # Metamap and also I don't know what 'rare positivity' means
                if phrase['PhraseText'].replace('.', '').replace(',', '') == 'rare positivity':
                    if 'rare positivity' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('rare positivity')
                        if debug:
                            print("added qualifier position 7")

                # Metamap doesn't seem to think 'pending' is anything
                if 'pending' in phrase['PhraseText'].lower():
                    if 'pending' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('pending')
                        if debug:
                            print('added qualifier position 64')

                # Some formulations of msi can be confusing
                if 'microsatellite instability-high' in phrase['PhraseText']:
                    if 'microsatellite instability-high' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('microsatellite instability-high')
                        if debug:
                            print('added qualifier position 65')
                    if 'microsatellite instability' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('microsatellite instability')
                        if debug:
                            print('added biomarker for qualifier position 65')

                # Let's get positive controls
                if 'positive control' in phrase['PhraseText'].replace('.', '').replace(',', '').lower():
                    if 'positive control' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('positive control')
                        if debug:
                            print("added qualifier position 51")

                # Metamap likes to split up some changes between phrases because of '>'
                if phrase['PhraseText'].startswith(('>t', '>a', '>c', '>g')):
                    if phrasePos > 0:
                        if utterance['Phrases'][phrasePos - 1]['PhraseText'].split()[-1].endswith(('a', 'g', 't', 'c')):
                            toAdd = utterance['Phrases'][phrasePos - 1]['PhraseText'].split()[-1] + phrase['PhraseText'].split()[0]
                            if toAdd not in qualifierList[phrasePos] and toAdd not in qualifierList[phrasePos - 1]:
                                qualifierList[phrasePos].append(toAdd)
                                if debug:
                                    print('added qualifier position 69')

                # It's hazy on the concept of a 'probe signal' and 'fusion signal
                if 'probe signal' in phrase['PhraseText']:
                    toAdd = 'probe signal'
                    split = phrase['PhraseText'].split()
                    try:
                        ind = split.index('probe')
                    except Exception as ex:
                        ind = len(split)
                    if split[ind - 2] in ['2', '3', '4', '5', '6', '7', '8', '9', '10']:
                        toAdd = split[ind - 2] + ' ' + toAdd + 's'
                    elif split[ind - 2] in ['1']:
                        toAdd = split[ind - 2] + ' ' + toAdd
                    if toAdd not in numericList[phrasePos]:
                        numericList[phrasePos].append(toAdd)
                        print('added numeric position 1')
                    if 'expressed' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('expressed')
                        if debug:
                            print("added qualifier position 8")
                # Sometimes it messes up on the probe signals
                if phrase['PhraseText'] == 'signals':
                    if phrasePos > 1:
                        if utterance['Phrases'][phrasePos - 1]['PhraseText'].endswith('probe'):
                            toAdd = 'probe signal'
                            split = (utterance['Phrases'][phrasePos - 1]['PhraseText'] + ' ' + phrase['PhraseText']).split()
                            try:
                                ind = split.index('probe')
                            except Exception as ex:
                                ind = len(split)
                            if split[ind - 2] in ['2', '3', '4', '5', '6', '7', '8', '9', '10']:
                                toAdd = split[ind - 2] + ' ' + toAdd + 's'
                            elif split[ind - 2] in ['1']:
                                toAdd = split[ind - 2] + ' ' + toAdd
                            if toAdd not in numericList[phrasePos - 1] and 'probe signals' not in ' '.join(numericList[phrasePos - 2]):
                                numericList[phrasePos - 1].append(toAdd)
                                print('added numeric position 1b')
                            if 'expressed' not in qualifierList[phrasePos - 1]:
                                qualifierList[phrasePos - 1].append('expressed')
                                if debug:
                                    print("added qualifier position 8b")

                if 'fusion signal' in phrase['PhraseText']:
                    toAdd = 'fusion signal'
                    split = phrase['PhraseText'].split()
                    ind = split.index('fusion')
                    added = False
                    if split[ind - 2] in ['2', '3', '4', '5', '6', '7', '8', '9', '10']:
                        toAdd = split[ind - 2] + ' ' + toAdd + 's'
                        added = True
                    elif split[ind - 2] in ['1']:
                        toAdd = split[ind - 2] + ' ' + toAdd
                        added = True
                    if toAdd not in numericList[phrasePos] and added:
                        numericList[phrasePos].append(toAdd)
                        print('added numeric position 2')
                    if 'expressed' not in qualifierList[phrasePos] and added:
                        qualifierList[phrasePos].append('expressed')
                        if debug:
                            print("added qualifier position 9")

                # Sometimes we use slang ('pos'), ('neg')
                if ' neg ' in ' ' + phrase['PhraseText'].lower().replace('.', '').replace(',', '') + ' ':
                    if 'negative' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('negative')
                        if debug:
                            print("added qualifier position 10")
                if ' pos ' in ' ' + phrase['PhraseText'].lower().replace('.', '').replace(',', '') + ' ' or ' positive ' in ' ' + phrase['PhraseText'].lower().replace('.', '').replace(',', '') + ' ':
                    if 'positive' not in qualifierList[phrasePos] and 'positive control' not in phrase['PhraseText'].lower().replace('.', '').replace(',', '') and \
                            not any(x in phrase['PhraseText'].lower().replace('.', '').replace(',', '') for x in ['percent positive', 'tumor positive']):
                        qualifierList[phrasePos].append('positive')
                        if debug:
                            print("added qualifier position 11")

                # Sentence boundaries are important! This is also where we'll put colon marks if they matter!
                # NOTE Phrases don't always end with periods! Let's see if we can get any periods ending words?
                for word in phrase['PhraseText'].split():
                    if word.endswith('.'):
                        for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'punc' and '.' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                                if '.' not in linkingList[phrasePos]:
                                    linkingList[phrasePos].append('.')
                                    hasIndicated = False
                    if word.endswith(':'):
                        for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'punc' and ':' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                                if ':' not in linkingList[phrasePos]:
                                    linkingList[phrasePos].append(':')
                                    hasIndicated = False
                    if word.endswith(';'):
                        for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'punc' and ';' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                                if ';' not in linkingList[phrasePos]:
                                    linkingList[phrasePos].append(';')
                                    hasIndicated = False

                    if '(' in word:
                        for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'punc' and '(' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                                if '(' not in linkingList[phrasePos]:
                                    linkingList[phrasePos].append('(')
                                    hasIndicated = False
                    if ')' in word:
                        for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'punc' and ')' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                                if ')' not in linkingList[phrasePos]:
                                    linkingList[phrasePos].append(')')
                                    hasIndicated = False
                    if ',' in word:
                        for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'punc' and ',' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                                if ',' not in linkingList[phrasePos]:
                                    linkingList[phrasePos].append(',')
                                    hasIndicated = False

                    # Let's get mutations here!
                    if len(word) > 6:
                        if word[0:3].lower() in ['ala', 'arg', 'asn', 'asp', 'cys', 'gln', 'glu', 'gly', 'his', 'ile', 'leu', 'lys', 'met', 'phe', 'pro', 'ser', 'thr', 'trp',
                                                 'tyr', 'val', 'xaa'] and (word[4].isnumeric() or word[4] == '*'):
                            if word.lower() not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(word.lower())
                                if debug:
                                    print("added biomarker position 3")
                    # and primes!
                    if word in ["3'", "5'"]:
                        if word.lower() + ' region' not in numericList[phrasePos]:
                            biomarkerList[phrasePos].append(word.lower() + ' region')
                            if debug:
                                print("added biomarker position 4")

                    # Not 100% sure I DO want this. This adds in greater than ranges - important?
                    if word.replace('<', '').replace('>', '').replace('=', '').replace('.', '').isnumeric() and ('>' in word or '<' in word) and '/' not in word \
                            and '~' + word not in utterance['UttText']:
                        toAdd = word.replace(',', '').replace('(', '')
                        if '=' + toAdd in utterance['UttText'] and (toAdd.startswith('>') or toAdd.startswith('<')):
                            char = toAdd[0]
                            toAdd = toAdd[1:]
                            toAdd = char + '=' + toAdd
                        while toAdd.endswith('.'):
                            toAdd = toAdd[:-1]
                        if toAdd not in numericList[phrasePos]:
                            numericList[phrasePos].append(toAdd)
                            print('added numeric position 3')

                    # This is for fusion signals
                    if word.replace('=', '').replace('f', '').replace('F', '').replace('.', '').isnumeric() and '=' in word:
                        if '>' + word in utterance['UttText'] or '<' + word in utterance['UttText']:
                            if '>' + word in utterance['UttText']:
                                if '>' + word not in numericList[phrasePos]:
                                    numericList[phrasePos].append('>' + word)
                                    print('added numeric position 25a')
                            if '<' + word in utterance['UttText']:
                                if '<' + word not in numericList[phrasePos]:
                                    numericList[phrasePos].append('<' + word)
                                    print('added numeric position 25b')
                    if word.replace('f', '').replace('F', '').replace('>', '').replace('<', '').isnumeric() and 'f' in word.lower() and ('>' in word.lower() or '<' in word.lower()):
                        if word not in numericList[phrasePos]:
                            numericList[phrasePos].append(word)
                            print('added numeric position 25c')

                    # Here we'll get stuff like 'combined positive = 2'
                    if word.isnumeric():
                        if '= ' + word in phrase['PhraseText']:
                            if word not in numericList[phrasePos]:
                                numericList[phrasePos].append(word)
                                print('added numeric position 25c')

                    # Getting some centromere names here!
                    if 'cen' in word:
                        if word.replace('cen', '').replace('(', '').replace(',', '').isnumeric() and 'nuc ish' not in phrase['PhraseText']:
                            if word.replace('(', '') not in biomarkerList[phrasePos]:
                                dontadd = False
                                # If this biomarker is part of a nuc ish, don't add it!
                                allBio = ' '.join(list(itertools.chain.from_iterable(biomarkerList)))
                                if 'nuc ish' in allBio:
                                    for bt in allBio.split(','):
                                        if 'nuc ish' in bt or ('[' in bt and ']' in bt) and word.replace('(', '') in bt:
                                            dontadd = True
                                if not dontadd:
                                    biomarkerList[phrasePos].append(word.replace('(', '').replace(',', ''))
                                    if debug:
                                        print("added biomarker position 5")

                    # Getting some aberrant probe names that don't fit otherwise here (we don't want sp#, as these are clone names)
                    if word.replace('d', '').replace('z', '').replace('s', '').replace('(', '').replace('p', '').replace('.', '').isnumeric() and \
                            ('d' in word or 'z' in word or 's' in word or "5'" in word or "3'" in word or 'p' in word) and not word.replace('sp', '').isnumeric():
                        dontadd = True
                        if word.replace('(', '') not in biomarkerList[phrasePos]:
                            if phrasePos > 0:
                                if '(' in word and word in ''.join(biomarkerList[phrasePos - 1]):
                                    continue
                                dontadd = False
                                # If this biomarker is part of a nuc ish, don't add it!
                                allBio = ' '.join(list(itertools.chain.from_iterable(biomarkerList)))
                                if 'nuc ish' in allBio:
                                    for bt in allBio.split(','):
                                        if 'nuc ish' in bt or ('[' in bt and ']' in bt) and word in bt:
                                            dontadd = True
                            if not dontadd:
                                biomarkerList[phrasePos].append(word.replace('(', ''))
                                if debug:
                                    print("added biomarker position 6")

                    if "5'" in word or "3'" in word:
                        if 'mll' in word:
                            if word.replace('(', '') not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(word.replace('(', ''))
                                if debug:
                                    print("added biomarker position 7")

                    # Sometimes the p. doesn't get picked up. Let's try here!
                    if 'p.' in word and not word.endswith('p.'):
                        if phrasePos < len(utterance['Phrases']) - 1:
                            if '>' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                                word = word + utterance['Phrases'][phrasePos + 1]['PhraseText'].replace(',', '').replace('.', '').split()[0]
                        if ('p.(' in word or '(p.' in word) and not word.endswith(')'):
                            word = word + ')'
                        if word not in qualifierList[phrasePos]:
                            qualifierList[phrasePos].append(word)
                            print('added qualifier position 73')

                    # Sometimes the c. doesn't get picked up. Let's try here!
                    # Experimental: Maybe we never want this as a biomarker?
                    if 'c.' in word and not word.endswith('c.'):
                        if phrasePos < len(utterance['Phrases']) - 1:
                            if '>' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                                word = word + utterance['Phrases'][phrasePos + 1]['PhraseText'].replace(',', '').replace('.', '').split()[0]
                        # if word.replace('(', '') not in biomarkerList[phrasePos]:
                        #    biomarkerList[phrasePos].append(word.replace('(', ''))
                        #    print('added biomarker position 126b')

                    # I think getting dates will be pretty easy. In fact, so easy, I think we can do it all right here!
                    if '/' in word and word.replace('/', '').replace('-', '').replace('.', '').replace(',', '').isnumeric():
                        toAdd = word
                        while toAdd.endswith('/') or toAdd.endswith('.') or toAdd.endswith(',') or toAdd.endswith('-'):
                            toAdd = toAdd[:-1]
                        isDate = False
                        if len(toAdd.split('\\')) == 2:
                            toAddSplit = toAdd.split('\\')
                            if (len(toAddSplit[0]) == 4 and len(toAddSplit[1]) == 2) or (len(toAddSplit[0]) == 2 and len(toAddSplit[1]) == 4):
                                isDate = True
                        if isDate:
                            if toAdd not in timeList[phrasePos]:
                                timeList[phrasePos].append(toAdd)
                                print('added time position 1')

                # Some things require us to look at the syntax unit. These list the part of speech, so we'll pull out all the adverbs
                for SU in range(0, len(phrase['SyntaxUnits'])):
                    if phrase['SyntaxUnits'][SU]['SyntaxType'] == "adv":
                        if 'adv' not in partOfSpeechList[phrasePos]:
                            partOfSpeechList[phrasePos].append('adv')

                    # This is in here to grab the c. and p. variations, which will NOT be recognized.
                    if phrase['SyntaxUnits'][SU]['SyntaxType'] == 'mod' and phrase['SyntaxUnits'][SU]['InputMatch'].replace(' ', '') == 'c.':
                        toAdd = phrase['SyntaxUnits'][SU]['LexMatch'].replace(' ', '')
                        if len(phrase['SyntaxUnits']) - 1 > SU:
                            toAdd = toAdd + phrase['SyntaxUnits'][SU + 1]['InputMatch']
                            # It's bad at picking up c.s or p.s with a '_' in the middle
                            if len(phrase['SyntaxUnits']) - 3 > SU:
                                if phrase['SyntaxUnits'][SU + 2]['InputMatch'] in ['_', '+', ]:
                                    toAdd = toAdd + phrase['SyntaxUnits'][SU + 2]['InputMatch'] + phrase['SyntaxUnits'][SU + 3]['InputMatch']
                            if len(utterance['Phrases']) - 1 > phrasePos:
                                if '>' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                                    toAdd = toAdd + utterance['Phrases'][phrasePos + 1]['PhraseText'].replace(',', '').replace('.', '').split()[0]
                            if toAdd.lower() not in qualifierList[phrasePos] and toAdd.lower() not in ' '.join(qualifierList[phrasePos]):
                                qualifierList[phrasePos].append(toAdd.lower())
                                if debug:
                                    print("added qualifier position 72")

                    if phrase['SyntaxUnits'][SU]['SyntaxType'] == 'mod' and phrase['SyntaxUnits'][SU]['InputMatch'].replace(' ', '') == 'p.':
                        toAdd = phrase['SyntaxUnits'][SU]['LexMatch'].replace(' ', '')
                        if not toAdd.endswith('.'):
                            toAdd = toAdd + '.'
                        if len(phrase['SyntaxUnits']) - 1 > SU:
                            toAdd = toAdd + phrase['SyntaxUnits'][SU + 1]['InputMatch']
                            if toAdd.lower() not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(toAdd.lower())
                                if debug:
                                    print("added biomarker position 9")

                            if phrasePos > 0:
                                # here, we'll attempt to grab a common biomarker (like 'kras') if it's applied to multiple p.'s
                                if biomarkerList[phrasePos - 1]:
                                    if 'p.' in ' '.join(biomarkerList[phrasePos - 1]):
                                        for biomarker in biomarkerList[phrasePos - 1]:
                                            if 'p.' not in biomarker and 'exon' not in biomarker:
                                                if biomarker not in biomarkerList[phrasePos]:
                                                    biomarkerList[phrasePos].append(biomarker)
                                                    if debug:
                                                        print("added biomarker position 10")

                # Does not appear doesn't show up for negations?
                if any(x in utterance['UttText'] for x in ['does not appear']):
                    if 'negative' not in qualifierList[0]:
                        qualifierList[0] = ['negative']
                        print('added qualifier position 78')

                # Maybe not the place for it? But sometimes a 'trisomy 1 and 3' will be in separate phrases. This gets the
                # second one.
                if phrase['PhraseText'].replace('.', '').replace(',', '').isnumeric() and phrasePos > 1:
                    if any(x in linkingList[phrasePos - 1] for x in ['or', 'and']) and conceptList[phrasePos - 2]:
                        if biomarkerList[phrasePos - 2]:
                            if biomarkerList[phrasePos - 2][0].split()[0].lower() in 'chromosome':
                                toAdd = 'chromosome ' + phrase['PhraseText'].replace('.', '').replace(',', '')
                        # else:
                        #    toAdd = phrase['PhraseText'].replace('.', '').replace(',', '')
                        # if toAdd.lower() not in biomarkerList[phrasePos] and toAdd not in biomarkerList[phrasePos]:
                        #    biomarkerList[phrasePos].append(toAdd.lower())
                        #    if debug:
                        #        print("added biomarker position 11")

                # Let's pull out the 'nuc ish' name wherever it is!
                if 'nuc ish' in phrase['PhraseText']:
                    postNucIsh = utterance['UttText'].split('nuc ish')[1].strip()
                    # I'm ASSUMING that a 'nuc ish' always ends with a []
                    if '[' in postNucIsh:
                        gene = 'nuc ish ' + postNucIsh.split('[')[0]
                        rest = postNucIsh.split('[')[1]
                        indexEndBracket = rest.index(']')
                        rest = rest[0:indexEndBracket]
                        if gene not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append(gene)
                            if debug:
                                print("added biomarker position 12")

                        if rest not in numericList[phrasePos]:
                            numericList[phrasePos].append(rest)
                            print('added numeric position 4')
                        # Now we're gonna see if there are MULTIPLE of these chained
                        pp = phrasePos
                        while ']' in postNucIsh:
                            pp = pp + 1
                            try:
                                endPos = postNucIsh.index(rest + ']')
                            except:
                                break
                            postNucIsh = postNucIsh[endPos + len(rest) + 1:].strip()
                            if not postNucIsh:
                                break
                            postNucIshSplit = postNucIsh.split()[0]
                            if postNucIshSplit[0] in ['/', '\\', ','] and '[' in postNucIshSplit:
                                if postNucIshSplit[0] == ',':
                                    postNucIsh = postNucIshSplit[1:]
                                gene = 'nuc ish ' + postNucIsh.split('[')[0]
                                gene = gene.replace('\\ ', '').replace('/ ', '')
                                rest = postNucIsh.split('[')[1]
                                indexEndBracket = rest.index(']')
                                rest = rest[0:indexEndBracket]
                                if gene not in biomarkerList[pp]:
                                    biomarkerList[pp].append(gene)
                                    print('added chained nuc ish biomarker')

                                if rest not in numericList[pp]:
                                    numericList[pp].append(rest)
                                endPos = postNucIsh.index(rest + ']')
                                postNucIsh = postNucIsh[endPos + len(rest) + 1:].strip()

                qName = ''
                # We don't seem to be GREAT at the whole 'knowing what ##q## is' thing. Let's add them in.
                if 'nuc ish' in phrase['PhraseText']:
                    postNucIsh = phrase['PhraseText'].split('nuc ish')[1].strip()
                    if postNucIsh.replace('q', '').replace('.', '').replace(',', '').isnumeric() and 'q' in postNucIsh:
                        qName = postNucIsh
                elif 'chromosome' in phrase['PhraseText'].replace('chromosomes', 'chromosome'):
                    postChromosomeWord = phrase['PhraseText'].replace('chromosomes', 'chromosome').split('chromosome')[1].strip()
                    if len(postChromosomeWord.split()) > 1:
                        postChromosomeWord = postChromosomeWord.split()[0]
                    if postChromosomeWord.replace('q', '').replace('.', '').replace(',', '').isnumeric() and 'q' in postChromosomeWord:
                        qName = postChromosomeWord
                    # This can be a sneaky way to get [chromosome 13] when its' not properly tagged
                    elif postChromosomeWord.replace('q', '').replace('.', '').replace(',', '').isnumeric() and 'q' not in postChromosomeWord:
                        if 'chromosome ' + postChromosomeWord.replace('q', '').replace('.', '').replace(',', '').lower() not in biomarkerList[phrasePos] and not hasSetsOrig:
                            biomarkerList[phrasePos].append('chromosome ' + postChromosomeWord.replace('q', '').replace('.', '').replace(',', '').lower())
                            if debug:
                                print("added biomarker position 13")
                    if len(phrase['PhraseText'].split('chromosome')[1].strip().split()) > 1:
                        if phrase['PhraseText'].split('chromosome')[1].strip().split()[1] == 'critical':
                            if phrase['PhraseText'].split('chromosome')[1].strip().split()[2] == 'region':
                                qName = qName + ' critical region'
                elif re.findall('[0-9]+q[0-9]+.?[0-9]*p?q?[0-9]?', phrase['PhraseText']):
                    index = re.findall('[0-9]+q[0-9]+.?[0-9]*p?q?[0-9]*', phrase['PhraseText'])
                    term = index[0]
                    if term.lower() not in biomarkerList[phrasePos] and term.lower() + '/' not in phrase['PhraseText'] and '/' + term.lower() not in phrase['PhraseText'] and 'nuc ish' not in phrase[
                        'PhraseText']:
                        isProbe = False
                        for x in biomarkerList:
                            x = ''.join(x)
                            if 'nuc ish' in x and term.lower() in x:
                                isProbe = True
                        if not isProbe:
                            biomarkerList[phrasePos].append(term.lower())
                            if debug:
                                print("added biomarker position 14")


                else:
                    if phrase['PhraseText'].replace('q', '').replace('.', '').replace(',', '').replace('the', '').strip().isnumeric() and 'q' in phrase['PhraseText']:
                        if phrase['PhraseText'].replace('.', '').replace(',', '').replace('the', '').strip() not in biomarkerList[phrasePos]:
                            qName = phrase['PhraseText'].replace(',', '').replace('the', '').strip()
                            if qName.endswith('.'):
                                qName = qName[:-1]
                if qName:
                    place = phrasePos + 1
                    if '(' in qName:
                        while utterance['Phrases'][place]['PhraseText'] != ')':
                            qName = qName + utterance['Phrases'][phrasePos + 1]['PhraseText']
                            place = place + 1
                        qName = qName + ')'
                    place = place + 1
                    if qName.lower() not in biomarkerList[phrasePos] and not hasSetsOrig:
                        biomarkerList[phrasePos].append(qName.lower())
                        if debug:
                            print("added biomarker position 15")

                    # Sometiems we have ([gene] locus) after the q.
                    if len(utterance['Phrases']) > phrasePos + 2:
                        if '(' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                            toAdd = utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('(', '')
                            place = phrasePos + 2
                            while ')' not in utterance['Phrases'][place]['PhraseText']:
                                toAdd = toAdd + utterance['Phrases'][place]['PhraseText']
                                if place < len(utterance['Phrases']) - 1:
                                    place = place + 1
                                else:
                                    break
                            toAdd = toAdd + ')'

                            if toAdd.lower() not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(toAdd.lower())
                                if debug:
                                    print("added biomarker position 16")

                    if len(utterance['Phrases']) > place:
                        if '[' in utterance['Phrases'][place]['PhraseText']:
                            numericList[phrasePos].append(utterance['Phrases'][place]['PhraseText'] + ']')
                            print('added numeric position 5')

                # Sometimes the negations don't work out super well, so let's add one for 'no evidence' here
                if 'no evidence' in phrase['PhraseText']:
                    if 'negative' not in qualifierList[phrasePos] and 'normal results' not in biomarkerList[phrasePos]:
                        qualifierList[phrasePos].append('negative')
                        if debug:
                            print("added qualifier position 12")

                if 'negative' in phrase['PhraseText'].lower():
                    if 'negative' not in qualifierList[phrasePos] and 'normal results' not in biomarkerList[phrasePos]:
                        qualifierList[phrasePos].append('negative')
                        if debug:
                            print("added qualifier position 13")

                if 'not' in phrase['PhraseText'].lower():
                    if len(utterance['Phrases']) > phrasePos + 1:
                        if 'detected' in utterance['Phrases'][phrasePos + 1]['PhraseText'].lower() or 'detected' in utterance['Phrases'][phrasePos]['PhraseText'].lower():
                            if 'negative' not in qualifierList[phrasePos] and 'normal results' not in biomarkerList[phrasePos]:
                                qualifierList[phrasePos].append('negative')
                                if debug:
                                    print("added qualifier position 14")
                # This might be unnecessary - we give everything positives at the end now.
                # if 'is ' in phrase['PhraseText'].lower():
                #    if len(utterance['Phrases']) > phrasePos + 1:
                #        if 'detected' in utterance['Phrases'][phrasePos + 1]['PhraseText'].lower() or 'detected' in utterance['Phrases'][phrasePos]['PhraseText'].lower():
                #            if 'positive' not in qualifierList[phrasePos]:
                #                qualifierList[phrasePos].append('positive')
                #                if debug:
                #                    print("added qualifier position 15")

                # And one for 'other than'
                if 'other than' in phrase['PhraseText']:
                    if 'Other Than' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('other than')
                        if debug:
                            print("added qualifier position 16")

                # And one for TPS
                if ' tps ' in phrase['PhraseText'].lower().replace('(', ' ') + ' ' or 'tumor proportion score' in phrase['PhraseText'].lower():
                    if 'tumor proportion score' not in conceptList[phrasePos]:
                        conceptList[phrasePos].append('tumor proportion score')
                        if debug:
                            print("added concept position 3")

                # And one for MSI
                if ' msi ' in phrase['PhraseText'].lower().replace('(', ' ') + ' ' or 'microsatellite instability' in phrase['PhraseText'].lower():
                    if 'microsatellite instability' not in conceptList[phrasePos]:
                        conceptList[phrasePos].append('ngs')
                        print('added concept position 56')
                    if 'microsatellite instability' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('microsatellite instability')
                        print('added biomarker position 128')

                # 'These Results' is something they often say when they start opining. Add it as a stopper
                # Talking about a previous test is the same, I think. Or associations. "Slides" is a good ending candidate
                # For alk rearrangements
                toFind = re.compile('these results|previous|associated|please refer|are observed')
                match_obj = toFind.search(phrase['PhraseText'])
                if match_obj:
                    linkingList[phrasePos].append('end$$$$' + match_obj.group(0))
                    if phrasePos == 0:
                        biomarkerList[phrasePos].append('Test Not Performed')
                        if debug:
                            print("added biomarker position 17")

                # HIGHLY EXPERIMENTAL - IF THE RESULT SAYS 'ARE OBSERVED', WE MIGHT WANT TO BLANK OUT THE REST OF THAT
                # PHRASE. CHANGE IF NEEDED
                if 'are ' in phrase['PhraseText'] and len(utterance['Phrases']) > phrasePos + 1:
                    if 'observed' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                        qualifierList[phrasePos].append('frequently observed')
                        if debug:
                            print("added qualifier position 17")

                if any(x in utterance['UttText'] for x in ['unlikely to yield a different result']):
                    if 'Rejected By Lab - unlikely new result' not in conceptList[0]:
                        conceptList[0].append("Rejected By Lab - unlikely new result")

                #   NOTE NOTE: This section is going away once I add these terms to the dictionary!
                # I hope this is the only blind spot, but 'myc' never gets detected.
                if 'myc' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ' and 'mycn' not in phrase['PhraseText']:
                    if ' myc ' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('myc')
                        if debug:
                            print("added biomarker position 18")
                # No. met is also missing. Hmph.
                if ' met ' in ' ' + phrase['PhraseText'].replace(',', '').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'met' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('met')
                        if debug:
                            print("added biomarker position 127")
                # No. Abl1 is also missing. Hmph.
                if ' abl1 ' in ' ' + phrase['PhraseText'].replace(',', '').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'abl1' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('abl1')
                        if debug:
                            print("added biomarker position 19")
                # No. Runx1 is also missing. Hmph.
                if ' runx1 ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'runx1' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('runx1')
                        if debug:
                            print("added biomarker position 20")
                # CCND1 is IN, but not picked up well? Odd.
                if ' ccnd1 ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'ccnd1' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('ccnd1')
                        if debug:
                            print("added biomarker position 21")
                # I'm not even sure what mll is, but it's in some reports.
                if ' mll ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'mll' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('mll')
                        if debug:
                            print("added biomarker position 22")
                # 5/9/15 is in some reports - it's a triple trisomy test.
                if ' 5/9/15 ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'chromosome 5' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('chromosome 5')
                        print('added 5/9/15')
                    if 'chromosome 9' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('chromosome 9')
                        print('added 5/9/15')
                    if 'chromosome 15' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('chromosome 15')
                        print('added 5/9/15')
                    if 'trisomy' not in conceptList[phrasePos]:
                        conceptList[phrasePos].append('trisomy')
                        print('added 5/9/15')
                # CBFB is another blind spot
                if ' cbfb ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'cbfb' not in biomarkerList[phrasePos] and 'cbfb-' not in ' '.join(list(itertools.chain.from_iterable(biomarkerList))):
                        biomarkerList[phrasePos].append('cbfb')
                        if debug:
                            print("added biomarker position 23")
                # blc2 is another blind spot
                if ' blc2 ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'blc2' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('blc2')
                        if debug:
                            print("added biomarker position 24")
                # We don't know that ROS-1 is ROS1
                if ' ros 1 ' in ' ' + phrase['PhraseText'].replace(',', '').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'ros1' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('ros1')
                        if debug:
                            print("added biomarker position 25")
                # rara is another blind spot
                if ' rara ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'rara' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('rara')
                        if debug:
                            print("added biomarker position 26")
                # egfrviii is another blind spot
                if ' egfrviii ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('-', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'egfr-viii' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('egfr-viii')
                        if debug:
                            print("added biomarker position 27")
                # pax-8 is another blind spot
                if ' pax-8 ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ':
                    if 'pax-8' not in biomarkerList[phrasePos]:
                        biomarkerList[phrasePos].append('pax-8')
                        if debug:
                            print("added biomarker position 28")
                # immunostain is another blind spot
                if ' immunostain ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ' or \
                        ' immunostaining ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('(', ' ').replace(':', ' ').lower() + ' ' or \
                        ' immunostains ' in ' ' + phrase['PhraseText'].replace(',', ' ').replace('.', ' ').replace('(', ' ').replace(':', ' ').lower():
                    if 'immunostain' not in conceptList[phrasePos]:
                        conceptList[phrasePos].append('immunostain')
                        print('added concept position 47')

                # We don't know PD-L1 antibodies, which makes some sense. If we have pd-l1 right before this, add it!
                # that means it's like PD-L1 (22c3)
                if ' 28-8 ' in ' ' + phrase['PhraseText'].replace(',', '').replace('(', '').lower() + ' ' or '28 8' in phrase['PhraseText']:
                    if phrasePos > 0:
                        if 'pd-l1' in biomarkerList[phrasePos - 1]:
                            if '28-8 pharmDx clone' not in biomarkerList[phrasePos - 1]:
                                biomarkerList[phrasePos - 1].append('28-8 pharmDx clone')
                            else:
                                if 'pd-l1' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('pd-l1')
                                    if debug:
                                        print("added biomarker position 29")
                                if '28-8 pharmDx clone' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('28-8 pharmDx clone')
                                    if debug:
                                        print("added biomarker position 30")
                    else:
                        if 'pd-l1' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('pd-l1')
                            if debug:
                                print("added biomarker position 31")
                        if '28-8 pharmDx clone' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('28-8 pharmDx clone')
                            if debug:
                                print("added biomarker position 32")
                # We don't know PD-L1 antibodies, which makes some sense.
                if ' 22c3 ' in ' ' + phrase['PhraseText'].replace(',', '').replace('(', ' ').lower() + ' ' or \
                        ' 22c3pharmadx ' in ' ' + phrase['PhraseText'].replace(',', '').replace('(', ' ').lower() + ' ':
                    if phrasePos > 0:
                        if 'pd-l1' in biomarkerList[phrasePos - 1]:
                            if 'pharmDx' not in biomarkerList[phrasePos - 1]:
                                biomarkerList[phrasePos - 1].append('22c3 pharmDx clone')
                        else:
                            if 'pd-l1' not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append('pd-l1')
                                if debug:
                                    print("added biomarker position 33")
                            if 'pharmDx' not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append('22c3 pharmDx clone')
                                if debug:
                                    print("added biomarker position 34")
                    else:
                        if 'pd-l1' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('pd-l1')
                            if debug:
                                print("added biomarker position 35")
                        if 'pharmDx' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('22c3 pharmDx clone')
                            if debug:
                                print("added biomarker position 36")
                # We don't know PD-L1 antibodies, which makes some sense. If we have pd-l1 right before this, add it!
                # that means it's like PD-L1 (22c3)
                if ' sp28-8 ' in ' ' + phrase['PhraseText'].replace(',', '').replace('(', '').lower() + ' ':
                    if phrasePos > 0:
                        if 'pd-l1' in biomarkerList[phrasePos - 1]:
                            if 'sp28-8' not in biomarkerList[phrasePos - 1]:
                                biomarkerList[phrasePos - 1].append('sp28-8 antibody')
                            else:
                                if 'pd-l1' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('pd-l1')
                                    if debug:
                                        print("added biomarker position 37")
                                if 'sp28-8 antibody' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('sp28-8 antibody')
                                    if debug:
                                        print("added biomarker position 38")
                    else:
                        if 'pd-l1' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('pd-l1')
                            if debug:
                                print("added biomarker position 39")
                        if 'sp28-8 antibody' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('sp28-8 antibody')
                            if debug:
                                print("added biomarker position 40")
                # We don't know PD-L1 antibodies, which makes some sense. If we have pd-l1 right before this, add it!
                # that means it's like PD-L1 (22c3)
                if ' sp263 ' in ' ' + phrase['PhraseText'].replace(',', '').replace('(', '').lower() + ' ':
                    if phrasePos > 0:
                        if 'pd-l1' in biomarkerList[phrasePos - 1]:
                            if 'sp263 clone' not in biomarkerList[phrasePos - 1]:
                                biomarkerList[phrasePos - 1].append('sp263 clone')
                                if debug:
                                    print("added biomarker position 41")
                            else:
                                if 'sp263 clone' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('pd-l1')
                                    if debug:
                                        print("added biomarker position 42")
                                if 'sp263 clone' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('sp263 clone')
                                    if debug:
                                        print("added biomarker position 43")
                    else:
                        if 'pd-l1' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('pd-l1')
                            if debug:
                                print("added biomarker position 44")
                        if 'sp263 clone' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('sp263 clone')
                            if debug:
                                print("added biomarker position 45")

                # We don't know PD-L1 antibodies, which makes some sense. If we have pd-l1 right before this, add it!
                # that means it's like PD-L1 (22c3)
                if ' sp142 ' in ' ' + phrase['PhraseText'].replace(',', '').replace('(', '').lower() + ' ':
                    if phrasePos > 0:
                        if 'pd-l1' in biomarkerList[phrasePos - 1]:
                            if 'sp142 clone' not in biomarkerList[phrasePos - 1]:
                                biomarkerList[phrasePos - 1].append('sp142 clone')
                                if debug:
                                    print("added biomarker position 41a")
                            else:
                                if 'sp142 clone' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('pd-l1')
                                    if debug:
                                        print("added biomarker position 42a")
                                if 'sp142 clone' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('sp142 clone')
                                    if debug:
                                        print("added biomarker position 43a")
                    else:
                        if 'pd-l1' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('pd-l1')
                            if debug:
                                print("added biomarker position 44a")
                        if 'sp142 clone' not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append('sp142 clone')
                            if debug:
                                print("added biomarker position 45a")

                # This one is actually an estrogen receptor one
                if ' sp1 ' in ' ' + phrase['PhraseText'].replace(',', '').replace('(', '').lower() + ' ':
                    if phrasePos > 0:
                        if 'estrogen receptor' in biomarkerList[phrasePos - 1]:
                            if 'ventana sp1 clone' not in biomarkerList[phrasePos - 1]:
                                biomarkerList[phrasePos - 1].append('ventana sp1 clone')
                                if debug:
                                    print("added biomarker position 128a")
                            else:
                                if 'sp142 clone' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('estrogen receptor')
                                    if debug:
                                        print("added biomarker position 128a")
                                if 'sp142 clone' not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append('ventana sp1 clone')
                                    if debug:
                                        print("added biomarker position 128c")
                        else:
                            if 'estrogen receptor' not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append('estrogen receptor')
                                if debug:
                                    print("added biomarker position 128a")
                            if 'ventana sp1 clone' not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append('ventana sp1 clone')
                                if debug:
                                    print("added biomarker position 128a")

                # It looks like 'unbalanced' isn't something we easily pull out.
                if 'unbalanced' in phrase['PhraseText']:
                    if 'unbalanced' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('unbalanced')
                        if debug:
                            print("added qualifier position 18")

                # Cannot be determined
                if 'determined' in phrase['PhraseText'].lower():
                    if utterance['Phrases'][phrasePos - 2]['PhraseText'].lower() in ['cannot']:
                        if 'indeterminate' not in qualifierList[phrasePos]:
                            qualifierList[phrasePos].append('indeterminate')
                            if debug:
                                print('added qualifier position 68')

                # EXPERIMENTAL: If a whole phrase is just a #, and we don't have it registered yet, maybe append it?
                if utterance['Phrases'][phrasePos]['PhraseText'].replace(',', '').replace('.', '').isnumeric():
                    isExonOrAA = False
                    pos = phrasePos

                    # We also don't want to have ones in location "chr##:103231"
                    if phrasePos > 1:
                        if utterance['Phrases'][phrasePos - 1]['PhraseText'] == ':' and 'chr' in utterance['Phrases'][phrasePos - 2]['PhraseText']:
                            isExonOrAA = True

                    # Go back until 1) we reach the beginning, or 2) we reach a non-numeric phrase. If that first non-numeric phrase
                    # has 'exon' or 'aa' in it, don't take those numbers. We are also including "# of observers". Rare but seen.
                    while pos >= 0:
                        if any(x in utterance['Phrases'][pos]['PhraseText'].replace(',', '').replace('.', '').replace('exons', 'exon').lower() for x in ['exon', '(aa', 'observers']):
                            isExonOrAA = True
                        elif not utterance['Phrases'][pos]['PhraseText'].replace(',', '').replace('.', '').isnumeric() and \
                                utterance['Phrases'][pos]['PhraseText'].replace(',', '').replace('.', '') not in ['and', ':']:
                            break
                        pos = pos - 1
                    # Here we're eliminating things like '3 to 8 copies'
                    if len(utterance['Phrases']) - 1 > phrasePos:
                        if utterance['Phrases'][phrasePos + 1]['PhraseText'].split()[0] in ['to']:
                            isExonOrAA = True
                    if utterance['Phrases'][phrasePos]['PhraseText'].replace(',', '').replace('.', '').lower() not in ''.join(biomarkerList[phrasePos]) and not isExonOrAA:
                        item = utterance['Phrases'][phrasePos]['PhraseText']
                        if int(utterance['Phrases'][phrasePos]['PhraseText'].replace(',', '').replace('.', '').lower()) < 27 and not ('.' in item and not item.endswith('.')) \
                                and 'is ' + item not in utterance['UttText'] and not any(time in utterance['UttText'] for time in [item + ':', ':' + item]):
                            biomarkerList[phrasePos].append(utterance['Phrases'][phrasePos]['PhraseText'].replace(',', '').replace('.', '').lower())
                            if debug:
                                print("added biomarker position 46")
                        # we want to be ok with periods ONLY as a ender (like '2.', stuff like 2.34 gets picked up elsewhere)
                        elif 'is ' + item in utterance['UttText'] and ('.' not in utterance['Phrases'][phrasePos]['PhraseText'][:-1]):
                            numericList[phrasePos].append(utterance['Phrases'][phrasePos]['PhraseText'].replace(',', '').replace('.', '').lower())
                            if debug:
                                print("added numeric position bio-46")

                # If we see "(2.2x), it means that's an amplification
                if utterance['Phrases'][phrasePos]['PhraseText'].replace(',', '').replace('.', '').replace('(', '').replace('x', '').isnumeric() and 'x' in utterance['Phrases'][phrasePos][
                    'PhraseText']:
                    if utterance['Phrases'][phrasePos]['PhraseText'].replace(',', '').replace('(', '') not in numericList[phrasePos]:
                        numericList[phrasePos].append(utterance['Phrases'][phrasePos]['PhraseText'].replace(',', '').replace('(', ''))
                        print('added numeric position 6')

                # It's a bit tricky pulling out fusion markings, but let's attempt it here! It's important to note
                # for comprehension that fusions normally begin a phrase, and start with an open parentheses. There
                # will then be an number of phrases worth of alphanumeric stuff, then the closing parenthases will, I think,
                # always be it's own phrase. No idea why. Also, sometimes the fusion will have a leading character.
                # T - transformation.
                if phrase['PhraseText'].startswith('('):
                    if phrasePos > 0:
                        if utterance['Phrases'][phrasePos - 1]['PhraseText'].endswith(' t'):
                            toAdd = 't' + phrase['PhraseText']
                            location = phrasePos + 1
                            while ')' not in utterance['Phrases'][location]['PhraseText']:
                                toAdd = toAdd + utterance['Phrases'][location]['PhraseText']
                                location = location + 1
                            toAdd = toAdd + ')'
                            biomarkerList[phrasePos].append(toAdd.lower())
                            if debug:
                                print("added biomarker position 47")

                # Making this lower for the Dups into dups
                phrase['PhraseText'] = phrase['PhraseText'].lower()
                if 't(' in phrase['PhraseText'] or ('del' in phrase['PhraseText'] and 'dele' not in phrase['PhraseText'] and 'deli' not in phrase['PhraseText']) \
                        or ('dup' in phrase['PhraseText'] and 'dupli' not in phrase['PhraseText']) \
                        or ('inv' in phrase['PhraseText'] and 'inve' not in phrase['PhraseText'] and 'inva' not in phrase['PhraseText']):
                    match = 'n0m4tch'
                    splitPhrase = phrase['PhraseText'].split()
                    for word in splitPhrase:
                        if 't(' in word or 'del' in word or 'dup' in word or 'inv' in word:
                            match = word
                    matchLocation = phrase['PhraseText'].split().index(match)
                    toAdd = phrase['PhraseText'].split()[matchLocation]
                    location = phrasePos + 1
                    if '(' in word:
                        while ')' not in utterance['Phrases'][location]['PhraseText'].replace('.', ' '):
                            word = word + utterance['Phrases'][location]['PhraseText']
                            location = location + 1
                        word = word + ')'
                        if word.startswith('t('):
                            toAdd = word
                        elif toAdd in word:
                            toAdd = word
                        else:
                            toAdd = toAdd + word
                        if toAdd.startswith('/'):
                            toAdd = toAdd[1:]
                        if toAdd.startswith('t('):
                            if 'translocation' not in conceptList[phrasePos]:
                                conceptList[phrasePos].append('translocation')
                                if debug:
                                    print('added concept position 59a')
                        if toAdd.startswith('inv('):
                            if 'inversion' not in conceptList[phrasePos]:
                                conceptList[phrasePos].append('inversion')
                                if debug:
                                    print('added concept position 59b')

                    # Fusion transcript names
                    if len(utterance['Phrases']) > location + 1:
                        if '-' in utterance['Phrases'][location + 1]['PhraseText'].split()[0] and 'fusion' in utterance['Phrases'][location + 1]['PhraseText']:
                            uttPos = 0
                            while utterance['Phrases'][location + 1]['PhraseText'].split()[uttPos].replace(',', '') != 'fusion':
                                toAdd = toAdd + ' ' + utterance['Phrases'][location + 1]['PhraseText'].split()[uttPos]
                                uttPos = uttPos + 1
                    while toAdd.startswith('/'):
                        toAdd = toAdd[1:]
                    if toAdd in ['del', 'inv', 'dup']:
                        phrPos = phrasePos + 1
                        if ')' in utterance['UttText'][utterance['UttText'].index(utterance['Phrases'][phrasePos]['PhraseText']):]:
                            while utterance['Phrases'][phrPos]['PhraseText'] != ')':
                                toAdd = toAdd + utterance['Phrases'][phrPos]['PhraseText']
                                phrPos = phrPos + 1
                            toAdd = toAdd + ')'
                    # Add the check for deletion here
                    if toAdd.startswith('del('):
                        if 'deletion' not in conceptList[phrasePos]:
                            conceptList[phrasePos].append('deletion')
                            if debug:
                                print('added concept position 59c')
                    if toAdd.lower() not in biomarkerList[phrasePos] and not toAdd.startswith(('c.', 'p.')):
                        biomarkerList[phrasePos].append(toAdd.lower())
                    if debug:
                        print("added biomarker position 48")

                # Let's here extract a common problem - reasons for failure
                phr = phrase['PhraseText']
                if len(utterance['Phrases']) - 1 > phrasePos + 1:
                    phr = phr + ' ' + utterance['Phrases'][phrasePos + 1]['PhraseText'] + ' ' + utterance['Phrases'][phrasePos + 2]['PhraseText']
                elif len(utterance['Phrases']) - 1 > phrasePos + 1:
                    phr = phr + ' ' + utterance['Phrases'][phrasePos + 1]['PhraseText']

                if any(substring in phr for substring in ['insufficient amount', 'QNS', 'not sufficient', 'insufficient quantity', 'insufficient tumor tissue', 'lack of relevant tissue']):
                    if ['qns'] not in qualifierList:
                        qualifierList[phrasePos].append('qns')
                        if debug:
                            print("added qualifier position 19")
                if 'poor quantity' in phr:
                    if ['poor quantity'] not in qualifierList:
                        qualifierList[phrasePos].append('poor quantity')
                        if debug:
                            print("added qualifier position 20")
                if 'poor quality' in phr:
                    if ['poor quality'] not in qualifierList:
                        qualifierList[phrasePos].append('poor quality')
                        if debug:
                            print("added qualifier position 21")
                if 'poor quantity and quality' in phr:
                    if ['poor quantity'] not in qualifierList:
                        qualifierList[phrasePos].append('poor quantity')
                        if debug:
                            print("added qualifier position 22")
                    if ['poor quality'] not in qualifierList:
                        qualifierList[phrasePos].append('poor quality')
                        if debug:
                            print("added qualifier position 23")
                if 'poor quality and quantity' in phr:
                    if ['poor quantity'] not in qualifierList:
                        qualifierList[phrasePos].append('poor quantity')
                        if debug:
                            print("added qualifier position 24")
                    if ['poor quality'] not in qualifierList:
                        qualifierList[phrasePos].append('poor quality')
                        if debug:
                            print("added qualifier position 25")
                if 'wild type' in phr:
                    if 'wild type' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('wild type')
                        if debug:
                            print("added qualifier position 26")

                if 'unsuccessful' in phr or 'cannot be performed' in phr or 'can not be performed' in phr:
                    if ['test'] not in biomarkerList:
                        biomarkerList[phrasePos].append('test')
                        if debug:
                            print("added biomarker position 49")
                    if 'low cellularity' in phr:
                        if 'low cellularity' not in qualifierList[phrasePos]:
                            qualifierList[phrasePos].append('low cellularity')
                    if ['unsuccessful'] not in qualifierList:
                        qualifierList[phrasePos].append('unsuccessful')
                        if debug:
                            print("added qualifier position 27")
                if 'insufficient tumor proportion' in phr:
                    if ['insufficient tumor proportion'] not in qualifierList:
                        qualifierList[phrasePos].append('insufficient tumor proportion')
                        if debug:
                            print("added qualifier position 28")
                    if ['test not performed'] not in biomarkerList:
                        biomarkerList[phrasePos].append('test not performed')
                        if debug:
                            print("added biomarker position 50")
                # MetaMap doesn't always know what's up with fractions. We'll fix that here.
                if '/' in phrase['PhraseText']:
                    for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                        if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and '/' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch'] and '-' not in phrase['PhraseText']:
                            fraction = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].replace(' ', '').replace('.', '')
                            if fraction.split('/')[0].replace('-', '').isnumeric() and fraction.split('/')[1].replace('-', '').isnumeric():
                                if fraction not in numericList[phrasePos] and fraction not in ''.join(timeList[phrasePos]) and not ('/200' in fraction and [fraction] in numericList):
                                    numericList[phrasePos].append(fraction)
                                    print('added numeric position 7')
                # This was added for things like #/8, which show up sometime
                if '/' in phrase['PhraseText']:
                    if phrase['PhraseText'].replace('#', '').replace('/', '').replace('.', '').replace(' ', '').isnumeric():
                        if phrase['PhraseText'].replace('.', '').replace(' ', '') not in numericList[phrasePos] and phrase['PhraseText'].count('/') < 2:
                            numericList[phrasePos].append(phrase['PhraseText'].replace('.', '').replace(' ', '').strip())
                            print('added numeric position 7a')

                # Or Decimals (or intensities!)
                if '.' in phrase['PhraseText'] or 'average intensity' in phrase['PhraseText']:
                    splitPhrase = phrase['PhraseText'].split()
                    for word in splitPhrase:
                        if word.replace('.', '').isnumeric():
                            num = word
                            if num.endswith('.'):
                                num = num[:-1]
                            if num not in numericList[phrasePos] and not 'probe sets' in utterance['UttText'] and not 'chromosome ' + num in utterance['UttText']:
                                if len(numericList[phrasePos]) > 0:
                                    if num not in numericList[phrasePos][0]:
                                        numericList[phrasePos].append(num)
                                        print('added numeric position 22a')
                                else:
                                    numericList[phrasePos].append(num)
                                    print('added numeric position 22b')

                # This is for extra copies
                if 'extra copies' in phrase['PhraseText'].lower():
                    if 'extra copies' not in qualifierList[phrasePos]:
                        qualifierList[phrasePos].append('extra copies')
                        if debug:
                            print('added qualifier position 76')

                # This is to pull out stuff like '2+'
                if '+' in phrase['PhraseText']:
                    for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                        if len(phrase['SyntaxUnits']) - 1 > syntaxUnit:
                            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and '+' in phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch']:
                                # we want "5+", not "5 + 3"
                                addMe = False
                                if len(phrase['SyntaxUnits']) <= syntaxUnit + 2:
                                    addMe = True
                                elif len(phrase['SyntaxUnits']) > syntaxUnit + 2:
                                    if phrase['SyntaxUnits'][syntaxUnit + 2]['SyntaxType'] != 'shapes':
                                        addMe = True
                                if addMe:
                                    num = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'] + phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch']
                                    if num not in numericList[phrasePos]:
                                        numericList[phrasePos].append(num)
                                        print('added numeric position 8')

                # Here we're pulling out ranges like 2-3
                if '-' in phrase['PhraseText']:
                    phr = phrase['PhraseText']
                    if phr.replace('(', '').replace('/', '').replace('-', '').replace('+', '').isnumeric():
                        # 28-8 is a PD-L1 clone
                        if phr.replace('(', '') not in numericList[phrasePos] and phr.replace('(', '') not in ['28-8']:
                            numericList[phrasePos].append(phr.replace('(', ''))
                            print('added numeric position 24')
                        # If our range was like 2-3 and '3' was already in this range, I'm ASSUMING we don't want it. FIX IF FALSE!
                        for num in numericList[phrasePos]:
                            if num == phr.replace('(', '').split('-')[1]:
                                numericList[phrasePos].remove(num)

                # This is to pull out (0). Also note that I've found '2f' to mean 2 fusion signals
                if '(' in phrase['PhraseText']:
                    if phrase['PhraseText'].replace('(', '').replace('.', '').replace('f', '').isnumeric():
                        if len(utterance['Phrases']) - 1 == phrasePos:
                            num = phrase['PhraseText'].replace('(', '')
                            if num not in numericList[phrasePos]:
                                numericList[phrasePos].append(num)
                                print('added numeric position 21b')
                        elif utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('.', '').startswith(')'):
                            num = phrase['PhraseText'].replace('(', '')
                            if num not in numericList[phrasePos] and 'del' not in utterance['Phrases'][phrasePos - 1]['PhraseText']:
                                numericList[phrasePos].append(num)
                                print('added numeric position 21')

                # We're also not great with decimals: Do we ALWAYS want to add a decimal? INVESTIGATE DONE BETTER BY POSITION 22
                # if '.' in phrase['PhraseText'][:-1]:
                #    potentialDecimal = phrase['PhraseText'][:-1]
                #    if potentialDecimal.replace('.', '').isnumeric():
                #        if potentialDecimal not in numericList[phrasePos]:
                #            numericList[phrasePos].append(potentialDecimal)
                #            print('added numeric position 20')

                # MetaMap is relatively poor at realizing what's going on with percentages. This section is designed to
                # correct that. There are two kinds of percentages we want to pull out. "% of nuclei" or whatever, and
                # [number] %.
                if '%' in phrase['PhraseText']:
                    numPercent = ''
                    placePercent = ''
                    percentUnit = 0
                    percentage = ''
                    # For some incomprehensible reason, sometimes they say (%) 50
                    if '(%' in phrase['PhraseText']:
                        if utterance['Phrases'][phrasePos + 1]['PhraseText'] == ')':
                            if len(utterance['Phrases']) > phrasePos + 2:
                                num = utterance['Phrases'][phrasePos + 2]['PhraseText'].split()[0]
                                numPercent = num + '%'
                                if numPercent not in numericList[phrasePos]:
                                    numericList[phrasePos].append(numPercent)
                                    print('added numeric position 9')

                    # for percentages we don't get elsewhere
                    if '%' in phrase['PhraseText']:
                        for word in phrase['PhraseText'].split():
                            if '%' in word:
                                if word.replace('(', '').replace('<', '').replace('>', '').replace(',', '').replace('.', '').replace('%', '').isnumeric():
                                    if word.replace('(', '').replace(',', '') not in numericList[phrasePos]:
                                        numericList[phrasePos].append(word.replace('(', '').replace(',', ''))
                                        if debug:
                                            print('added numeric position 29')

                    # This is for percentages
                    for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                        if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and '%' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                            numPercent = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].replace(' ', '')
                            if len(phrase['SyntaxUnits']) > syntaxUnit + 2:
                                print(phrase['PhraseText'])
                                # This is for '% of nuclei'
                                if 'LexCat' in phrase['SyntaxUnits'][syntaxUnit + 2].keys():
                                    if phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch'] == 'of':
                                        if phrase['SyntaxUnits'][syntaxUnit + 2]['LexCat'] == 'noun':
                                            placePercent = phrase['SyntaxUnits'][syntaxUnit + 2]['InputMatch']
                                # Sometimes 'these' is in there
                                if len(phrase['SyntaxUnits']) > syntaxUnit + 3:
                                    if 'LexCat' in phrase['SyntaxUnits'][syntaxUnit + 3].keys():
                                        if phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch'] == 'of':
                                            if phrase['SyntaxUnits'][syntaxUnit + 2]['InputMatch'] in ['these', 'those']:
                                                if phrase['SyntaxUnits'][syntaxUnit + 3]['LexCat'] == 'noun':
                                                    placePercent = phrase['SyntaxUnits'][syntaxUnit + 3]['InputMatch']
                                            elif phrase['SyntaxUnits'][syntaxUnit + 3]['LexCat'] == 'adj' and 'LexCat' in phrase['SyntaxUnits'][syntaxUnit + 4].keys():
                                                if phrase['SyntaxUnits'][syntaxUnit + 4]['LexCat'] == 'noun':
                                                    placePercent = phrase['SyntaxUnits'][syntaxUnit + 4]['InputMatch']
                                if placePercent == 'interphase':
                                    placePercent = 'interphase cells'
                                # This is for 'tumor positive'
                                if phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch'] == 'tumor':
                                    if phrase['SyntaxUnits'][syntaxUnit + 2]['InputMatch'] == 'positive':
                                        placePercent = 'tumor positive'
                                if phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch'] == 'tumor':
                                    if phrase['SyntaxUnits'][syntaxUnit + 2]['InputMatch'] == 'cells':
                                        placePercent = 'tumor cells'
                                if numPercent and placePercent:
                                    percentage = numPercent + ' ' + placePercent
                                else:
                                    percentage = numPercent
                                # For ranges
                                if syntaxUnit > 1:
                                    if phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] in ['-']:
                                        if phrase['SyntaxUnits'][syntaxUnit - 2]['InputMatch'].isnumeric():
                                            percentage = phrase['SyntaxUnits'][syntaxUnit - 2]['InputMatch'] + phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] + percentage
                                # Here we're going to get the < or > that comes before the percentage.
                                if syntaxUnit > 0:
                                    if phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] in ['<', '>']:
                                        percentage = phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] + percentage
                                # Now finally let's append it
                                if percentage not in numericList[phrasePos]:
                                    # If we have <1% and <1% tumor positive, we'll want to remove the plain <1%
                                    for num in numericList[phrasePos]:
                                        if num in percentage:
                                            numericList[phrasePos].remove(num)
                                    numericList[phrasePos].append(percentage)
                                    print('added numeric position 10')

                                # Now here we have to check to see if there are any previous results. If there's a linking
                                # word, we'll go one further back and add it to the numeric column! If the previous phrase
                                # was a linking word, and the phrase before THAT has a % in it, add that in!
                                if phrasePos > 1:
                                    if linkingList[phrasePos - 1]:
                                        if '%' in utterance['Phrases'][phrasePos - 2]['PhraseText']:
                                            for phrasePart in utterance['Phrases'][phrasePos - 2]['PhraseText'].split():
                                                if '%' in phrasePart:
                                                    numericList[phrasePos].insert(0, phrasePart + ' ' + placePercent)
                            # This is if the % is at the end of the phrase!
                            elif syntaxUnit >= 2:
                                if phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] == '-':
                                    if phrase['SyntaxUnits'][syntaxUnit - 2]['InputMatch'].isnumeric():
                                        toAdd = phrase['SyntaxUnits'][syntaxUnit - 2]['InputMatch'] + phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] \
                                                + phrase['SyntaxUnits'][syntaxUnit]['InputMatch']
                                        # We don't want to get the TPS range - not useful (lab-specific)
                                        # RETRACTED ACTUALLY WE DO
                                        # if toAdd not in numericList[phrasePos] and 'tumor positive' not in ''.join(list(itertools.chain.from_iterable(numericList))):
                                        if toAdd.replace(' %', '%') not in numericList[phrasePos]:
                                            numericList[phrasePos].append(toAdd.replace(' %', '%'))
                                            print('added numeric position 11')

                                # We might just have a % at the end of a phrase!
                                # MAYBE CHANGE THIS but I'm gonna make it so we don't add a numeric unless we can match it with a biomarker
                                # OR if there's no other numbers.
                                else:
                                    if numPercent:
                                        if len(biomarkerList[phrasePos]) == len(numericList[phrasePos]) + 1:
                                            numericList[phrasePos].append(numPercent)
                                            print('added numeric position 12')

                                        else:
                                            isNum = False
                                            for numPlace in range(0, len(numericList)):
                                                if numericList[numPlace]:
                                                    isNum = True
                                            if not isNum:
                                                numericList[phrasePos].append(numPercent)
                                                print('added numeric position 13')

                            # This one is for phrases that are just the percentage
                            else:
                                if syntaxUnit > 0:
                                    if phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] in ['<', '>']:
                                        percentage = phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] + numPercent
                                    else:
                                        percentage = numPercent
                                if phrase['PhraseText'].replace('>', '').replace('<', '').replace('%', '').isnumeric() and ('>' in phrase['PhraseText'] or '<' in phrase['PhraseText']):
                                    percentage = phrase['PhraseText']
                                if not percentage:
                                    percentage = numPercent
                                # Sometimes the phrase '45% of nuclei' gets split up.
                                if len(utterance['Phrases']) > phrasePos + 1:
                                    if utterance['Phrases'][phrasePos + 1]['PhraseText'].startswith('of'):
                                        percentage = numPercent + ' ' + ' '.join(utterance['Phrases'][phrasePos + 1]['PhraseText'].split()[0:3])
                                # Now finally let's append it UNLESS it's ALSO in a previous phrase!
                                if percentage not in numericList[phrasePos]:
                                    if phrasePos > 0:
                                        numPos = phrasePos
                                        while numPos >= 0:
                                            if ' ' + percentage + ' ' in ' '.join(numericList[numPos]):
                                                percentage = ''
                                            numPos = numPos - 1
                                        # I'm getting a lot of cases where the TPS % is given right after the PD-L1 %
                                        # for num in range(0, len(numericList)):
                                        # if 'tumor positive' in ' '.join(numericList[num]):
                                        #    percentage = ''
                                        # if conceptList[phrasePos - 1] == 'tumor proportion score' and '%' in ' '.join(numericList[phrasePos - 1]):
                                        #    percentage = ''
                                    if percentage:
                                        numericList[phrasePos].append(percentage)
                                        print('added numeric position 14')

                # Not sure why, but sometimes '3 to 4' gets broken up in phrases like 3 | to 4
                if phrase['PhraseText'].isnumeric():
                    if len(utterance['Phrases']) > phrasePos + 1:
                        if utterance['Phrases'][phrasePos + 1]['PhraseText'].startswith('to'):
                            toAdd = phrase['PhraseText'] + ' ' + ' '.join(utterance['Phrases'][phrasePos + 1]['PhraseText'].split()[0:2])
                            if 'probe signals' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                                toAdd = toAdd + ' probe signals'
                            if 'copies' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                                toAdd = toAdd + ' copies'
                            if toAdd not in numericList[phrasePos]:
                                numericList[phrasePos].append(toAdd)
                                print('added numeric position 26')

                # This one pieces apart ranges (for copy number etc.) - I noticed lots of reports would
                # reference "3 to 10" copies of some number.
                numRange = ''
                for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                    if len(phrase['SyntaxUnits']) > syntaxUnit + 3:
                        if 'LexCat' in phrase['SyntaxUnits'][syntaxUnit + 3].keys():
                            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and \
                                    phrase['SyntaxUnits'][syntaxUnit + 1]['SyntaxType'] == 'prep' and \
                                    phrase['SyntaxUnits'][syntaxUnit + 2]['SyntaxType'] == 'shapes' and \
                                    phrase['SyntaxUnits'][syntaxUnit + 3]['LexCat'] == 'noun':
                                numRange = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'] + ' ' + \
                                           phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch'] + ' ' + \
                                           phrase['SyntaxUnits'][syntaxUnit + 2]['InputMatch'] + ' ' + \
                                           phrase['SyntaxUnits'][syntaxUnit + 3]['InputMatch']
                                if numRange not in numericList[phrasePos]:
                                    if numRange not in numericList[phrasePos]:
                                        firstOne = numRange.split()[0]
                                        secondOne = numRange.split()[2]
                                        if firstOne in numericList[phrasePos]:
                                            numericList[phrasePos].remove(firstOne)
                                        if secondOne in numericList[phrasePos]:
                                            numericList[phrasePos].remove(secondOne)
                                        numericList[phrasePos].append(numRange)
                                        print('added numeric position 15')
                            # This bit is tagged on to catch if they say "3 copies" without the range
                            elif phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and \
                                    'LexCat' in phrase['SyntaxUnits'][syntaxUnit + 1].keys():
                                if phrase['SyntaxUnits'][syntaxUnit + 1]['LexCat'] == 'noun' and \
                                        not numRange and phrase['SyntaxUnits'][syntaxUnit + 1]['Tokens'][0] in ['copies', 'copy'] and \
                                        phrase['SyntaxUnits'][syntaxUnit - 1]['InputMatch'] not in ['-', '/'] and 'hg' not in phrase['SyntaxUnits'][syntaxUnit + 1]['Tokens'][0]:
                                    numRange = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'] + ' ' + phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch']
                                    if numRange not in numericList[phrasePos]:
                                        numericList[phrasePos].append(numRange)
                                        print('added numeric position 16')
                                if phrase['SyntaxUnits'][syntaxUnit + 1]['LexCat'] == 'noun' and phrase['SyntaxUnits'][syntaxUnit + 1]['Tokens'][0] == 'centromere':
                                    numRange = phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch'] + ' ' + phrase['SyntaxUnits'][syntaxUnit]['InputMatch']
                                    if numRange.lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(numRange.lower())
                                        if debug:
                                            print("added biomarker position 51")
                # We're also on the lookout for linking words.
                for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                    if phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].lower() == 'but':
                        if 'but' not in linkingList[phrasePos]:
                            linkingList[phrasePos].append('but')
                    if phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].lower() == 'or':
                        if 'or' not in linkingList[phrasePos]:
                            linkingList[phrasePos].append('or')
                    if phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].lower() == 'and':
                        if 'and' not in linkingList[phrasePos]:
                            linkingList[phrasePos].append('and')
                    if phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].lower() == 'with':
                        if 'with' not in linkingList[phrasePos]:
                            linkingList[phrasePos].append('with')
                    if phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].lower() == 'respectively':
                        if 'respectively' not in qualifierList[phrasePos]:
                            qualifierList[phrasePos].append('respectively')
                            if debug:
                                print("added qualifier position 29")

                # Sometimes they say one (%) or both (%) chromosome long arms
                phraseText = utterance['Phrases'][phrasePos]['PhraseText']
                if len(utterance['Phrases']) - 1 > phrasePos:
                    if (phraseText == '1' or phraseText == 'both') and utterance['Phrases'][phrasePos + 1]['PhraseText'].startswith('('):
                        percent = utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('(', '')
                        arms = phraseText
                        if percent not in numericList[phrasePos]:
                            numericList[phrasePos].append(percent)
                            print('added numeric position 17')
                        if arms not in qualifierList[phrasePos]:
                            qualifierList[phrasePos].append(arms)
                            if debug:
                                print("added qualifier position 30")

                # My expectation is, at this point we've gotten all the numeric and linking words mapped out.
                # At this point, it's time to add the concepts, qualifiers, and biomarkers.

                # Scratch that. It looks like we'll have to go through all mappings to try to get what we want. It's because
                # of the negations, more than anything!
                for mapPos in range(0, len(phrase['Mappings'])):
                    mapping = phrase['Mappings'][mapPos]
                    for mcPos in range(0, len(mapping['MappingCandidates'])):
                        mapCan = mapping['MappingCandidates'][mcPos]
                        mapText = mapCan['CandidateMatched']

                        # Get some variants this way.
                        if len(mapText.split()) == 2:
                            if mapText.split()[1].startswith('p.'):
                                if mapText.split()[0].lower() not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append(mapText.split()[0].lower())
                                    if debug:
                                        print("added biomarker position 52")
                                if mapText.split()[1].lower() not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append(mapText.split()[1].lower())
                                    if debug:
                                        print("added biomarker position 53")
                        for semPos in range(0, len(mapCan['SemTypes'])):
                            semType = mapCan['SemTypes'][semPos]
                            # Concepts/quals being the easiest part (I say, famous last words) - let's start there!

                            # This is for 'diagnostic procedures'
                            if semType in ['diap']:
                                if mapText.lower() in ['immunohistochemistry', 'ihc']:
                                    if mapText.lower() not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(mapText.lower())
                                        print('added concept position 49')
                                # Or TMB
                                elif mapCan['CandidatePreferred'].lower() in ['tumor burden']:
                                    if mapCan['CandidatePreferred'].lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(mapCan['CandidatePreferred'].lower())
                                        print('added biomarker position 130')

                            # Expression in 'subsets' of cells are interesting, and the like
                            if semType in ['clas']:
                                if mapText.lower() in ['subset']:
                                    if mapText.lower() not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append(mapText.lower())
                                        print('added qualifier position 73')

                            # This is for MSI
                            if semType in ['patf']:
                                if mapCan['CandidatePreferred'].lower() in ['microsatellite instability']:
                                    if mapCan['CandidatePreferred'].lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(mapCan['CandidatePreferred'].lower())
                                        print('added biomarker position 129')
                                    if 'ngs' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('ngs')
                                        print('added concept position 57')

                            # This is for genetic alteration concepts
                            if semType in ['genf', 'comd', 'ftcn'] and any(ss in mapText.lower()
                                                                           for ss in ['rearrangement', 'amplification', 'deletion', 'fusion', 'endoreduplication', 'deleted', 'hyperdiploid',
                                                                                      'mutation', 'substitution', 'duplication', 'gain', 'loss', 'partial deletion', 'absence']):
                                # These seem to be for rearrangements
                                if len(mapText.split()) == 2 and mapText.split()[0].lower() == 'gene':
                                    mapText = mapText.split()[1]
                                if len(mapText.split()) == 2 and mapText.split()[1].lower() in ['mutation', 'amplification']:
                                    toAdd = mapText.split()[0].lower()
                                    if mapText.split()[0].lower() in ['missense', 'deleterious']:
                                        toAdd = mapText.lower()
                                        if toAdd not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append(toAdd)
                                            print('added concept position 52a')
                                    else:
                                        if toAdd not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(toAdd)
                                            print('added biomarker position 125')
                                        toAdd = mapText.split()[1].lower()
                                        if toAdd not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append(toAdd)
                                            print('added concept position 52')

                                if len(mapText.split()) == 3 and mapText.split()[1].lower() == 'gene':
                                    if mapText.split()[0].lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(mapText.split()[0].lower())
                                        if debug:
                                            print("added biomarker position 54")
                                        # Sometimes it's [gene]-[gene] rearrangement
                                        if (mapText.split()[0].lower() + '-') in utterance['Phrases'][phrasePos]['PhraseText'].lower():
                                            if utterance['Phrases'][phrasePos]['PhraseText'].split('-')[1].split()[0].lower() not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append(utterance['Phrases'][phrasePos]['PhraseText'].split('-')[1].split()[0].lower())
                                                if debug:
                                                    print("added biomarker position 55")
                                    mapText = mapText.split()[2]

                                # Here's for [x] of chromosome #
                                if len(mapText.split()) == 4 and mapText.split()[0].lower() in ['duplication', 'gain', 'loss']:
                                    phrtxt = utterance['Phrases'][phrasePos]['PhraseText'].lower().replace('gains', 'gain').split()
                                    dupindex = ''
                                    try:
                                        dupindex = phrtxt.index(mapText.split()[0].lower())
                                    except:
                                        dupindex = ''
                                    if dupindex:
                                        if phrtxt[dupindex] not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append(phrtxt[dupindex])
                                            if debug:
                                                print("added concept position 4")

                                # This is for deletions and rearrangements
                                if len(mapText.split()) == 2 and mapText.split()[1].lower() in ['deletion', 'rearrangement']:
                                    if mapText.split()[0] in ['Partial', 'partial']:
                                        if mapText.split()[0] not in qualifierList[phrasePos]:
                                            mapText = mapText.lower()
                                    elif mapText.split()[0].lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(mapText.split()[0].lower())
                                        if debug:
                                            print("added biomarker position 56")
                                        mapText = mapText.split()[1]
                                if len(mapText.split()) == 2 and mapText.split()[0].lower() in ['deletion', 'rearrangement']:
                                    if mapText.split()[1].lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(mapText.split()[1].lower())
                                        if debug:
                                            print("added biomarker position 57")
                                        # Might be a parentheses after it!
                                        if len(utterance['Phrases']) > phrasePos + 2:
                                            if utterance['Phrases'][phrasePos + 1]['PhraseText'].startswith('('):
                                                toAdd = utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('(', '')
                                                if ')' in utterance['Phrases'][phrasePos + 1]['PhraseText']:
                                                    toAdd = toAdd.replace(')', '')
                                                else:
                                                    place = phrasePos + 2
                                                    while ')' not in utterance['Phrases'][place]['PhraseText']:
                                                        toAdd = toAdd + utterance['Phrases'][place]['PhraseText']
                                                        place = place + 1
                                                if toAdd.lower() not in biomarkerList[phrasePos]:
                                                    biomarkerList[phrasePos].append(toAdd.lower())
                                                    if debug:
                                                        print("added biomarker position 58")
                                mapTextO = mapText
                                mapText = mapText.split()[0]
                                mapText = mapText.replace('loidy', 'loid')
                                mapText = mapText.lower()

                                # It might be 'fusion signal'
                                if mapText in ['fusion']:
                                    if 'fusion signal' in utterance['Phrases'][phrasePos]['PhraseText'].lower():
                                        mapText = 'fusion signal'
                                    if mapText[-1] == 's':
                                        mapText = mapText[0:-1]

                                mapText = mapTextO
                                if mapText.lower() not in ' '.join(conceptList[phrasePos]) and mapText.split()[0].lower() not in conceptList[phrasePos]:
                                    if len(mapText.split()) == 1:
                                        conceptList[phrasePos].append(mapText.lower())
                                        if debug:
                                            print("added concept position 5")
                                    elif len(mapText.split()) == 2 and 'partial' in mapText.split():
                                        conceptList[phrasePos].append(mapText)
                                        if debug:
                                            print("added concept position 6")

                                # This is for ones like 'exon 14 skipping mutation'
                                ms = mapText.lower().split()
                                if len(ms) > 2 and ms[-1] in ['mutation']:
                                    if ms[0] not in biomarkerList[phrasePos]:
                                        toAdd = ms[0]
                                        if ms[1].replace('v', '').replace('e', '').isnumeric():
                                            toAdd = toAdd + ' ' + ms[1]
                                        biomarkerList[phrasePos].append(toAdd)
                                        if debug:
                                            print("added biomarker position 59")
                                    if ms[-1] not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(ms[-1])
                                        if debug:
                                            print("added concept position 7")

                            # Let's get some gene rearrangements this way!
                            if semType in ['lbtr'] and 'rearrangement' in mapText.lower():
                                if len(mapCan['CandidateMatched'].lower().split()) >= 3:
                                    if mapCan['CandidateMatched'].lower().split()[0].lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(mapCan['CandidateMatched'].lower().split()[0].lower())
                                        if debug:
                                            print("added biomarker position 60")
                                if 'rearrangement' not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append('rearrangement')
                                    if debug:
                                        print("added concept position 8")
                                if 'negative' in mapCan['CandidateMatched'].lower():
                                    if 'negative' not in qualifierList[phrasePos] and 'normal results' not in biomarkerList[phrasePos]:
                                        qualifierList[phrasePos].append('negative')
                                        if debug:
                                            print("added qualifier position 31")
                            # Let's get some gene rearrangements this way!
                            if semType in ['lbpr', 'lbtr'] and 'mutation' in mapText.lower():
                                if len(mapCan['CandidateMatched'].lower().split()) >= 3:
                                    if mapCan['CandidateMatched'].lower().split()[0].lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(mapCan['CandidateMatched'].lower().split()[0].lower())
                                        if debug:
                                            print("added biomarker position 61")
                                if 'mutation' not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append('mutation')
                                    if debug:
                                        print("added concept position 9")
                                if 'negative' in mapCan['CandidateMatched'].lower():
                                    if 'negative' not in qualifierList[phrasePos] and 'normal results' not in biomarkerList[phrasePos]:
                                        qualifierList[phrasePos].append('negative')
                                        if debug:
                                            print("added qualifier position 32")

                            if semType in ['lbpr'] and mapText.lower() == 'preserved':
                                if 'preserved' not in qualifierList[phrasePos]:
                                    qualifierList[phrasePos].append('preserved')
                                    print('added qualifier position 66')

                            # I'm finding some tests marked 'lbpr' (laboratory procedure)
                            if semType in ['lbpr', 'aapp', 'neop']:
                                phraseText = utterance['Phrases'][phrasePos]['PhraseText']
                                lastPhrase = ''
                                if len(utterance['Phrases']) - 1 > phrasePos:
                                    lastPhrase = utterance['Phrases'][phrasePos - 1]['PhraseText']
                                if 'estrogen' in mapCan['CandidateMatched'].lower() or 'estrogen' in lastPhrase:
                                    if 'immunocytochemical' in phraseText.lower() or 'immunohistochemical' in phraseText.lower():
                                        if 'erica' not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append('erica')
                                            if debug:
                                                print("added concept position 10")
                                        if 'er' not in biomarkerList[phrasePos] and 'estrogen receptor' not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append('estrogen receptor')
                                            if debug:
                                                print("added biomarker position 62")
                                if 'progesterone' in mapCan['CandidateMatched'].lower() or 'progesterone' in lastPhrase:
                                    if 'immunocytochemical' in phraseText.lower() or 'immunohistochemical' in phraseText.lower():
                                        if 'prica' not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append('prica')
                                            if debug:
                                                print("added concept position 11")
                                        if 'pr' not in biomarkerList[phrasePos] and 'progesterone receptor' not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append('progesterone receptor')
                                            if debug:
                                                print("added biomarker position 63")
                                if 'proliferation index' in phraseText.lower():
                                    if 'proliferation index' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('proliferation index')
                                        if debug:
                                            print("added concept position 12")
                                if 'stain' in phraseText.lower():
                                    if 'stain' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('stain')
                                        if debug:
                                            print('added concept position 12-b')
                                # This gets some measurements (ki-67 among others)
                                if 'measurement' in mapCan['CandidatePreferred'].lower() and ' '.join(mapCan['CandidatePreferred'].lower().split()[:-1]) not in biomarkerList[phrasePos] and \
                                        mapCan['CandidateMatched'].lower() not in biomarkerList[phrasePos]:
                                    # We dont' want big long phrases I THINK
                                    if len(mapCan['CandidatePreferred'].lower().split()[:-1]) < 3 and 'Methionine' not in mapCan['CandidatePreferred']:
                                        biomarkerList[phrasePos].append(' '.join(mapCan['CandidatePreferred'].lower().split()[:-1]))
                                        print('added biomarker position 121')

                            # And some expressions! In fact, let's just try to pull NEGATIVE expresion.
                            elif semType in ['lbtr'] and 'negative' in mapText.lower():
                                if mapText.lower().split()[0] in ['negative', 'positive']:
                                    if ' '.join(mapText.lower().split()[1:]) not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(' '.join(mapText.lower().split()[1:]))
                                        print('added biomarker position 122')
                                elif mapText.lower().split()[0] not in biomarkerList[phrasePos] and mapText.lower().split()[0] == mapCan['MatchedWords'][0].lower():
                                    toAdd = mapText.lower().split()[0]
                                    if len(mapText.lower().split()) > 1:
                                        if mapText.lower().split()[1] in ['receptor', 'receptors']:
                                            toAdd = toAdd + " " + mapText.lower().split()[1]
                                    biomarkerList[phrasePos].append(toAdd)
                                    if debug:
                                        print("added biomarker position 64")
                                elif mapText.lower().split()[0] == mapCan['MatchedWords'][0].lower() + '-' + mapCan['MatchedWords'][1].lower() and mapText.lower().split()[0] not in biomarkerList[
                                    phrasePos]:
                                    biomarkerList[phrasePos].append(mapText.lower().split()[0])
                                    if debug:
                                        print("added biomarker position 65")
                                elif mapCan['CandidatePreferred'].lower().split()[0] not in biomarkerList[phrasePos] and \
                                        mapCan['CandidatePreferred'].lower().split()[0] == mapCan['MatchedWords'][0]:
                                    biomarkerList[phrasePos].append(mapCan['CandidatePreferred'].lower().split()[0])
                                    if debug:
                                        print("added biomarker position 66")
                                if mapText.lower().split()[1] not in qualifierList[phrasePos] and mapText.lower().split()[1] not in ['gene', 'rearrangement', 'receptor', 'progesterone', 'estrogen']:
                                    qualifierList[phrasePos].append(mapText.lower().split()[1])
                                    if debug:
                                        print("added qualifier position 33")
                                if 'negative' not in qualifierList[phrasePos] and biomarkerList[phrasePos] and 'normal results' not in biomarkerList[phrasePos]:
                                    qualifierList[phrasePos].append('negative')
                                    if debug:
                                        print("added qualifier position 34")
                                else:
                                    gene = mapText.lower().split('negative')[0].strip()
                                    for mark in range(0, len(biomarkerList)):
                                        if gene in ' '.join(biomarkerList[mark]):
                                            if not qualifierList[mark]:
                                                qualifierList[mark].append('negative')
                                    for mark in range(0, len(finalBiomarkerResults)):
                                        if gene in ' '.join(finalBiomarkerResults[mark]):
                                            if not finalQualifierResults[mark]:
                                                finalQualifierResults[mark].append('negative')
                            # And some expressions! In fact, let's just try to pull POSITIVE expression.
                            elif semType in ['lbtr'] and 'positive' in mapText.lower():
                                if mapText.lower().split()[0] == 'positive':
                                    if 'positive' not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append('positive')
                                        print('qualifier added position 60')
                                    if ' '.join(mapText.lower().split()[1:]) not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(' '.join(mapText.lower().split()[1:]))
                                        print('biomarker added position 124')
                                elif mapText.lower().split()[0] not in biomarkerList[phrasePos] and mapText.lower().split()[0] == mapCan['MatchedWords'][0].lower():
                                    toAdd = mapText.lower().split()[0]
                                    if mapText.lower().split()[1] in ['receptor']:
                                        toAdd = toAdd + ' ' + mapText.lower().split()[1]
                                    if toAdd not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(toAdd)
                                        if debug:
                                            print("added biomarker position 67")
                                elif mapCan['CandidatePreferred'].lower().split()[0] not in biomarkerList[phrasePos] and \
                                        mapCan['CandidatePreferred'].lower().split()[0] == mapCan['MatchedWords'][0]:
                                    biomarkerList[phrasePos].append(mapCan['CandidatePreferred'].lower().split()[0])
                                    if debug:
                                        print("added biomarker position 68")
                                if mapText.lower().split()[1] not in qualifierList[phrasePos] and mapText.lower().split()[1] not in ['gene', 'rearrangement', 'receptor'] and \
                                        mapText.lower().split()[0] not in ['positive', 'negative']:
                                    qualifierList[phrasePos].append(mapText.lower().split()[1])
                                    print('qualifier added position 68b')
                                if 'positive' not in qualifierList[phrasePos] and biomarkerList[phrasePos]:
                                    qualifierList[phrasePos].append('positive')
                                    if debug:
                                        print("added qualifier position 35")
                            # lbtr also shows microsatellite status
                            if semType in ['lbtr'] and 'microsatellite' in mapText.lower():
                                if mapCan['CandidateMatched'].lower() not in qualifierList[phrasePos] and 'microsatellite stability' not in phrase['PhraseText']:
                                    qualifierList[phrasePos].append(mapCan['CandidateMatched'].lower())
                                    print('added qualifier position 35-b')
                                if 'microsatellite' not in ''.join(list(itertools.chain.from_iterable(biomarkerList))):
                                    biomarkerList[phrasePos].append('microsatellite instability')
                                    print('added biomarker with qualifier position 35-b')

                            # It can also be the second half of fusions
                            if semType in ['lbtr'] and 'fusion' in mapText.lower():
                                if mapText.lower().split()[0] not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append(mapText.lower().split()[0])
                                    print('added biomarker with qualifier position 35-c')
                                if 'fusion' not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append('fusion')
                                    print('added concept with qualifier position 35-c')

                            # Hey, sometimes loss shows up here!
                            if semType in ['lbtr'] and 'loss' in mapText.lower():
                                if len(mapText.lower().split()) == 2:
                                    if mapText.lower().split()[1] == 'loss':
                                        if 'loss' not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append('loss')
                                            if debug:
                                                print("added concept position 13")
                                        if mapText.lower().split()[0].lower() not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(mapText.lower().split()[0].lower())
                                            if debug:
                                                print("added biomarker position 69")
                            # This is HIGHLY EXPERIMENTAL - but maybe we can get 'indicated' from 'most consistent with'. Seems
                            # like common phrasing!
                            if semType in ['idcn'] and 'consistent' in mapText.lower():
                                if 'consistent with result' not in qualifierList[phrasePos]:
                                    qualifierList[phrasePos].append('consistent with result')
                                    if debug:
                                        print("added qualifier position 36")

                            if semType in ['mnob'] and 'copies' in phrase['PhraseText']:
                                phraseText = phrase['PhraseText'].replace('(', '')
                                if len(phraseText.split()) == 2 and phraseText.split()[0].replace('.', '').isnumeric():
                                    if phraseText not in numericList[phrasePos]:
                                        numericList[phrasePos].append(phraseText)
                                        if debug:
                                            print('added numeric position 28')

                            # Here we're looking for markers of where expression is.
                            if semType in ['spco'] and mapText.lower() in ['nuclear']:
                                if mapText.lower() not in qualifierList[phrasePos]:
                                    qualifierList[phrasePos].append(mapText.lower())
                                    if debug:
                                        print('added qualifier position 67')

                            # I've found few measures under 'clna' - 'clinical attribute'
                            if semType in ['clna']:
                                if mapCan['CandidatePreferred'].lower() == 'allred score':
                                    if 'allred score' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('allred score')
                                        if debug:
                                            print("added concept position 14")
                                if len(mapCan['CandidateMatched'].split()) == 2:
                                    if mapCan['CandidateMatched'].split()[1].lower() in ['positive', 'negative']:
                                        if mapCan['CandidateMatched'].split()[0].lower() not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(mapCan['CandidateMatched'].split()[0].lower())
                                            print('added biomarker position 120')
                                            if mapCan['CandidateMatched'].split()[1].lower() not in qualifierList[phrasePos]:
                                                qualifierList[phrasePos].append(mapCan['CandidateMatched'].split()[1].lower())
                                                print('added qualifier position 57')

                            # This is for 'retained nuclear expression of'
                            if semType in ['idcn'] and 'expression' in mapText.lower():
                                if isinstance(phraseText, list):
                                    phraseText = ' '.join(phraseText)
                                if 'expression' in mapText.lower() and 'retained' in phraseText.lower():
                                    if 'expression' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('expression')
                                        if debug:
                                            print("added concept position 15")
                                    if 'positive' not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append('positive')
                                        if debug:
                                            print("added qualifier position 37")

                            # Some concepts seem to be under 'cgab', like anomalies
                            if semType in ['cgab'] and 'anomaly' in mapText.lower():
                                # Just to standardize
                                mapText = mapText.replace('chromosomes', 'chromosome')
                                # I'm expecting it to read 'anomaly of chromosome'. Also we might need to pick up another
                                # chromosome!
                                if len(mapText.split()) == 3:
                                    if mapText.split()[2].lower() == 'chromosome':
                                        index = phrase['PhraseText'].replace('chromosomes', 'chromosome').split().index('chromosome')
                                        if phrase['PhraseText'].split()[index + 1].replace('.', '').replace(',', '').isnumeric():
                                            toAdd = 'chromosome ' + phrase['PhraseText'].split()[index + 1].replace('.', '').replace(',', '')
                                            if 'anomaly' not in conceptList[phrasePos] and toAdd not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append(toAdd)
                                                if debug:
                                                    print("added biomarker position 70")
                                                conceptList[phrasePos].append('anomaly')
                                                if debug:
                                                    print("added concept position 16")
                                                if len(utterance['Phrases']) - 1 > phrasePos:
                                                    if utterance['Phrases'][phrasePos + 1]['PhraseText'].lower() == 'or':
                                                        if utterance['Phrases'][phrasePos + 2]['PhraseText'].replace('.', '').replace(',', '').isnumeric():
                                                            newAdd = 'chromosome ' + utterance['Phrases'][phrasePos + 2]['PhraseText'].replace('.', '').replace(',', '')
                                                            if newAdd not in biomarkerList[phrasePos + 2]:
                                                                biomarkerList[phrasePos + 2].append(newAdd)
                                            elif 'anomaly' not in conceptList[phrasePos] and toAdd in biomarkerList[phrasePos]:
                                                ph = phrase['PhraseText'].replace('chromosomes', 'chromosome').replace('anomalies', 'anomaly')
                                                conceptList[phrasePos].append('anomaly')
                                                if debug:
                                                    print("added concept position 17")
                                                if 'no anomaly' in ph:
                                                    qualifierList[phrasePos].append('negative')
                                                    if debug:
                                                        print("added qualifier position 38")

                            # For 'alteration' or 'expression's
                            if semType == 'idcn' and mapText.lower().replace('.', '').replace(',', '') in ['alteration', 'expression']:
                                toAdd = mapText.lower().replace('.', '').replace(',', '')
                                if 'over-expression' in ' '.join(phraseText).lower():
                                    toAdd = 'over-expression'
                                if toAdd not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append(toAdd)
                                    if debug:
                                        print("added concept position 18")
                                if 'normal ' + mapText.lower().replace('.', '').replace(',', '') in utterance['Phrases'][phrasePos]['PhraseText'].lower():
                                    if 'normal' not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append('normal')
                                        if debug:
                                            print("added qualifier position 39")

                            # This is real dumb, but this is how we get a fish assay
                            if semType == 'fish':
                                if mapText.lower() == 'fish':
                                    if 'fish' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('fish')
                                        print('added concept position 50')

                            # Let's pull out the allelic frequency
                            if semType == 'qnco' and 'allelic frequency' in mapText.lower():
                                toAdd = ''
                                pos = phrasePos
                                while pos < len(utterance['Phrases']) - 1 and '%' not in utterance['Phrases'][pos]['PhraseText']:
                                    if utterance['Phrases'][pos]['PhraseText'].replace('.', '').replace('(', '').isnumeric():
                                        toAdd = toAdd + utterance['Phrases'][pos]['PhraseText'].replace('.', '').replace('(', '').isnumeric()
                                    pos = pos + 1
                                if '%' in utterance['Phrases'][pos]['PhraseText']:
                                    toAdd = toAdd + utterance['Phrases'][pos]['PhraseText'].replace('(', '').replace(')', '').replace(',', '')
                                    toAdd = 'allelic frequency: ' + toAdd
                                    if toAdd not in numericList[phrasePos]:
                                        numericList[phrasePos].append(toAdd)
                                        print('added numeric position 18')

                            if semType == 'qnco' and mapText.lower() in ['average', 'intermediate', 'increased']:
                                if mapText.lower() not in qualifierList[phrasePos]:
                                    qualifierList[phrasePos].append(mapText.lower())
                                    print('added qualifier position 56')

                            if semType == 'qnco' and mapText.lower() in ['gain', 'gains', 'loss']:
                                if mapText.lower() not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append(mapText.lower())
                                    print('added concept position 53')

                            # EXPERIMENTAL I think this will catch some percentages
                            if semType == 'qnco' and mapText.replace('%', '').lower().isnumeric() and '%' in phraseText:
                                if '%' not in mapText and mapText + '%' in phraseText:
                                    mapText = mapText + '%'
                                if '-' in ''.join(numericList[phrasePos]):
                                    for num in numericList[phrasePos]:
                                        if '-' in num:
                                            if mapText.replace('%', '') == num.split('-')[0].replace('%', '') or num.split('-')[1].replace('%', ''):
                                                mapText = ''
                                if mapText not in ' '.join(numericList[phrasePos]):
                                    numericList[phrasePos].append(mapText)
                                    print('added numeric position 23')

                            # This is a copy number signifier
                            if semType == 'mnob' and mapText.lower() in ['copies']:
                                if mapText.lower() in ['copies']:
                                    addMe = 'copy number'
                                if addMe not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append(addMe)
                                    print('added concept position 55')

                            # Now let's try to grab the harder-to-get gains/losses
                            if semType == 'qnco' and mapText.lower() in ['loss', 'gain', 'ratio']:
                                split = phrase['PhraseText'].split()
                                # We can sometimes get hidden '#p's here
                                for item in split:
                                    if item.replace('p', '').isnumeric():
                                        if item not in ' '.join(biomarkerList[phrasePos]):
                                            biomarkerList[phrasePos].append(item)
                                            if debug:
                                                print("added biomarker position 71")
                                    # or #qs
                                    elif item.replace('q', '').isnumeric():
                                        if item not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(item)
                                            if debug:
                                                print("added biomarker position 72")
                                if mapCan['CandidateMatched'].lower() in split:
                                    # This is for 'the loss', 'the ratio' - we'll want this in the next phrase
                                    if len(split) == 2 and split[0] in ['the'] and len(utterance['Phrases']) > phrasePos + 2:
                                        if mapCan['CandidateMatched'].lower() not in qualifierList[phrasePos + 2]:
                                            qualifierList[phrasePos + 2].append(mapCan['CandidateMatched'].lower())
                                            if debug:
                                                print("added qualifier position 75")

                                    startIndex = split.index(mapCan['CandidateMatched'].lower())
                                    if startIndex < len(split) - 1:
                                        if split[startIndex + 1] == 'of' and startIndex < len(split) - 3:
                                            if split[startIndex + 2].endswith('.'):
                                                split[startIndex + 2] = split[startIndex + 2][:-1]
                                            if split[startIndex + 2] not in biomarkerList[phrasePos] and split[startIndex + 2] not in ['the', 'a']:
                                                biomarkerList[phrasePos].append(split[startIndex + 2])
                                                if debug:
                                                    print("added biomarker position 73")
                                            if split[startIndex] not in conceptList[phrasePos]:
                                                toAdd = split[startIndex]
                                                if startIndex > 0:
                                                    if split[startIndex - 1] == 'relative':
                                                        toAdd = 'relative ' + toAdd
                                                if toAdd not in conceptList[phrasePos]:
                                                    conceptList[phrasePos].append(toAdd)
                                                    if debug:
                                                        print("added concept position 19")
                                        elif split[startIndex + 1] == 'of':
                                            if split[startIndex].lower() not in conceptList[phrasePos]:
                                                conceptList[phrasePos].append(split[startIndex].lower())
                                                print("added concept position 51")
                                    else:
                                        if split[startIndex].lower() not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append(split[startIndex].lower())
                                            print("added concept position 51-b")

                            # 'nnon' is for probes
                            if semType in ['nnon'] and 'centromere' in mapText.lower() or mapText.lower().startswith('cen'):
                                if mapText.lower() not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append(mapText.lower())
                                    if debug:
                                        print('added biomarker position 134')

                            # 'Orga' seems to be useful for fetal sex so far.
                            if semType == 'orga' and 'sex' in mapText.lower():
                                if utterance['Phrases'][phrasePos + 1]['PhraseText'].lower() == 'is':
                                    if 'genotype' in utterance['Phrases'][phrasePos + 2]['Mappings'][0]['MappingCandidates'][0]['CandidatePreferred'].lower():
                                        if mapText.lower() not in conceptList[phrasePos + 2]:
                                            conceptList[phrasePos + 2].append(mapText.lower())
                                        if utterance['Phrases'][phrasePos + 2]['Mappings'][0]['MappingCandidates'][0]['CandidateMatched'].lower() not in biomarkerList[phrasePos + 2]:
                                            biomarkerList[phrasePos + 2].append(utterance['Phrases'][phrasePos + 2]['Mappings'][0]['MappingCandidates'][0]['CandidateMatched'].lower())
                                    elif utterance['Phrases'][phrasePos + 2]['PhraseText'].replace('.', '').replace(',', '').lower().split()[0] == 'xx' or \
                                            utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('.', '').replace(',', '').lower().split()[0] == 'xy':
                                        if mapText.lower() not in conceptList[phrasePos + 2]:
                                            conceptList[phrasePos + 2].append(mapText.lower())
                                        if utterance['Phrases'][phrasePos + 2]['PhraseText'].replace('.', '').replace(',', '').lower().split()[0] not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos + 2].append(utterance['Phrases'][phrasePos + 2]['PhraseText'].replace('.', '').replace(',', '').lower().split()[0])

                            # A 'cell population' is a biomarker OR NOT PUT BACK IN LATER?
                            # if semType == 'cell' and mapCan['CandidateMatched'].lower() == 'cell':
                            #    if 'population' in utterance['Phrases'][phrasePos]['PhraseText'].lower().replace('.' , '').replace(',', ''):
                            #        if 'cell population' not in biomarkerList[phrasePos]:
                            #            biomarkerList[phrasePos].append('cell population')

                            # Here's a place for getting some procedures
                            if semType in ['mbrt']:
                                if mapCan['CandidateMatched'].lower() in ['in situ hybridization']:
                                    if mapCan['CandidateMatched'].lower() not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(mapCan['CandidateMatched'].lower())
                                        print('Added concept position 58')

                            # Let's try to more carefully get subsets of cells
                            if semType in ['cell']:
                                if mapCan['CandidateMatched'].lower() in ['b cells']:
                                    if mapCan['CandidateMatched'].lower() not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append(mapCan['CandidateMatched'].lower())
                                        print('Added qualifier position 74')

                            if semType == 'cell' and mapCan['CandidateMatched'].lower() == 'clone':
                                if 'abnormal' in utterance['Phrases'][phrasePos]['PhraseText'].lower().replace('.', '').replace(',', ''):
                                    if 'abnormal clone' not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append('abnormal clone')
                                        if debug:
                                            print("added biomarker position 74")
                            if semType == 'genf' and 'rearrangement' in mapCan['CandidateMatched'].lower() or 'overexpression' in mapCan['CandidateMatched'].lower() or 'overexpress' in mapCan[
                                'CandidateMatched']:
                                if mapCan['CandidateMatched'] == 'overexpress':
                                    toAdd = 'overexpression'
                                else:
                                    toAdd = mapCan['CandidateMatched']
                                if toAdd.lower() not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append(toAdd.lower())
                                    if debug:
                                        print("added concept position 20")

                            # This is for concepts like 'monosomy', 'aneuploidy', etc.
                            if semType in ['dsyn', 'comd', 'cgab'] and any(x in mapText.lower() for x in ['somy', 'ploidy']):
                                index = 999
                                term = ''
                                location = ''
                                # They're normally one word in length.
                                if len(mapText.split()) == 1:
                                    # The only thing we need to check for, is if they're followed by a #
                                    term = mapText.lower()
                                    phraseText = [x.lower() for x in phrase['PhraseText'].split()]
                                    index = 999
                                    for x in range(0, len(phraseText)):
                                        if term in phraseText[x]:
                                            index = x
                                            break
                                    if index < len(phraseText) - 1:
                                        # Sometimes it'll be 'of chromosome' here.
                                        if phraseText[index + 1].replace('.', '').replace(',', '') == 'of':
                                            if phraseText[index + 2].replace('.', '').replace(',', '') in ['chromosome', 'chromosomes']:
                                                if phraseText[index + 3].replace('.', '').replace(',', '').isnumeric():
                                                    location = phraseText[index + 3].replace('.', '').replace(',', '')
                                        # Otherwise it might just be standard
                                        elif phraseText[index + 1].replace('.', '').replace(',', '').isnumeric():
                                            location = phraseText[index + 1].replace('.', '').replace(',', '')
                                    if mapText.lower() not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(mapText.lower())
                                        if debug:
                                            print("added concept position 21")
                                    if location and location.lower() and 'chromosome ' + location not in biomarkerList[phrasePos]:
                                        if 'chromosome' not in location:
                                            locorig = location
                                            location = 'chromosome ' + location
                                        biomarkerList[phrasePos].append(location.lower())
                                        if debug:
                                            print("added biomarker position 75")
                                        if locorig in numericList[phrasePos]:
                                            numericList[phrasePos].remove(locorig)
                                # "Monosomy X", Trisomy 11, the list goes on.
                                if len(mapText.split()) == 2:
                                    # First, we need to check that this is divided up correctly. For whatever reason, it's sometimes not.
                                    term = mapText.split()[0].lower()
                                    phraseText = [x.lower() for x in phrase['PhraseText'].split()]

                                    # May need to add more terms here! Some extra words creep in like 'of monosmoy x'.
                                    for phr in phraseText:
                                        if phr in ['of']:
                                            phraseText.remove(phr)

                                    if term in phraseText:
                                        index = phraseText.index(term)
                                        if phraseText[index + 1] != mapText.split()[1]:
                                            if phraseText[index + 1].lower() == 'chromosome':
                                                if phraseText[index + 2].replace('.', '').isnumeric():
                                                    location = phraseText[index + 1].lower() + ' ' + phraseText[index + 2].replace('.', '')
                                            else:
                                                location = phraseText[index + 1].replace('.', '')
                                        else:
                                            location = mapText.split()[1].replace('.', '')
                                    else:
                                        location = mapText.split()[1]
                                    # By this point, we should have gotten the correct location. Kind of a hassle.
                                    if term not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(term)
                                        if debug:
                                            print("added concept position 22")
                                    if len(location.split()) == 1:
                                        location = 'chromosome ' + location
                                    if location.replace(',', '').lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(location.replace(',', '').lower())
                                        if location.split()[1] in numericList[phrasePos]:
                                            numericList[phrasePos].remove(location.split()[1])
                                        if debug:
                                            print("added biomarker position 76")
                                # There can be yet a third type - 'chromosome 18 aneuploidy'
                                if len(mapText.split()) == 3:
                                    if mapText.split()[0].lower() == 'chromosome':
                                        if ' '.join(mapText.split()[0:2]).lower() not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(' '.join(mapText.split()[0:2]).lower())
                                            if debug:
                                                print("added biomarker position 77")
                                        if mapText.split()[2] not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append(mapText.split()[2])
                                            if debug:
                                                print("added concept position 23")

                            if semType in ['orch', 'phsu', 'topp']:
                                # This one catches a lot of things that aren't actually the gnees that we want - gene descriptive names. We'll cut them off here.
                                if mapText.lower() not in biomarkerList[phrasePos] and ', nos' not in mapText.lower() and mapText.lower().replace('-', '') not in biomarkerList[phrasePos] \
                                        and mapText.lower() not in ['expression', 'detected', 'fusions', 'fusion', 'presence', 'perform', 'favor',
                                                                    'complete excision'] and not mapText.lower().startswith(
                                    't-') and not mapText.lower().startswith('nm-') and not mapText.lower() in ' '.join(biomarkerList[phrasePos]):
                                    # No gene names if they're only part of nuc ish!
                                    if 'nuc ish' in utterance['UttText']:
                                        nucish = utterance['UttText'][utterance['UttText'].index('nuc ish'):]
                                        nucish = nucish[:nucish.index(']') + 1]
                                        if mapText.lower() not in utterance['UttText'].replace(nucish, '').replace('amplification', ''):
                                            continue
                                    biomarkerList[phrasePos].append(mapText.lower())
                                    print('added biomarker position 118')
                                    if 'refused' in utterance['UttText'] or 'refuse' in utterance['UttText'] or 'declined' in utterance['UttText'] or 'decline' in utterance[
                                        'UttText'] or 'not interested' in \
                                            utterance['UttText']:
                                        if 'refused' not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append('refused')
                                            print('added concept position 46')
                                    if 'no ' + mapText.lower() in utterance['Phrases'][phrasePos]['PhraseText']:
                                        if 'negative' not in qualifierList[phrasePos]:
                                            qualifierList[phrasePos].append('negative')

                            if mapText.lower() == '':
                                continue
                            if semType in ['fndg'] and mapText.lower() in ['contraindicated', 'strong positive', 'detected', 'likely pathogenic', 'unknown significance', 'low probability',
                                                                           'uncertain significance', 'pathogenic', 'positive', 'equivocal result', 'intact nuclear expression', 'unstable',
                                                                           'decreased'] or mapText.lower().split()[-1] in ['status']:
                                if mapText.lower() in ['strong positive']:
                                    mapText = 'strong'
                                # We want to capture negations here
                                if mapCan['Negated'] == '1':
                                    if 'negative' not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append('negative')
                                        print('added qualifier position 61')
                                # These first ones are statuses - like 'estrogen receptor status'. No, they don't get listed as independent gngms. Don't know why.
                                if mapText.lower().split()[-1] in ['status']:
                                    if ' '.join(mapText.lower().split()[:-1]) not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(' '.join(mapText.lower().split()[:-1]))
                                        print('added biomarker position 136')
                                elif mapText.lower() not in qualifierList[phrasePos] and not (mapText.lower() == 'positive' and any(x in phrase['PhraseText'].lower().replace('.', '').replace(',', '')
                                                                                                                                    for x in ['percent positive', 'tumor positive'])):

                                    qualifierList[phrasePos].append(mapText.lower())
                                    print('added qualifier position 58')

                            # This is for non-specific things that we might be interested in, like 'signal' strength
                            if semType in ['phpr']:
                                if mapText.lower() in ['signal']:
                                    if mapText.lower() not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(mapText.lower())
                                        print('added concept position 48')

                            # This is to get chromosomes and the like
                            if semType in ['celc'] and 'chromosome' in mapText.lower():
                                if mapText.lower() not in ' '.join(biomarkerList[phrasePos]).split() and mapText.lower() not in biomarkerList[phrasePos] and not hasSetsOrig:
                                    biomarkerList[phrasePos].append(mapText.lower())
                                    if debug:
                                        print("added biomarker position 78")
                                if 'chromosomes' in phrase['PhraseText']:
                                    if mapText.lower().replace('chromosome ', '').isnumeric() and not hasSetsOrig:
                                        if mapText.lower() not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(mapText.lower())
                                            if debug:
                                                print("added biomarker position 79")
                                    ps = phrasePos
                                    if len(utterance['Phrases']) > phrasePos + 1:
                                        ps = ps + 1
                                        while '(' in utterance['Phrases'][ps]['PhraseText'] or utterance['Phrases'][ps]['PhraseText'] in [',', ')'] or utterance['Phrases'][ps][
                                            'PhraseText'].replace(',', '').isnumeric() and ps < len(utterance['Phrases']):
                                            if utterance['Phrases'][ps]['PhraseText'].replace(',', '').isnumeric():
                                                num = 'chromosome ' + utterance['Phrases'][ps]['PhraseText'].replace(',', '')
                                                if 'chromosome ' + num not in biomarkerList[ps]:
                                                    biomarkerList[ps].append(num)

                                            ps = ps + 1
                            # This is to get centromeres and the like
                            if semType in ['celc'] and 'centromere' in mapText.lower():
                                phrasesp = utterance['Phrases'][phrasePos]['PhraseText'].replace('/', ' ').replace('centromere.', 'centromere').split()
                                centroPos = phrasesp.index('centromere')
                                if centroPos > 0 and len(phrasesp) - 1 > centroPos:
                                    if phrasesp[centroPos - 1].isnumeric() and not phrasesp[centroPos + 1].isnumeric():
                                        toAdd = phrasesp[centroPos] + ' ' + phrasesp[centroPos - 1]
                                        # Delete less specific tokens
                                        if 'centromere' in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].remove('centromere')
                                        if toAdd not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(toAdd)
                                            print('biomarker added position 119')

                            # Can also get vouses
                            if semType == 'nusq' and mapText.lower() in ['variant of uncertain significance', 'variant of unknown significance']:
                                if mapText.lower() not in qualifierList[phrasePos]:
                                    qualifierList[phrasePos].append(mapText.lower())
                                    print('added qualifier position 62')

                            # A chromosome can also be 'nusq', but let's only add if it really IS a chromosome.
                            if semType == 'nusq' and len(mapCan['CandidatePreferred'].split()) == 2:
                                if mapCan['CandidatePreferred'].split()[0].lower() == 'chromosome' and not hasSetsOrig:
                                    if mapCan['CandidatePreferred'].split()[1].lower() not in ''.join(biomarkerList[phrasePos]) and \
                                            mapCan['CandidatePreferred'].split()[1].lower() not in ''.join(biomarkerList[phrasePos - 1]):
                                        biomarkerList[phrasePos].append(mapCan['CandidatePreferred'].split()[1].lower())
                                        if debug:
                                            print("added biomarker position 80")
                            # It can also just be like '3q' off by itself - OR it can call itself 'chromosome # long arms'
                            if semType == 'nusq' and (mapText.replace('q', '').isnumeric() and 'q' in mapText or mapCan['CandidatePreferred'].replace('q', '').isnumeric()):
                                if mapText.lower() not in biomarkerList[phrasePos] and mapText.replace('q', '').isnumeric() and not hasSetsOrig:
                                    biomarkerList[phrasePos].append(mapText.lower())
                                    if debug:
                                        print("added biomarker position 81")
                                elif mapCan['CandidatePreferred'].lower() not in biomarkerList[phrasePos] and \
                                        mapCan['CandidatePreferred'].replace('q', '').isnumeric() and not hasSetsOrig:
                                    biomarkerList[phrasePos].append(mapCan['CandidatePreferred'].lower())
                                    if debug:
                                        print("added biomarker position 82")

                            # This is for probe regions that have 'probe' in the name.
                            if semType == 'celc' and 'probe' in phrase['PhraseText']:
                                if mapText.lower() in phrase['PhraseText'].lower():
                                    if mapText.replace(' ', '').lower() not in ' '.join(biomarkerList[phrasePos]) and mapText.replace(' ', '').lower() not in ['centromere']:
                                        biomarkerList[phrasePos].append(mapText.replace(' ', '').lower())
                                        if debug:
                                            print("added biomarker position 83")

                            # Some probe regions don't have 'probe' in the text. We'll see if they're right before
                            # a gene name here. Also note that for some reason, metamap doesn't always show the
                            # period, so we'll have to go looking.
                            elif semType == 'celc' and mapText.lower().replace('p', '').replace('x', '').replace('.', '').isnumeric() and 'nuc ish' not in phrase['PhraseText']:
                                if '.' not in mapText:
                                    if mapText in phrase['PhraseText']:
                                        for word in phrase['PhraseText'].split():
                                            if mapText in word:
                                                mapText = word.replace('(', '')
                                ppos = phrasePos
                                numText = ''
                                if len(utterance['Phrases']) > ppos + 1:
                                    if 'x' in utterance['Phrases'][ppos + 1]['PhraseText']:
                                        mapText = mapText + utterance['Phrases'][ppos + 1]['PhraseText']
                                        ppos = ppos + 1
                                if len(utterance['Phrases']) > ppos + 1:
                                    if '[' in utterance['Phrases'][ppos + 1]['PhraseText']:
                                        numText = utterance['Phrases'][ppos + 1]['PhraseText'] + ']'

                                # Don't THINK we'd ever want the end period being on "2p23." Remove this bit if that's wrong!
                                if mapText.lower().endswith('.') or mapText.lower().endswith(','):
                                    mapText = mapText[:-1]

                                if mapText.lower() not in biomarkerList[phrasePos]:
                                    dontadd = False
                                    # If this biomarker is part of a nuc ish, don't add it!
                                    allBio = ' '.join(list(itertools.chain.from_iterable(biomarkerList)))
                                    if 'nuc ish' in allBio:
                                        for bt in allBio.split(','):
                                            if 'nuc ish' in bt or ('[' in bt and ']' in bt) and mapText.lower() in bt:
                                                dontadd = True
                                    if not dontadd:
                                        biomarkerList[phrasePos].append(mapText.lower())
                                        if debug:
                                            print("added biomarker position 84")
                                if numText:
                                    if numText not in numericList[phrasePos]:
                                        numericList[phrasePos].append(numText)
                                        print('added numeric position 19')
                                # If we have [#] and it isn't [#/#], that's a sign we didn't see anything.
                                if numText and '/' not in numText:
                                    if 'negative' not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append('negative')
                                        if debug:
                                            print("added qualifier position 40")
                                        if hasIndicated:
                                            hasIndicated = False

                            # For procedures like karyotypes
                            if semType in ['mbrt'] and mapText.lower() in ['karyotype']:
                                if mapText.lower() not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append(mapText.lower())
                                    print('added concept position 60')

                            # CD138 and such
                            if semType in ['gngm'] and mapText.lower().startswith('cd'):
                                if mapText.lower() not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append(mapText.lower())
                                    print('added biomarker position 137')

                            # This is for genes - some have 'gene name' around them
                            if semType in ['gngm']:
                                phraseText = [x.lower() for x in phrase['PhraseText'].replace('.', '').replace(',', '').split()]
                                # Sometimes, the word 'locus' is right next to the gene
                                hasLocus = False
                                if len(mapping['MappingCandidates']) - 1 > mcPos:
                                    if mapping['MappingCandidates'][mcPos + 1]['CandidateMatched'].lower() == 'locus':
                                        hasLocus = True
                                toAdd = ''
                                if len(mapText.split()) > 1:
                                    if mapText.split()[1].lower() == 'gene':
                                        toAdd = mapText.split()[0]
                                        if hasLocus:
                                            toAdd = toAdd + ' locus'
                                # CHANGE THIS BACK IF WANTED - THIS TAKES OUT GENE-#
                                elif len(mapText.split('-')) > 1:
                                    # I'm going to put this in, to make sure that we don't put in a more specific gene
                                    # If we don't have that.
                                    # I'm also making sure we don't add something and pd-l1 expression
                                    phraseText = [x.lower() for x in phrase['PhraseText'].replace('.', '').replace(',', '').split()]
                                    # Just add it if we can
                                    if phraseText not in biomarkerList[phrasePos] and 'expression' not in phraseText:
                                        if hasLocus:
                                            toAdd = ' '.join(phraseText).replace('(', '')
                                        else:
                                            toAdd = ' '.join(phraseText)

                                    if '(' in toAdd:
                                        toAdd = toAdd.replace('(', '')

                                    # It's common here that we'll capture 'pd-l1 tumor proportion score'
                                    # We occasionally also get descriptions of the assay. If we know it's pd-l1, let's leave
                                    # that out!
                                    if 'pd' in phraseText and 'l1' in phraseText:
                                        pdstart = phraseText.index('pd')
                                        del phraseText[pdstart + 1]
                                        phraseText[pdstart] = 'pd-l1'
                                    if 'pd-l1' in phraseText:
                                        phraseText = phraseText[phraseText.index('pd-l1'):]
                                    if phraseText[0] == 'pd-l1':
                                        if len(phraseText) > 1:
                                            if phraseText[1] in ['tumor', 'ihc', 'clone']:
                                                toAdd = 'pd-l1'
                                            elif 'assay' in phraseText:
                                                for entry in biomarkerList:
                                                    if 'pd-l1' in entry:
                                                        toAdd = ''
                                            else:
                                                toAdd = 'pd-l1'
                                        else:
                                            toAdd = 'pd-l1'
                                    # And if not, we'll get something like 'no pd-l1 expression'
                                    elif len(phraseText) > 1:
                                        if phraseText[1] == 'pd-l1':
                                            if phraseText[0].replace('(', '') in ['high', 'no', 'low']:
                                                toAdd = 'pd-l1'
                                                for entry in biomarkerList:
                                                    if 'pd-l1' in entry:
                                                        toAdd = ''
                                                for entry in finalBiomarkerResults:
                                                    if 'pd-l1' in ' '.join(entry):
                                                        toAdd = ''
                                                if toAdd:
                                                    toAdd = 'pd-l1'
                                    for i, s in enumerate(phraseText):
                                        if mapText.split('-')[0] in s:
                                            if i not in biomarkerList[phrasePos]:
                                                if mapText.split('-')[1].isnumeric():
                                                    if mapText.replace('-', '').lower() not in biomarkerList[phrasePos]:
                                                        if hasLocus:
                                                            toAdd = mapText.replace('(', '')
                                                        # toAdd = mapText.split('-')[0]
                                                        else:
                                                            toAdd = mapText
                                if 'for the ' in toAdd:
                                    toAdd = toAdd.replace('for the ', '')
                                if toAdd and toAdd.lower() not in biomarkerList[phrasePos]:
                                    if '-' in toAdd and toAdd not in ['pd-l1', 'pd-1'] and 'her-2' not in toAdd and not toAdd.endswith('-'):
                                        if len(toAdd.split('-')[0].split()) == 1:
                                            firstAdd = toAdd.split('-')[0].split()[0]
                                            secondAdd = toAdd.split('-')[1].split()[0]
                                            if firstAdd not in ' '.join(biomarkerList[phrasePos]):
                                                biomarkerList[phrasePos].append(firstAdd)
                                                if debug:
                                                    print("added biomarker position 85")
                                            if secondAdd not in ' '.join(biomarkerList[phrasePos]):
                                                biomarkerList[phrasePos].append(secondAdd)
                                                if debug:
                                                    print("added biomarker position 86")
                                    elif 'probe' not in biomarkerList[phrasePos] and 'probe region' not in biomarkerList[phrasePos] and toAdd.lower() not in biomarkerList[phrasePos]:
                                        if 'of' in toAdd:
                                            if toAdd.split('of')[1] not in biomarkerList[phrasePos] and not toAdd.endswith('of'):
                                                # This is sometimes 'the 2p23 alk probe region'. And I already have 2p23 elsewhere.
                                                toAddHere = toAdd.split('of')[1].replace('the', '').strip()
                                                if len(toAddHere.split()) == 4:
                                                    if toAddHere.split()[2] == 'probe' and toAddHere.split()[3] == 'region':
                                                        if toAddHere.split()[0].lower() not in biomarkerList[phrasePos]:
                                                            biomarkerList[phrasePos].append(toAddHere.split()[0].lower())
                                                            if debug:
                                                                print("added biomarker position 87")
                                                        toAddHere = toAddHere.split()[1]
                                                if toAddHere not in biomarkerList[phrasePos] and toAddHere.split()[0] not in biomarkerList[phrasePos] and toAddHere not in ['<', '>']:
                                                    if len(toAddHere.split()) > 1:
                                                        if toAddHere.split()[1] not in ['present']:
                                                            biomarkerList[phrasePos].append(toAddHere)
                                                    else:
                                                        biomarkerList[phrasePos].append(toAddHere)
                                                    if debug:
                                                        print("added biomarker position 88")
                                            if toAdd.split('of')[0].strip() not in conceptList[phrasePos] and 'cop' not in toAdd.split('of')[0].strip() and 'ratio' \
                                                    not in toAdd.split('of')[0].strip() and toAdd.split('of')[0].strip() != '':
                                                conceptList[phrasePos].append(toAdd.split('of')[0].strip())
                                                if debug:
                                                    print("added concept position 24")

                                        else:
                                            # getting duplicates of pd-l1. Others? This keeps that from getting duplicated.
                                            if (toAdd not in ['pd-l1'] or toAdd not in itertools.chain.from_iterable(biomarkerList)) and 'her2' not in toAdd.lower().replace('-', '') and len(
                                                    toAdd.split()) < 3 and not any(
                                                x in ' '.join(list(itertools.chain.from_iterable(biomarkerList))) for x in [toAdd.lower() + '-', '-' + toAdd.lower()]) \
                                                    and 'rearrangements' not in toAdd:
                                                biomarkerList[phrasePos].append(toAdd.lower())
                                                if debug:
                                                    print("added biomarker position 89")

                                    # This is for [gene]/[gene] rearrangement
                                    if len(' '.join(phraseText).split('/')) > 1:
                                        gene1 = ' '.join(phraseText).split('/')[0].replace('her-2', 'her2')
                                        gene2 = ' '.join(phraseText).split('/')[1].split()[0]
                                        con = ' '.join(phraseText).split('/')[1].split()[-1]
                                        if gene1 not in ' '.join(biomarkerList[phrasePos]) and gene1 not in ['her-2', 'her2'] and 'staining' not in gene1 and 'her2' not in gene1:
                                            biomarkerList[phrasePos].append(gene1)
                                            if debug:
                                                print("added biomarker position 90")
                                        if gene2 not in ' '.join(biomarkerList[phrasePos]) and gene1 not in ['her-2', 'her2'] and not any(x in gene1 for x in ['fish', 'cish']):
                                            biomarkerList[phrasePos].append(gene2)
                                            if debug:
                                                print("added biomarker position 91")
                                        if con not in ' '.join(conceptList[phrasePos]) and con not in ['negative', 'neu', 'oncoprotein', 'of']:
                                            conceptList[phrasePos].append(con)
                                            if debug:
                                                print("added concept position 25")

                                # We might have a [gene] probe region in a longer string
                                elif 'probe region' in ' '.join(phraseText):
                                    probeStart = phraseText.index('probe')
                                    if probeStart > 0:
                                        probeStart = probeStart - 1
                                        if phraseText[probeStart] in biomarkerList[phrasePos]:
                                            if phraseText[probeStart] + ' probe region' not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].remove(phraseText[probeStart])
                                                biomarkerList[phrasePos].append(phraseText[probeStart] + ' probe region')
                                                if debug:
                                                    print("added biomarker position 92")

                                # We'll want 'probe' to go in with the other names surrounding the probe
                                elif mapText.lower() == 'probe' and len(biomarkerList[phrasePos]) > 1:
                                    toAdd = 'probe'
                                    if len(mapping['MappingCandidates']) > mcPos + 1:
                                        if mapping['MappingCandidates'][mcPos + 1]['CandidateMatched'].lower() == 'region':
                                            toAdd = toAdd + ' region'
                                    else:
                                        if 'probe region' in ' '.join(phraseText):
                                            toAdd = toAdd + ' region'
                                    if biomarkerList[phrasePos - 1] and not biomarkerList[phrasePos] and mapText not in biomarkerList[phrasePos - 1]:
                                        biomarkerList[phrasePos - 1].append(toAdd)
                                    elif toAdd not in ' '.join(biomarkerList[phrasePos]):
                                        if toAdd == 'probe region':
                                            biomarkerList[phrasePos].append(toAdd)
                                            if debug:
                                                print("added biomarker position 93")
                                        else:
                                            biomarkerList[phrasePos][len(biomarkerList[phrasePos]) - 1] = biomarkerList[phrasePos][len(biomarkerList[phrasePos]) - 1] + ' ' + toAdd

                                # Finally, this is just for genes just named the gene name
                                elif 'gene' in mapCan['CandidatePreferred'].lower() and not toAdd and mapCan['MatchedWords'][0] not in biomarkerList[phrasePos] \
                                        and 'expression' not in phraseText and 'assay' not in phraseText and 'nuc' not in phraseText and 'high' not in phraseText \
                                        and 'no' not in phraseText and 'low' not in phraseText:
                                    # No gene names if they're only part of nuc ish!
                                    if 'nuc ish' in utterance['UttText']:
                                        nucish = utterance['UttText'][utterance['UttText'].index('nuc ish'):]
                                        nucish = nucish[:nucish.index(']') + 1]
                                        if mapCan['MatchedWords'][0] not in utterance['UttText'].replace(nucish, ''):
                                            continue
                                    if hasLocus:
                                        mapText = mapText + ' locus'
                                    # sometimes when it's 'sep', that means it's part of a probe
                                    if mapCan['MatchedWords'][0] in ['sep', 'x3']:
                                        if '(' in ''.join(phraseText) or ''.join(phraseText).replace('x', '').replace('-', '').isnumeric():
                                            mapCan['MatchedWords'][0] = ''
                                    if mapCan['MatchedWords'][0] and not any(x in ' '.join(mapCan['MatchedWords']).lower() for x in ['locus', 'gene']):
                                        # This might seem like a rare condition, but sometimes it thinks something that's really a mutation
                                        # (like ggt>ggt) is a gene, since the phrases are 'ggt' , '>ggt'
                                        if len(utterance['Phrases']) - 1 > phrasePos:
                                            if not utterance['Phrases'][phrasePos + 1]['PhraseText'].startswith('>') or len(utterance['Phrases'][phrasePos]['PhraseText'].split()) > 1:
                                                if mapCan['MatchedWords'][0] not in biomarkerList[phrasePos]:
                                                    if not conceptList[phrasePos] and pocketConcept:
                                                        conceptList[phrasePos].append(pocketConcept)
                                                        if debug:
                                                            print("added concept position 26")

                                                        pocketConcept = ''
                                                    if mapCan['MatchedWords'][0].lower() not in biomarkerList[phrasePos]:
                                                        toAdd = mapCan['MatchedWords'][0].lower()
                                                        if len(mapCan['MatchedWords']) > 1:
                                                            if mapCan['MatchedWords'][1].lower() in ['receptor', 'receptors', 'clock']:
                                                                toAdd = toAdd + ' receptor'
                                                            # if it's 'her 2' change it to 'her2'
                                                            elif mapCan['MatchedWords'][1].lower().isnumeric():
                                                                toAdd = toAdd + mapCan['MatchedWords'][1].lower()
                                                        if toAdd not in ''.join(biomarkerList[phrasePos]) and \
                                                                not any(x in ' '.join(list(itertools.chain.from_iterable(biomarkerList))) for x in [toAdd + '-', '-' + toAdd]):
                                                            # No gene names if they're only part of nuc ish, OR just 'amplification'
                                                            if 'nuc ish' in utterance['UttText']:
                                                                nucish = utterance['UttText'][utterance['UttText'].index('nuc ish'):]
                                                                nucish = nucish[:nucish.index(']') + 1]
                                                                if toAdd not in utterance['UttText'].replace(nucish, '').replace('amplification', ''):
                                                                    continue
                                                            biomarkerList[phrasePos].append(toAdd)
                                                            if debug:
                                                                print("added biomarker position 94")
                                        else:
                                            if mapCan['MatchedWords'][0] not in biomarkerList[phrasePos]:
                                                toAdd = mapCan['MatchedWords'][0]
                                                if len(mapCan['MatchedWords']) > 1:
                                                    toAdd = toAdd + ' ' + mapCan['MatchedWords'][1]
                                                if toAdd not in biomarkerList[phrasePos]:
                                                    if not conceptList[phrasePos] and pocketConcept:
                                                        conceptList[phrasePos].append(pocketConcept)
                                                        if debug:
                                                            print("added concept position 27")
                                                        pocketConcept = ''
                                                    if toAdd.lower() not in biomarkerList[phrasePos]:
                                                        # This is to catch stuff like "her2/neu"
                                                        if len(mapCan['MatchedWords']) > 1:
                                                            if '-' in mapCan['CandidateMatched'] and mapCan['CandidateMatched'] not in biomarkerList[phrasePos]:
                                                                toAdd = mapCan['CandidateMatched']
                                                        if toAdd not in biomarkerList[phrasePos] and toAdd.replace(' ', '-') not in ' '.join(biomarkerList[phrasePos]) \
                                                                and toAdd.replace(' -', '').replace(' ', '').lower() not in biomarkerList[phrasePos]:
                                                            biomarkerList[phrasePos].append(toAdd)
                                                            if debug:
                                                                print("added biomarker position 95")
                                    elif mapCan['MatchedWords'][0] and 'locus' in ' '.join(mapCan['MatchedWords']):
                                        if ' '.join(mapCan['MatchedWords']).lower() not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(' '.join(mapCan['MatchedWords']))
                                            if debug:
                                                print("added biomarker position 96")
                                    elif 'gene' in mapCan['CandidatePreferred'] and len(mapCan['CandidatePreferred'].split()) > 1:
                                        if mapCan['CandidatePreferred'].split()[1] == 'gene':
                                            if mapCan['CandidatePreferred'].split()[0].lower() not in biomarkerList[phrasePos] and mapCan['CandidatePreferred'].split()[0].lower() not in ['clock']:
                                                biomarkerList[phrasePos].append(mapCan['CandidatePreferred'].split()[0].lower())
                                                if debug:
                                                    print('added biomarker position 133')

                            # Sometimes the signal ratio is thrown off and we get '/ [gene] signal ratio'
                            if ''.join(phraseText).startswith('/'):
                                if ' '.join(phraseText).split()[-1] in ['ratio']:
                                    if ' '.join(phraseText).split()[-1] not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(phraseText.split()[-1])
                                        print('added concept position 54')

                            # "imft", or immunologic factor, seems to show up! Sometimes 'd' is coded as 'd nos' though, and that's no good.
                            if semType == 'imft' and mapping['MappingCandidates'][mcPos]['MatchedWords'][0] not in ['d']:
                                add = mapText.lower()
                                if '-' in mapText.lower() and mapText.lower() not in ['pd-l1']:
                                    add = mapText.lower().replace('-', '')
                                if add not in ' '.join(biomarkerList[phrasePos]).replace('-', '') and add not in biomarkerList[phrasePos] and 'block ' + add not in utterance['UttText']:
                                    biomarkerList[phrasePos].append(add)
                                    if debug:
                                        print("added biomarker position 97")

                            # If nothing is wrong, sometimes the finding will be 'normal results'. The finding can also relate
                            # to a loss or gain - or, as it turns out, a 'structural abnormality
                            if semType == 'fndg':
                                wholeResults = np.nan
                                if 'normal' in mapText.lower() and 'abnormal' not in mapText.lower():
                                    wholeResults = ''
                                    for x in biomarkerList:
                                        wholeResults = wholeResults + ''.join(x)
                                    if not wholeResults:
                                        biomarkerList[phrasePos].append('normal results')
                                        if debug:
                                            print("added biomarker position 98")
                                        qualifierList[phrasePos].append('normal')
                                        if debug:
                                            print("added qualifier position 41")
                                        if hasIndicated:
                                            hasIndicated = False
                                        if conceptList[phrasePos] == ['coding variant']:
                                            conceptList[phrasePos] = []
                                            pocketConcept = 'coding variant'
                                if 'normal results' in mapText.lower() and wholeResults and 'abnormal' not in mapText.lower():
                                    if 'normal results' not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append('normal results')
                                        print('added qualifier position 42a')
                                if 'abnormal results' in mapText.lower():
                                    if 'abnormal results' not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append('abnormal results')
                                        print('added qualifier position 42c')
                                if 'normal limits' in mapText.lower() and 'abnormal' not in mapText.lower():
                                    if 'within normal limits' not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append('within normal limits')
                                        if debug:
                                            print("added qualifier position 42")

                                elif 'loss' in mapText.lower():
                                    if mapText not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(mapText)
                                        if debug:
                                            print("added concept position 28")
                                elif mapText.lower() in ['present', 'absent']:
                                    if mapText.lower() not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append(mapText.lower())
                                        print('qualifier added position 55')
                                # This is for '[gene] gene rearrangement's
                                if len(mapText.split()) == 3 and mapText.split()[2].lower() in ['deletion', 'rearrangement']:
                                    if mapText.split()[1].lower() == 'gene':
                                        if mapText.split()[0].lower() not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(mapText.split()[0].lower())
                                            if debug:
                                                print("added biomarker position 99")
                                        if mapText.split()[2].lower() not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append(mapText.split()[2].lower())
                                            if debug:
                                                print("added concept position 29")

                                elif 'structural abnormalit' in mapText.lower():
                                    if 'structural abnormality' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('structural abnormality')
                                        if debug:
                                            print("added concept position 30")


                                elif 'rearrangement' in mapText.lower():
                                    if 'rearrangement' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('rearrangement')
                                        if debug:
                                            print("added concept position 31")
                                    if len(mapText.lower().split()) == 2:
                                        if mapText.lower().split()[1] == 'rearrangement':
                                            if mapText.lower().split()[0] not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append(mapText.lower().split()[0])
                                                if debug:
                                                    print("added biomarker position 100")

                                elif 'separation' in mapText.lower():
                                    if 'separation' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('separation')
                                        if debug:
                                            print("added concept position 32")

                                elif 'expression' in mapText.lower():
                                    if 'low' in mapText.lower():
                                        if 'low expression' not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append('low expression')
                                            if debug:
                                                print("added concept position 33")
                                    elif 'high' in mapText.lower():
                                        if 'high expression' not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append('high expression')
                                            if debug:
                                                print("added concept position 33")
                                    else:
                                        if 'expression' not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append('expression')
                                            if debug:
                                                print("added concept position 34")

                            # This is for diagnoses
                            if semType == 'neop' and 'diagnosis' in conceptList[phrasePos]:
                                if mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append(mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower())
                                    if debug:
                                        print("added biomarker position 101")

                            # This is for 'tumor proportion score' and 'tumor positive'
                            if semType == 'fndg':
                                if 'tumor' in mapText.lower():
                                    if len(mapping['MappingCandidates']) > mcPos + 2:
                                        if mapping['MappingCandidates'][mcPos + 1]['MatchedWords'][0].lower() == 'proportion' and \
                                                mapping['MappingCandidates'][mcPos + 2]['MatchedWords'][0].replace(':', '').lower() == 'score':
                                            if 'tumor proportion score' not in conceptList[phrasePos]:
                                                conceptList[phrasePos].append('tumor proportion score')
                                                if debug:
                                                    print("added concept position 35")
                                            if phrasePos == 0 and not biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append('pd-l1')
                                                if debug:
                                                    print("added biomarker position 102")
                                if 'combine' in mapText.lower() or 'combined' in mapText.lower():
                                    if len(mapping['MappingCandidates']) > mcPos + 2:
                                        if mapping['MappingCandidates'][mcPos + 1]['MatchedWords'][0].lower() == 'positive' and \
                                                mapping['MappingCandidates'][mcPos + 2]['MatchedWords'][0].replace(':', '').lower() == 'score':
                                            if 'combined positive score' not in conceptList[phrasePos]:
                                                conceptList[phrasePos].append('combined positive score')
                                                if debug:
                                                    print("added concept position 36")
                                            if phrasePos == 0 and not biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append('pd-l1')
                                                if debug:
                                                    print("added biomarker position 103")
                                if 'her2' in mapText.lower():
                                    if mapping['MappingCandidates'][mcPos]['MatchedWords'][-1] in ['positive', 'negative']:
                                        if mapping['MappingCandidates'][mcPos]['MatchedWords'][0] not in biomarkerList[phrasePos]:
                                            biomarkerList[phrasePos].append(mapping['MappingCandidates'][mcPos]['MatchedWords'][0])
                                            print('added biomarker position 123')
                                            if mapping['MappingCandidates'][mcPos]['MatchedWords'][-1] not in qualifierList[phrasePos]:
                                                qualifierList[phrasePos].append(mapping['MappingCandidates'][mcPos]['MatchedWords'][-1])
                                                print('added qualifier position 59')


                                # If we've ever SEEN pd-l1 before, add it here. ADD ON LATER IF WE NEED MORE BIOMARKERS
                                elif 'tumor cells positive' in utterance['Phrases'][phrasePos]['PhraseText']:
                                    for marker in biomarkerList:
                                        if 'pd-l1' in marker:
                                            if 'pd-l1' not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append('pd-l1')
                                                if debug:
                                                    print("added biomarker position 104")
                                    for marker in finalBiomarkerResults:
                                        if 'pd-l1' in marker:
                                            if 'pd-l1' not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append('pd-l1')
                                                if debug:
                                                    print("added biomarker position 105")

                            # We might get syndromes and such here. Maybe we don't want? Maybe we do.
                            if semType == 'dsyn' and not any(x in mapText for x in ['somy', 'ploidy']):
                                if mapText not in biomarkerList[phrasePos]:
                                    # I'm too cautious to rule out macrophage activation syndrome forever, but I bet it's mostly 'mass'
                                    if 'macrophage' in utterance['UttText'] or 'mas' not in mapText.lower():
                                        if ('syndrome' not in mapText.lower() or ('syndrome' in mapText.lower() and 'syndrome' not in ' '.join(biomarkerList[phrasePos]).lower())) and \
                                                'stricture' not in mapText.lower():
                                            toAdd = mapText.lower()
                                            if mapText.lower().split()[len(mapText.lower().split()) - 1] in ['amplification']:
                                                if mapText.lower().split()[len(mapText.lower().split()) - 1] not in conceptList[phrasePos]:
                                                    conceptList[phrasePos].append(mapText.lower().split()[len(mapText.lower().split()) - 1])
                                                    print('concept added position 47')
                                                toAdd = ' '.join(mapText.lower().split()[:-1])
                                                # Drop stuff like 'her2 gene' down to just 'her2'
                                                if len(toAdd.split()) == 2:
                                                    if toAdd.split()[1] in ['gene']:
                                                        toAdd = toAdd.split()[0]
                                            if toAdd not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append(toAdd)
                                                if debug:
                                                    print("added biomarker position 106")

                            # The 'qnco' seems to be important for diminished signals, who knows what else? But we're adding
                            # slowly, is the point.
                            if semType == 'qnco' and 'diminished' in mapText.lower():
                                if 'diminished signal' not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append('diminished signal')
                                    if debug:
                                        print("added concept position 37")
                            # 'qlco' seems like it gives qualifier words
                            if semType == 'qlco':

                                # Though it can also give intensities
                                if mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() in ['intensity', 'normal']:
                                    if mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower())
                                        if debug:
                                            print("added concept position 38")
                                    # Sometimes the intensity is a number
                                    if len(utterance['Phrases']) > phrasePos + 1:
                                        if '(' in utterance['Phrases'][phrasePos + 1]['PhraseText'] and utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('(', '').replace('+', '').isnumeric():
                                            if utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('(', '') not in qualifierList[phrasePos]:
                                                qualifierList[phrasePos].append(utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('(', ''))
                                                if debug:
                                                    print("added qualifier position 52")
                                        elif len(utterance['Phrases'][phrasePos]['PhraseText'].split()) > 1 and utterance['Phrases'][phrasePos]['PhraseText'].split()[1].replace('.', '').replace('+',
                                                                                                                                                                                                  '').isnumeric():
                                            if utterance['Phrases'][phrasePos]['PhraseText'].split()[1].replace('.', '') not in qualifierList[phrasePos]:
                                                qualifierList[phrasePos].append(utterance['Phrases'][phrasePos]['PhraseText'].split()[1].replace('.', ''))
                                                if debug:
                                                    print("added qualifier position 53")
                                            # Sometimes it's a sample with '#'
                                            elif '(' in utterance['Phrases'][phrasePos + 1]['PhraseText'] and utterance['Phrases'][phrasePos + 1]['PhraseText'].replace('(', '') == '#':
                                                if 'unspecified' not in qualifierList[phrasePos]:
                                                    qualifierList[phrasePos].append('unspecified')
                                                    if debug:
                                                        print("added qualifier position 54")

                                # Or strengths
                                if mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() in ['strong', 'weak', 'moderate', 'equivocal', 'patchy', 'atypical', 'indeterminate',
                                                                                                       'patchy distribution', 'low']:
                                    if mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() not in qualifierList[phrasePos]:
                                        qualifierList[phrasePos].append(mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower())
                                        if debug:
                                            print("added qualifier position 43")

                                # Most of the rest of what we're looking for are adverbs
                                if 'adv' in partOfSpeechList[phrasePos]:
                                    if mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() not in qualifierList[phrasePos] \
                                            and mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() not in ['to', 'sufficient', 'insufficient', 'molecular']:
                                        if mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() in ['diagnosis']:
                                            if mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower() not in conceptList[phrasePos]:
                                                conceptList[phrasePos].append(mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower())
                                                if debug:
                                                    print("added concept position 39")

                                        else:
                                            qualifierList[phrasePos].append(mapping['MappingCandidates'][mcPos]['CandidateMatched'].lower())
                                            if debug:
                                                print("added qualifier position 44")
                                        if hasIndicated:
                                            hasIndicated = False
                                # This is also a place we can capture 'no coding variants'
                                if 'no coding variants' in phrase['PhraseText'].lower():
                                    if 'normal results' not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append('normal results')
                                        if debug:
                                            print("added biomarker position 107")
                                        qualifierList[phrasePos].append('positive')
                                        if debug:
                                            print("added qualifier position 45")
                                        if hasIndicated:
                                            hasIndicated = False
                                        if conceptList[phrasePos] == ['coding variant']:
                                            conceptList[phrasePos] = []
                                            pocketConcept = 'coding variant'
                                if 'combine' in phrase['PhraseText'].lower():
                                    if 'positive score' in phrase['PhraseText'].lower():
                                        if 'combined positive score' not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append('combined positive score')
                                            if debug:
                                                print("added concept position 40")

                            # 'imft' can be our first-choice for pd-l1 sometimes (others?)
                            if 'aapp' in mapCan['SemTypes'] and any(x in mapCan['SemTypes'] for x in ['imft']):
                                phraseText = [x.lower() for x in phrase['PhraseText'].replace('.', '').replace(',', '').replace('-', ' ').split()]
                                if 'pd' in phraseText and 'l1' in phraseText:
                                    if 'pd-l1' not in ''.join(list(itertools.chain.from_iterable(biomarkerList))):
                                        biomarkerList[phrasePos].append('pd-l1')
                                        if debug:
                                            print("added biomarker position 108")
                            # I want to be careful adding in 'aapp's. Let's try it only if they are also receptors!
                            # Also, we want to make sure that the actual 'candidatePreferred' is in the next
                            if 'aapp' in mapCan['SemTypes'] and any(x in mapCan['SemTypes'] for x in ['rcpt', 'enzy', 'bacs']):
                                toAdd = ''
                                phraseText = [x.lower() for x in phrase['PhraseText'].replace('.', '').replace(',', '').replace('-', ' ').replace('(', '').replace('+', ' ').split()]
                                if mapCan['CandidateMatched'].lower() in phraseText:
                                    toAdd = mapCan['CandidateMatched'].lower()
                                elif 'oncogene protein' in mapCan['CandidateMatched'].lower() and mapCan['CandidateMatched'].lower() != 'oncogene protein':
                                    toAdd = mapCan['CandidateMatched'].lower()
                                elif mapCan['CandidatePreferred'].split()[0].lower() in phraseText:
                                    toAdd = mapCan['CandidatePreferred'].split()[0].lower()
                                    if len(mapCan['CandidatePreferred'].split()) > 1:
                                        if mapCan['CandidatePreferred'].split()[1].lower() in ['receptor', 'receptors']:
                                            toAdd = toAdd + ' receptor'
                                elif mapCan['MatchedWords'][0] in phraseText:
                                    toAdd = mapCan['MatchedWords'][0]
                                    # for genes like 'gcdfp-15'
                                    if len(mapCan['MatchedWords']) > 1:
                                        if mapCan['MatchedWords'][1].isnumeric() and '-' in mapCan['CandidateMatched']:
                                            toAdd = toAdd + '-' + mapCan['MatchedWords'][1]
                                        if mapCan['MatchedWords'][1] in ['receptor', 'receptors']:
                                            toAdd = toAdd + ' receptor'
                                if len(mapCan['CandidatePreferred']) > 1:
                                    if toAdd and mapCan['CandidatePreferred'][1] in ['receptor', 'receptors']:
                                        toAdd = toAdd + ' receptor'
                                    if mapCan['CandidatePreferred'][1].isnumeric() and '-' in mapCan['CandidateMatched']:
                                        toAdd = toAdd + '-' + mapCan['CandidatePreferred'][1]
                                if toAdd and toAdd not in biomarkerList[phrasePos] and toAdd not in ['to']:
                                    if 'fish' in phraseText and 'assay' in phraseText:
                                        toAdd = ''
                                    if toAdd + ' locus' in ' '.join(phraseText).lower():
                                        toAdd = toAdd + ' locus'
                                    if len(toAdd.split('/')) > 1:
                                        if toAdd.split('/')[0] in biomarkerList[phrasePos]:
                                            toAdd = ''
                                    if toAdd and toAdd.lower().replace('-', '') not in ' '.join(biomarkerList[phrasePos]).replace('-', '') and not (toAdd.lower() in
                                                                                                                                                    ['sep', 'mismatch', 'proteins', 'ms', 'oncogene',
                                                                                                                                                     'receptors', 'cish', 'hormone receptor', 'fish']):
                                        # if the gene was listed as "egfr+", we want to assume that means "egfr positive"
                                        if toAdd + '+' in phrase['PhraseText']:
                                            if 'positive' not in qualifierList[phrasePos]:
                                                qualifierList[phrasePos].append('positive')
                                                print('added qualifier position 64')
                                        elif toAdd + '- ' in phrase['PhraseText']:
                                            if 'negative' not in qualifierList[phrasePos]:
                                                qualifierList[phrasePos].append('negative')
                                                print('added qualifier position 63')
                                        # Special catch for granzymes
                                        if toAdd in ['granzyme'] and 'granzyme b' in utterance['UttText'].lower():
                                            toAdd = toAdd + ' b'
                                        if toAdd.lower() not in biomarkerList[phrasePos] and toAdd.lower() not in ' '.join(biomarkerList[phrasePos - 1]):
                                            # No gene names if they're only part of nuc ish!
                                            if 'nuc ish' in utterance['UttText']:
                                                nucish = utterance['UttText'][utterance['UttText'].index('nuc ish'):]
                                                nucish = nucish[:nucish.index(']') + 1]
                                                if toAdd.lower() not in utterance['UttText'].replace(nucish, ''):
                                                    continue
                                            biomarkerList[phrasePos].append(toAdd.lower())
                                            if debug:
                                                print("added biomarker position 109")
                                        if '-' in phrase['PhraseText']:
                                            if phrase['PhraseText'].replace('.', '').replace(',', '').split('-')[1].isnumeric():
                                                if phrase['PhraseText'].replace('.', '').replace(',', '') not in biomarkerList[phrasePos]:
                                                    biomarkerList[phrasePos].remove(toAdd.lower())
                                                    biomarkerList[phrasePos].append(phrase['PhraseText'].replace('.', '').replace(',', '').replace('; ', ''))
                                                    if debug:
                                                        print("added biomarker position 110")
                                            elif phrase['PhraseText'].replace('.', '').replace(',', '').split('-')[1]:
                                                toAddOld = toAdd
                                                toAdd = phrase['PhraseText'].replace('.', '').replace(',', '').split('-')[1].split()[0]
                                                if toAdd not in ' '.join(biomarkerList[phrasePos]) and toAdd.lower() not in ['to', 'unsuccessful', 'expressed', 'expression', 'negative/absent',
                                                                                                                             'decreased', 'transplant'] and toAdd.lower() not in toAddOld \
                                                        and not toAdd.replace('/', '').isnumeric() and 'splice site' not in phrase['PhraseText'] and 'oncogene protein' not in phrase['PhraseText']:
                                                    biomarkerList[phrasePos].append(toAdd.lower())
                                                    if debug:
                                                        print("added biomarker position 111")
                                                if toAdd in ['unsuccessful']:
                                                    if toAdd not in qualifierList[phrasePos]:
                                                        qualifierList[phrasePos].append(toAdd)
                                                        if debug:
                                                            print("added qualifier position 46")
                            # Likewise, 'ftcn' was good for a few qualifers, but let's add piecemeal.
                            if semType == 'ftcn' and mapText in ['suggestive']:
                                if 'possible' not in qualifierList[phrasePos]:
                                    qualifierList[phrasePos].append('possible')
                                    if debug:
                                        print("added qualifier position 47")
                                    if hasIndicated:
                                        hasIndicated = False

                            if semType == 'ftcn' and mapText in ['anomalies', 'anomaly']:
                                if 'anomaly' not in conceptList[phrasePos]:
                                    conceptList[phrasePos].append('anomaly')
                                    if debug:
                                        print("added concept position 41")

                            # I guess we can call deletions 'deleted's? Fine.
                            if semType == 'acty' and mapText.lower() in ['deleted'] and len(utterance['Phrases']) > phrasePos + 1:
                                if utterance['Phrases'][phrasePos + 1]['PhraseText'].isnumeric():
                                    if mapText not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(mapText)
                                        if debug:
                                            print("added concept position 42")
                                    if utterance['Phrases'][phrasePos + 1]['PhraseText'].lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(utterance['Phrases'][phrasePos + 1]['PhraseText'].lower())
                                        if debug:
                                            print("added biomarker position 112")
                                # It can also be 'evidence of deleted xq'
                                elif utterance['Phrases'][phrasePos]['PhraseText'].split('deleted')[1].strip().replace('.', '').replace(',', '').replace('q', '').isnumeric():
                                    if 'deletion' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('deletion')
                                        if debug:
                                            print("added concept position 43")
                                    if utterance['Phrases'][phrasePos]['PhraseText'].split('deleted')[1].strip().replace('.', '').replace(',', '').lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(utterance['Phrases'][phrasePos]['PhraseText'].split('deleted')[1].strip().replace('.', '').replace(',', '').lower())
                                        if debug:
                                            print("added biomarker position 113")
                            # Also note that it can be the last phrase - smushed together.
                            if semType == 'acty' and 'deleted' in mapText.lower() and len(utterance['Phrases']) == phrasePos + 1:
                                if utterance['Phrases'][phrasePos]['PhraseText'].split('deleted')[1].strip().replace('.', '').replace(',', '').replace('q', '').isnumeric():
                                    if 'deletion' not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append('deletion')
                                        if debug:
                                            print("added concept position 44")
                                    if utterance['Phrases'][phrasePos]['PhraseText'].split('deleted')[1].strip().replace('.', '').replace(',', '').lower() not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(utterance['Phrases'][phrasePos]['PhraseText'].split('deleted')[1].strip().replace('.', '').lower())
                                        if debug:
                                            print("added biomarker position 114")

                            # "5' Region" (and I should put 3' in here too)
                            if semType == 'geoa' and mapText.lower() == 'region':
                                phraseTextSamp = [x.lower() for x in phrase['PhraseText'].replace('s', '').replace('.', '').replace(',', '').split()]
                                for pt in range(0, len(phraseTextSamp)):
                                    if phraseTextSamp[pt] == 'regions':
                                        phraseTextSamp[pt] = 'region'
                                wordIndex = [i for i, elem in enumerate(phraseTextSamp) if 'region' in elem][0]
                                if wordIndex > 0:
                                    if phraseTextSamp[wordIndex - 1] in ["5'", "3'"]:
                                        toAdd = phraseTextSamp[wordIndex - 1] + ' region'
                                        if toAdd not in qualifierList[phrasePos]:
                                            qualifierList[phrasePos].append(toAdd)
                                            if debug:
                                                print("added qualifier position 48")
                                            if hasIndicated:
                                                hasIndicated = False

                            # the "Nusq" type isn't usually appropriate, but SOMETIMES it's how they indicate
                            # a part of a probe location.
                            if semType == 'nusq' and len(utterance['Phrases']) - 1 > phrasePos:
                                if utterance['Phrases'][phrasePos + 1]['PhraseText'].startswith('(') and mapText.replace('p', '').isnumeric():
                                    toAdd = mapText
                                    location = phrasePos + 1
                                    while ')' not in utterance['Phrases'][location]['PhraseText']:
                                        toAdd = toAdd + utterance['Phrases'][location]['PhraseText']
                                        if location < len(utterance['Phrases']) - 1:
                                            location = location + 1
                                        else:
                                            break
                                    toAdd = toAdd + ')'
                                    if toAdd.lower() not in biomarkerList[phrasePos + 1]:
                                        biomarkerList[phrasePos + 1].append(toAdd.lower())
                                        print('added biomarker HIDDEN LOCATION 1')
                                        for bit in biomarkerList[phrasePos]:
                                            if bit in toAdd.lower():
                                                biomarkerList[phrasePos].remove(bit)

                            # Get some high-level concepts
                            if any(x in utterance['Phrases'][phrasePos]['PhraseText'].lower() for x in ['coding variant', 'copy number alteration', 'gene fusion']):
                                for y in ['coding variant', 'copy number alteration', 'gene fusion']:
                                    if y in utterance['Phrases'][phrasePos]['PhraseText'].lower():
                                        if not conceptList[phrasePos] and 'Normal Results' not in biomarkerList[phrasePos] and y not in biomarkerList[phrasePos]:
                                            conceptList[phrasePos].append(y)
                                            if debug:
                                                print("added concept position 45")

                            # This is for Exons. I'm ASSUMING here that we'll always mention a gene before an exon/AA list.
                            # Wrong. Look for 'exon 4 of the [x] gene'
                            if semType in ['bacs', 'comd'] and 'exon' in phrase['PhraseText'].replace('(', '').lower():
                                lastMarker = ''
                                fixedPhrase = phrase['PhraseText'].lower().replace('exons', 'exon')
                                if fixedPhrase + ' of the' in utterance['UttText'].lower():
                                    fixedPhrase = fixedPhrase.replace('to ', '')
                                    if fixedPhrase not in numericList[phrasePos]:
                                        numericList[phrasePos].append(fixedPhrase)
                                else:
                                    # Assuming the phrase is something like 'EGFR exon 4,'
                                    gene = ''
                                    if len(fixedPhrase.split('exon')) > 1:
                                        if len(fixedPhrase.split('exon')[0]) >= 1:
                                            # We'll pull the previous word in IF it's a noun!
                                            for unit in phrase['SyntaxUnits']:
                                                if 'LexCat' in unit.keys():
                                                    if unit['InputMatch'].lower() == fixedPhrase.split('exon')[0].split()[-1] and unit['LexCat'] == 'noun':
                                                        gene = fixedPhrase.split('exon')[0].split()[-1]
                                        fixedPhrase = fixedPhrase.split('exon')[1].replace(',', '').strip()
                                        fixedPhraseFull = fixedPhrase
                                        if len(fixedPhrase.split()) == 0:
                                            continue
                                        fixedPhrase = fixedPhrase.split()[0]
                                        lastMarker = phrasePos
                                        phrPosition = phrasePos
                                        # We'll scan backwards, and, if we find a biomarker, attach the exons to it.
                                        if not biomarkerList[lastMarker]:
                                            while lastMarker >= 0 and not biomarkerList[lastMarker]:
                                                lastMarker = lastMarker - 1
                                        # If this is the only negative after a lot of positives, deal with it here
                                        if qualifierList[lastMarker] != qualifierList[phrasePos]:
                                            biomarkerList[phrasePos].append('exon ' + fixedPhrase)
                                            if debug:
                                                print("added biomarker position 115")
                                        elif 'exon ' + fixedPhrase not in biomarkerList[lastMarker]:
                                            biomarkerList[lastMarker].append('exon ' + fixedPhrase)
                                            print('added biomarker position exon 1')
                                        if gene and gene not in biomarkerList[lastMarker]:
                                            biomarkerList[lastMarker].append(gene)
                                            print('added biomarker position exon 2')
                                        phrPosition = phrPosition + 1
                                        if phrPosition + 1 < len(utterance['Phrases']):
                                            # We'll move forward, getting more tokens as they come. Ranges are good too!
                                            # Starting with the original phrase
                                            if len(fixedPhraseFull.split()) > 1:
                                                fixedPhraseFull = fixedPhraseFull.split()
                                                for p in range(1, len(fixedPhraseFull)):
                                                    if fixedPhraseFull[p].replace(',', '').replace('-', '').isnumeric() \
                                                            or fixedPhraseFull[p].replace(',', '').replace('-', '').lower() == 'and':
                                                        if 'exon ' + fixedPhraseFull[p].replace(',', '').replace('.', '') not in biomarkerList[lastMarker] \
                                                                and utterance['Phrases'][phrPosition]['PhraseText'].replace(',', '').replace('.', '') not in ['and']:
                                                            # Some special instructions to get ranges
                                                            if '-' in fixedPhraseFull[p].replace(',', '').replace('.', ''):
                                                                toAdd = ''
                                                                rangeEx = fixedPhraseFull[p].replace(',', '').replace('.', '')
                                                                lower = rangeEx.split('-')[0]
                                                                higher = rangeEx.split('-')[1]

                                                                for x in range(int(lower), int(higher) + 1):
                                                                    if 'exon ' + str(x) not in biomarkerList[lastMarker]:
                                                                        biomarkerList[lastMarker].append('exon ' + str(x))
                                                            else:
                                                                biomarkerList[lastMarker].append('exon ' + fixedPhraseFull[p].replace(',', '').replace('.', ''))

                                            # Then the rest
                                            while phrPosition < len(utterance['Phrases']) and '(' not in utterance['Phrases'][phrPosition]['PhraseText']:
                                                if utterance['Phrases'][phrPosition]['PhraseText'].replace('-', '').replace(',', '').replace('.', '').isnumeric() \
                                                        or utterance['Phrases'][phrPosition]['PhraseText'].replace('-', '').replace(',', '').replace('.', '').lower() == 'and':
                                                    if 'exon ' + utterance['Phrases'][phrPosition]['PhraseText'].replace(',', '').replace('.', '') not in biomarkerList[lastMarker] \
                                                            and utterance['Phrases'][phrPosition]['PhraseText'].replace(',', '').replace('.', '') not in ['and']:
                                                        # Some special instructions to get ranges
                                                        if '-' in utterance['Phrases'][phrPosition]['PhraseText'].replace(',', '').replace('.', ''):
                                                            toAdd = ''
                                                            rangeEx = utterance['Phrases'][phrPosition]['PhraseText'].replace(',', '').replace('.', '')
                                                            lower = rangeEx.split('-')[0]
                                                            higher = rangeEx.split('-')[1]

                                                            for x in range(int(lower), int(higher) + 1):
                                                                if 'exon ' + str(x) not in biomarkerList[lastMarker]:
                                                                    biomarkerList[lastMarker].append('exon ' + str(x))
                                                        else:
                                                            biomarkerList[lastMarker].append('exon ' + utterance['Phrases'][phrPosition]['PhraseText'].replace(',', '').replace('.', ''))
                                                phrPosition = phrPosition + 1
                                            if phrPosition == len(utterance['Phrases']):
                                                phrPosition = phrPosition - 1
                                            # Sometimes right after an exon sequence we'll get a special variant - this is not an amino acid sequence.
                                            if '(' in utterance['Phrases'][phrPosition]['PhraseText'] and 'aa' not in utterance['Phrases'][phrPosition]['PhraseText'].lower() \
                                                    and 'variant' not in utterance['Phrases'][phrPosition]['PhraseText'].lower():
                                                toAdd = utterance['Phrases'][phrPosition]['PhraseText'].replace('(', '')
                                                phrPosition = phrPosition + 1
                                                if phrPosition < len(utterance['Phrases']):
                                                    while ')' not in utterance['Phrases'][phrPosition]['PhraseText'] and phrPosition + 1 < len(utterance['Phrases']):
                                                        toAdd = toAdd + utterance['Phrases'][phrPosition]['PhraseText']
                                                        phrPosition = phrPosition + 1
                                                if toAdd not in biomarkerList[lastMarker]:
                                                    biomarkerList[lastMarker].append(toAdd)
                                    # I might need to change this later. I'm assuming 'exons' and 'amino acids' are part of the panel, so we'll add that result - CHANGED
                                    if 'tested' not in qualifierList[lastMarker] and not conceptList[lastMarker] and 'negative' not in qualifierList[lastMarker]:
                                        # qualifierList[lastMarker].append('tested')
                                        if hasIndicated:
                                            hasIndicated = False

                            # And here, sometimes, it looks like exons just aren't tagged sometimes?
                            elif 'exon' in phrase['PhraseText'].replace('(', '').lower():
                                phraseWithExon = phrase['PhraseText'].replace('(', '').lower()
                                indices = [m.start() for m in re.finditer('exon', phraseWithExon)]
                                for ind in range(0, len(indices) - 1):
                                    subphrase = phraseWithExon[indices[ind]:indices[ind + 1]]
                                    subphrase = subphrase.split()
                                    subphrase = subphrase[1:]
                                    for s in subphrase:
                                        if s.replace(',', '').isnumeric():
                                            if 'exon ' + s not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append('exon ' + s)
                                                if debug:
                                                    print("added biomarker position 116")
                                        else:
                                            break
                                    # This catches the last one.
                                    subphrase = phraseWithExon[indices[-1]:]
                                    subphrase = subphrase.split()
                                    subphrase = subphrase[1:]
                                    for s in subphrase:
                                        if s.replace(',', '').isnumeric():
                                            if 'exon ' + s not in biomarkerList[phrasePos]:
                                                biomarkerList[phrasePos].append('exon ' + s)
                                                if debug:
                                                    print("added biomarker position 117")
                                        else:
                                            break

                            # This is for Amino Acid Ranges. I'm ASSUMING here that we'll always mention a gene before an exon/AA list.
                            if 'aa ' in phrase['PhraseText'].replace('(', '').lower():
                                if phrase['PhraseText'].lower().replace('(', '').replace('-', '').replace(',', '').replace('.', '').replace('aa', '').replace(' ', '').isnumeric():
                                    lastMarker = phrasePos
                                    phrPosition = phrasePos
                                    # This way, if a biomarker popped up earlier, we'll add the AAs to it. If none has popped up, they'll be added to the first place.
                                    # Seems like the right way to go.
                                    if not biomarkerList[lastMarker]:
                                        while lastMarker >= 0 and not biomarkerList[lastMarker]:
                                            lastMarker = lastMarker - 1
                                    if 'aa ' + phrase['PhraseText'].lower().split('aa')[1].replace(' ', '').replace(',', '') not in biomarkerList[lastMarker]:
                                        biomarkerList[lastMarker].append('aa ' + phrase['PhraseText'].lower().split('aa')[1].replace(' ', '').replace(',', ''))

                                    phrPosition = phrPosition + 1
                                    if phrPosition < len(utterance['Phrases']):
                                        while phrPosition < len(utterance['Phrases']) and ')' not in utterance['Phrases'][phrPosition]['PhraseText']:
                                            if 'aa ' + utterance['Phrases'][phrPosition]['PhraseText'].replace(',', '').replace('.', '') not in biomarkerList[lastMarker]:
                                                biomarkerList[lastMarker].append('aa ' + utterance['Phrases'][phrPosition]['PhraseText'].replace(',', '').replace('.', ''))
                                            phrPosition = phrPosition + 1
                                    # I might need to change this later. I'm assuming 'exons' and 'amino acids' are part of the panel, so we'll add that result
                                    if 'tested' not in qualifierList[lastMarker]:
                                        qualifierList[lastMarker] = ['tested']
                                        print('qualifier list updated by aa panel')
                                        if hasIndicated:
                                            hasIndicated = False

                            # If the result is negated, we'll want to note that. Negations go in the qualifier list.
                            if mapCan['Negated'] == '1' or mapCan['CandidateMatched'].lower() == 'negative':
                                # We don't want to negate an already negative! We MIGHT only want to negate something else?
                                if 'no' not in toAdd.lower():
                                    if 'negative' not in qualifierList[phrasePos] and (biomarkerList[phrasePos] or conceptList[phrasePos] or numericList[phrasePos]):
                                        if 'normal results' not in biomarkerList[phrasePos]:
                                            qualifierList[phrasePos].append('negative')
                                            if debug:
                                                print("added qualifier position 49")
                                            if hasIndicated:
                                                hasIndicated = False

                            # If it's not something else, and we've seen one of the 'guessing' words, make it tentative!
                            if not qualifierList[phrasePos] and hasIndicated:
                                qualifierList[phrasePos].append('consistent with result')
                                if notIndicated:
                                    qualifierList[phrasePos].append('negative')
                                if debug:
                                    print("added qualifier position 50")
                # NEW ADDITION - we're looking for tiebreakers here. That is to say, if THIS phrase has BOTH a token AND one of the 'important' linking words ('but', '.', 'End' for now)
                # then we'll want to know if it came BEFORE, or AFTER the period. We'll demarcate this by means of a tiebreaking tag. It'll be $$$Before$. and $$$After$.
                # The structure of the token is - three $s for the start. Then 'before' or 'after' to show position. Then a $, then the actual linking word.

                for link in linkingList[phrasePos]:
                    if link == '.':
                        if utterance['Phrases'][phrasePos]['PhraseText'].endswith('.'):
                            for bio in range(0, len(biomarkerList[phrasePos])):
                                biomarkerList[phrasePos][bio] = biomarkerList[phrasePos][bio] + '$$$$Before$.'
                            for con in range(0, len(conceptList[phrasePos])):
                                conceptList[phrasePos][con] = conceptList[phrasePos][con] + '$$$$Before$.'
                            for num in range(0, len(numericList[phrasePos])):
                                numericList[phrasePos][num] = numericList[phrasePos][num] + '$$$$Before$.'
                            for qua in range(0, len(qualifierList[phrasePos])):
                                qualifierList[phrasePos][qua] = qualifierList[phrasePos][qua] + '$$$$Before$.'
                            for tim in range(0, len(timeList[phrasePos])):
                                timeList[phrasePos][tim] = timeList[phrasePos][tim] + '$$$$Before$.'
                        else:
                            # This is to add space in case we have a .,
                            text = utterance['Phrases'][phrasePos]['PhraseText'].replace(',', ' ,').lower()
                            indicePeriod = [m.start() for m in re.finditer(r'\.(\s)', text)]
                            if indicePeriod:
                                indicePeriod = indicePeriod[0]
                            else:
                                indicePeriod = 0
                            for bio in range(0, len(biomarkerList[phrasePos])):
                                newMarker = biomarkerList[phrasePos][bio]
                                if newMarker not in ['medically relevant']:
                                    newMarker = newMarker.replace(')', '\)').replace('(', '\(')
                                    indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                                if indiceMarker:
                                    indiceMarker = indiceMarker[0]
                                else:
                                    indiceMarker = 999
                                if indicePeriod < indiceMarker:
                                    newMarker = newMarker + '$$$$After$.'
                                else:
                                    newMarker = newMarker + '$$$$Before$.'
                                biomarkerList[phrasePos][bio] = newMarker.replace('\)', ')').replace('\(', '(')
                            for con in range(0, len(conceptList[phrasePos])):
                                newMarker = conceptList[phrasePos][con]
                                if newMarker not in ['fetal sex']:
                                    indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                                if indiceMarker:
                                    indiceMarker = indiceMarker[0]
                                else:
                                    indiceMarker = 999
                                if indicePeriod < indiceMarker:
                                    newMarker = newMarker + '$$$$After$.'
                                else:
                                    newMarker = newMarker + '$$$$Before$.'
                                conceptList[phrasePos][con] = newMarker
                            for num in range(0, len(numericList[phrasePos])):
                                wholeMarker = numericList[phrasePos][num]
                                # We frequently futz around with the numeric, so I'm protecting that here.
                                newMarker = numericList[phrasePos][num].split()[0]
                                indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                                if indiceMarker:
                                    indiceMarker = indiceMarker[0]
                                else:
                                    indiceMarker = 999
                                if indicePeriod < indiceMarker:
                                    newMarker = wholeMarker + '$$$$After$.'
                                else:
                                    newMarker = wholeMarker + '$$$$Before$.'
                                numericList[phrasePos][num] = newMarker
                            for qua in range(0, len(qualifierList[phrasePos])):
                                indiceMarker = []
                                newMarker = qualifierList[phrasePos][qua]
                                # newMarker = newMarker.split()[0]
                                if newMarker not in ['consistent with result', 'qns']:
                                    indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                                if indiceMarker:
                                    indiceMarker = indiceMarker[0]
                                else:
                                    indiceMarker = 999
                                if indicePeriod < indiceMarker:
                                    newMarker = newMarker + '$$$$After$.'
                                else:
                                    newMarker = newMarker + '$$$$Before$.'
                                qualifierList[phrasePos][qua] = newMarker
                            for tim in range(0, len(timeList[phrasePos])):
                                indiceMarker = []
                                newMarker = timeList[phrasePos][tim]
                                newMarker = newMarker.split()[0]
                                if newMarker not in ['no counters yet']:
                                    indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                                if indiceMarker:
                                    indiceMarker = indiceMarker[0]
                                else:
                                    indiceMarker = 999
                                if indicePeriod < indiceMarker:
                                    newMarker = newMarker + '$$$$After$.'
                                else:
                                    newMarker = newMarker + '$$$$Before$.'
                                timeList[phrasePos][tim] = newMarker


                    # Since 'end' is a token that I add whenever we find some words that mean we stop looking for tokens, I've
                    # made it's pattern ' end$$$$[word] '. We'll have to extract that. The other words (just 'but' so far) are
                    # just held alone.
                    elif link in ['but'] or 'end$$$$' in link:
                        # If the token is 'end', let's separate that out now.
                        isEnd = False
                        if len(link.split('$$$$')) > 1:
                            isEnd = True
                            oldLink = link
                            link = link.split('$$$$')[1]
                        text = utterance['Phrases'][phrasePos]['PhraseText'].replace(',', ' ,')
                        indicePeriod = ''
                        if link not in ['*']:
                            indicePeriod = [m.start() for m in re.finditer(link, text)]
                        if indicePeriod:
                            indicePeriod = indicePeriod[0]
                        else:
                            indicePeriod = 0
                        if isEnd:
                            linkingList[phrasePos].remove(oldLink)
                            link = 'end'
                            linkingList[phrasePos] = ['end']
                        for bio in range(0, len(biomarkerList[phrasePos])):
                            newMarker = biomarkerList[phrasePos][bio]
                            indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                            if indiceMarker:
                                indiceMarker = indiceMarker[0]
                            else:
                                indiceMarker = 999
                            if indicePeriod < indiceMarker:
                                newMarker = newMarker + '$$$$After$' + link
                            else:
                                newMarker = newMarker + '$$$$Before$' + link
                            biomarkerList[phrasePos][bio] = newMarker
                        for con in range(0, len(conceptList[phrasePos])):
                            newMarker = conceptList[phrasePos][con]
                            indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                            if indiceMarker:
                                indiceMarker = indiceMarker[0]
                            else:
                                indiceMarker = 999
                            if indicePeriod < indiceMarker:
                                newMarker = newMarker + '$$$$After$' + link
                            else:
                                newMarker = newMarker + '$$$$Before$' + link
                            conceptList[phrasePos][con] = newMarker
                        for num in range(0, len(numericList[phrasePos])):
                            wholeMarker = numericList[phrasePos][num]
                            # We frequently futz around with the numeric, so I'm protecting that here.
                            newMarker = numericList[phrasePos][num].split()[0]
                            indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                            indiceMarker = indiceMarker[0]
                            if indicePeriod < indiceMarker:
                                newMarker = wholeMarker + '$$$$After$' + link
                            else:
                                newMarker = wholeMarker + '$$$$Before$' + link
                            numericList[phrasePos][num] = newMarker
                            numericList[phrasePos][num] = newMarker
                        for qua in range(0, len(qualifierList[phrasePos])):
                            newMarker = qualifierList[phrasePos][qua].split('$$$$')[0]
                            indiceMarker = ''
                            if newMarker not in ['commonly seen in this situation', 'consistent with result', 'frequently observed', 'associated with', 'qns']:
                                indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                            if indiceMarker:
                                if isinstance(indiceMarker, list):
                                    indiceMarker = indiceMarker[0]
                            else:
                                indiceMarker = 999
                            if indicePeriod < indiceMarker:
                                newMarker = newMarker + '$$$$After$' + link
                            else:
                                newMarker = newMarker + '$$$$Before$' + link
                            qualifierList[phrasePos][qua] = newMarker
                        for tim in range(0, len(timeList[phrasePos])):
                            newMarker = timeList[phrasePos][tim].split('$$$$')[0]
                            indiceMarker = ''
                            if newMarker not in ['no counters yet']:
                                indiceMarker = [m.start() for m in re.finditer(newMarker, text)]
                            if indiceMarker:
                                if isinstance(indiceMarker, list):
                                    indiceMarker = indiceMarker[0]
                            else:
                                indiceMarker = 999
                            if indicePeriod < indiceMarker:
                                newMarker = newMarker + '$$$$After$' + link
                            else:
                                newMarker = newMarker + '$$$$Before$' + link
                            timeList[phrasePos][time] = newMarker

            if debug:
                print(biomarkerList)
                print(conceptList)
                print(numericList)
                print(qualifierList)
                print(linkingList)
                print(timeList)
                print('')
                # input()

            # ################################################################################################################
            # ###############################################################################################################
            # ########## ALRIGHT, NOW IT'S TIME TO MAKE THE LISTS. Note that we're assuming at this point that we've got
            # a number of lists of identical length - biomarker, concept, numeric, qualifier. We've also got
            # linkingLists which is of equal length, and contains the concept boundaries.

            # A result can be a biomarker without a concept ("We found ALK"), a concept without a biomarker ("we found
            # aneuploidy"), or both ("Aneuploidy of Chromosome 2"), and any of those three can have a numeric or qualifier,
            # but you can never have a numeric or qualifier without a concept or biomarker. An assumption of this process,
            # WHICH MAY BE PROVED TO BE WRONG, is that a sentence boundary (semi-colons too?) and the word 'but' always
            # indicate that we've stopped talking about one biomarker, and are starting to talk about another one.
            if not endBiomarkerScan:
                conceptOnDeck = []
                numberOnDeck = []
                qualifierOnDeck = []
                biomarkerOnDeck = []
                timeOnDeck = []

                # The linkerOnDeck is especially valuable. This is what lets us know what kind of behavior to
                # do with the stuff we encounter.
                linkerOnDeck = ''
                previousLinker = ''
                prepreviousLinker = ''

                # The default of Used is actually maybe 'False'. Let's see!
                conceptUsed = False
                numberUsed = False
                qualifierUsed = False
                biomarkerUsed = False
                timeUsed = False

                # Since all lists are the same length, len(biomarkerList) might as well be conceptList or any other.
                for i in range(0, len(biomarkerList)):

                    # This is here so that we don't put a biomarker on deck and immediately remove it!
                    newBioOnDeck = False

                    # toAdd is for anything that comes BEFORE the linker, toAdd2 is for anything that comes AFTER. If only one is filled at the end,
                    # we'll just add that one. If both are filled, we'll add them one at a time!
                    toAddBioBefore = []
                    toAddBioAfter = []
                    toAddBioOnly = []
                    toAddConBefore = []
                    toAddConAfter = []
                    toAddConOnly = []
                    toAddNumBefore = []
                    toAddNumAfter = []
                    toAddNumOnly = []
                    toAddQualBefore = []
                    toAddQualAfter = []
                    toAddQualOnly = []
                    toAddTimeBefore = []
                    toAddTimeAfter = []
                    toAddTimeOnly = []

                    # Metamap splits up (> when it shouldn't
                    if '(' in ''.join(linkingList[i]):
                        if len(numericList) > i + 1:
                            if '>' in ''.join(numericList[i + 1]) or '<' in ''.join(numericList[i + 1]):
                                numericList[i] = numericList[i + 1]
                                numericList[i + 1] = []

                    # End tokens mean we're done looking for tokens.
                    if 'end' in linkingList[i]:
                        # If we're ABSOLUTELY SURE there's no biomarker, we can just add a concept here.
                        if conceptOnDeck and len(resultsListBiomarker) == 0:
                            for con in conceptOnDeck:
                                resultsListConcept.append([con])
                            resultsListBiomarker.append([])
                            if numberOnDeck:
                                for num in numberOnDeck:
                                    resultsListNumeric.append([num])
                            else:
                                resultsListNumeric.append([])
                            if qualifierOnDeck:
                                for qual in qualifierOnDeck:
                                    resultsListQualifier.append([qual])
                            else:
                                resultsListQualifier.append([])
                            if timeOnDeck:
                                for tim in timeOnDeck:
                                    resultsListTime.append(tim)
                            else:
                                resultsListTime.append([])
                        if 'Testing Not Performed' in ''.join(biomarkerList[i]):
                            finalBiomarkerResults.append(['testing not performed'])
                            if qualifierList[i]:
                                finalQualifierResults.append(qualifierList[i])
                        elif 'test not performed' in ''.join(biomarkerList[i]):
                            finalBiomarkerResults.append(['test not performed'])
                            if qualifierList[i]:
                                quals = []
                                for q in qualifierList[i]:
                                    q = q.replace('$$$$After$end', '')
                                    quals.append(q)
                                finalQualifierResults.append(quals)
                            if timeList[i]:
                                tims = []
                                for t in timeList[i]:
                                    t = t.replace('$$$After$end', '')
                                    tims.append(t)
                                finalTimeResults.append(tims)
                        elif 'no results' in ''.join(biomarkerList[i]):
                            finalBiomarkerResults.append(['no results'])
                            if qualifierList[i]:
                                quals = []
                                for q in qualifierList[i]:
                                    q = q.replace('$$$$After$end', '')
                                    quals.append(q)
                                finalQualifierResults.append(quals)
                            if timeList[i]:
                                tims = []
                                for t in timeList[i]:
                                    t = t.replace('$$$After$end', '')
                                    tims.append(t)
                                finalTimeResults.append(tims)
                        # No more guesswork with the tags. Add the concept IF it comes before the end!
                        if conceptList[i]:
                            for con in conceptList[i]:
                                if '$$$$' in con:
                                    if con.split('$$$$')[1] == 'Before':
                                        finalConceptResults.append(conceptList[i])
                        if qualifierList[i]:
                            if resultsListQualifier:
                                if not resultsListQualifier[-1]:
                                    resultsListQualifier[-1] = [' '.join(qualifierList[i]).split('$$$$')[0]]
                            else:
                                resultsListQualifier = [[' '.join(qualifierList[i]).split('$$$$')[0]]]
                        if conceptList[i]:
                            if resultsListConcept:
                                if not resultsListConcept[-1]:
                                    resultsListConcept[-1] = [' '.join(conceptList[i]).split('$$$$')[0]]
                            else:
                                resultsListConcept = [[' '.join(conceptList[i]).split('$$$$')[0]]]
                        if numericList[i]:
                            if resultsListNumeric:
                                if not resultsListNumeric[-1]:
                                    resultsListNumeric[-1] = [' '.join(numericList[i]).split('$$$$')[0]]
                            else:
                                resultsListNumeric = [[' '.join(numericList[i]).split('$$$$')[0]]]
                        if timeList[i]:
                            if resultsListTime:
                                if not resultsListTime[-1]:
                                    resultsListTime[-1] = [' '.join(timeList[i]).split('$$$$')[0]]
                            else:
                                resultsListTime = [[' '.join(timeList[i]).split('$$$$')[0]]]

                        endBiomarkerScan = True
                        break

                    # Now that we handled the extreme case of the 'end', let's see what else we might have in this position.
                    # First up: biomarkers.
                    if biomarkerList[i]:
                        # There might be multiple biomarkers, so we go through each of 'em
                        for marker in biomarkerList[i]:

                            # relPosition will be 'before' if the biomarker comes before the linking word in position i, 'after', if it comes after, and blank
                            # if there's no linking word in position i
                            relPositionBio = ''

                            # '$$$$' is the padding I put to separate out 'before' and 'after's for words in the same phrase as a linking word.
                            if '$$$$' in marker:
                                if marker.split('$$$$')[1].split('$')[0] == 'Before':
                                    relPositionBio = 'Before'
                                elif marker.split('$$$$')[1].split('$')[0] == 'After':
                                    relPositionBio = 'After'
                                marker = marker.split('$$$$')[0]

                            # If a marker is just a number (FOR NOW) then it's really 'chromosome #'
                            if marker.isnumeric() and marker not in ' '.join(numericList[i]) + ' '.join(qualifierList[i]) and 'exon ' + marker not in ' '.join(biomarkerList[i]):
                                if i > 0:
                                    otherThanMarker = biomarkerList[i].copy()
                                    for otm in otherThanMarker:
                                        if '$$$$' in otm:
                                            if marker == otm.split('$$$$')[0]:
                                                otherThanMarker.remove(otm)
                                        else:
                                            if marker == otm:
                                                otherThanMarker.remove(otm)
                                    if marker in ' '.join(biomarkerList[i - 1]) or marker in ' '.join(otherThanMarker):
                                        continue
                                lowerCase = 'chromosome ' + marker
                                upperCase = 'Chromosome ' + marker
                                if lowerCase not in biomarkerList[i] and upperCase not in biomarkerList[i] and int(marker) < 27:
                                    marker = 'chromosome ' + marker
                                else:
                                    continue
                            # UNLESS we've already seen this marker in the qualifier or numeric list. Sometimes a lone number
                            # gets added by mistake!
                            elif marker in ' '.join(numericList[i]) + ' '.join(qualifierList[i]) and marker not in ['microsatellite instability']:
                                continue
                            # If we have relPositionBio == '', then we're in the middle of a sentence. If it's 'Before', that's the end of a sentence.
                            # 'After' is the start of a new. Maybe confusing?
                            if marker and relPositionBio == '':
                                toAddBioOnly.append(marker)
                            if marker and relPositionBio == 'Before':
                                toAddBioBefore.append(marker)
                            if marker and relPositionBio == 'After':
                                toAddBioAfter.append(marker)

                    # Next, concepts.
                    if conceptList[i]:

                        # There might be multiple biomarkers, so we go through each of 'em
                        for marker in conceptList[i]:

                            # relPosition will be 'before' if the biomarker comes before the linking word in position i, 'after', if it comes after, and blank
                            # if there's no linking word in position i
                            relPositionCon = ''

                            # '$$$$' is the padding I put to separate out 'before' and 'after's for words in the same phrase as a linking word.
                            if '$$$$' in marker:
                                if marker.split('$$$$')[1].split('$')[0] == 'Before':
                                    relPositionCon = 'Before'
                                elif marker.split('$$$$')[1].split('$')[0] == 'After':
                                    relPositionCon = 'After'
                                marker = marker.split('$$$$')[0]

                            # If we have relPositionBio == '', then we're in the middle of a sentence. If it's 'Before', that's the end of a sentence.
                            # 'After' is the start of a new. Maybe confusing?
                            if marker and relPositionCon == '':
                                toAddConOnly.append(marker)
                            if marker and relPositionCon == 'Before':
                                toAddConBefore.append(marker)
                            if marker and relPositionCon == 'After':
                                toAddConAfter.append(marker)

                        conceptList[i] = []

                    # Now that we handled the extreme case of the 'end', let's see what else we might have in this position.
                    # First up: biomarkers.
                    if numericList[i]:

                        # There might be multiple biomarkers, so we go through each of 'em
                        for marker in numericList[i]:

                            # relPosition will be 'before' if the biomarker comes before the linking word in position i, 'after', if it comes after, and blank
                            # if there's no linking word in position i
                            relPositionNum = ''

                            # '$$$$' is the padding I put to separate out 'before' and 'after's for words in the same phrase as a linking word.
                            if '$$$$' in marker:
                                if marker.split('$$$$')[1].split('$')[0] == 'Before':
                                    relPositionNum = 'Before'
                                elif marker.split('$$$$')[1].split('$')[0] == 'After':
                                    relPositionNum = 'After'
                                marker = marker.split('$$$$')[0]

                            # If we have relPositionNum == '', then we're in the middle of a sentence. If it's 'Before', that's the end of a sentence.
                            # 'After' is the start of a new. Maybe confusing?
                            if marker and relPositionNum == '':
                                toAddNumOnly.append(marker)
                            if marker and relPositionNum == 'Before':
                                toAddNumBefore.append(marker)
                            if marker and relPositionNum == 'After':
                                toAddNumAfter.append(marker)

                        numericList[i] = []

                    # Now that we handled the extreme case of the 'end', let's see what else we might have in this position.
                    # Next up: time.
                    if timeList[i]:

                        # There might be multiple times, so we go through each of 'em
                        for marker in timeList[i]:

                            # relPosition will be 'before' if the time comes before the linking word in position i, 'after', if it comes after, and blank
                            # if there's no linking word in position i
                            relPositionTim = ''

                            # '$$$$' is the padding I put to separate out 'before' and 'after's for words in the same phrase as a linking word.
                            if '$$$$' in marker:
                                if marker.split('$$$$')[1].split('$')[0] == 'Before':
                                    relPositionTim = 'Before'
                                elif marker.split('$$$$')[1].split('$')[0] == 'After':
                                    relPositionTim = 'After'
                                marker = marker.split('$$$$')[0]

                            # If we have relPositionNum == '', then we're in the middle of a sentence. If it's 'Before', that's the end of a sentence.
                            # 'After' is the start of a new. Maybe confusing?
                            if marker and relPositionTim == '':
                                toAddTimeOnly.append(marker)
                            if marker and relPositionTim == 'Before':
                                toAddTimeBefore.append(marker)
                            if marker and relPositionTim == 'After':
                                toAddTimeAfter.append(marker)

                        timeList[i] = []

                    # Now that we handled the extreme case of the 'end', let's see what else we might have in this position.
                    # Finally: qualifiers
                    if qualifierList[i]:

                        # There might be multiple qualifiers, so we go through each of 'em
                        for marker in qualifierList[i]:

                            # relPosition will be 'before' if the qualifier comes before the linking word in position i, 'after', if it comes after, and blank
                            # if there's no linking word in position i
                            relPositionQual = ''

                            # '$$$$' is the padding I put to separate out 'before' and 'after's for words in the same phrase as a linking word.
                            if '$$$$' in marker:
                                if marker.split('$$$$')[1].split('$')[0] == 'Before':
                                    relPositionQual = 'Before'
                                elif marker.split('$$$$')[1].split('$')[0] == 'After':
                                    relPositionQual = 'After'
                                marker = marker.split('$$$$')[0]

                            # If we have relPositionQual == '', then we're in the middle of a sentence. If it's 'Before', that's the end of a sentence.
                            # 'After' is the start of a new. Maybe confusing?
                            if marker and relPositionQual == '':
                                toAddQualOnly.append(marker)
                            if marker and relPositionQual == 'Before':
                                toAddQualBefore.append(marker)
                            if marker and relPositionQual == 'After':
                                toAddQualAfter.append(marker)

                            # Here's a special case. If we find 'respectively' in the linkingList slot, and there are multiple numbers in the latest
                            # numbers slot, we need to distribute them! We're going to assume the easiest case and add to this later if need be.
                            if marker == 'respectively' and resultsListNumeric:
                                # First, we'll try an overloaded numeric
                                endPosition = len(resultsListNumeric) - 1
                                while resultsListNumeric[endPosition] == [] and endPosition > 0:
                                    endPosition = endPosition - 1
                                if len(resultsListNumeric[endPosition]) - 1 > 1:
                                    if resultsListNumeric[endPosition] == resultsListNumeric[endPosition - 1] and len(resultsListNumeric) > len(resultsListBiomarker):
                                        del resultsListNumeric[endPosition]
                                        endPosition = endPosition - 1
                                        break
                                    overloadedNumeric = resultsListNumeric[endPosition]
                                    inPlaceConcept = resultsListConcept[endPosition]
                                    inPlaceQualifier = resultsListQualifier[endPosition]
                                    inPlaceTime = resultsListTime[endPosition]
                                    if len(overloadedNumeric) == len(resultsListNumeric) - endPosition:
                                        resultsListNumeric[endPosition] = []
                                        for num in overloadedNumeric:
                                            resultsListNumeric[endPosition].append(num)
                                            if not resultsListConcept[endPosition]:
                                                resultsListConcept[endPosition] = inPlaceConcept
                                            if not resultsListQualifier[endPosition]:
                                                resultsListQualifier[endPosition] = inPlaceQualifier
                                            if not resultsListTime[endPosition]:
                                                resultsListTime[endPosition] = inPlaceTime
                                            endPosition = endPosition + 1

                                # If not that, we'll try an overloaded concept. That's it!
                                endPosition = len(resultsListConcept) - 1
                                if endPosition > 0:
                                    while resultsListConcept[endPosition] == [] and endPosition >= 0:
                                        endPosition = endPosition - 1
                                    if len(resultsListConcept[endPosition]) > 1:
                                        overloadedConcept = resultsListConcept[endPosition]
                                        inPlaceNumeric = resultsListNumeric[endPosition]
                                        inPlaceQualifier = resultsListQualifier[endPosition]
                                        if len(overloadedConcept) == len(resultsListConcept) - endPosition:
                                            resultsListConcept[endPosition] = []
                                            for con in overloadedConcept:
                                                resultsListConcept[endPosition].append(con)
                                                if not resultsListNumeric[endPosition]:
                                                    resultsListNumeric[endPosition] = inPlaceNumeric
                                                if not resultsListQualifier[endPosition]:
                                                    resultsListQualifier[endPosition] = inPlaceQualifier
                                                endPosition = endPosition + 1
                                # Then clean up our mess!
                                if relPositionQual == '':
                                    toAddQualOnly.remove(marker)
                                if relPositionQual == 'Before':
                                    toAddQualBefore.remove(marker)
                                if relPositionQual == 'After':
                                    toAddQualAfter.remove(marker)

                    if linkingList[i]:
                        # This is for the application of multiple biomarkers
                        if any(x in ['or'] for x in linkingList[i]):
                            prepreviousLinker = previousLinker
                            previousLinker = linkerOnDeck
                            linkerOnDeck = 'or'

                        # This is situational - but shows us when not to apply a concept where it doesn't belong.
                        if any(x in ['and'] for x in linkingList[i]):
                            prepreviousLinker = previousLinker
                            previousLinker = linkerOnDeck
                            linkerOnDeck = 'and'

                        if ',' in linkingList[i]:
                            prepreviousLinker = previousLinker
                            previousLinker = linkerOnDeck
                            linkerOnDeck = ','
                        if ')' in linkingList[i]:
                            prepreviousLinker = previousLinker
                            previousLinker = linkerOnDeck
                            linkerOnDeck = ')'
                        if '(' in linkingList[i]:
                            prepreviousLinker = previousLinker
                            previousLinker = linkerOnDeck
                            linkerOnDeck = '('

                        # Finally, if we meet a stopping word (AND IT'S NOT THE END?), drop all the decks.
                        # I'm keeping this just numeric for now, since I've seen this just be like (1+)
                        if any(x in ')' for x in ' '.join(linkingList[i])):
                            if numberOnDeck and not numberUsed:
                                if len(resultsListNumeric) > 0:
                                    pos = len(resultsListNumeric) - 1
                                    while pos >= 0 and resultsListNumeric[pos] == []:
                                        if isinstance(numberOnDeck, list):
                                            resultsListNumeric[pos] = resultsListNumeric[pos] + numberOnDeck
                                        else:
                                            resultsListNumeric[pos].append(numberOnDeck)
                                        pos = pos - 1
                                        numberUsed = False
                                        numberOnDeck = ''
                            if qualifierOnDeck and not qualifierUsed:
                                if len(resultsListQualifier) != 0:
                                    if qualifierOnDeck not in resultsListQualifier[-1]:
                                        resultsListQualifier[-1].append(' '.join(qualifierOnDeck))
                                        qualifierOnDeck = ''
                                        qualifierUsed = False

                        if any(x in ['but', '.', 'with'] for x in linkingList[i]) and i < len(biomarkerList) - 1:
                            if 'but' in linkingList[i]:
                                prepreviousLinker = previousLinker
                                previousLinker = linkerOnDeck
                                linkerOnDeck = 'but'
                            elif '.' in linkingList[i]:
                                prepreviousLinker = previousLinker
                                previousLinker = linkerOnDeck
                                linkerOnDeck = '.'
                            elif 'with' in linkingList[i]:
                                prepreviousLinker = previousLinker
                                previousLinker = linkerOnDeck
                                linkerOnDeck = 'with'
                            elif ':' in linkingList[i]:
                                prepreviousLinker = previousLinker
                                previousLinker = linkerOnDeck
                                linkerOnDeck = ':'

                            # If there's a 'before' token, we might still want it!
                            if not toAddQualBefore and not toAddBioBefore and not toAddNumBefore and not toAddConBefore and not toAddTimeBefore:
                                qualifierOnDeck = []
                                qualifierUsed = False
                                conceptOnDeck = []
                                conceptUsed = False
                                numberOnDeck = []
                                numberUsed = False
                                timeOnDeck = []
                                timeUsed = False
                            # numberOnDeck = []
                            # conceptOnDeck = []
                            # qualifierOnDeck = []
                            # numberUsed = False
                            # biomarkerUsed = False
                            # conceptUsed = False
                            # qualifierUsed = False
                    # ASSUMPTION NOTE: I'm ASSUMING that we'll never encounter a situation where we have TWO on-deck biomarkers
                    # in one phrase. If that's not true, I'll have to make this section better.
                    # Here we detect on-deck biomarkers. If we have two, I THINK we'll call that a unit?
                    for marker in toAddBioBefore:
                        # This is where we detect those on-deck biomarkers!
                        if ('t(' in marker or 'del(' in marker or 'dup(' in marker or 'inv(' in marker or marker.replace('q', '').replace('.', '').isnumeric()
                            or marker.replace('p', '').replace('.', '').isnumeric()
                            or marker.replace('cen', '').isnumeric()) and len(marker) > 3 and not biomarkerOnDeck:
                            biomarkerOnDeck = [marker]
                            toAddBioBefore.remove(marker)
                            # I've noticed SOMETIMES they leave out 'fusion'. A little argot. This MIGHT mess up? But I bet 'fusion' is toward the end of a phrase.
                            # Also maybe make this more reliable? Just 'fusion' anywhere in the utterance seems too broad.
                            if 'fusion' in utterance['UttText'].lower() and len(toAddBioBefore) > 1:
                                if 'fusion' not in toAddConBefore:
                                    toAddConBefore.append('fusion')
                            elif 'fusion' in utterance['UttText'].lower() and len(toAddBioBefore) == 1:
                                if conceptOnDeck and conceptUsed:
                                    conceptOnDeck = ['fusion']
                                    conceptUsed = False
                                elif conceptOnDeck and not conceptUsed and 'fusion' not in conceptOnDeck and 'rearrangement' not in conceptOnDeck:
                                    conceptOnDeck.append('fusion')
                        elif len(marker.split()) == 2 and not biomarkerOnDeck:
                            if marker.split()[1] == 'locus':
                                biomarkerOnDeck = [marker]
                                toAddBioBefore.remove(marker)
                    for marker in toAddBioAfter:
                        # This is where we detect those on-deck biomarkers!
                        # I'm leaving out the condition FOR NOW where we have TWO biomarkers On Deck. Add it later if needed
                        if ('t(' in marker or 'del(' in marker or 'inv(' in marker or 'dup(' in marker or marker.replace('q', '').replace('.', '').isnumeric() \
                            or marker.replace('p', '').replace('.', '').isnumeric()
                            or marker.replace('cen', '').isnumeric()) and len(marker) > 3 and not biomarkerOnDeck:
                            biomarkerOnDeck = [marker]
                            toAddBioAfter.remove(marker)
                            # I've noticed SOMETIMES they leave out 'fusion'. A little argot. This MIGHT mess up? But I bet 'fusion' is toward the end of a phrase.
                            # Also maybe make this more reliable? Just 'fusion' anywhere in the utterance seems too broad.
                            if 'fusion' in utterance['UttText'].lower() and len(toAddBioAfter) > 1:
                                if 'fusion' not in toAddConAfter:
                                    toAddConAfter.append('fusion')
                            elif 'fusion' in utterance['UttText'].lower() and len(toAddBioAfter) == 1:
                                if conceptOnDeck and conceptUsed:
                                    conceptOnDeck = ['fusion']
                                    conceptUsed = False
                                elif conceptOnDeck and not conceptUsed and 'fusion' not in conceptOnDeck and 'rearrangement' not in conceptOnDeck:
                                    conceptOnDeck.append('fusion')
                        elif len(marker.split()) == 2 and not biomarkerOnDeck:
                            if marker.split()[1] == 'locus':
                                biomarkerOnDeck = [marker]
                                toAddBioAfter.remove(marker)

                    for marker in toAddBioOnly:
                        # This is where we detect those on-deck biomarkers!
                        if ('t(' in marker or 'del(' in marker or 'dup(' in marker or 'inv(' in marker or marker.replace('q', '').replace('.', '').isnumeric()
                            or marker.replace('p', '').replace('.', '').isnumeric() or marker.replace('cen', '').isnumeric()) and len(marker) > 3 and not biomarkerOnDeck:
                            biomarkerOnDeck = [marker]
                            if resultsListBiomarker:
                                dontadd = False
                                # If this is a new phrase, don't add it to the previous!
                                if len(resultsListBiomarker) > 0:
                                    thisBit = len(resultsListBiomarker) - 1
                                    if '$$$NewPhrase' in ''.join(resultsListNumeric[thisBit]) or '$$$NewPhrase' in ''.join(resultsListConcept[thisBit]) \
                                            or '$$$NewPhrase' in ''.join(resultsListQualifier[thisBit]) or '$$$NewPhrase' in ''.join(resultsListTime[thisBit]):
                                        dontadd = True
                                # Otherwise, do append it to the previous one!
                                if len(resultsListBiomarker[-1]) == 1 and not dontadd:
                                    resultsListBiomarker[-1].append(biomarkerOnDeck[0])
                                    biomarkerOnDeck = []
                            # I've noticed SOMETIMES they leave out 'fusion'. A little argot. This MIGHT mess up? But I bet 'fusion' is toward the end of a phrase.
                            # Also maybe make this more reliable? Just 'fusion' anywhere in the utterance seems too broad.
                            if len(toAddBioOnly) > 1:
                                if 'fusion' in utterance['UttText'].lower() and 'fusion' not in toAddConOnly:
                                    toAddConOnly.append('fusion')
                            elif len(toAddBioOnly) == 1:
                                if conceptOnDeck and conceptUsed and 'fusion' in utterance['UttText'].lower():
                                    conceptOnDeck = ['fusion']
                                    conceptUsed = False
                                elif conceptOnDeck and not conceptUsed and 'fusion' in utterance['UttText'].lower() and 'fusion' not in conceptOnDeck and 'rearrangement' not in conceptOnDeck:
                                    conceptOnDeck.append('fusion')
                            toAddBioOnly.remove(marker)
                        elif len(marker.split()) == 2 and not biomarkerOnDeck:
                            if marker.split()[1] == 'locus':
                                biomarkerOnDeck = [marker]
                                toAddBioOnly.remove(marker)

                    # #####################################################
                    # #####################################################
                    # #####################################################
                    # Now here's the logic on what to add!
                    # The FRIST thing we do is to see if this is a linker.
                    # If we've had a list and only ','s and now there's a '('...
                    # We'll want to separate out what's coming from the biomarkers that are in right now
                    # BETTER DOCUMENTATION YO. Find this when it fires again.
                    if linkerOnDeck == '(' and previousLinker in [',', 'and'] and prepreviousLinker in [',', 'and'] and not biomarkerOnDeck and len(resultsListBiomarker) > 0 and \
                            (toAddNumOnly or toAddQualOnly) and ['estrogen receptor'] not in biomarkerList:
                        # Again, I really only want this to apply to long lists. We'll fix later if there are more cases
                        if len(resultsListBiomarker[-1]) > 1:
                            biomarkerOnDeck = [resultsListBiomarker[-1][0]]
                            biomarkerUsed = False
                            resultsListBiomarker[-1] = resultsListBiomarker[-1][1:]
                        else:
                            biomarkerOnDeck = resultsListBiomarker[-1]
                            resultsListBiomarker[-1] = biomarkerOnDeck
                            biomarkerUsed = False
                        # We want to add everything we have on-deck to the previous biomarkers!
                        if qualifierOnDeck:
                            qualEnd = len(resultsListQualifier) - 1
                            while qualEnd >= 0:
                                levelResults = ''.join(resultsListQualifier[qualEnd]) + ''.join(resultsListNumeric[qualEnd]) + ''.join(resultsListConcept[qualEnd]) + ''.join(resultsListTime[qualEnd])
                                if '$$$New' not in levelResults:
                                    resultsListQualifier[qualEnd] = qualifierOnDeck
                                qualEnd = qualEnd - 1
                            qualifierOnDeck = ''
                            qualifierUsed = False
                        if conceptOnDeck:
                            concEnd = len(resultsListBiomarker) - 1
                            while concEnd >= 0:
                                levelResults = ''.join(resultsListConcept[concEnd]) + ''.join(resultsListNumeric[concEnd]) + ''.join(resultsListNumeric[concEnd]) + ''.join(resultsListTime[concEnd])
                                if '$$$New' not in levelResults:
                                    resultsListConcept[concEnd] = conceptOnDeck
                                concEnd = concEnd - 1
                            conceptOnDeck = []
                            conceptUsed = False
                        if numberOnDeck:
                            numbEnd = len(resultsListConcept) - 1
                            while numbEnd >= 0:
                                levelResults = ''.join(resultsListConcept[numbEnd]) + ''.join(resultsListNumeric[numbEnd]) + ''.join(resultsListNumeric[numbEnd]) + ''.join(resultsListTime[numbEnd])
                                if '$$$New' not in levelResults:
                                    resultsListNumeric[numbEnd] = numberOnDeck
                                numbEnd = numbEnd - 1
                            numberOnDeck = ''
                            numericUsed = False
                        if timeOnDeck:
                            timEnd = len(resultsListConcept) - 1
                            while timEnd >= 0:
                                resultsListTime[timEnd] = timeOnDeck
                            timEnd = timEnd - 1
                            timeOnDeck = ''
                            timeUsed = False

                    # After we've pulled in the requisite values about that biomarker...
                    # We'll want to add them!
                    if linkerOnDeck == ')' and previousLinker in [',', '('] and biomarkerOnDeck and ')' not in ' '.join(biomarkerOnDeck):
                        resultsListBiomarker.append(biomarkerOnDeck)
                        biomarkerOnDeck = []
                        if numberOnDeck:
                            resultsListNumeric.append(numberOnDeck)
                            numberOnDeck = []
                        else:
                            resultsListNumeric.append([])
                        if qualifierOnDeck:
                            resultsListQualifier.append(qualifierOnDeck)
                            qualifierOnDeck = []
                        else:
                            resultsListQualifier.append([])
                        resultsListTime.append([])
                        resultsListConcept.append([])
                        resultsListQualifier[-1].append('$$$NewPhrase$$$')
                        resultsListNumeric[-1].append('$$$NewPhrase$$$')
                        resultsListTime[-1].append('$$$NewPhrase$$$')

                    # If it's NOT that kind of a thing, we might NOT want to include concepts in parentheses. Maybe?
                    if linkerOnDeck == '(' and previousLinker in [',', 'and'] and not biomarkerOnDeck and len(resultsListBiomarker) > 0 and \
                            (toAddConOnly):
                        resultsListConcept[-1].append('$$$NewPhrase$$$')

                    # We're moving down the lists 1 by 1. There are two major KINDS of list positions.
                    # In the one, we've found a biomarker. In the other, we haven't.
                    if toAddBioBefore or toAddBioAfter or toAddBioOnly:
                        # I'm making having a biomarker but no linking word (only) the same as having a biomarker before the linking word
                        if (toAddBioBefore and not toAddBioAfter) or toAddBioOnly:
                            # Just set them equal here - they'll get erased after this pass anyway.
                            if toAddBioBefore:
                                if biomarkerOnDeck:
                                    toAddBioBefore.append(biomarkerOnDeck[0])
                                    biomarkerOnDeck = []
                                toAddBioBefore.append("$$$NewPhrase$$$")

                                resultsListBiomarker.append(toAddBioBefore)
                            if toAddBioOnly:
                                if linkerOnDeck in ['but', '.', ':']:
                                    if resultsListBiomarker:
                                        if '$$$NewPhrase$$$' not in resultsListBiomarker[-1]:
                                            resultsListBiomarker[-1].append('$$$NewPhrase$$$')
                                            linkerOnDeck = ''
                                if biomarkerOnDeck:
                                    if len(resultsListBiomarker) == 0:
                                        if biomarkerOnDeck[0] not in toAddBioOnly:
                                            toAddBioOnly.append(biomarkerOnDeck[0])
                                    else:
                                        if biomarkerOnDeck[0] not in toAddBioOnly and biomarkerOnDeck[0] not in resultsListBiomarker[-1]:
                                            toAddBioOnly.append(biomarkerOnDeck[0])
                                    biomarkerOnDeck = []

                                # If we've got a reverse biomarker on deck/biomarker group, this will get them.
                                if i < len(biomarkerList) - 1:
                                    if not toAddNumBefore and not toAddNumAfter and not toAddNumOnly and not toAddConBefore and not toAddConAfter and not toAddConOnly and not \
                                            toAddQualOnly and not toAddQualAfter and not toAddQualBefore and len(biomarkerList[i + 1]) == 1:
                                        if biomarkerOnDeck != '':
                                            biomarkerOnDeck.append(', '.join(toAddBioOnly))
                                        else:
                                            biomarkerOnDeck = [', '.join(toAddBioOnly)]
                                        resultsListBiomarker.append([])
                                    else:
                                        resultsListBiomarker.append(toAddBioOnly)
                                else:
                                    resultsListBiomarker.append(toAddBioOnly)

                        # If we've got a biomarker on deck, but only a new biomarker AFTER a break token, we'll append the on-deck one to the last
                        # biomarker. THIS MIGHT CRASH if one of the on-decks is the only biomarker we get in the first break. Update if so.
                        elif toAddBioAfter and not toAddBioBefore:
                            if biomarkerOnDeck and resultsListBiomarker:
                                resultsListBiomarker[-1].append(biomarkerOnDeck[0])
                                biomarkerOnDeck = []
                                # This is a token for removal later!
                                resultsListBiomarker[-1] = resultsListBiomarker[-1] + ["$$$NewPhrase$$$"]
                            elif resultsListBiomarker:
                                resultsListBiomarker[-1] = resultsListBiomarker[-1] + ["$$$NewPhrase$$$"]
                            resultsListBiomarker.append(toAddBioAfter)
                            toAddBioAfter = []

                        # If we've got both, the biomarker on deck gets added to the first one, then they're appended one after the other.
                        elif toAddBioBefore and toAddBioAfter:
                            if biomarkerOnDeck:
                                toAddBioBefore.append(biomarkerOnDeck[0])
                                biomarkerOnDeck = []
                            # This is a token for removal later!
                            toAddBioBefore.append("$$$NewPhrase$$$")
                            # new plan - if it's both, add the next round at the END
                            resultsListBiomarker.append(toAddBioBefore)
                            # resultsListBiomarker.append(toAddBioAfter)

                        # ###########
                        # ## CONCEPT
                        # ##########
                        # ## Now let's tackle concepts! 'only's are the easiest.
                        if toAddConOnly:
                            if linkerOnDeck in ['but', '.', ':'] and resultsListConcept:
                                if '$$$NewPhrase$$$' not in resultsListConcept[-1]:
                                    resultsListConcept[-1].append('$$$NewPhrase$$$')
                                    linkerOnDeck = ''
                            # No concept on deck. Easy, just add this concept
                            if not conceptOnDeck:
                                resultsListConcept.append(toAddConOnly)
                                # There are a few concepts that are definitely single-use ONLY!
                                if ''.join(toAddConOnly) not in ['microsatellite instability']:
                                    conceptOnDeck = toAddConOnly
                                    conceptUsed = True
                                    # Apply backwards if needed
                                    position = len(resultsListConcept) - 1
                                    if position >= 1:
                                        position = position - 1
                                        absPos = i - 1
                                        while not resultsListConcept[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                     and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                     and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                     and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                            resultsListConcept[position] = toAddConOnly
                                            position = position - 1
                                            absPos = absPos - 1
                                        if not resultsListConcept[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListConcept[position]):
                                            resultsListConcept[position] = toAddConOnly
                                    elif resultsListConcept == [[]]:
                                        resultsListConcept = [toAddConOnly]
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif conceptOnDeck and not conceptUsed:
                                if 'or' in linkingList[i - 1]:
                                    conceptOnDeck = conceptOnDeck + toAddConOnly
                                    resultsListConcept.append(conceptOnDeck)
                                    conceptUsed = True
                                else:
                                    resultsListConcept.append(conceptOnDeck)
                                    conceptOnDeck = toAddConOnly
                                    conceptUsed = False
                            # Deck used - then use the current concept. Drop the deck
                            elif conceptOnDeck and conceptUsed:
                                if ''.join(toAddConOnly) in conceptOnDeck:
                                    toAddConOnly = conceptOnDeck
                                # Apply backwards if needed
                                position = len(resultsListConcept) - 1
                                if position > 1:
                                    position = position
                                    absPos = i
                                    while not resultsListConcept[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListConcept[position] = conceptOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListConcept[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListConcept[position]):
                                        resultsListConcept[position] = conceptOnDeck
                                elif resultsListConcept == [[]]:
                                    resultsListConcept = [conceptOnDeck]
                                resultsListConcept.append(toAddConOnly)
                                conceptOnDeck = toAddConOnly
                                conceptUsed = True

                        # Just BEFORE - this is the most common breakpoint setup, and functionally identical to the
                        # onlys, except that I also drop the on decks.
                        # ALSO BEING USED for both now. We'll handle the before here and the after later!
                        elif (toAddConBefore and not toAddConAfter) or (toAddConBefore and toAddConAfter):
                            if '$$$NewPhrase$$$' not in toAddConBefore:
                                toAddConBefore.append("$$$NewPhrase$$$")
                            # No concept on deck. Easy, just add this concept
                            if not conceptOnDeck:
                                if ' '.join(toAddConBefore) in ['microsatellite instability $$$NewPhrase$$$']:
                                    resultsListConcept.append([])
                                if ' '.join(toAddConBefore) not in ['microsatellite instability $$$NewPhrase$$$']:
                                    resultsListConcept.append(toAddConBefore)
                                    conceptOnDeck = []
                                    conceptUsed = False
                                    # Apply backwards if needed
                                    position = len(resultsListConcept) - 1
                                    if position > 1:
                                        position = position - 1
                                        absPos = i - 1
                                        while not resultsListConcept[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                      and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                      and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                      and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                            resultsListConcept[position] = toAddConBefore
                                            conceptUsed = True
                                            position = position - 1
                                            absPos = absPos - 1
                                        if not resultsListConcept[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListConcept[position]):
                                            resultsListConcept[position] = toAddConBefore
                                            conceptUsed = True
                                    elif resultsListConcept == [[]]:
                                        resultsListConcept = [toAddConBefore]
                                        conceptUsed = True
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif conceptOnDeck and not conceptUsed:
                                conceptOnDeck = conceptOnDeck + toAddConBefore
                                resultsListConcept.append(conceptOnDeck)
                                conceptOnDeck = []
                                conceptUsed = False

                            # Deck used - then use the current concept. Drop the deck
                            elif conceptOnDeck and conceptUsed:
                                resultsListConcept.append(toAddConBefore)
                                conceptOnDeck = []
                                conceptUsed = False
                            if toAddConAfter:
                                if "$$$NewPhrase$$$" not in resultsListConcept[-1]:
                                    resultsListConcept[-1] = resultsListConcept[-1] + ["$$$NewPhrase$$$"]
                                conceptOnDeck = toAddConAfter
                                conceptUsed = False
                                toAddConAfter = []

                        # Just AFTER - this means there's a biomarker + concept at the START of a sentence. This is actually SUPER easy. Just add it
                        elif toAddConAfter and not toAddConBefore:
                            # This is a token for removal later!
                            if resultsListConcept:
                                resultsListConcept[-1] = resultsListConcept[-1] + ["$$$NewPhrase$$$"]
                                resultsListConcept.append(toAddConAfter)
                            else:
                                resultsListConcept.append(['$$$NewPhrase$$$'])
                                resultsListConcept[-1] = resultsListConcept[-1] + toAddConAfter
                            # Apply backwards if needed
                            if conceptOnDeck and conceptUsed:
                                position = len(resultsListConcept) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListConcept[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListConcept[position] = conceptOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListConcept[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListConcept[position]):
                                        resultsListConcept[position] = conceptOnDeck
                                elif resultsListConcept == [[]]:
                                    resultsListConcept = [conceptOnDeck]
                            conceptOnDeck = toAddConAfter
                            conceptUsed = True

                        # If there's no concept at all, then if there's a concept on deck, add it. If not, just add a blank and move on.
                        elif not toAddConBefore and not toAddConAfter:
                            if conceptOnDeck and not conceptUsed:
                                resultsListConcept.append(conceptOnDeck)
                                conceptUsed = True
                                if toAddBioBefore:
                                    conceptOnDeck = []
                                    conceptUsed = False
                            elif conceptOnDeck and 'and' in linkingList[i - 1] or ',' in linkingList[i - 1] or linkingList[i - 1] == []:
                                resultsListConcept.append(conceptOnDeck)
                                conceptUsed = True
                                if toAddBioBefore:
                                    conceptOnDeck = []
                                    conceptUsed = False
                            else:
                                resultsListConcept.append([])

                        # ###########
                        # ## NUMERIC
                        # ##########
                        # ## Now let's tackle numerics! 'only's are the easiest.
                        if toAddNumOnly:
                            if linkerOnDeck in ['but', '.', ':']:
                                if resultsListNumeric:
                                    if '$$$NewPhrase$$$' not in resultsListNumeric[-1]:
                                        resultsListNumeric[-1].append('$$$NewPhrase$$$')
                                        linkerOnDeck = ''
                            # No concept on deck. Easy, just add this concept
                            if not numberOnDeck:
                                resultsListNumeric.append(toAddNumOnly.copy())
                                numberOnDeck = toAddNumOnly
                                numberUsed = True
                                # Apply backwards if needed
                                position = len(resultsListNumeric) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while len(resultsListNumeric) < len(resultsListBiomarker):
                                        resultsListNumeric.append([])
                                    while not resultsListNumeric[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListNumeric[position] = toAddNumOnly
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                        resultsListNumeric[position] = toAddNumOnly
                                elif resultsListNumeric == [[]]:
                                    resultsListNumeric = [toAddNumOnly]
                                    numberUsed = True
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif numberOnDeck and not numberUsed:
                                for nod in numberOnDeck:
                                    for numb in toAddNumOnly:
                                        if numericSimilarty(nod, numb) and nod in numberOnDeck:
                                            numberOnDeck.remove(nod)
                                            if len(resultsListNumeric) > 0:
                                                resultsListNumeric[-1].append(nod)
                                            else:
                                                resultsListNumeric = [[nod]]
                                resultsListNumeric.append(numberOnDeck.copy())
                                numberOnDeck = numberOnDeck + toAddNumOnly
                                numberUsed = False
                            # Deck used - then use the current concept. Drop the deck
                            elif numberOnDeck and numberUsed:
                                for nod in numberOnDeck:
                                    for bef in toAddNumOnly:
                                        if numericSimilarty(nod, bef) and nod in numberOnDeck:
                                            numberOnDeck.remove(nod)
                                numberOnDeck = toAddNumOnly + numberOnDeck
                                resultsListNumeric.append(numberOnDeck.copy())
                                numberUsed = True

                        # Just BEFORE - this is the most common breakpoint setup, and functionally identical to the
                        # onlys, except that I also drop the on decks.
                        # WE'RE ALSO USING THIS FOR BOTH NOW. We'll do the 'before' here and handle the 'after' later
                        elif (toAddNumBefore and not toAddNumAfter) or (toAddNumBefore and toAddNumAfter):
                            toAddNumBefore.append("$$$NewPhrase$$$")
                            # No concept on deck. Easy, just add this concept
                            if not numberOnDeck:
                                resultsListNumeric.append(toAddNumBefore.copy())
                                numberOnDeck = []
                                numberUsed = False
                                # Apply backwards if needed
                                position = len(resultsListNumeric) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListNumeric[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListNumeric[position] = toAddNumBefore
                                        numberUsed = True
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                        resultsListNumeric[position] = toAddNumBefore
                                        numberUsed = True
                                elif resultsListNumeric == [[]]:
                                    resultsListNumeric = [toAddNumBefore]
                                    numberUsed = True
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif numberOnDeck and not numberUsed:
                                for nod in numberOnDeck:
                                    for numb in toAddNumBefore:
                                        if numericSimilarty(nod, numb):
                                            numberOnDeck.remove(nod)
                                numberOnDeck = numberOnDeck + toAddNumBefore
                                resultsListNumeric.append(numberOnDeck.copy())
                                numberOnDeck = []
                                numberUsed = False

                            # Deck used - then use the current concept. Drop the deck
                            elif numberOnDeck and numberUsed:
                                for nod in numberOnDeck:
                                    for numb in toAddNumBefore:
                                        if numericSimilarty(nod, numb):
                                            try:
                                                numberOnDeck.remove(nod)
                                            except:
                                                pass
                                toAddNumBefore = toAddNumBefore + numberOnDeck
                                resultsListNumeric.append(toAddNumBefore.copy())
                                numberOnDeck = []
                                numberUsed = True

                        # Just AFTER - this means there's a biomarker + number at the START of a sentence. This is actually SUPER easy. Just add it
                        elif toAddNumAfter and not toAddNumBefore:
                            # This is a token for removal later!
                            resultsListNumeric.append(toAddNumBefore)
                            # Apply backwards if needed
                            if numberOnDeck and numberUsed:
                                position = len(resultsListNumeric) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListNumeric[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListNumeric[position] = numberOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                        resultsListNumeric[position] = numberOnDeck
                                elif resultsListNumeric == [[]]:
                                    resultsListNumeric = [numberOnDeck]
                            numberOnDeck = toAddNumBefore
                            numberUsed = True
                            if toAddNumAfter:
                                toAddNumAfter.append("$$$NewPhrase$$$")
                                numberOnDeck = toAddNumAfter
                                numberUsed = False
                                toAddNumAfter = []

                        # If there's no number at all, then if there's a number on deck, add it. If not, just add a blank and move on.
                        elif not toAddNumBefore and not toAddNumAfter:
                            if numberOnDeck and numberUsed:
                                # Apply backwards if needed
                                if numberOnDeck and numberUsed and len(resultsListBiomarker) > len(resultsListNumeric):
                                    resultsListNumeric.append([])
                                if numberOnDeck and numberUsed and len(resultsListQualifier) >= len(resultsListBiomarker):
                                    position = len(resultsListBiomarker) - 1
                                    if '$$$NewPhrase$$$' in resultsListBiomarker[position] or '$$$NewPhrase$$$' in resultsListQualifier[position]:
                                        resultsListNumeric.append([])
                                        numberOnDeck = []
                                        numberUsed = False
                                    if position > 1:
                                        position = position - 1
                                        absPos = i - 1
                                        while not resultsListNumeric[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                     and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                     and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                     and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                            resultsListNumeric[position] = numberOnDeck
                                            position = position - 1
                                            absPos = absPos - 1
                                        if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                            resultsListNumeric[position] = numberOnDeck
                                    elif resultsListNumeric == [[]]:
                                        resultsListNumeric = [numberOnDeck]
                                if '$$$NewPhrase$$$' in resultsListNumeric[-1] or '$$$NewPhrase$$$' in resultsListBiomarker[-1] or '$$$NewPhrase$$$' in resultsListConcept[-1]:
                                    numberOnDeck = []
                                    numberUsed = False
                            elif numberOnDeck and not numberUsed:
                                if len(resultsListNumeric) < len(resultsListBiomarker):
                                    if resultsListBiomarker[-1] != []:
                                        resultsListNumeric.append(numberOnDeck)
                                        numberUsed = True
                                        if toAddBioBefore:
                                            numberOnDeck = []
                                            numberUsed = False
                                    else:
                                        resultsListNumeric.append([])
                                else:
                                    resultsListNumeric.append([])
                            else:
                                if len(resultsListBiomarker) > len(resultsListNumeric):
                                    if numberOnDeck:
                                        resultsListNumeric.append(numberOnDeck)
                                        numberUsed = True
                                    else:
                                        resultsListNumeric.append([])

                        # ###########
                        # ## TIME
                        # ##########
                        # ## Now let's tackle time! 'only's are the easiest.
                        if toAddTimeOnly:
                            if linkerOnDeck in ['but', '.', ':']:
                                if resultsListTime:
                                    if '$$$NewPhrase$$$' not in resultsListTime[-1]:
                                        resultsListTime[-1].append('$$$NewPhrase$$$')
                                        linkerOnDeck = ''
                            # No time on deck. Easy, just add this concept
                            if not timeOnDeck:
                                resultsListTime.append(toAddTimeOnly)
                                timeOnDeck = toAddTimeOnly
                                timeUsed = True
                                # Apply backwards if needed
                                position = len(resultsListTime) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while len(resultsListTime) < len(resultsListBiomarker):
                                        resultsListTime.append([])
                                    while not resultsListTime[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListTime[position] = toAddTimeOnly
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                        resultsListTime[position] = toAddTimeOnly
                                elif resultsListTime == [[]]:
                                    resultsListTime = [toAddTimeOnly]
                                    timeUsed = True
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif timeOnDeck and not timeUsed:
                                resultsListTime.append(timeOnDeck.copy())
                                for tim in timeOnDeck:
                                    for time in toAddTimeOnly:
                                        if numericSimilarty(tim, time) and tim in timeOnDeck:
                                            timeOnDeck.remove(tim)
                                timeOnDeck = timeOnDeck + toAddTimeOnly
                                timeUsed = False
                            # Deck used - then use the current concept. Drop the deck
                            elif timeOnDeck and timeUsed:
                                for tim in timeOnDeck:
                                    for bef in toAddTimeOnly:
                                        if numericSimilarty(tim, bef) and tim in timeOnDeck:
                                            timeOnDeck.remove(tim)
                                timeOnDeck = toAddTimeOnly + timeOnDeck
                                resultsListTime.append(timeOnDeck.copy())
                                timeUsed = True

                        # Just BEFORE - this is the most common breakpoint setup, and functionally identical to the
                        # onlys, except that I also drop the on decks.
                        # WE'RE ALSO USING THIS FOR BOTH NOW. We'll do the 'before' here and handle the 'after' later
                        elif (toAddTimeBefore and not toAddTimeAfter) or (toAddTimeBefore and toAddTimeAfter):
                            toAddTimeBefore.append("$$$NewPhrase$$$")
                            # No concept on deck. Easy, just add this concept
                            if not timeOnDeck:
                                resultsListTime.append(toAddTimeBefore.copy())
                                timeOnDeck = []
                                timeUsed = False
                                # Apply backwards if needed
                                position = len(resultsListTime) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListTime[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListTime[position] = toAddTimeBefore
                                        timeUsed = True
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                        resultsListTime[position] = toAddTimeBefore
                                        timeUsed = True
                                elif resultsListTime == [[]]:
                                    resultsListTime = [toAddTimeBefore]
                                    timeUsed = True
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif timeOnDeck and not timeUsed:
                                for tim in timeOnDeck:
                                    for time in toAddTimeBefore:
                                        if numericSimilarty(tim, time):
                                            timeOnDeck.remove(tim)
                                timeOnDeck = timeOnDeck + toAddTimeBefore
                                resultsListTime.append(timeOnDeck.copy())
                                timeOnDeck = []
                                timeUsed = False

                            # Deck used - then use the current concept. Drop the deck
                            elif timeOnDeck and timeUsed:
                                for tim in timeOnDeck:
                                    for time in toAddTimeBefore:
                                        if numericSimilarty(tim, time):
                                            try:
                                                timeOnDeck.remove(tim)
                                            except:
                                                pass
                                toAddTimeBefore = toAddTimeBefore + timeOnDeck
                                resultsListTime.append(toAddTimeBefore.copy())
                                timeOnDeck = []
                                timeUsed = True

                            # Just AFTER - this means there's a biomarker + number at the START of a sentence. This is actually SUPER easy. Just add it
                        elif toAddTimeAfter and not toAddTimeBefore:
                            # This is a token for removal later!
                            resultsListTime.append(toAddTimeBefore)
                            # Apply backwards if needed
                            if timeOnDeck and timeUsed:
                                position = len(resultsListTime) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListTime[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListTime[position] = timeOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                        resultsListTime[position] = timeOnDeck
                                elif resultsListTime == [[]]:
                                    resultsListTime = [timeOnDeck]
                            timeOnDeck = toAddTimeBefore
                            timeUsed = True
                            if toAddTimeAfter:
                                toAddTimeAfter.append("$$$NewPhrase$$$")
                                timeOnDeck = toAddTimeAfter
                                timeUsed = False
                                toAddTimeAfter = []

                        # If there's no time at all, then if there's a time on deck, add it. If not, just add a blank and move on.
                        elif not toAddTimeBefore and not toAddTimeAfter:
                            if timeOnDeck and timeUsed:
                                # Apply backwards if needed
                                if timeOnDeck and timeUsed:
                                    position = len(resultsListTime) - 1
                                    if position > 1:
                                        position = position - 1
                                        absPos = i - 1
                                        while not resultsListTime[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                  and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                            resultsListTime[position] = timeOnDeck
                                            position = position - 1
                                            absPos = absPos - 1
                                        if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                            resultsListTime[position] = timeOnDeck
                                    elif resultsListTime == [[]]:
                                        resultsListTime = [timeOnDeck]
                                    else:
                                        resultsListTime.append(timeOnDeck)
                            elif timeOnDeck and not timeUsed:
                                resultsListTime.append(timeOnDeck)
                                timeUsed = True
                                if toAddBioBefore:
                                    timeOnDeck = []
                                    timeUsed = False
                            else:
                                resultsListTime.append([])

                        # ###########
                        # ## QUALIFIER
                        # ##########
                        # ## Now let's tackle qualifiers! 'only's are the easiest.
                        if toAddQualOnly:
                            if linkerOnDeck in ['but', '.', ':']:
                                if resultsListQualifier:
                                    if '$$$NewPhrase$$$' not in resultsListQualifier[-1]:
                                        resultsListQualifier[-1].append('$$$NewPhrase$$$')
                                        linkerOnDeck = ''
                            # No qualifier on deck. Easy, just add this concept
                            if not qualifierOnDeck:
                                resultsListQualifier.append(toAddQualOnly)
                                if 'microsatellite' not in ''.join(toAddQualOnly):
                                    qualifierOnDeck = toAddQualOnly
                                    qualifierUsed = True
                                # Apply backwards if needed
                                position = len(resultsListQualifier) - 1
                                if position >= 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListQualifier[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = toAddQualOnly
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = toAddQualOnly
                                elif resultsListQualifier[position] == []:
                                    resultsListQualifier[position] = toAddQualOnly
                                    qualifierUsed = True
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif qualifierOnDeck and not qualifierUsed:
                                resultsListQualifier.append(qualifierOnDeck)
                                if i > 0:
                                    if 'and' in linkingList[i - 1]:
                                        resultsListQualifier[-1] = resultsListQualifier[-1] + toAddQualOnly
                                qualifierOnDeck = toAddQualOnly
                                qualifierUsed = False
                            # Deck used - then use the current concept. Drop the deck
                            elif qualifierOnDeck and qualifierUsed:
                                # Apply backwards if needed
                                position = len(resultsListQualifier) - 1
                                if position > 1:
                                    position = position
                                    absPos = i
                                    while not resultsListQualifier[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                elif resultsListQualifier == [[]]:
                                    resultsListQualifier = [qualifierOnDeck]
                                    qualifierUsed = True
                                resultsListQualifier.append(toAddQualOnly)
                                qualifierOnDeck = toAddQualOnly
                                qualifierUsed = True


                        # Just BEFORE - this is the most common breakpoint setup, and functionally identical to the
                        # onlys, except that I also drop the on decks.
                        # THIS IS ALSO BEING USED FOR THE 'BOTH' NOW. We'll handle before now, and after later
                        elif (toAddQualBefore and not toAddQualAfter) or (toAddQualBefore and toAddQualAfter):
                            toAddQualBefore.append("$$$NewPhrase$$$")
                            # No concept on deck. Easy, just add this concept
                            if not qualifierOnDeck:
                                resultsListQualifier.append(toAddQualBefore)
                                qualifierOnDeck = []
                                qualifierUsed = False
                                # Apply backwards if needed
                                position = len(resultsListQualifier) - 1
                                if position > 1 and linkerOnDeck != 'and':
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListQualifier[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = toAddQualBefore
                                        qualifierUsed = True
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = toAddQualBefore
                                        qualifierUsed = True
                                elif resultsListQualifier == [[]]:
                                    resultsListQualifier = [toAddQualBefore]
                                    qualifierUsed = True
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif qualifierOnDeck and not qualifierUsed:
                                resultsListQualifier.append(qualifierOnDeck)
                                qualifierOnDeck = []
                                qualifierUsed = False
                                if toAddBioBefore:
                                    qualifierOnDeck = []
                                    qualifierUsed = False

                            # Deck used - then use the current concept. Drop the deck
                            elif qualifierOnDeck and qualifierUsed:
                                # If the qualifier is before and the biomarker is after, don't add here!
                                if len(resultsListBiomarker) > 1:
                                    if '$$$NewPhrase$$$' not in resultsListBiomarker[-2]:
                                        resultsListQualifier.append(toAddQualBefore)
                                    else:
                                        resultsListQualifier[-1] = resultsListQualifier[-1] + toAddQualBefore
                                        if not toAddQualAfter:
                                            resultsListQualifier.append([])
                                        qualifierUsed = True
                                # Apply backwards if needed
                                position = len(resultsListQualifier)
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListQualifier[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                elif resultsListQualifier == [[]]:
                                    resultsListQualifier = [qualifierOnDeck]
                                    qualifierUsed = True
                                elif resultsListQualifier == []:
                                    resultsListQualifier = [qualifierOnDeck]
                                    qualifierUsed = True
                                qualifierOnDeck = []
                                qualifierUsed = True
                                if toAddBioBefore:
                                    qualifierOnDeck = []
                                    qualifierUsed = False
                            if toAddQualAfter:
                                toAddQualAfter.append("$$$NewPhrase$$$")
                                qualifierOnDeck = toAddQualAfter
                                qualifierUsed = False
                                toAddQualAfter = []

                        # Just AFTER - this means there's a biomarker + number at the START of a sentence. This is actually SUPER easy. Just add it
                        elif toAddQualAfter and not toAddQualBefore:
                            # This is a token for removal later!
                            toAddQualAfter.append("$$$NewPhrase$$$")
                            resultsListQualifier.append(toAddQualAfter)
                            # Apply backwards if needed
                            if qualifierOnDeck and qualifierUsed:
                                position = len(resultsListQualifier) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListQualifier[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                elif resultsListQualifier == [[]]:
                                    resultsListQualifier = [qualifierOnDeck]
                            qualifierOnDeck = toAddQualAfter
                            qualifierUsed = True

                        # NEITHER ONE, then if there's a concept on deck, add it. If not, just add a blank and move on.
                        elif not toAddQualBefore and not toAddQualAfter:
                            # Apply backwards if needed
                            if qualifierOnDeck and qualifierUsed:
                                position = len(resultsListQualifier) - 1
                                if position > 1:
                                    position = position
                                    absPos = i
                                    while not resultsListQualifier[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                        qualifierUsed = True
                                elif resultsListQualifier == [[]]:
                                    resultsListQualifier = [qualifierOnDeck]
                            if qualifierOnDeck and not qualifierUsed:
                                # If we put that biomarker on deck, we don't want to add THIS on-deck one!
                                if resultsListBiomarker[-1] != []:
                                    resultsListQualifier.append(qualifierOnDeck)
                                    qualifierUsed = True
                                elif ''.join(list(itertools.chain.from_iterable(resultsListBiomarker))) == '':
                                    resultsListQualifier.append(['$$$NewPhrase$$$'])
                                else:
                                    resultsListQualifier.append([])
                                # I'm not 100% sure why this was here. Take out for now, but put back in if needed!
                                # if toAddBioBefore:
                                #    qualifierOnDeck = []
                                #    qualifierUsed = False
                            elif len(resultsListQualifier) < len(resultsListBiomarker):
                                resultsListQualifier.append([])

                        # NOW, we deal with the 'after' part of "both"s. If there's a toAddBioAfter at this point, it's because there was a before AND an after.
                        # if there was just a after, the idea is, we will have cleared out after.

                        if toAddBioAfter:
                            resultsListBiomarker.append(toAddBioAfter)
                            toAddBioAfter = []
                            if toAddNumAfter:
                                resultsListNumeric.append(toAddNumAfter)
                                numberOnDeck = toAddNumAfter
                                numberUsed = True
                                toAddNumAfter = []
                            else:
                                resultsListNumeric.append([])
                            if toAddConAfter:
                                resultsListConcept.append(toAddConAfter)
                                conceptOnDeck = toAddConAfter
                                conceptUsed = True
                                toAddConAfter = []
                            else:
                                resultsListConcept.append([])
                            if toAddQualAfter:
                                resultsListQualifier.append(toAddQualAfter)
                                qualifierOnDeck = toAddQualAfter
                                qualifierUsed = True
                                toAddQualAfter = []
                            else:
                                resultsListQualifier.append([])
                            if toAddTimeAfter:
                                resultsListTime.append(toAddTimeAfter)
                                timeOnDeck = toAddTimeAfter
                                timeUsed = True
                                toAddTimeAfter = []
                            else:
                                resultsListTime.append([])

                    # The NEXT major kind of phrase is one that DOESN'T have any biomarker info in it! I'm PRETTY SURE the only thing we'll ever
                    # want to record on it's own (in fact, I'm almost 100% sure - I don't think a numeric or qualifier on their own are sensible
                    # results - is a concept!
                    elif not toAddBioBefore and not toAddBioAfter and not toAddBioOnly:
                        # #######
                        # Biomarker
                        # #######
                        # Slim pickins' here. IF there's a biomarker on deck AND we've got a phrase ender, append the biomarker.
                        if biomarkerOnDeck:
                            if '.' in ' '.join(linkingList[i]) or 'but' in ' '.join(linkingList[i]):
                                biomarkerOnDeck.append('$$$NewPhrase$$$')
                                resultsListBiomarker.append(biomarkerOnDeck)
                                resultsListConcept.append(conceptOnDeck)
                                resultsListNumeric.append(numberOnDeck)
                                resultsListQualifier.append(qualifierOnDeck)
                                resultsListTime.append(timeOnDeck)
                                biomarkerOnDeck = ''
                                conceptOnDeck = []
                                conceptUsed = False
                                numberOnDeck = []
                                numberUsed = False
                                qualifierOnDeck = []
                                qualifierUsed = False
                                timeOnDeck = []
                                timeUsed = False

                        # #######
                        # Concept
                        # #######
                        # Might as well start with concepts first! Remember, 'only' is the MIDDLE of a unit.
                        if toAddConOnly:
                            if linkerOnDeck in ['but', '.', ':'] and resultsListConcept:
                                if '$$$NewPhrase$$$' not in resultsListConcept[-1]:
                                    resultsListConcept[-1].append('$$$NewPhrase$$$')
                                    linkerOnDeck = ''
                            # If we've got something on deck and it hasn't been used, we'll save it up.
                            if conceptOnDeck and not conceptUsed and ', '.join(toAddConOnly) not in conceptOnDeck:
                                conceptOnDeck = conceptOnDeck + toAddConOnly
                            # If we've used the thing on deck, throw it away and make this our new on-deck
                            elif conceptOnDeck and conceptUsed:
                                # If it's like 'x and y' or 'x or y', then have them both!
                                if (linkerOnDeck in ['or', 'and'] and ''.join(toAddConOnly) not in conceptOnDeck) and conceptOnDeck[0] not in ['copy number']:
                                    if resultsListConcept[-1] == conceptOnDeck:
                                        resultsListConcept[-1].append(toAddConOnly[0])
                                else:
                                    conceptOnDeck = toAddConOnly
                                    conceptUsed = False
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck
                            elif not conceptOnDeck:
                                conceptOnDeck = toAddConOnly
                                if len(resultsListConcept) > 0:
                                    if not resultsListConcept[-1] and '$$$NewPhrase$$$' not in resultsListBiomarker[-1] and '$$$NewPhrase$$$' not in resultsListNumeric[-1] and \
                                            '$$$NewPhrase$$$' not in resultsListQualifier[-1]:
                                        resultsListConcept[-1] = conceptOnDeck
                                        position = len(resultsListConcept) - 2
                                        while resultsListConcept[position] == [] and '$$$NewPhrase' not in resultsListBiomarker[position] and '$$$NewPhrase' not \
                                                in resultsListNumeric[position] and '$$$NewPhrase' not in resultsListQualifier[position] and position >= 0:
                                            resultsListConcept[position] = conceptOnDeck
                                            position = position - 1
                                        conceptUsed = True
                                    else:
                                        conceptUsed = False
                                else:
                                    conceptUsed = False

                        # It's a different case at the END of a sentence. If the previous biomarker slot has an empty space, we'll fill it with this concept.
                        # If it DOESN'T, we'll add a NEW concept on and blank out the biomarker
                        if toAddConBefore and not toAddConAfter:
                            if '$$$NewPhrase$$$' not in toAddConBefore:
                                toAddConBefore.append("$$$NewPhrase$$$")
                            # If we've got something on deck and it hasn't been used, we'll append it to the concept list along with the current concept, and make a blank biomarker space.
                            if conceptOnDeck and not conceptUsed:
                                conceptOnDeck = conceptOnDeck + toAddConBefore
                                resultsListConcept.append(conceptOnDeck)
                                conceptOnDeck = []
                                conceptUsed = False
                            # If we've used the thing on deck, throw it away and append the new
                            elif conceptOnDeck and conceptUsed:
                                resultsListConcept[-1] = resultsListConcept[-1] + toAddConBefore
                                conceptOnDeck = []
                                conceptUsed = False
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck
                            elif not conceptOnDeck:
                                conceptOnDeck = toAddConBefore
                                conceptUsed = False

                        # 'After' is right at the start of a sentence!
                        elif toAddConAfter and not toAddConBefore:
                            # Apply backwards if needed
                            if conceptOnDeck and conceptUsed:
                                position = len(resultsListConcept) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListConcept[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListConcept[position] = conceptOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListConcept[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListConcept[position]):
                                        resultsListConcept[position] = conceptOnDeck
                                elif resultsListConcept == [[]]:
                                    resultsListConcept = [conceptOnDeck]
                            conceptOnDeck = toAddConAfter
                            conceptUsed = False

                        elif toAddConBefore and toAddConAfter:
                            if '$$$NewPhrase$$$' not in toAddConBefore:
                                toAddConBefore.append("$$$NewPhrase$$$")
                            # No concept on deck. Easy, just add this concept
                            if not conceptOnDeck:
                                if ' '.join(toAddConBefore) in ['microsatellite instability $$$NewPhrase$$$']:
                                    resultsListConcept.append([])
                                if ' '.join(toAddConBefore) not in ['microsatellite instability $$$NewPhrase$$$']:
                                    resultsListConcept.append(toAddConBefore)
                                    conceptOnDeck = []
                                    conceptUsed = False
                                    # Apply backwards if needed
                                    position = len(resultsListConcept) - 1
                                    if position > 1:
                                        position = position - 1
                                        absPos = i - 1
                                        while not resultsListConcept[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                      and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                      and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                      and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                            resultsListConcept[position] = toAddConBefore
                                            conceptUsed = True
                                            position = position - 1
                                            absPos = absPos - 1
                                        if not resultsListConcept[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListConcept[position]):
                                            resultsListConcept[position] = toAddConBefore
                                            conceptUsed = True
                                    elif resultsListConcept == [[]]:
                                        resultsListConcept = [toAddConBefore]
                                        conceptUsed = True
                            # Deck not used - then use the on-deck concept and make this one on-deck.
                            elif conceptOnDeck and not conceptUsed:
                                conceptOnDeck = conceptOnDeck + toAddConBefore
                                resultsListConcept.append(conceptOnDeck)
                                conceptOnDeck = []
                                conceptUsed = False

                            # Deck used - then use the current concept. Drop the deck
                            elif conceptOnDeck and conceptUsed:
                                resultsListConcept.append(toAddConBefore)
                                conceptOnDeck = []
                                conceptUsed = False
                            if toAddConAfter:
                                if "$$$NewPhrase$$$" not in resultsListConcept[-1]:
                                    resultsListConcept[-1] = resultsListConcept[-1] + ["$$$NewPhrase$$$"]
                                conceptOnDeck = toAddConAfter
                                conceptUsed = False
                                toAddConAfter = []

                        # #######
                        # Numeric
                        # #######
                        # Next we'll do numbers! Remember, 'only' is the MIDDLE
                        if toAddNumOnly:
                            # if we've got a parenthetical, take it
                            if linkerOnDeck in ['(', ','] and biomarkerOnDeck:
                                numberOnDeck = toAddNumOnly
                                numberUsed = False

                            if linkerOnDeck in ['but', '.', ':'] and resultsListNumeric:
                                if '$$$NewPhrase$$$' not in resultsListNumeric[-1]:
                                    resultsListNumeric[-1].append('$$$NewPhrase$$$')
                                    linkerOnDeck = ''

                            if numberOnDeck and not numberUsed and not biomarkerOnDeck:
                                if len(resultsListNumeric) > 0:
                                    if not resultsListNumeric[-1]:
                                        resultsListNumeric[-1] = numberOnDeck + toAddNumOnly
                                    else:
                                        for nod in numberOnDeck:
                                            for numb in toAddNumOnly:
                                                # If we haven't used this yet, we do want to add it
                                                if numericSimilarty(nod, numb):
                                                    resultsListNumeric[-1].append(nod)
                                                    numberOnDeck.remove(nod)
                                                    break
                                        numberOnDeck = numberOnDeck + toAddNumOnly
                                        resultsListNumeric.append(numberOnDeck.copy())
                                        numberUsed = True

                                else:
                                    #for nod in numberOnDeck:
                                    #    for numb in toAddNumOnly:
                                    #        if numericSimilarty(nod, numb) and nod in numberOnDeck:
                                    #            numberOnDeck.remove(nod)
                                    numberOnDeck = numberOnDeck + toAddNumOnly
                                    #resultsListNumeric.append(numberOnDeck.copy())
                                    numberUsed = False
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif numberOnDeck and numberUsed:
                                # Apply backwards if needed
                                position = len(resultsListNumeric) - 1
                                if position >= 1:
                                    position = position
                                    absPos = i
                                    while not resultsListNumeric[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                 and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                 and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                 and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListNumeric[position] = numberOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                        resultsListNumeric[position] = numberOnDeck

                                numberOnDeck = toAddNumOnly
                                numberUsed = False
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck. I THINK this is the only case where we need to apply backwards
                            elif not numberOnDeck:
                                # if we've got a parenthetical, take it
                                if linkerOnDeck in ['(', ','] and biomarkerOnDeck:
                                    numberOnDeck = toAddNumOnly
                                    numberUsed = False
                                elif i == 0 or (i > 0 and ':' not in linkingList[i - 1]):
                                    if resultsListNumeric == [[]]:
                                        resultsListNumeric = [toAddNumOnly]
                                        numberUsed = True
                                    else:
                                        numberOnDeck = toAddNumOnly
                                        numberUsed = False
                                # Add it here if needed
                                elif i > 0:
                                    if ':' in linkingList[i - 1]:
                                        if len(resultsListNumeric) > 1:
                                            resultsListNumeric[-1] = resultsListNumeric[-1] + toAddNumOnly
                                        elif len(resultsListBiomarker) == len(resultsListNumeric):
                                            if len(resultsListNumeric) > 0:
                                                if resultsListNumeric[-1] == []:
                                                    resultsListNumeric[-1] = resultsListNumeric[-1] + toAddNumOnly
                                                else:
                                                    toAdd = True
                                                    for num in resultsListNumeric[-1]:
                                                        if numericSimilarty(toAddNumOnly[0], num):
                                                            toAdd = False
                                                    if toAdd:
                                                        resultsListNumeric[-1] = resultsListNumeric[-1] + toAddNumOnly
                                            else:
                                                resultsListNumeric = [toAddNumOnly]
                                        else:
                                            resultsListNumeric.append(toAddNumOnly)
                                        numberUsed = True
                                else:
                                    numberOnDeck = toAddNumOnly
                                    numberUsed = False

                                # Apply backwards if needed
                                position = len(resultsListNumeric)
                                if position > 1 and not (numberOnDeck != '' and not numberUsed):
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListNumeric[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListNumeric[position] = toAddNumOnly
                                        numberUsed = True
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                        resultsListNumeric[position] = toAddNumOnly
                                        numberUsed = True
                                # Here, if there's a biomarker, and it's from a previous phrase, then put this number on deck. If the biomarker is in the SAME
                                # phrase, add the biomarker back.
                                elif resultsListNumeric == [[]]:
                                    position = i
                                    inBetween = False
                                    if resultsListBiomarker:
                                        lastBio = resultsListBiomarker[-1]
                                        while position > -1 and lastBio not in biomarkerList[position]:
                                            if 'but' in linkingList[position] or '.' in linkingList[position]:
                                                inBetween = True
                                            position = position - 1
                                    if inBetween:
                                        numberOnDeck = toAddNumOnly
                                        numberUsed = False
                                    else:
                                        resultsListNumeric = [toAddNumOnly]
                                        numberUsed = True

                        # 'Before' is right at the end of a sentence!
                        elif toAddNumBefore and not toAddNumAfter:
                            toAddNumBefore.append("$$$NewPhrase$$$")
                            # If we've got something on deck and it hasn't been used, we'll just assume that it, AND whatever we have now, belong to the last thing.
                            # If there's no last thing, throw it away
                            if numberOnDeck and not numberUsed:
                                if len(resultsListNumeric) > 0:
                                    resultsListNumeric[-1] = numberOnDeck.append(toAddNumBefore)
                                numberOnDeck = []
                                numberUsed = False
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif numberOnDeck and numberUsed:
                                for nod in numberOnDeck:
                                    for bef in toAddNumOnly:
                                        if numericSimilarty(nod, bef):
                                            numberOnDeck.remove(nod)
                                numberOnDeck = toAddNumOnly + numberOnDeck
                                resultsListNumeric.append(numberOnDeck.copy())
                                numberUsed = True
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck
                            elif not numberOnDeck:
                                # Apply backwards if needed
                                position = len(resultsListNumeric)
                                if position > 1:
                                    position = position - 1
                                    resultsListNumeric[position] = resultsListNumeric[position] + toAddNumBefore
                                    absPos = i - 1
                                    position = position - 1
                                    while not resultsListNumeric[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                 and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                 and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                 and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListNumeric[position] = toAddNumBefore
                                        numberUsed = True
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                        resultsListNumeric[position] = toAddNumBefore
                                        numberUsed = True
                                elif resultsListNumeric == [[]]:
                                    resultsListNumeric = [toAddNumBefore]
                                    numberUsed = True
                                elif resultsListNumeric == []:
                                    # If this is related to the previous utterance, let's add it in there, otherwise we'll add it here
                                    if finalNumericResults:
                                        if finalNumericResults[-1] == []:
                                            finalNumericResults[-1] = toAddNumBefore
                                        else:
                                            resultsListNumeric = [toAddNumBefore]
                                            numberUsed = True
                                    else:
                                        resultsListNumeric = [toAddNumBefore]
                                        numberUsed = True
                                else:
                                    for num in toAddNumBefore:
                                        resultsListNumeric[-1].append(num)
                                    numberUsed = True
                                numberOnDeck = []
                                numberUsed = False

                        # 'After' is right at the start of a sentence!
                        elif toAddNumAfter and not toAddNumBefore:
                            # Apply backwards if needed
                            if numberOnDeck and numberUsed:
                                position = len(resultsListNumeric) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListNumeric[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                  and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListNumeric[position] = numberOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                        resultsListNumeric[position] = numberOnDeck
                                elif resultsListNumeric == [[]]:
                                    resultsListNumeric = [numberOnDeck]
                            numberOnDeck = toAddNumAfter
                            numberUsed = False

                        # If we've got both, we'll want to basically combine - add the number before THEN put after on deck.
                        elif toAddNumBefore and toAddNumAfter:
                            toAddNumBefore.append("$$$NewPhrase$$$")
                            # If we've got something on deck and it hasn't been used, we'll just assume that it, AND whatever we have now, belong to the last thing.
                            # If there's no last thing, throw it away
                            if numberOnDeck and not numberUsed:
                                if len(resultsListNumeric) > 0:
                                    resultsListNumeric[-1] = numberOnDeck.append(toAddNumBefore)
                                numberOnDeck = []
                                numberUsed = False
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif numberOnDeck and numberUsed:
                                for nod in numberOnDeck:
                                    for bef in toAddNumOnly:
                                        if numericSimilarty(nod, bef):
                                            numberOnDeck.remove(nod)
                                numberOnDeck = toAddNumOnly + numberOnDeck
                                resultsListNumeric.append(numberOnDeck.copy())
                            else:
                                if len(resultsListNumeric) > 0:
                                    resultsListNumeric[-1] = toAddNumBefore
                                numberOnDeck = []
                                numberUsed = False
                            numberOnDeck = toAddNumAfter
                            numberUsed = False

                        # No numbers at all, what now?
                        else:
                            if numberOnDeck and len(resultsListNumeric) < len(resultsListBiomarker):
                                resultsListNumeric.append(numberOnDeck)
                            elif len(resultsListNumeric) < len(resultsListBiomarker):
                                resultsListNumeric.append([])
                            # elif numberUsed:
                            #    numberOnDeck = []
                            #    numberUsed = False

                        # #######
                        # Time
                        # #######
                        # Next we'll do time! Remember, 'only' is the MIDDLE
                        if toAddTimeOnly:
                            if linkerOnDeck in ['but', '.', ':'] and resultsListTime:
                                if '$$$NewPhrase$$$' not in resultsListTime[-1]:
                                    resultsListTime[-1].append('$$$NewPhrase$$$')
                                    linkerOnDeck = ''
                            if timeOnDeck and not timeUsed:
                                if len(resultsListTime) > 0:
                                    if not resultsListTime[-1]:
                                        resultsListTime[-1] = timeOnDeck + toAddTimeOnly
                                    else:
                                        for tim in timeOnDeck:
                                            for time in toAddTimeOnly:
                                                if numericSimilarty(tim, time):
                                                    timeOnDeck.remove(tim)
                                        timeOnDeck = timeOnDeck + toAddTimeOnly
                                        resultsListTime.append(timeOnDeck.copy())
                                        timeUsed = False

                                else:
                                    for tim in timeOnDeck:
                                        for time in toAddTimeOnly:
                                            if numericSimilarty(tim, time) and tim in timeOnDeck:
                                                timeOnDeck.remove(tim)
                                    timeOnDeck = timeOnDeck + toAddTimeOnly
                                    resultsListTime.append(timeOnDeck.copy())
                                    timeUsed = False
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif timeOnDeck and timeUsed:
                                # Apply backwards if needed
                                position = len(resultsListTime) - 1
                                if position >= 1:
                                    position = position
                                    absPos = i
                                    while not resultsListTime[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListTime[position] = timeOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                        resultsListTime[position] = timeOnDeck

                                timeOnDeck = toAddTimeOnly
                                timeUsed = False
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck. I THINK this is the only case where we need to apply backwards
                            elif not timeOnDeck:
                                if i == 0 or (i > 0 and ':' not in linkingList[i - 1]):
                                    if resultsListTime == [[]]:
                                        resultsListTime = [toAddTimeOnly]
                                        timeUsed = True
                                    else:
                                        timeOnDeck = toAddTimeOnly
                                        timeUsed = False
                                # Add it here if needed
                                elif i > 0:
                                    if ':' in linkingList[i - 1]:
                                        if len(resultsListTime) > 1:
                                            resultsListTime[-1] = resultsListTime[-1] + toAddTimeOnly
                                        elif len(resultsListBiomarker) == len(resultsListTime):
                                            if len(resultsListTime) > 0:
                                                if resultsListTime[-1] == []:
                                                    resultsListTime[-1] = resultsListTime[-1] + toAddTimeOnly
                                                else:
                                                    toAdd = True
                                                    for tim in resultsListTime[-1]:
                                                        if numericSimilarty(toAddTimeOnly[0], tim):
                                                            toAdd = False
                                                    if toAdd:
                                                        resultsListTime[-1] = resultsListTime[-1] + toAddTimeOnly
                                            else:
                                                resultsListTime = [toAddTimeOnly]
                                        else:
                                            resultsListTime.append(toAddTimeOnly)
                                        timeUsed = True
                                else:
                                    timeOnDeck = toAddTimeOnly
                                    timeUsed = False

                                # Apply backwards if needed
                                position = len(resultsListTime)
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListTime[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListTime[position] = toAddTimeOnly
                                        timeUsed = True
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                        resultsListTime[position] = toAddTimeOnly
                                        timeUsed = True
                                # Here, if there's a biomarker, and it's from a previous phrase, then put this number on deck. If the biomarker is in the SAME
                                # phrase, add the biomarker back.
                                elif resultsListTime == [[]]:
                                    position = i
                                    inBetween = False
                                    if resultsListBiomarker:
                                        lastBio = resultsListBiomarker[-1]
                                        while position > -1 and lastBio not in biomarkerList[position]:
                                            if 'but' in linkingList[position] or '.' in linkingList[position]:
                                                inBetween = True
                                            position = position - 1
                                    if inBetween:
                                        timeOnDeck = toAddTimeOnly
                                        timeUsed = False
                                    else:
                                        resultsListTime = [toAddTimeOnly]
                                        timeUsed = True

                        # 'Before' is right at the end of a sentence!
                        elif toAddTimeBefore and not toAddTimeAfter:
                            toAddTimeBefore.append("$$$NewPhrase$$$")
                            # If we've got something on deck and it hasn't been used, we'll just assume that it, AND whatever we have now, belong to the last thing.
                            # If there's no last thing, throw it away
                            if timeOnDeck and not timeUsed:
                                if len(resultsListTime) > 0:
                                    resultsListTime[-1] = timeOnDeck.append(toAddTimeBefore)
                                timeOnDeck = []
                                timeUsed = False
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif timeOnDeck and timeUsed:
                                for tim in timeOnDeck:
                                    for bef in toAddTimeOnly:
                                        if numericSimilarty(tim, bef):
                                            timeOnDeck.remove(tim)
                                timeOnDeck = toAddTimeOnly + timeOnDeck
                                resultsListTime.append(timeOnDeck.copy())
                                timeUsed = True
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck
                            elif not timeOnDeck:
                                # Apply backwards if needed
                                position = len(resultsListTime)
                                if position > 1:
                                    position = position - 1
                                    resultsListTime[position] = resultsListTime[position] + toAddTimeBefore
                                    absPos = i - 1
                                    position = position - 1
                                    while not resultsListTime[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                              and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                              and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                              and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListTime[position] = toAddTimeBefore
                                        timeUsed = True
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                        resultsListTime[position] = toAddTimeBefore
                                        timeUsed = True
                                elif resultsListTime == [[]]:
                                    resultsListTime = [toAddTimeBefore]
                                    timeUsed = True
                                elif resultsListTime == []:
                                    # If this is related to the previous utterance, let's add it in there, otherwise we'll add it here
                                    if finalTimeResults:
                                        if finalTimeResults[-1] == []:
                                            finalTimeResults[-1] = toAddTimeBefore
                                        else:
                                            resultsListTime = [toAddTimeBefore]
                                            timeUsed = True
                                    else:
                                        resultsListTime = [toAddTimeBefore]
                                        timeUsed = True
                                else:
                                    for tim in toAddTimeBefore:
                                        resultsListTime[-1].append(tim)
                                    timeUsed = True
                                timeOnDeck = []
                                timeUsed = False

                        # 'After' is right at the start of a sentence!
                        elif toAddTimeAfter and not toAddTimeBefore:
                            # Apply backwards if needed
                            if timeOnDeck and timeUsed:
                                position = len(resultsListTime) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListTime[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                                               and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListTime[position] = timeOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                        resultsListTime[position] = timeOnDeck
                                elif resultsListTime == [[]]:
                                    resultsListTime = [timeOnDeck]
                            timeOnDeck = toAddTimeAfter
                            timeUsed = False

                        # If we've got both, we'll want to basically combine - add the number before THEN put after on deck.
                        elif toAddTimeBefore and toAddTimeAfter:
                            toAddTimeBefore.append("$$$NewPhrase$$$")
                            # If we've got something on deck and it hasn't been used, we'll just assume that it, AND whatever we have now, belong to the last thing.
                            # If there's no last thing, throw it away
                            if timeOnDeck and not timeUsed:
                                if len(resultsListTime) > 0:
                                    resultsListTime[-1] = timeOnDeck.append(toAddTimeBefore)
                                timeOnDeck = []
                                timeUsed = False
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif timeOnDeck and timeUsed:
                                for tim in timeOnDeck:
                                    for bef in toAddTimeOnly:
                                        if numericSimilarty(tim, bef):
                                            timeOnDeck.remove(tim)
                                timeOnDeck = toAddTimeOnly + timeOnDeck
                                resultsListTime.append(timeOnDeck.copy())
                            else:
                                if len(resultsListTime) > 0:
                                    resultsListTime[-1] = toAddTimeBefore
                                timeOnDeck = []
                                timeUsed = False
                            timeOnDeck = toAddTimeAfter
                            timeUsed = False

                        # #######
                        # Qualifier
                        # #######
                        # Next we'll do qualifiers! Remember, 'only' is the MIDDLE
                        if toAddQualOnly:
                            # if we've got a parenthetical, take it
                            if linkerOnDeck in ['('] and biomarkerOnDeck:
                                qualifierOnDeck = toAddQualOnly
                                qualifierUsed = False

                            if linkerOnDeck in ['but', '.', ':'] and resultsListQualifier and resultsListQualifier != [[]]:
                                if '$$$NewPhrase$$$' not in resultsListQualifier[-1]:
                                    resultsListQualifier[-1].append('$$$NewPhrase$$$')
                                    linkerOnDeck = ''
                            if qualifierOnDeck and not qualifierUsed and not biomarkerOnDeck:
                                if len(resultsListQualifier) > 0:
                                    if not resultsListQualifier[-1]:
                                        resultsListQualifier[-1] = qualifierOnDeck
                                        qualifierOnDeck = toAddQualOnly
                                    else:
                                        if qualifierOnDeck != toAddQualOnly:
                                            qualifierOnDeck = qualifierOnDeck + toAddQualOnly
                                else:
                                    if qualifierOnDeck != toAddQualOnly:
                                        qualifierOnDeck = qualifierOnDeck + toAddQualOnly
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif qualifierOnDeck and qualifierUsed:
                                # Apply backwards if needed
                                position = len(resultsListQualifier)
                                if position >= 1:
                                    position = position - 1
                                    while not resultsListQualifier[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                   and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                        position = position - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck

                                qualifierOnDeck = toAddQualOnly
                                qualifierUsed = False
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck
                            elif qualifierOnDeck == [] or qualifierOnDeck == '':
                                qualifierOnDeck = toAddQualOnly
                                qualifierUsed = False

                        # 'Before' is right at the end of a sentence!
                        elif toAddQualBefore and not toAddQualAfter:
                            toAddQualPast = toAddQualBefore.copy()
                            toAddQualBefore.append("$$$NewPhrase$$$")
                            # If we've got something on deck and it hasn't been used, we'll just assume that it, AND whatever we have now, belong to the last thing.
                            if qualifierOnDeck and not qualifierUsed:
                                if len(resultsListQualifier) > 0:
                                    # qualifierOnDeck.append(qualifierOnDeck + toAddQualBefore)
                                    resultsListQualifier[-1] = qualifierOnDeck
                                qualifierOnDeck = []
                                qualifierUsed = False
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif qualifierOnDeck and qualifierUsed:
                                if len(resultsListQualifier) > 0:
                                    resultsListQualifier[-1] = resultsListQualifier[-1] + toAddQualBefore
                                    qualifierOnDeck = []
                                    qualifierUsed = False
                                else:
                                    resultsListQualifier = [toAddQualBefore]
                                    qualifierOnDeck = []
                                    qualifierUsed = False
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck
                            elif not qualifierOnDeck and resultsListQualifier:
                                resultsListQualifier[-1] = toAddQualBefore
                                # Apply backwards if needed
                                position = len(resultsListNumeric) - 1
                                if position >= 1:
                                    position = position - 1
                                    while not resultsListQualifier[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = toAddQualPast
                                        qualifierUsed = True
                                        position = position - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = toAddQualPast
                                        qualifierUsed = True
                                elif resultsListQualifier == [[]]:
                                    resultsListQualifier = [toAddQualBefore]
                                    qualifierUsed = True
                                qualifierOnDeck = []
                                qualifierUsed = False

                            else:
                                qualifierOnDeck = toAddQualPast
                                qualifierUsed = False

                        # 'After' is right at the start of a sentence!
                        elif toAddQualAfter and not toAddQualBefore:
                            # Apply backwards if needed
                            if qualifierOnDeck and qualifierUsed:
                                position = len(resultsListQualifier) - 1
                                if position > 1:
                                    position = position - 1
                                    absPos = i - 1
                                    while not resultsListQualifier[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                        position = position - 1
                                        absPos = absPos - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = qualifierOnDeck
                                elif resultsListQualifier == [[]]:
                                    resultsListQualifier = [qualifierOnDeck]
                            qualifierOnDeck = toAddQualAfter
                            qualifierUsed = False

                        # Finally, what if we have both?
                        elif toAddQualAfter and toAddQualBefore:
                            toAddQualPast = toAddQualBefore.copy()
                            toAddQualBefore.append("$$$NewPhrase$$$")
                            # If we've got something on deck and it hasn't been used, we'll just assume that it, AND whatever we have now, belong to the last thing.
                            if qualifierOnDeck and not qualifierUsed:
                                if len(resultsListQualifier) > 0:
                                    # qualifierOnDeck.append(qualifierOnDeck + toAddQualBefore)
                                    resultsListQualifier[-1] = qualifierOnDeck
                                qualifierOnDeck = []
                                qualifierUsed = False
                            # If we've used the thing on deck, throw it away and add THIS to the end. We don't need to check if the list is long, since we know it is
                            elif qualifierOnDeck and qualifierUsed:
                                if len(resultsListQualifier) > 0:
                                    resultsListQualifier[-1] = resultsListQualifier[-1] + toAddQualBefore
                                    qualifierOnDeck = []
                                    qualifierUsed = False
                                else:
                                    resultsListQualifier = [toAddQualBefore]
                                    qualifierOnDeck = []
                                    qualifierUsed = False
                            # Finally, if we've got nothing on deck, we'll just make this our new on-deck
                            elif not qualifierOnDeck and resultsListQualifier:
                                resultsListQualifier[-1] = toAddQualBefore
                                # Apply backwards if needed
                                position = len(resultsListNumeric) - 1
                                if position >= 1:
                                    position = position - 1
                                    while not resultsListQualifier[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                                    and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                        resultsListQualifier[position] = toAddQualPast
                                        qualifierUsed = True
                                        position = position - 1
                                    if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                        resultsListQualifier[position] = toAddQualPast
                                        qualifierUsed = True
                                elif resultsListQualifier == [[]]:
                                    resultsListQualifier = [toAddQualBefore]
                                    qualifierUsed = True

                            qualifierOnDeck = toAddQualAfter
                            qualifierUsed = False

                    # Turn this on to see the lists as they grow
                    if watchGrow:
                        if (toAddBioBefore or toAddBioAfter or toAddBioOnly or toAddConBefore or toAddConAfter or toAddConOnly or toAddNumBefore or toAddNumAfter or toAddNumOnly \
                                or toAddQualBefore or toAddQualAfter or toAddQualOnly or endBiomarkerScan):
                            print(resultsListBiomarker)
                            print(resultsListConcept)
                            print(resultsListNumeric)
                            print(resultsListQualifier)
                            input()

                    # As an extra, anything that we determine should ONLY be around for one marker should go here. First candidate: variant allelic frequency. Unlikely to be more than one!
                    if 'allelic frequency' in ''.join(numberOnDeck):
                        numberOnDeck = []

                # #############################
                # If we've reached the very end, we'll want to fill in any blanks
                # #############################
                if resultsListBiomarker == [] and not biomarkerOnDeck:
                    resultsListBiomarker.append([])
                    resultsListConcept.append([])
                    resultsListNumeric.append([])
                    resultsListQualifier.append([])
                    resultsListTime.append([])
                if resultsListBiomarker == [] and biomarkerOnDeck:
                    resultsListBiomarker.append(biomarkerOnDeck)
                    resultsListConcept.append([])
                    resultsListNumeric.append([])
                    resultsListQualifier.append([])
                    resultsListTime.append([])
                if biomarkerOnDeck and resultsListBiomarker:
                    resultsListBiomarker[-1] = resultsListBiomarker[-1] + biomarkerOnDeck
                    biomarkerOnDeck = []
                if resultsListConcept[-1] == []:
                    if conceptOnDeck:
                        resultsListConcept[-1] = conceptOnDeck
                        conceptUsed = True
                        # Apply backwards if needed
                        position = len(resultsListConcept) - 1
                        if position > 1:
                            position = position - 1
                            absPos = i - 1
                            while not resultsListConcept[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                          and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                          and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                          and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                resultsListConcept[position] = conceptOnDeck
                                position = position - 1
                                absPos = absPos - 1
                            if not resultsListConcept[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListConcept[position]):
                                resultsListConcept[position] = conceptOnDeck
                        elif resultsListConcept == [[]]:
                            resultsListConcept = [conceptOnDeck]
                if resultsListNumeric[-1] == []:
                    if numberOnDeck:
                        resultsListNumeric[-1] = numberOnDeck
                        numberUsed = True
                        # Apply backwards if needed
                        position = len(resultsListNumeric) - 1
                        if position > 1:
                            position = position - 1
                            absPos = i - 1
                            while not resultsListNumeric[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                          and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                          and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                                          and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                resultsListNumeric[position] = numberOnDeck
                                position = position - 1
                                absPos = absPos - 1
                            if not resultsListNumeric[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListNumeric[position]):
                                resultsListNumeric[position] = numberOnDeck
                        elif resultsListNumeric == [[]]:
                            resultsListNumeric = [numberOnDeck]
                if resultsListTime[-1] == []:
                    if timeOnDeck:
                        resultsListTime[-1] = timeOnDeck
                        timeUsed = True
                        # Apply backwards if needed
                        position = len(resultsListTime) - 1
                        if position > 1:
                            position = position - 1
                            absPos = i - 1
                            while not resultsListTime[position] and position > 0 and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                                       and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                                       and '$$$NewPhrase$$$' not in resultsListTime[position]
                                                                                                       and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                resultsListTime[position] = timeOnDeck
                                position = position - 1
                                absPos = absPos - 1
                            if not resultsListTime[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListTime[position]):
                                resultsListTime[position] = timeOnDeck
                        elif resultsListTime == [[]]:
                            resultsListTime = [timeOnDeck]
                if resultsListQualifier[-1] == []:
                    if not qualifierOnDeck and toAddQualBefore:
                        resultsListQualifier[-1] = toAddQualBefore
                    if qualifierOnDeck:
                        resultsListQualifier[-1] = qualifierOnDeck
                        qualifierUsed = True
                        # Apply backwards if needed
                        position = len(resultsListQualifier) - 1
                        if position >= 1:
                            position = position - 1
                            while not resultsListQualifier[position] and position > 0 and ('$$$NewPhrase$$$' not in resultsListBiomarker[position]
                                                                                           and '$$$NewPhrase$$$' not in resultsListConcept[position]
                                                                                           and '$$$NewPhrase$$$' not in resultsListNumeric[position]
                                                                                           and '$$$NewPhrase$$$' not in resultsListQualifier[position]):
                                resultsListQualifier[position] = qualifierOnDeck
                                position = position - 1
                            if not resultsListQualifier[position] and (position == 0 or '$$$NewPhrase$$$' in resultsListQualifier[position]):
                                resultsListQualifier[position] = qualifierOnDeck
                        elif resultsListQualifier == [[]]:
                            resultsListQualifier = [qualifierOnDeck]
                # Add any on-decks
                if conceptOnDeck and not conceptUsed:
                    if resultsListConcept:
                        resultsListConcept[-1] = resultsListConcept[-1] + conceptOnDeck
                # Add any on-decks
                if numberOnDeck and not numberUsed:
                    if resultsListNumeric:
                        resultsListNumeric[-1] = resultsListNumeric[-1] + numberOnDeck
                # Add any on-decks
                if timeOnDeck and not timeUsed:
                    if resultsListTime:
                        resultsListTime[-1] = resultsListTime[-1] + timeOnDeck
                # Add any on-decks
                if qualifierOnDeck and not qualifierUsed:
                    if resultsListQualifier:
                        resultsListQualifier[-1] = resultsListQualifier[-1] + qualifierOnDeck

                # Is this bad? Take out if it is, otherwise it ensures lists are justified
                while len(resultsListNumeric) < len(resultsListBiomarker):
                    resultsListNumeric.append([])
                while len(resultsListQualifier) < len(resultsListBiomarker):
                    resultsListQualifier.append([])
                while len(resultsListConcept) < len(resultsListBiomarker):
                    resultsListConcept.append([])
                while len(resultsListTime) < len(resultsListBiomarker):
                    resultsListTime.append([])

                # Good for panels
                for i in range(0, len(resultsListQualifier)):
                    if resultsListQualifier[i] in ['within normal limits', 'expressed']:
                        for j in range(0, len(resultsListQualifier)):
                            if resultsListQualifier[j] == [] and (resultsListBiomarker[j] or resultsListConcept[j] or resultsListNumeric[j]):
                                resultsListQualifier[j] = resultsListQualifier[i]
                # This is assuming that our panels will be listed with
                # if resultsListBiomarker and not any(resultsListQualifier):
                #     for i in range(0, len(resultsListBiomarker)):
                #         if resultsListBiomarker[i]:
                #             resultsListQualifier[i] = ['tested']

                # Remove any qualifiers with no other info
                for i in range(len(resultsListBiomarker) - 1, -1, -1):
                    if resultsListQualifier[i] and not resultsListBiomarker[i] and not resultsListConcept[i] and not resultsListNumeric[i]:
                        resultsListQualifier[i] = []

                # Now remove any spots with no info
                for i in range(len(resultsListBiomarker) - 1, -1, -1):
                    if not resultsListQualifier[i] and not resultsListBiomarker[i] and not resultsListConcept[i] and not resultsListNumeric[i] and not resultsListTime[i]:
                        del resultsListQualifier[i]
                        del resultsListBiomarker[i]
                        del resultsListNumeric[i]
                        del resultsListConcept[i]
                        del resultsListTime[i]

                # No all-blanks
                if resultsListBiomarker != [[]] or resultsListConcept != [[]] or resultsListNumeric != [[]] or resultsListQualifier != [[]] or resultsListTime != [[]]:
                    finalBiomarkerResults = finalBiomarkerResults + resultsListBiomarker
                    finalConceptResults = finalConceptResults + resultsListConcept
                    finalNumericResults = finalNumericResults + resultsListNumeric
                    finalQualifierResults = finalQualifierResults + resultsListQualifier
                    finalTimeResults = finalTimeResults + resultsListTime
                # print(finalBiomarkerResults)
                # print(finalConceptResults)
                # print(finalNumericResults)
                # print(finalQualifierResults)
                # input()
                # print(toAddBio)
                # print(toAddBioAfter)
                # print(toAddCon)
                # print(toAddConAfter)
                # print(toAddNum)
                # print(toAddNumAfter)
                # print(toAddQual)
                # print(toAddQualAfter)
                # print(linkerOnDeck)

            # POST-HOC NORMALIZATION AHOY
            # List-lengthening for special cases

            if not finalBiomarkerResults:
                finalBiomarkerResults = []
            if not finalConceptResults:
                finalConceptResults = []
            if not finalNumericResults:
                finalNumericResults = []
            if not finalQualifierResults:
                finalQualifierResults = []
            if not finalTimeResults:
                finalTimeResults = []

            while len(finalBiomarkerResults) > len(finalQualifierResults):
                finalQualifierResults.append([])
            while len(finalBiomarkerResults) > len(finalConceptResults):
                finalConceptResults.append([])
            while len(finalBiomarkerResults) > len(finalNumericResults):
                finalNumericResults.append([])
            while len(finalBiomarkerResults) > len(finalTimeResults):
                finalTimeResults.append([])

            if debug:
                print('final results')
                print(finalBiomarkerResults)
                print(finalConceptResults)
                print(finalNumericResults)
                print(finalQualifierResults)
                print(finalTimeResults)

            for i in range(0, len(finalBiomarkerResults)):
                for x in finalBiomarkerResults[i]:
                    if '(' + x + ')' in ''.join(finalBiomarkerResults[i]):
                        finalBiomarkerResults[i].remove(x)

            # Maybe gonna take this one out. Any 'none's get changed to blanks
            for i in range(0, len(finalBiomarkerResults)):

                if finalNumericResults[i] is None:
                    finalNumericResults[i] = []

                # Sometimes a numeric might be separated
                if i > 0:
                    if finalNumericResults[i - 1] == [] and finalTimeResults[i] != [] and finalBiomarkerResults[i] == [] and finalConceptResults[i] == [] and finalQualifierResults[
                        i] == [] and finalTimeResults == []:
                        finalNumericResults[i - 1] = finalNumericResults[i]

                # If we pull subsets of nuc ish in as biomarkers, delete 'em
                if 'nuc ish' in ' '.join(finalBiomarkerResults[i]):
                    toDelete = []
                    if len(finalBiomarkerResults[i]) > 1:
                        for x in range(0, len(finalBiomarkerResults[i])):
                            if 'nuc ish' in finalBiomarkerResults[i][x]:
                                for y in range(0, len(finalBiomarkerResults[i])):
                                    if y != x and finalBiomarkerResults[i][y] in finalBiomarkerResults[i][x]:
                                        toDelete.append(finalBiomarkerResults[i][y])
                    for de in toDelete:
                        finalBiomarkerResults[i].remove(de)

                if '$$$NewPhrase$$$' in finalBiomarkerResults[i]:
                    finalBiomarkerResults[i].remove('$$$NewPhrase$$$')
                finalBiomarkerResults[i] = list(dict.fromkeys(finalBiomarkerResults[i]))
                if '$$$NewPhrase$$$' in finalConceptResults[i]:
                    finalConceptResults[i].remove('$$$NewPhrase$$$')
                finalConceptResults[i] = list(dict.fromkeys(finalConceptResults[i]))
                if '$$$NewPhrase$$$' in finalNumericResults[i]:
                    finalNumericResults[i].remove('$$$NewPhrase$$$')
                finalNumericResults[i] = list(dict.fromkeys(finalNumericResults[i]))
                if '$$$NewPhrase$$$' in finalQualifierResults[i]:
                    finalQualifierResults[i].remove('$$$NewPhrase$$$')
                finalQualifierResults[i] = list(dict.fromkeys(finalQualifierResults[i]))
                if '$$$NewPhrase$$$' in finalTimeResults[i]:
                    finalTimeResults[i].remove('$$$NewPhrase$$$')
                finalTimeResults[i] = list(dict.fromkeys(finalTimeResults[i]))

                for y in range(0, len(finalBiomarkerResults[i])):
                    if 'xstarx' in finalBiomarkerResults[i][y]:
                        finalBiomarkerResults[i][y] = finalBiomarkerResults[i][y].replace('xstarx', '*')

                for y in range(0, len(finalQualifierResults[i])):
                    if 'xstarx' in finalQualifierResults[i][y]:
                        finalQualifierResults[i][y] = finalQualifierResults[i][y].replace('xstarx', '*')

                # Allelic frequencies should always be positive - no just TESTING for one!
                if 'allelic frequency' in ''.join(finalNumericResults[i]):
                    finalQualifierResults[i] = []

                # 'sep' always means separation, and probably never the gene 'sep'. CHANGE IF FALSE
                if finalBiomarkerResults[i] == ['sep']:
                    finalBiomarkerResults[i] = ['separation']

                if finalQualifierResults[i] == ['within']:
                    finalQualifierResults[i] = ['within normal limits']

                # nuc ish cell counts are always positive - unless they're not proportions
                if 'nuc ish' in ' '.join(finalBiomarkerResults[i]) and '/' in ' '.join(finalNumericResults[i]):
                    finalQualifierResults[i] = ['positive']
                elif 'nuc ish' in ' '.join(finalBiomarkerResults[i]) and '/' not in ' '.join(finalNumericResults[i]):
                    finalQualifierResults[i] = ['probe used']

                if finalBiomarkerResults[i] == ['test'] and 'unsuccessful' in finalQualifierResults[i]:
                    for qual in range(0, len(finalQualifierResults)):
                        if qual != i:
                            finalQualifierResults[qual] = ['test not performed']
                # I was going to call everything else negative. Maybe not?
                # if finalBiomarkerResults[i] == ['normal results']:
                #    for qual in range(0, len(finalQualifierResults)):
                #        if qual != i:
                #            finalQualifierResults[qual] = ['negative']

                # Nothing without a biomarker or concept exists
                if not finalBiomarkerResults[i] and (not finalConceptResults[i] or finalConceptResults[i] in [['Fusion'], ['fusion'], ['ratio']]):
                    finalConceptResults[i] = []
                    finalNumericResults[i] = []
                    finalQualifierResults[i] = []
                    finalTimeResults[i] = []

                # For now, anything that's 'most common' isn't captured.
                if finalQualifierResults[i] == ['most common']:
                    finalBiomarkerResults[i] = []
                    finalConceptResults[i] = []
                    finalQualifierResults[i] = []
                    finalNumericResults[i] = []
                    finalTimeResults[i] = []

        # If it's all nothing, just delete it
        for i in range(len(finalBiomarkerResults) - 1, -1, -1):
            if not finalBiomarkerResults[i] and not finalQualifierResults[i] and not finalNumericResults[i] and not finalConceptResults[i] and not finalTimeResults[i]:
                del finalBiomarkerResults[i]
                del finalConceptResults[i]
                del finalNumericResults[i]
                del finalQualifierResults[i]
                del finalTimeResults[i]

        # We want to delete any results that are subsets of other results
        dropIds = []
        for i in range(0, len(finalBiomarkerResults)):
            for j in range(i, len(finalBiomarkerResults)):
                if i != j and ' '.join(finalBiomarkerResults[i]) in ' '.join(finalBiomarkerResults[j]) and \
                        ' '.join(finalConceptResults[i]) in ' '.join(finalConceptResults[j]) and ' '.join(finalQualifierResults[i]) in ' '.join(finalQualifierResults[j]) and \
                        ' '.join(finalNumericResults[i]) in ' '.join(finalNumericResults[j]) and ' '.join(finalTimeResults[i]) in ' '.join(finalTimeResults[j]):
                    dropIds.append(i)

        dropIds = list(dict.fromkeys(dropIds))
        dropIds.sort(reverse=True)

        for num in dropIds:
            finalBiomarkerResults.pop(num)
            finalConceptResults.pop(num)
            finalNumericResults.pop(num)
            finalQualifierResults.pop(num)
            finalTimeResults.pop(num)

        # Anything 'blank' gets turned into 'positive' unless it's an exon or something like 2p23
        for i in range(0, len(finalBiomarkerResults)):
            if finalQualifierResults[i] == []:
                if finalBiomarkerResults[i]:
                    if ('exon' in ' '.join(finalBiomarkerResults[i]) or \
                        ' '.join(finalBiomarkerResults[i]).replace('(', ' ').split()[0].replace('p', '').replace('d', '').replace('z', '').replace('.', '').isnumeric()) and 'allelic frequency' not in \
                            ''.join(finalNumericResults[i]):
                        finalQualifierResults[i] = ['tested']
                    elif 'pd-l1' in ' '.join(finalBiomarkerResults[i]) and '<1%' in ' '.join(finalNumericResults[i]):
                        finalQualifierResults[i] = ['negative']
                    else:
                        finalQualifierResults[i] = ['positive']
            elif not any(x not in ['nuclear', 'intact nuclear expression'] for x in finalQualifierResults[i]):
                finalQualifierResults[i].append('positive')

        zippedList = list(zip(finalBiomarkerResults, finalConceptResults, finalNumericResults, finalQualifierResults, finalTimeResults))

        zippedList = sorted(zippedList)
        dedup = [zippedList[i] for i in range(len(zippedList)) if i == 0 or zippedList[i] != zippedList[i - 1]]

        finalList = pd.DataFrame(dedup, columns=['Biomarker', 'Concept', 'Numeric', 'Qualifier', 'Time'])

        finalList = finalList.replace(['xstarx'], '*')

        theResults = ''
        print('')
        print('')
        for index, rowa in finalList.iterrows():
            biom = ', '.join(rowa['Biomarker'])
            con = ', '.join(rowa['Concept'])
            num = ', '.join(rowa['Numeric'])
            qual = ', '.join(rowa['Qualifier'])
            tim = ', '.join(rowa['Time'])

        theResults = finalList

        return theResults
    except Exception as e:
        print("OOPS!")
        print(e)
        print(data['AllDocuments'][0]['Document']['Utterances'])
        input()
        raise ValueError('File could not be run')