import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import earthpy.plot as ep
import gdal
import gc


def save_ndvi_vis(ndvi_tif_path, out_img_path):
    ndvi_array = gdal.Open(ndvi_tif_path).ReadAsArray()
    plt.figure()
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_title("Normalized Difference Vegetation Index (NDVI)")
    plt.imshow(ndvi_array, vmin=-1, vmax=1, cmap="RdYlGn")
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(out_img_path)
    plt.close()  # for releasing memory
    gc.collect()  # for releasing memory


def save_ndvi_classes_vis(ndvi_tif_path, out_img_path):
    ndvi_array = gdal.Open(ndvi_tif_path).ReadAsArray()
    # classify ndvi
    # Create classes and apply to NDVI results
    ndvi_class_bins = [-np.inf, 0, 0.1, 0.25, 0.4, np.inf]
    ndvi_landsat_class = np.digitize(ndvi_array, ndvi_class_bins)
    # Apply the nodata mask to the newly classified NDVI data
    ndvi_landsat_class = np.ma.masked_where(
        np.ma.getmask(ndvi_array), ndvi_landsat_class
    )
    np.unique(ndvi_landsat_class)
    # Define color map
    nbr_colors = ["gray", "y", "yellowgreen", "g", "darkgreen"]
    nbr_cmap = ListedColormap(nbr_colors)
    # Define class names
    ndvi_cat_names = [
        "No Vegetation",
        "Bare Area",
        "Low Vegetation",
        "Moderate Vegetation",
        "High Vegetation",
    ]
    # Get list of classes
    classes = np.unique(ndvi_landsat_class)
    classes = classes.tolist()
    # The mask returns a value of none in the classes. remove that
    classes = classes[0:5]
    # Plot your data
    fig, ax = plt.subplots(figsize=(12, 9))
    im = ax.imshow(ndvi_landsat_class, cmap=nbr_cmap)
    ep.draw_legend(im_ax=im, classes=classes, titles=ndvi_cat_names)
    ax.set_title(
        "Normalized Difference Vegetation Index (NDVI) Classes",
        fontsize=14,
    )
    ax.set_axis_off()
    # Auto adjust subplot to fit figure size
    plt.tight_layout()
    plt.savefig(out_img_path)
    plt.close()  # for releasing memory
    gc.collect()  # for releasing memory


if __name__ == "__main__":
    pass
