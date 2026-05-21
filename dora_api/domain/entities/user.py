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
    email: str | None
    password_hash: str | None
    send_deals_on_day: int
    username: str
    is_admin: bool = False
    # Opt-out flag so users can disable the weekly deals email without losing
    # their preferred send day; defaults to True so existing users keep
    # receiving emails unless they explicitly turn it off.
    deals_email_enabled: bool = True
    deals_email_compact: bool = False
    theme: str = THEME_SYSTEM
    font_family: str = FONT_FAMILY_DEFAULT
    font_size: str = FONT_SIZE_MD
    # TODO: avoid god object | separate auth credential from user profile

    class Fields(BaseEntity.Fields):
        EMAIL = "email"
        PASSWORD_HASH = "password_hash"
        SEND_DEALS_ON_DAY = "send_deals_on_day"
        USERNAME = "username"
        IS_ADMIN = "is_admin"
        DEALS_EMAIL_ENABLED = "deals_email_enabled"
        DEALS_EMAIL_COMPACT = "deals_email_compact"
        THEME = "theme"
        FONT_FAMILY = "font_family"
        FONT_SIZE = "font_size"
