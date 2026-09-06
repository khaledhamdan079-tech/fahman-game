from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import Settings
from app.core.errors import AppError


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    subject: str
    email: str
    display_name: str
    avatar_url: str | None


class GoogleTokenVerifier(Protocol):
    def verify(self, token: str) -> GoogleIdentity: ...


class DefaultGoogleTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._client_ids = set(settings.google_client_ids)
        self._request = google_requests.Request()

    def verify(self, token: str) -> GoogleIdentity:
        if not self._client_ids:
            raise AppError(
                "GOOGLE_AUTH_NOT_CONFIGURED",
                "Google authentication is not configured",
                status_code=503,
            )

        try:
            claims = google_id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                token,
                self._request,
            )
        except ValueError as exc:
            raise AppError(
                "AUTH_GOOGLE_TOKEN_INVALID",
                "The Google identity token is invalid",
                status_code=401,
            ) from exc

        if claims.get("aud") not in self._client_ids:
            raise AppError(
                "AUTH_GOOGLE_AUDIENCE_INVALID",
                "The Google identity token was issued for another application",
                status_code=401,
            )
        if claims.get("email_verified") is not True:
            raise AppError(
                "AUTH_GOOGLE_EMAIL_UNVERIFIED",
                "The Google account email is not verified",
                status_code=401,
            )

        subject = claims.get("sub")
        email = claims.get("email")
        if not isinstance(subject, str) or not isinstance(email, str):
            raise AppError(
                "AUTH_GOOGLE_CLAIMS_INVALID",
                "Required Google identity claims are missing",
                status_code=401,
            )

        name = claims.get("name")
        picture = claims.get("picture")
        return GoogleIdentity(
            subject=subject,
            email=email,
            display_name=name if isinstance(name, str) and name else email.split("@", 1)[0],
            avatar_url=picture if isinstance(picture, str) else None,
        )
