import pytest

from geoservercloud import GeoServerCloud

GEOSERVER_URL = "http://localhost:8080/geoserver"


@pytest.fixture(scope="session")
def geoserver():
    geoserver = GeoServerCloud(url=GEOSERVER_URL)
    yield geoserver
