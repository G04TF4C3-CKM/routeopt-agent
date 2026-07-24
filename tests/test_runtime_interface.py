"""Red Team regressions for workflow runtime display and view navigation."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import math
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP_PATH = REPOSITORY_ROOT / "streamlit_app.py"
UI_UTILS_PATH = REPOSITORY_ROOT / "src" / "ui_utils.py"

UI_UTILS_SPEC = importlib.util.find_spec("src.ui_utils")
UI_UTILS: ModuleType | None = (
    importlib.import_module("src.ui_utils") if UI_UTILS_SPEC is not None else None
)
FORMAT_RUNTIME_SECONDS = (
    getattr(UI_UTILS, "format_runtime_seconds", None)
    if UI_UTILS is not None
    else None
)
requires_runtime_formatter = pytest.mark.skipif(
    not callable(FORMAT_RUNTIME_SECONDS),
    reason="src.ui_utils.format_runtime_seconds has not been implemented yet",
)

STREAMLIT_APP_TREE = ast.parse(
    STREAMLIT_APP_PATH.read_text(encoding="utf-8"),
    filename=str(STREAMLIT_APP_PATH),
)
UI_UTILS_TREE = ast.parse(
    UI_UTILS_PATH.read_text(encoding="utf-8"),
    filename=str(UI_UTILS_PATH),
)
APP_FUNCTIONS = {
    node.name: node
    for node in STREAMLIT_APP_TREE.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
DETAIL_TIMING_LABELS = (
    "Routing-engine runtime",
    "Problem setup runtime",
    "Solver runtime",
    "Progress callback runtime",
    "Solver logic runtime",
    "Termination tail runtime",
    "Result finalization runtime",
    "Workflow outside routing engine",
    "Solver bookkeeping remainder",
)
AUGMENTATION_TIMING_LABELS = (
    "Solver phase",
    "Augmentation runtime",
    "Cumulative solver runtime",
)


def _call_name(call: ast.Call) -> str | None:
    """Return the terminal name of a direct or attribute call."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _contains_exact_string(node: ast.AST, expected: str) -> bool:
    return any(
        isinstance(child, ast.Constant)
        and isinstance(child.value, str)
        and child.value == expected
        for child in ast.walk(node)
    )


def _contains_call_named(node: ast.AST, expected: str) -> bool:
    return any(
        isinstance(child, ast.Call) and _call_name(child) == expected
        for child in ast.walk(node)
    )


def _function(name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    function = APP_FUNCTIONS.get(name)
    assert function is not None, f"streamlit_app.py is missing {name}."
    return function


def _visible_runtime_calls(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.Call]:
    """Find non-JSON presentation calls containing the label and formatted value."""
    calls: list[ast.Call] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node) in {"json", "format_runtime_seconds"}:
            continue
        if not _contains_exact_string(node, "Workflow runtime"):
            continue
        if not _contains_call_named(node, "format_runtime_seconds"):
            continue
        calls.append(node)
    return calls


def _visible_calls_with_label(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    label: str,
) -> list[ast.Call]:
    """Find non-JSON presentation calls containing one exact visible label."""
    return [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and _call_name(node) != "json"
        and _contains_exact_string(node, label)
    ]


def _find_button_call(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    label: str,
) -> ast.Call:
    matches = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and _call_name(node) == "button"
        and _contains_exact_string(node, label)
    ]
    assert len(matches) == 1, (
        f"Expected exactly one {label!r} button in {function.name}; "
        f"found {len(matches)}."
    )
    return matches[0]


def _keyword(call: ast.Call, name: str) -> ast.keyword | None:
    return next((item for item in call.keywords if item.arg == name), None)


def _button_is_if_test(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    button: ast.Call,
) -> bool:
    return any(
        isinstance(node, ast.If)
        and any(candidate is button for candidate in ast.walk(node.test))
        for node in ast.walk(function)
    )


def _reachable_callback_functions(callback: ast.AST) -> list[ast.AST]:
    """Resolve module-local helpers reachable from a callback expression."""
    pending = [
        node.id
        for node in ast.walk(callback)
        if isinstance(node, ast.Name) and node.id in APP_FUNCTIONS
    ]
    visited: set[str] = set()
    functions: list[ast.AST] = []

    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        function = APP_FUNCTIONS[name]
        functions.append(function)
        pending.extend(
            node.id
            for node in ast.walk(function)
            if isinstance(node, ast.Name)
            and node.id in APP_FUNCTIONS
            and node.id not in visited
        )

    return functions


