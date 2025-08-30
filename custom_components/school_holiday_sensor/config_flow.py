import os
import yaml

from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_COUNTRY, CONF_REGION, CONF_HOLIDAYS, CONF_NAME

# Find countries from files in holidays folder
def get_country_options():
    folder = os.path.join(os.path.dirname(__file__), "holidays")
    return sorted(f[:-5] for f in os.listdir(folder) if f.endswith(".yaml"))

def load_yaml(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return []

# Regions in the selected country file
def get_region_options(country):
    path = os.path.join(os.path.dirname(__file__), "holidays", f"{country}.yaml")
    regions_raw = load_yaml(path) or []
    regions: list[str] = []

    for entry in regions_raw:
        if isinstance(entry, dict) and "name" in entry and "holidays" in entry:
            regions.append(str(entry["name"]).strip())

    return sorted(regions)

# Holidays names for the selected region
def get_holiday_options(country, region):
    path = os.path.join(os.path.dirname(__file__), "holidays", f"{country}.yaml")
    regions_raw = load_yaml(path) or []

    for entry in regions_raw:
        if isinstance(entry, dict) and entry.get("name", "").strip() == region and "holidays" in entry:
            holidays = entry["holidays"]
            return [str(h.get("name", "")).strip() for h in holidays if isinstance(h, dict) and "name" in h]

    return []

class SchoolHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""
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
                }
            )

        holidays = get_holiday_options(self.country, self.region)
        if not holidays:
            return self.async_abort(reason="no_holidays_found")

        schema = vol.Schema({
            vol.Optional(CONF_NAME, default="School Holiday"): cv.string,
            vol.Required(CONF_HOLIDAYS): vol.All(cv.ensure_list, [vol.In(holidays)]),
        })
        return self.async_show_form(step_id="holidays", data_schema=schema)
