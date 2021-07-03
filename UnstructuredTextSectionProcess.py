import pandas as pd
import re
from UnstructuredSpecificTests import splitUpPanel

# Turn this on when checking to see what's coming in
showResults = False
# Turn this on to see how the samples are being digested
audit = False
# Turn this on to see progress through the program
monitor = False

monaud = False

if monaud:
    monitor = True
    audit = True

# This is where we take incoming sections and extract the results from them.
def processSection(text, testtype, pathol, dr, do, regxp, repid, bioms, sampleL, fullText):
    # We're skipping these for now
    if 'cosmic census genes:' in text:
        text = ''
    origText = text
    sampleLOrig = sampleL
    specimenSection = sampleL
    text = ' ' + text
    # This is the sections, prepared for metamap, that we're returning
    returnBit = ''
    # These are the locations that we're returning
    returnLocation = ''
    # These sections have not passed any of our tests, and have no content in them
    noContentSections = []
    noContentSectionsIds = []
    # These are the sections we remove, assuming that they are full of only non-results
    removedSections = []
    removedSectionIds = []
    # These are the sections
    addendumLeftovers = []
    addendumLeftoverIds = []
    print(repid)

    # These are sections that we exclude for either being about previous results, speculative results, or other something
    excludedSections = []
    excludedReasons = []
    excludedIds = []

    # This regexp is given to us from the main program - it'll vary by biomarker type
    regexp = regxp
    gotSomething = False
    text = text + '\n*endAdd*'
    text = text.replace('her-2', 'her2').replace('over expression', 'overexpression').replace('strongly overexpression', 'strongly overexpressed').replace('mib 1', 'mib-1')
    text = text.replace('cep 17', 'centromere 17').replace('pdl-1', 'pd-l1')
    text = text.replace('stain for msi', 'stains for msi')
    text = text.replace('dna analysis for: ', '')

    # I don't want this in, because it just is a preamble to the actual sample nane

    # Test names to take out
    if any(x in text for x in ['\nmicrosatellite instability:\n', 'immunohistochemistry microsatellite instability panel', 'pd-l1 immunohistochemical analysis:',
                               'microsatellite instability testing', 'microsatellite instability (msi) testing', 'ancillary studies: performed - msi']):
        for x in ['\nmicrosatellite instability:\n', 'immunohistochemistry microsatellite instability panel', 'microsatellite instability testing', 'pd-l1 immunohistochemical analysis:',
                  'microsatellite instability (msi) testing', 'ancillary studies: performed - msi']:
            if x in text:
                text = text.replace(x, '')
                removedSections.append(x.replace('\n', ''))
                removedSectionIds.append(repid)

    # EXPERIMENTAL - replace "part a:" with "a."?
    if '\npart' in text:
        text = re.sub(r'(\npart )([a-z])(: )', '\n\\2. ', text)

    # Sometimes we get a lot of 1). 2). - which we'll turn into just 1. 2.
    if text.count(').') > 2:
        for line in text.split('\n'):
            if len(line.split()) > 0:
                if line.split()[0].endswith(').'):
                    lineChange = line.replace(').', '.', 1)
                    text = text.replace(line, lineChange)

    # If we start with a panel, let's add it
    if text.split()[0].endswith(':') and text.split()[0] not in ['tp:']:
        text = 'panel_results\n' + text
        textS = text.split('\n')
        for x in range(0, len(textS)):
            if ':' not in textS[x] and ':' not in textS[x+1]:
                break
        textS.insert(x, 'panel_results_end')
        text = '\n'.join(textS)

    # Common misspellings
    text = text.replace('msh2and', 'msh2 and').replace('mlh1and', 'mlh1 and').replace('stablereported', 'stable reported')
    text = text.replace('gene\ntranscripts', 'gene transcripts').replace('patients\nwith', 'patients with')
    text = text.replace('\\\\t\\\\', '').replace('breast cancer risk assessment  management panel', 'breast cancer risk assessment management panel').replace('\\\\r\\\\', ' ')
    text = text.replace('panelnegative', 'panel negative').replace('positve', 'positive')
    text = text.replace('h. pylori', 'h pylori')
    text = text.replace('will be reported in an\n', 'will be reported in an ').replace('will be reported as an\n', 'will be reported as an ')
    text = text.replace('within normal limits\n', 'within normal limits.\n').replace('reported in an addendum\n', 'reported in an addendum.\n').replace('as an\naddendum.', 'as an addendum.')
    text = text.replace('reported under\nprocedures/addenda', 'reported under procedures/addenda').replace('reported under procedures/addenda', 'reported under procedures & addenda')
    text = text.replace('stain results are as follows.', 'stain results are as follows:').replace('cells\nare positive for', 'cells are positive for')
    text = text.replace('results in the tumor cells: ', 'results: ').replace('results within the tumor:', 'results:').replace('showed the following results\n', 'showed the following results:\n')
    text = text.replace('hormone receptor\nstudies', 'hormone receptor studies').replace('custom hereditary\n', 'custom hereditary ').replace('\nof tumor cells', ' of tumor cells')
    text = text.replace('of\ncells', 'of cells').replace('of\ntumor', 'of tumor').replace('tumor\ncells', 'tumor cells')

    # period-deliniated lists? No, hypen!
    text = text.replace('\n . ', '\n - ').replace('\n. ', '\n- ')

    # These headers we don't need
    while any(x in text.split('\n')[0] for x in ['date ordered:', 'additional immunohistochemical staining', 'addendum comment']):
        text = '\n'.join(text.split('\n')[1:])

    # These are headers that are always redundant - they give no extra new informationz
    if '\nestrogen receptor\n' in text:
        text = text.replace('\nestrogen receptor\n', '\n')
    if '\nprogesterone receptor\n' in text:
        text = text.replace('\nprogesterone receptor\n', '\n')

    if ('addendum' in text or 'procedures/addenda' in text) and 'her2/ neu protein assay (ihc)' in text:
        textSplit = text.split('\n')
        for line in range(0, len(textSplit)-1):
            if 'date ordered:' in textSplit[line+1] and 'assay' not in textSplit[line+1] and any(x in textSplit[line] for x in ['estrogen and progesterone receptor assay',
                                                                                                                              'her2/ neu protein assay (ihc)']):
                textSplit[line] = textSplit[line] + ' ' + textSplit[line+1]
                textSplit[line+1] = ''
        textSplit = list(filter(None, textSplit))
        text = '\n'.join(textSplit)

    # Let's save block info for later


    block = "none"
    if 'separate\nslides' in text:
        text = text.replace('separate\nslides', 'separate slides')
    if any(x in text for x in ['immunohistochemical staining was performed on separate slides', 'immunohistochemical staining is performed on separate slides',\
        'immunohistochemistry study performed with appropriate controls on separate slides', 'immuohistochemical stains were performed on separate unstained slides',
                               'immunohistochemistry was performed at the original institution']):
        if 'separate unstained slides' in text:
            text = text.replace('separate unstained slides', 'separate slides')
        if 'on separate slides' not in text:
            if 'at the original institution' in text:
                block = text[text.index('at the original institution'):]
            else:
                print(text)
                print('WEIRD BLOCK')
                input()
        else:
            block = text[text.index('on separate slides'):]
        if 'following results:' in block:
            block = block[:block.index('following results:')]
        elif 'show tumor cells are' in block:
            block = block[:block.index('show tumor cells are')]
        elif '.' in block:
            block = block[:block.index('.')]
        elif any(x in block for x in ['and showed', 'tumor cells showed', 'and\nshowed', 'which showed']):
            block = block[:block.index('showed')]
        elif ':\n' in block:
            block = block[:block.index(':\n')]
        elif ',' in block:
            block = block[:block.index(',')]
        elif 'and' in block:
            block = block[:block.index('and')]
        elif 'the' in block:
            block = block[:block.index('the')]
        else:
            print(block)
            print('ABERRENT BLOCK!')
            input()
            block = block
        text = text.replace(block, '')
    elif 'immunostains for' in text and 'following results:' in text:
        block = text[text.index('immunostains for'):]
        block = block[:block.index('following results:') + len('following results:')]
        text = text.replace(block, '')
    # First, we're looking for block info that talks about the stains used on a block
    elif 'on separate slides from' in text:
        for sent in re.split((r'(?<!( i|\.e))\.(?![0-9])'), text):
            if sent:
                if 'on separate slides from' in sent:
                    # If there are actually RESULTS, we don't want to delete it!
                    if any(x in sent for x in ['positive', 'negative', 'equivocal', 'showed']):
                        pass
                    else:
                        if ')' in sent:
                            sent = sent[:sent.index(')') + 1]
                        text = text.replace(sent, '')
                        block = sent.replace('\n', ' ').strip()
                    break
    while 'immunohistochemical stains in part' in text:
        block = text[text.index('immunohistochemical stains in part'):]
        block = block[:block.index('.')]
        if any(x in block for x in ['positive', 'negative', 'equivocal']):
            print(block)
            print('POSSIBLY WEIRD BLOCK')
            input()
        if regexp.search(block):
            removedSections.append(block)
            removedSectionIds.append(repid)
        text = text.replace(block, '')

    # I think we need to pick this part out, and possibly save it for determining sample location
    if 'immunostains are performed on separate slides from block' in text:
        sampleIdea = text[text.index('immunostains are performed on separate slides from block'):]
        sampleIdea = sampleIdea[:sampleIdea.index(':')]
        text = text.replace(sampleIdea, '')

    # This is a test name that I want gone
    if 'her2, molecular pathology and genomic test:' in text:
        removedSections.append(text[:text.index('interpretation:')])
        removedSectionIds.append(repid)
        text = text[text.index('interpretation:'):]

    # Don't split up er/pr results
    if '\n estrogen receptor:' in text:
        for x in ['\n estrogen receptor:', '\n progesterone receptor:']:
            if x in text:
                bit = text[text.index(x)+1:]
                if '/8' not in bit:
                    if not any(x in bit for x in ['staining\n', '%)', 'pattern']):
                        print('WEIRDBIT')
                        print(bit)
                        input()
                    else:
                        for x in ['staining\n', '%)', 'pattern']:
                            if x in bit:
                                end = x
                else:
                    end = '/8'
                if end not in bit:
                    bit = bit[:bit.index('.')].replace('\n', ' ')
                else:
                    bit = bit[:bit.index(end)]
                origBit = bit
                bit = bit.replace('\n', ' ')
                text = text.replace(origBit, bit)

    # I make sure to add 'her2' to the results on this test
    if any(x in text for x in ['gastroesophageal biopsy her2/neu summary', 'colorectal adenocarcinoma her2/neu summary', 'gastric biopsy her2/neu summary',
                               'intestinal adenocarcinoma her2/neu summary', 'biopsy her2/neu summary']):
        if 'interpretation:' in text:
            text = text.replace('interpretation: ', 'interpretation: her2 ')
            for x in ['gastroesophageal biopsy her2/neu summary', 'colorectal adenocarcinoma her2/neu summary', 'gastric biopsy her2/neu summary',
                      'intestinal adenocarcinoma her2/neu summary', 'biopsy her2/neu summary']:
                if x in text:
                    text = text.replace(x, '')

    if monitor:
        print('--------')
        print(text)
        print('here!')
        print(fullText)
        input()

    # This is common for some reasons
    if 'mutation (pcr): \n' in text:
        text = text.replace('mutation (pcr): \n - negative -', 'mutation (pcr): negative ')

    # if there are no biomarkers, this will remain false. If it's true, we found at least one result
    hasBiom = False
    # This will be true if we find a samplename that includes our biomarker of interest.
    sampleNameBiomarker = False

    # We don't need the interpretation section!
    if 'i. variant interpretation' in text:
        sect = text[text.index('i. variant interpretation'):]
        if 'report comments ' not in sect:
            if 'risk estimates:' not in sect:
                if '(variant #1)' not in sect:
                    if 'ii.' not in sect:
                        sect = sect
                    else:
                        sect = sect[:sect.index('ii. ')]
                else:
                    sect = text[text.index('(variant #1):'):]
            else:
                sect = sect[:sect.index('risk estimates:')]
        else:
            sect = sect[:sect.index('report comments ')]
        text = text.replace(sect, '')

    # Keep going as long as there's any biomarkers of interest in this section
    while regexp.search(text):
        # This indicates that we did have at least one biomarker in this test.
        # If we don't, we don't mind an empty result!
        # Here, we're ingesting a section (or the whole test) that has one of the biomarkers of interest in it.
        # We'll want to break it into as many component parts as possible, and from there, decide how
        # to segment it. Segments with biomarkers of interest will be extracted.

        text = text.strip()

        # First off, let's see if this section is referencing a particular one of the specimen sites.
        # If this is the case, we can not have the giant specimen list
        specimenSection = sampleL

        if 'additional disease-relevant genes with no reportable alterations identified:' in text:
            textSplit = text.split('\n')
            for z in range(0, len(textSplit)):
                if 'additional disease-relevant genes with no reportable alterations identified:' in textSplit[z]:
                    break
                else:
                    z = z + 1
            z = z + 1
            while len(textSplit[z].split()) == 1:
                textSplit[z] = 'no reportable alterations identified in ' + textSplit[z]
                z = z + 1
            text = '\n'.join(textSplit)

        # Sometimes we have split-up results. This is enough of an elaboration that I handle it under 'specific tests'
        if any(x in text for x in ['results\nnegative', 'no pathogenic mutations,', 'results\npositive', 'no additional pathogenic', 'no other pathogenic', 'results\nvous']):
            # Sometimes the gene list is hidden here
            text = splitUpPanel(text, testtype)
            # These are the explanatory parts of the panels and may have biomarker names we don't want
            if 'target coverage at 50x or higher:' in text:
                textSp = text.split('\n')
                lineN = 0
                while 'target coverage at 50x or higher:' not in textSp[lineN]:
                    lineN = lineN + 1
                lineN = lineN + 1
                section = text[text.index(textSp[lineN]):]
                if 'limitations:' in section:
                    section = section[:section.index('limitations: ')]
                text = text.replace(section, '')
                if regexp.search(section):
                    removedSections.append(section)
                    removedSectionIds.append(repid)

        if not text:
            print(origText)
            print(testtype)
            input()

        # Don't want extra results from the test type
        if testtype in text and regexp.search(testtype):
            text = text.replace(testtype, '')

        # Special removal sections
        if '\ngene exon\n' in text:
            text = text.replace('\ngene exon\n', '\ngene exons \n')
        if '\ngene exons \n' in text:
            lineIndex = text.split('\n').index('gene exons ')
            lineIndex = lineIndex + 1
            while text.split('\n')[lineIndex].split()[-1].isnumeric():
                lineIndex = lineIndex + 1
                if lineIndex > len(text.split('\n')) - 1 or len(text.split('\n')[lineIndex].split()) == 0:
                    break

            equivocalSection = '\n'.join(text.split('\n')[text.split('\n').index('gene exons '):lineIndex])
            text = text.replace(equivocalSection, '')

        # Let's look at removing some sections
        removalSectionStarts = ['breast cancer risk assessment management panel', 'recommendations:', 'next generation sequencing (ngs) provides', 'dna quality: ',
                                'checklist: ', 'a her2 to chromosome 17 centromere ratio greater', 'test description:', 'analyte specific reagent (asr) disclaimer',
                                'methods:', 'the results suggest that', 'a panel of immunohistochemical stains', 'the patient has a disclaimer', 'note: the procedure of',
                                'immunostaining for mmr', 'immunostains were performed', 'cancer predisposition mutation in', 'hereditary breast and ovarian cancer panel',
                                'gross deletions and duplications at each', 'to determine the presence or absence', 'taken together', 'formalin fixed,', 'erbb2 is altered in',
                                'immunohistochemical staining for her2/neu is interpreted ', '(results for invasive carcinoma', 'her2 her2 ihc pattern', 'physician of record',
                                'submitted immunostains', 'era/pra reference range by ihc', 'fluorescent in situ hybridization (fish)', 'name: ', 'this test was developed',
                                'interpretation of pathology language in proper medical context.', 'variant interpretation:', 'slides are also reviewed', 'this\nlaboratory',
                                'note is made', 'this next generation sequencing panel', 'results for other genes included on the', 'reference normal result:', '\nnote: this assay',
                                'the morphology and the immunophenotype', 'amended:', 'among the variants', 'results are delayed for', 'the overall findings',
                                'met del exon14 is a met splice variant', 'patients with', 'differential diagnoses include', 'due to the results', 'this result is ', 'this result is\n'
                                'this analysis included targeted mutation analysis for detection', 'a her2 to d17z1 ratio', 'caution:', 'scoring criteria:', 'this analysis included',
                                'fish testing for n-myc and alk resulted on touch prep slides from', 'tissue is sufficient to perform', 'designate block for future studies:',
                                'refer to appendix for limitation statements', 'limitations: ', 'brca1 and brca2 are genes', 'risk estimates: ', '\nindication for testing: ',
                                '\n molecular genetic studies:', 'comment\nthis is an',
                                'multiple endocrine neoplasia type 2', 'this negative result alone', 'this finding is similar', 'inherited genetic mutations in']

        removalSectionEnds = ['*endAdd*', 'report comments', 'target coverage at 50x or higher:', 'necrosis: ', 'over-expression in breast cancer. ', 'diagnosis of malignancy',
                              'immunohistochemical staining is used', 'demonstrates the', 'staining of these proteins.', 'interpretation of this patient', 'included in this analysis.',
                              'and on separate', 'dab detection kit: \n', 'dab detection kit: ', 'or incisional biopsy)', 'and demonstrate', 'the tumor is', 'or for research.',
                              'breast biomarker testing ', 'following results:', 'immunoperoxidase for her2', 'were scored. ', 'were scored for each probe.', 'karyotype:', '\nprobe.\n',
                              'microscopic description', 'test description:', 'special studies', 'scored for each probe.', 'may be warranted.', 'to confirm the', 'disclaimer:',
                              '\nproduced_panel_results_positive', '\nproduced_panel_results_vous', '\nproduced_panel_results_negative', 'disclaimer:', 'time of sign out):',
                              'separate slides from block', 'testing performed on case number', 'on separate slides for', 'for details', '\ncomment\n',
                              'clinically validated computational data', 'scored for each probe.', 'summary of cytogenetic analysis: ', 'following results:', 'cells retain', 'cell retains']
        while any(section in text for section in removalSectionStarts):
            for section in removalSectionStarts:
                if section in text:
                    removeSection = text[text.index(section):]
                    endPos = 9999999999
                    endChoice = ''
                    for endSec in removalSectionEnds:
                        if endSec in removeSection and removeSection.index(endSec) + len(endSec) < endPos and endSec not in section:
                            endPos = removeSection.index(endSec) + len(endSec)
                            endChoice = endSec
                    if endChoice in ['target coverage at 50x or higher:', 'necrosis: ']:
                        endPos = removeSection[endPos:].index('\n') + endPos
                    removeSection = removeSection[:endPos]
                    # Some things we want to keep
                    if endChoice in ['dab detection kit: \n', 'or incisional biopsy)', 'dab detection kit: ']:
                        text = text.replace(removeSection, ' ')
                    elif endChoice in ['immunoperoxidase for her2', 'karyotype:', 'test description:', 'were scored for each probe.', 'scored for each probe.', 'following results:',
                                       '\nproduced_panel_results_positive', '\nproduced_panel_results_vous', '\nproduced_panel_results_negative', 'time of sign out):']:
                        text = text.replace(removeSection, endChoice)
                    else:
                        text = text.replace(removeSection, '\n')
                    if regexp.search(removeSection):
                        removedSections.append(removeSection)
                        removedSectionIds.append(repid)
                    if monitor:
                        print(removeSection)
                        print('REMOVING')
                        print("THIS IS NOW")
                        print(text)
                        input()

        # if we JUST get a list, add a space in so we can process it
        if text.startswith((' - ', '- ')):
            text = '\n' + text
        karyotype = 'none'
        # Pick out the karyotype if there is one - we'd like that as a result.
        if 'karyotype:' in text:
            karyotype = text[text.index('karyotype:'):]
            if 'interpretation:' not in karyotype:
                if ']' not in karyotype:
                    karyotype = 'none'
                else:
                    karyotype = karyotype[:karyotype.index(']')+1]
            else:
                karyotype = karyotype[:karyotype.index('interpretation:')]
            text = text.replace(karyotype, '')
            karyotype = karyotype.replace('karyotype: \n', 'karyotype: ').replace('\n', '').strip()

        text = text.strip()
        # Now let's see if there are any ways to split it up like a. or b. - EXPERIMENTAL: MOVING ALL THE SPLITS TO THIS REGEX. that's a. a) a:
        if len(re.findall(r'([\n ]+|^)(?=[a-zA-Z0-9](\. |: |\)))', text)) > 1:
            newsubsections = []
            subs = re.split(r'([\n ]+|^)(?=[a-zA-Z0-9](\. |: |\)))', text)
            for s in subs:
                if regexp.search(s):
                    newsubsections.append(s)
            subsections = newsubsections

        # If not experimental put back here

        # Ok, so it's all one thing
        else:
            subsections = [text]

        # These section headers should be the parts that potentially contain test info.
        subsectionheaders = ['\nimmunocytochemical assay (erica):', '\nimmunocytochemical assay (prica):', 'tumor cells are ', ': immunostain for', 'er, pr and her2', 'her2-neu immunostain ',
                             'comment: results from', 'the tumor nuclei retain', 'showed the following results:', 'neoplastic cells retain', 'the tumor cell nuclei retain', 'er and pr and',
                             'report comments', '\ninterpretation\n', 'summary of cytogenetic analysis:', 'interpretation:', 'results:', 'results-comments', 'er and pr immunostains',
                             'control reviewed):','immunohistochemistry for', 'demonstrate the tumor is', 'her2 by immunohistochemistry', 'by immunohistochemistry,', 'addendum diagnosis',
                             'the result is abnormal', 'er and pr,', 'immunostains demonstrate', 'her2 testing', 'her2 are', 'immunohistochemical staining for', '\n - ', '\n- ',
                             'there was no evidence', 'we found evidence of', 'attempts were made', 'were scored for each probe.', 'the result is within normal', 'the neoplastic cell nuclei',
                             'er and pr allred score:', 'microscopic description', 'the tumor cells are', 'the neoplastic cells are', 'panel of immunostains', '\ner ', '\nresult:\n',
                             'were scored.', 'era result (clone', 'shows positive', 'in addition', 'this finding ', 'immunostains:', 'additional markers', 'interpretation',
                             'this test was developed', 'prognostic markers:', 'addendum comment', 'these results', '\naddendum\n', 'special studies', 'stain results are as follows:',
                             'procedures/addenda', 'positive: ', '\nnegative: ', 'her2 will', 'immunostaining for', 'the number of', '\n variant histology:', 'found to be satisfactory.',
                             'her2 immunostaining', 'scored for each probe.\n', 'cells were scored.\n', 'the following immunoperoxidase stains', 'estrogen receptor (er):',
                             'progesterone receptor (pgr):', 'the spindle cells are', 'per original pathology report', 'microsatellite and her2/neu', 'microsatellite immunohistochemical',
                             'microsatellite instability by immunohistochemical staining', 'immunohistochemical staining', 'mismatch repair protein expression:', 'stains for msi',
                             '\ner and pr immunostains for', 'immunostains for', 'were reviewed', 'the cells are positive for', '\n estrogen receptor', 'adequate controls.',
                             'show tumor cells are', 'the cells are diffusely', '\n tumor necrosis:', 'immunohistochemical staining was performed', 'spaces are positive',
                             'her2/neu immunohistochemical stain ', 'her2/neu immunohistochemical stain:', 'p40 immunostain', '\nmlh1: ', 'msi and her2/neu', 'msi markers', 'msi testing',
                             'immunohistochemistry (ihc) results for mismatch repair (mmr) proteins: ', 'microsatellite stable', 'msi stains', 'mismatch repair protein expression',
                             'the biopsy specimen is', '\nnegative for', ' this laboratory is', 'demonstrate the presence of', 'the tumor nuclei show', 'glioma panel', 'an attempt was made',
                             'insufficient tissue is present', 'we will not be performing', 'the tumor demonstrates', 'the results are abnormal', 'produced_panel_results_positive\n',
                             'produced_panel_results_vous\n','produced_panel_results_negative\n', 'cytogenetic analysis revealed', 'comment:', 'hormone receptor studies',
                             'hormone receptor immunohistochemical stains', 'her2 immunohistochemical assay', 'her2/neu expression status:', 'this is an', 'the aspirate',
                             'panel_results', 'controls stain appropriately.',
                             ]
        # '*endAdd*' should always be last
        subsectionenders = ['\n---', 'results:', '*endAdd*', 'results-comments', 'addendum comment', 'immunostains are performed on separate slides.', 'as an addendum.', 'as addenda.'
                            'icd code(s):', 'in an addendum.', 'immunohistochemical staining', 'gross description', 'immunostains for', 'the number of', 'these immunostaining results',
                            'interpretation:', 'er and pr allred score:', '\ndue to the results', 'this laboratory is', 'these results are consistent', '\n number of cores',
                            'following results:', 'diagnosis of malignancy', 'fluorescent in situ hybridization (fish) was performed', 'slides from a paraffin', 'time of sign out):',
                            'end_panel_results_positive', 'end_panel_results_vous','end_panel_results_negative', 'note: this assay', 'high probability of', 'panel_results_end',]

        newsubsections = []
        newLocations = []
        thisLocation = []
        # If we don't have any biomarkers after removing sections, just move on!
        if regexp.search(' '.join(subsections)):
            hasBiom = True
        for sub in subsections:
            subsectionLocation = ''
            # Let's see if it starts with a description of the sample
            if re.search(r'([\n ]+|^)(?=[a-zA-Z0-9][\.:] )', sub):
                sampleName = sub[re.search(r'([\n ]+|^)(?=[a-zA-Z0-9][\.:] )', sub).start():]
                endPuncPos = 999999
                # We're going to see if we can get some punctuation indicating that we have a sample name (like ending with : or .)
                # If we can't find those, it's probably just a. or b.
                goodCandidate = False
                if any(p in sampleName for p in [': \n', ':\n', '.\n', '. \n']):
                    for endPunc in [': \n', '.\n', ':\n', '.\n', '. \n']:
                        if endPunc in sampleName:
                            if sampleName.index(endPunc) < endPuncPos:
                                endPuncPos = sampleName.index(endPunc) + 1
                                if len(sampleName[:endPuncPos].strip().split('\n')) < 3:
                                    goodCandidate = True
                                    if regexp.search(sampleName[:endPuncPos].strip()):
                                        goodCandidate = False
                if not goodCandidate:
                    if '. ' in sampleName:
                        endPuncPos = sampleName.index('. ') + 1
                if any(x in sampleName for x in [': \n', ':\n', '.\n', '. ']):
                    sampleName = sampleName[:endPuncPos].strip()
                    if not any(y in sampleName for y in ['no coding variants']):
                        newSub = sub.replace(sampleName, '')
                        subsections[subsections.index(sub)] = newSub
                        sub = newSub
                        text = text.replace(sampleName, '')
                        removedSections.append(sampleName)
                        removedSectionIds.append(repid)
                        # and if that was it for the sample...
                        if not regexp.search(' '.join(subsections)):
                            hasBiom = False
                        subsectionLocation = sampleName
                else:
                    if re.search(r'[a-z][\.:] ', sampleName):
                        subsectionLocation = sampleName.strip()
                    else:
                        print(sampleName)
                        print(text)
                        print('sample with no token')
                        input()

            else:
                # if we have to use the original sample location, let's see if it needs to be split up
                if len(re.findall(r'([\n ]+|^)(?=[a-zA-Z0-9][\.:] )', sampleLOrig)) > 1:
                    locList = re.split(r'([\n ]+|^)(?=[a-zA-Z0-9][\.:] )', sampleLOrig)
                    locList = list(filter(None, locList))
                else:
                    locList = [sampleLOrig]
                for l in locList:
                    if l != '\n':
                        subsectionLocation = subsectionLocation + ' . . ' + l

            textSplit = []
            # REPLACE HYPHEN HERE?

            if sub.split('\n')[0] == ':':
                sub = '\n'.join(sub.split('\n')[1:])

            # If we don't have any sub-sections, then the whole thing is one item on the list
            if (not any(st in sub for st in subsectionheaders) and not any(nd in sub.replace('*endAdd*', '').replace('-','') for nd in subsectionenders)) and textSplit == []:
                panelChoices = ['positive', 'negative', 'equivocal', 'positivity', 'wild-type', '%', 'abnormal', 'lost', 'highlights', 'intact', 'wild type', 'staining', 'n/a',
                                'overexpression', 'weak', 'patchyx', 'probe signals', 'staining', 'higher']
                # We might just have a results panel
                if len(sub.split('\n')) > 2:
                    if any(x in sub.split('\n')[0] for x in panelChoices) and any(x in sub.split('\n')[1] for x in panelChoices) and sub.split('\n')[0].count('.') < 2:
                        panelResultsOrig = []
                        panelResults = []
                        subz = sub.split('\n')
                        start = 0
                        while any(x in subz[start] for x in panelChoices) or (').' not in subz[start-1] and ').' in subz[start]) or len(subz[start].split()) <= 2 or subz[start].split()[0].endswith(','):
                            while not any(x in subz[start] for x in panelChoices) or subz[start].split()[0].endswith(','):
                                if start == len(subz) - 1:
                                    break
                                if not any(x in subz[start + 1] for x in panelChoices) and (any(x in subz[start + 1] for x in panelChoices) or len(subz[start+1].split()) <= 2):
                                    panelResults[-1] = panelResults[-1] + ' ' + subz[start]
                                    panelResultsOrig.append(subz[start])
                                    if start == len(subz) - 1:
                                        break
                                    start = start + 1
                                else:
                                    break
                            panelResults.append(subz[start])
                            panelResultsOrig.append(subz[start])
                            if start == len(subz) - 1:
                                break
                            start = start + 1
                        sec = '\n'.join(panelResults)
                        secOrig = '\n'.join(panelResultsOrig)
                        text = text.replace(secOrig, '')
                        sub = sec
                textSplit = [sub]

            # This should get rid of any stragglers - if we have a sample name with the biomarker of interest in it, for instance
            elif (sum(x in sub.replace('*endAdd*', '') for x in subsectionheaders) == sum(x in sub.replace('*endAdd*', '') for x in subsectionenders) == 1):
                textSplit = [sub]

            # Otherwise, if we only have headers or only have enders, just split on those.
            elif (not any(st in sub for st in subsectionheaders)):
                for st in subsectionenders:
                    if st in sub:
                        if st in ['in an addendum.', 'as an addendum.', 'immunohistochemical staining', 'due to the results', 'note: this assay', 'high probability of',
                                  'diagnosis of malignancy',  'time of sign out):']:
                            if st == 'time of sign out):':
                                st = 'time of sign out\):'
                                reString = '(?<=' + st + ')(\n)+'
                            else:
                                reString = '(?<=' + st + ')( )+'
                            reString = re.compile(reString)
                            textSplit = re.split(reString, sub)
            # Otherwise, we'll split all the sections that have results into their own snug section
            else:
                while any(x in sub for x in subsectionheaders):
                    # When there's one string, and it's both a starter and an ender...
                    if sum(x in sub for x in subsectionheaders) == sum(y in sub for y in subsectionenders) == 1:
                        textSplit.append(sub)
                        sub = ''

                    if monitor:
                        print('===============')
                        print(sub)
                        print('STILL HAS')
                        print('===============')
                        for x in subsectionheaders:
                            if x in sub:
                                print(x)
                        print('===============')
                        print('AND ENDERS')
                        for x in subsectionenders:
                            if x in sub:
                                print(x)
                        print('===============')
                        input()
                    for x in subsectionheaders:
                        if x in sub:
                            # This is for if we have multiple of one header and that's it
                            if not any(y in sub.replace(x, '') for y in subsectionenders):
                                bitOrig = sub
                                bit = sub.split(x)
                            bitOrig = sub[sub.index(x):]
                            # Some headers we want to keep in
                            if x in ['era result (clone', 'her2 will', 'immunostains for', 'immunostaining for', 'the number of', 'her2 immunostaining', 'her2 testing', 'her2 are',
                                     'the result is abnormal', 'er and pr,', 'immunohistochemistry for', 'her2 by immunohistochemistry', 'stain results are as follows:', 'msi stains',
                                     'er and pr immunostains', 'additional markers', 'er, pr and her2', 'estrogen receptor (er):', 'progesterone receptor (pgr):', '\ner', '\nmlh1: ',
                                     '\n estrogen receptor (er):', '\ner and pr immunostains for', 'positive: ', '\nnegative: ', 'the cells are positive for', '\n estrogen receptor:',
                                     'her2-neu immunostain ', 'her2/neu immunohistochemical stain', 'p40 immunostain', 'her2/neu immunohistochemical stain ', 'microsatellite stable',
                                     'stains for msi', 'msi testing',  'there was no evidence', 'negative for', 'we found evidence of', 'demonstrate the presence of', 'the tumor demonstrates',
                                     'the tumor nuclei retain', 'following results:', 'tumor cell nuclei retain', 'neoplastic cells retain', 'the tumor cell nuclei retain', 'this is an',
                                     'the neoplastic cell nuclei', 'produced_panel_results_positive\n', 'produced_panel_results_vous\n', 'produced_panel_results_negative\n',
                                     'her2/neu immunohistochemical stain:', 'microsatellite immunohistochemical', 'microsatellite instability by immunohistochemical staining',
                                     'the aspirate', 'panel_results'
                                     'cytogenetic analysis revealed', 'er and pr and', 'her2 immunohistochemical assay', 'her2/neu expression status:', 'high probability of']:
                                bit = sub[sub.index(x):]
                            # Some we don't want, but we ALSO want to delete from the text (so that they aren't picked up in later scans
                            elif x in ['er and pr allred score:']:
                                bit = sub[sub.index(x) + len(x):]
                                text = text.replace(x, '', 1)
                                bitSplit = bit.split('\n')
                                for bitline in range(0, len(bitSplit)):
                                    if ('(proportion') in bitSplit[bitline]:
                                        text = text.replace(bitSplit[bitline], '\n')
                                        bitSplit[bitline] = bitSplit[bitline][:bitSplit[bitline].index('(proportion')]
                                    if 'allred score: %' in bitSplit[bitline]:
                                        break
                                bitSplit = list(filter(None, bitSplit))
                                bit = '\n'.join(bitSplit[0:bitline-1])
                            # This is a test split up between multiple lines. Let's concatenate them!
                            elif x in ['\nimmunocytochemical assay (erica):', '\nimmunocytochemical assay (prica):']:
                                bit = sub[sub.index(x):]
                                bitSplit = bit.split('\n')
                                activeLine = 2
                                if 'percent positive' not in bitSplit[activeLine]:
                                    print('ODD SECTION FOR ASSAY 1')
                                    print(bit)
                                    print(bitSplit[activeLine])
                                    input()
                                activeLine = activeLine + 1
                                if 'intensity' not in bitSplit[activeLine]:
                                    print('ODD SECTION FOR ASSAY 2')
                                    print(bit)
                                    print(bitSplit[activeLine])
                                    input()
                                bitOrig = '\n'.join(bitSplit[1:activeLine+1])
                                bit = ' '.join(bitSplit[1:activeLine+1])
                                if x == '\nimmunocytochemical assay (erica):':
                                    bit = bit.replace('immunocytochemical assay', 'estrogen receptor')
                                else:
                                    bit = bit.replace('immunocytochemical assay', 'progesterone receptor')
                                bit = bit.replace('percent positive: ', ' ')
                                sub = sub.replace(bitOrig, '')

                            else:
                                bit = sub[sub.index(x) + len(x):]
                            endPos = 9999999999
                            endChoice = ''
                            if not any(y in bit for y in subsectionenders):
                                bit = bit
                            # If there's only one 'ender', and it's the same as the header, take the whole chunk.
                            elif sum(y in bit.replace(x, '') for y in subsectionenders) == 0:
                                bit = bit
                            else:
                                for endSec in subsectionenders:
                                    if endSec in bit and bit.index(endSec) < endPos and endSec not in x:
                                        endPos = bit.index(endSec)
                                        endChoice = endSec
                                bit = bit[:bit.index(endChoice)]
                                if endChoice in ['in an addendum.', 'as an addendum.']:
                                    bit = bit + endChoice

                                if x in ['\nblock'] and 'block' not in bit:
                                    bit = 'block' + bit
                                bitOrig = bitOrig[:bitOrig.index(endChoice)]
                                if endChoice in ['in an addendum.', 'as an addendum.']:
                                    bitOrig = bitOrig + endChoice
                            if monitor:
                                print(x)
                                print(endChoice)
                                print('SNIP OUT!')
                                print(bit)
                                input()
                            # If we start with a location, we want to split it here
                            if len(bit.split()) > 0:
                                if re.findall(r'( |^)[a-z][\.:]', bit.split()[0].replace('h.pylori', '')):
                                    enders = [')\n', '. \n', '.\n', '\nnuc ish', '.nuc', ') \n', ')nuc', '):\n']
                                    endLoc = 999999999999
                                    if not any(x in bit for x in enders):
                                        if bit.split()[0].endswith(('.', ':')):
                                            endLoc = bit.index(' ') - 1
                                        else:
                                            print(bit)
                                            print('ODD SAMPLE')
                                            input()
                                    else:
                                        for end in enders:
                                            if end in bit:
                                                if bit.index(end) < endLoc:
                                                    endLoc = bit.index(end)
                                    end = endLoc + 2
                                    if bit[:end].endswith('\nn'):
                                        end = end - 2
                                    thisLocation.append(bit[:end])
                                    bit = bit[endLoc + 2:]
                            textSplit.append(bit.strip())

                            sub = sub.replace(bitOrig, '', 1)
                            text = text.replace(bitOrig, '', 1)
                            if monitor:
                                print('===============')
                                print(textSplit)
                                print('================')
                                print('IS NOW')
                                print(sub)
                                input()

                            # If we don't have any sub-sections, then the whole thing is one item on the list
                            if (not any(st in sub for st in subsectionheaders) and not any(nd in sub.replace('*endAdd*', '').replace('-', '') for nd in subsectionenders)):
                                panelChoices = ['positive', 'negative', 'equivocal', 'positivity', 'wild-type', '%', 'abnormal', 'lost', 'highlights', 'intact', 'wild type', 'staining',
                                                'overexpression', 'weak', 'patchy']
                                # We might just have a results panel
                                if len(sub.split('\n')) > 2:
                                    if any(x in sub.split('\n')[0] for x in panelChoices) and any(x in sub.split('\n')[1] for x in panelChoices):
                                        panelResults = []
                                        panelResultsOrig = []
                                        subz = sub.split('\n')
                                        start = 0
                                        while any(x in subz[start] for x in panelChoices) or (').' not in subz[start - 1] and ').' in subz[start]) or len(subz[start].split()) <= 2 or subz[start].split()[
                                            0].endswith(','):
                                            while not any(x in subz[start] for x in panelChoices) or subz[start].split()[0].endswith(','):
                                                if start == len(subz) - 1:
                                                    break
                                                if not any(x in subz[start + 1] for x in panelChoices) and (any(x in subz[start + 1] for x in panelChoices) or len(subz[start + 1].split()) <= 2):
                                                    panelResults[-1] = panelResults[-1] + ' ' + subz[start]
                                                    panelResultsOrig.append(subz[start])
                                                    if start == len(subz) - 1:
                                                        break
                                                    start = start + 1
                                                else:
                                                    break
                                            panelResults.append(subz[start])
                                            panelResultsOrig.append(subz[start])
                                            if start == len(subz) - 1:
                                                break
                                            start = start + 1
                                        sec = '\n'.join(panelResults)
                                        secOrig = '\n'.join(panelResultsOrig)
                                        text = text.replace(secOrig, '')
                                        sub = sec
                                    textSplit.append(sub)
                                # This is a short snippet that we might just add
                                else:
                                    if regexp.search(sub):
                                        textSplit.append(sub)

                            # If we have any headers, we'll keep looping, so we only need to handle if we have no headers OR enders, or jsut no headers. This section handles
                            # JUST no headers.
                            elif (not any(st in sub for st in subsectionheaders)):
                                if regexp.search(sub):
                                    textSplit.append(sub)

                # Here, we've extracted all the sections we know about. Let's add anything to 'removed sections' if it still has a biomarker of interest,
                # for later review
                if regexp.search(sub):
                    # We want to take it if it's one of the a) b) c) groups
                    if sub[1] in [')', '.', '-', ' ']:
                        removedSections.append(sub)
                        removedSectionIds.append(repid)
                        text = text.replace(sub, '')
            # At this point, we should have either a list of sections, or just one section, as the only item in a list.
            # For each place in this list, we're going to figure out how to break things up.
            for section in textSplit:
                # if no match, just push on
                if not (regexp.search(section) or 'nuc ish' in section):
                    if monitor:
                        print("DIDN'T FIND A BIOMARKER IN")
                        print(section)
                        print('')
                    continue

                # sectionOrig is going to be to replace this in the main body of text later
                sectionOrig = section
                section = section.strip()

                # First, let's see about splitting up by paragraph. Not for SURE that we'll want this.
                if '\n\n' in section:
                    inners = section.split('\n\n')
                    inners = list(filter(None, inners))

                else:
                    inners = [section]

                # Don't split nuc ishs by line
                for inner in inners:
                    if 'nuc ish' in inner:
                        nucBit = inner[inner.index('nuc ish'):]
                        if '\n' in nucBit and ']' in nucBit:
                            nucOrig = nucBit
                            while nucBit.index('\n') < nucBit.index(']'):
                                nucBit = nucBit.replace('\n', ' ', 1)
                                if not '\n' in nucBit:
                                    break
                            inners[inners.index(inner)] = nucBit
                            text = text.replace(nucOrig, nucBit)

                if monitor:
                    print('--------')
                    print(inners)
                    print(textSplit)
                    print('here with inners!')
                    input()

                # Remove extraneous bits
                for x in ['\n*endAdd*', '*endAdd*']:
                    if x in inners:
                        inners.remove(x)

                # If we had more than one subsection, that SHOULD mean that we have putative results that should be applied to all
                # sample locations, right?
                if '. .' in subsectionLocation:
                    subsectionLocation = subsectionLocation.split(' . . ')
                if not isinstance(subsectionLocation, list):
                    subsectionLocation = [subsectionLocation]
                subsectionLocation = list(filter(None, subsectionLocation))

                for inner in inners:
                    if thisLocation == []:
                        if subsectionLocation == []:
                            print(sampleLOrig)
                            input()

                        if len(subsectionLocation[0].replace(' ', '').replace('.', '')) == 1:
                            appended = False
                            locationLetter = subsectionLocation[0].replace(' ', '').replace('.', '')
                            sampleSplit = re.split(r'(^| |\n)(?=[a-z]: )', sampleLOrig)
                            for s in sampleSplit:
                                if s.startswith(locationLetter):
                                    appended = True
                                    newLocations.append(s.replace('\n', ' '))
                            if not appended:
                                newLocations.append(sampleLOrig)
                        else:
                            newLocations.append(', '.join(subsectionLocation).replace('\n', ' '))
                    elif len(thisLocation) == 1:
                        locationLetter = thisLocation[0].replace('\n', ' ').strip()
                        locationLetter = locationLetter[0]
                        appended = False
                        for item in subsectionLocation:
                            if item.startswith(locationLetter):
                                appended = True
                                newLocations.append(item)
                        if not appended:
                            sampleSplit = re.split(r'(^| |\n)(?=[a-z]: )', sampleLOrig)
                            for s in sampleSplit:
                                if s.startswith(locationLetter):
                                    appended = True
                                    newLocations.append(s)
                        if not appended:
                            newLocations.append(thisLocation[0])

                    else:
                        print(thisLocation)
                        print(subsectionLocation)
                        print(inner)
                        input()

                    newsubsections.append(inner)

                    if newLocations == []:
                        print(subsections)
                        print(subsectionLocation)
                        print(sampleLOrig)
                        print(thisLocation)
                        print('empty location!')
                        input()

        subsections = newsubsections
        thisLocation = newLocations
        if len(subsections) != len(thisLocation):
            print(subsections)
            print(subsectionLocation)
            print(sampleLOrig)
            print(thisLocation)
            input()
        newSections = []
        newLocations = []

        ##############################################
        ##############################################
        # At this point, we have all the sections we want to divide up for results. Let's dig in!
        ##############################################
        ##############################################
        for subsection in subsections:
            subInd = subsections.index(subsection)
            subLoc = thisLocation[subInd]
            if monitor:
                print(subsection)
                print('GOING TO ANALYZE THIS')
                input()
            subsectionOrig = subsection
            newsub = subsection.replace('\n', ' ').replace('*endAdd*', '')

            if 'positive:' in subsection and 'negative:' in subsection:
                subsection = subsection.replace('negative:', '. negative:')

            if '; negative for' in subsection:
                subsection = subsection.replace('; negative for', '. negative for')


            # We might want to combine some lines
            if (any(x in subsection for x in ['\ner expression status:', '\nper expression status:'])):
                subsectionS = subsection.split('\n')
                newSub = []
                # We might have a bit that doesn't have these lines that might need combining
                if 'additional pathologic findings: ---' in subsectionS:
                    findingsPart = subsectionS[subsectionS.index('additional pathologic findings: ---'):]
                    nonfindingsPart = subsectionS[:subsectionS.index('additional pathologic findings: ---')]
                    for line in nonfindingsPart:
                        newSub.append(line)
                    subsectionS = findingsPart
                for line in subsectionS:
                    print(subsectionS)
                    if ':' in line or ' - ' in line:
                        newSub.append(line)
                    else:
                        newSub[-1] = newSub[-1] + ' ' + line
                newS = '\n'.join(newSub)
                text = text.replace(subsection, newS)
                subsection = newS

            if sum((x.startswith('- ') or x.startswith(' - ')) for x in subsection.split('\n')) > 2:
                for sent in re.split(r'(\n|^)(- | - )', subsection):
                    if isinstance(sent, str):
                        # We here sometimes have extraneous information after a semi-colon
                        senSplit = sent.split('.')
                        for sen in senSplit:
                            if regexp.search(sen):
                                newSections.append(sen.replace('\n', ' '))
                                newLocations.append(subLoc)
                            else:
                                removedSections.append(sen)
                                removedSectionIds.append(repid)


            # Certain phrases indicate sentence breakups
            elif (any(x in subsection for x in ['the tumor cells are positive', 'in an addendum.', 'as an addendum.', 'her2/neu (ihc):', 'her2-neu (ihc):', 'er and pr immunostains',
                                             'this is an', 'the aspirate', 'i.e., ', '. there is',
                                             'and negative for', 'supporting the above diagnosis.', '. negative stains', '. negative for', 'positive for', '. the findings',
                                              'immunostains).', 'negative:', 'n/a', 'notified of diagnosis', 'intact.', 'cytogenetic analysis', 'is indicated.'])\
                    and not any(x in subsection for x in ['calcifications:', '\ner expression status:', '\n estrogen receptor (er) status:', '\nnegative: ', '\n - negative: ',
                                                          '\n idh1/2: ']))\
                    or subsection.startswith(('positive:')):
                if audit:
                    print('split by firstline word - sentences')
                subsection = subsection.replace('\n', ' ')
                if any(y in subsection for y in ['and negative for']):
                    subsection = subsection.replace('and negative for', ' . . negative for')
                # this is a negative lookahed - so no periods immediately followed by a number, and no i.e.s
                for sent in re.split((r'(?<!( i|\.e))\.(?![0-9])'), subsection):
                    if isinstance(sent, str):
                        # We here sometimes have extraneous information after a semi-colon
                        if any(y in sent for y in ['i.e.,']):
                            if ';' in sent:
                                sent = sent[:sent.index(';')]
                        if regexp.search(sent):
                            newSections.append(sent)
                            newLocations.append(subLoc)
                        else:
                            removedSections.append(sent)
                            removedSectionIds.append(repid)

            # If it's a section talking about tumor stuff, then probably also newline (also including some other markers of newline splits
            elif any(x in subsection for x in ['\ncalcifications:', '\nchecklist:', '\npathologic stage', '\ner expression status:', '\n estrogen receptor (er) status:', '\n. er',
                                             'estrogen receptor score:', 'comment: repeat er', 'era result (clone', '\ner - ', 'reported: pending  estrogen', '\n calcifications:',
                                            '\nno reportable alterations identified in', 'estrogen receptor (er):', '\nthese immunohistochemical features support', '\ner negative\n',
                                            'er positive\n', '\nmlh1:', '\nmsi  ms-stable', 'msi stains', '\n idh1/2:', '\n egfrviii mutation:', '\n brca1 mutation',
                                            'produced_panel_results_positive', 'produced_panel_results_vous', 'produced_panel_results_negative', '\nepcam (ber-ep4):',
                                            'panel_results', '\nmib1 (ki-67 proliferation index)', '\nki67 score -', '\nmib-1 ', 'mib1 marks', '\nmib-1: '
                                            '\ner positive, ', '\ner negative, ', '- estrogen receptor:', '\n estrogen receptor', '\n - ', '\n egfr:', '\ngenomic alterations identified',
                                               ]) or subsection.startswith(('nuc ish')):
                if audit:
                    print('split by firstline word')
                # don't split up parens with newlines
                for m in re.finditer('\(', subsection):
                    sec = subsection[m.start():]
                    secOrig = sec
                    if '\n' in sec and ')' in sec:
                        while sec.index('\n') < sec.index(')'):
                            sec = sec[:sec.index('\n')] + ' ' + sec[sec.index('\n') + 1:]
                            if '\n' not in sec:
                                break
                        subsection = subsection.replace(secOrig, sec)
                newsub = subsection.split('\n')
                addNext = False
                for sub in newsub:
                    if addNext:
                        newSections[-1] = newSections[-1] + ' ' + sub
                        if '(clone' not in newSections[-1] or '%' in newSections[-1]:
                            addNext = False
                    if regexp.search(sub) or sub.startswith('nuc ish'):
                        if '(proportion' in sub:
                            sub = sub[:sub.index('(proportion')]
                        if sub.endswith(('will be')) or '(clone' in sub and '%' not in sub:
                            addNext = True
                        newSections.append(sub)
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(sub)
                        removedSectionIds.append(repid)
            # If we find a bunch of newlines then dashes then newlines, that's how it's split
            elif len(re.findall(r'(?<=\n)( )?(-)', subsection)) > 2:
                if audit:
                    print('split by line then dash')
                newsub = re.split(r'(?<=\n)( )?(-)', subsection)
                for sub in range(0, len(newsub)):
                    if not newsub[sub]:
                        continue
                    if regexp.search(newsub[sub]) or newsub[sub].startswith('nuc ish'):
                        if 'notes:' in newsub[sub]:
                            newsub[sub] = newsub[sub][:newsub[sub].index('notes:')]
                        newsub[sub] = newsub[sub].replace(' - ', '')
                        newSections.append(newsub[sub].replace('\n', ' '))
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(newsub[sub])
                        removedSectionIds.append(repid)

            # If we find a bunch of periods ending in newlines, probably split by newline?
            elif len(re.findall(r'.\.([\n]|$)', subsection)) > 2:
                if audit:
                    print('split by period ending in newline')
                newsub = subsection.split('\n')
                for sub in newsub:
                    if regexp.search(sub) or sub.startswith('nuc ish'):
                        newSections.append(sub)
                        newLocations.append(subLoc)
                    elif '%' in sub:
                        if '%' in sub.split()[0] and len(newSections) > 0:
                            newSections[-1] = newSections[-1] + ' ' + sub.split()[0]
                        else:
                            removedSections.append(sub)
                            removedSectionIds.append(repid)
                    else:
                        removedSections.append(sub)
                        removedSectionIds.append(repid)

            # Sometimes we want to full section
            elif any(x in subsection for x in ['there was no evidence']):
                if audit:
                    print('Split by testing chunk')
                newsub = subsection.replace('\n', ' ')
                if regexp.search(newsub):
                    newSections.append(newsub)
                    newLocations.append(subLoc)

            # If we find a bunch of newlines where the first word ends with ':', good bet it's newline split
            elif len(re.findall(r'(\n)( )?(\S)+:', subsection)) >= 2:
                if audit:
                    print('split by first word colon')
                newsub = subsection.split('\n')
                for sub in newsub:
                    if regexp.search(sub) or sub.startswith('nuc ish'):
                        newSections.append(sub)
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(sub)
                        removedSectionIds.append(repid)

            # Ok, let's see how common this is
            elif 'stain results are as follows:' in newsub:
                newsub = subsection
                if audit:
                    print('split by "stain results are as follows"')
                # It's either split by "er: [result] pr: [result]" or by line
                if ':' in newsub[newsub.index('as follows:') + len('as follows:'):]:
                    newsub = re.split(r'\n(?=[^:\n]+:)', newsub)
                else:
                    newsub = subsection.split('\n')

                for sub in range(0, len(newsub)):
                    if regexp.search(newsub[sub]):
                        newSections.append((newsub[sub]).replace('\n', ' '))
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(newsub[sub].replace('\n', ' '))
                        removedSectionIds.append(repid)


            # If we find a bunch of internal periods, probably split by period?
            elif len(re.findall(r'(\S)+\.(([ \n])+|$)', newsub.replace('dr.', 'dr'))) >= 2:
                if audit:
                    print('split by a bunch of internal periods')
                # Unless they're all 'dr.' or decimals
                newsub = re.split((r'(?<![0-9])\.(?![0-9])(([ \n])+|$)'), newsub.replace('dr.', 'dr'))
                newsub = list(filter(None, newsub))
                for sub in newsub:
                    if regexp.search(sub):
                        newSections.append(sub)
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(sub)
                        removedSectionIds.append(repid)

            # Lack of periods and a number of colons? Colon-deliniated!
            elif len(re.findall(r'\.', newsub)) < 2 and len(re.findall(r':', newsub)) > 2:
                if audit:
                    print('split by no periods and internal colons')
                newsub = re.split(r':', newsub)
                for sub in newsub:
                    if regexp.search(sub):
                        newSections.append(sub.replace('\n', ' '))
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(sub)
                        removedSectionIds.append(repid)

            # As kind of a last chance, let's see if we can split by commas - make sure this doesn't split up lists!
            elif len(re.findall(r',', newsub)) > 2 and not any(x in newsub for x in ['were detected', 'nuclear expression', 'in situ hybridization (fish or cish)',
                                                                                     'normal expression', 'loss of', 'coding variants', 'risk test']):
                if audit:
                    print('split by commas')
                newsub = re.split(r',', newsub)
                for sub in newsub:
                    if regexp.search(sub):
                        newSections.append(sub.replace('\n', ' '))
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(sub)
                        removedSectionIds.append(repid)

            # If it's just a snippet, then we'll just add it
            elif len(re.findall('\.', subsection)) == 1 and subsection.endswith('.'):
                if audit:
                    print('split by snippet')
                # Unless it's long!
                longform = subsection.replace('\n', ' ')
                if 'with antibodies against' in longform:
                    newsub1 = longform[longform.index('with antibodies against') + len('with antibodies against'):]
                    newsub2 = newsub1[newsub1.index(':'):]
                    if ';' in newsub2:
                        newsub2 = newsub2[:newsub2.index(';')]
                    if 'is prepared' in newsub1:
                        newsub1 = newsub1[:newsub1.index('is prepared')]
                    if 'obtained on' in newsub1:
                        newsub1 = newsub1[:newsub1.index('obtained on')]
                    newsub = newsub1 + newsub2
                    subsection = newsub

                if regexp.search(subsection):
                    newSections.append(subsection.replace('\n', ' '))
                    newLocations.append(subLoc)
                else:
                    removedSections.append(subsection)
                    removedSectionIds.append(repid)
            elif '\n' in subsection and len(subsection.split('\n')) == 2:
                if audit:
                    print('split as two-lengther')
                if 'expression' in subsection.split('\n')[0] and not any(x in subsection.split('\n')[0] for x in ['overexpression', 'wild type', 'by immunohistochemistry']) \
                        and regexp.search(subsection.split('\n')[1]):
                    subs = subsection.replace('\n', ' ')
                # This is for two-line pd-l1 tests
                elif 'expression by immunohistochemistry:' in subsection.split('\n')[0] and any(y in subsection.split('\n')[1] for y in ['combined', 'tumor positive']):
                    subs = [subsection.split('\n')[1]]
                elif any(x in subsection.split('\n')[1] for x in ['mismatch repair', 'clinical panel\nnegative:']):
                    subs = subsection.repalce('\n', ' ')
                else:
                    subs = subsection.split('\n')
                if isinstance(subs, str):
                    subs = [subs]
                for s in subs:
                    if regexp.search(s):
                        newSections.append(s)
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(s)
                        removedSectionIds.append(repid)

            elif sum(x.endswith(('negative', 'positive')) for x in subsection.split('\n')) > len(subsection.split('\n')) - 2:
                if audit:
                    print('split by just results section!')
                subs = subsection.split('\n')
                for s in subs:
                    if regexp.search(s):
                        newSections.append(s)
                        newLocations.append(subLoc)
                    else:
                        removedSections.append(s)
                        removedSectionIds.append(repid)

            else:
                if audit:
                    print('no split!')
                if newsub.replace(' ', '') and regexp.search(newsub):
                    newSections.append(newsub)
                    newLocations.append(subLoc)

            # I THINK this is the right substitution here. Change if not
            if monitor:
                print('out of')
                print(text)
            text = text.replace(subsectionOrig, '')
            if monitor:
                print('replaced')
                print('-------------')
                print(subsectionOrig)
                print('-------------')
                print(text)
                print('================')
                print(re.findall(regexp, text))
                input()

        newSections = list(filter(None, newSections))
        subsections = newSections
        thisLocation = newLocations

        # For now, let's separate out previous studies
        for s in subsections:
            if any(x in s for x in ['previous']):
                excludedSections.append(s)
                excludedReasons.append('previous results')
                excludedIds.append(repid)
                thisLocation.remove(thisLocation[subsections.index(s)])
                subsections.remove(s)
            if any(x in s for x in ['is indicated', 'additional work-up', 'is recommended', 'may be considered', 'would also exclude', 'should be considered']):
                excludedSections.append(s)
                excludedReasons.append('recommendation for testing')
                excludedIds.append(repid)
                thisLocation.remove(thisLocation[subsections.index(s)])
                subsections.remove(s)
            if any(x in s for x in ['custom hereditary', 'molecular pathology and genomic test']):
                excludedSections.append(s)
                excludedReasons.append('test/sample name')
                excludedIds.append(repid)
                thisLocation.remove(thisLocation[subsections.index(s)])
                subsections.remove(s)
            if any(x in s for x in ['to be ruled out', '(pmid:']):
                excludedSections.append(s)
                excludedReasons.append('variant discussion')
                excludedIds.append(repid)
                thisLocation.remove(thisLocation[subsections.index(s)])
                subsections.remove(s)
            if any(x in s for x in ['the diagnosis of', 'the diagnosis requires']):
                excludedSections.append(s)
                excludedReasons.append('diagnosis discussion')
                excludedIds.append(repid)
                thisLocation.remove(thisLocation[subsections.index(s)])
                subsections.remove(s)
            if len(subsections) == 0:
                hasBiom = False

        # A divide up for particularly challenging karyotypes
        for s in range(0, len(subsections)):
            if 'probe signals' in subsections[s]:
                if '):' in subsections[s]:
                    subsections[s] = subsections[s][subsections[s].index('): ') + 3:].replace(';', ' . . ')
                    while len(thisLocation[s].split(' . . ')) < len(subsections[s].split(' . . ')):
                        add = thisLocation[s].split(' . . ')[0]
                        thisLocation[s] = thisLocation[s] + ' . . ' + add
        # Finally, add all results to the return bit
        if len(subsections) > 1:
            #print(subsections)
            #print(thisLocation)
            #print('MORE THAN ONE')
            #input()
            returnBit = ' . . ' + returnBit + ' . . ' + ' . . '.join(subsections)
            returnLocation = ' . . ' + returnLocation + ' . . ' + ' . . '.join(thisLocation)
        elif len(subsections) == 0 and hasBiom and not sampleNameBiomarker:
            print('========================******==================')
            print(origText)
            print('-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_')
            print(returnBit)
            print('****')
            print(text)
            input()
        elif sampleNameBiomarker:
            removedSections.append(text)
            removedSectionIds.append(repid)
            text = ''
        elif not hasBiom:
            returnBit = ''
            thisLocation = ''
        else:
            returnBit = ' . . ' + returnBit + ' . . ' + subsections[0]
            returnLocation = ' . . ' + returnLocation + ' . . ' + thisLocation[0]
        if karyotype != 'none':
            returnBit = returnBit + ' . . ' + karyotype
            returnLocation = returnLocation + ' . . ' + returnLocation.split(' . . ')[0]
        for bit in returnBit.split(' . . '):
            if len(bit) > 130:
                if not any(x in bit for x in ['there is insufficient tumor cell content', 'are pending and will be reported separately',
                                              'by immunohistochemical staining performed on', 'were detected in the ', 'were detected',
                                              'they are negative for', 'seen in the prior metastasis', 'immunoperoxidase for her2/neu',
                                              'it does, however']):
                    #print(origText)
                    #print('----------------------')
                    #print(text)
                    #print(subsection)
                    #print('----------------------')
                    #print(sectionOrig)
                    #print('----------------------')
                    #print(bit)
                    print("WE SURE?!")
                    #print(repid)
                    #input()

    while returnBit.startswith((' ', '.')):
        returnBit = returnBit[1:]
    while returnLocation.startswith((' ', '.')):
        returnLocation = returnLocation[1:]

    if showResults or monitor:
        print(origText)
        print('****RETURN VALUE OF***')
        print(returnBit)
        print('location is')
        print(returnLocation)
        input()
    return(returnBit, noContentSections, noContentSectionsIds, removedSections, removedSectionIds, addendumLeftovers,
           addendumLeftoverIds, returnLocation, excludedSections, excludedReasons, excludedIds)

