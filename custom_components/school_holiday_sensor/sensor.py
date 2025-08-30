# custom_components/school_holiday/sensor.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    CONF_COUNTRY,
    CONF_REGION,
    CONF_HOLIDAYS,
    CONF_NAME,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=6)  # holiday windows change slowly

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up School Holiday sensor from a config entry."""
    country: str = entry.data.get(CONF_COUNTRY)
    region: str | None = entry.data.get(CONF_REGION)
    selected_holidays: list[str] = entry.data.get(CONF_HOLIDAYS, [])
    friendly_name: str = entry.data.get(CONF_NAME, "School Holiday")

    # You likely already have a YAML loader in config_flow.py.
    # Reuse/import a helper here (or duplicate carefully) to get the *date ranges*.
    # Expected structure per holiday (example):
    #   {"name": "Summer", "start": "2025-07-12", "end": "2025-08-25"}
    from .config_flow import load_yaml  # reuse safely
    import os

    holidays_path = os.path.join(os.path.dirname(__file__), "holidays", f"{country}.yaml")
    regions_raw = load_yaml(holidays_path)

    # Extract only the selected region and only the user-selected holiday names.
    def _collect_selected_ranges() -> list[dict[str, Any]]:
        ranges: list[dict[str, Any]] = []
        for entry_region in regions_raw or []:
            if not isinstance(entry_region, dict):
                continue
            if entry_region.get("name", "").strip() != (region or "").strip():
                continue
            for h in entry_region.get("holidays", []):
                if not isinstance(h, dict):
                    continue
                name = h.get("name")
                if name and name.strip() in selected_holidays:
                    # Parse start/end as dates; keep naive date in UTC.
                    start_s = h.get("start")
                    end_s = h.get("end")
                    if not start_s or not end_s:
                        continue
                    try:
                        start_d = datetime.fromisoformat(start_s).date()
                        end_d = datetime.fromisoformat(end_s).date()
                    except Exception as exc:
                        _LOGG_
