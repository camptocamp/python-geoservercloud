import json
from unittest.mock import Mock

import pytest

from geoservercloud.models import FeatureTypes  # Replace with the correct module path


# Test initialization of FeatureTypes class
def test_featuretypes_initialization():
    featuretypes = ["feature1", "feature2"]
    feature_types_instance = FeatureTypes(featuretypes)

    assert feature_types_instance.featuretypes == featuretypes


# Test from_response method with a valid response
def test_featuretypes_from_response_valid():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "featureTypes": {"featureType": [{"name": "feature1"}, {"name": "feature2"}]}
    }

    feature_types_instance = FeatureTypes.from_response(mock_response)

    assert feature_types_instance.featuretypes == ["feature1", "feature2"]


# Test __repr__ method
def test_featuretypes_repr():
    featuretypes = ["feature1", "feature2"]
    feature_types_instance = FeatureTypes(featuretypes)

    expected_repr = json.dumps(featuretypes, indent=4)

    assert repr(feature_types_instance) == expected_repr
