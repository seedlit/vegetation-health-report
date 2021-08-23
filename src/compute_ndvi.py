import os
import gdal
from src import utils


def generate_ndvi_tif(nir_band_path, red_band_path, aoi_vector_path, out_dir):
    nir_array = gdal.Open(nir_band_path).ReadAsArray().astype(float)
    red_array = gdal.Open(red_band_path).ReadAsArray().astype(float)
    # calculating NDVI
    ndvi_array = (nir_array - red_array) / (nir_array + red_array)
    # saving this array as geotif
    ndvi_tif_out_path = os.path.join(out_dir, "ndvi.tif")
    utils.save_array_as_geotif(ndvi_array, nir_band_path, ndvi_tif_out_path)
    # clipping NDVI tif wrt AOI
    clipped_ndvi_tif_out_path = os.path.join(out_dir, "ndvi_clipped.tif")
    utils.clip_tif(ndvi_tif_out_path, aoi_vector_path, clipped_ndvi_tif_out_path)
    return clipped_ndvi_tif_out_path


if __name__ == "__main__":
    pass
