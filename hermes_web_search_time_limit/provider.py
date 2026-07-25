"""DuckDuckGo timed search provider.

Searches DuckDuckGo with a time filter (past day / week / month / year).
No API key required — uses the ``ddgs`` Python package.

This provider is framework-agnostic: it implements the Hermes
:class:`agent.web_search_provider.WebSearchProvider` interface so it can be
registered as a Hermes plugin, but the core ``search()`` method has no Hermes
dependencies and can be called directly.
"""

from __future__ import annotations

import concurrent.futures as _cf
import logging
from typing import Any, Dict

try:
    from agent.web_search_provider import WebSearchProvider
except ImportError:
    # Standalone mode: define a minimal ABC stub so the class is importable
    # without the full Hermes codebase.
    import abc
    class WebSearchProvider(abc.ABC):
        @property
        @abc.abstractmethod
        def name(self) -> str: ...
        def is_available(self) -> bool: return False
        def supports_search(self) -> bool: return True
        def supports_extract(self) -> bool: return False
        def search(self, query: str, limit: int = 5, **kwargs: Any) -> Dict[str, Any]: ...

logger = logging.getLogger(__name__)

_SEARCH_TIMEOUT_SECS = 30

_VALID_TIME_RANGES = frozenset({"d", "w", "m", "y"})

_TIME_RANGE_MAP = {"d": "d", "w": "w", "m": "m", "y": "y"}


def _run_ddgs_timed_search(
    query: str, safe_limit: int, time_range: str | None
) -> list[dict[str, Any]]:
    """Run the blocking ddgs query with an optional time filter.

    Module-level so tests can patch it without spawning a real thread.
    """
    from ddgs import DDGS  # type: ignore

    results: list[dict[str, Any]] = []
    with DDGS(timeout=10) as client:
        ddgs_timelimit = _TIME_RANGE_MAP.get(time_range) if time_range else None
        for i, hit in enumerate(
            client.text(query, timelimit=ddgs_timelimit, max_results=safe_limit)
        ):
            if i >= safe_limit:
                break
            url = str(hit.get("href") or hit.get("url") or "")
            results.append(
                {
                    "title": str(hit.get("title", "")),
                    "url": url,
                    "description": str(hit.get("body", "")),
                    "position": i + 1,
                }
            )
    return results


class DDGSWebSearchTimeLimitProvider(WebSearchProvider):
    """DuckDuckGo search with time filtering.

    Supports ``time_range`` = ``d`` (past 24 h), ``w`` (past week),
    ``m`` (past month), ``y`` (past year).  Other backends that inherit
    from :class:`WebSearchProvider` but do not support time filtering can
    simply ignore the ``time_range`` kwarg they receive via ``**kwargs``.
    """

    @property
    def name(self) -> str:
        return "hermes-web-search-time-limit"

    @property
    def display_name(self) -> str:
        return "DuckDuckGo — Time-Limited Search"

    def is_available(self) -> bool:
        """Return True when the ``ddgs`` package is importable."""
        try:
            import ddgs  # noqa: F401
            return True
        except ImportError:
            return False

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return False

    def search(
        self, query: str, limit: int = 5, **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute a DuckDuckGo search with optional time filtering.

        Args:
            query: Search query string.
            limit: Maximum number of results.
            time_range: Optional time filter — ``d``, ``w``, ``m``, or ``y``.
                Passed via ``**kwargs`` so backends that don't support time
                filtering can ignore it.

        Returns:
            ``{"success": True, "data": {"web": [...]}}`` or
            ``{"success": False, "error": "..."}``.
        """
        try:
            import ddgs  # type: ignore  # noqa: F401
        except ImportError:
            return {
                "success": False,
                "error": "ddgs package is not installed — run `pip install ddgs`",
            }

        safe_limit = max(1, int(limit))
        time_range: str | None = kwargs.get("time_range")

        if time_range is not None and time_range not in _VALID_TIME_RANGES:
            return {
                "success": False,
                "error": (
                    f"Invalid time_range '{time_range}'. "
                    f"Must be one of: {', '.join(sorted(_VALID_TIME_RANGES))}"
                ),
            }

        pool = _cf.ThreadPoolExecutor(max_workers=1)
        try:
            future = pool.submit(
                _run_ddgs_timed_search, query, safe_limit, time_range
            )
            try:
                web_results = future.result(timeout=_SEARCH_TIMEOUT_SECS)
            except _cf.TimeoutError:
                logger.warning(
                    "DDGS timed search timed out after %ds for query: %r",
                    _SEARCH_TIMEOUT_SECS,
                    query,
                )
                return {
                    "success": False,
                    "error": (
                        f"DuckDuckGo timed search timed out after {_SEARCH_TIMEOUT_SECS}s — "
                        "DuckDuckGo may be rate-limiting or slow. Try again later."
                    ),
                }
        except Exception as exc:  # noqa: BLE001
            logger.warning("DDGS timed search error: %s", exc)
            return {
                "success": False,
                "error": f"DuckDuckGo timed search failed: {exc}",
            }
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

        logger.info(
            "DDGS timed search '%s' (time_range=%s): %d results",
            query,
            time_range,
            len(web_results),
        )
        return {"success": True, "data": {"web": web_results}}


# ---------------------------------------------------------------------------
# Hermes plugin entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Register this provider with the Hermes plugin context.

    This function is called by Hermes when the plugin is loaded.
    It is only present when running inside a Hermes environment.
    """
    ctx.register_web_search_provider(DDGSWebSearchTimeLimitProvider())
