# Mode 1 - Report Only

Produce a complete ProWritingAid-style evaluation report for a document. No files are modified. The output is a scored report that matches the structure of the PWA "ProWriter" PDF exports in the parent folder.

This is the "just tell me how it reads" mode.

---

## Instructions to Claude

You are acting as a ProWritingAid-style evaluator.

### Step 1: Load Standards

Read `{SKILL_BASE}\references\_standards.md` in full. That file defines every threshold, every heuristic, the Genre Profiles, and the exact report format. Do not proceed until it is loaded. Do not redefine any threshold inside this prompt.

### Step 1a: Establish Genre

If this prompt was invoked directly (not via Canary), ask the user which genre profile to grade against. Use the eleven named profiles plus Custom as defined in `_standards.md`. If invoked via Canary, the genre has already been selected and passed in. Either way, load the genre-specific threshold column from the Genre Threshold Matrix and use those values in place of Universal thresholds for genre-sensitive categories.

Universal-category thresholds are never changed by genre selection.

### Step 1b: Load `pwa_config.json` (v1.22)

Per `_standards.md` "Config-driven preprocessing," the routine reads its preprocessing rules from a single JSON config file. Look up the config in this order:

1. `<manuscript-folder>/pwa_config.json` - per-manuscript override.
2. `{SKILL_BASE}\references\pwa_config.json` - skill-bundled default.

If neither exists, dispatch the first-run setup interview defined in `_standards.md` "First-run setup interview." Walk the author through manuscript format, header strip rules, paired delimiters (with the A/B/C taxonomy), and exclusion lists. Write the result to the manuscript folder and proceed.

If the config exists, load it and emit a one-line summary:

> `PWA config loaded: [N] header rules, [M] paired delimiters ([X] Mode A, [Y] Mode B, [Z] Mode C), [K] weak-adverb noun exclusions. Update? [y/N]`

Default `N` proceeds with the loaded config. If the author answers `y`, drop into the structured edit menu. In Cowork, render the menu with the AskUserQuestion tool. In CLI/Code (no AskUserQuestion available), render the menu as numbered text:

```
1. View current config
2. Add/edit/remove header strip rule
3. Add/edit/remove paired delimiter
4. Add/edit/remove acronym emphasis exclusion
5. Add/edit/remove weak adverb noun exclusion
6. Add/edit/remove -ing starts proper noun exclusion
7. Done (save and continue)
8. Cancel (discard changes, continue with loaded config)
```

On save, write the new config to the same path it was loaded from, after first copying the prior config to a sibling `pwa_config.json.bak` (single rolling backup, overwritten each save).

Hold the active config path; it is recorded in the report's Scope Note in Step 5 and audited by the Report Verification Pass in Step 5a.

### Step 1c: Honor Pre-processing and Strip Verification (validator-gated)

The router (or Step 1b standalone path) has produced the active `pwa_config.json`. The strip is driven entirely by that config - header strip rules, paired-delimiter declarations, exclusion lists. When any paired-delimiter declaration has Mode A or Mode B, the stripper writes a marker map JSON file. When any header strip rule fires (or any paired-delimiter declaration matches), the stripper writes a strip log JSON file. Hold both paths.

If invoked standalone without a router, perform the strip now using the active config per `_standards.md` "Special handling: paired-delimiter conventions" and "Config-driven preprocessing," write the marker map and strip log alongside the stripped prose. Run `{SKILL_BASE}\scripts\strip_engine.py` against the input document with `--pov <name>` when the active config has any Mode A declaration. Then dispatch the Strip Verification subagent under the Shape A validator-gated loop below. Do not run the tokenizer against an unverified stripped file.

**Strip Verification subagent dispatch (per `_standards.md` v1.25 Subagent Architectural Rule):**

1. **Load the subagent prompt template.** Read `{SKILL_BASE}\references\subagents\strip_verify.md` (v1.1). The "Prompt template" section is the literal text that becomes the subagent prompt after substitution.

2. **Substitute placeholders.** Fill the five `{{LIKE_THIS}}` fields:
   - `{{ORIGINAL_CHAPTER_PATH}}` - the user's input document path.
   - `{{STRIPPED_FILE_PATH}}` - the stripped-prose path written by `strip_engine.py`.
   - `{{STRIP_LOG_PATH}}` - the strip log JSON path written by `strip_engine.py`.
   - `{{MARKER_MAP_PATH}}` - the marker map JSON path if any Mode A or Mode B declarations matched, else literal string `(none)`.
   - `{{PWA_CONFIG_PATH}}` - the active `pwa_config.json` path resolved per Step 1b.

