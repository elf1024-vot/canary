# Writing Evaluation Standards Reference

> **Bundled reference** — This file is loaded automatically on every Canary run as the technical foundation: detection heuristics, genre profiles, report format, subagent contracts, and base thresholds. To customize thresholds, banned patterns, or project-specific rules for your work, run the standards builder (say "run the standards builder") and Canary will create a `standards.md` alongside your document that layers on top of this file.

## What this document is

This is a rulebook template. It defines what "good" looks like for a piece of writing, in numbers, so a tool can grade a manuscript against it and produce a report the author can argue with.

Every threshold, banned pattern, tier rule, and exemption must be defined in the user's active standards document. No threshold is defined inside any prompt. If you want to change how the tool grades writing, edit your standards document. The prompts inherit the change automatically.

## Why a standards document exists at all

Most writing tools hardcode their rules inside the code. The rules are opaque, often inconsistent, and almost never under the author's control. If the tool disagrees with your voice, your options are "argue with a product manager" or "ignore the report."

A standards document flips that. The rules are a text file. You can read them, fork them, and change them. When the tool grades your work, it grades against rules you can see. When you disagree with a flag, you can track it back to the exact line in this document that produced it. If you would rather grade a different way, you edit this file; the prompts do not need to change.

That is the whole point. The yardstick should belong to the writer.

## If you are reading this because you want to fork it

Skip to the Category Table. Everything downstream of it (heuristics, genre profiles, auto-fix tiers, report format) is interpretation layered on top of the table. Change the thresholds to your taste. Add or remove categories. Replace the genre matrix. Rewrite the tier assignments. The prompts will follow.

The only non-negotiables are the File Safety Invariants near the end. Those protect the author's original file from destructive writes. Every other rule in this document is a style opinion, and style opinions are supposed to be yours.

---

## Relationship to ProWritingAid

The category list and report shape deliberately mirror ProWritingAid's "ProWriter" export. A reader familiar with PWA reports should be able to open a report from this tool and feel oriented immediately. The similarity stops at the surface: the thresholds, the heuristics, the genre handling, and the auto-fix behavior are all defined here and are independent of any PWA product.

This tool exists because the author of these prompts believes PWA's design, not its category list, is the problem. A standards document under the writer's control fixes more of that problem than better math ever would.

---

## Report Scope

A PWA-style report evaluates an entire written document (a chapter, an article, a short story, or a full manuscript) across 12 categories, produces numeric scores per category, and rolls up a single top-line metric: **% of goals achieved**.

One "goal" = one category threshold. A category either meets its threshold (goal achieved) or does not (goal not achieved). Top-line % = (goals achieved / total goals) rounded to the nearest whole percent.

Total goals by default: 20 maximum (see the category table below). Rows 20-22 (dialogue) are exempt when there is no dialogue; rows 21a and 21b are additionally exempt when tag count < 15. Engagement Score was removed in v1.14 as inherently unmeasurable.

---

## Category Table

Every category has a name, a metric, a threshold, and a direction (higher-is-better or lower-is-better).

| # | Category                  | Metric                                   | Threshold            | Direction |
|---|---------------------------|------------------------------------------|----------------------|-----------|
| 1 | Grammar Score             | % of sentences free of grammar issues    | 100%                 | higher    |
| 2 | Spelling Score            | % of words recognized / spelled correctly| 100%                 | higher    |
| 3 | Style Score               | % of sentences free of style flags       | >= 80%               | higher    |
| 4 | Sentence Length           | Avg words per sentence                   | 9.0 to 18.0          | in-range  |
| 5 | Sentence Variety          | Variety index                            | >= 5.0               | higher    |
| 6 | Very Long Sentences       | % of sentences over ~30 words            | < 3%                 | lower     |
| 7 | Passive Voice             | Passives per 100 sentences               | < 25.0               | lower     |
| 9 | Emotion Tells             | Filter-word constructions as % of sentences | < 20%             | lower     |
|10 | Weak Adverbs              | Weak adverbs per 1,000 words             | < 10.0               | lower     |
|12 | Complex Paragraphs        | % of paragraphs flagged complex          | < 15%                | lower     |
|13 | Glue Index                | % of glue words                          | < 40%                | lower     |
|14 | Conjunction Starts        | % of sentences starting with conjunctions| < 9%                 | lower     |
|15 | -ing Starts               | % of sentences starting with -ing word   | < 2%                 | lower     |
|16 | Slow Pacing               | % of slow-paced text                     | < 30%                | lower     |
|17 | Quote Consistency         | % of quote marks consistent              | 100%                 | higher    |
|18 | Acronym Consistency       | % of acronyms styled consistently (fiction); first-use definition + styling (non-fiction) | 100% | higher |
|19 | Long Repeated Phrases     | Distinct 5+ word phrases appearing 3+ times | < 3              | lower     |
|20 | Dialogue Tags             | % of dialogue lines that use a tag       | < 50%                | lower     |
|21a| Voice Consistency (Tags)  | Dominant tag verb as % of all tags       | >= 50%               | higher    |
|21b| Performance Tag Rate      | % of tags drawn from the performance list| < 18%                | lower     |
|22 | Dialogue Tags with Adverbs| % of tags paired with an adverb          | < 12%                | lower     |
|23 | Character Dialogue Consistency | Zero unexplained voice drift + zero attribution mismatches across characters clearing the 6-line floor | zero flags | lower     |

