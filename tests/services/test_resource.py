import pytest
import responses

from geoservercloud.models.resourcedirectory import ResourceDirectory
from geoservercloud.services.restservice import RestService


@pytest.fixture
def rest_service():
    yield RestService("http://geoserver", auth=("test", "test"))


@pytest.fixture
def resource_dir_get_response():
    yield {
        "ResourceDirectory": {
            "name": "test_resource_directory",
            "parent": {
                "path": "workspace/parent",
                "name": "parent",
                "link": {"href": "http://example.com", "type": "application/json"},
            },
            "children": {
                "child": [
                    {
                        "name": "child1.svg",
                        "link": {
                            "href": "http://example.com/child1",
                            "type": "image/svg+xml",
                        },
                    },
                    {
                        "name": "child2.xml",
                        "link": {
                            "href": "http://example.com/child2",
                            "type": "application/xml",
                        },
                    },
                ]
            },
        }
    }


def test_get_workspace_style_resource_directory(
    rest_service: RestService, resource_dir_get_response: dict
):
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{rest_service.url}/rest/resource/workspaces/test/styles",
            status=200,
            json=resource_dir_get_response,
            match=[responses.matchers.header_matcher({"Accept": "application/json"})],
        )
        resource_dir, code = rest_service.get_resource_directory(
            path="styles", workspace_name="test"
        )
        assert isinstance(resource_dir, ResourceDirectory)
        assert len(resource_dir.children) == 2


def test_get_global_style_resource_directory(
    rest_service: RestService, resource_dir_get_response: dict
):
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{rest_service.url}/rest/resource/styles",
            status=200,
            json=resource_dir_get_response,
            match=[responses.matchers.header_matcher({"Accept": "application/json"})],
        )
        resource_dir, code = rest_service.get_resource_directory(path="styles")
        assert isinstance(resource_dir, ResourceDirectory)
        assert len(resource_dir.children) == 2
