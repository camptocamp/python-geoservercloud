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
        return f"{self.base_url}/workspaces/{workspace_name}/styles/{style_name}.json"

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
        return f"{self.base_url}/security/roles/role/{role_name}/user/{username}.json"
