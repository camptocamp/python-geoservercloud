import json

import xmltodict
from requests.models import Response


class Style:

    def __init__(
        self,
        name: str,
        workspace: str | None = None,
        format: str | None = "sld",
        language_version: dict | None = {"version": "1.0.0"},
        filename: str | None = None,
        date_created: str | None = None,
        date_modified: str | None = None,
        legend_url: str | None = None,
        legend_format: str | None = None,
        legend_width: int | None = None,
        legend_height: int | None = None,
    ) -> None:
        self._workspace = workspace
        self._name = name
        self._format = format
        self._language_version = language_version
        self._filename = filename
        self._date_created = date_created
        self._date_modified = date_modified
        self._legend = self.create_legend(
            legend_url, legend_format, legend_width, legend_height
        )

    # create one property for each attribute
    @property
    def workspace(self):
        return self._workspace

    @property
    def name(self):
        return self._name

    @property
    def format(self):
        return self._format

    @property
    def language_version(self):
        return self._language_version

    @property
    def filename(self):
        return self._filename

    @property
    def date_created(self):
        return self._date_created

    @property
    def date_modified(self):
        return self._date_modified

    @property
    def legend(self):
        return self._legend

    def create_legend(
        self,
        url: str | None,
        image_format: str | None,
        width: int | None,
        height: int | None,
    ):
        if any([url, image_format, width, height]):
            legend: dict = {}
            if url:
                legend["onlineResource"] = url
            if image_format:
                legend["format"] = image_format
            if width:
                legend["width"] = width
            if height:
                legend["height"] = height
        else:
            legend = None  # type: ignore
        return legend

    def put_payload(self):
        payload = {
            "style": {
                "name": self.name,
                "format": self.format,
                "languageVersion": self.language_version,
                "filename": self.filename,
            }
        }
        if self.legend:
            payload["style"]["legend"] = self.legend
        return payload

    def post_payload(self):
        return self.put_payload()

    @classmethod
    def from_response(cls, response: Response):
        json_data = response.json()
        style_data = json_data.get("style", {})
        return cls(
            workspace=style_data.get("workspace"),
            name=style_data.get("name"),
            format=style_data.get("format"),
            language_version=style_data.get("languageVersion", None),
            filename=style_data.get("filename"),
            date_created=style_data.get("dateCreated"),
            date_modified=style_data.get("dateModified"),
            legend_url=style_data.get("legend", {}).get("onlineResource"),
            legend_format=style_data.get("legend", {}).get("format"),
            legend_width=style_data.get("legend", {}).get("width"),
            legend_height=style_data.get("legend", {}).get("height"),
        )

    def xml_post_payload(self):
        return xmltodict.unparse(self.post_payload()).split("\n", 1)[1]

    def xml_put_payload(self):
        return xmltodict.unparse(self.put_payload()).split("\n", 1)[1]

    def __repr__(self):
        return json.dumps(self.put_payload(), indent=4)
