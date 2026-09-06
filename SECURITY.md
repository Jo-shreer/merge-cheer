# Security

Merge Cheer is meant to run on `pull_request_target` so a fork merge
can still get a comment. That event has access to this repository's
secrets. The Action therefore:

- does not check out the pull request head
- reads the title from an environment variable
- only posts a comment

Report a vulnerability in a public GitHub issue on the Action
repository. Do not paste live tokens.
