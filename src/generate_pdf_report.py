from fpdf import FPDF
import os
from PIL import Image


def generate_pdf(src_dir, aoi_name, date, n_clusters, out_pdf_path):
    rgb_path = os.path.join(src_dir, "rgb.png")
    ndvi_path = os.path.join(src_dir, "ndvi_vis.png")
    ndvi_classes_path = os.path.join(src_dir, "ndvi_classes_vis.png")
    clusters_rgb_path = os.path.join(src_dir, "clustered_rgb.png")
    superimposed_path = os.path.join(src_dir, "superimposed.png")

    # creating a new image file with light blue color with A4 size --. to be used as pdf background
    img = Image.new("RGB", (210, 297), color=(230, 230, 230))
    pdf_background_path = os.path.join(src_dir, "pdf_background.png")
    img.save(pdf_background_path)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.image(pdf_background_path, x=0, y=0, w=210, h=297, type="", link="")
    pdf.rect(5.0, 5.0, 200.0, 287.0)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)

    pdf.text(10, 10, "Report on Vegetation health for: {}".format(aoi_name))
    pdf.text(10, 15, "Date: {}".format(date))
    pdf.text(10, 18, "RGB image")
    pdf.image(rgb_path, x=45, y=30, w=120, h=90)

    pdf.add_page()
    pdf.image(pdf_background_path, x=0, y=0, w=210, h=297, type="", link="")
    pdf.rect(5.0, 5.0, 200.0, 287.0)
    pdf.text(10, 18, "NDVI (Normalized Difference Vegetation Index")
    pdf.image(ndvi_path, x=45, y=30, w=120, h=90)

    # pdf.add_page()
    pdf.text(10, 138, "Hardcoded thresholded classes on NDVI")
    pdf.image(ndvi_classes_path, x=45, y=160, w=120, h=90)

    pdf.add_page()
    pdf.image(pdf_background_path, x=0, y=0, w=210, h=297, type="", link="")
    pdf.rect(5.0, 5.0, 200.0, 287.0)
    pdf.text(
        10,
        18,
        "Generated clusters using K-means clustering. No. of clusters = {}".format(
            n_clusters
        ),
    )
    pdf.image(clusters_rgb_path, x=45, y=30, w=120, h=90)

    # pdf.add_page()
    pdf.text(10, 138, "Clusters superimposed on RGB")
    pdf.image(superimposed_path, x=45, y=160, w=120, h=90)

    # saving pdf
    pdf.output(out_pdf_path)


if __name__ == "__main__":
    pass
