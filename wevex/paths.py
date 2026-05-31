"""Cross-platform location of Wevex's per-user state directory.

History
-------
For iterations 1-26 Wevex hardcoded ``Path.home() / ".config" / "wevex"`` in
~10 modules. That directory holds:

  * ``wevex.db``      – the SQLite store
  * ``config.json``   – per-user config (port, embedding provider, token)
  * ``.env``          – optional API-key file (sourced at config load)
  * ``connections.json`` – which LLM clients are connected
  * ``projects.json`` – registry of active projects
  * ``daemon.pid``    – PID file for the nohup backend
  * ``logs/``         – daemon + watcher stdout/stderr
  * ``watchers/``     – per-project watcher PID files

This worked on macOS and Linux because both honor the XDG-ish ``~/.config``
convention. On Windows there is no ``~/.config`` — the per-user state root
is ``%APPDATA%`` (Roaming) for things that should follow the user across
machines, or ``%LOCALAPPDATA%`` for machine-local cache. Wevex's DB is
small (~40 MB), portable, and the user moving machines would reasonably
expect their fragments to come along, so we use ``%APPDATA%`` (Roaming).

Design choices (deliberate)
---------------------------
1. **macOS/Linux paths are unchanged.** ``~/.config/wevex/`` stays exactly
   where it was. No migration, no surprise relocations. The fleet of
   existing developer installs (n=1: me) continues to work bit-identically.
2. **Windows uses ``%APPDATA%\\wevex\\``** with a ``Path.home() / "AppData"
   / "Roaming" / "wevex"`` fallback when the env var is not set (some CI
   runners and minimal containers don't set ``APPDATA``).
3. **No ``platformdirs`` dependency.** ``platformdirs.user_data_dir`` would
   put us under ``~/Library/Application Support/wevex/`` on macOS — that
   silently relocates the existing live DB. Branching by OS keeps the
   blast radius to Windows only.
4. **Functions, not constants.** Returning ``Path`` from a function lets
   tests monkeypatch ``HOME`` or ``APPDATA`` and re-call. The handful of
   module-level constants in ``daemon.py`` and ``watcher_manager.py``
   still resolve at import time (existing behavior); they read from
   ``wevex_home()`` once, which is fine for production but means tests
   that want to override the location must do so before importing those
   modules — same constraint as before.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_windows() -> bool:
    return sys.platform.startswith("win") or os.name == "nt"


def wevex_home() -> Path:
    """Return the per-user Wevex state directory.

    * Windows:        ``%APPDATA%\\wevex\\``   (fallback: ``~/AppData/Roaming/wevex/``)
    * macOS / Linux:  ``~/.config/wevex/``     (unchanged from pre-iter-27)
    """
    if _is_windows():
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "wevex"
        return Path.home() / "AppData" / "Roaming" / "wevex"
    return Path.home() / ".config" / "wevex"


def default_db_path() -> Path:
    return wevex_home() / "wevex.db"


def default_config_path() -> Path:
    return wevex_home() / "config.json"


def default_env_file() -> Path:
    return wevex_home() / ".env"


def daemon_pid_file() -> Path:
    return wevex_home() / "daemon.pid"


def daemon_lock_file() -> Path:
    return wevex_home() / "daemon.lock"


def daemon_log_dir() -> Path:
    return wevex_home() / "logs"


def watcher_pid_dir() -> Path:
    return wevex_home() / "watchers"


def watcher_log_dir() -> Path:
    return wevex_home() / "logs"


def connections_path() -> Path:
    return wevex_home() / "connections.json"


def projects_registry_path() -> Path:
    return wevex_home() / "projects.json"


def events_jsonl_path() -> Path:
    return wevex_home() / "events.jsonl"


def backend_cache_file() -> Path:
    return wevex_home() / "backend"


def atomic_write_text(
    path: Path, text: str, *, secret: bool = False, restrict_parent: bool = True,
) -> None:
    """Write ``text`` to ``path`` atomically (temp file + ``os.replace``).

    Atomicity prevents a crash or concurrent writer from leaving a truncated /
    half-written file (corrupting e.g. the user's ``.claude/settings.json`` or
    Wevex's own ``config.json``).

    When ``secret=True`` the file holds a credential (the daemon bearer token):
    the file is chmod'd to ``0o600`` *before* it is moved into place, so it is
    never momentarily world-readable on a multi-user POSIX host. When the file
    lives in a directory Wevex itself owns, ``restrict_parent=True`` also tightens
    that directory to ``0o700``; pass ``restrict_parent=False`` for third-party
    tool config dirs (``~/.cursor``, ``~/.gemini``, …) so we don't reach in and
    re-permission a directory we don't own — the ``0o600`` file is enough.
    ``chmod`` is best-effort on Windows (it only toggles the read-only bit
    there) and never fatal.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if secret and restrict_parent:
        try:
            os.chmod(path.parent, 0o700)
        except OSError:
            pass
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        if secret:
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
        os.replace(tmp, path)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
