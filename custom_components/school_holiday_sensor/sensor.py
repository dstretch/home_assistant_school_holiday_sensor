import logging
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_COUNTRY, CONF_REGION, CONF_NAME
from .school_holiday_api import SchoolHolidayAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    country = config_entry.data.get(CONF_COUNTRY)
    region = config_entry.data.get(CONF_REGION)
    name = config_entry.data.get(CONF_NAME, "School Holiday")
    if not country or not region:
        _LOGGER.error("Missing country or region in config entry")
        return
    api = SchoolHolidayAPI()
    async_add_entities([SchoolHolidaySensor(api, country, region, name)], True)

class SchoolHolidaySensor(Entity):
    def __init__(self, api: SchoolHolidayAPI, country: str, region: str, name: str):
        self._api = api
        self._country = country
        self._region = region
        self._name = name
        self._state = None
        self._attributes = {}
        self._unique_id = f"school_holiday_{country}_{region}".lower().replace(" ", "_")

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def should_poll(self):
        return True

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        try:
            data = await self.hass.async_add_executor_job(
                self._api.get_holidays, self._country, self._region
            )
            if data:
                self._state = data.get("current_holiday_status", False)
                self._attributes = data
            else:
                self._state = "Unknown"
                self._attributes = {}
        except Exception as e:
            self._state = "Error"
            self._attributes = {"error": str(e)}
            _LOGGER.exception("Error updating school holidays for %s - %s", self._country, self._region)
