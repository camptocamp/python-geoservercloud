from typing import Any

import pytest
import responses

from geoservercloud.geoservercloud import GeoServerCloud

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


def test_create_feature_type(
    geoserver: GeoServerCloud, feature_type_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{LAYER}.json",
            status=404,
        )
        rsps.post(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes.json",
            match=[responses.matchers.json_params_matcher(feature_type_payload)],
            status=201,
        )
        response = geoserver.create_feature_type(
            workspace=WORKSPACE,
            datastore=STORE,
            layer=LAYER,
            title={"en": "English"},
            abstract={"en": "English"},
        )

        assert response
        assert response.status_code == 201


def test_update_feature_type(
    geoserver: GeoServerCloud, feature_type_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{LAYER}.json",
            status=200,
        )
        rsps.put(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{LAYER}.json",
            match=[responses.matchers.json_params_matcher(feature_type_payload)],
            status=200,
        )
        response = geoserver.create_feature_type(
            workspace=WORKSPACE,
            datastore=STORE,
            layer=LAYER,
            title={"en": "English"},
            abstract={"en": "English"},
        )

        assert response
        assert response.status_code == 200
