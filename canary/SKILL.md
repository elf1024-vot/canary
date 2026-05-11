---
name: canary
description: "Writing evaluation routine for manuscripts. Runs a ProWritingAid-style report (Mode 1), grammar/spelling correction (Mode 2), or full user-configured auto-fix (Mode 3). Interview-once design: collects genre, mode, and preprocessing rules on first run and saves them to pwa_config.json alongside the manuscript for reuse on all subsequent runs. Use this skill whenever the user wants to evaluate, score, or improve a manuscript, chapter, or written document - especially when they say \"run canary\", \"run PWA\", \"evaluate my chapter\", \"score this\", \"fix my grammar\", \"check my writing\", or \"proofread this.\""
---

# Canary

**Skill name:** canary
**Routine version:** v1.25.1
**Skill version:** v1.3 (generic authoring + standards builder)

Entry point for the Canary writing-evaluation routine. Runs an interview once per manuscript, saves answers to a config file alongside the manuscript, and reuses that file on all subsequent runs. Dispatches to Mode 1, 2, or 3 based on the saved or newly collected mode selection.

---

## Skill base directory

Your session header shows:
> Base directory for this skill: <path>

That path is `{SKILL_BASE}` throughout this file and all bundled mode prompts. Substitute it wherever you see `{SKILL_BASE}` in any file path or bash command.

