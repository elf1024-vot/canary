# Mode 2 - Grammar and Spelling Correction Only

Produce a full PWA-style report, then apply **safe** grammar and spelling fixes to a copy of the document. Flag ambiguous cases (homophones, proper nouns, foreign words, coined terms) for user review rather than auto-applying them.

The original document is never modified.

---

## Instructions to Claude

### Step 1: Load Standards

Load using the same two-layer approach as Mode 1 Step 1: bundled `{SKILL_BASE}\references\_standards.md` always, then project `{{DOC_FOLDER}}\standards.md` (or `STANDARDS_PATH`) as an override layer if present. Read both in full, paying attention to:

- The Grammar and Spelling detection heuristics
- The Auto-fix Tiers section, specifically the note about homophones and proper nouns being `prompt`-tier within the otherwise `safe` Grammar and Spelling categories
- The Genre Profiles section

### Step 1a: Genre Context

Grammar and Spelling are both **universal** categories - their thresholds (100% each) do not shift by genre. However, the embedded Mode 1 report DOES honor the genre selection for all genre-sensitive categories. Accept the genre selection from the router (or ask the user directly if this prompt is invoked standalone) and pass it through to Mode 1. The fix behavior in this mode is not affected by genre.

### Step 2: Run Mode 1

Execute the Mode 1 workflow in full: produce a complete PWA-style report and save it to `{{DOC_FOLDER}}\[Title] - PWA Review [YYYY-MM-DD].md`.

Do not skip the report. The report is part of Mode 2's deliverables.

### Step 3: Create the Working Copy

Copy the original document to:

```
{{DOC_FOLDER}}\[Title] - edited copy [YYYY-MM-DD].[ext]
```

Where `[ext]` matches the original file's extension. If the original is a PDF, convert to `.docx` for the working copy since PDF is not easily editable; note the conversion in the change log.

The word "copy" appears in every working filename by design. It is a durable visual cue that survives every file manager and operating system. Never drop it.

**Do not open or write to the original file path under any circumstance.** See the pre-flight path check in Step 3a.

### Step 3a: Pre-flight Path Check

Before creating the working copy, verify:

1. The computed working-copy path is not the same as the original path (byte-for-byte comparison after normalization).
2. The working-copy path is under `{{DOC_FOLDER}}\` or another location the user has explicitly named as the output directory.
3. The working-copy filename contains the word "copy" (case-insensitive).

If any of these checks fail, hard-stop. Do not write anything. Report the failure to the user and ask for instructions. Do not attempt to auto-correct the path; the user must resolve the ambiguity.

### Step 4: Classify Detected Issues

From the Mode 1 Grammar and Spelling subagent JSON output (see `_standards.md` "Grammar and Spelling Pass"), separate the detected issues into two buckets using the `tier` field attached to each issue. `tier: "safe"` goes to the auto-fix bucket. `tier: "prompt"` goes to the review bucket. Unknown-words-for-review items are copied verbatim to the review bucket without reclassification. Do NOT re-run detection; use the subagent's output as authoritative.

Tier-to-bucket reference:

**Auto-fix bucket (apply without asking):**

- Missing commas after introductory phrases
- Missing hyphens in compound modifiers used attributively (e.g., "proof of concept plan" -> "proof-of-concept plan")
- Obvious punctuation errors (missing period at end of sentence, missing space after punctuation)
- Possessive apostrophe errors where only one interpretation is grammatical
- True misspellings of common English words where the correct spelling is unambiguous (e.g., "teh" -> "the", "recieve" -> "receive")
- Subject/verb agreement errors with a single obvious fix
- Capitalization of proper nouns that are clearly names
- Normalization of smart quotes to curly, or curly to straight, based on the document's dominant style

**Review bucket (do not auto-apply, list for the author):**

- Homophone confusion (its/it's, their/there/they're, your/you're, let's/lets, her/she)
- Possible missing determiner flags where multiple readings work
- Possible confused prepositions
- Possible confused words without an unambiguous correct replacement
- Spelling flags on proper nouns (character names, place names)
- Spelling flags on foreign-language words (Spanish, Latin, etc.)
- Spelling flags on coined or slang terms (e.g., "pwned", "narcocorridos")

### Step 5: Apply the Auto-fix Bucket

Walk through the auto-fix bucket and apply each change to the working copy. For each change, record in the change log:

- The exact original text
- The exact replacement text
- A short line of context (the sentence the change was made in)
- The issue type (e.g., "missing comma after introductory phrase")

Apply changes in order of appearance to keep offsets consistent. If a file format requires it (e.g., .docx), use the `docx` skill to make the edits preserve structure.

### Step 6: Write the Change Log

Save the change log to:

```
{{DOC_FOLDER}}\[Title] - Grammar+Spelling Fixlog [YYYY-MM-DD].md
```

Structure:

```
# [Title] - Grammar and Spelling Fix Log

**Original file (unchanged):** [original path]
**Working copy (edited):** [working copy path]

---

Report: [report path]
Date: [YYYY-MM-DD]

## Summary

- Auto-applied: [N] changes
- Deferred for review: [M] items

## Auto-applied Changes

| # | Context | Before | After | Issue Type |
|---|---------|--------|-------|------------|
| 1 | ...The budget was thin anyway they agreed. | budget was thin anyway | budget was thin, anyway | Missing comma before 'anyway' |
| 2 | ...the proof of concept plan... | proof of concept plan | proof-of-concept plan | Missing hyphens in compound modifier |
...

## Deferred for Author Review

These items require judgment. They were NOT modified in the working copy.

| # | Location | Flagged Text | Flag | Suggested Action |
|---|----------|--------------|------|------------------|
| 1 | Para 4, sent 2 | it's teeth | Possible confused word (it's vs. its) | Confirm possessive vs. contraction |
| 2 | Para 12, sent 1 | Exactamente | Unknown word (Spanish) | Confirm intentional; add to custom dictionary if so |
...
```

### Step 7: Deliver

Return computer:// links to:

1. The PWA report (Mode 1 output)
2. The grammar+spelling-fixed working copy
3. The fix log

Headline verdict should name the counts: "Applied [N] grammar and spelling fixes. Deferred [M] items for your review. Full report attached."

Do not restate the changes in chat. The fix log is the deliverable.

---

## File Safety

1. The original input document is NEVER modified.
2. The working copy filename is always distinct from the original.
3. If a working copy filename already exists from today, append `-v2`, `-v3`.
4. The Review bucket is never silently ignored. Every item in it appears in the change log.

---

## Inputs Expected

- Path to the document (required)
- Genre selection (required for the embedded Mode 1 report; Grammar and Spelling fix behavior is genre-neutral)
- Standards document path (optional; if not supplied, Step 1 checks `{{DOC_FOLDER}}\standards.md` then asks the user)
- Optional: title override
- Optional: path to a custom dictionary to treat listed proper nouns / foreign words / coined terms as correct
