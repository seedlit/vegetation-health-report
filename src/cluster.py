import os
import numpy as np
from src import utils
from sklearn.cluster import KMeans
from sklearn.utils import shuffle
from kneed import KneeLocator
from time import time
import gdal


def recreate_image(custer_centers, labels, w, h):
    """Recreate the image from the custer_centers & labels"""
    d = custer_centers.shape[1]
    image = np.zeros((w, h, d))
    label_idx = 0
    for i in range(w):
        for j in range(h):
            image[i][j] = custer_centers[labels[label_idx]]
            label_idx += 1
    return image


def plot_elbow_curve(data_array, max_clusters=15):
    start_time = time()
    sum_of_squared_error = {}
    for k in range(1, max_clusters):
        km = KMeans(n_clusters=k)
        km = km.fit(data_array)
        sum_of_squared_error[k] = km.inertia_
    # from matplotlib import pyplot as plt
    # plt.plot(range(1, max_clusters), list(sum_of_squared_error.values()), "bx-")
    # plt.xlabel("k")
    # plt.ylabel("Sum_of_squared_distances")
    # plt.title("Elbow Method For Optimal k")
    # plt.show()
    kn = KneeLocator(
        x=list(sum_of_squared_error.keys()),
        y=list(sum_of_squared_error.values()),
        curve="convex",
        direction="decreasing",
    )
    print("Plotted elbow curve in %0.3fs." % (time() - start_time))
    return kn.knee


def cluster_kmeans(src_array, n_clusters):
    """
    src_array: 2D array
    n_clusters: int number of clusters
    """
    start_time = time()
    if len(src_array.shape) == 2:
        w, h = tuple(src_array.shape)
        d = 1
    else:
        w, h, d = tuple(src_array.shape)
    image_array = np.reshape(src_array, (w * h, d))
    image_array_sample = shuffle(image_array, random_state=0)
    if n_clusters is None:
        n_clusters = plot_elbow_curve(image_array)
        print("######### identified num_clusters = ", n_clusters)
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(image_array_sample)
    # Get labels for all points
    # predicting clusters on the full image
    start_time = time()
    labels = kmeans.predict(image_array)
    image = recreate_image(kmeans.cluster_centers_, labels, w, h)
    image = np.reshape(image, (w, h))
    print("Clustered in %0.3fs." % (time() - start_time))
    return image, n_clusters


def generate_clustered_img(in_img_path, out_img_path, vector_path, n_clusters):
    src_array = gdal.Open(in_img_path).ReadAsArray()
    clustered_array, n_clusters = cluster_kmeans(src_array, n_clusters)
    temp_clustered_path = (
        out_img_path.split(".")[0] + "_temp." + out_img_path.split(".")[1]
    )
    utils.save_array_as_geotif(clustered_array, in_img_path, temp_clustered_path)
    utils.clip_tif(temp_clustered_path, vector_path, out_img_path)
    return n_clusters


if __name__ == "__main__":
    pass
