from unittest.mock import Mock

import pytest

from geoservercloud.models import DataStores  # Replace with the actual module name


# Test initialization of DataStores class
def test_datastores_initialization():
    workspace_name = "test_workspace"
    datastores = ["store1", "store2"]

    ds = DataStores(workspace_name, datastores)

    assert ds.workspace_name == "test_workspace"
    assert ds.datastores == datastores


# Test the from_response class method with a valid response
def test_datastores_from_response(mocker):
    mock_response = Mock()
    mock_response.json.return_value = {
        "dataStores": {
            "workspace": {"name": "test_workspace"},
            "dataStore": [{"name": "store1"}, {"name": "store2"}],
        }
    }

    ds = DataStores.from_response(mock_response)

    assert ds.workspace_name == "test_workspace"
    assert ds.datastores == ["store1", "store2"]


# Test from_response with an empty response
def test_datastores_from_response_empty():
    mock_response = Mock()
    mock_response.json.return_value = {
        "dataStores": {"workspace": {"name": "empty_workspace"}, "dataStore": []}
    }

    ds = DataStores.from_response(mock_response)

    assert ds.workspace_name == "empty_workspace"
    assert ds.datastores == []


# Test the __repr__ method
def test_datastores_repr():
    ds = DataStores("test_workspace", ["store1", "store2"])

    expected_repr = "['store1', 'store2']"

    assert repr(ds) == expected_repr
