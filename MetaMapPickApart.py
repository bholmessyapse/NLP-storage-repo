import pandas as pd
import numpy
import operator
import re
import pymetamap
from subprocess import call
import subprocess
import os
import json

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

dataResults = set()


# If we don't find any other results, but we do find a mention of things being normal, that means the test came back
# all normal.
allNormal = False

#####
# So the default assumption we're going with for now is that people will either refer to a concept then a quantity
# (loss of chromosome 9 in 50% of cells), or vice versa (50% of cells showed a loss of chromosome 9). And will NEVER
# Do so in a nested fashion (50% of cells, 50% of which had a loss of chromosome 10 and 13, had a loss of at least
# chromosome 10). This would be a horribly badly written report, but I suppose it's not impossible! If this
# becomes a larger problem, we'll probably have to go all deep learning on it.
####


# Utterances are large sentence blocks. This MIGHT go away, if I decide to feed in one sentence at a time? But
# on the other hand, it might be useful to look ahead.
for utt in range(0, len(data['AllDocuments'][0]['Document']['Utterances'])):
    utterance = data['AllDocuments'][0]['Document']['Utterances'][utt]

    # This only gets filled in if we have a percentage for something to be. Let's see how often
    # this works out!
    percentage = ''

    # This only gets filled in if we find a phrase in this range. Further testing is warranted
    # to see if the range always shows up in the same phrase!
    numRange = ''

    # Possible qualification words
    quals = []
    qual = ''

    # Result Genes
    genes = set()

    # Condition is something like a rearrangement, loss, monosomy, etc.
    condition = ''

    # Occasionally, for whatever reason, we don't catch 'no evidence' as a negation. Correcting that.
    noEvidence = False

    # Phrases are shorter semantic blocks. These we might DEFINITELY want to search through.
    # NOTE: The assumption, FOR NOW, is that information about quantities (ranges, percentages)
    # will commonly persist only in a particular utterance. Let's see how often this stays true!
    for phr in range(0, len(utterance['Phrases'])):
        phrase = utterance['Phrases'][phr]
        #print(phrase['PhraseText'])

        if 'no evidence' in phrase['PhraseText'].lower():
            noEvidence = True

        # Here we're going to pull out percentages - this might measure signal strength (% of cells showing signal)
        # or probe signal (80% of nuclei showed the aberrant signal) - something like that.
        if '%' in phrase['PhraseText']:
            numPercent = ''
            placePercent = ''
            percentUnit = 0
            for syntaxUnit in range(0, len(phrase['SyntaxUnits'])):
                if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and '%' in phrase['SyntaxUnits'][syntaxUnit]['InputMatch']:
                    numPercent = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].replace(' ','')
                    percentUnit = syntaxUnit
                # There isn't always a LexCat - so if there is one, we want the noun that the % refers to
                if 'LexCat' in phrase['SyntaxUnits'][syntaxUnit].keys():
                    if phrase['SyntaxUnits'][syntaxUnit]['LexCat'] == 'noun' and syntaxUnit > percentUnit:
                        placePercent = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'].replace(' ','')
                        break
            if numPercent and placePercent:
                percentage = numPercent + ' ' + placePercent

        # This one pieces apart ranges (for copy number etc.) - I noticed lots of reports would
        # reference "3 to 10" copies of some number.
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
                # This bit is tagged on to catch if they say "3 copies" without the range
                elif phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'shapes' and \
                        'LexCat' in phrase['SyntaxUnits'][syntaxUnit + 1].keys():
                    if phrase['SyntaxUnits'][syntaxUnit + 1]['LexCat'] ==  'noun' and \
                        not numRange and phrase['SyntaxUnits'][syntaxUnit +1]['Tokens'][0] != 'chromosome':
                        numRange = phrase['SyntaxUnits'][syntaxUnit]['InputMatch'] + ' ' \
                        + phrase['SyntaxUnits'][syntaxUnit + 1]['InputMatch']

            # Here we're looking for qualifiers - and we assume those will get applied later in the sentence.
            # This one we might need to revisit! I think the fastest way to do this is to make a list of all
            # the adverbs, and check if they are qualification types later. Note that we're doing this while
            # piggybacking off the other attempt to find ranges, because that looks through SemanticTypes
            if phrase['SyntaxUnits'][syntaxUnit]['SyntaxType'] == 'adv':
                quals.append(phrase['SyntaxUnits'][syntaxUnit]['Tokens'][0])

        # Mappings I actually probably don't want to be able to look ahead on, and instead just want
        # to cycle through. They're different interpretations of the phrase.
        for mapping in phrase['Mappings']:
            probeName = ""
            probeGene = ""
            isNegated = False
            for candidate in range(0, len(mapping['MappingCandidates'])):
                # Dunno how useful these are gonna be. isNegated is obviously useful, to make sure
                # I'm showing negations. stringToAdd is the result that I add. The other two are
                # holders that might or might not get filled.
                semtypes = []
                words = []
                stringToAdd = ""

                if mapping['MappingCandidates'][candidate]['Negated'] == '1':
                    isNegated = True

                # semtype shows what KIND of text we're looking at. This is where we do most of the heavy lifting.
                for semtype in mapping['MappingCandidates'][candidate]['SemTypes']:

                    # We're looking for genes that are going to be mapped to a new result later on here.
                    # MetaMap likes to do "[genename] Gene", so we're splitting that off.
                    if semtype == 'gngm':
                        gene = mapping['MappingCandidates'][candidate]['CandidateMatched']
                        if 'probe' not in gene.lower():
                            if len(gene.split()) == 2:
                                if gene.split()[1] == 'Gene':
                                    gene = gene.split()[0]
                            genes.add(gene)

                    # We're looking for qualification words here - if we already know one is an adverb, let's see
                    # if it's also a qualification concept. If it is, remove it from the list!
                    if semtype == 'qlco' and mapping['MappingCandidates'][candidate]['MatchedWords'][0] in quals:
                        quals.remove(mapping['MappingCandidates'][candidate]['MatchedWords'][0])
                        qual = mapping['MappingCandidates'][candidate]['MatchedWords'][0]

                    # Sometimes the 'probe' word gets put in the next phrase. boooo.
                    if phr + 1 < len(utterance['Phrases']):
                        if utterance['Phrases'][phr+1]['PhraseText'].lower().startswith('probe'):
                            phrase['PhraseText'] = phrase['PhraseText'] + ' probe'

                    # Now we'll attempt to find information about probes - we're breaking this up by
                    # common semantic type. More research, as always, required.
                    if (semtype == 'celc' and 'probe' in phrase['PhraseText']):
                        probeName = '.'.join(mapping['MappingCandidates'][candidate]['MatchedWords'])
                    if semtype == 'aapp' and 'probe' in phrase['PhraseText']:
                        probeGene = mapping['MappingCandidates'][candidate]['MatchedWords'][0].upper()
                        probeGene = probeGene + ' probe -'
                    if probeGene and probeName:
                        condition = probeGene + ' ' + probeName
                        genes = set()

                    # 'FNDG' is a "finding". Probably important! 'COMD' is also very popular.
                    if (semtype == 'fndg' or semtype == 'comd' or semtype == 'cgab'):
                        words = mapping['MappingCandidates'][candidate]['CandidateMatched']
                        if 'rearrangement' in words.lower() or 'amplification' in words.lower() or 'deletion' in words\
                                .lower() or 'gain' in words.lower():
                            # We're getting rid of duplicates here - "Gene Rearrangement", "Rearrangement", and
                            # "[gene] Gene Rearrangement
                            if len(mapping['MappingCandidates'][candidate]['CandidateMatched'].split()) == 2 and \
                                    mapping['MappingCandidates'][candidate]['CandidateMatched'].split()[0].lower() == 'gene':
                                condition = mapping['MappingCandidates'][candidate]['CandidateMatched'].split()[1]
                            if len(mapping['MappingCandidates'][candidate]['CandidateMatched'].split()) == 3 and \
                                    mapping['MappingCandidates'][candidate]['CandidateMatched'].split()[1].lower() == 'gene':
                                condition = mapping['MappingCandidates'][candidate]['CandidateMatched'].split()[2]
                                genes.add(mapping['MappingCandidates'][candidate]['CandidateMatched'].split()[0])
                            else:
                                condition = mapping['MappingCandidates'][candidate]['CandidateMatched']
                            # If one of the genes didn't get matched, match it now
                            if 0 < candidate < len(mapping['MappingCandidates']):
                                if mapping['MappingCandidates'][candidate-1]['SemTypes'][0] == 'lbtr':
                                    condition = mapping['MappingCandidates'][candidate-1]['MatchedWords'][0].upper() + '-' + condition
                        # We might have monosomy alone or with a candidate
                        if 'monosomy' in words.lower():
                            if 'x' in words.lower():
                                condition = words
                                genes = set()
                        # This is for the larger concepts
                        if candidate + 1 < len(mapping['MappingCandidates']):
                            if (semtype == 'comd' or semtype == 'cgab') and (
                                    'celc' in mapping['MappingCandidates'][candidate + 1]['SemTypes']
                                    or 'nusq' in mapping['MappingCandidates'][candidate + 1]['SemTypes']):
                                concept = mapping['MappingCandidates'][candidate]['CandidateMatched']
                                location = mapping['MappingCandidates'][candidate + 1]['CandidateMatched']
                                condition = concept + ' ' + location
                            # If there's a linking word like "or" (add more?) - go back adding concepts.
                            startLocation = phr
                            while utterance['Phrases'][startLocation-1]['PhraseText'] == 'or':
                                # I'm assuming that the word "OR" means that either option is possible. Correct?
                                qual = 'possible'
                                startLocation = startLocation-2
                                for phrMap in utterance['Phrases'][startLocation]['Mappings']:
                                    for phrcand in phrMap['MappingCandidates']:
                                        for phrSem in phrcand['SemTypes']:
                                            if phrSem == 'comd':
                                                newAdd = phrcand['CandidateMatched'] + ' ' + location
                                            if newAdd not in condition:
                                                condition = newAdd + ' or ' + condition

                        # This is for normal tests
                        if semtype == 'fndg' and 'normal limits' in mapping['MappingCandidates'][candidate]['CandidateMatched'].lower():
                            allNormal = True


                # Now, time to put it together for the results
                if condition and (len(condition.split()) > 1 or len(genes) > 0):
                    lenStart = len(dataResults)
                    result = condition
                    condition = ''
                    if result in ' '.join(dataResults):
                        break
                    # For whatever reason, metamap sometimes leaves out the ending decimal point in probes?
                    for res in dataResults:
                        if len(res.split(' - ')) > 2 and len(result.split(' - ')) > 1:
                            if res.split(' - ')[1] in result.split(' - ')[1]:
                                newResult = ' - '.join(result.split(' - ')[0:2]) + ' - ' + ' - '.join(res.split(' - ')[2:])
                                dataResults.remove(res)
                                dataResults.add(newResult)
                                result = ''
                                break
                    if noEvidence:
                        isNegated = True
                    if ' or ' in result:
                        results = result.split(' or ')
                        qual = 'possible'
                    else:
                        results = [result]

                    for resul in results:
                        if isNegated:
                            resul = resul + ' - negative'
                        if qual:
                            if qual != 'to':
                                if qual == 'possible': qual = 'Possible'
                                resul = resul + ' - ' + qual
                        if numRange:
                            resul = resul + ' - ' + numRange
                        if percentage:
                            resul = resul + ' - ' + percentage
                        if len(genes) > 0:
                            for gene in genes:
                                if(gene + ' - ' + resul + ' - negative' ) not in dataResults and resul not in dataResults:
                                    dataResults.add(gene + ' - ' + resul)
                            genes = set()
                        else:
                            if resul and resul + " - negative" not in dataResults:
                                dataResults.add(resul)
                        if len(dataResults) > lenStart:
                            noEvidence = False
                            isNegated = False
                            percentage = ''
                            numRange = ''

if allNormal and not dataResults:
    dataResults.add("All Results Normal")

print('')
print("==========RESULTS===========")
for data in dataResults:
    print(data)