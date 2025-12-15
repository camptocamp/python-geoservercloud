import responses

from geoservercloud import GeoServerCloud


def test_get_version(geoserver: GeoServerCloud) -> None:
    about = {
        "about": {
            "resource": [
                {
                    "@name": "GeoServer",
                    "Build-Timestamp": "03-Dec-2025 08:01",
                    "Version": "3.0-SNAPSHOT",
                    "Git-Revision": "60c6a60bb2a880faf17ae820a0a43a1f06a9fd5c",
                },
                {
                    "@name": "GeoTools",
                    "Build-Timestamp": "02-Dec-2025 15:11",
                    "Version": "35-SNAPSHOT",
                    "Git-Revision": "2fd68f8a0ff179d9a8406e4d6ed86b6fe15c38d6",
                },
                {
                    "@name": "GeoWebCache",
                    "Version": "2.0-SNAPSHOT",
                    "Git-Revision": "origin/main/ca0302974c89d5847de6c6f690b32e53269faaf9",
                },
            ]
        }
    }
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/about/version.json",
            status=200,
            json=about,
        )

        content, code = geoserver.get_version()

        assert content == about
        assert code == 200
