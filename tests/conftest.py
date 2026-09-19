"""Drive the blueprint through the real Home Assistant automation engine.

Entities are plain states and every service the blueprint calls is a recording
mock, so a test reads like a print: set states, advance the clock, assert on
the calls.
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

BLUEPRINT_PATH = (
    Path(__file__).resolve().parent.parent
    / "blueprints/automation/dabo53ck/bambu_printer_notifications.yaml"
)
BLUEPRINT_RELATIVE = "dabo53ck/bambu_printer_notifications.yaml"

AUTOMATION_ALIAS = "P1S Notify"
AUTOMATION_KEY = "p1s_notify"

STATUS = "sensor.p1s_print_status"
STAGE = "sensor.p1s_current_stage"
PROGRESS = "sensor.p1s_print_progress"
PRINTER_NAME = "sensor.p1s_printer_name"
TASK_NAME = "sensor.p1s_task_name"
WEIGHT = "sensor.p1s_print_weight"
ERROR = "binary_sensor.p1s_print_error"
CAMERA = "camera.p1s_camera"
ENABLED = "input_boolean.bambu_notifications"
LIGHT = "light.p1s_chamber"

REQUIRED_INPUTS = {
    "print_status_sensor": STATUS,
    "print_error_binary": ERROR,
    "current_stage_sensor": STAGE,
    "progress_sensor": PROGRESS,
    "printer_name_sensor": PRINTER_NAME,
    "task_name_sensor": TASK_NAME,
    "print_weight_sensor": WEIGHT,
    "camera": CAMERA,
    "notifications_enabled_boolean": ENABLED,
    # Zero snapshot delay keeps the clock arithmetic in most tests trivial.
    "snapshot_delay_seconds": 0,
    "notify_device": "mobile_app_phone",
}


@dataclass
class Calls:
    notify: list[ServiceCall] = field(default_factory=list)
    send_message: list[ServiceCall] = field(default_factory=list)
    snapshot: list[ServiceCall] = field(default_factory=list)
    light_on: list[ServiceCall] = field(default_factory=list)
    light_off: list[ServiceCall] = field(default_factory=list)
    persistent: list[ServiceCall] = field(default_factory=list)
    on_success: list[ServiceCall] = field(default_factory=list)
    on_fault: list[ServiceCall] = field(default_factory=list)


class Printer:
    """A Bambu printer as the automation sees it."""

    def __init__(self, hass: HomeAssistant, freezer: Any, calls: Calls) -> None:
        self.hass = hass
        self.freezer = freezer
        self.calls = calls

    @staticmethod
    async def settle() -> None:
        """Let the automation run until it waits or finishes.

        async_block_till_done() cannot be used: a run parked in wait_template
        under a frozen clock would keep it waiting forever.
        """
        for _ in range(100):
            await asyncio.sleep(0)

    async def state(self, entity_id: str, value: str | int) -> None:
        self.hass.states.async_set(entity_id, str(value))
        await self.settle()

    async def advance(self, seconds: float) -> None:
        self.freezer.tick(timedelta(seconds=seconds))
        async_fire_time_changed(self.hass)
        await self.settle()

    async def finish_print(self) -> None:
        """Status and progress reach their final values."""
        await self.state(PROGRESS, 100)
        await self.state(STATUS, "finish")


@pytest.fixture
def calls(hass: HomeAssistant) -> Calls:
    recorded = Calls()
    recorded.notify = async_mock_service(hass, "notify", "mobile_app_phone")
    recorded.send_message = async_mock_service(hass, "notify", "send_message")
    recorded.snapshot = async_mock_service(hass, "camera", "snapshot")
    recorded.light_on = async_mock_service(hass, "light", "turn_on")
    recorded.light_off = async_mock_service(hass, "light", "turn_off")
    recorded.persistent = async_mock_service(hass, "persistent_notification", "create")
    recorded.on_success = async_mock_service(hass, "test", "on_success")
    recorded.on_fault = async_mock_service(hass, "test", "on_fault")
    return recorded


@pytest.fixture
def printer(hass: HomeAssistant, freezer: Any, calls: Calls) -> Printer:
    return Printer(hass, freezer, calls)


@pytest.fixture
async def setup_blueprint(
    hass: HomeAssistant, tmp_path: Path, freezer: Any, printer: Printer
):
    """Install the blueprint and create one automation from it."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2026-09-19 12:00:00+00:00")

    async def _setup(**overrides: Any) -> None:
        target = tmp_path / "blueprints/automation" / BLUEPRINT_RELATIVE
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(BLUEPRINT_PATH, target)
        hass.config.config_dir = str(tmp_path)

        inputs = {**REQUIRED_INPUTS, **overrides}

        hass.states.async_set(STATUS, "running")
        hass.states.async_set(STAGE, "printing")
        hass.states.async_set(PROGRESS, "50")
        hass.states.async_set(PRINTER_NAME, "P1S")
        hass.states.async_set(TASK_NAME, "benchy.3mf")
        hass.states.async_set(WEIGHT, "12.4")
        hass.states.async_set(ERROR, "off")
        hass.states.async_set(ENABLED, "on")
        hass.states.async_set(LIGHT, "off")

        assert await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "alias": AUTOMATION_ALIAS,
                    "use_blueprint": {"path": BLUEPRINT_RELATIVE, "input": inputs},
                }
            },
        )
        await hass.async_block_till_done()

    return _setup
