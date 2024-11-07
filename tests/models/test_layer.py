from geoservercloud.models.layer import Layer


def test_layer_post_payload():
    layer = Layer(
        name="test_point",
        resource_name="test_workspace:test_point",
        type="VECTOR",
        default_style_name="point",
        styles=["burg", "capitals"],
        queryable=True,
        attribution={"logoWidth": 0, "logoHeight": 0},
    )

    content = layer.post_payload()

    assert content == {
        "layer": {
            "name": "test_point",
            "type": "VECTOR",
            "defaultStyle": {"name": "point"},
            "styles": {
                "style": [
                    {"name": "burg"},
                    {"name": "capitals"},
                ],
            },
            "resource": {
                "name": "test_workspace:test_point",
            },
            "queryable": True,
            "attribution": {"logoWidth": 0, "logoHeight": 0},
        }
    }


def test_from_get_response_payload():
    content = {
        "layer": {
            "name": "test_point",
            "type": "VECTOR",
            "defaultStyle": {
                "name": "point",
                "href": "http://localhost:9099/geoserver/rest/styles/point.json",
            },
            "styles": {
                "@class": "linked-hash-set",
                "style": [
                    {
                        "name": "burg",
                        "href": "http://localhost:9099/geoserver/rest/styles/burg.json",
                    },
                    {
                        "name": "capitals",
                        "href": "http://localhost:9099/geoserver/rest/styles/capitals.json",
                    },
                ],
            },
            "resource": {
                "@class": "featureType",
                "name": "test_workspace:test_point",
                "href": "http://localhost:9099/geoserver/rest/workspaces/elden/datastores/elden/featuretypes/test_point.json",
            },
            "attribution": {"logoWidth": 0, "logoHeight": 0},
            "dateCreated": "2024-11-06 10:16:07.328 UTC",
            "dateModified": "2024-11-06 14:48:09.460 UTC",
        }
    }

    layer = Layer.from_get_response_payload(content)

    assert layer.name == "test_point"
    assert layer.resource_name == "test_workspace:test_point"
    assert layer.type == "VECTOR"
    assert layer.default_style_name == "point"
    assert layer.styles == ["burg", "capitals"]
    assert layer.attribution == {"logoWidth": 0, "logoHeight": 0}
    assert layer.queryable is None
