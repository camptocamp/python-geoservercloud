import responses

from geoservercloud import GeoServerCloud


def test_create_resource(geoserver: GeoServerCloud) -> None:
    path = "/new/resource"
    resource_path = "/new/resource/resource.json"
    payload = {"something": "new"}
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}{resource_path}",
            status=404,
        )
        rsps.post(
            url=f"{geoserver.url}{path}",
            status=201,
            match=[responses.matchers.json_params_matcher(payload)],
        )

        response = geoserver.create_or_update_resource(path, resource_path, payload)

        assert response.status_code == 201


def test_update_resource(geoserver: GeoServerCloud) -> None:
    path = "/some/resource"
    resource_path = "/some/resource/resource.json"
    payload = {"something": "something"}
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}{resource_path}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}{resource_path}",
            status=200,
            match=[responses.matchers.json_params_matcher(payload)],
        )

        response = geoserver.create_or_update_resource(path, resource_path, payload)

        assert response.status_code == 200
