"""Tests for the goga_tool_complex_build package facade."""

import goga_tool_complex_build as facade
from goga_tool_complex_build import registration


class TestInit:
    def test_facade_reexports_contract_api_by_identity(self) -> None:
        assert facade.__all__ == ["register_hooks", "review_presets"]
        assert facade.register_hooks is registration.register_hooks
        assert facade.review_presets is registration.review_presets
