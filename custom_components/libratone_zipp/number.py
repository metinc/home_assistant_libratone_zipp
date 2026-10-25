"""Sleep timer, speaker-side maximum volume and LED level."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SCAN_INTERVAL, LibratoneZippEntity  # noqa: F401  (SCAN_INTERVAL is read by HA)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    zipp = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, "Libratone Zipp")
    async_add_entities(
        [
            ZippSleepTimer(zipp, name),
            ZippMaxVolume(zipp, name),
            ZippLedLevel(zipp, name),
        ]
    )


class ZippSleepTimer(LibratoneZippEntity, NumberEntity):
    """Minutes until the speaker goes to standby. 0 = no timer.

    Reading returns the remaining time (rounded up); writing starts a new timer.
    The speaker is polled once a minute, so the remaining time updates in minute steps.
    """

    _key = "sleep_timer"
    _attr_name = "Sleep timer"
    _attr_icon = "mdi:timer-sand"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 720
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    @property
    def native_value(self):
        seconds = self._zipp.timer
        if seconds is None:
            return 0
        return -(-int(seconds) // 60)  # ceil

    async def async_set_native_value(self, value: float) -> None:
        minutes = int(value)
        if minutes <= 0:
            await self._run(self._zipp.timer_off)
        else:
            await self._run(self._zipp.timer_set_seconds, minutes * 60)


class ZippMaxVolume(LibratoneZippEntity, NumberEntity):
    """Volume cap enforced by the speaker itself (also applies to the app and buttons)."""

    _key = "max_volume"
    _attr_name = "Maximum volume"
    _attr_icon = "mdi:volume-vibrate"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self):
        value = self._zipp.get_extra("max_volume")
        return int(value) if value is not None and value.isdigit() else None

    async def async_set_native_value(self, value: float) -> None:
        await self._run(self._zipp.max_volume_set, int(value))


class ZippLedLevel(LibratoneZippEntity, NumberEntity):
    """LED brightness level, 0..2 as used by the official app."""

    _key = "led_level"
    _attr_name = "LED level"
    _attr_icon = "mdi:led-on"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 2
    _attr_native_step = 1
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self):
        value = self._zipp.get_extra("led_level")
        return int(value) if value is not None and value.isdigit() else None

    async def async_set_native_value(self, value: float) -> None:
        await self._run(self._zipp.led_level_set, int(value))
