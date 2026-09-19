"""Behaviour of the blueprint, one print scenario per test."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util.yaml import load_yaml

from .conftest import (
    AUTOMATION_KEY,
    BLUEPRINT_PATH,
    ERROR,
    LIGHT,
    PRINTER_NAME,
    PROGRESS,
    STAGE,
    STATUS,
    Printer,
)


async def test_home_assistant_accepts_the_blueprint(
    hass: HomeAssistant, setup_blueprint: Any
) -> None:
    await setup_blueprint()

    assert hass.states.get(f"automation.{AUTOMATION_KEY}").state == "on"


def test_declared_minimum_version() -> None:
    metadata = load_yaml(str(BLUEPRINT_PATH))["blueprint"]
    assert metadata["homeassistant"]["min_version"] == "2024.10.0"


class TestSnapshotTiming:
    async def test_snapshot_is_taken_when_the_stage_ends_not_when_the_print_does(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()

        await printer.state(STAGE, "idle")

        assert len(printer.calls.snapshot) == 1
        assert printer.calls.notify == []

    async def test_notification_follows_once_status_and_progress_are_final(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(STAGE, "idle")

        await printer.finish_print()
        await printer.advance(2)

        assert len(printer.calls.notify) == 1
        assert printer.calls.notify[0].data["message"].split("\n") == [
            "✅ Print Successful",
            "File: benchy.3mf",
            "Weight: 12.4g",
            "Progress: 100%",
            "Time: 12:00:02",
        ]
        assert len(printer.calls.snapshot) == 1

    async def test_snapshot_delay_is_honoured(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(snapshot_delay_seconds=3)

        await printer.state(STAGE, "idle")
        assert printer.calls.snapshot == []

        await printer.advance(3)
        assert len(printer.calls.snapshot) == 1


class TestTriggers:
    async def test_stage_change_within_the_print_does_not_trigger(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()

        await printer.state(STAGE, "inspecting_first_layer")
        await printer.state(STAGE, "printing")

        assert printer.calls.snapshot == []
        assert printer.calls.notify == []

    async def test_mqtt_dropout_mid_print_does_not_trigger(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()

        await printer.state(STAGE, "unavailable")

        assert printer.calls.snapshot == []

    async def test_progress_fallback_fires_when_progress_skips_to_100(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(PROGRESS, 97)
        assert printer.calls.snapshot == []

        await printer.state(PROGRESS, 100)
        await printer.state(STATUS, "finish")
        await printer.advance(2)

        assert len(printer.calls.notify) == 1

    async def test_progress_returning_from_unavailable_is_not_a_finished_print(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(PROGRESS, "unavailable")

        await printer.state(PROGRESS, 100)

        assert printer.calls.snapshot == []

    async def test_late_triggers_of_the_same_print_are_dropped(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        """Stage, progress and status all fire; only one snapshot and one message."""
        await setup_blueprint()

        await printer.state(STAGE, "idle")
        await printer.state(PROGRESS, 100)
        await printer.state(STATUS, "finish")
        await printer.advance(2)

        assert len(printer.calls.snapshot) == 1
        assert len(printer.calls.notify) == 1

    async def test_disabled_switch_blocks_everything(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state("input_boolean.bambu_notifications", "off")

        await printer.state(STAGE, "idle")

        assert printer.calls.snapshot == []

    async def test_unavailable_printer_name_blocks_the_run(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(PRINTER_NAME, "unavailable")

        await printer.state(STAGE, "idle")

        assert printer.calls.snapshot == []


class TestWaitingForTheEnd:
    async def test_finish_that_already_became_idle_does_not_wait(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        """The 10 minute delay: `finish` is gone before the wait even starts."""
        await setup_blueprint()
        await printer.state(STATUS, "idle")

        await printer.state(STAGE, "idle")
        await printer.advance(2)

        assert len(printer.calls.notify) == 1

    async def test_status_already_finished_does_not_wait(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(PROGRESS, 100)
        await printer.state(STATUS, "finish")
        await printer.advance(2)
        printer.calls.notify.clear()

        await printer.state(STATUS, "running")
        await printer.state(STAGE, "idle")
        await printer.state(STATUS, "finish")
        await printer.advance(2)

        assert len(printer.calls.notify) == 1

    async def test_run_ends_silently_after_ten_minutes_and_the_next_print_works(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(STAGE, "idle")

        await printer.advance(11 * 60)
        assert printer.calls.notify == []

        await printer.state(STATUS, "running")
        await printer.state(STATUS, "finish")
        await printer.advance(2)
        assert len(printer.calls.notify) == 1

    async def test_sensor_dropout_while_waiting_is_not_reported_as_success(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(STAGE, "idle")

        await printer.state(STATUS, "unavailable")
        await printer.advance(2)

        assert printer.calls.notify == []


class TestFaults:
    async def test_failed_print_is_reported_as_fault(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(
            fault_actions=[{"action": "test.on_fault"}],
            success_actions=[{"action": "test.on_success"}],
        )
        await printer.state(PROGRESS, 63)

        await printer.state(STATUS, "failed")
        await printer.advance(2)

        [call] = printer.calls.notify
        assert call.data["title"] == "P1S FAULT"
        assert call.data["message"].split("\n") == [
            "❌ Print Failed",
            "File: benchy.3mf",
            "Progress: 63%",
            "Status: failed",
            "Time: 12:00:02",
        ]
        assert call.data["data"]["sticky"] is True
        assert call.data["data"]["persistent"] is True
        assert len(printer.calls.persistent) == 1
        assert len(printer.calls.on_fault) == 1
        assert printer.calls.on_success == []

    async def test_fault_at_zero_progress_is_still_reported(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(PROGRESS, 0)
        await printer.state(STAGE, "heatbed_preheating")

        await printer.state(ERROR, "on")
        await printer.advance(2)

        [call] = printer.calls.notify
        assert call.data["title"] == "P1S FAULT"

    async def test_fault_stays_a_fault_when_the_error_flag_clears_again(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(ERROR, "on")
        await printer.state(ERROR, "off")
        await printer.advance(2)

        [call] = printer.calls.notify
        assert call.data["title"] == "P1S FAULT"


class TestDelivery:
    async def test_the_service_of_a_selected_device_carries_image_tag_and_flags(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        await printer.state(STAGE, "idle")
        await printer.finish_print()
        await printer.advance(2)

        [call] = printer.calls.notify
        data = call.data["data"]
        assert call.data["title"] == "P1S Print Complete"
        # No query string: the iOS Companion App answers such URLs with a 404.
        assert data["image"] == f"/local/snapshots/{AUTOMATION_KEY}.jpg"
        assert data["tag"] == f"bambu_print_{AUTOMATION_KEY}"
        assert data["sticky"] is False
        assert data["persistent"] is False
        assert data["actions"] == []
        assert printer.calls.snapshot[0].data["filename"] == (
            f"/config/www/snapshots/{AUTOMATION_KEY}.jpg"
        )

    async def test_every_selected_device_is_notified(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(
            notify_devices=[printer.add_phone("phone"), printer.add_phone("tablet")]
        )
        await printer.state(STATUS, "failed")
        await printer.advance(2)

        assert len(printer.calls.phones["phone"]) == 1
        assert len(printer.calls.phones["tablet"]) == 1

    async def test_a_device_that_is_not_selected_is_not_notified(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()
        printer.add_phone("someone_else")

        await printer.state(STATUS, "failed")
        await printer.advance(2)

        assert len(printer.calls.notify) == 1
        assert printer.calls.phones["someone_else"] == []

    async def test_printers_view_becomes_an_action_button(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(printers_view_uri="/lovelace/3d_printers")
        await printer.state(STATUS, "failed")
        await printer.advance(2)

        [call] = printer.calls.notify
        assert call.data["data"]["actions"] == [
            {"action": "URI", "title": "Open Printers", "uri": "/lovelace/3d_printers"}
        ]

    async def test_without_devices_only_the_other_outputs_run(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(
            notify_devices=[], fault_actions=[{"action": "test.on_fault"}]
        )
        await printer.state(STATUS, "failed")
        await printer.advance(2)

        assert printer.calls.phones == {}
        assert len(printer.calls.persistent) == 1
        assert len(printer.calls.on_fault) == 1

    async def test_a_device_without_the_legacy_service_does_not_block_the_other_outputs(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(
            notify_devices=[
                printer.add_phone("phone"),
                printer.add_phone("no_service", service=False),
            ],
            fault_actions=[{"action": "test.on_fault"}],
        )
        await printer.state(STATUS, "failed")
        await printer.advance(2)

        assert len(printer.calls.notify) == 1
        assert len(printer.calls.persistent) == 1
        assert len(printer.calls.on_fault) == 1

    async def test_success_custom_actions_run(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(success_actions=[{"action": "test.on_success"}])
        await printer.state(STAGE, "idle")
        await printer.finish_print()
        await printer.advance(2)

        assert len(printer.calls.on_success) == 1
        assert printer.calls.on_fault == []


class TestTimeInTheMessage:
    @pytest.mark.parametrize(
        ("time_format", "expected"),
        [("24h", "Time: 14:05:09"), ("12h", "Time: 02:05:09 PM")],
    )
    @pytest.mark.parametrize("failed", [False, True])
    async def test_time_with_seconds_in_success_and_fault(
        self,
        setup_blueprint: Any,
        printer: Printer,
        time_format: str,
        expected: str,
        failed: bool,
    ) -> None:
        await setup_blueprint(time_format=time_format)
        printer.freezer.move_to("2026-09-19 14:05:07+00:00")

        if failed:
            await printer.state(STATUS, "failed")
        else:
            await printer.finish_print()
        await printer.advance(2)

        assert expected in printer.calls.notify[0].data["message"]

    async def test_default_is_24h(self, setup_blueprint: Any, printer: Printer) -> None:
        await setup_blueprint()
        printer.freezer.move_to("2026-09-19 21:30:00+00:00")

        await printer.state(STATUS, "failed")
        await printer.advance(2)

        assert "Time: 21:30:02" in printer.calls.notify[0].data["message"]


class TestCriticalAlerts:
    @pytest.mark.parametrize(
        ("options", "now", "critical"),
        [
            ({"success_notification_type": "critical"}, "12:00:00", True),
            ({"success_notification_type": "critical"}, "22:00:00", False),
            ({"success_notification_type": "normal"}, "12:00:00", False),
            ({"success_notification_type": "never_critical"}, "12:00:00", False),
            (
                {
                    "success_notification_type": "critical",
                    "success_critical_start": "09:00:00",
                    "success_critical_end": "09:00:00",
                },
                "09:00:00",
                False,
            ),
            (
                {
                    "success_notification_type": "critical",
                    "success_critical_start": "22:00:00",
                    "success_critical_end": "06:00:00",
                },
                "23:30:00",
                True,
            ),
            (
                {
                    "success_notification_type": "critical",
                    "success_critical_start": "22:00:00",
                    "success_critical_end": "06:00:00",
                },
                "12:00:00",
                False,
            ),
        ],
    )
    async def test_success_window(
        self,
        setup_blueprint: Any,
        printer: Printer,
        options: dict[str, str],
        now: str,
        critical: bool,
    ) -> None:
        await setup_blueprint(**options)
        printer.freezer.move_to(f"2026-09-19 {now}+00:00")

        await printer.finish_print()
        await printer.advance(2)

        push = printer.calls.notify[0].data["data"]["push"]
        if critical:
            assert push == {"sound": {"name": "default", "critical": 1, "volume": 1.0}}
        else:
            assert push == {}

    async def test_fault_is_critical_by_default_inside_the_window(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(critical_sound="alert", critical_volume=0.5)

        await printer.state(STATUS, "failed")
        await printer.advance(2)

        push = printer.calls.notify[0].data["data"]["push"]
        assert push == {"sound": {"name": "alert", "critical": 1, "volume": 0.5}}


class TestSnapshotLight:
    async def test_light_is_on_for_the_photo_and_off_again_afterwards(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(snapshot_light=LIGHT, snapshot_light_brightness=40)

        await printer.state(STAGE, "idle")

        [on] = printer.calls.light_on
        assert on.data["brightness_pct"] == 40
        assert len(printer.calls.snapshot) == 1
        assert len(printer.calls.light_off) == 1

    async def test_light_that_was_on_returns_to_its_brightness(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint(snapshot_light=LIGHT)
        printer.hass.states.async_set(LIGHT, "on", {"brightness": 77})

        await printer.state(STAGE, "idle")

        assert printer.calls.light_off == []
        assert printer.calls.light_on[-1].data["brightness"] == 77

    async def test_no_light_is_touched_when_none_is_configured(
        self, setup_blueprint: Any, printer: Printer
    ) -> None:
        await setup_blueprint()

        await printer.state(STAGE, "idle")

        assert printer.calls.light_on == []
        assert printer.calls.light_off == []
