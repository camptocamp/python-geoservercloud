from geoservercloud.models import DataStores


def test_datastores_initialization():
    workspace_name = "test_workspace"
    datastores = ["store1", "store2"]

    ds = DataStores(workspace_name, datastores)

    assert ds.workspace_name == "test_workspace"
    assert ds.datastores == datastores


def test_datastores_from_dict():
    mock_response = {
        "dataStores": {
            "workspace": {"name": "test_workspace"},
            "dataStore": [{"name": "store1"}, {"name": "store2"}],
        }
    }

    ds = DataStores.from_dict(mock_response)

    assert ds.workspace_name == "test_workspace"
    assert ds.datastores == ["store1", "store2"]


def test_datastores_from_dict_empty():
    mock_response = {
        "dataStores": {"workspace": {"name": "empty_workspace"}, "dataStore": []}
    }

    ds = DataStores.from_dict(mock_response)

    assert ds.workspace_name == "empty_workspace"
    assert ds.datastores == []


def test_datastores_repr():
    ds = DataStores("test_workspace", ["store1", "store2"])

    expected_repr = "['store1', 'store2']"

    assert repr(ds) == expected_repr
