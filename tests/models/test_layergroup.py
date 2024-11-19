from geoservercloud.models.common import ReferencedObjectModel
from geoservercloud.models.layergroup import LayerGroup


def test_layer_group_initialization():
    layer_group = LayerGroup(
        name="test_name",
        workspace_name="test_workspace",
        mode="SINGLE",
        enabled=True,
        advertised=True,
        title={"en": "Test Title"},
        abstract={"en": "Test Abstract"},
        publishables=["test_workspace:layer1", "test_workspace:layer2"],
        styles=["style1", "style2"],
        bounds={"minx": -180, "maxx": 180, "miny": -90, "maxy": 90, "crs": "EPSG:4326"},
    )

    assert layer_group.name == "test_name"
    assert layer_group.workspace_name == "test_workspace"
    assert layer_group.mode == "SINGLE"
    assert layer_group.enabled == True
    assert layer_group.advertised == True
    assert layer_group.title.asdict()["internationalTitle"] == {"en": "Test Title"}
    assert layer_group.abstract.asdict()["internationalAbstract"] == {
        "en": "Test Abstract"
    }
    assert isinstance(layer_group.publishables, list)
    assert [p.name for p in layer_group.publishables] == [
        "test_workspace:layer1",
        "test_workspace:layer2",
    ]
    assert isinstance(layer_group.styles, list)
    assert [s.name for s in layer_group.styles] == ["style1", "style2"]
    assert layer_group.bounds == {
        "minx": -180,
        "maxx": 180,
        "miny": -90,
        "maxy": 90,
        "crs": "EPSG:4326",
    }


def test_layer_group_from_get_response_payload():
    mock_response = {
        "layerGroup": {
            "name": "test_name",
            "workspace": {"name": "test_workspace"},
            "mode": "SINGLE",
            "publishables": {
                "published": [
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer1",
                        "href": "http://localhost",
                    },
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer2",
                        "href": "http://localhost",
                    },
                ]
            },
            "styles": {
                "style": [
                    {
                        "name": "point",
                        "href": "https://georchestra-127-0-1-1.traefik.me/geoserver/rest/styles/point.json",
                    },
                    {
                        "name": "line",
                        "href": "https://georchestra-127-0-1-1.traefik.me/geoserver/rest/styles/line.json",
                    },
                ]
            },
            "bounds": {
                "minx": -180,
                "maxx": 180,
                "miny": -90,
                "maxy": 90,
                "crs": "EPSG:4326",
            },
            "enabled": True,
            "advertised": True,
            "title": "Test Title",
            "abstract": "Test Abstract",
        }
    }

    layer_group = LayerGroup.from_get_response_payload(mock_response)

    assert layer_group.name == "test_name"
    assert layer_group.workspace_name == "test_workspace"
    assert layer_group.mode == "SINGLE"
    assert layer_group.enabled == True
    assert layer_group.advertised == True
    assert layer_group.title.asdict()["title"] == "Test Title"
    assert layer_group.abstract.asdict()["abstract"] == "Test Abstract"
    assert isinstance(layer_group.publishables, list)
    assert [p.name for p in layer_group.publishables] == [
        "test_workspace:layer1",
        "test_workspace:layer2",
    ]
    assert isinstance(layer_group.styles, list)
    assert [s.name for s in layer_group.styles] == ["point", "line"]
    assert layer_group.bounds == {
        "minx": -180,
        "maxx": 180,
        "miny": -90,
        "maxy": 90,
        "crs": "EPSG:4326",
    }


def test_layer_group_from_get_response_payload_one_layer():
    mock_response = {
        "layerGroup": {
            "name": "test_name",
            "workspace": {"name": "test_workspace"},
            "mode": "SINGLE",
            "publishables": {
                "published": {
                    "@type": "layer",
                    "name": "test_workspace:layer",
                    "href": "http://localhost",
                }
            },
            "styles": {
                "style": {
                    "name": "test_style",
                    "href": "http://localhost",
                }
            },
        }
    }

    layer_group = LayerGroup.from_get_response_payload(mock_response)

    assert isinstance(layer_group.publishables, list)
    assert [p.name for p in layer_group.publishables] == [
        "test_workspace:layer",
    ]
    assert isinstance(layer_group.styles, list)
    assert [s.name for s in layer_group.styles] == ["test_style"]


def test_layer_group_from_get_response_payload_default_styles():
    mock_response = {
        "layerGroup": {
            "name": "test_name",
            "workspace": {"name": "test_workspace"},
            "mode": "SINGLE",
            "publishables": {
                "published": [
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer1",
                        "href": "http://localhost",
                    },
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer2",
                        "href": "http://localhost",
                    },
                ]
            },
            "styles": {"style": [""] * 2},
        }
    }

    layer_group = LayerGroup.from_get_response_payload(mock_response)

    assert isinstance(layer_group.publishables, list)
    assert [p.name for p in layer_group.publishables] == [
        "test_workspace:layer1",
        "test_workspace:layer2",
    ]
    assert isinstance(layer_group.styles, list)
    assert [s.name for s in layer_group.styles] == ["", ""]


def test_layer_group_post_payload():
    layer_group = LayerGroup(
        name="test_group",
        workspace_name="test_workspace",
        mode="SINGLE",
        enabled=True,
        advertised=True,
        title={"en": "Test Title"},
        abstract={"en": "Test Abstract"},
        publishables=["test_workspace:layer1", "test_workspace:layer2"],
        styles=["point", "line"],
        bounds={"minx": -180, "maxx": 180, "miny": -90, "maxy": 90, "crs": "EPSG:4326"},
    )

    assert layer_group.post_payload() == {
        "layerGroup": {
            "name": "test_group",
            "mode": "SINGLE",
            "enabled": True,
            "advertised": True,
            "workspace": {"name": "test_workspace"},
            "internationalTitle": {
                "en": "Test Title",
            },
            "internationalAbstract": {
                "en": "Test Abstract",
            },
            "publishables": {
                "published": [
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer1",
                    },
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer2",
                    },
                ]
            },
            "styles": {
                "style": [
                    {
                        "name": "point",
                    },
                    {
                        "name": "line",
                    },
                ]
            },
            "bounds": {
                "minx": -180,
                "maxx": 180,
                "miny": -90,
                "maxy": 90,
                "crs": "EPSG:4326",
            },
        }
    }


def test_layer_group_post_payload_one_layer():
    layer_group = LayerGroup(
        publishables=["test_workspace:layer"],
        styles=["point"],
    )

    assert layer_group.post_payload() == {
        "layerGroup": {
            "publishables": {
                "published": [
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer",
                    }
                ],
            },
            "styles": {
                "style": [
                    {
                        "name": "point",
                    }
                ],
            },
        }
    }


def test_layer_group_post_payload_default_styles():
    layer_group = LayerGroup(
        publishables=["test_workspace:layer1", "test_workspace:layer2"],
    )

    assert layer_group.post_payload() == {
        "layerGroup": {
            "publishables": {
                "published": [
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer1",
                    },
                    {
                        "@type": "layer",
                        "name": "test_workspace:layer2",
                    },
                ]
            },
            "styles": {
                "style": [
                    {
                        "name": "",
                    },
                    {
                        "name": "",
                    },
                ]
            },
        }
    }
