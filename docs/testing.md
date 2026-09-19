# Testing

Three layers. The first two run in CI; the third is you and a real print.

## 1. Static checks

```bash
pip install pyyaml yamllint
yamllint -c .yamllint.yml blueprints tests/fixtures .github
python scripts/validate_blueprints.py
```

`validate_blueprints.py` checks the metadata, that every `!input` is declared and
every input used, that tuning inputs have defaults, that `source_url` points at
this file, that links to blueprint files in the README and docs exist, and that
the blueprint version matches the newest CHANGELOG section.

## 2. Behaviour tests

`tests/` runs the blueprint through the real Home Assistant automation engine.
Entities are plain states and every service the blueprint calls is a recording
mock. A test reads like a print: set states, advance the clock, assert on the
calls.

```bash
pip install -r requirements-test.txt
pytest
```

Home Assistant does not run on native Windows. Use Linux, macOS, WSL or a
container; CI runs on Ubuntu against the declared minimum and the latest Home
Assistant.

Every behaviour that was once a bug has a test: the stage trigger not firing
mid-print, progress skipping to 100, the print already past `finish`, the
10 minute timeout, a missing notify service, a fault that clears again.

### `check_config`

CI also lets Home Assistant itself generate the automation from
`tests/fixtures/check_config/automations.yaml`, which sets every input. That
catches broken selectors and templates that a mock cannot. Locally, with Docker:

```bash
mkdir -p ha/blueprints/automation/dabo53ck
cp blueprints/automation/dabo53ck/*.yaml ha/blueprints/automation/dabo53ck/
cp tests/fixtures/check_config/automations.yaml ha/automations.yaml
printf 'homeassistant:\n  name: CI\n  time_zone: UTC\nautomation: !include automations.yaml\n' > ha/configuration.yaml
docker run --rm -v "$PWD/ha:/config" ghcr.io/home-assistant/home-assistant:stable \
  python -m homeassistant --script check_config -c /config
```

## 3. A real print

No mock can tell you whether the snapshot shows the print or the plate on its
way down. Work on a `dev` branch (see [CONTRIBUTING.md](../CONTRIBUTING.md)) and
test it on your Home Assistant without copying files:

1. Import the blueprint from the branch, once:
   `https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/dabo53ck/bambu-printer-notifications-blueprint/blob/dev/blueprints/automation/dabo53ck/bambu_printer_notifications.yaml`
2. Create a second automation from it next to your working one and disable the
   working one for the test. Snapshot file and notification tag are per
   automation, so they do not collide, but you would get two notifications.
3. Per iteration: push to `dev`, then **Settings → Automations & Scenes →
   Blueprints → ⋮ → Re-import blueprint**, reload automations, and start a print.
4. Read the trace (automation → ⋮ → **Traces**). The trigger should be the stage
   sensor, and the `camera.snapshot` step should be within a few dozen
   milliseconds of the trigger.

`raw.githubusercontent.com` caches for about five minutes. To skip the wait, add
a cache buster to the import URL: `…yaml?v=<timestamp>`.

**Important:** an import stamps the imported URL as the blueprint's
`source_url`, so "Re-import blueprint" keeps following `dev`. After the release,
re-import once from `main` so Home Assistant tracks `main` again. A deleted `dev`
branch would answer with a 404:
`https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/dabo53ck/bambu-printer-notifications-blueprint/blob/main/blueprints/automation/dabo53ck/bambu_printer_notifications.yaml`

Reloading blueprints and automations is enough; a Home Assistant restart is
never needed for this.
