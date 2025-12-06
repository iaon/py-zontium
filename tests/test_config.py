from pathlib import Path

import pytest

from zontium.config import DEFAULT_CONFIG_PATH, ZontSettings, load_settings


def test_load_yaml_settings(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text("base_url: https://example.com\ntoken: abc\ntimeout: 5", encoding="utf-8")
    settings = load_settings(config)

    assert settings.base_url == "https://example.com"
    assert settings.token == "abc"
    assert settings.timeout == 5
    assert settings.headers["Authorization"] == "Bearer abc"
    assert settings.headers["X-ZONT-Client"] == "https://github.com/iaon/py-zontium"


def test_load_json_settings(tmp_path: Path):
    config = tmp_path / "config.json"
    config.write_text('{"base_url": "https://json.example", "token": "xyz", "timeout": 2}', encoding="utf-8")

    settings = load_settings(config)
    assert settings.base_url == "https://json.example"
    assert settings.timeout == 2
    assert settings.headers["Authorization"] == "Bearer xyz"
    assert settings.headers["X-ZONT-Client"] == "https://github.com/iaon/py-zontium"


def test_missing_config_raises(tmp_path: Path):
    missing = tmp_path / "absent.yaml"
    with pytest.raises(FileNotFoundError):
        load_settings(missing)


def test_defaults_used_when_not_provided(tmp_path: Path, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_text("{}", encoding="utf-8")

    settings = load_settings(config)
    assert settings.base_url == ZontSettings.base_url
    assert settings.timeout == ZontSettings.timeout
    assert settings.token == ""
    assert "Authorization" not in settings.headers
    assert settings.headers["X-ZONT-Client"] == "https://github.com/iaon/py-zontium"
