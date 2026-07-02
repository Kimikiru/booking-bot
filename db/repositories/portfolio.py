"""Репозиторий портфолио — доступ к таблице portfolio_items."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import PortfolioItem


class PortfolioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count_active(self) -> int:
        result = await self.session.execute(
            select(func.count(PortfolioItem.id)).where(PortfolioItem.is_active.is_(True))
        )
        return int(result.scalar_one())

    async def get_by_offset(self, offset: int) -> PortfolioItem | None:
        """Элемент по порядковому номеру (0-based) среди активных."""
        result = await self.session.execute(
            select(PortfolioItem)
            .where(PortfolioItem.is_active.is_(True))
            .order_by(PortfolioItem.position, PortfolioItem.id)
            .offset(offset)
            .limit(1)
        )
        return result.scalars().first()

    async def add(
        self, file_id: str, caption: str | None, position: int = 0
    ) -> PortfolioItem:
        item = PortfolioItem(file_id=file_id, caption=caption, position=position)
        self.session.add(item)
        await self.session.flush()
        return item
