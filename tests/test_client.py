import io
import json
from urllib import error
from unittest import mock

import pytest

from zontium.client import ZontAPIError, ZontClient
from zontium.config import ZontSettings


class DummyResponse:
    def __init__(self, payload: bytes, status: int = 200):
        self.payload = payload
        self.status = status

    def read(self) -> bytes:  # pragma: no cover - trivial
        return self.payload

    def getcode(self) -> int:  # pragma: no cover
        return self.status

    def __enter__(self):  # pragma: no cover - context support
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover
        return False


def mock_urlopen(return_value=None, side_effect=None):
    return mock.patch("zontium.client.request.urlopen", return_value=return_value, side_effect=side_effect)


@pytest.fixture
def client():
    settings = ZontSettings(base_url="https://example.com/api", token="abc")
    with ZontClient(settings) as c:
        yield c


def test_get_user_success(client):
    response = DummyResponse(b'{"id": 1, "email": "user@example.com"}')
    with mock_urlopen(response):
        data = client.get_user()
    assert data["email"] == "user@example.com"


def test_error_response_raises(client):
    http_error = error.HTTPError(
        "https://example.com/api/devices",
        401,
        "Unauthorized",
        hdrs=None,
        fp=io.BytesIO(b'{"message":"Unauthorized"}'),
    )
    with mock_urlopen(side_effect=http_error), pytest.raises(ZontAPIError) as exc:
        client.list_devices()
    assert exc.value.status == 401
    assert "Unauthorized" in str(exc.value)


def test_execute_action(client):
    response = DummyResponse(b'{"status": "ok", "device": "1"}')
    with mock_urlopen(response):
        payload = client.execute_action("1", "reboot", {"force": True})
    assert payload["status"] == "ok"


def test_get_authtoken(client):
    response = DummyResponse(b'{"authtoken": "secret-token"}')
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["request"] = req
        return response

    with mock_urlopen(side_effect=fake_urlopen):
        payload = client.get_authtoken("user", "password", client_name="Cool app")

    assert payload["authtoken"] == "secret-token"
    sent_headers = captured["request"].headers
    assert sent_headers.get("Authorization") == "Basic dXNlcjpwYXNzd29yZA=="
    assert "Bearer" not in sent_headers.get("Authorization", "")
    assert json.loads(captured["request"].data.decode("utf-8")) == {"client_name": "Cool app"}


def test_call_raw_with_params(client):
    response = DummyResponse(b'{"hello": "world"}')
    with mock_urlopen(response):
        result = client.call_raw("get", "custom/path", params={"a": 1})
    assert result == {"hello": "world"}


def test_verbose_request_logging(capsys):
    settings = ZontSettings(base_url="https://example.com/api", token="secret", verbose=True)
    response = DummyResponse(b"{}")
    with ZontClient(settings) as client:
        with mock_urlopen(response):
            client.get_user()

    output = capsys.readouterr().err
    assert "GET https://example.com/api/user" in output
    assert "Authorization" in output
    assert "secret" not in output  # redacted
