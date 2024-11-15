import pytest

from geoservercloud.models.wmssettings import WmsSettings


@pytest.fixture
def mock_wms_settings():
    return {
        "autoEscapeTemplateValues": False,
        "bboxForEachCRS": False,
        "cacheConfiguration": {
            "enabled": False,
            "maxEntries": 1000,
            "maxEntrySize": 51200,
        },
        "citeCompliant": False,
        "defaultGroupStyleEnabled": True,
        "dynamicStylingDisabled": False,
        "enabled": True,
        "featuresReprojectionDisabled": False,
        "getFeatureInfoMimeTypeCheckingEnabled": False,
        "getMapMimeTypeCheckingEnabled": False,
        "interpolation": "Nearest",
        "maxBuffer": 0,
        "maxRenderingErrors": 0,
        "maxRenderingTime": 0,
        "maxRequestMemory": 0,
        "maxRequestedDimensionValues": 100,
        "name": "WMS",
        "remoteStyleMaxRequestTime": 60000,
        "remoteStyleTimeout": 30000,
        "schemaBaseURL": "http://schemas.opengis.net",
        "transformFeatureInfoDisabled": False,
        "verbose": False,
        "versions": {
            "org.geotools.util.Version": [
                {"version": "1.1.1"},
                {"version": "1.3.0"},
            ]
        },
        "watermark": {
            "enabled": False,
            "position": "BOT_RIGHT",
            "transparency": 100,
        },
        "workspace": {"name": "test_workspace"},
    }


def test_wms_settings_initialization():
    wms_settings = WmsSettings(workspace_name="test_workspace")
    assert wms_settings.asdict() == {"workspace": "test_workspace"}
    assert wms_settings.post_payload() == {
        "wms": {"workspace": {"name": "test_workspace"}}
    }
    assert wms_settings.put_payload() == {
        "wms": {"workspace": {"name": "test_workspace"}}
    }


def test_wms_settings(mock_wms_settings):
    wms_settings = WmsSettings.from_get_response_payload({"wms": mock_wms_settings})
    assert wms_settings.post_payload().get("wms") == mock_wms_settings
    assert wms_settings.put_payload().get("wms") == mock_wms_settings
