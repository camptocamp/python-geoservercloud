from pathlib import Path

import pytest
import responses

from geoservercloud import GeoServerCloud
from geoservercloud.models import Styles
from tests.conftest import GEOSERVER_URL

STYLE = "test_style"


def test_get_styles_no_workspace(geoserver: GeoServerCloud):
    # Mock the self.rest_endpoints.styles() URL
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/styles.json",
            status=200,
            json={
                "styles": {
                    "style": [
                        {
                            "name": "style1",
                            "href": f"{GEOSERVER_URL}/rest/styles/style1.json",
                        },
                        {
                            "name": "style2",
                            "href": f"{GEOSERVER_URL}/rest/styles/style2.json",
                        },
                    ]
                }
            },
        )
        result = geoserver.get_styles()

    assert result == ["style1", "style2"]


def test_get_styles_with_workspace(geoserver: GeoServerCloud):
    workspace_name = "test_workspace"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{workspace_name}/styles.json",
            status=200,
            json={
                "styles": {
                    "style": [
                        {
                            "name": "style3",
                            "href": f"{GEOSERVER_URL}/rest/workspaces/{workspace_name}/styles/style3.json",
                        },
                        {
                            "name": "style4",
                            "href": f"{GEOSERVER_URL}/rest/workspaces/{workspace_name}/styles/style4.json",
                        },
                    ]
                }
            },
        )
        result = geoserver.get_styles(workspace_name)

    assert result == ["style3", "style4"]


def test_get_style_no_workspace(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/styles/{STYLE}.json",
            status=200,
            json={"style": {"name": STYLE}},
        )

        style = geoserver.get_style(STYLE)

        assert style.name == STYLE  # type: ignore
        assert style.workspace is None  # type: ignore


def test_create_style(geoserver: GeoServerCloud) -> None:
    file_path = (Path(__file__).parent / "resources/style.sld").resolve()
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/styles/{STYLE}.json",
            status=404,
        )
        rsps.post(
            url=f"{GEOSERVER_URL}/rest/styles.json",
            status=201,
        )

        response = geoserver.create_style_from_file(
            style=STYLE,
            file=str(file_path),
        )

        assert response.status_code == 201


def test_update_style(geoserver: GeoServerCloud) -> None:
    file_path = (Path(__file__).parent / "resources/style.sld").resolve()
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/styles/{STYLE}.json",
            status=200,
        )
        rsps.put(
            url=f"{GEOSERVER_URL}/rest/styles/{STYLE}.json",
            status=200,
        )

        response = geoserver.create_style_from_file(
            style=STYLE,
            file=str(file_path),
        )

        assert response.status_code == 200


def test_create_style_zip(geoserver: GeoServerCloud) -> None:
    file_path = (Path(__file__).parent / "resources/style.zip").resolve()
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/styles/{STYLE}.json",
            status=404,
        )
        rsps.post(
            url=f"{GEOSERVER_URL}/rest/styles.json",
            status=201,
        )

        response = geoserver.create_style_from_file(
            style=STYLE,
            file=str(file_path),
        )

        assert response.status_code == 201


def test_create_style_unsupported_format(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock():
        with pytest.raises(ValueError) as excinfo:
            geoserver.create_style_from_file(
                style=STYLE,
                file="resources/style.txt",
            )
        assert "Unsupported file extension" in str(excinfo.value)


def test_set_default_layer_style(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"
    layer = "test_layer"
    style = "test_style"
    with responses.RequestsMock() as rsps:
        rsps.put(
            url=f"{GEOSERVER_URL}/rest/layers/{workspace}:{layer}.json",
            status=200,
            match=[
                responses.matchers.json_params_matcher(
                    {"layer": {"defaultStyle": {"name": style}}}
                )
            ],
        )

        response = geoserver.set_default_layer_style(layer, workspace, style)

        assert response.status_code == 200
