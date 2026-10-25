"""Room setting and speaker channel (stereo / left / right)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SCAN_INTERVAL, LibratoneZippEntity  # noqa: F401  (SCAN_INTERVAL is read by HA)
from .extras import STEREO_TYPE_IDS, STEREO_TYPES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    zipp = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, "Libratone Zipp")
    async_add_entities([ZippRoomSelect(zipp, name), ZippChannelSelect(zipp, name)])


class ZippRoomSelect(LibratoneZippEntity, SelectEntity):
    """Room setting (placement compensation), e.g. floor / wall / corner."""

    _key = "room"
    _attr_name = "Room setting"
    _attr_icon = "mdi:speaker-wireless"

    @property
    def options(self) -> list[str]:
        return list(self._zipp.room_list or [])

    @property
    def current_option(self):
        room = self._zipp.room
        return room if room in self.options else None

    async def async_select_option(self, option: str) -> None:
        await self._run(self._zipp.room_set, option)


class ZippChannelSelect(LibratoneZippEntity, SelectEntity):
    """Which channel this speaker plays when it is paired with a second one."""

    _key = "speaker_channel"
    _attr_name = "Speaker channel"
    _attr_icon = "mdi:speaker-multiple"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(STEREO_TYPE_IDS)

    @property
    def current_option(self):
        return STEREO_TYPES.get(self._zipp.get_extra("stereo_type") or "")

    async def async_select_option(self, option: str) -> None:
        await self._run(self._zipp.stereo_type_set, option)