All bundled resources:
- `{SKILL_BASE}\references\` - mode prompts, standards reference, subagent prompts, default config
- `{SKILL_BASE}\scripts\` - Python strip engine, tokenizer, and router/validator package

---

## Safety guarantee

State this to the user verbatim before any other output:

> **Your original file is never modified. All edits are written to a clearly named copy. The original path is treated as read-only for the entire run.**

Do not skip this line. Repeat it if the user selects Mode 2 or Mode 3.

---

## Step 1: Collect document path

If the user did not provide a document path in their invocation message, ask for one now. Accept any file format (.txt, .md, .docx, .html). Record the resolved absolute path as `{{DOCUMENT_PATH}}` and derive the document folder as `{{DOC_FOLDER}}`.

---

## Step 2: Check for saved config

Look for `{{DOC_FOLDER}}\pwa_config.json`.

**If the file exists and contains both a `genre` field and a `mode` field:**

Load the file. Read `genre`, `mode`, and any preprocessing rules it contains. Present a one-line summary to the user:

> Saved config found: genre = [genre label], mode = [mode label]. Run with these settings?

Use AskUserQuestion with three options:
1. Yes, run with saved settings
2. Change genre or mode only (keep preprocessing rules)
3. Re-run the full interview (overwrite all settings)

If the user picks **1**, skip to Step 5 (Execute).
If the user picks **2**, skip to Step 3b (Genre and Mode only).
If the user picks **3**, continue to Step 3a.

**If the file does not exist or is missing `genre` or `mode`:**

Continue to Step 3a (full interview).

---

## Step 3a: Pre-processing interview (first run or full re-interview)

Read `{SKILL_BASE}\references\_standards.md` so the strip-rule defaults for the detected format are in context.

Detect the file format from `{{DOCUMENT_PATH}}`'s extension.

**For `.txt` files:**

Ask the user what to exclude from scoring. Plain text has no structural signal, so the routine cannot guess. Suggest common patterns as examples based on what the user's file appears to contain (detect from a brief Read of the first 30 lines). Do not present AskUserQuestion for plain text - use a free-text prompt:

> I see this is a .txt file. I need to know what to strip before scoring. Based on the first few lines, I can see [brief observation]. Common patterns to consider: chapter title lines, YAML front matter or preamble blocks, heading lines, or tagged production markers like [[THOUGHT: ...]] or <!--production notes-->.
>
> What should I strip? Name specific patterns, or say "strip nothing."

**For `.md` files:**

Use AskUserQuestion with four options:
1. Use suggested markdown defaults (headings, YAML front-matter, code blocks, horizontal rules)
2. Use defaults with additions (I will name what else to strip)
3. Use defaults minus some items (I will name what to keep)
4. Strip nothing, score every line

If the user picks 2 or 3, collect the additions or exclusions as free text.

**For `.docx`, `.html`, or other formats:**

Ask what structural elements to exclude, presenting format-appropriate suggestions from `_standards.md`.

Confirm the final strip list back to the user before proceeding. Record it as `{{STRIP_LIST}}`.

---

## Step 3b: Genre and Mode interview

### Genre selection

If `pwa_config.json` exists and already has a `genre` field, offer it as the default:

> Current genre: [label]. Keep this or change?

Use AskUserQuestion with two options: keep current / change. If the user keeps it, record the existing genre and skip the genre question.

If no saved genre or user wants to change, use AskUserQuestion with these 12 options:

**Fiction**
1. Literary / Upmarket Fiction
2. Thriller / Suspense / Crime
3. Romance
4. Science Fiction / Fantasy
5. Horror / Gothic

**Non-fiction**
6. Journalism / Reportage
7. Memoir / Personal Essay
8. Business / Self-help
9. Academic / Scholarly
10. Popular Science / Narrative Non-fiction

**Other**
11. Universal / No genre (use flat defaults)
12. Custom / Describe it

If the user picks **12 (Custom)**, follow the Custom Genre Construction flow in `_standards.md`:
1. Ask the user to describe the work in a sentence or two.
2. Identify the one or two closest named genres.
3. Ask the user to confirm the blend.
4. Compute weighted-average thresholds.
5. Show the computed profile and ask for confirmation.

Record the genre selection (or custom profile) as `{{GENRE}}`.

### Mode selection

If `pwa_config.json` exists and already has a `mode` field (and the user picked option 2 in Step 2), offer it as the default:

> Current mode: [mode label]. Keep this or change?

Use AskUserQuestion with two options: keep current / change.

If no saved mode or user wants to change, use AskUserQuestion with three options:

1. **Report only** - Score the document, no changes.
2. **Grammar and spelling fix** - Fix typos and grammar errors in a copy; leave everything else alone.
3. **User configuration + auto-fix** - Run the report, show deviations, configure preferences, apply all safe fixes.

Record the selection as `{{MODE}}` (1, 2, or 3).

---

## Step 4: Save config

Write `{{DOC_FOLDER}}\pwa_config.json`.

If the file already exists, load it first (to preserve all existing strip rules). Then set or overwrite these fields:

```json
{
  "genre": "{{GENRE label string}}",
  "mode": {{MODE integer}},
  "header_strip_patterns": [...existing or new rules from Step 3a...],
  "paired_delimiters": [...existing or carried forward...],
  "acronym_emphasis_exclusions": [...existing or []...],
  "weak_adverb_noun_exclusions": [...existing or default list...],
  "ing_starts_proper_noun_exclusions": [...existing or []...]
}
```

If this is a first-run, seed the preprocessing fields from the skill-bundled default (`{SKILL_BASE}\references\pwa_config.json`) merged with the strip list collected in Step 3a.

Keep a single rolling backup as `pwa_config.json.bak` before each overwrite.

Tell the user: "Config saved to [path]. Future runs will reuse genre and mode unless you ask to change them."

---

## Step 4b: Offer the standards builder (first run only)

Run this step only on a first-run interview (Step 3 was executed, not skipped).

Check whether `{{DOC_FOLDER}}\standards.md` already exists. If it does, skip this step.

If it does not exist, ask:

> "One more optional step: do you want to set up project-specific craft standards? This lets you define banned phrases, required elements, threshold adjustments, and voice rules that Canary will enforce on every run. Takes 5-15 minutes. You can always do it later by saying 'run the standards builder'."

Use AskUserQuestion with two options:
1. Yes, set up project standards now
2. Skip for now (use the bundled defaults)

If the user picks **1**, run the standards builder from `{SKILL_BASE}\references\standards_builder.md`. After it completes, proceed to Step 5.

If the user picks **2**, proceed to Step 5 immediately.

---

## Step 5: Execute

State the safety guarantee again if Mode is 2 or 3.

**POV character**: if any paired delimiter in the active config has `mode: "A"` and `attributed_to_pov: true`, ask the user for the POV character name before dispatching. Record as `{{POV}}`.

Dispatch to the appropriate mode prompt, passing:
- `{{DOCUMENT_PATH}}`
- `{{GENRE}}`
- `{{MODE}}`
- `{{POV}}` (if applicable)
- The active config path: `{{DOC_FOLDER}}\pwa_config.json`

Mode dispatch:
- Mode 1 -> Load and execute `{SKILL_BASE}\references\mode_1_report_only.md`
- Mode 2 -> Load and execute `{SKILL_BASE}\references\mode_2_grammar_spelling_fix.md`
- Mode 3 -> Load and execute `{SKILL_BASE}\references\mode_3_user_config_autofix.md`

---

## Step 6: Return deliverables

After the mode prompt completes, return links to all produced files and a one-line verdict. Do not restate the full content of any file in chat.

For Mode 1: link to the report file (.md, and .pdf if the user requested it).
For Mode 2: link to the report, the fixed copy, and the change log.
For Mode 3: link to the report, the fixed copy, the change log, and the updated config.

---

## Config schema reference

`pwa_config.json` fields the skill reads and writes:

| Field | Type | Purpose |
|---|---|---|
| `genre` | string | Genre label from the 12 options or custom blend description. Read at Step 2 to offer reuse. |
| `mode` | integer | 1, 2, or 3. Read at Step 2 to offer reuse. |
| `header_strip_patterns` | array | Preprocessing rules for headers and structural lines. See `_standards.md` for schema. |
| `paired_delimiters` | array | Mode A/B/C paired-delimiter rules. See `_standards.md` for schema. |
| `acronym_emphasis_exclusions` | array | Tokens excluded from the Acronym Consistency detector. |
| `weak_adverb_noun_exclusions` | array | Tokens excluded from the Weak Adverbs detector. |
| `ing_starts_proper_noun_exclusions` | array | Proper nouns excluded from the -ing Starts detector. |

Do not write any other fields to `pwa_config.json`. The strip engine and tokenizer ignore unknown fields but it is bad hygiene to accumulate them.

---

## File safety rules

1. `{{DOCUMENT_PATH}}` is never opened for writing under any mode.
2. Mode 2 and Mode 3 write fixes to a copy named `[Title] - fixed [YYYY-MM-DD].txt` (or `.md`/`.docx` matching the original extension).
3. Reports, working copies, change logs, and all intermediate files land in `{{DOC_FOLDER}}\` unless the user specifies otherwise.
4. If a write would overwrite an existing file from today, append `-v2`, `-v3`, etc.
5. The `pwa_config.json` backup (`pwa_config.json.bak`) is a single rolling backup - one file, overwritten each save.

---

## Version history

- **v1.2 (2026-04-23)** - First-live-run hardening. Bumped routine version to v1.25.1 for the schema-shape mechanical-normalization escape hatch in `mode_1_report_only.md` Step 1c (also applies to Steps 2a, 3b, 3c when second-attempt failures are pure schema-shape with valid content). Bumped `grammar_spelling.md` to v1.4 (paragraph-definition hardening with worked example). Bumped `character_dialogue.md` to v1.2 (modes-shape WRONG/RIGHT callout). Bumped `summary_beat_sheet.md` to v1.2 (word-count procedure + structural_observations array constraint). These four edits address the concrete failure modes observed in the first live run: paragraph=line-number drift, modes-as-array drift, chapter_word_count off by ~16%, and structural_observations as single string.
- **v1.1 (2026-04-23)** - Portable skill release. All hardcoded author-specific paths replaced with `{SKILL_BASE}` (skill base directory) and `{{DOC_FOLDER}}` (manuscript folder). Output paths moved to `{{DOC_FOLDER}}\`. Default config seed changed from hardcoded path to `{SKILL_BASE}\references\pwa_config.json`. Mode dispatch paths updated to `{SKILL_BASE}\references\`. Bundled: `_standards.md`, three mode prompts, five subagent prompts, default `pwa_config.json`, `strip_engine.py`, `tokenizer.py`, full `router/` package.
- **v1.0 (2026-04-23)** - Initial portable skill release. Replaced `00_run.md` as the canonical entry point for PWA Mode 1/2/3 dispatch. Interview-once / config-reuse pattern saves genre, mode, and preprocessing rules to `pwa_config.json` next to the manuscript. POV character collected only when the active config requires it.
