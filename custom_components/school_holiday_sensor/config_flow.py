
import os
import yaml
from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

CONF_COUNTRY = "country"
CONF_REGION = "region"
CONF_HOLIDAYS = "holidays"
CONF_NAME = "name"

def get_country_options():
    folder = os.path.join(os.path.dirname(__file__), "holidays")
    return sorted(f[:-5] for f in os.listdir(folder) if f.endswith(".yaml"))

def get_region_options(country):
    path = os.path.join(os.path.dirname(__file__), "holidays", f"{country}.yaml")
    try:
        with open(path, "r") as f:
            return [r["name"] for r in yaml.safe_load(f)]
    except:
        return []

def get_holiday_options(country, region):
    path = os.path.join(os.path.dirname(__file__), "holidays", f"{country}.yaml")
    try:
        with open(path, "r") as f:
            regions = yaml.safe_load(f)
            for r in regions:
                if r["name"] == region:
                    return [h["name"] for h in r["holidays"]]
    except:
        return []

class SchoolHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.country = None
        self.region = None

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.country = user_input[CONF_COUNTRY]
            return await self.async_step_region()

        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required(CONF_COUNTRY): vol.In(get_country_options())
        }))

    async def async_step_region(self, user_input=None):
        if user_input is not None:
            self.region = user_input[CONF_REGION]
            return await self.async_step_holidays()

        return self.async_show_form(step_id="region", data_schema=vol.Schema({
            vol.Required(CONF_REGION): vol.In(get_region_options(self.country))
        }))

    async def async_step_holidays(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input.get(CONF_NAME, "School Holiday"), data={
                CONF_NAME: user_input.get(CONF_NAME, "School Holiday"),
                CONF_COUNTRY: self.country,
                CONF_REGION: self.region,
                CONF_HOLIDAYS: user_input[CONF_HOLIDAYS],
            })

        return self.async_show_form(step_id="holidays", data_schema=vol.Schema({
            vol.Optional(CONF_NAME, default="School Holiday"): str,
            vol.Required(CONF_HOLIDAYS): vol.All(cv.ensure_list, [vol.In(get_holiday_options(self.country, self.region))])
        }))
