import responses

from geoservercloud.geoservercloud import GeoServerCloud


def test_create_role(geoserver: GeoServerCloud) -> None:
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/rest/security/roles/role/{role}",
            status=201,
        )

        response = geoserver.create_role(role)

        assert response.status_code == 201


def test_create_role_if_not_exists_case_true(geoserver: GeoServerCloud) -> None:
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/security/roles", status=200, json={"roles": []}
        )
        rsps.post(
            url=f"{geoserver.url}/rest/security/roles/role/{role}",
            status=201,
        )

        response = geoserver.create_role_if_not_exists(role)
        assert response
        assert response.status_code == 201


def test_create_role_if_not_exists_case_false(geoserver: GeoServerCloud) -> None:
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/security/roles",
            status=200,
            json={"roles": [role]},
        )

        response = geoserver.create_role_if_not_exists(role)
        assert response is None


def test_delete_role(geoserver: GeoServerCloud) -> None:
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/rest/security/roles/role/{role}",
            status=200,
        )

        response = geoserver.delete_role(role)

        assert response.status_code == 200
