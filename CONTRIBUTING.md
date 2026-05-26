# Contributing to Wevex

Thanks for considering a contribution. Wevex is a small project run by
one person with a real time budget — readable issues and small focused
PRs help a lot.

## Quick links

- **Found a bug?** Open an issue using the *Bug report* template. Include
  `wevex doctor` output and the contents of `~/.config/wevex/logs/daemon.log`.
- **Want a feature?** Open a *Feature request* issue. We talk before
  code lands.
- **Security?** Email atogambaev@gmail.com, do not open a public issue.

## Development setup

Wevex targets Python 3.9+, but development is easiest on 3.12.

```bash
git clone https://github.com/Asanali111/wevex
cd wevex
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest -q
```

641 tests pass on `main` as of v0.2.0. Anything new should land with
a test. Fixtures live in `tests/conftest.py` — most tests use the
`storage` / `seeded_storage` / `authed_client` fixtures so you rarely
need to wire up the daemon by hand.

Run the daemon in dev mode:

```bash
WEVEX_PORT=8766 python -m wevex serve --port 8766 --host 127.0.0.1
```

Use a different port from your real `wevex up` daemon (8765) so you can
hack without breaking your day-to-day Wevex.

## What we're working on

The [project roadmap](https://github.com/Asanali111/wevex/issues?q=is%3Aissue+label%3Aroadmap)
labels track the next 2-3 iterations. Issues labelled `good first issue`
are scoped for newcomers — small, self-contained, with clear acceptance
criteria.

## PR guidelines

- **One logical change per PR.** Easier to review, easier to revert.
- **Conventional Commit prefix** on the title (`feat:`, `fix:`, `chore:`,
  `test:`, `refactor:`, `docs:`, `perf:`). Merge commits are exempt.
- **Update tests.** New behaviour needs an antibody. Bug fixes need a
  regression test.
- **No co-author lines.** Just commit normally.
- **Run `pytest -q` before pushing.** If it's red on your branch, fix
  it before asking for review.

## Architecture (one paragraph)

Wevex is a local FastAPI daemon that exposes an MCP Streamable HTTP
endpoint on 127.0.0.1:8765. SQLite holds *fragments* (typed context
units — decisions, facts, observations, etc.) and *chunks* (code search
index). Every MCP-capable LLM tool (Claude Code, Cursor, Codex, etc.)
connects via the same daemon, so they share project context without
copy-paste. The CLI is intentionally small (10 visible commands) — agents
get a richer surface via MCP tools. See `AGENTS.md` for the full
"how to use Wevex in this project" guide that the daemon regenerates.

## License

Apache 2.0. By contributing you agree your changes ship under the same
license.