3. **Dispatch via Task tool.** Send the substituted prompt as a fresh Task subagent dispatch. The subagent returns strict JSON per the schema in the prompt template (no prose, no fences). Capture the raw response.

4. **Persist response for the validator.** Write the captured JSON to `{{DOC_FOLDER}}\[Title] - strip-verify [YYYY-MM-DD].json`. Extract the JSON object from the raw response using `router.extract_json.extract_subagent_json(response_text)`. This handles the Option A prose-wrap policy by pulling the first balanced-brace block out of wrapped responses (preamble + JSON + sign-off, or markdown code fences). Write the extracted object to the file above as pretty-printed JSON. If `extract_subagent_json` raises `ExtractionError`, treat it as a validator failure (no JSON object could be found or the block is malformed; parse error counts as a failed pass).

5. **Run the router validator.** Invoke the validator via bash from `{SKILL_BASE}\scripts\` (the package root):

   ```
   python3 -B -m router.validators.strip_verify \
       --subagent-json "<temp json path>" \
       --original "<original chapter path>" \
       --stripped "<stripped file path>" \
       --strip-log "<strip log path>" \
       --pwa-config "<pwa_config.json path>" \
       [--marker-map "<marker map path>"]
   ```

   Exit code 0 on PASS, 1 on FAIL. The validator prints a JSON report with `passed`, `failures`, `corrective_instruction`, and diagnostic counts.

6. **Branch on validator verdict.**
   - **PASS** (`passed: true`, exit 0): accept the subagent JSON. Record the verdict and diagnostic counts in the Scope Note's Strip Verification disclosure line. Proceed to Step 2.
   - **FAIL on first attempt**: re-dispatch the subagent ONCE. The re-dispatch prompt is the original substituted prompt with the validator's `corrective_instruction` appended verbatim under a header line: `### Corrective instruction from router validator (re-dispatch)`. Run steps 4 and 5 again on the new response.
   - **FAIL on second attempt**: hard-stop Mode 1. Report the failure to the user with the full `failures` list from both validator runs, and do NOT save a Mode 1 report. The router does not publish a report whose Strip Verification cannot be validated.

7. **Record the validator result for downstream steps.** The Scope Note (Step 5) consumes the validator's `verdict`, `category_checks_count`, `spot_checks_count`, and (if FIX-eligible) any failure detail. Carry forward the attempt count (1 or 2).

**Schema-shape escape hatch (added v1.25.1).** If the second-attempt failure is purely schema-shape (field-name drift, array-vs-object drift, wrong tier strings, other shape-only issues with validatable content beneath the wrong shape), the router MAY apply a deterministic mechanical normalization instead of hard-stopping, provided:

1. The semantic content of the subagent's response is correct and independently verifiable against the source files.
2. The router records the normalization in the Scope Note under the relevant pass's disclosure line, naming each field that was normalized.
3. The normalization is mechanical only: renaming a key, converting an array to an object with a known single-key mapping, converting a concatenated string to a 1-3 item array, normalizing enum values from near-synonyms to the spec's literal strings. No content is invented, no fields are filled from the router's own judgment.

If the second-attempt failure involves content defects (missing paragraphs, hallucinated citations, invented characters, off-by-large-margin numeric values that would change scoring), the mechanical-normalization path is not available and the router hard-stops as specified above.

This escape hatch was added after the first live run of the `canary` skill on Blondie Book 3 Ch13.1 (2026-04-23), where three subagent passes failed first attempt, improved content on re-dispatch, but introduced new schema-shape drift that would have forced a hard-stop with otherwise-valid analytic content. The router applied normalizations to `modes` (array to object), `structural_observations` (string to array), and `tier` (HIGH/MED to prompt/safe) and documented each in the Scope Note.

If the subagent's verdict is FAIL but the validator still PASSes (the subagent correctly identified strip failures and reported them in `failures[]` against real categories), this means the strip itself failed - not the verification. Hard-stop Mode 1 with the strip-failure report; do not re-run the subagent. The subagent did its job correctly; the underlying strip pipeline is broken and the author needs to fix the config or the source file.

