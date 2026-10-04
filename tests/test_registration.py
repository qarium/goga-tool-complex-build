"""Tests for goga_tool_complex_build.registration."""

import inspect
import re
from collections.abc import Callable

import pytest
from goga.config.hooks.events import (
    ConfigHooks,
    ToolAmendment,
    build_hook_arguments,
    merge_config_amendments,
    wrap_context,
)
from goga.config.project import AdditionalReviewConfig, BuildConfig, ProjectConfig, ReviewConfig
from goga.hooks.registry import state as registry_state
from goga.hooks.tools.packages import enumerate_tool_packages
from goga.hooks.tools.registration import HookRegistrar
from goga_tool_complex_build import registration

PRESET_SET_CALLS = [
    ("build.review.strategy", "full"),
    ("build.review.max_iterations", 5),
    ("build.review.additional.patience", 2),
    ("build.review.additional.max_iterations", 3),
]

PRESET_BUFFERED_AMENDMENTS = [
    ("build.review.strategy", "set", "full"),
    ("build.review.max_iterations", "set", 5),
    ("build.review.additional.patience", "set", 2),
    ("build.review.additional.max_iterations", "set", 3),
]

STRATEGY_CONFLICT_MESSAGE = (
    "authored value at build.review.strategy conflicts with the tool's purpose; "
    "remove the authored strategy or uninstall the tool"
)


