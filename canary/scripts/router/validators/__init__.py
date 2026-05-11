"""
Router-side validators for Mode 1 subagent outputs.

One module per subagent. Each module exposes a `validate(...)` function
that returns a `ValidationResult` dataclass. The router consumes the
result and either accepts the subagent's output or re-dispatches with the
corrective instruction.

Modules:

- `grammar_spelling`  - Grammar and Spelling subagent validator
- `strip_verify`      - Strip Verification subagent validator
- `summary_beat_sheet`- Summary and Beat Sheet subagent validator
- `character_dialogue`- Character Dialogue Consistency subagent validator
- `report_verify`     - Report Verification subagent validator
"""
