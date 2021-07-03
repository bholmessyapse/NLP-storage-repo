import pandas as pd
# For regex
import re
from MetaMapForLots import metamapstringoutput
from metamapLoader import metamapStarter
from metamapLoader import metamapCloser
from collections import Counter

def estrogenProgesteroneTest(lower):
    if 'estrogen and progesterone receptor assay' in lower:
        section = lower[lower.index('estrogen and progesterone receptor assay'):]
        if 'test description' not in section:
            return '', lower
        section = section[:section.index('test description')]
        sectionOrig = section
        if 'estrogen receptor\n' in section:
            section = section[section.index('estrogen receptor\n'):]
            if 'progesterone receptor' not in section:
                if 'er and pr' not in section:
                    if any(x in section for x in ['percent positive: n/a']):
                        return 'test failed', lower
                    # Or it could have just ER and NOT mention 'er and pr'
                    else:
                        erBit = section[:section.index('er allred score:')].replace('\n', ' ').strip()
                        erAllred = section[section.index('estrogen receptor score:'):]
                        erAllred = erAllred[:erAllred.index('(')]
                        erBit = erBit + ' ' + erAllred
                        return erBit, lower
                erBit = section[:section.index('er and pr')].replace('\n', ' ').strip()
                erAllred = section[section.index('estrogen receptor score:'):]
                erAllred = erAllred[:erAllred.index('(')]
                erAllred = erAllred.replace('estrogen receptor score:', 'allred score:')
                erBit = erBit + ' ' + erAllred
                return erBit, lower
            else:
                erBit = section[:section.index('progesterone receptor')].replace('\n', ' ').strip()
                if 'progesterone receptor\n' not in section:
                    if 'er and pr' in section:
                        erBit = section[:section.index('er and pr')].replace('\n', ' ').strip()
                    prBit = ''
                else:
                    prBit = section[section.index('progesterone receptor\n'):]
                if 'er and pr' in section:
                    if prBit != '':
                        prBit = prBit[:prBit.index('er and pr')].replace('\n', ' ').strip()
                    if 'estrogen receptor score:' not in section:
                        erAllred = ''
                    else:
                        erAllred = section[section.index('estrogen receptor score:'):]
                        erAllred = erAllred[:erAllred.index('(')]
                    # Sometimes prog. rep. sco. is missing the colon
                    if 'progesterone receptor score:' not in section:
                        section = section.replace('progesterone receptor score', 'progesterone receptor score:')
                    # Sometimes it's 'estrogen [receptor score: twice?
                    if 'progesterone receptor score:' not in section:
                        sectionSecond = section[section.index('estrogen receptor score:') + len('estrogen receptor score:'):]
                        sectionThird = sectionSecond.replace('estrogen receptor score:', 'progesterone receptor score:')
                        section = section.replace(sectionSecond, sectionThird)
                    # Or it might just be absent. Sometimes you gotta give up.
                    if 'progesterone receptor score:' not in section:
                        erAllred = erAllred.replace('estrogen receptor score:', 'allred score:')
                        prAllred = ''
                    else:
                        prAllred = section[section.index('progesterone receptor score:'):]
                        prAllred = prAllred[:prAllred.index('(')]
                        erAllred = erAllred.replace('estrogen receptor score:', 'allred score:')
                        if 'prica' in prBit:
                            prAllred = prAllred.replace('progesterone receptor score:', 'allred score:')
                    erBit = erBit + ' ' + erAllred
                    prBit = prBit + ' ' + prAllred
                else:
                    prBit = prBit.replace('\n', ' ').strip()
                lower = lower.replace(sectionOrig, '')
                if 'allred score: %' in prBit:
                    prBit = prBit[:prBit.index('allred score: %')]
                return erBit + ' . . ' + prBit, lower
        else:
            print(section)
            print('NEW ER/PR')
            return '', lower

        print(section)
        input()


