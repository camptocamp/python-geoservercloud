import responses

from geoservercloud import GeoServerCloud


def test_create_role_if_not_exists_case_true(geoserver: GeoServerCloud) -> None:
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/security/roles.json",
            status=200,
            json={"roles": []},
        )
        rsps.post(
            url=f"{geoserver.url}/rest/security/roles/role/{role}.json",
            status=201,
        )

        content, code = geoserver.create_role(role)
        assert content == ""
        assert code == 201


def test_create_role_if_not_exists_case_false(geoserver: GeoServerCloud) -> None:
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/security/roles.json",
            status=200,
            json={"roles": [role]},
        )

        content, code = geoserver.create_role(role)
        assert content == ""
        assert code == 200


def test_delete_role(geoserver: GeoServerCloud) -> None:
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/rest/security/roles/role/{role}.json",
            status=200,
            body=b"",
        )

        content, code = geoserver.delete_role(role)

        assert content == ""
        assert code == 200


def test_get_user_roles(geoserver: GeoServerCloud) -> None:
    user = "test_user"
    roles = ["test_role1", "test_role2"]
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/security/roles/user/{user}.json",
            status=200,
            json={"roles": roles},
        )

        content, code = geoserver.get_user_roles(user)

        assert content == roles
        assert code == 200


def test_assign_role_to_user(geoserver: GeoServerCloud) -> None:
    user = "test_user"
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/rest/security/roles/role/{role}/user/{user}.json",
            status=200,
            body=b"",
        )

        content, code = geoserver.assign_role_to_user(user, role)

        assert content == ""
        assert code == 200


def test_remove_role_from_user(geoserver: GeoServerCloud) -> None:
    user = "test_user"
    role = "test_role"
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/rest/security/roles/role/{role}/user/{user}.json",
            status=200,
            body=b"",
        )

        content, code = geoserver.remove_role_from_user(user, role)

        assert content == ""
        assert code == 200
