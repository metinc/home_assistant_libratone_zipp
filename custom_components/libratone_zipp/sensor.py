"""Battery, Wi-Fi signal, firmware, firmware update state and serial number sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SCAN_INTERVAL, LibratoneZippEntity  # noqa: F401  (SCAN_INTERVAL is read by HA)
from .extras import FW_UPDATE_STATES, SOURCE_TYPE_OPTIONS


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    zipp = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, "Libratone Zipp")
    async_add_entities(
        [
            ZippBatterySensor(zipp, name),
            ZippSignalSensor(zipp, name),
            ZippFirmwareSensor(zipp, name),
            ZippSerialSensor(zipp, name),
            ZippFirmwareUpdateSensor(zipp, name),
            ZippSourceSensor(zipp, name),
        ]
    )


class ZippBatterySensor(LibratoneZippEntity, SensorEntity):
    _key = "battery"
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self._zipp.battery_percent


class ZippSignalSensor(LibratoneZippEntity, SensorEntity):
    _key = "wifi_signal"
    _attr_name = "Wi-Fi signal"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self._zipp.wifi_rssi

    @property
    def extra_state_attributes(self):
        return {"quality_percent": self._zipp.wifi_quality_percent}


class ZippFirmwareSensor(LibratoneZippEntity, SensorEntity):
    _key = "firmware"
    _attr_name = "Firmware"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self._zipp.version


class ZippSerialSensor(LibratoneZippEntity, SensorEntity):
    _key = "serial_number"
    _attr_name = "Serial number"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        return self._zipp.serialnumber


class ZippFirmwareUpdateSensor(LibratoneZippEntity, SensorEntity):
    """Update state reported by the speaker itself (it checks for packages on its own)."""

    _key = "firmware_update"
    _attr_name = "Firmware update"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = sorted(set(FW_UPDATE_STATES.values()) | {"unknown"})
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:update"

    @property
    def native_value(self):
        state = self._zipp.firmware_update
        return state[0] if state else None

    @property
    def extra_state_attributes(self):
        state = self._zipp.firmware_update
        return {"error_code": state[1] if state else None, "installed_version": self._zipp.version}


class ZippSourceSensor(LibratoneZippEntity, SensorEntity):
    """What the speaker plays from: preset station, AirPlay, Bluetooth, AUX, ..."""

    _key = "playback_source"
    _attr_name = "Playback source"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SOURCE_TYPE_OPTIONS
    _attr_icon = "mdi:import"

    @property
    def native_value(self):
        return self._zipp.source_type
