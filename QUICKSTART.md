# Canary — Quick Start

Canary is a writing evaluation skill. You give it a document; it gives you a scored report against a set of craft standards you provide.

---

## What You Need

**Before your first run, have two things ready:**

1. **Your document** — any prose file (.txt, .md, .docx, .pdf). Fiction, nonfiction, or academic.
2. **A genre selection** — Canary grades against genre-appropriate thresholds. Options: F1 Literary, F2 Thriller, F3 Romance, F4 SFF, F5 Horror, NF1 Narrative Nonfiction, NF2 Academic/Technical, or Custom (you describe the blend).

Canary ships with a built-in standards reference (`canary/references/_standards.md`) covering all thresholds, genre profiles, and evaluation criteria. You do not need to supply a standards file to get started. If you want to define project-specific rules — banned phrases, threshold adjustments, required elements, voice fingerprints — Canary includes a **standards builder** that walks you through a 5-15 minute interview and writes a `standards.md` to your project folder. On first run, Canary will offer to run the builder automatically. You can also trigger it any time by saying "run the standards builder."

---

## Pick a Mode

| Mode | What it does | When to use it |
|------|--------------|----------------|
| **Mode 0 - Lite** | Tokenizer metrics only, no subagents | Mid-draft pulse check; fast iteration |
| **Mode 1 - Report** | Full scored report with grammar, dialogue, and beat analysis | Pre-submission review; first look at a new draft |
| **Mode 2 - Grammar Fix** | Full report + grammar and spelling fixes applied to a copy | Copyedit pass; grammar cleanup before beta readers |
| **Mode 3 - Auto-fix** | Full report + user-configured auto-fixes across multiple categories | Final polish pass; author-directed cleanup |

Start with Mode 1 if you are not sure.

---

## First Run

1. Place your document in a folder.
2. Run Canary and specify the document path and genre.
4. On first run, Canary will ask you three quick questions about what to skip when scoring (headings, markers, etc.) and write a `pwa_config.json` config file to your document folder.
5. The config is reused on every future run. You will see a one-line summary and can update it if your manuscript format changes.

---

## What You Get

**Mode 1 produces:**
- A PWA report file: `[Title] - PWA Review [YYYY-MM-DD].md`
- A tokenizer JSON: `[Title] - tokenizer [YYYY-MM-DD].json`
- A stripped prose file: `[Title] - stripped [YYYY-MM-DD].txt`
- A marker map (if you use paired delimiters): `[Title] - marker map [YYYY-MM-DD].json`

**Mode 2 adds:**
- An edited copy: `[Title] - edited copy [YYYY-MM-DD].[ext]`
- A fix log: `[Title] - Grammar+Spelling Fixlog [YYYY-MM-DD].md`

**Mode 3 adds:**
- A working copy with all approved fixes applied: `[Title] - auto-fixed copy [YYYY-MM-DD].[ext]`
- An auto-fix log: `[Title] - Auto-fix Log [YYYY-MM-DD].md`
- A saved config: `user_config.json`

The original document is never modified. Every output file has the date in its name.

---

## Config Files

Two config files live in your document folder after first run:

- **`pwa_config.json`** — strip rules (what to skip when scoring) and exclusion lists. Written at first-run setup. Edit anytime via the restart prompt.
- **`user_config.json`** — Mode 3 settings: genre, threshold overrides, which categories to auto-fix, exclusions. Written at the end of Mode 3 Step 6.

---

## Genre Options

| Code | Profile |
|------|---------|
| F1 | Literary Fiction |
| F2 | Thriller / Crime |
| F3 | Romance |
| F4 | Science Fiction / Fantasy |
| F5 | Horror / Gothic |
| NF1 | Narrative Nonfiction / Memoir |
| NF2 | Academic / Technical |
| U | Universal (genre-neutral defaults) |
| C | Custom (you describe the blend) |

For Custom, Canary will ask you to describe the work, pick the closest genre profiles, and set the blend weights.

---

## What Canary Does Not Do

- It does not modify your original document.
- It does not invent plot events, characters, or claims — everything in a Mode 1 report traces back to your document or the tokenizer output.
- It does not compare your work against other authors or external corpora beyond the thresholds in your standards file.
- It does not provide line-by-line developmental feedback. It provides scored metrics and flagged items you can act on.

---

## More Detail

- Full standards reference: `canary/references/_standards.md`
- Mode instructions: `canary/references/mode_0_lite.md`, `mode_1_report_only.md`, `mode_2_grammar_spelling_fix.md`, `mode_3_user_config_autofix.md`
- Tokenizer script: `canary/scripts/tokenizer.py`
- Config template: `canary/references/pwa_config.json`
