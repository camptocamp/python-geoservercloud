from typing import Any

import pytest
import responses

from geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL

LAYER_GROUP = "test_layer_group"
LAYERS = ["layer1", "layer2"]
WORKSPACE = "test_workspace"
TITLE = {"en": "English Title"}
ABSTRACT = {"en": "English Abstract"}


@pytest.fixture(scope="module")
def layer_group_payload() -> dict[str, dict[str, Any]]:
    return {
        "layerGroup": {
            "name": LAYER_GROUP,
            "workspace": {"name": WORKSPACE},
            "mode": "SINGLE",
            "publishables": {
                "published": [
                    {"@type": "layer", "name": f"{WORKSPACE}:{LAYERS[0]}"},
                    {"@type": "layer", "name": f"{WORKSPACE}:{LAYERS[1]}"},
                ]
            },
            "styles": {"style": [{"name": ""}, {"name": ""}]},
            "bounds": {
                "minx": -180,
                "maxx": 180,
                "miny": -90,
                "maxy": 90,
                "crs": "EPSG:4326",
            },
            "enabled": True,
            "advertised": True,
            "internationalTitle": {"en": "English Title"},
            "internationalAbstract": {"en": "English Abstract"},
        }
    }


def test_create_layer_group(
    geoserver: GeoServerCloud, layer_group_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/layergroups/{LAYER_GROUP}.json",
            status=404,
        )
        rsps.post(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/layergroups.json",
            status=201,
            body=b"test_layer_group",
            match=[responses.matchers.json_params_matcher(layer_group_payload)],
        )

        content, code = geoserver.create_layer_group(
            group=LAYER_GROUP,
            workspace_name=WORKSPACE,
            layers=LAYERS,
            title=TITLE,
            abstract=ABSTRACT,
        )

        assert content == "test_layer_group"
        assert code == 201


def test_update_layer_group(
    geoserver: GeoServerCloud, layer_group_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/layergroups/{LAYER_GROUP}.json",
            status=200,
        )
        rsps.put(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/layergroups/{LAYER_GROUP}.json",
            status=200,
            body=b"",
            match=[responses.matchers.json_params_matcher(layer_group_payload)],
        )

        content, code = geoserver.create_layer_group(
            group=LAYER_GROUP,
            workspace_name=WORKSPACE,
            layers=LAYERS,
            title=TITLE,
            abstract=ABSTRACT,
        )

        assert content == ""
        assert code == 200
