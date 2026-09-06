#!/usr/bin/env python3
"""Pick a merge GIF and comment it on the pull request. Stdlib only."""

from __future__ import annotations

import json
import os
import random
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Public group names. Users pass these as `topic`.
GROUPS = (
    "ship",
    "fix",
    "docs",
    "tests",
    "cleanup",
    "celebration",
    "welcome",
    "party",
    "space",
    "magic",
    "coffee",
    "robot",
)

# Extra spellings that resolve to a group. `auto` is handled separately.
ALIASES = {
    "ship": "ship",
    "launch": "ship",
    "ship-it": "ship",
    "ship it": "ship",
    "fix": "fix",
    "nailed-it": "fix",
    "nailed it": "fix",
    "docs": "docs",
    "doc": "docs",
    "nice-work": "docs",
    "nice work": "docs",
    "tests": "tests",
    "test": "tests",
    "ci": "tests",
    "high-five": "tests",
    "high five": "tests",
    "cleanup": "cleanup",
    "refactor": "cleanup",
    "clean": "cleanup",
    "celebration": "celebration",
    "welcome": "welcome",
    "first": "welcome",
    "first-contribution": "welcome",
    "party": "party",
    "congrats": "party",
    "woo": "party",
    "hooray": "party",
    "space": "space",
    "cosmos": "space",
    "galaxy": "space",
    "magic": "magic",
    "sparkle": "magic",
    "coffee": "coffee",
    "latte": "coffee",
    "robot": "robot",
    "bot": "robot",
}

# Giphy search text when a key is set.
GIPHY_TAG = {
    "ship": "ship it",
    "fix": "nailed it",
    "docs": "nice work",
    "tests": "high five",
    "cleanup": "cleanup",
    "celebration": "celebration",
    "welcome": "high five",
    "party": "celebration",
    "space": "stars",
    "magic": "magic",
    "coffee": "coffee",
    "robot": "robot",
}

# Alt text for the posted image.
LABEL = {
    "ship": "ship it",
    "fix": "nailed it",
    "docs": "nice work",
    "tests": "high five",
    "cleanup": "cleanup",
    "celebration": "celebration",
    "welcome": "welcome",
    "party": "party",
    "space": "space",
    "magic": "magic",
    "coffee": "coffee",
    "robot": "robot",
}

FIRST_TIMERS = frozenset({"FIRST_TIMER", "FIRST_TIME_CONTRIBUTOR"})

# Title keywords, first match wins. Conventional types stay above mood
# groups so "feat" / "fix" are not stolen. Keep "ship" and "space" off
# bare substrings ("fellowship", "namespace").
_TITLE_RULES = (
    ("fix", ("fix", "bug", "hotfix", "patch")),
    ("ship", ("feat", "add ", "added", "new ", "launch", "ship:", "ship ")),
    ("docs", ("doc", "readme")),
    ("tests", ("test", "ci")),
    ("cleanup", ("refactor", "clean")),
    ("welcome", ("welcome", "first contrib", "good first", "first-time")),
    ("party", ("party", "congrats", "woo", "hooray", "celebrate")),
    ("space", ("cosmos", "galaxy", "orbit", "planet", "outer space")),
    ("magic", ("magic", "sparkle", "wand", "spell")),
    ("coffee", ("coffee", "latte", "caffeine", "espresso")),
    ("robot", ("robot", "android")),
)


def allowed_topics() -> str:
    return ", ".join(("auto",) + GROUPS)


def normalize_topic(value: str) -> str:
    raw = (value or "auto").strip().lower().replace("_", "-")
    if raw in ("", "auto"):
        return "auto"
    return ALIASES.get(raw, "")


def pick_from_title(title: str, association: str = "") -> str:
    low = title.lower()
    for group, words in _TITLE_RULES:
        if any(word in low for word in words):
            return group
    if association.upper() in FIRST_TIMERS:
        return "welcome"
    return "celebration"


def resolve_group(title: str, topic: str, association: str = "") -> str:
    """Pick a group. Unknown explicit topics fall back to celebration."""
    chosen = normalize_topic(topic)
    if chosen == "auto":
        return pick_from_title(title, association)
    if not chosen:
        print(
            f"unknown topic {topic!r}; allowed: {allowed_topics()}",
            file=sys.stderr,
        )
        return "celebration"
    return chosen


def action_root() -> Path:
    override = os.environ.get("ACTION_PATH", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1]


def group_gif_names(root: Path, group: str) -> list[str]:
    folder = root / "gifs" / group
    return [path.name for path in sorted(folder.glob("*.gif"))]


def pick_gif_name(names: list[str], seed: str) -> str:
    if not names:
        return ""
    return names[random.Random(seed).randrange(len(names))]


def choose_gif(root: Path, group: str, seed: str) -> tuple[str, str]:
    names = group_gif_names(root, group)
    if not names and group != "celebration":
        group = "celebration"
        names = group_gif_names(root, group)
    return group, pick_gif_name(names, f"{seed}:{group}")


def slug(tag: str) -> str:
    return tag.replace(" ", "-")


def normalize_ref(ref: str) -> str:
    value = (ref or "main").strip() or "main"
    for prefix in ("refs/heads/", "refs/tags/"):
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def bundled_url(action_repo: str, action_ref: str, group: str, name: str) -> str:
    if not name:
        return ""
    return (
        f"https://raw.githubusercontent.com/{action_repo}/"
        f"{normalize_ref(action_ref)}/gifs/{group}/{name}"
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
    topic = os.environ.get("TOPIC", "auto")
    association = os.environ.get("PR_AUTHOR_ASSOCIATION", "")
    group = resolve_group(title, topic, association)
    root = action_root()
    group, name = choose_gif(root, group, os.environ.get("PR_NUMBER", ""))
    gif = giphy_url(
        os.environ.get("GIPHY_API_KEY", "").strip(),
        GIPHY_TAG[group],
        os.environ.get("GIPHY_RATING", "g").strip() or "g",
    )
    if not gif:
        gif = bundled_url(
            os.environ.get("ACTION_REPO", "").strip(),
            os.environ.get("ACTION_REF", "main"),
            group,
            name,
        )
    author = os.environ.get("PR_AUTHOR", "").strip()
    label = LABEL[group]
    body = comment_body(os.environ.get("MESSAGE", ""), author, label, gif)
    write_output(
        os.environ.get("GITHUB_OUTPUT", ""),
        {
            "url": gif,
            "tag": label,
            "group": group,
            "body": body.replace("\n", "%0A"),
        },
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
