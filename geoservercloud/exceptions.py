from typing import Dict, Any
from requests import Request, Response
from dataclasses import dataclass, field


@dataclass
class GsDetail:
    message: str
    info: Dict[str, Any] = field(default_factory=lambda: {})


class GsException(Exception):
    def __init__(
            self,
            code: int,
            detail: GsDetail,
            parent_request: Request = None,
            parent_response: Response = None
    ):
        super().__init__()
        self.code = code
        self.detail = detail
        self.parent_request = parent_request
        self.parent_response = parent_response


class AuthException(GsException):
    pass


class DatastoreMissing(GsException):
    pass


class WorkspaceMissing(GsException):
    pass
