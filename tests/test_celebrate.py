"""Merge Cheer must pick a GIF for every mood and never shell the title."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "action.yml"
SCRIPT = ROOT / "src" / "celebrate.py"
GIFS = ROOT / "gifs"

TAGS = (
    "nailed it",
    "ship it",
    "nice work",
    "high five",
    "cleanup",
    "celebration",
)


def _load():
    spec = importlib.util.spec_from_file_location("celebrate", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CelebrateTest(unittest.TestCase):
    def test_every_mood_has_a_gif(self) -> None:
        names = {path.stem for path in GIFS.glob("*.gif")}
        for tag in TAGS:
            self.assertIn(tag.replace(" ", "-"), names)

    def test_no_gif_is_unused(self) -> None:
        used = {tag.replace(" ", "-") for tag in TAGS}
        names = {path.stem for path in GIFS.glob("*.gif")}
        self.assertEqual(sorted(names - used), [])

    def test_gifs_are_small_enough_for_a_comment(self) -> None:
        oversized = [
            f"{path.name} {path.stat().st_size // 1024} KB"
            for path in GIFS.glob("*.gif")
            if path.stat().st_size > 180 * 1024
        ]
        self.assertEqual(oversized, [])

    def test_title_picks_the_mood(self) -> None:
        celebrate = _load()
        self.assertEqual(celebrate.pick_tag("fix: leak"), "nailed it")
        self.assertEqual(celebrate.pick_tag("feat: add login"), "ship it")
        self.assertEqual(celebrate.pick_tag("docs: readme"), "nice work")
        self.assertEqual(celebrate.pick_tag("test: cover ci"), "high five")
        self.assertEqual(celebrate.pick_tag("refactor: clean path"), "cleanup")
        self.assertEqual(celebrate.pick_tag("chore: bump"), "celebration")

    def test_bundled_url_strips_ref_prefixes(self) -> None:
        celebrate = _load()
        url = celebrate.bundled_url(
            "YauhenBichel/merge-cheer", "refs/tags/v1", "ship it"
        )
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/YauhenBichel/merge-cheer/v1/gifs/ship-it.gif",
        )

    def test_comment_mentions_the_author(self) -> None:
        celebrate = _load()
        body = celebrate.comment_body(
            "Merged — thank you @{author}.",
            "alice",
            "ship it",
            "https://example.test/ship-it.gif",
        )
        self.assertIn("@alice", body)
        self.assertIn("ship-it.gif", body)

    def test_action_never_checkouts_the_pull_request(self) -> None:
        text = ACTION.read_text(encoding="utf-8")
        self.assertNotIn("actions/checkout", text)
        self.assertIn("PR_TITLE: ${{ github.event.pull_request.title }}", text)
        self.assertNotIn(
            "${{ github.event.pull_request.title }}\n      run:",
            text,
        )

    def test_action_uses_the_stdlib_script(self) -> None:
        text = ACTION.read_text(encoding="utf-8")
        self.assertIn("src/celebrate.py", text)
        self.assertNotIn("github-script", text)


if __name__ == "__main__":
    unittest.main()
