import argparse
import shutil
from importlib import resources
from pathlib import Path


def copy_test_data():
    parser = argparse.ArgumentParser(description="Copy GeoServer acceptance test data.")
    parser.add_argument(
        "target_dir",
        help="Directory where test data should be copied",
    )

    args = parser.parse_args()
    target = Path(args.target_dir)
    target.mkdir(parents=True, exist_ok=True)

    with resources.path("geoserver_acceptance_tests.data", "sampledata.tgz") as p:
        shutil.copy(p, target / "sampledata.tgz")

    print(f"Copied test data to: {target}")


def extract_test_data():
    parser = argparse.ArgumentParser(
        description="Extract GeoServer acceptance test data."
    )
    parser.add_argument(
        "target_dir",
        help="Directory where test data should be extracted",
    )

    args = parser.parse_args()
    target = Path(args.target_dir)
    target.mkdir(parents=True, exist_ok=True)

    with resources.path("geoserver_acceptance_tests.data", "sampledata.tgz") as p:
        shutil.unpack_archive(p, target)

    print(f"Extracted test data to: {target}")
