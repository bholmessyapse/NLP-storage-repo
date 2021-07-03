####
# Ben Holmes
# Syapse
####

# Programmed using the scikit-learn fuzzy toolkit, skfuzzy

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

####
# Input goes here
# lengs = length of document in words: 0-500
# abnormals = # of abnormal words: 0-30
# fails = # of 'failure' words: 0-15
###

# Each one of these lists holds one of the three input values. THE LISTS MUST BE THE SAME SIZE OF COURSE.
# Lengths should be between 0-100
# abnormals should be between 0-30
# fails should be between 0-15

titlesList = ["A - clear failure:", "B - clear abnormal:", "C- clear normal:", "D- erroneous:", "E- erroneous:", "F- ambiguous:"]
lengthList = [15, 351, 206, 314, 0, 291]
abnormalList = [1, 20, 1, 2, 0, 17]
failList = [6, 2, 0, 15, 0, 8]

# We loop through these, so I can try many examples in a hurry.
for x in range(0, len(lengthList)):
    lengs = lengthList[x]
    abnormals = abnormalList[x]
    fails = failList[x]

    # we specify the universe, then label, then defuzzification method for consequents. Antecedents obviously don't need defuzzification methods!
    length = ctrl.Antecedent(np.arange(0, 500, 1), 'length')
    failWords = ctrl.Antecedent(np.arange(0, 15.01, 1), 'failWords')
    abnormalWords = ctrl.Antecedent(np.arange(0, 30.01, 1), 'abnormalWords')
    toRead = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'toRead', 'centroid')

    #######
    # Normal defuzzification functions - centroid
    #######
    # isNormal = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'isNormal', 'centroid')
    # isAbnormal = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'isAbnormal', 'centroid')
    # isFailed = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'isFailed', 'centroid')
    #isErr = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'isErr', 'centroid')

    ######
    # Alternate defuzzification functions - Mean of Maximum
    ######
    isNormal = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'isNormal', 'mom')
    isAbnormal = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'isAbnormal', 'mom')
    isFailed = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'isFailed', 'mom')
    isErr = ctrl.Consequent(np.arange(0, 100.01, 1.0), 'isErr', 'mom')

    #####
    # Normal Membership Functions
    #####

    # Triangle function for length
    length['short'] = fuzz.trimf(length.universe, [0, 0, 250])
    length['medium'] = fuzz.trimf(length.universe, [0, 250, 500])
    length['long'] = fuzz.trimf(length.universe, [250, 500, 500])

    # Triangle function for abnormal and failed word lengths
    abnormalWords['low'] = fuzz.trimf(abnormalWords.universe, [0, 0, 15])
    abnormalWords['high'] = fuzz.trimf(abnormalWords.universe, [15, 30, 30])

    failWords['low'] = fuzz.trimf(failWords.universe, [0, 0, 3])
    failWords['high'] = fuzz.trimf(failWords.universe, [3, 15, 15])

    #####
    # Alternate Membership Functions
    #####

    # ZMF to Gaussian to SMF for length
    #length['short'] = fuzz.zmf(length.universe, 0, 300)
    #length['medium'] = fuzz.gaussmf(length.universe, 250, 75)
    #length['long'] = fuzz.smf(length.universe, 225, 500)

    # ZMF to SMF for abnormal and failed
    #abnormalWords['low'] = fuzz.zmf(abnormalWords.universe, 0, 5)
    #abnormalWords['high'] = fuzz.smf(abnormalWords.universe, 3, 30)

    #failWords['low'] = fuzz.zmf(failWords.universe, 0, 4)
    #failWords['high'] = fuzz.smf(failWords.universe, 3, 15)

    # We'll model the outputs as triangles
    toRead['low'] = fuzz.trimf(toRead.universe, [0, 0, 50])
    toRead['medium'] = fuzz.trimf(toRead.universe, [0, 50, 100])
    toRead['high'] = fuzz.trimf(toRead.universe, [50, 100, 100])

    isNormal['low'] = fuzz.trimf(isNormal.universe, [0, 0, 50])
    isNormal['medium'] = fuzz.trimf(isNormal.universe, [0, 50, 100])
    isNormal['high'] = fuzz.trimf(isNormal.universe, [50, 100, 100])

    isAbnormal['low'] = fuzz.trimf(isAbnormal.universe, [0, 0, 50])
    isAbnormal['medium'] = fuzz.trimf(isAbnormal.universe, [0, 50, 100])
    isAbnormal['high'] = fuzz.trimf(isAbnormal.universe, [50, 100, 100])

    isFailed['low'] = fuzz.trimf(isFailed.universe, [0, 0, 50])
    isFailed['medium'] = fuzz.trimf(isFailed.universe, [0, 50, 100])
    isFailed['high'] = fuzz.trimf(isFailed.universe, [50, 100, 100])

    isErr['low'] = fuzz.trimf(isErr.universe, [0, 0, 50])
    isErr['medium'] = fuzz.trimf(isErr.universe, [0, 50, 100])
    isErr['high'] = fuzz.trimf(isErr.universe, [50, 100, 100])

    ######
    # Normal Ruleset
    # If SHORT and LOW abnormal and LOW fail then LOW chance abnormal and LOW chance is failed and MEDIUM chance is normal and HIGH chance is err and HIGH reason to read
    # if SHORT and LOW abnormal and HIGH fail then LOW chance abnormal and HIGH chance failed and LOW chance normal and LOW chance err and HIGH reason to read
    # if SHORT and HIGH abnormal and LOW fail then MEDIUUM chance abnormal and LOW chance failed and LOW chance normal and MEDIUM chance err and MEDIUM reason to read
    # if SHORT and HIGH abnormal and HIGH fail then MEDIUM chance abnormal and MEDIUM chance failed and LOW chance normal and HIGH chance err and MEDIUM reason to read
    #
    # if MEDIUM and LOW abnormal and LOW fail then LOW chance abnormal and LOW chance failed and HIGH chance normal and LOW chance err and LOW reason to read
    # if MEDIUM and LOW abnormal and HIGH fail then LOW chance abnormal and MEDIUM chance failed and MEDIUM chance normal and HIGH chance err and HIGH reason to read
    # if MEDIUM and HIGH abnormal and LOW fail then HIGH chance abnormal and LOW chance failed and MEDIUM chance normal and LOW chance err and HIGH reason to read
    # if MEDIUM and HIGH abnormal and HIGH fail then HIGH chance abnormal and HIGH chance failed and LOW chance normal and MEDIUM chance err and HIGH reason to read
    #
    # if LONG and LOW abnormal and LOW fail then LOW chance abnormal and LOW chance failed and MEDIUM chance normal and MEDIUM chance err and LOW reason to read
    # if LONG and LOW abnormal and HIGH fail then LOW chance abnormal and MEDIUM chance failed and LOW chance normal and HIGH chance err and HIGH reason to read
    # if LONG and HIGH abnormal and LOW fail then HIGH chance abnormal and LOW chance failed and LOW chance normal and LOW chance err and HIGH reason to read
    # if LONG and HIGH abnormal and HIGH fail then HIGH chance abnormal and HIGH chance failed and LOW chance normal and HIGH chance err and HIGH reason to read

    rule1 = ctrl.Rule(length['short'] & abnormalWords['low'] & failWords['low'], [isAbnormal['low'], isFailed['low'], isNormal['medium'], isErr['high'], toRead['high']])
    rule2 = ctrl.Rule(length['short'] & abnormalWords['low'] & failWords['high'], [isAbnormal['low'], isFailed['high'], isNormal['low'], isErr['low'], toRead['high']])
    rule3 = ctrl.Rule(length['short'] & abnormalWords['high'] & failWords['low'], [isAbnormal['medium'], isFailed['low'], isNormal['low'], isErr['medium'], toRead['medium']])
    rule4 = ctrl.Rule(length['short'] & abnormalWords['high'] & failWords['high'], [isAbnormal['medium'], isFailed['medium'], isNormal['low'], isErr['high'], toRead['high']])
    rule5 = ctrl.Rule(length['medium'] & abnormalWords['low'] & failWords['low'], [isAbnormal['low'], isFailed['low'], isNormal['high'], isErr['low'], toRead['low']])
    rule6 = ctrl.Rule(length['medium'] & abnormalWords['low'] & failWords['high'], [isAbnormal['low'], isFailed['medium'], isNormal['medium'], isErr['high'], toRead['high']])
    rule7 = ctrl.Rule(length['medium'] & abnormalWords['high'] & failWords['low'], [isAbnormal['high'], isFailed['low'], isNormal['medium'], isErr['low'], toRead['high']])
    rule8 = ctrl.Rule(length['medium'] & abnormalWords['high'] & failWords['high'], [isAbnormal['high'], isFailed['high'], isNormal['low'], isErr['medium'], toRead['high']])
    rule9 = ctrl.Rule(length['long'] & abnormalWords['low'] & failWords['low'], [isAbnormal['low'], isFailed['low'], isNormal['medium'], isErr['medium'], toRead['low']])
    rule10 = ctrl.Rule(length['long'] & abnormalWords['low'] & failWords['high'], [isAbnormal['low'], isFailed['medium'], isNormal['low'], isErr['high'], toRead['high']])
    rule11 = ctrl.Rule(length['long'] & abnormalWords['high'] & failWords['low'], [isAbnormal['high'], isFailed['low'], isNormal['low'], isErr['low'], toRead['high']])
    rule12 = ctrl.Rule(length['long'] & abnormalWords['high'] & failWords['high'], [isAbnormal['high'], isFailed['high'], isNormal['low'], isErr['high'], toRead['high']])

    # Alternative ruleset flipping 'AND' to 'OR
    #rule1 = ctrl.Rule(length['short'] | abnormalWords['low'] | failWords['low'], [isAbnormal['low'], isFailed['low'], isNormal['medium'], isErr['high'], toRead['high']])
    #rule2 = ctrl.Rule(length['short'] | abnormalWords['low'] | failWords['high'], [isAbnormal['low'], isFailed['high'], isNormal['low'], isErr['low'], toRead['high']])
    #rule3 = ctrl.Rule(length['short'] | abnormalWords['high'] | failWords['low'], [isAbnormal['medium'], isFailed['low'], isNormal['low'], isErr['medium'], toRead['medium']])
    #rule4 = ctrl.Rule(length['short'] | abnormalWords['high'] | failWords['high'], [isAbnormal['medium'], isFailed['medium'], isNormal['low'], isErr['high'], toRead['high']])
    #rule5 = ctrl.Rule(length['medium'] | abnormalWords['low'] | failWords['low'], [isAbnormal['low'], isFailed['low'], isNormal['high'], isErr['low'], toRead['low']])
    #rule6 = ctrl.Rule(length['medium'] | abnormalWords['low'] | failWords['high'], [isAbnormal['low'], isFailed['medium'], isNormal['medium'], isErr['high'], toRead['high']])
    #rule7 = ctrl.Rule(length['medium'] | abnormalWords['high'] | failWords['low'], [isAbnormal['high'], isFailed['low'], isNormal['medium'], isErr['low'], toRead['high']])
    #rule8 = ctrl.Rule(length['medium'] | abnormalWords['high'] | failWords['high'], [isAbnormal['medium'], isFailed['medium'], isNormal['low'], isErr['medium'], toRead['high']])
    #rule9 = ctrl.Rule(length['long'] | abnormalWords['low'] | failWords['low'], [isAbnormal['low'], isFailed['low'], isNormal['medium'], isErr['medium'], toRead['low']])
    #rule10 = ctrl.Rule(length['long'] | abnormalWords['low'] | failWords['high'], [isAbnormal['low'], isFailed['medium'], isNormal['low'], isErr['high'], toRead['high']])
    #rule11 = ctrl.Rule(length['long'] | abnormalWords['high'] | failWords['low'], [isAbnormal['high'], isFailed['low'], isNormal['low'], isErr['low'], toRead['high']])
    #rule12 = ctrl.Rule(length['long'] | abnormalWords['high'] | failWords['high'], [isAbnormal['medium'], isFailed['medium'], isNormal['low'], isErr['medium'], toRead['medium']])

    report_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12])

    reportGuesser = ctrl.ControlSystemSimulation(report_ctrl)

    reportGuesser.input['length'] = lengs
    reportGuesser.input['abnormalWords'] = abnormals
    reportGuesser.input['failWords'] = fails

    reportGuesser.compute()
    print(titlesList[x])
    print("Length - ", str(lengs), " # Abnormal Words - ", str(abnormals), " # Failed Words - ", str(fails))
    print('% chance of normal - ', reportGuesser.output['isNormal'])
    print('% chance of abnormal - ', reportGuesser.output['isAbnormal'])
    print('% chance of failed - ', reportGuesser.output['isFailed'])
    print('% chance of err - ',  reportGuesser.output['isErr'])
    print('% chance we want to read - ', reportGuesser.output['toRead'])
    print("")
    print('')