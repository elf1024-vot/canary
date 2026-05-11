"""
Router-side validator for the Grammar and Spelling subagent.

Spec: `_standards.md` v1.25, "Subagent Architectural Rule: Subagents
Report, the Router Validates", Validator Config for "Grammar and
Spelling".

Contract:

    result = validate(subagent_json, stripped_file_path)

    result.passed                -> bool
    result.failures              -> list[str], one line per failure
    result.corrective_instruction -> str or None; non-None iff not passed

The router:

1. On `result.passed is True`, accepts the subagent JSON and proceeds.
2. On `result.passed is False` and this is the first attempt, re-dispatches
   the subagent with `result.corrective_instruction` appended to the prompt.
3. On second failure, hard-stops Mode 1 and reports to the author.

Per the architectural rule: this validator NEVER asks the subagent to
re-check itself. All checks are deterministic Python operating on the
returned JSON plus the stripped file on disk.

Scope (v1.25): the subagent reports only confirmed misspellings and
misuses (step 6 of the Recognition Order). Steps 1 through 5 are silent
internal exclusions and are not part of the output schema. This module
validates what the subagent DID claim, not what it should have claimed
alongside: schema shape, stripped_file_read match, score math, issue-list
caps, substring checks (every cited excerpt / context / word must appear
verbatim in the stripped file), guaranteed-hallucination-marker filter
(strip-removed tokens cannot appear in any citation), paragraph range.

Router version: v0.2
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._path_compare import paths_equivalent as _paths_equivalent

# Sanity cap on issue lists per the subagent prompt.
ISSUE_CAP = 50

# Score math tolerance (subagent rounds to 2 decimals).
SCORE_ROUNDING_TOLERANCE = 0.011


@dataclass
class ValidationResult:
    """Outcome of a single validation pass."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    corrective_instruction: str | None = None

    # Diagnostic fields the router can log / surface in reports.
    paragraph_count: int | None = None
    total_words_reported: int | None = None
    grammar_issues_count: int | None = None
    spelling_issues_count: int | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_paragraphs(text: str) -> int:
    """Paragraphs are blank-line-separated blocks of non-whitespace text."""
    blocks = re.split(r"\n\s*\n", text)
    return sum(1 for b in blocks if b.strip())


def _is_float_in_range(value: Any, lo: float, hi: float) -> bool:
    if not isinstance(value, (int, float)):
        return False
    v = float(value)
    return lo <= v <= hi


def _expected_score(issues_found: int, total: int) -> float:
    if total <= 0:
        return 100.0
    raw = 100.0 * (1.0 - (issues_found / total))
    if raw < 0.0:
        raw = 0.0
    if raw > 100.0:
        raw = 100.0
    return round(raw, 2)


