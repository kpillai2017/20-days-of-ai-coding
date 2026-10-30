# Offline definitions: attribution, licence, changes and coverage

This dataset is **not CC0**. It is separate from `words.txt` and the MIT Python
code. The adapted definition database is distributed under **CC BY-SA 4.0**.
Preserve this attribution and licence when redistributing/adapting the data.

## Source and attribution

- Original text: **English Wiktionary contributors**, https://en.wiktionary.org/.
  Each displayed sense retains its originating Wiktionary page URL. Page history
  and contributors are accessible from that page; source links are attribution,
  not runtime requests or a claim to have authored the dictionary text.
- Machine-readable extraction: **Tatu Ylönen / Wiktextract and Kaikki.org**,
  https://kaikki.org/dictionary/English/index.html.
- Kaikki licensing statement: https://kaikki.org/dictionary/index.html, under
  “Copyright and license”, states the data has Wiktionary's CC-BY-SA/GFDL terms.
- Wikimedia text licensing: https://en.wiktionary.org/wiki/Wiktionary:Copyrights.
  We distribute this adaptation under the CC BY-SA 4.0 option; no claim that the
  definitions are relicensed MIT or CC0 is made.
- Licence: https://creativecommons.org/licenses/by-sa/4.0/; full legal code is
  preserved in `CC-BY-SA-4.0.html`, retrieved from the official
  `https://creativecommons.org/licenses/by-sa/4.0/legalcode.en` endpoint.
- No endorsement by Wiktionary, Wikimedia, Kaikki, Hasbro or Mattel is claimed.

## Download and reproducibility

- Downloaded 30 October 2026.
- Source: https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz
- HTTP Last-Modified: 25 October 2026; archive size: 534,137,553 bytes.
- Archive SHA-256: `3ff7bef28ce7ad077ea55cedd9bde2cb7981c40f68adf63c8ceea347341392dc`.
- Gameplay word-list SHA-256: `b78af5ad2f66bed4e64fd48334af7d5620a91c45e7a578c084b9b72f9abcd5dd`.
- This upstream URL changes with future extracts. Check the checksum to reproduce
  this exact snapshot; the build tool records the actual source checksum.
- The large source archive is not bundled. `definitions.sqlite3` is the local
  filtered database. Rebuild from a legally obtained archive with:

```sh
python tools/build_definitions.py /path/to/english.jsonl.gz
```

The rebuild tool does not download anything automatically. No network connection
is needed during gameplay or when clicking a word.

## Changes made to the source

Filtered to English entries and the 270,652 playable uppercase word keys; retained
at most three initial senses per word, parts of speech, sense tags and source
URLs. Gloss arrays are joined into short text, truncated at 2,400 characters.
Capitalisation variants are merged under uppercase gameplay keys; this can mix
common words with abbreviations/proper-name senses. These are learning aids, not
context-sensitive authoritative definitions or a Scrabble validity authority.

If no exact headword sense is available, a form may be linked **only when the
source explicitly records it** as a plural, tense, participle or comparison.
No suffix-stripping guesses or AI-generated meanings are used. Source `form_of`
links are preserved, and the UI can show one level of a base word's meaning when
that base is also present in this filtered dictionary. Cycles are bounded.
Definition payloads are JSON compressed per row using zlib, indexed in SQLite.

## Measured coverage

| Category | Words |
|---|---:|
| Exact uppercase-matched source headword with a gloss | 248,719 |
| Source-recorded form linked to a sourced gloss | 808 |
| No sourced meaning in this filtered extract | 21,125 |
| **Total indexed gameplay words** | **270,652** |
| **Words with sourced glosses/form references** | **249,527 (92.2%)** |

Every gameplay word has a row; this is **not** 100% meaning coverage. Some exact
entries are merely “plural of …”, “alternative form of …” or similar references,
not standalone semantic definitions. Missing rows return an explicit message,
never a fabricated meaning. Different custom word lists can include absent words.

Source text may contain errors, archaic usage, offensive language and unsuitable
content. Not every sense is selected or disambiguated for the word as played.
The dictionary remains unfiltered; no child-safe or exhaustive coverage claim.
