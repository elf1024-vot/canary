"""PWA / Canary v1.23 config-driven strip engine.

Reads a manuscript source file, applies preprocessing rules from pwa_config.json
(per-manuscript override layered over routine-level default), and writes three
output files alongside one another in the temp directory:

  1. <Title> - stripped <YYYY-MM-DD>.txt   - scored prose (Mode A interior kept)
  2. <Title> - marker map <YYYY-MM-DD>.json
  3. <Title> - strip log <YYYY-MM-DD>.json

Header strip rule types supported (per _standards.md v1.23):

  - line_starts_with    (optional and_contains; scope first_line_only|all;
                         consume single_line|until_blank_line|until_next_heading)
  - exact_line          (same scope/consume options)
  - markdown_heading    (required levels:[int]; same options)
  - html_tag            (required tags:[str]; consume tag_block|opener_line|
                         closer_line|opener_and_closer_lines)
  - regex               (required pattern:str; optional flags:["DOTALL", ...])

Paired-delimiter taxonomy (three modes):

  - Mode A: markers stripped, content KEPT in scored prose, span recorded in
            internal_mode_spans (paragraphs reference final stripped file).
  - Mode B: markers AND content stripped from scored prose, span recorded in
            non_character_voice_spans (paragraphs reference PRE-STRIP source).
  - Mode C: markers AND content stripped silently. Nothing recorded.

Disambiguation: array order, first-match-wins.

Per-manuscript override semantics: shallow merge, with array fields concatenated
(manuscript entries appended AFTER routine entries -> manuscript entries have
LOWER priority under first-match-wins).

Undeclared paired-delimiter warning: any [[<TAG>: ... ]] span (or other common
paired-delimiter shape) the script encounters that no declared rule matched is
logged to the strip log as a warning, paragraph-numbered against the source.

Usage:
    python strip_engine.py \\
        --source "C:\\path\\to\\source.txt" \\
        --title "Chapter 1" \\
        --pov "Alice" \\
        [--config "C:\\path\\to\\manuscript\\pwa_config.json"] \\
        [--routine-config "C:\\path\\to\\routine\\pwa_config.json"] \\
        [--out-dir "C:\\path\\to\\temp"] \\
        [--date YYYY-MM-DD]

If --config and --routine-config are omitted, the engine looks for:
  1. <source-folder>/pwa_config.json
  2. <routine-script-dir>/pwa_config.json  (resolved via __file__ at runtime)
If neither exists, the engine exits with a clear error directing the author to
run the first-run setup interview (which lives in the calling routine, not in
this engine).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from copy import deepcopy
from typing import Any


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

# Routine-level default lives next to this script, so the path resolves
# correctly under both Windows (C:\...\PWA\routine\) and any Linux mount.
ROUTINE_CONFIG_DEFAULT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pwa_config.json"
)

# Default output directory: two levels up from the routine dir (i.e., the
# CoWork root's temp/ folder), resolved at runtime so the script works
# regardless of install location.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR_DEFAULT = os.path.join(_SCRIPT_DIR, "..", "..", "temp")

ARRAY_FIELDS = (
    "header_strip_patterns",
    "paired_delimiters",
    "acronym_emphasis_exclusions",
    "weak_adverb_noun_exclusions",
    "ing_starts_proper_noun_exclusions",
)


def _load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_config(
    source_path: str,
    manuscript_config: str | None,
    routine_config: str | None,
) -> tuple[dict[str, Any], list[str]]:
    """Resolve and merge config files.

    Returns (merged_config, paths_loaded). paths_loaded is in load order
    (routine first, manuscript second) so the caller can disclose them.
    """
    routine_path = routine_config or ROUTINE_CONFIG_DEFAULT
    manuscript_path = manuscript_config or os.path.join(
        os.path.dirname(os.path.abspath(source_path)), "pwa_config.json"
    )

    routine_present = os.path.isfile(routine_path)
    manuscript_present = os.path.isfile(manuscript_path)

    if not routine_present and not manuscript_present:
        sys.stderr.write(
            "ERROR: No pwa_config.json found.\n"
            f"  Looked at manuscript path: {manuscript_path}\n"
            f"  Looked at routine path:    {routine_path}\n"
            "Run the first-run setup interview in mode_1_report_only.md "
            "(Step 1b) to create one.\n"
        )
        sys.exit(2)

    paths_loaded: list[str] = []
    merged: dict[str, Any] = {}

    if routine_present:
        merged = deepcopy(_load_json(routine_path))
        paths_loaded.append(routine_path)
    if manuscript_present:
        manuscript_cfg = _load_json(manuscript_path)
        for key, val in manuscript_cfg.items():
            if key in ARRAY_FIELDS:
                base = list(merged.get(key, []))
                base.extend(val)
                merged[key] = base
            else:
                merged[key] = val
        paths_loaded.append(manuscript_path)

    # Defensive defaults so downstream code never KeyErrors on a sparse config.
    for field in ARRAY_FIELDS:
        merged.setdefault(field, [])

    return merged, paths_loaded


# ---------------------------------------------------------------------------
# Header strip rule application
# ---------------------------------------------------------------------------


def _resolve_consume(rule: dict[str, Any], default: str) -> str:
    return rule.get("consume", default)


def _consume_block(
    lines: list[str],
    start_idx: int,
    consume: str,
) -> int:
    """Return the index of the first line AFTER the consumed block.

    consume options:
      single_line          -> consume only the matched line
      until_blank_line     -> matched line + everything until (and including)
                              the next blank line
      until_next_heading   -> matched line + everything until the next line
                              that starts with '#' (markdown heading marker)
                              OR a blank line that precedes such a heading.
                              For safety we use markdown heading as the boundary;
                              if no next heading exists, consume to EOF.
    """
    if consume == "single_line":
        return start_idx + 1
    if consume == "until_blank_line":
        i = start_idx + 1
        while i < len(lines):
            if lines[i].strip() == "":
                return i + 1
            i += 1
        return i
    if consume == "until_next_heading":
        i = start_idx + 1
        while i < len(lines):
            stripped = lines[i].lstrip()
            if stripped.startswith("#"):
                return i
            i += 1
        return i
    # Unknown consume value: be conservative, drop only the matched line.
    return start_idx + 1


def _line_starts_with_match(line: str, rule: dict[str, Any]) -> bool:
    value = rule["value"]
    if not line.startswith(value):
        return False
    needle = rule.get("and_contains")
    if needle and needle not in line:
        return False
    return True


def _exact_line_match(line: str, rule: dict[str, Any]) -> bool:
    return line == rule["value"]


def _markdown_heading_match(line: str, rule: dict[str, Any]) -> bool:
    """Match ATX headings: '#', '##', etc. followed by whitespace."""
    levels = rule.get("levels", [])
    stripped = line.lstrip()
    for level in levels:
        prefix = "#" * level
        # Heading must be the exact level: prefix followed by space (or EOL)
        # and not a longer run of #s (## should not match a level=1 rule).
        if stripped.startswith(prefix):
            after = stripped[len(prefix):]
            if after.startswith("#"):
                continue  # higher level; let its own rule match
            if after == "" or after.startswith(" ") or after.startswith("\t"):
                return True
    return False


_SETEXT_H1_RE = re.compile(r"^=+\s*$")
_SETEXT_H2_RE = re.compile(r"^-+\s*$")


def _setext_heading_match(text_line: str, underline: str | None, rule: dict[str, Any]) -> bool:
    """True if text_line + underline form a setext heading at one of the rule's levels.

    Setext H1: text followed by a line of '=' characters.
    Setext H2: text followed by a line of '-' characters.
    Only fires when the text_line is non-blank (blank lines cannot be headings).
    """
    if not text_line.strip() or underline is None:
        return False
    levels = rule.get("levels", [])
    if 1 in levels and _SETEXT_H1_RE.match(underline):
        return True
    if 2 in levels and _SETEXT_H2_RE.match(underline):
        return True
    return False


def apply_line_oriented_rules(
    text: str,
    rules: list[dict[str, Any]],
) -> tuple[str, dict[str, dict[str, int]]]:
    """Apply line_starts_with, exact_line, markdown_heading rules.

    Returns (new_text, per_rule_stats) where per_rule_stats maps rule label to
    {"matches": int, "lines_consumed": int}.
    """
    lines = text.splitlines(keepends=True)
    # Strip trailing newlines for matching but preserve them for output.
    bare = [ln.rstrip("\n").rstrip("\r") for ln in lines]

    # Track which lines are dropped.
    drop = [False] * len(lines)
    stats: dict[str, dict[str, int]] = {}

    # Track whether a "first_line_only" rule has fired yet (per rule).
    first_line_consumed: set[int] = set()  # rule indices

    i = 0
    while i < len(lines):
        if drop[i]:
            i += 1
            continue
        line = bare[i]
        for r_idx, rule in enumerate(rules):
            rtype = rule["type"]
            if rtype not in ("line_starts_with", "exact_line", "markdown_heading"):
                continue
            scope = rule.get("scope", "all")
            if scope == "first_line_only":
                if i != 0 and r_idx not in first_line_consumed:
                    # first_line_only means the rule may only fire on line 0.
                    # If we're past line 0 and it never fired, it never will.
                    continue
                if i != 0:
                    continue

            matched = False
            setext_matched = False
            if rtype == "line_starts_with":
                matched = _line_starts_with_match(line, rule)
            elif rtype == "exact_line":
                matched = _exact_line_match(line, rule)
            elif rtype == "markdown_heading":
                matched = _markdown_heading_match(line, rule)
                if not matched:
                    next_line = bare[i + 1] if i + 1 < len(bare) else None
                    setext_matched = _setext_heading_match(line, next_line, rule)
                    matched = setext_matched

            if not matched:
                continue

            label = rule.get("label", f"<rule {r_idx}>")
            slot = stats.setdefault(label, {"matches": 0, "lines_consumed": 0})
            consume = _resolve_consume(rule, "single_line")
            end_idx = _consume_block(bare, i, consume)
            # Setext headings span two lines (text + underline); ensure both are consumed.
            if setext_matched:
                end_idx = max(end_idx, i + 2)
            for k in range(i, end_idx):
                if not drop[k]:
                    drop[k] = True
                    slot["lines_consumed"] += 1
            slot["matches"] += 1
            if scope == "first_line_only":
                first_line_consumed.add(r_idx)
            i = end_idx
            break
        else:
            i += 1
            continue

    out = "".join(ln for ln, d in zip(lines, drop) if not d)
    return out, stats


def apply_html_tag_rules(
    text: str,
    rules: list[dict[str, Any]],
) -> tuple[str, dict[str, dict[str, int]]]:
    """Apply html_tag rules. Operates on the raw text (multi-line aware)."""
    stats: dict[str, dict[str, int]] = {}
    for rule in rules:
        if rule.get("type") != "html_tag":
            continue
        label = rule.get("label", f"html_tag:{','.join(rule.get('tags', []))}")
        tags = rule.get("tags", [])
        consume = rule.get("consume", "tag_block")
        slot = stats.setdefault(label, {"matches": 0, "lines_consumed": 0})

        for tag in tags:
            if consume == "tag_block":
                # Strip <tag ...> ... </tag> inclusive, multi-line aware.
                pattern = re.compile(
                    rf"<{re.escape(tag)}\b[^>]*>.*?</{re.escape(tag)}\s*>",
                    re.DOTALL | re.IGNORECASE,
                )
                count = 0

                def _sub(m: re.Match[str]) -> str:
                    nonlocal count
                    count += 1
                    return ""

                text = pattern.sub(_sub, text)
                slot["matches"] += count
            elif consume == "opener_line":
                pattern = re.compile(
                    rf"^.*<{re.escape(tag)}\b[^>]*>.*\n?",
                    re.IGNORECASE | re.MULTILINE,
                )
                matches = pattern.findall(text)
                text = pattern.sub("", text)
                slot["matches"] += len(matches)
                slot["lines_consumed"] += len(matches)
            elif consume == "closer_line":
                pattern = re.compile(
                    rf"^.*</{re.escape(tag)}\s*>.*\n?",
                    re.IGNORECASE | re.MULTILINE,
                )
                matches = pattern.findall(text)
                text = pattern.sub("", text)
                slot["matches"] += len(matches)
                slot["lines_consumed"] += len(matches)
            elif consume == "opener_and_closer_lines":
                opener_pat = re.compile(
                    rf"^.*<{re.escape(tag)}\b[^>]*>.*\n?",
                    re.IGNORECASE | re.MULTILINE,
                )
                closer_pat = re.compile(
                    rf"^.*</{re.escape(tag)}\s*>.*\n?",
                    re.IGNORECASE | re.MULTILINE,
                )
                op_matches = opener_pat.findall(text)
                text = opener_pat.sub("", text)
                cl_matches = closer_pat.findall(text)
                text = closer_pat.sub("", text)
                slot["matches"] += len(op_matches) + len(cl_matches)
                slot["lines_consumed"] += len(op_matches) + len(cl_matches)
    return text, stats


def apply_regex_rules(
    text: str,
    rules: list[dict[str, Any]],
) -> tuple[str, dict[str, dict[str, int]]]:
    """Apply regex rules. flags: list of strings -> re.<FLAG>."""
    stats: dict[str, dict[str, int]] = {}
    for rule in rules:
        if rule.get("type") != "regex":
            continue
        label = rule.get("label", "<regex>")
        slot = stats.setdefault(label, {"matches": 0, "lines_consumed": 0})
        flag_value = re.MULTILINE
        for flag_name in rule.get("flags", []):
            flag_value |= getattr(re, flag_name.upper(), 0)
        pat = re.compile(rule["pattern"], flag_value)
        count = 0

        def _sub(m: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return ""

        text = pat.sub(_sub, text)
        slot["matches"] += count
    return text, stats


# ---------------------------------------------------------------------------
# Paired-delimiter handling (three-mode taxonomy)
# ---------------------------------------------------------------------------


def _paragraph_index(text: str, char_offset: int) -> int:
    """1-indexed paragraph number for the paragraph containing char_offset.

    Paragraphs are split by one or more blank lines.
    """
    if char_offset < 0:
        return 1
    # Count paragraph boundaries (\n\s*\n) before char_offset.
    para = 1
    for m in re.finditer(r"\n\s*\n", text):
        if m.end() > char_offset:
            break
        para += 1
    return para


def apply_paired_delimiters(
    pre_strip_text: str,
    text: str,
    pairs: list[dict[str, Any]],
) -> tuple[
    str,
    list[dict[str, Any]],   # internal_mode_spans (paragraphs vs FINAL)
    list[dict[str, Any]],   # non_character_voice_spans (paragraphs vs SOURCE)
    list[dict[str, Any]],   # silent_strip_records (Mode C, internal use)
    dict[str, dict[str, int]],  # per-rule stats
]:
    """Walk paired delimiters in array order, first-match-wins.

    Operates on `text` (the post-line/regex strip text) for actual stripping.
    Uses `pre_strip_text` only to compute Mode B paragraph numbers against
    the original source.

    Mode A: marker pair removed; interior text reinserted at the same offset.
            Span recorded with paragraph numbers against the FINAL stripped
            text (computed in a second pass after all stripping completes —
            this function records pending interior text + a stable signature).
    Mode B: marker pair AND interior removed. Span recorded with paragraph
            numbers against pre_strip_text, since Mode B content is gone
            from the output.
    Mode C: marker pair AND interior removed silently.

    Returns text and three span lists. internal_mode_spans entries carry
    {"text": interior, "word_count": int, "_pending_paragraphs": True} —
    the caller resolves paragraph numbers after final assembly.
    """
    stats: dict[str, dict[str, int]] = {}
    internal_mode_spans: list[dict[str, Any]] = []
    non_character_voice_spans: list[dict[str, Any]] = []
    silent_strip_records: list[dict[str, Any]] = []

    # We process pair rules in declaration order. For each rule we walk the
    # text from left to right, find non-overlapping opener/closer pairs, and
    # mutate `text` accordingly. After each rule completes, the next rule
    # operates on the updated text. This implements first-match-wins:
    # earlier rules consume their spans before later rules see them.
    for pair in pairs:
        opener = pair["opener"]
        closer = pair["closer"]
        mode = pair["mode"].upper()
        label = pair.get("label", f"{opener}...{closer}")
        slot = stats.setdefault(
            f"{label} (Mode {mode})",
            {"matches": 0, "interior_words_kept": 0, "interior_words_excluded": 0},
        )

        new_parts: list[str] = []
        cursor = 0
        while True:
            o_idx = text.find(opener, cursor)
            if o_idx < 0:
                new_parts.append(text[cursor:])
                break
            c_idx = text.find(closer, o_idx + len(opener))
            if c_idx < 0:
                # Opener with no closer -> leave text alone, advance cursor
                # past the opener so the next iteration doesn't loop forever.
                new_parts.append(text[cursor:o_idx + len(opener)])
                cursor = o_idx + len(opener)
                continue

            interior = text[o_idx + len(opener): c_idx].strip()
            interior_word_count = len(interior.split())

            # Append everything BEFORE the opener.
            new_parts.append(text[cursor:o_idx])

            if mode == "A":
                # Keep interior in scored prose.
                new_parts.append(interior)
                internal_mode_spans.append({
                    "label": label,
                    "text": interior,
                    "word_count": interior_word_count,
                    "_pending_paragraphs": True,
                })
                slot["interior_words_kept"] += interior_word_count
            elif mode == "B":
                # Drop interior from scored prose; record source paragraph.
                # Paragraph number is computed against pre_strip_text using
                # the verbatim opener text as a signature.
                source_offset = pre_strip_text.find(opener)
                source_para = _paragraph_index(pre_strip_text, source_offset) if source_offset >= 0 else None
                non_character_voice_spans.append({
                    "register_label": pair.get("register_label", label),
                    "register_description": pair.get("register_description", ""),
                    "source_paragraph_start": source_para,
                    "source_paragraph_end": source_para,
                    "word_count": interior_word_count,
                    "text": interior,
                    "note": "stripped from scored corpus per Mode B",
                })
                slot["interior_words_excluded"] += interior_word_count
            elif mode == "C":
                silent_strip_records.append({
                    "label": label,
                    "word_count": interior_word_count,
                })
                slot["interior_words_excluded"] += interior_word_count
            else:
                # Unknown mode: leave the span alone and warn via stats.
                new_parts.append(text[o_idx:c_idx + len(closer)])
                cursor = c_idx + len(closer)
                continue

            slot["matches"] += 1
            cursor = c_idx + len(closer)

        text = "".join(new_parts)

    return text, internal_mode_spans, non_character_voice_spans, silent_strip_records, stats


def resolve_internal_paragraphs(
    final_text: str,
    spans: list[dict[str, Any]],
) -> None:
    """Mutate spans in place, replacing _pending_paragraphs with real numbers.

    Locates each interior text in final_text by stable signature and computes
    paragraph_start / paragraph_end (1-indexed, blank-line separated).
    """
    # Pre-split final text into paragraphs with their character spans.
    paragraphs: list[tuple[int, int, int]] = []  # (idx, start, end)
    cursor = 0
    p_idx = 1
    for m in re.finditer(r"\n\s*\n", final_text):
        end = m.start()
        paragraphs.append((p_idx, cursor, end))
        cursor = m.end()
        p_idx += 1
    if cursor <= len(final_text):
        paragraphs.append((p_idx, cursor, len(final_text)))

    def offset_to_paragraph(offset: int) -> int | None:
        for idx, start, end in paragraphs:
            if start <= offset <= end:
                return idx
        return paragraphs[-1][0] if paragraphs else None

    # Track repeated occurrences so two identical spans get distinct hits.
    search_cursors: dict[str, int] = {}

    for span in spans:
        if not span.pop("_pending_paragraphs", False):
            continue
        interior = span["text"]
        # Use first 60 chars as a stable signature (or the full string if shorter).
        needle = interior[:60] if len(interior) >= 10 else interior
        start_at = search_cursors.get(needle, 0)
        loc = final_text.find(needle, start_at)
        if loc < 0:
            span["paragraph_start"] = None
            span["paragraph_end"] = None
            span["resolution_note"] = (
                "interior text not located in final stripped file "
                "(whitespace or punctuation drift)"
            )
            continue
        search_cursors[needle] = loc + len(needle)
        end_loc = loc + len(interior)
        span["paragraph_start"] = offset_to_paragraph(loc)
        span["paragraph_end"] = offset_to_paragraph(end_loc)


# ---------------------------------------------------------------------------
# Undeclared paired-delimiter detection
# ---------------------------------------------------------------------------

# Common paired-delimiter shapes the warning system checks for.
# Matches [[<TAG>: ... ]] where TAG is uppercase letters/spaces.
UNDECLARED_PATTERNS = [
    re.compile(r"\[\[[A-Z][A-Z\s]*[A-Z](?::|\s)[^\]]{0,500}\]\]", re.DOTALL),
    re.compile(r"<<[A-Z][A-Z\s]*[A-Z]>>.*?</[A-Z][A-Z\s]*[A-Z]>>", re.DOTALL),
]


def detect_undeclared_paired_delimiters(
    pre_strip_text: str,
    declared_pairs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return warnings for [[<TAG>:...]] (or similar) spans not declared."""
    warnings: list[dict[str, Any]] = []
    declared_openers = [p["opener"] for p in declared_pairs]

    for pat in UNDECLARED_PATTERNS:
        for m in pat.finditer(pre_strip_text):
            span_text = m.group(0)
            # Skip if any declared opener appears at the start of this span.
            if any(span_text.startswith(op) for op in declared_openers):
                continue
            excerpt = span_text[:80].replace("\n", " ")
            para = _paragraph_index(pre_strip_text, m.start())
            warnings.append({
                "warning": "undeclared paired-delimiter-shaped content",
                "paragraph": para,
                "excerpt": excerpt,
                "guidance": (
                    "Classify this opener/closer in pwa_config.json "
                    "paired_delimiters as Mode A (kept + attributed), "
                    "Mode B (diagnostic-only, not scored), or Mode C "
                    "(silent strip), or accept as scored prose."
                ),
            })
    return warnings


