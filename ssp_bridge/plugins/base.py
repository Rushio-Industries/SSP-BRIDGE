"""Plugin base classes.

Defines the minimal interface required by the runtime and auto-detect logic."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class TelemetryPlugin(ABC):
    """
    Base interface for simulator plugins.

    Contract:
      - open() prepares resources (shared memory, sockets, SDK, etc.)
      - read_frame() returns:
          * dict SSP frame when data is available
          * None when no fresh data is available yet (non-fatal)
        It should raise only on hard failure / stale mapping that requires reopen.
      - capabilities() returns a JSON-serializable capabilities dict
      - close() releases resources safely
    """

    id: str = "unknown"
    name: str = "Unknown Plugin"

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def read_frame(self) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def close(self) -> None:
        ...