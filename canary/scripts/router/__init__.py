"""
PWA routine router package.

The router is the trusted root of the Subagent Architectural Rule (see
`_standards.md` v1.24): subagents report raw observations, the router
validates those observations deterministically and re-dispatches on failure.

Public entry points:

- `validators.grammar_spelling.validate(subagent_json, stripped_file_path)`

Later validator modules (strip_verify, summary_beat_sheet,
character_dialogue, report_verify) will land alongside.

Router version: v0.2 (Grammar and Spelling validator only)
"""

__version__ = "v0.1"
