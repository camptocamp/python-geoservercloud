from geoservercloud import GeoServerCloud


def test_get_version(geoserver: GeoServerCloud):
    content, status = geoserver.get_version()

    assert status == 200
    assert isinstance(content, dict)
    assert "about" in content
    assert "resource" in content["about"]
    assert isinstance(content["about"]["resource"], list)
