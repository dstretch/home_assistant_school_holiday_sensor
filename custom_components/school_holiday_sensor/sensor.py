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
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from typing import Any, Callable, Optional

from .const import (
    DOMAIN,
    CONF_COUNTRY,
    CONF_REGION,
    CONF_HOLIDAYS,
    CONF_NAME,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=6)  # holiday windows change slowly

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    # This function is called by Home Assistant when using config flow
    # The actual setup is handled by async_setup_entry
    pass

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up School Holiday sensor from a config entry."""
    country: str = entry.data.get(CONF_COUNTRY)
    region: str | None = entry.data.get(CONF_REGION)
    selected_holidays: list[str] = entry.data.get(CONF_HOLIDAYS, [])
    friendly_name: str = entry.data.get(CONF_NAME, "School Holiday")

    # Load holiday data from YAML files
    # Expected structure per holiday: {"name": "Summer", "start": "2025-07-12", "end": "2025-08-25"}
    from .config_flow import load_yaml
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
                        _LOGGER.warning("Skipping holiday %s due to bad dates: %s", name, exc)
                        continue
                    ranges.append({"name": name.strip(), "start": start_d, "end": end_d})
        return ranges

    async def _async_update_data() -> dict[str, Any]:
        """Compute whether today is within any selected holiday ranges."""
        today = datetime.now(timezone.utc).date()
        ranges = _collect_selected_ranges()

        current = None
        next_h = None

        # Find current holiday (today within [start, end])
        for r in ranges:
            if r["start"] <= today <= r["end"]:
                current = r
                break

        # Find next holiday by earliest start date in the future
        future = [r for r in ranges if r["start"] > today]
        if future:
            next_h = sorted(future, key=lambda r: r["start"])[0]

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

    coordinator = DataUpdateCoordinator[dict[str, Any]](
        hass,
        _LOGGER,
        name=f"{DOMAIN} coordinator {country}/{region}",
        update_method=_async_update_data,
        update_interval=UPDATE_INTERVAL,
    )

    # Prime data once before creating entities
    await coordinator.async_config_entry_first_refresh()

    entity = SchoolHolidaySensor(
        coordinator=coordinator,
        name=friendly_name,
        unique_id=f"{entry.entry_id}_holiday_status",
        entry_id=entry.entry_id,
    )
    async_add_entities([entity], update_before_add=False)


class SchoolHolidaySensor(CoordinatorEntity[DataUpdateCoordinator[dict[str, Any]]], SensorEntity):
    """Sensor that indicates whether today is a school holiday."""

    _attr_icon = "mdi:school"
    _attr_native_unit_of_measurement = None

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, Any]],
        name: str,
        unique_id: str,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._entry_id = entry_id

    @property
    def native_value(self) -> StateType:
        """Return True/False as state: whether today is a holiday."""
        data = self.coordinator.data or {}
        return data.get("on_holiday", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return rich attributes: current/next holiday info and selection context."""
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
    def device_info(self) -> dict[str, Any]:
        """Group under a single device in the registry."""
        data = self.coordinator.data or {}
        country = data.get("country")
        region = data.get("region")
        return {
            "identifiers": {(DOMAIN, f"{self._entry_id}")},
            "name": f"School Holidays ({country}/{region})",
            "manufacturer": "Community",
            "model": "School Holiday Sensor",
        }
