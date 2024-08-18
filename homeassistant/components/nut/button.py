"""Provides a switch for switchable NUT outlets."""

from __future__ import annotations

import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NutConfigEntry, PyNUTData, _get_nut_device_info
from .const import DOMAIN, OUTLET_COUNT, OUTLET_PREFIX, OUTLET_SUFFIX_LOAD_CYCLE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NutConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NUT buttons."""

    pynut_data = config_entry.runtime_data
    coordinator = pynut_data.coordinator
    data = pynut_data.data
    unique_id = pynut_data.unique_id
    status = coordinator.data

    if (num_outlets := status.get(OUTLET_COUNT)) is not None:
        entities = []
        for outlet_num in range(1, int(num_outlets) + 1):
            if (
                OUTLET_PREFIX + str(outlet_num) + OUTLET_SUFFIX_LOAD_CYCLE
                in pynut_data.device_all_action_commands
            ):
                entities += [
                    NUTButton(
                        ButtonEntityDescription(
                            key=OUTLET_PREFIX + str(outlet_num) + ".powercycle",
                            translation_key="outlet_number_powercycle",
                            translation_placeholders={"outlet_num": str(outlet_num)},
                            device_class=ButtonDeviceClass.RESTART,
                            entity_registry_enabled_default=True,
                        ),
                        data,
                        unique_id,
                    )
                ]

        async_add_entities(entities)


class NUTButton(ButtonEntity):
    """Representation of a button entity for NUT status values."""

    _attr_has_entity_name = True

    def __init__(
        self,
        button_description: ButtonEntityDescription,
        data: PyNUTData,
        unique_id: str,
    ) -> None:
        """Initialize the button."""
        self.pynut_data = data
        self.entity_description = button_description

        device_name = data.name.title()
        self._attr_unique_id = f"{unique_id}_{button_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=device_name,
        )
        self._attr_device_info.update(_get_nut_device_info(data))

    async def async_press(self) -> None:
        """Press the button."""
        _LOGGER.debug("press button")

        name_list = self.entity_description.key.split(".")
        command_name = name_list[0] + "." + name_list[1] + OUTLET_SUFFIX_LOAD_CYCLE
        await self.pynut_data.async_run_command(command_name)
