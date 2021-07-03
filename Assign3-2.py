# Ben Holmes
# Assignment 3
# Machine Learning
# Fall 2020

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Import machine learning methods
from sklearn.linear_model import LogisticRegression

# The logarithmic activation function
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

# Alternate cost function for linear
def leastSquares(z, y):
    m = y.size
    return (np.sum(np.square((z - y))) / (2 * m))

# Here's where we do the logistic regression. Not named "LogisticRegression" to not overlap with the sklearn model.
class LogisticReg(object):
    def __init__(self, alpha, iters, regularType, C, costF):

        self.alpha = alpha
        self.iters = iters
        self.regularType = regularType
        self.C = C
        self.costF = costF

    # This part adjusts the weights based on our 'hypothesis'
    def fitWeights(self, X_train, y_train, tolr = 0.0001):
        self.weightArray = np.zeros(np.shape(X_train)[1] + 1)
        self.costs = []

        toleranceWeight = tolr * np.ones([1, np.shape(X_train)[1] + 1])
        X_train = np.c_[np.ones([np.shape(X_train)[0], 1]), X_train]

        for i in range(self.iters):
            z = np.dot(X_train, self.weightArray)
            errors = y_train - sigmoid(z)

            # I'd like the ability to add different kinds of regularization in later, but for now it's just l2
            # Any other values we'll interpret as mistakes
            if self.regularType == 'L2':
                weightChange = self.alpha * (self.C * np.dot(errors, X_train) + np.sum(self.weightArray))
            else:
                weightChange = self.alpha * np.dot(errors, X_train)

            self.iterationsPerformed = i

            # We want to update if our weight change is above the tolerance
            if np.all(abs(weightChange) >= toleranceWeight):
                self.weightArray += weightChange
                # Again, I'd like to add other kinds of cost functions in
                if self.regularType == 'L2':
                    self.costs.append(regularized_logCost(X_train, self.weightArray, y_train, self.C))
                elif not self.costF:
                    self.costs.append(logCost(z, y_train))
                else:
                    self.costs.append(leastSquares(z, y_train))
            else:
                break

        return self

    # So here we make our calls, with 0.5 as the cutoff (experiment with different ones?)
    # If the value is above 0.5, we consider it to be in the positive group. Below, in the
    # negative
    def predict(self, X_test, cutoff = 0.5):
        z = self.weightArray[0] + np.dot(X_test, self.weightArray[1:])
        probIsPos = np.array([sigmoid(i) for i in z])
        positiveOrNegative = np.where(probIsPos >= cutoff, 1, 0)

        return positiveOrNegative, probIsPos

    # This step is where we review our findings - since we're interested in the
    # confusion matrix, I print TP, FP, TN, FN
    def reviewResults(self, positiveOrNegative, y_test):
        # Initialize
        TP = 0
        TN = 0
        FP = 0
        FN = 0

        for idx, test_sample in enumerate(y_test):

            if positiveOrNegative[idx] == test_sample == 1:
                TP += 1
            elif positiveOrNegative[idx] == test_sample == 0:
                TN += 1
            elif positiveOrNegative[idx] == 0 and test_sample == 1:
                FN += 1
            elif positiveOrNegative[idx] == 1 and test_sample == 0:
                FP += 1

        accuracy = (TP + TN) / len(y_test)
        print("Accuracy: ", accuracy)
        print("True Positive: ", TP)
        print("False Positive: ", FP)
        print("True Negative: ", TN)
        print("False Negative: ", FN)
        return

# This is the cost function if we're doing regularization. It takes into account C, which is lambda,
# the weight.
def regularized_logCost(x, weightArray, y, C):
    z = np.dot(x, weightArray)
    reg_term = (1 / (2 * C)) * np.dot(weightArray.T, weightArray)

    return -1 * np.sum((y * np.log(sigmoid(z))) + ((1 - y) * np.log(1 - sigmoid(z)))) + reg_term

