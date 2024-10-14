from unittest.mock import Mock

import pytest

from geoservercloud.models import Workspace


# Test normal initialization of the Workspace class
def test_workspace_initialization():
    workspace = Workspace("test_workspace", isolated=True)

    assert workspace.name == "test_workspace"
    assert workspace.isolated is True


# Test the put_payload method with isolated=True
def test_workspace_put_payload_isolated():
    workspace = Workspace("test_workspace", isolated=True)

    expected_payload = {"workspace": {"name": "test_workspace", "isolated": True}}

    assert workspace.put_payload() == expected_payload


# Test the put_payload method with isolated=False
def test_workspace_put_payload_not_isolated():
    workspace = Workspace("test_workspace", isolated=False)

    expected_payload = {"workspace": {"name": "test_workspace"}}

    assert workspace.put_payload() == expected_payload


# Test the post_payload method (should be the same as put_payload)
def test_workspace_post_payload():
    workspace = Workspace("test_workspace", isolated=True)

    expected_payload = workspace.put_payload()

    assert workspace.post_payload() == expected_payload


# Test the from_response class method with isolated=True in response
def test_workspace_from_response_isolated():
    mock_response = Mock()
    mock_response.json.return_value = {
        "workspace": {"name": "test_workspace", "isolated": True}
    }

    workspace = Workspace.from_response(mock_response)

    assert workspace.name == "test_workspace"
    assert workspace.isolated is True


# Test the from_response class method with isolated=False (not present) in response
def test_workspace_from_response_not_isolated():
    mock_response = Mock()
    mock_response.json.return_value = {"workspace": {"name": "test_workspace"}}

    workspace = Workspace.from_response(mock_response)

    assert workspace.name == "test_workspace"
    assert workspace.isolated is False


# Test the from_response class method with missing workspace name
def test_workspace_from_response_missing_name():
    mock_response = Mock()
    mock_response.json.return_value = {"workspace": {}}

    workspace = Workspace.from_response(mock_response)

    assert workspace.name is None
    assert workspace.isolated is False
