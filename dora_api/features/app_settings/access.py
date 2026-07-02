"""Accessor for the single AppSetting row.

Used by the get/update endpoints (admin UI) and read server-side by the
assistant. Get-or-create means the install works before anyone visits Settings.
"""
from dora_api.domain.entities.app_setting import AppSetting
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


def get_or_create_app_setting(repository: SqlAlchemyRepository) -> AppSetting:
    existing = repository.get(AppSetting).all()
    if existing:
        return existing[0]
    # FU-153: install-wide LLM URL/model/enabled fields moved to the User
    # row (per-user); only the master kill-switch lives here now (defaults
    # to True so a fresh install allows users to opt in to AI mode
    # individually).
    setting = AppSetting(
        master_llm_enabled=True, scanning_enabled=False,
        buy_verdict_enabled=True,
    )
    repository.add(setting)
    repository.save_changes()
    return setting
