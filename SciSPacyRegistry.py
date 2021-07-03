import spacy
import scispacy
import pandas as pd
from scispacy.linking import EntityLinker

registry = pd.read_csv("/Users/bholmes/Desktop/DeleteMeSoon/Josh/registry.csv", low_memory=False)

# Index(['id', 'identifiers', 'registrytext', 'treatmentsextracted', 'rxtype','sourcename', 'suborg', 'datasourcetype', 'datasourceid', 'datasourcefile', 'datasourcecreateddts',
# 'datasourceupdateddts','extractdts', 'ishidden', 'addeddts', 'addedby', 'updateddts', 'updatedby'], dtype='object')
# print(registry.columns)
# input()

registryText = list(registry['registrytext'])

nlp = spacy.load("en_core_sci_sm")

linker = EntityLinker(resolve_abbreviations=True, name="umls")

nlp.add_pipe(linker)

doc = nlp(registryText[0])

results = []
interp = []

x = 0

for docBit in registryText:
    print('number ', x, ' of ', len(registryText))
    mappings = []
    x = x + 1
    try:
        doc = nlp(docBit)
        results.append(doc.ents)
        for entity in doc.ents:
            for umls_ent in entity._.umls_ents:
                mappings.append(linker.umls.cui_to_entity[umls_ent[0]])
        interp.append(mappings)
    except:
        results.append('could not parse')
        interp.append('could not parse')

textDF = pd.DataFrame(list(zip(registryText, results, interp)),
                                                            columns=['text', 'tokens', 'mappings'])

textDF.to_csv("~/Desktop/DeleteMeSoon/Josh/SciSpacyresults.csv", index=False)