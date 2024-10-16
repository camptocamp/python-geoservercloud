from json import JSONDecodeError
from typing import Any

from requests import Response

from geoservercloud.models import DataStores, PostGisDataStore, Workspace, Workspaces
from geoservercloud.services.restclient import RestClient
from geoservercloud.templates import Templates


class RestService:
    """
    Service responsible for serializing and deserializing payloads and routing requests to GeoServer

    Attributes
    ----------
    url : str
        base GeoServer URL
    auth : tuple[str, str]
        username and password for GeoServer
    """

    def __init__(self, url: str, auth: tuple[str, str]) -> None:
        self.url: str = url
        self.auth: tuple[str, str] = auth
        self.rest_client = RestClient(url, auth)
        self.acl_endpoints = self.AclEndpoints()
        self.gwc_endpoints = self.GwcEndpoints()
        self.ows_endpoints = self.OwsEndpoints()
        self.rest_endpoints = self.RestEndpoints()

    def get_workspaces(self) -> tuple[Workspaces | str, int]:
        response = self.rest_client.get(self.rest_endpoints.workspaces())
        return self.deserialize_response(response, Workspaces)

    def get_workspace(self, name: str) -> tuple[Workspace | str, int]:
        response = self.rest_client.get(self.rest_endpoints.workspace(name))
        return self.deserialize_response(response, Workspace)

    def create_workspace(self, workspace: Workspace) -> tuple[str, int]:
        path: str = self.rest_endpoints.workspaces()
        response: Response = self.rest_client.post(path, json=workspace.post_payload())
        if response.status_code == 409:
            path = self.rest_endpoints.workspace(workspace.name)
            response = self.rest_client.put(path, json=workspace.put_payload())
        return response.content.decode(), response.status_code

    def delete_workspace(self, workspace: Workspace) -> tuple[str, int]:
        path: str = self.rest_endpoints.workspace(workspace.name)
        params: dict[str, str] = {"recurse": "true"}
        response: Response = self.rest_client.delete(path, params=params)
        return response.content.decode(), response.status_code

    def publish_workspace(self, workspace: Workspace) -> tuple[str, int]:
        data: dict[str, dict[str, Any]] = Templates.workspace_wms(workspace.name)
        response = self.rest_client.put(
            self.rest_endpoints.workspace_wms_settings(workspace.name), json=data
        )
        return response.content.decode(), response.status_code

    def set_default_locale_for_service(
        self, workspace: Workspace, locale: str | None
    ) -> None:
        data: dict[str, dict[str, Any]] = {
            "wms": {
                "defaultLocale": locale,
            }
        }
        self.rest_client.put(
            self.rest_endpoints.workspace_wms_settings(workspace.name), json=data
        )

    def get_datastores(self, workspace_name: str) -> tuple[DataStores | str, int]:
        response = self.rest_client.get(self.rest_endpoints.datastores(workspace_name))
        return self.deserialize_response(response, DataStores)

    def get_pg_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[PostGisDataStore | str, int]:
        response = self.rest_client.get(
            self.rest_endpoints.datastore(workspace_name, datastore_name)
        )
        return self.deserialize_response(response, PostGisDataStore)

    def create_pg_datastore(
        self, workspace_name: str, datastore: PostGisDataStore
    ) -> tuple[str, int]:
        if not self.resource_exists(
            self.rest_endpoints.datastore(workspace_name, datastore.name)
        ):
            response: Response = self.rest_client.post(
                self.rest_endpoints.datastores(workspace_name),
                json=datastore.post_payload(),
            )
        else:
            response: Response = self.rest_client.put(
                self.rest_endpoints.datastore(workspace_name, datastore.name),
                json=datastore.put_payload(),
            )
        return response.content.decode(), response.status_code

    def create_jndi_datastore(
        self, workspace_name: str, datastore: PostGisDataStore
    ) -> tuple[str, int]:
        if not self.resource_exists(
            self.rest_endpoints.datastore(workspace_name, datastore.name)
        ):
            response: Response = self.rest_client.post(
                self.rest_endpoints.datastores(workspace_name),
                json=datastore.post_payload(),
            )
        else:
            response: Response = self.rest_client.put(
                self.rest_endpoints.datastore(workspace_name, datastore.name),
                json=datastore.put_payload(),
            )
        return response.content.decode(), response.status_code

    def resource_exists(self, path: str) -> bool:
        response = self.rest_client.get(path)
        return response.status_code == 200

    def deserialize_response(
        self, response: Response, data_type: type
    ) -> tuple[Any, int]:
        try:
            content = response.json()
        except JSONDecodeError:
            return response.content.decode(), response.status_code
        return data_type.from_get_response_payload(content), response.status_code

    class AclEndpoints:
        def __init__(self, base_url: str = "/acl") -> None:
            self.base_url: str = base_url

        def adminrules(self) -> str:
            return f"{self.base_url}/api/adminrules"

        def adminrule(self, id: int) -> str:
            return f"{self.base_url}/api/adminrules/id/{id}"

        def rules(self) -> str:
            return f"{self.base_url}/api/rules"

    class GwcEndpoints:
        def __init__(self, base_url: str = "/gwc/rest") -> None:
            self.base_url: str = base_url

        def reload(self) -> str:
            return f"{self.base_url}/reload"

        def layers(self, workspace_name: str) -> str:
            return f"{self.base_url}/layers.json"

        def layer(self, workspace_name: str, layer_name: str) -> str:
            return f"{self.base_url}/layers/{workspace_name}:{layer_name}.json"

        def gridsets(self) -> str:
            return f"{self.base_url}/gridsets.json"

        def gridset(self, epsg: int) -> str:
            return f"{self.base_url}/gridsets/EPSG:{str(epsg)}.xml"

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

    class RestEndpoints:
        def __init__(self, base_url: str = "/rest") -> None:
            self.base_url: str = base_url

        def styles(self) -> str:
            return f"{self.base_url}/styles.json"

        def style(self, style_name: str) -> str:
            return f"{self.base_url}/styles/{style_name}.json"

        def workspaces(self) -> str:
            return f"{self.base_url}/workspaces.json"

        def workspace(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}.json"

        def workspace_styles(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/styles.json"

        def workspace_style(self, workspace_name: str, style_name: str) -> str:
            return (
                f"{self.base_url}/workspaces/{workspace_name}/styles/{style_name}.json"
            )

        def workspace_layer(self, workspace_name: str, layer_name: str) -> str:
            return f"{self.base_url}/layers/{workspace_name}:{layer_name}.json"

        def workspace_wms_settings(self, workspace_name: str) -> str:
            return f"{self.base_url}/services/wms/workspaces/{workspace_name}/settings.json"

        def workspace_wfs_settings(self, workspace_name: str) -> str:
            return f"{self.base_url}/services/wfs/workspaces/{workspace_name}/settings.json"

        def datastores(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/datastores.json"

        def datastore(self, workspace_name: str, datastore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/datastores/{datastore_name}.json"

        def featuretypes(self, workspace_name: str, datastore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/datastores/{datastore_name}/featuretypes.json"

        def featuretype(
            self, workspace_name: str, datastore_name: str, featuretype_name: str
        ) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/datastores/{datastore_name}/featuretypes/{featuretype_name}.json"

        def layergroup(self, workspace_name: str, layergroup_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/layergroups/{layergroup_name}.json"

        def layergroups(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/layergroups.json"

        def coveragestores(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/coveragestores.json"

        def coveragestore(self, workspace_name: str, coveragestore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/coveragestores/{coveragestore_name}.json"

        def coverages(self, workspace_name: str, coveragestore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages.json"

        def coverage(
            self, workspace_name: str, coveragestore_name: str, coverage_name: str
        ) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages/{coverage_name}.json"

        def wmsstores(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmsstores.json"

        def wmsstore(self, workspace_name: str, wmsstore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmsstores/{wmsstore_name}.json"

        def wmtsstores(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmtsstores.json"

        def wmtsstore(self, workspace_name: str, wmtsstore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmtsstores/{wmtsstore_name}.json"

        def wmtslayers(self, workspace_name: str, wmtsstore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmtsstores/{wmtsstore_name}/layers.json"

        def wmtslayer(
            self, workspace_name: str, wmtsstore_name: str, wmtslayer_name: str
        ) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmtsstores/{wmtsstore_name}/layers/{wmtslayer_name}.json"

        def namespaces(self) -> str:
            return f"{self.base_url}/namespaces.json"

        def namespace(self, namespace_name: str) -> str:
            return f"{self.base_url}/namespaces/{namespace_name}.json"

        def users(self) -> str:
            return f"{self.base_url}/security/usergroup/users.json"

        def user(self, username: str) -> str:
            return f"{self.base_url}/security/usergroup/user/{username}.json"

        def roles(self) -> str:
            return f"{self.base_url}/security/roles.json"

        def user_roles(self, username: str) -> str:
            return f"{self.base_url}/security/roles/user/{username}.json"

        def role(self, role_name: str) -> str:
            return f"{self.base_url}/security/roles/role/{role_name}.json"

        def role_user(self, role_name: str, username: str) -> str:
            return (
                f"{self.base_url}/security/roles/role/{role_name}/user/{username}.json"
            )
