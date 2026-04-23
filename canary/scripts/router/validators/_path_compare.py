"""
Cross-OS / cross-mount path equivalence helpers for router validators.

The Mode 1 router can run in two environments:

1. CLI/Code on the Windows host: dispatched paths and subagent-reported paths
   are both Windows-form (e.g. `C:\\Users\\elf10\\ClaudeCoWork\\...`).
2. Cowork bash sandbox: dispatched paths are Linux-form
   (`/sessions/<token>/mnt/ClaudeCoWork/...`) but subagents run on the host
   and report Windows-form paths. Both refer to the same logical file.

Naive string equality fails case 2 even though the strip is correct. These
helpers reduce both forms to the same canonical comparison key so the
existing path-echo checks in the validators succeed when the paths point at
the same logical file.

Spec: surfaced by Babydoll Ch19.1 end-to-end Mode 1 dry run, 2026-04-22 -
Strip Verification subagent returned correct PASS JSON but validator hard-
failed all three path-echo checks because the Linux mount path the validator
received via CLI did not string-equal the Windows path the subagent reported.

Used by: strip_verify.py, summary_beat_sheet.py, grammar_spelling.py,
character_dialogue.py, report_verify.py.

Routine version: v1.25
Helper version: v0.1
"""

from __future__ import annotations


def normalize_path_for_compare(p: str) -> str:
    """
    Reduce a path string to a forward-slash, lowercase, mount-stripped tail.

    Strategy:
      1. Convert backslashes to forward slashes.
      2. Lowercase (Windows paths are case-insensitive; the routine's
         tree never relies on case to disambiguate).
      3. Strip known mount-prefix shapes:
           - `c:/users/elf10/`               (Windows form)
           - `/sessions/<token>/mnt/`        (bash sandbox mount form)
         leaving the relative tail under the user's home / cowork tree.
      4. Strip leading slashes from the result.

    Two paths pointing at the same logical file under either OS will reduce
    to the same key.
    """
    if not isinstance(p, str):
        return ""
    s = p.replace("\\", "/").lower()
    if s.startswith("c:/users/elf10/"):
        s = s[len("c:/users/elf10/") :]
    if s.startswith("/sessions/"):
        rest = s[len("/sessions/") :]
        slash_idx = rest.find("/")
        if slash_idx != -1 and rest[slash_idx:].startswith("/mnt/"):
            s = rest[slash_idx + len("/mnt/") :]
    return s.lstrip("/")


def paths_equivalent(dispatched: str, reported: str | None) -> bool:
    """
    Return True if `reported` is None or refers to the same logical file as
    `dispatched`, accounting for backslash/forward-slash, case differences,
    and the Windows-host vs Linux-sandbox mount-prefix gap.

    The router treats `reported is None` as "subagent did not echo this
    path" - which is fine; the substring checks against the file content
    are the load-bearing integrity gates, not the path-echo check.
    """
    if reported is None:
        return True
    if reported == dispatched:
        return True
    return normalize_path_for_compare(dispatched) == normalize_path_for_compare(
        reported
    )
