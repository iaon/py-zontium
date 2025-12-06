from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional
from urllib import error, parse, request

from .config import ZontSettings


class ZontAPIError(RuntimeError):
    """Raised when the ZONT API reports an error."""

    def __init__(self, status: int, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(f"API error {status}: {message}")
        self.status = status
        self.payload = payload or {}


class ZontClient:
    """HTTP client for the ZONT API.

    The client exposes convenience helpers for common API calls while still
    allowing fully custom requests for endpoints not yet wrapped.
    """

    def __init__(self, settings: ZontSettings):
        self.settings = settings

    def _make_url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        base = self.settings.base_url.rstrip("/")
        suffix = path.lstrip("/")
        url = f"{base}/{suffix}"
        if params:
            url = f"{url}?{parse.urlencode(params)}"
        return url

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data_bytes = None
        headers = self.settings.headers
        if json_payload is not None:
            data_bytes = json.dumps(json_payload).encode("utf-8")

        req = request.Request(
            self._make_url(path, params),
            data=data_bytes,
            method=method.upper(),
            headers=headers,
        )

        try:
            with request.urlopen(req, timeout=self.settings.timeout) as response:
                content = response.read().decode("utf-8")
                status = getattr(response, "status", response.getcode())
        except error.HTTPError as exc:
            status = exc.code
            body = exc.read().decode("utf-8") if hasattr(exc, "read") else str(exc)
            try:
                details = json.loads(body)
                message = details.get("message") or body
            except Exception:
                details = None
                message = body
            raise ZontAPIError(status, message, details)

        if not (200 <= status < 300):
            raise ZontAPIError(status, content)

        if not content:
            return {}
        try:
            return json.loads(content)
        except ValueError as exc:  # pragma: no cover - unexpected failure path
            raise ZontAPIError(status, "Invalid JSON in response") from exc

    # Convenience wrappers for common API methods
    def get_user(self) -> Dict[str, Any]:
        return self._request("GET", "user")

    def list_devices(self) -> Dict[str, Any]:
        return self._request("GET", "devices")

    def get_authtoken(self, login: str, password: str) -> Dict[str, Any]:
        """Request a fresh authentication token using login credentials."""

        payload = {"login": login, "password": password}
        return self._request("POST", "get_authtoken", json_payload=payload)

    def get_device(self, device_id: str) -> Dict[str, Any]:
        return self._request("GET", f"devices/{device_id}")

    def get_device_history(
        self,
        device_id: str,
        *,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
    ) -> Dict[str, Any]:
        params = {"from": from_ts, "to": to_ts}
        filtered_params = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", f"devices/{device_id}/history", params=filtered_params)

    def execute_action(self, device_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"devices/{device_id}/{action}", json_payload=payload)

    def call_raw(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an arbitrary API request.

        This helper ensures new API functions can be reached without waiting for
        the library to gain dedicated wrappers.
        """

        return self._request(method.upper(), path, params=params, json_payload=payload)

    def close(self) -> None:
        return None

    def __enter__(self) -> "ZontClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


__all__: Iterable[str] = ["ZontAPIError", "ZontClient"]
