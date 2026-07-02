"""Репозиторий услуг — единственная точка доступа к таблице services."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Service


class ServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[Service]:
        result = await self.session.execute(
            select(Service).where(Service.is_active.is_(True)).order_by(Service.id)
        )
        return list(result.scalars().all())

    async def get(self, service_id: int) -> Service | None:
        return await self.session.get(Service, service_id)

    async def add(self, title: str, duration_min: int, price: int | None) -> Service:
        service = Service(title=title, duration_min=duration_min, price=price)
        self.session.add(service)
        await self.session.flush()
        return service
