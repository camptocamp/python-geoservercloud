from geoservercloud.services import RestService


class GeoServerCloudSync:
    """
    Facade class allowing synchronization of GeoServer resources between two GeoServer instances

    Attributes
    ----------
    src_url : str
        base GeoServer URL for source GeoServer instance
    src_user : str
        GeoServer username for source GeoServer instance
    src_password : str
        GeoServer password for source GeoServer instance
    dst_url : str
        base GeoServer URL for destination GeoServer instance
    dst_user : str
        GeoServer username for destination GeoServer instance
    dst_password : str
        GeoServer password for destination GeoServer instance
    """

    def __init__(
        self,
        src_url: str,
        src_user: str,
        src_password: str,
        dst_url: str,
        dst_user: str,
        dst_password: str,
    ) -> None:
        self.src_url: str = src_url.strip("/")
        self.src_user: str = src_user
        self.src_password: str = src_password
        self.src_auth: tuple[str, str] = (src_user, src_password)
        self.src_instance: RestService = RestService(src_url, self.src_auth)
        self.dst_url: str = dst_url.strip("/")
        self.dst_user: str = dst_user
        self.dst_password: str = dst_password
        self.dst_auth: tuple[str, str] = (dst_user, dst_password)
        self.dst_instance: RestService = RestService(dst_url, self.dst_auth)

    def copy_workspace(self, workspace_name: str) -> tuple[str, int]:
        """
        Shallow copy a workspace from source to destination GeoServer instance
        """
        workspace, status_code = self.src_instance.get_workspace(workspace_name)
        if isinstance(workspace, str):
            return workspace, status_code
        return self.dst_instance.create_workspace(workspace)

    def copy_pg_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[str, int]:
        """
        Shallow copy a datastore from source to destination GeoServer instance
        """
        datastore, status_code = self.src_instance.get_pg_datastore(
            workspace_name, datastore_name
        )
        if isinstance(datastore, str):
            return datastore, status_code
        return self.dst_instance.create_pg_datastore(workspace_name, datastore)

    def copy_feature_types_in_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> list[tuple[str, int]] | tuple[str, int]:
        """
        Copy all feature types in a datastore from source to destination GeoServer instance
        """
        feature_types, status_code = self.src_instance.get_feature_types(
            workspace_name, datastore_name
        )
        if isinstance(feature_types, str):
            return feature_types, status_code
        return [
            self.copy_feature_type(workspace_name, datastore_name, feature_type_name)
            for feature_type_name in feature_types.aslist()
        ]

    def copy_feature_type(
        self, workspace_name: str, datastore_name: str, feature_type_name: str
    ) -> tuple[str, int]:
        """
        Copy a feature type from source to destination GeoServer instance
        """
        feature_type, status_code = self.src_instance.get_feature_type(
            workspace_name, datastore_name, feature_type_name
        )
        if isinstance(feature_type, str):
            return feature_type, status_code
        return self.dst_instance.create_feature_type(feature_type)

    def copy_style(self, workspace_name: str, style_name: str) -> tuple[str, int]:
        """
        Copy a style from source to destination GeoServer instance
        curl -vf -XPUT -u testadmin:testadmin -H "Content-type:application/vnd.ogc.sld+xml" -T "metro_canton_situation_polygon.sld"
        """
        style, status_code = self.src_instance.get_style(style_name, workspace_name)
        if isinstance(style, str):
            return style, status_code
        return self.dst_instance.create_style(style, workspace_name)
