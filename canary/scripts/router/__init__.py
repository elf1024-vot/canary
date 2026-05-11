"""
PWA routine router package.

The router is the trusted root of the Subagent Architectural Rule (see
`_standards.md` v1.24): subagents report raw observations, the router
validates those observations deterministically and re-dispatches on failure.

Public entry points:

- `validators.grammar_spelling.validate(subagent_json, stripped_file_path)`
- `validators.strip_verify.validate(subagent_json, original_chapter_path, stripped_file_path, strip_log_path, marker_map_path, pwa_config_path)`
- `validators.summary_beat_sheet.validate(subagent_json, original_chapter_path)`
- `validators.character_dialogue.validate(subagent_json, stripped_file_path)`
- `validators.report_verify.validate(subagent_json, paths)`
- `extract_json.extract_subagent_json(response_text)` -> dict

Router version: v0.3
"""

__version__ = "v0.3"
