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
    setting = AppSetting(llm_enabled=False, llm_base_url="", llm_model="")
    repository.add(setting)
    repository.save_changes()
    return setting
