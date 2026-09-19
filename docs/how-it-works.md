# How the end of a print is detected

The blueprint reacts to the end of a print in three steps: it notices the end,
takes the snapshot immediately, and sends the notification once the printer
reports its final values.

## Why not a progress threshold

The progress sensor is the obvious trigger, and it does not work reliably on a
Bambu P1S. Recorded sensor history from a real print:

| Time | Sensor | Change |
| ---- | ------ | ------ |
| 19:47:54.282 | current stage | `printing` → `idle` |
| 19:47:54.289 | progress | 96 → **97 %** |
| 19:48:35.750 | progress | 97 → **100 %** |
| 19:48:35.759 | print status | `running` → `finish` |

- **Progress skips values.** It went from 97 % straight to 100 %. A threshold of
  98 % or 99 % is never crossed as a distinct value; it fires on the jump to
  100 %, when the print is already over.
- **The plate is already moving.** Between the stage change and the progress and
  status update lie about 41 seconds in which the P1S lowers the build plate. A
  snapshot taken at the later timestamp shows a plate on its way down.

The stage sensor leaves `printing` at the start of that window and is a
discrete state change that cannot be skipped. That is the primary trigger.

## Triggers

| Trigger id | Fires when | Role |
| ---------- | ---------- | ---- |
| `stage_ended` | stage goes from `printing`, `inspecting_first_layer` or `auto_bed_leveling` to `idle` | primary, earliest signal |
| `progress_threshold` | progress rises above 99 | fallback for a missing stage sensor or other models |
| `status_finish` | status `running` → `finish` | fallback |
| `status_failed` | status `running`, `prepare` or `pause` → `failed` | fault |
| `error_detected` | the error binary sensor turns on | fault |

Only the change *to* `idle` counts for the stage trigger. Stages also change
inside a print (`printing` → `inspecting_first_layer` at the first layer), and
those must not look like the end.

## Run order

1. **Snapshot**, immediately. Optionally with the snapshot light on.
2. **Wait until the print has ended**: status `finish`, `failed` or `idle`, or the
   error sensor on, for at most 10 minutes. The check uses the *current* state
   first. `finish` is short-lived and often already `idle` by the time this step
   runs; waiting for a change that has already happened would sit out the
   whole timeout.
3. **Two seconds** for the remaining sensors to settle.
4. **Read the final values** for progress, status and weight. The stage trigger
   fires before they are final; without this the message would say 97 %.
5. **Deliver**: the notification to each selected device, the persistent
   notification (faults) and the custom actions run independently of each other.

## One run at a time

`mode: single` with `max_exceeded: silent`. Stage, progress and status triggers
all fire for the same print. Only the first starts a run; the others are
dropped. Otherwise they would overwrite the correctly timed snapshot and replace
the notification. In the automation trace, a discarded run shows up as
`failed_single`; that is expected, not a second notification.