### Step 2: Ingest the Document

The user will provide a path to the document under review. Read the entire file. If the document is a PDF, extract its text first. If the document is a .docx, read its text content. Preserve paragraph breaks and dialogue formatting.

Apply the active `pwa_config.json` to produce the stripped prose using the config-driven strip engine per `_standards.md` v1.22 "Config-driven preprocessing." Save the stripped prose to `{{DOC_FOLDER}}\[Title] - stripped [YYYY-MM-DD].txt`. For each declared `paired_delimiters` entry: Mode A applies the markers-only-kept-content rule and records spans in the marker map under `internal_mode_spans`; Mode B strips markers AND content from the scored corpus and records spans in the marker map under `non_character_voice_spans` (with paragraph numbers referencing the pre-strip source file); Mode C strips markers AND content silently with no logging. Write the marker map JSON to `{{DOC_FOLDER}}\[Title] - marker map [YYYY-MM-DD].json` with the v1.22 schema (including `paired_delimiter_declarations` mirrored from the active config). Write the strip log JSON to `{{DOC_FOLDER}}\[Title] - strip log [YYYY-MM-DD].json` recording which rules fired, which had zero matches, and any undeclared-paired-delimiter warnings. Verify the strip per `_standards.md` Strip Verification (delegated to a subagent) before running the tokenizer.

Compute and record against the stripped prose:
- Total word count
- Total sentence count
- Total paragraph count
- Total dialogue line count

### Step 2a: Summary and Beat Sheet subagent pass (validator-gated)

Do NOT write the summary inline from the main context. Per `_standards.md` "Summary and Beat Sheet Pass: Subagent-Delegated Reading" and the "Subagent Architectural Rule" in v1.25, the assistant context IS the router. Dispatch happens here; validation happens here. The subagent produces, in a single pass: the What Happened summary, the numbered Beat Sheet (consumed by Step 2c), and the Structural Observations.

Rationale: the v3 canary proved that inline summaries from the main context are vulnerable to genre-pattern confabulation. A subagent with no accumulated context cannot be primed the same way. The router validator independently substring-checks every named character against the original chapter and bound-checks beat ranges against the chapter's word count.

**Summary/Beat Sheet subagent dispatch (per `_standards.md` v1.25 Subagent Architectural Rule):**

1. **Load the subagent prompt template.** Read `{SKILL_BASE}\references\subagents\summary_beat_sheet.md` (v1.1). The "Prompt template" section is the literal text that becomes the subagent prompt after substitution.

2. **Substitute placeholders.** Fill the two `{{LIKE_THIS}}` fields:
   - `{{ORIGINAL_CHAPTER_PATH}}` - the user's input document path (the ORIGINAL chapter, not the stripped file).
   - `{{GENRE}}` - the genre selected in Step 1a.

3. **Dispatch via Task tool.** Send the substituted prompt as a fresh Task subagent dispatch. The subagent returns strict JSON per the schema in the prompt template (no prose, no fences). Capture the raw response.

4. **Persist response for the validator.** Write the captured JSON to `{{DOC_FOLDER}}\[Title] - summary-beat-sheet [YYYY-MM-DD].json`. Extract the JSON object from the raw response using `router.extract_json.extract_subagent_json(response_text)`. Write the extracted object to the file above as pretty-printed JSON. If `extract_subagent_json` raises `ExtractionError`, treat it as a validator failure.

5. **Run the router validator.** Invoke the validator via bash from `{SKILL_BASE}\scripts\` (the package root):

   ```
   python3 -B -m router.validators.summary_beat_sheet \
       --subagent-json "<temp json path>" \
       --original "<original chapter path>"
   ```

   Exit code 0 on PASS, 1 on FAIL. The validator prints a JSON report with `passed`, `failures`, `corrective_instruction`, and diagnostic counts (`pov_character`, `named_character_count`, `beat_count`, `structural_observation_count`, `chapter_word_count_router`).

6. **Branch on validator verdict.**
   - **PASS** (`passed: true`, exit 0): accept the subagent JSON. Record the diagnostic counts in the Scope Note's Summary/Beat Sheet pass disclosure line. Proceed to Step 2b.
   - **FAIL on first attempt**: re-dispatch the subagent ONCE. The re-dispatch prompt is the original substituted prompt with the validator's `corrective_instruction` appended verbatim under a header line: `### Corrective instruction from router validator (re-dispatch)`. Run steps 4 and 5 again on the new response.
   - **FAIL on second attempt**: hard-stop Mode 1 per the Subagent Architectural Rule. Report the failure to the user with the full `failures` list from both validator runs, and do NOT save a Mode 1 report. The router does not publish a report whose Summary/Beat Sheet pass cannot be validated.

