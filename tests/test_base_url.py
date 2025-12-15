import responses

from geoservercloud import GeoServerCloud


def test_base_url():
    geoserver_no_trailing_slash = GeoServerCloud(url="http://localhost:8080/geoserver")
    geoserver_with_trailing_slash = GeoServerCloud(
        url="http://localhost:8080/geoserver/"
    )

    assert geoserver_no_trailing_slash.url == "http://localhost:8080/geoserver"
    assert geoserver_with_trailing_slash.url == "http://localhost:8080/geoserver"

    with responses.RequestsMock() as rsps:
        rsps.get(
            url="http://localhost:8080/geoserver/rest/about/version.json",
            status=200,
            json={"about": {"resource": [{"@name": "GeoServer"}]}},
        )

        response_no_slash = geoserver_no_trailing_slash.get_version()
        response_with_slash = geoserver_with_trailing_slash.get_version()

        assert response_no_slash == response_with_slash