class _FakeRegistrar:
    """Registration double recording subscribe envelopes."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, Callable[..., object]]] = []

    def subscribe(self, domain: str, action: str, name: str, hook: Callable[..., object]) -> None:
        """Records the subscription envelope.

        Args:
            domain: Subscription domain.
            action: Subscription action inside the domain.
            name: Hook name under the address.
            hook: Subscribed hook routine.
        """
        self.calls.append((domain, action, name, hook))


class TestContract:
    def test_contract_routines_expose_declared_signatures(self) -> None:
        register_parameters = inspect.signature(registration.register_hooks).parameters
        review_parameters = inspect.signature(registration.review_presets).parameters

        assert list(register_parameters) == ["hooks"]
        assert list(review_parameters) == ["context"]

        for parameter in (*register_parameters.values(), *review_parameters.values()):
            assert parameter.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)


class TestRegisterHooks:
    def test_register_hooks_subscribes_single_hook_to_config_amend_config(self) -> None:
        fake = _FakeRegistrar()

        registration.register_hooks(fake)

        assert len(fake.calls) == 1
        assert fake.calls[0][:3] == ("config", "amend_config", "review_presets")
        assert fake.calls[0][3] is registration.review_presets

    def test_register_hooks_envelope_accepted_by_real_registrar(self) -> None:
        registrar = HookRegistrar(tool="complex-build")

        registration.register_hooks(registrar)

        assert len(registrar.subscriptions) == 1
        assert [(s.domain, s.action, s.name) for s in registrar.subscriptions] == [
            ("config", "amend_config", "review_presets")
        ]
        assert registrar.rejections == []


class TestReviewPresets:
    def test_review_presets_buffers_four_presets_on_silent_config(self, project_config, recording_view) -> None:
        view = recording_view(project_config(build=None))

        registration.review_presets(view)

        assert view.set_calls == PRESET_SET_CALLS
        assert view.force_calls == []

    def test_review_presets_with_authored_full_strategy_buffers_unconditionally(
        self, project_config, recording_view
    ) -> None:
        view = recording_view(project_config(build=BuildConfig(review=ReviewConfig(strategy="full"))))

        registration.review_presets(view)

        assert view.set_calls == PRESET_SET_CALLS

    def test_review_presets_raises_value_error_on_conflicting_strategy_before_any_set(
        self, project_config, recording_view
    ) -> None:
        view = recording_view(project_config(build=BuildConfig(review=ReviewConfig(strategy="short"))))

        with pytest.raises(ValueError, match=re.escape(STRATEGY_CONFLICT_MESSAGE)) as excinfo:
            registration.review_presets(view)

        assert str(excinfo.value) == STRATEGY_CONFLICT_MESSAGE
        assert "build.review.strategy" in str(excinfo.value)
        assert view.set_calls == []
        assert view.force_calls == []

    def test_review_presets_error_message_never_contains_authored_value(self, project_config, recording_view) -> None:
        view = recording_view(project_config(build=BuildConfig(review=ReviewConfig(strategy="s3cr3t-strategy-value"))))

        with pytest.raises(ValueError, match=re.escape(STRATEGY_CONFLICT_MESSAGE)) as excinfo:
            registration.review_presets(view)

        assert "s3cr3t-strategy-value" not in str(excinfo.value)
        assert "build.review.strategy" in str(excinfo.value)
        assert view.set_calls == []

    def test_review_presets_authored_empty_string_strategy_raises(self, project_config, recording_view) -> None:
        view = recording_view(project_config(build=BuildConfig(review=ReviewConfig(strategy=""))))

        with pytest.raises(ValueError, match=re.escape(STRATEGY_CONFLICT_MESSAGE)) as excinfo:
            registration.review_presets(view)

        assert str(excinfo.value) == STRATEGY_CONFLICT_MESSAGE
        assert view.set_calls == []

    @pytest.mark.parametrize("strategy", [5, True, 1.5])
    def test_review_presets_non_string_authored_strategy_raises(self, project_config, recording_view, strategy) -> None:
        view = recording_view(project_config(build=BuildConfig(review=ReviewConfig(strategy=strategy))))

        with pytest.raises(ValueError, match=re.escape(STRATEGY_CONFLICT_MESSAGE)) as excinfo:
            registration.review_presets(view)

        assert str(excinfo.value) == STRATEGY_CONFLICT_MESSAGE
        assert view.set_calls == []

    def test_review_presets_absent_review_branch_with_present_build_section(
        self, project_config, recording_view
    ) -> None:
        view = recording_view(project_config(build=BuildConfig(agent="claude")))

        registration.review_presets(view)

        assert view.set_calls == PRESET_SET_CALLS

    def test_review_presets_reads_strategy_chain_only(self, recording_view, trap) -> None:
        config = ProjectConfig(
            language="python",
            image=trap,
            dockerfile=trap,
            build=BuildConfig(
                agent=trap,
                env=trap,
                max_iterations=trap,
                session_timeout=trap,
                idle_timeout=trap,
                wait=trap,
                prompts_dir=trap,
                agents_dir=trap,
                proxy=trap,
                hosts=trap,
                review=ReviewConfig(
                    skip=trap,
                    agent=trap,
                    env=trap,
                    roles=trap,
                    base_ref=trap,
                    strategy=None,
                    finalize=trap,
                    additional=None,
                    session_timeout=trap,
                    idle_timeout=trap,
                    wait=trap,
                    max_iterations=trap,
                ),
            ),
            pipeline=trap,
            commands=trap,
            codemanifest=trap,
            tools=trap,
            usages=trap,
            lint=trap,
            topics=trap,
        )
        view = recording_view(config)

        registration.review_presets(view)

        assert view.set_calls == PRESET_SET_CALLS


class TestDelivery:
    def test_review_presets_through_real_delivery_projection(self, project_config, recording_view) -> None:
        view = recording_view(project_config(build=None))

        proxy = wrap_context(view)
        args = build_hook_arguments(registration.review_presets, proxy, object())
        registration.review_presets(**args)

        assert sorted(args) == ["context"]
        assert view.set_calls == PRESET_SET_CALLS
        assert [(a.path, a.intent, a.value) for a in view._amendments.values()] == PRESET_BUFFERED_AMENDMENTS

    def test_presets_merge_into_effective_review_config(self, project_config, recording_view) -> None:
        base = project_config(build=None)
        view = recording_view(base)

        registration.review_presets(view)
        contribution = ToolAmendment(tool="complex-build", amendments=list(view._amendments.values()))
        overlay = merge_config_amendments(base, [contribution])

        review = overlay.config.build.review
        assert review.strategy == "full"
        assert review.max_iterations == 5
        assert review.additional.patience == 2
        assert review.additional.max_iterations == 3

        assert len(overlay.applied) == 4
        assert all(record.tool == "complex-build" and record.intent == "set" for record in overlay.applied)
        assert overlay.summary_lines == [
            "config amendments: 4 applied",
            "- complex-build set build.review.strategy",
            "- complex-build set build.review.max_iterations",
            "- complex-build set build.review.additional.patience",
            "- complex-build set build.review.additional.max_iterations",
        ]
        assert base.build is None

    def test_presets_merge_honors_authored_wins_on_authored_leaves(self, project_config, recording_view) -> None:
        base = project_config(
            build=BuildConfig(
                review=ReviewConfig(strategy=None, additional=AdditionalReviewConfig(patience=4, max_iterations=0))
            )
        )
        view = recording_view(base)

        registration.review_presets(view)
        contribution = ToolAmendment(tool="complex-build", amendments=list(view._amendments.values()))
        overlay = merge_config_amendments(base, [contribution])

        review = overlay.config.build.review
        assert review.strategy == "full"
        assert review.max_iterations == 5
        assert review.additional.patience == 4
        assert review.additional.max_iterations == 0
        assert [record.path for record in overlay.applied] == [
            "build.review.strategy",
            "build.review.max_iterations",
        ]


class TestCheckpointIntegration:
    def test_tool_amends_through_real_checkpoint(self, project_config, monkeypatch) -> None:
        # The shared dev venv carries foreign goga_tool_* packages whose sets contest the same
        # preset paths (later-tool-wins); the environment seam is pinned to the package under
        # test so the checkpoint's design-verified literals hold. Everything downstream —
        # facade import, registration, delivery, merge — stays the real platform code.
        packages = [
            package for package in enumerate_tool_packages() if package.module_name == "goga_tool_complex_build"
        ]
        assert packages

        monkeypatch.setattr(registry_state, "enumerate_tool_packages", lambda: packages)
        config = project_config(build=None)
        overlay = ConfigHooks().amend_config(config=config)

        review = overlay.config.build.review
        assert review.strategy == "full"
        assert review.max_iterations == 5
        assert review.additional.patience == 2
        assert review.additional.max_iterations == 3

        complex_build_records = [record for record in overlay.applied if record.tool == "complex-build"]
        assert [(record.path, record.intent) for record in complex_build_records] == [
            ("build.review.strategy", "set"),
            ("build.review.max_iterations", "set"),
            ("build.review.additional.patience", "set"),
            ("build.review.additional.max_iterations", "set"),
        ]
        assert "- complex-build set build.review.strategy" in overlay.summary_lines
        assert config.build is None