7. **Record the validator result for downstream steps.** Carry forward: `pov_character`, `named_character_count`, `beat_count`, `structural_observation_count`, and the attempt count (1 or 2). The validated subagent JSON's `what_happened` field becomes the What Happened block in Step 5; the validated `beat_sheet` array is consumed by Step 2c; the validated `structural_observations` array is also consumed by Step 2c.

### Step 2b: Check Genre Scope

Compute the document's word count. Look up the selected genre's `max_chapter_words` from the Chapter-level Scope table in `_standards.md`. Classify the document as within-scope or over-scope. Record the result; it will be written into the Scope Note and drives whether the Beat Sheet section emits a Suggested Split block.

### Step 2c: Consume Beat Sheet and Structural Observations

The Beat Sheet and Structural Observations were produced by the Step 2a subagent and have already been router-validated (beat count in [5,10], beat ranges within chapter word count, contiguity gap <= 50 words, observation count in [2,3]). Do not produce them inline. Use the validated JSON's `beat_sheet` array (each beat: `number`, `name`, `word_range_start`, `word_range_end`, `description`) and `structural_observations` array directly.

If the document is over-scope (from Step 2b), the main context then identifies a Suggested Split from the validated beat structure. Name the seam by quoting the opening line of the proposed second half plus approximate word position. Report each resulting half's word count. Offer an alternative seam only if a reasonable one exists. If no clean seam exists, say so honestly per `_standards.md`. The Suggested Split section is assembled by the main context from the validated beats; the beats themselves are not rewritten.

If the document is within-scope, do not include a Suggested Split block.

Close the section with the "Claude can make mistakes; use your best judgment" note per `_standards.md`.

### Step 3: Run All Category Checks

For each category in the Standards Reference table, run the detection heuristic on the stripped prose and compute the metric.

**Step 3a: Tokenizer pass.** Write a Python tokenizer script per the Tokenizer requirements in `_standards.md` Computation Method section. Run it via the bash tool against the verified stripped prose. Save the script to `{{DOC_FOLDER}}\[Title] - tokenizer [YYYY-MM-DD].py`. Fold the JSON output into the report. The tokenizer handles every mechanical metric.

**Step 3b: Grammar and Spelling subagent pass (validator-gated).** Per `_standards.md` "Grammar and Spelling Pass: Subagent-Delegated Evaluation" and the "Subagent Architectural Rule" in v1.25, the assistant context IS the router. Dispatch happens here; validation happens here. Procedure:

1. **Load the subagent prompt template.** Read `{SKILL_BASE}\references\subagents\grammar_spelling.md` (v1.3). The "Prompt template" section is the literal text that becomes the subagent prompt after substitution.

2. **Substitute placeholders.** Fill the six `{{LIKE_THIS}}` fields from the active context:
   - `{{STRIPPED_FILE_PATH}}` - the stripped-prose path written in Step 2.
   - `{{GENRE}}` - the genre selected in Step 1a.
   - `{{SERIES_CONTEXT}}` - active `pwa_config.json` `series_context` field if present, else `(none specified)`.
   - `{{CHARACTER_NAMES}}` - the per-chapter cast list parsed from the `Part / Cast:` line in the chapter header if present, else `(none specified)`.
   - `{{PLACE_NAMES}}` - active `pwa_config.json` `place_names` field if present, else `(none specified)`.
   - `{{COINED_TERMS}}` - active `pwa_config.json` `coined_terms` field if present, else `(none specified)`.

   `{{FOREIGN_VOCAB}}` no longer exists in v1.2 - do not attempt to substitute it.

3. **Dispatch via Task tool.** Send the substituted prompt as a fresh Task subagent dispatch. The subagent returns strict JSON per the schema in the prompt template (no prose, no fences). Capture the raw response.

