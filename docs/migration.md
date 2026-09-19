# Migrating

This project ships as a new blueprint (`bambu_printer_notifications.yaml`), so
Home Assistant treats it as a different blueprint than the one you may be using
today. Your old automation keeps running until you switch it over.

## From the upstream blueprint or the earlier fork

The earlier fork lived in `dabo53ck/bambu-print-notify-blueprint` and is
archived. It was based on
[HallyAus/homeassistant-bambu-blueprints](https://github.com/HallyAus/homeassistant-bambu-blueprints).

1. Import this blueprint (see [Installation](../README.md#installation)).
2. Open your existing automation, then ⋮ → **Edit in YAML**.
3. Change the blueprint path and delete inputs that no longer exist:

   ```yaml
   use_blueprint:
     path: dabo53ck/bambu_printer_notifications.yaml
     input:
       # keep everything you had, except the inputs listed below
   ```

4. Save. Optionally delete the old blueprint under **Settings → Automations &
   Scenes → Blueprints** once nothing uses it.

Input names are unchanged, so your entities, notify service, critical alert
settings and custom actions carry over.

### Inputs that are gone

These belong to features this blueprint does not have. Delete them from the
automation YAML: an input the blueprint does not declare can keep the
automation from loading.

| Input | Why |
| ----- | --- |
| `progress_trigger_threshold` | The stage trigger comes first; the progress fallback is fixed at 100 %. |
| `cooldown_minutes` | `mode: single` already drops repeated triggers of the same print. |
| `tts_enable`, `tts_service`, `tts_media_player`, `tts_volume`, `tts_success_message`, `tts_fault_message`, `tts_quiet_hours_enable`, `tts_quiet_hours_start`, `tts_quiet_hours_end` | Text-to-speech is not part of this blueprint. Use the custom success and fault actions for announcements. |

### Inputs that are new

| Input | Default |
| ----- | ------- |
| `notify_entities` | none |
| `time_format` | `24h` |

### Things that behave differently

- **Snapshot file.** It is now `/config/www/snapshots/bambu_<automation>.jpg`,
  named after the automation instead of the printer. Old files can be deleted.
- **Notification tag.** Also per automation. Notifications of a new automation do
  not replace those of the old one; disable the old automation.
- **Current stage sensor.** It is the primary trigger. Make sure it is mapped.
- **Minimum Home Assistant version** is 2024.10.0.
