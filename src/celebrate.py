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
    "comic",
    "sunny",
    "game",
    "sticker",
    "yeah",
    "devops",
    "sre",
    "qa",
    "design",
    "architecture",
    "engineering",
    "backend",
    "frontend",
    "java",
    "python",
    "cpp",
    "golang",
)

# Extra spellings that resolve to a group. `auto` and `title` are not aliases.
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
    "comic": "comic",
    "kapow": "comic",
    "sunny": "sunny",
    "sunshine": "sunny",
    "game": "game",
    "level-up": "game",
    "levelup": "game",
    "combo": "game",
    "sticker": "sticker",
    "stickers": "sticker",
    "yeah": "yeah",
    "lets-go": "yeah",
    "let's-go": "yeah",
    "fist-pump": "yeah",
    "devops": "devops",
    "k8s": "devops",
    "kubernetes": "devops",
    "docker": "devops",
    "terraform": "devops",
    "sre": "sre",
    "oncall": "sre",
    "on-call": "sre",
    "qa": "qa",
    "testing": "qa",
    "sdet": "qa",
    "design": "design",
    "ux": "design",
    "ui": "design",
    "figma": "design",
    "architecture": "architecture",
    "arch": "architecture",
    "adr": "architecture",
    "engineering": "engineering",
    "swe": "engineering",
    "software-engineering": "engineering",
    "backend": "backend",
    "back-end": "backend",
    "frontend": "frontend",
    "front-end": "frontend",
    "javascript": "frontend",
    "typescript": "frontend",
    "js": "frontend",
    "react": "frontend",
    "java": "java",
    "jdk": "java",
    "jvm": "java",
    "python": "python",
    "py": "python",
    "cpp": "cpp",
    "c++": "cpp",
    "cplusplus": "cpp",
    "cxx": "cpp",
    "golang": "golang",
    "go": "golang",
    "gopher": "golang",
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
    "comic": "comic",
    "sunny": "sunny",
    "game": "level up",
    "sticker": "sticker",
    "yeah": "yeah",
    "devops": "devops",
    "sre": "sre",
    "qa": "testing",
    "design": "design",
    "architecture": "architecture",
    "engineering": "engineering",
    "backend": "backend",
    "frontend": "frontend",
    "java": "java",
    "python": "python",
    "cpp": "c++",
    "golang": "golang",
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
    "comic": "comic",
    "sunny": "sunny",
    "game": "game",
    "sticker": "sticker",
    "yeah": "yeah",
    "devops": "devops",
    "sre": "sre",
    "qa": "qa",
    "design": "design",
    "architecture": "architecture",
    "engineering": "engineering",
    "backend": "backend",
    "frontend": "frontend",
    "java": "java",
    "python": "python",
    "cpp": "c++",
    "golang": "golang",
}

FIRST_TIMERS = frozenset({"FIRST_TIMER", "FIRST_TIME_CONTRIBUTOR"})

# Title keywords, first match wins. Conventional types stay above mood
# groups so "feat" / "fix" are not stolen. Keep "ship" and "space" off
# bare substrings ("fellowship", "namespace").
_TITLE_RULES = (
    ("fix", ("fix", "bug", "hotfix", "patch", "revert:", "revert ")),
    ("ship", ("feat", "add ", "added", "new ", "launch", "ship:", "ship ", "perf:", "perf ")),
    ("docs", ("doc", "readme")),
    ("tests", ("test", " ci", "ci:", "ci ", "-ci")),
    ("cleanup", ("refactor", "clean", "deps:", "deps ")),
    ("welcome", ("welcome", "first contrib", "good first", "first-time")),
    ("party", ("party", "congrats", "woo", "hooray", "celebrate")),
    ("space", ("cosmos", "galaxy", "orbit", "planet", "outer space")),
    ("magic", ("magic", "sparkle", "wand", "spell")),
    ("coffee", ("coffee", "latte", "caffeine", "espresso")),
    ("robot", ("robot", "android")),
    ("comic", ("comic", "kapow")),
    ("sunny", ("sunny", "sunshine", "sunbeam")),
    ("game", ("level-up", "level up", "combo", "high-score", "high score")),
    ("sticker", ("sticker",)),
    ("yeah", ("yeah", "let's go", "lets go", "fist pump", "fist-pump")),
    ("devops", ("devops", "kubernetes", "k8s", "terraform", "docker", "helm")),
    ("sre", ("sre", "on-call", "oncall", "error budget", "slo")),
    ("qa", (" qa", "qa:", "sdet", "quality")),
    ("design", ("design", "figma", "ux ", " ui:", "mockup")),
    ("architecture", ("architecture", "adr", "system design")),
    ("engineering", ("software engineering", " swe ", "swe:", "swe ")),
    ("backend", ("backend", "back-end", "graphql")),
    ("frontend", ("frontend", "front-end", "javascript", "typescript", "react", "vue")),
    ("python", ("python", "django", "flask")),
    ("cpp", ("c++", "cplusplus", " cpp", "cpp:", "cpp ")),
    ("golang", ("golang", "gopher")),
    ("java", ("java:", "java ", "jdk", "jvm", "spring boot")),
)


