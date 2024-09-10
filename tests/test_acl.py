import responses
import responses.matchers

from geoservercloud.geoservercloud import GeoServerCloud


def test_create_acl_admin_rule(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/acl/api/adminrules",
            status=201,
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "priority": 1,
                        "access": "ADMIN",
                        "role": "TEST_ROLE",
                        "user": "TEST_USER",
                        "workspace": "TEST_WORKSPACE",
                    }
                )
            ],
        )

        response = geoserver.create_acl_admin_rule(
            priority=1,
            access="ADMIN",
            role="TEST_ROLE",
            user="TEST_USER",
            workspace="TEST_WORKSPACE",
        )
        assert response.status_code == 201


def test_create_acl_rule(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/acl/api/rules",
            status=201,
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "priority": 1,
                        "access": "ALLOW",
                        "role": "TEST_ROLE",
                        "workspace": "TEST_WORKSPACE",
                        "service": "WMS",
                    }
                )
            ],
        )

        response = geoserver.create_acl_rule(
            priority=1,
            access="ALLOW",
            role="TEST_ROLE",
            workspace="TEST_WORKSPACE",
            service="WMS",
        )
        assert response.status_code == 201


def test_delete_acl_admin_rule(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/acl/api/adminrules/id/1",
            status=200,
        )

        response = geoserver.delete_acl_admin_rule(1)
        assert response.status_code == 200


def test_delete_all_acl_admin_rules(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/acl/api/adminrules",
            status=200,
        )

        response = geoserver.delete_all_acl_admin_rules()
        assert response.status_code == 200


def test_delete_all_acl_rules(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/acl/api/rules",
            status=200,
        )

        response = geoserver.delete_all_acl_rules()
        assert response.status_code == 200
