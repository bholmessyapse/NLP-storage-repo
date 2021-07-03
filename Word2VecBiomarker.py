from __future__ import unicode_literals
import pandas as pd
import numpy as np
import spacy
from numpy import dot
from numpy.linalg import norm
import math
import json

nlp = spacy.load('en')

def vec(s):
    return nlp(s).vector

def addv(coord1, coord2):
    return [c1 + c2 for c1, c2 in zip(coord1, coord2)]
addv([10, 1], [5, 2])

def subtractv(coord1, coord2):
    return [c1 - c2 for c1, c2 in zip(coord1, coord2)]
subtractv([10, 1], [5, 2])

def distance(coord1, coord2):
    # note, this is VERY SLOW, don't use for actual code
    return math.sqrt(sum([(i - j)**2 for i, j in zip(coord1, coord2)]))
distance([10, 1], [5, 2])

def meanv(coords):
    # assumes every item in coords has same length as item 0
    sumv = [0] * len(coords[0])
    for item in coords:
        for i in range(len(item)):
            sumv[i] += item[i]
    mean = [0] * len(sumv)
    for i in range(len(sumv)):
        mean[i] = float(sumv[i]) / len(coords)
    return mean

def closest(space, coord, n=10):
    closest = []
    for key in sorted(space.keys(),
                        key=lambda x: distance(coord, space[x]))[:n]:
        closest.append(key)
    return closest

# cosine similarity
def cosine(v1, v2):
    if norm(v1) > 0 and norm(v2) > 0:
        return dot(v1, v2) / (norm(v1) * norm(v2))
    else:
        return 0.0

def spacy_closest(token_list, vec_to_check, n=10):
    return sorted(token_list,
                  key=lambda x: cosine(vec_to_check, vec(x)),
                  reverse=True)[:n]

color_data = json.loads(open("/Users/bholmes/Desktop/DeleteMeSoon/word2vec/colors.json").read())

def hex_to_int(s):
    s = s.lstrip("#")
    return int(s[:2], 16), int(s[2:4], 16), int(s[4:6], 16)

colors = dict()
for item in color_data['colors']:
    colors[item["color"]] = hex_to_int(item["hex"])

# The path reports are located here
reports = pd.read_csv("/Users/bholmes/Desktop/DeleteMeSoon/MSMDR Narratives/PathReports.csv", low_memory=False)

# 'description' is the text of the reports
reports = reports['description']

brcaReports = []

# Looking at colors
# We'll collect the breast-containing reports
#reportsOrig = reports
for report in reports:
    if 'autopsy' in report:
        #startSection = report[report.index("MICROSCOPIC:"):]
        #section = startSection[:startSection.index('\n\n')]
        #brcaReports.append(section)
        brcaReports.append(report)
#        print(len(brcaReports))

reports = ' '.join(brcaReports)
reports = reports.replace('\n', ' ')
reports = reports.split(' ')
microscopic_colors = [colors[word.lower()] for word in reports if word.lower() in colors]
avg_color = meanv(microscopic_colors)
print(avg_color)
print(closest(colors, avg_color))
input()

# Looking for similarity words!
#reports = reportsOrig
# We'll collect the breast-containing reports
#for report in reports:
#    brcaReports.append(report)

#reports = ' '.join(brcaReports)
#reports = reports.replace('\n', ' ')
#reports = reports.lower()
#reports = reports.split(' ')

#tokens = list(set([w for w in reports if w]))

#print(spacy_closest(tokens, vec("carcinoma")))

def sentvec(s):
    sent = nlp(s)
    return meanv([w.vector for w in sent])

reports = reportsOrig
for report in reports:
    if 'PATHOLOGICAL DIAGNOSIS:' in report:
        report = report[report.index('PATHOLOGICAL DIAGNOSIS:') + len('PATHOLOGICAL DIAGNOSIS: '):]
        if '\n\n' in report:
            report = report[:report.index('\n\n')]
        else:
            print("HERE!")
            print(report)
            input()
        brcaReports.append(report)
        brcaReports = brcaReports[0:1000]
        print(len(brcaReports))

reports = ' '.join(brcaReports)
reports = reports.replace('\n', ' ')
reports = reports.lower()
sentences = nlp(reports)
sentences = list(sentences.sents)

def spacy_closest_sent(space, input_str, n=10):
    input_vec = sentvec(input_str)
    return sorted(space, key=lambda x: cosine(np.mean([w.vector for w in x], axis=0), input_vec), reverse=True)[:n]

for sent in spacy_closest_sent(sentences, "We were able to find a large lesion"):
    print(sent)
    print("---")