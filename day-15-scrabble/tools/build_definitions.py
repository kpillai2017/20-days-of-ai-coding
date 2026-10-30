#!/usr/bin/env python3
"""Filter a licensed Kaikki/Wiktionary English JSONL dump into a local index.

No morphological guesses or generated meanings: exact senses take priority;
otherwise only forms explicitly recorded in the source point to lemma senses.
The source archive is supplied by the caller, so rebuilding never silently
initiates a half-gigabyte download. Use --help for the reproducible command.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import zlib
from urllib.parse import quote

SOURCE = "https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz"
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"


def build(archive, words_path, output):
    """Write one row for every gameplay word, including honest missing rows."""
    words = {
        w.strip().upper()
        for w in words_path.read_text().splitlines()
        if w.strip().isascii() and w.strip().isalpha() and 2 <= len(w.strip()) <= 15
    }
    exact, forms = {}, {}
    processed = 0
    with gzip.open(archive, "rt", encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("lang_code") != "en":
                continue
            head = record.get("word", "")
            normalized = head.upper()
            form_targets = [
                f
                for f in record.get("forms", [])
                if isinstance(f.get("form"), str)
                and f["form"].upper() in words
                and any(
                    tag in f.get("tags", [])
                    for tag in (
                        "plural",
                        "past",
                        "present",
                        "participle",
                        "comparative",
                        "superlative",
                    )
                )
            ]
            if normalized not in words and not form_targets:
                continue
            entries = []
            for sense in record.get("senses", []):
                glosses = sense.get("glosses", [])
                if not glosses or "no-gloss" in sense.get("tags", []):
                    continue
                text = "; ".join(g for g in glosses if isinstance(g, str))
                if not text:
                    continue
                tags = sense.get("tags", [])
                entries.append(
                    {
                        "part": record.get("pos", ""),
                        "text": text[:2400],
                        "tags": tags[:12],
                        "form_of": [
                            item.get("word", "")
                            for item in sense.get("form_of", [])
                            if item.get("word")
                        ],
                        "sources": [
                            "https://en.wiktionary.org/wiki/" + quote(head, safe="")
                        ],
                        "license": {"name": "CC BY-SA 4.0", "url": LICENSE},
                    }
                )
                if len(entries) == 3:
                    break
            if entries and normalized in words:
                exact.setdefault(normalized, []).extend(
                    entries[: max(0, 3 - len(exact.get(normalized, [])))]
                )
            for form in form_targets:
                target = form["form"].upper()
                if target == normalized or not entries or target in forms:
                    continue
                label = ", ".join(form.get("tags", []))
                forms[target] = [
                    {
                        "part": item["part"],
                        "text": f"Source-recorded {label} form of {head}: "
                        + item["text"],
                        "tags": item["tags"],
                        "sources": item["sources"],
                        "license": item["license"],
                        "lemma": head,
                        "match": "source-form",
                    }
                    for item in entries
                ]
            processed += 1
            if processed % 25000 == 0:
                print(
                    f"Processed {processed:,} relevant entries; {len(exact):,} exact headwords",
                    flush=True,
                )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    connection = sqlite3.connect(output)
    connection.execute(
        "CREATE TABLE definitions (word TEXT PRIMARY KEY, match TEXT NOT NULL, payload BLOB NOT NULL) WITHOUT ROWID"
    )
    counts = {"exact": 0, "source-form": 0, "missing": 0}
    for word in sorted(words):
        entries = exact.get(word) or forms.get(word) or []
        kind = "exact" if exact.get(word) else "source-form" if entries else "missing"
        counts[kind] += 1
        result = {
            "status": "Offline Wiktionary definitions"
            if entries
            else "No local definition available.",
            "match": kind,
            "entries": entries,
        }
        payload = zlib.compress(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode(), 9
        )
        connection.execute(
            "INSERT INTO definitions VALUES (?, ?, ?)", (word, kind, payload)
        )
    metadata = {
        "schema": 1,
        "source_url": SOURCE,
        "source_sha256": sha256(archive),
        "wordlist_sha256": sha256(words_path),
        "total": len(words),
        "coverage": counts,
        "license": "CC BY-SA 4.0",
        "source_last_modified": "2026-10-25",
        "transform": "English entries, uppercase match, at most 3 senses; source-recorded inflections only; no inferred meanings.",
    }
    connection.execute(
        "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    for key, value in metadata.items():
        connection.execute(
            "INSERT INTO metadata VALUES (?, ?)", (key, json.dumps(value))
        )
    connection.commit()
    connection.close()
    print(json.dumps(metadata, indent=2))
    return metadata


def sha256(path):
    """Hash in chunks without loading the large archive into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    """Rebuild from a downloaded source, keeping runtime entirely offline."""
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "archive", type=Path, help="Downloaded English JSONL.gz extract"
    )
    parser.add_argument("--words", type=Path, default=root / "words" / "words.txt")
    parser.add_argument(
        "--output", type=Path, default=root / "words" / "definitions.sqlite3"
    )
    args = parser.parse_args()
    build(args.archive, args.words, args.output)


if __name__ == "__main__":
    main()
