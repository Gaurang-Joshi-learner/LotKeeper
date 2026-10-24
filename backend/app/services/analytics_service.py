"""Read-only reporting for the admin dashboard."""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.models import InventoryEvent, Vehicle, utcnow
from app.schemas import AnalyticsOut, CategoryStat, DayStat, LowStockItem
from app.services.base import BaseService


class AnalyticsService(BaseService):
    def summary(self, days: int = 14, low_stock_threshold: int = 2) -> AnalyticsOut:
        vehicles = list(self.db.scalars(select(Vehicle)))

        by_cat: dict[str, list[Decimal | int]] = defaultdict(lambda: [0, Decimal(0)])
        for v in vehicles:
            by_cat[v.category][0] += v.quantity
            by_cat[v.category][1] += v.price * v.quantity

        sold_units, revenue = self.db.execute(
            select(func.count(InventoryEvent.id), func.coalesce(func.sum(InventoryEvent.amount), 0)).where(
                InventoryEvent.type == "purchase"
            )
        ).one()

        today = utcnow().date()
        start = today - timedelta(days=days - 1)
        buckets = {start + timedelta(days=i): [0, Decimal(0)] for i in range(days)}
        recent = self.db.scalars(
            select(InventoryEvent).where(
                InventoryEvent.type == "purchase",
                InventoryEvent.created_at >= utcnow() - timedelta(days=days + 1),
            )
        )
        for e in recent:
            day = e.created_at.date()
            if day in buckets:
                buckets[day][0] += 1
                buckets[day][1] += e.amount or Decimal(0)

        return AnalyticsOut(
            vehicle_count=len(vehicles),
            units_in_stock=sum(v.quantity for v in vehicles),
            units_reserved=sum(v.reserved for v in vehicles),
            inventory_value=float(sum((v.price * v.quantity for v in vehicles), Decimal(0))),
            units_sold=int(sold_units),
            revenue=float(revenue or 0),
            by_category=sorted(
                (CategoryStat(category=c, units=int(u), value=float(val)) for c, (u, val) in by_cat.items()),
                key=lambda s: -s.value,
            ),
            purchases_by_day=[
                DayStat(date=d.isoformat(), purchases=n, revenue=float(r)) for d, (n, r) in sorted(buckets.items())
            ],
            low_stock=sorted(
                (
                    LowStockItem(id=v.id, label=v.label, available=v.available)
                    for v in vehicles
                    if v.available <= low_stock_threshold
                ),
                key=lambda i: i.available,
            ),
        )
