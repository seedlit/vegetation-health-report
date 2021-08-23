from src import utils
import folium
import geopandas as gpd
import matplotlib.pyplot as plt


def plot_shp(shp_path, field_name="DN"):
    fig, ax = plt.subplots(figsize=(12, 6))
    vector_df = gpd.read_file(shp_path)
    vector_df.plot(ax=ax, color="lightgrey")
    vector_df.plot(column=field_name, ax=ax, cmap="viridis")
    ax.set_axis_off()
    plt.show()


def get_shp_centroid(shp_path):
    vector_df = gpd.read_file(shp_path)
    bounds = vector_df.total_bounds
    lat_centroid = (bounds[1] + bounds[3]) / 2
    lon_centroid = (bounds[0] + bounds[2]) / 2
    return lat_centroid, lon_centroid


def save_folium_map(
    vector_path, map_out_path, key_field, value_field, zoom_start_level
):
    vector_df = gpd.read_file(vector_path)
    lat_centroid, lon_centroid = get_shp_centroid(vector_path)
    # plot base map
    m = folium.Map(
        location=[lat_centroid, lon_centroid],  # center of the folium map
        tiles="cartodbpositron",  # type of map
        zoom_start=zoom_start_level,
    )  # initial zoom

    # plot chorpleth over the base map
    folium.Choropleth(
        vector_df,
        data=vector_df,
        key_on="feature.properties.{}".format(key_field),  # feature.properties.key
        columns=[key_field, value_field],  # [key, value]
        # fill_color='RdPu',
        fill_color="RdBu",  # cmap
        line_weight=0.1,  # line wight (of the border)
        line_opacity=0.5,  # line opacity (of the border)
        legend_name="zones",
    ).add_to(
        m
    )  # name on the legend color bar

    # add layer controls
    folium.LayerControl().add_to(m)
    m.save(map_out_path)
    # # also saving as png
    # from PIL import Image
    # import io
    # from selenium import webdriver
    # import time
    # img_data = m._to_png(0.001)
    # img = Image.open(io.BytesIO(img_data))
    # img.save(map_out_path.replace(".html", ".png"))
    # # # temp hack
    # # browser = webdriver.Firefox()
    # # browser.get(map_out_path)
    # # #Give the map tiles some time to load
    # # time.sleep(0.001)
    # # browser.save_screenshot(map_out_path.replace(".html", ".png"))
    # # browser.quit()


def generate_folium_map(
    src_tif_path,
    out_shp_path,
    out_map_path,
    key_field="poly",
    value_field="DN",
    zoom_start_level=13,
):
    utils.polygonize_raster(src_tif_path, out_shp_path)
    utils.remove_background(out_shp_path, 0.0)
    utils.add_field(out_shp_path, key_field)
    save_folium_map(
        out_shp_path, out_map_path, key_field, value_field, zoom_start_level
    )


if __name__ == "__main__":
    pass
