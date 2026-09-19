<div align="center">

# Bambu Printer Notifications

**A notification with a camera snapshot when your Bambu Lab printer finishes or faults — photographed before the build plate lowers.**

[![Release][release-badge]][release-url] &nbsp; [![Validate][validate-badge]][validate-url] &nbsp; [![Tests][tests-badge]][tests-url] &nbsp; [![License: MIT][license-badge]][license-url]

</div>

A Home Assistant blueprint for the [Bambu Lab integration](https://github.com/greghesp/ha-bambulab).
When a print ends, you get a mobile notification with a photo of the finished
print, the file name, weight, progress and the time. When it faults, you get the
same with the failure status and, if you like, a critical alert.

<img src="docs/images/notification-example.png" alt="Print complete notification with snapshot" width="300">

The snapshot is triggered by the printer **stage** leaving the printing phase,
not by a progress percentage. On a P1S that is roughly 40 seconds earlier, so
the photo shows the print, not the plate on its way down. See
[how it works](docs/how-it-works.md) for the measurements.

> **Not affiliated** with Bambu Lab. Bambu Lab and the printer names are
> trademarks of their owners.

---

## Features

| Area | What you get |
| ---- | ------------ |
| Snapshot | Taken at the earliest reliable end-of-print signal, optionally with a light switched on and restored afterwards. |
| Message | File, weight, progress and time of day **with seconds**, in 24h or 12h AM/PM. |
| Delivery | A legacy `notify.<service>` (image, critical alerts, action button) and/or notify entities. Both can be used together. |
| Critical alerts | iOS critical notifications with a time window, separately for success and fault. |
| Faults | Sticky notification, persistent notification in Home Assistant, and your own actions. |
| Custom actions | Any Home Assistant actions on success or on fault: indicator lights, smart plugs, scripts, more notifications. |
| Several printers | One automation per printer. Snapshot file and notification tag are per automation. |

---

## Requirements

- Home Assistant **2024.10.0** or newer
- The [Bambu Lab integration](https://github.com/greghesp/ha-bambulab) with your printer set up
- A camera entity for the printer
- A snapshot folder, see [Setup](#setup)
- The Home Assistant Companion App for notifications with images and critical alerts (optional)

---

## Installation

### One-click import

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fdabo53ck%2Fbambu-printer-notifications-blueprint%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fdabo53ck%2Fbambu_printer_notifications.yaml)

Needs the [My Home Assistant](https://my.home-assistant.io/) redirect, which is
on by default. Confirm with **Preview** → **Import**.

### Import via URL

1. **Settings → Automations & Scenes → Blueprints → Import Blueprint**
2. Paste:
   `https://github.com/dabo53ck/bambu-printer-notifications-blueprint/blob/main/blueprints/automation/dabo53ck/bambu_printer_notifications.yaml`
3. **Preview** → **Import**

### Manual

1. Copy `blueprints/automation/dabo53ck/bambu_printer_notifications.yaml` to
   `/config/blueprints/automation/dabo53ck/bambu_printer_notifications.yaml`
2. **Settings → Automations & Scenes → Blueprints → ⋮ → Reload**

Coming from the upstream blueprint or an earlier version of this fork? See
[docs/migration.md](docs/migration.md).

---

## Setup

### 1. Create the snapshot folder

The blueprint writes the snapshot to a fixed folder and links to it from a
fixed URL. For an automation named `automation.p1s_notify`:

```
File written by camera.snapshot:  /config/www/snapshots/bambu_p1s_notify.jpg
URL used in the notification:     /local/snapshots/bambu_p1s_notify.jpg
```

Home Assistant serves everything under `/config/www/` at the public path
`/local/`, which is why the two paths differ but point at the same file.

**Home Assistant does not create the folder.** If it is missing, `camera.snapshot`
fails without stopping the automation: the notification arrives with a broken
image instead of a photo, and there is no error in the log that points at the
cause. Create it once:

- **File editor / Studio Code Server:** in `/config/www/`, create a folder named `snapshots`.
- **Samba share:** open `\\<your-ha-ip>\config\www\` and create `snapshots`.
- **Terminal / SSH:** `mkdir -p /config/www/snapshots`

### 2. Create the automation

**Settings → Automations & Scenes → Create Automation → Use Blueprint → Bambu
Printer Notifications.** Map your printer's entities (the pickers only offer
entities of the Bambu Lab integration), pick an `input_boolean` as the master
switch and enter your notify service or notify entities.

---

## Configuration

### Printer sensors

| Input | Entity of the Bambu Lab integration |
| ----- | ----------------------------------- |
| Print status sensor | states `running`, `finish`, `failed` |
| Print error binary sensor | turns on when the printer reports an error |
| **Current stage sensor** | **drives the primary trigger, should be mapped** |
| Progress sensor | print progress in percent |
| Printer name sensor | printer name, used in the notification title |
| Task name sensor | name of the current job |
| Print weight sensor | weight in grams |
| Printer camera | your printer's camera |

### Snapshot settings

| Input | Default | Description |
| ----- | ------- | ----------- |
| Snapshot light | *none* | Light switched on before the photo and restored afterwards. |
| Light brightness | 100 % | Brightness while the photo is taken. |
| Snapshot delay | 1 s | Wait for light warm-up or camera exposure. **Every second counts:** the plate starts lowering shortly after the print ends, so keep this at 0–1 s. |

### Notification settings

| Input | Default | Description |
| ----- | ------- | ----------- |
| Notifications enabled | *required* | `input_boolean` that must be on for anything to be sent. |
| Notify service (legacy) | *empty* | Name of a notify service, for example `mobile_app_your_phone`, with or without the `notify.` prefix. |
| Notify entities | *none* | Notify entities that receive title and message through `notify.send_message`. |
| Time format | 24h | `24h` (`14:05:09`) or `12h` AM/PM (`02:05:09 PM`). Seconds are always shown. |
| Success type | Normal | Normal / Critical / Never critical |
| Fault type | Critical | Normal / Critical / Never critical |
| Success window | 07:00–21:00 | Only when the type is Critical. |
| Fault window | 07:00–21:00 | Only when the type is Critical. |

Identical start and end time means **never critical**. For critical around the
clock use `00:00:00`–`23:59:59`. A window that crosses midnight (`22:00`–`06:00`)
works.

#### Legacy service or notify entities

| | Legacy service | Notify entities |
| - | :-: | :-: |
| Title and message | yes | yes |
| Snapshot image | yes | no |
| Critical alerts (iOS) | yes | no |
| "Open Printers" button | yes | no |
| Works without `notify.mobile_app_*` service | no | yes |

`notify.send_message` cannot carry the extra data that images and critical
alerts need. If your Companion App only offers a notify entity, you get text
notifications through that path. Both inputs can be filled at once.

### Critical alert settings

| Input | Default | Description |
| ----- | ------- | ----------- |
| Critical alert sound | `default` | iOS sound name. |
| Critical alert volume | 1.0 | 0.0–1.0 |

### Custom actions

Any Home Assistant actions, on success or on fault: indicator lights, smart
plugs, scripts, more notification services, announcements, pausing other
printers.

### Optional

| Input | Default | Description |
| ----- | ------- | ----------- |
| Printers view path | *empty* | Dashboard path such as `/lovelace/3d_printers`. Adds an "Open Printers" button (legacy service only). |

---

## Troubleshooting

Start with the trace: **Settings → Automations & Scenes → your automation → ⋮ →
Traces**. It shows which trigger fired, when, and where the run stopped.

**The snapshot still shows the plate lowering.**
The trigger should be your *stage* sensor and the `camera.snapshot` step should
be within a few dozen milliseconds of it. If the trigger is the progress sensor
instead, the stage sensor is not mapped or was unavailable. Also check the
snapshot delay.

**The notification arrives minutes late.**
Look for a `wait_template` step that ran into its 10 minute timeout. That means
the print status never reached `finish` or `failed`.

**Two notifications per print.**
Should not happen. A run that shows `failed_single` is the expected, discarded
second trigger, not a second notification.

**The notification has a broken image.**
`/config/www/snapshots/` is missing, see [Setup](#1-create-the-snapshot-folder).
`camera.snapshot` runs with `continue_on_error`, so this is not logged as an error.

**No image with notify entities.**
`notify.send_message` cannot carry images, see
[Legacy service or notify entities](#legacy-service-or-notify-entities).

**"Action notify.xxx not found" in the trace.**
The notify service name does not exist. The other outputs (notify entities,
persistent notification, custom actions) still run; fix the name or leave the
field empty.

**The pickers show no entities.**
They only offer entities of the Bambu Lab integration. Check that the
integration is set up and the printer is online.

More questions: [Discussions](https://github.com/dabo53ck/bambu-printer-notifications-blueprint/discussions).
Bugs: [Issues](https://github.com/dabo53ck/bambu-printer-notifications-blueprint/issues).

---

## Documentation

- [How it works](docs/how-it-works.md): why the stage sensor, run order, `mode: single`
- [Migrating](docs/migration.md): from the upstream blueprint or the earlier fork
- [Testing](docs/testing.md): test suite, CI and testing on a live Home Assistant
- [Changelog](CHANGELOG.md), [Contributing](CONTRIBUTING.md)

---

## Credits

Based on the original blueprint by [@HallyAus](https://github.com/HallyAus) —
[homeassistant-bambu-blueprints](https://github.com/HallyAus/homeassistant-bambu-blueprints).
Thank you for the foundation. Built on the
[Bambu Lab integration](https://github.com/greghesp/ha-bambulab) by
[@greghesp](https://github.com/greghesp) and contributors.

## License

MIT, see [LICENSE](LICENSE). The upstream blueprint is released under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

[release-badge]: https://img.shields.io/github/v/release/dabo53ck/bambu-printer-notifications-blueprint?label=release
[release-url]: https://github.com/dabo53ck/bambu-printer-notifications-blueprint/releases
[validate-badge]: https://github.com/dabo53ck/bambu-printer-notifications-blueprint/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/dabo53ck/bambu-printer-notifications-blueprint/actions/workflows/validate.yml
[tests-badge]: https://github.com/dabo53ck/bambu-printer-notifications-blueprint/actions/workflows/tests.yml/badge.svg
[tests-url]: https://github.com/dabo53ck/bambu-printer-notifications-blueprint/actions/workflows/tests.yml
[license-badge]: https://img.shields.io/badge/License-MIT-green.svg
[license-url]: LICENSE
