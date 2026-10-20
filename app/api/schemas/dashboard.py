from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    """
    Real-time operational metrics queried from PostgreSQL for the desktop dashboard.
    """
    total_medicines: int
    active_medicines: int
    total_categories: int
    total_batches: int
    total_stock_units: int
    low_stock_medicines: int
    expiring_soon_batches: int  # Expiring within 30 days
    expired_batches: int
