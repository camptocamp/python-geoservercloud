import json

from geoservercloud.models import FeatureTypes  # Replace with the correct module path


def test_featuretypes_initialization():
    featuretypes = ["feature1", "feature2"]
    feature_types_instance = FeatureTypes(featuretypes)

    assert feature_types_instance.featuretypes == featuretypes


def test_featuretypes_from_dict_valid():
    mock_response = {
        "featureTypes": {"featureType": [{"name": "feature1"}, {"name": "feature2"}]}
    }

    feature_types_instance = FeatureTypes.from_dict(mock_response)

    assert feature_types_instance.featuretypes == ["feature1", "feature2"]


def test_featuretypes_repr():
    featuretypes = ["feature1", "feature2"]
    feature_types_instance = FeatureTypes(featuretypes)

    expected_repr = json.dumps(featuretypes, indent=4)

    assert repr(feature_types_instance) == expected_repr
