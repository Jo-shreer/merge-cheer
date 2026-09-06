# How to ship a Merge Cheer release

A Marketplace-facing Release is **tests plus a human review**. Pushing a
tag does not publish anything. GitHub also cannot tick the Marketplace
box through the API — this workflow only creates the GitHub Release.

## One-time: review environment

The `release` job uses `environment: marketplace`. That name does
nothing until a required reviewer exists.

1. Open [Settings → Environments](https://github.com/YauhenBichel/merge-cheer/settings/environments)
2. Create an environment named **`marketplace`** (exact spelling)
3. Enable **Required reviewers** and add at least one person
4. Save

Until that Settings click, the job will not wait for Approve.

## Cut a reviewed release

Land the work on the default branch. Wait until **CI / test** is green
on the commit you intend to ship. Then tag that commit. Semver only
(`vMAJOR.MINOR.PATCH`). Do not force-move `v1`.

```
git tag v1.2.0
git push origin v1.2.0
```

`v1` is the first tag on this repository, not a floating major this
workflow maintains. Consumers may keep `uses: YauhenBichel/merge-cheer@v1`
only if a human later chooses to move that tag. Never `git tag -f v1`
from automation.

1. Actions → **Release** → Run workflow
2. Use the default branch (or the tag itself)
3. Version input: `v1.2.0` (leading `v`, three numbers)
4. The **test** job checks out that tag and runs
   `python3 -m unittest discover -s tests -q`
5. If tests fail, stop. Nothing is published.
6. The **release** job then waits on the `marketplace` environment.
   Open the deployment review and click **Approve**.
7. `gh release create` publishes the GitHub Release for that tag.
   `action.yml` is not an asset — the tag **is** the Action version.

## Marketplace (browser, first listing only)

After the reviewed Release exists, and only then:

https://github.com/YauhenBichel/merge-cheer/releases/edit/v1.2.0

Tick **Publish this Action to the GitHub Marketplace**, pick a
category, and save. 2FA is required. That checkbox is a one-time
browser step. Later reviewed Releases update the existing listing if
it is already published.

Do not add a Marketplace badge until that listing is live.
