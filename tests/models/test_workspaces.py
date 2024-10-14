from unittest.mock import Mock

import jsonschema
import pytest

from geoservercloud.models import Workspaces


# Test initialization of the Workspaces class
def test_workspaces_initialization():
    initial_workspaces = {"Workspace1": "http://example.com/ws1"}
    workspaces = Workspaces(initial_workspaces)

    assert workspaces.workspaces == initial_workspaces


# Test the find method to ensure it finds existing workspaces
def test_workspaces_find_existing():
    initial_workspaces = {"Workspace1": "http://example.com/ws1"}
    workspaces = Workspaces(initial_workspaces)

    assert workspaces.find("Workspace1") == "http://example.com/ws1"


# Test the find method to ensure it returns None for non-existing workspaces
def test_workspaces_find_non_existing():
    workspaces = Workspaces({"Workspace1": "http://example.com/ws1"})

    assert workspaces.find("NonExistingWorkspace") is None


# Test the from_response method with an empty response
def test_workspaces_from_response_empty():
    mock_response = Mock()
    mock_response.json.return_value = {"workspaces": {}}

    workspaces = Workspaces.from_response(mock_response)

    assert len(workspaces.workspaces) == 0
