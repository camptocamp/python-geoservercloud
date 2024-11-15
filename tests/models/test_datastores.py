from pytest import fixture

from geoservercloud.models.datastores import DataStores


@fixture(scope="module")
def mock_response():
    return {
        "dataStores": {
            "dataStore": [
                {
                    "name": "DataStore1",
                    "href": "http://example.com/ds1",
                },
                {
                    "name": "DataStore2",
                    "href": "http://example.com/ds2",
                },
            ],
        }
    }


def test_datastores_from_get_response_payload(mock_response):

    ds = DataStores.from_get_response_payload(mock_response)

    assert ds.aslist() == ["DataStore1", "DataStore2"]


def test_datastores_from_get_response_payload_empty():
    mock_response = {"dataStores": ""}

    ds = DataStores.from_get_response_payload(mock_response)

    assert ds.aslist() == []


def test_datastores_repr():
    ds = DataStores(["DataStore1", "DataStore2"])

    expected_repr = "[{'name': 'DataStore1'}, {'name': 'DataStore2'}]"

    assert repr(ds) == expected_repr
