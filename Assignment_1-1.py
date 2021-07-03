###
# Benjamin Holmes
# Wright State University
# Assignment 1 - Machine Learning
# K-means and fuzzy c-means
# Problem 1 part 1 - k-means
###

# First, the imports. Numpy for number manipulation, pandas for dataframe handling, the others for
# convenience of operations.

## Initialization

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from scipy import stats
import copy
import Assignment_1_Dunn_Index as dunn

###
# Initial Housekeeping
###

###
# Randomness
# If set to true, we'll use a seed for repeatable trials. If false, we won't, and the trials will differ every time.
repeatableRandom = False
if repeatableRandom:
    np.random.seed(242)

###
# Here, enter the number of means we want.
###

# We're going to do a lot of repeats. the maxDunnCluster value will hold the # of clusters that has our greatest dunn clustering score.
maxDunnCluster = 0
# The maxDunn value will hold the actual max dunn value.
maxDunn = 0
for a in range(7, 8):
    for b in range(0, 10):
        k = a

        ###
        # This selects a random color for our clusters, for better visualization.
        # I want at least three to be RGB, so they're very seperable!
        number_of_colors = k
        color = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                     for i in range(number_of_colors)]
        # But let's a cheat a little and make the first three colors RGB
        color[0] = '#FF0000'
        if k > 1:
            color[1] = '#00FF00'
        if k > 2:
            color[2] = '#0000FF'

        ####
        # For the first assignment,
        # Columns are
        # ['Student', 'Vaccin', 'HndWshQual', 'HndWshFreq', 'SociDist',
        #        'NoFaceContact', 'RespEttiqu', 'PersnDist', 'HandSanit', 'Risk',
        #        'Complications', 'Barriers', 'Inefficacy', 'KnowlTrans', 'KnowlMgmt',
        #        'Sick', 'Flu', 'Female']
        data = pd.read_csv("/Users/bholmes/Desktop/Assign/Assignment1_data.csv", low_memory=False)
        #data = data[['Risk', 'NoFaceContact', 'Sick', 'HandSanit']]
        data = data[['Risk', 'NoFaceContact', 'Sick']]
        #data = data[['Risk', 'Barriers', 'Sick']]

        # We can't do 3d plots (for now) unless we only have 3 features!

        if len(data.columns) != 3:
            plotIt = False
        else:
            plotIt = True

        # You can also manually shut off the graph display here
        #plotIt = False
        plotIt = True

        # We're choosing to drop any rows with NA in them. If we had longer in the assignment, we might try to impute the missing values!
        data = data.dropna()
        data = data.reset_index(drop=True)

        # Let's handle some outlier removal, too
        # We'll remove anything with a z-score over 4
        for column in range(0, len(data.columns)):
            data['z_score'] = stats.zscore(data[data.columns[column]])
            data = data[data['z_score'] < 4]
        del data['z_score']
        data = data.reset_index(drop=True)

        # And we're also going to normalize all our axes!
        data=(data-data.min())/(data.max()-data.min())


        # This will define our initial centroids.
        # We pass in both the dataframe that we're going to use,
        # and the number of centroids, k
        # I'm assuming that every column which is put in will be either a float, double, or int.
        # If not, the process will throw an error.

        # I'm designing this to take an arbitrary dataframe, so I won't assume anything about the size
        # of the dataframe beforehand. I'm sure there are libraries that could do this more elegantly,
        # but for the purposes of this assignment I'm writing it from scratch.

        # We'll generate a list of lists. Every sub-list will be the points on one axis of the final centroid points.
        # So the list of lists [[1,2] [2,3]] would be the points 1,2 and 2,3
        # The list of lists [[1,2] [1,5] [1,10]] would be the points 1,1,1 and 2,5,10
        def getRandomInitialCentroids(dataframe, numCentroids):
            points = []
            for column in dataframe:
                axisLocations = []
                # Error out if we don't have a numeric column
                if dataframe[column].dtypes != 'float' and dataframe[column].dtypes != 'int' and dataframe[column].dtypes != 'double':
                    raise Exception("Dataframe has non-numeric columns!")
                values = dataframe[column]
                for i in range(0, numCentroids):
                    axisLocations.append(np.random.uniform(values.min(), values.max()))
                points.append(axisLocations)
            return points

        # This takes a dataframe and a list of lists (centroids) from getRandomInitialCentroids - This assumes a 3D Graph!
        # If we really wanted to build this out, it wouldn't be too hard to make a function that collapsed (or expanded) a dataframe into 3D
        def initialPlot3DDataframeAndCentroids(dataframe, centroids):
            if len(dataframe.columns) != 3 or len(centroids) != 3:
                raise Exception("Can't handle non-3D data!")
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.scatter(dataframe[dataframe.columns[0]], dataframe[dataframe.columns[1]], dataframe[dataframe.columns[2]], c='b', marker='o', s=2, jitter=True)
            for i in range(0, len(centroids[0])):
                ax.scatter(centroids[0][i], centroids[1][i], centroids[2][i], c=color[i], marker='x', s=60)
            ax.set_xlabel(dataframe.columns[0])
            ax.set_ylabel(dataframe.columns[1])
            ax.set_zlabel(dataframe.columns[2])
            plt.show()

        # This is to be run any time after the first assignment. Again, it only takes 3D data.
        # If we don't have 3D, project or expand the data to 3D first.
        def laterPlot3DDataframeAndCentroids(dataframe, centroids):
            if 'distance' not in dataframe.columns[3]:
                raise Exception("Can't handle non-3D data!")
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            for i in range(0, len(centroids[0])):
                ax.scatter(centroids[0][i], centroids[1][i], centroids[2][i], c=color[i], marker='x', s=60)
            for k in range(0, len(dataframe[dataframe.columns[0]])):
                ax.scatter(dataframe[dataframe.columns[0]][k], dataframe[dataframe.columns[1]][k], dataframe[dataframe.columns[2]][k], c=dataframe['color'][k], marker='o', s=2)
            ax.set_xlabel(dataframe.columns[0])
            ax.set_ylabel(dataframe.columns[1])
            ax.set_zlabel(dataframe.columns[2])
            plt.show()

        # I'm separating this out so we could more easily add other distance metrics in the future if needed
        # I'm expecting a dataframe with the same number of columns as the centroid that it's given.
        # centroidLoc is a list with coordinates of a centroid [1, 4.5, 3.2] for instance.
        # This returns a list of the euclidian distances of the centroid from each point in the DF.
        def euclidianDistance(dataframe, centroidLoc):
            distances = []
            # For every point in the dataframe...
            for k in range(0, len(dataframe[dataframe.columns[0]])):
                distance = 0
                for j in range(0, len(centroidLoc)):
                    distance = distance + ((dataframe[dataframe.columns[j]][k] - centroidLoc[j]) ** 2)
                distances.append(np.sqrt(distance))
            return distances

        # Now we'll assign centroids to a cluster.
        # Here, as before, dataframe is the dataframe of interest, and centroids is the list of list with centroids in it.
        def assignment(dataframe, centroids):
            # First, we need to err out if the centroids and dataframe aren't of the same dimensionatiy.
            if len(centroids) != len(dataframe.columns):
                print(centroids)
                print(dataframe)
                raise Exception("Can't assign centroids of different dimensionality to dataframe!")
            # we have i centroids, where i is the length of any sub-list.
            # we have j dimensions, where j is the length of the list of lists
            centroidsFull = []
            for i in range(0, len(centroids[0])):
                # Centroid location will be the position of a centroid (say, [1,2,3]).
                centroidLocation = []
                for j in range(0, len(centroids)):
                    centroidLocation.append(centroids[j][i])
                # At this point, centroidLocation is a list containing all coordinates for one centroid.
                # For every point in our dataframe, we'll take the euclidian distance.
                centroidsFull.append(centroidLocation)

            for i in range(0, len(centroidsFull)):
                cenDist = euclidianDistance(dataframe, centroidsFull[i])
                # And add a new column to the database, which is the euclidian distance of each point to one of the centroids
                dataframe['distance_from_centroid_{}'.format(i)] = (cenDist)

            # Ok, at this point we have k extra columns on our dataframe, each one with the distance of that point from a particular centroid.
            # Now let's find the lowest distance
            # that's the lowest number in the last k columns
            cols_with_distance = ['distance_from_centroid_{}'.format(i) for i in range(0, len(centroids[0]))]
            dataframe['closest'] = dataframe.loc[:, cols_with_distance].idxmin(axis=1)
            dataframe.to_csv("~/Desktop/Assign/DF.csv", index=False)
            dataframe['closest'] = dataframe['closest'].str.replace("distance_from_centroid_", '')
            dataframe['closest'] = dataframe['closest'].astype(int)
            dataframe['color'] = dataframe['closest'].map(lambda x: color[x])

            return dataframe

        # Once assigned, we update
        def update(cents):
            for j in range(0, len(cents[0])):
                for i in range(0, len(cents)):
                    cents[i][j] = np.mean(data[data['closest'] == j][data.columns[i]])
            return cents


        ################
        ### Here starts the main run of the program
        ################

        centroids = getRandomInitialCentroids(data, k)
        #initialPlot3DDataframeAndCentroids(data, centroids)
        origData = copy.deepcopy(data)
        origData2 = copy.deepcopy(origData)
        data = assignment(data, centroids)

        # We need to be convinced that we picked good initial centroids. I'm going to guess that we'll
        # want at least a few points in each centroid. Let's say 1/10 of the total at least!
        goodInitials = False
        while not goodInitials:
            while len(data['closest'].value_counts()) < k:
                centroids = getRandomInitialCentroids(origData, k)
                data = assignment(origData, centroids)
                origData = copy.deepcopy(origData2)
            goodInitials = True
            for value in data['closest'].value_counts():
                if value < 5:
                    print(data['closest'].value_counts())
                    goodInitials = False
            if not goodInitials:
                centroids = getRandomInitialCentroids(origData, k)
                data = assignment(origData, centroids)
                origData = copy.deepcopy(origData2)

        # Uncomment for mid-algorithm plots
        #if plotIt:
        #    laterPlot3DDataframeAndCentroids(data, centroids)
        previous_cents = copy.deepcopy(centroids)
        centroids = update(centroids)

        origCols = []
        for x in range(0, len(centroids)):
            origCols.append(data.columns[x])
        data = data[origCols]
        data = assignment(data, centroids)
        # Uncomment for mid-algorithm plots
        #if plotIt:
        #    laterPlot3DDataframeAndCentroids(data, centroids)

        while True:
            closest_centroids = copy.deepcopy(data['closest'])
            centroids = update(centroids)
            origCols = []
            for x in range(0, len(centroids)):
                origCols.append(data.columns[x])
            data = data[origCols]
            data = assignment(data, centroids)
            if closest_centroids.equals(data['closest']):
                break
            else:
                print('no')

        if plotIt:
            laterPlot3DDataframeAndCentroids(data, centroids)

        # Now time to get results - we'll use the dunn index imported from the other module we wrote!
        resultsCols = []
        for x in range(0, len(centroids)):
            resultsCols.append(data.columns[x])
        resultsCols.append('closest')
        results = data[resultsCols]

        cluster_list = []
        for i in range(0, k):
            clust_value = results.loc[results.closest == i]
            cluster_list.append(clust_value.values)

        print(cluster_list)

        input()
        dunnValue = dunn.dunnCalculator(cluster_list)
        if dunnValue > maxDunn:
            maxDunn = dunnValue
            maxDunnCluster = i

        #laterPlot3DDataframeAndCentroids(data, centroids)

print(maxDunnCluster)
print(maxDunn)