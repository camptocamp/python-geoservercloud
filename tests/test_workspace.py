import responses
from responses import matchers

from geoservercloud.geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL


def test_list_workspaces(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces.json",
            status=200,
            json={
                "workspaces": {
                    "workspace": [
                        {
                            "name": "test_workspace",
                            "href": "http://localhost:8080/geoserver/rest/workspaces/test_workspace.json",
                        }
                    ]
                }
            },
        )
        workspaces = geoserver.get_workspaces()
        assert workspaces.workspaces == ["test_workspace"]


def test_create_workspace(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"
    isolated = True

    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{GEOSERVER_URL}/rest/workspaces.json",
            status=201,
            match=[
                matchers.json_params_matcher(
                    {
                        "workspace": {
                            "name": workspace,
                            "isolated": isolated,
                        }
                    }
                )
            ],
        )

        response = geoserver.create_workspace(workspace, isolated=isolated)

        assert response.status_code == 201


def test_update_workspace(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{GEOSERVER_URL}/rest/workspaces.json",
            status=409,
        )
        rsps.put(
            url=f"{GEOSERVER_URL}/rest/workspaces/{workspace}.json",
            status=200,
        )

        response = geoserver.create_workspace(workspace)

        assert response.status_code == 200


def test_delete_workspace(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{GEOSERVER_URL}/rest/workspaces/{workspace}.json",
            status=200,
        )

        response = geoserver.delete_workspace(workspace)

        assert response.status_code == 200


def test_recreate_workspace(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{GEOSERVER_URL}/rest/workspaces/{workspace}.json",
            status=200,
        )
        rsps.post(
            url=f"{GEOSERVER_URL}/rest/workspaces.json",
            status=201,
        )

        response = geoserver.recreate_workspace(workspace)

        assert response.status_code == 201


def test_publish_workspace(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"

    with responses.RequestsMock() as rsps:
        rsps.put(
            url=f"{GEOSERVER_URL}/rest/services/wms/workspaces/{workspace}/settings.json",
            status=200,
            match=[
                matchers.json_params_matcher(
                    {
                        "wms": {
                            "workspace": {"name": workspace},
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
                )
            ],
        )

        response = geoserver.publish_workspace(workspace)

        assert response.status_code == 200
