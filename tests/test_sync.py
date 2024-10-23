import pytest
import responses
from responses import matchers

from geoservercloud import GeoServerCloudSync

GEOSERVER_SRC_URL = "http://source-geoserver"
GEOSERVER_DST_URL = "http://destination-geoserver"


@pytest.fixture
def geoserver_sync():
    return GeoServerCloudSync(
        GEOSERVER_SRC_URL,
        "admin",
        "geoserver",
        GEOSERVER_DST_URL,
        "admin",
        "geoserver",
    )


def test_copy_workspace(geoserver_sync):

    workspace_name = "test_workspace"
    workspace = {"name": workspace_name, "isolated": True}

    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_SRC_URL}/rest/workspaces/{workspace_name}.json",
            status=200,
            json={"workspace": workspace},
        )
        rsps.post(
            url=f"{GEOSERVER_DST_URL}/rest/workspaces.json",
            status=201,
            body=b"test_workspace",
            match=[matchers.json_params_matcher({"workspace": workspace})],
        )

        assert geoserver_sync.copy_workspace(workspace_name) == (workspace_name, 201)
