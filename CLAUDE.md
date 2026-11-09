# resume-builder

Single-page app: everything lives in `index.html`.

## Second opinion with Codex

OpenAI Codex is wired in as an independent reviewer (`/codex` skill,
`.claude/skills/codex/SKILL.md`, wrapper `scripts/codex.sh`).

- Before committing a non-trivial change, run `scripts/codex.sh review` and
  act on confirmed findings.
- When stuck, or when choosing between approaches, ask Codex with
  `scripts/codex.sh ask "..."`.
- If Codex is not signed in, carry on without it and tell the user.
