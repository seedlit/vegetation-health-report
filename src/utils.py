import os
import gdal
import ogr
import osr
import numpy as np
import geopandas as gpd
from PIL import Image


def save_array_as_geotif(array, source_tif_path, out_path, precision="float"):
    """
    Generates a geotiff raster from the input numpy array (height * width * depth)
    Input:
        array: {numpy array} numpy array to be saved as geotiff
        source_tif_path: {string} path to the geotiff from which projection and geotransformation information will be extracted.
    Output:
        out_path: {string} path to the generated Geotiff raster
    """
    if len(array.shape) > 2:
        height, width, depth = array.shape
    else:
        height, width = array.shape
        depth = 1
    source_tif = gdal.Open(source_tif_path)
    driver = gdal.GetDriverByName("GTiff")
    if precision == "float":
        dataset = driver.Create(out_path, width, height, depth, gdal.GDT_Float32)
    else:
        dataset = driver.Create(out_path, width, height, depth, gdal.GDT_Byte)
    if depth != 1:
        for i in range(depth):
            dataset.GetRasterBand(i + 1).WriteArray(array[:, :, i])
    else:
        dataset.GetRasterBand(1).WriteArray(array)
    geotrans = source_tif.GetGeoTransform()
    proj = source_tif.GetProjection()
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    dataset = None


def clip_tif(src_tif_path, vector_path, out_tif_path):
    if os.path.isfile(out_tif_path):
        os.remove(out_tif_path)
    try:
        os.system(
            "gdalwarp -q -of GTiff -cutline {} -crop_to_cutline {} {}".format(
                vector_path, src_tif_path, out_tif_path
            )
        )
    except Exception as e:
        print(e)
        print("some issue in clipping")


def polygonize_raster(raster_path, out_vector_path):
    sourceRaster = gdal.Open(raster_path)
    band = sourceRaster.GetRasterBand(1)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    outShp = out_vector_path
    # If shapefile already exist, delete it
    if os.path.exists(outShp):
        driver.DeleteDataSource(outShp)
    outDatasource = driver.CreateDataSource(outShp)
    # get proj from raster
    srs = osr.SpatialReference()
    srs.ImportFromWkt(sourceRaster.GetProjectionRef())
    # create layer with proj
    outLayer = outDatasource.CreateLayer(outShp, srs)
    # Add class column (0,255) to shapefile
    newField = ogr.FieldDefn("DN", ogr.OFTReal)
    outLayer.CreateField(newField)
    # gdal.Polygonize(band, None, outLayer, 0, [], callback=None)
    gdal.FPolygonize(band, None, outLayer, 0, [], callback=None)
    outDatasource.Destroy()
    sourceRaster = None


def add_field(shp_path, field_name):
    source = ogr.Open(shp_path, update=True)
    layer = source.GetLayer()
    # Add a new field
    new_field = ogr.FieldDefn(field_name, ogr.OFTString)
    layer.CreateField(new_field)
    count = 1
    for i in layer:
        i.SetField(field_name, "poly_{}".format(count))
        layer.SetFeature(i)
        count += 1
    source = None


# def remove_background(shp_path, remove_DN_value=0):
#     ds = ogr.Open(shp_path, update=True)  # True allows to edit the shapefile
#     lyr = ds.GetLayer()
#     i = 0
#     for _ in lyr:
#         if _["DN"] == remove_DN_value:
#             lyr.DeleteFeature(i)
#             i += 1
#     lyr = None
#     ds.Destroy()


def remove_background(shp_path, remove_DN_value=0):
    vector_df = gpd.read_file(shp_path)
    vector_df.drop(vector_df.index[vector_df["DN"] == remove_DN_value], inplace=True)
    vector_df.to_file(shp_path)


def gray_to_rgb(in_img_path, out_img_path):
    gray_img_array = gdal.Open(in_img_path).ReadAsArray()
    unique_values = np.unique(gray_img_array)
    rgb_array = np.dstack((gray_img_array, gray_img_array, gray_img_array))
    for i in range(len(unique_values)):
        value = unique_values[i]
        if value == 0:
            rgb_array[rgb_array == value] = 17
        else:
            try:
                rgb_array[:, :, i % 3][rgb_array[:, :, i % 3] == value] = 255 / i
            except:
                rgb_array[:, :, i % 3][rgb_array[:, :, i % 3] == value] = 255 / (i + 1)
    save_array_as_geotif(rgb_array, in_img_path, out_img_path, "byte")
    set_no_data_value(out_img_path)


def set_no_data_value(tif_path):
    ds = gdal.Open(tif_path, 1)  # The 1 means that you are opening the file to edit it)
    for i in range(3):
        rb = ds.GetRasterBand(i + 1)  # assuming our raster has 3 bands
        rb.SetNoDataValue(17)
        rb = None
    ds = None


def tif_to_png(src_tif_path, out_png_path, rgb=True):  # hack
    # also rescales from float to Byte
    src_array = gdal.Open(src_tif_path).ReadAsArray()
    # transposing to proper shape
    src_array = np.transpose(src_array, (1, 2, 0))
    if rgb:
        # for i in range(src_array.shape[2]):
        #     src_array[:,:,i] /= src_array[:,:,i].max()
        src_array /= src_array.max()
    else:
        # for i in range(src_array.shape[2]):
        #     np.multiply(src_array[:,:,i], src_array[:,:,i].max(), out=src_array[:,:,i], casting="unsafe")
        np.multiply(src_array, src_array.max(), out=src_array, casting="unsafe")
    out_img = Image.fromarray((src_array * 255).astype(np.uint8))
    out_img.save(out_png_path)


def buffer(in_path, out_path, buffer_radius=0, driver="GeoJSON"):
    vector = gpd.read_file(in_path)
    buffer_file = vector.copy()
    buffer_file.geometry = buffer_file["geometry"].buffer(buffer_radius)
    buffer_file.to_file(out_path, driver=driver)


if __name__ == "__main__":
    pass
