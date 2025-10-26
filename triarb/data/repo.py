from __future__ import annotations

from typing import Sequence

from sqlalchemy import select

from triarb.data.db import SessionLocal
from triarb.data.models import OpportunityModel, TradeModel


class Repository:
    async def record_opportunity(self, triangle_hash: str, gross: float, net: float, notional: float) -> int:
        async with SessionLocal() as session:
            model = OpportunityModel(
                triangle_hash=triangle_hash,
                gross_bps=gross,
                net_bps=net,
                notional_quote=notional,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return model.id

    async def record_trade(self, opportunity_id: int, details: dict, pnl_quote: float) -> int:
        async with SessionLocal() as session:
            trade = TradeModel(opportunity_id=opportunity_id, details=details, pnl_quote=pnl_quote)
            session.add(trade)
            await session.commit()
            await session.refresh(trade)
            return trade.id

    async def recent_trades(self, limit: int = 50) -> Sequence[TradeModel]:
        async with SessionLocal() as session:
            result = await session.execute(select(TradeModel).order_by(TradeModel.id.desc()).limit(limit))
            return result.scalars().all()
