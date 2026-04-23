# Mode 3 - User Configuration + Auto-fix

Run the PWA report, show the user where their document deviates from standard thresholds, ask them to clarify which deviations matter and which categories they want auto-fixed, then apply every configured auto-fix to a copy of the document.

This is the "make it match my vision" mode.

The original document is never modified.

---

## Instructions to Claude

### Step 1: Load Standards

Read `{SKILL_BASE}\references\_standards.md` in full. Every threshold, heuristic, auto-fix tier, and genre profile comes from there.

### Step 1a: Establish Genre

If invoked via Canary, the genre was already selected and passed in; use it. If invoked standalone, ask the user which genre profile to grade against (see `_standards.md` for the 11 named options plus Custom). The genre determines the baseline thresholds that the deviation analysis in Step 4 is measured against.

If the user selects Custom, follow the Custom Genre Construction flow in `_standards.md` (describe the work, pick closest genres, set the blend, compute weighted thresholds, confirm).

### Step 2: Check for an Existing User Config

Look for `{{DOC_FOLDER}}\user_config.json`. If it exists and is valid, remember its contents but do not apply it yet. Ask the user:

> "I found an existing configuration from [date]. Do you want to reuse it, start fresh, or adjust it for this document?"

Via AskUserQuestion. Three options: Reuse, Adjust, Start fresh.

If no config file exists, proceed to Step 3 with defaults from `_standards.md`.

### Step 3: Run Mode 1

Execute the Mode 1 workflow in full: produce a complete PWA-style report and save it to `{{DOC_FOLDER}}\[Title] - PWA Review [YYYY-MM-DD].md`. The report is a required deliverable.

### Step 4: Identify Deviations

From the Mode 1 output, build a deviation list: every category where the document's metric missed the **genre-adjusted threshold** (or the Universal threshold for universal categories).

For each deviation, capture:
- Category name
- Current value
- Genre-adjusted threshold (name which genre)
- Universal threshold (for reference)
- Direction (higher/lower/in-range)
- Auto-fix tier (safe, prompt, manual) from the Standards Reference

Sort deviations by tier (safe first, then prompt, then manual) and within tier by magnitude of deviation.

When presenting deviations to the user in Step 5, show the genre-adjusted threshold as the primary target. Only reference the Universal threshold if the user explicitly asks.

### Step 5: Present and Clarify

Show the user the deviation list in a compact table, then walk through three clarification questions. Do not walk through every single deviation; the user already said line-by-line is tedious. The three questions are:

**Question A - Thresholds to override.**

"Here are the categories where your document differs from the standard threshold. For each, the standard is the PWA default. Are there any you want to change? For example, if you prefer a slightly higher glue index because of your voice, you can raise it. Leave the rest at defaults."

Show the deviation table. Accept overrides as user input. Validate each override against the metric's direction.

**Question B - Categories to auto-fix.**

"Of the categories where the document is below target, which do you want me to auto-fix? The safe-tier categories can be applied mechanically. The prompt-tier categories are usually correct but can change voice - I'll apply them if you say yes. The manual-tier categories require judgment; I won't auto-fix those but I'll flag them for you."

Show a short table:

| Category | Tier | Current | Target | Auto-fix? |
|----------|------|---------|--------|-----------|
| Grammar | safe | 99% | 100% | [default: yes] |
| Spelling | safe | 99% | 100% | [default: yes] |
| Style | prompt | 85% | 80% or higher | [default: no, already in range] |
| Weak Adverbs | prompt | 11.2 | < 10.0 | [default: yes] |
| Dialogue Tags with Adverbs | prompt | 19% | < 12% | [default: yes] |
| Glue Index | prompt | 41% | < 40% | [default: ask] |
| Long Repeated Phrases | manual | 355 | < 3 | [manual - flag only] |
| Passive Voice | manual | 1.7 | < 25.0 | [already in range] |
...

