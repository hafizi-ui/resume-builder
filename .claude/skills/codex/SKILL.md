---
name: codex
description: Get an independent second opinion from OpenAI Codex. Use before committing a non-trivial change (Codex reviews the diff), when stuck on a bug after two failed attempts, when choosing between designs, or when the user asks for a cross-check of code, a thesis chapter, a research method or any written work. Invoke as /codex, optionally with "review", "review <base-branch>" or a question.
---

# Codex second opinion

Codex is a separate AI model. Its value is that it does not share Claude's
blind spots, so use it to **check** work, not to replace Claude's own thinking.

All calls go through `scripts/codex.sh` (it installs Codex if missing and
stops with sign-in steps if it is not signed in).

## 1. Check it is ready

```bash
scripts/codex.sh status
```

If it prints "Not logged in", stop and tell the user. They can sign in with
an API key (`printenv OPENAI_API_KEY | codex login --with-api-key`) or a
ChatGPT account (`codex login --device-auth`). Never ask for the key in chat.

## 2. Pick the mode

| Situation | Command |
|---|---|
| Review uncommitted changes before a commit | `scripts/codex.sh review` |
| Review the whole branch | `scripts/codex.sh review main` |
| Question, design choice, bug hypothesis, writing review | `scripts/codex.sh ask "<prompt>"` |
| Long prompt (paste file contents, chapter text) | write it to a scratch file, then `scripts/codex.sh ask - < file` |

`ask` runs Codex **read-only**. It can read the repo but cannot change files.

## 3. Write a good `ask` prompt

Give Codex what it needs to judge on its own:
- the goal, in one or two sentences
- the relevant file paths (it can read them) or the pasted text
- what you want back: "list concrete problems, most severe first, with file:line"
- for academic writing: the required format (for example the user's thesis
  format, chapter structure, citation style) and ask it to check
  argument, structure, evidence and citations against that format

Do not tell Codex what Claude concluded first. That biases it.

## 4. Use the answer critically

- Verify each point against the code or text. Codex can be wrong.
- Fix what is confirmed. Say which points you rejected and why.
- Report to the user in short form: what Codex found, what you changed,
  what you disagreed with.
