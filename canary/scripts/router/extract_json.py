"""
router/extract_json.py - Prose-wrap-tolerant JSON extractor.

Policy: Option A (Lenient), resolved 2026-04-23 (see prose_wrap_policy_memo.md).

Subagents in the PWA routine reliably return wrapped responses despite prompt
instructions. Preamble like "I've analyzed the file, here are my findings..."
then JSON then a sign-off. The subagent architectural rule is preserved: prompts
still say "no prose before, no prose after" so the schema is unambiguous to the
subagent. This helper handles the observed reality at the receiving side: find
the JSON object in a wrapped response and return it parsed.

Contract:

    extract_subagent_json(response_text: str) -> dict

    On success: returns the parsed JSON object.
    On failure: raises ExtractionError with .reason and .excerpt attributes.

The extractor is intentionally simple. It:

  1. Strips leading/trailing whitespace.
  2. Strips a markdown code fence (```json ... ``` or ``` ... ```) if the whole
     response is wrapped in one.
  3. Scans for the first `{` that begins a balanced-brace block terminating in
     `}`, tracking quoted strings so braces inside string literals don't
     confuse the balance count.
  4. Slices that block and feeds it to json.loads.
  5. Requires json.loads to return a dict (not a list or scalar).

If the subagent returns multiple top-level JSON blocks, only the first parseable
one is returned. The subagents in the PWA routine are specified to return a
single object, so seeing multiple is itself a signal the subagent is
malformed; the validator will catch shape issues downstream.

No attempt is made to "repair" malformed JSON (trailing commas, single quotes,
etc.). If the block is present but not parseable, ExtractionError is raised and
the router treats it as a validator failure per Mode 1 Step 4.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


class ExtractionError(Exception):
    """Raised when no parseable JSON object can be found in the response."""

    def __init__(self, reason: str, excerpt: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.excerpt = excerpt


@dataclass
class ExtractionResult:
    """Metadata about the extraction, for optional telemetry (Option C upgrade)."""

    payload: dict
    prose_wrap_detected: bool
    leading_prose_chars: int
    trailing_prose_chars: int
    code_fence_detected: bool


_CODE_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*\n(.*?)\n```\s*$",
    re.DOTALL | re.IGNORECASE,
)


def extract_subagent_json(response_text: str) -> dict:
    """
    Extract the first balanced-brace JSON object from a (possibly wrapped)
    subagent response. Returns the parsed dict.

    Raises ExtractionError if no parseable JSON object can be found.
    """
    return extract_subagent_json_with_meta(response_text).payload


def extract_subagent_json_with_meta(response_text: str) -> ExtractionResult:
    """
    Same as extract_subagent_json but returns an ExtractionResult carrying
    telemetry fields. Option C will consume these; Option A ignores them.
    """
    if not isinstance(response_text, str):
        raise ExtractionError(
            f"response is not str, got {type(response_text).__name__}"
        )

    raw = response_text
    stripped = raw.strip()
    if not stripped:
        raise ExtractionError("response is empty or whitespace-only")

    # Strip whole-response markdown code fence if present.
    code_fence_detected = False
    fence_match = _CODE_FENCE_RE.match(stripped)
    if fence_match:
        stripped = fence_match.group(1).strip()
        code_fence_detected = True

    start = stripped.find("{")
    if start < 0:
        raise ExtractionError(
            "no '{' found in response",
            excerpt=stripped[:200],
        )

    end = _find_matching_brace(stripped, start)
    if end < 0:
        raise ExtractionError(
            f"no balanced '}}' found after '{{' at offset {start}",
            excerpt=stripped[start : start + 200],
        )

    block = stripped[start : end + 1]
    try:
        payload = json.loads(block)
    except json.JSONDecodeError as exc:
        raise ExtractionError(
            f"JSON block present but not parseable: {exc.msg} "
            f"at line {exc.lineno} col {exc.colno}",
            excerpt=block[:200],
        ) from exc

    if not isinstance(payload, dict):
        raise ExtractionError(
            f"parsed JSON is not an object, got {type(payload).__name__}",
            excerpt=block[:200],
        )

    leading_prose_chars = start
    # Count non-whitespace chars after the closing brace as trailing-prose length.
    trailing = stripped[end + 1 :]
    trailing_prose_chars = len(trailing.strip())
    prose_wrap_detected = (
        leading_prose_chars > 0
        or trailing_prose_chars > 0
        or code_fence_detected
    )

    return ExtractionResult(
        payload=payload,
        prose_wrap_detected=prose_wrap_detected,
        leading_prose_chars=leading_prose_chars,
        trailing_prose_chars=trailing_prose_chars,
        code_fence_detected=code_fence_detected,
    )


def _find_matching_brace(text: str, open_idx: int) -> int:
    """
    Return the index of the '}' matching the '{' at open_idx.

    Tracks double-quoted string literals so braces inside strings do not
    disturb the depth count. Honors backslash escapes within strings per
    JSON grammar. Returns -1 if no match is found.
    """
    depth = 0
    i = open_idx
    n = len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            if ch == "\\":
                # Skip the escaped character entirely.
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1
