"""Charging state."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SCAN_INTERVAL, LibratoneZippEntity  # noqa: F401  (SCAN_INTERVAL is read by HA)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    zipp = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZippChargingSensor(zipp, entry.data.get(CONF_NAME, "Libratone Zipp"))])


class ZippChargingSensor(LibratoneZippEntity, BinarySensorEntity):
    _key = "charging"
    _attr_name = "Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    @property
    def is_on(self):
        return self._zipp.is_charging

    @property
    def extra_state_attributes(self):
        # Raw status code from the speaker (the Android app treats 1 as charging;
        # 2 was observed at 100 % battery)
        return {"raw_status": getattr(self._zipp, "chargingstatus", None)}
