import numpy as np
import pandas as pd
from sklearn import preprocessing
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
import math

# Import machine learning methods
from sklearn.linear_model import LogisticRegression

# I'm going to make a boolean that determines if we print out everything when this is run or not.
# Setting it to 'true' will print everything, for display at the end.
# Setting it to 'false' will make everything not print, to not crowd the screen during development.
displayOn = False

# Likewise, we turn this on if we want to use scaling. We'll scale between -1 and 1
useScaling = False

# These turn on the different parts of the program
doPart1 = False
doPart2 = False
doPart3 = False
doPart4 = False
doPart5 = True

# Open our dataset
df = pd.read_csv("/Users/bholmes/Desktop/Assign/Assignment1_data.csv", low_memory=False)

# Columns: ['Student', 'Vaccin', 'HndWshQual', 'HndWshFreq', 'SociDist', 'NoFaceContact', 'RespEttiqu', 'PersnDist', 'HandSanit', 'Risk', 'Complications', 'Barriers', 'Inefficacy',
#  'KnowlTrans', 'KnowlMgmt', 'Sick', 'Flu', 'Female']
if displayOn:
    print("Columns in dataframe: ", df.columns)

#####
# UNIVARIATE
####

# Make sure there are no NAs to impute for Risk or Flu
if displayOn:
    print("number of NA values for 'Risk': ", df['Risk'].isna().sum())
    print("number of NA values for 'Flu': ", df['Flu'].isna().sum())

# Actually, there are 36 NAs for 'flu'. Let's see what the values of Risk are when Flu is NA
if displayOn:
    print("Values of Risk when 'Flu' is NA")
    print(df.loc[df['Flu'].isna()]['Risk'])

# So the values for 'Risk' are not null when 'Flu' is null.
# We could do two things here: we could impute NA to be 0, or we could drop the rows with
# NA values. Let's drop.

# Dropping the NA values
df = df.loc[~df['Flu'].isna()]

# Let's see what the breakdown is of flu to non-flu
sns.countplot(x='Flu', data=df)
if displayOn:
    plt.show()

# Let's look at the plot by risk
sns.countplot(x='Flu', hue='Risk', data=df)
plt.legend().set_visible(False)
if displayOn:
    plt.show()

# Pretty neat - it shows that there does seem to be a correlation (though it isn't perfect) - lower values for not flu, higher values for flu.

# Now, we're meant to model 'Flu' based only off of 'Risk'
X = df[['Risk']]
X = np.array(X)
Y = df['Flu']
Y = np.array(Y)

# We'll do a 75/25 train/test split
X_train,X_test,Y_train,Y_test = train_test_split(X, Y, test_size=0.25)

# I'm including the 'scikit learn' standard LogisticRegression model as a benchmark.
# We'll be able to compare this against what we can come up with!
clf = LogisticRegression()
clf.fit(X_train,Y_train)

# For numIter cycles, we find gradients that take the values of theta, perform gradient descent,
# and find new values. Also of note: alf (alpha), the learning rate
# X is the list of features that we're training, Y contains the labels.
def Logistic_Regression(X, Y, alf, tht, numIter, confusionOrNot):
    z = len(Y)

    # For every iteration we have, do another round of gradient descent
    for x in range(numIter):
        nextTht = Gradient_Descent(X, Y, tht, z, alf)
        tht = nextTht

    # For every example, see if we did it right or not!
    numRight = 0
    length = len(X_test)
    truePositive = 0
    falsePositive = 0
    trueNegative = 0
    falseNegative = 0
    for x in range(length):
        prediction = round(Linear_Combine(X_test[x], tht))
        answer = Y_test[x]
        if prediction == answer:
            numRight += 1
        if prediction == answer == 1:
            truePositive = truePositive + 1
        if prediction == answer == 0:
            trueNegative = trueNegative + 1
        if prediction == 0 and answer == 1:
            falseNegative = falseNegative + 1
        if prediction == 1 and answer == 0:
            falsePositive = falsePositive + 1

    # Once we're all done with the iterations, let's find what our final accuracy score is!
    finalScore = float(numRight) / float(length)

    if confusionOrNot:
        print('TP: ', truePositive)
        print('FP: ', falsePositive)
        print('TN: ', trueNegative)
        print('FN: ', falseNegative)

    return finalScore

# Gradient descent means finding the vector from our current location to the spot of greatest
# derivative change - and reversing direction, going downhill.
def Gradient_Descent(X, Y, tht, z, alf):
    thetaResult = []
    for b in range(len(tht)):
        GradDeriv = Get_Gradient(X, Y, tht, b, z, alf)
        nextTheta = tht[b] - GradDeriv
        thetaResult.append(nextTheta)
    return thetaResult

# Here we get the gradient component for theta. We also worry about the 'learning rate', alpha (alf)
def Get_Gradient(X, Y, tht, b, z, alf):
    totalErr = 0
    for a in range(z):
        xa = X[a]
        xab = xa[b]
        hi = Linear_Combine(tht, X[a])
        error = (hi - Y[a]) * xab
        totalErr = totalErr + error
    m = len(Y)
    learn = float(alf) / float(m)
    J = learn * totalErr
    return J

# We take a linear combination of all the known factors + their est. coefficients theta[i]
# Note that the return value is the sigmoid function of the cost
def Linear_Combine(tht, factor):
    cost = 0
    for zx in range(len(tht)):
        cost = cost + (factor[zx] * tht[zx])
    return float(1.0 / float((1.0 + math.exp(-1.0 * cost))))

