# References and provenance

## Rules and edition

- Hasbro, [instruction catalogue](https://instructions.hasbro.com/).
  Select your region and search for the British London edition product code
  when comparing rules. The `/en-gb` URL redirected to `/en-au` in this
  environment on 27 October 2026, so it is not labelled a verified UK manual.
  Hasbro publishes multiple editions at different URLs; verify your edition's rules
  instructions match the physical box. This project's exact configuration and
  differences are recorded in [RULES.md](RULES.md).
- Hasbro US PDF (supplemental): [classic US rulebook](https://www.hasbro.com/common/instruct/00009.pdf).
  Referenced for universal mechanics only; London and US editions differ in property
  names, taxes and station names.

The program implements classic British London property names, rent values and
station references as educational information. Card descriptions are short
functional summaries in original wording, not card scans. No commercial artwork,
logo, mascot, token designs, board textures or sound recordings are copied or
bundled. Rules descriptions in this folder are our own educational explanations,
not reproduced manual text.

## Python and Pygame

- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html):
  automatic constructors, mutable versus frozen records.
- [Python deque](https://docs.python.org/3/library/collections.html#collections.deque):
  pending-effect queues and why removing from the front is efficient.
- [Python random.Random](https://docs.python.org/3/library/random.html):
  isolated reproducible game randomness, not cryptographic randomness.
- [Python unittest](https://docs.python.org/3/library/unittest.html):
  fixtures, assertions, regression tests and standard-library discovery.
- [Pygame documentation](https://www.pygame.org/docs/): drawing, rectangles,
  fonts, events, display scaling and frame timing.
- [Pygame LGPL notice](https://www.pygame.org/LGPL): separate dependency licence.

## Rights boundary

Monopoly is a Hasbro trademark. Real London place names are used to identify
the British board; no exclusive ownership of ordinary place names is asserted. This independent educational project is not
licensed, endorsed or affiliated with Hasbro. The root MIT licence applies to
our original implementation and prose only; it is not a grant of rights to
Hasbro's trademarks, game presentation, reference PDFs or other protected
material. Original geometric art avoids copying commercial assets but does not
constitute a legal clearance opinion. Educational purpose is not claimed as a
universal exemption. Consider rights independently before commercial release.

Pygame is installed separately, not vendored or packaged as an executable.
Pygame's LGPL and its bundled default font/native library terms remain applicable;
see the repository's [third-party notices](../THIRD_PARTY_NOTICES.md).
