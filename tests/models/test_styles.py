from geoservercloud.models import Styles


def test_styles_initialization():
    workspace = "test_workspace"
    styles = ["style1", "style2"]

    styles_instance = Styles(styles, workspace)

    assert styles_instance.workspace == workspace
    assert styles_instance.styles == styles


def test_styles_from_dict_valid():
    mock_response = {
        "styles": {
            "workspace": "test_workspace",
            "style": [{"name": "style1"}, {"name": "style2"}],
        }
    }

    styles_instance = Styles.from_dict(mock_response)

    assert styles_instance.workspace == "test_workspace"
    assert styles_instance.styles == ["style1", "style2"]


def test_styles_from_dict_no_workspace():
    mock_response = {"styles": {"style": [{"name": "style1"}, {"name": "style2"}]}}

    styles_instance = Styles.from_dict(mock_response)

    assert styles_instance.workspace is None
    assert styles_instance.styles == ["style1", "style2"]


def test_styles_from_dict_empty_styles():
    mock_response = {"styles": {"workspace": "test_workspace", "style": []}}

    styles_instance = Styles.from_dict(mock_response)

    assert styles_instance.workspace == "test_workspace"
    assert styles_instance.styles == []


def test_styles_from_dict_no_styles_section():
    mock_response = {}

    styles_instance = Styles.from_dict(mock_response)

    assert styles_instance.workspace is None
    assert styles_instance.styles == []
