"""
Router-side validator for the Strip Verification subagent.

Spec: `_standards.md` v1.25, "Subagent Architectural Rule: Subagents
Report, the Router Validates", Validator Config for "Strip Verification".

Contract:

    result = validate(
        subagent_json,
        original_chapter_path,
        stripped_file_path,
        strip_log_path,
        marker_map_path,         # may be None
        pwa_config_path,
    )

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
returned JSON plus the strip log + marker map + chapter files on disk.

What this validator confirms (independent of the subagent's claims):

- Schema shape (subagent_version + path-echo fields + verdict + arrays).
- Every category_checks[].label corresponds to a real label in the strip
  log's `rules_applied` array OR a real paired-delimiter `label` in the
  active config.
- Every category_checks[].expected_absent_token is substring-checked
  against the stripped file. If the token IS present but the subagent
  said found_in_stripped: false, the subagent is wrong.
- Every narrative_spot_checks[].paragraph_excerpt_from_original is
  substring-checked against the original chapter (must be present) AND
  against the stripped file (the subagent's found_in_stripped claim is
  independently verified).
- word_count_delta_check.reported_delta matches the strip log's
  word_counts.delta exactly.
- Every failures[] entry references a category that appears in the strip
  log or the active config.

Router version: v0.1
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._path_compare import paths_equivalent as _paths_equivalent


@dataclass
class ValidationResult:
    """Outcome of a single Strip Verification validation pass."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    corrective_instruction: str | None = None

    # Diagnostic fields the router can log / surface in the Scope Note.
    verdict: str | None = None
    category_checks_count: int | None = None
    spot_checks_count: int | None = None
    failure_count_reported: int | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _load_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return None


# Cross-OS path equivalence is delegated to router.validators._path_compare
# (imported as `_paths_equivalent` at the top of this module). v0.2 (2026-04-22).


