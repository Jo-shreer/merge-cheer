# List Merge Cheer on GitLab and Bitbucket

The GitHub Action stays the source. GitLab and Bitbucket reuse
`src/celebrate.py`. GIFs stay on GitHub raw URLs. This file is the
listing work a human still has to do — neither catalog can be ticked
from this repository alone.

Do not claim a listing is live until the catalog URL returns 200.

## GitLab CI/CD Catalog

GitLab’s marketplace is the [CI/CD Catalog](https://gitlab.com/explore/catalog).
A component project must live **on GitLab**.

1. Create a public GitLab project (for example `yauhenbichel/merge-cheer`).
2. Mirror this GitHub repo into it (pull mirror, or push both remotes).
3. Set a project description. Keep `README.md` and `templates/merge-cheer.yml`.
4. Settings → General → Visibility → **CI/CD Catalog project** (Owner).
5. Add a project access token named `GITLAB_TOKEN` with `api` scope.
   `CI_JOB_TOKEN` cannot post merge-request notes.
6. Push a semver tag (`v1.3.0`). `.gitlab-ci.yml` runs tests, then a
   `release:` job. GitLab only indexes versions created with that keyword.
7. Search the catalog for Merge Cheer. The include path is:

```yaml
include:
  - component: $CI_SERVER_FQDN/yauhenbichel/merge-cheer/merge-cheer@v1.3.0
    inputs:
      topic: auto
      token: $GITLAB_TOKEN
```

Until the catalog row exists, consumers can copy
[examples/gitlab-ci.yml](examples/gitlab-ci.yml).

## Bitbucket Pipes

Bitbucket’s directory is [Pipes](https://support.atlassian.com/bitbucket-cloud/docs/what-are-pipes/).
A complete pipe needs a public Docker image.

1. Build and push `yauhenbichel/merge-cheer:1.3.0` from this `Dockerfile`
   (Docker Hub account required).
2. Keep `pipe.yml` pointing at that image.
3. Store `BITBUCKET_ACCESS_TOKEN` on the consumer repo (pullrequest write).
4. To appear in the Pipelines UI catalog, open a PR against
   [official-pipes](https://bitbucket.org/atlassian/official-pipes) with a
   `pipes/merge-cheer.yml` manifest. Atlassian reviews it.
5. Until that review lands, consumers run
   [examples/bitbucket-pipelines.yml](examples/bitbucket-pipelines.yml)
   or:

```yaml
script:
  - pipe: docker://yauhenbichel/merge-cheer:1.3.0
    variables:
      TOPIC: auto
      BITBUCKET_ACCESS_TOKEN: $BITBUCKET_ACCESS_TOKEN
```

## GitHub Marketplace

Still the browser tick on `releases/edit/<tag>` for the first listing.
See [RELEASE.md](RELEASE.md).
