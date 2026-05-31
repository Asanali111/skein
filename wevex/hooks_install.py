"""Install/uninstall autonomous hooks for Claude Code, Cursor, and friends.

What this writes (when target tools are detected):

  Claude Code (per-project):
    .claude/settings.json        — merged with existing; adds Wevex hooks
    .wevex/scope                 — pins the project scope handle for hooks

  Claude Code (user-global, optional):
    ~/.claude/settings.json      — same merge, applies to all projects

  Cursor (per-project):
    .cursor/rules/wevex.mdc      — auto-applied rule pointing at wevex

  Codex CLI / Gemini CLI / opencode / Antigravity:
    rely on AGENTS.md (already written by `wevex sync`); no extra hook file.

The merge is conservative: existing wevex entries are replaced; user keys
outside the wevex-owned blocks are preserved.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("wevex.hooks_install")

# Marker so we can find and remove our own entries idempotently
_WEVEX_MARKER_KEY = "__wevex_managed"


@dataclass
class InstallReport:
    written: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def ok(self, label: str, path: str) -> None:
        self.written.append(f"{label}: {path}")

    def skip(self, label: str, reason: str) -> None:
        self.skipped.append(f"{label}: {reason}")

    def err(self, label: str, msg: str) -> None:
        self.errors.append(f"{label}: {msg}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def install_hooks(
    repo_path: Path,
    scope_handle: str,
    *,
    wevex_bin: str = "wevex",
    user_global: bool = False,
) -> InstallReport:
    """Install autonomous hooks for all detected clients."""
    report = InstallReport()

    # 1. Pin the scope for this project (read by hook handlers)
    _write_scope_pin(repo_path, scope_handle, report)

    # 2. Claude Code project hooks
    _install_claude_code(repo_path, scope_handle, wevex_bin, report)
    if user_global:
        _install_claude_code_global(scope_handle, wevex_bin, report)

    # 3. Cursor rule
    _install_cursor_rule(repo_path, scope_handle, wevex_bin, report)

    return report


def uninstall_hooks(repo_path: Path) -> InstallReport:
    """Remove Wevex-managed hooks (preserves user-added entries)."""
    report = InstallReport()

    # Remove .wevex/scope (and the dir if empty)
    scope_pin = repo_path / ".wevex" / "scope"
    if scope_pin.exists():
        scope_pin.unlink()
        try:
            scope_pin.parent.rmdir()
        except OSError:
            pass
        report.ok(".wevex/scope", str(scope_pin))

    # Strip from .claude/settings.json
    claude_settings = repo_path / ".claude" / "settings.json"
    if claude_settings.exists():
        _strip_wevex_from_claude_settings(claude_settings, report)

    # Remove .cursor/rules/wevex.mdc
    cursor_rule = repo_path / ".cursor" / "rules" / "wevex.mdc"
    if cursor_rule.exists():
        cursor_rule.unlink()
        report.ok("Cursor rule", str(cursor_rule))

    return report


# ---------------------------------------------------------------------------
# Scope pin
# ---------------------------------------------------------------------------

def _write_scope_pin(repo_path: Path, scope_handle: str, report: InstallReport) -> None:
    try:
        wevex_dir = repo_path / ".wevex"
        wevex_dir.mkdir(exist_ok=True)
        (wevex_dir / "scope").write_text(scope_handle + "\n")
        report.ok("Scope pin", str(wevex_dir / "scope"))
    except Exception as e:
        report.err("Scope pin", str(e))


# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------

def _install_claude_code(
    repo_path: Path, scope_handle: str, wevex_bin: str, report: InstallReport,
) -> None:
    settings_path = repo_path / ".claude" / "settings.json"
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = _read_json_or_empty(settings_path)
        _merge_claude_wevex_hooks(settings, wevex_bin, scope_handle)
        _write_json(settings_path, settings)
        report.ok("Claude Code (project)", str(settings_path))
    except Exception as e:
        report.err("Claude Code (project)", str(e))


def _install_claude_code_global(
    scope_handle: str, wevex_bin: str, report: InstallReport,
) -> None:
    settings_path = Path.home() / ".claude" / "settings.json"
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = _read_json_or_empty(settings_path)
        # User-global doesn't pin scope; hooks rely on per-project .wevex/scope
        _merge_claude_wevex_hooks(settings, wevex_bin, scope_handle=None)
        _write_json(settings_path, settings)
        report.ok("Claude Code (global)", str(settings_path))
    except Exception as e:
        report.err("Claude Code (global)", str(e))


def _quote_bin(wevex_bin: str) -> str:
    """Quote a binary path for embedding in a shell command string.

    Claude Code's hook runner spawns each ``command`` via the OS shell
    (bash/zsh on POSIX, cmd.exe on Windows). The old implementation only
    quoted when a *space* was present — so a path with no space but a shell
    metacharacter (``C:\\tools\\a&calc.exe\\wevex.exe`` on Windows, or
    ``/opt/a;b/wevex`` on POSIX) was emitted bare and the shell would treat
    ``&`` / ``;`` / ``|`` as a command separator: command injection on every
    hook event, baked into the user's ``settings.json``.

    POSIX: ``shlex.quote`` is the correct, complete escaping (and leaves a
    bare ``wevex`` bare). Windows cmd.exe has no equivalent stdlib helper;
    double-quoting makes the path a single token and neutralises the
    separators ``& | < > ( )``. We quote whenever a space or metacharacter is
    present so the safe common case (a plain ``wevex``) stays unquoted.
    """
    import os
    import shlex

    if os.name != "nt":
        return shlex.quote(wevex_bin)
    if wevex_bin.startswith('"') and wevex_bin.endswith('"'):
        return wevex_bin
    if any(c in wevex_bin for c in ' \t&|<>^()%"'):
        return '"' + wevex_bin + '"'
    return wevex_bin


def _merge_claude_wevex_hooks(
    settings: dict, wevex_bin: str, scope_handle: Optional[str],
) -> None:
    """Merge Wevex hook entries into a Claude Code settings dict, idempotently.

    Format follows the Claude Code 'hooks' schema:
      { "hooks": { "<EventName>": [ {"matcher": "*", "hooks": [{"type":"command", "command":"..."}]} ] } }

    Note on scope: earlier iterations prefixed the command with
    ``WEVEX_SCOPE=<handle>`` (POSIX shell env-var syntax), but that is not
    a valid construct in Windows ``cmd.exe`` and ``cmd.exe`` is what
    Claude Code on Windows spawns hooks through. We rely entirely on the
    ``.wevex/scope`` pin file (written next to ``.claude/settings.json`` by
    :func:`_install_claude_code`) for scope resolution. The hook subprocess
    starts in Claude Code's cwd (== repo root) and walks up via
    :func:`scope_resolver.find_scope_pin`, so the pin always wins. The
    ``scope_handle`` argument is kept for backwards-compatible call
    signatures but is no longer embedded in the command string.
    """
    hooks_root = settings.setdefault("hooks", {})
    bin_q = _quote_bin(wevex_bin)

    events = {
        "SessionStart":     f"{bin_q} hook session-start",
        "UserPromptSubmit": f"{bin_q} hook user-prompt-submit",
        "Stop":             f"{bin_q} hook stop",
        "PostToolUse":      f"{bin_q} hook post-tool-use",
    }

    for event_name, command in events.items():
        existing_blocks = hooks_root.setdefault(event_name, [])
        # Remove any prior Wevex-managed block for this event
        existing_blocks[:] = [
            b for b in existing_blocks
            if not (isinstance(b, dict) and b.get(_WEVEX_MARKER_KEY))
        ]
        # Add ours
        block = {
            _WEVEX_MARKER_KEY: True,
            "matcher": "*",
            "hooks": [{"type": "command", "command": command}],
        }
        existing_blocks.append(block)


def _strip_wevex_from_claude_settings(path: Path, report: InstallReport) -> None:
    try:
        settings = _read_json_or_empty(path)
        hooks_root = settings.get("hooks", {})
        changed = False
        for event_name, blocks in list(hooks_root.items()):
            if not isinstance(blocks, list):
                continue
            new_blocks = [
                b for b in blocks
                if not (isinstance(b, dict) and b.get(_WEVEX_MARKER_KEY))
            ]
            if len(new_blocks) != len(blocks):
                changed = True
                if new_blocks:
                    hooks_root[event_name] = new_blocks
                else:
                    del hooks_root[event_name]
        if changed:
            if not hooks_root:
                settings.pop("hooks", None)
            _write_json(path, settings)
            report.ok("Claude Code (cleaned)", str(path))
        else:
            report.skip("Claude Code", "no Wevex-managed hooks found")
    except Exception as e:
        report.err("Claude Code", str(e))


# ---------------------------------------------------------------------------
# Cursor rule (.cursor/rules/wevex.mdc)
# ---------------------------------------------------------------------------

_CURSOR_RULE_TEMPLATE = """---
description: Wevex context bus integration — call recall/remember automatically
alwaysApply: true
---

