"""Finite set of valid Process Control Block states."""

from enum import Enum


class ProcessState(str, Enum):
    """Life-cycle states for each simulated process."""

    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    TERMINATED = "TERMINATED"
