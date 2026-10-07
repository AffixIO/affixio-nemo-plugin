import os

import pytest
from affixio_nemo.exceptions import AffixIOConfigurationError
from affixio_nemo.middleware import AffixIONeMoGuard, AffixIONeMoGuardConfig
from pydantic import SecretStr


def test_config_rejects_missing_api_key(monkeypatch) -> None:
    monkeypatch.delenv("AFFIXIO_API_KEY", raising=False)
    with pytest.raises(AffixIOConfigurationError):
        AffixIONeMoGuard(AffixIONeMoGuardConfig())


def test_config_uses_environment_api_key(monkeypatch) -> None:
    monkeypatch.setenv("AFFIXIO_API_KEY", "aio_env")
    guard = AffixIONeMoGuard(AffixIONeMoGuardConfig())
    try:
        assert guard._client.config.api_key.get_secret_value() == "aio_env"
    finally:
        os.environ.pop("AFFIXIO_API_KEY", None)


def test_config_prefers_explicit_api_key(monkeypatch) -> None:
    monkeypatch.setenv("AFFIXIO_API_KEY", "aio_env")
    guard = AffixIONeMoGuard(AffixIONeMoGuardConfig(api_key=SecretStr("aio_explicit")))
    assert guard._client.config.api_key.get_secret_value() == "aio_explicit"
