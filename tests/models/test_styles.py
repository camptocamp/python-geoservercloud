import pytest

from geoservercloud.models import Styles


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
    styles = ["style1", "style2"]

    styles_instance = Styles(styles, workspace)

    assert styles_instance.workspace == workspace
    assert styles_instance.aslist() == styles


def test_styles_from_get_response(styles_get_response_payload):
    styles_instance = Styles.from_get_response_payload(styles_get_response_payload)

    assert styles_instance.aslist() == ["style1", "style2"]


def test_styles_from_get_response_empty(empty_styles_get_response_payload):

    styles_instance = Styles.from_get_response_payload(
        empty_styles_get_response_payload
    )

    assert styles_instance.aslist() == []
