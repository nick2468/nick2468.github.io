"""Tests for site/build.py. Run with: python -m unittest discover -s site"""

import tempfile
import unittest
from pathlib import Path

import build

HOME = """---
title: Apps I have built
name: Test Person
url: https://example.github.io/
tagline: A test tagline.
github: https://github.com/example
---
An intro with [a link](https://example.com).
"""

APP = """---
title: Test App
summary: A test app.
platforms: Windows, Web browser
play: https://example.com/play
source: https://github.com/example/app
media:
  - file: 01-shot.png
    alt: A screenshot.
  - file: 02-clip.mp4
    alt: A short clip.
    poster: 02-poster.png
---
The first paragraph.

The second paragraph.
"""


class Repo:
    """A throwaway repository: home.md plus apps written by the test."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "site" / "dist"
        (self.root / "home.md").write_text(HOME, encoding="utf-8")

    def app(self, folder, text=APP, files=("01-shot.png", "02-clip.mp4", "02-poster.png")):
        path = self.root / "apps" / folder
        path.mkdir(parents=True)
        (path / "app.md").write_text(text, encoding="utf-8")
        for name in files:
            (path / name).write_bytes(b"x")
        return path

    def build(self):
        return build.build(self.root, self.out)

    def close(self):
        self.tmp.cleanup()


class ParseTest(unittest.TestCase):
    def test_reads_fields_media_and_body(self):
        meta, body = build.parse_front_matter(APP, "app.md")
        self.assertEqual(meta["title"], "Test App")
        self.assertEqual(meta["play"], "https://example.com/play")
        self.assertEqual(len(meta["media"]), 2)
        self.assertEqual(meta["media"][1]["poster"], "02-poster.png")
        self.assertTrue(body.startswith("The first paragraph."))

    def test_needs_a_closing_line(self):
        with self.assertRaisesRegex(build.BuildError, "no closing"):
            build.parse_front_matter("---\ntitle: x\n", "app.md")

    def test_needs_title_and_summary(self):
        meta, _ = build.parse_front_matter("---\ntitle: x\n---\n", "app.md")
        with self.assertRaisesRegex(build.BuildError, "missing 'summary'"):
            build.check_app(meta, "app.md")

    def test_links_must_be_https(self):
        meta, _ = build.parse_front_matter(APP.replace("https://example.com/play",
                                                       "http://example.com/play"), "app.md")
        with self.assertRaisesRegex(build.BuildError, "'play' must be an https"):
            build.check_app(meta, "app.md")

    def test_media_needs_alt_text(self):
        meta, _ = build.parse_front_matter(APP.replace("    alt: A screenshot.\n", ""), "app.md")
        with self.assertRaisesRegex(build.BuildError, "no 'alt'"):
            build.check_app(meta, "app.md")

    def test_media_must_be_a_known_type(self):
        meta, _ = build.parse_front_matter(APP.replace("01-shot.png", "01-shot.gif"), "app.md")
        with self.assertRaisesRegex(build.BuildError, "not PNG, JPG or MP4"):
            build.check_app(meta, "app.md")

    def test_media_must_sit_in_the_folder(self):
        meta, _ = build.parse_front_matter(APP.replace("01-shot.png", "../01-shot.png"), "app.md")
        with self.assertRaisesRegex(build.BuildError, "own folder"):
            build.check_app(meta, "app.md")

    def test_links_in_text_allow_only_web_addresses(self):
        self.assertIn('<a href="https://a.b">x</a>', build.inline_markdown("[x](https://a.b)"))
        self.assertNotIn("<a", build.inline_markdown("[x](javascript:alert(1))"))
        self.assertIn("&lt;b&gt;", build.inline_markdown("<b>"))


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.close()

    def test_writes_home_app_page_and_media(self):
        self.repo.app("001-test-app")
        summary = self.repo.build()
        self.assertEqual(summary, {"apps": 1, "media": 2})
        out = self.repo.out
        home = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="test-app/index.html">Test App</a>', home)
        self.assertIn('<a href="https://example.com">a link</a>', home)
        self.assertIn('content="https://example.github.io/test-app/01-shot.png"', home)
        page = (out / "test-app" / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="button main" href="https://example.com/play">Play it', page)
        self.assertIn('class="button" href="https://github.com/example/app">See the source code', page)
        self.assertIn("Runs on Windows, Web browser", page)
        self.assertIn('poster="02-poster.png"', page)
        self.assertIn('<link rel="canonical" href="https://example.github.io/test-app/">', page)
        for name in ("01-shot.png", "02-clip.mp4", "02-poster.png"):
            self.assertTrue((out / "test-app" / name).is_file(), name)
        self.assertTrue((out / "404.html").is_file())
        self.assertTrue((out / ".nojekyll").is_file())

    def test_folder_number_orders_the_cards(self):
        self.repo.app("002-second", APP.replace("Test App", "Second"))
        self.repo.app("001-first", APP.replace("Test App", "First"))
        self.repo.build()
        home = (self.repo.out / "index.html").read_text(encoding="utf-8")
        self.assertLess(home.index(">First<"), home.index(">Second<"))

    def test_an_app_with_no_pictures_gets_a_letter_cover(self):
        text = APP.split("media:")[0] + "---\nText.\n"
        self.repo.app("001-plain", text, files=())
        self.repo.build()
        home = (self.repo.out / "index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="cover-text" aria-hidden="true">T</div>', home)

    def test_source_alone_is_never_the_main_button(self):
        text = APP.replace("play: https://example.com/play\n", "")
        self.repo.app("001-code-only", text)
        self.repo.build()
        page = (self.repo.out / "code-only" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("button main", page)

    def test_missing_media_file_fails(self):
        self.repo.app("001-test-app", files=("01-shot.png",))
        with self.assertRaisesRegex(build.BuildError, "'02-clip.mp4' is not in the folder"):
            self.repo.build()

    def test_bad_folder_name_fails(self):
        self.repo.app("Test App")
        with self.assertRaisesRegex(build.BuildError, "<number>-<name>"):
            self.repo.build()

    def test_two_apps_cannot_share_an_address(self):
        self.repo.app("001-same")
        self.repo.app("002-same")
        with self.assertRaisesRegex(build.BuildError, "cannot share one address"):
            self.repo.build()

    def test_home_needs_its_url(self):
        (self.repo.root / "home.md").write_text(HOME.replace("url: https://example.github.io/\n", ""),
                                                encoding="utf-8")
        with self.assertRaisesRegex(build.BuildError, "missing 'url'"):
            self.repo.build()

    def test_refuses_to_clear_a_folder_it_did_not_make(self):
        self.repo.out.mkdir(parents=True)
        (self.repo.out / "precious.txt").write_text("keep me", encoding="utf-8")
        with self.assertRaisesRegex(build.BuildError, "refusing to clear"):
            self.repo.build()
        self.assertTrue((self.repo.out / "precious.txt").is_file())

    def test_rebuild_removes_an_app_that_was_deleted(self):
        path = self.repo.app("001-test-app")
        self.repo.build()
        for child in path.iterdir():
            child.unlink()
        path.rmdir()
        self.repo.build()
        self.assertFalse((self.repo.out / "test-app").exists())


if __name__ == "__main__":
    unittest.main()
