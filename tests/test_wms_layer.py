from typing import Any

import pytest
import responses

from geoservercloud import GeoServerCloud

LAYER = "test_layer"
WORKSPACE = "test_workspace"
STORE = "test_store"


@pytest.fixture(scope="module")
def wms_layer_common_attributes() -> dict[str, Any]:
    return {
        "name": LAYER,
        "nativeName": LAYER,
        "srs": "EPSG:4326",
        "store": {"name": f"{WORKSPACE}:{STORE}"},
        "title": "Wms Layer Title",
        "abstract": "Wms Layer Abstract",
    }


@pytest.fixture(scope="module")
def wms_layer_get_response_payload(wms_layer_common_attributes) -> dict[str, Any]:
    content = wms_layer_common_attributes.copy()
    content["namespace"] = {
        "name": WORKSPACE,
        "href": "http://localhost/namespace.json",
    }
    content["description"] = "Wms Layer Description"
    content["keywords"] = {"string": ["example"]}
    content.update(
        {
            "projectionPolicy": "FORCE_DECLARED",
            "enabled": True,
            "serviceConfiguration": False,
            "forcedRemoteStyle": "",
            "preferredFormat": "image/png",
            "metadataBBoxRespected": False,
        }
    )
    return {"wmsLayer": content}


@pytest.fixture(scope="module")
def wms_layer_as_dict(wms_layer_common_attributes) -> dict[str, Any]:
    content = wms_layer_common_attributes.copy()
    content["namespace"] = {"name": WORKSPACE}
    content["description"] = "Wms Layer Description"
    content["keywords"] = ["example"]
    content.update(
        {
            "projectionPolicy": "FORCE_DECLARED",
            "enabled": True,
            "serviceConfiguration": False,
            "forcedRemoteStyle": "",
            "preferredFormat": "image/png",
            "metadataBBoxRespected": False,
        }
    )
    return content


@pytest.fixture(scope="module")
def wms_layer_post_payload() -> dict[str, dict[str, Any]]:
    return {
        "wmsLayer": {
            "name": LAYER,
            "nativeName": LAYER,
            "store": {"name": f"{WORKSPACE}:{STORE}"},
        }
    }


def test_get_wms_layer(
    geoserver: GeoServerCloud,
    wms_layer_get_response_payload: dict[str, Any],
    wms_layer_as_dict: dict[str, Any],
) -> None:

    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}/wmslayers/{LAYER}.json",
            status=200,
            json=wms_layer_get_response_payload,
        )
        content, code = geoserver.get_wms_layer(
            workspace_name=WORKSPACE, wms_store_name=STORE, wms_layer_name=LAYER
        )

        assert content == wms_layer_as_dict
        assert code == 200


def test_create_wms_layer(
    geoserver: GeoServerCloud, wms_layer_post_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}/wmslayers/{LAYER}.json",
            status=404,
        )
        rsps.post(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}/wmslayers.json",
            match=[responses.matchers.json_params_matcher(wms_layer_post_payload)],
            status=201,
            body=b"",
        )
        content, code = geoserver.create_wms_layer(
            workspace_name=WORKSPACE,
            wms_store_name=STORE,
            native_layer_name=LAYER,
        )

        assert content == ""
        assert code == 201


def test_update_wms_layer(
    geoserver: GeoServerCloud, wms_layer_post_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}/wmslayers/{LAYER}.json",
            status=200,
        )
        rsps.delete(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}/wmslayers/{LAYER}.json",
            status=200,
            body=b"",
            match=[responses.matchers.query_param_matcher({"recurse": "true"})],
        )
        rsps.post(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}/wmslayers.json",
            match=[responses.matchers.json_params_matcher(wms_layer_post_payload)],
            status=201,
            body=b"",
        )
        content, code = geoserver.create_wms_layer(
            workspace_name=WORKSPACE,
            wms_store_name=STORE,
            native_layer_name=LAYER,
        )

        assert content == ""
        assert code == 201


def test_delete_wms_layer(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.delete(
            f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}/wmslayers/{LAYER}.json",
            status=200,
            body=b"",
            match=[responses.matchers.query_param_matcher({"recurse": "true"})],
        )
        content, code = geoserver.delete_wms_layer(
            workspace_name=WORKSPACE,
            wms_store_name=STORE,
            wms_layer_name=LAYER,
        )

        assert content == ""
        assert code == 200
