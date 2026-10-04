"""Tests for the goga_tool_complex_build package facade."""

import subprocess
import sys
from pathlib import Path

import goga_tool_complex_build as facade
from goga_tool_complex_build import registration

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

# A None entry for every known goga module key makes each `import goga...` raise
# ImportError — proving the facade needs no goga at runtime.
GOGA_BLOCKED_IMPORT = (
    "import sys\n"
    "sys.modules['goga'] = None\n"
    "sys.modules['goga.config'] = None\n"
    "sys.modules['goga.hooks'] = None\n"
    "import goga_tool_complex_build\n"
    "print(goga_tool_complex_build.__all__)\n"
    "print(goga_tool_complex_build.register_hooks, goga_tool_complex_build.review_presets)\n"
)


class TestInit:
    def test_facade_reexports_contract_api_by_identity(self) -> None:
        assert facade.__all__ == ["register_hooks", "review_presets"]
        assert facade.register_hooks is registration.register_hooks
        assert facade.review_presets is registration.review_presets

    def test_facade_imports_without_goga_installed(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", GOGA_BLOCKED_IMPORT],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "register_hooks" in result.stdout
        assert "review_presets" in result.stdout
