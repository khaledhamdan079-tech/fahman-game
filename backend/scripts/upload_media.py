from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request_json(
    url: str,
    *,
    method: str,
    admin_key: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Admin-Key": admin_key,
        },
    )
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - operator URL
            return dict(json.load(response))
    except HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"API request failed ({error.code}): {detail}") from error


def upload_file(url: str, path: Path, headers: dict[str, str]) -> None:
    request = Request(url, data=path.read_bytes(), method="PUT", headers=headers)
    try:
        with urlopen(request, timeout=300):  # noqa: S310 - signed storage URL
            return
    except HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"Storage upload failed ({error.code}): {detail}") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload a private question-media file and verify it with the Fahman API."
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--kind", required=True, choices=("image", "audio", "video"))
    parser.add_argument("--mime")
    parser.add_argument("--duration-ms", type=int)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("FAHMAN_API_BASE_URL", "http://localhost:8000/v1"),
    )
    parser.add_argument("--admin-key", default=os.getenv("ADMIN_API_KEY"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path: Path = args.path.resolve()
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    if not args.admin_key:
        print("Set ADMIN_API_KEY or pass --admin-key.", file=sys.stderr)
        return 2
    mime_type = args.mime or mimetypes.guess_type(path.name)[0]
    if not mime_type:
        print("Could not detect MIME type; pass --mime.", file=sys.stderr)
        return 2
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = {
        "file_name": path.name,
        "kind": args.kind,
        "mime_type": mime_type,
        "size_bytes": path.stat().st_size,
        "checksum_sha256": checksum,
        "duration_ms": args.duration_ms,
        "width": args.width,
        "height": args.height,
    }
    base_url = args.api_base_url.rstrip("/")
    presigned = request_json(
        f"{base_url}/admin/media/presign-upload",
        method="POST",
        admin_key=args.admin_key,
        payload=payload,
    )
    upload_file(
        str(presigned["upload_url"]),
        path,
        {str(key): str(value) for key, value in presigned["required_headers"].items()},
    )
    completed = request_json(
        f"{base_url}/admin/media/{presigned['media_asset_id']}/complete",
        method="POST",
        admin_key=args.admin_key,
    )
    print(json.dumps(completed, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