# Wevex integration

This project uses **Wevex** for cross-LLM context sharing. The local daemon
exposes an MCP server you have access to.

## Use these tools proactively

- **At the start of any non-trivial task**, call the `recall` MCP tool with a
  query that summarises the task. Treat the returned fragments as authoritative
  context that other agents have left for you.
- **After each significant decision**, call `remember` (or `note_decision`) to
  persist it. Use `type="decision"` for choices, `"observation"` for code-level
  changes, `"requirement"` for hard rules, `"preference"` for style.
- **Before editing files in a shared area**, call `claim_lease` with the file
  glob, so other agents won't clobber your work.

## Scope

Use scope handle `{scope}` for this project.

## Fallback

If the MCP server is unavailable, run shell commands instead:
```
{wevex_bin} recall "<query>"
{wevex_bin} remember "<content>" --type decision
```

(This file is auto-managed by `wevex hooks install`. Delete it or run
`wevex hooks uninstall` to remove.)
"""


def _install_cursor_rule(
    repo_path: Path, scope_handle: str, wevex_bin: str, report: InstallReport,
) -> None:
    rules_dir = repo_path / ".cursor" / "rules"
    try:
        rules_dir.mkdir(parents=True, exist_ok=True)
        rule_path = rules_dir / "wevex.mdc"
        content = _CURSOR_RULE_TEMPLATE.format(scope=scope_handle, wevex_bin=wevex_bin)
        rule_path.write_text(content)
        report.ok("Cursor rule", str(rule_path))
    except Exception as e:
        report.err("Cursor rule", str(e))


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _read_json_or_empty(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, data: dict) -> None:
    # Atomic write: this merges into the user's own .claude/settings.json,
    # which can hold unrelated hooks/permissions. A plain open("w") truncates
    # first, so a crash or concurrent `wevex up`/`connect` between truncate and
    # full dump leaves the user's settings empty or half-written. tmp+replace
    # makes the swap atomic.
    from . import paths as _paths
    _paths.atomic_write_text(path, json.dumps(data, indent=2) + "\n")
