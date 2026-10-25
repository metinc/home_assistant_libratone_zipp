"""Shared base for the additional Libratone Zipp entities."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

# Values are read from the client's cache (filled by the speaker's replies), so polling is cheap.
SCAN_INTERVAL = timedelta(seconds=15)


def host_tag(host: str) -> str:
    """Same normalisation the media player uses for its unique_id."""
    return str(host).replace(".", "_").replace(":", "_").lower()


def device_info(zipp, name: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, host_tag(zipp.host))},
        name=name,
        manufacturer="Libratone",
        model="Zipp",
    )


class LibratoneZippEntity(Entity):
    """Entity bound to one speaker; subclasses set _key and _attr_name."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    _key: str = ""

    def __init__(self, zipp, device_name: str) -> None:
        self._zipp = zipp
        self._device_name = device_name
        self._attr_unique_id = f"libratone_{host_tag(zipp.host)}_{self._key}"
        self._attr_device_info = device_info(zipp, device_name)

    async def _run(self, func, *args):
        """Run a blocking client call and refresh the state immediately afterwards."""
        await self.hass.async_add_executor_job(func, *args)
        self.async_write_ha_state()
