import json

from geoservercloud import GeoServerCloud


def test_installed_fonts(config: dict, geoserver: GeoServerCloud):
    """Verify that custom fonts are installed in GeoServer."""

    response = geoserver.rest_service.rest_client.get(
        "/rest/fonts",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200

    data = json.loads(response.content.decode("utf-8"))
    fonts = data.get("fonts", [])

    for font in config["expected_fonts"]:
        assert font in fonts, f"Expected font '{font}' not found in installed fonts"
