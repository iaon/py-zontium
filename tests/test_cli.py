import json
from pathlib import Path
from unittest import mock

from zontium.cli import main


class DummyResponse:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.status = 200

    def read(self) -> bytes:  # pragma: no cover - trivial
        return self.payload

    def __enter__(self):  # pragma: no cover
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover
        return False

    def getcode(self):  # pragma: no cover
        return self.status


def write_config(tmp_path: Path, token: str = "token") -> Path:
    config = tmp_path / "config.yaml"
    config.write_text(f"base_url: https://example.com/api\ntoken: {token}\ntimeout: 5", encoding="utf-8")
    return config


def test_cli_devices(tmp_path: Path, capsys):
    config = write_config(tmp_path)
    response = DummyResponse(b'{"items": [{"id": "1"}]}')
    with mock.patch("zontium.client.request.urlopen", return_value=response):
        exit_code = main(["--config", str(config), "devices"])

    assert exit_code == 0
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert payload["items"][0]["id"] == "1"


def test_cli_request_with_payload(tmp_path: Path, capsys):
    config = write_config(tmp_path)
    response = DummyResponse(b'{"status": "ok"}')
    with mock.patch("zontium.client.request.urlopen", return_value=response):
        exit_code = main(
            [
                "--config",
                str(config),
                "request",
                "POST",
                "devices/1/reboot",
                "--payload",
                "{\"force\": true}",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
