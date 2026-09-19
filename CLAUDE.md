# Repository guide

Home Assistant **blueprint** for Bambu Lab printers — one automation blueprint
plus its tests, docs and CI. Not a Python package. The root
`Claude Code/CLAUDE.md` applies as well (never restart Home Assistant).

## Layout

- `blueprints/automation/dabo53ck/bambu_printer_notifications.yaml` — the blueprint (all logic lives here)
- `tests/` — pytest scenarios against the real Home Assistant automation engine
- `tests/fixtures/check_config/automations.yaml` — CI fixture: drives the blueprint with every input set
- `scripts/validate_blueprints.py` — static checks (inputs, metadata, doc links, version consistency)
- `docs/` — how-it-works, migration, testing
- `.github/` — CI (`validate.yml`, `tests.yml`), issue forms, PR template, Dependabot

## Branches

- `main` is what users import (the blueprint's `source_url` and the README badge point at it). It is always releasable.
- `dev` exists **only while there is something to test on the live Home Assistant**. Create it from `main`, work on it (or on topic branches merged into it), test with the import loop in `docs/testing.md`.
- At **every release** `dev` is deleted, locally and on GitHub. The next round of testing starts a fresh `dev` from `main`.
- Changes that need no live test (docs, CI, typos) go through a short-lived topic branch (`fix/…`, `feat/…`, `docs/…`) straight to `main`.
- Conventional Commits.

## Releases

Tags are `vX.Y.Z` or `vX.Y.Z-beta`; the CHANGELOG heading has no `v`.

1. One PR `dev` → `main` with the version bumped in the blueprint description badge and the CHANGELOG heading (`## [X.Y.Z-beta] - <release date>`). `scripts/validate_blueprints.py` fails if the two disagree.
2. Merge, then tag `vX.Y.Z-beta` on `main`.
3. GitHub release from the CHANGELOG section. **Not marked as pre-release**, marked as **Latest**, also for `-beta` versions: `gh release create vX.Y.Z-beta --latest --notes-file …`.
4. Delete `dev` (local and remote).
5. Re-import the blueprint once from `main` on the live Home Assistant (an import from `dev` stamps that URL as `source_url`).

## Conventions

- Input keys are a public API: never rename or remove one without a CHANGELOG entry and a migration note. New inputs need a `default` (only entity pickers may be required), an entry in the README tables and in `tests/fixtures/check_config/automations.yaml`.
- Entity pickers filter by `domain` only, never by `integration`: while the printer is off its integration is not loaded and such a picker lists nothing.
- A behaviour change or bug fix needs a test first. The suite is the specification.
- Blueprint edits must keep `yamllint`, `scripts/validate_blueprints.py`, `pytest` and `check_config` green.
- Documents must never link to a blueprint path that does not exist; the validator checks this.
- README, docs and code comments are in English.

## Commit messages

Do **not** add AI / assistant attribution to commit messages or PR descriptions:
no `Co-Authored-By:` line naming an AI, no `Claude-Session:` line, no
"Generated with …" footer. Commits are authored solely by the repository owner.

A `commit-msg` hook enforces this — enable it once per clone:

```sh
git config core.hooksPath .githooks
```
