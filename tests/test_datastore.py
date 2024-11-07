from collections.abc import Generator
from typing import Any

import pytest
import responses
from responses import matchers

from geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL

WORKSPACE = "test_workspace"
STORE = "test_store"
HOST = "localhost"
PORT = 5432
DATABASE = "test_db"
USER = "test_user"
PASSWORD = "test_password"
SCHEMA = "test_schema"
JNDI = "java:comp/env/jdbc/data"
DESCRIPTION = "test description"


@pytest.fixture(scope="module")
def pg_payload() -> Generator[dict[str, dict[str, Any]], Any, None]:
    yield {
        "dataStore": {
            "name": STORE,
            "type": "PostGIS",
            "enabled": True,
            "connectionParameters": {
                "entry": [
                    {"@key": "dbtype", "$": "postgis"},
                    {"@key": "host", "$": HOST},
                    {"@key": "port", "$": PORT},
                    {"@key": "database", "$": DATABASE},
                    {"@key": "user", "$": USER},
                    {"@key": "passwd", "$": PASSWORD},
                    {"@key": "schema", "$": SCHEMA},
                    {
                        "@key": "namespace",
                        "$": f"http://{WORKSPACE}",
                    },
                    {"@key": "Expose primary keys", "$": "true"},
                ]
            },
            "workspace": {"name": WORKSPACE},
        }
    }


@pytest.fixture(scope="module")
def jndi_payload() -> Generator[dict[str, dict[str, Any]], Any, None]:
    yield {
        "dataStore": {
            "name": STORE,
            "description": DESCRIPTION,
            "type": "PostGIS (JNDI)",
            "enabled": True,
            "connectionParameters": {
                "entry": [
                    {"@key": "dbtype", "$": "postgis"},
                    {
                        "@key": "jndiReferenceName",
                        "$": JNDI,
                    },
                    {
                        "@key": "schema",
                        "$": SCHEMA,
                    },
                    {
                        "@key": "namespace",
                        "$": f"http://{WORKSPACE}",
                    },
                    {"@key": "Expose primary keys", "$": "true"},
                ]
            },
            "workspace": {"name": WORKSPACE},
        }
    }


@pytest.fixture(scope="module")
def datastore_get_response() -> Generator[dict[str, Any], Any, None]:
    yield {
        "dataStore": {
            "name": STORE,
            "description": DESCRIPTION,
            "type": "PostGIS (JNDI)",
            "enabled": True,
            "workspace": {
                "name": WORKSPACE,
                "href": f"http://localhost:8080/geoserver/rest/workspaces/{WORKSPACE}.json",
            },
            "connectionParameters": {
                "entry": [
                    {"@key": "schema", "$": SCHEMA},
                    {"@key": "jndiReferenceName", "$": JNDI},
                    {"@key": "Expose primary keys", "$": "true"},
                    {"@key": "dbtype", "$": "postgis"},
                    {"@key": "namespace", "$": "http://{WORKSPACE}"},
                ]
            },
            "_default": False,
            "disableOnConnFailure": False,
            "featureTypes": f"http://localhost:8080/geoserver/rest/workspaces/{WORKSPACE}/datastores/{STORE}/featuretypes.json",
        }
    }


@pytest.fixture(scope="module")
def datastores_get_response() -> Generator[dict[str, Any], Any, None]:
    yield {
        "dataStores": {
            "dataStore": [
                {
                    "name": STORE,
                    "href": f"http://localhost:8080/geoserver/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
                }
            ]
        }
    }


def test_get_datastores(
    geoserver: GeoServerCloud, datastores_get_response: dict[str, Any]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores.json",
            status=200,
            json=datastores_get_response,
        )

        datastores, status_code = geoserver.get_datastores(workspace_name=WORKSPACE)
        assert datastores == datastores_get_response["dataStores"]["dataStore"]
        assert status_code == 200


def test_get_pg_datastore_ok(
    geoserver: GeoServerCloud, datastore_get_response: dict[str, Any]
) -> None:
    expected_datastore = {
        "name": STORE,
        "description": DESCRIPTION,
        "type": "PostGIS (JNDI)",
        "enabled": True,
        "workspace": WORKSPACE,
        "connectionParameters": {
            "entry": {
                "schema": "test_schema",
                "jndiReferenceName": "java:comp/env/jdbc/data",
                "Expose primary keys": "true",
                "dbtype": "postgis",
                "namespace": "http://{WORKSPACE}",
            }
        },
        "_default": False,
        "disableOnConnFailure": False,
    }
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            status=200,
            json=datastore_get_response,
        )
        content, status_code = geoserver.get_pg_datastore(WORKSPACE, STORE)
        assert content == expected_datastore
        assert status_code == 200


def test_get_pg_datastore_not_found(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            status=404,
            body=b"No such datastore: test_workspace,test_datastore",
        )
        content, status_code = geoserver.get_pg_datastore(WORKSPACE, STORE)
        assert content == "No such datastore: test_workspace,test_datastore"
        assert status_code == 404


def test_create_pg_datastore(
    geoserver: GeoServerCloud, pg_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            status=404,
        )
        rsps.post(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores.json",
            status=201,
            body=b"test_store",
            match=[matchers.json_params_matcher(pg_payload)],
        )

        content, code = geoserver.create_pg_datastore(
            workspace_name=WORKSPACE,
            datastore_name=STORE,
            pg_host=HOST,
            pg_port=PORT,
            pg_db=DATABASE,
            pg_user=USER,
            pg_password=PASSWORD,
            pg_schema=SCHEMA,
        )

        assert content == STORE
        assert code == 201


def test_update_pg_datastore(
    geoserver: GeoServerCloud, pg_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            status=200,
        )
        rsps.put(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            status=200,
            body=b"",
            match=[matchers.json_params_matcher(pg_payload)],
        )

        content, code = geoserver.create_pg_datastore(
            workspace_name=WORKSPACE,
            datastore_name=STORE,
            pg_host=HOST,
            pg_port=PORT,
            pg_db=DATABASE,
            pg_user=USER,
            pg_password=PASSWORD,
            pg_schema=SCHEMA,
        )

        assert content == ""
        assert code == 200


def test_create_jndi_datastore(
    geoserver: GeoServerCloud, jndi_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            status=404,
        )
        rsps.post(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores.json",
            status=201,
            body=b"test_store",
            match=[matchers.json_params_matcher(jndi_payload)],
        )

        content, code = geoserver.create_jndi_datastore(
            workspace_name=WORKSPACE,
            datastore_name=STORE,
            jndi_reference=JNDI,
            pg_schema=SCHEMA,
            description=DESCRIPTION,
        )

        assert content == STORE
        assert code == 201


def test_update_jndi_datastore(
    geoserver: GeoServerCloud, jndi_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            status=200,
        )
        rsps.put(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            status=200,
            body=b"",
            match=[matchers.json_params_matcher(jndi_payload)],
        )

        content, code = geoserver.create_jndi_datastore(
            workspace_name=WORKSPACE,
            datastore_name=STORE,
            jndi_reference=JNDI,
            pg_schema=SCHEMA,
            description=DESCRIPTION,
        )

        assert content == ""
        assert code == 200
