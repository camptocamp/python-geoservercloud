from typing import Any

import pytest
import responses

from geoservercloud import GeoServerCloud

LAYER = "test_layer"
WORKSPACE = "test_workspace"
STORE = "test_store"


@pytest.fixture(scope="module")
def feature_types_get_response_payload() -> dict[str, Any]:
    return {
        "featureTypes": {
            "featureType": [
                {
                    "href": "http://localhost/featuretype1.json",
                    "name": "featuretype1",
                },
                {
                    "href": "http://localhost/featuretype2.json",
                    "name": "featuretype2",
                },
                {
                    "href": "http://localhost/featuretype3.json",
                    "name": "featuretype3",
                },
            ]
        }
    }


@pytest.fixture(scope="module")
def feature_type_common_attributes() -> dict[str, Any]:
    return {
        "name": LAYER,
        "nativeName": LAYER,
        "srs": "EPSG:4326",
        "store": {"name": f"{WORKSPACE}:{STORE}"},
        "internationalTitle": {"en": "English"},
        "internationalAbstract": {"en": "English"},
    }


@pytest.fixture(scope="module")
def feature_type_get_response_payload(feature_type_common_attributes) -> dict[str, Any]:
    content = feature_type_common_attributes.copy()
    content["namespace"] = {
        "name": WORKSPACE,
        "href": "http://localhost/namespace.json",
    }
    content["attributes"] = {
        "attribute": [
            {
                "name": "geom",
                "minOccurs": 1,
                "maxOccurs": 1,
                "nillable": False,
                "binding": "org.locationtech.jts.geom.Point",
            }
        ]
    }
    content["keywords"] = {"string": ["example"]}
    content.update(
        {
            "projectionPolicy": "FORCE_DECLARED",
            "enabled": True,
            "advertised": True,
            "serviceConfiguration": False,
            "simpleConversionEnabled": False,
            "padWithZeros": False,
            "forcedDecimals": False,
            "overridingServiceSRS": False,
            "skipNumberMatch": False,
            "circularArcPresent": False,
            "encodeMeasures": False,
        }
    )
    return {"featureType": content}


@pytest.fixture(scope="module")
def feature_type_as_dict(feature_type_common_attributes) -> dict[str, Any]:
    content = feature_type_common_attributes.copy()
    content["namespace"] = {"name": WORKSPACE}
    content["attributes"] = [
        {
            "name": "geom",
            "minOccurs": 1,
            "maxOccurs": 1,
            "nillable": False,
            "binding": "org.locationtech.jts.geom.Point",
        }
    ]
    content["keywords"] = ["example"]
    content.update(
        {
            "projectionPolicy": "FORCE_DECLARED",
            "enabled": True,
            "advertised": True,
            "serviceConfiguration": False,
            "simpleConversionEnabled": False,
            "padWithZeros": False,
            "forcedDecimals": False,
            "overridingServiceSRS": False,
            "skipNumberMatch": False,
            "circularArcPresent": False,
            "encodeMeasures": False,
        }
    )
    return content


@pytest.fixture(scope="module")
def feature_type_post_payload(
    feature_type_common_attributes,
) -> dict[str, dict[str, Any]]:
    content = feature_type_common_attributes.copy()
    content["attributes"] = {
        "attribute": [
            {
                "name": "geom",
                "minOccurs": 1,
                "maxOccurs": 1,
                "nillable": False,
                "binding": "org.locationtech.jts.geom.Point",
            }
        ]
    }
    content["keywords"] = {"string": ["example"]}
    content["nativeBoundingBox"] = {
        "crs": {"$": "EPSG:4326", "@class": "projected"},
        "maxx": 180,
        "maxy": 90,
        "minx": -180,
        "miny": -90,
    }
    content["latLonBoundingBox"] = {
        "crs": "EPSG:4326",
        "maxx": 180,
        "maxy": 90,
        "minx": -180,
        "miny": -90,
    }
    return {"featureType": content}


def test_get_feature_types(
    geoserver: GeoServerCloud, feature_types_get_response_payload: dict[str, Any]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes.json",
            status=200,
            json=feature_types_get_response_payload,
        )
        content, code = geoserver.get_feature_types(
            workspace_name=WORKSPACE, datastore_name=STORE
        )

        assert content == ["featuretype1", "featuretype2", "featuretype3"]
        assert code == 200


def test_get_feature_type(
    geoserver: GeoServerCloud,
    feature_type_get_response_payload: dict[str, Any],
    feature_type_as_dict: dict[str, Any],
) -> None:
    from pprint import pprint

    pprint(feature_type_get_response_payload.get("featureType"))
    pprint(feature_type_as_dict)

    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{LAYER}.json",
            status=200,
            json=feature_type_get_response_payload,
        )
        content, code = geoserver.get_feature_type(
            workspace_name=WORKSPACE, datastore_name=STORE, feature_type_name=LAYER
        )

        assert content == feature_type_as_dict
        assert code == 200


def test_create_feature_type(
    geoserver: GeoServerCloud, feature_type_post_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{LAYER}.json",
            status=404,
        )
        rsps.post(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes.json",
            match=[responses.matchers.json_params_matcher(feature_type_post_payload)],
            status=201,
            body=b"",
        )
        content, code = geoserver.create_feature_type(
            workspace_name=WORKSPACE,
            datastore=STORE,
            layer=LAYER,
            title={"en": "English"},
            abstract={"en": "English"},
            keywords=["example"],
        )

        assert content == ""
        assert code == 201


def test_update_feature_type(
    geoserver: GeoServerCloud, feature_type_post_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{LAYER}.json",
            status=200,
        )
        rsps.put(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes/{LAYER}.json",
            match=[responses.matchers.json_params_matcher(feature_type_post_payload)],
            status=200,
            body=b"",
        )
        content, code = geoserver.create_feature_type(
            workspace_name=WORKSPACE,
            datastore=STORE,
            layer=LAYER,
            title={"en": "English"},
            abstract={"en": "English"},
            keywords=["example"],
        )

        assert content == ""
        assert code == 200
