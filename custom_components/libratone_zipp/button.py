"""One button per preset station (favorites 1-5)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LibratoneZippEntity

FAVORITE_SLOTS = (1, 2, 3, 4, 5)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    zipp = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, "Libratone Zipp")
    async_add_entities([ZippFavoriteButton(zipp, name, slot) for slot in FAVORITE_SLOTS])


class ZippFavoriteButton(LibratoneZippEntity, ButtonEntity):
    """Plays preset `slot`. The entity name is fixed (stable entity_id); the station is an attribute."""

    _attr_icon = "mdi:radio"
    _attr_should_poll = True

    def __init__(self, zipp, device_name: str, slot: int) -> None:
        self._slot = slot
        self._key = f"favorite_{slot}"
        self._attr_name = f"Favorite {slot}"
        super().__init__(zipp, device_name)

    @property
    def extra_state_attributes(self):
        return {"station": self._zipp.favorite_name(self._slot), "slot": self._slot}

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(self._zipp.favorite_play, str(self._slot))
