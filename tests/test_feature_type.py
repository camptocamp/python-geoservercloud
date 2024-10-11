from typing import Any

import pytest
import responses

from geoservercloud import GeoServerCloud

# TODO: add tests for
# - geoservercloud.get_featuretypes()
# - geoservercloud.get_featuretype()
# for the moment just import them as import tests
from geoservercloud.models import FeatureType, FeatureTypes

LAYER = "test_layer"
WORKSPACE = "test_workspace"
STORE = "test_store"


@pytest.fixture(scope="module")
def feature_type_payload() -> dict[str, dict[str, Any]]:
    return {
        "featureType": {
            "name": LAYER,
            "nativeName": LAYER,
            "srs": "EPSG:4326",
            "enabled": True,
            "store": {
                "name": f"{WORKSPACE}:{STORE}",
            },
            "attributes": {
                "attribute": [
                    {
                        "name": "geom",
                        "minOccurs": 1,
                        "maxOccurs": 1,
                        "nillable": False,
                        "binding": "org.locationtech.jts.geom.Point",
                    }
                ]
            },
            "latLonBoundingBox": {
                "crs": "EPSG:4326",
                "maxx": 180,
                "maxy": 90,
                "minx": -180,
                "miny": -90,
            },
            "nativeBoundingBox": {
                "crs": {"$": "EPSG:4326", "@class": "projected"},
                "maxx": 180,
                "maxy": 90,
                "minx": -180,
                "miny": -90,
            },
            "internationalTitle": {
                "en": "English",
            },
            "internationalAbstract": {
                "en": "English",
            },
        }
    }
