"""Mute and voice prompts."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SCAN_INTERVAL, LibratoneZippEntity  # noqa: F401  (SCAN_INTERVAL is read by HA)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    zipp = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, "Libratone Zipp")
    async_add_entities([ZippMuteSwitch(zipp, name), ZippVoicePromptSwitch(zipp, name)])


class ZippMuteSwitch(LibratoneZippEntity, SwitchEntity):
    _key = "mute"
    _attr_name = "Mute"
    _attr_icon = "mdi:volume-off"

    @property
    def is_on(self):
        return self._zipp.is_muted

    async def async_turn_on(self, **kwargs) -> None:
        await self._run(self._zipp.mute)

    async def async_turn_off(self, **kwargs) -> None:
        await self._run(self._zipp.unmute)


class ZippVoicePromptSwitch(LibratoneZippEntity, SwitchEntity):
    """Spoken status messages of the speaker ("Wi-Fi connected", ...)."""

    _key = "voice_prompts"
    _attr_name = "Voice prompts"
    _attr_icon = "mdi:account-voice"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self):
        value = self._zipp.get_extra("voice_prompt")
        return None if value is None else value == "1"

    async def async_turn_on(self, **kwargs) -> None:
        await self._run(self._zipp.voice_prompt_set, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._run(self._zipp.voice_prompt_set, False)
