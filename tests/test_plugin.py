from __future__ import annotations

import csv
from pathlib import Path

# third-party imports
from depsight.core.plugins.base import BasePlugin
from npm.npm import NpmPlugin


class TestCollect:
    """Verify collect() populates dependencies correctly."""

    def test_plugin_implements_base_plugin_contract(self):
        plugin = NpmPlugin()

        assert isinstance(plugin, BasePlugin)
        assert plugin.name == "npm"
        assert plugin.default_file == "package-lock.json"
        assert "package-lock.json" in plugin.dependency_files
        assert isinstance(plugin.default_file, str)
        assert plugin.default_file.strip()
        assert Path(plugin.default_file).name == plugin.default_file
        assert plugin.default_file not in {".", ".."}
        assert plugin.default_file in plugin.dependency_files

    def test_collect_dependency_details(self):
        plugin = NpmPlugin()
        fixture_dir = Path(__file__).parent / "fixtures"
        plugin.collect(fixture_dir, file=plugin.default_file)

        assert len(plugin.dependencies) == 3
        parsed = {(dep.name, dep.version, dep.tool_name) for dep in plugin.dependencies}
        assert parsed == {
            ("accepts", "1.3.8", "npm"),
            ("express", "4.21.2", "npm"),
            ("typescript", "5.9.2", "npm"),
        }


class TestExport:
    """Verify export() writes a valid CSV."""

    def test_export_csv(self, tmp_path: Path):
        plugin = NpmPlugin()
        fixture_dir = Path(__file__).parent / "fixtures"
        plugin.collect(fixture_dir, file=plugin.default_file)
        csv_path = plugin.export("/some/project", tmp_path)
        assert csv_path.exists()

        assert csv_path.name == "npm_project.csv"

        with csv_path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))

        assert len(rows) == 3
        assert {row["name"] for row in rows} == {"accepts", "express", "typescript"}
