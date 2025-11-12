from typing import Any

import requests

from .restlogger import gs_logger

TIMEOUT = 120


class RestClient:
    """
    HTTP client responsible for issuing requests

    Attributes
    ----------
    url : str
        base GeoServer URL
    auth : tuple[str, str]
        username and password for GeoServer
    """

    def __init__(self, url: str, auth: tuple[str, str], verifytls: bool = True) -> None:
        self.url: str = url
        self.auth: tuple[str, str] = auth
        self.verifytls: bool = verifytls

    def get(
        self,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        full_url = f"{self.url}{path}"
        response: requests.Response = requests.get(
            full_url,
            params=params,
            headers=headers,
            auth=self.auth,
            timeout=TIMEOUT,
            verify=self.verifytls,
        )
        gs_logger.info(
            "[GET] (%s) - %s",
            response.status_code,
            full_url,
            extra={"response": response},
        )
        if response.status_code != 404:
            response.raise_for_status()
        return response

    def post(
        self,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, dict[str, Any] | Any] | None = None,
        data: bytes | str | None = None,
    ) -> requests.Response:
        full_url = f"{self.url}{path}"
        response: requests.Response = requests.post(
            full_url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            auth=self.auth,
            timeout=TIMEOUT,
            verify=self.verifytls,
        )
        gs_logger.info(
            "[POST] (%s) - %s",
            response.status_code,
            full_url,
            extra={"response": response},
        )
        if response.status_code != 409:
            response.raise_for_status()
        return response

    def put(
        self,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, dict[str, Any] | Any] | None = None,
        data: bytes | str | None = None,
    ) -> requests.Response:
        full_url = f"{self.url}{path}"
        response: requests.Response = requests.put(
            full_url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            auth=self.auth,
            timeout=TIMEOUT,
            verify=self.verifytls,
        )
        gs_logger.info(
            "[PUT] (%s) - %s",
            response.status_code,
            full_url,
            extra={"response": response},
        )
        response.raise_for_status()
        return response

    def delete(
        self,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        full_url = f"{self.url}{path}"
        response: requests.Response = requests.delete(
            full_url,
            params=params,
            headers=headers,
            auth=self.auth,
            timeout=TIMEOUT,
            verify=self.verifytls,
        )
        gs_logger.info(
            "[DELETE] (%s) - %s",
            response.status_code,
            full_url,
            extra={"response": response},
        )
        if response.status_code != 404:
            response.raise_for_status()
        return response
