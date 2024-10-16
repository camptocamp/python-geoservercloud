import responses
import responses.matchers

from geoservercloud import GeoServerCloud


def test_create_acl_admin_rule(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/acl/api/adminrules",
            status=200,
            json={
                "id": "a",
                "priority": 22,
                "access": "ADMIN",
                "role": "TEST_ROLE",
                "user": "TEST_USER",
                "workspace": "TEST_WORKSPACE",
            },
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "priority": 22,
                        "access": "ADMIN",
                        "role": "TEST_ROLE",
                        "user": "TEST_USER",
                        "workspace": "TEST_WORKSPACE",
                    }
                )
            ],
        )

        content, code = geoserver.create_acl_admin_rule(
            priority=22,
            access="ADMIN",
            role="TEST_ROLE",
            user="TEST_USER",
            workspace_name="TEST_WORKSPACE",
        )
        assert content == {
            "id": "a",
            "priority": 22,
            "access": "ADMIN",
            "role": "TEST_ROLE",
            "user": "TEST_USER",
            "workspace": "TEST_WORKSPACE",
        }
        assert code == 200


def test_create_acl_rule(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/acl/api/rules",
            status=201,
            json={
                "id": "62",
                "priority": 12,
                "access": "ALLOW",
                "role": "TEST_ROLE",
                "workspace": "TEST_WORKSPACE",
                "service": "WMS",
            },
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "priority": 12,
                        "access": "ALLOW",
                        "role": "TEST_ROLE",
                        "workspace": "TEST_WORKSPACE",
                        "service": "WMS",
                    }
                )
            ],
        )

        content, code = geoserver.create_acl_rule(
            priority=12,
            access="ALLOW",
            role="TEST_ROLE",
            workspace_name="TEST_WORKSPACE",
            service="WMS",
        )
        assert content == {
            "id": "62",
            "priority": 12,
            "access": "ALLOW",
            "role": "TEST_ROLE",
            "workspace": "TEST_WORKSPACE",
            "service": "WMS",
        }
        assert code == 201


def test_create_acl_rule_for_requests(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/acl/api/rules",
            status=201,
            json={
                "id": "64",
                "priority": 11,
                "access": "ALLOW",
                "role": "TEST_ROLE",
                "service": "WMS",
                "request": "GETCAPABILITIES",
                "workspace": "TEST_WORKSPACE",
            },
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "priority": 11,
                        "access": "ALLOW",
                        "role": "TEST_ROLE",
                        "workspace": "TEST_WORKSPACE",
                        "service": "WMS",
                        "request": "GetCapabilities",
                    }
                )
            ],
        )
        rsps.post(
            url=f"{geoserver.url}/acl/api/rules",
            status=201,
            json={
                "id": "65",
                "priority": 11,
                "access": "ALLOW",
                "role": "TEST_ROLE",
                "service": "WMS",
                "request": "GETMAP",
                "workspace": "TEST_WORKSPACE",
            },
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "priority": 11,
                        "access": "ALLOW",
                        "role": "TEST_ROLE",
                        "workspace": "TEST_WORKSPACE",
                        "service": "WMS",
                        "request": "GetMap",
                    }
                )
            ],
        )

        r1, r2 = geoserver.create_acl_rules_for_requests(
            priority=11,
            access="ALLOW",
            role="TEST_ROLE",
            workspace_name="TEST_WORKSPACE",
            service="WMS",
            requests=["GetCapabilities", "GetMap"],
        )
        content, code = r1
        assert content == {
            "id": "64",
            "priority": 11,
            "access": "ALLOW",
            "role": "TEST_ROLE",
            "service": "WMS",
            "request": "GETCAPABILITIES",
            "workspace": "TEST_WORKSPACE",
        }
        assert code == 201
        content, code = r2
        assert content == {
            "id": "65",
            "priority": 11,
            "access": "ALLOW",
            "role": "TEST_ROLE",
            "service": "WMS",
            "request": "GETMAP",
            "workspace": "TEST_WORKSPACE",
        }
        assert code == 201


def test_delete_acl_admin_rule(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/acl/api/adminrules/id/a",
            status=200,
            body=b"",
        )

        content, code = geoserver.delete_acl_admin_rule("a")
        assert content == ""
        assert code == 200


def test_delete_all_acl_admin_rules(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/acl/api/adminrules",
            status=200,
            body=b"10",
        )

        content, code = geoserver.delete_all_acl_admin_rules()
        assert content == "10"
        assert code == 200


def test_delete_all_acl_rules(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/acl/api/rules",
            status=200,
            body=b"100",
        )

        content, code = geoserver.delete_all_acl_rules()
        assert content == "100"
        assert code == 200
