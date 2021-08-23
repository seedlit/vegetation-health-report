from src import utils
from src import fetch_data
from src import compute_ndvi
from src import cluster
from src import generate_ndvi_vis
from src import generate_folium_map
from src import generate_rgb_vis
from src import generate_pdf_report
from src import utils
import glob
import os
import argparse
from time import time
from tqdm import tqdm


def generate_health_report(
    aoi_path,
    start_date,
    end_date,
    out_dir,
    s2_bands_list,
    data_collection,
    cloud_cover_threshold,
    target_crs,
    n_clusters,
):

    # downloading data
    start_time = time()
    # applying buffer = 0 on aoi, to make it valid (in case it is invalid)
    utils.buffer(aoi_path, aoi_path, 0)
    fetch_data.fetch_cog_data(
        aoi_path,
        start_date,
        end_date,
        out_dir,
        s2_bands_list,
        data_collection,
        cloud_cover_threshold,
        target_crs,
    )
    print("############## Downloading took {} seconds".format(time() - start_time))

    # generating ndvi
    start_time = time()
    all_b04_paths = [
        f for f in glob.glob("{}/**/B04.tif".format(out_dir), recursive=True)
    ]
    for red_band_path in tqdm(all_b04_paths):
        print("working on ", red_band_path)
        nir_band_path = red_band_path.replace("B04", "B08")
        current_dir = red_band_path.replace("/B04.tif", "/generated_files")
        os.makedirs(current_dir, exist_ok=True)
        ndvi_tif_path = compute_ndvi.generate_ndvi_tif(
            nir_band_path, red_band_path, aoi_path, current_dir
        )

        # generating NDVI vis
        ndvi_vis_path = os.path.join(current_dir, "ndvi_vis.png")
        ndvi_classes_vis_path = os.path.join(current_dir, "ndvi_classes_vis.png")
        try:
            generate_ndvi_vis.save_ndvi_vis(ndvi_tif_path, ndvi_vis_path)
            generate_ndvi_vis.save_ndvi_classes_vis(
                ndvi_tif_path, ndvi_classes_vis_path
            )
        except Exception as e:
            print("some error occurred while generating NDVI")
            print("error :", e)

        # generating clustered img
        clustered_tif_path = os.path.join(current_dir, "clustered.tif")
        clustered_rgb_tif_path = os.path.join(current_dir, "clustered_rgb.tif")
        try:
            n_clusters = cluster.generate_clustered_img(
                ndvi_tif_path, clustered_tif_path, aoi_path, n_clusters=n_clusters
            )
            utils.gray_to_rgb(clustered_tif_path, clustered_rgb_tif_path)
        except Exception as e:
            print("some error occurred while clustering")
            print("error :", e)

        # generating rgb and superimposing clusters on rgb
        try:
            green_band_path = red_band_path.replace("B04", "B03")
            blue_band_path = red_band_path.replace("B04", "B02")
            rgb_tif_path = os.path.join(current_dir, "rgb.tif")
            generate_rgb_vis.rgb_tif_from_bands(
                red_band_path, green_band_path, blue_band_path, rgb_tif_path
            )
            rgb_png_path = rgb_tif_path.replace("rgb.tif", "rgb.png")
            utils.tif_to_png(rgb_tif_path, rgb_png_path)
            clustered_rgb_png_path = clustered_rgb_tif_path.replace(
                "clustered_rgb.tif", "clustered_rgb.png"
            )
            utils.tif_to_png(clustered_rgb_tif_path, clustered_rgb_png_path, False)
            superimposed_img_path = os.path.join(current_dir, "superimposed.png")
            generate_rgb_vis.superimpose_cluster_on_rgb(
                rgb_png_path, clustered_rgb_png_path, superimposed_img_path, 0.3
            )
        except Exception as e:
            print("some error occurred while generating RGB")
            print("error :", e)

        # generating folium map
        clustered_shp_path = os.path.join(current_dir, "clusters.shp")
        folium_map_path = os.path.join(current_dir, "clusters_map.html")
        try:
            generate_folium_map.generate_folium_map(
                clustered_tif_path,
                clustered_shp_path,
                folium_map_path,
                zoom_start_level=14,
            )
        except Exception as e:
            print("some error occurred while generating folium map")
            print("error :", e)

        # generating PDF report
        try:
            aoi_name = aoi_path.split("/")[-1].split(".")[0]
            date = red_band_path.split("/")[-3]
            out_pdf_path = os.path.join(
                current_dir, "generated_report_{}.pdf".format(date)
            )
            generate_pdf_report.generate_pdf(
                current_dir, aoi_name, date, n_clusters, out_pdf_path
            )
        except Exception as e:
            print("some error in generating pdf report")
            print("error ", e)

    print("############## Processing took {} seconds".format(time() - start_time))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Download COGs")
    parser.add_argument(
        "--aoi", help="path to aoi vector file (geojson or shapefile)", type=str
    )
    parser.add_argument(
        "--clusters",
        default=None,
        help="Number of clusters desired in output",
        type=int,
    )
    parser.add_argument(
        "--out_dir",
        default="generated_data",
        help="path to directory where data will be downloaded",
        type=str,
    )
    parser.add_argument(
        "--start_date", default=None, help="start date in YYYY-MM-DD format", type=str
    )
    parser.add_argument(
        "--end_date", default=None, help="end date in YYYY-MM-DD format", type=str
    )
    parser.add_argument(
        "--crs",
        help="target CRS of the generated data. If skipped, CRS will match input aoi's CRS",
        type=str,
    )
    parser.add_argument("--cloud_threshold", default=5, help="Cloud cover threshold")

    args = parser.parse_args()
    aoi_path = args.aoi
    out_dir = args.out_dir
    start_date = args.start_date
    end_date = args.end_date
    target_crs = args.crs
    cloud_cover_threshold = args.cloud_threshold
    n_clusters = args.clusters
    s2_bands_list = ["B02", "B03", "B04", "B08"]
    data_collection = "sentinel-s2-l2a-cogs"

    # B02 --> Blue
    # B03 --> Green
    # B04 --> Red
    # B08 --> NIR

    generate_health_report(
        aoi_path,
        start_date,
        end_date,
        out_dir,
        s2_bands_list,
        data_collection,
        cloud_cover_threshold,
        target_crs,
        n_clusters,
    )
