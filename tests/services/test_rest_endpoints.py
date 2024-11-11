from collections.abc import Generator
from typing import Any

import pytest

from geoservercloud.services.restservice import RestService


@pytest.fixture
def endpoints() -> Generator[RestService.RestEndpoints, Any, None]:
    yield RestService("http://geoserver", auth=("test", "test")).rest_endpoints


def test_styles_endpoint(endpoints: RestService.RestEndpoints):
    assert endpoints.styles() == "/rest/styles.json"


def test_style_endpoint(endpoints: RestService.RestEndpoints):
    assert endpoints.style("test_style") == "/rest/styles/test_style.json"


@pytest.mark.parametrize(
    "format,path",
    [
        ("json", "/rest/styles.json"),
        ("xml", "/rest/styles"),
        ("sld", "/rest/styles"),
        ("zip", "/rest/styles"),
    ],
)
def test_styles_endpoint_format(
    endpoints: RestService.RestEndpoints, format: str, path: str
):
    assert endpoints.styles(format=format) == path


@pytest.mark.parametrize(
    "format,path",
    [
        ("json", "/rest/styles/test_style.json"),
        ("xml", "/rest/styles/test_style"),
        ("sld", "/rest/styles/test_style.sld"),
        ("zip", "/rest/styles/test_style"),
    ],
)
def test_style_endpoint_format(
    endpoints: RestService.RestEndpoints, format: str, path: str
):
    assert endpoints.style(style_name="test_style", format=format) == path


@pytest.mark.parametrize(
    "format,path",
    [
        ("json", "/rest/workspaces/test/styles.json"),
        ("xml", "/rest/workspaces/test/styles"),
        ("sld", "/rest/workspaces/test/styles"),
        ("zip", "/rest/workspaces/test/styles"),
    ],
)
def test_workspace_styles_endpoint(
    endpoints: RestService.RestEndpoints, format: str, path: str
):
    assert endpoints.styles(workspace_name="test", format=format) == path


@pytest.mark.parametrize(
    "format,path",
    [
        ("json", "/rest/workspaces/test/styles/test_style.json"),
        ("xml", "/rest/workspaces/test/styles/test_style"),
        ("sld", "/rest/workspaces/test/styles/test_style.sld"),
        ("zip", "/rest/workspaces/test/styles/test_style"),
    ],
)
def test_workspace_style_endpoint(
    endpoints: RestService.RestEndpoints, format: str, path: str
):
    assert (
        endpoints.style(style_name="test_style", workspace_name="test", format=format)
        == path
    )


def test_resource_directory_endpoint(endpoints: RestService.RestEndpoints):
    assert (
        endpoints.resource_directory("styles", "test_workspace")
        == "/rest/resource/workspaces/test_workspace/styles"
    )
    assert endpoints.resource_directory("styles") == "/rest/resource/styles"


def test_resource_endpoint(endpoints: RestService.RestEndpoints):
    assert (
        endpoints.resource("styles", "image.svg", "test_workspace")
        == "/rest/resource/workspaces/test_workspace/styles/image.svg"
    )
    assert (
        endpoints.resource("styles", "image.svg") == "/rest/resource/styles/image.svg"
    )
