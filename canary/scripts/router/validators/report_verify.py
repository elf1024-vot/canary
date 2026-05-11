"""
Router-side validator for the Report Verification subagent.

Spec: `_standards.md` v1.25, "Subagent Architectural Rule: Subagents
Report, the Router Validates", Validator Config for "Report
Verification".

Contract:

    result = validate(subagent_json, paths)

    paths is a dict-like with keys:
        report
        original_chapter
        tokenizer_json
        grammar_spelling_json
        summary_beat_sheet_json
        character_dialogue_json
        marker_map        (optional; pass None or "(none)" if absent)
        pwa_config
        strip_log

    result.passed                 -> bool
    result.failures               -> list[str], one line per failure
    result.corrective_instruction -> str or None; non-None iff not passed

The router:

1. On `result.passed is True`, accepts the subagent JSON. The verdict
   field drives the next step:
     - PASS  -> proceed to save the report.
     - FIX   -> apply each `discrepancies[].correction` then save.
     - FAIL  -> hard-stop and report to the author.
2. On `result.passed is False` and this is the first attempt,
   re-dispatches the verifier with `result.corrective_instruction`
   appended to the prompt.
3. On second failure, hard-stops Mode 1 and reports to the author.

Per the architectural rule: this validator NEVER asks the subagent to
re-check itself. All checks are deterministic Python operating on the
returned JSON plus the source artifacts on disk.

Recursion depth: this validator does NOT dispatch yet another verifier
to validate this verifier's output. The router itself is the trusted
root, per `_standards.md` v1.25.

Validation surface:

  1. Schema shape and path echoes match dispatched paths.
  2. `verdict` in {PASS, FIX, FAIL}.
  3. `narrative_checks[]`: every claim substring-checked against the
     report file; every claim with `found_in_chapter: true` is
     INDEPENDENTLY substring-checked against the original chapter.
  4. `metric_checks[]`: every `report_value` substring-checked against
     the report; every `source_value` substring-checked against the
     cited source artifact.
  5. `flagged_item_checks[]`: every `category` substring-checked against
     the report.
  6. `discrepancies[]`: every entry has tier in {FIX, FAIL}, non-empty
     category in the eleven valid categories, non-empty location and
     evidence; FIX entries have non-empty `correction`.
  7. `verdict` consistency: PASS implies discrepancies empty; FIX
     implies discrepancies non-empty with no FAIL; FAIL implies at
     least one FAIL discrepancy.
  8. `disclosure_checks`, `character_dialogue_checks`,
     `non_character_voice_checks`, `config_and_strip_log_checks` are
     all objects with the expected shape (or `applicable: false`).

Router version: v0.1
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._path_compare import paths_equivalent as _paths_equivalent

VALID_VERDICTS = ("PASS", "FIX", "FAIL")
VALID_DISCREPANCY_TIERS = ("FIX", "FAIL")

# Eleven valid check categories per `_standards.md` "Report Verification
# Pass" section. These are the categories a discrepancy may cite.
VALID_DISCREPANCY_CATEGORIES = (
    "narrative_check",
    "metric_check",
    "grammar_spelling_check",
    "threshold_direction_check",
    "disclosure_check",
    "placeholder_text",
    "report_language_check",
    "flagged_item_check",
    "character_dialogue_check",
    "non_character_voice_check",
    "config_and_strip_log_check",
)

# Source artifact labels valid for `metric_checks[].source_artifact`.
VALID_SOURCE_ARTIFACTS = (
    "tokenizer_json",
    "grammar_spelling_json",
    "summary_beat_sheet_json",
    "character_dialogue_json",
    "marker_map",
    "pwa_config",
    "strip_log",
)

# Required keys in `disclosure_checks`.
EXPECTED_DISCLOSURE_KEYS = (
    "strip_verification",
    "grammar_spelling_pass",
    "summary_beat_sheet_pass",
    "character_dialogue_pass",
    "non_character_voice_registers",
    "active_config_path",
    "strip_log_presence",
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Outcome of a single validation pass."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    corrective_instruction: str | None = None

    # Diagnostic fields the router can log / surface in reports.
    verdict: str | None = None
    narrative_check_count: int | None = None
    narrative_found_in_chapter_count: int | None = None
    metric_check_count: int | None = None
    flagged_item_check_count: int | None = None
    discrepancy_count: int | None = None
    fix_discrepancy_count: int | None = None
    fail_discrepancy_count: int | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_nonempty_string(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _path_matches(reported: Any, expected: str | None) -> bool:
    """Compare a reported path string to the dispatched path. Allow the
    literal '(none)' when expected is None. Uses cross-OS path normalization
    so a Windows-form path and a Linux-mount-form path that point at the
    same logical file compare equal."""
    if expected is None:
        return reported == "(none)"
    if not isinstance(reported, str):
        return False
    return _paths_equivalent(expected, reported)


def _read_text_or_fail(
    path: str | Path | None,
    label: str,
    failures: list[str],
) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_file():
        failures.append(f"{label} file not found: {path}")
        return None
    try:
        return p.read_text(encoding="utf-8")
    except Exception as exc:
        failures.append(f"{label} unreadable: {exc}")
        return None


def _load_json_text_or_fail(
    path: str | Path | None,
    label: str,
    failures: list[str],
) -> str | None:
    """Return the raw JSON text (not parsed) so we can substring-check
    `source_value` strings against it."""
    return _read_text_or_fail(path, label, failures)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def validate(
    subagent_json: dict[str, Any],
    paths: dict[str, str | None],
) -> ValidationResult:
    """Validate a Report Verification subagent response."""

    failures: list[str] = []
    result = ValidationResult(passed=False)

    # ---- Section 1: Top-level schema ----------------------------------

    if not isinstance(subagent_json, dict):
        failures.append("subagent response is not a JSON object")
        result.failures = failures
        result.corrective_instruction = _build_corrective(failures)
        return result

    if "error" in subagent_json:
        failures.append(
            f"subagent reported error: {subagent_json['error']}"
        )
        result.failures = failures
        result.corrective_instruction = _build_corrective(failures)
        return result

    sv = subagent_json.get("subagent_version")
    if not isinstance(sv, str) or not sv.startswith("v1."):
        failures.append(
            f"subagent_version must be a v1.x string; got {sv!r}"
        )

    # ---- Section 2: Path echoes ---------------------------------------

    path_echo_map = (
        ("report_read", paths.get("report"), "report"),
        ("original_chapter_read", paths.get("original_chapter"),
         "original_chapter"),
        ("tokenizer_json_read", paths.get("tokenizer_json"),
         "tokenizer_json"),
        ("grammar_spelling_json_read", paths.get("grammar_spelling_json"),
         "grammar_spelling_json"),
        ("summary_beat_sheet_json_read",
         paths.get("summary_beat_sheet_json"),
         "summary_beat_sheet_json"),
        ("character_dialogue_json_read",
         paths.get("character_dialogue_json"),
         "character_dialogue_json"),
        ("marker_map_read", paths.get("marker_map"), "marker_map"),
        ("pwa_config_read", paths.get("pwa_config"), "pwa_config"),
        ("strip_log_read", paths.get("strip_log"), "strip_log"),
    )
    for field_name, expected, label in path_echo_map:
        reported = subagent_json.get(field_name)
        if not _path_matches(reported, expected):
            failures.append(
                f"{field_name} mismatch: subagent reported '{reported}', "
                f"dispatched path was '{expected}'"
            )

    # ---- Section 3: verdict field -------------------------------------

    verdict = subagent_json.get("verdict")
    result.verdict = verdict if isinstance(verdict, str) else None
    if verdict not in VALID_VERDICTS:
        failures.append(
            f"verdict must be one of {list(VALID_VERDICTS)}; got {verdict!r}"
        )

    # ---- Section 4: Load source artifact texts ------------------------

    report_text = _read_text_or_fail(
        paths.get("report"), "report", failures
    )
    original_text = _read_text_or_fail(
        paths.get("original_chapter"), "original chapter", failures
    )
    artifact_texts: dict[str, str | None] = {
        "tokenizer_json": _load_json_text_or_fail(
            paths.get("tokenizer_json"), "tokenizer JSON", failures
        ),
        "grammar_spelling_json": _load_json_text_or_fail(
            paths.get("grammar_spelling_json"),
            "Grammar/Spelling JSON",
            failures,
        ),
        "summary_beat_sheet_json": _load_json_text_or_fail(
            paths.get("summary_beat_sheet_json"),
            "Summary/Beat Sheet JSON",
            failures,
        ),
        "character_dialogue_json": _load_json_text_or_fail(
            paths.get("character_dialogue_json"),
            "Character Dialogue JSON",
            failures,
        ),
        "pwa_config": _load_json_text_or_fail(
            paths.get("pwa_config"), "pwa_config.json", failures
        ),
        "strip_log": _load_json_text_or_fail(
            paths.get("strip_log"), "strip log JSON", failures
        ),
    }
    if paths.get("marker_map") is not None:
        artifact_texts["marker_map"] = _load_json_text_or_fail(
            paths.get("marker_map"), "marker map JSON", failures
        )
    else:
        artifact_texts["marker_map"] = None

    # If we couldn't load critical files, return now; downstream checks
    # would fault.
    if report_text is None or original_text is None:
        result.failures = failures
        result.corrective_instruction = _build_corrective(failures)
        return result

    # ---- Section 5: narrative_checks ----------------------------------

    narrative_checks = subagent_json.get("narrative_checks")
    if not isinstance(narrative_checks, list):
        failures.append("narrative_checks must be an array")
        narrative_checks = []
    result.narrative_check_count = len(narrative_checks)

    narrative_found_count = 0
    for n_idx, entry in enumerate(narrative_checks):
        if not isinstance(entry, dict):
            failures.append(f"narrative_checks[{n_idx}] is not an object")
            continue

        claim = entry.get("claim")
        if not _is_nonempty_string(claim):
            failures.append(
                f"narrative_checks[{n_idx}].claim must be a non-empty string"
            )
            continue

        if claim not in report_text:
            excerpt = claim[:80] + ("..." if len(claim) > 80 else "")
            failures.append(
                f"narrative_checks[{n_idx}].claim not found verbatim in "
                f"the assembled report: '{excerpt}'"
            )

        found_in_chapter = entry.get("found_in_chapter")
        if not isinstance(found_in_chapter, bool):
            failures.append(
                f"narrative_checks[{n_idx}].found_in_chapter must be boolean"
            )
            continue

        if found_in_chapter:
            narrative_found_count += 1
            # Independent re-check: the source excerpt must be in the
            # original chapter, AND the claim must be substring-locatable
            # there too (the verifier should be quoting the chapter).
            source_excerpt = entry.get("source_excerpt_from_chapter")
            if _is_nonempty_string(source_excerpt):
                if source_excerpt not in original_text:
                    excerpt = source_excerpt[:80] + (
                        "..." if len(source_excerpt) > 80 else ""
                    )
                    failures.append(
                        f"narrative_checks[{n_idx}].source_excerpt_from_"
                        f"chapter not found verbatim in original chapter: "
                        f"'{excerpt}'"
                    )
            # The claim itself need not be a verbatim substring of the
            # chapter (the report often paraphrases, e.g., "POV: Alex"
            # for a chapter that just shows Alex narrating). But if the
            # subagent claims found_in_chapter: true AND there's no
            # source_excerpt to anchor it, that's a defect.
            if not _is_nonempty_string(source_excerpt):
                failures.append(
                    f"narrative_checks[{n_idx}].found_in_chapter is true "
                    f"but no source_excerpt_from_chapter was provided"
                )

    result.narrative_found_in_chapter_count = narrative_found_count

    # ---- Section 6: metric_checks -------------------------------------

    metric_checks = subagent_json.get("metric_checks")
    if not isinstance(metric_checks, list):
        failures.append("metric_checks must be an array")
        metric_checks = []
    result.metric_check_count = len(metric_checks)

    for m_idx, entry in enumerate(metric_checks):
        if not isinstance(entry, dict):
            failures.append(f"metric_checks[{m_idx}] is not an object")
            continue

        report_value = entry.get("report_value")
        source_value = entry.get("source_value")
        source_artifact = entry.get("source_artifact")

        if not _is_nonempty_string(entry.get("metric_label")):
            failures.append(
                f"metric_checks[{m_idx}].metric_label must be non-empty string"
            )

        if not _is_nonempty_string(report_value):
            failures.append(
                f"metric_checks[{m_idx}].report_value must be non-empty string"
            )
        elif report_value not in report_text:
            failures.append(
                f"metric_checks[{m_idx}].report_value '{report_value}' not "
                f"found verbatim in assembled report"
            )

        if source_artifact not in VALID_SOURCE_ARTIFACTS:
            failures.append(
                f"metric_checks[{m_idx}].source_artifact must be one of "
                f"{list(VALID_SOURCE_ARTIFACTS)}; got {source_artifact!r}"
            )
            artifact_text = None
        else:
            artifact_text = artifact_texts.get(source_artifact)
            if artifact_text is None:
                failures.append(
                    f"metric_checks[{m_idx}].source_artifact "
                    f"'{source_artifact}' not loadable for substring check"
                )

        if not _is_nonempty_string(source_value):
            failures.append(
                f"metric_checks[{m_idx}].source_value must be non-empty string"
            )
        elif artifact_text is not None and source_value not in artifact_text:
            failures.append(
                f"metric_checks[{m_idx}].source_value '{source_value}' not "
                f"found verbatim in source artifact '{source_artifact}'"
            )

        if not isinstance(entry.get("matches"), bool):
            failures.append(
                f"metric_checks[{m_idx}].matches must be boolean"
            )

    # ---- Section 7: flagged_item_checks -------------------------------

    flagged_item_checks = subagent_json.get("flagged_item_checks")
    if not isinstance(flagged_item_checks, list):
        failures.append("flagged_item_checks must be an array")
        flagged_item_checks = []
    result.flagged_item_check_count = len(flagged_item_checks)

    for f_idx, entry in enumerate(flagged_item_checks):
        if not isinstance(entry, dict):
            failures.append(f"flagged_item_checks[{f_idx}] is not an object")
            continue
        category = entry.get("category")
        if not _is_nonempty_string(category):
            failures.append(
                f"flagged_item_checks[{f_idx}].category must be non-empty"
            )
        elif category not in report_text:
            failures.append(
                f"flagged_item_checks[{f_idx}].category '{category}' not "
                f"found in assembled report"
            )
        for required in ("flag_count", "row_count"):
            if not isinstance(entry.get(required), int):
                failures.append(
                    f"flagged_item_checks[{f_idx}].{required} must be int"
                )
        for required in ("table_present", "text_verified_in_chapter"):
            if not isinstance(entry.get(required), bool):
                failures.append(
                    f"flagged_item_checks[{f_idx}].{required} must be boolean"
                )

    # ---- Section 8: disclosure_checks ---------------------------------

    disclosure_checks = subagent_json.get("disclosure_checks")
    if not isinstance(disclosure_checks, dict):
        failures.append("disclosure_checks must be an object")
    else:
        for key in EXPECTED_DISCLOSURE_KEYS:
            if key not in disclosure_checks:
                failures.append(f"disclosure_checks.{key} missing")
            elif not isinstance(disclosure_checks.get(key), bool):
                failures.append(f"disclosure_checks.{key} must be boolean")

    # ---- Section 9: placeholder_text_findings -------------------------

    placeholder_findings = subagent_json.get("placeholder_text_findings")
    if not isinstance(placeholder_findings, list):
        failures.append("placeholder_text_findings must be an array")
    else:
        for p_idx, entry in enumerate(placeholder_findings):
            if not isinstance(entry, dict):
                failures.append(
                    f"placeholder_text_findings[{p_idx}] is not an object"
                )
                continue
            if not _is_nonempty_string(entry.get("location")):
                failures.append(
                    f"placeholder_text_findings[{p_idx}].location must be "
                    f"non-empty string"
                )
            if not _is_nonempty_string(entry.get("string_found")):
                failures.append(
                    f"placeholder_text_findings[{p_idx}].string_found must "
                    f"be non-empty string"
                )

    # ---- Section 10: report_language_checks ---------------------------

    rlc = subagent_json.get("report_language_checks")
    if not isinstance(rlc, list):
        failures.append("report_language_checks must be an array")
    else:
        for r_idx, entry in enumerate(rlc):
            if not isinstance(entry, dict):
                failures.append(
                    f"report_language_checks[{r_idx}] is not an object"
                )
                continue
            for required in ("location", "offense", "original", "rewritten"):
                if not _is_nonempty_string(entry.get(required)):
                    failures.append(
                        f"report_language_checks[{r_idx}].{required} must "
                        f"be non-empty string"
                    )
            # The 'original' must be substring-checkable in the report.
            original = entry.get("original")
            if _is_nonempty_string(original) and original not in report_text:
                excerpt = original[:80] + ("..." if len(original) > 80 else "")
                failures.append(
                    f"report_language_checks[{r_idx}].original not found "
                    f"verbatim in assembled report: '{excerpt}'"
                )

    # ---- Section 11: character_dialogue_checks (shape only) ----------

    cdc = subagent_json.get("character_dialogue_checks")
    if not isinstance(cdc, dict):
        failures.append("character_dialogue_checks must be an object")
    else:
        if "pass_ran" not in cdc or not isinstance(cdc.get("pass_ran"), bool):
            failures.append(
                "character_dialogue_checks.pass_ran must be boolean"
            )

    # ---- Section 12: non_character_voice_checks (shape only) ---------

    ncv = subagent_json.get("non_character_voice_checks")
    if not isinstance(ncv, dict):
        failures.append("non_character_voice_checks must be an object")
    elif ncv.get("applicable") is False:
        # Acceptable: marker map absent or no Mode B spans.
        pass
    else:
        for required in (
            "marker_map_has_mode_b_spans",
            "section_present_in_report",
            "diagnostic_disclosure_language_present",
            "mode_b_content_absent_from_stripped",
        ):
            if not isinstance(ncv.get(required), bool):
                failures.append(
                    f"non_character_voice_checks.{required} must be boolean "
                    f"(or set non_character_voice_checks to {{\"applicable\": "
                    f"false}} if no marker map / no Mode B spans)"
                )

    # ---- Section 13: config_and_strip_log_checks (shape only) --------

    cslc = subagent_json.get("config_and_strip_log_checks")
    if not isinstance(cslc, dict):
        failures.append("config_and_strip_log_checks must be an object")
    else:
        for required_bool in (
            "config_path_in_scope_note",
            "strip_log_present",
            "strip_log_labels_match_config_labels",
            "strip_log_summary_present",
        ):
            if not isinstance(cslc.get(required_bool), bool):
                failures.append(
                    f"config_and_strip_log_checks.{required_bool} must be "
                    f"boolean"
                )
        if not _is_nonempty_string(cslc.get("active_config_path")):
            failures.append(
                "config_and_strip_log_checks.active_config_path must be "
                "non-empty string"
            )

    # ---- Section 14: discrepancies ------------------------------------

    discrepancies = subagent_json.get("discrepancies")
    if not isinstance(discrepancies, list):
        failures.append("discrepancies must be an array")
        discrepancies = []
    result.discrepancy_count = len(discrepancies)

    fix_count = 0
    fail_count = 0
    for d_idx, entry in enumerate(discrepancies):
        if not isinstance(entry, dict):
            failures.append(f"discrepancies[{d_idx}] is not an object")
            continue

        tier = entry.get("tier")
        if tier not in VALID_DISCREPANCY_TIERS:
            failures.append(
                f"discrepancies[{d_idx}].tier must be one of "
                f"{list(VALID_DISCREPANCY_TIERS)}; got {tier!r}"
            )
        elif tier == "FIX":
            fix_count += 1
            if not _is_nonempty_string(entry.get("correction")):
                failures.append(
                    f"discrepancies[{d_idx}] tier=FIX requires non-empty "
                    f"correction field"
                )
        elif tier == "FAIL":
            fail_count += 1

        category = entry.get("category")
        if category not in VALID_DISCREPANCY_CATEGORIES:
            failures.append(
                f"discrepancies[{d_idx}].category must be one of "
                f"{list(VALID_DISCREPANCY_CATEGORIES)}; got {category!r}"
            )

        for required in ("location", "evidence"):
            if not _is_nonempty_string(entry.get(required)):
                failures.append(
                    f"discrepancies[{d_idx}].{required} must be non-empty "
                    f"string"
                )

    result.fix_discrepancy_count = fix_count
    result.fail_discrepancy_count = fail_count

    # ---- Section 15: verdict consistency ------------------------------

    if verdict == "PASS" and len(discrepancies) > 0:
        failures.append(
            f"verdict='PASS' but discrepancies has {len(discrepancies)} "
            f"entries; PASS requires empty discrepancies"
        )
    elif verdict == "FIX":
        if len(discrepancies) == 0:
            failures.append(
                "verdict='FIX' but discrepancies is empty; FIX requires at "
                "least one discrepancy"
            )
        if fail_count > 0:
            failures.append(
                f"verdict='FIX' but discrepancies contains {fail_count} "
                f"FAIL-tier entries; verdict must be 'FAIL' if any FAIL "
                f"exists"
            )
    elif verdict == "FAIL":
        if fail_count == 0:
            failures.append(
                "verdict='FAIL' but no discrepancy has tier='FAIL'; FAIL "
                "verdict requires at least one FAIL discrepancy"
            )

    # ---- Finalise -----------------------------------------------------

    result.failures = failures
    if failures:
        result.corrective_instruction = _build_corrective(failures)
        result.passed = False
    else:
        result.passed = True

    return result


def _build_corrective(failures: list[str]) -> str:
    lines = [
        "Your previous response failed router validation. The following",
        "items must be corrected before this pass can complete:",
        "",
    ]
    for f in failures:
        lines.append(f"- {f}")
    lines.append("")
    lines.append(
        "Re-read the source files, correct every listed item, and return "
        "the full corrected JSON object. Do not return only a diff."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Report Verification subagent JSON response "
            "against the assembled report and all source artifacts."
        )
    )
    parser.add_argument("--subagent-json", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--original-chapter", required=True)
    parser.add_argument("--tokenizer-json", required=True)
    parser.add_argument("--grammar-spelling-json", required=True)
    parser.add_argument("--summary-beat-sheet-json", required=True)
    parser.add_argument("--character-dialogue-json", required=True)
    parser.add_argument("--pwa-config", required=True)
    parser.add_argument("--strip-log", required=True)
    parser.add_argument(
        "--marker-map",
        default=None,
        help="Marker map JSON path; omit if no marker map exists.",
    )
    args = parser.parse_args()

    sj_path = Path(args.subagent_json)
    if not sj_path.is_file():
        report = {
            "passed": False,
            "failures": [f"subagent JSON file not found: {sj_path}"],
            "corrective_instruction": None,
        }
        print(json.dumps(report, indent=2))
        return 1

    try:
        subagent_json = json.loads(sj_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report = {
            "passed": False,
            "failures": [f"subagent JSON parse error: {exc}"],
            "corrective_instruction": (
                "Your previous response was not valid JSON. Return strict "
                "JSON only, with no surrounding prose, no markdown code "
                "fences, and no trailing commentary."
            ),
        }
        print(json.dumps(report, indent=2))
        return 1

    paths: dict[str, str | None] = {
        "report": args.report,
        "original_chapter": args.original_chapter,
        "tokenizer_json": args.tokenizer_json,
        "grammar_spelling_json": args.grammar_spelling_json,
        "summary_beat_sheet_json": args.summary_beat_sheet_json,
        "character_dialogue_json": args.character_dialogue_json,
        "pwa_config": args.pwa_config,
        "strip_log": args.strip_log,
        "marker_map": args.marker_map,
    }

    result = validate(subagent_json, paths)

    report = {
        "passed": result.passed,
        "failures": result.failures,
        "corrective_instruction": result.corrective_instruction,
        "diagnostics": {
            "verdict": result.verdict,
            "narrative_check_count": result.narrative_check_count,
            "narrative_found_in_chapter_count":
                result.narrative_found_in_chapter_count,
            "metric_check_count": result.metric_check_count,
            "flagged_item_check_count": result.flagged_item_check_count,
            "discrepancy_count": result.discrepancy_count,
            "fix_discrepancy_count": result.fix_discrepancy_count,
            "fail_discrepancy_count": result.fail_discrepancy_count,
        },
    }
    print(json.dumps(report, indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(_cli())
