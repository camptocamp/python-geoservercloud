import json
from typing import Any

import xmltodict

from geoservercloud.models.common import EntityModel, ReferencedObjectModel


class Style(EntityModel):
    def __init__(
        self,
        name: str,
        workspace_name: str | None = None,
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
        self._workspace: ReferencedObjectModel | None = None
        if workspace_name:
            self._workspace = ReferencedObjectModel(workspace_name)
        self._name = name
        self._format = format
        self._language_version = language_version
        self._filename = filename
        self._date_created = date_created
        self._date_modified = date_modified
        self._legend = self.create_legend(
            legend_url, legend_format, legend_width, legend_height
        )

    @property
    def workspace_name(self) -> str | None:
        return self._workspace.name if self._workspace else None

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
    ) -> dict[str, str | int] | None:
        legend: dict[str, str | int] = {}
        if any([url, image_format, width, height]):
            if url:
                legend["onlineResource"] = url
            if image_format:
                legend["format"] = image_format
            if width:
                legend["width"] = width
            if height:
                legend["height"] = height
        else:
            return None
        return legend

    def asdict(self) -> dict[str, Any]:
        content = {
            "name": self.name,
            "format": self.format,
            "languageVersion": self.language_version,
        }
        optional_items = {
            "workspace": self.workspace_name,
            "filename": self.filename,
            "dateCreated": self.date_created,
            "dateModified": self.date_modified,
            "legend": self.legend,
        }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, dict[str, Any]]:
        content = self.asdict()
        if self._workspace:
            content["workspace"] = self._workspace.asdict()
        return {"style": content}

    def put_payload(self) -> dict[str, dict[str, Any]]:
        return self.post_payload()

    @classmethod
    def from_get_response_payload(cls, content: dict):
        style_data = content["style"]
        return cls(
            name=style_data["name"],
            workspace_name=style_data.get("workspace", {}).get("name"),
            format=style_data["format"],
            language_version=style_data["languageVersion"],
            filename=style_data["filename"],
            date_created=style_data.get("dateCreated"),
            date_modified=style_data.get("dateModified"),
            legend_url=style_data.get("legend", {}).get("onlineResource"),
            legend_format=style_data.get("legend", {}).get("format"),
            legend_width=style_data.get("legend", {}).get("width"),
            legend_height=style_data.get("legend", {}).get("height"),
        )

    def xml_post_payload(self) -> str:
        return xmltodict.unparse(self.post_payload()).split("\n", 1)[1]

    def xml_put_payload(self) -> str:
        return xmltodict.unparse(self.put_payload()).split("\n", 1)[1]

    def __repr__(self) -> str:
        return json.dumps(self.put_payload(), indent=4)
