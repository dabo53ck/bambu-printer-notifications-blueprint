# Changelog

All notable changes to this project are documented here. The format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). SemVer,
pre-release identifiers included (`v0.0.1-beta`, …).

## [v0.0.1-beta] - 2026-09-19

First release as a standalone project. It continues the work of an earlier
fork of [HallyAus/homeassistant-bambu-blueprints](https://github.com/HallyAus/homeassistant-bambu-blueprints),
rewritten on current Home Assistant syntax and covered by automated tests. It is
a **new blueprint** in Home Assistant: see [docs/migration.md](docs/migration.md)
if you used the upstream blueprint or the earlier fork.

### Added

- **Stage-based snapshot trigger.** The snapshot is taken when the printer stage
  returns to `idle`, roughly 40 seconds before the progress and status sensors
  update on a P1S, which is before the build plate starts to lower. A progress
  trigger at 100 % and the status triggers remain as fallbacks. See
  [docs/how-it-works.md](docs/how-it-works.md).
- **Device picker for notifications.** New input *Devices* replaces the free-text
  notify service of earlier versions. Pick your phones and tablets from your
  paired Companion App devices; the blueprint finds each device's notify service
  itself. The notification carries the snapshot image, critical alerts and the
  action button.
- **Time of day in every message**, with seconds. New input *Time format*
  (24h or 12h AM/PM, default 24h).
- **One snapshot file and one notification tag per automation**
  (`/config/www/snapshots/<automation>.jpg`), so several printers or
  automations never overwrite each other.
- **Independent outputs.** The notifications, the persistent notification and
  the custom actions run in separate branches. A notify service that does not
  exist no longer stops the persistent notification or your custom actions.
- Faults at zero progress are reported (a print that fails while heating).
- Test suite that runs the blueprint through the real Home Assistant automation
  engine, plus `check_config` against the minimum and the latest Home Assistant.

### Changed

- Waiting for the end of the print uses `wait_template`, which checks the
  current state first. A print whose status already passed `finish` (usually on
  to `idle`) while the snapshot was taken no longer waits out the 10 minute
  timeout.
- The stage trigger only fires on `printing`, `inspecting_first_layer` or
  `auto_bed_leveling` → `idle`, not on every change away from those stages.
- A sensor returning from `unavailable` (for example progress jumping to 100)
  is not treated as a finished print.
- A fault stays a fault when the error flag clears again before the
  notification is built.
- Entity pickers are limited to the Bambu Lab integration.
- Minimum Home Assistant version is 2024.10.0.