Use AskUserQuestion to collect yes/no per prompt-tier row that is currently deviating.

**Question C - Exclusions.**

"Any specific phrases, words, or patterns you want me to leave alone because they are intentional voice? For example, if 'the kind of' is a deliberate stylistic choice, tell me and I'll skip it."

Accept a list of phrases or patterns to exclude from auto-fix.

### Step 6: Save the User Config

Write the resulting configuration to `{{DOC_FOLDER}}\user_config.json` with this shape:

```json
{
  "version": "1.2",
  "updated": "YYYY-MM-DD",
  "genre": {
    "selected": "F5",
    "name": "Horror / Gothic",
    "custom": null
  },
  "preprocessing": {
    "format": "txt",
    "strip": [
      "First line if it starts with 'Chapter'",
      "Lines starting with 'Part ' or 'Cast:'",
      "Lines starting with 'WHAT HAPPENED:'",
      "Lines containing [[...]] bracketed tags"
    ],
    "include_despite_defaults": [],
    "notes": "VoT plain-text chapter format."
  },
  "thresholds": {
    "glue_index": 43,
    "weak_adverbs": 11.0
  },
  "autofix": {
    "grammar": true,
    "spelling": true,
    "style": false,
    "weak_adverbs": true,
    "dialogue_tags_with_adverbs": true,
    "glue_index": false,
    "voice_consistency": false,
    "performance_tag_rate": false,
    "quote_consistency": true,
    "acronym_consistency": true
  },
  "exclusions": {
    "phrases": ["the kind of", "began to"],
    "words": [],
    "patterns": []
  },
  "notes": "Optional: free-text notes about this author's voice."
}
```

The `preprocessing` block mirrors the decisions made in the router's Step 2a. `format` is the detected file extension. `strip` is the final exclusion list. `include_despite_defaults` captures any format default the author explicitly overrode to KEEP scoring. `notes` is free text.

For a Custom genre selection, set `genre.selected` to `"C"` and populate the `genre.custom` object:

```json
"genre": {
  "selected": "C",
  "name": "Custom: Western SciFi (Firefly-style)",
  "custom": {
    "description": "Space western fan fiction; tone blends frontier grit with ensemble crew banter.",
    "blend": [
      { "profile": "F2", "weight": 0.5 },
      { "profile": "F4", "weight": 0.5 }
    ],
    "thresholds": {
      "sentence_length": "9.0 to 16.0",
      "sentence_variety": ">= 5.5",
      "passive_voice": "< 20.0",
      "readability_grade": "<= 9",
      "complex_paragraphs": "< 16%",
      "glue_index": "< 40%",
      "weak_adverbs": "< 10.0",
      "slow_pacing": "< 30%",
      "dialogue_tags": "< 52%",
      "voice_consistency": ">= 50%",
      "performance_tag_rate": "< 18%",
      "dialogue_tags_with_adverbs": "< 12%",
      "emotion_tells": "< 21%",
      "style_score": ">= 81%",
      "very_long_sentences": "< 3%",
      "conjunction_starts": "< 9%"
    }
  }
}
```

Only include the `thresholds` block for user-specific overrides ON TOP OF the genre defaults. The `genre.custom.thresholds` block holds the computed custom-profile values; `thresholds` holds any further overrides the user specified.

Only include autofix entries for categories the user answered. Preserve exclusions verbatim.

### Step 7: Create the Working Copy

Copy the original document to:

```
{{DOC_FOLDER}}\[Title] - auto-fixed copy [YYYY-MM-DD].[ext]
```

If the original is a PDF, convert to `.docx` for the working copy and note this in the change log.

The word "copy" appears in every working filename by design. It is a durable visual cue that survives every file manager and operating system. Never drop it.

**Do not open or write to the original file path.** See the pre-flight path check in Step 7a.

### Step 7a: Pre-flight Path Check

Before creating the working copy, verify:

