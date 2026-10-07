from pathlib import Path

import tomllib


def test_package_declares_nemo_entry_point() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text())
    entry_points = data["project"]["entry-points"]["nat.plugins"]
    assert entry_points["affixio_nemo"] == "affixio_nemo.register"


def test_runtime_dependencies_are_declared() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text())
    dependencies = data["project"]["dependencies"]
    assert any(item.startswith("httpx") for item in dependencies)
    assert any(item.startswith("pydantic") for item in dependencies)
