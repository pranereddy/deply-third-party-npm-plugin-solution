from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from depsight.core.plugins.base import BasePlugin
from depsight.core.plugins.dependency import Dependency


class NpmPlugin(BasePlugin):
    """Depsight plugin that reads npm dependencies from package-lock.json."""

    def __init__(self) -> None:
        self.dependencies: list[Dependency] = []

    @property
    def name(self) -> str:
        return "npm"

    @property
    def dependency_files(self) -> tuple[str, ...]:
        return ("package-lock.json",)

    @property
    def default_file(self) -> str:
        return "package-lock.json"

    def collect(self, project_dir: str | Path, file: str | None = None) -> None:
        lockfile = Path(project_dir) / (file or self.default_file)
        if not lockfile.exists():
            self.dependencies = []
            return

        try:
            with lockfile.open(encoding="utf-8") as fh:
                lock_data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            self.dependencies = []
            return

        by_name: dict[str, Dependency] = {}

        packages = lock_data.get("packages")
        if isinstance(packages, dict):
            for package_path, package_data in packages.items():
                if package_path == "" or not isinstance(package_path, str):
                    continue
                if "node_modules/" not in package_path:
                    continue
                if not isinstance(package_data, dict):
                    continue

                name = package_path.rsplit("node_modules/", 1)[-1].strip("/")
                version = package_data.get("version")
                if not name or not isinstance(version, str) or not version:
                    continue
                by_name.setdefault(
                    name,
                    Dependency(name=name, version=version, tool_name=self.name),
                )
        else:
            self._collect_v1(lock_data.get("dependencies"), by_name)

        self.dependencies = sorted(by_name.values(), key=lambda dep: dep.name.lower())

    def _collect_v1(
        self,
        dependencies: Any,
        by_name: dict[str, Dependency],
    ) -> None:
        if not isinstance(dependencies, dict):
            return

        for dep_name, dep_info in dependencies.items():
            if not isinstance(dep_name, str) or not dep_name:
                continue
            if not isinstance(dep_info, dict):
                continue

            version = dep_info.get("version")
            if isinstance(version, str) and version:
                by_name.setdefault(
                    dep_name,
                    Dependency(name=dep_name, version=version, tool_name=self.name),
                )

            self._collect_v1(dep_info.get("dependencies"), by_name)
