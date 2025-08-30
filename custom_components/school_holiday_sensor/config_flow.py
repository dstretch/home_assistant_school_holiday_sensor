from __future__ import annotations

import os
import yaml

from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_COUNTRY, CONF_REGION, CONF_HOLIDAYS, CONF_NAME

def _holidays_folder() -> str:
    return os.path.join(os.path.dirname(__file__), "holidays")

def get_country_options() -> list[str]:
    folder = _holidays_folder()
    try:
        files = [f for f in os.listdir(folder) if f.endswith(".yaml")]
    except FileNotFoundError:
        return []
    return sorted(f[:-5] for f in files)

def load_yaml(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def get_region_options(country: str) -> list[str]:
    path = os.path.join(_holidays_folder(), f"{country}.yaml")
    regions_raw = load_yaml(path)
    regions: list[str] = []
    for entry in regions_raw:
        if isinstance(entry, dict) and "name" in entry and "holidays" in entry:
            regions.append(str(entry["name"]).strip())
    return sorted(regions)

def get_holiday_options(country: str, region: str) -> list[str]:
    path = os.path.join(_holidays_folder(), f"{country}.yaml")
    regions_raw = load_yaml(path)
    for entry in regions_raw:
        if isinstance(entry, dict) and entry.get("name", "").strip() == region and "holidays" in entry:
            return [str(h.get("name", "")).strip() for h in entry["holidays"] if isinstance(h, dict) and h.get("name")]
    return []

class SchoolHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.country: str | None = None
        self.region: str | None = None

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.country = user_input[CONF_COUNTRY]
            return await self.async_step_region()

        countries = get_country_options()
        if not countries:
            return self.async_abort(reason="no_countries_found")

        schema = vol.Schema({
            vol.Required(CONF_COUNTRY): vol.In(countries)
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_region(self, user_input=None):
        if user_input is not None:
            self.region = user_input[CONF_REGION]
            return await self.async_step_holidays()

        regions = get_region_options(self.country)
        if not regions:
            return self.async_abort(reason="invalid_yaml_file")

        schema = vol.Schema({
            vol.Required(CONF_REGION): vol.In(regions)
        })
        return self.async_show_form(step_id="region", data_schema=schema)

    async def async_step_holidays(self, user_input=None):
        if user_input is not None:
            title = f"{user_input.get(CONF_NAME, 'School Holiday')} ({self.country}/{self.region})"
            return self.async_create_entry(
                title=title,
                data={
                    CONF_NAME: user_input.get(CONF_NAME, "School Holiday"),
                    CONF_COUNTRY: self.country,
                    CONF_REGION: self.region,
                    CONF_HOLIDAYS: user_input[CONF_HOLIDAYS],
                },
            )

        holidays = get_holiday_options(self.country, self.region)
        if not holidays:
            return self.async_abort(reason="no_holidays_found")

        schema = vol.Schema({
            vol.Optional(CONF_NAME, default="School Holiday"): cv.string,
            vol.Required(CONF_HOLIDAYS): vol.All(cv.ensure_list, [vol.In(holidays)]),
        })
        return self.async_show_form(step_id="holidays", data_schema=schema)
