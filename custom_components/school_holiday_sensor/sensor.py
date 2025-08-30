from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Optional, Dict, List

import voluptuous as vol
from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    CONF_COUNTRY,
    CONF_REGION,
    CONF_HOLIDAYS,
    CONF_NAME,
)

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(hours=6)

# Permissive platform schema to avoid 'extra keys not allowed' if someone added YAML.
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({}, extra=vol.ALLOW_EXTRA)

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Guard against YAML platform setup. We only support config flow."""
    _LOGGER.error(
        "School Holiday Sensor must be set up via the UI (config flow). "
        "Please remove any YAML under 'sensor: - platform: school_holiday'. "
        "Proceed to Settings → Devices & Services → Add Integration."
    )
    # Do nothing else.

def _parse_date(s: Optional[str]):
    """Parse either YYYY-MM-DD (preferred) or DD-MM-YYYY into a date."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    country: str = entry.data.get(CONF_COUNTRY)
    region: Optional[str] = entry.data.get(CONF_REGION)
    selected_holidays: List[str] = entry.data.get(CONF_HOLIDAYS, [])
    friendly_name: str = entry.data.get(CONF_NAME, "School Holiday")

    from .config_flow import load_yaml  # reuse helper
    import os

    holidays_path = os.path.join(os.path.dirname(__file__), "holidays", f"{country}.yaml")
    regions_raw = load_yaml(holidays_path) or []

    target_region = (region or "").strip()

    def _collect_selected_ranges() -> List[Dict[str, Any]]:
        ranges: List[Dict[str, Any]] = []
        for entry_region in regions_raw:
            if not isinstance(entry_region, dict):
                continue
            if entry_region.get("name", "").strip() != target_region:
                continue

            for h in entry_region.get("holidays", []):
                if not isinstance(h, dict):
                    continue
                name = str(h.get("name", "")).strip()
                if not name:
                    continue
                if selected_holidays and name not in selected_holidays:
                    continue

                start_d = _parse_date(h.get("start"))
                end_d = _parse_date(h.get("end"))
                if not start_d or not end_d:
                    _LOGGER.warning("Skipping holiday %r due to invalid dates: start=%r end=%r", name, h.get("start"), h.get("end"))
                    continue

                ranges.append({"name": name, "start": start_d, "end": end_d})
        return ranges

    async def _async_update_data() -> Dict[str, Any]:
        today = datetime.now(timezone.utc).date()
        ranges = _collect_selected_ranges()

        current = next((r for r in ranges if r["start"] <= today <= r["end"]), None)
        future = sorted((r for r in ranges if r["start"] > today), key=lambda r: r["start"]) if ranges else []
        next_h = future[0] if future else None

        return {
            "on_holiday": current is not None,
            "current_holiday": current["name"] if current else None,
            "current_start": current["start"].isoformat() if current else None,
            "current_end": current["end"].isoformat() if current else None,
            "next_holiday": next_h["name"] if next_h else None,
            "next_start": next_h["start"].isoformat() if next_h else None,
            "next_end": next_h["end"].isoformat() if next_h else None,
            "region": region,
            "country": country,
            "selected_holidays": selected_holidays,
            "ranges_count": len(ranges),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    coordinator = DataUpdateCoordinator[Dict[str, Any]](
        hass,
        _LOGGER,
        name=f"{DOMAIN} coordinator {country}/{region}",
        update_method=_async_update_data,
        update_interval=UPDATE_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        SchoolHolidaySensor(
            coordinator=coordinator,
            name=friendly_name,
            unique_id=f"{entry.entry_id}_holiday_status",
            entry_id=entry.entry_id,
        )
    ], update_before_add=False)

class SchoolHolidaySensor(CoordinatorEntity[DataUpdateCoordinator[Dict[str, Any]]], SensorEntity):
    _attr_icon = "mdi:school"
    _attr_native_unit_of_measurement = None

    def __init__(self, coordinator, name: str, unique_id: str, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._entry_id = entry_id

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data or {}
        return data.get("on_holiday", False)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "current_holiday": data.get("current_holiday"),
            "current_start": data.get("current_start"),
            "current_end": data.get("current_end"),
            "next_holiday": data.get("next_holiday"),
            "next_start": data.get("next_start"),
            "next_end": data.get("next_end"),
            "country": data.get("country"),
            "region": data.get("region"),
            "selected_holidays": data.get("selected_holidays"),
            "ranges_count": data.get("ranges_count"),
            "last_updated": data.get("last_updated"),
        }

    @property
    def device_info(self) -> Dict[str, Any]:
        data = self.coordinator.data or {}
        country = data.get("country")
        region = data.get("region")
        return {
            "identifiers": {(DOMAIN, f"{self._entry_id}")},
            "name": f"School Holidays ({country}/{region})",
            "manufacturer": "Community",
            "model": "School Holiday Sensor",
        }
