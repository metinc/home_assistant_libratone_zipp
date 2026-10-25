# Libratone Zipp controller for Home Assistant

This controls a Libratone Zipp speaker within [Home Assistant](https://www.home-assistant.io/) using [this Python library](https://github.com/Chouffy/python_libratone_zipp).

Besides the media player, every speaker gets one device with sensors, switches, numbers, selects and favorite buttons. Most of them
use commands found by decompiling the official Android app. Everything listed below was verified on a **Zipp 2 (firmware 1536)**; other
models may behave differently.

## Limitations / Known bugs

* Major:
    * On Bluetooth and when the music is playing, you only get "Play" button, not Pause.
* Minor:
    * After a restart of Home Assistant, the integration can be in an "unknown" state before the 1st music is played
    * Shuffle and repeat are only offered while the active source supports them. Only the read/write of the setting was tested; no source that supports it (USB, DLNA, Bluetooth) was available.
    * Stations cannot be searched locally; a favorite needs its vTuner station id (see [Favorites](#favorites)).

## Usage

### Installation via [HACS](https://hacs.xyz/)

1. Search for *Libratone Zipp* in the integration tab of HACS
1. Click *Install*
1. Restart Home Assistant
1. Go to _Settings_ → _Devices & services_ → _Add integration_ and search for **Libratone Zipp**
1. Add the IP of the speaker and a name
1. Repeat the last step if you have multiple speakers

Note: if you're using Docker/devcontainer, you need to forward `3333/udp` and `7778/udp`.

## Features

### Media player

* Turn on / off (standby), play, pause, stop, next, previous
* Volume (set and step), mute
* Sound mode (the speaker's "voicing", with the names the speaker reports)
* Source: the five preset stations, selected by station name or slot number (`"1"` ... `"5"`)
* Current title and sub-title, current source (the station name while a preset plays)
* Shuffle and repeat, offered only while the active source supports them
* Multi-room: SoundSpace Link (`media_player.join` / `unjoin`)
* Several speakers, added and removed in the UI

### Entities

Each speaker is one device. Entity ids below use the config entry name `Zipp2`, so `sensor.zipp2_battery` and so on.
Values are read from the speaker every 60 s and updated right after a change from Home Assistant.

| Platform | Entity | Notes |
|-|-|-|
| sensor | Battery | % |
| binary_sensor | Charging | the Android app treats status `1` as charging; the raw value is the `raw_status` attribute |
| sensor | Playback source | `none`, `preset`, `airplay`, `dlna`, `spotify`, `usb`, `sd_card`, `tunein`, `line_in`, `aux`, `bluetooth`, `url`, `group`, `voice`, `other` |
| sensor (diagnostic) | Wi-Fi signal | dBm, with a `quality_percent` attribute |
| sensor (diagnostic) | Firmware | version number reported by the speaker (1536 on the tested Zipp 2) |
| sensor (diagnostic) | Firmware update | what the speaker itself reports: `none`, `available`, `downloading`, `ready`, `updating`, `updated`, `mandatory` (read-only) |
| sensor (diagnostic) | Serial number | disabled by default |
| switch | Mute | same as the media player's mute |
| number | Sleep timer | minutes until standby, 0 = off; shows the remaining time |
| number (config) | Maximum volume | volume cap enforced by the speaker itself, 0-100 |
| number (config) | LED level | 0-2 |
| switch (config) | Voice prompts | the speaker's spoken status messages |
| select | Room setting | placement compensation; the names come from the speaker (Neutral, Outdoor, Shelf, Table, Floor) |
| select (config) | Speaker channel | `stereo`, `left` or `right` (for two paired speakers) |
| button | Favorite 1-5 | play a preset; the station name is the `station` attribute |

### Services

* `libratone_zipp.set_favorite`: store a station in one of the five presets (`favorite` 1-5, `station_id`, optional `name` and `channel_type`, default `vtuner`).

### Favorites

The speaker has five preset slots. Each one is a JSON object:

```json
{"channel_id": 1, "channel_identity": "77320", "channel_name": "Klassik Radio Classic Dreams", "channel_type": "vtuner"}
```

* The media player's `source_list` contains the station names.
* `button.zipp2_favorite_1` ... `_5` play a preset. Their entity names are fixed so the entity ids do not change when a preset is replaced.
* `libratone_zipp.set_favorite` replaces a preset. `station_id` is the vTuner station id, the same value the speaker reports as
  `channel_identity` for existing presets. Non-ASCII names work. The official app finds stations through the vendor's cloud API,
  which this integration does not use, so there is no station search.

### Playback source, shuffle and repeat

Command 10 returns the active source as bytes. Byte 0 is the source code (the ASCII value of the app's `SourceInfo` constants: `0` none,
`1` AirPlay, `2`/`3` DLNA, `4` Spotify, `5` USB, `<` line in, `?` preset station, `A` Bluetooth, `B` AUX, ...); bytes 3-6 are little-endian
ability flags. Command 1541 holds the play mode: `0` normal, `1` shuffle + repeat all, `2` repeat one, `3` repeat all, `6` shuffle,
`7` shuffle + repeat one. The media player offers shuffle and repeat only while the source sets ability flag 262144 (bit 18).

### Firmware

`Firmware update` shows the answer of command 66 with data `0`, `{"state": n, "err": n}`. The state names come from the app's log texts.
The integration only reads this state. Installing is not implemented: the app starts it with command 66 and data `1`, which could not be
tested safely.

### Lovelace example

A tile for the media player (tapping it opens a bubble-card popup `#zipp`) and one favorite showing the current station name:

```yaml
type: tile
entity: media_player.zipp2
features:
  - type: media-player-playback
    controls: [on_off, previous, play_pause, next]
  - type: media-player-volume-slider
state_content: [state, media_title, media_artist]
tap_action: {action: navigate, navigation_path: "#zipp"}
---
type: tile
entity: button.zipp2_favorite_1
name: Favorite 1
state_content: [station]
tap_action:
  action: perform-action
  perform_action: button.press
  target: {entity_id: button.zipp2_favorite_1}
```

### Functionality coverage

* Module
    * [x] Clean text variables, declare variable on top instead of using text like "play"
    * [x] Make the module usable with multiple speakers
    * [x] Handle exit properly - but need max `_KEEPALIVE_CHECK_PERIOD` seconds to exit
* Playback
    * [x] Retrieve basic playback status: play, pause, stop
    * [x] Set basic playback status: play, pause, stop, next, prev
    * [x] Retrieve and set volume, mute
    * [x] Retrieve current title and sub-title
    * [x] Retrieve current playback source and media type: preset, AirPlay, Bluetooth, AUX, ...
    * [x] Set and retrieve shuffle and repeat (when the source supports it)
* Standby
    * [x] Retrieve the actual speaker state and set immediate standby / wakeup
    * [x] Set and retrieve a standby timer
* Voicing & Room Setting
    * [x] Set and retrieve the Voicing (sound mode) and the Room Setting
* Favorites
    * [x] Play a favorite, with its proper title
    * [x] Set a favorite
* Speaker configuration
    * [x] Retrieve the name, serial number, color, firmware, battery level, charging state and Wi-Fi signal
    * [x] Set the speaker name (library only)
    * [x] Set the maximum volume, LED level and voice prompts
    * [x] Retrieve the firmware update state
* Multi-room
    * [x] SoundSpace Link
    * [x] Set the speaker channel (stereo, left, right)

### Not planned / open

* [ ] Make the module async (needs a rewrite of the Python library)
* [ ] Submit it for official integration (needs an async library on PyPI and tests)
* [ ] Add support for other Libratone speakers (only a Zipp 2 was available for testing)
* [ ] Set the input source. Tested on a Zipp 2 while a preset played: commands 537 (line in) and 121 (Bluetooth) are answered with status 1 but did not change the active source. Command 122 only switches the *output* (Bluetooth / speaker / AUX out), so it is not offered either. Details in the [library README](https://github.com/vnc0/python_libratone_zipp#input-source).
* [ ] Install firmware updates
* [ ] Search stations
* [ ] Set the speaker color

## How it works

`custom_components/libratone_zipp/extras.py` subclasses the library's `LibratoneZipp` (`ZippExtended`) and caches the replies for the
extra commands. Two details come from the speaker:

* It silently drops GETs that arrive in a burst, so a poll cycle spaces them out by 0.3 s. A value is read back 0.8 s after it was set.
* The library's receive loop does not catch exceptions, so one malformed reply (for example an empty Player JSON) used to stop the
  result thread and every later answer was dropped. `ZippExtended` catches them.

Commands used (UDP, GET = command type 1, SET = command type 2, sent to port 7777; answers arrive on 7778 and 3333):

| Command | Meaning |
|-|-|
| 5 | firmware version |
| 10 | source info (active source and ability flags) |
| 14 | power mode |
| 15 | sleep timer (GET; SET data `2<seconds>`, `F0` cancels) |
| 40 | play control: `PLAY`, `STOP`, `PAUSE`, `NEXT`, `PREV`, `MUTE`, `UNMUTE` |
| 51, 64 | play status, volume |
| 66 | firmware update state (GET with data `0`) |
| 90 | speaker name |
| 103, 502, 503 | SoundSpace Link notification, join, leave |
| 256 / 257 | battery level (the value arrives as command 257) |
| 275, 276, 277 | read the five favorites, write one, play one |
| 278 | player info (title, sub-title) |
| 293 | voice prompts (`1` / `0`) |
| 296 | LED level (`0`-`2`) |
| 300 | maximum volume |
| 512 / 515 | speaker channel (`0` stereo, `1` left, `2` right) |
| 516, 518, 524 | voicing: current, set, list |
| 517, 519, 525 | room setting: current, set, list |
| 520 | mute status (`UNMUTE` or `MUTE,<previous volume>`) |
| 529 | Wi-Fi info: `ssid,rssi,quality/max` |
| 769, 770 | serial number, color |
| 1284 | charging status |
| 1541 | play mode (shuffle / repeat) |

Commands seen on the speaker but not used: 301 (LED percent), 613 (LED all off), 1285 (private mode), 545 (room correction),
123 / 128 (output sources), 121 / 122 / 537 (input switching), 530 (automatic firmware download), 65 (older firmware update command).

## Acknowledgment

This work is based on the following:

* The first Libratone command list is [coming from this work from Benjamin Hanke](https://www.loxwiki.eu/display/LOX/Libratone+Zipp+WLan+Lautsprecher)
* Further commands come from decompiling the Android app (`com.libratone.v3.model.LSSDPNode`, `luci.MIDCONST`)
* Entity to use: [Media Player](https://developers.home-assistant.io/docs/core/entity/media-player)
* Example of [integrations](https://www.home-assistant.io/integrations/#media-player):
    * Simple: [Harman Kardon AVR integration](https://www.home-assistant.io/integrations/harman_kardon_avr/) which use [this module](https://github.com/Devqon/hkavr)
    * Simple: [Clementine Music Player integration](https://github.com/home-assistant/core/blob/dev/homeassistant/components/clementine/media_player.py) which use [this module]()
    * Async: [Frontier Silicon integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/frontier_silicon) with [this module](https://github.com/zhelev/python-afsapi/tree/master/afsapi)
    * Async with extended features: [Yamaha integration](https://github.com/home-assistant/core/blob/dev/homeassistant/components/yamaha/) with [this module](https://github.com/wuub/rxv)

## License

See LICENSE file.
