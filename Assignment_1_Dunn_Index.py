import numpy as np

### Supplemental File
# Ben Holmes
# Dunn index calculator. This attempts to find the Dunn index given
# an array list. Each cluster has an array. This contains all the features
# (all positions but the last) and the cluster the point belongs to (the last position)

def dunnCalculator(clusters):
    # Make the nxn matrix... (and increase the values for a steeper drop)
    lowercaseDeltas = np.ones([len(clusters), len(clusters)]) * 100
    # And the nx1 zeroing matrix...
    uppercaseDeltas = np.zeros([len(clusters), 1])
    # We'll want every position.
    sizeOfClusterList = []
    for place in range(0, len(clusters)):
        sizeOfClusterList.append(place)
    # now, for every combination of clusters, we find the distance between them...
    for i in sizeOfClusterList:
        for j in (sizeOfClusterList[0:i] + sizeOfClusterList[i + 1:]):
            lowercaseDeltas[i, j] = numerator(clusters[i], clusters[j])
        # And we find the distance WITHIN a cluster as well.
        uppercaseDeltas[i] = denominator(clusters[j])
    # The dunn index is the min. INTER cluster diff over the max INTRA cluster diff
    dunnIndex = np.min(lowercaseDeltas) / np.max(uppercaseDeltas)
    return dunnIndex

# Getting the numerator means finding the minimum distance BETWEEN clusters. We'd like this to be large.
def numerator(clusterNum, clusterLen):
    values = np.ones([len(clusterNum), len(clusterLen)]) * 100
    for i in range(0, len(clusterNum)):
        for j in range(0, len(clusterLen)):
            values[i, j] = np.linalg.norm(clusterNum[i] - clusterLen[j])
    return np.min(values)

# The denominator wants the distance WITHIN a cluster. We want this to be small.
def denominator(clusterEdges):
    values = np.zeros([len(clusterEdges), len(clusterEdges)])
    for i in range(0, len(clusterEdges)):
        for j in range(0, len(clusterEdges)):
            values[i, j] = np.linalg.norm(clusterEdges[i] - clusterEdges[j])

    return np.max(values)