# Merge Cheer

Comment a G-rated celebration GIF when a pull request merges.

No Giphy key. No checkout of the pull request. The action ships its own
moods and picks one from the title (`fix` / `feat` / `docs` / `test` /
`refactor`, otherwise a general celebration).

## Install

```yaml
name: Celebrate merge
on:
  pull_request_target:
    types: [closed]
permissions:
  pull-requests: write
jobs:
  celebrate:
    if: github.event.pull_request.merged && github.event.pull_request.user.type != 'Bot'
    runs-on: ubuntu-latest
    steps:
      - uses: YauhenBichel/merge-cheer@v1
```

`pull_request_target` is what lets a fork merge get a comment. The action
never checks out the pull request head.

## Moods

| Title contains | GIF |
| --- | --- |
| `fix`, `bug`, `hotfix`, `patch` | ![nailed it](gifs/nailed-it.gif) |
| `feat`, `add `, `added`, `new ` | ![ship it](gifs/ship-it.gif) |
| `doc`, `readme` | ![nice work](gifs/nice-work.gif) |
| `test`, `ci` | ![high five](gifs/high-five.gif) |
| `refactor`, `clean` | ![cleanup](gifs/cleanup.gif) |
| anything else | ![celebration](gifs/celebration.gif) |

## Inputs

| Input | Default | What it does |
| --- | --- | --- |
| `github-token` | `${{ github.token }}` | Posts the comment |
| `giphy-api-key` | empty | Optional. When set, try a G-rated Giphy GIF first |
| `message` | `Merged — thank you @{author}.` | `{author}` becomes the PR author |
| `rating` | `g` | Giphy rating when a key is set |

```yaml
- uses: YauhenBichel/merge-cheer@v1
  with:
    giphy-api-key: ${{ secrets.GIPHY_API_KEY }}
    message: "Shipped. Thank you @{author}."
```

## Why this instead of a random Giphy Action

Most merge-GIF actions need a Giphy key and post whatever the API
returns. Merge Cheer works on a new repository with zero secrets, and
the fallback is a set of owned looping GIFs — not a pixel parrot.

## Security

- The title is read from an environment variable, not interpolated into a shell.
- The action does not check out code.
- It only comments. It does not push, merge, or approve.

See [SECURITY.md](SECURITY.md).

## Publish a release

This folder is the Action. On GitHub: create a **public** repository
named `merge-cheer`, push `main`, then tag `v1`. Marketplace listing is
**Settings → actions → publish** after that tag exists.

## Rebuild the GIFs

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/make_gifs.py
```

## License

MIT. The GIFs are original stills animated for this Action. See [NOTICE](NOTICE).

## Contributors

Thank you to everyone who has helped.

<!-- readme: contributors,bots/- -start -->
<!-- readme: contributors,bots/- -end -->

Filled from GitHub commits (bots omitted). Live demo: [readme-contributors](https://github.com/YauhenBichel/readme-contributors#live-demo).