def _score_matches(reported: Any, expected: float) -> bool:
    if not isinstance(reported, (int, float)):
        return False
    return abs(float(reported) - expected) <= SCORE_ROUNDING_TOLERANCE


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def validate(
    subagent_json: dict,
    stripped_file_path: str,
    active_config: dict | None = None,
) -> ValidationResult:
    """
    Validate a Grammar and Spelling subagent JSON payload.

    Parameters
    ----------
    subagent_json
        Parsed JSON as returned by the subagent. MUST follow the schema
        in `subagents/grammar_spelling.md` v1.2.
    stripped_file_path
        The exact path the router dispatched the subagent with. The
        subagent's `stripped_file_read` must match this.
    active_config
        The parsed pwa_config.json for this run. Used to derive the
        hallucination-marker set (paired_delimiters openers and
        line_starts_with / exact_line header rule values). Pass None
        to skip hallucination-marker checks.

    Returns
    -------
    ValidationResult
    """
    failures: list[str] = []
    corrective_lines: list[str] = []
    diagnostics: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 1. Schema presence / shape
    # ------------------------------------------------------------------
    for field_name in ("subagent_version", "stripped_file_read", "grammar", "spelling"):
        if field_name not in subagent_json:
            failures.append(f"missing top-level field: {field_name}")

    if "stripped_file_read" in subagent_json and not _paths_equivalent(
        stripped_file_path, subagent_json["stripped_file_read"]
    ):
        failures.append(
            "stripped_file_read does not match dispatched path "
            f"(expected {stripped_file_path!r}, got {subagent_json['stripped_file_read']!r})"
        )
        corrective_lines.append(
            "You reported reading a different file than the one you were dispatched to. "
            f"Re-read EXACTLY this file and no other: {stripped_file_path}"
        )

    grammar = subagent_json.get("grammar") or {}
    spelling = subagent_json.get("spelling") or {}

    for k in ("total_sentences", "issues_found", "score_pct", "issues"):
        if k not in grammar:
            failures.append(f"grammar.{k} missing")
    for k in ("total_words", "issues_found", "score_pct", "issues"):
        if k not in spelling:
            failures.append(f"spelling.{k} missing")

    # If the shape is broken, skip further checks that assume the shape.
    if failures:
        return _finalize(failures, corrective_lines, diagnostics)

    # ------------------------------------------------------------------
    # 2. Stripped file readable
    # ------------------------------------------------------------------
    try:
        stripped_text = Path(stripped_file_path).read_text(encoding="utf-8")
    except Exception as exc:
        failures.append(f"stripped file not readable by router: {exc}")
        return _finalize(failures, corrective_lines, diagnostics)

    paragraph_count = _count_paragraphs(stripped_text)
    diagnostics["paragraph_count"] = paragraph_count

    # ------------------------------------------------------------------
    # 3. Score ranges + score math
    # ------------------------------------------------------------------
    if not _is_float_in_range(grammar["score_pct"], 0, 100):
        failures.append(f"grammar.score_pct out of range: {grammar['score_pct']!r}")
    if not _is_float_in_range(spelling["score_pct"], 0, 100):
        failures.append(f"spelling.score_pct out of range: {spelling['score_pct']!r}")

    g_total = grammar.get("total_sentences", 0)
    g_issues = grammar.get("issues_found", 0)
    s_total = spelling.get("total_words", 0)
    s_issues = spelling.get("issues_found", 0)

    if isinstance(g_total, int) and isinstance(g_issues, int):
        expected_g = _expected_score(g_issues, g_total)
        if not _score_matches(grammar["score_pct"], expected_g):
            failures.append(
                f"grammar.score_pct math mismatch: reported {grammar['score_pct']}, "
                f"expected {expected_g} from {g_issues}/{g_total}"
            )

    if isinstance(s_total, int) and isinstance(s_issues, int):
        expected_s = _expected_score(s_issues, s_total)
        if not _score_matches(spelling["score_pct"], expected_s):
            failures.append(
                f"spelling.score_pct math mismatch: reported {spelling['score_pct']}, "
                f"expected {expected_s} from {s_issues}/{s_total}"
            )

    diagnostics["total_words_reported"] = s_total if isinstance(s_total, int) else None
    diagnostics["grammar_issues_count"] = len(grammar.get("issues", []))
    diagnostics["spelling_issues_count"] = len(spelling.get("issues", []))

    # ------------------------------------------------------------------
    # 4. Issue-list caps + forbidden-field check
    #
    # v1.25 schema forbids unknown_words_for_review and any calibration
    # block. A subagent emitting those is running an outdated prompt.
    # ------------------------------------------------------------------
    if len(grammar.get("issues", [])) > ISSUE_CAP:
        failures.append(
            f"grammar.issues exceeds cap of {ISSUE_CAP} ({len(grammar['issues'])} entries)"
        )
    if len(spelling.get("issues", [])) > ISSUE_CAP:
        failures.append(
            f"spelling.issues exceeds cap of {ISSUE_CAP} ({len(spelling['issues'])} entries)"
        )

    for forbidden in ("unknown_words_for_review", "calibration", "passes_calibration"):
        if forbidden in spelling or forbidden in subagent_json:
            failures.append(
                f"forbidden field present in output: {forbidden!r} "
                "(v1.25 schema removed the Recognition Order walk log; "
                "subagent appears to be running an outdated prompt)"
            )
            corrective_lines.append(
                f"Remove `{forbidden}` from your output. The v1.2 grammar_spelling prompt "
                "does not emit any field describing the Recognition Order walk — only step-6 "
                "hits go into spelling.issues."
            )
            break

    # ------------------------------------------------------------------
    # 5. Substring checks against stripped file
    #
    # Every `excerpt`, `context`, and `word` must appear verbatim in the
    # stripped file. Build the hallucination marker set from the active
    # config: paired_delimiters openers (all modes are stripped from the
    # scored file) and line_starts_with / exact_line header rule values.
    # ------------------------------------------------------------------
    _markers: list[str] = []
    if active_config:
        for pd in active_config.get("paired_delimiters", []):
            opener = pd.get("opener")
            if opener and isinstance(opener, str):
                _markers.append(opener)
        for rule in active_config.get("header_strip_patterns", []):
            val = rule.get("value")
            if val and isinstance(val, str) and rule.get("type") in (
                "line_starts_with", "exact_line"
            ):
                _markers.append(val)
    hallucination_markers: tuple[str, ...] = tuple(_markers)

    def _substring_check(label: str, item: dict, key: str) -> None:
        val = item.get(key)
        if val is None:
            return
        if not isinstance(val, str):
            failures.append(f"{label}.{key} is not a string: {val!r}")
            return
        if not val.strip():
            return  # empty string not substantive
        for marker in hallucination_markers:
            if marker in val:
                failures.append(
                    f"{label}.{key} cites a stripped-out marker ({marker!r}); "
                    f"subagent read the wrong file or hallucinated"
                )
                corrective_lines.append(
                    f"You cited the marker `{marker}` in {label}.{key}. The strip engine "
                    "removed that marker before you received the file, so it cannot appear "
                    "in any legitimate citation. Re-read the stripped file and cite only "
                    "text that exists there verbatim."
                )
                return
        if val not in stripped_text:
            failures.append(
                f"{label}.{key} not found verbatim in stripped file: {val!r}"
            )
            corrective_lines.append(
                f"You cited `{val!r}` in {label}.{key}, but that string does not appear in "
                f"the stripped file. Re-read the file and cite only verbatim text."
            )

    for i, issue in enumerate(grammar.get("issues", [])):
        label = f"grammar.issues[{i}]"
        _substring_check(label, issue, "excerpt")
        _substring_check(label, issue, "context")

    for i, issue in enumerate(spelling.get("issues", [])):
        label = f"spelling.issues[{i}]"
        _substring_check(label, issue, "word")
        _substring_check(label, issue, "context")

    # ------------------------------------------------------------------
    # 6. Paragraph range check
    # ------------------------------------------------------------------
    def _paragraph_check(label: str, item: dict) -> None:
        p = item.get("paragraph")
        if p is None:
            return
        if not isinstance(p, int):
            failures.append(f"{label}.paragraph not an int: {p!r}")
            return
        if p < 1 or p > paragraph_count:
            failures.append(
                f"{label}.paragraph {p} outside file range [1, {paragraph_count}]"
            )

    for i, issue in enumerate(grammar.get("issues", [])):
        _paragraph_check(f"grammar.issues[{i}]", issue)
    for i, issue in enumerate(spelling.get("issues", [])):
        _paragraph_check(f"spelling.issues[{i}]", issue)

    return _finalize(failures, corrective_lines, diagnostics)


