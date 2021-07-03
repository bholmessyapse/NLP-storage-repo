import pandas as pd
import numpy
import operator
import re
import pymetamap
from subprocess import call
import subprocess
import os
import json

# Intro loading of metamap and etc.
os.chdir('/Users/bholmes/public_mm')
call(["bin/skrmedpostctl", "start"])
call(["bin/wsdserverctl", "start"])

# This uses metamap to create an output file based on the input file.
os.system("bin/metamap --JSONf 2 --negex --nomap NoMapFile /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
          "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")

call(["bin/skrmedpostctl", "stop"])
call(["bin/wsdserverctl", "stop"])
with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
    data = json.load(json_file)

###
# Ok, time for the the real NLP to begin.
###

# Let's take this one at a time, by utterance. I don't know if this is the right way to do things, but I'm
# going to assume FOR NOW that important results will all be contained within one utterance. Maybe that's
# dumb, but that's how I'm gonna do it.
for utt in range(0, len(data['AllDocuments'][0]['Document']['Utterances'])):
    utterance = data['AllDocuments'][0]['Document']['Utterances'][utt]

    # Every utterance is made up of phrases, and we're gonna scan through them looking for particular tokens.
    # The assumption here is that something we care about is either: a result, a qualifier (maybe, indicated, etc.,
    # or a numeric component ("85% of nuclei, etc.). The linking list contains words that give clues as to how
    # to split up the tokens we'll be generating
    conceptList = [[] for z in range (len(utterance['Phrases']))]
    qualifierList = [[] for z in range (len(utterance['Phrases']))]
    numericList = [[] for z in range (len(utterance['Phrases']))]
    linkingList = [[] for z in range (len(utterance['Phrases']))]
    biomarkerList = [[] for z in range (len(utterance['Phrases']))]

    # The results will be saved in a final results list for concatenation
    resultsList = []

    # We'll keep a list of adverbs that are also qualitative concepts. These tend to be the qualifiers that we're
    # looking for. The part of speech tagger probably isn't going to get used much!
    partOfSpeechList = [[] for z in range (len(utterance['Phrases']))]

    # Now we'll loop through every phrase in the utterance, looking for such tokens.
    for phrasePos in range(0, len(utterance['Phrases'])):
        phrase = utterance['Phrases'][phrasePos]

        # Sentence boundaries are important!
        if '.' in phrase['PhraseText']:
            for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'punc' and '.' in phrase['SyntaxUnits'][syntaxUnit][
                    'InputMatch']:
                    if '.' not in linkingList[phrasePos]:
                        linkingList[phrasePos].append('.')

        for SU in range(0, len(phrase['SyntaxUnits'])-1):
            if phrase['SyntaxUnits'][SU]['SyntaxType'] == 'adv':
                if 'adv' not in partOfSpeechList[phrasePos]:
                    partOfSpeechList[phrasePos].append('adv')

            # This is in here to grab the c. and p. variations, which will NOT be recognized.
            if phrase['SyntaxUnits'][SU]['SyntaxType'] == 'mod' and phrase['SyntaxUnits'][SU]['InputMatch'].replace(' ','') == 'c.':
                toAdd = phrase['SyntaxUnits'][SU]['LexMatch'].replace(' ','')
                if len(phrase['SyntaxUnits'])-1 > SU:
                    toAdd = toAdd + phrase['SyntaxUnits'][SU+1]['InputMatch']
                    biomarkerList[phrasePos].append(toAdd)

        # It's a bit tricky pulling out fusion markings, but let's attempt it here!
        if phrase['PhraseText'].startswith('('):
            if phrasePos > 0:
                if utterance['Phrases'][phrasePos-1]['PhraseText'].endswith('t'):
                    toAdd = 't' + phrase['PhraseText']
                    location = phrasePos+1
                    while utterance['Phrases'][location]['PhraseText'] != ')':
                        toAdd = toAdd + utterance['Phrases'][location]['PhraseText']
                        location = location+1
                    toAdd = toAdd + ')'
                    biomarkerList[phrasePos].append(toAdd)

        # We're of course interested in the semantic types. MetaMap is relatively poor at realizing what's
        # going on with percentages. This section is designed to correct that.
        if '%' in phrase['PhraseText']:
            numPercent = ''
            placePercent = ''
            percentUnit = 0
            for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and '%' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                    numPercent = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].replace(' ','')
                    if len(phrase['SyntaxUnits'])-1 > syntaxUnit+1:
                        if phrase['SyntaxUnits'][syntaxUnit+1]['InputMatch'] == 'of':
                            if phrase['SyntaxUnits'][syntaxUnit+2]['LexCat'] == 'noun':
                                placePercent = phrase['SyntaxUnits'][syntaxUnit+2]['InputMatch']
                        if numPercent and placePercent:
                            percentage = numPercent + ' ' + placePercent
                        if percentage not in numericList[phrasePos]:
                            numericList[phrasePos].append(percentage)

                        # Now here we have to check to see if there are any previous results. If there's a linking
                        # word, we'll go one further back and add it to the numeric column!
                        if phrasePos > 1:
                            if linkingList[phrasePos-1]:
                                if '%' in utterance['Phrases'][phrasePos-2]['PhraseText']:
                                    for phrasePart in utterance['Phrases'][phrasePos-2]['PhraseText'].split():
                                        if '%' in phrasePart:
                                            numericList[phrasePos].insert(0, phrasePart + ' ' + placePercent)

        # This one pieces apart ranges (for copy number etc.) - I noticed lots of reports would
        # reference "3 to 10" copies of some number.
        numRange = ''
        for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
            if len(phrase['SyntaxUnits']) > syntaxUnit + 2:
                if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and \
                    phrase['SyntaxUnits'][syntaxUnit+1]['SyntaxType'] == 'prep' and \
                    phrase['SyntaxUnits'][syntaxUnit + 2]['SyntaxType'] == 'shapes' and \
                    phrase['SyntaxUnits'][syntaxUnit + 3]['LexCat'] == 'noun':
                        numRange = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'] + ' ' + \
                        phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch'] + ' ' + \
                        phrase['SyntaxUnits'][syntaxUnit + 2]['InputMatch'] + ' ' + \
                        phrase['SyntaxUnits'][syntaxUnit + 3]['InputMatch']
                        if numRange not in numericList[phrasePos]:
                            numericList[phrasePos].append(numRange)
                # This bit is tagged on to catch if they say "3 copies" without the range
                elif phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and \
                        'LexCat' in phrase['SyntaxUnits'][syntaxUnit + 1].keys():
                    if phrase['SyntaxUnits'][syntaxUnit + 1]['LexCat'] ==  'noun' and \
                        not numRange and phrase['SyntaxUnits'][syntaxUnit +1]['Tokens'][0] not in ['chromosome', 'wi']:
                        numRange = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'] + ' ' \
                        + phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch']
                        if numRange not in numericList[phrasePos]:
                            numericList[phrasePos].append(numRange)


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


        # There are three parts to a phrase that might give us interesting information: there's the text itself,
        # the synatctic structure, and the concepts. Concepts being easiest, let's start there. We DO have to dive
        # all the way down to "SemTypes" - a list within a list (MappingCandidates) within a list (Mappings).
        for mapPos in range(0, len(phrase['Mappings'])):
            mapping = phrase['Mappings'][mapPos]
            for mcPos in range(0, len(mapping['MappingCandidates'])):
                mapCan = mapping['MappingCandidates'][mcPos]
                for semPos in range(0, len(mapCan['SemTypes'])):
                    semType = mapCan['SemTypes'][semPos]
                    if semType in ['comd', 'cgab', 'celc', 'fndg', 'virs', 'dsyn'] or (semType == 'qnco' \
                                                                        and mapCan['CandidateMatched'].lower() in ['loss', 'gain']):
                        # Sometimes, "[Gene] Gene Rearrangement/Amplification/Deletion" will be a whole concept. Let's split it!
                        if len(mapCan['CandidateMatched'].split()) == 3 and ('Gene Rearrangement' in mapCan['CandidateMatched'] or\
                                'Amplification' in mapCan['CandidateMatched'] or 'Deletion' in mapCan['CandidateMatched']):
                            if mapCan['CandidateMatched'].split()[0] not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(mapCan['CandidateMatched'].split()[0])
                            if ' '.join(mapCan['CandidateMatched'].split()[1:3]) not in conceptList[phrasePos]:
                                conceptList[phrasePos].append(' '.join(mapCan['CandidateMatched'].split()[1:3]))
                        # And sometimes, it'll be [Gene] Gene Rearrangement Negative. Huh.
                        elif len(mapCan['CandidateMatched'].split()) == 4 and ('Gene Rearrangement' in mapCan['CandidateMatched'] or\
                                'Amplification' in mapCan['CandidateMatched'] or 'Deletion' in mapCan['CandidateMatched']):
                            if mapCan['CandidateMatched'].split()[0] not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(mapCan['CandidateMatched'].split()[0])
                            if ' '.join(mapCan['CandidateMatched'].split()[1:3]) not in conceptList[phrasePos]:
                                conceptList[phrasePos].append(' '.join(mapCan['CandidateMatched'].split()[1:3]))
                            qualifierList[phrasePos].append(mapCan['CandidateMatched'].split()[3])
                        # 'celc' can sometimes mean that we have further information about a region
                        elif semType == 'celc' and biomarkerList[phrasePos] and mapCan['CandidateMatched'].lower() not in ['nucleus']:
                            biomarkerList[phrasePos][len(biomarkerList[phrasePos])-1] =\
                                biomarkerList[phrasePos][len(biomarkerList[phrasePos])-1] + ' - ' + mapCan['CandidateMatched']
                        # We've also seen 'comd' indicate a mutation that we know about. If not, add it to concept!
                        elif semType == 'comd':
                            # The Tetrasomies seem like they get messed up sometimes. Let's fix it!
                            if 'somy' in mapCan['CandidateMatched']:
                                toAdd = mapCan['MatchedWords'][0]
                                splitSent = phrase['PhraseText'].split()
                                if toAdd in splitSent:
                                    address = splitSent.index(toAdd)
                                    toAdd = toAdd + ' ' + splitSent[address + 1]
                                else:
                                    toAdd = ''
                                if toAdd not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append(toAdd)
                            else:
                                for biom in biomarkerList[phrasePos]:
                                    if biom in mapCan['CandidateMatched']:
                                        biomarkerList[phrasePos].remove(biom)
                                        biomarkerList[phrasePos].append(mapCan['CandidateMatched'])
                                if mapCan['CandidateMatched'] not in biomarkerList[phrasePos]:
                                        if mapCan['CandidateMatched'] not in conceptList[phrasePos]:
                                            conceptList[phrasePos].append(mapCan['CandidateMatched'])

                        # Now let's try to grab the harder to get gains/losses
                        elif semType == 'qnco':
                            split = phrase['PhraseText'].split()
                            if mapCan['CandidateMatched'].lower() in split:
                                startIndex = split.index(mapCan['CandidateMatched'].lower())
                                if split[startIndex+1] == 'of':
                                    if split[startIndex + 2].endswith('.'):
                                        split[startIndex + 2] = split[startIndex + 2][:-1]
                                    if split[startIndex+2] not in biomarkerList[phrasePos]:
                                        biomarkerList[phrasePos].append(split[startIndex+2])
                                    if split[startIndex] not in conceptList[phrasePos]:
                                        conceptList[phrasePos].append(split[startIndex])

                        # I've seen trisomies be cgab
                        elif semType == 'cgab' and 'somy' in mapCan['CandidateMatched']:
                            if mapCan['CandidateMatched'] not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(mapCan['CandidateMatched'])

                        # These terms typically map to biomarkerType
                        elif semType in ['virs', 'dsyn']:
                            if mapCan['CandidateMatched'] not in biomarkerList[phrasePos] and \
                                    ' '.join(biomarkerList[phrasePos]) not in mapCan['CandidateMatched']:
                                biomarkerList[phrasePos].append(mapCan['CandidateMatched'])


                        #  lbtr and nusq are a last-resort adds. If there's anything else, add it. I THINK.
                        elif semType in ['nusq', 'lbtr'] and conceptList[phrasePos]:
                            continue

                        # If nothing is wrong, sometimes the finding witll be 'normal results
                        elif semType == 'fndg':
                            if 'normal' in mapCan['CandidateMatched'].lower():
                                wholeResults = ''
                                for x in biomarkerList:
                                    wholeResults = wholeResults + ''.join(x)
                                if not wholeResults:
                                    biomarkerList[phrasePos].append(mapCan['CandidateMatched'])

                        # Otherwise, we just want to add it!
                        elif mapCan['CandidateMatched'].lower() not in [x.lower() for x in conceptList[phrasePos]]\
                                and mapCan['CandidateMatched'].lower() not in ["nucleus", "negative", 'abnormal']:
                            conceptList[phrasePos].append(mapCan['CandidateMatched'])

                        # If the result is negated, we'll want to note that. Negations go in the qualifier list.
                        if mapCan['Negated'] == '1' or mapCan['CandidateMatched'].lower() == 'negative':
                            if 'Negative' not in qualifierList[phrasePos]:
                                qualifierList[phrasePos].append('Negative')
                        else:
                            if 'Positive' not in qualifierList[phrasePos]:
                                qualifierList[phrasePos].append('Positive')

                    # the "Nusq" type isn't usually appropriate, but SOMETIMES it's how they indicate
                    # a part of a probe location.
                    if semType == 'nusq' and len(utterance['Phrases'])-1 > phrasePos:
                        if utterance['Phrases'][phrasePos+1]['PhraseText'].startswith('('):
                            if mapCan['CandidateMatched'] not in conceptList[phrasePos]:
                                conceptList[phrasePos].append(mapCan['CandidateMatched'])

                    # Likewise, I've seen 'lbtr' sometimes indicate a gene, but let's only use it if we don't have
                    # other examples.
                    if semType == 'lbtr' and len(mapCan['CandidatePreferred'].split()) == 2:
                        if mapCan['CandidatePreferred'].split()[1] == "Positive":
                            if mapCan['MatchedWords'][0] not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(mapCan['MatchedWords'][0])

                    # This sometimes means a probe point out by itself.
                    if semType == 'nusq' and (utterance['Phrases'][phrasePos]['SyntaxUnits'][0]['InputMatch'].replace('p','').isnumeric()\
                        or utterance['Phrases'][phrasePos]['SyntaxUnits'][0]['InputMatch'].replace('q','').isnumeric()):
                        if utterance['Phrases'][phrasePos]['SyntaxUnits'][0]['InputMatch'] not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append(utterance['Phrases'][phrasePos]['SyntaxUnits'][0]['InputMatch'])

                    # Metamap has this really weird habit of splitting up tokens in parenthases by having the
                    # opening paren along with the concept, and then the closing paren as it's own phrase.
                    # We'll want to pull out this paren and attach it to the last thing.
                    if semType in ['gngm', 'aapp', 'enzy'] and phrase['PhraseText'].startswith('(') and\
                            len(utterance['Phrases']) > phrasePos+1:
                        if utterance['Phrases'][phrasePos+1]['PhraseText'].startswith(')'):
                            toAdd = phrase['PhraseText'] + ')'
                            if conceptList[phrasePos-1]:
                                if toAdd not in ' '.join(conceptList[phrasePos-1]) and toAdd not in ' '.join(biomarkerList[phrasePos-1]):
                                    biomarkerList[phrasePos-1].append(conceptList[phrasePos-1][len(conceptList[phrasePos-1])-1] + toAdd)
                                    conceptList[phrasePos-1].remove(conceptList[phrasePos-1][len(conceptList[phrasePos-1])-1])
                            elif toAdd not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(toAdd)

                    # We'll concatenate some results here if it's a probe.
                    # Assuming there will be only one result per phrase. FIX IF WRONG.
                    elif semType == 'gngm' and mapCan['CandidateMatched'].lower() == 'probe':
                        if biomarkerList[phrasePos] and conceptList[phrasePos]:
                            if 'probe' not in ' '.join(biomarkerList[phrasePos]):
                                newGene = ''.join(conceptList[phrasePos]) + ' ' + ''.join(biomarkerList[phrasePos]) \
                                          + ' ' + mapCan['CandidateMatched'].lower()
                                if newGene not in biomarkerList[phrasePos]:
                                    biomarkerList[phrasePos].append(newGene)

                    # It looks like fusions can sometimes be 'ftcn's
                    elif semType == 'ftcn' and mapCan['CandidateMatched'] not in conceptList[phrasePos]:
                        if mapCan['CandidateMatched'] not in ['Using']:
                            conceptList[phrasePos].append(mapCan['CandidateMatched'])

                    # 'spco' (spatial concept) right after a biomarker can mean we're talking about a locus
                    elif semType == 'spco' and biomarkerList[phrasePos] and 'normal' not in ' '.join(biomarkerList[phrasePos]).lower():
                        biomarkerList[phrasePos][len(biomarkerList[phrasePos])-1] = \
                            biomarkerList[phrasePos][len(biomarkerList[phrasePos]) - 1] + ' ' + mapCan['CandidateMatched']

                    # Now we'll pull out the gene names. Different than concepts!
                    elif semType == 'gngm':
                        if len(mapCan['CandidateMatched'].split()) > 1:
                            if mapCan['CandidateMatched'].split()[1].lower() == 'gene':
                                toAdd = mapCan['CandidateMatched'].split()[0]
                        elif len(mapCan['CandidateMatched'].split('-')) > 1:
                            if mapCan['CandidateMatched'].split('-')[1].isnumeric():
                                toAdd = mapCan['CandidateMatched'].split('-')[0]
                        else:
                            toAdd = mapCan['CandidateMatched']
                        if toAdd not in biomarkerList[phrasePos] and mapCan['MatchedWords'][0] not in biomarkerList[phrasePos]:
                            biomarkerList[phrasePos].append(toAdd)

                    # Now the experience of some probes being [aapp] + 'probe'
                    elif semType in ['aapp', 'enzy'] and len(mapping['MappingCandidates']) > mcPos+1:
                        if mapping['MappingCandidates'][mcPos+1]['CandidateMatched'].lower() == 'probe':
                            if mapCan['MatchedWords'][0] not in biomarkerList[phrasePos]:
                                biomarkerList[phrasePos].append(mapCan['MatchedWords'][0])
                    # This find qualifier words - which are most frequently adverbs!
                    elif semType == 'qlco':
                        if 'adv' in partOfSpeechList[phrasePos]:
                            if mapping['MappingCandidates'][mcPos]['CandidateMatched'] not in qualifierList[phrasePos]:
                                qualifierList[phrasePos].append(mapping['MappingCandidates'][mcPos]['CandidateMatched'])

                    # This one is for some larger concepts - rearrangements especially!
                    elif semType == 'genf':
                        if mapCan['MatchedWords'][0].lower() in ['rearrangement']:
                            if mapCan['MatchedWords'][0].lower() not in conceptList[phrasePos]:
                                conceptList[phrasePos].append(mapCan['MatchedWords'][0].lower())

    # Here we're doing some cleanup. If a gene name is added, but the probe is in that phrase too, we want the probe.
    # I THINK. Go back and fix this if possible.
    for i in range(0, len(biomarkerList)):
        if len(biomarkerList[i]) > 1:
            if biomarkerList[i][0] in biomarkerList[i][1]:
                biomarkerList[i].remove(biomarkerList[i][0])
    for i in range(0, len(conceptList)):
        if ''.join(conceptList[i]) in ' '.join(biomarkerList[i]):
            conceptList[i] = []
    # The word 'or' probably always(?) indicates that both things the or is referring to are possibilities
    for i in range(0, len(linkingList)):
        if 'or' in linkingList[i]:
            qualifierList[i-1].append('Possible')
            qualifierList[i+1].append('Possible')

    # Now let's move any 'chromosome' concept up to the gene list.
    for i in range(0, len(conceptList)):
        for j in range(0, len(conceptList[i])):
            if 'chromosome' in conceptList[i][j].lower() and len(conceptList[i][j].split()) == 2:
                if conceptList[i][j].split()[1].isnumeric() or conceptList[i][j].split[1].lower() in ['x', 'y']:
                    if conceptList[i][j] not in biomarkerList[i]:
                        biomarkerList[i].append(conceptList[i][j])
                    conceptList[i].remove(conceptList[i][j])

    print(biomarkerList)
    print(conceptList)
    print(qualifierList)
    print(numericList)
    print(linkingList)
    print(' ')

    # Now we'll cycle through and actually come up with some RESULTS. We'll also want to keep track of if they've been
    # used. If we run into the end of a concept and they haven't we'll use them then.
    conceptOnDeck = []
    numberOnDeck = []
    qualifierOnDeck = []
    biomarkerOnDeck = []
    conceptUsed = False
    numberUsed = False
    qualifierUsed = False
    biomarkerUsed = False

    biomarker = ''
    concept = ''
    qualifier = ''
    number = ''
    for i in range(0, len(biomarkerList)):
        # If we come across a biomarker, the other bits of information about it are either in the same phrase,
        # an earlier phrase, or a later phrase. If they're in the same phrase, add them all at once. If they're
        # in an earlier phrase, they're stored in 'onDeck'. If they're in a future phrase, I'm counting on running
        # into them before I run into another biomarker.
        if biomarkerList[i]:
            biomarker = []
            if biomarkerOnDeck and biomarkerUsed:
                biomarkerOnDeck = []
            elif biomarkerOnDeck:
                biomarker = biomarkerOnDeck
                biomarkerOnDeck = []
            biomarker = biomarker + biomarkerList[i]
            biomarkerList[i] = []
            concept = ''
            qualifier = ''
            number = ''
            # There are some additional checks when adding in concepts - first, no repeats. Second, if one is more
            # detailed than the other, add the more detailed. Third, if the stuff shows up in the gene list, add
            # the more detailed one in there.
            if conceptList[i]:
                concept = ''
                concept = conceptList[i]
                if conceptOnDeck:
                    concept = concept + conceptOnDeck
                    conceptUsed = True
                for con in concept:
                    restOfList = concept[:]
                    restOfList.remove(con)
                    if restOfList:
                        for otherCon in restOfList:
                            if con in otherCon:
                                concept.remove(con)

                for con in concept:
                    bioList = biomarker
                    for bio in range(0, len(bioList)-1):
                        if bioList[bio] in con:
                            bioList[bio] = con
                            if con in concept:
                                concept.remove(con)
                        biomarker = bioList

                conceptList[i] = []

            # It's like this for now: we want each separate CONCEPT to have a different line.
            # But EACH LINE should include all the numeric stuff we find. I THINK. Further investigation,
            # of course, warranted.
            if numericList[i]:
                number = ''
                number = numericList[i]
                number = ' '.join(number)

            if numberOnDeck:
                if len(numberOnDeck) > 1:
                    if '%' in numberOnDeck[0] and '%' in numberOnDeck[1]:
                        number = numberOnDeck[0]
                        del numberOnDeck[0]
                    else:
                        number = ' - '.join(numberOnDeck)
                elif '%' in numberOnDeck[0] and '%' in number:
                    switcher = number
                    number = numberOnDeck[0]
                    numberOnDeck[0] = switcher

            numericList[i] = []


            # I THINK the qualifier always gets exploded down to 1. Actually, no. Possible and Negative might
            # co-exist? Let's wait until we see it.
            if qualifierList[i]:
                qualifier = ''
                qualifier = qualifierList[i]
                if qualifierOnDeck:
                    qualifier = qualifier + qualifierOnDeck
                    qualifierUsed = True
                for qual in qualifier:
                    if qual in ['Possibly', 'Possible']:
                        while 'Possibly' in qualifier:
                            qualifier.remove('Possibly')
                        qualifier.append('Possible')
                        while 'Positive' in qualifier:
                            qualifier.remove('Positive')
                    if qual == 'Negative':
                        while 'Positive' in qualifier:
                            qualifier.remove('Positive')
                    if qual == 'Approximately':
                        while 'Approximately' in qualifier:
                            qualifier.remove('Approximately')
                        qualifier.append('Approximate')
                    qualifierOnDeck = qualifier
                    rest = []
                    # Delete duplicates here
                    if len(qualifier) > 1:
                        for q in qualifier:
                            if q not in rest:
                                rest.append(q)
                        qualifier = rest
                qualifier = ' - '.join(qualifier)
                qualifierList[i] = []

            # MABYE NOT TRUE - INVESTIGATE! This is for the biomarkerOnDeck. It basically assumes that if we run
            # into a biomarker, with no other information, it'll probably be coming later. MAYBE NOT TRUE?
            if biomarker and not concept and not number and not qualifier:
                biomarkerOnDeck = biomarker
                biomarker = []

            ####
            #### And now, we finally put our results together!!
            ####
            if biomarker:
                if len(biomarker) > 1 and len(biomarker) == len(concept):
                    for pos in range(0, len(biomarker)):
                        resultsSandwich = [biomarker[pos], concept[pos], number, qualifier]
                        while '' in resultsSandwich:
                            resultsSandwich.remove('')
                        resultsSandwich = ' - '.join(resultsSandwich)
                        resultsList.append(resultsSandwich)
                elif concept:
                    biomarker = ' '.join(biomarker)
                    for con in concept:
                        resultsSandwich = [biomarker, con, number, qualifier]
                        while '' in resultsSandwich:
                            resultsSandwich.remove('')
                        resultsSandwich = ' - '.join(resultsSandwich)
                        resultsList.append(resultsSandwich)
                else:
                    biomarker = ' '.join(biomarker)
                    resultsSandwich = [biomarker, '', number, qualifier]
                    while '' in resultsSandwich:
                        resultsSandwich.remove('')
                    resultsSandwich = ' - '.join(resultsSandwich)
                    resultsList.append(resultsSandwich)

        # If we get down to concept, numeric, or qualifier, that means that we've ruled out the possibility that
        # there's a biomarker in this position. There might be more than two of anything else
        if conceptList[i]:
            for con in conceptList[i]:
                if conceptOnDeck:
                    if con not in conceptOnDeck:
                        conceptOnDeck.append(con)
                else:
                    conceptOnDeck = [con]
            conceptList[i] = []
            conceptUsed = False
        if numericList[i]:
            for num in numericList[i]:
                if numberOnDeck:
                    if num not in numberOnDeck:
                        numberOnDeck.append(num)
                else:
                    numberOnDeck = [num]
            numericList[i] = []
            numberUsed = False
        if qualifierList[i]:
            for qual in qualifierList[i]:
                if qualifierOnDeck:
                    if qual not in qualifierOnDeck:
                        qualifierOnDeck.append(qual)
                else:
                    qualifierOnDeck = [qual]
            qualifierList[i] = []
            qualifierUsed = False


        # I'm going to have to pay attention to this. My basic assumption is that when we hit a boundary like 'but' or
        # a new sentence, we can assume that we've finished the current thought, and we'll now start talking about other
        # biomarkers, and will probably mention them by name. This MAY NOT be borne out by the actual evidence, so keep it
        # under observation, sucka!
        if linkingList[i]:
            if linkingList[i][0] in ['but' , '.']:
                # So first we handle the case where we've been hanging on to a biomarker:
                if biomarkerOnDeck:
                    concept = []
                    number = ''
                    qualifier = ''
                    biomarker = biomarkerOnDeck
                    if conceptList[i]:
                        concept = concept + conceptList[i]
                    if conceptOnDeck and not conceptUsed:
                        concept = concept + conceptOnDeck
                        conceptOnDeck = []
                    if numericList[i]:
                        number = number + ' - '.join(numericList[i])
                    if numberOnDeck:
                        number = number + ' - '.join(numberOnDeck)
                        numberOnDeck = []
                    if qualifierList[i]:
                        qualifier = qualifier + ' - '.join(qualifierList[i])
                    if qualifierOnDeck:
                        qualifier = qualifier + ' - '.join(qualifierOnDeck)
                        qualifierOnDeck = []
                    for con in concept:
                        finalResult = [biomarker, con, number, qualifier]
                        while '' in finalResult:
                            finalResult.remove('')
                        if biomarker not in ' '.join(resultsList):
                            resultsList.append(' - '.join(finalResult))
                # Then we handle the other case - where there's a biomarker in the slot right now.
                elif resultsList:
                    if conceptOnDeck and not conceptUsed:
                        for con in conceptOnDeck:
                            resultsList[len(resultsList)-1] = resultsList[len(resultsList)-1] + ' - ' + con
                    if numberOnDeck and not numberUsed:
                        for num in numberOnDeck:
                            resultsList[len(resultsList)-1] = resultsList[len(resultsList)-1] + ' - ' + num
                            if '%' in num:
                                index = len(resultsList)-2
                                while '%' not in resultsList[index]:
                                    resultsList[index] = resultsList[index] + ' - ' + num
                                    index = index-1

                    if qualifierOnDeck and not qualifierUsed:
                        for qual in qualifierOnDeck:
                            if qual == 'Positive' and 'Negative' in resultsList[len(resultsList)-1] or\
                                'Possible' in resultsList[len(resultsList)-1]:
                                qual = ""
                            if qual == 'Possible' and 'Possible' in resultsList[len(resultsList)-1]:
                                qual = ""
                            if qual == 'Positive' and 'Positive' in resultsList[len(resultsList)-1]:
                                qual = ""
                            if qual == 'Negative' and 'Negative' in resultsList[len(resultsList)-1]:
                                qual = ""
                            if qual:
                                resultsList[len(resultsList)-1] = resultsList[len(resultsList)-1] + ' - ' + qual
                numberOnDeck = []
                qualifierOnDeck = []
                conceptOnDeck = []

    print("=======RESULTS=======")
    for result in resultsList:
        print(result)
    print("=====================")
    print("")
    print("")
    print("")