(The "Total goals" headline % sums the rows above that apply to the document. If a document has no dialogue, rows 20-23 are exempt and the denominator adjusts. Rows 21a and 21b are jointly the replacement for the legacy "Unusual Dialogue Tags" single metric and are each scored as one goal. Both have a 15-tag sample-size floor: if tag count < 15, both rows read N/A with the disclosure "You have fewer than 15 tags, this is not enough for evaluation," and both are exempt from the denominator. Row 23 has a per-character 6-line floor: if no character in the chapter reaches 6 lines of dialogue, the row reads N/A with the disclosure "No character reaches the 6-line dialogue floor in this chapter; voice-fingerprint analysis needs more lines per speaker to be meaningful," and row 23 is exempt from the denominator. Row 23's flags are judgment-sensitive: a narratively justified voice shift (drunk, panicked, lying, performing) is still flagged, and the author decides whether to accept.)

---

## Scoring Rules

1. **Run the whole document.** Do not sample. If the manuscript is long, chunk it, compute per-chunk metrics, then aggregate.
2. **Counts are literal.** When the report says "355 long repeated phrases", it means 355 distinct phrase instances were detected, not a projection.
3. **No score may be estimated.** If a metric cannot be computed from the text provided, mark it `N/A` and exclude it from the goals denominator.
4. **Thresholds are fixed.** Do not relax a threshold because the draft is early or because the author prefers a style. The report grades against the standard; the author decides what to act on.
5. **Every flagged issue gets a row, and every flagged issue names the actual text.** The Grammar, Spelling, Style, Passive Voice, Emotion Tells, Weak Adverbs, Very Long Sentences, Complex Paragraphs, Conjunction Starts, -ing Starts, Slow Pacing, Long Repeated Phrases, and Dialogue Tags sections each emit a table listing the detected text verbatim (the sentence, the phrase, the paragraph preview) plus its paragraph number. An author reading the report MUST be able to copy the text into a Find box and jump straight to the flag. Counts without text are not acceptable output. Per-category fields are defined in the Flagged Items section under each category's Detection Heuristics entry. When flag counts exceed 50 in a single category, the table truncates to the first 50 by paragraph ascending and discloses "showing first 50 of N" in the section header.

---

## Pre-processing: What Gets Scored

Before any metric is computed, the author decides what counts as prose. Structural elements that the reader does not process as prose (headings, front-matter, production markers) skew every metric if scored. But what counts as structural is author-specific: one author might use `[[THOUGHT:]]` brackets for interiority, another might use `<<TAG>>`, another might use nothing and want every line scored.

This section defines the question. The router asks it at the start of every run.

### The pre-processing question

Every run MUST resolve the author's pre-processing intent before scoring. Resolution happens via the **config-driven preprocessing** mechanism described below. On first run, the author is interviewed and a config file is written. On subsequent runs, the config is loaded silently with a one-line summary, and the author is offered the chance to update it before the run continues. The author either accepts the loaded config, edits it interactively, or declines to use it (in which case the routine falls back to the first-run interview).

### Config-driven preprocessing (v1.22)

The routine reads its preprocessing rules from a single JSON config file. This replaces the prior pattern of asking every preprocessing question fresh on every run, and replaces every hardcoded preprocessing rule in the strip script with a data-driven entry.

**Config file location.** The routine looks for the config at:

`{{DOC_FOLDER}}\pwa_config.json`

If none exists, the routine triggers the first-run setup interview (below) and writes the result to `{{DOC_FOLDER}}\pwa_config.json`.

**Schema (v1.22).**

```json
{
  "schema_version": "1.0",
  "header_strip_patterns": [
    {
      "label": "chapter title",
      "type": "line_starts_with",
      "value": "Chapter ",
      "scope": "first_line_only",
      "consume": "single_line"
    },
    {
      "label": "YAML front matter",
      "type": "line_starts_with",
      "value": "---",
      "scope": "first_line_only",
      "consume": "until_pattern",
      "until_pattern": "---"
    }
  ],
  "paired_delimiters": [
    {
      "opener": "[[THOUGHT:",
      "closer": "]]",
      "mode": "A",
      "label": "internal thought",
      "attributed_to_pov": true
    }
  ],
  "acronym_emphasis_exclusions": [],
  "weak_adverb_noun_exclusions": ["assembly", "family", "supply", "reply", "rally"],
  "ing_starts_proper_noun_exclusions": ["nothing", "something", "morning", "evening"]
}
```

**`header_strip_patterns` — rule types.** Each rule has a human-readable `label` (used in the edit menu and strip log so the author can audit which rules fired) and a `type`:

- **`line_starts_with`** — exact prefix match. Optional `and_contains` adds a substring requirement on the same line. Optional `scope`: `first_line_only`, `all` (default). Optional `consume`: `single_line` (default), `until_blank_line`, `until_next_heading`.
- **`exact_line`** — full-line equality match. Same `scope` and `consume` options.
- **`markdown_heading`** — strips Markdown ATX headings (`#`, `##`, etc.). Required `levels` array (e.g., `[1, 2, 3]`). Same `scope` and `consume` options.
- **`html_tag`** — strips HTML tag blocks. Required `tags` array (e.g., `["h1", "h2", "h3"]`). User-configurable `consume`: `tag_block` (strip opener through closer inclusive; handles inline `<h3>Title</h3>` and multi-line `<h3>\nTitle\n</h3>` the same way), `opener_line` (strip only the line containing the opener), `closer_line` (strip only the line containing the closer), `opener_and_closer_lines` (strip both opener and closer lines, keep content between them in scored prose). The author chooses `consume` per rule at setup; the default offered is `tag_block`.
- **`regex`** — escape hatch for anything else. Required `pattern` (Python regex string). Same `scope` and `consume` options. The strip script applies `re.MULTILINE` by default; for multi-line patterns the rule MAY include `flags: ["DOTALL"]`.

The skill ships with no strip rules in the bundled template config; all patterns are defined by the author at first-run setup.

**`paired_delimiters` — three-mode taxonomy.** See *Special handling: paired-delimiter conventions* above for the A/B/C definitions. Each entry has `opener`, `closer`, `mode` (`"A"`, `"B"`, or `"C"`), `label` (human-readable, used in strip log and report). Mode A entries MAY include `attributed_to_pov: true` (default behavior — interior content attributed to the chapter's POV character whose name is supplied at runtime). Mode B entries MUST include `register_label` (used as the section header) and MAY include `register_description` (used in the section disclosure). Mode C entries need only `opener`, `closer`, `mode`, `label`.

Disambiguation: array order, first-match-wins. The author orders entries from most-specific opener to least-specific.

**`character_names`** — optional array of strings naming the characters in this document. Used by the Grammar and Spelling subagent to avoid flagging character names as misspellings. Example: `["Alex", "Jordan", "Stranger"]`. Default empty; populate at first-run setup or any time via the edit menu.

**Exclusion lists.** Three editable arrays carry per-manuscript exclusions for the secondary-fix detectors:

- `acronym_emphasis_exclusions` — ALL-CAPS sequences that the Acronym Consistency detector should treat as typographic emphasis (book/franchise titles, in-world organization names, stylistic shouts) rather than acronyms. Default empty; populated per manuscript at setup or as canaries surface false positives.
- `weak_adverb_noun_exclusions` — common -ly nouns (assembly, family, supply, reply, rally, etc.) the Weak Adverbs detector should skip because they are nouns not adverbs. Seed default populated with common English false positives; authors append per-manuscript as canaries surface more.
- `ing_starts_proper_noun_exclusions` — capitalized -ing tokens that are proper nouns or non-participle words rather than verb participles (character surnames, place names, etc.). Seed default populated with common English false positives (nothing, something, morning, etc.); authors append per-manuscript as canaries surface more.

Each exclusion list applies to its corresponding detector via case-insensitive substring or token match; the detector's Detection Heuristics section specifies the exact comparison rule.

**First-run setup interview.** When no config file exists for the document, the routine runs a short conversational interview. The goal is to capture what the author wants ignored in plain English; the routine translates answers into config entries without exposing JSON structure to the author.

**Q1 — What should I ignore?**

Read the first 30 lines of the document and show them to the author. Ask:

> "Here's the top of your document. What should I skip when scoring? For example: headings, chapter titles, a 'Cast of Characters' block, anything in special brackets — or 'nothing, score everything'."

Translate each answer into a `header_strip_patterns` entry. Translation table:

| Author says | Config entry type |
|---|---|
| "All lines starting with #" | `markdown_heading`, all levels |
| "The first line if it's a chapter title" | `line_starts_with`, `"Chapter "`, `first_line_only` |
| "Lines starting with 'Cast:'" | `line_starts_with`, `"Cast:"`, `all` |
| "The YAML front matter at the top" | `line_starts_with`, `"---"`, `first_line_only`, `consume: until_pattern` |
| "H3 headings" | `markdown_heading`, levels [3] |
| "Anything in all-caps on its own line" | `regex_match`, `"^[A-Z\s]{4,}$"`, `all` |

If the author is unsure, offer the suggestion appropriate to their file type (see "Suggested starting defaults by format" below).

**Q2 — Do you use any special markers?**

Ask:

> "Do you use any special markers for things like internal thoughts, production notes, or atmospheric voice? For example: `[[THINKING: some text ]]`, `<< note >>`, or text in asterisks. If not, say 'no'."

If yes, ask one follow-up to classify:

> "Should the text inside those markers count toward the scored prose (just strip the markers), or should the whole block be excluded from scoring?"

Map the answer to a mode:

- **Strip markers only, keep and score the content** → Mode A (attributed to POV character; use for character interiority)
- **Exclude the whole block from scoring, but mention it in the report** → Mode B (use for non-character voice registers, editor notes)
- **Remove silently, no mention in report** → Mode C (use for purely production-side annotations)

**Q3 — Anything to exclude from specific checks?**

Ask:

> "Are there any words ending in -ly that aren't actually adverbs in your writing? For example: character surnames, place names, or specialist terms. I already skip common English nouns like 'family' and 'supply'. Leave blank to use the defaults, or name additional words to exclude."

Accept a comma-separated list. Append to `weak_adverb_noun_exclusions`.

**Q4 — Character names.**

Ask:

> "What character names appear in this document? I'll pass them to the spelling checker so they are not flagged as misspellings. Leave blank if you prefer to skip this."

Accept a comma-separated list. Store as `character_names` array.

**Confirm before saving.** Present a plain-English summary:

> "Based on your answers, I'll ignore: [list in plain English]. Special markers: [list with mode]. Everything else gets scored. Does this look right? [y/edit]"

If the author wants changes, loop back. If confirmed, write `{{DOC_FOLDER}}\pwa_config.json` and proceed.

The result is written to `{{DOC_FOLDER}}\pwa_config.json`. Subsequent runs load it silently.

**Restart prompt behavior.** On subsequent runs, after loading the config the routine reports a plain-English summary in the same conversational register as the first-run interview:

> "Skipping: [list what is being ignored in plain English, e.g. 'chapter titles, H3 headings']. Markers: [e.g. 'internal thoughts (scored and attributed to POV)']. Ready to run. Want to change any of this? [y/n]"

Default `n` proceeds straight to the run. If the author answers `y`, the routine drops into a structured edit menu (numbered text menu in CLI/Code, AskUserQuestion picker in Cowork — the routine detects context). The menu offers add/edit/remove for each top-level array, plus view-current-config, save-and-continue, and cancel-discard-changes options. Edits are written back to the config file on save; a single `.bak` of the prior config is kept (overwritten each save) so a bad edit can be reverted.

**Strip log.** Alongside the marker map JSON, the strip script writes a strip log recording which rules fired and how many times:

```json
{
  "rules_applied": [
    { "label": "chapter title", "matches": 1 },
    { "label": "YAML front matter", "matches": 1, "lines_consumed": 3 },
    { "label": "internal thought (Mode A)", "matches": 11, "interior_words_kept": 332 },
    { "label": "omniscient narrator (Mode B)", "matches": 1, "interior_words_excluded": 18 }
  ],
  "rules_zero_matches": ["markdown h3", "blockquotes"],
  "summary": "9 of 9 active rules processed; 2 rules with zero matches."
}
```

Zero-match rules are surfaced explicitly so the author can prune dead rules from their config or recognize a manuscript-format mismatch (declared markdown headings against a file that has none).

**Undeclared paired-delimiter warning.** During strip, if the script encounters any `[[<TAG>: ...]]`-shaped (or other common paired-delimiter-shaped) span that no declared `paired_delimiters` entry matched, it emits a warning to the strip log: `"WARNING: undeclared paired-delimiter-shaped content at paragraph N: [[<excerpt>...]]. Classify in pwa_config.json paired_delimiters or accept as scored prose."` The warning is informational, not blocking — the run continues with that span treated as prose — but it surfaces the exact failure mode (silent leakage of author markers into scored corpus) that produced the v1.22 patch in the first place.

### Suggested starting defaults by format

These are defaults the router offers as starting points. The author can accept, modify, or replace them.

- **Markdown (.md)**: all heading levels (`#` through `######`), YAML front-matter blocks between `---` fences at the top of the document, fenced code blocks, horizontal rules (`---`, `***`, `___`).
- **DOCX**: paragraphs styled as Heading 1 through Heading 9, Title, Subtitle, TOC, Caption, or any other non-body-text style.
- **Plain text (.txt)**: prompt the author for specifics. Plain text has no structural signal; the router cannot guess what is front-matter vs. first-paragraph prose. Ask for a list of patterns to strip (line starting with "Chapter", line starting with "Cast:", lines containing `[[` brackets, etc.), or let the author say "nothing, score every line."
- **HTML**: heading tags `<h1>` through `<h6>`, `<title>`, `<header>`, `<nav>`. Extract the text content of body-prose tags (`<p>`, `<div>` containing prose).

### Special handling: paired-delimiter conventions (v1.22)

Some authors mark interior monologue, atmospheric voice, or production-only notes with paired delimiters like `[[THOUGHT: ... ]]`, `<<THINKING>>...</THINKING>>`, asterisk-wrapped *italics*, HTML comments, or any other author-specific convention. These markers are structural wrappers, not prose, but they fall into different functional categories and require different handling.

**The three-mode taxonomy (v1.22).** Every paired-delimiter convention an author declares is classified into exactly one of three modes. The author makes this classification at first-run setup (see *Config-driven preprocessing* below); the routine treats unclassified `[[<TAG>: ...]]`-shaped content as prose and warns the author so they can classify it on the next run.

- **Mode A — Character interiority (scored, attributed).** Markers stripped; interior content kept in scored prose; interior spans recorded in the marker map under `internal_mode_spans` and attributed to a named POV character as a second speech mode. The Character Dialogue Consistency subagent reads the marker map and renders two fingerprints (spoken + internal) for that POV character.
- **Mode B — Non-character voice register (diagnostic, not scored).** Markers AND interior content both stripped from the scored corpus; interior spans recorded in the marker map under `non_character_voice_spans`. A dedicated *Non-Character Voice Registers* report section surfaces count, paragraph numbers, and verbatim text with explicit disclosure that this register was excluded from scoring. No score impact, no penalty, no goal counted against. Use Mode B for atmospheric narration, choric voice, omniscient intrusions, or any voice that is not a named character speaking but is part of the manuscript's intentional register.
- **Mode C — Production-only strip (silent).** Markers and interior content both stripped; nothing logged or surfaced. For author-side notes, TODO markers, scene-break placeholders, structural cues that should never appear in any version of the report.

Authors with paired conventions (e.g., `[[THINKING: ... ]]`, `<<NARRATOR>>...</NARRATOR>>`, asterisk-italics, custom XML-style tags) declare their opener/closer pair plus mode at first-run setup and the stripper applies the appropriate rule. The "strip everything including content" behavior is Mode C and remains selectable.

**Disambiguation.** When multiple declared pairs could match the same span (e.g., both `[[THOUGHT:` and a fallback `[[`), the strip script processes pairs in declaration array order, first-match-wins. Authors put the more specific opener earlier in the array.

### Marker map file

When paired-delimiter stripping is used (any Mode A or Mode B declarations exist), the stripper writes a marker map alongside the stripped prose:

`{{DOC_FOLDER}}\[Title] - marker map [YYYY-MM-DD].json`

Schema (v1.22):

```json
{
  "pov_character": "Marcus",
  "source_chapter": "{{DOC_FOLDER}}\\source.txt",
  "stripped_file": "{{DOC_FOLDER}}\\stripped.txt",
  "paired_delimiter_declarations": [
    {
      "opener": "[[THOUGHT:",
      "closer": "]]",
      "mode": "A",
      "label": "internal thought",
      "attributed_to_pov": true
    },
    {
      "opener": "[[NARRATOR:",
      "closer": "]]",
      "mode": "B",
      "label": "non-character voice register",
      "register_label": "Omniscient Narrator",
      "register_description": "Atmospheric voice; not a named character; diagnostic only, not scored."
    },
    {
      "opener": "<!--",
      "closer": "-->",
      "mode": "C",
      "label": "production notes"
    }
  ],
  "internal_mode_spans": [
    {
      "paragraph_start": 14,
      "paragraph_end": 14,
      "word_count": 42,
      "text": "Three years and it still sounds like he's reading copy from a livestock catalog..."
    }
  ],
  "non_character_voice_spans": [
    {
      "register_label": "Omniscient Narrator",
      "source_paragraph_start": 151,
      "source_paragraph_end": 151,
      "word_count": 18,
      "text": "The city never forgave its deserters. It only waited, patient as a debt collector.",
      "note": "stripped from scored corpus per Mode B"
    }
  ]
}
```

`pov_character` comes from the author's answer to the preprocessing question (or is inferred by the subagent if a single POV is obvious from the chapter). `paired_delimiter_declarations` mirrors the active config's `paired_delimiters` array so the marker map is self-describing without the config file.

`internal_mode_spans` (Mode A) reference paragraph numbers in the **final stripped file**, since Mode A content remains in scored prose. The Character Dialogue Consistency subagent reads this array to partition the POV character's lines into spoken-mode and internal-mode for the two-fingerprint analysis.

`non_character_voice_spans` (Mode B) reference paragraph numbers in the **pre-strip source file**, since Mode B content has been removed from the stripped file. The report's *Non-Character Voice Registers* section surfaces these spans for author review with explicit disclosure that they were excluded from scoring.

Downstream passes (Grammar/Spelling/Style/tokenizer) ignore the marker map and score the stripped prose as a single continuous document.

### Required disclosure

The report's scope note MUST disclose what was stripped, verbatim. Minimum format:

> Pre-processing: stripped [list of what was stripped, including the author's custom additions or subtractions]. Scored: narrative prose only.

If the author said "strip nothing," the disclosure reads: "Pre-processing: nothing stripped. Scored: full document as-is."

### Why this is a question, not a default

Different authors use different markup. Forcing a default strips things the author wants scored or leaves things in that skew counts. The author knows their manuscript. The tool does not. Asking is faster than guessing wrong, and cheaper than letting a wrong guess pollute a report the author then has to argue with.

### Reuse

All three modes (Mode 1, Mode 2, Mode 3) read preprocessing rules from `{{DOC_FOLDER}}\pwa_config.json`. The first-run interview writes the config; subsequent runs load it silently and offer the restart prompt described above.

---

## Computation Method: Precise (Python tokenizer)

Every run produces its counts through a Python tokenizer run via bash against the stripped prose. There is no ballpark mode. Eye-surveyed numbers were surveyed against Precise-mode numbers during shakedown and missed by 15+ percentage points on Glue Index and by roughly 12x on Long Repeated Phrases. Error ranges at that scale do not earn a place in a report the author acts on.

### Why there is no choice

The tool's premise is that the rulebook is readable and the math is defensible. An estimate that a human cannot reproduce is neither. If the author needs a fast pass, the faster path is to run the tokenizer against a smaller excerpt, not to eyeball the full document.

### Required disclosure

The report's scope note MUST include:

> Computation: counts produced by Python tokenizer run against the stripped prose. Script saved alongside the report.

The disclosure is non-optional. A reader must always be able to locate and rerun the script.

### Tokenizer requirements

The Python script MUST:

1. Read the stripped prose from a temp file (not re-strip; pre-processing has already run).
2. Produce counts for every metric in the Category Table that can be mechanically tokenized (sentence count, word count, average sentence length, sentence length standard deviation for variety, very-long-sentence count, passive construction count, weak adverb count via -ly suffix against the weak-verb list, glue word count, conjunction-start count, -ing-start count, repeated-phrase detection at 5+ word windows with 3+ occurrence floor, paragraph count, complex-paragraph detection, emotion-tell construction detection against the filter-verb and emotion-word lists, slow-pacing paragraph classification against the action-verb list, style-flag detection against the pattern list).
3. For every category that flags at the sentence, paragraph, or phrase level, the tokenizer MUST emit a `flagged_items` array alongside the count. Each item contains the actual text the author can paste into a word-processor Find box to locate the flag in their document, plus the minimum context needed to interpret it. Exact per-category fields are specified in the Flagged Items section of each category's Detection Heuristics entry and summarized in the Flagged Items Schema below.
4. Output a JSON blob with one key per metric. Claude reads the JSON and fills the report sections.
5. Save to `[output_dir]\[Title] - tokenizer [YYYY-MM-DD].py` alongside the report so the author (or a stranger forking this) can inspect and rerun the exact counts.

After the v1.14 tightening, the remaining judgment-call metrics are: Dialogue Tag classification (which verb is invisible, which is performance — the lists are explicit but edge cases like "declared" still require a call). Every other metric in the Category Table is fully mechanical and traceable to a line in this document.

### Flagged Items Schema

Every flagged item is an object with at minimum these fields:

- `text`: the actual text of the flag, copied verbatim from the document. For sentence-level flags this is the full sentence. For paragraph-level flags this is the first 25 words of the paragraph followed by an ellipsis. For phrase-level flags this is the matched phrase.
- `paragraph`: the 1-indexed paragraph number in the stripped prose (so the author can jump to it).
- `pattern` or `rule`: the specific pattern name or heuristic that matched (e.g., `"acquired -> gained"` for Style, `"felt + afraid"` for Emotion Tells, `"conjunction-start: But"` for Conjunction Starts).

Per-category extensions are specified inline in each Detection Heuristics section. The tokenizer output must be a JSON array under the category's top-level key (e.g., `style_score.flagged_items`, `emotion_tells.flagged_items`). If a category's flag count exceeds 50, the tokenizer may truncate the array to the first 50 items sorted by paragraph ascending, and emit a sibling field `flagged_items_truncated_at: 50` so the report discloses the truncation. The total count is always the true count, not the truncated count.

Why this exists: A report that says "2 flagged sentences" without naming the sentences forces the author to re-read the chapter to find them. That is the exact opacity this routine exists to correct. If the tool can locate a flag, the tool can name the flag. The author decides whether to act on it.

### Reuse

The Computation Method is no longer a user-facing choice, so nothing is persisted. `user_config.json` no longer carries a `computation` field.

---

## Subagent Architectural Rule: Subagents Report, the Router Validates

Every subagent the routine dispatches (Strip Verification, Grammar and Spelling, Summary and Beat Sheet, Character Dialogue Consistency, Report Verification) follows one architectural rule: **the subagent reports raw observations; the router validates those observations against the declared inputs and re-dispatches on failure.**

### Why the gate cannot live in the subagent prompt

Surfaced during an end-to-end canary run. The Grammar and Spelling subagent's prompt contained a self-evaluation gate with explicit pass / fail thresholds. The subagent returned a result that violated the gate AND reported its own verdict as "passed." The prompt instruction was ignored.

This is a structural property of subagent dispatch, not a quirk of one bad run: a subagent reading a long instruction will tend to produce output that looks like what the instruction seems to want, regardless of whether the underlying observation supports that output. Asking the subagent to self-reject is asking it to fight that gradient. It will not reliably do so.

### The rule

For every subagent in the routine:

1. **The subagent's prompt asks only for observations and counts.** No "if X then re-do" branches inside the prompt. No "self-check before returning" instructions. The subagent's job is to read the input and return what it saw, in the schema specified.
2. **The router validates the returned JSON before consuming it.** Validation is deterministic Python: schema check, range check, cross-reference check (every cited excerpt must appear in the stripped file, every paragraph reference must be `<=` the file's paragraph count, no guaranteed-hallucination markers appear in citations).
3. **On validation failure, the router re-dispatches once with a corrective instruction citing the specific failure** (e.g., "you cited excerpt `<text>` at paragraph 14, but that string does not appear in the stripped file; re-read the file and cite only verbatim text").
4. **On second failure, the router hard-stops the Mode 1 run and reports the failure to the author**, exactly as a strip-verification failure would. The report does not publish with unvalidated subagent inputs.

### What this means for prompt files

Subagent prompt files in `subagents/` MAY include quality expectations as documentation for the human reading the prompt — but those numbers exist to inform the router's validation logic, not to instruct the subagent. The subagent's hard constraints are limited to: which file to read, what schema to return, and what tokens / patterns it must not invent.

### What this means for the verification chain

Strip Verification (subagent) is itself bound by this rule: the router checks the verifier's JSON against the strip log's claims before accepting it. Report Verification (subagent) is the router's final audit pass against the assembled report — the router validates the verifier's verdict against the verifier's own cited evidence, so a verifier that returns "PASS" while citing a failure is rejected. Validation is recursive only one level deep; the router itself is the trusted root.

### Validator config the router carries

Each subagent has a router-side validator config defining the validation rules:

- **Grammar and Spelling**: every `excerpt`, `context`, and `word` substring-checked against the stripped file; every `paragraph` field in range `[1, file_paragraph_count]`; no citation contains a guaranteed-hallucination marker (strip-removed tokens such as paired-delimiter content, heading lines, or other patterns declared in the author's config); `score_pct` matches `100 * (1 - issues_found / total)` to 2 decimals.
- **Strip Verification**: `verdict` field present; every `failures` entry references a real category from the strip log.
- **Summary and Beat Sheet**: 5 `<=` beat count `<=` 10; every named character must appear in the source chapter; word ranges must fit within the chapter's word count.
- **Character Dialogue Consistency**: every fingerprint's `line_count >= 6` for any non-`insufficient` `sample_status`; every drift_flag and attribution_flag's `paragraph` and `text` substring-checked against stripped file; cross-mode drift flags (spoken-to-internal for the same POV character) are zero (else FIX).
- **Report Verification**: every cited claim must reference a real source artifact (chapter, tokenizer JSON, or upstream subagent JSON) and the citation must check out.

### A clean chapter producing clean scores is the expected outcome, not a subagent failure

A canary against a multi-pass-reviewed chapter will often return Grammar 100% and Spelling 100%. That is the correct result. The router validates what the subagent DID claim (the citations in its issue arrays substring-check against the stripped file; its paragraph references land inside the file; its score math is correct), not what it should have claimed alongside. A subagent that short-circuits and returns zero issues on a genuinely clean chapter produces the same output as one that did the work and found nothing — the router does not try to distinguish them.

This reflects a deliberate architectural narrowing: spelling integrity is a function of what the subagent flags (step 6 of the Recognition Order — true misspellings and misuses), not a function of what it excluded along the way. Foreign vocabulary, proper nouns, coined terms, and genuine unknowns are not reported and are not gated on. The router's job is to confirm that the issues the subagent DOES report are real (exist in the file, reference real paragraphs, not invented).

---

## Strip Verification: Confirm the Denominator Before Scoring

Before any metric is computed, the router MUST verify that the stripped prose file accurately reflects the author's pre-processing intent. This is a separate step from pre-processing. Pre-processing decides what should be removed; strip verification confirms what was actually removed.

### Why this exists

Every downstream metric divides by the wrong denominator if the stripping pass has a bug. A regex that misses one class of marker silently inflates the word count; a regex that is too greedy silently removes narrative paragraphs and shrinks the count. Either failure mode produces confident numbers in the report that are wrong. The author has no way to know.

An independent verification step catches both failure modes before the tokenizer runs against a polluted input.

### The verification step

After stripping and before the tokenizer runs, the router MUST:

1. **Compare the author's declared strip list against what the stripping pass actually produced.** Every category the author named (e.g., chapter title line, YAML front matter, paired-delimiter markers) must appear zero times in the stripped file. If any category survives, the strip failed and the script must be re-run or fixed before continuing.
2. **Confirm no narrative prose was removed.** Spot-check: pick at least three narrative paragraphs from the original at varied positions (opening, middle, closing) and verify each appears verbatim in the stripped file. If any declared-prose paragraph is missing, the strip over-reached.
3. **Sanity-check the word-count delta.** Compute `original_word_count - stripped_word_count = delta`. The delta should be plausible given the strip list: a rough sum of the word counts for each declared category. If the delta is off by more than 10% in either direction, re-verify.
4. **Record the verification result in a Strip Verification note.** The note lists each strip category with a found/not-found result and the word-count delta.

### Required disclosure

The report's Scope Note MUST include a Strip Verification line confirming the result:

> Strip verification: confirmed. [categories] removed cleanly; [original word count] original, [stripped word count] stripped, delta [N] words plausible.

If verification fails, the report does not publish. The router hard-stops and reports the failure to the author, exactly as a File Safety Invariant failure would.

### Delegation

Strip verification SHOULD be performed by a subagent (Task tool) rather than the main context, so the verifier reads both files with fresh eyes and cannot be influenced by assumptions about what the strip was "supposed to" do. The subagent returns a short pass/fail report; the main context records the result in the Scope Note and proceeds.

---

## Grammar and Spelling Pass: Subagent-Delegated Evaluation

Grammar and Spelling are not tokenizable the way mechanical metrics are. A regex cannot tell you whether "lie" should be "lay" in context, whether a Spanish word is used correctly, whether a comma after an introductory phrase is missing, or whether "its" should be "it's." These require language understanding.

That does not make Grammar and Spelling unscorable. It makes them subagent-delegated, exactly like Strip Verification. An LLM evaluator reading the stripped prose with fresh eyes and the Detection Heuristics in hand produces a real count of issues, which feeds a real score. This is how human copyeditors work. The routine reflects that.

### Why this is a routine step, not a tokenizer field

The v3 canary left Grammar and Spelling as "deferred to LLM pass" placeholders and the Mode 1 report inherited the punt. That was wrong. The whole premise of this routine is that every category has a defensible score or a documented reason it cannot be scored. "The tokenizer cannot evaluate grammar" is a technical note, not a score. This section closes that gap.

### The evaluation step

After strip verification passes and before report assembly, the router MUST dispatch a Grammar and Spelling subagent. The subagent:

1. **Receives** the path to the verified stripped prose file, the genre, and the relevant portions of the Detection Heuristics (Grammar section, Spelling section with its six-step Recognition Order, and the Exclusions list).
2. **Reads** the full stripped prose.
3. **Scans** for grammar issues per the Detection Heuristics Grammar section: missing determiners, missing commas after introductory phrases, confused prepositions, homophone confusion (its/it's, their/there, your/you're, affect/effect), missing hyphens in compound modifiers, punctuation errors, subject/verb disagreement, tense drift within a paragraph, dangling modifiers, comma splices, run-on sentences.
4. **Scans** for spelling issues per the Detection Heuristics Spelling section. Applies the six-step Recognition Order internally and reports ONLY step 6 hits — confirmed misspellings of English words and confirmed wrong-word-for-context usages. Does NOT flag and does NOT log foreign-language words used correctly, proper nouns recognizable from context, coined terms, or genuine unknowns. Those are silent exclusions.
5. **Returns** a JSON blob in the following shape:

```json
{
  "subagent_version": "v1.2",
  "stripped_file_read": "<dispatched path>",
  "grammar": {
    "total_sentences": 548,
    "issues_found": 7,
    "score_pct": 98.72,
    "issues": [
      {
        "type": "missing_comma_after_introductory_phrase",
        "tier": "safe",
        "paragraph": 14,
        "context": "...before context...",
        "excerpt": "Sentence with the issue.",
        "suggested_fix": "Sentence with, the issue."
      }
    ]
  },
  "spelling": {
    "total_words": 5367,
    "issues_found": 1,
    "score_pct": 99.98,
    "issues": [
      {
        "type": "true_typo",
        "tier": "safe",
        "word": "teh",
        "paragraph": 42,
        "context": "...went teh kitchen...",
        "suggested_fix": "the"
      }
    ]
  }
}
```

The `score_pct` formula for Grammar is `100 x (1 - issues_found / total_sentences)`, clamped at [0, 100]. The `score_pct` formula for Spelling is `100 x (1 - issues_found / total_words)`, clamped at [0, 100].

The `tier` field marks each issue as `safe` (Mode 3 can auto-apply: true typos, missing punctuation of well-defined kind, clear capitalization errors) or `prompt` (Mode 3 surfaces for review: homophone confusion, dangling modifiers, ambiguous comma placement).

**Scope of spelling issues.** The subagent walks the six-step Recognition Order internally but reports ONLY step 6 hits — confirmed misspellings of English words and confirmed wrong-word-for-context usages. Steps 1 through 5 (English dictionary, multi-language recognition, proper nouns from context, coined / jargon terms, genuine unknowns) are exclusions the subagent applies silently. They are not logged, not reported, and not subject to validation. The spelling score reflects only the misspellings and misuses the subagent flagged, period.

### Integration into Mode 1

The Mode 1 report's Grammar Check and Spelling Check sections use the subagent's JSON output directly. Neither section says "deferred to LLM pass" ever again. Both report a real percentage, the issue count, and a table of the flagged issues with context. Thresholds from the Category Table apply as written (Grammar 100%, Spelling 100%; any issue count > 0 counts against the goal).

### Integration into Mode 3

Mode 3 consumes the same JSON output from the Mode 1 subagent run. Safe-tier issues are auto-applied to the working copy. Prompt-tier issues are surfaced to the user via AskUserQuestion and applied only on confirmation.

### Required disclosure

The report's Scope Note MUST include a Grammar/Spelling Pass line confirming the delegation:

> Grammar/Spelling pass: delegated to subagent, completed. [N] grammar issues, [M] spelling issues.

If the subagent fails (e.g., returns malformed JSON or times out), the router hard-stops and reports the failure, exactly as a strip-verification failure would. The report does not publish with missing Grammar or Spelling scores.

### Delegation rationale

A subagent is used rather than the main context for three reasons:

1. **Fresh eyes.** The main context may have built assumptions about the document during strip verification, pre-processing decisions, or genre selection. A subagent reads the prose clean.
2. **Context isolation.** The subagent's output is a compact JSON blob. The main context does not absorb 5,000 words of prose it already has access to; it absorbs the judgment.
3. **Matches the existing pattern.** Strip Verification is already a subagent. The Grammar/Spelling Pass mirrors that architecture, which keeps the Mode 1 flow consistent.

---

## Summary and Beat Sheet Pass: Subagent-Delegated Reading

The report's What Happened summary and Beat Sheet appear in the first two sections the reader encounters. They establish whether the evaluator understood the document before any metric is presented. If they are wrong, every number that follows is suspect regardless of how carefully it was computed.

An early canary run exposed the failure mode: the main context produced a What Happened that invented characters not in the chapter, plot events that never occurred, and a fundamental misread of genre. The POV character's name was wrong. None of the summary was on the page. The metrics that followed were correct, but the report as a deliverable was not, because a reader who noticed the fabrication in the opening sections had no reason to trust the rest.

This is the same architectural failure as the Grammar/Spelling punt in v3: LLM-sourced content produced inline from the main context, with no fresh-eyes check against the actual prose. The fix is the same: delegate to a subagent reading the full chapter with a clean context window and a strict no-invention constraint.

### Why this is a routine step, not an inline task

The main context during Mode 1 has already: selected a genre, decided what to strip, received a strip verification, chosen a tokenizer architecture, and begun reasoning about thresholds. By the time it reaches the summary step, it is primed to write the summary the genre suggests rather than the summary the chapter delivers. A subagent with no accumulated context and an explicit directive to report only what is on the page cannot be primed the same way.

### The summary step

Before writing the report, the router MUST dispatch a Summary and Beat Sheet subagent. The subagent:

1. **Receives** the path to the original (NOT stripped) chapter file, the genre, and the instructions below.
2. **Reads** the full chapter in its entirety. Not a skim, not a title-inference, not a genre-pattern-fill.
3. **Produces** the What Happened summary (two to three paragraphs, flat professional tone, no craft commentary). Covers POV, setting, inciting action, key turns, ending state. Names only characters who actually appear on the page. Quotes language only if it appears in the chapter. If a character is unnamed, refers to them by role.
4. **Produces** the Beat Sheet: 5 to 10 numbered beats with approximate word-position ranges and one-line descriptions of what each beat does on the page. Names what happens, not what a genre convention would predict.
5. **Produces** 2 to 3 Structural Observations based on what was actually read. Flat tone.
6. **Returns** the output in a structured format the main context folds directly into the report.

### Hard constraints the subagent MUST observe

- **No invention.** If a character is not named on the page, do not name them. If an event did not happen on the page, do not describe it. If a language is not spoken on the page, do not claim it was. If a relationship is not established on the page, do not imply it.
- **No genre-pattern completion.** The chapter is what the chapter is. A horror chapter title and a desert setting do not mean the chapter is a kidnap-rescue, a buried-alive-and-survived, or any other pattern. Read what is there.
- **No craft commentary inside What Happened.** Observations about pacing, genre, or structure go in Structural Observations. What Happened describes what happened.
- **Uncertainty is allowed.** "An unnamed figure" is better than inventing a name. "Before dawn" is better than inventing a specific hour.

### Output format

The subagent returns:

```
## What Happened

[two to three paragraphs]

## Beat Sheet

1. **Beat name (word range).** Description.
2. **Beat name (word range).** Description.
...

### Structural Observations

- [observation 1]
- [observation 2]
- [observation 3]
```

The main context folds this output verbatim into the report's corresponding sections, appends the "Claude can make mistakes; use your best judgment" closing line after Structural Observations, and proceeds.

### Required disclosure

The report's Scope Note MUST include a Summary/Beat Sheet Pass line confirming the delegation:

> Summary/Beat Sheet pass: delegated to subagent, completed. POV: [name from subagent]. [N] beats identified.

If the subagent output is malformed (missing What Happened, missing Beat Sheet, fewer than 5 beats or more than 10, obvious invention flagged by spot-check), the router either re-dispatches with a corrective instruction or hard-stops and reports the failure. The report does not publish with a summary the main context wrote itself.

### Delegation rationale

The same three reasons as Strip Verification and the Grammar/Spelling Pass apply:

1. **Fresh eyes.** The subagent has no accumulated genre assumptions, threshold context, or pre-processing memory. It reads the chapter as a first-time reader would.
2. **Context isolation.** The main context receives a structured summary, not 5,000 words of prose it would have to read for itself. The judgment is what crosses the context boundary, not the raw material.
3. **Matches the existing pattern.** Strip Verification and Grammar/Spelling are already subagents. The Summary/Beat Sheet Pass mirrors their architecture. Mode 1 becomes a pipeline of (1) strip, (2) verify strip, (3) tokenizer, (4) grammar/spelling subagent, (5) summary/beat-sheet subagent, (6) assemble report.

The cost is a slightly slower Mode 1 run. The benefit is that the reader's first contact with the report is an accurate account of the document rather than a plausible-sounding confabulation. The article thesis is that opaque metrics corrode trust; producing reports that open with fabricated plot events would corrode trust faster than any opaque number ever could.

---

## Report Verification Pass: Final Check Before Delivery

After the Mode 1 report is fully assembled and before it is saved as the final deliverable, the router MUST run a Report Verification Pass. This is a targeted audit, not a re-analysis: the verifier checks that the claims in the report trace to either the chapter or the tokenizer/subagent outputs. It does not re-run the tokenizer. It does not rewrite the summary. It flags what does not match.

### Why this exists

Even with Strip Verification, the Grammar/Spelling Pass, and the Summary/Beat Sheet Pass all delegated to subagents, the main context still does one last thing: it assembles the report. Assembly is where transcription errors, context-window drift, and last-mile confabulation can slip in. The strip may have verified cleanly, the tokenizer may have run correctly, and the summary subagent may have returned an accurate block, and yet the final report can still contain a claim the main context hallucinated during assembly. Verification catches that.

### What the verifier checks

1. **Narrative claims in What Happened and Beat Sheet appear in the chapter.** Names, events, locations, quoted phrases, languages mentioned. Every specific claim is spot-checkable against the original chapter file.
2. **Metric values in the report match the tokenizer JSON output.** If the report says Style Score is 99.64%, the tokenizer output must say 99.64%. Numbers are not rounded differently, inverted, or transcribed with errors.
3. **Grammar/Spelling section claims match the subagent JSON.** Issue counts, score percentages, and tier classifications match what the subagent returned.
4. **Threshold comparisons are correct.** If a metric is reported as MET, the value must actually clear the threshold direction. "29 per 100 < 30 threshold = MET" is correct. "35 per 100 < 30 threshold = MET" is a transcription error the verifier catches.
5. **Scope Note disclosures are present.** Strip Verification, Grammar/Spelling Pass, and Summary/Beat Sheet Pass disclosure lines all appear with actual values filled in.
6. **No placeholder text remains.** No "[N] issues found" without an N, no "deferred to LLM pass," no "TBD," no "tokenizer cannot evaluate."
7. **Report language is final-verdict prose, not draft thought.** The report is a deliverable, not a scratchpad. The verifier flags any prose that reads like the writer's reasoning process leaked into the page. Specifically:
   - **Mid-sentence self-corrections.** Parentheticals that reverse or walk back the main clause ("the stddev is 7.97 which is above the baseline of 9 (wait, 7.97 is below 9.0)", "the score is 85% or actually closer to 88% once rounded"). Either the original claim or the correction is wrong; the final report carries only the correct claim.
   - **Visible uncertainty hedges.** "I think," "I believe," "it seems to me," "probably," "maybe," "perhaps" used in verdict or metric prose. The report presents what the tokenizer computed; hedging a number is incoherent.
   - **Thinking-out-loud interjections.** "wait," "actually," "hmm," "let me check," "hold on," "on second thought."
   - **Self-referential process notes.** "The evaluator noticed," "I had to recompute," "at first I thought," "after reconsidering." Process notes belong in the change log or the session summary, not the report.
   - **Unresolved compound verdicts.** "Met, but actually missed by one," "MET (barely)," "close to the threshold (unclear)." Either MET or MISSED.
   - **Em dashes, double hyphens, triple hyphens, or any dash variant beyond a single hyphen.** Per project-wide response formatting standard (see `CLAUDE.md`).

When the verifier finds a report-language violation, the tier is always FIX (not FAIL): rewrite the offending line as final-verdict prose preserving the numeric claim and threshold comparison. Example: "the stddev is 7.97 which is above the Sichel baseline of 9 in absolute terms (wait, 7.97 is below 9.0), suggesting the chapter could benefit from more contrast" becomes "the stddev is 7.97, below the Sichel (1974) fiction baseline of 9.0; the chapter could benefit from more contrast between short and long sentences."

Report-language checks apply to: BLUF bullets, Summary Report verdicts, per-section verdict lines, the "If you do one thing" line, Structural Observations, and any prose the main context wrote during assembly. They do NOT apply to: the What Happened summary (subagent-produced, already constrained), the Beat Sheet (subagent-produced), the tokenizer-sourced metric tables, or direct quotations from the chapter.

8. **Flagged-item tables are present and populated when flags exist.** Per `_standards.md` Scoring Rule #5 (v1.19), every category that detected at least one flag MUST include a flagged-items table with the actual text and paragraph number. The verifier checks: for each category whose flag count > 0 in the tokenizer or subagent JSON, a corresponding flagged-items table exists in the report section; the table has at least one row; each row includes both the flag text and its paragraph number; each row's text can be found in the original chapter via string search. If a section shows "Flagged sentences: N" without a table of N rows (or without disclosed truncation above 50), that is a FIX-tier discrepancy. If a flagged row cites text not present in the chapter, that is a FAIL-tier discrepancy.

9. **Character Dialogue Check section matches the subagent JSON (v1.20, extended v1.21).** If the Character Dialogue Consistency Pass ran, the verifier checks: every character in the subagent JSON appears in the report section; headline lines combine name, line count, and identity label as specified; fingerprint tables have one row per dimension; drift and attribution flag tables include text that can be string-searched in the chapter; characters below the 6-line floor are listed with their line count and the "insufficient sample" note; the Scope Note Character Dialogue Pass disclosure line is present with filled-in counts. **For POV characters with two speech modes (v1.21):** the verifier confirms each mode (`spoken`, `internal`) is rendered as its own block with its own headline, identity label, fingerprint table, and flag tables; that drift flags within a mode are present with chapter-verifiable text; that no flags exist for cross-mode shifts (since cross-mode drift is explicitly not flagged); that any mode below the per-mode 6-line floor is listed with the "insufficient sample for [mode]-mode fingerprint" note; and that the Scope Note disclosure names which mode(s) ran per POV character. Missing table or mismatched counts = FIX. Flagged line text not in the chapter = FAIL. A flag emitted for a cross-mode shift = FIX (the verifier directs the subagent's output to be re-rendered without that flag). If the pass ran N/A (no character cleared the floor), the verifier confirms the Scope Note N/A disclosure is present and the section reads the N/A statement without a per-character table.

10. **Non-Character Voice Registers section matches the marker map (v1.22).** If the marker map's `non_character_voice_spans` array is non-empty, the verifier checks: a *Non-Character Voice Registers* section exists in the report; the section header includes the "diagnostic, not scored" disclosure language; every span in the marker map is rendered with its `register_label`, `source_paragraph_start`/`source_paragraph_end`, `word_count`, and verbatim `text`; no Mode B span content appears in the stripped file (Mode B content must NOT leak back into scored prose); the Scope Note names every active Mode B `register_label` in addition to the per-POV speech modes from check #9. Missing section or missing spans = FIX. Mode B content found in the stripped file = FAIL (the strip pipeline did not honor the Mode B contract). If the marker map's `non_character_voice_spans` array is empty or absent, the section is omitted from the report and no check fires.

11. **Config metadata and strip log present (v1.22).** The verifier confirms: the active `pwa_config.json` path is recorded in the report's Scope Note (so a stranger forking this run knows which config produced it); the strip log JSON file exists alongside the marker map; the strip log's `rules_applied` array matches the active config's rule labels (every label in the config appears in the log, even if `matches: 0`); the strip log's `summary` line is present. Missing config path disclosure = FIX. Strip log absent or missing rule labels = FAIL.

### What the verifier does NOT do

- Does NOT re-run the tokenizer.
- Does NOT re-read the full chapter for comprehension (the Summary subagent already did that).
- Does NOT rescore or rethreshold any metric.
- Does NOT rewrite prose the main context produced (BLUF, Summary Report table, section verdicts). It checks those against their sources.

### The verification step

After report assembly, dispatch a Report Verification subagent. The subagent receives:

- The assembled report file path.
- The original chapter file path.
- The tokenizer JSON output.
- The Grammar/Spelling subagent JSON output.
- The Summary/Beat Sheet subagent block.
- The Character Dialogue Consistency subagent JSON output (v1.20, two-mode extended v1.21).
- The marker map JSON file path, if v1.21/v1.22 paired-delimiter pre-processing was used (so the verifier can confirm internal-mode fingerprint flag text traces to a span the marker map identified, and so the verifier can audit Mode B `non_character_voice_spans` against the report's *Non-Character Voice Registers* section).
- The active `pwa_config.json` file path (v1.22) — so the verifier can confirm config metadata is recorded in the Scope Note and that strip-log labels match config-rule labels.
- The strip log JSON file path (v1.22) — so the verifier can audit which rules fired, which rules had zero matches, and that the strip pipeline honored the active config.

The subagent returns one of three outcomes:

1. **PASS.** Every spot-check matched. The report is cleared for delivery. Return a short confirmation line.
2. **FIX.** One or more discrepancies found, each small enough to be a transcription error (number mismatch, missing disclosure line, wrong threshold direction in a single verdict). Return a list of discrepancies with the specific location and the corrected value. The main context applies each fix before delivery.
3. **FAIL.** A discrepancy is substantive (a narrative claim not in the chapter, a metric value that doesn't exist in the tokenizer output, a whole section missing). Return the failures and hard-stop. The router does not publish.

### Output format

```json
{
  "verdict": "PASS" | "FIX" | "FAIL",
  "narrative_checks": [
    { "claim": "POV: Maya", "found_in_chapter": true },
    { "claim": "confronts the rival", "found_in_chapter": true }
  ],
  "metric_checks": [
    { "report_value": "99.64%", "source_value": "99.64", "matches": true },
    { "report_value": "5.47", "source_value": "5.47", "matches": true }
  ],
  "threshold_direction_checks": [
    { "metric": "Passive Voice", "value": 5.47, "threshold": "< 30.0", "verdict_in_report": "MET", "correct": true }
  ],
  "disclosure_checks": {
    "strip_verification": true,
    "grammar_spelling_pass": true,
    "summary_beat_sheet_pass": true
  },
  "report_language_checks": [
    {
      "location": "BLUF, 'If you do one thing' bullet",
      "offense": "mid-sentence self-correction",
      "original": "the stddev is 7.97 which is above the baseline of 9 (wait, 7.97 is below 9.0)",
      "rewritten": "the stddev is 7.97, below the Sichel (1974) fiction baseline of 9.0"
    }
  ],
  "flagged_item_checks": [
    {
      "category": "Writing Style Check",
      "flag_count": 2,
      "table_present": true,
      "row_count": 2,
      "text_verified_in_chapter": true
    },
    {
      "category": "Emotion Tells",
      "flag_count": 17,
      "table_present": true,
      "row_count": 17,
      "text_verified_in_chapter": true
    }
  ],
  "character_dialogue_checks": {
    "pass_ran": true,
    "marker_map_present": true,
    "characters_in_json": ["Maya", "Rosa", "Stranger"],
    "characters_in_report": ["Maya", "Rosa", "Stranger"],
    "pov_characters_with_two_modes": ["Maya"],
    "modes_rendered_per_pov": {
      "Maya": ["spoken", "internal"]
    },
    "missing_headline_labels": [],
    "drift_flag_count_in_json": 1,
    "drift_flag_rows_in_report": 1,
    "attribution_flag_count_in_json": 1,
    "attribution_flag_rows_in_report": 1,
    "cross_mode_drift_flags_present": false,
    "flag_text_verified_in_chapter": true,
    "scope_note_disclosure_present": true,
    "scope_note_names_modes_per_pov": true
  },
  "non_character_voice_checks": {
    "marker_map_has_mode_b_spans": true,
    "section_present_in_report": true,
    "diagnostic_disclosure_language_present": true,
    "registers_in_marker_map": ["Omniscient Narrator"],
    "registers_in_report": ["Omniscient Narrator"],
    "registers_in_scope_note": ["Omniscient Narrator"],
    "spans_in_marker_map": 1,
    "spans_rendered_in_report": 1,
    "mode_b_content_absent_from_stripped": true
  },
  "config_and_strip_log_checks": {
    "config_path_in_scope_note": true,
    "active_config_path": "{{DOC_FOLDER}}\\pwa_config.json",
    "strip_log_present": true,
    "strip_log_labels_match_config_labels": true,
    "strip_log_summary_present": true
  },
  "discrepancies": []
}
```

### Required disclosure

The report's Scope Note MUST include a Report Verification line confirming the pass:

> Report verification: [PASS | FIX applied] on [date]. [N] narrative claims, [M] metric values, [K] threshold verdicts spot-checked.

The Report Verification Pass does not appear in the report as its own section; its sole artifact is the Scope Note disclosure line and, if any fixes were applied, a one-line note in the deliverable's metadata ("N transcription fixes applied during verification").

### Delegation rationale

This pass exists because the main context is the only part of the pipeline that touches every other output. It assembles. Assembly is where slippage happens. A subagent doing a targeted spot-check against all the source artifacts closes the last gap without repeating the expensive work that produced those artifacts.

---

## Character Dialogue Consistency Pass: Subagent-Delegated Per-Character Voice Analysis

Per-character voice consistency is the second chapter-scale check that pattern-matching software cannot do. A tokenizer can count tags, classify verbs, and measure adverb-pairing, but it cannot tell you whether Maya sounds like Maya across 20 lines of dialogue, or whether a line attributed to Maya reads like Rosa would say it. That is language work. The routine delegates it to a subagent, mirroring the Summary and Grammar/Spelling architectures.

Scope is chapter-internal only. This pass does NOT compare the chapter against prior chapters, a character profile, or MCP canon. It measures whether each character's voice holds together inside the current chapter and whether tagged lines match the fingerprint the character established elsewhere in that same chapter. Cross-chapter voice drift and canon-consistency are out of scope by design; the only input this pass receives is the chapter (plus, when available, the marker map identifying internal-mode spans per the v1.21 pre-processing rule).

### Speech modes: spoken and internal (v1.21)

Dialogue is not only quoted speech. When a chapter uses paired-delimiter markers for interiority (e.g., `[[THOUGHT: ... ]]`) and the pre-processing rule has retained that prose while stripping the markers, the retained spans ARE voice data — the POV character speaking to themselves. The Character Dialogue Consistency pass treats these as a second speech mode.

For the POV character (or characters, if a chapter has multiple POVs), the subagent builds **two fingerprints**:

- **Spoken fingerprint**: built from quoted dialogue lines attributed to the character.
- **Internal fingerprint**: built from the marker-map-identified internal-mode spans.

The two fingerprints are reported side by side in the report. Drift within each mode is flagged normally. **Drift between the two modes is NOT flagged**: the natural gap between how a person speaks and how they think is expected, and flagging it would produce false positives on every POV chapter. What IS flagged is drift within the internal mode (a POV character whose interior voice shifts mid-chapter from, say, sardonic Gen-Z Latina to a formal older register without narrative cause) and within the spoken mode (a POV character whose spoken voice destabilizes).

The 6-line sample floor applies per mode. If the POV character has 8 spoken lines and 3 internal-mode spans, spoken clears the floor and gets a fingerprint; internal does not and is listed with the "insufficient sample for internal-mode fingerprint" note. Non-POV characters have only a spoken mode.

Attribution mismatch in the internal mode is rare but possible: if the POV character has clearly established an internal fingerprint and a single internal-mode span reads as someone else's interiority, the subagent flags it. This catches POV slippage (author briefly inhabiting a different consciousness inside a POV chapter) which is a real craft failure mode.

If no marker map is present (chapter without paired-delimiter interiority, or author opted for the strip-everything option), the subagent runs with spoken mode only. The report's Scope Note discloses which mode(s) ran per character.

### Why this is a routine step, not a tokenizer field

Voice fingerprint detection requires judgment about diction register, sentence-structure patterns, and idiolect. A regex can count contractions, but cannot judge whether the character who uses them constantly just delivered a line without any. The subagent reads every line of dialogue attributable to each speaker, builds a fingerprint across five dimensions, and reports drift or mismatch against that fingerprint. This is work only a language-model reader can do.

### Sample floor

Per-character floor: **6 lines of dialogue minimum**. Below this floor, the character is listed in the report as "insufficient sample" and excluded from the scored denominator. The floor is a pragmatic chapter-scale compromise, not a stylometric guarantee (authorship-attribution research typically uses 500-word minimums; 6 dialogue lines is the smallest count at which recognizable patterns in diction, sentence length, and tics can hold up to inspection).

If no character in the chapter reaches the floor, the whole row reads N/A with the disclosure:

> No character reaches the 6-line dialogue floor in this chapter; voice-fingerprint analysis needs more lines per speaker to be meaningful.

And row 23 is exempt from the goals denominator.

### Fingerprint dimensions

For each character who clears the floor, the subagent builds a fingerprint across an **identity label** plus five dimensions:

0. **Identity label.** A short phrase naming what the voice IS, not just its component parts. Two to five tags, comma-separated, drawn from what the dialogue itself establishes: generation (Gen Z, millennial, Gen X, boomer, youth, elder), cultural background where visible in speech (Latina, Southern US, Appalachian, British, Australian, Mexican-American, etc.), register stance (formal, street, academic, corporate, military, clerical), and one defining attitude or role where it reads clearly (world-weary, performatively chipper, sardonic, deferential, paternal, predatory, traumatized). Example: "Maya: Gen Z, sardonic, terse, code-switches." "Rosa: elder, formal, measured, rarely contracts." The label is the evaluator's read of who is speaking, based strictly on how they speak in this chapter. It is not a character bio and is not sourced from outside the chapter. If the chapter does not give enough signal for a dimension (e.g., generation unclear), omit that tag rather than guess.

1. **Sentence length distribution.** Short-clipped (avg <= 8 words), medium (9-15), long-rolling (16+), or mixed (no clear center).
2. **Diction register.** Formal, informal, vulgar, archaic, technical, or code-switched (mixes registers deliberately). Note any consistent linguistic tics (honorifics, profanity frequency, slang markers).
3. **Sentence structure.** Dominant type: declaratives, questions, imperatives, fragments, or mixed. Note if one type is conspicuously absent.
4. **Signature markers.** Recurring phrases, verbal tics, code-switching into another language, unusual punctuation habits (em-dash breaks, ellipsis trailing, all caps for emphasis). Note what is recurrent, not one-offs.
5. **Contractions use.** Always contracts (casual), never contracts (formal/foreign/archaic), or inconsistent (flag as voice instability on its own).

The fingerprint is summarized in the report with the identity label as its headline and the five dimensions as evidence. Drift and mismatch flags cite the specific dimensions that moved, with the identity label as the frame ("Maya: Gen Z, sardonic, terse — drift at paragraph 34 where line reads as formal, long, uncontracted, matching an older or academic register the character has not established elsewhere").

### The analysis step

After strip verification passes, the Grammar/Spelling subagent completes, and the Summary/Beat Sheet subagent completes, the router dispatches a Character Dialogue Consistency subagent. The subagent:

1. **Receives** the path to the verified stripped prose file, the path to the marker map file (if present; v1.21), the genre, and the Fingerprint dimensions specification from this section.
2. **Reads** the full stripped prose and, if provided, the marker map identifying internal-mode spans per POV character.
3. **Attributes** every line of dialogue to a speaker using explicit tags ("Maya said"), contextual cues (response to a named addressee, paragraph structure, the speaker being the POV character), and proper-noun tracking across the chapter. Internal-mode spans from the marker map are attributed to the specified POV character as internal speech mode. If a line is genuinely unattributable, count it as "unattributed" and exclude it from every character's line count but note the total at the report's end.
4. **Counts** dialogue lines per character per mode. Any character-mode pair below 6 lines is listed with its count and the "insufficient sample" note; no fingerprint is built for that pair. A POV character may clear the floor in spoken mode only, internal mode only, both, or neither.
5. **Builds** a fingerprint per character-mode pair that clears the floor, across all five dimensions plus the identity label. For POV characters with both modes cleared, builds two fingerprints side by side.
6. **Scans** each character-mode pair's dialogue for **drift**: any line where the fingerprint established within that mode shifts without narrative cause (register jump, sudden formalization or coarsening, sentence-length outlier, loss of a signature marker, contraction habit break). Narrative cause can be drunk, panicked, lying, performing, praying, addressing a superior, etc.; the subagent notes suspected cause if visible in context. Cross-mode shifts within a single POV character (spoken vs. internal) are NOT flagged as drift.
7. **Scans** tagged dialogue for **attribution mismatch**: any spoken line whose content, register, or structure matches a different character's fingerprint more closely than the tagged speaker's. The subagent names the other character and the specific dimensions where the line fits their fingerprint better. Additionally, scans internal-mode spans for POV-slip mismatch: an internal-mode span that reads as a non-POV character's interiority.
8. **Returns** a JSON blob in the following shape:

```json
{
  "character_dialogue_consistency": {
    "total_dialogue_lines": 87,
    "unattributed_lines": 2,
    "characters": [
      {
        "name": "Maya",
        "is_pov": true,
        "modes": {
          "spoken": {
            "line_count": 24,
            "sample_status": "cleared",
            "fingerprint": {
              "identity_label": "Gen Z, sardonic, terse, code-switches",
              "sentence_length": "short-clipped (avg 6 words)",
              "diction_register": "informal, occasional profanity, code-switch when frustrated",
              "sentence_structure": "declaratives and fragments dominant; questions rare",
              "signature_markers": "trailing ellipsis, rhetorical dismissals",
              "contractions": "always contracts"
            },
            "drift_flags": [
              {
                "paragraph": 34,
                "text": "I had not anticipated that she would pursue the matter to its logical conclusion.",
                "shifted_from": "short-clipped, informal, always contracts",
                "shifted_to": "long, formal, no contractions",
                "suspected_cause": "none visible in context",
                "tier": "review"
              }
            ],
            "attribution_flags": []
          },
          "internal": {
            "line_count": 11,
            "sample_status": "cleared",
            "fingerprint": {
              "identity_label": "Gen Z, sardonic, analytical, second-person self-address",
              "sentence_length": "medium (avg 13 words)",
              "diction_register": "informal to dryly observational, occasional profanity",
              "sentence_structure": "declaratives and sentence fragments; rhetorical questions common",
              "signature_markers": "self-directed 'you,' catalog metaphors",
              "contractions": "always contracts"
            },
            "drift_flags": [],
            "attribution_flags": []
          }
        }
      },
      {
        "name": "Rosa",
        "is_pov": false,
        "modes": {
          "spoken": {
            "line_count": 18,
            "sample_status": "cleared",
            "fingerprint": {
              "identity_label": "elder, formal, measured, rarely contracts",
              "sentence_length": "medium (avg 12 words)",
              "diction_register": "formal, measured, no profanity",
              "sentence_structure": "declaratives and questions balanced",
              "signature_markers": "hedges ('I suppose,' 'it would seem'), full sentences without fragments",
              "contractions": "rarely contracts"
            },
            "drift_flags": [],
            "attribution_flags": [
              {
                "paragraph": 51,
                "text": "Come on, I told you already.",
                "matches_character_better": "Maya",
                "dimensions_matched": "diction register (informal, clipped), contractions (always contracts)",
                "tier": "review"
              }
            ]
          }
        }
      },
      {
        "name": "Stranger",
        "is_pov": false,
        "modes": {
          "spoken": {
            "line_count": 3,
            "sample_status": "insufficient sample",
            "fingerprint": null,
            "drift_flags": [],
            "attribution_flags": []
          }
        }
      }
    ],
    "goal_verdict": "MISSED (2 flags across characters clearing the floor)",
    "flag_count_total": 2
  }
}
```

### Scoring rule

Zero drift flags AND zero attribution flags across every character who clears the 6-line floor = goal achieved. Any flag = goal missed, but the report presents the flag as judgment-sensitive: the author reviews each flag and decides whether it is narratively justified (a character who is drunk, panicked, lying, or performing can legitimately depart from their fingerprint) or a genuine voice slip. The category appears in the BLUF judgment-flags list when any flag is emitted.

The scoring rule is deliberately conservative. The goal exists to surface every voice shift for author review, not to penalize shifts that do narrative work. An author who reviews the flags and accepts them all still "missed" the goal by the threshold but has done the work the check exists to require.

### Integration into Mode 1

The Mode 1 report's new **Character Dialogue Check** section (positioned after Dialogue Tags Check) uses the subagent's JSON output directly. For each character clearing the floor, the section renders in this order:

1. **Headline line**: `**[Name]** ([line count] lines) - [identity_label]`. Example: `**Maya** (24 lines) - Gen Z, sardonic, terse, code-switches`.
2. **Fingerprint table** (one row per dimension: Sentence length, Diction register, Sentence structure, Signature markers, Contractions), so a reader can see the evidence behind the identity label.
3. **Drift flags** (if any): a table with columns for paragraph, line text, shifted-from, shifted-to, suspected cause.
4. **Attribution flags** (if any): a table with columns for paragraph, line text, matches-character-better, dimensions-matched.

Characters below the floor are listed with their line count and the "insufficient sample" note. Unattributed line count is reported at the section's close. The section closes with the "Claude can make mistakes; use your best judgment" note mirroring the Beat Sheet's closing note.

### Integration into Mode 3

Mode 3 does NOT auto-fix dialogue consistency flags. Every flag is prompt-tier: the author reviews the flagged line and either accepts the flag (rewrites the line to match the fingerprint) or rejects it (narrative cause justifies the shift). Mode 3 surfaces each flag via AskUserQuestion with the flagged line, the fingerprint it shifted from, and the suspected cause; applies accepted rewrites to the working copy; logs rejected flags in the change log under "Voice shifts reviewed and retained."

### Required disclosure

The report's Scope Note MUST include a Character Dialogue Pass line confirming the delegation:

> Character dialogue pass: delegated to subagent, completed. [N] characters analyzed, [M] below sample floor, [K] drift flags, [L] attribution flags.

If no character cleared the floor:

> Character dialogue pass: delegated to subagent, N/A (no character reached 6-line floor).

### Delegation rationale

This is language work. A regex cannot judge whether a line of dialogue matches a character's established register. A language-model reader can, given the chapter and the fingerprint specification. The subagent has no prior-chapter context and no canon access by design, so its reading is grounded in what the chapter itself establishes; the check surfaces internal consistency failures, not cross-chapter drift. That is the right scope for a chapter-scale writing evaluation.

---

## Detection Heuristics

These are the rules each specialist prompt uses. They are intentionally mechanical.

### Grammar
Flag: missing determiners, missing commas after introductory phrases, confused prepositions, homophone confusion (its/it's, their/there), missing hyphens in compound modifiers (e.g., "proof of concept" used as adjective), punctuation errors, subject/verb disagreement.

### Spelling

The evaluator is not a dumb dictionary lookup. It is a language model that can read multiple languages, recognize proper nouns in context, and verify unfamiliar terms via web search. Use those capabilities before flagging anything.

**Recognition order (apply in this sequence before flagging a token):**

1. **English dictionary check.** If the token is a standard English word, not a flag and not a count against the score.
2. **Multi-language recognition.** If the token is a word in a language the evaluator can read (Spanish, French, German, Italian, Latin, etc.) and is used correctly in context, not a flag and not a count against the score. The evaluator must not treat "narcocorrido," "compadre," "Schadenfreude," "in medias res," etc. as spelling errors. Multilingual prose is prose, not an error state.
3. **Proper noun recognition from context.** If the token is capitalized and context makes it clear it is a name (a person, place, band, brand, street, deity, etc.), not a flag and not a count against the score. Use the rest of the chapter, any external canon tools the author's project provides, or pattern recognition ("Smith said" tells you Smith is a name).
4. **Coined or domain-specific terms.** If the token is not in any dictionary but is plausibly a coined term (e.g., "pwned," invented slang, technical jargon), attempt a web search to verify. If the search confirms it exists and is used correctly, not a flag and not a count.
5. **Genuine unknowns.** Only after steps 1-4 fail: flag the token in an "Unknown words" table with location and let the author judge. Do NOT count these against the Spelling Score automatically. They are flagged for review, not errors by default.
6. **Genuine misuses.** If a real word is used incorrectly in context (wrong sense, wrong language for the intended meaning, typo that happens to produce another real word), flag it as a misuse and count it against the Spelling Score.

**What counts against the Spelling Score:**

- True typos (e.g., "teh" for "the").
- Clear misspellings of English words.
- Confirmed misuse of a real word (wrong sense in context).

**What does NOT count against the Spelling Score:**

- Foreign-language words used correctly.
- Proper nouns recognized in context or verifiable via canon/web.
- Coined or jargon terms verified via web search.
- Any token the evaluator flags for author review without confirming it is an error.

**Why this matters.** The whole premise of this tool is that the evaluator has real intelligence behind it. An evaluator that can read Spanish but still flags Spanish as spelling errors is reproducing exactly the failure the tool exists to replace. If the evaluator does not use what it knows, it is not better than a dictionary lookup and the Spelling Score is dishonest.

### Style

**Style Score formula**: For each sentence, determine whether it contains at least one match against any pattern in the list below. Style Score = (sentences with zero matches) / (total sentences), as a percentage. One sentence with three matches counts as one flagged sentence, not three. Threshold is >= 80%. The formula is explicit so "% of sentences free of style flags" is no longer ambiguous.

Flag phrases that can be simplified for readability. Core patterns:

- "the kind of" -> "the"
- "a kind of" -> "a"
- "the fact that" -> "that"
- "a particular kind of" -> "a particular"
- "a different kind of" -> "a different"
- "was learning that" -> "learned that"
- "was beginning to X" -> "was X-ing" or past tense
- "began to X" -> simple past "X-ed"
- "started to X" -> "X-ed"
- "made the decision to X" -> "decided to X"
- "managed to X" -> past tense "X-ed"
- "found himself/herself X-ing" -> simple past
- "indicate/indicates" -> "show/shows"
- "demonstrate" -> "show"
- "assistance" -> "help"
- "methodology" -> "method"
- "initiated" -> "started"
- "terminated" -> "ended"
- "procured" -> "bought"
- "relocated" -> "moved"
- "anticipated" -> "expected"
- "acquired" -> "gained"
- "objective" -> "aim"
- "remove redundant 'that'" after reporting verbs (said, told, knew, realized, reinforces, emphasizes, reveals, establishes)
- "in the corner of the X" -> "in the X's corner"
- "in the presence of X" -> "in X's presence"
- "was intended to be" -> "was"
- "was either" -> "was"
- "didn't say anything" -> "said nothing"
- "had no idea" -> flag as informal
- "very [adj]" -> try a stronger adjective
- "very [adv]" -> drop the "very"
- "really bad" / "really [X]" -> try a stronger word
- "wishful thinking" and similar cliches -> avoid cliches
- "Can you bring these together for clarity?" for phrases like "whether you're ready or not"
- "Can you just use the verb?" for constructions like "contrasting sharply with"
- "Possibly redundant expression" for phrases like "hear the sound of"

**Flagged items (Style)**. For each flagged sentence, emit:
- `text`: the full sentence as it appears in the stripped prose.
- `paragraph`: 1-indexed paragraph number.
- `pattern`: the pattern that matched (e.g., `"acquired -> gained"`).
- `matched_phrase`: the substring of the sentence that triggered the match (e.g., `"acquired"`).
- `suggestion`: the right-hand side of the pattern (e.g., `"gained"`).

If a sentence matches more than one pattern, emit one flagged item per pattern, all referencing the same sentence. The Style Score numerator still counts that sentence once (per the formula above); the flagged_items array is diagnostic.

### Passive Voice
Count "to be" + past participle constructions that lack a clear agent. Express as passives per 100 sentences.

**Flagged items (Passive Voice)**. For each detected passive construction, emit:
- `text`: the full sentence containing the construction.
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"passive-construction"`.
- `matched_phrase`: the to-be-verb + past-participle span (e.g., `"was taken"`).

### Emotion Tells (filter-word constructions)

Emotion Tells are counted mechanically as filter-word constructions: a pronoun or noun subject, followed by a *filter verb*, followed by an emotion or sensation word. These are the constructions the "show, don't tell" principle targets.

**Definition**: For each sentence, count it as containing an emotion tell if it matches any construction of the form:

`[he | she | they | I | we | PROPER_NOUN] + [filter_verb] + [emotion_word | filter_complement]`

Emotion Tells rate = (sentences containing at least one emotion-tell construction) / (total sentences), as a percentage.

**Filter verbs (default list, editable via user config)**:
felt, feels, feeling, was, were, is, am, are, seemed, looked, watched, heard, saw, noticed, noted, realized, thought, wondered, decided, knew, understood, considered, believed, assumed, pondered, perceived.

**Emotion / sensation words (default list, editable via user config)**:
sad, happy, angry, afraid, scared, terrified, nervous, anxious, excited, relieved, embarrassed, ashamed, guilty, proud, jealous, confused, surprised, shocked, disgusted, tired, exhausted, bored, frustrated, furious, calm, content, lonely, worried, hopeful, hopeless, desperate, helpless, overwhelmed, numb, empty, hollow, cold, hot, dizzy, sick, weak.

**Rationale**: This replaces the legacy "explicit statements of emotion" judgment call with an explicit tokenizable rule grounded in the publishing-industry "filter words" literature (Anne R. Allen, Janice Hardy, Kathy Steinemann, Louise Harnby). The lists are deliberately narrow defaults; an author whose voice uses "considered" or "realized" intentionally as tempo markers can shorten the filter-verb list via user config.

**Flagged items (Emotion Tells)**. For each sentence containing an emotion-tell construction, emit:
- `text`: the full sentence.
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"filter-construction"`.
- `filter_verb`: the matched filter verb (e.g., `"felt"`).
- `emotion_word`: the matched emotion or sensation word (e.g., `"afraid"`).
- `subject`: the subject of the construction (e.g., `"she"`).

### Engagement Score (removed)

Engagement Score was removed in v1.14. The v1.13 definition ("a composite that rewards varied vocabulary, active verbs, and sensory grounding") had no formula behind it, which is exactly the opacity the routine exists to correct. A single black-box composite score for "engagement" is not measurable; if the underlying metrics (passive voice, sentence variety, glue index, emotion tells, slow pacing) are in range, the prose engages. A standalone Engagement Score that ignores the underlying metrics is theater.

### Weak Adverbs

Count -ly adverbs that are adjacent to (immediately before or after) a verb from the dialogue-tag list OR from the weak-verb list below. Adverbs attached to other verbs are not counted. Report per 1,000 words and list the most-frequent offenders.

**Weak verbs (default list, editable via user config)**:
said, asked, replied, answered, whispered, shouted, cried, gasped, sighed, went, walked, ran, looked, saw, heard, was, were, felt, moved, turned, reached, opened, closed, stood, sat, came, got, put, took.

**-ly noun exclusion (v1.22)**. Many English nouns end in -ly without being adverbs (assembly, family, supply, reply, rally, ally, anomaly, monopoly, bully, jolly, holly, etc.). These tokens MUST NOT be counted as weak adverbs. The detector consults `pwa_config.json:weak_adverb_noun_exclusions` (case-insensitive token match against the lowercased token, ignoring trailing punctuation) and skips any token that appears in the list. The seed config ships with the obvious common cases; authors append more as their manuscripts surface them. Optionally, if a lightweight POS tagger is available, the detector may additionally require the token to be tagged as RB (adverb) before counting; the noun-exclusion list is the minimum guarantee even without POS tagging. Surfaced during a canary run where `assembly came` (assembly = noun, came = adjacent verb) was incorrectly flagged.

**Rationale**: The v1.13 definition included "-ly adverbs that substitute for a stronger verb," which was a judgment call. The explicit weak-verb list converts that into a mechanical check. Adverbs attached to strong, specific verbs ("he moved cautiously" vs. "he crept") are not flagged here because the strong verb is doing work; the adverb is texture, not a crutch. Authors who want stricter or looser enforcement edit the weak-verb list directly.

**Flagged items (Weak Adverbs)**. For each flagged adverb/verb pair, emit:
- `text`: the full sentence containing the pair.
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"weak-adverb-adjacent-to-weak-verb"` or `"weak-adverb-adjacent-to-dialogue-tag"`.
- `adverb`: the -ly adverb (e.g., `"quietly"`).
- `verb`: the adjacent weak or tag verb (e.g., `"said"`).
- `matched_phrase`: the adverb + verb span as it appears (e.g., `"said quietly"`).

### Sentence Length / Variety

Compute average sentence length in words. Very long = > 30 words.

**Sentence Variety formula**: Variety = clamp(stddev_of_sentence_lengths / 2.0, 0, 10). A standard deviation of 10 words maps to a Variety score of 5.0; a standard deviation of 18 words maps to 9.0. The threshold of >= 5.0 therefore corresponds to a standard deviation of at least 10 words, which matches the empirical range for published fiction (Sichel 1974; published fiction typically shows sentence-length standard deviations of 9+, vs. 6-8 for nonfiction).

**Rationale**: The v1.13 definition specified "mapped to a 0-10 scale" but left the mapping function unstated. The divide-by-2.0 mapping makes the scale explicit and grounds the 5.0 threshold in published-fiction measurement rather than a guess.

**Flagged items (Very Long Sentences)**. For each sentence with > 30 words, emit:
- `text`: the full sentence.
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"very-long-sentence"`.
- `word_count`: integer word count of the sentence.

### Complex Paragraphs
A paragraph is complex if its average sentence length > 20 words AND it contains > 3 sentences.

**Flagged items (Complex Paragraphs)**. For each flagged paragraph, emit:
- `text`: the first 25 words of the paragraph followed by an ellipsis (`...`).
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"complex-paragraph"`.
- `avg_sentence_length`: average words per sentence in the paragraph, rounded to one decimal.
- `sentence_count`: integer sentence count in the paragraph.

### Glue Index
Glue words = "of, in, to, for, and, the, a, is, was, it, that, this, with, as, but, on, at, by" plus auxiliary verbs. Glue Index = glue word count / total word count.

### Conjunction Starts / -ing Starts
Count sentences whose first token is a coordinating conjunction (And, But, So, Or, Yet) or an -ing participle. Express as % of total sentences.

**Flagged items (Conjunction Starts)**. For each sentence opening with a coordinating conjunction, emit:
- `text`: the full sentence.
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"conjunction-start"`.
- `opener`: the first word (e.g., `"But"`).

**Flagged items (-ing Starts)**. For each sentence opening with an -ing participle, emit:
- `text`: the full sentence.
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"ing-start"`.
- `opener`: the first word (e.g., `"Walking"`).

**Proper noun and non-participle exclusion (v1.22)**. Capitalized words ending in letter sequences that look -ing-adjacent (Harrington, Inferior, Practitioner) are not always present participles. The detector MUST require the opener to actually be a present participle before counting. The minimum check: the token MUST end in the literal three letters `ing` (lowercased), AND the LITERAL lowercase form of the token MUST appear elsewhere in the chapter as written (not "the result of lowercasing every other token in the chapter" — that is a tautology because the capitalized opener itself lowercases into the inventory). If the literal-lowercase form never appears as written, the token is treated as a proper noun and skipped. The detector additionally consults `pwa_config.json:ing_starts_proper_noun_exclusions` (case-insensitive token match) and skips any token in the list. Authors populate the list with manuscript-specific character surnames or capitalized non-participle words, and the routine seed ships with universal English indefinite-pronoun and common-noun -ing words (nothing, something, anything, everything, morning, evening, ceiling, ring, spring, string, thing, king, wing, during, according) so authors do not have to populate them per manuscript.

### Slow Pacing

Slow Pacing = % of paragraphs that meet ALL THREE of the following conditions:

1. The paragraph contains zero dialogue (no quoted speech anywhere in the paragraph).
2. The paragraph contains zero action verbs from the action-verb list below (case-insensitive, any inflection).
3. The paragraph is > 50 words long (short paragraphs are exempt; they cannot be "slow" in a way that harms pacing regardless of content).

**Action verbs (default list, editable via user config)**:
ran, walked, jumped, grabbed, pulled, pushed, threw, opened, closed, slammed, turned, reached, stood, sat, fell, crossed, entered, left, shouted, whispered, said, asked, replied, answered, stepped, climbed, drove, rode, flew, swam, dove, lunged, struck, hit, kicked, shoved, caught, released, dropped, lifted, carried, placed, set, took, put, handed, threw, tossed, rolled, crawled, knelt, rose, bent, leaned, turned, spun, pivoted, moved, shifted, slipped, crept, raced, sprinted, dashed, charged, fled, chased, followed, led.

**Rationale**: The v1.13 definition ("passages dominated by exposition, backstory, or interior thought with no action, dialogue, or sensory beats") was a judgment call. The three-condition rule is mechanical and matches how pacing research (Bookshaper, Payton Hayes, etc.) describes slow sections: long paragraphs of interior monologue with no dialogue and no physical motion. This heuristic will over-flag pure reflective passages and under-flag technically-active-but-actually-slow prose; that is the accepted tradeoff for mechanical measurability. The action-verb list is deliberately broad so any scene with physical motion registers as active.

**Flagged items (Slow Pacing)**. For each paragraph meeting all three conditions, emit:
- `text`: the first 25 words of the paragraph followed by an ellipsis (`...`).
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"slow-pacing"`.
- `word_count`: integer word count of the paragraph.

### Consistency
Quote consistency: do all quotation marks use the same style (curly vs. straight, single vs. double)?

Acronym consistency: genre-branched.

**Fiction genres (F1-F5)**: The check is styling-consistency only. For each distinct acronym or initialism (ALL-CAPS tokens of length 2+, excluding sentence-initial pronouns and common all-caps words like "I", "OK"), collapse variants to a base form (FBI / F.B.I. / F B I all collapse to FBI), then verify the styling is consistent across every occurrence. Flag any acronym that appears in more than one styling within the same document. Pass = 100% consistent styling. **No first-use-definition requirement is applied to fiction**, per CMOS Shop Talk's "Abbreviations in Fiction" (2020): "there's no need to spell out an unfamiliar abbreviation immediately upon first occurrence, and explaining an abbreviation by putting the spelled-out version in parentheses will not often be a good idea." Fiction introduces acronyms through context or dialogue, not via parenthetical glosses.

**Typographic-emphasis exclusion (v1.22)**. ALL-CAPS sequences in fiction are sometimes typographic emphasis rather than acronyms — book/franchise titles styled in caps (`PALE HORSE`), in-world organization names, stylistic shouts, or non-character voice tags that survived stripping. The detector MUST consult `pwa_config.json:acronym_emphasis_exclusions` (case-insensitive substring match against the candidate token) and skip any token that appears in the list. The exclusion list is editable per manuscript; authors append entries as canaries surface them. Default empty. Surfaced during a canary run where paired-delimiter content that escaped Mode B stripping in a pre-v1.22 run, and in-world organization names styled as typographic emphasis in narrative prose, were both flagged as acronyms with inconsistent styling.

**Non-fiction genres (N1-N5)**: The check is styling-consistency AND first-use definition. For each distinct acronym, verify (a) styling is consistent across every occurrence, and (b) the first occurrence either spells out the full form in parentheses on first use (e.g., "Chicago Manual of Style (CMOS)") OR the full form appears within the preceding sentence. Exempt list (bare use accepted without definition): FBI, CIA, NASA, DNA, USA, UK, EU, UN, NATO, AM, PM, CEO, CFO, CTO, PhD, MD, JD, BA, MA, BS, MS, UFO, GPS, HTML, CSS, HTTP, HTTPS, URL, API, AI, IT, TV, DVD, CD, PDF, FAQ, OK, ASAP, DIY, FYI, RSVP. This list is editable via user config.

**Universal genre (U)**: Defaults to fiction rule (styling-only). If the document is clearly non-fiction (detected by the presence of headings, references, or a Custom genre-blend that weights N-profiles > 0.5), escalate to the non-fiction rule.

**Custom genre (C)**: Inherits the rule of whichever parent profiles carry the higher blend weight. If fiction profiles > 50%, apply the fiction rule; otherwise apply the non-fiction rule.

**Rationale**: Trade fiction does not follow the technical-writing "define at first use" convention. Parenthetical glosses read as academic and break narrative voice. The editorial test in fiction is consistency-of-form across the manuscript, not first-use-definition. This branching prevents the routine from penalizing fiction for following its own convention while preserving the stricter rule where it actually applies (articles, essays, technical prose, academic work).

### Long Repeated Phrases

Two parameters control detection; both are editable via user config.

**Defaults**:
- Minimum phrase length: **5 words**
- Minimum occurrences: **3**

**Metric**: Count of distinct phrases that are at least 5 words long AND appear at least 3 times in the document. Threshold: < 3 such phrases.

**Why 5/3 and not 3/2 (the PWA inheritance)**: At 3-word windows, English has massive unavoidable structural overlap ("he said to," "one of the," "she looked at") that flags as repetition but is not stylistic. Corpus-linguistics research (Biber, Conrad, and Cortes 2004) defines "lexical bundles" as recurrent 4+ word sequences; stylistic-tic detection in authorship work (Burrows, Hoover) typically uses 4-5 word minimums. At 5+ words, repetition is almost always a verbal tic or habitual phrasing. At 3 occurrences, coincidence is ruled out and a pattern is the simpler explanation. An early canary run demonstrated why: 139 extra 3-word occurrences in a 4,500-word chapter is noise, not signal.

**Tiered output**: The report emits two tables.

1. **Flagged phrases** (the scored metric): all distinct phrases meeting both floors, sorted by (length x occurrences) descending. If the count is >= 3, the goal is missed.
2. **Diagnostic top-20** (informational, not scored): the top 20 repeated 4+ word phrases regardless of occurrence count, sorted the same way. Lets the author see near-patterns that did not cross the threshold without those near-patterns affecting the score.

**Flagged items (Long Repeated Phrases)**. For each flagged phrase, emit:
- `text`: the phrase verbatim (the entire repeated span).
- `paragraphs`: an array of 1-indexed paragraph numbers where each occurrence appears.
- `rule`: `"repeated-phrase"`.
- `length`: integer word count of the phrase.
- `occurrences`: integer count of occurrences in the document.

The diagnostic top-20 uses the same schema under a sibling key `long_repeated_phrases.diagnostic_top_20`.

**Genre sensitivity**: Universal by default (no per-genre matrix values). Repetition-as-voice is an author choice, not a genre expectation, so it does not belong in the genre threshold matrix. Authors with liturgical, ritual, or refrain-driven voices override the occurrence minimum via user config rather than the genre matrix.

### Dialogue Tags

The tag family splits into four metrics: tag-rate, voice consistency, performance-tag rate, and adverb pairing. Voice consistency and performance-tag rate together replaced the legacy "Unusual Dialogue Tags" metric in v1.12. The old metric (anything not "said" or "asked") confused voice drift with genre-native verb choice and scored both identically; the two-metric replacement measures them separately.

**Sample-size floor.** If total tag count < 15, Voice Consistency and Performance Tag Rate both read N/A with the disclosure:

> You have fewer than 15 tags, this is not enough for evaluation.

Both rows are exempt from the goals denominator when N/A. The floor applies to voice/performance only; Dialogue Tag Rate and Dialogue Tags with Adverbs still score at any count.

**Dialogue Tag Rate.** % of dialogue lines that have an accompanying tag. No sample floor; a dialogue-light chapter is still scored.

**Voice Consistency.** Count tag verbs. Dominant tag verb = the most-frequent tag verb in the chapter. Voice Consistency = (occurrences of dominant tag) / (total tags), as a percentage. Threshold: >= 50% across all genres (this measures the author's own discipline, not genre convention). Misses indicate tag vocabulary is drifting — the evaluator is reaching for novelty rather than committing to a sound.

**Performance Tag Rate.** Tags are classified as either *invisible* or *performance* per the editable lists below. Performance Tag Rate = (performance-tag occurrences) / (total tags), as a percentage. Threshold is genre-sensitive (see Genre Threshold Matrix). Misses indicate tags are doing emotion-work that prose and action beats should be doing.

**Empirical grounding.** The numeric anchors for Voice Consistency and Performance Tag Rate are drawn from Elliott Slaughter's 2020 empirical dialogue-tag analysis of four published novels: *The Lord of the Rings* (Tolkien, fantasy), *Pride and Prejudice* (Austen, literary/romance), *Harry Potter and the Philosopher's Stone* (Rowling, middle-grade fantasy), and *The President Is Missing* (Clinton/Patterson, thriller). Hand-counted tag distributions: LOTR 75% basic / 10% functional / 15% descriptive; P&P 50% / 32% / 18%; HP1 77% / 5% / 18%; President 83% / 10% / 7%. These four books anchor Voice Consistency at >= 50% (Austen floor) and set the Performance Tag Rate genre defaults. Caveat: n=4 books across 3 genres by 4 authors; author variation cannot be statistically separated from genre variation at this sample size. The thresholds are defensible starting points, not corpus-validated norms. The whole point of the standards document is that the author can override them.

**Dialogue Tags with Adverbs.** % of tags paired with an -ly adverb ("he said quietly"). No sample floor; this is counted literally.

**Flagged items (Dialogue Tags)**. The tokenizer emits flagged items for each of the four sub-metrics. Schema per item:

Tag rate items (all detected tags):
- `text`: the full dialogue line with tag, as it appears (e.g., `"'Get down,' she hissed."`).
- `paragraph`: 1-indexed paragraph number.
- `rule`: `"tagged-dialogue"`.
- `tag_verb`: the tag verb (e.g., `"hissed"`).
- `classification`: `"invisible"`, `"performance"`, or `"other"` (other = in neither list; requires judgment).

Performance tag items: the subset of the above where `classification == "performance"`. The report's Dialogue Tags section surfaces this subset so the author sees the exact tag lines under scrutiny.

Adverb-paired tag items: the subset where the tag is followed (or preceded) by an -ly adverb.
- Same shape as tag rate items, plus `adverb`: the -ly adverb (e.g., `"quietly"`).

### Tag Verb Lists (editable)

These lists are the explicit word lists the Voice Consistency and Performance Tag Rate heuristics classify against. They are editable via `user_config.json` under a `tag_verbs` field (Mode 3). The defaults are:

**Invisible tags** (do not count against Performance Tag Rate):
said, asked, replied, answered, added, continued, began.

**Performance tags** (count against Performance Tag Rate):
whispered, hissed, murmured, growled, snarled, barked, spat, gasped, breathed, sighed, laughed, cried, yelled, shouted, screamed, bellowed, mumbled, muttered, called, stammered, croaked, rasped, purred, drawled, snapped.

Verbs not in either list (e.g., "declared," "explained," "noted") are counted in the total for Voice Consistency but are excluded from the Performance Tag Rate numerator. Author may add either type to their user config.

---

## Report Format

Every report MUST match this structure and heading style:

```
# [Document Title] - PWA-style Writing Review

Source: [filename] | [word count] words | [page estimate] pages

---

## What Happened

[Two to three short paragraphs summarizing the document's beats. For fiction: POV, setting, inciting action, key turns, ending state. For non-fiction: thesis, supporting moves, conclusion. Hard cap: three paragraphs. No interpretation, no craft commentary, just what the piece does.]

This section serves two jobs at once. First, orientation: an author scanning a folder of ten reports should know which one belongs to which chapter without opening the manuscript. Second, comprehension check: the author should read this paragraph and be able to tell whether the evaluator actually understood the piece. If the summary misidentifies the POV, the setting, or the key turn, every downstream judgment call in the report (Engagement, Emotion Tells, Style, pacing) is suspect. A bad summary is a signal to rerun or to distrust the scoring.

---

## Beat Sheet

[A numbered list of the narrative or argumentative beats in the order they appear. Each beat has a short name, an approximate word position, and a one-line description of what the beat does. Typical chapters produce 5 to 10 beats. Short chapters or articles produce 3 to 5. Long chapters produce 8 to 12.]

Format:

```
1. [Beat name]. Word ~1-400. [One line describing what happens in the beat.]
2. [Beat name]. Word ~400-900. [One line.]
3. [Beat name]. Word ~900-1,600. [One line.]
...
```

Beat names are descriptive, not framework-forced. Use the genre's typical pattern from the Per-Genre Beat Patterns table as a reference lens, but name what is actually on the page. If the chapter opens in media res, the first beat is "in media res opening," not "hook" because thriller convention expects "hook."

**Structural Observations** (included only when something is worth saying):

- Pacing imbalance (e.g., "Beats 1-4 cover the first 60% of the chapter; beats 5-8 compress into the last 40%. Pacing tilts front-loaded.")
- Missing convention beats (e.g., "F5 Horror convention expects an aftermath beat; this chapter cuts on the confrontation. Check against the book's rhythm.")
- Structural gaps (e.g., "No visible cost beat after the climax. The chapter ends on action without consequence. Intentional, or missing?")
- Genre convention fit (e.g., "Classic four-beat F5 structure: normalcy, intrusion, escalation, confrontation, aftermath. Genre-clean.")

Observations are diagnostic, not violations. The author decides whether the observed structure is the point or a gap.

**Suggested Split** (included only when the document is over the genre's max_chapter_words):

- Looks at the beat sheet and identifies the cleanest narrative seam.
- Names the seam by quoting the opening line of the proposed second half plus approximate word position.
- Reports the word count of each resulting half and what each ends on.
- Offers an alternative seam if a reasonable one exists.
- If no clean seam exists, says so: "This reads as a single sustained scene without a natural break. Over-scope is structural, not two-scenes-in-one-chapter. Revision options: tighten, or accept the length."

The split suggestion is derived from the beat analysis, not a separate pass. A chapter whose beats 1-4 form a complete arc and whose beats 5-9 form a second complete arc is a chapter that should probably be two chapters, and the beat sheet makes that visible.

**Closing note.** The Beat Sheet is the evaluator's structural reading. It is not authoritative. An author may disagree with a beat identification or an observation. Claude can make mistakes; use your best judgment.

---

## BLUF - Bottom Line Up Front

[Three to six bullets, maximum. What the evaluator thinks about this piece after running the numbers. The author's biggest wins, the author's biggest problems, and a one-line verdict. No gushing. No "Nice work!" No "Wonderful!" Professional tone: call it like it reads. If the chapter is strong, say "strong across X and Y; watch Z." If the chapter has real problems, say so. If the evaluator is uncertain because a metric is judgment-sensitive, say that too.]

Format:

- **Verdict**: [one line - e.g., "Publishable with light revision," "Needs a structural pass on pacing," "Solid scene work, voice consistent, glue index worth a look"]
- **Strongest**: [one to two categories with numbers]
- **Weakest**: [one to two categories with numbers, with brief context on whether it is a craft issue or an intentional genre feature]
- **Judgment flags**: [categories where the score is judgment-sensitive and the author should not treat the number as definitive - e.g., Long Repeated Phrases when voice echo is intentional]
- **If you do one thing**: [single most impactful revision move, or "nothing urgent" if the chapter is clean]

The BLUF is the honest answer to "should I spend time on this report." If it says "nothing urgent," the author can close the file and move on. If it names a real problem, the author knows where to look before reading the category sections.

---

## Scope Note

- Pre-processing: [what was stripped, verbatim from the active config's `header_strip_patterns` and `paired_delimiters` labels]
- Active config: [`pwa_config.json` path used for this run, including whether a per-manuscript override was applied] (v1.22)
- Paired delimiters: [list of declared pairs by mode — Mode A attributed POVs, Mode B register labels, Mode C silent-strip labels] (v1.22)
- Computation: [Precise or Ballpark, with the disclosure sentence from the Computation Method section]
- Genre: [selected profile]

---

## Summary Report

### Your key scores

[X]% of goals achieved

### Where your document looks great

[list categories that met threshold, each with metric + threshold]

### Where your document may need work

[list categories that missed threshold, each with current value + target]

---

## Grammar Check
## Spelling Check
## Writing Style Check
## Passive Voice
## Emotion Tells
## Weak Adverbs
## Sentence Length Check
## Sentence Variety
## Very Long Sentences
## Complex Paragraphs
## Sticky Sentences Check (Glue Index)
## Sentence Structure Check
## Pacing Check
## Consistency Check
## Repeats Check
## Dialogue Tags Check
## Character Dialogue Check
## Non-Character Voice Registers
```

The **Non-Character Voice Registers** section (v1.22) is rendered only when the marker map's `non_character_voice_spans` array is non-empty (at least one Mode B paired-delimiter declaration matched in the source). The section format:

```
## Non-Character Voice Registers

Diagnostic only — content in this section was stripped from the scored corpus and is NOT counted in any metric, gate, or goal. This section surfaces declared non-character voice register usage for author review.

### [Register label, e.g., "Omniscient Narrator"]

[Optional one-sentence register description from the config.]

[Span count] spans, [total word count] words.

| # | Source paragraph | Words | Text |
|---|------------------|-------|------|
| 1 | 151 | 18 | The city never forgave its deserters. It only waited, patient as a debt collector. |
```

If multiple Mode B registers were declared, render one subsection per register. Source paragraph numbers reference the **pre-strip source file** (since Mode B content was removed from the stripped file); the verbatim text lets the author Find-in-document in the original.

Each section opens with a one-sentence verdict, states the score and the threshold, and lists the detected issues in a table that names the actual text. Counts alone are not sufficient; the author must be able to locate each flag in their document without re-reading the chapter.

**Pattern-summary + flagged-sentence format**. For categories that detect against a pattern list (Style, Emotion Tells, Weak Adverbs), sections emit two tables:

1. **Pattern summary**: count per pattern, sorted descending. Shows the distribution at a glance.
2. **Flagged items**: one row per flag with the actual sentence and the paragraph number. Up to 50 rows; truncate disclosed if exceeded.

Example Style section:

```
## Writing Style Check

In range. 99.6% against a threshold of 80%.

**Pattern summary**

| # | Pattern | Count |
|---|---------|-------|
| 1 | really X -> stronger X | 1 |
| 2 | acquired -> gained | 1 |

**Flagged sentences**

| # | Paragraph | Text | Pattern |
|---|-----------|------|---------|
| 1 | 14 | She was really tired after the drive. | really X -> stronger X |
| 2 | 41 | He had acquired a taste for the vintage. | acquired -> gained |
```

For sentence-level single-rule categories (Passive Voice, Very Long Sentences, Conjunction Starts, -ing Starts), emit a single flagged-items table. For paragraph-level categories (Complex Paragraphs, Slow Pacing), emit a single flagged-items table with the paragraph preview and the metric value for that paragraph.

The verdict is one line, numeric where applicable, and does not editorialize. The tables list what the evaluator detected; the author decides what to accept.

---

## Formatting Rules

1. Tables are GitHub-flavored markdown tables.
2. Numeric scores use the same precision the thresholds use (e.g., 9.7 not 9.72, 85% not 85.0%).
3. Section verdict lines are flat and professional. No cheerleading, no exclamation points, no "Nice work," "Wonderful," "Brilliant," "Fantastic," or similar. Patterns:
   - Goal met: "In range." / "Meets threshold." / "No issues." / "Within genre band."
   - Goal missed: "Above threshold by [X]." / "Below threshold by [X]." / "Reduce [metric] to [target]." — direct, numeric, no softening.
   - Judgment-sensitive: "In range, but judgment-sensitive. See note." or similar.
4. Do not include emoji decorations that PWA uses in the PDF export; they do not survive markdown conversion reliably.
5. Follow standard professional writing conventions in the report itself.
6. Tone: an editor's assessment, not a cheerleader's. The report is information for the author to act on. Treat the author as a professional who can handle a number without a compliment attached.

---

## Genre Profiles

Many thresholds vary by genre. A literary novel at readability grade 10 is normal; a cozy mystery at grade 10 is high. A romance with 12 weak adverbs per 1,000 words is in range; a literary novel at 12 is above range. This section defines genre-specific threshold adjustments.

The metric itself never changes (weak adverbs are still counted the same way). Only the threshold the metric is judged against changes per genre.

### Genre Sensitivity

Each category is either **universal** (same threshold across all genres) or **genre-sensitive** (threshold shifts with genre selection).

| Category | Sensitivity |
|----------|-------------|
| Grammar | universal |
| Spelling | universal |
| Quote Consistency | universal |
| Acronym Consistency | genre-branched (fiction: styling-only; non-fiction: styling + first-use definition) |
| Long Repeated Phrases | universal |
| -ing Starts | universal |
| Style Score | genre-sensitive |
| Sentence Length | genre-sensitive |
| Sentence Variety | genre-sensitive |
| Very Long Sentences | genre-sensitive |
| Passive Voice | genre-sensitive |
| Emotion Tells | genre-sensitive |
| Weak Adverbs | genre-sensitive |
| Complex Paragraphs | genre-sensitive |
| Glue Index | genre-sensitive |
| Conjunction Starts | genre-sensitive |
| Slow Pacing | genre-sensitive |
| Dialogue Tags | genre-sensitive |
| Voice Consistency (Tags) | universal |
| Performance Tag Rate | genre-sensitive |
| Dialogue Tags with Adverbs | genre-sensitive |

Universal thresholds come from the Category Table above and do not change.

### Chapter-level Scope and Genre Max Words

This tool is chapter-scoped. Each genre carries a `max_chapter_words` value reflecting the upper end of typical chapter length in that genre. Documents at or under the genre max are within scope; everything runs with full confidence. Documents over the genre max are over-scope; the Scope Note flags this and the Beat Sheet analysis (see Report Format) surfaces a suggested split point derived from the beat structure.

| Genre | max_chapter_words | Rationale |
|-------|-------------------|-----------|
| F1 Literary | 5,500 | Literary runs long but rarely past here before it becomes novella-section territory |
| F2 Thriller | 3,000 | Patterson / Baldacci / Child short-chapter convention |
| F3 Romance | 5,500 | Scene-driven, tops out around here |
| F4 SciFi / F | 6,000 | World-building needs room; Sanderson-scale chapters use Custom |
| F5 Horror | 5,500 | Tension-driven; longer than this dilutes dread |
| N1 Journalism | 2,500 | Feature-length article territory |
| N2 Memoir | 5,000 | Personal essay or memoir chapter |
| N3 Business | 4,000 | Self-help chapters trend long |
| N4 Academic | 10,000 | Journal articles and monograph chapters run long |
| N5 PopSci | 5,000 | Malcolm Gladwell chapter length |
| U Universal | 5,000 | Defensible middle ground |
| C Custom | weighted average of the blended profile maxes | Same math as threshold blending |

Over-scope behavior: the Scope Note discloses the over-scope status in words, and the Beat Sheet section produces a suggested split point based on the natural seams in the beat structure. If no clean seam exists, the Beat Sheet says so honestly. The tool does not block over-scope runs; it runs with a caveat and gives the author actionable structural feedback.

### Per-Genre Beat Patterns

Each genre has a `typical_beat_pattern` string describing what a well-built chapter in that genre tends to contain. The Beat Sheet section uses this as a reference lens to flag deviations as observations, not errors. An author may intentionally break convention; the tool surfaces the break without scoring against it.

| Genre | typical_beat_pattern |
|-------|----------------------|
| F1 Literary | Opening state (often interior or atmospheric), inciting moment, complication or reflection, turn, new understanding or unresolved close. Literary often ends on a question, not an answer. |
| F2 Thriller | Hook (in the action or under tension), escalation, reversal or revelation, cliffhanger. Aftermath is minimal or skipped; next chapter picks up the tension. |
| F3 Romance | Emotional or relational goal stated or implied, obstacle, tension peak (conflict, misunderstanding, or attraction), moment (connection, rupture, or recognition), aftermath. The moment is the beat romance cannot skip. |
| F4 SciFi / F | Opening state (world or situation grounding), inciting action or reveal, escalation often with world-mechanic integration, turn, close that advances the larger arc. World-building threads through every beat. |
| F5 Horror / Gothic | Normalcy (establishes what is at risk), intrusion (the wrong note, the thing that should not be), escalation (the wrongness grows or is confirmed), confrontation (the character faces it or fails to), aftermath (the price, the mark left, the changed world). Missing the aftermath reads more thriller than horror. |
| N1 Journalism | Lede (the hook, often a scene or figure), nut graf (why this story matters now), supporting evidence (interviews, data, precedent), counterpoint or complication, conclusion or kicker. Missing the nut graf is structural. |
| N2 Memoir | Present-moment anchor, reflection or recall, scene from past or formative moment, insight or earned realization, return to present with changed understanding. The earned realization beat is the one memoir cannot skip. |
| N3 Business / Self-help | Problem or pain point, anecdote or illustration, framework or principle, application or example, call to action or takeaway. Each chapter should close with something the reader does. |
| N4 Academic | Claim or research question, literature or precedent, methodology or argument structure, findings or analysis, implications or next steps. Discipline-specific variance accepted. |
| N5 PopSci / Narrative NF | Scene or anecdote hook, the idea or phenomenon, mechanism or evidence, complication or caveat, synthesis or broader implication. Often mirrors magazine feature structure. |
| U Universal | Opening state, inciting moment, complication, turn, close. Flat pattern for genre-neutral grading. |
| C Custom | Weighted blend of the closest named profiles' beat patterns. Described at runtime during Custom genre construction. |

The Beat Sheet section reports the observed beats and, when relevant, compares against the genre pattern. Deviations are observations: "F5 Horror convention expects an aftermath beat; this chapter cuts on the confrontation. Check against the book's rhythm." The author decides whether the deviation is the point or a gap.

### The Eleven Genre Profiles

Ten named profiles plus Universal. A Custom profile can be built at runtime.

#### Fiction

**F1. Literary / Upmarket Fiction**
Longer sentences, higher complexity, more interiority, moderate-to-low dialogue density, lean adverb use, tolerant of slow pacing, tolerant of "sticky" voice constructions.

**F2. Thriller / Suspense / Crime**
Short sentences, tight pacing, high dialogue density, lean prose, low complex-paragraph tolerance, low passive-voice tolerance, low slow-pacing tolerance.

**F3. Romance**
Moderate sentences, high dialogue density, higher emotion-tell tolerance, higher adverb tolerance, higher dialogue-tag tolerance, moderate pacing.

**F4. Science Fiction / Fantasy**
Moderate-to-long sentences for world-building, moderate dialogue, higher glue-index tolerance, higher complex-paragraph tolerance, moderate slow-pacing tolerance for exposition.

**F5. Horror / Gothic**
Moderate-to-longer sentences, high sensory grounding, low dialogue density, tolerant of passive voice for dread effect, moderate slow-pacing tolerance.

#### Non-fiction

**N1. Journalism / Reportage**
Short-to-moderate sentences, strict active voice, low adverb, low passive, grade 6-8 target, strict glue index, low complex-paragraph.

**N2. Memoir / Personal Essay**
Longer sentences, high variety, higher emotion-tell tolerance, moderate complexity, grade 8-10 target.

**N3. Business / Self-help**
Short sentences, high readability, low glue index, low complex-paragraph, grade 6-8 target, moderate dialogue tolerance (anecdotes).

**N4. Academic / Scholarly**
Long sentences, high complexity tolerance, high glue-index tolerance, high passive-voice tolerance, grade 12+ accepted, low dialogue (usually none).

**N5. Popular Science / Narrative Non-fiction**
Moderate sentences, moderate complexity, grade 8-10 target, active voice preferred, low adverb, moderate dialogue tolerance.

**U. Universal**
The defaults from the Category Table. Used when no genre is selected or when the user wants genre-neutral grading.

**C. Custom**
Built at runtime when the user's work does not fit any named profile. See "Custom Genre Construction" below.

### Genre Threshold Matrix

Threshold syntax: same as the Category Table. Metric direction (higher/lower/in-range) is unchanged from the Category Table; only the numeric target shifts.

| Category                    | U (Universal)   | F1 Lit       | F2 Thriller  | F3 Romance   | F4 SciFi/F   | F5 Horror    | N1 Journ     | N2 Memoir    | N3 Biz       | N4 Acad      | N5 PopSci    |
|-----------------------------|-----------------|--------------|--------------|--------------|--------------|--------------|--------------|--------------|--------------|--------------|--------------|
| Style Score                 | >= 80%          | >= 75%       | >= 85%       | >= 78%       | >= 78%       | >= 78%       | >= 88%       | >= 78%       | >= 88%       | >= 72%       | >= 82%       |
| Sentence Length             | 9.0 to 18.0     | 12.0 to 22.0 | 8.0 to 14.0  | 9.0 to 16.0  | 10.0 to 18.0 | 10.0 to 18.0 | 10.0 to 16.0 | 11.0 to 20.0 | 10.0 to 15.0 | 14.0 to 24.0 | 11.0 to 18.0 |
| Sentence Variety            | >= 5.0          | >= 6.5       | >= 5.5       | >= 5.0       | >= 5.5       | >= 5.5       | >= 5.5       | >= 6.0       | >= 5.0       | >= 5.0       | >= 5.5       |
| Very Long Sentences         | < 3%            | < 6%         | < 2%         | < 3%         | < 5%         | < 5%         | < 2%         | < 5%         | < 2%         | < 10%        | < 4%         |
| Passive Voice               | < 25.0          | < 25.0       | < 15.0       | < 22.0       | < 25.0       | < 30.0       | < 12.0       | < 22.0       | < 15.0       | < 40.0       | < 18.0       |
| Emotion Tells               | < 20%           | < 15%        | < 20%        | < 30%        | < 22%        | < 25%        | < 10%        | < 28%        | < 15%        | < 8%         | < 15%        |
| Weak Adverbs                | < 10.0          | < 7.0        | < 10.0       | < 13.0       | < 10.0       | < 10.0       | < 6.0        | < 10.0       | < 7.0        | < 8.0        | < 8.0        |
| Complex Paragraphs          | < 15%           | < 25%        | < 10%        | < 15%        | < 22%        | < 20%        | < 8%         | < 20%        | < 10%        | < 45%        | < 15%        |
| Glue Index                  | < 40%           | < 44%        | < 38%        | < 40%        | < 42%        | < 42%        | < 38%        | < 42%        | < 38%        | < 48%        | < 40%        |
| Conjunction Starts          | < 9%            | < 12%        | < 10%        | < 9%         | < 9%         | < 10%        | < 6%         | < 10%        | < 7%         | < 5%         | < 8%         |
| Slow Pacing                 | < 30%           | < 45%        | < 20%        | < 30%        | < 40%        | < 38%        | < 25%        | < 38%        | < 22%        | no cap       | < 35%        |
| Dialogue Tags               | < 50%           | < 45%        | < 55%        | < 60%        | < 50%        | < 45%        | < 40%        | < 45%        | < 40%        | < 30%        | < 45%        |
| Voice Consistency (Tags)    | >= 50%          | >= 50%       | >= 50%       | >= 50%       | >= 50%       | >= 50%       | >= 50%       | >= 50%       | >= 50%       | >= 50%       | >= 50%       |
| Performance Tag Rate        | < 18%           | < 18%        | < 10%        | < 22%        | < 18%        | < 25%        | < 7%         | < 15%        | < 10%        | < 5%         | < 12%        |
| Dialogue Tags with Adverbs  | < 12%           | < 8%         | < 12%        | < 18%        | < 12%        | < 12%        | < 5%         | < 10%        | < 8%         | < 5%         | < 8%         |

"no cap" means the category is not scored against a ceiling for that genre (e.g., Academic work is expected to be slow-paced by definition).

### Custom Genre Construction

When the user selects "Custom / Describe it," ask them to describe the work in a sentence or two. Then:

1. Identify the one or two named genres the work is closest to (e.g., "Firefly fan fiction" = F2 Thriller blended with F4 SciFi/F; "food memoir with recipes" = N2 Memoir blended with N3 Business).
2. Ask the user which genre is dominant, or whether the blend is roughly 50/50.
3. Construct a custom profile by taking a weighted average of the threshold values. For a 60/40 blend of F2 and F4, each genre-sensitive threshold becomes `0.6 * F2_value + 0.4 * F4_value`, rounded to match the metric's precision.
4. Show the computed profile to the user in a table for confirmation before saving.
5. Save the custom profile as a named entry in `user_config.json` so it is reusable for future sessions on the same project.

Custom profiles inherit all universal thresholds unchanged.

### Applying Genre Selection

When a prompt runs against a genre-selected document, every genre-sensitive category uses the genre's threshold in place of the Universal threshold. Universal categories are unaffected.

The report output MUST name the genre in the Summary section header and list any per-category thresholds that shifted from Universal so the reader can tell what yardstick was used.

Example:

```
## Summary Report

Genre: Horror / Gothic (F5)
Goals achieved: 82% (18 of 22)

Threshold adjustments from Universal:
- Passive Voice: < 30.0 (Universal: < 25.0)
- Slow Pacing: < 38% (Universal: < 30%)
- Emotion Tells: < 25% (Universal: < 20%)
- [etc.]
```

---

## File Safety Invariants

These rules apply to every prompt in the routine, across every mode. They are non-negotiable and exist because the product's value to the skeptical user segment depends entirely on the trust contract they establish.

1. **The original input file is never modified.** Every prompt treats the original path as read-only for the full run.
2. **All edits land in a clearly named copy.** The working-copy filename includes the word "copy" as a durable visual cue.
3. **Pre-flight path check before any write.** Before any write operation:
   - Compare the target path to the source path (byte-for-byte, after path normalization). They must not match.
   - Verify the target is under the configured output directory (the document's folder, `{{DOC_FOLDER}}`).
   - Verify the target filename contains "copy" (case-insensitive).
   - If any check fails, hard-stop. Do not write. Do not attempt to auto-correct the path. Report the failure to the user and wait for instructions.
4. **Same-day collision handling.** If the target filename already exists from an earlier run today, append `-v2`, `-v3`, and so on. Never overwrite a prior output.
5. **Fix logs lead with paths.** Every change log or fix log opens with an explicit original-unchanged / working-copy-edited disclosure so the user can confirm the safety contract was honored before reading anything else.
6. **Violation is a bug, not a feature request.** If any future prompt proposes an exception to these rules, it is rejected by default. Exceptions require an explicit change to this section with a version bump and a justification.

These invariants compose into defense in depth: a mistake in a single prompt is not enough to produce a destructive write. The filename must drop "copy," the pre-flight check must fail silently, and the target path normalization must produce a false negative. All three have to go wrong at once.

---

## Auto-fix Tiers

Each category is tagged with an auto-fix tier that Mode 2 and Mode 3 prompts consult when deciding whether to apply changes automatically.

- **safe**: Mechanical transform with a single correct answer. Claude may apply without asking.
- **prompt**: Fix is usually correct but can change voice or meaning. Mode 3 applies by default if the category is enabled; Mode 2 skips (Mode 2 is safe-only).
- **manual**: Requires structural judgment. Claude never auto-applies; surfaces an annotation for the author.

| Category | Tier | Rationale |
|----------|------|-----------|
| Grammar | safe | Missing commas, missing hyphens in compound modifiers, subject/verb agreement, punctuation. Homophones are prompt-tier (see note). |
| Spelling | safe | Dictionary-backed replacement. Foreign words, proper nouns, and coined terms are prompt-tier. |
| Style | prompt | Most substitutions are mechanical ("began to X" to past tense, redundant "that"), but some are voice calls. |
| Passive Voice | manual | Active rewrites require knowing the agent and re-pacing the sentence. |
| Emotion Tells | manual | Fix = rewrite the beat to show rather than tell. Requires authorial judgment. |
| Weak Adverbs | prompt | Adverb removal is often safe; adverb-to-stronger-verb is prompt-tier. |
| Sentence Length | manual | Combining or splitting sentences is a craft call. |
| Sentence Variety | manual | Requires restructuring. |
| Very Long Sentences | manual | Same. |
| Complex Paragraphs | manual | Requires splitting or restructuring. |
| Glue Index | prompt | Specific patterns ("in the corner of the X" to possessive) are safe; general glue reduction is a rewrite. |
| Conjunction Starts | manual | Removing "And"/"But" starts changes rhythm. |
| -ing Starts | manual | Requires a rewrite. |
| Slow Pacing | manual | Requires inserting beats or restructuring. |
| Quote Consistency | safe | Normalize to dominant style. |
| Acronym Consistency | safe | Normalize to dominant style. |
| Long Repeated Phrases | manual | Often intentional. |
| Dialogue Tags | prompt | Adverb stripping is safe; tag-to-action-beat substitution is manual. |
| Voice Consistency (Tags) | manual | Voice drift is a craft call; cannot be mechanically fixed. |
| Performance Tag Rate | prompt | "whispered" to "said" is a voice call; author reviews per-instance. |
| Dialogue Tags with Adverbs | prompt | Adverb stripping is usually safe. |

**Homophone and proper-noun note**: Within Grammar and Spelling, the category is `safe` overall but individual issue types within it can be `prompt`-tier. The Mode 2 prompt handles this by applying true typos (e.g., "teh" -> "the", missing punctuation) automatically while deferring homophone confusion (its/it's) and unknown-word flags (foreign language, coined terms) to a review list.

---

## Version

v1.25 (2026-04-22). If thresholds, tiers, genre profiles, pre-processing rules, or safety invariants are updated, bump the version and record the change here.

### Version History

- v1.25 - **Scope of spelling-subagent reporting narrowed to step 6 only; calibration-ratio apparatus removed.** The only spelling outcome the routine cares about is a genuine misspelled or misused English word. Foreign vocabulary, proper nouns from context, coined terms, and genuine unknowns are exclusions the subagent applies silently — not reported, not logged, not gated on. Removed `unknown_words_for_review` from the Grammar/Spelling subagent JSON schema. Removed the calibration-ratio floor (2.0 code-switching / 0.5 default) and the 0.0-hard-fail-on-chapters-over-1000-words gate from the v1.24 Validator Config section. Rewrote the "a clean chapter producing clean scores is the expected outcome" subsection to reflect the narrower architecture: the router validates what the subagent DID claim (substring checks, paragraph range, hallucination-marker filter, score math) rather than what it should have claimed alongside. A subagent that short-circuits and returns zero issues on a genuinely clean chapter produces the same output as one that did the work and found nothing, and the router does not try to distinguish them. Rewrote the Scans step of the Grammar/Spelling pass to reflect "walk Recognition Order internally, report only step 6 hits." Added explicit "Scope of spelling issues" note under the schema. Updated the Scope Note disclosure line to drop the unknown-words count. Companion changes: `subagents/grammar_spelling.md` v1.1 → v1.2 (removes `unknown_words_for_review` from schema, hard constraints, and substitution checklist; removes the `{{FOREIGN_VOCAB}}` placeholder since it no longer affects any gate); `router/validators/grammar_spelling.py` v0.1 → v0.2 (removes calibration-ratio computation, removes `series_context` / `foreign_vocab` parameters, keeps schema / score math / substring / paragraph-range / hallucination-marker gates). Net effect: one less config path for authors to maintain, one less apparatus for the subagent to ignore, and the router's remaining gates still catch the worst failure mode (citing text that is not in the stripped file).
- v1.24 - **Subagent Architectural Rule formalized: subagents report, the router validates.** Surfaced during an end-to-end canary dry run on 2026-04-22. The Grammar and Spelling subagent's hardened prompt (subagents/grammar_spelling.md v1.0) carried an explicit calibration gate with pass / fail thresholds. The subagent returned a result with `unknown_review_ratio: 0.0`, an empty `unknown_words_for_review` array, AND `passes_calibration: true` - violated the gate AND lied about violating it. The prompt instruction was ignored. Diagnosis: a subagent reading a long instruction tends to produce output that looks like what the instruction seems to want regardless of whether the underlying observation supports that output. Asking a subagent to self-reject is asking it to fight that gradient and it will not reliably do so. New top-level section "Subagent Architectural Rule: Subagents Report, the Router Validates" added between Performance Notes and Strip Verification, codifying: (1) subagent prompts ask only for observations and counts, no self-check branches; (2) router validates returned JSON deterministically (schema, range, cross-reference); (3) on validation failure, router re-dispatches once with a corrective instruction citing the specific failure; (4) on second failure, router hard-stops Mode 1 and reports to author; (5) calibration thresholds in subagent prompt files are documentation for the human reading the prompt, not instructions for the subagent. Section enumerates the per-subagent validator config the router carries (Grammar/Spelling unknown-review ratio floor + substring + paragraph checks; Strip Verification verdict-and-failures cross-check; Summary/Beat Sheet beat-count + named-character + word-range checks; Character Dialogue per-mode floor + substring + zero-cross-mode-drift checks; Report Verification recursive-only-one-level cited-claim checks). Also clarifies "a clean chapter producing clean scores is the expected outcome, not a subagent failure" - canaries against multi-pass-reviewed chapters often return Grammar 100% / Spelling 100%, and the audit trail (not the issue counts) is what the router validates for subagent integrity. Clean canaries are particularly good at surfacing subagent-integrity bugs: on a dirty chapter, issue counts can mask a missing audit trail; on a clean chapter, the missing audit trail is the only signal. Reframed the Grammar and Spelling section's `unknown_words_for_review` paragraph from "informational sanity-check list" to "audit trail the router validates" and added a pointer to the architectural rule. Created `canary/references/subagents/` directory with `grammar_spelling.md` v1.0 as the first hardened, versioned subagent prompt template (router substitutes `{{PLACEHOLDERS}}` before dispatch). The next concrete unblocker before skill extraction is the router-side validator (Python module that consumes subagent JSON, runs the per-subagent validator config from this section, and re-dispatches on failure); after that, Mode 1 assembly and end-to-end Report Verification become the final pre-skill gates.

- v1.23 - **Strip engine + tokenizer build-out, plus -ing morphological-check precision fix.** Built `canary/scripts/strip_engine.py` implementing the v1.22 contract end-to-end: per-manuscript-then-routine config layering with array concatenation, all five header strip rule types (`line_starts_with` with optional `and_contains`, `exact_line`, `markdown_heading` with `levels`, `html_tag` with user-configurable `consume`, `regex` with optional flags), three-mode paired-delimiter taxonomy (Mode A markers stripped + interior kept + spans recorded against final stripped file; Mode B markers + interior stripped + spans recorded against pre-strip source; Mode C silent strip), undeclared paired-delimiter warning system, three output files (stripped prose, marker map JSON, strip log JSON), Mode-A-without-`--pov` guardrail. Built `canary/scripts/tokenizer.py` covering every tokenizer-eligible category in the Category Table with the v1.22 exclusion lists wired in: `acronym_emphasis_exclusions` (case-insensitive substring match against ALL-CAPS sequences declared as typographic emphasis), `weak_adverb_noun_exclusions` (skips -ly nouns adjacent to verbs), `ing_starts_proper_noun_exclusions` (skips declared non-participle openers). All `flagged_items` schemas match the per-category specification with the 50-item-per-category truncation rule. **Morphological-check precision fix.** The v1.22 -ing Starts heuristic intent was: token ends in literal `ing` AND its literal lowercase form appears elsewhere in the chapter (a real present-participle leaves lowercase footprints; a proper noun like `Sterling` does not). The v1.22 prose was ambiguous and the first tokenizer implementation built `lower_inventory = {w.lower() for w in tokens}` which is tautologically true for the capitalized opener itself (because lowercasing is applied to every token in the chapter, the capitalized opener's lowercase form is always present). Surfaced during a canary run where a capitalized surname (5 occurrences, 0 lowercase) passed the check despite never appearing as a lowercase participle. Fixed by switching to `literal_token_set = set(raw_inventory)` (case-preserved) and testing `first_lower in literal_token_set` — only true if the literal lowercase form appears as written. Clarified the `_standards.md` heuristic prose accordingly. **Seed `ing_starts_proper_noun_exclusions` populated.** Routine-level config seed previously empty; populated with 15 universal English entries (`nothing`, `something`, `anything`, `everything`, `morning`, `evening`, `ceiling`, `ring`, `spring`, `string`, `thing`, `king`, `wing`, `during`, `according`) covering indefinite pronouns and high-frequency common nouns ending in -ing. Authors continue to populate per-manuscript with character surnames and other capitalized non-participle openers. **Canary validation.** Re-ran tokenizer against the v1.23 implementation: -ing flags reduced from 20 to 6 (all legitimate present-participle openers); acronym false positives on ALL-CAPS typographic emphasis suppressed; `assembly came` weak-adverb false positive suppressed. Both engine and tokenizer are now skill-extraction candidates pending verifier subagent extraction, first-run interview as callable routine, restart-prompt edit menu as callable routine, and a second canary on a Mode-A-only chapter.

- v1.22 - **Config-driven preprocessing.** Replaced every hardcoded preprocessing rule with a single JSON config file (`pwa_config.json`) read from a per-manuscript override path first, then a routine-level default. On first run the routine walks the author through a structured setup interview (manuscript format, header strip rules, paired delimiters, exclusion lists) and writes the result to disk. On subsequent runs the config loads silently with a one-line summary and a `Update? [y/N]` prompt; default `N` proceeds with the loaded config, `y` drops into a structured edit menu (AskUserQuestion picker in Cowork, numbered text menu in CLI/Code; the routine detects context). Single rolling `.bak` of the prior config is kept on each save; multi-backup rotation deliberately rejected since the config is git-tracked and small. Per-manuscript override semantics are shallow-merge with array concatenation; manuscript entries appended after routine entries (so manuscript entries take *lower* priority under first-match-wins, matching the file lookup order). **Generalized paired-delimiter handling.** The v1.21 INTERNAL DIALOGUE rule generalized to a three-mode taxonomy declared per pair in the config: **Mode A** (character interiority, scored, attributed to a named POV character — v1.21 behavior); **Mode B** (non-character voice register, markers AND content stripped from scored corpus, surfaced in a dedicated diagnostic-only report section with explicit "not scored" disclosure); **Mode C** (production-only strip, markers AND content stripped silently with no logging). The v1.22 patch was surfaced by a canary where a Mode B paired-delimiter block passed through intact because v1.21's rule only handled one specific opener, leaking author-side production markers into the scored corpus and triggering false-positive acronym flags. The Mode B classification handles non-character atmospheric voice — neither a named character (no Mode A fit) nor production noise (no Mode C fit). Schema designed author-agnostic: no manuscript-specific terminology in `_standards.md`; the author declares opener/closer/mode/register_label per pair at setup. Disambiguation is array order, first-match-wins. **Header strip rule schema.** Five `type` values cover the field: `line_starts_with` (with optional `and_contains` substring requirement), `exact_line`, `markdown_heading` (with `levels` array), `html_tag` (with `tags` array and user-configurable `consume`: `tag_block`, `opener_line`, `closer_line`, `opener_and_closer_lines`; HTML tag selection is per-author since the routine ships with no HTML tag rules), `regex` (escape hatch). Each rule has a human-readable `label` used in the edit menu and strip log. **Strip log.** Sibling JSON file alongside the marker map records which rules fired, which had zero matches, and a summary line; surfaces dead rules and manuscript-format mismatches. **Undeclared paired-delimiter warning.** During strip, any `[[<TAG>: ...]]`-shaped span that no declared `paired_delimiters` entry matched emits a warning to the strip log naming the excerpt and paragraph; informational, not blocking; surfaces the exact failure mode (silent leakage of author markers into scored corpus) that produced this patch. **Marker map schema extended** with `paired_delimiter_declarations` (mirrors active config so the marker map is self-describing), `non_character_voice_spans` array (Mode B spans, paragraph numbers reference the pre-strip source file since Mode B content is gone from the stripped file). **Three secondary fixes** bundled, all aligned with the v1.15 "editable exclusion" pattern: (1) Acronym Consistency consults `acronym_emphasis_exclusions` (case-insensitive substring match) and skips ALL-CAPS sequences declared as typographic emphasis (book titles, in-world organization names, stylistic shouts); (2) Weak Adverbs consults `weak_adverb_noun_exclusions` and skips -ly nouns (assembly, family, supply, reply, rally) — surfaced by `assembly came` flagged as weak-adverb adjacency in a canary run; (3) -ing Starts requires actual present-participle form (token ends in `ing` AND is recognizable participle OR appears lowercase elsewhere in chapter) and consults `ing_starts_proper_noun_exclusions` to skip declared proper nouns and non-participle words (Harrington, Inferior, Practitioner) — surfaced by capitalized proper-noun openers flagged as -ing starts in a canary run. Default exclusion lists ship sensibly (empty for acronym emphasis and -ing proper nouns, populated for weak-adverb -ly nouns); authors append per-manuscript as canaries surface false positives. **Report Format extensions:** Scope Note now includes active config path and paired-delimiter mode declarations; new optional Non-Character Voice Registers section (rendered only when Mode B spans exist) with diagnostic-only disclosure header, per-register subsection format with source paragraph + word count + verbatim text columns. **Report Verification Pass extensions:** new check #10 audits the Non-Character Voice Registers section against the marker map (every Mode B span rendered; section disclosure language present; Mode B content absent from stripped file = FAIL since the strip pipeline didn't honor the Mode B contract); new check #11 audits config metadata and strip log (active config path in Scope Note; strip log present; strip log labels match config rule labels). Verifier inputs extended with active `pwa_config.json` path and strip log JSON path. Verifier JSON schema extended with `non_character_voice_checks` and `config_and_strip_log_checks` blocks. **Reuse paragraph rewritten:** all three modes now read from `pwa_config.json` rather than the per-mode preprocessing question; legacy `user_config.json.preprocessing` field retained for backward compatibility but Mode 3 should migrate values into `pwa_config.json` on first read. Rationale: the v1.21 patch closed the structural-check gap from v1.10 but exposed a different gap — preprocessing rules were still hardcoded into the strip script, which made every new manuscript convention a code edit and produced bugs the architecture should have prevented. Moving rules to data closes that gap and makes the same routine work against any manuscript format any author declares.

- v1.21 - Added **internal-dialogue handling** to Pre-processing and **two-mode (spoken + internal) fingerprint analysis** to the Character Dialogue Consistency Pass. Surfaced during a canary preparation where a chapter contained many paired-delimiter interiority blocks, and the v1.20 default of stripping the entire block (markers + content) would have thrown away the richest voice signal in the chapter — the POV character speaking to themselves — exactly the data a Character Dialogue Consistency pass needs most. The fix: paired-delimiter markers wrapping interiority are stripped (markers only), the prose between them is kept in the scored denominator, and a sibling marker map JSON file records the paragraph ranges of those internal-mode spans so the Character Dialogue subagent can attribute them to the POV character as a separate speech mode. POV characters now get two fingerprints side by side (spoken from quoted dialogue, internal from marker-map spans), each with its own identity label and five-dimension table. Drift within each mode is flagged normally; **drift between modes is explicitly NOT flagged** (the gap between how a person speaks and how they think is expected and would generate false positives on every POV chapter). The 6-line sample floor applies per mode; a POV character can clear the floor in spoken only, internal only, both, or neither. Attribution mismatch in the internal mode catches POV slippage (the author briefly inhabiting a different consciousness inside a POV chapter), a real craft failure mode that pre-v1.21 had no way to surface. Authors with any paired conventions can declare the opener/closer pair and inherit the same markers-only-kept-content rule. Added marker map file schema, updated subagent input list, updated subagent JSON example to show two-mode structure (`modes.spoken`, `modes.internal`) for the POV character with both fingerprints rendered side by side. Extended Report Verification Pass check #9 to confirm: each mode rendered as its own block with headline + identity label + fingerprint table + flag tables; per-mode floor handling for insufficient-sample modes; no flags emitted for cross-mode shifts (FIX if found); Scope Note disclosure names which mode(s) ran per POV character. Extended verifier JSON schema with `marker_map_present`, `pov_characters_with_two_modes`, `modes_rendered_per_pov`, `cross_mode_drift_flags_present`, `scope_note_names_modes_per_pov`. The "strip markers + content" behavior is now Mode C and remains selectable when interiority analysis is not desired. Rationale: interiority is dialogue the character has not said aloud, and treating it as prose alongside spoken dialogue collapses the two voices into a single denominator that obscures both. The fix preserves both signals and reports them side by side with the explicit constraint that natural variation between spoken and internal voice is expected, not a defect.

- v1.20 - Added **Character Dialogue Consistency Pass** as a subagent-delegated Mode 1 routine step, closing the second of the two structural checks flagged in v1.10 as pending (the other being the Beat Sheet, delivered in v1.10). Category Table row 23: "Character Dialogue Consistency" with a zero-flags threshold and a 6-line-per-character sample floor; row is N/A and denominator-exempt when no character clears the floor. Subagent receives only the chapter (no canon, no prior chapters, no character profiles) and builds a per-character fingerprint across an identity label (headline phrase like "Gen Z, Latina, sardonic, code-switches Spanish" or "elder, formal, Old-World Mexican, measured") plus five dimensions: sentence length distribution, diction register, sentence structure, signature markers, contractions use. Subagent scans for two failure modes: **drift** (a line where a character's established fingerprint shifts without narrative cause) and **attribution mismatch** (a tagged line whose content, register, or structure matches a different character's fingerprint better). Both failure modes are judgment-sensitive: the author reviews each flag because a valid narrative reason (drunk, panicked, lying, performing) can justify a shift. Scoring rule is deliberately conservative: any flag = goal missed, on the principle that surfacing every shift for author review is the purpose. New Mode 1 Character Dialogue Check section (positioned after Dialogue Tags Check) renders headline line + fingerprint table + drift flags table + attribution flags table per character, with "insufficient sample" listing for characters below the 6-line floor. Mode 3 never auto-fixes; every flag is prompt-tier with AskUserQuestion review. Added Scope Note disclosure line, added check #9 to Report Verification Pass (confirms the section matches the subagent JSON and flagged text is chapter-verifiable), added character_dialogue_checks array to verifier JSON schema, added Step 3c to Mode 1 pipeline. Rationale: per-character voice consistency is the second chapter-scale check that pattern-matching software cannot do; the v1.10 entry flagged Per-Character Dialogue as the primary case for why a language-model evaluator is a different tool than PWA. Scope is deliberately chapter-internal only because the routine assumes only the chapter as input; cross-chapter drift and canon-consistency are out of scope and would require a different tool with manuscript-wide context. Identity label added per user feedback: the fingerprint needed to lead with a human-readable tag that says what the voice IS (generation, cultural background, register stance, defining attitude), not just the five component measurements, so the report leads with recognition rather than evidence.

- v1.19 - Added **actionable flagged-item output** across every sentence-, paragraph-, and phrase-level category. Prior versions of the tokenizer emitted counts and pattern summaries but not the actual text that matched, so a report reading "Style Score: 99.6%. Flagged sentences: 2 of 548. Top patterns: `really X -> stronger X` (1), `acquired -> gained` (1)" left the author with no way to find either sentence without re-reading the chapter. That is the exact PWA-style opacity this routine exists to correct. The fix: tokenizer now emits a `flagged_items` array for every applicable category with per-item `text` (verbatim sentence, paragraph preview, or phrase), `paragraph` (1-indexed paragraph number, findable in the document), `rule` or `pattern` (which heuristic matched), and category-specific context fields (matched_phrase, filter_verb + emotion_word, adverb + verb, opener, word_count, etc.). Report sections now emit the flagged text in a table: Style shows the sentence plus the pattern, Weak Adverbs shows the adverb/verb pair in context, Emotion Tells shows the filter construction in its sentence, Slow Pacing shows the paragraph preview, Very Long Sentences shows the sentence, Complex Paragraphs shows the paragraph preview, Conjunction Starts and -ing Starts show the sentence, Long Repeated Phrases gains per-occurrence paragraph numbers, Dialogue Tags shows the tag line classified. Truncation rule: 50 items per category max, truncation disclosed in the section header. Added Flagged Items Schema to Tokenizer requirements, extended every Detection Heuristics category with a Flagged items subsection specifying fields, rewrote Scoring Rule #5 to require text not just counts, rewrote the Report Format Writing Style Check example to show pattern-summary + flagged-sentence two-table layout. Rationale: the routine's thesis is that every flag must be traceable to a line the author can read, argue with, and act on. Counts without text fail that thesis.

- v1.18 - Added **report-language check** to the Report Verification Pass. The v1.17 verifier caught factual errors (narrative, metric, threshold, disclosure, placeholder) but had no explicit rule against prose that exposes the writer's reasoning process. The v3 canary shipped with a BLUF bullet containing a mid-sentence self-correction ("the stddev is 7.97 which is above the baseline of 9 in absolute terms (wait, 7.97 is below 9.0)") that was grammatically fine, numerically defensible, and narratively disqualifying: a deliverable that reads like a scratchpad corrodes reader trust at exactly the moment trust needs to be built. The v1.18 check flags: mid-sentence self-corrections, visible uncertainty hedges ("I think," "probably," "maybe" in metric prose), thinking-out-loud interjections ("wait," "actually," "hmm"), self-referential process notes ("the evaluator noticed," "after reconsidering"), unresolved compound verdicts ("MET but barely," "close to threshold (unclear)"), and dash variants beyond single hyphen (per the project's response formatting standard). Always a FIX-tier verdict (not FAIL): the verifier rewrites the offending line as final-verdict prose preserving the numeric claim. Applies to BLUF, verdict lines, Structural Observations, and any main-context-assembled prose. Does NOT apply to subagent-produced What Happened/Beat Sheet or tokenizer metric tables. Rationale: reports are deliverables, not scratchpads. The article thesis is that opaque metrics corrode trust; prose that narrates the writer's in-progress reasoning corrodes trust the same way.

- v1.17 - Added **Summary and Beat Sheet Pass** and **Report Verification Pass** as subagent-delegated Mode 1 routine steps. An early canary run exposed a different failure mode from the Grammar/Spelling punt: the What Happened summary and Beat Sheet were produced inline from the main context and contained invented characters, fabricated plot events, and a fundamental misread of genre. The metrics were correct; the report's first two sections were fiction about the document. Because those sections are the reader's first contact with the report, the fabrication corroded trust in the numbers that followed. The fix, mirroring the v1.16 Grammar/Spelling architecture, delegates the summary, beat sheet, and structural observations to a subagent reading the full chapter with fresh eyes and strict no-invention constraints. The subagent cannot be primed by accumulated genre assumptions because it has no accumulated context. Added **Report Verification Pass** as a separate subagent dispatched after assembly and before delivery: spot-checks narrative claims against the chapter, metric values against the tokenizer JSON, grammar/spelling claims against the subagent JSON, threshold-direction verdicts for correctness, Scope Note disclosure presence, and absence of placeholder text. Does NOT re-run the tokenizer or re-read the chapter for comprehension. Returns PASS/FIX/FAIL; FAIL hard-stops delivery. Mode 1 pipeline is now: strip, verify strip (subagent), tokenizer (bash), grammar/spelling (subagent), summary/beat-sheet (subagent), assemble, verify assembly (subagent), save. Added corresponding Scope Note disclosure lines. Rationale: assembly is where slippage happens; an audit against every source artifact closes the last gap. The article thesis is that opaque metrics corrode trust; reports that open with fabricated plot events corrode trust faster than any opaque number ever could.

- v1.16 - Formalized **Grammar and Spelling Pass** as a subagent-delegated Mode 1 routine step. The v3 canary exposed a hole: the tokenizer correctly refused to score Grammar and Spelling (regex cannot evaluate homophones, multilingual prose, context-dependent word choice), and the Mode 1 report inherited that punt with "deferred to LLM pass" placeholders. That produced reports where the first two sections said "we don't know." The premise of this routine is that every scored category has a defensible number or a documented reason it cannot be scored - "the tokenizer can't do it" is a technical note, not a reason. The fix mirrors Strip Verification's architecture: a subagent reads the stripped prose with fresh eyes, applies the Detection Heuristics Grammar and Spelling sections (including the six-step Recognition Order for Spelling and the full exclusion list), and returns a JSON blob with per-issue tier tags (safe/prompt). Mode 1 folds that JSON into the report's Grammar Check and Spelling Check sections as real percentages. Mode 3 and Mode 2 both consume the same JSON as their authoritative source rather than re-running detection. Added required disclosure in the Scope Note mirroring the Strip Verification disclosure line. Rationale: human copyeditors produce grammar/spelling counts by reading with judgment. An LLM subagent doing the same is not a compromise, it is the correct method. The tokenizer handles what regex can handle; the subagent handles what requires language understanding; both feed the same report.

- v1.15 - Genre-branched **Acronym Consistency**. The v1.14 rule applied a single "100% consistent" test to all genres, but the implicit editorial expectation drifted toward non-fiction convention (spell out at first use, match later). That convention does not apply to trade fiction. Per CMOS Shop Talk's "Abbreviations in Fiction" (2020) and Articulate Editing's fiction style guide: in fiction there is no need to spell out an unfamiliar abbreviation on first occurrence, and the parenthetical-definition move reads as academic and breaks voice. Fiction introduces acronyms through context or in-dialogue explanation; the editorial test is consistency-of-styling across the manuscript, not first-use-definition. Split the rule: fiction genres (F1-F5) get a styling-only check; non-fiction genres (N1-N5) get styling + first-use definition with an editable 40+ entry exempt list of universally-known acronyms (FBI, NASA, PhD, etc.). Universal (U) defaults to the fiction rule, escalating to non-fiction when document shape signals non-fiction. Custom (C) inherits from whichever parent profile weight dominates. Rationale: the routine exists to make every number traceable to a documented standard; applying a non-fiction convention to fiction without basis would silently punish authors for correctly following their genre's own rules. Category Table row 18, Detection Heuristics Consistency section, and Genre Sensitivity table all updated.

- v1.14 - Eliminated judgment-call metrics wherever a mechanical definition was possible. Removed **Engagement Score** entirely: the v1.13 definition ("composite that rewards varied vocabulary, active verbs, and sensory grounding") was unmeasurable, and a standalone score for "engagement" that ignores the underlying metrics is the exact opacity this routine exists to correct. Rewrote **Emotion Tells** as filter-word constructions (subject + filter verb + emotion word) grounded in the publishing-industry filter-words literature (Allen, Hardy, Steinemann, Harnby); both lists are editable. Rewrote **Slow Pacing** as a three-condition paragraph rule: zero dialogue AND zero action-verb matches AND length > 50 words; action-verb list editable. Defined **Style Score** formula explicitly: one flagged sentence = one sentence containing any pattern match, not a per-match count. Defined **Sentence Variety** mapping explicitly: clamp(stddev / 2.0, 0, 10), which anchors the >= 5.0 threshold to a stddev of 10 words (empirical fiction baseline per Sichel 1974). Rewrote **Weak Adverbs** against an explicit weak-verb list, replacing the "substitutes for a stronger verb" judgment clause. Rewrote **Long Repeated Phrases** with two editable parameters (minimum phrase length 5, minimum occurrences 3) and tiered output (flagged phrases scored, diagnostic top-20 informational-only); defaults grounded in Biber/Conrad/Cortes lexical-bundle research. Updated tokenizer requirements, auto-fix tiers, genre sensitivity table, and genre threshold matrix to reflect all changes. Total goals count updated from 16 to 20-max (with dialogue and sample-size exemptions explicit). Rationale: if a metric is not mechanically defined, it is not a metric, it is a vibe. The article thesis requires that every number in a report trace back to a line in this document the author can read, argue with, and override.
- v1.13 - Grounded Voice Consistency and Performance Tag Rate thresholds in Elliott Slaughter's 2020 empirical dialogue-tag study (hand-counted tag distributions across LOTR, Pride and Prejudice, Harry Potter 1, and The President Is Missing). Lowered Voice Consistency universal threshold from >= 60% to >= 50% (Austen floor at 50% and not considered drifting). Revised Performance Tag Rate genre matrix to align with measured values: Universal < 18%, F1 Literary < 18% (P&P anchor), F2 Thriller < 10% (President at 7%), F4 SFF < 22% (LOTR 15%, HP1 18%), F5 Horror < 25% (kept above F4 for genre convention), others tightened proportionally. Added "Empirical grounding" paragraph to the Dialogue Tags heuristic section crediting Slaughter and disclosing the n=4 sample-size caveat. Rationale: v1.12 thresholds were reasonable spitballs but had no stated source; Slaughter is the most directly applicable publicly available work (n=4 books, 3 genres, hand-counted) and gives the numbers a defensible floor. Thresholds remain editable per the standards-document philosophy; this establishes a grounded default rather than a corpus-validated norm.
- v1.12 - Replaced the legacy "Unusual Dialogue Tags" metric (< N% of tags not "said" or "asked") with two separate metrics: Voice Consistency (dominant tag verb as % of all tags, universal threshold >= 60%) and Performance Tag Rate (% of tags drawn from an explicit performance-verb list, genre-sensitive threshold). Rationale: the legacy metric conflated two different failure modes — voice drift (author doesn't know what they sound like) and verb-crutch (tags doing emotion-work prose should do) — and scored both against a hard-coded word list that ignored genre. Surfaced by a horror-genre canary run where genre-native tag verbs were flagged as unusual and produced a 33% score on a 6-tag sample. Added a 15-tag sample-size floor below which both new metrics read N/A with the disclosure "You have fewer than 15 tags, this is not enough for evaluation." Added explicit editable Invisible and Performance tag-verb lists (Mode 3 persists to `user_config.json` under a `tag_verbs` field).
- v1.11 - Collapsed Computation Method to Precise-only. Removed Ballpark eye-survey as a user-facing option after a canary run showed eye-survey counts missing the tokenizer by 15+ percentage points on Glue Index and by roughly 12x on Long Repeated Phrases. Error ranges at that scale are not "directional," they are wrong enough to misdirect revision. Removed the `computation` field from `user_config.json` since there is no longer a choice to persist. Added Strip Verification as a required routine step between pre-processing and tokenizer execution: an independent verification (ideally delegated to a subagent for fresh eyes) that confirms every declared strip category was removed, no narrative prose was over-stripped, and the word-count delta is plausible. Report's Scope Note now includes a Strip Verification disclosure line. Rationale: every downstream metric divides by the wrong denominator if the stripping pass has a bug, and the author has no way to know; an independent check catches both false-strip and missed-marker failure modes before the tokenizer pollutes the report.
- v1.10 - Declared chapter-level scope as a first-class design principle. Added per-genre `max_chapter_words` values (F1-F5, N1-N5, U, C) anchored to genre convention rather than a universal number; over-scope documents run with a caveat and a beat-sheet-derived split suggestion rather than a hard block. Added per-genre `typical_beat_pattern` strings used as a reference lens. Added a required Beat Sheet section to the Report Format, positioned between What Happened and BLUF; beat sheet is diagnostic only (no score impact), produces structural observations where warranted, and composes with the over-scope split suggestion so structural advice is grounded in visible beats rather than vibes. Closing note on the Beat Sheet: "Claude can make mistakes; use your best judgment." These two features (Beat Sheet and Per-Character Dialogue, pending) are the ones that structurally cannot be done by pattern-matching software and are the primary case for why a language-model-based evaluator is a different tool than PWA.
- v1.9 - Added BLUF (Bottom Line Up Front) as a required report section between "What Happened" and "Scope Note." Three to six bullets: verdict, strongest, weakest, judgment flags, and "if you do one thing." Flat professional tone required. Rewrote Formatting Rules to kill the inherited PWA cheerleading ("Nice work," "Wonderful," "Brilliant," "Fantastic"). Section verdict lines are now direct and numeric - "In range. 85% against a threshold of 80%" replaces "Nice work. Your style is looking good." Rationale: the report is information for the author to act on; a serious evaluator does not cheerlead.
- v1.8 - Rewrote the Spelling heuristic. Old rule ("flag any token not in a standard English dictionary, including foreign words and proper nouns") reproduced exactly the dictionary-lookup stupidity the tool exists to replace. New rule defines a six-step recognition order: English dictionary -> multi-language recognition (the evaluator can read Spanish, French, German, Latin, etc.) -> proper noun recognition from context -> coined/jargon terms verified via web search -> genuine unknowns flagged for review but NOT counted against the score -> genuine misuses flagged and counted. Foreign words, recognized proper nouns, and verified coined terms no longer dock the Spelling Score. Surfaced by a canary run where multilingual text and character names were flagged as "unknown" and cost a percentage point of Spelling Score despite the evaluator being perfectly capable of recognizing them.
- v1.7 - Added Computation Method section (Precise Python tokenizer vs Ballpark eye-survey) as the second router question, with mandatory report disclosure of which method produced the counts. Added a "What Happened" section at the top of the report format (two to three paragraphs summarizing document beats) and a dedicated Scope Note block so pre-processing, computation, and genre are all visible above the fold. The summary serves two purposes: orientation (skim a folder of reports and identify each one at a glance) and comprehension check (if the evaluator cannot describe the piece accurately, the judgment-sensitive scores cannot be trusted). Surfaced by shakedown Finding 3 (scoring was eye-survey not mechanical) combined with the author's observation that a stranger skimming a folder of reports needs orientation faster than the summary section provides.
- v1.6 - Reframed pre-processing from default-driven to author-driven. The router now asks the author what to strip before scoring, using format-specific suggested defaults only as a starting point. Different authors use different markup; forcing a default strips things the author wants scored or leaves things in that skew counts. Added `preprocessing` field to `user_config.json` schema so Mode 3 persists the author's choices.
- v1.5 - Added Pre-processing section. Before any metric is computed, structural elements the narrative reader does not read as prose are stripped: markdown headings and front-matter, DOCX heading/title styles, plain-text chapter titles and bracketed production markers, HTML heading/nav tags. Report scope note must disclose what was stripped. Surfaced by an early shakedown canary run where author-side structural markers would have skewed every metric if counted as prose.
- v1.4 - Stranger-readability pass on the opening. New "What this document is," "Why a standards document exists at all," "If you are reading this because you want to fork it," and "Relationship to ProWritingAid" sections replace the old internal-spec preamble. No threshold, heuristic, or tier change.
- v1.3 - Added File Safety Invariants as a first-class framework rule. Pre-flight path check, "copy" in every working filename, fix log leads with path disclosure, same-day collision rules, and defense-in-depth framing. These now inherit to every prompt in the routine.
- v1.2 - Added Genre Profiles section with 11-genre threshold matrix (10 named profiles plus Universal) and Custom genre construction rules. Genre-sensitive categories now shift thresholds based on user selection; universal categories are unchanged.
- v1.1 - Added Auto-fix Tiers section to support Mode 2 (grammar + spelling fix) and Mode 3 (user config + auto-fix).
- v1.0 - Initial version with thresholds, heuristics, and report format.
