#!/usr/bin/env python3
"""Pick a merge GIF and comment it on the pull request. Stdlib only."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

TAGS = (
    "nailed it",
    "ship it",
    "nice work",
    "high five",
    "cleanup",
    "celebration",
)


def pick_tag(title: str) -> str:
    low = title.lower()
    if any(word in low for word in ("fix", "bug", "hotfix", "patch")):
        return "nailed it"
    if any(word in low for word in ("feat", "add ", "added", "new ")):
        return "ship it"
    if any(word in low for word in ("doc", "readme")):
        return "nice work"
    if any(word in low for word in ("test", "ci")):
        return "high five"
    if any(word in low for word in ("refactor", "clean")):
        return "cleanup"
    return "celebration"


def slug(tag: str) -> str:
    return tag.replace(" ", "-")


def normalize_ref(ref: str) -> str:
    value = (ref or "main").strip() or "main"
    for prefix in ("refs/heads/", "refs/tags/"):
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def bundled_url(action_repo: str, action_ref: str, tag: str) -> str:
    return (
        f"https://raw.githubusercontent.com/{action_repo}/"
        f"{normalize_ref(action_ref)}/gifs/{slug(tag)}.gif"
    )


def giphy_url(key: str, tag: str, rating: str) -> str:
    if not key:
        return ""
    query = urllib.parse.urlencode(
        {"api_key": key, "tag": tag, "rating": rating or "g"}
    )
    request = urllib.request.Request(
        f"https://api.giphy.com/v1/gifs/random?{query}",
        headers={"User-Agent": "merge-cheer"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"giphy skipped: {exc}", file=sys.stderr)
        return ""
    images = (payload.get("data") or {}).get("images") or {}
    return str(
        (images.get("downsized") or {}).get("url")
        or (images.get("original") or {}).get("url")
        or ""
    )


def comment_body(message: str, author: str, tag: str, gif: str) -> str:
    text = (message or "Merged — thank you @{author}.").replace("{author}", author)
    if not text.endswith("\n"):
        text += "\n"
    if gif:
        text += f"\n![{tag}]({gif})\n"
    return text


def post_comment(token: str, repo: str, number: str, body: str) -> None:
    if not token or not repo or not number:
        raise SystemExit("GITHUB_TOKEN, GITHUB_REPOSITORY, and PR_NUMBER are required")
    data = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{number}/comments",
        data=data,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "merge-cheer",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        print(f"commented {response.status}")


def write_output(path: str, values: dict[str, str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    title = os.environ.get("PR_TITLE", "")
    tag = pick_tag(title)
    gif = giphy_url(
        os.environ.get("GIPHY_API_KEY", "").strip(),
        tag,
        os.environ.get("GIPHY_RATING", "g").strip() or "g",
    )
    if not gif:
        gif = bundled_url(
            os.environ.get("ACTION_REPO", "").strip(),
            os.environ.get("ACTION_REF", "main"),
            tag,
        )
    author = os.environ.get("PR_AUTHOR", "").strip()
    body = comment_body(os.environ.get("MESSAGE", ""), author, tag, gif)
    write_output(
        os.environ.get("GITHUB_OUTPUT", ""),
        {"url": gif, "tag": tag, "body": body.replace("\n", "%0A")},
    )
    if os.environ.get("DRY_RUN") == "1":
        print(body)
        return 0
    post_comment(
        os.environ.get("GITHUB_TOKEN", "").strip(),
        os.environ.get("GITHUB_REPOSITORY", "").strip(),
        os.environ.get("PR_NUMBER", "").strip(),
        body,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
