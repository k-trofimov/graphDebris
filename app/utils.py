import math

from exif import Image
from shapely.geometry import Polygon

STANRARD_FILM_DIAGIONAL = 43.3
DJI_META_FIELDS = [
    "AbsoluteAltitude",
    "RelativeAltitude",
    "GimbalRollDegree",
    "GimbalYawDegree",
    "GimbalPitchDegree",
    "FlightRollDegree",
    "FlightYawDegree",
    "FlightPitchDegree",
]
XMP_START = b"<x:xmpmeta"
XMP_STOP = b"</x:xmpmeta"


def coco_area_update_if_null_(coco_dict: dict) -> None:
    """Updates area field in coco_dict if it is None."""

    def list_to_pairs(lst):
        return [(lst[i], lst[i + 1]) for i in range(0, len(lst), 2)]

    for ann in coco_dict["annotations"]:
        if ann["area"] is None:
            # We use Shoelace formula for a polygon area
            ann["area"] = Polygon(list_to_pairs(ann["segmentation"][0])).area


def pixel_area(
    relative_altitude: float,
    fov: float,
    image_height: float,
    image_width: float,
    gimbal_pitch_degree: float,
    flight_pitch_degree: float,
    flight_roll_degree: float,
    gimbal_roll_degree: float,
    correct_roll_pitch=False,
) -> float:
    """Calculates area of a pixel in meters squared."""

    # get size w.r.t. FOV, hight and resolution
    lens_correction = 2 * math.tan(fov / 2) * relative_altitude
    pixel_width = lens_correction / image_width
    pixel_height = lens_correction / image_height

    # TODO: pitch and roll correction
    """ I have doubts about this correction formula, seems like it should be more complicated than just multiplication by
    a sin, since part of the image is shrunk. I would need more time to potentially refine it
    """
    if correct_roll_pitch:
        correction_factor = 1 / (
            math.sin(math.radians(gimbal_pitch_degree + flight_pitch_degree))
            + math.sin(math.radians(flight_roll_degree + gimbal_roll_degree))
        )

        pixel_width *= correction_factor
        pixel_height *= correction_factor

    return pixel_width * pixel_height


def get_dji_meta(filepath: str) -> dict:
    """
    Returns a dict with DJI-specific metadata stored in the XMB portion of the image
    """

    # read file in binary format and look for XMP metadata portion
    with open(filepath, "rb") as fd:
        d = fd.read()
    xmp_start = d.find(XMP_START)
    xmp_end = d.find(XMP_STOP)

    # convert bytes to string
    xmp_b = d[xmp_start : xmp_end + 12]
    xmp_str = xmp_b.decode()

    # parse the XMP string to grab the values
    xmp_dict = {}
    for m in DJI_META_FIELDS:
        istart = xmp_str.find(m)
        ss = xmp_str[istart : istart + len(m) + 10]
        val = float(ss.split('"')[1])
        xmp_dict.update({m: val})

    return xmp_dict


def get_image_pixel_area(filepath: str) -> float:
    """
    Extracts image metadata and calculates FOV and return pixel area in meters squared
    """
    dji_data = get_dji_meta(filepath)
    with open(filepath, "rb") as image_file:
        img = Image(image_file)
    image_height = img.get("image_height")
    image_width = img.get("image_width")
    focal_length = img.get("focal_length_in_35mm_film")

    # calculate FOV according to from  focal length
    fov = 2 * math.atan(STANRARD_FILM_DIAGIONAL / (2 * focal_length))

    return pixel_area(
        dji_data["RelativeAltitude"],
        fov,
        image_height,
        image_width,
        dji_data["GimbalPitchDegree"],
        dji_data["FlightPitchDegree"],
        dji_data["FlightRollDegree"],
        dji_data["GimbalRollDegree"],
    )


def get_image_id_map(data_dict: dict) -> dict:
    """
    Creates a mapping of image id to file name
    """
    id_map = {}
    for img in data_dict["images"]:
        id_map.update({img["id"]: img["file_name"]})
    return id_map