def logCost(z, y):
    return -1 * np.sum((y * np.log(sigmoid(z))) + ((1 - y) * np.log(1 - sigmoid(z))))

df = pd.read_csv("/Users/bholmes/Desktop/Assign/Assignment1_data.csv", low_memory=False)
# "flu" and "knowlTrans" have some NA values. That'll be important later! We'll drop them. We could also impute, were this a longer assignment
df = df.loc[~df['Flu'].isna()]
df = df.loc[~df['KnowlTrans'].isna()]

###
# UNIVARIATE
###

X = df[['Risk']]
X = np.array(X)
Y = df['Flu']
Y = np.array(Y)

# We'll do a 75/25 train/test split
X_train,X_test,Y_train,Y_test = train_test_split(X, Y, test_size=0.25)

# Now fit the model...
model = LogisticReg(alpha = 0.01, iters = 2000, regularType = None, C = 0.01, costF = False)
model.fitWeights(X_train, Y_train, tolr = 10 ** -3)

# Get the results
positiveOrNegative, probIsPos = model.predict(X_test, 0.5)
print("UNIVARITAE: ")
model.reviewResults(positiveOrNegative, Y_test)

clf = LogisticRegression()
clf.fit(X_train,Y_train)
scikit_score = clf.score(X_test, Y_test)
print(scikit_score)
print('----------------------')

####
# ALL FIELDS
###

X = df[['Vaccin', 'HndWshQual', 'HndWshFreq', 'SociDist', 'NoFaceContact', 'RespEttiqu', 'PersnDist', 'HandSanit', 'Risk', 'Inefficacy', 'KnowlTrans', 'KnowlMgmt']]
X = np.array(X)
Y = df['Flu']
Y = np.array(Y)


# We'll do a 75/25 train/test split
X_train,X_test,Y_train,Y_test = train_test_split(X, Y, test_size=0.25)

# Now fit the model...
model = LogisticReg(alpha = 0.01, iters = 2000, regularType = None, C = 0.01, costF = False)
model.fitWeights(X_train, Y_train, tolr = 10 ** -3)

# Get the results
positiveOrNegative, probIsPos = model.predict(X_test, 0.5)
print("ALL VARIATES: ")
model.reviewResults(positiveOrNegative, Y_test)

clf = LogisticRegression()
clf.fit(X_train,Y_train)
scikit_score = clf.score(X_test, Y_test)
print(scikit_score)
print('----------------------')

import statsmodels.formula.api as smf

# We need the 'label' to be a part of the columns in 'data', or the method will fail
# This forward selection method will pick out the features that don't make the
# model WORSE, and present them in order
def forwardSelection(data, label):
    scoreNow = 0.0
    bestScore = 0.0
    usableFeatures = []
    featuresLeft = list(data.columns)
    featuresLeft.remove(label)
    while len(featuresLeft) > 0 and scoreNow == bestScore:
        candidates = []
        for candidate in featuresLeft:
            additiveFormula = label + ' ~ ' + ' + '.join(usableFeatures + [candidate]) + ' + 1'
            score = smf.ols(additiveFormula, data).fit().rsquared_adj
            candidates.append((score, candidate))
        candidates.sort()
        bestScore, bestOption = candidates.pop()
        if scoreNow < bestScore:
            featuresLeft.remove(bestOption)
            usableFeatures.append(bestOption)
            scoreNow = bestScore
    return usableFeatures

X = df[['Vaccin', 'HndWshQual', 'HndWshFreq', 'SociDist', 'NoFaceContact', 'RespEttiqu', 'PersnDist', 'HandSanit', 'Risk', 'Inefficacy', 'KnowlTrans', 'KnowlMgmt', 'Flu']]
print(forwardSelection(X, 'Flu'))
print('----------------------')

features = ['Risk', 'HndWshQual', 'PersnDist', 'KnowlMgmt', 'Vaccin']

