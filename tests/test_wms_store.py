from collections.abc import Generator
from typing import Any

import pytest
import responses

from geoservercloud import GeoServerCloud

WORKSPACE = "test_workspace"
STORE = "test_store"
CAPABILITIES_URL = (
    "https://wms.geo.admin.ch/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"
)


@pytest.fixture(scope="module")
def wms_payload() -> Generator[dict[str, dict[str, Any]], Any, None]:
    yield {
        "wmsStore": {
            "capabilitiesURL": CAPABILITIES_URL,
            "enabled": True,
            "name": STORE,
            "type": "WMS",
            "workspace": {"name": WORKSPACE},
        }
    }


@pytest.fixture(scope="module")
def wmsstore_get_response() -> Generator[dict[str, Any], Any, None]:
    yield {
        "wmsStore": {
            "name": STORE,
            "type": "WMS",
            "enabled": True,
            "workspace": {
                "name": WORKSPACE,
                "href": f"http://localhost:8080/geoserver/rest/workspaces/{WORKSPACE}.json",
            },
            "metadata": {"entry": {"@key": "useConnectionPooling", "$": "true"}},
            "_default": False,
            "disableOnConnFailure": False,
            "capabilitiesURL": CAPABILITIES_URL,
            "maxConnections": 6,
            "readTimeout": 60,
            "connectTimeout": 30,
            "wmslayers": f"http://localhost:8080/geoserver/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}/wmslayers.json",
        }
    }


def test_get_wms_store_ok(
    geoserver: GeoServerCloud, wmsstore_get_response: dict[str, Any]
) -> None:
    expected_wmsstore = {
        "name": STORE,
        "type": "WMS",
        "enabled": True,
        "workspace": WORKSPACE,
        "capabilitiesURL": CAPABILITIES_URL,
        "_default": False,
        "disableOnConnFailure": False,
    }
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}.json",
            status=200,
            json=wmsstore_get_response,
        )
        content, status_code = geoserver.get_wms_store(WORKSPACE, STORE)
        assert content == expected_wmsstore
        assert status_code == 200


def test_get_wms_store_not_found(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}.json",
            status=404,
            body=b"No wms store: test_workspace,test_wmsstore",
        )
        content, status_code = geoserver.get_wms_store(WORKSPACE, STORE)
        assert content == "No wms store: test_workspace,test_wmsstore"
        assert status_code == 404


def test_create_wms_store(
    geoserver: GeoServerCloud, wms_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}.json",
            status=404,
        )
        rsps.post(
            url=f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores.json",
            status=201,
            body=b"test_store",
            match=[responses.matchers.json_params_matcher(wms_payload)],
        )

        content, code = geoserver.create_wms_store(
            workspace_name=WORKSPACE,
            wms_store_name=STORE,
            capabilities_url=CAPABILITIES_URL,
        )

        assert content == STORE
        assert code == 201


def test_update_wms_store(
    geoserver: GeoServerCloud, wms_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}.json",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}.json",
            status=200,
            body=b"",
            match=[responses.matchers.json_params_matcher(wms_payload)],
        )

        content, code = geoserver.create_wms_store(
            workspace_name=WORKSPACE,
            wms_store_name=STORE,
            capabilities_url=CAPABILITIES_URL,
        )

        assert content == ""
        assert code == 200


def test_delete_wms_store(geoserver: GeoServerCloud) -> None:

    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/rest/workspaces/{WORKSPACE}/wmsstores/{STORE}.json",
            status=200,
            body=b"",
        )

        content, status_code = geoserver.delete_wms_store(WORKSPACE, STORE)
        assert content == ""
        assert status_code == 200