def _finalize(
    failures: list[str],
    corrective_lines: list[str],
    diagnostics: dict[str, Any],
) -> ValidationResult:
    passed = not failures
    instruction: str | None = None
    if not passed:
        if not corrective_lines:
            corrective_lines = [
                "Your JSON output failed router validation. Specific failures:",
                *(f"- {f}" for f in failures),
                "Re-read the stripped file and return corrected JSON.",
            ]
        instruction = "\n".join(corrective_lines)

    return ValidationResult(
        passed=passed,
        failures=failures,
        corrective_instruction=instruction,
        paragraph_count=diagnostics.get("paragraph_count"),
        total_words_reported=diagnostics.get("total_words_reported"),
        grammar_issues_count=diagnostics.get("grammar_issues_count"),
        spelling_issues_count=diagnostics.get("spelling_issues_count"),
    )


# ---------------------------------------------------------------------------
# CLI for ad-hoc testing against real canary outputs.
#
#     python -m router.validators.grammar_spelling \
#         --subagent-json path/to/grammar-spelling.json \
#         --stripped-file "path/to/stripped.txt"
#
# Exit code 0 on PASS, 1 on FAIL.
# ---------------------------------------------------------------------------

def _cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Router-side validator for Grammar and Spelling subagent output."
    )
    parser.add_argument("--subagent-json", required=True)
    parser.add_argument("--stripped-file", required=True)
    parser.add_argument("--config", default=None, help="Path to pwa_config.json (optional; enables hallucination-marker checks)")
    args = parser.parse_args()

    with open(args.subagent_json, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    active_config: dict | None = None
    if args.config:
        with open(args.config, "r", encoding="utf-8") as fh:
            active_config = json.load(fh)

    result = validate(payload, stripped_file_path=args.stripped_file, active_config=active_config)

    print(json.dumps(
        {
            "passed": result.passed,
            "failures": result.failures,
            "corrective_instruction": result.corrective_instruction,
            "paragraph_count": result.paragraph_count,
            "total_words_reported": result.total_words_reported,
            "grammar_issues_count": result.grammar_issues_count,
            "spelling_issues_count": result.spelling_issues_count,
        },
        indent=2,
    ))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(_cli())

# end of file
# mount sync trigger v3 - 2026-04-22T18:00 - force bash mount to refresh after Edit-tool path-compare integration
