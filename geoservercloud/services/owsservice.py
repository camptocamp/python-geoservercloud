from json import JSONDecodeError
from typing import Any

import xmltodict
from owslib.map.wms130 import WebMapService_1_3_0
from owslib.wmts import WebMapTileService
from requests import Response

from geoservercloud.services.restclient import RestClient


class OwsService:
    def __init__(self, url: str, auth: tuple[str, str], verifytls: bool = True) -> None:
        self.url: str = url
        self.auth: tuple[str, str] = auth
        self.ows_endpoints = self.OwsEndpoints()
        self.rest_client = RestClient(url, auth, verifytls)

    def create_wms(self, workspace_name: str | None = None) -> WebMapService_1_3_0:
        if workspace_name is None:
            return WebMapService_1_3_0(
                f"{self.url}{self.ows_endpoints.wms()}",
                username=self.auth[0],
                password=self.auth[1],
            )
        return WebMapService_1_3_0(
            f"{self.url}{self.ows_endpoints.workspace_wms(workspace_name)}",
            username=self.auth[0],
            password=self.auth[1],
        )

    def create_wmts(self) -> WebMapTileService:
        return WebMapTileService(
            f"{self.url}{self.ows_endpoints.wmts()}",
            version="1.0.0",
            username=self.auth[0],
            password=self.auth[1],
        )

    def get_wms_capabilities(
        self, workspace_name: str, accept_languages: str | None = None
    ) -> dict[str, Any]:
        path: str = self.ows_endpoints.workspace_wms(workspace_name)
        params: dict[str, str] = {
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetCapabilities",
        }
        if accept_languages:
            params["AcceptLanguages"] = accept_languages
        response: Response = self.rest_client.get(path, params=params)
        return xmltodict.parse(response.content)

    def get_wms_layers(
        self, workspace_name: str, accept_languages: str | None = None
    ) -> Any | dict[str, Any]:

        capabilities: dict[str, Any] = self.get_wms_capabilities(
            workspace_name, accept_languages
        )
        try:
            return capabilities["WMS_Capabilities"]["Capability"]["Layer"]
        except KeyError:
            return capabilities

    def get_legend_graphic(
        self,
        layer: list[str],
        format: str = "image/png",
        language: str | None = None,
        style: str | None = None,
        workspace_name: str | None = None,
    ) -> Response:
        """
        WMS GetLegendGraphic request
        """
        path: str
        if not workspace_name:
            path = self.ows_endpoints.wms()
        else:
            path = self.ows_endpoints.workspace_wms(workspace_name)
        params: dict[str, Any] = {
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetLegendGraphic",
            "format": format,
            "layer": layer,
        }
        if language:
            params["language"] = language
        if style:
            params["style"] = style
        return self.rest_client.get(path, params=params)

    def get_wfs_capabilities(self, workspace_name: str) -> dict[str, Any]:
        params: dict[str, str] = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetCapabilities",
        }
        response: Response = self.rest_client.get(
            self.ows_endpoints.workspace_wfs(workspace_name), params=params
        )
        return xmltodict.parse(response.content)

    def get_wfs_layers(self, workspace_name: str) -> Any | dict[str, Any]:
        capabilities: dict[str, Any] = self.get_wfs_capabilities(workspace_name)
        try:
            return capabilities["wfs:WFS_Capabilities"]["FeatureTypeList"]
        except KeyError:
            return capabilities

    def get_feature(
        self,
        workspace_name: str,
        type_name: str,
        feature_id: int | None = None,
        max_feature: int | None = None,
        format: str = "application/json",
    ) -> dict[str, Any] | str:
        path = self.ows_endpoints.workspace_wfs(workspace_name)
        params = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typeName": type_name,
            "outputFormat": format,
        }
        if feature_id:
            params["featureID"] = str(feature_id)
        if max_feature:
            params["maxFeatures"] = str(max_feature)
        response = self.rest_client.get(path, params=params)
        try:
            return response.json()
        except JSONDecodeError:
            return response.content.decode()

    def describe_feature_type(
        self,
        workspace_name: str | None = None,
        type_name: str | None = None,
        format: str = "application/json",
    ) -> dict[str, Any] | str:
        if not workspace_name:
            path = self.ows_endpoints.wfs()
        else:
            path = self.ows_endpoints.workspace_wfs(workspace_name)
        params = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "DescribeFeatureType",
            "outputFormat": format,
        }
        if type_name:
            params["typeName"] = type_name
        response = self.rest_client.get(path, params=params)
        try:
            return response.json()
        except JSONDecodeError:
            return response.content.decode()

    def get_property_value(
        self,
        workspace_name: str,
        type_name: str,
        property: str,
    ) -> dict | list | str:
        path = self.ows_endpoints.workspace_wfs(workspace_name)
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetPropertyValue",
            "typeNames": type_name,
            "valueReference": property,
        }
        response = self.rest_client.get(path, params=params)
        value_collection = xmltodict.parse(response.content).get("wfs:ValueCollection")
        if not value_collection:
            return response.content.decode()
        else:
            return value_collection.get("wfs:member", {})

    class OwsEndpoints:
        def __init__(self, base_url: str = "") -> None:
            self.base_url: str = base_url

        def ows(self) -> str:
            return f"{self.base_url}/ows"

        def wms(self) -> str:
            return f"{self.base_url}/wms"

        def wfs(self) -> str:
            return f"{self.base_url}/wfs"

        def wcs(self) -> str:
            return f"{self.base_url}/wcs"

        def wmts(self) -> str:
            return f"{self.base_url}/gwc/service/wmts"

        def workspace_ows(self, workspace_name: str) -> str:
            return f"{self.base_url}/{workspace_name}/ows"

        def workspace_wms(self, workspace_name: str) -> str:
            return f"{self.base_url}/{workspace_name}/wms"

        def workspace_wfs(self, workspace_name: str) -> str:
            return f"{self.base_url}/{workspace_name}/wfs"

        def workspace_wcs(self, workspace_name: str) -> str:
            return f"{self.base_url}/{workspace_name}/wcs"
