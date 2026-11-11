from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.store_setting import StoreSetting


class StoreSettingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        setting = self.db.get(StoreSetting, key)
        return setting.value if setting else default

    def set_value(self, key: str, value: str) -> StoreSetting:
        setting = self.db.get(StoreSetting, key)
        if not setting:
            setting = StoreSetting(key=key, value=value)
            self.db.add(setting)
        else:
            setting.value = value
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def get_all(self) -> Dict[str, str]:
        stmt = select(StoreSetting)
        settings = self.db.scalars(stmt).all()
        return {s.key: s.value for s in settings}