# ---------------------------------------------------------------------------
# Top-level pipeline
# ---------------------------------------------------------------------------


def normalize_blank_lines(text: str) -> str:
    """Collapse 3+ consecutive newlines to 2; trim trailing whitespace."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def strip_chapter(
    source_path: str,
    title: str,
    pov: str | None,
    config: dict[str, Any],
    config_paths_loaded: list[str],
    out_dir: str,
    date: str,
) -> dict[str, str]:
    with open(source_path, encoding="utf-8") as f:
        pre_strip_text = f.read()

    # 1. Apply line-oriented rules (line_starts_with, exact_line, markdown_heading).
    text_after_lines, line_stats = apply_line_oriented_rules(
        pre_strip_text, config["header_strip_patterns"]
    )

    # 2. Apply html_tag rules.
    text_after_html, html_stats = apply_html_tag_rules(
        text_after_lines, config["header_strip_patterns"]
    )

    # 3. Apply regex rules.
    text_after_regex, regex_stats = apply_regex_rules(
        text_after_html, config["header_strip_patterns"]
    )

    # 4. Apply paired-delimiter rules (three modes).
    text_after_pairs, internal_spans, non_char_spans, silent_records, pair_stats = \
        apply_paired_delimiters(
            pre_strip_text, text_after_regex, config["paired_delimiters"]
        )

    # 5. Normalize blank lines.
    final_text = normalize_blank_lines(text_after_pairs)

    # 6. Resolve internal_mode_spans paragraph numbers against final_text.
    resolve_internal_paragraphs(final_text, internal_spans)

    # 7. Detect undeclared paired-delimiter spans against PRE-STRIP source.
    undeclared_warnings = detect_undeclared_paired_delimiters(
        pre_strip_text, config["paired_delimiters"]
    )

    # ------------------------------------------------------------------
    # Write outputs.
    # ------------------------------------------------------------------
    os.makedirs(out_dir, exist_ok=True)
    stripped_path = os.path.join(out_dir, f"{title} - stripped {date}.txt")
    marker_map_path = os.path.join(out_dir, f"{title} - marker map {date}.json")
    strip_log_path = os.path.join(out_dir, f"{title} - strip log {date}.json")

    with open(stripped_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    marker_map = {
        "pov_character": pov,
        "source_chapter": source_path,
        "stripped_file": stripped_path,
        "paired_delimiter_declarations": config["paired_delimiters"],
        "internal_mode_spans": internal_spans,
        "non_character_voice_spans": non_char_spans,
    }
    with open(marker_map_path, "w", encoding="utf-8") as f:
        json.dump(marker_map, f, indent=2, ensure_ascii=False)

    # Build strip log.
    rules_applied: list[dict[str, Any]] = []
    rules_seen_labels: set[str] = set()
    for stats_block in (line_stats, html_stats, regex_stats):
        for label, info in stats_block.items():
            if info["matches"] > 0:
                entry: dict[str, Any] = {"label": label, "matches": info["matches"]}
                if info.get("lines_consumed"):
                    entry["lines_consumed"] = info["lines_consumed"]
                rules_applied.append(entry)
                rules_seen_labels.add(label)

    for label, info in pair_stats.items():
        if info["matches"] > 0:
            entry = {"label": label, "matches": info["matches"]}
            if info.get("interior_words_kept"):
                entry["interior_words_kept"] = info["interior_words_kept"]
            if info.get("interior_words_excluded"):
                entry["interior_words_excluded"] = info["interior_words_excluded"]
            rules_applied.append(entry)
            rules_seen_labels.add(label)

    # Zero-match rules: anything declared in config but not in rules_seen_labels.
    declared_labels: list[str] = []
    for rule in config["header_strip_patterns"]:
        declared_labels.append(rule.get("label", f"<{rule.get('type', '?')}>"))
    for pair in config["paired_delimiters"]:
        mode = pair.get("mode", "?").upper()
        declared_labels.append(f"{pair.get('label', '<pair>')} (Mode {mode})")
    rules_zero_matches = [lbl for lbl in declared_labels if lbl not in rules_seen_labels]

    total_active = len(declared_labels)
    summary = (
        f"{len(rules_applied)} of {total_active} active rules processed; "
        f"{len(rules_zero_matches)} rules with zero matches."
    )

    strip_log = {
        "schema_version": "1.0",
        "engine_version": "v1.23",
        "source_chapter": source_path,
        "stripped_file": stripped_path,
        "config_paths_loaded": config_paths_loaded,
        "rules_applied": rules_applied,
        "rules_zero_matches": rules_zero_matches,
        "summary": summary,
        "undeclared_paired_delimiter_warnings": undeclared_warnings,
        "silent_strip_record_count": len(silent_records),
        "word_counts": {
            "source": len(pre_strip_text.split()),
            "stripped": len(final_text.split()),
            "delta": len(pre_strip_text.split()) - len(final_text.split()),
        },
    }
    with open(strip_log_path, "w", encoding="utf-8") as f:
        json.dump(strip_log, f, indent=2, ensure_ascii=False)

    return {
        "stripped_file": stripped_path,
        "marker_map": marker_map_path,
        "strip_log": strip_log_path,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="PWA / Canary v1.23 strip engine.")
    p.add_argument("--source", required=True, help="Path to manuscript source file.")
    p.add_argument("--title", required=True, help="Output filename stem (e.g., 'Chapter 1').")
    p.add_argument("--pov", default=None, help="POV character name (required when any Mode A pair is declared).")
    p.add_argument("--config", default=None, help="Per-manuscript pwa_config.json path (optional override).")
    p.add_argument("--routine-config", default=None, help="Routine-level pwa_config.json path (optional override).")
    p.add_argument("--out-dir", default=OUT_DIR_DEFAULT, help="Output directory (default: two levels up from routine dir, i.e. the project temp/ folder).")
    p.add_argument("--date", default=_dt.date.today().isoformat(), help="Date stamp YYYY-MM-DD.")
    args = p.parse_args(argv)

    config, paths_loaded = load_config(args.source, args.config, args.routine_config)

    has_mode_a = any(pair.get("mode", "").upper() == "A" for pair in config["paired_delimiters"])
    if has_mode_a and not args.pov:
        sys.stderr.write(
            "ERROR: Config declares at least one Mode A paired delimiter "
            "but --pov was not supplied. Mode A requires a POV character "
            "for attribution. Pass --pov '<character name>'.\n"
        )
        return 2

    outputs = strip_chapter(
        source_path=args.source,
        title=args.title,
        pov=args.pov,
        config=config,
        config_paths_loaded=paths_loaded,
        out_dir=args.out_dir,
        date=args.date,
    )
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
