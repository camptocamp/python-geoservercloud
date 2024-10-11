from pathlib import Path

import pytest
import responses

from geoservercloud.geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL

STYLE = "test_style"


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
