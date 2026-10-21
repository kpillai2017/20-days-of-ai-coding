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

## A learning rhythm

1. Run the project before studying it.
2. Read its README and follow one input through the code.
3. Predict what a small change will do, then try it.
4. Run the tests and add a test for a new behaviour.
5. Write down what you learned before starting the next day.

No software licence has been selected yet; this repository does not currently grant an open-source licence.
