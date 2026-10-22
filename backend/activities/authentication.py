import jwt

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import AuthenticationFailed


class AccessTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()

        if not parts:
            return None

        if parts[0].lower() != b"bearer" or len(parts) != 2:
            raise AuthenticationFailed(
                "Usá Authorization: Bearer <access_token>.",
                code="invalid_authorization_header",
            )

        try:
            payload = jwt.decode(
                parts[1],
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                options={"require": ["sub", "type", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed(
                "El access token venció.",
                code="token_expired",
            )
        except jwt.InvalidTokenError:
            raise AuthenticationFailed(
                "El token no es válido.",
                code="invalid_token",
            )

        if payload["type"] != "access":
            raise AuthenticationFailed(
                "Se requiere un access token.",
                code="invalid_token_type",
            )

        User = get_user_model()

        try:
            user = User.objects.get(
                pk=payload["sub"],
                is_active=True,
            )
        except (
            User.DoesNotExist,
            ValueError,
            TypeError,
            OverflowError,
            ValidationError,
        ):
            raise AuthenticationFailed(
                "El usuario no existe o está inactivo.",
                code="invalid_user",
            )

        return user, payload

    def authenticate_header(self, request):
        return "Bearer"

    def decode_refresh_token(self, token):

        if not token:
            raise AuthenticationFailed(
                "Falta la cookie refresh_token.",
                code="refresh_missing",
            )

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                options={"require": ["sub", "type", "jti", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed(
                "El refresh token venció.",
                code="refresh_expired",
            )
        except jwt.InvalidTokenError:
            raise AuthenticationFailed(
                "El refresh token no es válido.",
                code="invalid_refresh",
            )

        if payload["type"] != "refresh":
            raise AuthenticationFailed(
                "Se requiere un refresh token.",
                code="invalid_token_type",
            )

        jti = payload["jti"]
        if not isinstance(jti, str) or not 1 <= len(jti) <= 36:
            raise AuthenticationFailed(
                "El identificador del refresh token no es válido.",
                code="invalid_refresh",
            )

        return payload