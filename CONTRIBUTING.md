# Contributing

Bug reports, ideas and pull requests are welcome.

## Reporting a problem

Use the [issue forms](https://github.com/dabo53ck/bambu-printer-notifications-blueprint/issues/new/choose).
The automation trace matters most: it shows which trigger fired and when. For
questions about how to use the blueprint, use Discussions.

Missing or wrong printer entities are a matter for the
[Bambu Lab integration](https://github.com/greghesp/ha-bambulab/issues).

## Making a change

1. Fork the repository and branch from `main` (`fix/…`, `feat/…`, `docs/…`).
2. Write a test for the behaviour first (see [docs/testing.md](docs/testing.md)).
3. Keep the checks green:

   ```bash
   yamllint -c .yamllint.yml blueprints tests/fixtures .github
   python scripts/validate_blueprints.py
   pytest
   ```

4. Add a line to the `Unreleased` part of [CHANGELOG.md](CHANGELOG.md). A new
   input also goes into the README tables and
   `tests/fixtures/check_config/automations.yaml`.
5. Open a pull request against `main`. Use [Conventional Commits](https://www.conventionalcommits.org/) for the commit messages.

Home Assistant does not run on native Windows; run the tests on Linux, macOS,
WSL or in a container.

## Input keys are a public API

Existing automations store inputs by key. Renaming or removing one breaks every
automation that uses it, so it needs a CHANGELOG entry and a migration note.

## Maintainers

`main` is always releasable. A short-lived `dev` branch exists only while a
change is being tested on a live Home Assistant and is deleted at every release.
The full procedure is in [CLAUDE.md](CLAUDE.md).
