from geoservercloud.models import (
    KeyDollarListDict,
    PostGisDataStore,
)


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


def test_postgisdatastore_post_payload():
    connection_parameters = KeyDollarListDict(
        [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]
    )

    datastore = PostGisDataStore(
        "test_workspace", "test_datastore", connection_parameters
    )

    assert datastore.post_payload() == datastore.put_payload()


def test_postgisdatastore_from_dict():
    mock_response = {
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

    datastore = PostGisDataStore.from_dict(mock_response)

    assert datastore.data_store_name == "test_datastore"
    assert datastore.data_store_type == "PostGIS"

    assert datastore.connection_parameters["host"] == "localhost"
    assert datastore.connection_parameters["port"] == "5432"


def test_postgisdatastore_parse_connection_parameters():
    content = {
        "dataStore": {
            "connectionParameters": {
                "entry": [
                    {"@key": "host", "$": "localhost"},
                    {"@key": "port", "$": "5432"},
                ]
            }
        }
    }

    connection_params = PostGisDataStore.parse_connection_parameters(content)

    assert isinstance(connection_params, KeyDollarListDict)
    assert connection_params["host"] == "localhost"
    assert connection_params["port"] == "5432"
