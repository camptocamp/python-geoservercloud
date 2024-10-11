import json

from geoservercloud.models import FeatureType


def test_featuretype_initialization():
    feature_type = FeatureType(
        namespace_name="test_namespace",
        name="test_name",
        native_name="test_native_name",
        srs="EPSG:4326",
        title="Test Title",
        abstract="Test Abstract",
        keywords={"keyword1": "test_keyword"},
        attributes={"attribute1": "value1"},
    )

    assert feature_type.namespace_name == "test_namespace"
    assert feature_type.name == "test_name"
    assert feature_type.native_name == "test_native_name"
    assert feature_type.srs == "EPSG:4326"
    assert feature_type.title.asdict()["title"] == "Test Title"
    assert feature_type.abstract.asdict()["abstract"] == "Test Abstract"
    assert feature_type.keywords == {"keyword1": "test_keyword"}
    assert feature_type.attributes == {"attribute1": "value1"}


def test_featuretype_post_payload():
    feature_type = FeatureType(
        namespace_name="test_namespace",
        name="test_name",
        native_name="test_native_name",
        srs="EPSG:4326",
        title={"de": "Test Title"},
        abstract={"de": "Test Abstract"},
        keywords={"keyword1": "test_keyword"},
        attributes={"attribute1": "value1"},
    )

    expected_payload = {
        "featureType": {
            "name": "test_name",
            "nativeName": "test_native_name",
            "internationalTitle": {"de": "Test Title"},
            "internationalAbstract": {"de": "Test Abstract"},
            "srs": "EPSG:4326",
            "keywords": {"keyword1": "test_keyword"},
            "attributes": {"attribute1": "value1"},
        }
    }

    assert feature_type.post_payload() == expected_payload


def test_featuretype_create_metadata_link():
    feature_type = FeatureType(
        namespace_name="test_namespace",
        name="test_name",
        native_name="test_native_name",
        metadata_url="http://example.com/metadata.xml",
        metadata_type="TC211",
        metadata_format="text/xml",
    )

    expected_metadata_link = {
        "metadataLink": {
            "type": "text/xml",
            "metadataType": "TC211",
            "content": "http://example.com/metadata.xml",
        }
    }

    assert feature_type.metadataLink == expected_metadata_link


def test_featuretype_from_dict():
    mock_response = {
        "featureType": {
            "namespace": {"name": "test_namespace"},
            "name": "test_name",
            "nativeName": "test_native_name",
            "srs": "EPSG:4326",
            "title": "Test Title",
            "abstract": "Test Abstract",
            "keywords": {"keyword1": "test_keyword"},
            "attributes": {"attribute1": "value1"},
            "metadataLinks": {
                "metadataLink": {
                    "type": "text/xml",
                    "metadataType": "TC211",
                    "content": "http://example.com/metadata.xml",
                }
            },
        }
    }

    feature_type = FeatureType.from_dict(mock_response)

    assert feature_type.namespace_name == "test_namespace"
    assert feature_type.name == "test_name"
    assert feature_type.native_name == "test_native_name"
    assert feature_type.srs == "EPSG:4326"
    assert feature_type.title.asdict()["title"] == "Test Title"
    assert feature_type.abstract.asdict()["abstract"] == "Test Abstract"
    assert feature_type.keywords == {"keyword1": "test_keyword"}
    assert feature_type.attributes == {"attribute1": "value1"}
    assert feature_type.metadataLink == {
        "metadataLink": {
            "type": "text/xml",
            "metadataType": "TC211",
            "content": "http://example.com/metadata.xml",
        }
    }


def test_featuretype_repr():
    feature_type = FeatureType(
        namespace_name="test_namespace",
        name="test_name",
        native_name="test_native_name",
        srs="EPSG:4326",
        title="Test Title",
        abstract="Test Abstract",
        keywords={"keyword1": "test_keyword"},
        attributes={"attribute1": "value1"},
    )

    expected_repr = json.dumps(feature_type.post_payload(), indent=4)

    assert repr(feature_type) == expected_repr
