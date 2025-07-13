
from homeassistant.components.binary_sensor import BinarySensorEntity
from datetime import datetime
import os
import yaml

from .const import DOMAIN

def parse_date(date_str):
    return datetime.strptime(date_str, "%d-%m-%Y").date()

async def async_setup_entry(hass, entry, async_add_entities):
    name = entry.data.get("name")
    country = entry.data.get("country")
    region = entry.data.get("region")
    holidays = entry.data.get("holidays")

    sensor = SchoolHolidaySensor(name, country, region, holidays)
    async_add_entities([sensor], update_before_add=True)

class SchoolHolidaySensor(BinarySensorEntity):
    def __init__(self, name, country, region, holidays):
        self._name = name or "School Holiday"
        self._country = country
        self._region = region
        self._holidays = holidays
        self._is_on = False
        self._attr_unique_id = f"{country}_{region}_school_holiday"

    def update(self):
        today = datetime.now().date()
        path = os.path.join(os.path.dirname(__file__), "holidays", f"{self._country}.yaml")
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        region_data = next((r for r in data if r["name"] == self._region), None)
        if not region_data:
            return

        for holiday in region_data.get("holidays", []):
            if holiday["name"] in self._holidays:
                start = parse_date(holiday["date_from"])
                end = parse_date(holiday["date_till"])
                if start <= today <= end:
                    self._is_on = True
                    return
        self._is_on = False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on
