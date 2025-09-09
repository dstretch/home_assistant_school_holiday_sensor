"""Config flow for the Home Assistant School Holiday Sensor."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .school_holiday_api import SchoolHolidayAPI

_LOGGER = logging.getLogger(__name__)

class SchoolHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.data = {}
        self.api = SchoolHolidayAPI()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.data = user_input
            return await self.async_step_region()

        countries = await self.hass.async_add_executor_job(self.api.get_countries)
        if not countries:
            return self.async_abort(reason="no_countries_found")

        schema = vol.Schema({
            vol.Required("country"): vol.In(sorted(list(countries.keys())))
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_region(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.data.update(user_input)
            return self.async_create_entry(
                title=f"{self.data['country']} - {self.data['region']}",
                data=self.data
            )

        country = self.data.get("country")
        regions = await self.hass.async_add_executor_job(self.api.get_regions, country)
        if not regions:
            return self.async_abort(reason="no_regions_found")

        schema = vol.Schema({
            vol.Required("region"): vol.In(sorted(list(regions.keys())))
        })
        return self.async_show_form(step_id="region", data_schema=schema, errors=errors)
