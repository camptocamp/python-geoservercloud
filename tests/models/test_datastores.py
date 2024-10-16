from pytest import fixture

from geoservercloud.models import DataStores


@fixture(scope="module")
def mock_datastore():
    return {
        "name": "DataStore1",
        "href": "http://example.com/ds1",
    }


@fixture(scope="module")
def mock_response(mock_datastore):
    return {
        "dataStores": {
            "dataStore": [mock_datastore],
        }
    }


def test_datastores_initialization(mock_datastore):
    ds = DataStores([mock_datastore])

    assert ds.aslist() == [mock_datastore]


def test_datastores_from_get_response_payload(mock_datastore, mock_response):

    ds = DataStores.from_get_response_payload(mock_response)

    assert ds.aslist() == [mock_datastore]


def test_datastores_from_get_response_payload_empty():
    mock_response = {"dataStores": ""}

    ds = DataStores.from_get_response_payload(mock_response)

    assert ds.aslist() == []


def test_datastores_repr(mock_datastore):
    ds = DataStores([mock_datastore])

    expected_repr = "[{'name': 'DataStore1', 'href': 'http://example.com/ds1'}]"

    assert repr(ds) == expected_repr
