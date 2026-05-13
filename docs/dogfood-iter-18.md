# Dogfood: Skein flips Claude Sonnet's tool-picking from filesystem-first to context-bus-first

**Date:** 2026-05-13 · **Method:** real `claude -p --model sonnet` headless session against this project · **Cost:** 49 input + 533k cache_read + 587 output tokens, 64 seconds wall

## Result

When asked *"Analyze this project and create a summary of its current state,"* Claude Sonnet's behavior with Skein installed:

### Sonnet's first thinking block (verbatim)

> "The user wants me to analyze the project and create a summary of its current state. Let me start by calling the Skein tools as instructed (project_briefing and recall), then also look at the actual codebase."

### Sonnet's first text to the user

> "I'll pull context from Skein first, then verify with the actual codebase."

### Tool call sequence (first three calls)

| # | Tool | Input |
|---|---|---|
| 1 | `ToolSearch` | loaded deferred-tool inventory |
| 2 | **`mcp__skein__project_briefing`** | `scope='project:ameliomar'` |
| 3 | **`mcp__skein__recall`** | `query='current project state architecture decisions recent work'` |

Skein was called **before any source file read.**

## Compare: equivalent Gemini CLI session (same project, same prompt)

Gemini's session — same MCP registration, same project, same prompt — defaulted to:

1. `Read README.md`
2. `Read AGENTS.md`
3. `list_directory skein/`
4. `Read pyproject.toml` + `Read storage.py` (lines 1-100) + `Read retrieval.py` + …
5. `git log` + `grep TODO/FIXME`
6. Final summary, **without ever calling Skein**

When directly challenged ("why haven't you used the skein tool?"), Gemini admitted Skein was available but rationalized choosing source-reading as more reliable.

## What changed between the two runs

Iter 18 of Skein landed in between. The three changes that mattered for tool-picking behavior:

1. **MCP tool descriptions rewritten as promises** with cost numbers and WHEN-to-use guidance. Example: `recall` advertises `"Returns top-K in <100ms, ~30 tokens per fragment — one recall typically replaces 5+ read_file calls"`.
2. **AGENTS.md template** leads with `"How to use Skein in this project — read BEFORE you do anything else"` and explicit token-cost comparison (`<50ms / ~300 tokens via project_briefing` vs `3000+ tokens via 5 read_file calls`).
3. **New `project_briefing` MCP tool** — zero-arg "give me the dashboard" entry point, advertised as `"The fastest path to 'what is happening here?'"`.

No model changes. No new infrastructure. Pure textual reframing of what was already exposed.

## The print-mode caveat

The Skein tool calls in this run returned `"Skein MCP needs approval"` — `claude -p` (non-interactive) doesn't auto-approve unknown MCP tools and there's no prompt to surface. Sonnet correctly fell back to filesystem analysis and produced a solid summary using HANDOFF.md + README + pyproject + git log.

This is a `claude -p` UX issue, not a Skein issue. In real interactive Claude Code, the user approves once and `project_briefing` returns the dashboard. The behavior flip — Sonnet choosing Skein over `read_file` as its first move — is verified independently of whether the call completes.

## Reproducibility

The session-replay is at [`/tmp/dogfood.jsonl`](file:///tmp/dogfood.jsonl) on the test machine (ephemeral). To reproduce on any machine with the Skein daemon running:

```bash
cd <your-project>
claude -p "Analyze this project and create a summary of its current state." \
       --model sonnet \
       --output-format stream-json \
       --verbose > dogfood.jsonl
```

Then grep the JSONL for `tool_use` events with `name` starting `mcp__skein__` — they should appear in the first three tool calls.

## Reference (commits)

The iter 18 work that produced this behavior change is in the public history:

```
fea770f  feat(agents_md): lead AGENTS.md with strong 'use Skein first' instruction
9c98d27  feat(mcp,api,cli): project_briefing tool + LLM-favorability tool descriptions
e1ba02b  fix(clients): drop unrecognized `transport` key from Gemini CLI config
68d2c88  fix(scanner): supersede duplicate facts via stable topic_key
```

See `git log --oneline` for context.
