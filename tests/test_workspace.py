from typing import Any

import pytest
import responses
from responses import matchers

from geoservercloud import GeoServerCloud


@pytest.fixture
def mock_wms_settings():
    return {
        "wms": {
            "workspace": {"name": "test_workspace"},
            "enabled": True,
            "name": "WMS",
            "versions": {
                "org.geotools.util.Version": [
                    {"version": "1.1.1"},
                    {"version": "1.3.0"},
                ]
            },
            "citeCompliant": False,
            "schemaBaseURL": "http://schemas.opengis.net",
            "verbose": False,
            "bboxForEachCRS": False,
            "watermark": {
                "enabled": False,
                "position": "BOT_RIGHT",
                "transparency": 100,
            },
            "interpolation": "Nearest",
            "getFeatureInfoMimeTypeCheckingEnabled": False,
            "getMapMimeTypeCheckingEnabled": False,
            "dynamicStylingDisabled": False,
            "featuresReprojectionDisabled": False,
            "maxBuffer": 0,
            "maxRequestMemory": 0,
            "maxRenderingTime": 0,
            "maxRenderingErrors": 0,
            "maxRequestedDimensionValues": 100,
            "cacheConfiguration": {
                "enabled": False,
                "maxEntries": 1000,
                "maxEntrySize": 51200,
            },
            "remoteStyleMaxRequestTime": 60000,
            "remoteStyleTimeout": 30000,
            "defaultGroupStyleEnabled": True,
            "transformFeatureInfoDisabled": False,
            "autoEscapeTemplateValues": False,
        }
    }


def test_list_workspaces(geoserver: GeoServerCloud) -> None:
    workspaces = [
        {
            "name": "test_workspace",
            "href": "http://localhost:8080/geoserver/rest/workspaces/test_workspace.json",
        }
    ]
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces.json",
            status=200,
            json={"workspaces": {"workspace": workspaces}},
        )
        assert geoserver.get_workspaces() == (workspaces, 200)


def test_get_workspace_ok(geoserver: GeoServerCloud) -> None:
    workspace_name = "test_workspace"
    workspace = {"name": workspace_name, "isolated": False}
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}.json",
            status=200,
            json={"workspace": workspace},
        )
        assert geoserver.get_workspace(workspace_name) == (workspace, 200)


def test_get_workspace_not_found(geoserver: GeoServerCloud) -> None:
    workspace_name = "test_workspace"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}.json",
            status=404,
            body=b"No such workspace: 'test_workspace' found",
        )
        assert geoserver.get_workspace(workspace_name) == (
            "No such workspace: 'test_workspace' found",
            404,
        )


def test_create_workspace(geoserver: GeoServerCloud) -> None:
    workspace_name = "test_workspace"
    isolated = True

    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/rest/workspaces.json",
            status=201,
            body=b"test_workspace",
            match=[
                matchers.json_params_matcher(
                    {
                        "workspace": {
                            "name": workspace_name,
                            "isolated": isolated,
                        }
                    }
                )
            ],
        )

        content, status_code = geoserver.create_workspace(workspace_name, isolated)

        assert content == workspace_name
        assert status_code == 201


def test_update_workspace(geoserver: GeoServerCloud) -> None:
    workspace_name = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/rest/workspaces.json",
            status=409,
            match=[
                matchers.json_params_matcher(
                    {
                        "workspace": {
                            "name": workspace_name,
                            "isolated": False,
                        }
                    }
                )
            ],
        )
        rsps.put(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}.json",
            match=[
                matchers.json_params_matcher(
                    {
                        "workspace": {
                            "name": workspace_name,
                            "isolated": False,
                        }
                    }
                )
            ],
            status=200,
            body=b"",
        )

        content, status_code = geoserver.create_workspace(workspace_name)

        assert content == ""
        assert status_code == 200


def test_delete_workspace(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/rest/workspaces/{workspace}.json",
            status=200,
            body=b"",
        )

        content, status_code = geoserver.delete_workspace(workspace)
        assert content == ""
        assert status_code == 200


def test_recreate_workspace(geoserver: GeoServerCloud) -> None:
    workspace_name = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}.json",
            status=200,
            body=b"",
        )
        rsps.post(
            url=f"{geoserver.url}/rest/workspaces.json",
            status=201,
            body=b"test_workspace",
            match=[
                matchers.json_params_matcher(
                    {
                        "workspace": {
                            "name": workspace_name,
                            "isolated": False,
                        }
                    }
                )
            ],
        )

        content, status_code = geoserver.recreate_workspace(workspace_name)
        assert content == workspace_name
        assert status_code == 201


def test_get_workspace_wms_settings(
    geoserver: GeoServerCloud, mock_wms_settings: dict[str, Any]
) -> None:
    workspace = "test_workspace"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/services/wms/workspaces/{workspace}/settings.json",
            status=200,
            json=mock_wms_settings,
        )
        content, status_code = geoserver.get_workspace_wms_settings(workspace)
        assert isinstance(content, dict)
        assert content.get("workspace") == "test_workspace"
        assert status_code == 200


def test_publish_workspace(
    geoserver: GeoServerCloud, mock_wms_settings: dict[str, Any]
) -> None:
    workspace = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.put(
            url=f"{geoserver.url}/rest/services/wms/workspaces/{workspace}/settings.json",
            status=200,
            match=[matchers.json_params_matcher(mock_wms_settings)],
        )

        content, status_code = geoserver.publish_workspace(workspace)
        assert content == ""
        assert status_code == 200


def test_set_service_locale(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.put(
            url=f"{geoserver.url}/rest/services/wms/workspaces/{workspace}/settings.json",
            status=200,
            match=[
                matchers.json_params_matcher(
                    {
                        "wms": {
                            "defaultLocale": "fr",
                        }
                    }
                )
            ],
        )

        content, status_code = geoserver.set_default_locale_for_service(workspace, "fr")
        assert content == ""
        assert status_code == 200
