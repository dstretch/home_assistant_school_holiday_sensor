import os
import yaml
import urllib.parse

from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_COUNTRY, CONF_REGION, CONF_HOLIDAYS, CONF_NAME

# First get country based on files in the holidays folder
def get_country_options():
    folder = os.path.join(os.path.dirname(__file__), "holidays")
    return sorted(f[:-5] for f in os.listdir(folder) if f.endswith(".yaml"))

def load_yaml(path):
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"YAML load failed: {e}")
        return []

# Then read file and get regions of that country file
def get_region_options(country):
    path = os.path.join(os.path.dirname(__file__), "holidays", f"{country}.yaml")
    regions_raw = load_yaml(path)
    regions = []

    for entry in regions_raw:
        if isinstance(entry, dict) and "name" in entry and "holidays" in entry:
            regions.append(entry["name"].strip())

    return sorted(regions)

# From the region file, get the holidays
def get_holiday_options(country, region):
    path = os.path.join(os.path.dirname(__file__), "holidays", f"{country}.yaml")
    regions_raw = load_yaml(path)

    for entry in regions_raw:
        if isinstance(entry, dict) and entry.get("name", "").strip() == region and "holidays" in entry:
            holidays = entry["holidays"]
            return [h["name"].strip() for h in holidays if "name" in h]

    return []

# Config flow
class SchoolHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.country = None
        self.region = None

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
            return self.async_create_entry(title=user_input.get(CONF_NAME, "School Holiday"), data={
                CONF_NAME: user_input.get(CONF_NAME, "School Holiday"),
                CONF_COUNTRY: self.country,
                CONF_REGION: self.region,
                CONF_HOLIDAYS: user_input[CONF_HOLIDAYS],
            })

        holidays = get_holiday_options(self.country, self.region)
        if not holidays:
            return self.async_abort(reason="no_holidays_found")

        schema = vol.Schema({
            vol.Optional(CONF_NAME, default="School Holiday"): str,
            vol.Required(CONF_HOLIDAYS): vol.All(cv.ensure_list, [vol.In(holidays)])
        })
        return self.async_show_form(step_id="holidays", data_schema=schema)
