import responses
import responses.matchers

from geoservercloud.geoservercloud import GeoServerCloud

TEST_USER = "test_user"


def test_create_user(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/rest/security/usergroup/users.json",
            status=201,
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "user": {
                            "userName": TEST_USER,
                            "password": "test_password",
                            "enabled": True,
                        }
                    }
                )
            ],
        )
        response = geoserver.create_user(TEST_USER, "test_password")
        assert response.status_code == 201


def test_update_user_password(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/rest/security/usergroup/user/{TEST_USER}.json",
            status=200,
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "user": {
                            "password": "new_password",
                        }
                    }
                )
            ],
        )
        response = geoserver.update_user(TEST_USER, password="new_password")
        assert response.status_code == 200


def test_update_user_enabled(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/rest/security/usergroup/user/{TEST_USER}.json",
            status=200,
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "user": {
                            "enabled": False,
                        }
                    }
                )
            ],
        )
        response = geoserver.update_user(TEST_USER, enabled=False)
        assert response.status_code == 200


def test_delete_user(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/rest/security/usergroup/user/{TEST_USER}.json",
            status=200,
        )
        response = geoserver.delete_user(TEST_USER)
        assert response.status_code == 200
