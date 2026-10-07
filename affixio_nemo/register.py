from __future__ import annotations

try:
    from nat.plugin_api import Builder, register_middleware
except ImportError:
    Builder = object
    register_middleware = None

from .middleware import AffixIONeMoGuard, AffixIONeMoGuardConfig

if register_middleware is not None:

    @register_middleware(config_type=AffixIONeMoGuardConfig)
    async def affixio_guard(config: AffixIONeMoGuardConfig, builder: Builder):
        guard = AffixIONeMoGuard(config=config, builder=builder)
        try:
            yield guard
        finally:
            await guard.aclose()
