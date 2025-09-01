"""Config flow for the Home Assistant School Holiday Sensor."""
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .school_holiday_api import SchoolHolidayAPI

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input."""
    # This function is not strictly needed for this simple example,
    # but it's good practice for complex validations.
    return {"title": f"School Holidays ({data['country']}-{data['region']})"}

class SchoolHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the school holiday sensor."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}
        self.api = SchoolHolidayAPI()

    async def async_step_user(self, user_input=None):
        """Handle the initial step of a user-initiated config flow."""
        errors = {}

        if user_input is not None:
            self.data = user_input
            return await self.async_step_region()

        countries = await self.hass.async_add_executor_job(self.api.get_countries)
        
        schema = vol.Schema({
            vol.Required("country"): vol.In(sorted(list(countries.keys()))),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )

    async def async_step_region(self, user_input=None):
        """Handle the region selection step."""
        errors = {}

        if user_input is not None:
            self.data.update(user_input)
            
            # Use the data to create a config entry.
            info = await validate_input(self.hass, self.data)
            
            return self.async_create_entry(
                title=info["title"],
                data=self.data
            )
        
        country = self.data.get("country")
        regions = await self.hass.async_add_executor_job(
            self.api.get_regions, country
        )

        schema = vol.Schema({
            vol.Required("region"): vol.In(sorted(list(regions.keys()))),
        })

        return self.async_show_form(
            step_id="region",
            data_schema=schema,
            errors=errors
        )
