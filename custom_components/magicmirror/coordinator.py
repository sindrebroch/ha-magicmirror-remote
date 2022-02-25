"""The MagicMirror integration."""
from __future__ import annotations

import asyncio

from datetime import timedelta

from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout
import attr
from voluptuous.error import Error

from homeassistant.core import HomeAssistant

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MagicMirrorApiClient
from .const import DOMAIN, LOGGER
from .models import MagicMirrorData, ModuleResponse, MonitorResponse, QueryResponse


class MagicMirrorDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching MagicMirror data."""

    data: MagicMirrorData

    def __init__(
        self,
        hass: HomeAssistant,
        api: MagicMirrorApiClient,
    ) -> None:
        """Initialize."""

        self.api = api
        self._attr_device_info = DeviceInfo(
            name="MagicMirror",
            model="MagicMirror",
            manufacturer="MagicMirror",
            identifiers={(DOMAIN, "MagicMirror")},
            configuration_url=f"{api.base_url}/remote.html",
        )

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self) -> MagicMirrorData:
        """Update data via library."""

        try:
            async with timeout(10):
                req = await asyncio.gather(
                    self.api.update_available(),
                    self.api.monitor_status(),
                    self.api.get_brightness(),
                    self.api.get_modules(),
                )

                update: QueryResponse = req[0]
                monitor: MonitorResponse = req[1]
                brightness: QueryResponse = req[2]
                modules: ModuleResponse = req[3]

                if not monitor.success:
                    LOGGER.warning("Failed to fetch monitor-status for MagicMirror")
                if not update.success:
                    LOGGER.warning("Failed to fetch update-status for MagicMirror")
                if not brightness.success:
                    LOGGER.warning("Failed to fetch brightness for MagicMirror")
                if not modules.success:
                    LOGGER.warning("Failed to fetch modules for MagicMirror")

                return MagicMirrorData(
                    monitor_status=monitor.monitor,
                    update_available=bool(update.result),
                    brightness=int(brightness.result),
                    modules=modules.data,
                )

        except (Error, ClientConnectorError) as error:
            LOGGER.error("Update error %s", error)
            raise UpdateFailed(error) from error
