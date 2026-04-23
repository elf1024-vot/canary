"""
Router-side validators for Mode 1 subagent outputs.

One module per subagent. Each module exposes a `validate(...)` function
that returns a `ValidationResult` dataclass. The router consumes the
result and either accepts the subagent's output or re-dispatches with the
corrective instruction.

Current modules:

- `grammar_spelling` - Grammar and Spelling subagent validator

Planned modules (blocked on subagent prompt hardening):

- `strip_verify`
- `summary_beat_sheet`
- `character_dialogue`
- `report_verify`
"""