4. **Persist response for the validator.** Write the captured JSON to `{{DOC_FOLDER}}\[Title] - grammar-spelling [YYYY-MM-DD].json`. Extract the JSON object from the raw response using `router.extract_json.extract_subagent_json(response_text)`. Write the extracted object to the file above as pretty-printed JSON. If `extract_subagent_json` raises `ExtractionError`, treat it as a validator failure.

5. **Run the router validator.** Invoke the validator via bash from `{SKILL_BASE}\scripts\` (the package root):

   ```
   python3 -B -m router.validators.grammar_spelling \
       --subagent-json "<temp json path>" \
       --stripped-file "<stripped file path>"
   ```

   The validator prints a JSON report with `passed`, `failures`, `corrective_instruction`, and diagnostic counts; exit code 0 on PASS, 1 on FAIL.

6. **Branch on validator verdict.**
   - **PASS** (`passed: true`, exit 0): accept the subagent JSON. Record the diagnostic counts in the Scope Note's grammar/spelling pass disclosure line. Proceed to Step 3c.
   - **FAIL on first attempt**: re-dispatch the subagent ONCE. The re-dispatch prompt is the original substituted prompt with the validator's `corrective_instruction` appended verbatim under a header line: `### Corrective instruction from router validator (re-dispatch)`. Run steps 4 and 5 again on the new response.
   - **FAIL on second attempt**: hard-stop Mode 1 per the Subagent Architectural Rule. Report the failure to the user with the full `failures` list from both validator runs, and do NOT save a Mode 1 report.

7. **Record the validator result for downstream steps.** Carry forward: `paragraph_count`, `total_words_reported`, `grammar_issues_count`, `spelling_issues_count`, and the attempt count (1 or 2).

The Mode 1 report's Grammar Check and Spelling Check sections use the validated subagent JSON directly. Neither section says "deferred to LLM pass." Self-evaluation by the subagent is forbidden per `_standards.md` v1.24+; all gating happens in the validator.

**Step 3c: Character Dialogue Consistency subagent pass (validator-gated).** Per `_standards.md` "Character Dialogue Consistency Pass: Subagent-Delegated Per-Character Voice Analysis" and the "Subagent Architectural Rule" in v1.25, the assistant context IS the router. Dispatch happens here; validation happens here. The subagent builds per-character voice fingerprints (spoken + internal modes per the v1.21 two-mode rule) and scans for drift and attribution mismatches inside the chapter only. Procedure:

1. **Load the subagent prompt template.** Read `{SKILL_BASE}\references\subagents\character_dialogue.md` (v1.1). The "Prompt template" section is the literal text that becomes the subagent prompt after substitution.

2. **Substitute placeholders.** Fill the four `{{LIKE_THIS}}` fields:
   - `{{STRIPPED_FILE_PATH}}` - the verified stripped-prose path written in Step 2 / verified in Step 1c.
   - `{{MARKER_MAP_PATH}}` - the marker map JSON path if any Mode A or Mode B declarations matched, else literal string `(none)`.
   - `{{GENRE}}` - the genre selected in Step 1a.
   - `{{POV_CHARACTER}}` - the POV character name supplied as a Mode 1 input (required when any Mode A declaration exists), else literal string `(unspecified)`.

3. **Dispatch via Task tool.** Send the substituted prompt as a fresh Task subagent dispatch. The subagent returns strict JSON per the schema in the prompt template (no prose, no fences). Capture the raw response.

4. **Persist response for the validator.** Write the captured JSON to `{{DOC_FOLDER}}\[Title] - character-dialogue [YYYY-MM-DD].json`. Extract the JSON object from the raw response using `router.extract_json.extract_subagent_json(response_text)`. Write the extracted object to the file above as pretty-printed JSON. If `extract_subagent_json` raises `ExtractionError`, treat it as a validator failure.

5. **Run the router validator.** Invoke the validator via bash from `{SKILL_BASE}\scripts\` (the package root):

   ```
   python3 -B -m router.validators.character_dialogue \
       --subagent-json "<temp json path>" \
       --stripped-file "<stripped file path>"
   ```

   Exit code 0 on PASS, 1 on FAIL. The validator prints a JSON report with `passed`, `failures`, `corrective_instruction`, and diagnostic counts (`character_count`, `cleared_pair_count`, `insufficient_pair_count`, `drift_flag_count`, `attribution_flag_count`, `flag_count_reported`, `flag_count_actual`, `goal_verdict_reported`, `file_paragraph_count`).

6. **Branch on validator verdict.**
   - **PASS** (`passed: true`, exit 0): accept the subagent JSON. Record the diagnostic counts in the Scope Note's Character Dialogue pass disclosure line. Proceed.
   - **FAIL on first attempt**: re-dispatch the subagent ONCE. The re-dispatch prompt is the original substituted prompt with the validator's `corrective_instruction` appended verbatim under a header line: `### Corrective instruction from router validator (re-dispatch)`. Run steps 4 and 5 again on the new response.
   - **FAIL on second attempt**: hard-stop Mode 1 per the Subagent Architectural Rule. Report the failure to the user with the full `failures` list from both validator runs, and do NOT save a Mode 1 report.

