from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .client import ZontClient
from .config import DEFAULT_CONFIG_PATH, ZontSettings, load_settings


class CLIError(RuntimeError):
    pass


def _load_client(config: Optional[Path], verbose: bool) -> ZontClient:
    settings = load_settings(config)
    settings.verbose = verbose or settings.verbose
    return ZontClient(settings)


def _parse_json_option(value: Optional[str]):
    if value is None:
        return None
    return json.loads(value)


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI for the ZONT API")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to config file")
    parser.add_argument("--verbose", action="store_true", help="Print outgoing requests")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("show-config", help="Display loaded configuration")

    auth_parser = subparsers.add_parser("get-authtoken", help="Obtain token using login credentials")
    auth_parser.add_argument("login", help="User login")
    auth_parser.add_argument("password", help="User password")

    subparsers.add_parser("user", help="Fetch account information")

    subparsers.add_parser("devices", help="List devices")

    device_parser = subparsers.add_parser("device", help="Fetch a single device")
    device_parser.add_argument("device_id")

    history_parser = subparsers.add_parser("history", help="Fetch device history")
    history_parser.add_argument("device_id")
    history_parser.add_argument("--from", dest="from_ts", type=int, default=None, help="Start timestamp")
    history_parser.add_argument("--to", dest="to_ts", type=int, default=None, help="End timestamp")

    action_parser = subparsers.add_parser("action", help="Execute a device action")
    action_parser.add_argument("device_id")
    action_parser.add_argument("action")
    action_parser.add_argument("--payload", default="{}", help="JSON payload")

    request_parser = subparsers.add_parser("request", help="Perform arbitrary API request")
    request_parser.add_argument("method")
    request_parser.add_argument("endpoint")
    request_parser.add_argument("--params", default=None, help="JSON encoded query parameters")
    request_parser.add_argument("--payload", default=None, help="JSON encoded request body")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "get-authtoken":
            try:
                settings = load_settings(args.config)
            except FileNotFoundError:
                settings = ZontSettings()
            settings.verbose = args.verbose or settings.verbose
            with ZontClient(settings) as client:
                _print_json(client.get_authtoken(args.login, args.password))
            return 0

        with _load_client(args.config, args.verbose) as client:
            if args.command == "show-config":
                settings = load_settings(args.config)
                settings.verbose = args.verbose or settings.verbose
                summary = {
                    "config_path": str(args.config),
                    "base_url": settings.base_url,
                    "timeout": settings.timeout,
                    "verbose": settings.verbose,
                    "token_present": bool(settings.token),
                }
                _print_json(summary)
            elif args.command == "user":
                _print_json(client.get_user())
            elif args.command == "devices":
                _print_json(client.list_devices())
            elif args.command == "device":
                _print_json(client.get_device(args.device_id))
            elif args.command == "history":
                _print_json(
                    client.get_device_history(args.device_id, from_ts=args.from_ts, to_ts=args.to_ts)
                )
            elif args.command == "action":
                payload = _parse_json_option(args.payload) or {}
                _print_json(client.execute_action(args.device_id, args.action, payload))
            elif args.command == "request":
                params = _parse_json_option(args.params)
                payload = _parse_json_option(args.payload)
                _print_json(client.call_raw(args.method, args.endpoint, params=params, payload=payload))
            else:  # pragma: no cover - defensive fallback
                raise CLIError(f"Unknown command: {args.command}")
    except Exception as exc:  # pragma: no cover - runtime errors shown to user
        parser.error(str(exc))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
