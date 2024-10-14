import json

from requests.models import Response

from geoservercloud.models import I18N


# TODO: import more default values from Templates
class FeatureType:
    def __init__(
        self,
        namespace_name: str,
        name: str,
        native_name: str,
        srs: str = "EPSG:4326",
        title: str | dict = "New Layer",
        abstract: str | dict = "New Layer",
        keywords={},
        metadata_url=None,
        metadata_type="TC211",
        metadata_format="text/xml",
        attributes: dict | None = None,
    ) -> None:
        self._namespace_name = namespace_name
        self._name = name
        self._title = I18N(("title", "internationalTitle"), title)
        self._abstract = I18N(("abstract", "internationalAbstract"), abstract)
        self._native_name = native_name
        self._srs = srs
        self._keywords = keywords
        self._attributes = attributes
        self.create_metadata_link(metadata_url, metadata_type, metadata_format)

    @property
    def namespace_name(self):
        return self._namespace_name

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def abstract(self):
        return self._abstract

    @property
    def native_name(self):
        return self._native_name

    @property
    def srs(self):
        return self._srs

    @property
    def keywords(self):
        return self._keywords

    @property
    def metadataLink(self):
        return self._metadataLink

    @property
    def attributes(self):
        return self._attributes

    def post_payload(self):
        payload = {
            "featureType": {
                "name": self.name,
                "nativeName": self.native_name,
                self._title.payload_tuple[0]: self._title.payload_tuple[1],
                self._abstract.payload_tuple[0]: self._abstract.payload_tuple[1],
                "srs": self.srs,
                "keywords": self.keywords,
            }
        }
        if self.metadataLink != {}:
            payload["featureType"]["metadataLinks"] = self.metadataLink
        if self.attributes:
            payload["featureType"]["attributes"] = self.attributes
        return payload

    def create_metadata_link(
        self, metadata_url=None, metadata_type="TC211", metadata_format="text/xml"
    ):
        self._metadataLink = {}
        if metadata_url:
            self._metadataLink["metadataLink"] = {
                "type": metadata_format,
                "metadataType": metadata_type,
                "content": metadata_url,
            }

    @classmethod
    def from_response(cls, response: Response):
        json_data = response.json()
        try:
            abstract = json_data["featureType"]["abstract"]
        except KeyError:
            abstract = json_data["featureType"]["internationalAbstract"]
        try:
            title = json_data["featureType"]["title"]
        except KeyError:
            title = json_data["featureType"]["internationalTitle"]

        return cls(
            namespace_name=json_data["featureType"]["namespace"]["name"],
            name=json_data["featureType"]["name"],
            native_name=json_data["featureType"]["nativeName"],
            title=title,
            abstract=abstract,
            srs=json_data["featureType"]["srs"],
            keywords=json_data["featureType"]["keywords"],
            attributes=json_data["featureType"].get("attributes", None),
            metadata_url=json_data["featureType"]
            .get("metadataLinks", {})
            .get("metadataLink", {})
            .get("content"),
            metadata_type=json_data["featureType"]
            .get("metadataLinks", {})
            .get("metadataLink", {})
            .get("metadataType"),
            metadata_format=json_data["featureType"]
            .get("metadataLinks", {})
            .get("metadataLink", {})
            .get("type"),
        )

    def __repr__(self):
        return json.dumps(self.post_payload(), indent=4)
