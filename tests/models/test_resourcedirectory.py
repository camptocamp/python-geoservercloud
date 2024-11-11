from geoservercloud.models.resourcedirectory import Resource, ResourceDirectory


def test_from_get_response_payload():
    payload = {
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

    resource_directory = ResourceDirectory.from_get_response_payload(payload)

    assert resource_directory.name == "test_resource_directory"
    assert resource_directory.parent.name == "workspace/parent"
    assert resource_directory.parent.href == "http://example.com"
    assert resource_directory.parent.type == "application/json"
    assert len(resource_directory.children) == 2
    assert resource_directory.children[0].name == "child1.svg"
    assert resource_directory.children[0].href == "http://example.com/child1"
    assert resource_directory.children[0].type == "image/svg+xml"
    assert resource_directory.children[1].name == "child2.xml"
    assert resource_directory.children[1].href == "http://example.com/child2"
    assert resource_directory.children[1].type == "application/xml"
