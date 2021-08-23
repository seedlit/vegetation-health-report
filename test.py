import os
import shutil
from src import fetch_data
from src import utils
from src import generate_ndvi_vis
from src import cluster
from src import generate_rgb_vis
from src import generate_folium_map
from src import generate_pdf_report
import intake
import shutil
import gdal


if __name__ == "__main__":

    aoi_path = "resources/test_aoi_river.geojson"

    # --------------------------------------------------------------------------------
    # running tests for fetch.py
    print("Sit back and relax! It could take up to a couple of minutes.")
    print("Running tests for src/fetch.py")

    utils.buffer(aoi_path, aoi_path, 0)
    assert os.path.isfile(aoi_path)

    aoi_bbox = fetch_data.get_vector_bbox(aoi_path)
    assert aoi_bbox == [
        78.04753759156934,
        29.53322085043803,
        78.0706313593568,
        29.549581413721345,
    ]

    data_collection = "sentinel-s2-l2a-cogs"
    query_results = fetch_data.query_cogs(data_collection, aoi_bbox, "2021-08-17", 5)
    assert query_results.found() == 2

    items = query_results.items()
    catalog = intake.open_stac_item_collection(items)
    tile_item = catalog[list(catalog)[0]]
    ds_band = fetch_data.get_band_from_cog("B02", tile_item)
    assert ds_band.shape == (1, 10980, 10980)

    cog_crs = fetch_data.get_cog_tile_crs(tile_item)
    assert cog_crs == 32644

    band_field = fetch_data.subset_cog(aoi_path, ds_band, cog_crs)
    assert band_field.shape == (1, 187, 229)

    band_field_reproject = fetch_data.reproject_cog(band_field, cog_crs, 4326)
    assert band_field_reproject.rio.crs == 4326

    out_dir = "tests_results"
    os.makedirs(out_dir, exist_ok=True)
    band_field_reproject.rio.to_raster(os.path.join(out_dir, "test_B02.tif"))
    assert os.path.isfile(os.path.join(out_dir, "test_B02.tif"))

    # removing temporary directory
    shutil.rmtree(out_dir)

    # --------------------------------------------------------------------------------
    # running tests for src/compute_ndvi.py
    print("running tests for src/compute_ndvi.py")
    fetch_data.fetch_cog_data(
        aoi_path,
        "2021-08-17",
        "2021-08-17",
        out_dir,
        ["B02", "B03", "B04", "B08"],
        data_collection,
        5,
        4326,
    )

    aoi_name = aoi_path.split("/")[-1].split(".")[0]
    out_dir = os.path.join(out_dir, aoi_name)
    # os.makedirs(out_dir, exist_ok=True)
    nir_band_path = os.path.join(out_dir, "2021-08-17", "1", "B08.tif")
    red_band_path = os.path.join(out_dir, "2021-08-17", "1", "B04.tif")
    nir_array = gdal.Open(nir_band_path).ReadAsArray().astype(float)
    red_array = gdal.Open(red_band_path).ReadAsArray().astype(float)
    ndvi_array = (nir_array - red_array) / (nir_array + red_array)
    out_dir = os.path.join(out_dir, "2021-08-17", "1", "generated_files")
    os.makedirs(out_dir, exist_ok=True)
    ndvi_tif_out_path = os.path.join(out_dir, "ndvi.tif")
    utils.save_array_as_geotif(ndvi_array, nir_band_path, ndvi_tif_out_path)
    assert os.path.isfile(ndvi_tif_out_path)

    clipped_ndvi_tif_out_path = os.path.join(out_dir, "ndvi_clipped.tif")
    utils.clip_tif(ndvi_tif_out_path, aoi_path, clipped_ndvi_tif_out_path)
    assert os.path.isfile(clipped_ndvi_tif_out_path)

    # ----------------------------------------------------------------------------------
    print("Running tests for src/generate_ndvi_vis.py")

    ndvi_vis_path = os.path.join(out_dir, "ndvi_vis.png")
    generate_ndvi_vis.save_ndvi_vis(clipped_ndvi_tif_out_path, ndvi_vis_path)
    assert os.path.isfile(ndvi_vis_path)

    ndvi_classes_vis_path = os.path.join(out_dir, "ndvi_classes_vis.png")
    generate_ndvi_vis.save_ndvi_classes_vis(ndvi_tif_out_path, ndvi_classes_vis_path)
    assert os.path.isfile(ndvi_classes_vis_path)

    # ----------------------------------------------------------------------------------
    print("Running tests for src/cluster.py")
    clustered_tif_path = os.path.join(out_dir, "clustered.tif")
    src_array = gdal.Open(clipped_ndvi_tif_out_path).ReadAsArray()
    clustered_array, n_clusters = cluster.cluster_kmeans(src_array, None)
    assert n_clusters == 2
    assert clustered_array.shape == (165, 233)
    utils.save_array_as_geotif(
        clustered_array, clipped_ndvi_tif_out_path, clustered_tif_path
    )
    clustered_rgb_tif_path = os.path.join(out_dir, "clustered_rgb.tif")
    utils.gray_to_rgb(clustered_tif_path, clustered_rgb_tif_path)
    assert os.path.isfile(clustered_rgb_tif_path)

    # ----------------------------------------------------------------------------------
    print("Running tests for src/generate_rgb_vis.py")
    green_band_path = red_band_path.replace("B04", "B03")
    blue_band_path = red_band_path.replace("B04", "B02")
    rgb_tif_path = os.path.join(out_dir, "rgb.tif")
    generate_rgb_vis.rgb_tif_from_bands(
        red_band_path, green_band_path, blue_band_path, rgb_tif_path
    )
    assert os.path.isfile(rgb_tif_path)
    rgb_png_path = rgb_tif_path.replace("rgb.tif", "rgb.png")
    utils.tif_to_png(rgb_tif_path, rgb_png_path)
    assert os.path.isfile(rgb_png_path)
    clustered_rgb_png_path = clustered_rgb_tif_path.replace(
        "clustered_rgb.tif", "clustered_rgb.png"
    )
    utils.tif_to_png(clustered_rgb_tif_path, clustered_rgb_png_path, False)
    assert os.path.isfile(clustered_rgb_png_path)
    superimposed_img_path = os.path.join(out_dir, "superimposed.png")
    generate_rgb_vis.superimpose_cluster_on_rgb(
        rgb_png_path, clustered_rgb_png_path, superimposed_img_path, 0.3
    )
    assert os.path.isfile(superimposed_img_path)

    # ----------------------------------------------------------------------------------
    print("Running tests for src/generate_folium_map.py")
    clustered_shp_path = os.path.join(out_dir, "clusters.shp")
    folium_map_path = os.path.join(out_dir, "clusters_map.html")
    generate_folium_map.generate_folium_map(
        clustered_tif_path,
        clustered_shp_path,
        folium_map_path,
        zoom_start_level=14,
    )
    assert os.path.isfile(folium_map_path)

    # ----------------------------------------------------------------------------------
    print("Running tests for src/generate_pdf_report.py")
    out_pdf_path = os.path.join(out_dir, "test_report.pdf")
    generate_pdf_report.generate_pdf(
        out_dir, aoi_name, "2018-08-17", n_clusters, out_pdf_path
    )
    assert os.path.isfile(out_pdf_path)

    # ----------------------------------------------------------------------------------
    out_dir = "tests_results"
    shutil.rmtree(out_dir)
    print("All tests passed!")