def allowed_topics() -> str:
    return ", ".join(("auto", "title") + GROUPS)


def normalize_topic(value: str) -> str:
    raw = (value or "auto").strip().lower().replace("_", "-")
    if raw in ("", "auto"):
        return "auto"
    if raw == "title":
        return "title"
    return ALIASES.get(raw, "")


def pick_from_title(title: str, association: str = "") -> str:
    low = title.lower()
    for group, words in _TITLE_RULES:
        if any(word in low for word in words):
            return group
    if association.upper() in FIRST_TIMERS:
        return "welcome"
    return "celebration"


def pick_random_group(seed: str = "") -> str:
    """Seeded by PR number when set; otherwise the clock."""
    return random.Random(seed or None).choice(GROUPS)


def resolve_group(
    title: str, topic: str, association: str = "", seed: str = ""
) -> str:
    """Pick a group. Unknown explicit topics fall back to celebration."""
    chosen = normalize_topic(topic)
    if chosen == "auto":
        return pick_random_group(seed)
    if chosen == "title":
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


# Filenames the Action ships. Used when gifs/ is not on disk (GitLab /
# Bitbucket curl the script only). Keep in sync with scripts/make_gifs.py.
BUNDLED_GIFS = {
    "ship": ("ship-it.gif", "alt.gif", "boost.gif"),
    "fix": ("nailed-it.gif", "alt.gif", "spark.gif"),
    "docs": ("nice-work.gif", "alt.gif", "glow.gif"),
    "tests": ("high-five.gif", "alt.gif"),
    "cleanup": ("cleanup.gif", "alt.gif", "sweep.gif"),
    "celebration": ("celebration.gif", "alt.gif", "burst.gif"),
    "welcome": ("high-five.gif", "celebration.gif"),
    "party": ("confetti.gif", "toast.gif"),
    "space": ("planet.gif", "comet.gif"),
    "magic": ("wand.gif", "sparkles.gif"),
    "coffee": ("mug.gif", "night.gif"),
    "robot": ("wave.gif", "dance.gif"),
    "comic": ("burst.gif", "pop.gif"),
    "sunny": ("sun.gif", "rainbow.gif"),
    "game": ("levelup.gif", "combo.gif"),
    "sticker": ("star.gif", "thumb.gif"),
    "yeah": ("pump.gif", "jump.gif"),
    "devops": ("loop.gif", "pipeline.gif"),
    "sre": ("lighthouse.gif", "pager.gif"),
    "qa": ("lens.gif", "pass.gif"),
    "design": ("palette.gif", "frames.gif"),
    "architecture": ("blocks.gif", "blueprint.gif"),
    "engineering": ("wrench.gif", "build.gif"),
    "backend": ("db.gif", "server.gif"),
    "frontend": ("browser.gif", "cursor.gif"),
    "java": ("mug.gif", "steam.gif"),
    "python": ("snake.gif", "coil.gif"),
    "cpp": ("plus.gif", "gear.gif"),
    "golang": ("gopher.gif", "wave.gif"),
}


def group_gif_names(root: Path, group: str) -> list[str]:
    folder = root / "gifs" / group
    names = [path.name for path in sorted(folder.glob("*.gif"))]
    if names:
        return names
    return list(BUNDLED_GIFS.get(group, ()))


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


