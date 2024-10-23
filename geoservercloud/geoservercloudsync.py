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
