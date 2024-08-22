import responses
from responses import matchers

from geoservercloud.geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL


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
