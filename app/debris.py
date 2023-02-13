import io
import json
from tempfile import NamedTemporaryFile

from cocojson.tools.filter_cat import filter_cat
from cocojson.utils.common import IMG_EXTS
from fastapi import (APIRouter, File, Response,
                     UploadFile, status)
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from plot_debris_area import plot_debris_area
from utils import (coco_area_update_if_null_, get_image_id_map,
                   get_image_pixel_area)

router = APIRouter()

DEPRI_CATS = [
    "cement_block_broken",
    "brick_standard",
    "pile_of_trash",
    "electrical_wires",
]


@router.post(
    "/submit",
    status_code=status.HTTP_201_CREATED,
    responses={200: {"content": {"image/png": {}}}},
)
def create_upload_files(
    files: list[UploadFile] = File(description="Multiple files as UploadFile"),
):
    data = []
    image_pixel_size = {}
    for file in files:
        filename = file.filename
        if filename.endswith(".json"):
            d = json.load(file.file)
            data_filtered = filter_cat(d, DEPRI_CATS)
            coco_area_update_if_null_(data_filtered)
            data.append((filename.rstrip(".json"), data_filtered))

        elif "." + filename.split(".")[-1] in IMG_EXTS:
            with NamedTemporaryFile() as temp_file:
                temp_file.write(file.file.read())
                image_pixel_size[filename] = get_image_pixel_area(temp_file.name)
    pixel_area = []
    surface_area = []
    for month_year in data:
        pixel_area_acc = 0
        surface_area_acc = 0
        img_id_map = get_image_id_map(month_year[1])
        for annotation in month_year[1]["annotations"]:
            pixel_area_acc += annotation["area"]
            surface_area_acc += (
                annotation["area"]
                * image_pixel_size[img_id_map[annotation["image_id"]]]
            )
        pixel_area.append((month_year[0], pixel_area_acc))
        surface_area.append((month_year[0], surface_area_acc))
    fig = plot_debris_area(surface_area)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue())
