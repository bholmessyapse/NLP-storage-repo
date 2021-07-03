# A new metamap? Will wonders never cease! The ask this time is to get codes for a list of medications.

# Keeping these here, as they're commonly useful.
import pandas as pd
import numpy as np
import re
from subprocess import call
import itertools

import os
import json

# Turn this on to see where everything is getting added
# Not really used much in the new medication list.
debug = False

def metamapstringoutput(inputMed):

    try:

        # First, write the name of the medication to the input folder
        file = '/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput'
        with open(file, 'w') as filetowrite:
            filetowrite.write(inputMed)

        # Read the file, and over-write it with the edited version.
        with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput', 'r+') as file:
            data = file.read()
            dataOrig = file.read()
            encoded_string = data.encode("ascii", "ignore")
            data = encoded_string.decode()

            file.seek(0)
            file.write(data + '\n')
            file.truncate()

        # If the name couldn't be matched, return it please
        if data in [' ', '']:
            return dataOrig, 'Non-Standard Name', ''

        # This uses metamap to create an output file based on the input file.
        os.system("bin/metamap -Z 2021AA -V USAbase --strict_model --JSONf 2 --negex --nomap NoMapFile --prune 30 -Q 0 /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                  "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
        try:
            with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
                data = json.load(json_file)
        except:
            # This uses metamap to create an output file based on the input file.
            os.system("bin/metamap --JSONf 2 --negex --nomap NoMapFile --prune 30 -Q 0 /Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleInput "
                      "/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt")
            with open('/Users/bholmes/Desktop/DeleteMeSoon/orus/MetaMapInput/sampleOutput.txt') as json_file:
                data = json.load(json_file)

        ###
        # Ok, time for the the real NLP to begin.
        ###

        CUI = 'COULD NOT FIND MATCH'
        medicationText = ''
        medicationSynonym = ''

        # Let's take this one at a time, by utterance. I'm scanning over all utterances for now. We've found that multiple
        # utterances can have important information.
        for utt in range(0, len(data['AllDocuments'][0]['Document']['Utterances'])):
            utterance = data['AllDocuments'][0]['Document']['Utterances'][utt]

        # Now we'll loop through every phrase in the utterance, and pull out the important info.
        # This is MUCH MUCH truncated for now, since we're just looking for medication names and CUIs
        for phrasePos in range(0, len(utterance['Phrases'])):
            phrase = utterance['Phrases'][phrasePos]

            # There is probably only one mapping per, because this is just a list of medications. Still: this'll be useful for the future!
            for mapPos in range(0, len(phrase['Mappings'])):
                mapping = phrase['Mappings'][mapPos]
                # For every mapping position, we go through all the candidates... again, assuming only one
                for mcPos in range(0, len(mapping['MappingCandidates'])):
                    mapCan = mapping['MappingCandidates'][mcPos]
                    mapText = mapCan['CandidateMatched']
                    # Next and final step down is going through the semantic types
                    # If we find any phsu tags, that's pharmaceutical substance, we'll take that
                    for semPos in range(0, len(mapCan['SemTypes'])):
                        semType = mapCan['SemTypes'][semPos]
                        # Concepts/quals being the easiest part (I say, famous last words) - let's start there!
                        # Phsu is semantic type
                        if semType in ['phsu', 'bacs']:
                            CUI = mapCan['CandidateCUI']
                            medicationText = mapCan['CandidateMatched']
                            medicationSynonym = mapCan['CandidatePreferred']

        return CUI, medicationText, medicationSynonym

    except:
        print("OOPS!")
        raise ValueError('File could not be run')
