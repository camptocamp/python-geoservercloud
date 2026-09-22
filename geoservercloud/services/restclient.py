import re
from typing import Any

import requests

from .restlogger import gs_logger

TIMEOUT = 120

# Depending on the order of the jars in WEB-INF/lib, vanilla GeoServer answers these
# GWC "not found" errors with 500 instead of 404, keeping GWC's message as the
# text/plain body.
GWC_NOT_FOUND_MESSAGE = re.compile(
    r'Unknown layer: .+|Failed to get GridSet\. A GridSet with name ".+" does not exist\.'
)


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
        gs_logger.debug("Doing GET request to: %s", full_url)
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
        self.restore_gwc_not_found_status(response)
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
        self.log_payload("POST", json, data)
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
        self.log_payload("PUT", json, data)
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
        self.restore_gwc_not_found_status(response)
        if response.status_code != 404:
            response.raise_for_status()
        return response

    def restore_gwc_not_found_status(self, response: requests.Response) -> None:
        if response.status_code != 500:
            return
        if not GWC_NOT_FOUND_MESSAGE.fullmatch(response.text.strip()):
            return
        gs_logger.warning(
            "GeoServer answered a GWC not found error with 500, treating it as 404: %s",
            response.url,
        )
        response.status_code = 404

    def log_payload(
        self, method: str, json: dict | None, data: bytes | str | None
    ) -> None:
        payload_string = None
        if json is not None:
            payload_string = str(json)
        elif data is not None:
            if isinstance(data, str):
                payload_string = data
            else:
                payload_string = f"<binary data, {len(data)} bytes>"
        gs_logger.debug("Doing %s request with payload: %s", method, payload_string)
