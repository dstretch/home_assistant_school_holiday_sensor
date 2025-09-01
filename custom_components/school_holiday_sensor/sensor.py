"""
Home Assistant sensor for school holidays.

This file provides the basic structure for the sensor entity. It retrieves
the configuration data from the config entry created by config_flow.py
and sets up the sensor accordingly.
"""

from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .school_holiday_api import SchoolHolidayAPI

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the school holiday sensor from a config entry."""
    country = config_entry.data.get("country")
    region = config_entry.data.get("region")

    if not country or not region:
        return

    api = SchoolHolidayAPI()
    async_add_entities([SchoolHolidaySensor(api, country, region)], True)


class SchoolHolidaySensor(Entity):
    """Representation of a school holiday sensor."""

    def __init__(self, api: SchoolHolidayAPI, country: str, region: str):
        """Initialize the sensor."""
        self._api = api
        self._country = country
        self._region = region
        self._state = None
        self._attributes = {}
        self._name = f"School Holidays ({country} - {region})"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    async def async_update(self):
        """Fetch the latest data from the API."""
        try:
            # You'll need to implement the async_get_holidays method in your API class.
            data = await self.hass.async_add_executor_job(
                self._api.get_holidays, self._country, self._region
            )

            # Update the state and attributes based on the fetched data.
            # This is a simplified example; you'll need to tailor this to your API's response.
            if data:
                self._state = data.get("current_holiday_status", "No school holiday")
                self._attributes = data
            else:
                self._state = "Unknown"
                self._attributes = {}

        except Exception as e:
            # Handle API call errors gracefully.
            self._state = "Error"
            _LOGGER.error("Error updating school holidays: %s", e)
