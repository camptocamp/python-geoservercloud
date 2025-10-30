import pytest

from geoservercloud.models.styles import Styles


@pytest.fixture
def styles_get_response_payload():
    return {
        "styles": {
            "style": [
                {
                    "name": "style1",
                    "href": "http://localhost/style1.json",
                },
                {
                    "name": "style2",
                    "href": "http://localhost/style2.json",
                },
            ]
        }
    }


@pytest.fixture
def empty_styles_get_response_payload():
    return {"styles": ""}


def test_styles_initialization():
    workspace = "test_workspace"
    styles = [
        {"name": "style1", "href": "http://localhost/style1.json"},
        {"name": "style2", "href": "http://localhost/style2.json"},
    ]

    styles_instance = Styles(styles, workspace)

    assert styles_instance.workspace == workspace
    assert styles_instance.aslist() == styles


def test_styles_from_get_response(styles_get_response_payload):
    styles_instance = Styles.from_get_response_payload(styles_get_response_payload)

    expected = [
        {"name": "style1", "href": "http://localhost/style1.json"},
        {"name": "style2", "href": "http://localhost/style2.json"},
    ]
    assert styles_instance.aslist() == expected


def test_styles_from_get_response_empty(empty_styles_get_response_payload):

    styles_instance = Styles.from_get_response_payload(
        empty_styles_get_response_payload
    )

    assert styles_instance.aslist() == []


def test_styles_post_payload():
    styles = [
        {"name": "style1", "href": "http://localhost/style1.json"},
        {"name": "style2", "href": "http://localhost/style2.json"},
    ]

    styles_instance = Styles(styles)

    assert styles_instance.post_payload() == {
        "styles": {
            "style": [
                {"name": "style1"},
                {"name": "style2"},
            ]
        }
    }
