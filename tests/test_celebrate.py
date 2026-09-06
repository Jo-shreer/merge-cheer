"""Merge Cheer must pick a GIF for every group and never shell the title."""

from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "action.yml"
SCRIPT = ROOT / "src" / "celebrate.py"
GIFS = ROOT / "gifs"
STILLS = ROOT / "stills"


def _load():
    spec = importlib.util.spec_from_file_location("celebrate", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CelebrateTest(unittest.TestCase):
    def test_every_group_has_a_gif(self) -> None:
        celebrate = _load()
        for group in celebrate.GROUPS:
            names = list((GIFS / group).glob("*.gif"))
            self.assertTrue(names, f"{group} has no GIF")

    def test_a_group_can_hold_several_gifs(self) -> None:
        celebrate = _load()
        counts = [len(list((GIFS / group).glob("*.gif"))) for group in celebrate.GROUPS]
        self.assertGreaterEqual(max(counts), 2)

    def test_mood_groups_have_two_owned_gifs(self) -> None:
        for group in ("party", "space", "magic", "coffee", "robot"):
            names = list((GIFS / group).glob("*.gif"))
            self.assertGreaterEqual(len(names), 2, group)

    def test_no_gif_is_unused(self) -> None:
        celebrate = _load()
        allowed = set(celebrate.GROUPS)
        leftovers = [path.name for path in GIFS.glob("*.gif")]
        leftovers.extend(
            str(path.relative_to(GIFS))
            for path in GIFS.rglob("*.gif")
            if path.parent != GIFS and path.parent.name not in allowed
        )
        self.assertEqual(leftovers, [])

    def test_gifs_are_small_enough_for_a_comment(self) -> None:
        oversized = [
            f"{path.relative_to(GIFS)} {path.stat().st_size // 1024} KB"
            for path in GIFS.rglob("*.gif")
            if path.stat().st_size > 180 * 1024
        ]
        self.assertEqual(oversized, [])

    def test_rebuild_stills_exist(self) -> None:
        for name in (
            "celebration",
            "celebration-burst",
            "ship-it",
            "ship-boost",
            "nailed-it",
            "fix-spark",
            "nice-work",
            "docs-glow",
            "high-five",
            "cleanup",
            "cleanup-sweep",
            "party-confetti",
            "party-toast",
            "space-planet",
            "space-comet",
            "magic-wand",
            "magic-sparkles",
            "coffee-mug",
            "coffee-night",
            "robot-wave",
            "robot-dance",
        ):
            self.assertTrue((STILLS / f"{name}.png").is_file(), name)

    def test_title_picks_the_group(self) -> None:
        celebrate = _load()
        self.assertEqual(celebrate.pick_from_title("fix: leak"), "fix")
        self.assertEqual(celebrate.pick_from_title("feat: add login"), "ship")
        self.assertEqual(celebrate.pick_from_title("docs: readme"), "docs")
        self.assertEqual(celebrate.pick_from_title("test: cover ci"), "tests")
        self.assertEqual(celebrate.pick_from_title("refactor: clean path"), "cleanup")
        self.assertEqual(celebrate.pick_from_title("chore: bump"), "celebration")
        self.assertEqual(celebrate.pick_from_title("welcome first contrib"), "welcome")
        self.assertEqual(celebrate.pick_from_title("party time"), "party")
        self.assertEqual(celebrate.pick_from_title("congrats team"), "party")
        self.assertEqual(celebrate.pick_from_title("woo hooray"), "party")
        self.assertEqual(celebrate.pick_from_title("chore: orbit cosmos"), "space")
        self.assertEqual(celebrate.pick_from_title("chore: magic wand"), "magic")
        self.assertEqual(celebrate.pick_from_title("chore: coffee"), "coffee")
        self.assertEqual(celebrate.pick_from_title("chore: robot helper"), "robot")

    def test_mood_keywords_do_not_steal_conventional_types(self) -> None:
        celebrate = _load()
        self.assertEqual(celebrate.pick_from_title("feat: add party mode"), "ship")
        self.assertEqual(celebrate.pick_from_title("fix: magic number"), "fix")
        self.assertEqual(celebrate.pick_from_title("docs: coffee guide"), "docs")
        self.assertEqual(celebrate.pick_from_title("namespace cleanup"), "cleanup")

    def test_first_timer_generic_title_is_welcome(self) -> None:
        celebrate = _load()
        self.assertEqual(
            celebrate.pick_from_title("chore: bump", "FIRST_TIME_CONTRIBUTOR"),
            "welcome",
        )
        self.assertEqual(celebrate.pick_from_title("fix: leak", "FIRST_TIMER"), "fix")

    def test_auto_topic_uses_the_title(self) -> None:
        celebrate = _load()
        self.assertEqual(celebrate.resolve_group("feat: add login", "auto"), "ship")
        self.assertEqual(celebrate.resolve_group("feat: add login", ""), "ship")

    def test_explicit_topic_selects_that_group(self) -> None:
        celebrate = _load()
        self.assertEqual(celebrate.resolve_group("fix: leak", "ship"), "ship")
        self.assertEqual(celebrate.resolve_group("fix: leak", "launch"), "ship")
        self.assertEqual(celebrate.resolve_group("chore: bump", "welcome"), "welcome")
        self.assertEqual(celebrate.resolve_group("chore: bump", "nailed-it"), "fix")
        self.assertEqual(celebrate.resolve_group("chore: bump", "party"), "party")
        self.assertEqual(celebrate.resolve_group("chore: bump", "congrats"), "party")
        self.assertEqual(celebrate.resolve_group("chore: bump", "space"), "space")
        self.assertEqual(celebrate.resolve_group("chore: bump", "magic"), "magic")
        self.assertEqual(celebrate.resolve_group("chore: bump", "coffee"), "coffee")
        self.assertEqual(celebrate.resolve_group("chore: bump", "bot"), "robot")

    def test_unknown_topic_falls_back_to_celebration(self) -> None:
        celebrate = _load()
        buf = io.StringIO()
        with redirect_stderr(buf):
            group = celebrate.resolve_group("fix: leak", "party-mode")
        self.assertEqual(group, "celebration")
        self.assertIn("party-mode", buf.getvalue())
        self.assertIn("ship", buf.getvalue())
        self.assertIn("welcome", buf.getvalue())

    def test_gif_pick_is_stable_for_a_seed(self) -> None:
        celebrate = _load()
        names = ["a.gif", "b.gif", "c.gif"]
        first = celebrate.pick_gif_name(names, "12:ship")
        second = celebrate.pick_gif_name(names, "12:ship")
        self.assertEqual(first, second)
        self.assertIn(first, names)

    def test_bundled_url_strips_ref_prefixes(self) -> None:
        celebrate = _load()
        url = celebrate.bundled_url(
            "YauhenBichel/merge-cheer", "refs/tags/v1", "ship", "ship-it.gif"
        )
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/YauhenBichel/merge-cheer/v1/gifs/ship/ship-it.gif",
        )

    def test_comment_mentions_the_author(self) -> None:
        celebrate = _load()
        body = celebrate.comment_body(
            "Merged — thank you @{author}.",
            "alice",
            "ship it",
            "https://example.test/ship/ship-it.gif",
        )
        self.assertIn("@alice", body)
        self.assertIn("ship-it.gif", body)

    def test_action_never_checkouts_the_pull_request(self) -> None:
        text = ACTION.read_text(encoding="utf-8")
        self.assertNotIn("actions/checkout", text)
        self.assertIn("PR_TITLE: ${{ github.event.pull_request.title }}", text)
        self.assertIn("TOPIC: ${{ inputs.topic }}", text)
        self.assertNotIn(
            "${{ github.event.pull_request.title }}\n      run:",
            text,
        )

    def test_action_documents_every_group(self) -> None:
        celebrate = _load()
        text = ACTION.read_text(encoding="utf-8")
        self.assertIn("topic:", text)
        for group in celebrate.GROUPS:
            self.assertIn(group, text)

    def test_action_uses_the_stdlib_script(self) -> None:
        text = ACTION.read_text(encoding="utf-8")
        self.assertIn("src/celebrate.py", text)
        self.assertNotIn("github-script", text)

    def test_readme_is_the_live_demo(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Live demo", text)
        self.assertIn("gifs/ship/ship-it.gif", text)
        self.assertIn("gifs/party/confetti.gif", text)
        self.assertIn("gifs/space/planet.gif", text)
        self.assertIn("gifs/magic/wand.gif", text)
        self.assertIn("gifs/coffee/mug.gif", text)
        self.assertIn("gifs/robot/wave.gif", text)
        self.assertIn(".github/workflows/celebrate.yml", text)
        dogfood = (ROOT / ".github" / "workflows" / "celebrate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("uses: ./", dogfood)
        self.assertIn("github.event.repository.default_branch", dogfood)
        self.assertNotIn("pull_request.head", dogfood)


if __name__ == "__main__":
    unittest.main()
