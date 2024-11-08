import pytest
import responses

from geoservercloud.services.restservice import RestService

STYLE = "test_style"


@pytest.fixture
def rest_service() -> RestService:
    return RestService("http://geoserver", auth=("test", "test"))


def test_get_style_no_workspace(rest_service: RestService):
    body = b"<sld>test</sld>"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"http://geoserver/rest/styles/{STYLE}.sld",
            status=200,
            body=body,
        )
        assert rest_service.get_style(STYLE) == (body, 200)


def test_get_style_with_workspace(rest_service: RestService):
    workspace_name = "test_workspace"
    body = b"<sld>test</sld>"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"http://geoserver/rest/workspaces/{workspace_name}/styles/{STYLE}.sld",
            status=200,
            body=body,
        )
        assert rest_service.get_style(STYLE, workspace_name) == (body, 200)