DEFAULT_ACTION_REPO = "YauhenBichel/merge-cheer"


def bundled_url(action_repo: str, action_ref: str, group: str, name: str) -> str:
    if not name:
        return ""
    repo = (action_repo or "").strip() or DEFAULT_ACTION_REPO
    return (
        f"https://raw.githubusercontent.com/{repo}/"
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


def detect_host() -> str:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return "github"
    if os.environ.get("GITLAB_CI") == "true":
        return "gitlab"
    if os.environ.get("BITBUCKET_COMMIT") or os.environ.get("BITBUCKET_REPO_FULL_NAME"):
        return "bitbucket"
    return "github"


def is_bot_author(author: str, kind: str = "") -> bool:
    if (kind or "").lower() == "bot":
        return True
    low = (author or "").lower()
    if not low:
        return False
    return (
        low.endswith("[bot]")
        or low.endswith("_bot")
        or low.endswith("-bot")
        or "dependabot" in low
        or low in {"ghost", "renovate-bot", "bitbucket-pipelines"}
    )


def _http_json(
    url: str, token: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None
) -> object:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers=headers
        or {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "merge-cheer",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
        print(f"{method} {response.status}")
        if not raw:
            return {}
        return json.loads(raw)


def post_github_comment(token: str, repo: str, number: str, body: str) -> None:
    if not token or not repo or not number:
        raise SystemExit("GITHUB_TOKEN, GITHUB_REPOSITORY, and PR_NUMBER are required")
    _http_json(
        f"https://api.github.com/repos/{repo}/issues/{number}/comments",
        token,
        method="POST",
        payload={"body": body},
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "merge-cheer",
            "Content-Type": "application/json",
        },
    )


def gitlab_headers(token: str) -> dict[str, str]:
    job = os.environ.get("CI_JOB_TOKEN", "").strip()
    if job and token == job:
        return {
            "JOB-TOKEN": token,
            "User-Agent": "merge-cheer",
            "Content-Type": "application/json",
        }
    return {
        "PRIVATE-TOKEN": token,
        "User-Agent": "merge-cheer",
        "Content-Type": "application/json",
    }


def gitlab_api_root() -> str:
    explicit = os.environ.get("CI_API_V4_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    host = os.environ.get("CI_SERVER_URL", "https://gitlab.com").rstrip("/")
    return f"{host}/api/v4"


def post_gitlab_note(token: str, project: str, iid: str, body: str) -> None:
    if not token or not project or not iid:
        raise SystemExit("GITLAB_TOKEN, CI_PROJECT_ID, and merge request iid are required")
    encoded = urllib.parse.quote(str(project), safe="")
    _http_json(
        f"{gitlab_api_root()}/projects/{encoded}/merge_requests/{iid}/notes",
        token,
        method="POST",
        payload={"body": body},
        headers=gitlab_headers(token),
    )


def lookup_gitlab_mr(token: str) -> dict[str, str]:
    project = os.environ.get("CI_PROJECT_ID", "").strip()
    iid = os.environ.get("CI_MERGE_REQUEST_IID", "").strip()
    sha = os.environ.get("CI_COMMIT_SHA", "").strip()
    if not token or not project:
        return {}
    encoded = urllib.parse.quote(project, safe="")
    data: object
    if iid:
        data = _http_json(
            f"{gitlab_api_root()}/projects/{encoded}/merge_requests/{iid}",
            token,
            headers=gitlab_headers(token),
        )
    elif sha:
        data = _http_json(
            f"{gitlab_api_root()}/projects/{encoded}/repository/commits/{sha}/merge_requests",
            token,
            headers=gitlab_headers(token),
        )
        if isinstance(data, list):
            data = data[0] if data else {}
    else:
        return {}
    if not isinstance(data, dict) or not data:
        return {}
    if str(data.get("state") or "") not in {"merged", ""}:
        if iid and str(data.get("state") or "") != "merged":
            return {}
    user = data.get("author") or {}
    return {
        "number": str(data.get("iid") or iid),
        "title": str(data.get("title") or ""),
        "author": str(user.get("username") or ""),
        "association": "FIRST_TIME_CONTRIBUTOR"
        if data.get("first_contribution")
        else "",
    }


def post_bitbucket_comment(token: str, workspace: str, slug: str, number: str, body: str) -> None:
    if not token or not workspace or not slug or not number:
        raise SystemExit(
            "BITBUCKET_ACCESS_TOKEN, BITBUCKET_WORKSPACE, BITBUCKET_REPO_SLUG, and PR id are required"
        )
    _http_json(
        f"https://api.bitbucket.org/2.0/repositories/{workspace}/{slug}/pullrequests/{number}/comments",
        token,
        method="POST",
        payload={"content": {"raw": body}},
    )


def lookup_bitbucket_pr(token: str) -> dict[str, str]:
    workspace = os.environ.get("BITBUCKET_WORKSPACE", "").strip()
    slug = os.environ.get("BITBUCKET_REPO_SLUG", "").strip()
    number = os.environ.get("BITBUCKET_PR_ID", "").strip()
    commit = os.environ.get("BITBUCKET_COMMIT", "").strip()
    if not token or not workspace or not slug:
        return {}
    data: object
    if number:
        data = _http_json(
            f"https://api.bitbucket.org/2.0/repositories/{workspace}/{slug}/pullrequests/{number}",
            token,
        )
    elif commit:
        data = _http_json(
            f"https://api.bitbucket.org/2.0/repositories/{workspace}/{slug}/commit/{commit}/pullrequests",
            token,
        )
        values = data.get("values") if isinstance(data, dict) else None
        data = values[0] if values else {}
    else:
        return {}
    if not isinstance(data, dict) or not data:
        return {}
    state = str(data.get("state") or "").upper()
    if state and state != "MERGED":
        return {}
    author = ((data.get("author") or {}).get("nickname") or "")
    return {
        "number": str(data.get("id") or number),
        "title": str(data.get("title") or ""),
        "author": str(author),
        "association": "",
    }


def post_comment(token: str, repo: str, number: str, body: str) -> None:
    post_github_comment(token, repo, number, body)


def write_output(path: str, values: dict[str, str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    host = detect_host()
    title = os.environ.get("PR_TITLE", "")
    topic = os.environ.get("TOPIC", "auto")
    association = os.environ.get("PR_AUTHOR_ASSOCIATION", "")
    author = os.environ.get("PR_AUTHOR", "").strip()
    number = os.environ.get("PR_NUMBER", "").strip()
    if host == "gitlab" and not number:
        found = lookup_gitlab_mr(
            (
                os.environ.get("GITLAB_TOKEN")
                or os.environ.get("CI_JOB_TOKEN")
                or ""
            ).strip()
        )
        title = title or found.get("title", "")
        author = author or found.get("author", "")
        number = found.get("number", "")
        association = association or found.get("association", "")
    if host == "bitbucket" and not number:
        found = lookup_bitbucket_pr(
            os.environ.get("BITBUCKET_ACCESS_TOKEN", "").strip()
        )
        title = title or found.get("title", "")
        author = author or found.get("author", "")
        number = found.get("number", "")
    if is_bot_author(author, os.environ.get("PR_AUTHOR_TYPE", "")):
        print("skip bot author")
        return 0
    if host in {"gitlab", "bitbucket"} and not number:
        print("skip: no merged merge request")
        return 0
    group = resolve_group(title, topic, association, number)
    root = action_root()
    group, name = choose_gif(root, group, number)
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
    if host == "gitlab":
        post_gitlab_note(
            (
                os.environ.get("GITLAB_TOKEN")
                or os.environ.get("CI_JOB_TOKEN")
                or ""
            ).strip(),
            os.environ.get("CI_PROJECT_ID", "").strip(),
            number,
            body,
        )
        return 0
    if host == "bitbucket":
        post_bitbucket_comment(
            os.environ.get("BITBUCKET_ACCESS_TOKEN", "").strip(),
            os.environ.get("BITBUCKET_WORKSPACE", "").strip(),
            os.environ.get("BITBUCKET_REPO_SLUG", "").strip(),
            number,
            body,
        )
        return 0
    post_github_comment(
        os.environ.get("GITHUB_TOKEN", "").strip(),
        os.environ.get("GITHUB_REPOSITORY", "").strip(),
        number,
        body,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