def _all_known_labels(strip_log: dict, pwa_config: dict | None) -> set[str]:
    """All labels the subagent is allowed to cite in category_checks / failures."""
    labels: set[str] = set()
    for entry in strip_log.get("rules_applied", []) or []:
        lab = entry.get("label")
        if isinstance(lab, str):
            labels.add(lab)
    if pwa_config is not None:
        for entry in pwa_config.get("paired_delimiters", []) or []:
            lab = entry.get("label")
            if isinstance(lab, str):
                labels.add(lab)
    return labels


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def validate(
    subagent_json: dict,
    original_chapter_path: str,
    stripped_file_path: str,
    strip_log_path: str,
    marker_map_path: str | None,
    pwa_config_path: str,
) -> ValidationResult:
    """
    Validate a Strip Verification subagent JSON payload.

    Parameters
    ----------
    subagent_json
        Parsed JSON as returned by the subagent. MUST follow the schema
        in `subagents/strip_verify.md` v1.0.
    original_chapter_path
        Pre-strip chapter file path.
    stripped_file_path
        Stripped chapter file path written by `strip_engine.py`.
    strip_log_path
        Strip log JSON path written by `strip_engine.py`.
    marker_map_path
        Marker map JSON path if any Mode A/B declarations matched; else
        None or the literal string "(none)".
    pwa_config_path
        Active `pwa_config.json` path resolved per Mode 1 Step 1b.

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
    required_top = (
        "subagent_version",
        "original_chapter_read",
        "stripped_file_read",
        "strip_log_read",
        "verdict",
        "category_checks",
        "narrative_spot_checks",
        "word_count_delta_check",
        "failures",
    )
    for field_name in required_top:
        if field_name not in subagent_json:
            failures.append(f"missing top-level field: {field_name}")

    if subagent_json.get("verdict") not in ("PASS", "FAIL", None):
        failures.append(
            f"verdict must be 'PASS' or 'FAIL', got {subagent_json.get('verdict')!r}"
        )

    diagnostics["verdict"] = subagent_json.get("verdict")

    # Path echoes (OS-aware: same logical file under Windows host or Linux sandbox)
    if not _paths_equivalent(
        original_chapter_path, subagent_json.get("original_chapter_read")
    ):
        failures.append(
            "original_chapter_read does not match dispatched path "
            f"(expected {original_chapter_path!r}, got {subagent_json['original_chapter_read']!r})"
        )
    if not _paths_equivalent(
        stripped_file_path, subagent_json.get("stripped_file_read")
    ):
        failures.append(
            "stripped_file_read does not match dispatched path "
            f"(expected {stripped_file_path!r}, got {subagent_json['stripped_file_read']!r})"
        )
    if not _paths_equivalent(strip_log_path, subagent_json.get("strip_log_read")):
        failures.append(
            "strip_log_read does not match dispatched path "
            f"(expected {strip_log_path!r}, got {subagent_json['strip_log_read']!r})"
        )

    # If the shape is broken, skip further checks.
    if failures:
        return _finalize(failures, corrective_lines, diagnostics)

    # ------------------------------------------------------------------
    # 2. Load supporting artifacts
    # ------------------------------------------------------------------
    original_text = _load_text(original_chapter_path)
    stripped_text = _load_text(stripped_file_path)
    strip_log = _load_json(strip_log_path)
    pwa_config = _load_json(pwa_config_path)

    if original_text is None:
        failures.append(f"original chapter not readable by router: {original_chapter_path}")
    if stripped_text is None:
        failures.append(f"stripped file not readable by router: {stripped_file_path}")
    if strip_log is None:
        failures.append(f"strip log not readable by router: {strip_log_path}")

    if failures:
        return _finalize(failures, corrective_lines, diagnostics)

    known_labels = _all_known_labels(strip_log, pwa_config)

    # ------------------------------------------------------------------
    # 3. Category-check validation
    #
    # Every claimed label must exist in strip log or config.
    # Every expected_absent_token is independently substring-checked
    # against the stripped file.
    # ------------------------------------------------------------------
    category_checks = subagent_json.get("category_checks", []) or []
    diagnostics["category_checks_count"] = len(category_checks)

    for i, check in enumerate(category_checks):
        label = check.get("label")
        token = check.get("expected_absent_token")
        claimed_absent = check.get("found_in_stripped")

        if not isinstance(label, str) or label not in known_labels:
            failures.append(
                f"category_checks[{i}].label {label!r} not found in strip log "
                "rules_applied or active config paired_delimiters"
            )
            corrective_lines.append(
                f"You cited the category label {label!r} in category_checks[{i}], but "
                "that label is not in the strip log's rules_applied array nor in the "
                "active pwa_config.json paired_delimiters array. Cite only labels that "
                "appear in those two places."
            )
            continue

        if not isinstance(token, str) or not token:
            failures.append(
                f"category_checks[{i}].expected_absent_token must be a non-empty string"
            )
            continue

        actually_present = token in stripped_text
        if actually_present and claimed_absent is False:
            failures.append(
                f"category_checks[{i}] for {label!r}: subagent reported "
                f"found_in_stripped: false but token {token!r} IS present in stripped file"
            )
            corrective_lines.append(
                f"For category {label!r}, the token {token!r} appears in the stripped "
                "file at least once, but you reported found_in_stripped: false. "
                "Re-read the stripped file and report the actual presence."
            )
        if not actually_present and claimed_absent is True:
            failures.append(
                f"category_checks[{i}] for {label!r}: subagent reported "
                f"found_in_stripped: true but token {token!r} is NOT present in stripped file"
            )
            corrective_lines.append(
                f"For category {label!r}, the token {token!r} does NOT appear in the "
                "stripped file, but you reported found_in_stripped: true. "
                "Re-read the stripped file and report the actual presence."
            )

    # ------------------------------------------------------------------
    # 4. Narrative spot-check validation
    #
    # Each excerpt MUST be present in the original chapter. The subagent's
    # found_in_stripped claim is independently re-verified.
    # ------------------------------------------------------------------
    spot_checks = subagent_json.get("narrative_spot_checks", []) or []
    diagnostics["spot_checks_count"] = len(spot_checks)

    if len(spot_checks) < 3:
        failures.append(
            f"narrative_spot_checks must have at least 3 entries, got {len(spot_checks)}"
        )

    for i, check in enumerate(spot_checks):
        excerpt = check.get("paragraph_excerpt_from_original")
        claimed_in_stripped = check.get("found_in_stripped")

        if not isinstance(excerpt, str) or not excerpt.strip():
            failures.append(
                f"narrative_spot_checks[{i}].paragraph_excerpt_from_original must be "
                "a non-empty string"
            )
            continue

        if excerpt not in original_text:
            failures.append(
                f"narrative_spot_checks[{i}].paragraph_excerpt_from_original "
                f"not found verbatim in original chapter: {excerpt[:60]!r}..."
            )
            corrective_lines.append(
                f"narrative_spot_checks[{i}] cites an excerpt that does not appear "
                "verbatim in the original chapter. Re-read the original and pick a "
                "literal narrative paragraph."
            )
            continue

        actually_in_stripped = excerpt in stripped_text
        if actually_in_stripped and claimed_in_stripped is False:
            failures.append(
                f"narrative_spot_checks[{i}]: subagent reported found_in_stripped: false "
                f"but excerpt IS present in stripped file: {excerpt[:60]!r}..."
            )
        if not actually_in_stripped and claimed_in_stripped is True:
            failures.append(
                f"narrative_spot_checks[{i}]: subagent reported found_in_stripped: true "
                f"but excerpt is NOT present in stripped file (strip over-reached): "
                f"{excerpt[:60]!r}..."
            )

    # ------------------------------------------------------------------
    # 5. Word-count delta check
    # ------------------------------------------------------------------
    delta_block = subagent_json.get("word_count_delta_check") or {}
    reported_delta = delta_block.get("reported_delta")
    log_word_counts = strip_log.get("word_counts") or {}
    log_delta = log_word_counts.get("delta")

    if reported_delta != log_delta:
        failures.append(
            f"word_count_delta_check.reported_delta ({reported_delta!r}) does not match "
            f"strip log's word_counts.delta ({log_delta!r})"
        )
        corrective_lines.append(
            f"You reported reported_delta = {reported_delta!r} but the strip log's "
            f"word_counts.delta is {log_delta!r}. Read the delta from the strip log "
            "and report it verbatim."
        )

    # ------------------------------------------------------------------
    # 6. Failures-array validation
    #
    # Every failures[] entry must reference a category that exists in the
    # strip log or active config (the v1.25 validator config requirement).
    # ------------------------------------------------------------------
    reported_failures = subagent_json.get("failures", []) or []
    diagnostics["failure_count_reported"] = len(reported_failures)

    for i, fail in enumerate(reported_failures):
        if not isinstance(fail, dict):
            failures.append(f"failures[{i}] must be an object")
            continue
        cat = fail.get("category")
        if not isinstance(cat, str) or cat not in known_labels:
            failures.append(
                f"failures[{i}].category {cat!r} not found in strip log rules_applied "
                "or active config paired_delimiters"
            )
            corrective_lines.append(
                f"failures[{i}].category {cat!r} is not a real category from the strip "
                "log. Cite only labels that appear in rules_applied or paired_delimiters."
            )

    # ------------------------------------------------------------------
    # 7. Verdict consistency
    #
    # If verdict is PASS, failures array must be empty. If FAIL, failures
    # must be non-empty.
    # ------------------------------------------------------------------
    verdict = subagent_json.get("verdict")
    if verdict == "PASS" and reported_failures:
        failures.append(
            f"verdict is PASS but failures array has {len(reported_failures)} entries; "
            "verdict and failures must agree"
        )
    if verdict == "FAIL" and not reported_failures:
        failures.append(
            "verdict is FAIL but failures array is empty; "
            "FAIL must list at least one specific failure"
        )

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
                "Re-read the source files and return corrected JSON.",
            ]
        instruction = "\n".join(corrective_lines)

    return ValidationResult(
        passed=passed,
        failures=failures,
        corrective_instruction=instruction,
        verdict=diagnostics.get("verdict"),
        category_checks_count=diagnostics.get("category_checks_count"),
        spot_checks_count=diagnostics.get("spot_checks_count"),
        failure_count_reported=diagnostics.get("failure_count_reported"),
    )


# ---------------------------------------------------------------------------
# CLI for ad-hoc testing.
#
#     python -m router.validators.strip_verify \
#         --subagent-json path/to/strip-verify.json \
#         --original "path/to/original.txt" \
#         --stripped "path/to/stripped.txt" \
#         --strip-log "path/to/strip log.json" \
#         --pwa-config "path/to/pwa_config.json" \
#         [--marker-map "path/to/marker map.json"]
#
# Exit code 0 on PASS, 1 on FAIL.
# ---------------------------------------------------------------------------


def _cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Router-side validator for Strip Verification subagent output."
    )
    parser.add_argument("--subagent-json", required=True)
    parser.add_argument("--original", required=True)
    parser.add_argument("--stripped", required=True)
    parser.add_argument("--strip-log", required=True)
    parser.add_argument("--pwa-config", required=True)
    parser.add_argument("--marker-map", default=None)
    args = parser.parse_args()

    with open(args.subagent_json, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    result = validate(
        payload,
        original_chapter_path=args.original,
        stripped_file_path=args.stripped,
        strip_log_path=args.strip_log,
        marker_map_path=args.marker_map,
        pwa_config_path=args.pwa_config,
    )

    print(json.dumps(
        {
            "passed": result.passed,
            "failures": result.failures,
            "corrective_instruction": result.corrective_instruction,
            "verdict": result.verdict,
            "category_checks_count": result.category_checks_count,
            "spot_checks_count": result.spot_checks_count,
            "failure_count_reported": result.failure_count_reported,
        },
        indent=2,
    ))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
# end of file
# mount sync trigger v3 - 2026-04-22T18:00 - force bash mount to refresh after Edit-tool path-compare integration
