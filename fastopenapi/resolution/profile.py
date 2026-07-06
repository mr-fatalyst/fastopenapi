import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastopenapi.core.constants import ParameterSource
from fastopenapi.core.params import Depends, Security
from fastopenapi.resolution.resolver import ParameterResolver


@dataclass(frozen=True)
class ExtractionProfile:
    """Which request payloads an endpoint (and its dependencies) consumes.

    Cheap always-available data (path, query, headers, cookies) is extracted
    unconditionally; only stream-consuming payloads are gated.
    """

    needs_body: bool = True
    needs_form: bool = True
    needs_files: bool = True


# Default when no profile is known: extract everything (safe fallback)
EXTRACT_ALL = ExtractionProfile()

_SOURCE_FLAGS = {
    ParameterSource.BODY: "needs_body",
    ParameterSource.FORM: "needs_form",
    ParameterSource.FILE: "needs_files",
}


class ExtractionProfileBuilder:
    """Compute and cache the extraction profile of an endpoint.

    Walks the endpoint signature (recursively through Depends/Security,
    which may declare their own Form/File/Body parameters) and records
    which payload kinds are actually referenced.
    """

    _cache: dict[Callable[..., Any], ExtractionProfile] = {}

    @classmethod
    def get(cls, endpoint: Callable[..., Any]) -> ExtractionProfile:
        profile = cls._cache.get(endpoint)
        if profile is None:
            try:
                flags = cls._collect(endpoint, seen=set())
            except Exception:
                # Unresolvable signature — fall back to extracting everything
                flags = {"needs_body": True, "needs_form": True, "needs_files": True}
            profile = ExtractionProfile(**flags)
            cls._cache[endpoint] = profile
        return profile

    @classmethod
    def _collect(
        cls, func: Callable[..., Any], seen: set[Callable[..., Any]]
    ) -> dict[str, bool]:
        flags = {"needs_body": False, "needs_form": False, "needs_files": False}
        params = ParameterResolver._get_signature(func)

        for name, param in params.items():
            default = param.default
            if isinstance(default, (Depends, Security)):
                dependency = default.dependency
                if dependency is None and callable(param.annotation):
                    # Depends() with the annotation acting as the factory
                    if param.annotation is not inspect.Parameter.empty:
                        dependency = param.annotation
                if dependency is not None and dependency not in seen:
                    seen.add(dependency)
                    for key, value in cls._collect(dependency, seen).items():
                        flags[key] = flags[key] or value
                continue

            source = ParameterResolver._determine_source(name, param, {}, None)
            flag = _SOURCE_FLAGS.get(source)
            if flag:
                flags[flag] = True

        return flags
