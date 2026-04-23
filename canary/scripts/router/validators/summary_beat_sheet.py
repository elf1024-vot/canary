"""
Router-side validator for the Summary and Beat Sheet subagent.

Spec: `_standards.md` v1.25, "Subagent Architectural Rule: Subagents
Report, the Router Validates", Validator Config for "Summary and Beat
Sheet".

Contract:

    result = validate(subagent_json, original_chapter_path)

    result.passed                -> bool
    result.failures              -> list[str], one line per failure
    result.corrective_instruction -> str or None; non-None iff not passed

The router:

1. On `result.passed is True`, accepts the subagent JSON and folds the
   What Happened block, the Beat Sheet, and the Structural Observations
   into the Mode 1 report.
2. On `result.passed is False` and this is the first attempt, re-dispatches
   the subagent with `result.corrective_instruction` appended to the prompt.
3. On second failure, hard-stops Mode 1 and reports to the author.

Per the architectural rule: this validator NEVER asks the subagent to
re-check itself. All checks are deterministic Python operating on the
returned JSON plus the original chapter file on disk.

Validator config from `_standards.md` v1.25 line 393:
"Summary and Beat Sheet: 5 <= beat count <= 10; every named character
must appear in the source chapter; word ranges must fit within the
chapter's word count."

This module also enforces:
- Schema shape (subagent_version, original_chapter_read, pov_character,
  named_characters, what_happened, beat_sheet, structural_observations).
- chapter_word_count within plus or minus 5% of the router's own
  whitespace-tokenized count.
- what_happened non-empty and at least 200 characters.
- structural_observations 2-3 entries.
- beats contiguous (no gap larger than 50 words between consecutive beats).

Router version: v0.1
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._path_compare import paths_equivalent as _paths_equivalent

# Sanity bounds.
MIN_BEATS = 5
MAX_BEATS = 10
MIN_OBSERVATIONS = 2
MAX_OBSERVATIONS = 3
MIN_WHAT_HAPPENED_CHARS = 200
WORD_COUNT_TOLERANCE_PCT = 5.0
MAX_BEAT_GAP_WORDS = 50


@dataclass
class ValidationResult:
    """Outcome of a single Summary/Beat Sheet validation pass."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    corrective_instruction: str | None = None

    # Diagnostic fields the router can log / surface in the Scope Note.
    pov_character: Any = None
    named_character_count: int | None = None
    beat_count: int | None = None
    structural_observation_count: int | None = None
    chapter_word_count_router: int | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def validate(
    subagent_json: dict,
    original_chapter_path: str,
) -> ValidationResult:
    """
    Validate a Summary and Beat Sheet subagent JSON payload.

    Parameters
    ----------
    subagent_json
        Parsed JSON as returned by the subagent. MUST follow the schema
        in `subagents/summary_beat_sheet.md` v1.0.
    original_chapter_path
        The exact path the router dispatched the subagent with.

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
        "genre",
        "chapter_word_count",
        "pov_character",
        "named_characters",
        "what_happened",
        "beat_sheet",
        "structural_observations",
    )
    for field_name in required_top:
        if field_name not in subagent_json:
            failures.append(f"missing top-level field: {field_name}")

    if "original_chapter_read" in subagent_json and not _paths_equivalent(
        original_chapter_path, subagent_json["original_chapter_read"]
    ):
        failures.append(
            "original_chapter_read does not match dispatched path "
            f"(expected {original_chapter_path!r}, got {subagent_json['original_chapter_read']!r})"
        )
        corrective_lines.append(
            "You reported reading a different file than the one you were dispatched to. "
            f"Re-read EXACTLY this file and no other: {original_chapter_path}"
        )

    diagnostics["pov_character"] = subagent_json.get("pov_character")

    if failures:
        return _finalize(failures, corrective_lines, diagnostics)

    # ------------------------------------------------------------------
    # 2. Original chapter readable + router's own word count
    # ------------------------------------------------------------------
    try:
        original_text = Path(original_chapter_path).read_text(encoding="utf-8")
    except Exception as exc:
        failures.append(f"original chapter not readable by router: {exc}")
        return _finalize(failures, corrective_lines, diagnostics)

    router_word_count = _word_count(original_text)
    diagnostics["chapter_word_count_router"] = router_word_count

    # ------------------------------------------------------------------
    # 3. chapter_word_count within tolerance
    # ------------------------------------------------------------------
    reported_wc = subagent_json.get("chapter_word_count")
    if not isinstance(reported_wc, int):
        failures.append(f"chapter_word_count must be an int, got {reported_wc!r}")
    else:
        if router_word_count > 0:
            pct_diff = abs(reported_wc - router_word_count) / router_word_count * 100.0
            if pct_diff > WORD_COUNT_TOLERANCE_PCT:
                failures.append(
                    f"chapter_word_count {reported_wc} is {pct_diff:.1f}% off from "
                    f"router count {router_word_count} (tolerance: {WORD_COUNT_TOLERANCE_PCT}%)"
                )
                corrective_lines.append(
                    f"You reported chapter_word_count = {reported_wc} but the router's "
                    f"whitespace tokenization yields {router_word_count}. Recount and "
                    "report a value within plus or minus 5% of the actual count."
                )

    # ------------------------------------------------------------------
    # 4. POV character shape
    # ------------------------------------------------------------------
    pov = subagent_json.get("pov_character")
    if pov is None or pov == "":
        failures.append("pov_character is missing or empty")
    elif isinstance(pov, list):
        if not pov or not all(isinstance(p, str) and p for p in pov):
            failures.append("pov_character list must contain at least one non-empty string")
    elif not isinstance(pov, str):
        failures.append(f"pov_character must be string or list of strings, got {type(pov).__name__}")

    # ------------------------------------------------------------------
    # 5. Named characters substring-checked against original chapter
    #
    # This is the v1.25 validator-config requirement: "every named
    # character must appear in the source chapter."
    # ------------------------------------------------------------------
    named_chars = subagent_json.get("named_characters", []) or []
    if not isinstance(named_chars, list):
        failures.append(f"named_characters must be a list, got {type(named_chars).__name__}")
    else:
        diagnostics["named_character_count"] = len(named_chars)
        for i, name in enumerate(named_chars):
            if not isinstance(name, str) or not name.strip():
                failures.append(f"named_characters[{i}] must be a non-empty string")
                continue
            if name not in original_text:
                failures.append(
                    f"named_characters[{i}] {name!r} does not appear verbatim in original chapter"
                )
                corrective_lines.append(
                    f"You named {name!r} in named_characters, but that exact string does "
                    "not appear in the original chapter. Re-read the chapter and name only "
                    "characters whose names are written on the page. If a character is "
                    "unnamed, refer to them by role in what_happened and omit them from "
                    "named_characters."
                )

    # ------------------------------------------------------------------
    # 6. What Happened non-empty and substantive
    # ------------------------------------------------------------------
    wh = subagent_json.get("what_happened")
    if not isinstance(wh, str) or not wh.strip():
        failures.append("what_happened must be a non-empty string")
    elif len(wh) < MIN_WHAT_HAPPENED_CHARS:
        failures.append(
            f"what_happened too short ({len(wh)} chars, minimum {MIN_WHAT_HAPPENED_CHARS}); "
            "summary must be substantive"
        )
        corrective_lines.append(
            f"what_happened is {len(wh)} characters; it should be a real two-to-three-paragraph "
            "summary. Expand it to cover POV, setting, inciting action, key turns, ending state."
        )

    # ------------------------------------------------------------------
    # 7. Beat sheet count + structure
    # ------------------------------------------------------------------
    beats = subagent_json.get("beat_sheet", []) or []
    if not isinstance(beats, list):
        failures.append(f"beat_sheet must be a list, got {type(beats).__name__}")
        return _finalize(failures, corrective_lines, diagnostics)

    diagnostics["beat_count"] = len(beats)

    if len(beats) < MIN_BEATS or len(beats) > MAX_BEATS:
        failures.append(
            f"beat_sheet has {len(beats)} entries; required range is "
            f"[{MIN_BEATS}, {MAX_BEATS}]"
        )
        corrective_lines.append(
            f"beat_sheet has {len(beats)} beats; the spec requires 5 to 10 inclusive. "
            f"{'Add more beats by splitting long sections.' if len(beats) < MIN_BEATS else 'Collapse adjacent beats; the current breakdown is too granular.'}"
        )

    # Per-beat shape + word-range validation
    prev_end = -1
    for i, beat in enumerate(beats):
        if not isinstance(beat, dict):
            failures.append(f"beat_sheet[{i}] must be an object")
            continue
        for key in ("number", "name", "word_range_start", "word_range_end", "description"):
            if key not in beat:
                failures.append(f"beat_sheet[{i}].{key} missing")
        wstart = beat.get("word_range_start")
        wend = beat.get("word_range_end")
        if not isinstance(wstart, int) or not isinstance(wend, int):
            failures.append(
                f"beat_sheet[{i}] word_range_start and word_range_end must be ints"
            )
            continue
        if wstart < 0 or wend < 0:
            failures.append(f"beat_sheet[{i}] word ranges cannot be negative")
        if wstart > wend:
            failures.append(
                f"beat_sheet[{i}] word_range_start ({wstart}) > word_range_end ({wend})"
            )
        if wend > router_word_count:
            failures.append(
                f"beat_sheet[{i}].word_range_end ({wend}) exceeds chapter word count "
                f"({router_word_count})"
            )
            corrective_lines.append(
                f"beat_sheet[{i}] ends at word {wend}, beyond the chapter's {router_word_count} "
                "words. Re-estimate beat ranges so the final beat ends at or before the "
                "actual word count."
            )
        # Contiguity: no large gap from previous beat
        if prev_end >= 0 and wstart > prev_end + MAX_BEAT_GAP_WORDS + 1:
            failures.append(
                f"beat_sheet[{i}] starts at word {wstart}, leaving a gap of "
                f"{wstart - prev_end - 1} words after beat[{i-1}] (max gap allowed: "
                f"{MAX_BEAT_GAP_WORDS}); beats must cover the chapter contiguously"
            )
        prev_end = wend

    # ------------------------------------------------------------------
    # 8. Structural observations 2-3
    # ------------------------------------------------------------------
    obs = subagent_json.get("structural_observations", []) or []
    if not isinstance(obs, list):
        failures.append(f"structural_observations must be a list, got {type(obs).__name__}")
    else:
        diagnostics["structural_observation_count"] = len(obs)
        if len(obs) < MIN_OBSERVATIONS or len(obs) > MAX_OBSERVATIONS:
            failures.append(
                f"structural_observations has {len(obs)} entries; required range is "
                f"[{MIN_OBSERVATIONS}, {MAX_OBSERVATIONS}]"
            )
        for i, ob in enumerate(obs):
            if not isinstance(ob, str) or not ob.strip():
                failures.append(f"structural_observations[{i}] must be a non-empty string")

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
                "Re-read the original chapter and return corrected JSON.",
            ]
        instruction = "\n".join(corrective_lines)

    return ValidationResult(
        passed=passed,
        failures=failures,
        corrective_instruction=instruction,
        pov_character=diagnostics.get("pov_character"),
        named_character_count=diagnostics.get("named_character_count"),
        beat_count=diagnostics.get("beat_count"),
        structural_observation_count=diagnostics.get("structural_observation_count"),
        chapter_word_count_router=diagnostics.get("chapter_word_count_router"),
    )


# ---------------------------------------------------------------------------
# CLI for ad-hoc testing.
#
#     python -m router.validators.summary_beat_sheet \
#         --subagent-json path/to/summary-beat-sheet.json \
#         --original "path/to/original.txt"
#
# Exit code 0 on PASS, 1 on FAIL.
# ---------------------------------------------------------------------------


def _cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Router-side validator for Summary and Beat Sheet subagent output."
    )
    parser.add_argument("--subagent-json", required=True)
    parser.add_argument("--original", required=True)
    args = parser.parse_args()

    with open(args.subagent_json, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    result = validate(payload, original_chapter_path=args.original)

    print(json.dumps(
        {
            "passed": result.passed,
            "failures": result.failures,
            "corrective_instruction": result.corrective_instruction,
            "pov_character": result.pov_character,
            "named_character_count": result.named_character_count,
            "beat_count": result.beat_count,
            "structural_observation_count": result.structural_observation_count,
            "chapter_word_count_router": result.chapter_word_count_router,
        },
        indent=2,
    ))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