def splitUpPanel(text, testtype):
    # These results are positive results (or vous results)
    positivePanelResults = []
    # The positive panel is held for negative imputation. The RETURN STRING is actually what gets returned from this function
    returnString = ''

    # There are a number of tests that just look for one gene, but would have identical other formats. Rather than
    # repeat the code to analyze these multiple times, we'll hold them here.
    singleGeneTests = ['ret', 'chek2', 'tp53']

    for gene in singleGeneTests:
        if 'in\n' + gene + ' gene' in text:
            text = text.replace('in\n' + gene + ' gene', 'in ' + gene + ' gene')

    # The first thing to handle is if we DID find results
    if 'results\npositive:' in text:
        if 'no other pathogenic mutations' in text:
            text = text.replace('no other pathogenic mutations', 'no additional pathogenic mutations')
        if 'no additional pathogenic mutations' not in text:
            print('WEIRD POSITIVE')
            print(text)
            input()

        panelSection = text[text.index('results\npositive:'):]
        panelSection = panelSection[:panelSection.index('no additional pathogenic')]
        sectionOrig = panelSection
        # This should give us the genes identified
        panelSection = panelSection.split('gene:')
        panelSection = panelSection[1:]
        returnString = '\nproduced_panel_results_positive'
        for sec in panelSection:
            returnBit = ''
            geneSec = sec.split('\n')
            returnBit = returnBit + geneSec[0].strip()
            positivePanelResults.append(geneSec[0].strip())
            for pos in range(0, len(geneSec)):
                line = geneSec[pos]
                if line.startswith(('variant:', 'variant classification:', 'variant type:', 'zygosity: ')):
                    returnBit = returnBit + ' ' + line[line.index(':') + 1:]
            returnString = returnString + '\n' + returnBit
        returnString = returnString + '\nend_panel_results_positive\n'
        text = text.replace(sectionOrig, returnString)

    if 'results\nvous:' in text and 'results\npositive:' not in text:
        if 'no other pathogenic mutations' in text:
            text = text.replace('no other pathogenic mutations', 'no additional pathogenic mutations')
        if 'no additional pathogenic mutations' not in text:
            print('WEIRD VOUS')
            print(text)
            input()
    # Next comes vous's
    if 'variants of uncertain significance (vous) were also identified:' in text:
        text = text.replace('variants of uncertain significance (vous) were also identified:', 'variants of uncertain significance (vous) identified:')
    if 'variant of uncertain significance identified' in text:
        text = text.replace('variant of uncertain significance identified', 'variant of uncertain significance (vous) identified:')
    if 'variant of' in text:
        text = text.replace('variant of', 'variants of')
    if 'variants of uncertain significance (vous) identified:' in text or 'variants of unknown significance (vous) identified:' in text:
        panelSection = text[text.index('(vous) identified') + len('(vous) identified'):]
        panelSection = panelSection[:panelSection.index('no additional pathogenic')]
        sectionOrig = panelSection
        # This should give us the genes identified
        panelSection = panelSection.split('gene:')
        panelSection = panelSection[1:]
        returnString = '\nproduced_panel_results_vous'
        for sec in panelSection:
            returnBit = ''
            geneSec = sec.split('\n')
            returnBit = returnBit + geneSec[0].strip()
            positivePanelResults.append(geneSec[0].strip())
            for pos in range(0, len(geneSec)):
                line = geneSec[pos]
                if line.startswith(('variant:', 'variant classification:', 'variant type:', 'zygosity: ')):
                    returnBit = returnBit + ' ' + line[line.index(':') + 1:]
            returnString = returnString + '\n' + returnBit
        returnString = returnString + '\nend_panel_results_vous\n'
        text = text.replace(sectionOrig, returnString)

    if returnString != '':
        # This is a really weird thing, but metamap recognizes both the p. and c. in a line ONLY if the p. is first. Dunno! So we'll swap 'em
        for line in returnString.split('\n'):
            if 'p.' in line and 'c.' in line:
                lineP = ''
                linePInd = 0
                lineC = ''
                lineCInd = 0
                lineS = line.split()
                for lpos in range(0, len(lineS)):
                    if lineS[lpos].startswith('c.'):
                        lineC = lineS[lpos]
                        lineCInd = lpos
                    elif lineS[lpos].startswith('p.'):
                        lineP = lineS[lpos]
                        linePInd = lpos
                if lineP !='' and lineC != '' and linePInd > lineCInd:
                    lineS[lineCInd] = lineP
                    lineS[linePInd] = lineC
                newline = ' '.join(lineS)
                text = text.replace(line, newline)

    # We've got some variant ways of specifying 'no results' here. Let's standardize them!
    # The text we're looking for is 'no pathogenic mutations, variants of unknown significance or
    # gross deletion(s)/duplication(s) were detected.
    if 'results\nnegative' in text:
        text = text.replace('results\nnegative', '')

    if 'pathogenic mutations or variants' in text:
        text = text.replace('pathogenic mutations or variants', 'pathogenic mutations, variants')

    # Sometimes there's a variant on 'we didn't find anything (else)'. Let's add it!
    if 'no pathogenic mutations' not in text and 'no additional pathogenic mutations' not in text:
        if 'pathogenic mutation(s): none detected\nvariant(s) of unknown significance: none detected\ngross deletion(s)/duplication(s): none detected' in text:
            text = text.replace('pathogenic mutation(s): none detected\nvariant(s) of unknown significance: none detected\ngross deletion(s)/duplication(s): none detected',
                                'no pathogenic mutations, variants of unknown significance, or gross deletions/duplications were detected')
        elif 'no other pathogenic mutation' in text:
            text = text.replace('no other pathogenic mutation', 'no pathogenic mutation')
        elif 'for gross deletions or duplications in brca1 or brca2 were detected,' in text:
            text = text.replace('for gross deletions or duplications in brca1 or brca2 were detected,', 'no pathogenic mutations, variants of unknown significance, \
            gross deletions, or duplications were detected')
        else:
            print(text)
            print('NO PANEL ENDER')
            input()
    # If we have a panel result with 'we didn't find anything', we'll want to add the genes they didn't find here
    if any(x in text for x in ['no pathogenic mutations, variants of unknown significance', 'no additional pathogenic mutations,',
                               'no pathogenic mutations, variants of uncertain significance']):
        text = text.replace('no additional pathogenic mutations', 'no pathogenic mutations')
        foundPanel = False
        if testtype in ['brca1/2 sequencing and common deletions / duplications', 'brca1/2 sequencing and full deletions / duplications', 'brca1/2 deletions and duplications']:
            negatives = ['brca1', 'brca2']
            for neg in negatives:
                if neg in positivePanelResults:
                    negatives.remove(neg)

            # All on one line, please
            text = text.replace('were detected', 'were detected ' + ', '.join(negatives) + '\nend_panel_results_negative\n')\
                .replace('gross\ndeletion', 'gross deletion').replace('or\ngross', 'or gross').replace('deletions\nor', 'deletions or')

            text = text.replace('no pathogenic mutations', '\nproduced_panel_results_negative\nno pathogenic mutations')
        elif any(x in text for x in ['genes linked to breast cancer:', 'breast and/or ovarian cancer:', 'pancreatic, breast, and colorectal\ncancer:', "this individual's children.",
                                     'other types of cancer:', 'to endometrial cancer:', 'duplications within chek2 gene', 'in chek2 gene', 'familial variant in palb2',
                                     'inherited forms of prostate cancer and other cancer\npredisposition:', 'and duplications within pms2.', 'known familial variant in',
                                     'duplications within ret gene.', 'in ret gene.', 'custom hereditary cancer risk panel includes 5 genes (', 'forms of colorectal cancer:',
                                     'duplications within tp53 gene.', 'in tp53 gene',]):

            for x in ['genes linked to breast cancer:', 'breast and/or ovarian cancer:', 'pancreatic, breast, and colorectal\ncancer:', 'to endometrial cancer:',
                      'inherited forms of prostate cancer and other cancer\npredisposition:', 'forms of colorectal cancer:', 'other types of cancer:']:
                if x in text:
                    foundPanel = True
                    negatives = text[text.index(x) + len(x):]
                    negatives = negatives[:negatives.index('. \n') + 3]
                    negatives = negatives.replace('\n', ' ').replace('and', '').replace('.', '')
                    negativesOrig = negatives
                    negatives = negatives.split(', ')
                    for neg in range(0, len(negatives)):
                        negatives[neg] = negatives[neg].strip()
                    for neg in negatives:
                        if neg.strip() in positivePanelResults:
                            negatives.remove(neg)
                    negatives = ', '.join(negatives)
                    text = text.replace(negativesOrig, '')
                    text = text.replace('were detected', 'were detected ' + negatives + '\nend_panel_results_negative\n').replace('gross\ndeletion', 'gross deletion').replace('or\ngross',
                                                                                                                                                                                 'or gross')
                    text = text.replace('no pathogenic mutations', '\nproduced_panel_results_negative\nno pathogenic mutations')
            # Separate custom test
            for x in ['custom hereditary cancer risk panel includes 5 genes (']:
                if x in text:
                    foundPanel = True
                    negatives = text[text.index(x) + len(x):]
                    negatives = negatives[:negatives.index(')')]
                    negatives = negatives.replace('\n', ' ').replace('and', '').replace('.', '')
                    negativesOrig = negatives
                    negatives = negatives.split(', ')
                    for neg in range(0, len(negatives)):
                        negatives[neg] = negatives[neg].strip()
                    for neg in negatives:
                        if neg.strip() in positivePanelResults:
                            negatives.remove(neg)
                    negatives = ', '.join(negatives)
                    text = text.replace(negativesOrig, '')
                    text = text.replace('were detected', 'were detected ' + negatives + '\nend_panel_results_negative\n').replace('gross\ndeletion', 'gross deletion').replace('or\ngross',
                                                                                                                                                                                 'or gross')
                    text = text.replace('no pathogenic mutations', '\nproduced_panel_results_negative\nno pathogenic mutations')

            for gene in singleGeneTests:
                for x in ['and duplications within' + gene + '.', 'in ' + gene + ' gene']:
                    if x in text:
                        foundPanel = True
                        negatives = gene
                        if gene in positivePanelResults:
                            text = text.replace(x, '')
                        else:
                            text = text.replace(x, '')
                            text = text.replace('were detected', 'were detected ' + negatives + '\nend_panel_results_negative\n')\
                                .replace('gross\ndeletion', 'gross deletion').replace('or\ngross', 'or gross')

            # These panels are just for brca
            for x in ['known familial variant in']:
                if x in text and not foundPanel:
                    negatives = text[text.index('known familial variant in'):]
                    negatives = negatives[:negatives.index('individual.') + len('individual.')]
                    text = text.replace(negatives, '')
            for x in ['familial variant in palb2']:
                if x in text and not foundPanel:
                    negatives = 'palb2'
                    text = text.replace('familial variant in palb2', '')
            for x in ["this individual's children."]:
                if x in text and not foundPanel:
                    negatives = text[text.index('based on these results'):]
                    negatives = negatives[:negatives.index("this individual's children")]
                    text = text.replace(negatives, '')

        # Could be a custom list
        elif testtype in ['custom hereditary cancer risk panel'] and 'dna analysis for:' in text:
            bit = text[text.index('dna analysis for:') + len('dna analysis for:'):]
            if ', custom hereditary' not in bit:
                print(bit)
                input()
            bit = bit[:bit.index(', custom hereditary')]
            if ':' in bit:
                bit = bit[bit.index(':')+1:]
            negatives = bit
            negativesOrig = negatives
            negatives = negatives.split(', ')
            for neg in range(0, len(negatives)):
                negatives[neg] = negatives[neg].strip()
            for neg in negatives:
                if neg.strip() in positivePanelResults:
                    negatives.remove(neg)
            negatives = ', '.join(negatives)
            text = text.replace(negativesOrig, '')
            text = text.replace('were detected', 'were detected ' + negatives + '\nend_panel_results_negative\n').replace('gross\ndeletion', 'gross deletion').replace('or\ngross',
                                                                                                                                                                      'or gross')
            text = text.replace('no pathogenic mutations', '\nproduced_panel_results_negative\nno pathogenic mutations')
        # This is for only one brca
        elif testtype in ['known familial variant for brca2', 'known familial variant for brca1']:
            if testtype == 'known familial variant for brca1':
                type = 'brca1'
            else:
                type = 'brca2'
            negatives = type
            if type in positivePanelResults:
                text = text
            else:
                text = text.replace('were detected', 'were detected ' + negatives + '\nend_panel_results_negative\n').replace('gross\ndeletion', 'gross deletion').replace('or\ngross',
                                                                                                                                                                           'or gross')
                text = text.replace('no pathogenic mutations', '\nproduced_panel_results_negative\nno pathogenic mutations')

        else:
            print(text)
            print('NEED NEW PANEL SECTION!')
            print(positivePanelResults)
            print(testtype)
            input()
        return text


def estrogenImmunocyto(lower):
    return('yo')