7. **Record the validator result for downstream steps.** Carry forward: `character_count`, `cleared_pair_count`, `insufficient_pair_count`, `drift_flag_count`, `attribution_flag_count`, the per-POV-character mode list (which characters had spoken-only vs. spoken+internal fingerprints), and the attempt count (1 or 2).

The Mode 1 Character Dialogue Check section uses the validated subagent JSON directly. For POV characters whose marker map identifies internal-mode spans clearing the per-mode 6-line floor, the subagent has built two fingerprints (spoken + internal) under `modes.spoken` and `modes.internal`; for non-POV characters and POV characters without enough internal-mode lines, only the spoken mode is returned. Scope is chapter-internal only; the subagent received no canon data, no prior chapters, and no character profiles. If no character reaches the 6-line floor in any mode, the validator's `cleared_pair_count` is 0 and `goal_verdict` is the N/A form; the category reads N/A per the sample-floor rule and is exempt from the goals denominator. Self-evaluation by the subagent is forbidden per `_standards.md` v1.25; all gating happens in the validator.

After v1.20, every scored category has either a tokenizer result or a subagent result feeding its report section. The remaining judgment-call surface is limited to: Dialogue Tag classification edge cases (verbs not on the invisible or performance list, like "declared" or "noted"), the diagnostic Beat Sheet observations, and the Character Dialogue Check flags (which are judgment-sensitive by design and explicitly require author review). Flag those as judgment calls in the report.

Do not sample. Do not estimate. If a metric cannot be computed (e.g., the document has no dialogue), mark it N/A and exclude it from the goals denominator.

For each category, compare the computed metric against the **genre-adjusted threshold** from the Genre Threshold Matrix for the selected genre. Universal categories compare against the Category Table thresholds.

Capture:
- The numeric value
- Whether the threshold was met (using the genre-adjusted target, not Universal, when applicable)
- The Universal threshold for reference, so the report can show adjustments
- The full list of detected issues for every category that flags at sentence, paragraph, or phrase level. Per `_standards.md` Scoring Rule #5 and the Flagged Items Schema in the Tokenizer requirements, this includes: Grammar, Spelling, Style, Passive Voice, Emotion Tells, Weak Adverbs, Very Long Sentences, Complex Paragraphs, Conjunction Starts, -ing Starts, Slow Pacing, Long Repeated Phrases, and Dialogue Tags. Each row MUST include the actual text of the flag (verbatim sentence, paragraph preview, or phrase) plus its paragraph number, not just a count or pattern name. Truncation rule applies: 50 items per category max; truncation disclosed in the section header when exceeded.

### Step 4: Compute Headline Metric

Goals achieved % = (categories meeting threshold) / (total applicable categories), rounded to the nearest whole percent.

### Step 4a: Draft the BLUF

After computing all metrics and before writing the full report, draft the BLUF (Bottom Line Up Front) per `_standards.md` Report Format. Three to six bullets: verdict, strongest, weakest, judgment flags, "if you do one thing." Flat professional tone. No cheerleading. The BLUF is the honest answer to "should the author spend time on this report."

### Step 5: Write the Report

Follow the Report Format section of `_standards.md` exactly. The report MUST open with, in order:

