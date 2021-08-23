import os
import earthpy.plot as ep
import gdal
import numpy as np
from matplotlib import pyplot as plt


if __name__ == "__main__":

    # plotting the NIR (B08), Red (B04), Green (B03), and Blue (B02) bands
    nir_band_path = "B08.tif"
    red_band_path = "B04.tif"
    green_band_path = "B03.tif"
    blue_band_path = "B02.tif"
    nir_array = gdal.Open(nir_band_path).ReadAsArray()
    red_array = gdal.Open(red_band_path).ReadAsArray()
    green_array = gdal.Open(green_band_path).ReadAsArray()
    blue_array = gdal.Open(blue_band_path).ReadAsArray()
    stacked_array = np.array([nir_array, red_array, green_array, blue_array])
    titles = ["NIR", "Red", "Green", "Blue"]
    ep.plot_bands(stacked_array, title=titles, cols=2, scale=True)
    plt.show()
    # plt.savefig(out_path)
