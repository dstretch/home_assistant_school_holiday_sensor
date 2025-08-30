"""The School Holiday Sensor integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required("name"): str,
        vol.Required("country"): str,
        vol.Required("region"): str,
        vol.Required("holidays"): vol.All(cv.ensure_list, [str])
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    """Set up the School Holiday Sensor component."""
    return True

async def async_setup_entry(hass, entry):
    """Set up School Holiday Sensor from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
