# I got tired of merge GIFs that needed a Giphy key

**A GitHub Action that comments a G-rated GIF when a pull request merges. v1.3.0 picks a random theme by default. No Giphy secret.**

Most “celebrate the merge” Actions do the same two things.

They ask for a Giphy API key. Then they post whatever the API returns. Sometimes that is a pixel parrot that has nothing to do with the pull request. Sometimes the key is missing and the comment is empty. You also have to trust a third-party GIF search on every merge.

I wanted the other shape: merge a PR, get one comment, see a GIF I actually own.

That is [Merge Cheer](https://github.com/YauhenBichel/merge-cheer).

It is a small GitHub Action. On `pull_request_target` closed, if the PR merged and the author is not a bot, it comments a thank-you plus a G-rated looping GIF. It does not check out the pull request. It does not need a secret. The GIFs live in the Action repo.

Live demo (the loops move on the page):

https://yauhenbichel.github.io/merge-cheer/

Two of the files the Action posts:

![comic pop](https://yauhenbichel.github.io/merge-cheer/gifs/comic/pop.gif)

![sunny](https://yauhenbichel.github.io/merge-cheer/gifs/sunny/sun.gif)

The comment itself is boring on purpose:

```
Merged — thank you @alice.

![comic](https://raw.githubusercontent.com/YauhenBichel/merge-cheer/v1.3.0/gifs/comic/pop.gif)
```

Install is one step, pinned to the current release:

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
      - uses: YauhenBichel/merge-cheer@v1.3.0
```

`topic` defaults to `auto`. That is a **random theme**, seeded by the pull request number so the same PR does not flip if the job reruns. Different PR numbers can land on comic, sunny, ship, party, and the rest.

Pin a mood when you want the same group every time:

```yaml
- uses: YauhenBichel/merge-cheer@v1.3.0
  with:
    topic: comic
```

`topic: title` is the old picker. It reads keywords in the PR title (`fix`, `feat`, `docs`, …). Keep it if you liked that. New installs can leave `topic` unset.

An unknown name falls back to `celebration` and prints the allowed list.

I already run this on the MoleCare repos, py-harness, python-vibe, and readme-contributors, all on the default branch at `@v1.3.0`.

Repo: https://github.com/YauhenBichel/merge-cheer

Release: https://github.com/YauhenBichel/merge-cheer/releases/tag/v1.3.0
