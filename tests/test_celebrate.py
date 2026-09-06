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
        for group in (
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
        ):
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
            "comic-burst",
            "comic-pop",
            "sunny-sun",
            "sunny-rainbow",
            "game-levelup",
            "game-combo",
            "sticker-star",
            "sticker-thumb",
            "yeah-pump",
            "yeah-jump",
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
        self.assertEqual(celebrate.pick_from_title("chore: comic kapow"), "comic")
        self.assertEqual(celebrate.pick_from_title("chore: sunny day"), "sunny")
        self.assertEqual(celebrate.pick_from_title("chore: level-up combo"), "game")
        self.assertEqual(celebrate.pick_from_title("chore: sticker pack"), "sticker")
        self.assertEqual(celebrate.pick_from_title("chore: yeah let's go"), "yeah")

    def test_mood_keywords_do_not_steal_conventional_types(self) -> None:
        celebrate = _load()
        self.assertEqual(celebrate.pick_from_title("feat: add party mode"), "ship")
        self.assertEqual(celebrate.pick_from_title("fix: magic number"), "fix")
        self.assertEqual(celebrate.pick_from_title("docs: coffee guide"), "docs")
        self.assertEqual(celebrate.pick_from_title("namespace cleanup"), "cleanup")
        self.assertEqual(celebrate.pick_from_title("feat: add comic mode"), "ship")
        self.assertEqual(celebrate.pick_from_title("fix: combo overflow"), "fix")
        self.assertEqual(celebrate.pick_from_title("docs: sticker pack"), "docs")
        self.assertEqual(celebrate.pick_from_title("test: sunny path"), "tests")
        self.assertEqual(celebrate.pick_from_title("refactor: yeah helper"), "cleanup")
        self.assertEqual(celebrate.pick_from_title("chore: power"), "celebration")
        self.assertEqual(celebrate.pick_from_title("chore: game night"), "celebration")

    def test_first_timer_generic_title_is_welcome(self) -> None:
        celebrate = _load()
        self.assertEqual(
            celebrate.pick_from_title("chore: bump", "FIRST_TIME_CONTRIBUTOR"),
            "welcome",
        )
        self.assertEqual(celebrate.pick_from_title("fix: leak", "FIRST_TIMER"), "fix")

    def test_auto_topic_picks_a_shipped_group(self) -> None:
        celebrate = _load()
        for topic in ("auto", ""):
            group = celebrate.resolve_group("feat: add login", topic, seed="12")
            self.assertIn(group, celebrate.GROUPS)

    def test_auto_topic_ignores_title_keywords(self) -> None:
        celebrate = _load()
        from_feat = celebrate.resolve_group("feat: add login", "auto", seed="12")
        from_fix = celebrate.resolve_group("fix: leak", "auto", seed="12")
        from_chore = celebrate.resolve_group("chore: bump", "auto", seed="12")
        self.assertEqual(from_feat, from_fix)
        self.assertEqual(from_fix, from_chore)
        self.assertIn(from_feat, celebrate.GROUPS)

    def test_auto_topic_can_vary_by_pr_number(self) -> None:
        celebrate = _load()
        groups = {
            celebrate.resolve_group("chore: bump", "auto", seed=str(number))
            for number in range(1, 80)
        }
        self.assertGreater(len(groups), 1)
        self.assertTrue(groups <= set(celebrate.GROUPS))

    def test_title_topic_uses_the_title(self) -> None:
        celebrate = _load()
        self.assertEqual(celebrate.resolve_group("feat: add login", "title"), "ship")
        self.assertEqual(celebrate.resolve_group("fix: leak", "title"), "fix")

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
        self.assertEqual(celebrate.resolve_group("chore: bump", "comic"), "comic")
        self.assertEqual(celebrate.resolve_group("chore: bump", "kapow"), "comic")
        self.assertEqual(celebrate.resolve_group("chore: bump", "sunny"), "sunny")
        self.assertEqual(celebrate.resolve_group("chore: bump", "level-up"), "game")
        self.assertEqual(celebrate.resolve_group("chore: bump", "sticker"), "sticker")
        self.assertEqual(celebrate.resolve_group("chore: bump", "yeah"), "yeah")
        self.assertEqual(celebrate.resolve_group("chore: bump", "lets-go"), "yeah")

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

    def test_bundled_url_falls_back_when_action_repo_is_empty(self) -> None:
        celebrate = _load()
        url = celebrate.bundled_url("", "v1.3.0", "ship", "ship-it.gif")
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/YauhenBichel/merge-cheer/v1.3.0/gifs/ship/ship-it.gif",
        )
        blank = celebrate.bundled_url("   ", "main", "comic", "burst.gif")
        self.assertEqual(
            blank,
            "https://raw.githubusercontent.com/YauhenBichel/merge-cheer/main/gifs/comic/burst.gif",
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
        self.assertIn("random theme", text)
        self.assertIn("title picks from the PR title", text)
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
        self.assertIn("gifs/comic/burst.gif", text)
        self.assertIn("gifs/sunny/sun.gif", text)
        self.assertIn("gifs/game/levelup.gif", text)
        self.assertIn("gifs/sticker/star.gif", text)
        self.assertIn("gifs/yeah/pump.gif", text)
        self.assertIn(".github/workflows/celebrate.yml", text)
        dogfood = (ROOT / ".github" / "workflows" / "celebrate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("uses: ./", dogfood)
        self.assertIn("github.event.repository.default_branch", dogfood)
        self.assertNotIn("pull_request.head", dogfood)

    def test_pages_site_is_public_and_searchable(self) -> None:
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        pages = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("<title>Merge Cheer", html)
        self.assertIn("GIF on merge", html)
        self.assertIn("random theme", html)
        self.assertIn("random theme", readme)
        self.assertIn("topic: title", readme)
        self.assertIn("YauhenBichel/merge-cheer@v1.1.0", html)
        self.assertIn("gifs/ship/ship-it.gif", html)
        self.assertIn("MoleCare/molecare-mcp", html)
        self.assertNotIn("/Users/", html)
        self.assertNotIn("DevBox/", html)
        self.assertNotIn("marketplace/actions", html)
        self.assertIn("https://yauhenbichel.github.io/merge-cheer/", readme)
        self.assertIn("actions/deploy-pages", pages)
        self.assertIn("cp -R gifs _site/gifs", pages)

    def test_release_workflow_is_reviewed_not_automatic(self) -> None:
        text = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("environment: marketplace", text)
        self.assertIn("needs: test", text)
        self.assertIn("contents: write", text)
        self.assertIn("python3 -m unittest discover -s tests -q", text)
        self.assertIn("gh release create", text)
        self.assertIn("ref: ${{ inputs.version }}", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("pull_request.head", text)
        self.assertNotIn("git tag -f", text)
        self.assertNotIn("--force", text)
        on_block = text.split("permissions:", 1)[0]
        self.assertNotIn("\n  push:", on_block)
        self.assertNotIn("tags:", on_block)
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("uses:"):
                continue
            pin = stripped.split("@", 1)[-1].split()[0]
            self.assertRegex(pin, r"^[0-9a-f]{40}$", stripped)
        notes = (ROOT / "RELEASE.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("environment: marketplace", notes)
        self.assertIn("Required reviewers", notes)
        self.assertIn("releases/edit/", notes)
        self.assertIn("RELEASE.md", readme)
        self.assertNotIn("/Users/", notes)
        self.assertNotIn("DevBox/", notes)
        self.assertNotIn("marketplace/actions", notes)

    def test_contributors_push_does_not_add_missing_readme_names(self) -> None:
        """Ubuntu git is case-sensitive; `git add README` exits 128."""
        text = (ROOT / ".github" / "workflows" / "contributors.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("git add README.md .github/contributors.svg", text)
        forbidden = {"README", "readme.md"}
        added: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("git add "):
                continue
            added.extend(stripped.split()[2:])
        self.assertIn("README.md", added)
        self.assertIn(".github/contributors.svg", added)
        self.assertEqual([name for name in added if name in forbidden], [])
        self.assertIn("pull-requests: write", text)
        self.assertIn("docs/contributors", text)
        self.assertIn("gh pr create", text)
        self.assertIn(
            "GitHub Actions is not permitted to create or approve pull requests",
            text,
        )
        self.assertIn(
            "https://github.com/YauhenBichel/merge-cheer/compare/main...docs/contributors",
            text,
        )
        self.assertIn("exit 0", text)
        self.assertIn("exit 1", text)
        self.assertNotIn("git push\n", text)


if __name__ == "__main__":
    unittest.main()
