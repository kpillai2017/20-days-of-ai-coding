"""Offline word meanings, independent of the CC0 gameplay lexicon.

The separately licensed Wiktionary extract is read-only SQLite. Every bundled
playable word has a row, but some rows explicitly have no sourced definition.
There is no runtime network access, guessed morphology or invented meaning.
"""

import json
from contextlib import closing
from pathlib import Path
import sqlite3
import zlib

DATABASE = Path(__file__).parent / "words" / "definitions.sqlite3"


def lookup(word, database=None, _include_lemmas=True):
    """Read one bounded local payload; a missing/custom word fails honestly."""
    if (
        not isinstance(word, str)
        or not 2 <= len(word) <= 15
        or not word.isascii()
        or not word.isalpha()
    ):
        raise ValueError("Look up an ASCII word of length 2–15.")
    path = Path(database) if database is not None else DATABASE
    missing = {
        "status": "No local definition available.",
        "match": "missing",
        "entries": [],
    }
    try:
        # A fresh short-lived read-only connection is thread-safe and does not
        # accidentally create an empty database when the asset is missing.
        with closing(
            sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        ) as connection:
            row = connection.execute(
                "SELECT payload FROM definitions WHERE word = ?", (word.upper(),)
            ).fetchone()
        if row is None:
            return missing
        result = json.loads(zlib.decompress(row[0]))
        if not isinstance(result, dict) or not isinstance(result.get("entries"), list):
            return missing
        # Include a lemma's meaning when the source explicitly says this is a
        # form of it. Do not guess suffixes (e.g. blindly stripping every S).
        related = []
        seen = {word.upper()}
        for entry in result["entries"] if _include_lemmas else []:
            for lemma in entry.get("form_of", []):
                key = lemma.upper()
                if key in seen:
                    continue
                seen.add(key)
                base = (
                    lookup(lemma, path, False)
                    if 2 <= len(lemma) <= 15 and lemma.isascii() and lemma.isalpha()
                    else missing
                )
                for sense in base["entries"][:1]:
                    related.append(
                        dict(sense, text=f"Meaning of {lemma}: " + sense["text"])
                    )
        result["entries"].extend(related[:3])
        return result
    except (OSError, sqlite3.Error, ValueError, zlib.error):
        return {
            "status": "Local definition file unavailable or damaged.",
            "match": "unavailable",
            "entries": [],
        }
