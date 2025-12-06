from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "zontium" / "config.yaml"


@dataclass
class ZontSettings:
    """Settings for connecting to the ZONT API."""

    base_url: str = "https://zont-online.ru/api"
    token: str = ""
    timeout: float = 10.0

    @property
    def headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


def _parse_simple_yaml(raw: str) -> Dict[str, Any]:
    """Parse a minimal YAML subset (key: value pairs)."""

    data: Dict[str, Any] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError("Invalid line in YAML content")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if value.lower() in {"true", "false"}:
            parsed: Any = value.lower() == "true"
        else:
            try:
                parsed = int(value)
            except ValueError:
                try:
                    parsed = float(value)
                except ValueError:
                    parsed = value
        data[key] = parsed
    return data


def _load_content(raw: str) -> Dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _parse_simple_yaml(raw)


def load_settings(path: Path | str | None = None) -> ZontSettings:
    """Load settings from a configuration file.

    Parameters
    ----------
    path:
        Optional custom path. If omitted, the default user configuration
        location ``~/.config/zontium/config.yaml`` is used.
    """

    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    raw = config_path.read_text(encoding="utf-8")
    content: Dict[str, Any] = _load_content(raw) if raw.strip() else {}

    if not isinstance(content, dict):
        raise ValueError("Configuration file must describe a mapping")

    return ZontSettings(
        base_url=str(content.get("base_url", ZontSettings.base_url)),
        token=str(content.get("token", "")),
        timeout=float(content.get("timeout", ZontSettings.timeout)),
    )


__all__ = ["ZontSettings", "load_settings", "DEFAULT_CONFIG_PATH"]
