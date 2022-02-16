"""The MagicMirror integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
    Platform,
)
from homeassistant.helpers import discovery
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import MagicMirrorApiClient
from .const import ATTR_CONFIG_ENTRY_ID, DATA_HASS_CONFIG, DOMAIN, LOGGER, PLATFORMS
from .coordinator import MagicMirrorDataUpdateCoordinator
from .services import async_unload_services, async_register_services


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the MagicMirror component."""

    hass.data[DATA_HASS_CONFIG] = config
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MagicMirror from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    api = MagicMirrorApiClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        api_key=entry.data[CONF_API_KEY],
        session=async_get_clientsession(hass),
    )

    coordinator = MagicMirrorDataUpdateCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    await async_setup_notify(hass, entry)

    await async_register_services(hass, api)

    return True


async def async_setup_notify(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup notify platform."""
    # set up notify platform, no entry support for notify component yet,
    # have to use discovery to load platform.
    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {
                CONF_NAME: DOMAIN,
                ATTR_CONFIG_ENTRY_ID: entry.entry_id,
            },
            hass.data[DATA_HASS_CONFIG],
        )
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    await async_unload_services(hass)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
