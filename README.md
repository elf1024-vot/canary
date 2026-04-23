# Canary

A writing-evaluation skill for [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) and Cowork. Canary runs a ProWritingAid-style report over fiction or non-fiction manuscripts, grading them against genre-specific thresholds and producing a scored report with flagged-issue tables for every craft category.

**Current version:** Skill v1.2 (routine v1.25.1)

## What Canary does

Given a manuscript file (`.txt`, `.md`, `.docx`, `.html`), Canary:

1. Strips headers, production markers, and paired-delimiter blocks per a per-manuscript config.
2. Tokenizes the stripped prose with a Python tokenizer that computes every mechanical metric (sentence length, variety, glue index, passive voice, emotion tells, weak adverbs, pacing, repeats, dialogue tags, and more).
3. Dispatches five validator-gated subagents: Strip Verification, Summary + Beat Sheet, Grammar + Spelling, Character Dialogue Consistency, and Report Verification.
4. Scores the manuscript against the chosen genre profile (F1 Literary through F5 Horror, N1 Journalism through N5 Popular Science, or a custom weighted blend).
5. Produces a single `.md` report with a BLUF, full category-by-category analysis, and flagged-item tables that name the actual text of every flag so authors can jump straight to each issue.

Canary never modifies the source file. All outputs land in the manuscript's folder with the date in the filename.

## Three modes

- **Mode 1 - Report only.** Score the document. No changes to any file.
- **Mode 2 - Grammar + spelling fix.** Apply safe-tier grammar and spelling fixes to a clearly-named copy. Report alongside.
- **Mode 3 - Full config + auto-fix.** Run the report, surface deviations, apply configured safe + prompt-tier fixes to a copy.

All three modes produce the same scored report. Mode 2 and Mode 3 additionally produce a fixed copy and a change log.

## Installation

Canary is distributed as a `.skill` bundle. See [Anthropic's skills documentation](https://docs.claude.com/en/docs/claude-code/slash-commands#skills) for how to install a skill.

Quick install for Cowork users:

1. Download `canary.skill` from this repo.
2. Place it in your Claude Code skills directory or install through the Cowork plugin manager.
3. Invoke with `/canary` and pass a document path.

## Development layout

This repo keeps two copies of the skill in sync:

- **`canary/`** - the unpacked source of truth. Edit files here.
- **`canary.skill`** - the packed zip bundle. Rebuild after any edit with `python scripts/pack-skill.py`.

The `pack-skill.py` helper zips `canary/` into `canary.skill` deterministically (file order preserved, external attributes normalized to `0o100644`).

## Architecture

The skill runs a small router (`canary/scripts/router/`) against the main conversation context. The router dispatches five subagents via the Task tool, validates each one's JSON output, and re-dispatches up to once on failure. If a second-attempt failure is purely schema-shape with valid content beneath, the router may apply deterministic mechanical normalization rather than hard-stopping, with explicit Scope Note disclosure (added in routine v1.25.1).

Subagent prompts live in `canary/references/subagents/` and are versioned independently. Each one produces strict JSON matching a literal schema; the router's validators in `canary/scripts/router/validators/` substring-check citations against source files, bound-check numeric metrics, and enumerate exact field names.

The full specification - gates, thresholds, genre profiles, detection heuristics, formatting rules - lives in `canary/references/_standards.md`. All prompts inherit from it by reference; no gate definition lives in more than one place.

## Genre profiles

Eleven named profiles plus Universal plus Custom:

- **Fiction:** F1 Literary/Upmarket, F2 Thriller/Suspense/Crime, F3 Romance, F4 SciFi/Fantasy, F5 Horror/Gothic.
- **Non-fiction:** N1 Journalism/Reportage, N2 Memoir/Personal Essay, N3 Business/Self-help, N4 Academic/Scholarly, N5 Popular Science/Narrative Non-fiction.
- **Universal** (flat defaults) for works that resist genre classification.
- **Custom** builds a weighted-average profile from two or more named genres.

Each profile sets genre-sensitive thresholds (sentence length range, sentence variety floor, passive voice ceiling, slow pacing ceiling, dialogue tag rate, etc.). Universal-category thresholds (grammar, spelling, style, acronym consistency) never shift by genre.

## Safety contract

Every Canary run states a verbatim safety guarantee before any other output:

> Your original file is never modified. All edits are written to a clearly named copy. The original path is treated as read-only for the entire run.

The skill enforces this with pre-flight path checks, same-day collision handling (`-v2`, `-v3`), and working-copy filenames that always contain the word "copy" or "fixed." The contract is non-negotiable and documented as a File Safety Invariants section in `_standards.md`.

## Contributing

Issues and PRs welcome. The skill is under active development and versioning is tracked per-file in each prompt's Version History footer.

## License

MIT. See `LICENSE`.
