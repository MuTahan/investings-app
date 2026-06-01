from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.base import utcnow
from app.db.models.device import Device
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository):
    async def upsert(self, user_id: uuid.UUID, device_token: str, platform: str = "ios") -> Device:
        stmt = select(Device).where(Device.user_id == user_id, Device.device_token == device_token)
        device = (await self.session.execute(stmt)).scalar_one_or_none()
        if device is None:
            device = Device(user_id=user_id, device_token=device_token, platform=platform)
            self.session.add(device)
        else:
            device.is_valid = True
            device.last_seen_at = utcnow()
        await self.session.flush()
        return device

    async def list_valid(self, user_id: uuid.UUID) -> list[Device]:
        stmt = select(Device).where(Device.user_id == user_id, Device.is_valid.is_(True))
        return list((await self.session.execute(stmt)).scalars().all())

    async def deactivate(self, user_id: uuid.UUID, device_token: str) -> bool:
        stmt = select(Device).where(Device.user_id == user_id, Device.device_token == device_token)
        device = (await self.session.execute(stmt)).scalar_one_or_none()
        if device is None:
            return False
        device.is_valid = False
        await self.session.flush()
        return True
