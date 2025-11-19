from pathlib import Path

from owslib.util import ResponseWrapper

from .conftest import BASE_PERSIST_DIR


def write_actual_image(
    tmp_directory: Path, relative_image_path: Path, response: ResponseWrapper
):
    """Write a test generated image to a file for later comparison.

    :param tmp_directory: Directory where to write the image (as Path).
    :param relative_image_path: Relative path to identify the image file, without file extension(as Path).
    :param response: owslib.util.ResponseWrapper containing the image data.
    """
    file = tmp_directory / relative_image_path
    file = file.with_name(f"{file.name}_actual.png")
    file.parent.mkdir(parents=True, exist_ok=True)
    with open(str(file), "wb") as fs:
        fs.write(response.read())


def compare_images(
    tmp_directory: Path,
    resource_directory: Path,
    relative_image_path: Path,
):
    """Compare a test generated image with the expected image.

    :param tmp_directory: Directory where the generated image is stored (as Path).
    :param resource_directory: Directory where the expected image is stored (as Path).
    :param relative_image_path: Relative path to identify the image file, without file extension(as Path).
    """
    actual = tmp_directory / relative_image_path
    actual = actual.with_name(f"{actual.name}_actual.png")
    expected = resource_directory / relative_image_path
    expected = expected.with_name(f"{expected.name}_expected.png")
    with open(str(actual), "rb") as fs1, open(str(expected), "rb") as fs2:
        assert (
            fs1.read() == fs2.read()
        ), f"Generated image (see in {BASE_PERSIST_DIR}) does not match expected image ({expected})."
