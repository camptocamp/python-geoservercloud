from unittest.mock import Mock

import pytest

from geoservercloud.models import Workspace


def test_workspace_initialization():
    workspace = Workspace("test_workspace", isolated=True)

    assert workspace.name == "test_workspace"
    assert workspace.isolated is True


def test_workspace_put_payload_isolated():
    workspace = Workspace("test_workspace", isolated=True)

    expected_payload = {"workspace": {"name": "test_workspace", "isolated": True}}

    assert workspace.put_payload() == expected_payload


def test_workspace_post_payload():
    workspace = Workspace("test_workspace", isolated=True)

    expected_payload = workspace.put_payload()

    assert workspace.post_payload() == expected_payload


def test_workspace_from_response_isolated():
    mock_response = Mock()
    mock_response.json.return_value = {
        "workspace": {"name": "test_workspace", "isolated": True}
    }

    workspace = Workspace.from_response(mock_response)

    assert workspace.name == "test_workspace"
    assert workspace.isolated is True


def test_workspace_from_response_not_isolated():
    mock_response = Mock()
    mock_response.json.return_value = {"workspace": {"name": "test_workspace"}}

    workspace = Workspace.from_response(mock_response)

    assert workspace.name == "test_workspace"
    assert workspace.isolated is False
