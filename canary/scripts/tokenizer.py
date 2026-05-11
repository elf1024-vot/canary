"""PWA / Canary v1.24 config-aware tokenizer.

Reads stripped prose (output of strip_engine.py) and a merged pwa_config.json,
emits one JSON blob with per-metric counts and flagged_items arrays. Honors the
three v1.22 editable exclusion lists:

  - acronym_emphasis_exclusions   (Acronym Consistency detector)
  - weak_adverb_noun_exclusions   (Weak Adverbs detector)
  - ing_starts_proper_noun_exclusions  (-ing Starts detector)

Per-category schema follows _standards.md v1.22 'Flagged Items Schema' and the
per-detector 'Flagged items' subsections.

Usage:
    python tokenizer.py \\
        --stripped "C:\\path\\to\\stripped.txt" \\
        --title "Chapter 1" \\
        [--config "C:\\path\\to\\manuscript\\pwa_config.json"] \\
        [--routine-config "C:\\path\\to\\routine\\pwa_config.json"] \\
        [--out-dir "C:\\path\\to\\temp"] \\
        [--date YYYY-MM-DD]

Writes:
    <out_dir>/<title> - tokenizer <date>.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import os
import re
import sys
from collections import Counter
from typing import Any

# Reuse the strip engine's config loader so merge semantics are identical.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_engine import load_config  # noqa: E402

# ---------------------------------------------------------------------------
# Word lists from _standards.md v1.22.
# ---------------------------------------------------------------------------

WEAK_VERBS = {
    "said", "asked", "replied", "answered", "whispered", "shouted", "cried",
    "gasped", "sighed", "went", "walked", "ran", "looked", "saw", "heard",
    "was", "were", "felt", "moved", "turned", "reached", "opened", "closed",
    "stood", "sat", "came", "got", "put", "took",
}

INVISIBLE_TAGS = {
    "said", "asked", "replied", "answered", "added", "continued", "began",
}

PERFORMANCE_TAGS = {
    "whispered", "hissed", "murmured", "growled", "snarled", "barked", "spat",
    "gasped", "breathed", "sighed", "laughed", "cried", "yelled", "shouted",
    "screamed", "bellowed", "mumbled", "muttered", "called", "stammered",
    "croaked", "rasped", "purred", "drawled", "snapped",
}

FILTER_VERBS = {
    "felt", "feels", "feeling", "was", "were", "is", "am", "are", "seemed",
    "looked", "watched", "heard", "saw", "noticed", "noted", "realized",
    "thought", "wondered", "decided", "knew", "understood", "considered",
    "believed", "assumed", "pondered", "perceived",
}

EMOTION_WORDS = {
    "sad", "happy", "angry", "afraid", "scared", "terrified", "nervous",
    "anxious", "excited", "relieved", "embarrassed", "ashamed", "guilty",
    "proud", "jealous", "confused", "surprised", "shocked", "disgusted",
    "tired", "exhausted", "bored", "frustrated", "furious", "calm", "content",
    "lonely", "worried", "hopeful", "hopeless", "desperate", "helpless",
    "overwhelmed", "numb", "empty", "hollow", "cold", "hot", "dizzy", "sick",
    "weak",
}

ACTION_VERBS = {
    "ran", "walked", "jumped", "grabbed", "pulled", "pushed", "threw",
    "opened", "closed", "slammed", "turned", "reached", "stood", "sat",
    "fell", "crossed", "entered", "left", "shouted", "whispered", "said",
    "asked", "replied", "answered", "stepped", "climbed", "drove", "rode",
    "flew", "swam", "dove", "lunged", "struck", "hit", "kicked", "shoved",
    "caught", "released", "dropped", "lifted", "carried", "placed", "set",
    "took", "put", "handed", "tossed", "rolled", "crawled", "knelt", "rose",
    "bent", "leaned", "spun", "pivoted", "moved", "shifted", "slipped",
    "crept", "raced", "sprinted", "dashed", "charged", "fled", "chased",
    "followed", "led",
}

GLUE_WORDS = {
    "of", "in", "to", "for", "and", "the", "a", "is", "was", "it", "that",
    "this", "with", "as", "but", "on", "at", "by",
    # auxiliary verbs
    "be", "been", "being", "am", "are", "were", "do", "does", "did",
    "have", "has", "had", "shall", "should", "will", "would", "may", "might",
    "must", "can", "could",
}

CONJUNCTION_OPENERS = {"and", "but", "so", "or", "yet"}

# Style patterns: (regex, replacement_or_label, suggestion).
# Each tuple = (compiled_pattern, "pattern label string", "suggestion string").
def _compile_style_patterns() -> list[tuple[re.Pattern[str], str, str]]:
    raw = [
        (r"\bthe kind of\b", "the kind of -> the", "the"),
        (r"\ba kind of\b", "a kind of -> a", "a"),
        (r"\bthe fact that\b", "the fact that -> that", "that"),
        (r"\ba particular kind of\b", "a particular kind of -> a particular", "a particular"),
        (r"\ba different kind of\b", "a different kind of -> a different", "a different"),
        (r"\bwas learning that\b", "was learning that -> learned that", "learned that"),
        (r"\bbegan to \w+", "began to X -> simple past X-ed", "simple past"),
        (r"\bstarted to \w+", "started to X -> X-ed", "X-ed"),
        (r"\bmade the decision to \w+", "made the decision to X -> decided to X", "decided to X"),
        (r"\bmanaged to \w+", "managed to X -> past tense X-ed", "past tense"),
        (r"\bfound (himself|herself|themself|themselves|myself|ourselves) \w+ing\b",
         "found himself/herself X-ing -> simple past", "simple past"),
        (r"\bindicate(s)?\b", "indicate -> show", "show"),
        (r"\bdemonstrate(s|d)?\b", "demonstrate -> show", "show"),
        (r"\bassistance\b", "assistance -> help", "help"),
        (r"\bmethodology\b", "methodology -> method", "method"),
        (r"\binitiated\b", "initiated -> started", "started"),
        (r"\bterminated\b", "terminated -> ended", "ended"),
        (r"\bprocured\b", "procured -> bought", "bought"),
        (r"\brelocated\b", "relocated -> moved", "moved"),
        (r"\banticipated\b", "anticipated -> expected", "expected"),
        (r"\bacquired\b", "acquired -> gained", "gained"),
        (r"\bobjective\b", "objective -> aim", "aim"),
        (r"\bin the corner of the \w+", "in the corner of the X -> in the X's corner", "in the X's corner"),
        (r"\bin the presence of \w+", "in the presence of X -> in X's presence", "in X's presence"),
        (r"\bwas intended to be\b", "was intended to be -> was", "was"),
        (r"\bwas either\b", "was either -> was", "was"),
        (r"\bdidn't say anything\b", "didn't say anything -> said nothing", "said nothing"),
        (r"\bhad no idea\b", "had no idea -> informal", "(informal)"),
        (r"\bvery [a-z]+", "very [adj/adv] -> stronger word or drop", "stronger word"),
        (r"\breally [a-z]+", "really [X] -> stronger word", "stronger word"),
        (r"\bwishful thinking\b", "wishful thinking -> avoid cliches", "avoid cliche"),
    ]
    return [(re.compile(p, re.IGNORECASE), label, suggestion) for p, label, suggestion in raw]


STYLE_PATTERNS = _compile_style_patterns()


# Acronym candidate: 2+ ALL-CAPS letters, optionally with periods between
# (FBI, F.B.I., F B I are all candidates). Excludes single-letter "I".
ACRONYM_PATTERN = re.compile(r"\b(?:[A-Z](?:\.?[A-Z])+)\b")
ACRONYM_EXCLUDE_TOKENS = {"I", "OK"}

# Sentence splitter: simple but conservative — splits on . ! ? followed by
# whitespace + uppercase letter, treating quotes and parentheses gently.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?\u201d\"\'])\s+(?=[A-Z\"\u201c\(])")

# Quoted dialogue detector (curly + straight double quotes).
QUOTED_DIALOGUE = re.compile(
    r"(?:\u201c[^\u201d]+\u201d|\"[^\"]+\")"
)

# Tag verb regex: matches `<quote>, <subject> <verb>` after dialogue.
# Captures verb in group 1.
TAG_AFTER_QUOTE = re.compile(
    r"(?:\u201d|\")\s*,?\s*(?:[A-Z][a-z]+\s+|he\s+|she\s+|they\s+|I\s+|we\s+)([a-z]+)",
)

# Past participle detector for passive: simple heuristic.
TO_BE = {"is", "was", "were", "are", "am", "be", "been", "being"}
# Common past-participle endings (very approximate; English is ugly).
PAST_PARTICIPLE_RE = re.compile(r"\b\w+(?:ed|en|wn|de|le|st|nt|rn|ck|me|nk|t)\b", re.IGNORECASE)
# Subset of common irregular past participles to bolster recall.
IRREGULAR_PARTICIPLES = {
    "taken", "given", "broken", "spoken", "written", "stolen", "frozen",
    "chosen", "forgotten", "hidden", "ridden", "shown", "thrown", "drawn",
    "known", "grown", "blown", "gone", "done", "seen", "made", "held",
    "told", "said", "found", "left", "kept", "felt", "heard", "brought",
    "caught", "taught", "bought", "thought", "fought", "got", "had", "put",
    "set", "cut", "hit", "let", "shut", "spent", "sent", "lost", "built",
    "burned", "burnt",
}


def looks_like_past_participle(token: str) -> bool:
    t = token.lower().strip(".,;:!?\"'\u201c\u201d")
    if t in IRREGULAR_PARTICIPLES:
        return True
    if t.endswith("ed") and len(t) > 3:
        return True
    if t.endswith("en") and len(t) > 3:
        return True
    return False


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def split_sentences(paragraph: str) -> list[str]:
    # Replace newlines inside a paragraph with spaces so the splitter sees a
    # single line.
    normalized = re.sub(r"\s+", " ", paragraph).strip()
    if not normalized:
        return []
    parts = SENTENCE_SPLIT.split(normalized)
    return [p.strip() for p in parts if p.strip()]


def words_in(text: str) -> list[str]:
    return re.findall(r"\b[\w'\u2019-]+\b", text)


def lowercase_token(token: str) -> str:
    return token.lower().strip(".,;:!?\"'\u201c\u201d-")


# ---------------------------------------------------------------------------
# Per-category detectors.
# ---------------------------------------------------------------------------


def detect_basics(paragraphs: list[str]) -> dict[str, Any]:
    sentences_by_para: list[list[str]] = []
    sent_lengths: list[int] = []
    total_words = 0

    for p in paragraphs:
        sents = split_sentences(p)
        sentences_by_para.append(sents)
        for s in sents:
            ws = words_in(s)
            sent_lengths.append(len(ws))
            total_words += len(ws)

    sent_count = len(sent_lengths)
    avg_sent_len = (sum(sent_lengths) / sent_count) if sent_count else 0
    if sent_count > 1:
        mean = avg_sent_len
        variance = sum((x - mean) ** 2 for x in sent_lengths) / (sent_count - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0
    variety_score = max(0.0, min(10.0, stddev / 2.0))

    return {
        "paragraph_count": len(paragraphs),
        "sentence_count": sent_count,
        "word_count": total_words,
        "average_sentence_length": round(avg_sent_len, 2),
        "sentence_length_stddev": round(stddev, 2),
        "sentence_variety_score": round(variety_score, 2),
        "_sentences_by_para": sentences_by_para,
        "_sent_lengths": sent_lengths,
    }


def detect_very_long_sentences(sentences_by_para: list[list[str]]) -> dict[str, Any]:
    flagged: list[dict[str, Any]] = []
    count = 0
    for p_idx, sents in enumerate(sentences_by_para, start=1):
        for s in sents:
            wc = len(words_in(s))
            if wc > 30:
                count += 1
                flagged.append({
                    "text": s,
                    "paragraph": p_idx,
                    "rule": "very-long-sentence",
                    "word_count": wc,
                })
    return {"count": count, "flagged_items": flagged}


def detect_complex_paragraphs(paragraphs: list[str], sentences_by_para: list[list[str]]) -> dict[str, Any]:
    flagged: list[dict[str, Any]] = []
    count = 0
    for p_idx, (p, sents) in enumerate(zip(paragraphs, sentences_by_para), start=1):
        if len(sents) <= 3:
            continue
        sent_lens = [len(words_in(s)) for s in sents]
        avg = sum(sent_lens) / len(sent_lens) if sent_lens else 0
        if avg > 20:
            count += 1
            words = words_in(p)
            preview = " ".join(words[:25]) + ("..." if len(words) > 25 else "")
            flagged.append({
                "text": preview,
                "paragraph": p_idx,
                "rule": "complex-paragraph",
                "avg_sentence_length": round(avg, 1),
                "sentence_count": len(sents),
            })
    return {"count": count, "flagged_items": flagged}


def detect_glue_index(text: str) -> dict[str, Any]:
    words = [w.lower() for w in words_in(text)]
    if not words:
        return {"glue_word_count": 0, "total_words": 0, "glue_index": 0.0}
    glue = sum(1 for w in words if w in GLUE_WORDS)
    return {
        "glue_word_count": glue,
        "total_words": len(words),
        "glue_index": round(glue / len(words), 4),
        "glue_index_pct": round(100 * glue / len(words), 2),
    }


def detect_conjunction_starts(sentences_by_para: list[list[str]]) -> dict[str, Any]:
    flagged: list[dict[str, Any]] = []
    total = 0
    count = 0
    for p_idx, sents in enumerate(sentences_by_para, start=1):
        for s in sents:
            total += 1
            ws = words_in(s)
            if not ws:
                continue
            first = ws[0].lower()
            if first in CONJUNCTION_OPENERS:
                count += 1
                flagged.append({
                    "text": s,
                    "paragraph": p_idx,
                    "rule": "conjunction-start",
                    "opener": ws[0],
                })
    pct = round(100 * count / total, 2) if total else 0.0
    return {"count": count, "total_sentences": total, "pct": pct, "flagged_items": flagged}


def detect_ing_starts(
    sentences_by_para: list[list[str]],
    full_text: str,
    exclusion_list: list[str],
) -> dict[str, Any]:
    """Apply v1.22 proper-noun + non-participle exclusion."""
    excl = {x.lower() for x in exclusion_list}
    # Build the inventory of tokens AS-WRITTEN (case-preserved). The
    # _standards.md heuristic says: a capitalized -ing opener counts as a
    # real participle only if the same word appears LOWERCASE somewhere
    # else in the chapter (which establishes it as a normal verb form).
    # Lowercasing every word and then checking membership is meaningless
    # because the capitalized opener itself lowercases into the set.
    raw_inventory = words_in(full_text)
    literal_token_set = set(raw_inventory)

    flagged: list[dict[str, Any]] = []
    total = 0
    count = 0
    for p_idx, sents in enumerate(sentences_by_para, start=1):
        for s in sents:
            total += 1
            ws = words_in(s)
            if not ws:
                continue
            first = ws[0]
            first_lower = first.lower()
            if not first_lower.endswith("ing"):
                continue
            if first_lower in excl:
                continue
            # Require that either: (a) the lowercased form appears elsewhere
            # in the chapter (so it's a normal verb form), or (b) the token
            # is already lowercase in the source (sentence opener that's
            # natively lowercase only happens after a colon, but allow it).
            # The literal lowercase form must appear as a token elsewhere
            # in the chapter (this rules out proper nouns whose only form
            # ever used in the chapter is the capitalized one, like 'Sterling').
            same_word_appears_lowercased_elsewhere = first_lower in literal_token_set
            if not same_word_appears_lowercased_elsewhere:
                # Could still be a real participle. Apply morphological check:
                # known participle patterns end in <verb-stem>ing; we approximate
                # by accepting tokens whose stem (minus 'ing') is a verb-shaped
                # word OR matches a known verb stem. To stay simple and avoid
                # false negatives on rare verbs, fall back to: accept if the
                # token is reasonably common -ing form (length >= 5 and ending
                # 'ing' and not in proper-noun exclusion list).
                # The safest move per _standards.md is to be conservative when
                # uncertain. We'll skip rather than flag when no lowercase
                # evidence exists; an early canary run surfaced false positives
                # on capitalized proper nouns and multi-syllable -ing words.
                continue
            count += 1
            flagged.append({
                "text": s,
                "paragraph": p_idx,
                "rule": "ing-start",
                "opener": first,
            })
    pct = round(100 * count / total, 2) if total else 0.0
    return {"count": count, "total_sentences": total, "pct": pct, "flagged_items": flagged}


def detect_passive_voice(sentences_by_para: list[list[str]]) -> dict[str, Any]:
    flagged: list[dict[str, Any]] = []
    count = 0
    sent_count = 0
    for p_idx, sents in enumerate(sentences_by_para, start=1):
        for s in sents:
            sent_count += 1
            ws = words_in(s)
            for i, w in enumerate(ws[:-1]):
                if w.lower() in TO_BE and looks_like_past_participle(ws[i + 1]):
                    count += 1
                    flagged.append({
                        "text": s,
                        "paragraph": p_idx,
                        "rule": "passive-construction",
                        "matched_phrase": f"{w} {ws[i + 1]}",
                    })
                    break  # one passive per sentence is enough for the count
    per_100 = round(100 * count / sent_count, 2) if sent_count else 0.0
    return {
        "count": count,
        "total_sentences": sent_count,
        "passives_per_100_sentences": per_100,
        "flagged_items": flagged,
    }


def detect_weak_adverbs(
    sentences_by_para: list[list[str]],
    word_count: int,
    noun_exclusions: list[str],
) -> dict[str, Any]:
    """v1.22 noun exclusion list is consulted before counting -ly tokens."""
    excl = {x.lower() for x in noun_exclusions}
    tag_verbs = INVISIBLE_TAGS | PERFORMANCE_TAGS
    flagged: list[dict[str, Any]] = []
    count = 0
    for p_idx, sents in enumerate(sentences_by_para, start=1):
        for s in sents:
            ws = words_in(s)
            for i, w in enumerate(ws):
                lw = w.lower()
                if not lw.endswith("ly"):
                    continue
                if len(lw) <= 3:
                    continue
                if lw in excl:
                    continue
                # Check adjacency to a tag verb or weak verb.
                adjacent: tuple[str, str] | None = None
                rule = None
                if i > 0:
                    prev = ws[i - 1].lower()
                    if prev in tag_verbs:
                        adjacent = (prev, w)
                        rule = "weak-adverb-adjacent-to-dialogue-tag"
                    elif prev in WEAK_VERBS:
                        adjacent = (prev, w)
                        rule = "weak-adverb-adjacent-to-weak-verb"
                if adjacent is None and i + 1 < len(ws):
                    nxt = ws[i + 1].lower()
                    if nxt in tag_verbs:
                        adjacent = (w, ws[i + 1])
                        rule = "weak-adverb-adjacent-to-dialogue-tag"
                    elif nxt in WEAK_VERBS:
                        adjacent = (w, ws[i + 1])
                        rule = "weak-adverb-adjacent-to-weak-verb"
                if adjacent is None:
                    continue
                count += 1
                flagged.append({
                    "text": s,
                    "paragraph": p_idx,
                    "rule": rule,
                    "adverb": w if adjacent[1] == w else w,
                    "verb": adjacent[0] if adjacent[1] == w else adjacent[1],
                    "matched_phrase": " ".join(adjacent),
                })
    per_1000 = round(1000 * count / word_count, 2) if word_count else 0.0
    return {
        "count": count,
        "weak_adverbs_per_1000_words": per_1000,
        "flagged_items": flagged,
    }


def detect_emotion_tells(sentences_by_para: list[list[str]]) -> dict[str, Any]:
    flagged: list[dict[str, Any]] = []
    sent_count = 0
    sent_with_tell = 0
    pronouns = {"he", "she", "they", "i", "we"}
    for p_idx, sents in enumerate(sentences_by_para, start=1):
        for s in sents:
            sent_count += 1
            ws = words_in(s)
            this_sent_flagged = False
            for i in range(len(ws) - 2):
                w0, w1, w2 = ws[i].lower(), ws[i + 1].lower(), ws[i + 2].lower()
                # Subject can be pronoun, "I"/"We", or proper noun (capitalized in source).
                subject_is_proper = ws[i][:1].isupper() and ws[i].isalpha()
                subject_ok = w0 in pronouns or subject_is_proper
                if not subject_ok:
                    continue
                if w1 not in FILTER_VERBS:
                    continue
                if w2 not in EMOTION_WORDS:
                    continue
                if not this_sent_flagged:
                    sent_with_tell += 1
                    this_sent_flagged = True
                flagged.append({
                    "text": s,
                    "paragraph": p_idx,
                    "rule": "filter-construction",
                    "filter_verb": w1,
                    "emotion_word": w2,
                    "subject": ws[i],
                })
    pct = round(100 * sent_with_tell / sent_count, 2) if sent_count else 0.0
    return {
        "count": sent_with_tell,
        "total_sentences": sent_count,
        "pct": pct,
        "flagged_items": flagged,
    }


def detect_slow_pacing(paragraphs: list[str]) -> dict[str, Any]:
    flagged: list[dict[str, Any]] = []
    count = 0
    total_eligible = 0
    for p_idx, p in enumerate(paragraphs, start=1):
        ws = words_in(p)
        if len(ws) <= 50:
            continue
        total_eligible += 1
        if QUOTED_DIALOGUE.search(p):
            continue
        # Action verb test (case-insensitive, any inflection: stem startswith match).
        lower_words = {lowercase_token(w) for w in ws}
        if lower_words & ACTION_VERBS:
            continue
        count += 1
        preview = " ".join(ws[:25]) + ("..." if len(ws) > 25 else "")
        flagged.append({
            "text": preview,
            "paragraph": p_idx,
            "rule": "slow-pacing",
            "word_count": len(ws),
        })
    pct = round(100 * count / len(paragraphs), 2) if paragraphs else 0.0
    return {
        "count": count,
        "total_paragraphs": len(paragraphs),
        "eligible_paragraphs": total_eligible,
        "pct_of_all_paragraphs": pct,
        "flagged_items": flagged,
    }


def detect_style_score(sentences_by_para: list[list[str]]) -> dict[str, Any]:
    flagged: list[dict[str, Any]] = []
    flagged_sentence_count = 0
    sent_count = 0
    for p_idx, sents in enumerate(sentences_by_para, start=1):
        for s in sents:
            sent_count += 1
            sentence_flagged = False
            for pat, label, suggestion in STYLE_PATTERNS:
                m = pat.search(s)
                if not m:
                    continue
                if not sentence_flagged:
                    flagged_sentence_count += 1
                    sentence_flagged = True
                flagged.append({
                    "text": s,
                    "paragraph": p_idx,
                    "pattern": label,
                    "matched_phrase": m.group(0),
                    "suggestion": suggestion,
                })
    pct_clean = round(100 * (sent_count - flagged_sentence_count) / sent_count, 2) if sent_count else 0.0
    return {
        "flagged_sentence_count": flagged_sentence_count,
        "total_sentences": sent_count,
        "style_score_pct": pct_clean,
        "flagged_items": flagged,
    }


def detect_long_repeated_phrases(text: str, min_length: int = 5, min_occurrences: int = 3) -> dict[str, Any]:
    paragraphs = split_paragraphs(text)
    # Build a flat token stream + a parallel paragraph-index stream.
    tokens: list[str] = []
    para_index_per_token: list[int] = []
    for p_idx, p in enumerate(paragraphs, start=1):
        for w in words_in(p):
            tokens.append(w.lower())
            para_index_per_token.append(p_idx)

    # Slide a window of size min_length across tokens.
    counts: Counter[tuple[str, ...]] = Counter()
    occurrences: dict[tuple[str, ...], list[int]] = {}
    for i in range(len(tokens) - min_length + 1):
        phrase = tuple(tokens[i:i + min_length])
        counts[phrase] += 1
        occurrences.setdefault(phrase, []).append(para_index_per_token[i])

    flagged: list[dict[str, Any]] = []
    for phrase, n in counts.most_common():
        if n < min_occurrences:
            continue
        flagged.append({
            "text": " ".join(phrase),
            "paragraphs": occurrences[phrase],
            "rule": "repeated-phrase",
            "length": min_length,
            "occurrences": n,
        })

    # Diagnostic top 20 at length 4, regardless of occurrence count.
    diag_counts: Counter[tuple[str, ...]] = Counter()
    diag_occurrences: dict[tuple[str, ...], list[int]] = {}
    for i in range(len(tokens) - 3):
        phrase = tuple(tokens[i:i + 4])
        diag_counts[phrase] += 1
        diag_occurrences.setdefault(phrase, []).append(para_index_per_token[i])
    diagnostic_top_20 = []
    for phrase, n in sorted(diag_counts.items(), key=lambda kv: (-kv[1] * 4, " ".join(kv[0])))[:20]:
        diagnostic_top_20.append({
            "text": " ".join(phrase),
            "paragraphs": diag_occurrences[phrase],
            "rule": "repeated-phrase",
            "length": 4,
            "occurrences": n,
        })

    return {
        "count": len(flagged),
        "min_length": min_length,
        "min_occurrences": min_occurrences,
        "flagged_items": flagged,
        "diagnostic_top_20": diagnostic_top_20,
    }


def detect_dialogue_tags(paragraphs: list[str]) -> dict[str, Any]:
    """Approximate but standards-compliant tag detection.

    For each paragraph, find dialogue lines (quoted spans) and look immediately
    after the closing quote for a `<subject>? <verb>` tag. Classify the verb
    against INVISIBLE_TAGS / PERFORMANCE_TAGS, and check for an adjacent -ly
    adverb either before or after the verb.
    """
    tag_items: list[dict[str, Any]] = []
    performance_items: list[dict[str, Any]] = []
    adverb_pair_items: list[dict[str, Any]] = []
    dialogue_line_count = 0
    tag_count = 0

    for p_idx, p in enumerate(paragraphs, start=1):
        # Count dialogue lines = quoted spans.
        quotes = list(QUOTED_DIALOGUE.finditer(p))
        dialogue_line_count += len(quotes)
        for q in quotes:
            tail = p[q.end():q.end() + 80]  # window after the close-quote
            m = re.match(
                r"\s*[,.\-]?\s*(?:[A-Z][a-z]+|he|she|they|I|we)\s+([a-z]+)(?:\s+([a-z]+ly))?",
                tail,
            )
            verb = adverb = None
            if m:
                verb = m.group(1).lower()
                adverb = m.group(2)
            if not verb:
                # Try inverted form: <verb> <subject>
                m2 = re.match(r"\s*[,.\-]?\s*([a-z]+)\s+(?:[A-Z][a-z]+|he|she|they|I|we)\b", tail)
                if m2:
                    verb = m2.group(1).lower()
            if not verb:
                continue
            tag_count += 1
            classification = (
                "invisible" if verb in INVISIBLE_TAGS
                else "performance" if verb in PERFORMANCE_TAGS
                else "other"
            )
            full_line = (q.group(0) + tail).strip()
            item = {
                "text": full_line,
                "paragraph": p_idx,
                "rule": "tagged-dialogue",
                "tag_verb": verb,
                "classification": classification,
            }
            tag_items.append(item)
            if classification == "performance":
                performance_items.append(item)
            if adverb:
                adv_item = dict(item)
                adv_item["adverb"] = adverb
                adverb_pair_items.append(adv_item)

    # Voice consistency: dominant tag verb / total tags.
    tag_rate = round(100 * tag_count / dialogue_line_count, 2) if dialogue_line_count else 0.0
    if tag_count >= 15:
        verb_counter = Counter(t["tag_verb"] for t in tag_items)
        dominant_verb, dominant_count = verb_counter.most_common(1)[0]
        voice_consistency_pct = round(100 * dominant_count / tag_count, 2)
        performance_pct = round(100 * sum(1 for t in tag_items if t["classification"] == "performance") / tag_count, 2)
        voice_status = "scored"
        sample_floor_note = None
    else:
        dominant_verb = None
        voice_consistency_pct = None
        performance_pct = None
        voice_status = "N/A"
        sample_floor_note = "fewer than 15 tags; below sample-size floor"

    adverb_pair_pct = round(100 * len(adverb_pair_items) / tag_count, 2) if tag_count else 0.0

    return {
        "dialogue_line_count": dialogue_line_count,
        "total_tags": tag_count,
        "tag_rate_pct": tag_rate,
        "voice_consistency_status": voice_status,
        "voice_consistency_pct": voice_consistency_pct,
        "dominant_tag_verb": dominant_verb,
        "performance_tag_rate_pct": performance_pct,
        "adverb_paired_tag_pct": adverb_pair_pct,
        "sample_floor_note": sample_floor_note,
        "flagged_items": tag_items,
        "performance_items": performance_items,
        "adverb_pair_items": adverb_pair_items,
    }


def detect_acronym_consistency(text: str, exclusion_list: list[str]) -> dict[str, Any]:
    """v1.22 typographic-emphasis exclusion: skip any candidate whose normalized
    form contains a substring from exclusion_list (case-insensitive)."""
    excl = [e.lower() for e in exclusion_list]
    candidates = ACRONYM_PATTERN.findall(text)
    by_base: dict[str, set[str]] = {}
    for c in candidates:
        if c in ACRONYM_EXCLUDE_TOKENS:
            continue
        base = c.replace(".", "").replace(" ", "")
        if any(e and e in c.lower() or e in base.lower() for e in excl):
            continue
        if any(e and e.replace(" ", "") in base.lower() for e in excl):
            continue
        by_base.setdefault(base, set()).add(c)

    # Also catch ALL-CAPS multi-word phrases (e.g., "PALE HORSE" without periods).
    multi_word = re.findall(r"\b[A-Z]{2,}(?:\s+[A-Z]{2,}){1,5}\b", text)
    for phrase in multi_word:
        # If any exclusion list entry matches (case-insensitive substring), skip.
        if any(e and e in phrase.lower() for e in excl):
            continue
        by_base.setdefault(phrase, set()).add(phrase)

    inconsistent: list[dict[str, Any]] = []
    for base, variants in by_base.items():
        if len(variants) > 1:
            inconsistent.append({
                "text": base,
                "rule": "acronym-styling-inconsistent",
                "variants": sorted(variants),
            })
    return {
        "distinct_acronym_count": len(by_base),
        "inconsistent_count": len(inconsistent),
        "passes_styling_consistency": len(inconsistent) == 0,
        "flagged_items": inconsistent,
        "exclusion_list_applied": exclusion_list,
    }


# ---------------------------------------------------------------------------
# Genre sanity hint (bucket-level only: Fiction / NonFiction / Academic).
# ---------------------------------------------------------------------------


def detect_genre_hint(
    basics: dict[str, Any],
    passive_voice: dict[str, Any],
    dialogue_tags: dict[str, Any],
) -> dict[str, Any]:
    """Bucket-level genre sanity hint for router mismatch detection.

    Returns detected_bucket (Fiction / NonFiction / Academic), confidence
    (high / medium / low), signals, and a rationale string.  The router uses
    this ONLY to challenge a gross mismatch on high-confidence detections.
    It never auto-selects genre and never affects scoring.

    Uses dialogue_tags.total_tags (quotes that carry an actual tag verb) rather
    than raw quote-span counts, so inline scare quotes and cited phrases in
    non-fiction prose do not register as fiction signals.
    """
    sent_count = basics.get("sentence_count", 0) or 1
    word_count = basics.get("word_count", 0) or 1
    para_count = basics.get("paragraph_count", 1) or 1
    avg_sent_len = basics.get("average_sentence_length", 0.0)
    passives_per_100 = passive_voice.get("passives_per_100_sentences", 0.0)
    total_tags = dialogue_tags.get("total_tags", 0)

    tagged_ratio = total_tags / sent_count
    avg_para_len = word_count / para_count

    signals: dict[str, Any] = {
        "tagged_dialogue_ratio": round(tagged_ratio, 4),
        "total_tagged_dialogue_lines": total_tags,
        "passives_per_100_sentences": round(passives_per_100, 2),
        "average_sentence_length": round(avg_sent_len, 2),
        "avg_paragraph_length": round(avg_para_len, 1),
    }

    if tagged_ratio > 0.08:
        detected_bucket = "Fiction"
        confidence = "high" if tagged_ratio > 0.15 else "medium"
        rationale = (
            f"Tagged dialogue ratio {tagged_ratio:.1%} ({total_tags} tagged lines / "
            f"{sent_count} sentences) indicates fiction."
        )
    elif tagged_ratio < 0.03:
        academic_signals = 0
        if passives_per_100 > 15.0:
            academic_signals += 1
        if avg_sent_len > 18.0:
            academic_signals += 1
        if academic_signals >= 2:
            detected_bucket = "Academic"
            confidence = "high"
            rationale = (
                f"Near-zero tagged dialogue ({tagged_ratio:.1%}), high passive rate "
                f"({passives_per_100:.1f}/100 sentences), long average sentence "
                f"({avg_sent_len:.1f} words) indicate academic or technical non-fiction."
            )
        else:
            detected_bucket = "NonFiction"
            confidence = "high" if academic_signals == 0 else "medium"
            if academic_signals == 1:
                rationale = (
                    f"Near-zero tagged dialogue ({tagged_ratio:.1%}) indicates non-fiction; "
                    f"one academic secondary signal present but not conclusive for NF2."
                )
            else:
                rationale = (
                    f"Near-zero tagged dialogue ({tagged_ratio:.1%}), moderate passive rate "
                    f"and sentence length indicate general non-fiction."
                )
    else:
        detected_bucket = "Fiction"
        confidence = "low"
        rationale = (
            f"Tagged dialogue ratio {tagged_ratio:.1%} is in the ambiguous zone (3-8%). "
            "Could be literary fiction with minimal dialogue or creative non-fiction. "
            "Genre selection requires author confirmation."
        )

    return {
        "detected_bucket": detected_bucket,
        "confidence": confidence,
        "rationale": rationale,
        "signals": signals,
    }


# ---------------------------------------------------------------------------
# Top-level orchestration.
# ---------------------------------------------------------------------------


def truncate_flagged(metric: dict[str, Any]) -> None:
    """Apply the 50-item-per-category truncation rule from _standards.md."""
    items = metric.get("flagged_items")
    if isinstance(items, list) and len(items) > 50:
        sorted_items = sorted(items, key=lambda x: x.get("paragraph", x.get("paragraphs", [0])[0] if x.get("paragraphs") else 0))
        metric["flagged_items"] = sorted_items[:50]
        metric["flagged_items_truncated_at"] = 50


def tokenize_chapter(stripped_path: str, config: dict[str, Any]) -> dict[str, Any]:
    with open(stripped_path, encoding="utf-8") as f:
        text = f.read()

    paragraphs = split_paragraphs(text)
    basics = detect_basics(paragraphs)
    sentences_by_para = basics.pop("_sentences_by_para")
    basics.pop("_sent_lengths")

    very_long = detect_very_long_sentences(sentences_by_para)
    complex_paras = detect_complex_paragraphs(paragraphs, sentences_by_para)
    glue = detect_glue_index(text)
    conj = detect_conjunction_starts(sentences_by_para)
    ing = detect_ing_starts(
        sentences_by_para, text,
        config.get("ing_starts_proper_noun_exclusions", []),
    )
    passive = detect_passive_voice(sentences_by_para)
    weak_adv = detect_weak_adverbs(
        sentences_by_para, basics["word_count"],
        config.get("weak_adverb_noun_exclusions", []),
    )
    emo = detect_emotion_tells(sentences_by_para)
    slow = detect_slow_pacing(paragraphs)
    style = detect_style_score(sentences_by_para)
    repeated = detect_long_repeated_phrases(text)
    tags = detect_dialogue_tags(paragraphs)
    acronyms = detect_acronym_consistency(
        text, config.get("acronym_emphasis_exclusions", []),
    )

    genre_hint = detect_genre_hint(basics, passive, tags)

    out = {
        "schema_version": "1.0",
        "engine_version": "v1.24",
        "stripped_file": stripped_path,
        "basics": basics,
        "very_long_sentences": very_long,
        "complex_paragraphs": complex_paras,
        "glue_index": glue,
        "conjunction_starts": conj,
        "ing_starts": ing,
        "passive_voice": passive,
        "weak_adverbs": weak_adv,
        "emotion_tells": emo,
        "slow_pacing": slow,
        "style_score": style,
        "long_repeated_phrases": repeated,
        "dialogue_tags": tags,
        "acronym_consistency": acronyms,
        "genre_hint": genre_hint,
    }

    # Apply 50-item truncation per category.
    for key, val in out.items():
        if isinstance(val, dict):
            truncate_flagged(val)

    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="PWA / Canary v1.24 tokenizer.")
    p.add_argument("--stripped", required=True, help="Path to stripped prose file.")
    p.add_argument("--title", required=True, help="Output filename stem.")
    p.add_argument("--config", default=None, help="Per-manuscript pwa_config.json.")
    p.add_argument("--routine-config", default=None, help="Routine-level pwa_config.json.")
    p.add_argument("--out-dir",
                   default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp"),
                   help="Output directory (default: two levels up from routine dir).")
    p.add_argument("--date", default=_dt.date.today().isoformat(), help="Date stamp YYYY-MM-DD.")
    args = p.parse_args(argv)

    # The tokenizer reads the same merged config the strip engine used so the
    # exclusion lists are consistent across the pipeline. We pass --stripped's
    # parent as the synthetic "source dir" to satisfy load_config's manuscript
    # lookup; if the caller wants the manuscript override they should pass
    # --config explicitly.
    config, paths_loaded = load_config(args.stripped, args.config, args.routine_config)

    blob = tokenize_chapter(args.stripped, config)
    blob["config_paths_loaded"] = paths_loaded

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, f"{args.title} - tokenizer {args.date}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(blob, f, indent=2, ensure_ascii=False)

    summary = {
        "tokenizer_output": out_path,
        "word_count": blob["basics"]["word_count"],
        "sentence_count": blob["basics"]["sentence_count"],
        "paragraph_count": blob["basics"]["paragraph_count"],
        "exclusion_lists_in_effect": {
            "acronym_emphasis": len(config.get("acronym_emphasis_exclusions", [])),
            "weak_adverb_noun": len(config.get("weak_adverb_noun_exclusions", [])),
            "ing_starts_proper_noun": len(config.get("ing_starts_proper_noun_exclusions", [])),
        },
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
