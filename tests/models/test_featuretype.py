import json

from geoservercloud.models import FeatureType
from geoservercloud.models.featuretype import MetadataLink


def test_featuretype_initialization():
    feature_type = FeatureType(
        namespace_name="test_namespace",
        workspace_name="test_workspace",
        store_name="test_store",
        name="test_name",
        native_name="test_native_name",
        srs="EPSG:4326",
        title="Test Title",
        abstract="Test Abstract",
        keywords=["keyword1", "keyword2"],
        attributes=[
            {
                "name": "id",
                "minOccurs": 1,
                "maxOccurs": 1,
                "nillable": False,
                "binding": "java.lang.Integer",
            },
        ],
    )

    assert feature_type.namespace_name == "test_namespace"
    assert feature_type.name == "test_name"
    assert feature_type.native_name == "test_native_name"
    assert feature_type.srs == "EPSG:4326"
    assert feature_type.title.asdict()["title"] == "Test Title"
    assert feature_type.abstract.asdict()["abstract"] == "Test Abstract"
    assert feature_type.keywords == ["keyword1", "keyword2"]
    assert feature_type.attributes == [
        {
            "name": "id",
            "minOccurs": 1,
            "maxOccurs": 1,
            "nillable": False,
            "binding": "java.lang.Integer",
        },
    ]


def test_featuretype_post_payload():
    feature_type = FeatureType(
        namespace_name="test_namespace",
        workspace_name="test_workspace",
        store_name="test_store",
        name="test_name",
        native_name="test_native_name",
        srs="EPSG:4326",
        title={"de": "Test Title"},
        abstract={"de": "Test Abstract"},
        keywords=["keyword1", "keyword2"],
        attributes=[
            {
                "name": "id",
                "minOccurs": 1,
                "maxOccurs": 1,
                "nillable": False,
                "binding": "java.lang.Integer",
            },
        ],
    )

    expected_payload = {
        "featureType": {
            "name": "test_name",
            "nativeName": "test_native_name",
            "internationalTitle": {"de": "Test Title"},
            "internationalAbstract": {"de": "Test Abstract"},
            "srs": "EPSG:4326",
            "keywords": {"string": ["keyword1", "keyword2"]},
            "attributes": {
                "attribute": [
                    {
                        "name": "id",
                        "minOccurs": 1,
                        "maxOccurs": 1,
                        "nillable": False,
                        "binding": "java.lang.Integer",
                    },
                ]
            },
            "store": {"name": "test_workspace:test_store"},
            "namespace": {"name": "test_namespace"},
        }
    }

    assert feature_type.post_payload() == expected_payload


def test_featuretype_create_metadata_link():
    feature_type = FeatureType(
        namespace_name="test_namespace",
        workspace_name="test_workspace",
        store_name="test_store",
        name="test_name",
        native_name="test_native_name",
        metadata_links=[
            MetadataLink(
                url="http://example.com/metadata.xml",
                metadata_type="TC211",
                mime_type="text/xml",
            )
        ],
    )

    expected_metadata_link = [
        {
            "type": "text/xml",
            "metadataType": "TC211",
            "content": "http://example.com/metadata.xml",
        }
    ]

    assert isinstance(feature_type.metadata_links, list)
    assert [m.asdict() for m in feature_type.metadata_links] == expected_metadata_link


def test_featuretype_from_get_response_payload():
    mock_response = {
        "featureType": {
            "namespace": {"name": "test_namespace"},
            "name": "test_name",
            "nativeName": "test_native_name",
            "store": {
                "@class": "dataStore",
                "name": "test_workspace:test_store",
                "href": "https://localhost",
            },
            "enabled": True,
            "advertised": True,
            "projectionPolicy": "FORCE_DECLARED",
            "srs": "EPSG:4326",
            "title": "Test Title",
            "abstract": "Test Abstract",
            "keywords": {"string": ["keyword1", "keyword2"]},
            "attributes": {
                "attribute": [
                    {
                        "name": "id",
                        "minOccurs": 1,
                        "maxOccurs": 1,
                        "nillable": False,
                        "binding": "java.lang.Integer",
                    },
                ]
            },
            "metadataLinks": {
                "metadataLink": [
                    {
                        "type": "text/xml",
                        "metadataType": "TC211",
                        "content": "http://example.com/metadata.xml",
                    }
                ]
            },
            "circularArcPresent": False,
            "encodeMeasures": False,
            "forcedDecimals": False,
            "overridingServiceSRS": False,
            "padWithZeros": False,
            "serviceConfiguration": False,
            "simpleConversionEnabled": False,
            "skipNumberMatch": False,
        }
    }

    feature_type = FeatureType.from_get_response_payload(mock_response)

    assert feature_type.namespace_name == "test_namespace"
    assert feature_type.name == "test_name"
    assert feature_type.native_name == "test_native_name"
    assert feature_type.store_name == "test_store"
    assert feature_type.workspace_name == "test_workspace"
    assert feature_type.srs == "EPSG:4326"
    assert feature_type.title.asdict()["title"] == "Test Title"
    assert feature_type.abstract.asdict()["abstract"] == "Test Abstract"
    assert feature_type.keywords == ["keyword1", "keyword2"]
    assert feature_type.attributes == [
        {
            "name": "id",
            "minOccurs": 1,
            "maxOccurs": 1,
            "nillable": False,
            "binding": "java.lang.Integer",
        },
    ]
    assert isinstance(feature_type.metadata_links, list)
    assert [m.asdict() for m in feature_type.metadata_links] == [
        {
            "type": "text/xml",
            "metadataType": "TC211",
            "content": "http://example.com/metadata.xml",
        }
    ]


def test_featuretype_repr():
    feature_type = FeatureType(
        namespace_name="test_namespace",
        workspace_name="test_workspace",
        store_name="test_store",
        name="test_name",
        native_name="test_native_name",
        srs="EPSG:4326",
        title="Test Title",
        abstract="Test Abstract",
        keywords=["keyword1", "keyword2"],
        attributes=[
            {
                "name": "id",
                "minOccurs": 1,
                "maxOccurs": 1,
                "nillable": False,
                "binding": "java.lang.Integer",
            },
        ],
    )

    expected_repr = json.dumps(feature_type.post_payload(), indent=4)

    assert repr(feature_type) == expected_repr
