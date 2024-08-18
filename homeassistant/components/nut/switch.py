"""Provides a switch for switchable NUT outlets."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import NutConfigEntry, PyNUTData, _get_nut_device_info
from .const import (
    DOMAIN,
    OUTLET_COUNT,
    OUTLET_PREFIX,
    OUTLET_SUFFIX_LOAD_OFF,
    OUTLET_SUFFIX_LOAD_ON,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NutConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NUT switches."""

    pynut_data = config_entry.runtime_data
    coordinator = pynut_data.coordinator
    data = pynut_data.data
    unique_id = pynut_data.unique_id
    status = coordinator.data

    if (num_outlets := status.get(OUTLET_COUNT)) is not None:
        entities = []
        for outlet_num in range(1, int(num_outlets) + 1):
            if (
                OUTLET_PREFIX + str(outlet_num) + OUTLET_SUFFIX_LOAD_ON
                in pynut_data.device_all_action_commands
            ) and (
                OUTLET_PREFIX + str(outlet_num) + OUTLET_SUFFIX_LOAD_OFF
                in pynut_data.device_all_action_commands
            ):
                entities += [
                    NUTSwitch(
                        coordinator,
                        SwitchEntityDescription(
                            key=OUTLET_PREFIX + str(outlet_num) + ".poweronoff",
                            translation_key="outlet_number_poweronoff",
                            translation_placeholders={"outlet_num": str(outlet_num)},
                            device_class=SwitchDeviceClass.OUTLET,
                            entity_registry_enabled_default=True,
                        ),
                        data,
                        unique_id,
                    )
                ]

        async_add_entities(entities)


class NUTSwitch(CoordinatorEntity[DataUpdateCoordinator[dict[str, str]]], SwitchEntity):
    """Representation of a switch entity for NUT status values."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, str]],
        switch_description: SwitchEntityDescription,
        data: PyNUTData,
        unique_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.pynut_data = data
        self.entity_description = switch_description

        device_name = data.name.title()
        self._attr_unique_id = f"{unique_id}_{switch_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=device_name,
        )
        self._attr_device_info.update(_get_nut_device_info(data))

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        status = self.coordinator.data

        name_list = self.entity_description.key.split(".")
        if (name_list[0] == "outlet") and (name_list[2] == "poweronoff"):
            return status.get(name_list[0] + "." + name_list[1] + ".status") == "on"
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the device."""
        _LOGGER.debug("turn_on -> kwargs: %s", kwargs)

        name_list = self.entity_description.key.split(".")
        command_name = name_list[0] + "." + name_list[1] + OUTLET_SUFFIX_LOAD_ON
        await self.pynut_data.async_run_command(command_name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the device."""
        _LOGGER.debug("turn_off -> kwargs: %s", kwargs)

        name_list = self.entity_description.key.split(".")
        command_name = name_list[0] + "." + name_list[1] + OUTLET_SUFFIX_LOAD_OFF
        await self.pynut_data.async_run_command(command_name)
