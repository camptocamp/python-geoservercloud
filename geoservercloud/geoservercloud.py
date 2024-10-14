import os.path
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import xmltodict
from owslib.map.wms130 import WebMapService_1_3_0
from owslib.util import ResponseWrapper
from owslib.wmts import WebMapTileService
from requests import Response

from geoservercloud import utils
from geoservercloud.models import (
    DataStores,
    FeatureType,
    FeatureTypes,
    KeyDollarListDict,
    PostGisDataStore,
    Style,
    Styles,
    Workspace,
    Workspaces,
)
from geoservercloud.services import (
    AclEndpoints,
    GwcEndpoints,
    OwsEndpoints,
    RestEndpoints,
    RestService,
)
from geoservercloud.templates import Templates


class GeoServerCloud:
    def __init__(
        self,
        url: str = "http://localhost:9090/geoserver/cloud",
        user: str = "admin",
        password: str = "geoserver",  # nosec
    ) -> None:

        self.url: str = url.strip("/")
        self.user: str = user
        self.password: str = password
        self.auth: tuple[str, str] = (user, password)
        self.rest_service: RestService = RestService(url, self.auth)
        self.acl_endpoints: AclEndpoints = AclEndpoints()
        self.gwc_endpoints: GwcEndpoints = GwcEndpoints()
        self.ows_endpoints: OwsEndpoints = OwsEndpoints()
        self.rest_endpoints: RestEndpoints = RestEndpoints()
        self.wms: WebMapService_1_3_0 | None = None
        self.wmts: WebMapTileService | None = None
        self.default_workspace: str | None = None
        self.default_datastore: str | None = None

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
            path: str = self.ows_endpoints.workspace_wms(self.default_workspace)
        else:
            path = self.ows_endpoints.wms()
        self.wms = WebMapService_1_3_0(
            f"{self.url}{path}",
            username=self.user,
            password=self.password,
            timeout=240,
        )

    def create_wmts(self) -> None:
        path = self.ows_endpoints.wmts()
        self.wmts = WebMapTileService(
            f"{self.url}{path}",
            version="1.0.0",
            username=self.user,
            password=self.password,
        )

    def get_workspaces(self) -> Workspaces:
        response: Response = self.get_request(self.rest_endpoints.workspaces())
        workspaces = Workspaces.from_response(response)
        return workspaces

    def create_workspace(
        self,
        workspace_name: str,
        isolated: bool = False,
        set_default_workspace: bool = False,
    ) -> Response:
        """
        Create a workspace in GeoServer, if it does not already exist.
        It if exists, update it
        """
        response: Response = self.post_request(
            self.rest_endpoints.workspaces(),
            json=Workspace(workspace_name, isolated).post_payload(),
        )
        if response.status_code == 409:
            response = self.put_request(
                self.rest_endpoints.workspace(workspace_name),
                json=Workspace(workspace_name, isolated).put_payload(),
            )
        if set_default_workspace:
            self.default_workspace = workspace_name
        return response

    def delete_workspace(self, workspace_name: str) -> Response:
        """
        Delete a GeoServer workspace (recursively)
        """
        response: Response = self.delete_request(
            self.rest_endpoints.workspace(workspace_name), params={"recurse": "true"}
        )
        if self.default_workspace == workspace_name:
            self.default_workspace = None
            self.wms = None
            self.wmts = None
        return response

    def recreate_workspace(
        self, workspace_name: str, set_default_workspace: bool = False
    ) -> Response:
        """
        Create a workspace in GeoServer, and first delete it if it already exists.
        """
        self.delete_workspace(workspace_name)
        return self.create_workspace(
            workspace_name, set_default_workspace=set_default_workspace
        )

    def publish_workspace(self, workspace_name) -> Response:
        """
        Publish the WMS service for a given workspace
        """
        data: dict[str, dict[str, Any]] = Templates.workspace_wms(workspace_name)
        return self.put_request(
            self.rest_endpoints.workspace_wms_settings(workspace_name), json=data
        )

    def set_default_locale_for_service(
        self, workspace_name: str, locale: str | None
    ) -> Response:
        """
        Set a default language for localized WMS requests
        """
        data: dict[str, dict[str, Any]] = {
            "wms": {
                "defaultLocale": locale,
            }
        }
        return self.put_request(
            self.rest_endpoints.workspace_wms_settings(workspace_name), json=data
        )

    def unset_default_locale_for_service(self, workspace_name) -> None:
        """
        Remove the default language for localized WMS requests
        """
        self.set_default_locale_for_service(workspace_name, None)

    def get_datastores(self, workspace_name: str) -> dict[str, Any]:
        """
        Get all datastores for a given workspace
        """
        response = self.get_request(self.rest_endpoints.datastores(workspace_name))
        return DataStores.from_response(response).datastores

    def get_postgis_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> dict[str, Any]:
        """
        Get a specific datastore
        """
        response = self.get_request(
            self.rest_endpoints.datastore(workspace_name, datastore_name)
        )
        return PostGisDataStore.from_response(response)

    def create_pg_datastore(
        self,
        workspace_name: str,
        datastore_name: str,
        pg_host: str,
        pg_port: int,
        pg_db: str,
        pg_user: str,
        pg_password: str,
        pg_schema: str = "public",
        description: str | None = None,
        set_default_datastore: bool = False,
    ) -> Response | None:
        """
        Create a PostGIS datastore from the DB connection parameters, or update it if it already exist.
        """
        response: None | Response = None
        datastore = PostGisDataStore(
            workspace_name,
            datastore_name,
            connection_parameters=KeyDollarListDict(
                input_dict={
                    "dbtype": "postgis",
                    "host": pg_host,
                    "port": pg_port,
                    "database": pg_db,
                    "user": pg_user,
                    "passwd": pg_password,
                    "schema": pg_schema,
                    "namespace": f"http://{workspace_name}",
                    "Expose primary keys": "true",
                }
            ),
            data_store_type="PostGIS",
            description=description,
        )
        payload = datastore.put_payload()

        if not self.resource_exists(
            self.rest_endpoints.datastore(workspace_name, datastore_name)
        ):
            response = self.post_request(
                self.rest_endpoints.datastores(workspace_name), json=payload
            )
        else:
            response = self.put_request(
                self.rest_endpoints.datastore(workspace_name, datastore_name),
                json=payload,
            )

        if set_default_datastore:
            self.default_datastore = datastore_name

        return response

    def create_jndi_datastore(
        self,
        workspace_name: str,
        datastore_name: str,
        jndi_reference: str,
        pg_schema: str = "public",
        description: str | None = None,
        set_default_datastore: bool = False,
    ) -> Response | None:
        """
        Create a PostGIS datastore from JNDI resource, or update it if it already exist.
        """
        response: None | Response = None
        datastore = PostGisDataStore(
            workspace_name,
            datastore_name,
            connection_parameters=KeyDollarListDict(
                input_dict={
                    "dbtype": "postgis",
                    "jndiReferenceName": jndi_reference,
                    "schema": pg_schema,
                    "namespace": f"http://{workspace_name}",
                    "Expose primary keys": "true",
                }
            ),
            data_store_type="PostGIS (JNDI)",
            description=description,
        )
        payload = datastore.put_payload()
        if not self.resource_exists(
            self.rest_endpoints.datastore(workspace_name, datastore_name)
        ):
            response = self.post_request(
                self.rest_endpoints.datastores(workspace_name), json=payload
            )
        else:
            response = self.put_request(
                self.rest_endpoints.datastore(workspace_name, datastore_name),
                json=payload,
            )

        if set_default_datastore:
            self.default_datastore = datastore_name

        return response

    def create_wmts_store(
        self,
        workspace_name: str,
        name: str,
        capabilities: str,
    ) -> Response:
        """
        Create a cascaded WMTS store, or update it if it already exist.
        """
        payload = Templates.wmts_store(workspace_name, name, capabilities)
        if not self.resource_exists(
            self.rest_endpoints.wmtsstore(workspace_name, name)
        ):
            return self.post_request(
                self.rest_endpoints.wmtsstores(workspace_name), json=payload
            )
        else:
            return self.put_request(
                self.rest_endpoints.wmtsstore(workspace_name, name), json=payload
            )

    def get_feature_types(
        self, workspace_name: str, datastore_name: str
    ) -> dict[str, Any]:
        """
        Get all feature types for a given workspace and datastore
        """
        featuretypes = FeatureTypes.from_response(
            self.get_request(
                self.rest_endpoints.featuretypes(workspace_name, datastore_name)
            )
        )
        return featuretypes

    def get_feature_type(
        self, workspace_name: str, datastore_name: str, feature_type_name: str
    ) -> dict[str, Any]:
        return FeatureType.from_response(
            self.get_request(
                self.rest_endpoints.featuretype(
                    workspace_name, datastore_name, feature_type_name
                )
            )
        )

    def create_feature_type(
        self,
        layer: str,
        workspace_name: str | None = None,
        datastore: str | None = None,
        title: str | dict = "Default title",
        abstract: str | dict = "Default abstract",
        attributes: dict = Templates.geom_point_attribute(),
        epsg: int = 4326,
    ) -> Response:
        """
        Create a feature type or update it if it already exist.
        """
        workspace_name = workspace_name or self.default_workspace
        if not workspace_name:
            raise ValueError("Workspace not provided")
        datastore = datastore or self.default_datastore
        if not datastore:
            raise ValueError("Datastore not provided")
        payload: dict[str, dict[str, Any]] = Templates.feature_type(
            layer=layer,
            workspace=workspace_name,
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

        if not self.resource_exists(
            self.rest_endpoints.featuretype(workspace_name, datastore, layer)
        ):
            return self.post_request(
                self.rest_endpoints.featuretypes(workspace_name, datastore),
                json=payload,
            )
        else:
            return self.put_request(
                self.rest_endpoints.featuretype(workspace_name, datastore, layer),
                json=payload,
            )

    def create_layer_group(
        self,
        group: str,
        workspace_name: str | None,
        layers: list[str],
        title: str | dict,
        abstract: str | dict,
        epsg: int = 4326,
        mode: str = "SINGLE",
    ) -> Response:
        """
        Create a layer group if it does not already exist.
        """
        workspace_name = workspace_name or self.default_workspace
        if not workspace_name:
            raise ValueError("Workspace not provided")
        payload: dict[str, dict[str, Any]] = Templates.layer_group(
            group=group,
            layers=layers,
            workspace=workspace_name,
            title=title,
            abstract=abstract,
            epsg=epsg,
            mode=mode,
        )
        if not self.resource_exists(
            self.rest_endpoints.layergroup(workspace_name, group)
        ):
            return self.post_request(
                self.rest_endpoints.layergroups(workspace_name), json=payload
            )
        else:
            return self.put_request(
                self.rest_endpoints.layergroup(workspace_name, group), json=payload
            )

    def create_wmts_layer(
        self,
        workspace_name: str,
        wmts_store: str,
        native_layer: str,
        published_layer: str | None = None,
        epsg: int = 4326,
        international_title: dict[str, str] | None = None,
        international_abstract: dict[str, str] | None = None,
    ) -> Response:
        """
        Publish a remote WMTS layer (first delete it if it already exists)
        """
        if not published_layer:
            published_layer = native_layer
        if self.resource_exists(
            self.rest_endpoints.wmtslayer(workspace_name, wmts_store, published_layer)
        ):
            self.delete_request(
                self.rest_endpoints.wmtslayer(
                    workspace_name, wmts_store, published_layer
                ),
                params={"recurse": "true"},
            )
        capabilities_url = (
            self.get_request(self.rest_endpoints.wmtsstore(workspace_name, wmts_store))
            .json()
            .get("wmtsStore")
            .get("capabilitiesURL")
        )
        wgs84_bbox = self.get_wmts_layer_bbox(capabilities_url, native_layer)

        payload = Templates.wmts_layer(
            published_layer,
            native_layer,
            wgs84_bbox=wgs84_bbox,
            epsg=epsg,
            international_title=international_title,
            international_abstract=international_abstract,
        )

        return self.post_request(
            self.rest_endpoints.wmtslayers(workspace_name, wmts_store), json=payload
        )

    def get_gwc_layer(self, workspace_name: str, layer: str) -> dict[str, Any] | None:
        response = self.get_request(self.gwc_endpoints.layer(workspace_name, layer))
        if response.status_code == 404:
            return None
        return response.json()

    def publish_gwc_layer(
        self, workspace_name: str, layer: str, epsg: int = 4326
    ) -> Response | None:
        # Reload config to make sure GWC is aware of GeoServer layers
        self.post_request(
            self.gwc_endpoints.reload(),
            headers={"Content-Type": "application/json"},
            data="reload_configuration=1",  # type: ignore
        )
        # Do not re-publish an existing layer
        if self.get_gwc_layer(workspace_name, layer):
            return None
        payload = Templates.gwc_layer(workspace_name, layer, f"EPSG:{epsg}")
        return self.put_request(
            self.gwc_endpoints.layer(workspace_name, layer),
            json=payload,
        )

    def get_styles(self, workspace_name: str | None = None) -> dict[str, Any]:
        """
        Get all styles for a given workspace
        """
        path = (
            self.rest_endpoints.styles()
            if not workspace_name
            else self.rest_endpoints.workspace_styles(workspace_name)
        )
        styles = Styles.from_response(self.get_request(path)).styles
        return styles

    def get_style(
        self, style: str, workspace_name: str | None = None
    ) -> dict[str, Any]:
        """
        Get a specific style
        """
        path = (
            self.rest_endpoints.style(style)
            if not workspace_name
            else self.rest_endpoints.workspace_style(workspace_name, style)
        )
        return Style.from_response(self.get_request(path))

    # TODO: add a create_style method that takes a Style object as input
    def create_style_from_file(
        self,
        style: str,
        file: str,
        workspace_name: str | None = None,
    ) -> Response:
        """Create a style from a file, or update it if it already exists.
        Supported file extensions are .sld and .zip."""
        path = (
            self.rest_endpoints.styles()
            if not workspace_name
            else self.rest_endpoints.workspace_styles(workspace_name)
        )
        resource_path = (
            self.rest_endpoints.style(style)
            if not workspace_name
            else self.rest_endpoints.workspace_style(workspace_name, style)
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
        self, layer: str, workspace_name: str, style: str
    ) -> Response:
        data = {"layer": {"defaultStyle": {"name": style}}}
        return self.put_request(
            self.rest_endpoints.workspace_layer(workspace_name, layer), json=data
        )

    def get_wms_capabilities(
        self, workspace_name: str, accept_languages=None
    ) -> dict[str, Any]:
        path: str = self.ows_endpoints.workspace_wms(workspace_name)
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
        self, workspace_name: str, accept_languages: str | None = None
    ) -> Any | dict[str, Any]:
        capabilities: dict[str, Any] = self.get_wms_capabilities(
            workspace_name, accept_languages
        )
        try:
            return capabilities["WMS_Capabilities"]["Capability"]["Layer"]
        except KeyError:
            return capabilities

    def get_wfs_capabilities(self, workspace_name: str) -> dict[str, Any]:
        params: dict[str, str] = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetCapabilities",
        }
        response: Response = self.get_request(
            self.ows_endpoints.workspace_wfs(workspace_name), params=params
        )
        return xmltodict.parse(response.content)

    def get_wfs_layers(self, workspace_name: str) -> Any | dict[str, Any]:
        capabilities: dict[str, Any] = self.get_wfs_capabilities(workspace_name)
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
        """
        WMS GetMap request
        """
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
        return None

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
        """
        WMS GetFeatureInfo request
        """
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
        return None

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
        response: Response = self.get_request(path, params=params)
        return response

    def get_tile(
        self, layer, format, tile_matrix_set, tile_matrix, row, column
    ) -> ResponseWrapper | None:
        """
        WMTS GetTile request
        """
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
        return None

    def get_feature(
        self,
        workspace_name: str,
        type_name: str,
        feature_id: int | None = None,
        max_feature: int | None = None,
        format: str = "application/json",
    ) -> dict[str, Any] | bytes:
        """WFS GetFeature request
        Return the feature(s) as dict if found, otherwise return the raw response content as bytes
        """
        # FIXME: we should consider also the global wfs endpoint
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
        response = self.get_request(path, params=params)
        try:
            return response.json()
        except JSONDecodeError:
            return response.content

    def describe_feature_type(
        self,
        workspace_name: str | None = None,
        type_name: str | None = None,
        format: str = "application/json",
    ) -> dict[str, Any] | bytes:
        """WFS DescribeFeatureType request
        Return the feature type(s) as dict if found, otherwise return the raw response content as bytes
        """
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
        response = self.get_request(path, params=params)
        try:
            return response.json()
        except JSONDecodeError:
            return response.content

    def get_property_value(
        self,
        workspace_name: str,
        type_name: str,
        property: str,
    ) -> dict | list | bytes:
        """WFS GetPropertyValue request
        Return the properties as dict (if one feature was found), a list (if multiple features were found)
        or an empty dict if no feature was found. Otherwise throw a requests.exceptions.HTTPError
        """
        # FIXME: we should consider also the global wfs endpoint
        path = self.ows_endpoints.workspace_wfs(workspace_name)
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetPropertyValue",
            "typeNames": type_name,
            "valueReference": property,
        }
        response = self.get_request(path, params=params)
        value_collection = xmltodict.parse(response.content).get("wfs:ValueCollection")
        if not value_collection:
            return response.content
        else:
            return value_collection.get("wfs:member", {})

    def create_user(self, user: str, password: str, enabled: bool = True) -> Response:
        """
        Create a GeoServer user
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        payload: dict[str, dict[str, Any]] = {
            "user": {
                "userName": user,
                "password": password,
                "enabled": enabled,
            }
        }
        return self.post_request(
            self.rest_endpoints.users(), json=payload, headers=headers
        )

    def update_user(
        self, user: str, password: str | None = None, enabled: bool | None = None
    ) -> Response:
        """
        Update a GeoServer user
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        payload: dict[str, dict[str, Any]] = {"user": {}}
        if password:
            payload["user"]["password"] = password
        if enabled is not None:
            payload["user"]["enabled"] = enabled
        return self.post_request(
            self.rest_endpoints.user(user), json=payload, headers=headers
        )

    def delete_user(self, user: str) -> Response:
        """
        Delete a GeoServer user
        """
        return self.delete_request(self.rest_endpoints.user(user))

    def create_role(self, role_name: str) -> Response:
        """
        Create a GeoServer role
        """
        return self.post_request(self.rest_endpoints.role(role_name))

    def delete_role(self, role_name: str) -> Response:
        """
        Delete a GeoServer role
        """
        return self.delete_request(self.rest_endpoints.role(role_name))

    def create_role_if_not_exists(self, role_name: str) -> Response | None:
        """
        Create a GeoServer role if it does not yet exist
        """
        if self.role_exists(role_name):
            return None
        return self.create_role(role_name)

    def role_exists(self, role_name: str) -> bool:
        """
        Check if a GeoServer role exists
        """
        response = self.get_request(
            self.rest_endpoints.roles(), headers={"Accept": "application/json"}
        )
        roles = response.json().get("roles", [])
        return role_name in roles

    def get_user_roles(self, user: str) -> list[str] | Response:
        """
        Get all roles assigned to a GeoServer user
        """
        response = self.get_request(self.rest_endpoints.user_roles(user))
        try:
            return response.json().get("roles")
        except JSONDecodeError:
            return response

    def assign_role_to_user(self, user: str, role: str) -> Response:
        """
        Assign a role to a GeoServer user
        """
        return self.post_request(self.rest_endpoints.role_user(role, user))

    def remove_role_from_user(self, user: str, role: str) -> Response:
        """
        Remove a role from a GeoServer user
        """
        return self.delete_request(self.rest_endpoints.role_user(role, user))

    def create_acl_admin_rule(
        self,
        priority: int = 0,
        access: str = "ADMIN",
        role: str | None = None,
        user: str | None = None,
        workspace_name: str | None = None,
    ) -> Response:
        """
        Create a GeoServer ACL admin rule
        """
        return self.post_request(
            self.acl_endpoints.adminrules(),
            json={
                "priority": priority,
                "access": access,
                "role": role,
                "user": user,
                "workspace": workspace_name,
            },
        )

    def delete_acl_admin_rule(self, id: int) -> Response:
        """
        Delete a GeoServer ACL admin rule by id
        """
        return self.delete_request(self.acl_endpoints.adminrule(id))

    def delete_all_acl_admin_rules(self) -> Response:
        """
        Delete all existing GeoServer ACL admin rules
        """
        return self.delete_request(self.acl_endpoints.adminrules())

    def get_acl_rules(self) -> dict[str, Any]:
        """
        Return all GeoServer ACL data rules
        """
        response = self.get_request(self.acl_endpoints.rules())
        return response.json()

    def create_acl_rules_for_requests(
        self,
        requests: list[str],
        priority: int = 0,
        access: str = "DENY",
        role: str | None = None,
        service: str | None = None,
        workspace_name: str | None = None,
    ) -> list[Response]:
        """
        Create ACL rules for multiple type of OGC requests
        """
        responses = []
        for request in requests:
            responses.append(
                self.create_acl_rule(
                    priority=priority,
                    access=access,
                    role=role,
                    request=request,
                    service=service,
                    workspace_name=workspace_name,
                )
            )
        return responses

    def create_acl_rule(
        self,
        priority: int = 0,
        access: str = "DENY",
        role: str | None = None,
        user: str | None = None,
        service: str | None = None,
        request: str | None = None,
        workspace_name: str | None = None,
    ) -> Response:
        """
        Create a GeoServer ACL data rule
        """
        json = {"priority": priority, "access": access}
        if role:
            json["role"] = role
        if user:
            json["user"] = user
        if service:
            json["service"] = service
        if request:
            json["request"] = request
        if workspace_name:
            json["workspace"] = workspace_name
        return self.post_request(self.acl_endpoints.rules(), json=json)

    def delete_all_acl_rules(self) -> Response:
        """
        Delete all existing GeoServer ACL data rules
        """
        return self.delete_request(self.acl_endpoints.rules())

    def create_gridset(self, epsg: int) -> Response | None:
        """
        Create a gridset for GeoWebCache for a given projection
        Supported EPSG codes are 2056, 21781 and 3857
        """
        if self.resource_exists(self.gwc_endpoints.gridset(epsg)):
            return None
        file_path: Path = Path(__file__).parent / "gridsets" / f"{epsg}.xml"
        headers: dict[str, str] = {"Content-Type": "application/xml"}
        try:
            data: bytes = file_path.read_bytes()
        except FileNotFoundError:
            raise ValueError(f"No gridset definition found for EPSG:{epsg}")
        return self.put_request(
            self.gwc_endpoints.gridset(epsg), data=data, headers=headers
        )

    def create_or_update_resource(self, path, resource_path, payload) -> Response:
        """
        Create a GeoServer resource or update it if it already exists
        """
        if not self.resource_exists(resource_path):
            return self.post_request(path, json=payload)
        else:
            return self.put_request(resource_path, json=payload)

    def resource_exists(self, path: str) -> bool:
        """
        Check if a resource (given its path) exists in GeoServer
        """
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
