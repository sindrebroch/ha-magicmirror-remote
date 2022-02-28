"""BinarySensor file for MagicMirror."""

from typing import Any, List


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import STATE_ON
from homeassistant.helpers.entity import (
    DeviceInfo,
    ToggleEntity,
    ToggleEntityDescription,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.magicmirror.const import DOMAIN, LOGGER
from custom_components.magicmirror.coordinator import MagicMirrorDataUpdateCoordinator
from custom_components.magicmirror.models import Entity, ModuleDataResponse

SWITCHES: tuple[ToggleEntityDescription, ...] = (
    ToggleEntityDescription(
        key=Entity.MONITOR_STATUS.value,
        name="MagicMirror Monitor",
        icon="mdi:mirror",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add MagicMirror entities from a config_entry."""

    coordinator: MagicMirrorDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    modules: List[ModuleDataResponse] = coordinator.data.modules

    async_add_entities(
        MagicMirrorModuleSwitch(coordinator, module) for module in modules
    )

    for description in SWITCHES:
        if description.key == Entity.MONITOR_STATUS.value:
            async_add_entities([MagicMirrorMonitorSwitch(coordinator, description)])
        else:
            async_add_entities([MagicMirrorSwitch(coordinator, description)])


class MagicMirrorSwitch(CoordinatorEntity, ToggleEntity):
    """Define a MagicMirror entity."""

    sensor_data: bool
    coordinator: MagicMirrorDataUpdateCoordinator

    def __init__(
        self,
        coordinator: MagicMirrorDataUpdateCoordinator,
        description: ToggleEntityDescription,
    ) -> None:
        """Initialize."""

        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{description.key}"
        self._attr_device_info = coordinator._attr_device_info

        self.update_from_data()

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""

        return self.sensor_data

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:toggle-switch" if self.is_on else "mdi:toggle-switch-off-outline"

    def update_from_data(self) -> None:
        """Update sensor data."""
        self.sensor_data = self.coordinator.data.__getattribute__(
            self.entity_description.key
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""

        self.update_from_data()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""

        LOGGER.error("Switch not implemented")
        self.sensor_data = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""

        LOGGER.error("Switch not implemented")
        self.sensor_data = False
        await self.coordinator.async_request_refresh()


class MagicMirrorMonitorSwitch(MagicMirrorSwitch):
    """Define a MagicMirror entity."""

    def update_from_data(self) -> None:
        """Update sensor data."""
        coordinator_data = self.coordinator.data.__getattribute__(self.entity_description.key)
        self.sensor_data = True if coordinator_data == STATE_ON else False
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""

        await self.coordinator.api.monitor_on()
        self.sensor_data = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""

        await self.coordinator.api.monitor_off()
        self.sensor_data = False
        await self.coordinator.async_request_refresh()


class MagicMirrorModuleSwitch(MagicMirrorSwitch):
    """Define a MagicMirrorModule entity."""

    def __init__(
        self,
        coordinator: MagicMirrorDataUpdateCoordinator,
        module: ModuleDataResponse,
    ) -> None:
        """Initialize."""

        super().__init__(
            coordinator,
            ToggleEntityDescription(key=f"{module.name}", name=f"{module.name}"),
        )
        self.module = module
        self._attr_unique_id = f"mm_module_{self.entity_description.name}"
        self.update_from_data()

    @property
    def device_info(self) -> DeviceInfo or None:
        return DeviceInfo(
            name=self.entity_description.key,
            model=self.entity_description.key,
            manufacturer="MagicMirror",
            identifiers={(DOMAIN, self.entity_description.key)},
            configuration_url=f"{self.coordinator.api.base_url}/remote.html",
        )

    def update_from_data(self) -> None:
        for module in self.coordinator.data.modules:
            if module.name == self.entity_description.name:
                self.sensor_data = False if module.hidden else True
                return
        self.sensor_data = "unknown"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""

        await self.coordinator.api.show_module(self.entity_description.name)
        self.sensor_data = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""

        await self.coordinator.api.hide_module(self.entity_description.name)
        self.sensor_data = False
        await self.coordinator.async_request_refresh()
