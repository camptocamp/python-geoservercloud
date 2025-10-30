import json
from typing import Any

from geoservercloud.models.abstractlayer import AbstractLayer
from geoservercloud.models.common import (
    EntityModel,
    MetadataLink,
)


class FeatureType(AbstractLayer):
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
        keywords: list[str] | None = None,
        native_bounding_box: dict[str, Any] | None = None,
        lat_lon_bounding_box: dict[str, Any] | None = None,
        attributes: list[dict[str, Any]] | None = None,
        projection_policy: str | None = None,
        enabled: bool | None = None,
        epsg_code: int | None = None,
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
    ) -> None:
        super().__init__(
            name=name,
            native_name=native_name,
            workspace_name=workspace_name,
            store_name=store_name,
            srs=srs,
            namespace_name=namespace_name,
            title=title,
            abstract=abstract,
            keywords=keywords,
            native_bounding_box=native_bounding_box,
            lat_lon_bounding_box=lat_lon_bounding_box,
            projection_policy=projection_policy,
            enabled=enabled,
            epsg_code=epsg_code,
            service_configuration=service_configuration,
        )
        self.attributes: list[dict[str, Any]] | None = attributes
        self.advertised: bool | None = advertised
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

    @classmethod
    def from_get_response_payload(cls, content: dict):
        feature_type = content["featureType"]
        workspace_name = feature_type["store"]["name"].split(":")[0]
        store_name = feature_type["store"]["name"].split(":")[1]
        title = feature_type.get("internationalTitle", feature_type.get("title"))
        abstract = feature_type.get(
            "internationalAbstract", feature_type.get("abstract")
        )
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
            attributes=feature_type["attributes"]["attribute"],
            metadata_links=metadata_links,
            enabled=feature_type["enabled"],
            circular_arc_present=feature_type["circularArcPresent"],
            overriding_service_srs=feature_type["overridingServiceSRS"],
            pad_with_zeros=feature_type["padWithZeros"],
            projection_policy=feature_type["projectionPolicy"],
            service_configuration=feature_type["serviceConfiguration"],
            advertised=feature_type.get("advertised"),
            native_bounding_box=feature_type.get("nativeBoundingBox"),
            lat_lon_bounding_box=feature_type.get("latLonBoundingBox"),
            keywords=feature_type.get("keywords", {}).get("string", []),
            encode_measures=feature_type.get("encodeMeasures"),
            forced_decimals=feature_type.get("forcedDecimals"),
            simple_conversion_enabled=feature_type.get("simpleConversionEnabled"),
            skip_number_match=feature_type.get("skipNumberMatch"),
        )

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = super().asdict()
        optional_items = {
            "advertised": self.advertised,
            "attributes": self.attributes,
            "serviceConfiguration": self.service_configuration,
            "simpleConversionEnabled": self.simple_conversion_enabled,
            "maxFeatures": self.max_features,
            "numDecimals": self.num_decimals,
            "padWithZeros": self.pad_with_zeros,
            "forcedDecimals": self.forced_decimals,
            "overridingServiceSRS": self.overriding_service_srs,
            "skipNumberMatch": self.skip_number_match,
            "circularArcPresent": self.circular_arc_present,
            "encodeMeasures": self.encode_measures,
        }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, Any]:
        content = self.asdict()
        if self.attributes is not None:
            content["attributes"] = {"attribute": self.attributes}
        if self.keywords is not None:
            content["keywords"] = {"string": self.keywords}
        return {"featureType": content}

    def put_payload(self) -> dict[str, Any]:
        content = self.post_payload()
        # Force a null value on non-i18ned attributes, otherwise GeoServer sets it to the first i18n value
        if content["featureType"].get("internationalTitle"):
            content["featureType"]["title"] = None
        if content["featureType"].get("internationalAbstract"):
            content["featureType"]["abstract"] = None
        return content

    def __repr__(self):
        return json.dumps(self.post_payload(), indent=4)
