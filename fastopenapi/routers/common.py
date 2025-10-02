from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class RequestEnvelope:
    """Unified wrapper for requests."""

    path_params: dict[str, str]
    request: Any | None
