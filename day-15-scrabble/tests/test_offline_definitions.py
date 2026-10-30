"""Offline coverage, source attribution and reproducible filtering tests."""

import gzip
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from definitions import lookup, DATABASE
from tools.build_definitions import build


class OfflineDefinitionTests(unittest.TestCase):
    """All temporary fixtures stay under the project workspace."""

    def test_all_playable_words_have_rows_and_honest_coverage(self):
        with sqlite3.connect(DATABASE) as db:
            rows = dict(
                db.execute("SELECT match, count(*) FROM definitions GROUP BY match")
            )
            total = db.execute("SELECT count(*) FROM definitions").fetchone()[0]
        self.assertEqual(270652, total)
        self.assertEqual({"exact": 248719, "source-form": 808, "missing": 21125}, rows)

    def test_click_lookup_is_entirely_offline(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network")):
            self.assertTrue(lookup("cat")["entries"])
            self.assertEqual("missing", lookup("ABATTU")["match"])
        entry = lookup("CAT")["entries"][0]
        self.assertEqual("CC BY-SA 4.0", entry["license"]["name"])
        self.assertTrue(
            entry["sources"][0].startswith("https://en.wiktionary.org/wiki/")
        )

    def test_documented_inflection_can_include_lemma_meaning(self):
        entries = lookup("CATS")["entries"]
        self.assertTrue(any("plural" in item["text"] for item in entries))
        self.assertTrue(
            any(item["text"].startswith("Meaning of cat:") for item in entries)
        )

    def test_missing_asset_is_not_created(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="tmp_rovo_", dir=root) as directory:
            missing = Path(directory) / "absent.sqlite3"
            self.assertEqual("unavailable", lookup("CAT", missing)["match"])
            self.assertFalse(missing.exists())

    def test_builder_uses_only_sourced_forms_not_guessed_suffixes(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="tmp_rovo_", dir=root) as directory:
            directory = Path(directory)
            words = directory / "words.txt"
            words.write_text("cat\ncats\ncatted\nzz\n")
            archive = directory / "source.gz"
            record = {
                "word": "cat",
                "lang_code": "en",
                "pos": "noun",
                "forms": [{"form": "cats", "tags": ["plural"]}],
                "senses": [{"glosses": ["A feline."]}],
            }
            with gzip.open(archive, "wt") as stream:
                stream.write(json.dumps(record) + "\n")
            output = directory / "out.sqlite3"
            metadata = build(archive, words, output)
            self.assertEqual(
                {"exact": 1, "source-form": 1, "missing": 2}, metadata["coverage"]
            )
            self.assertEqual("source-form", lookup("CATS", output)["match"])
            self.assertEqual("missing", lookup("CATTED", output)["match"])


if __name__ == "__main__":
    unittest.main()
