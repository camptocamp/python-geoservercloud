from unittest.mock import Mock

import pytest

from geoservercloud.models import Styles  # Replace with the correct import path


# Test initialization of Styles class
def test_styles_initialization():
    workspace = "test_workspace"
    styles = ["style1", "style2"]

    styles_instance = Styles(styles, workspace)

    assert styles_instance.workspace == workspace
    assert styles_instance.styles == styles


# Test the from_response method with a valid response
def test_styles_from_response_valid():
    mock_response = Mock()
    mock_response.json.return_value = {
        "styles": {
            "workspace": "test_workspace",
            "style": [{"name": "style1"}, {"name": "style2"}],
        }
    }

    styles_instance = Styles.from_response(mock_response)

    assert styles_instance.workspace == "test_workspace"
    assert styles_instance.styles == ["style1", "style2"]


# Test the from_response method when no workspace is provided
def test_styles_from_response_no_workspace():
    mock_response = Mock()
    mock_response.json.return_value = {
        "styles": {"style": [{"name": "style1"}, {"name": "style2"}]}
    }

    styles_instance = Styles.from_response(mock_response)

    assert styles_instance.workspace is None
    assert styles_instance.styles == ["style1", "style2"]


# Test the from_response method with empty styles list
def test_styles_from_response_empty_styles():
    mock_response = Mock()
    mock_response.json.return_value = {
        "styles": {"workspace": "test_workspace", "style": []}
    }

    styles_instance = Styles.from_response(mock_response)

    assert styles_instance.workspace == "test_workspace"
    assert styles_instance.styles == []


# Test the from_response method with no styles section
def test_styles_from_response_no_styles_section():
    mock_response = Mock()
    mock_response.json.return_value = {}

    styles_instance = Styles.from_response(mock_response)

    assert styles_instance.workspace is None
    assert styles_instance.styles == []
