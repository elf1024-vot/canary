# Standards Builder

**Routine version:** v1.25
**File version:** v1.0

This routine conducts a conversational interview with the author and writes a `standards.md` file to their project folder. That file is loaded alongside the skill's bundled reference (`_standards.md`) on every subsequent Canary run. Rules in `standards.md` take precedence where they overlap with the bundled reference; all other bundled rules remain in effect.

The interview takes 5-15 minutes. Run it once per project. Re-run any time you want to update project standards.

You do NOT need this if you are satisfied with the bundled defaults. Canary runs without a project `standards.md`.

---

## Instructions to Claude

Conduct the interview conversationally. Do not dump all questions at once. Work through each section, confirm answers in plain English before moving on, and offer to skip any section the author says does not apply.

### Section 1: Project context

Ask:

> "What is this project? A sentence is enough — novel, newsletter, short story collection, academic paper, whatever it is."

> "What should I call it in the standards file?"

Record:
- `project_name` — what the author gives
- `project_type` — infer fiction / non-fiction / mixed from the description, or ask if unclear

---

### Section 2: Voice profile

Tell the author:

> "A few questions about voice and tone. These go into the file as a reference for the evaluator when it assesses Character Dialogue and report language. Skip any that don't apply."

Ask in sequence:

**2a.** "How does the writing sound? Pick words that feel right: formal, sardonic, literary, direct, breezy, authoritative, lyrical, genre-pulpy, academic, dry, warm — whatever fits."

**2b.** "Is there anything that MUST appear in every piece — a tonal element, a structural move, or a type of moment? If not, skip."

**2c.** "Are there any voice elements that are absolutely off-limits — a register or tone you are actively avoiding? If not, skip."

Record each answer or mark skipped.

---

### Section 3: Threshold adjustments

Tell the author:

> "Here are the default thresholds for your genre. Tell me if any feel wrong for this project — too tight, too loose, or not applicable."

Pull the thresholds for the author's selected genre from the bundled `_standards.md` Category Table and display them as a plain table with three columns: Category, Default Threshold, Direction. Show all 20 rows.

Ask:

> "Any you want to change? Or skip entirely? Name the category and your target."

Accept any number of changes. "Skip category X" removes it from grading and the goals denominator for this project. Record all changes.

---

### Section 4: Banned patterns

Tell the author:

> "Now banned patterns — things that should never appear. Skip any type that does not apply."

Ask in sequence:

**4a.** "Any phrases or expressions that are off-limits? For example: corporate jargon, AI-tell phrases, clichés specific to your genre, filler expressions."

**4b.** "Any structural patterns that are banned? For example: a forbidden punctuation mark, sentences that open a certain way, passive constructions used a specific way, a disallowed narrative mode."

**4c.** "Any terms off-limits for IP, world-specific, or editorial reasons? Terms that carry the wrong connotation for this project, or belong to a register you are not using."

Record each list separately. Any sub-list the author leaves empty is omitted from the output.

---

### Section 5: Required elements

Tell the author:

> "Anything that MUST appear in every piece? Skip this section if you have no hard requirements."

Ask in sequence:

**5a.** "Any content element that must appear regardless of subject? For example: a specific type of opening move, a required structural beat, a type of evidence or sourcing, a required kind of ending."

**5b.** "Any format requirements? For example: title conventions, heading rules, citation style, image requirements, cross-linking rules."

Record each requirement. Omit this section entirely if both answers are empty.

---

### Section 6: Scoring adjustments

Ask:

**6a.** "Any of the 20 Canary categories you never want to see in a report for this project? They won't count against the score."

**6b.** "Any categories you want as hard gates — a miss blocks the run until it is fixed? By default, Grammar and Spelling are soft-fail."

Record skips and hard gates. Omit sections that are empty.

---

### Section 7: Author fingerprints (optional)

Tell the author:

> "Last section, optional. If you have a sense of what makes this writing distinctly yours when it is working, I can add fingerprint guidance to the standards. The evaluator uses it as a lens on the Character Dialogue and Report Verification passes. Skip if you are not sure yet."

Ask:

**7a.** "What makes this writing distinctly yours? Two or three qualities — not polish goals, but things already there when you are writing well."

**7b.** "Should these be tiered? For example: some always appear, some appear only under pressure or in specific chapter types, some are arc-level or rare. If not, I will list them flat."

Record fingerprints and tiers, or mark skipped.

---

## Confirm before writing

Show a plain-English summary of every recorded answer:

> "Here is what I have. [Summary]. Does this look right, or do you want to change anything?"

Offer to revisit any section. On confirmation, write the file.

---

## Output format

Write `{{DOC_FOLDER}}\standards.md` with this structure. Omit any section whose content is empty.

```markdown
# Project Standards: [project_name]

**Project type:** [fiction / non-fiction / mixed]
**Genre profile:** [genre label]
**Loaded alongside:** the bundled `canary/references/_standards.md`

Rules in this file take precedence over the bundled reference where they overlap. All technical rules, detection heuristics, report format, and subagent contracts from the bundled reference remain in effect unless explicitly overridden here.

---

## Voice Profile

[Render Section 2 answers as a short paragraph or bullet list.]

---

## Threshold Overrides

[Table of only the categories the author changed:]

| Category | This Project | Bundled Default |
|---|---|---|
| Passive Voice | < 12.0 / 100 sent | < 25.0 / 100 sent |

[If no overrides: "All category thresholds use the bundled genre defaults."]

---

## Skipped Categories

The following categories are excluded from scoring and do not count toward the goals denominator for this project:
- [Category name]

---

## Hard Gates

The following categories are hard gates for this project. A miss hard-stops the run before the report is delivered:
- [Category name]

---

## Banned Patterns

### Phrases and expressions
- [Pattern]

### Structural patterns
- [Pattern]

### Project-specific terms
- [Pattern]

---

## Required Elements

Every piece in this project must contain:
- [Requirement]

### Format requirements
- [Rule]

---

## Author Fingerprints

These qualities mark writing that is working for this project.

**Tier 1 - always present:**
- [Fingerprint]

**Tier 2 - present under pressure:**
- [Fingerprint]

**Tier 3 - arc-level or rare:**
- [Fingerprint]

---

*Generated by the Canary standards builder. Edit directly to update. Re-run via the Canary edit menu to regenerate.*
```

---

## Notes for the router

- Write to `{{DOC_FOLDER}}\standards.md` only. Do not touch `pwa_config.json`.
- If `standards.md` already exists, warn before overwriting: "A `standards.md` already exists for this project. Running the builder will replace it. Continue?" Offer a side-by-side diff of old vs. new before the author confirms.
- After writing, the newly written file is active for the remainder of the session. No restart needed.
- The output file is a supplement, not a replacement. Every Canary mode loads the bundled `_standards.md` first, then layers this file on top.