def _referenced_names(nodes: list[ast.AST]) -> set[str]:
    names: set[str] = set()
    for node in nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.add(child.id)
            elif isinstance(child, ast.Attribute):
                names.add(child.attr)
    return names


def _function_and_reachable_helpers(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.AST]:
    return [function, *_reachable_callback_functions(function)]


def _assigned_value(nodes: list[ast.AST], target_name: str) -> ast.AST | None:
    for root in nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == target_name
                for target in node.targets
            ):
                return node.value
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == target_name
            ):
                return node.value
    return None


def _references_metric(node: ast.AST, metric_name: str) -> bool:
    accepted_names = {
        metric_name,
        f"{metric_name}_seconds",
        f"total_{metric_name}",
        f"total_{metric_name}_seconds",
    }
    accepted_keys = {
        metric_name,
        f"{metric_name}_seconds",
    }
    if metric_name == "workflow_runtime":
        accepted_keys.add("runtime_seconds")
    return any(
        (
            isinstance(child, ast.Name)
            and child.id in accepted_names
        )
        or (
            isinstance(child, ast.Constant)
            and isinstance(child.value, str)
            and child.value in accepted_keys
        )
        for child in ast.walk(node)
    )


def test_ui_utils_exposes_format_runtime_seconds() -> None:
    assert callable(FORMAT_RUNTIME_SECONDS), (
        "src.ui_utils must expose format_runtime_seconds(runtime_seconds: float) "
        "for workflow-runtime presentation."
    )


@requires_runtime_formatter
@pytest.mark.parametrize(
    ("runtime_seconds", "expected"),
    (
        (0.0, "0 ms"),
        (0.125, "125 ms"),
        (0.999, "999 ms"),
        (1.0, "1.00 s"),
        (1.25, "1.25 s"),
        (12.5, "12.50 s"),
        (65.25, "1m 5.25s"),
        (125.0, "2m 5.00s"),
    ),
)
def test_format_runtime_seconds_contract(
    runtime_seconds: float,
    expected: str,
) -> None:
    assert FORMAT_RUNTIME_SECONDS(runtime_seconds) == expected


@requires_runtime_formatter
@pytest.mark.parametrize(
    "runtime_seconds",
    (-0.001, math.inf, -math.inf, math.nan),
)
def test_format_runtime_seconds_rejects_invalid_values(
    runtime_seconds: float,
) -> None:
    with pytest.raises(ValueError):
        FORMAT_RUNTIME_SECONDS(runtime_seconds)


@requires_runtime_formatter
def test_runtime_formatter_does_not_import_streamlit() -> None:
    streamlit_imports = [
        node
        for node in ast.walk(UI_UTILS_TREE)
        if (
            isinstance(node, ast.Import)
            and any(alias.name.split(".", 1)[0] == "streamlit" for alias in node.names)
        )
        or (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.split(".", 1)[0] == "streamlit"
        )
    ]
    assert not streamlit_imports, (
        "format_runtime_seconds must remain available without a Streamlit dependency."
    )


@pytest.mark.parametrize(
    "function_name",
    ("_render_manager_summary", "_render_run_details"),
)
def test_render_path_visibly_presents_workflow_runtime(
    function_name: str,
) -> None:
    function = _function(function_name)
    assert _visible_runtime_calls(function), (
        f"{function_name} must visibly present record runtime with the exact label "
        "'Workflow runtime' and format_runtime_seconds; an st.json field alone "
        "does not satisfy the presentation contract."
    )


@pytest.mark.parametrize("label", DETAIL_TIMING_LABELS)
def test_run_details_visibly_presents_backend_timing_label(label: str) -> None:
    function = _function("_render_run_details")
    assert _visible_calls_with_label(function, label), (
        "_render_run_details must visibly present the exact backend timing "
        f"label {label!r}; a raw st.json field alone is insufficient."
    )


@pytest.mark.parametrize("label", AUGMENTATION_TIMING_LABELS)
def test_run_details_augmentation_display_includes_timing_label(
    label: str,
) -> None:
    function = _function("_render_run_details")
    assert _visible_calls_with_label(function, label), (
        "The ordered augmentation display must visibly include the exact "
        f"column label {label!r}."
    )


def test_run_details_has_explicit_older_timing_fallback() -> None:
    function = _function("_render_run_details")
    fallback = "Detailed solver timing was not captured for this run."
    assert _visible_calls_with_label(function, fallback), (
        "_render_run_details must explicitly explain missing detailed timing "
        "for older run-history records."
    )