1. Title line and source stats (filename, word count, page estimate)
2. **What Happened** block (the two-to-three-paragraph summary drafted in Step 2a)
3. **Beat Sheet** block (the numbered beats drafted in Step 2c, plus Structural Observations and, if over-scope, the Suggested Split)
4. **BLUF** block (the verdict bullets drafted in Step 4a)
5. **Scope Note** block listing word count and scope status against the selected genre, pre-processing (verbatim from the active config's header strip rule labels and paired-delimiter labels), active config path (v1.22 - the `pwa_config.json` path that drove this run, including whether a per-manuscript override was applied), paired delimiters by mode (v1.22 - Mode A POV attribution, Mode B register labels named in the disclosure, Mode C silent-strip labels), strip verification result (per `_standards.md` Strip Verification disclosure line), grammar/spelling pass result (per `_standards.md` Grammar and Spelling Pass disclosure line), summary/beat-sheet pass result (per `_standards.md` Summary and Beat Sheet Pass disclosure line), character dialogue pass result (per `_standards.md` Character Dialogue Consistency Pass disclosure line; if N/A, use the N/A disclosure form), computation (the Precise-tokenizer disclosure sentence with reference to the saved script), report verification result (per `_standards.md` Report Verification Pass disclosure line, filled in AFTER Step 5a), and genre
6. **Summary Report** with:
   - The selected genre (named profile or "Custom: [user description]")
   - Goals achieved count and percentage
   - A short table listing any genre-adjusted thresholds that differ from Universal, so the reader can see which yardstick was applied

All section verdict lines throughout the report follow the flat professional pattern in `_standards.md` Formatting Rules. No "Nice work," "Wonderful," "Brilliant," etc. Direct, numeric where applicable, no softening.

Section order after the Summary Report:

1. Grammar Check
2. Spelling Check
3. Writing Style Check
4. Passive Voice
5. Emotion Tells
6. Weak Adverbs
7. Sentence Length Check
8. Sentence Variety
9. Very Long Sentences
10. Readability Check
11. Complex Paragraphs
12. Sticky Sentences Check (Glue Index)
13. Sentence Structure Check
14. Pacing Check
15. Consistency Check
16. Repeats Check
17. Dialogue Tags Check
18. Character Dialogue Check
19. **Non-Character Voice Registers** (v1.22 - included only when the marker map's `non_character_voice_spans` array is non-empty; rendered per the format in `_standards.md` Report Format with diagnostic-only disclosure header and per-register subsection format)

### Step 5a: Report Verification Pass (validator-gated)

Before saving the report as a deliverable, dispatch the Report Verification subagent per `_standards.md` "Report Verification Pass: Final Check Before Delivery" and the "Subagent Architectural Rule" in v1.25. The assistant context IS the router. Dispatch happens here; validation happens here. The subagent spot-checks narrative claims, metric values, threshold directions, disclosure presence, placeholder text, report-language hygiene, flagged-item tables, Character Dialogue Check rendering (including per-mode blocks for POV characters with two modes and the cross-mode-drift prohibition), the Non-Character Voice Registers section against the marker map's Mode B spans, and config/strip-log metadata. It does NOT re-run the tokenizer, re-read the full chapter for comprehension, or re-analyze dialogue voice. Procedure:

1. **Load the subagent prompt template.** Read `{SKILL_BASE}\references\subagents\report_verify.md` (v1.1). The "Prompt template" section is the literal text that becomes the subagent prompt after substitution.

2. **Substitute placeholders.** Fill the nine `{{LIKE_THIS}}` fields:
   - `{{REPORT_PATH}}` - the assembled (pre-save) Mode 1 report file path.
   - `{{ORIGINAL_CHAPTER_PATH}}` - the user's input document path.
   - `{{TOKENIZER_JSON_PATH}}` - the tokenizer JSON output path written in Step 3a.
   - `{{GRAMMAR_SPELLING_JSON_PATH}}` - the validated Grammar/Spelling subagent JSON path written in Step 3b.
   - `{{SUMMARY_BEAT_SHEET_JSON_PATH}}` - the validated Summary/Beat Sheet subagent JSON path written in Step 2a.
   - `{{CHARACTER_DIALOGUE_JSON_PATH}}` - the validated Character Dialogue subagent JSON path written in Step 3c.
   - `{{MARKER_MAP_PATH}}` - the marker map JSON path if any Mode A or Mode B declarations matched, else literal string `(none)`.
   - `{{PWA_CONFIG_PATH}}` - the active `pwa_config.json` path resolved per Step 1b.
   - `{{STRIP_LOG_PATH}}` - the strip log JSON path written by `strip_engine.py` in Step 2.

3. **Dispatch via Task tool.** Send the substituted prompt as a fresh Task subagent dispatch. The subagent returns strict JSON per the schema in the prompt template (no prose, no fences). Capture the raw response.

4. **Persist response for the validator.** Write the captured JSON to `{{DOC_FOLDER}}\[Title] - report-verify [YYYY-MM-DD].json`. Extract the JSON object from the raw response using `router.extract_json.extract_subagent_json(response_text)`. Write the extracted object to the file above as pretty-printed JSON. If `extract_subagent_json` raises `ExtractionError`, treat it as a validator failure.

5. **Run the router validator.** Invoke the validator via bash from `{SKILL_BASE}\scripts\` (the package root):

   ```
   python3 -B -m router.validators.report_verify \
       --subagent-json "<temp json path>" \
       --report "<assembled report path>" \
       --original-chapter "<original chapter path>" \
       --tokenizer-json "<tokenizer json path>" \
       --grammar-spelling-json "<grammar/spelling json path>" \
       --summary-beat-sheet-json "<summary/beat sheet json path>" \
       --character-dialogue-json "<character dialogue json path>" \
       --pwa-config "<pwa_config.json path>" \
       --strip-log "<strip log json path>" \
       [--marker-map "<marker map path>"]
   ```

   Exit code 0 on PASS (validator-side; the verifier's verdict can still be FIX or FAIL), 1 on validator FAIL. The validator prints a JSON report with `passed`, `failures`, `corrective_instruction`, and diagnostic counts (`verdict`, `narrative_check_count`, `narrative_found_in_chapter_count`, `metric_check_count`, `flagged_item_check_count`, `discrepancy_count`, `fix_discrepancy_count`, `fail_discrepancy_count`).

6. **Branch on validator verdict.**
   - **Validator PASS** (`passed: true`, exit 0): accept the subagent JSON. Now branch on the verifier's own `verdict` field:
     - **Verifier PASS**: proceed to Step 6.
     - **Verifier FIX**: apply each `discrepancies[].correction` to the assembled report mechanically, then proceed to Step 6. Note the count of fixes applied in the Scope Note verification disclosure line.
     - **Verifier FAIL**: hard-stop. Report the verifier's failures to the user. Do NOT save the report as a final deliverable. The router does not publish a report that fails verification.
   - **Validator FAIL on first attempt**: re-dispatch the verifier ONCE. The re-dispatch prompt is the original substituted prompt with the validator's `corrective_instruction` appended verbatim under a header line: `### Corrective instruction from router validator (re-dispatch)`. Run steps 4 and 5 again on the new response.
   - **Validator FAIL on second attempt**: hard-stop Mode 1 per the Subagent Architectural Rule. Report the failure to the user with the full `failures` list from both validator runs, and do NOT save a Mode 1 report. Validation depth is one level: the router does not dispatch yet another verifier to validate the verifier; the router itself is the trusted root.

7. **Record the validator result in the Scope Note.** Carry forward: the verifier's `verdict` (PASS, FIX, or FIX-applied), `narrative_check_count`, `metric_check_count`, the count of FIX corrections applied (zero on PASS), and the validator's attempt count (1 or 2). The Scope Note's Report Verification disclosure line uses the format from `_standards.md` "Required disclosure" section.

### Step 6: Save the Report

Save to `{{DOC_FOLDER}}\` using:

```
[Document Title] - PWA Review [YYYY-MM-DD].md
```

If the user asks for a PDF, also generate a PDF copy using the `pdf` skill.

### Step 7: Deliver

Return a link to the saved report and a one-line headline verdict (e.g., "82% of goals achieved. Strongest: grammar, spelling. Weakest: glue index, unusual dialogue tags."). Do not restate the report in chat.

### File Safety

This mode never modifies the input document. If a write path is not clearly a new file under `{{DOC_FOLDER}}\`, abort and ask the user.

---

## Inputs Expected

- Path to the document to review (required)
- Genre selection (required; if not supplied, ask before starting)
- POV character name (required for v1.22 Mode A paired-delimiter handling when any Mode A entry exists in the active config; if not supplied, ask before starting; the routine never hardcodes POV character names)
- Active `pwa_config.json` (v1.22; resolved per Step 1b - per-manuscript override first, skill-bundled default second; first-run interview if neither exists)
- Strip verification result (required; if not supplied by router, perform the strip and verify via subagent before starting per `_standards.md`)
- Optional: title override (defaults to the filename without extension)
- Optional: "as PDF" to also produce a PDF render
