from sys import stdout
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random
from scipy import stats
import Assignment_1_Dunn_Index as dunn

###
# Benjamin Holmes
# Wright State University
# Assignment 1 - Machine Learning
# K-means and fuzzy c-means
# Problem 1 part 2 - fuzzy c-means
###


# K is our # of clusters again
k = 7

# A fuzziness of 1 means a 'hard' decision boundary. Higher numbers mean more fuzzy!
fuzz_factor = 2
stopping_threshold=0.0000000001
max_iterations = 400

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
# For the first assignment, (comment in whichever combo of featues we want)
data = pd.read_csv("/Users/bholmes/Desktop/Assign/Assignment1_data.csv", low_memory=False)
data = data[['Risk', 'Sick', 'Inefficacy']]
#data = data[['Risk', 'NoFaceContact', 'Sick']]

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
data = (data - data.min()) / (data.max() - data.min())
dataframe = data
data = data.values

# We can't do 3d plots (for now) unless we only have 3 features!

if len(dataframe.columns) != 3:
    plotIt = False
else:
    plotIt = True

# You can also manually shut off the graph display here
# plotIt = False
plotIt = False

# Let's get the length of things
length = data.shape[0]

# Random initial centroids
points = []
for column in dataframe:
    axisLocations = []
    values = dataframe[column]
    for i in range(0, k):
        axisLocations.append(np.random.uniform(values.min(), values.max()))
    points.append(axisLocations)

centroids = []
for j in range(0, k):
    point = []
    for i in range(0, len(points)):
        point.append(points[i][j])
    centroids.append(point)

centroids = np.array(centroids)
#print(centroids)

# This will start up our partition matrix with some random values
# We'll then normalize it.
f_matrix = np.random.randint(low=100, high=200, size=(length, k))
f_matrix = f_matrix / f_matrix.sum(axis=1, keepdims=True)

# Now we need to optimize on the squared error.
# SSE is
f_matrix_fuzzed = np.power(f_matrix, fuzz_factor)
err_sum_squares = 0

# We calculate the squared err.
for j in range(k):
    for i in range(length):
        distanceSquared = np.linalg.norm(data[[i]] - centroids[j]) ** 2
        prob = f_matrix_fuzzed[i][j]
        err_sum_squares = err_sum_squares + prob * distanceSquared

trials = 1

# This is now the main loop. We'll update our centroids, then update the partition matrix, then re-calculate the SSE
while trials < max_iterations:
    # Print iteration number for clarity of progress
    print("Trial # {}...".format(trials))
    print(str(err_sum_squares))
    trials = trials + 1

    # Each element powered to the fuzz factor, then divide each column by the sum
    f_matrix_fuzzed = np.power(f_matrix, fuzz_factor)
    f_matrix_fuzzed = f_matrix_fuzzed / f_matrix_fuzzed.sum(axis=0, keepdims=True)

    # Numpy to the rescue again, with a handy matrix multiplication!
    centroid_update = np.matmul(f_matrix_fuzzed.T, data)

    # Update the partition matrix
    updated_f_matrix = np.zeros(shape=(length, k))
    leng = updated_f_matrix.shape[0]
    wid = updated_f_matrix.shape[1]
    for i in range(leng):
        for j in range(wid):
            updated_f_matrix[i][j] = 1 / np.linalg.norm(data[i] - centroid_update[j])

    updated_f_matrix = np.power(updated_f_matrix, 2 / (fuzz_factor - 1))

    updated_f_matrix = updated_f_matrix / updated_f_matrix.sum(axis=1, keepdims=True)

    # Now we find the new SSE
    updated_f_matrix_fuzzed = np.power(updated_f_matrix, fuzz_factor)
    new_err_sum_squares = 0
    for j in range(k):
        for i in range(length):
            distanceSquared = np.linalg.norm(data[[i]] - centroid_update[j]) ** 2
            prob = updated_f_matrix_fuzzed[i][j]
            new_err_sum_squares = new_err_sum_squares + prob * distanceSquared

    # We stop when we've reached the max number of iterations, OR when the difference between two trials is below epsilon.
    # Otherwise, we keep updating
    if (err_sum_squares - new_err_sum_squares) < stopping_threshold:
        break
    centroids = centroid_update.copy()
    f_matrix = updated_f_matrix.copy()
    err_sum_squares = new_err_sum_squares

max_membership_indices = np.argmax(f_matrix, axis=1)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
# We have our color list from before - we'll use that to color in the clusters
for i in range(f_matrix.shape[0]):

    max_membership_idx = max_membership_indices[i]
    for j in range(0, len(color)):
        if (max_membership_idx == j):
            ax.scatter(data[i][0], data[i][1], data[i][2], c=color[j], marker='o', s=2)

for i in range(0, len(centroids)):
    ax.scatter(centroids[i][0], centroids[i][1], centroids[i][2], c=color[i], marker='x', s=60)

ax.set_xlabel(dataframe.columns[0])
ax.set_ylabel(dataframe.columns[1])
ax.set_zlabel(dataframe.columns[2])
if plotIt:
    plt.show()
print('\n')
dataframe['closest'] = max_membership_indices
clusters = []
for i in range(0, k):
    clust_value = dataframe.loc[dataframe.closest == i]
    clusters.append(clust_value.values)
#print(cluster_list)
dunnValue = dunn.dunnCalculator(clusters)
print(dunnValue)