from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # noqa: S104 - container must accept Railway traffic
        port=port,
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