@pytest.mark.parametrize(
    ("target_name", "metric_names", "minimum_subtractions"),
    (
        (
            "solver_logic_runtime",
            ("solver_runtime", "progress_callback_runtime"),
            1,
        ),
        (
            "workflow_outside_routing_engine",
            ("workflow_runtime", "routing_engine_runtime"),
            1,
        ),
        (
            "solver_bookkeeping_remainder",
            (
                "solver_runtime",
                "augmentation_runtime",
                "progress_callback_runtime",
                "termination_tail_runtime",
            ),
            3,
        ),
    ),
)
def test_run_details_uses_required_derived_timing_formula(
    target_name: str,
    metric_names: tuple[str, ...],
    minimum_subtractions: int,
) -> None:
    function = _function("_render_run_details")
    nodes = _function_and_reachable_helpers(function)
    expression = _assigned_value(nodes, target_name)

    assert expression is not None, (
        f"_render_run_details must calculate {target_name} from captured timing "
        "fields rather than relabeling another duration."
    )
    subtraction_count = sum(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)
        for node in ast.walk(expression)
    )
    assert subtraction_count >= minimum_subtractions
    for metric_name in metric_names:
        assert _references_metric(expression, metric_name), (
            f"{target_name} must reference {metric_name}."
        )


def test_run_details_does_not_silently_clamp_negative_solver_remainder() -> None:
    function = _function("_render_run_details")
    nodes = _function_and_reachable_helpers(function)
    expression = _assigned_value(nodes, "solver_bookkeeping_remainder")

    assert expression is not None
    assert not any(
        isinstance(node, ast.Call) and _call_name(node) == "max"
        for node in ast.walk(expression)
    ), (
        "A materially negative solver bookkeeping remainder must not be hidden "
        "with max(0, remainder)."
    )

    diagnostic_warnings = [
        node
        for root in nodes
        for node in ast.walk(root)
        if isinstance(node, ast.Call)
        and _call_name(node) == "warning"
        and any(
            isinstance(child, ast.Constant)
            and isinstance(child.value, str)
            and (
                "inconsistent" in child.value.casefold()
                or "negative" in child.value.casefold()
            )
            for child in ast.walk(node)
        )
    ]
    assert diagnostic_warnings, (
        "_render_run_details must issue a diagnostic warning for materially "
        "negative or inconsistent timing remainders."
    )


@pytest.mark.parametrize(
    "function_name",
    ("_render_manager_summary", "_render_run_details"),
)
def test_navigation_renderer_does_not_call_st_rerun(
    function_name: str,
) -> None:
    function = _function(function_name)
    rerun_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "st"
        and node.func.attr == "rerun"
    ]
    assert not rerun_calls, (
        f"{function_name} must rely on the button's normal rerun and must not "
        "call st.rerun()."
    )


@pytest.mark.parametrize(
    ("function_name", "button_label", "target_view"),
    (
        ("_render_manager_summary", "View Run Details", "details"),
        ("_render_run_details", "Back to Summary", "summary"),
    ),
)
def test_navigation_button_uses_session_view_callback(
    function_name: str,
    button_label: str,
    target_view: str,
) -> None:
    function = _function(function_name)
    button = _find_button_call(function, button_label)
    callback_keyword = _keyword(button, "on_click")

    assert callback_keyword is not None and not (
        isinstance(callback_keyword.value, ast.Constant)
        and callback_keyword.value.value is None
    ), f"{button_label!r} must define an on_click callback."
    assert not _button_is_if_test(function, button), (
        f"{button_label!r} must not mutate navigation state through the "
        "button's transient return value; its callback must perform the transition."
    )

    callback_configuration = [callback_keyword.value]
    callback_configuration.extend(
        keyword.value
        for keyword in button.keywords
        if keyword.arg in {"args", "kwargs"}
    )
    callback_functions = _reachable_callback_functions(callback_keyword.value)
    callback_nodes = callback_configuration + callback_functions
    referenced_names = _referenced_names(callback_nodes)

    uses_session_transition = (
        "_switch_session_view" in referenced_names
        or {"set_active_view", "_write_session_history"} <= referenced_names
    )
    assert uses_session_transition, (
        f"{button_label!r} callback must use the existing canonical session-view "
        "transition behavior."
    )
    assert any(
        _contains_exact_string(node, target_view) for node in callback_nodes
    ), (
        f"{button_label!r} callback must transition to the {target_view!r} view "
        "through its helper or callback arguments."
    )
    assert "run_routing_workflow" not in referenced_names, (
        f"{button_label!r} callback must only navigate existing run history; "
        "it must not invoke the routing workflow."
    )
