# Security

Merge Cheer is meant to run on `pull_request_target` so a fork merge
can still get a comment. That event has access to this repository's
secrets. The Action therefore:

- does not check out the pull request head
- reads the title, body, and labels from environment variables
- only posts a comment
- calls a model only when `model` / `model-api-key` is set; a failed
  or unsafe reply falls back to the stdlib path

## Reporting a vulnerability

Open a **public** GitHub issue on this repo. Label it `security` if you can.

Include:

- what the issue is and where in the code it lives
- how to reproduce it
- what an attacker could do with it

Do **not** paste live API keys, tokens, or `.env` contents into the issue.
Redact secrets and describe them instead.

## Scope

In scope:

- checking out pull request head from `pull_request_target`
- interpolating `PR_TITLE` into a shell
- secrets committed to the repository
- a comment that does more than post Markdown

Out of scope (a normal issue is fine):

- Giphy returning a dull GIF when a key is set
- a title keyword mapping you disagree with

## Data safety

- Never commit `.env` or tokens
- Never paste a real API key into an issue, even as a "repro"
