# 20 Days of AI Coding

**One small project a day. Learn by building, reading and experimenting.**

A beginner-friendly series of AI-assisted coding projects: games, utilities and small experiments written in **Python** (with pygame where relevant) or **HTML + CSS + JavaScript**. AI helps with the coding; projects do not necessarily use AI themselves.

Each day should include runnable code, explanatory comments, installation and usage instructions, a walkthrough of how it works, tests where practical, and references for further learning.

## Project index

| Day | Project | Stack | Learn |
| --- | --- | --- | --- |
| 01 | [Pixel Life](day-01-pixel-life/) | HTML / CSS / JavaScript | Conway’s Game of Life, arrays, canvas, events and simulation loops |
| 02 | [Breakout](day-02-breakout/) | Python / pygame | Game loops, delta time, collision detection and game state |

**Days 03–20:** not built yet. Each will be a separate small project in this repository.

## Run Day 02

See [the Breakout guide](day-02-breakout/README.md) for Windows and macOS/Linux setup. With Python 3.9–3.13, from the repository root on macOS/Linux:

```sh
cd day-02-breakout
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Move with arrows or A/D; Space launches; P pauses; R restarts. Run all Day 02 tests from that folder with `python -m unittest discover -s tests -v`.

## Run Day 01

Download and extract the repository, then open **`day-01-pixel-life/index.html`** in your browser. No installation, API key, build step or library is required.

Alternatively, from the repository folder:

```sh
cd day-01-pixel-life
python3 -m http.server 8000 --bind 127.0.0.1
```

Visit **http://localhost:8000**. On Windows use `py` instead of `python3`. Stop the server with Ctrl+C.

Read [the Day 01 guide](day-01-pixel-life/README.md) for controls, a code tour, troubleshooting, exercises and references.

## Test Day 01

With Node.js 20+ installed, from the repository root:

```sh
node --test day-01-pixel-life/tests/life.test.cjs
```

Node is only needed for the tests. GitHub Actions also runs them automatically on pushes and pull requests.

## Repository hygiene and development

The root [`.gitignore`](.gitignore) applies to **both projects and all future day folders**. It excludes Python environments/bytecode, Node dependencies, build output, test reports, coverage, editor metadata, logs and local `.direnv/`, `.envrc` and `.env*` configuration. Local files remain on your machine; ignoring them does not delete them.

- Keep real credentials out of source and configuration committed to Git.
- Sanitised `.env.example` files are allowed; never put secrets in an example.
- JavaScript lockfiles are deliberately **not ignored**. If a future day adds dependencies, commit its lockfile for reproducible installs. Day 01 has none.
- Check `git status --short` before staging. For an ignored path, use `git check-ignore -v path/to/file` to see which rule applies.
- `.gitignore` does not untrack an already committed file. Review `git ls-files -ci --exclude-standard` for tracked files that now match ignore rules.

Both projects separate their rules from their interface: `life.js` from `app.js`, and `game.py` from `main.py`. Refactors should preserve that separation, update each day's walkthrough, and add regression tests for changed behavior.

### Run all checks

From the repository root, after installing Day 02's requirements in its virtual environment:

```sh
node --check day-01-pixel-life/app.js
node --check day-01-pixel-life/life.js
node --test day-01-pixel-life/tests/life.test.cjs
cd day-02-breakout
.venv/bin/python -m unittest discover -s tests -v
```

On Windows, use `.venv\\Scripts\\python.exe` for the final command. CI runs these test suites and a headless pygame smoke test on every push and pull request.

## A learning rhythm

1. Run the project before studying it.
2. Read its README and follow one input through the code.
3. Predict what a small change will do, then try it.
4. Run the tests and add a test for a new behaviour.
5. Write down what you learned before starting the next day.

No software licence has been selected yet; this repository does not currently grant an open-source licence.
