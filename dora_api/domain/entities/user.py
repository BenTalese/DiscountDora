from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


# Preference enum-like constants. Kept here so handlers and DTOs share one
# source of truth and the frontend can validate against these values too.
THEME_SYSTEM = "system"
THEME_LIGHT = "light"
THEME_DARK = "dark"
ALLOWED_THEMES = (THEME_SYSTEM, THEME_LIGHT, THEME_DARK)

FONT_FAMILY_DEFAULT = "default"
FONT_FAMILY_URBANIST = "urbanist"
FONT_FAMILY_NUNITO = "nunito"
ALLOWED_FONT_FAMILIES = (FONT_FAMILY_DEFAULT, FONT_FAMILY_URBANIST, FONT_FAMILY_NUNITO)

FONT_SIZE_SM = "sm"
FONT_SIZE_MD = "md"
FONT_SIZE_LG = "lg"
ALLOWED_FONT_SIZES = (FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG)


@dataclass
class User(BaseEntity):
    EMAIL = "email"
    email: str | None

    PASSWORD_HASH = "password_hash"
    password_hash: str | None

    SEND_DEALS_ON_DAY = "send_deals_on_day"
    send_deals_on_day: int

    USERNAME = "username"
    username: str

    DEALS_EMAIL_COMPACT = "deals_email_compact"
    deals_email_compact: bool = False

    DEALS_EMAIL_ENABLED = "deals_email_enabled"
    deals_email_enabled: bool = True

    FONT_FAMILY = "font_family"
    font_family: str = FONT_FAMILY_DEFAULT

    FONT_SIZE = "font_size"
    font_size: str = FONT_SIZE_MD

    IS_ADMIN = "is_admin"
    is_admin: bool = False

    THEME = "theme"
    theme: str = THEME_SYSTEM

    # TODO: avoid god object | separate auth credential from user profile

    # Opt-out flag so users can disable the weekly deals email without losing
    # their preferred send day; defaults to True so existing users keep
    # receiving emails unless they explicitly turn it off.
