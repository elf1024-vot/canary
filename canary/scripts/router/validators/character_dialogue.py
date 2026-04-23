"""
Router-side validator for the Character Dialogue Consistency subagent.

Spec: `_standards.md` v1.25, "Subagent Architectural Rule: Subagents
Report, the Router Validates", Validator Config for "Character Dialogue
Consistency".

Contract:

    result = validate(subagent_json, stripped_file_path)

    result.passed                 -> bool
    result.failures               -> list[str], one line per failure
    result.corrective_instruction -> str or None; non-None iff not passed

The router:

1. On `result.passed is True`, accepts the subagent JSON and proceeds.
2. On `result.passed is False` and this is the first attempt, re-dispatches
   the subagent with `result.corrective_instruction` appended to the prompt.
3. On second failure, hard-stops Mode 1 and reports to the author.

Per the architectural rule: this validator NEVER asks the subagent to
re-check itself. All checks are deterministic Python operating on the
returned JSON plus the stripped file on disk.

Scope (v1.25): the subagent reports per-character voice fingerprints
across speech modes (spoken / internal) plus drift_flags and
attribution_flags. This module validates:

  1. Schema shape and path echo.
  2. Per-mode 6-line floor for any cleared sample_status.
  3. Fingerprint shape on cleared (six fields, all non-empty); null on
     insufficient.
  4. Every flag's `paragraph` is an integer in `[1, file_paragraph_count]`.
  5. Every flag's `text` is substring-checked against the stripped file.
  6. Cross-mode drift flags are prohibited: a POV character's drift_flag
     in one mode must not describe a shift TOWARD the other mode's
     established fingerprint.
  7. `flag_count_total` matches the actual count.
  8. `goal_verdict` is consistent with the flag count.

Router version: v0.1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._path_compare import paths_equivalent as _paths_equivalent

# Per-mode sample floor per `_standards.md`.
SAMPLE_FLOOR_LINES = 6

# Fingerprint dimensions (six fields including identity_label).
FINGERPRINT_FIELDS = (
    "identity_label",
    "sentence_length",
    "diction_register",
    "sentence_structure",
    "signature_markers",
    "contractions",
)

# Valid sample_status values.
VALID_SAMPLE_STATUSES = ("cleared", "insufficient sample")

# Mode keys recognised by the spec.
SPOKEN = "spoken"
INTERNAL = "internal"
VALID_MODE_KEYS = (SPOKEN, INTERNAL)


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
    character_count: int | None = None
    cleared_pair_count: int | None = None
    insufficient_pair_count: int | None = None
    drift_flag_count: int | None = None
    attribution_flag_count: int | None = None
    flag_count_reported: int | None = None
    flag_count_actual: int | None = None
    goal_verdict_reported: str | None = None
    file_paragraph_count: int | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_paragraphs(text: str) -> int:
    """Paragraphs are blank-line-separated blocks of non-whitespace text."""
    blocks = re.split(r"\n\s*\n", text)
    return sum(1 for b in blocks if b.strip())


def _is_nonempty_string(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _is_nonneg_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _flag_describes_other_mode(
    flag: dict[str, Any],
    other_fingerprint: dict[str, Any],
) -> bool:
    """Return True iff the drift flag's `shifted_to` text reads as a
    description of the OTHER mode's fingerprint.

    Heuristic: take the other mode's six fingerprint field values, lowercase
    and tokenise on word characters. Lowercase the flag's `shifted_to`
    field. If a substantial fraction of the other-mode fingerprint's
    significant tokens (length >= 4, not common stopwords) appear in the
    flag's shifted_to text, this is cross-mode drift.

    Rationale: a real within-mode drift flag describes a shift with no
    coherent destination ("long, formal, no contractions, no signature
    markers"). A cross-mode drift flag describes the OTHER mode's
    established pattern, which the spec says is normal and not a flag.
    """
    shifted_to = flag.get("shifted_to")
    if not isinstance(shifted_to, str) or not shifted_to.strip():
        return False

    shifted_to_l = shifted_to.lower()

    # Collect significant tokens from the other mode's fingerprint.
    stopwords = {
        "with", "from", "into", "that", "this", "these", "those",
        "have", "been", "were", "more", "less", "very", "some",
        "always", "never", "rarely", "often", "type", "form",
        "word", "words", "line", "lines", "the", "and", "for",
        "but", "not", "are", "use",
    }

    sig_tokens: set[str] = set()
    for field_name in FINGERPRINT_FIELDS:
        value = other_fingerprint.get(field_name)
        if not isinstance(value, str):
            continue
        for tok in re.findall(r"[a-z]+", value.lower()):
            if len(tok) >= 4 and tok not in stopwords:
                sig_tokens.add(tok)

    if not sig_tokens:
        return False

    matches = sum(1 for tok in sig_tokens if tok in shifted_to_l)

    # Conservative threshold: cross-mode drift must show a clear majority
    # of the other mode's distinctive tokens in the shifted_to description.
    # 50% + at least 3 absolute matches keeps the false-positive rate low.
    return matches >= max(3, len(sig_tokens) // 2)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def validate(
    subagent_json: dict[str, Any],
    stripped_file_path: str | Path,
) -> ValidationResult:
    """Validate a Character Dialogue Consistency subagent response."""

    failures: list[str] = []
    result = ValidationResult(passed=False)

    # ---- Section 1: Top-level schema and path echo --------------------

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

    # Accept any v1.x subagent release. Prompt v1.1 added schema-literalness
    # hardening (2026-04-23); schema itself is unchanged from v1.0.
    _sv = subagent_json.get("subagent_version")
    if not isinstance(_sv, str) or not _sv.startswith("v1."):
        failures.append(
            "subagent_version field missing or not a 'v1.x' release"
        )

    expected_path = str(stripped_file_path)
    reported_path = subagent_json.get("stripped_file_read")
    if not isinstance(reported_path, str):
        failures.append("stripped_file_read field missing or not a string")
    elif not _paths_equivalent(expected_path, reported_path):
        failures.append(
            f"stripped_file_read mismatch: subagent reported "
            f"'{reported_path}', dispatched path was '{expected_path}'"
        )

    # ---- Section 2: Load stripped file --------------------------------

    stripped_path = Path(stripped_file_path)
    if not stripped_path.is_file():
        failures.append(f"stripped file not found: {stripped_file_path}")
        result.failures = failures
        result.corrective_instruction = _build_corrective(failures)
        return result

    try:
        stripped_text = stripped_path.read_text(encoding="utf-8")
    except Exception as exc:
        failures.append(
            f"stripped file unreadable as UTF-8: {exc}"
        )
        result.failures = failures
        result.corrective_instruction = _build_corrective(failures)
        return result

    file_paragraph_count = _count_paragraphs(stripped_text)
    result.file_paragraph_count = file_paragraph_count

    # ---- Section 3: character_dialogue_consistency object -------------

    cdc = subagent_json.get("character_dialogue_consistency")
    if not isinstance(cdc, dict):
        failures.append(
            "character_dialogue_consistency object missing or not an object"
        )
        result.failures = failures
        result.corrective_instruction = _build_corrective(failures)
        return result

    for required_key in (
        "total_dialogue_lines",
        "unattributed_lines",
        "characters",
        "goal_verdict",
        "flag_count_total",
    ):
        if required_key not in cdc:
            failures.append(
                f"character_dialogue_consistency.{required_key} missing"
            )

    if not _is_nonneg_int(cdc.get("total_dialogue_lines")):
        failures.append(
            "character_dialogue_consistency.total_dialogue_lines must be a "
            "non-negative integer"
        )

    if not _is_nonneg_int(cdc.get("unattributed_lines")):
        failures.append(
            "character_dialogue_consistency.unattributed_lines must be a "
            "non-negative integer"
        )

    characters = cdc.get("characters")
    if not isinstance(characters, list):
        failures.append(
            "character_dialogue_consistency.characters must be an array"
        )
        result.failures = failures
        result.corrective_instruction = _build_corrective(failures)
        return result

    result.character_count = len(characters)
    result.goal_verdict_reported = (
        cdc.get("goal_verdict")
        if isinstance(cdc.get("goal_verdict"), str)
        else None
    )

    # ---- Section 4: Per-character / per-mode validation ---------------

    cleared_pair_count = 0
    insufficient_pair_count = 0
    drift_flag_count_actual = 0
    attribution_flag_count_actual = 0

    # For cross-mode-drift detection we need to know each POV character's
    # other-mode fingerprint when checking a drift flag.
    pov_fingerprints: dict[str, dict[str, dict[str, Any] | None]] = {}

    for ch_idx, character in enumerate(characters):
        if not isinstance(character, dict):
            failures.append(
                f"characters[{ch_idx}] is not an object"
            )
            continue

        name = character.get("name")
        if not _is_nonempty_string(name):
            failures.append(
                f"characters[{ch_idx}].name must be a non-empty string"
            )
            name_label = f"<index {ch_idx}>"
        else:
            name_label = name

        is_pov = character.get("is_pov")
        if not isinstance(is_pov, bool):
            failures.append(
                f"characters[{ch_idx}] '{name_label}'.is_pov must be a boolean"
            )

        modes = character.get("modes")
        if not isinstance(modes, dict):
            failures.append(
                f"characters[{ch_idx}] '{name_label}'.modes must be an object"
            )
            continue

        if SPOKEN not in modes:
            failures.append(
                f"characters[{ch_idx}] '{name_label}'.modes is missing "
                f"required 'spoken' key (every character has a spoken mode)"
            )

        # Track fingerprints for the cross-mode-drift check (POV only).
        if is_pov is True and name_label not in pov_fingerprints:
            pov_fingerprints[name_label] = {SPOKEN: None, INTERNAL: None}

        for mode_key, mode_obj in modes.items():
            if mode_key not in VALID_MODE_KEYS:
                failures.append(
                    f"characters[{ch_idx}] '{name_label}'.modes contains "
                    f"unknown key '{mode_key}'; valid keys are "
                    f"{list(VALID_MODE_KEYS)}"
                )
                continue

            if not isinstance(mode_obj, dict):
                failures.append(
                    f"characters[{ch_idx}] '{name_label}'.modes."
                    f"{mode_key} must be an object"
                )
                continue

            line_count = mode_obj.get("line_count")
            if not _is_nonneg_int(line_count):
                failures.append(
                    f"characters[{ch_idx}] '{name_label}'.modes."
                    f"{mode_key}.line_count must be a non-negative integer"
                )
                line_count = -1

            sample_status = mode_obj.get("sample_status")
            if sample_status not in VALID_SAMPLE_STATUSES:
                failures.append(
                    f"characters[{ch_idx}] '{name_label}'.modes."
                    f"{mode_key}.sample_status must be one of "
                    f"{list(VALID_SAMPLE_STATUSES)}; got "
                    f"'{sample_status}'"
                )

            fingerprint = mode_obj.get("fingerprint")

            if sample_status == "cleared":
                cleared_pair_count += 1

                # Section 4a: per-mode 6-line floor
                if isinstance(line_count, int) and line_count >= 0:
                    if line_count < SAMPLE_FLOOR_LINES:
                        failures.append(
                            f"characters[{ch_idx}] '{name_label}'.modes."
                            f"{mode_key} reports sample_status='cleared' "
                            f"with line_count={line_count}; the per-mode "
                            f"floor is {SAMPLE_FLOOR_LINES} lines, so this "
                            f"pair must use sample_status='insufficient "
                            f"sample' with fingerprint=null"
                        )

                # Section 4b: fingerprint shape on cleared
                if not isinstance(fingerprint, dict):
                    failures.append(
                        f"characters[{ch_idx}] '{name_label}'.modes."
                        f"{mode_key} reports sample_status='cleared' but "
                        f"fingerprint is not an object"
                    )
                else:
                    for fp_field in FINGERPRINT_FIELDS:
                        val = fingerprint.get(fp_field)
                        if not _is_nonempty_string(val):
                            failures.append(
                                f"characters[{ch_idx}] '{name_label}'."
                                f"modes.{mode_key}.fingerprint.{fp_field} "
                                f"must be a non-empty string"
                            )
                    # Track POV fingerprints for cross-mode-drift detection.
                    if is_pov is True and name_label in pov_fingerprints:
                        pov_fingerprints[name_label][mode_key] = fingerprint

            elif sample_status == "insufficient sample":
                insufficient_pair_count += 1
                if fingerprint is not None:
                    failures.append(
                        f"characters[{ch_idx}] '{name_label}'.modes."
                        f"{mode_key} reports sample_status='insufficient "
                        f"sample' but fingerprint is not null"
                    )

            # Section 4c: drift_flags shape, range, and substring checks
            drift_flags = mode_obj.get("drift_flags", [])
            if not isinstance(drift_flags, list):
                failures.append(
                    f"characters[{ch_idx}] '{name_label}'.modes."
                    f"{mode_key}.drift_flags must be an array"
                )
                drift_flags = []
            else:
                for f_idx, flag in enumerate(drift_flags):
                    drift_flag_count_actual += 1
                    _validate_flag(
                        flag,
                        flag_kind="drift_flag",
                        char_index=ch_idx,
                        char_name=name_label,
                        mode_key=mode_key,
                        flag_index=f_idx,
                        stripped_text=stripped_text,
                        file_paragraph_count=file_paragraph_count,
                        failures=failures,
                    )

            # Section 4d: attribution_flags shape, range, and substring
            attribution_flags = mode_obj.get("attribution_flags", [])
            if not isinstance(attribution_flags, list):
                failures.append(
                    f"characters[{ch_idx}] '{name_label}'.modes."
                    f"{mode_key}.attribution_flags must be an array"
                )
                attribution_flags = []
            else:
                for f_idx, flag in enumerate(attribution_flags):
                    attribution_flag_count_actual += 1
                    _validate_flag(
                        flag,
                        flag_kind="attribution_flag",
                        char_index=ch_idx,
                        char_name=name_label,
                        mode_key=mode_key,
                        flag_index=f_idx,
                        stripped_text=stripped_text,
                        file_paragraph_count=file_paragraph_count,
                        failures=failures,
                    )

    result.cleared_pair_count = cleared_pair_count
    result.insufficient_pair_count = insufficient_pair_count
    result.drift_flag_count = drift_flag_count_actual
    result.attribution_flag_count = attribution_flag_count_actual

    # ---- Section 5: Cross-mode drift prohibition ----------------------
    #
    # For every POV character with BOTH spoken and internal fingerprints
    # cleared, scan their drift_flags in each mode. If a drift_flag's
    # `shifted_to` reads as a description of the OTHER mode's fingerprint,
    # that's a cross-mode drift flag and the spec forbids it.

    for character in characters:
        if not isinstance(character, dict):
            continue
        if character.get("is_pov") is not True:
            continue
        name = character.get("name")
        if not _is_nonempty_string(name):
            continue
        modes = character.get("modes")
        if not isinstance(modes, dict):
            continue

        spoken_fp = pov_fingerprints.get(name, {}).get(SPOKEN)
        internal_fp = pov_fingerprints.get(name, {}).get(INTERNAL)

        if not (isinstance(spoken_fp, dict) and isinstance(internal_fp, dict)):
            # Need both modes cleared to even compute cross-mode drift.
            continue

        # Spoken-mode drift flags must not describe the internal fingerprint.
        spoken_obj = modes.get(SPOKEN)
        if isinstance(spoken_obj, dict):
            for f_idx, flag in enumerate(spoken_obj.get("drift_flags", []) or []):
                if not isinstance(flag, dict):
                    continue
                if _flag_describes_other_mode(flag, internal_fp):
                    failures.append(
                        f"character '{name}' modes.spoken.drift_flags[{f_idx}] "
                        f"describes a shift toward the internal-mode "
                        f"fingerprint; cross-mode drift (spoken-to-internal) "
                        f"is explicitly excluded by the spec and must not "
                        f"be flagged"
                    )

        # Internal-mode drift flags must not describe the spoken fingerprint.
        internal_obj = modes.get(INTERNAL)
        if isinstance(internal_obj, dict):
            for f_idx, flag in enumerate(internal_obj.get("drift_flags", []) or []):
                if not isinstance(flag, dict):
                    continue
                if _flag_describes_other_mode(flag, spoken_fp):
                    failures.append(
                        f"character '{name}' modes.internal.drift_flags"
                        f"[{f_idx}] describes a shift toward the spoken-mode "
                        f"fingerprint; cross-mode drift (internal-to-spoken) "
                        f"is explicitly excluded by the spec and must not "
                        f"be flagged"
                    )

    # ---- Section 6: flag_count_total math -----------------------------

    flag_count_reported = cdc.get("flag_count_total")
    result.flag_count_reported = (
        flag_count_reported if _is_nonneg_int(flag_count_reported) else None
    )
    flag_count_actual = drift_flag_count_actual + attribution_flag_count_actual
    result.flag_count_actual = flag_count_actual

    if not _is_nonneg_int(flag_count_reported):
        failures.append(
            "character_dialogue_consistency.flag_count_total must be a "
            "non-negative integer"
        )
    elif flag_count_reported != flag_count_actual:
        failures.append(
            f"character_dialogue_consistency.flag_count_total reports "
            f"{flag_count_reported} but actual sum of drift_flags "
            f"({drift_flag_count_actual}) plus attribution_flags "
            f"({attribution_flag_count_actual}) is {flag_count_actual}"
        )

    # ---- Section 7: goal_verdict consistency --------------------------

    goal_verdict = cdc.get("goal_verdict")
    if not _is_nonempty_string(goal_verdict):
        failures.append(
            "character_dialogue_consistency.goal_verdict must be a "
            "non-empty string"
        )
    else:
        gv_lower = goal_verdict.lower()
        if cleared_pair_count == 0:
            # No character cleared: must be N/A verdict.
            if "n/a" not in gv_lower:
                failures.append(
                    f"goal_verdict='{goal_verdict}' but no character-mode "
                    f"pair cleared the {SAMPLE_FLOOR_LINES}-line floor; "
                    f"verdict must be an N/A form"
                )
        elif flag_count_actual == 0:
            # Cleared characters with zero flags: ACHIEVED form.
            if "achiev" not in gv_lower:
                failures.append(
                    f"goal_verdict='{goal_verdict}' but flag_count_total "
                    f"is 0 with {cleared_pair_count} cleared pair(s); "
                    f"verdict must be an ACHIEVED form"
                )
        else:
            # Nonzero flags: MISSED form.
            if "miss" not in gv_lower:
                failures.append(
                    f"goal_verdict='{goal_verdict}' but flag_count_total "
                    f"is {flag_count_actual}; verdict must be a MISSED form"
                )

    # ---- Finalise -----------------------------------------------------

    result.failures = failures
    if failures:
        result.corrective_instruction = _build_corrective(failures)
        result.passed = False
    else:
        result.passed = True

    return result


def _validate_flag(
    flag: Any,
    *,
    flag_kind: str,
    char_index: int,
    char_name: str,
    mode_key: str,
    flag_index: int,
    stripped_text: str,
    file_paragraph_count: int,
    failures: list[str],
) -> None:
    """Validate one drift_flag or attribution_flag entry in place.

    Appends any failures encountered to the shared `failures` list.
    """
    prefix = (
        f"characters[{char_index}] '{char_name}'.modes.{mode_key}."
        f"{flag_kind}s[{flag_index}]"
    )

    if not isinstance(flag, dict):
        failures.append(f"{prefix} is not an object")
        return

    paragraph = flag.get("paragraph")
    if not (isinstance(paragraph, int) and not isinstance(paragraph, bool)):
        failures.append(f"{prefix}.paragraph must be an integer")
    elif not (1 <= paragraph <= file_paragraph_count):
        failures.append(
            f"{prefix}.paragraph={paragraph} is out of range "
            f"[1, {file_paragraph_count}]"
        )

    text = flag.get("text")
    if not _is_nonempty_string(text):
        failures.append(f"{prefix}.text must be a non-empty string")
    elif text not in stripped_text:
        # Truncate for the error message.
        excerpt = text[:80] + ("..." if len(text) > 80 else "")
        failures.append(
            f"{prefix}.text not found verbatim in stripped file: "
            f"'{excerpt}'"
        )

    if flag_kind == "drift_flag":
        for required in ("shifted_from", "shifted_to", "tier"):
            val = flag.get(required)
            if not _is_nonempty_string(val):
                failures.append(
                    f"{prefix}.{required} must be a non-empty string"
                )
        # `suspected_cause` is allowed to be empty or "none visible in
        # context" but must be present and a string.
        if not isinstance(flag.get("suspected_cause"), str):
            failures.append(
                f"{prefix}.suspected_cause must be a string"
            )
    elif flag_kind == "attribution_flag":
        for required in ("matches_character_better", "dimensions_matched", "tier"):
            val = flag.get(required)
            if not _is_nonempty_string(val):
                failures.append(
                    f"{prefix}.{required} must be a non-empty string"
                )


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
            "Validate a Character Dialogue Consistency subagent JSON "
            "response against the stripped chapter file."
        )
    )
    parser.add_argument(
        "--subagent-json",
        required=True,
        help="Path to the JSON file containing the subagent's raw response.",
    )
    parser.add_argument(
        "--stripped-file",
        required=True,
        help="Path to the verified stripped prose file the subagent read.",
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

    result = validate(subagent_json, args.stripped_file)

    report = {
        "passed": result.passed,
        "failures": result.failures,
        "corrective_instruction": result.corrective_instruction,
        "diagnostics": {
            "character_count": result.character_count,
            "cleared_pair_count": result.cleared_pair_count,
            "insufficient_pair_count": result.insufficient_pair_count,
            "drift_flag_count": result.drift_flag_count,
            "attribution_flag_count": result.attribution_flag_count,
            "flag_count_reported": result.flag_count_reported,
            "flag_count_actual": result.flag_count_actual,
            "goal_verdict_reported": result.goal_verdict_reported,
            "file_paragraph_count": result.file_paragraph_count,
        },
    }
    print(json.dumps(report, indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(_cli())