1. The computed working-copy path is not the same as the original path (byte-for-byte comparison after normalization).
2. The working-copy path is under `{{DOC_FOLDER}}\` or another location the user has explicitly named as the output directory.
3. The working-copy filename contains the word "copy" (case-insensitive).

If any of these checks fail, hard-stop. Do not write anything. Report the failure to the user and ask for instructions. Do not attempt to auto-correct the path; the user must resolve the ambiguity.

### Step 8: Apply Auto-fixes

Walk through every issue from Mode 1 detection that:

1. Belongs to a category marked `autofix: true` in the user config, AND
2. Is not in the exclusions list (phrases, words, or patterns).

**Grammar and Spelling source:** the Grammar and Spelling issues are consumed directly from the subagent JSON blob produced during Mode 1 Step 3b (see `_standards.md` "Grammar and Spelling Pass"). Do NOT re-run grammar/spelling detection; use the `issues` arrays and their `tier` fields as the source of truth. Safe-tier items auto-apply; prompt-tier items are surfaced to the user via AskUserQuestion before application. Unknown-words-for-review are copied to the change log under Flagged for Manual Review without modification.

Apply in order of appearance. For each change, record in the change log:

- Category
- Exact original text
- Exact replacement text
- Sentence-of-context
- Reason / pattern matched

Safe-tier changes follow the rules from Mode 2. Prompt-tier changes follow the pattern rules in the Standards Reference "Detection Heuristics - Style" section and the related category sections.

For manual-tier categories, do not modify anything. Instead, add an annotation to the change log under "Flagged for Manual Review".

### Step 9: Write the Change Log

Save to:

```
{{DOC_FOLDER}}\[Title] - Auto-fix Log [YYYY-MM-DD].md
```

Structure:

```
# [Title] - Auto-fix Log

**Original file (unchanged):** [original path]
**Working copy (edited):** [working copy path]

---

Report: [report path]
Config: [user config path]
Date: [YYYY-MM-DD]

## Configuration Summary

- Thresholds overridden: [list any]
- Categories auto-fixed: [list]
- Categories flagged for manual review only: [list]
- Exclusions respected: [list]

## Summary of Changes

- Total auto-applied: [N]
- Flagged for manual review: [M]
- Respected exclusions: [K]

## Auto-applied Changes by Category

### Grammar ([N] changes)

| # | Context | Before | After | Reason |
|---|---------|--------|-------|--------|
...

### Spelling ([N] changes)
...

### Weak Adverbs ([N] changes)
...

[etc. - one subsection per auto-fixed category]

## Flagged for Manual Review

### Long Repeated Phrases ([M] items)

[List the top offenders with location hints.]

### [Other manual-tier category] ([M] items)
...

## Respected Exclusions

| Pattern | Matches skipped |
|---------|-----------------|
| the kind of | 145 |
| began to | 48 |
...
```

### Step 10: Deliver

Return computer:// links to:

1. The PWA report (Mode 1 output)
2. The auto-fixed working copy
3. The auto-fix change log
4. The user config file (newly saved or updated)

Headline verdict: "Applied [N] fixes across [K] categories. Flagged [M] items for manual review. Config saved for reuse."

Do not restate the report or change log in chat. The files are the deliverables.

---

## File Safety

1. The original input document is NEVER modified.
2. All output filenames include the ISO date and are distinct from the original.
3. The user config is written to `{{DOC_FOLDER}}\user_config.json`. If the user opts to reuse or adjust an existing config, preserve any fields they did not touch.
4. Exclusions are authoritative. A phrase in the exclusions list is never auto-fixed regardless of category settings.

---

## Inputs Expected

- Path to the document (required)
- Genre selection (required; ask or inherit from router)
- Optional: title override
- Optional: "reuse config" to skip the clarification step and apply the existing user_config.json as-is

If "reuse config" is passed and no config exists, fall back to the full Step 2 flow.