######
# ALRIGHT, THAT ASIDE, LET'S GET ROLLING!
######

# Here we set an initial value for theta, and the learning rate.
# We can play around with each, but be careful - a learning rate
# that's too low doesn't close in on the appropriate answer.

# Alpha of 0.1 and iterations of 1k are pretty standard, so we'll stick with those.


initial_theta = [0] * len(X[0])
alpha = 0.1
iterations = 1000
finalScore = []
if doPart1:
    for x in range(0, 20):
        finalScore.append(Logistic_Regression(X, Y, alpha, initial_theta, iterations, False))
    finalScore = sum(finalScore)/len(finalScore)
    scikit_score = clf.score(X_test,Y_test)
    print('Avg. Final Score Univariate: ', finalScore)
    print('Benchmark Score: ', scikit_score)
    # One more time to get the confusion matrix
    Logistic_Regression(X, Y, alpha, initial_theta, iterations, True)

import statsmodels.formula.api as smf

# We need the 'label' to be a part of the columns in 'data', or the method will fail
def forwardSelection(data, label):
    currentScore = 0.0
    bestScore = 0.0
    passingFeatures = []
    featuresToGo = list(data.columns)
    featuresToGo.remove(label)
    while len(featuresToGo) > 0 and currentScore == bestScore:
        scores_with_candidates = []
        for candidate in featuresToGo:
            formula = "{} ~ {} + 1".format(label, ' + '.join(passingFeatures + [candidate]))
            score = smf.ols(formula, data).fit().rsquared_adj
            scores_with_candidates.append((score, candidate))
        scores_with_candidates.sort()
        bestScore, best_candidate = scores_with_candidates.pop()
        if currentScore < bestScore:
            featuresToGo.remove(best_candidate)
            passingFeatures.append(best_candidate)
            currentScore = bestScore

    return passingFeatures

######
# NOW IT'S TIME FOR QUESTION 2
######

df2 = df[['Vaccin', 'HndWshQual', 'HndWshFreq', 'SociDist', 'NoFaceContact', 'RespEttiqu', 'PersnDist', 'HandSanit', 'Risk', 'Inefficacy', 'KnowlTrans', 'KnowlMgmt', 'Flu']]
df2 = df2.dropna()
X = df2[['Vaccin', 'HndWshQual', 'HndWshFreq', 'SociDist', 'NoFaceContact', 'RespEttiqu', 'PersnDist', 'HandSanit', 'Risk', 'Inefficacy', 'KnowlTrans', 'KnowlMgmt']]
X = np.array(X)
Y = df2['Flu']
Y = np.array(Y)

# We'll do a 75/25 train/test split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

clf = LogisticRegression()
clf.fit(X_train,Y_train)
scikit_score = clf.score(X_test, Y_test)

initial_theta = [0] * len(X[0])
finalScore = []
if doPart2:
    for x in range(0, 20):
        print("part 2 iteration ", x)
        finalScore.append(Logistic_Regression(X, Y, alpha, initial_theta, iterations, False))
    finalScore = sum(finalScore)/len(finalScore)
    scikit_score = clf.score(X_test,Y_test)
    print('Avg. Final Score Univariate: ', finalScore)
    print('Benchmark Score: ', scikit_score)
    # One more time to get the confusion matrix
    Logistic_Regression(X, Y, alpha, initial_theta, iterations, True)

#####
# Now for a bit of feature selection!
#####

if doPart3:
    X = df[['Vaccin', 'HndWshQual', 'HndWshFreq', 'SociDist', 'NoFaceContact', 'RespEttiqu', 'PersnDist', 'HandSanit', 'Risk', 'Inefficacy', 'KnowlTrans', 'KnowlMgmt', 'Flu']]
    # I'm including the 'scikit learn' standard LogisticRegression model as a benchmark.
    # We'll be able to compare this against what we can come up with!
    clf = LogisticRegression()
    clf.fit(X_train,Y_train)
    print(forwardSelection(X, 'Flu'))

#####
# Now that we've done the feature selection, let's run each of the models
#####

if doPart4:
    features = ['Risk', 'KnowlMgmt', 'Vaccin', 'Inefficacy', 'RespEttiqu', 'PersnDist', 'HandSanit']

    for ind in range(len(features)-1, len(features)):
        subFeatures = features[0:ind+1]
        subFeatures.append('Flu')
        df2 = df[subFeatures]
        df2 = df2.dropna()
        X = df2
        X.drop(columns=['Flu'])
        X = np.array(X)
        Y = df2['Flu']
        Y = np.array(Y)

        # We'll do a 75/25 train/test split
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

        clf = LogisticRegression()
        clf.fit(X_train,Y_train)
        scikit_score = clf.score(X_test, Y_test)

        initial_theta = [0] * len(X[0])
        finalScore = []
        for x in range(0, 20):
            print("part 4 iteration ", x)
            finalScore.append(Logistic_Regression(X, Y, alpha, initial_theta, iterations, False))
        finalScore = sum(finalScore)/len(finalScore)
        scikit_score = clf.score(X_test,Y_test)
        subFeatures.remove('Flu')
        print("feature list is ", subFeatures)
        print('Avg. Final Score Univariate: ', finalScore)
        print('Benchmark Score: ', scikit_score)
        # One more time to get the confusion matrix
        Logistic_Regression(X, Y, alpha, initial_theta, iterations, True)
        input()
