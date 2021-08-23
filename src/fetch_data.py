import satsearch
import geopandas as gpd
import datetime
import numpy as np
import os
import intake
import rioxarray
import rasterio
import argparse


def get_vector_bbox(vector_path):
    # get bounds of the input aoi vector file
    aoi_df = gpd.read_file(vector_path)
    aoi_geometry = aoi_df["geometry"]
    aoi_bounds = aoi_geometry.bounds
    aoi_bbox = [
        aoi_bounds["minx"][0],
        aoi_bounds["miny"][0],
        aoi_bounds["maxx"][0],
        aoi_bounds["maxy"][0],
    ]
    return aoi_bbox


def fetch_cog_data(
    vector_path,
    start_date,
    end_date,
    out_dir,
    s2_bands_list,
    data_collection,
    cloud_cover_threshold,
    target_crs=None,
):
    aoi_bbox = get_vector_bbox(vector_path)
    if start_date is None:
        start_date = datetime.datetime.today()
    else:
        cog_start_year = int(start_date.split("-")[0])
        cog_start_month = int(start_date.split("-")[1])
        cog_start_date = int(start_date.split("-")[2])
        start_date = datetime.datetime(cog_start_year, cog_start_month, cog_start_date)
    if end_date is None:
        end_date = datetime.datetime.today()
    else:
        cog_end_year = int(end_date.split("-")[0])
        cog_end_month = int(end_date.split("-")[1])
        cog_end_date = int(end_date.split("-")[2])
        end_date = datetime.datetime(cog_end_year, cog_end_month, cog_end_date)
    delta = end_date - start_date
    for i in range(delta.days + 1):
        day = start_date + datetime.timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        print("Querying COG for {}".format(date_str))
        results = query_cogs(data_collection, aoi_bbox, date_str, cloud_cover_threshold)
        generate_cog_data(
            out_dir, vector_path, s2_bands_list, date_str, results, target_crs
        )


def query_cogs(data_collection, bbox, date, cloud_cover_threshold):
    URL = "https://earth-search.aws.element84.com/v0"
    results = satsearch.Search.search(
        url=URL,
        collections=[data_collection],
        datetime=date,
        bbox=bbox,
        # sort=["<datetime"],
        sortby="-properties.eo:cloud_cover",
        **{"eo:cloud_cover": "0/{}".format(cloud_cover_threshold)},
    )
    return results


def generate_cog_data(out_dir, aoi_path, s2_bands, date_str, query_results, target_crs):
    if not query_results.found():
        print("No data avaialble for {}".format(date_str))

    else:
        print("Downloading data for {}".format(date_str))
        items = query_results.items()
        catalog = intake.open_stac_item_collection(items)
        for cog_num in range(0, np.shape(list(catalog))[0]):
            # if (
            #     cog_num > 0
            # ):  # only download data for the first result (assuming sorting works correctly)
            #     continue
            for band_name in s2_bands:
                tile_item = catalog[list(catalog)[cog_num]]
                ds_band = get_band_from_cog(band_name, tile_item)
                cog_crs = get_cog_tile_crs(tile_item)
                band_field = subset_cog(aoi_path, ds_band, cog_crs)
                # subsetting increases clipping speed
                if target_crs is None:
                    # then reproject to the source vector file's crs
                    target_crs = int(str(gpd.read_file(aoi_path).crs).split(":")[1])
                band_field_reproject = reproject_cog(band_field, cog_crs, target_crs)
                field_name = aoi_path.split("/")[-1].split(".")[0]
                cogs_out_dir = os.path.join(
                    out_dir, field_name, date_str, str(cog_num + 1)
                )
                os.makedirs(cogs_out_dir, exist_ok=True)
                out_path = os.path.join(cogs_out_dir, "{}.tif".format(band_name))
                band_field_reproject.rio.to_raster(out_path)
        return None


def get_cog_tile_crs(tile_item):
    crs_out = tile_item.metadata["proj:epsg"]
    return crs_out


def get_band_from_cog(band_name, tile_item):
    return tile_item[band_name].to_dask()


def subset_cog(aoi_geojson, cog_ds, tile_crs):
    aoi_vector = gpd.read_file(aoi_geojson)
    field_data = aoi_vector.to_crs(epsg=tile_crs)
    bbox_transform = field_data.bounds
    subset = cog_ds.sel(
        y=slice(int(bbox_transform["maxy"]), int(bbox_transform["miny"])),
        x=slice(int(bbox_transform["minx"]), int(bbox_transform["maxx"])),
    )
    return subset


def reproject_cog(cog_ds, cog_crs, target_crs):
    crs = "EPSG:" + str(cog_crs)
    cog_ds = cog_ds.rio.write_crs(crs)
    crs = "EPSG:" + str(target_crs)
    ds = cog_ds.rio.reproject(crs)
    return ds


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Download COGs")
    parser.add_argument(
        "--aoi", help="path to aoi vector file (geojson or shapefile)", type=str
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
    parser.add_argument(
        "--bands_list",
        default=["B04", "B08"],
        help="List of bands to be downloaded",
        type=list,
    )
    parser.add_argument(
        "--collection",
        default="sentinel-s2-l2a-cogs",
        help="Which data collection should be downloaded",
        type=str,
    )

    args = parser.parse_args()
    aoi_path = args.aoi
    out_dir = args.out_dir
    start_date = args.start_date
    end_date = args.end_date
    target_crs = args.crs
    cloud_cover_threshold = args.cloud_threshold
    bands_list = args.bands_list
    data_collection = args.collection
    fetch_cog_data(
        aoi_path,
        start_date,
        end_date,
        out_dir,
        bands_list,
        data_collection,
        cloud_cover_threshold,
        target_crs,
    )

    # available s2 bands:
    # bands_list = [
    #         "AOT",
    #         "B01",
    #         "B02",
    #         "B03",
    #         "B04",
    #         "B05",
    #         "B06",
    #         "B07",
    #         "B08",
    #         "B09",
    #         "B11",
    #         "B12",
    #         "B8A",
    #         "SCL",
    #         "WVP",
    #     ]
