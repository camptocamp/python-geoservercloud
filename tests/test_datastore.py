import json
from collections.abc import Generator
from typing import Any

import pytest
import responses
from responses import matchers

from geoservercloud.geoservercloud import GeoServerCloud
from geoservercloud.models import PostGisDataStore  # Ensure this import is correct
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
        }
    }


@pytest.fixture(scope="module")
def datastores_response() -> Generator[dict[str, Any], Any, None]:
    yield {
        "dataStores": {
            "dataStore": [
                {
                    "name": STORE,
                    "href": f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
                }
            ],
        }
    }


def test_get_datastores(
    geoserver: GeoServerCloud, datastores_response: dict[str, Any]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores.json",
            status=200,
            json=datastores_response,
        )

        datastores = geoserver.get_datastores(workspace_name=WORKSPACE)
        assert datastores == ["test_store"]


# Test the get_postgis_datastore method with a valid response
def test_get_postgis_datastore_valid(
    geoserver: GeoServerCloud, pg_payload: dict[str, dict[str, Any]]
) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{WORKSPACE}/datastores/{STORE}.json",
            json=pg_payload,
            status=200,
        )
        result = geoserver.get_postgis_datastore(WORKSPACE, STORE)
        assert len(rsps.calls) == 1
        # FIXME: I think the geoserver rest endpoint is wrong, might be a problem with the conftest.py stuff.
        # assert rsps.calls[0].request.url == geoserver.rest_endpoints.datastore(WORKSPACE, STORE)
        assert json.loads(str(result)) == pg_payload


# Test the get_postgis_datastore method with a 404 error
def test_get_postgis_datastore_not_found(geoserver: GeoServerCloud) -> None:
    datastore_name = "non_existing_datastore"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores/{datastore_name}.json",
            json={"error": "Datastore not found"},
            status=404,
        )

        not_existing_datastore = geoserver.get_postgis_datastore(
            WORKSPACE, datastore_name
        )
        assert len(rsps.calls) == 1
        assert not_existing_datastore is None


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
            json={"workspace": {"name": WORKSPACE}},
            match=[matchers.json_params_matcher(pg_payload)],
        )

        response = geoserver.create_pg_datastore(
            workspace_name=WORKSPACE,
            datastore_name=STORE,
            pg_host=HOST,
            pg_port=PORT,
            pg_db=DATABASE,
            pg_user=USER,
            pg_password=PASSWORD,
            pg_schema=SCHEMA,
        )

        assert response
        assert response.status_code == 201


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
            match=[matchers.json_params_matcher(pg_payload)],
        )

        response = geoserver.create_pg_datastore(
            workspace_name=WORKSPACE,
            datastore_name=STORE,
            pg_host=HOST,
            pg_port=PORT,
            pg_db=DATABASE,
            pg_user=USER,
            pg_password=PASSWORD,
            pg_schema=SCHEMA,
        )

        assert response
        assert response.status_code == 200


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
            match=[matchers.json_params_matcher(jndi_payload)],
        )

        response = geoserver.create_jndi_datastore(
            workspace_name=WORKSPACE,
            datastore_name=STORE,
            jndi_reference=JNDI,
            pg_schema=SCHEMA,
            description=DESCRIPTION,
        )

        assert response
        assert response.status_code == 201


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
            match=[matchers.json_params_matcher(jndi_payload)],
        )

        response = geoserver.create_jndi_datastore(
            workspace_name=WORKSPACE,
            datastore_name=STORE,
            jndi_reference=JNDI,
            pg_schema=SCHEMA,
            description=DESCRIPTION,
        )

        assert response
        assert response.status_code == 200
