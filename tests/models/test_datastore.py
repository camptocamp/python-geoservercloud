import pytest

from geoservercloud.models.common import KeyDollarListDict
from geoservercloud.models.datastore import DataStore


@pytest.fixture(scope="module")
def pg_payload():
    yield {
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
            "workspace": {"name": "test_workspace"},
        }
    }


def test_postgisdatastore_initialization():
    connection_parameters = KeyDollarListDict(
        [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]
    )

    datastore = DataStore(
        "test_workspace", "test_datastore", connection_parameters, "PostGIS"
    )

    assert datastore.workspace_name == "test_workspace"
    assert datastore.name == "test_datastore"
    assert datastore.connection_parameters == connection_parameters
    assert datastore.type == "PostGIS"


def test_postgisdatastore_put_payload(pg_payload):
    connection_parameters = KeyDollarListDict(
        [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]
    )

    datastore = DataStore(
        "test_workspace", "test_datastore", connection_parameters, "PostGIS"
    )

    assert datastore.put_payload() == pg_payload


def test_postgisdatastore_post_payload():
    connection_parameters = KeyDollarListDict(
        [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]
    )

    datastore = DataStore(
        "test_workspace", "test_datastore", connection_parameters, "PostGIS"
    )

    assert datastore.post_payload() == datastore.put_payload()


def test_postgisdatastore_from_get_response_payload(pg_payload):

    datastore = DataStore.from_get_response_payload(pg_payload)

    assert datastore.name == "test_datastore"
    assert datastore.type == "PostGIS"

    assert isinstance(datastore.connection_parameters, KeyDollarListDict)
    assert datastore.connection_parameters["host"] == "localhost"
    assert datastore.connection_parameters["port"] == "5432"


def test_postgisdatastore_asdict(pg_payload):
    datastore = DataStore.from_get_response_payload(pg_payload)

    assert datastore.asdict() == {
        "name": "test_datastore",
        "type": "PostGIS",
        "enabled": True,
        "connectionParameters": {
            "entry": {
                "host": "localhost",
                "port": "5432",
            }
        },
        "workspace": "test_workspace",
    }
