# Mode 0 - Lite (Tokenizer Only)

Run the tokenizer against the document and return the raw metric table. No subagents, no grammar pass, no character dialogue analysis, no summary. Fast mid-draft iteration check.

This is the "just show me the numbers" mode.

---

## Instructions to Claude

### Step 1: Load Standards

Load using the same two-layer approach as Mode 1 Step 1: bundled `{SKILL_BASE}\references\_standards.md` always, then `{{DOC_FOLDER}}\standards.md` (or `STANDARDS_PATH`) as a project override layer if present. Read the Genre Profiles and Category Table. You do not need the subagent sections in Lite mode.

### Step 1a: Establish Genre

Same as Mode 1 Step 1a. The genre determines which threshold column to grade against. Accept genre from the router or ask the user.

### Step 2: Load or Create Config

Look for `{{DOC_FOLDER}}\pwa_config.json`. If it exists, load it silently and report the active strip rules in one plain-English line. If none exists, run the first-run setup interview (see `_standards.md` "Config-driven preprocessing") and write the config before continuing.

### Step 3: Strip the Document

Apply the strip rules from the config. Produce the stripped prose file at:

```
{{DOC_FOLDER}}\[Title] - stripped [YYYY-MM-DD].txt
```

No Strip Verification subagent in Lite mode. Apply a quick sanity check: confirm the word count delta is plausible given the declared strip rules. If the delta looks wrong (> 20% of total words removed on rules that should affect only a few lines), pause and report to the user before continuing.

### Step 4: Run the Tokenizer

Invoke `{SKILL_BASE}\scripts\tokenizer.py`:

```
python "{SKILL_BASE}\scripts\tokenizer.py" \
  --input "{{DOC_FOLDER}}\[Title] - stripped [YYYY-MM-DD].txt" \
  --config "{{DOC_FOLDER}}\pwa_config.json" \
  --out-dir "{{DOC_FOLDER}}"
```

The tokenizer writes its JSON output to `{{DOC_FOLDER}}\[Title] - tokenizer [YYYY-MM-DD].json`.

### Step 5: Render the Metric Table

Read the tokenizer JSON and render a compact metric table. For each category, show:

- Category name
- Value
- Genre-adjusted threshold
- MET / MISSED

**Lite mode table format:**

```
Genre: [selected genre]
Document: [title] — [word count] words, [sentence count] sentences

| Category                    | Value    | Threshold        | Status |
|-----------------------------|----------|------------------|--------|
| Grammar                     | (skipped)|                  | —      |
| Spelling                    | (skipped)|                  | —      |
| Style Score                 | 98.3%    | >= 80%           | MET    |
| Sentence Length (avg)       | 12.4 wds | 9.0 to 18.0      | MET    |
| Sentence Variety            | 6.8      | >= 5.0           | MET    |
| Very Long Sentences         | 2.1%     | < 5%             | MET    |
| Passive Voice               | 8.4%     | < 25%            | MET    |
| Complex Paragraphs          | 14%      | < 20%            | MET    |
| Glue Index                  | 43.1%    | < 40%            | MISSED |
| Weak Adverbs                | 8.2      | < 10.0           | MET    |
| Slow Pacing                 | 18%      | < 30%            | MET    |
| Dialogue Tag Rate           | 68%      | < 75%            | MET    |
| Voice Consistency           | 72%      | >= 50%           | MET    |
| Performance Tag Rate        | 14%      | < 18%            | MET    |
| Dialogue Tags with Adverbs  | 8%       | < 12%            | MET    |
| Emotion Tells               | 12%      | < 20%            | MET    |
| Conjunction Starts          | 6.1%     | < 9%             | MET    |
| -ing Starts                 | 4.2%     | < 6%             | MET    |
| Long Repeated Phrases       | 0        | < 3              | MET    |
| Acronym Consistency         | 100%     | 100%             | MET    |
| Quote Consistency           | 100%     | 100%             | MET    |
| Character Dialogue          | (skipped)|                  | —      |

Goals met: 18 / 20 scored. Grammar, Spelling, and Character Dialogue skipped in Lite mode.
```

Mark Grammar, Spelling, and Character Dialogue as `(skipped)` — they require subagents not run in Lite mode. Exclude them from the goals denominator.

For any MISSED category, append the top 3 flagged items from the tokenizer's `flagged_items` array directly in the table row as a sub-list, so the author can act immediately without opening the JSON.

### Step 6: Deliver

Return the metric table inline (no separate file). Optionally note:

> Run Mode 1 for the full report with Grammar/Spelling and Character Dialogue analysis. Run Mode 2 to also apply grammar and spelling fixes.

Do not save a PWA report file. The only output files are the stripped prose and the tokenizer JSON, both in `{{DOC_FOLDER}}`.

---

## What Lite Mode Skips

- Grammar and Spelling pass (requires subagent)
- Strip Verification subagent
- Summary and Beat Sheet subagent
- Character Dialogue Consistency subagent
- Report Verification subagent
- PWA report file

## What Lite Mode Produces

- Stripped prose file
- Tokenizer JSON
- Inline metric table in chat

---

## When to Use Lite Mode

- Mid-draft pulse checks where the author wants numbers fast, not a full report
- Iterating on a specific metric (e.g., glue index) across multiple drafts without waiting for subagents
- Testing a new strip config against a document before committing to a full Mode 1 run

---

## Inputs Expected

- Path to the document (required)
- Genre selection (required)
- Standards document path (optional; if not supplied, Step 1 falls back to the bundled `{SKILL_BASE}\references\_standards.md`)
- Optional: title override
