import json
from typing import Any

from geoservercloud.models import I18N, EntityModel, ReferencedObjectModel
from geoservercloud.utils import EPSG_BBOX


class MetadataLink:
    def __init__(self, url: str, metadata_type="TC211", mime_type: str = "text/xml"):
        self.url: str = url
        self.metadata_type: str = metadata_type
        self.type: str = mime_type

    @classmethod
    def from_get_response_payload(cls, content: dict):
        return cls(
            url=content["content"],
            metadata_type=content["metadataType"],
            mime_type=content["type"],
        )

    def asdict(self) -> dict[str, str]:
        return {
            "content": self.url,
            "metadataType": self.metadata_type,
            "type": self.type,
        }


class FeatureType(EntityModel):

    def __init__(
        self,
        # Mandatory fields
        name: str,
        native_name: str,
        workspace_name: str,
        store_name: str,
        # Nullable fields
        srs: str | None = None,
        namespace_name: str | None = None,
        title: dict[str, str] | str | None = None,
        abstract: dict[str, str] | str | None = None,
        keywords: list[str] | None = [],
        native_bounding_box: dict[str, Any] | None = None,
        lat_lon_bounding_box: dict[str, Any] | None = None,
        attributes: list[dict[str, Any]] | None = None,
        projection_policy: str | None = None,
        enabled: bool | None = None,
        advertised: bool | None = None,
        service_configuration: bool | None = None,
        simple_conversion_enabled: bool | None = None,
        max_features: int | None = None,
        num_decimals: int | None = None,
        pad_with_zeros: bool | None = None,
        forced_decimals: bool | None = None,
        overriding_service_srs: bool | None = None,
        skip_number_match: bool | None = None,
        circular_arc_present: bool | None = None,
        encode_measures: bool | None = None,
        metadata_links: list[MetadataLink] | None = None,
        epsg_code: int | None = None,
    ) -> None:
        self.name: str = name
        self.native_name: str = native_name
        self.srs: str | None = srs
        self.workspace_name: str = workspace_name
        self.store = ReferencedObjectModel(f"{workspace_name}:{store_name}")
        self.namespace: ReferencedObjectModel | None = (
            ReferencedObjectModel(namespace_name) if namespace_name else None
        )
        self.title: I18N | None = (
            I18N(("title", "internationalTitle"), title) if title else None
        )
        self.abstract: I18N | None = (
            I18N(("abstract", "internationalAbstract"), abstract) if abstract else None
        )
        self.keywords: list[str] | None = keywords
        self.native_bounding_box: dict[str, Any] | None = native_bounding_box
        self.lat_lon_bounding_box: dict[str, Any] | None = lat_lon_bounding_box
        self.attributes: list[dict[str, Any]] | None = attributes
        self.projection_policy: str | None = projection_policy
        self.enabled: bool | None = enabled
        self.advertised: bool | None = advertised
        self.service_configuration: bool | None = service_configuration
        self.simple_conversion_enabled: bool | None = simple_conversion_enabled
        self.max_features: int | None = max_features
        self.num_decimals: int | None = num_decimals
        self.pad_with_zeros: bool | None = pad_with_zeros
        self.forced_decimals: bool | None = forced_decimals
        self.overriding_service_srs: bool | None = overriding_service_srs
        self.skip_number_match: bool | None = skip_number_match
        self.circular_arc_present: bool | None = circular_arc_present
        self.encode_measures: bool | None = encode_measures
        self.metadata_links: list[MetadataLink] | None = metadata_links
        self.epsg_code: int | None = epsg_code

    @property
    def store_name(self) -> str:
        return self.store.name.split(":")[1]

    @property
    def namespace_name(self) -> str | None:
        return self.namespace.name if self.namespace else None

    @classmethod
    def from_get_response_payload(cls, content: dict):
        feature_type = content["featureType"]
        workspace_name = feature_type["store"]["name"].split(":")[0]
        store_name = feature_type["store"]["name"].split(":")[1]
        try:
            abstract = feature_type["abstract"]
        except KeyError:
            abstract = feature_type["internationalAbstract"]
        try:
            title = feature_type["title"]
        except KeyError:
            title = feature_type["internationalTitle"]
        if feature_type.get("metadataLinks"):
            metadata_links_payload = feature_type["metadataLinks"]["metadataLink"]
            metadata_links = [
                MetadataLink.from_get_response_payload(metadata_link)
                for metadata_link in metadata_links_payload
            ]
        else:
            metadata_links = None

        return cls(
            namespace_name=feature_type["namespace"]["name"],
            name=feature_type["name"],
            native_name=feature_type["nativeName"],
            workspace_name=workspace_name,
            store_name=store_name,
            title=title,
            abstract=abstract,
            srs=feature_type["srs"],
            keywords=feature_type["keywords"]["string"],
            attributes=feature_type["attributes"]["attribute"],
            metadata_links=metadata_links,
            enabled=feature_type["enabled"],
            circular_arc_present=feature_type["circularArcPresent"],
            overriding_service_srs=feature_type["overridingServiceSRS"],
            pad_with_zeros=feature_type["padWithZeros"],
            projection_policy=feature_type["projectionPolicy"],
            service_configuration=feature_type["serviceConfiguration"],
            advertised=feature_type.get("advertised"),
            encode_measures=feature_type.get("encodeMeasures"),
            forced_decimals=feature_type.get("forcedDecimals"),
            simple_conversion_enabled=feature_type.get("simpleConversionEnabled"),
            skip_number_match=feature_type.get("skipNumberMatch"),
        )

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = {
            "name": self.name,
            "nativeName": self.native_name,
            "store": self.store.asdict(),
        }
        if self.namespace is not None:
            content["namespace"] = self.namespace.asdict()
        if self.srs:
            content["srs"] = self.srs
        if self.title:
            content.update(self.title.asdict())
        if self.abstract:
            content.update(self.abstract.asdict())
        if self.keywords:
            content["keywords"] = self.keywords
        if self.native_bounding_box:
            content["nativeBoundingBox"] = self.native_bounding_box
        elif self.epsg_code:
            content["nativeBoundingBox"] = EPSG_BBOX[self.epsg_code][
                "nativeBoundingBox"
            ]
        if self.lat_lon_bounding_box:
            content["latLonBoundingBox"] = self.lat_lon_bounding_box
        elif self.epsg_code:
            content["latLonBoundingBox"] = EPSG_BBOX[self.epsg_code][
                "latLonBoundingBox"
            ]
        if self.attributes:
            content["attributes"] = self.attributes
        if self.projection_policy is not None:
            content["projectionPolicy"] = self.projection_policy
        if self.enabled is not None:
            content["enabled"] = self.enabled
        if self.advertised is not None:
            content["advertised"] = self.advertised
        if self.service_configuration is not None:
            content["serviceConfiguration"] = self.service_configuration
        if self.simple_conversion_enabled is not None:
            content["simpleConversionEnabled"] = self.simple_conversion_enabled
        if self.max_features is not None:
            content["maxFeatures"] = self.max_features
        if self.num_decimals is not None:
            content["numDecimals"] = self.num_decimals
        if self.pad_with_zeros is not None:
            content["padWithZeros"] = self.pad_with_zeros
        if self.forced_decimals is not None:
            content["forcedDecimals"] = self.forced_decimals
        if self.overriding_service_srs is not None:
            content["overridingServiceSRS"] = self.overriding_service_srs
        if self.skip_number_match is not None:
            content["skipNumberMatch"] = self.skip_number_match
        if self.circular_arc_present is not None:
            content["circularArcPresent"] = self.circular_arc_present
        if self.encode_measures is not None:
            content["encodeMeasures"] = self.encode_measures
        return content

    def post_payload(self) -> dict[str, Any]:
        content = self.asdict()
        content["attributes"] = {"attribute": self.attributes}
        content["keywords"] = {"string": self.keywords}
        return {"featureType": content}

    def put_payload(self) -> dict[str, Any]:
        return self.post_payload()

    def __repr__(self):
        return json.dumps(self.post_payload(), indent=4)
