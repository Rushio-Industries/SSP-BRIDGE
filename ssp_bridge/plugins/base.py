from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class TelemetryPlugin(ABC):
    """
    Base interface for simulator plugins.

    Contract:
      - open() must prepare any resources (shared memory, sockets, SDK, etc.)
      - read_frame() must return a JSON-serializable SSP Frame dict
      - capabilities() must return a JSON-serializable capabilities dict
      - close() must release resources safely
    """

    # short id used in CLI: --game ac
    id: str = "unknown"

    # human-friendly name
    name: str = "Unknown Plugin"

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def read_frame(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def close(self) -> None:
        ...