for x in range(0, len(features)):
    subFeatures = features[0:x + 1]
    X = df[subFeatures]
    X = np.array(X)
    Y = df['Flu']
    Y = np.array(Y)

    # We'll do a 75/25 train/test split
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

    # Now fit the model...
    model = LogisticReg(alpha=0.01, iters=2000, regularType=None, C=0.01, costF = False)
    model.fitWeights(X_train, Y_train, tolr=10 ** -3)

    # Get the results
    positiveOrNegative, probIsPos = model.predict(X_test, 0.5)
    print("VARIABLES: ", subFeatures)
    model.reviewResults(positiveOrNegative, Y_test)

    clf = LogisticRegression()
    clf.fit(X_train, Y_train)
    scikit_score = clf.score(X_test, Y_test)
    print(scikit_score)
    print('----------------------')

X = df[['Risk', 'HndWshQual', 'PersnDist', 'KnowlMgmt', 'Vaccin', 'Inefficacy']]
X = np.array(X)
Y = df['Flu']
Y = np.array(Y)

# We'll do a 75/25 train/test split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

# Now fit the model...
model = LogisticReg(alpha=0.01, iters=2000, regularType=None, C=0.01, costF = False)
model.fitWeights(X_train, Y_train, tolr=10 ** -3)

# Get the results
positiveOrNegative, probIsPos = model.predict(X_test, 0.5)
print("VARIABLES: ", ['Risk', 'HndWshQual', 'PersnDist', 'KnowlMgmt', 'Vaccin', 'Inefficacy'])
model.reviewResults(positiveOrNegative, Y_test)

clf = LogisticRegression()
clf.fit(X_train, Y_train)
scikit_score = clf.score(X_test, Y_test)
print(scikit_score)
print('----------------------')

X = df[['Risk', 'HndWshQual', 'PersnDist', 'KnowlMgmt', 'Vaccin']]
X = np.array(X)
Y = df['Flu']
Y = np.array(Y)

# We'll do a 75/25 train/test split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

# Now fit the model...
model = LogisticReg(alpha=0.01, iters=2000, regularType='L2', C = 1, costF = False)
model.fitWeights(X_train, Y_train, tolr=10 ** -3)

# Get the results
positiveOrNegative, probIsPos = model.predict(X_test, 0.001)
print("Regularization")
model.reviewResults(positiveOrNegative, Y_test)

clf = LogisticRegression()
clf.fit(X_train, Y_train)
scikit_score = clf.score(X_test, Y_test)
print(scikit_score)
print('----------------------')

X = df[['Risk', 'HndWshQual', 'PersnDist', 'KnowlMgmt', 'Vaccin']]
X = np.array(X)
Y = df['Flu']
Y = np.array(Y)

# We'll do a 75/25 train/test split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

#Z-score normalization
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

# Now fit the model...
model = LogisticReg(alpha = 0.01, iters = 2000, regularType = None, C = 1, costF = False)
model.fitWeights(X_train, Y_train, tolr=10 ** -3)

# Get the results
positiveOrNegative, probIsPos = model.predict(X_test, 0.5)
print("Scaling")
model.reviewResults(positiveOrNegative, Y_test)

clf = LogisticRegression()
clf.fit(X_train, Y_train)
scikit_score = clf.score(X_test, Y_test)
print(scikit_score)
print('----------------------')

X = df[['Risk', 'HndWshQual', 'PersnDist', 'KnowlMgmt', 'Vaccin']]
X = np.array(X)
Y = df['Flu']
Y = np.array(Y)

# We'll do a 75/25 train/test split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25)

# Now fit the model...
model = LogisticReg(alpha=0.01, iters=2000, regularType = None, C = 1, costF = True)
model.fitWeights(X_train, Y_train, tolr=10 ** -3)

# Get the results
positiveOrNegative, probIsPos = model.predict(X_test, 0.001)
print("Alternate Cost Function")
model.reviewResults(positiveOrNegative, Y_test)

clf = LogisticRegression()
clf.fit(X_train, Y_train)
scikit_score = clf.score(X_test, Y_test)
print(scikit_score)
print('----------------------')