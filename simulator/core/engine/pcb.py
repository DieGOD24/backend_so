"""Process Control Block with execution and I/O bookkeeping for the simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .states import ProcessState


@dataclass(slots=True)
class PCB:
    """Minimal PCB structure enriched with execution time and optional I/O schedule."""

    pid: int
    arrival_time: int
    burst_time: int
    priority: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    remaining_time: int = field(init=False)
    state: ProcessState = field(default=ProcessState.NEW, init=False)
    start_time: int | None = field(default=None, init=False)
    finish_time: int | None = field(default=None, init=False)
    response_time: int | None = field(default=None, init=False)
    waiting_time: int | None = field(default=None, init=False)
    turnaround_time: int | None = field(default=None, init=False)
    executed_time: int = field(default=0, init=False)

    # I/O
    io_schedule: list[tuple[int, int]] = field(default_factory=list, init=False, repr=False)
    io_remaining_time: int | None = field(default=None, init=False)
    _next_io_index: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.remaining_time = self.burst_time

    def set_state(self, state: ProcessState) -> None:
        """Update PCB state; algorithms may hook extra bookkeeping before or after."""
        self.state = state

    def consume(self, time_slice: int) -> None:
        """
        Reduce remaining burst time after execution.

        This function does not validate the time slice, so callers must avoid
        passing values larger than the remaining time.
        """
        self.remaining_time = max(0, self.remaining_time - time_slice)
        self.executed_time += time_slice

    # ---------- I/O helpers ----------

    def prepare_io_schedule(
        self,
        *,
        interval_mean: float,
        interval_stddev: float,
        duration_mean: float,
        duration_stddev: float,
        max_events: int | None = None,
        enabled: bool = True,
    ) -> None:
        """
        Attach an I/O schedule generated from normal distributions.

        Each event is a tuple (cpu_time_at_request, io_duration). Events are
        bounded to the total burst time to avoid overshooting completion.
        """
        if not enabled or interval_mean <= 0 or duration_mean <= 0:
            self.io_schedule = []
            return

        import random

        events: list[tuple[int, int]] = []
        cpu_cursor = 0
        while True:
            if max_events is not None and len(events) >= max_events:
                break
            gap = max(1, round(random.normalvariate(interval_mean, interval_stddev)))
            cpu_cursor += gap
            if cpu_cursor >= self.burst_time:
                break
            duration = max(1, round(random.normalvariate(duration_mean, duration_stddev)))
            events.append((cpu_cursor, duration))
        self.io_schedule = events
        self._next_io_index = 0

    def io_request_due(self) -> tuple[bool, int | None]:
        """Return whether an I/O should start after the last CPU consumption."""
        if self._next_io_index >= len(self.io_schedule):
            return (False, None)
        trigger_at, duration = self.io_schedule[self._next_io_index]
        if self.executed_time >= trigger_at and self.remaining_time > 0:
            self._next_io_index += 1
            self.io_remaining_time = duration
            return (True, duration)
        return (False, None)

    def tick_io(self) -> None:
        """Advance I/O timer for a blocked process."""
        if self.io_remaining_time is None:
            return
        self.io_remaining_time = max(0, self.io_remaining_time - 1)
        if self.io_remaining_time == 0:
            self.io_remaining_time = None
