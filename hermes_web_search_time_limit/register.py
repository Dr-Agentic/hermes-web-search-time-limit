"""Hermes plugin registration entry point.

Called by Hermes at startup when the plugin is loaded.
"""

from hermes_web_search_time_limit.provider import DDGSWebSearchTimeLimitProvider


def register(ctx) -> None:
    """Register the DDGS time-limited search provider with the Hermes plugin context."""
    ctx.register_web_search_provider(DDGSWebSearchTimeLimitProvider())
