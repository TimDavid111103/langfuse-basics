"""Lightweight in-process event bus for pipeline extensibility."""

from collections import defaultdict
from collections.abc import Callable
from typing import Any

EventHandler = Callable[[Any], None]


class EventBus:
    """Subscribe handlers to event types and emit events synchronously."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    def emit(self, event: Any) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)

    def clear(self) -> None:
        self._handlers.clear()


_default_bus = EventBus()


def get_event_bus() -> EventBus:
    return _default_bus


def reset_event_bus() -> None:
    """Clear all handlers; intended for tests."""
    _default_bus.clear()
