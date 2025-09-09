from dataclasses import dataclass, field
from typing import Any

from requests import Request, Response


@dataclass
class GsDetail:
    message: str
    info: dict[str, Any] = field(default_factory=lambda: {})


class GsException(Exception):
    def __init__(
        self,
        code: int,
        detail: GsDetail,
        parent_request: Request | None = None,
        parent_response: Response | None = None,
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
