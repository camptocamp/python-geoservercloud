from pathlib import Path

import pytest
import responses

from geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL

STYLE = "test_style"


def test_get_styles_no_workspace(geoserver: GeoServerCloud):
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
        content, code = geoserver.get_styles()

    assert content == ["style1", "style2"]
    assert code == 200


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
        content, code = geoserver.get_styles(workspace_name)

    assert content == ["style3", "style4"]
    assert code == 200


def test_get_style_no_workspace(geoserver: GeoServerCloud):
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/styles/{STYLE}.json",
            status=200,
            json={
                "style": {
                    "name": STYLE,
                    "format": "sld",
                    "languageVersion": {"version": "1.0.0"},
                    "filename": f"{STYLE}.sld",
                }
            },
        )
        content, code = geoserver.get_style(STYLE)

    assert content == {
        "name": STYLE,
        "format": "sld",
        "languageVersion": {"version": "1.0.0"},
        "filename": f"{STYLE}.sld",
    }
    assert code == 200


def test_get_style_with_workspace(geoserver: GeoServerCloud):
    workspace_name = "test_workspace"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{workspace_name}/styles/{STYLE}.json",
            status=200,
            json={
                "style": {
                    "name": STYLE,
                    "workspace": {"name": workspace_name},
                    "format": "sld",
                    "languageVersion": {"version": "1.0.0"},
                    "filename": f"{STYLE}.sld",
                }
            },
        )
        content, code = geoserver.get_style(STYLE, workspace_name)

    assert content == {
        "name": STYLE,
        "format": "sld",
        "languageVersion": {"version": "1.0.0"},
        "filename": f"{STYLE}.sld",
        "workspace": workspace_name,
    }
    assert code == 200


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
            body=b"test_style",
            # Matching of binary content is not supported by responses
        )

        content, code = geoserver.create_style_from_file(
            style=STYLE,
            file=str(file_path),
        )

        assert content == STYLE
        assert code == 201


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
            body=b"",
            # Matching of binary content is not supported by responses
        )

        content, code = geoserver.create_style_from_file(
            style=STYLE,
            file=str(file_path),
        )

        assert content == ""
        assert code == 200


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
            body=b"test_style",
            # Matching of binary content is not supported by responses
        )

        content, code = geoserver.create_style_from_file(
            style=STYLE,
            file=str(file_path),
        )

        assert content == STYLE
        assert code == 201


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
            body=b"",
            match=[
                responses.matchers.json_params_matcher(
                    {"layer": {"defaultStyle": {"name": style}}}
                )
            ],
        )

        content, code = geoserver.set_default_layer_style(layer, workspace, style)

        assert content == ""
        assert code == 200
