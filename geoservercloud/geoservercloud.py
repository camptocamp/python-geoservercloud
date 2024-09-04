import os.path
from pathlib import Path
from typing import Any

import xmltodict
from owslib.map.wms130 import WebMapService_1_3_0
from owslib.util import ResponseWrapper
from owslib.wmts import WebMapTileService
from requests import Response

from geoservercloud import utils
from geoservercloud.restservice import RestService
from geoservercloud.templates import Templates


class GeoServerCloud:
    def __init__(
        self,
        url: str = "http://localhost:9090/geoserver/cloud/",
        user: str = "admin",
        password: str = "geoserver",
    ) -> None:

        self.url: str = url
        self.user: str = user
        self.password: str = password
        self.auth: tuple[str, str] = (user, password)
        self.rest_service: RestService = RestService(url, self.auth)
        self.wms: WebMapService_1_3_0 | None = None
        self.wmts: WebMapTileService | None = None
        self.default_workspace: str | None = None
        self.default_datastore: str | None = None

    @staticmethod
    def workspace_wms_settings_path(workspace: str) -> str:
        return f"/rest/services/wms/workspaces/{workspace}/settings.json"

    @staticmethod
    def get_wmts_layer_bbox(
        url: str, layer_name: str
    ) -> tuple[float, float, float, float] | None:
        wmts = WebMapTileService(url)
        try:
            return wmts[layer_name].boundingBoxWGS84
        except (KeyError, AttributeError):
            return None

    def create_wms(self) -> None:
        if self.default_workspace:
            path: str = f"/{self.default_workspace}/wms"
        else:
            path = "/wms"
        self.wms = WebMapService_1_3_0(
            f"{self.url}{path}",
            username=self.user,
            password=self.password,
            timeout=240,
        )

    def create_wmts(self) -> None:
        path = "/gwc/service/wmts"
        self.wmts = WebMapTileService(
            f"{self.url}{path}",
            version="1.0.0",
            username=self.user,
            password=self.password,
        )

    def create_workspace(
        self,
        workspace: str,
        isolated: bool = False,
        set_default_workspace: bool = False,
    ) -> Response:
        """
        Create a workspace in GeoServer, if it does not already exist.
        It if exists, update it
        """
        payload: dict[str, dict[str, Any]] = {
            "workspace": {
                "name": workspace,
                "isolated": isolated,
            }
        }
        response: Response = self.post_request("/rest/workspaces.json", json=payload)
        if response.status_code == 409:
            response = self.put_request(
                f"/rest/workspaces/{workspace}.json", json=payload
            )
        if set_default_workspace:
            self.default_workspace = workspace
        return response

    def delete_workspace(self, workspace: str) -> Response:
        path: str = f"/rest/workspaces/{workspace}.json?recurse=true"
        response: Response = self.delete_request(path)
        if self.default_workspace == workspace:
            self.default_workspace = None
            self.wms = None
            self.wmts = None
        return response

    def recreate_workspace(
        self, workspace: str, set_default_workspace: bool = False
    ) -> Response:
        """
        Create a workspace in GeoServer, and first delete it if it already exists.
        """
        self.delete_workspace(workspace)
        return self.create_workspace(
            workspace, set_default_workspace=set_default_workspace
        )

    def publish_workspace(self, workspace) -> Response:
        path: str = f"{self.workspace_wms_settings_path(workspace)}"

        data: dict[str, dict[str, Any]] = Templates.workspace_wms(workspace)
        return self.put_request(path, json=data)

    def set_default_locale_for_service(
        self, workspace: str, locale: str | None
    ) -> None:
        path: str = self.workspace_wms_settings_path(workspace)
        data: dict[str, dict[str, Any]] = {
            "wms": {
                "defaultLocale": locale,
            }
        }
        self.put_request(path, json=data)

    def unset_default_locale_for_service(self, workspace) -> None:
        self.set_default_locale_for_service(workspace, None)

    def create_pg_datastore(
        self,
        workspace: str,
        datastore: str,
        pg_host: str,
        pg_port: int,
        pg_db: str,
        pg_user: str,
        pg_password: str,
        pg_schema: str = "public",
        set_default_datastore: bool = False,
    ) -> Response | None:
        """
        Create a PostGIS datastore from the DB connection parameters, or update it if it already exist.
        """
        response: None | Response = None
        path = f"/rest/workspaces/{workspace}/datastores.json"
        resource_path = f"/rest/workspaces/{workspace}/datastores/{datastore}.json"
        payload: dict[str, dict[str, Any]] = Templates.postgis_data_store(
            datastore=datastore,
            pg_host=pg_host,
            pg_port=pg_port,
            pg_db=pg_db,
            pg_user=pg_user,
            pg_password=pg_password,
            namespace=f"http://{workspace}",
            pg_schema=pg_schema,
        )
        if not self.resource_exists(resource_path):
            response = self.post_request(path, json=payload)
        else:
            response = self.put_request(resource_path, json=payload)

        if set_default_datastore:
            self.default_datastore = datastore

        return response

    def create_jndi_datastore(
        self,
        workspace: str,
        datastore: str,
        jndi_reference: str,
        pg_schema: str = "public",
        description: str | None = None,
        set_default_datastore: bool = False,
    ) -> Response | None:
        """
        Create a PostGIS datastore from JNDI resource, or update it if it already exist.
        """
        response: None | Response = None
        path = f"/rest/workspaces/{workspace}/datastores.json"
        resource_path = f"/rest/workspaces/{workspace}/datastores/{datastore}.json"
        payload: dict[str, dict[str, Any]] = Templates.postgis_jndi_data_store(
            datastore=datastore,
            jndi_reference=jndi_reference,
            namespace=f"http://{workspace}",
            pg_schema=pg_schema,
            description=description,
        )
        if not self.resource_exists(resource_path):
            response = self.post_request(path, json=payload)
        else:
            response = self.put_request(resource_path, json=payload)

        if set_default_datastore:
            self.default_datastore = datastore

        return response

    def create_wmts_store(
        self,
        workspace: str,
        name: str,
        capabilities: str,
    ) -> Response:
        """
        Create a cascaded WMTS store, or update it if it already exist.
        """
        path = f"/rest/workspaces/{workspace}/wmtsstores.json"
        resource_path = f"/rest/workspaces/{workspace}/wmtsstores/{name}.json"
        payload = Templates.wmts_store(workspace, name, capabilities)
        if not self.resource_exists(resource_path):
            return self.post_request(path, json=payload)
        else:
            return self.put_request(resource_path, json=payload)

    def create_feature_type(
        self,
        layer: str,
        workspace: str | None = None,
        datastore: str | None = None,
        title: str | dict = "Default title",
        abstract: str | dict = "Default abstract",
        attributes: dict = Templates.geom_point_attribute(),
        epsg: int = 4326,
    ) -> Response:
        """
        Create a feature type or update it if it already exist.
        """
        workspace = workspace or self.default_workspace
        if not workspace:
            raise ValueError("Workspace not provided")
        datastore = datastore or self.default_datastore
        if not datastore:
            raise ValueError("Datastore not provided")
        path: str = (
            f"/rest/workspaces/{workspace}/datastores/{datastore}/featuretypes.json"
        )
        resource_path: str = (
            f"/rest/workspaces/{workspace}/datastores/{datastore}/featuretypes/{layer}.json"
        )
        payload: dict[str, dict[str, Any]] = Templates.feature_type(
            layer=layer,
            workspace=workspace,
            datastore=datastore,
            attributes=utils.convert_attributes(attributes),
            epsg=epsg,
        )
        if type(title) is dict:
            payload["featureType"]["internationalTitle"] = title
        else:
            payload["featureType"]["title"] = title
        if type(abstract) is dict:
            payload["featureType"]["internationalAbstract"] = abstract
        else:
            payload["featureType"]["abstract"] = abstract

        if not self.resource_exists(resource_path):
            return self.post_request(path, json=payload)
        else:
            return self.put_request(resource_path, json=payload)

    def create_layer_group(
        self,
        group: str,
        workspace: str | None,
        layers: list[str],
        title: str | dict,
        abstract: str | dict,
        epsg: int = 4326,
        mode: str = "SINGLE",
    ) -> Response:
        """
        Create a layer group if it does not already exist.
        """
        workspace = workspace or self.default_workspace
        if not workspace:
            raise ValueError("Workspace not provided")
        path: str = f"/rest/workspaces/{workspace}/layergroups.json"
        resource_path: str = f"/rest/workspaces/{workspace}/layergroups/{group}.json"
        payload: dict[str, dict[str, Any]] = Templates.layer_group(
            group=group,
            layers=layers,
            workspace=workspace,
            title=title,
            abstract=abstract,
            epsg=epsg,
            mode=mode,
        )
        if not self.resource_exists(resource_path):
            return self.post_request(path, json=payload)
        else:
            return self.put_request(resource_path, json=payload)

    def create_wmts_layer(
        self,
        workspace: str,
        wmts_store: str,
        native_layer: str,
        published_layer: str | None = None,
        epsg: int = 4326,
    ) -> Response | None:
        """
        Publish a remote WMTS layer if it does not already exist.
        """
        if not published_layer:
            published_layer = native_layer
        if self.resource_exists(
            f"/rest/workspaces/{workspace}/wmtsstores/{wmts_store}/layers/{published_layer}.json"
        ):
            return None
        wmts_store_path = f"/rest/workspaces/{workspace}/wmtsstores/{wmts_store}.json"
        capabilities_url = (
            self.get_request(wmts_store_path)
            .json()
            .get("wmtsStore")
            .get("capabilitiesURL")
        )
        wgs84_bbox = self.get_wmts_layer_bbox(capabilities_url, native_layer)

        path = f"/rest/workspaces/{workspace}/wmtsstores/{wmts_store}/layers.json"
        payload = Templates.wmts_layer(
            published_layer, native_layer, wgs84_bbox=wgs84_bbox, epsg=epsg
        )

        return self.post_request(path, json=payload)

    def publish_gwc_layer(
        self, workspace: str, layer: str, epsg: int = 4326
    ) -> Response | None:
        # Reload config to make sure GWC is aware of GeoServer layers
        self.post_request(
            "/gwc/rest/reload",
            headers={"Content-Type": "application/json"},
            data="reload_configuration=1",  # type: ignore
        )
        payload = Templates.gwc_layer(workspace, layer, f"EPSG:{epsg}")
        return self.put_request(
            f"/gwc/rest/layers/{workspace}:{layer}.json",
            json=payload,
        )

    def create_style_from_file(
        self,
        style: str,
        file: str,
        workspace: str | None = None,
    ) -> Response:
        """Create a style from a file, or update it if it already exists.
        Supported file extensions are .sld and .zip."""
        path = (
            "/rest/styles" if not workspace else f"/rest/workspaces/{workspace}/styles"
        )
        resource_path = (
            f"/rest/styles/{style}.json"
            if not workspace
            else f"/rest/workspaces/{workspace}/styles/{style}.json"
        )

        file_ext = os.path.splitext(file)[1]
        if file_ext == ".sld":
            content_type = "application/vnd.ogc.sld+xml"
        elif file_ext == ".zip":
            content_type = "application/zip"
        else:
            raise ValueError(f"Unsupported file extension: {file_ext}")
        with open(f"{file}", "rb") as fs:
            data: bytes = fs.read()
        headers: dict[str, str] = {"Content-Type": content_type}

        if not self.resource_exists(resource_path):
            return self.post_request(path, data=data, headers=headers)
        else:
            return self.put_request(resource_path, data=data, headers=headers)

    def set_default_layer_style(
        self, layer: str, workspace: str, style: str
    ) -> Response:
        path = f"/rest/layers/{workspace}:{layer}.json"
        data = {"layer": {"defaultStyle": {"name": style}}}
        return self.put_request(path, json=data)

    def get_wms_capabilities(
        self, workspace: str, accept_languages=None
    ) -> dict[str, Any]:
        path: str = f"/{workspace}/wms"
        params: dict[str, str] = {
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetCapabilities",
        }
        if accept_languages:
            params["AcceptLanguages"] = accept_languages
        response: Response = self.get_request(path, params=params)
        return xmltodict.parse(response.content)

    def get_wms_layers(
        self, workspace: str, accept_languages: str | None = None
    ) -> Any | dict[str, Any]:
        capabilities: dict[str, Any] = self.get_wms_capabilities(
            workspace, accept_languages
        )
        try:
            return capabilities["WMS_Capabilities"]["Capability"]["Layer"]
        except KeyError:
            return capabilities

    def get_wfs_capabilities(self, workspace: str) -> dict[str, Any]:
        path: str = f"/{workspace}/wfs"
        params: dict[str, str] = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetCapabilities",
        }
        response: Response = self.get_request(path, params=params)
        return xmltodict.parse(response.content)

    def get_wfs_layers(self, workspace: str) -> Any | dict[str, Any]:
        capabilities: dict[str, Any] = self.get_wfs_capabilities(workspace)
        try:
            return capabilities["wfs:WFS_Capabilities"]["FeatureTypeList"]
        except KeyError:
            return capabilities

    def get_map(
        self,
        layers: list[str],
        bbox: tuple[float, float, float, float],
        size: tuple[int, int],
        srs: str = "EPSG:2056",
        format: str = "image/png",
        transparent: bool = True,
        styles: list[str] | None = None,
        language: str | None = None,
    ) -> ResponseWrapper | None:
        if not self.wms:
            self.create_wms()
        params: dict[str, Any] = {
            "layers": layers,
            "srs": srs,
            "bbox": bbox,
            "size": size,
            "format": format,
            "transparent": transparent,
            "styles": styles,
        }
        if language is not None:
            params["language"] = language
        if self.wms:
            return self.wms.getmap(
                **params,
                timeout=120,
            )

    def get_feature_info(
        self,
        layers: list[str],
        bbox: tuple[float, float, float, float],
        size: tuple[int, int],
        srs: str = "EPSG:2056",
        info_format: str = "application/json",
        transparent: bool = True,
        styles: list[str] | None = None,
        xy: list[float] = [0, 0],
    ) -> ResponseWrapper | None:
        if not self.wms:
            self.create_wms()
        params = {
            "layers": layers,
            "srs": srs,
            "bbox": bbox,
            "size": size,
            "info_format": info_format,
            "transparent": transparent,
            "styles": styles,
            "xy": xy,
        }
        if self.wms:
            return self.wms.getfeatureinfo(
                **params,
            )

    def get_legend_graphic(
        self,
        layer: list[str],
        format: str = "image/png",
        language: str | None = None,
        style: str | None = None,
        workspace: str | None = None,
    ) -> Response:
        if not workspace:
            path = "/wms"
        else:
            path: str = f"/{workspace}/wms"
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
        response: Response = self.get_request(path, params=params)
        return response

    def get_tile(
        self, layer, format, tile_matrix_set, tile_matrix, row, column
    ) -> ResponseWrapper | None:
        if not self.wmts:
            self.create_wmts()
        if self.wmts:
            return self.wmts.gettile(
                layer=layer,
                format=format,
                tilematrixset=tile_matrix_set,
                tilematrix=tile_matrix,
                row=row,
                column=column,
            )

    def create_role(self, role_name: str):
        self.post_request(f"/rest/security/roles/role/{role_name}")

    def delete_role(self, role_name: str):
        self.delete_request(f"/rest/security/roles/role/{role_name}")

    def create_role_if_not_exists(self, role_name: str) -> Response | None:
        if self.role_exists(role_name):
            return None
        return self.create_role(role_name)

    def role_exists(self, role_name: str) -> bool:
        response = self.get_request(
            f"/rest/security/roles", headers={"Accept": "application/json"}
        )
        roles = response.json().get("roles", [])
        return role_name in roles

    def create_acl_admin_rule(
        self,
        priority: int = 0,
        access: str = "ADMIN",
        role: str | None = None,
        user: str | None = None,
        workspace: str | None = None,
    ) -> Response:
        path = "/acl/api/adminrules"
        return self.post_request(
            path,
            json={
                "priority": priority,
                "access": access,
                "role": role,
                "user": user,
                "workspace": workspace,
            },
        )

    def delete_acl_admin_rule(self, id: int) -> Response:
        path = f"/acl/api/adminrules/id/{id}"
        return self.delete_request(path)

    def delete_all_acl_admin_rules(self) -> Response:
        path = "/acl/api/adminrules"
        return self.delete_request(path)

    def create_acl_rule(
        self,
        priority: int = 0,
        access: str = "DENY",
        role: str | None = None,
        service: str | None = None,
        workspace: str | None = None,
    ) -> Response:
        path = "/acl/api/rules"
        return self.post_request(
            path,
            json={
                "priority": priority,
                "access": access,
                "role": role,
                "service": service,
                "workspace": workspace,
            },
        )

    def delete_all_acl_rules(self) -> Response:
        path = "/acl/api/rules"
        return self.delete_request(path)

    def create_or_update_resource(self, path, resource_path, payload) -> Response:
        if not self.resource_exists(resource_path):
            return self.post_request(path, json=payload)
        else:
            return self.put_request(resource_path, json=payload)

    def create_gridset(self, epsg: int) -> Response | None:
        resource_path: str = f"/gwc/rest/gridsets/EPSG:{epsg}.xml"
        if self.resource_exists(resource_path):
            return None
        file_path: Path = Path(__file__).parent / "gridsets" / f"{epsg}.xml"
        headers: dict[str, str] = {"Content-Type": "application/xml"}
        try:
            data: bytes = file_path.read_bytes()
        except FileNotFoundError:
            raise ValueError(f"No gridset definition found for EPSG:{epsg}")
        return self.put_request(resource_path, data=data, headers=headers)

    def resource_exists(self, path: str) -> bool:
        # GeoServer raises a 500 when posting to a datastore or feature type that already exists, so first do
        # a get request
        response = self.get_request(path)
        return response.status_code == 200

    def get_request(
        self,
        path,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        return self.rest_service.get(path, params=params, headers=headers)

    def post_request(
        self,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        data: bytes | None = None,
    ) -> Response:
        return self.rest_service.post(
            path, params=params, headers=headers, json=json, data=data
        )

    def put_request(
        self,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, dict[str, Any]] | None = None,
        data: bytes | None = None,
    ) -> Response:
        return self.rest_service.put(
            path, params=params, headers=headers, json=json, data=data
        )

    def delete_request(
        self,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        return self.rest_service.delete(path, params=params, headers=headers)
