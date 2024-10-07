from typing import Any

import pytest
import responses

from geoservercloud.geoservercloud import GeoServerCloud

WORKSPACE = "test_workspace"
STORE = "test_wmtsstore"
CAPABILITIES_URL = "http://wmts?request=GetCapabilities&service=WMTS&version=1.0.0"
LAYER = "test_layer"
NATIVE_LAYER = "test_native_layer"
CAPABILITIES = """<?xml version="1.0" encoding="UTF-8"?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0" version="1.0.0" xmlns:ows="http://www.opengis.net/ows/1.1">
    <Contents>
        <Layer>
            <ows:Identifier>test_native_layer</ows:Identifier>
            <ows:WGS84BoundingBox>
                <ows:LowerCorner>5.140242 45.398181</ows:LowerCorner>
                <ows:UpperCorner>11.47757 48.230651</ows:UpperCorner>
            </ows:WGS84BoundingBox>
        </Layer>
    </Contents>
</Capabilities>
"""


@pytest.fixture(scope="module")
def wmts_store_payload() -> dict[str, dict[str, Any]]:
    return {
        "wmtsStore": {
            "name": STORE,
            "type": "WMTS",
            "capabilitiesURL": CAPABILITIES_URL,
            "workspace": {"name": WORKSPACE},
            "enabled": True,
            "metadata": {"entry": {"@key": "useConnectionPooling", "text": True}},
        }
    }


@pytest.fixture(scope="module")
def wmts_layer_payload() -> dict[str, dict[str, Any]]:
    return {
        "wmtsLayer": {
            "advertised": True,
            "enabled": True,
            "name": LAYER,
            "nativeName": NATIVE_LAYER,
            "projectionPolicy": "FORCE_DECLARED",
            "serviceConfiguration": False,
            "simpleConversionEnabled": False,
            "srs": "EPSG:4326",
            "latLonBoundingBox": {
                "crs": "EPSG:4326",
                "minx": 5.140242,
                "maxx": 11.47757,
                "miny": 45.398181,
                "maxy": 48.230651,
            },
            "nativeBoundingBox": {
                "crs": "EPSG:4326",
                "minx": 5.140242,
                "maxx": 11.47757,
                "miny": 45.398181,
                "maxy": 48.230651,
            },
        }
    }


def test_create_wmts_store(
    geoserver: GeoServerCloud, wmts_store_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}.json",
            status=404,
        )
        rsps.post(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores.json",
            match=[responses.matchers.json_params_matcher(wmts_store_payload)],
            status=201,
        )
        response = geoserver.create_wmts_store(
            workspace=WORKSPACE,
            name=STORE,
            capabilities=CAPABILITIES_URL,
        )

        assert response.status_code == 201


def test_update_wmts_store(
    geoserver: GeoServerCloud, wmts_store_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}.json",
            status=200,
        )
        rsps.put(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}.json",
            match=[responses.matchers.json_params_matcher(wmts_store_payload)],
            status=200,
        )
        response = geoserver.create_wmts_store(
            workspace=WORKSPACE,
            name=STORE,
            capabilities=CAPABILITIES_URL,
        )

        assert response.status_code == 200


def test_create_wmts_layer(
    geoserver: GeoServerCloud, wmts_layer_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}/layers/{LAYER}.json",
            status=404,
        )
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}.json",
            status=200,
            json={"wmtsStore": {"capabilitiesURL": CAPABILITIES_URL}},
        )
        rsps.get(
            CAPABILITIES_URL,
            status=200,
            body=CAPABILITIES,
            headers={"Content-Type": "application/xml"},
        )
        rsps.post(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}/layers.json",
            match=[responses.matchers.json_params_matcher(wmts_layer_payload)],
            status=201,
        )
        response = geoserver.create_wmts_layer(
            workspace=WORKSPACE,
            wmts_store=STORE,
            native_layer=NATIVE_LAYER,
            published_layer=LAYER,
        )

        assert response
        assert response.status_code == 201


def test_create_wmts_layer_already_exists(
    geoserver: GeoServerCloud, wmts_layer_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}/layers/{LAYER}.json",
            status=200,
        )
        rsps.delete(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}/layers/{LAYER}.json",
            status=200,
            match=[responses.matchers.query_param_matcher({"recurse": "true"})],
        )
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}.json",
            status=200,
            json={"wmtsStore": {"capabilitiesURL": CAPABILITIES_URL}},
        )
        rsps.get(
            CAPABILITIES_URL,
            status=200,
            body=CAPABILITIES,
            headers={"Content-Type": "application/xml"},
        )
        rsps.post(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}/layers.json",
            match=[responses.matchers.json_params_matcher(wmts_layer_payload)],
            status=201,
        )
        response = geoserver.create_wmts_layer(
            workspace=WORKSPACE,
            wmts_store=STORE,
            native_layer=NATIVE_LAYER,
            published_layer=LAYER,
        )

        assert response.status_code == 201


def test_create_wmts_layer_international_title(
    geoserver: GeoServerCloud, wmts_layer_payload: dict[str, dict[str, Any]]
) -> None:
    wmts_layer_payload["wmtsLayer"]["internationalTitle"] = {"en": "Title"}
    wmts_layer_payload["wmtsLayer"]["internationalAbstract"] = {"en": "Abstract"}
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}/layers/{LAYER}.json",
            status=404,
        )
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}.json",
            status=200,
            json={"wmtsStore": {"capabilitiesURL": CAPABILITIES_URL}},
        )
        rsps.get(
            CAPABILITIES_URL,
            status=200,
            body=CAPABILITIES,
            headers={"Content-Type": "application/xml"},
        )
        rsps.post(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmtsstores/{STORE}/layers.json",
            match=[responses.matchers.json_params_matcher(wmts_layer_payload)],
            status=201,
        )
        response = geoserver.create_wmts_layer(
            workspace=WORKSPACE,
            wmts_store=STORE,
            native_layer=NATIVE_LAYER,
            published_layer=LAYER,
            international_title={"en": "Title"},
            international_abstract={"en": "Abstract"},
        )

        assert response.status_code == 201
