"""Binary sensor file for MagicMirror."""

from custom_components.magicmirror.models import Entity
from typing import Optional

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN as MAGICMIRROR_DOMAIN
from .coordinator import MagicMirrorDataUpdateCoordinator

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=Entity.UPDATE_AVAILABLE.value,
        name="Update Available",
        icon="mdi:arrow-up-box", # TODO different icon for on / off
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add MagicMirror entities from a config_entry."""

    coordinator: MagicMirrorDataUpdateCoordinator = hass.data[MAGICMIRROR_DOMAIN][entry.entry_id]

    for binary_sensor_description in BINARY_SENSORS:
        async_add_entities([MagicMirrorSensor(coordinator, binary_sensor_description)])

class MagicMirrorSensor(CoordinatorEntity, BinarySensorEntity):
    """Define a MagicMirror entity."""

    coordinator: MagicMirrorDataUpdateCoordinator

    def __init__(
        self,
        coordinator: MagicMirrorDataUpdateCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize."""

        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = description

        self.sensor_data = self.get_sensor_data()

        self._attr_unique_id = f"{description.key}"
        self._attr_device_info = coordinator._attr_device_info
    
    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the binary sensor is on."""

        return self.sensor_data

    def get_sensor_data(self) -> bool:
        if self.coordinator.data[self.entity_description.key] == STATE_ON:
            return True
        elif self.coordinator.data[self.entity_description.key] == STATE_OFF:
            return False
        else:
            return self.coordinator.data[self.entity_description.key]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""

        self.sensor_data = self.get_sensor_data()
        super()._handle_coordinator_update()
