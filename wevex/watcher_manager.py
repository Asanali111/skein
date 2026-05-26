"""Spawn / track / kill per-project watcher subprocesses.

The watcher must live in the *user's session* (not under launchd) so that
on macOS it has full TCC access to read source files in ~/Documents,
~/Desktop, iCloud, etc.  This module spawns ``wevex watch`` as a detached
background subprocess and tracks its PID at:

    ~/.config/wevex/watchers/<sanitised-source-root>.pid

The watcher is fire-and-forget from the parent's perspective; it survives
the shell that spawned it (``start_new_session=True``), but dies on logout.
``wevex up`` re-spawns it on next invocation.

This split — daemon under launchd, watchers in user session — is the
design Phase 3.5 of the project plan landed on after we discovered launchd
processes can't read files inside macOS TCC-protected dirs.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from . import _proc, paths as _wevex_paths
from .projects import ProjectEntry

logger = logging.getLogger("wevex.watcher_manager")

# Both move to %APPDATA%\wevex\ on Windows, stay at ~/.config/wevex/ on
# macOS / Linux. See wevex/paths.py.
WATCHER_PID_DIR = _wevex_paths.watcher_pid_dir()
WATCHER_LOG_DIR = _wevex_paths.watcher_log_dir()


def _slug(text: str) -> str:
    """Filesystem-safe single-segment slug."""
    return re.sub(r"[^A-Za-z0-9_.\-]+", "-", text).strip("-") or "default"


def pid_file_for(entry: ProjectEntry) -> Path:
    return WATCHER_PID_DIR / f"{_slug(entry.scope)}.pid"


def log_file_for(entry: ProjectEntry) -> Path:
    return WATCHER_LOG_DIR / f"watcher-{_slug(entry.scope)}.log"


def _read_pid(pid_file: Path) -> Optional[int]:
    try:
        return int(pid_file.read_text().strip())
    except (OSError, ValueError):
        return None


def _alive(pid: int) -> bool:
    # Thin alias kept for readability at call sites. The cross-platform
    # probe lives in _proc.pid_alive — os.kill(pid, 0) on Windows raises
    # OSError("Invalid argument") and breaks the original implementation.
    return _proc.pid_alive(pid)


def is_running(entry: ProjectEntry) -> bool:
    pid_file = pid_file_for(entry)
    if not pid_file.exists():
        return False
    pid = _read_pid(pid_file)
    if pid is None:
        return False
    if not _alive(pid):
        try:
            pid_file.unlink()
        except OSError:
            pass
        return False
    return True


def spawn(entry: ProjectEntry, *, wevex_bin: Optional[str] = None) -> Optional[int]:
    """Spawn a detached ``wevex watch`` for this project.

    Returns the new PID, or None if a watcher is already running.
    """
    if is_running(entry):
        return None

    WATCHER_PID_DIR.mkdir(parents=True, exist_ok=True)
    WATCHER_LOG_DIR.mkdir(parents=True, exist_ok=True)

    wevex_bin = wevex_bin or sys.argv[0]
    if not Path(wevex_bin).is_file():
        # ``sys.argv[0]`` may be just "wevex" if invoked from PATH
        import shutil
        wevex_bin = shutil.which("wevex") or wevex_bin

    log_file = log_file_for(entry)
    cmd = [
        wevex_bin, "watch",
        entry.root,
        "--scope", entry.scope,
        "--source-root", entry.source_root,
    ]
    # The child inherits a dup of the log FD; the parent's handle must close
    # after spawn_detached or each spawn leaks one FD into the daemon
    # process forever. Detach mechanics (start_new_session on POSIX vs
    # CREATE_NEW_PROCESS_GROUP on Windows) live in wevex/_proc.py.
    with open(log_file, "ab") as log_handle:
        pid = _proc.spawn_detached(
            cmd,
            stdout=log_handle, stderr=subprocess.STDOUT,
        )
    pid_file_for(entry).write_text(str(pid))
    return pid


def kill(entry: ProjectEntry) -> bool:
    """Stop the watcher for one project. Returns True if anything was killed."""
    pid_file = pid_file_for(entry)
    pid = _read_pid(pid_file)
    if pid is None:
        try:
            pid_file.unlink()
        except OSError:
            pass
        return False
    # Graceful → hard kill across platforms (SIGTERM/SIGKILL on POSIX,
    # CTRL_BREAK_EVENT/TerminateProcess on Windows).
    _proc.terminate_pid(pid, timeout=2.0)
    try:
        pid_file.unlink()
    except OSError:
        pass
    return True


def kill_all() -> list[ProjectEntry]:
    """Stop every active watcher. Returns the entries that were running."""
    from .projects import list_projects
    killed = []
    for entry in list_projects():
        if is_running(entry) and kill(entry):
            killed.append(entry)
    return killed
