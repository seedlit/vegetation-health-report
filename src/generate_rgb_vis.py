import os
import numpy as np
import gdal
from matplotlib import pyplot as plt
from src import utils
from PIL import Image


def generate_rgb_array(r_band_path, g_band_path, b_band_path):
    r_array = gdal.Open(r_band_path).ReadAsArray()
    g_array = gdal.Open(g_band_path).ReadAsArray()
    b_array = gdal.Open(b_band_path).ReadAsArray()
    rgb_array = np.dstack((r_array, g_array, b_array))
    return rgb_array


def superimpose_cluster_on_rgb(
    rgb_path, cluster_img_path, out_img_path, transparency_factor=0.5
):
    rgb_img = Image.open(rgb_path)
    cluster_img = Image.open(cluster_img_path)
    rgb_img = rgb_img.convert("RGBA")
    cluster_img = cluster_img.convert("RGBA")
    cluster_img = cluster_img.resize(rgb_img.size)
    new_img = Image.blend(rgb_img, cluster_img, transparency_factor)
    new_img.save(out_img_path, "PNG")


def rgb_tif_from_bands(r_band_path, g_band_path, b_band_path, out_rgb_tif_path):
    rgb_array = generate_rgb_array(r_band_path, g_band_path, b_band_path)
    utils.save_array_as_geotif(rgb_array, r_band_path, out_rgb_tif_path)


if __name__ == "__main__":
    pass
