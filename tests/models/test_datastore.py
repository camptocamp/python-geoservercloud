from unittest.mock import Mock

import pytest

from geoservercloud.models import (  # Adjust based on your actual module name
    KeyDollarListDict,
    PostGisDataStore,
)


# Test initialization of the PostGisDataStore class
def test_postgisdatastore_initialization():
    connection_parameters = KeyDollarListDict(
        [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]
    )

    datastore = PostGisDataStore(
        "test_workspace", "test_datastore", connection_parameters
    )

    assert datastore.workspace_name == "test_workspace"
    assert datastore.data_store_name == "test_datastore"
    assert datastore.connection_parameters == connection_parameters
    assert datastore.data_store_type == "PostGIS"


# Test put_payload method
def test_postgisdatastore_put_payload():
    connection_parameters = KeyDollarListDict(
        [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]
    )

    datastore = PostGisDataStore(
        "test_workspace", "test_datastore", connection_parameters
    )

    expected_payload = {
        "dataStore": {
            "name": "test_datastore",
            "type": "PostGIS",
            "enabled": True,
            "connectionParameters": {
                "entry": [
                    {"@key": "host", "$": "localhost"},
                    {"@key": "port", "$": "5432"},
                ]
            },
        }
    }

    assert datastore.put_payload() == expected_payload


# Test post_payload method (should return the same as put_payload)
def test_postgisdatastore_post_payload():
    connection_parameters = KeyDollarListDict(
        [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]
    )

    datastore = PostGisDataStore(
        "test_workspace", "test_datastore", connection_parameters
    )

    assert datastore.post_payload() == datastore.put_payload()


# Test from_response class method
def test_postgisdatastore_from_response(mocker):
    mock_response = Mock()
    mock_response.json.return_value = {
        "dataStore": {
            "name": "test_datastore",
            "type": "PostGIS",
            "connectionParameters": {
                "entry": [
                    {"@key": "host", "$": "localhost"},
                    {"@key": "port", "$": "5432"},
                ]
            },
        }
    }

    datastore = PostGisDataStore.from_response(mock_response)

    assert datastore.data_store_name == "test_datastore"
    assert datastore.data_store_type == "PostGIS"

    # Check that connection parameters were correctly parsed into a KeyDollarListDict
    assert datastore.connection_parameters["host"] == "localhost"
    assert datastore.connection_parameters["port"] == "5432"


# Test parse_connection_parameters method
def test_postgisdatastore_parse_connection_parameters():
    json_data = {
        "dataStore": {
            "connectionParameters": {
                "entry": [
                    {"@key": "host", "$": "localhost"},
                    {"@key": "port", "$": "5432"},
                ]
            }
        }
    }

    connection_params = PostGisDataStore.parse_connection_parameters(json_data)

    assert isinstance(connection_params, KeyDollarListDict)
    assert connection_params["host"] == "localhost"
    assert connection_params["port"] == "5432"
