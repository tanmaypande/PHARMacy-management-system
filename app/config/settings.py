"""
Canonical configuration re-export module.
Delegates to app.core.config to ensure a single Pydantic Settings instance
across the entire application.
"""
from app.core.config import settings, Settings

__all__ = ["settings", "Settings"]
