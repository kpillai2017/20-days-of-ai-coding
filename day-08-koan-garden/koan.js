/* Koan Garden's MODEL: ordinary JavaScript with no browser dependencies.
 * This is a small writing machine, not a language model or a Zen teacher.
 * Keeping the rules separate from the interface makes them easy to test. */
(() => {
  "use strict";

  const MAX_LENGTH = 600; // JavaScript strings and HTML maxlength use UTF-16 units.
  // Eight endings per scene; this is a finite writing system, not an LLM.
  const ENDINGS = [
    "What changed when nobody demanded an answer?",
    "Where did the question end and the looking begin?",
    "Which was harder to carry: the thing, or its name?",
    "What would remain if the explanation fell silent?",
    "Who had moved: the world, or the one watching?",
    "Could the next step be taken without owning the whole path?",
    "What had been present before anyone tried to grasp it?",
    "If nothing needed proving, what could be noticed now?"
  ];

  // These are original writing ingredients, not quotations from Zen literature.
  // A theme has concrete words to match, an image, a tension to explore, and
  // questions. Do not mistake a keyword score for understanding someone's mind.
  const THEMES = [
    { id: "control", name: "Control and letting go",
      words: ["control", "controlling", "plan", "plans", "outcome", "outcomes", "certain", "certainty"],
      object: "a handful of river water", place: "beside a river", action: "closed their fingers", response: "The tighter the hand became, the less water it held.",
      tension: "the difference between taking useful action and demanding a guaranteed outcome",
      question: "What is within your influence, and what are you asking to obey you?",
      practice: "Name one action you can take and one outcome you cannot guarantee. Let them be two different things." },
    { id: "change", name: "Change and impermanence",
      words: ["change", "changes", "changing", "changed", "loss", "lost", "leave", "leaving", "ending", "ends", "begin", "beginning"],
      object: "a fallen leaf", place: "under a tree", action: "asked the branch to take it back", response: "A new bud moved in the same wind.",
      tension: "the wish to keep something still in a world that moves",
      question: "What are you trying to preserve, and what is already taking a new shape?",
      practice: "Notice one small thing that has changed today. Describe it without deciding whether it is good or bad." },
    { id: "perfection", name: "Perfection and mistakes",
      words: ["perfect", "perfection", "mistake", "mistakes", "fail", "failed", "failure", "wrong", "enough", "flawless"],
      object: "an uneven clay bowl", place: "at a potter’s table", action: "turned the bowl to hide its uneven edge", response: "From every side, it still held the tea.",
      tension: "the difference between caring about a craft and requiring yourself to be flawless",
      question: "What useful thing becomes invisible when you look only for a flaw?",
      practice: "Choose a small, low-stakes task. Define what would be useful rather than perfect before you begin." },
    { id: "time", name: "Time and attention",
      words: ["time", "busy", "hurry", "rushing", "deadline", "deadlines", "late", "future", "past", "procrastinate", "procrastination"],
      object: "an unlit candle", place: "by an open window", action: "waited for tomorrow’s light", response: "The afternoon shadow crossed the candle anyway.",
      tension: "the pull of another moment while this one is passing",
      question: "Which part of your question belongs to now, and which part lives in an imagined moment?",
      practice: "For a few comfortable breaths, attend to a sound nearby. Then choose one small next step, not a whole future." },
    { id: "identity", name: "Identity and labels",
      words: ["identity", "myself", "self", "worth", "success", "successful", "achievement", "achievements", "purpose", "meaning"],
      object: "a name written in sand", place: "on a quiet shore", action: "traced a border around the name", response: "The next wave could not read the border.",
      tension: "the difference between a useful description of yourself and the whole of your experience",
      question: "What remains of your experience when you set one familiar label aside?",
      practice: "Describe something you did today without turning it into a judgement about what kind of person you are." },
    { id: "relationships", name: "Relationships and listening",
      words: ["friend", "friends", "family", "partner", "relationship", "relationships", "love", "lonely", "alone", "argument", "listen", "listening"],
      object: "two empty cups", place: "at a small table", action: "spoke into one cup and listened to the other", response: "Neither cup interrupted; neither had yet heard a person.",
      tension: "the space between preparing an answer and actually hearing another person",
      question: "What might you notice if you did not have to supply the next answer?",
      practice: "Recall a conversation. Separate what was actually said from what you guessed it meant; do not assume you know another person’s thoughts." },
    { id: "uncertainty", name: "Questions and uncertainty",
      words: ["uncertain", "uncertainty", "unsure", "confused", "confusion", "doubt", "doubts", "decide", "decision", "choice", "choices", "afraid", "fear", "worried", "worry"],
      object: "a lantern in the mist", place: "at a fork in a path", action: "lifted the lantern to see the entire road", response: "The light reached the next stone, not the end of the journey.",
      tension: "wanting the whole answer before discovering the next workable step",
      question: "What could you explore without pretending that you already know the outcome?",
      practice: "Write one thing you know, one thing you do not know, and a small reversible way to learn more." },
    { id: "attention", name: "Everyday attention", words: [],
      object: "a smooth stone", place: "beside a garden gate", action: "turned the stone over to find its answer", response: "The other side was also a stone; the hand holding it had become warmer.",
      tension: "the possibility that changing how you attend to a question changes what you notice",
      question: "What detail in your situation have you not yet looked at closely?",
      practice: "Describe a nearby ordinary object in three concrete details. Return to your question and notice whether anything feels different." }
  ];

  /** Validate at the model boundary as well as in HTML. A test or future caller
   * can bypass a form, so maxlength alone would not protect this function. */
  function normalizeInput(value) {
    if (typeof value !== "string") throw new TypeError("Please enter a statement or question.");
    // Measure BEFORE collapsing whitespace, matching the form's maxlength rule.
    if (value.length > MAX_LENGTH) throw new RangeError(`Please use ${MAX_LENGTH} characters or fewer.`);
    // Single-line text keeps a multi-line paste from breaking the story layout.
    const context = value.replace(/\s+/gu, " ").trim();
    if (!context) throw new RangeError("Please enter a statement or question first.");
    return context;
  }

  /** Count distinct whole-word matches, not substrings: 'time' must not match
   * 'sometimes'. Unicode letters/numbers prevent matching inside non-English
   * words too. The vocabulary itself is English; it does not handle negation. */
  function selectTheme(context) {
    const tokens = new Set(context.toLowerCase().match(/[\p{L}\p{N}]+/gu) || []);
    let selected = THEMES[THEMES.length - 1]; // Fallback when no keyword matches.
    let bestScore = 0;
    for (const theme of THEMES) {
      const score = theme.words.filter(word => tokens.has(word)).length;
      // Strict > makes ties predictable: the first listed theme wins.
      if (score > bestScore) { selected = theme; bestScore = score; }
    }
    return { theme: selected, score: bestScore };
  }

  // Each scene keeps its image and interpretation together. Randomly mixing
  // unrelated morals with scenery would add variety at the expense of meaning.
  function scene(title, opening, turn, reading) {
    return { title, opening, turn, reading };
  }

  const EXTRA_SCENES = {
    control: [
      scene("The uncommanded sail", "A sailor ordered the wind to turn toward home.", "The wind continued; the sailor turned the sail.", "Changing the sail suggests working with conditions rather than commanding them. It is not an instruction to accept avoidable harm."),
      scene("The river's knot", "A child tied a knot in a rope to stop the river.", "The knot stayed firm; the river found both sides of it.", "The knot can stand for a plan that is sound in itself but cannot govern everything around it.")
    ],
    change: [
      scene("The emptied nest", "A gardener kept an empty nest safe from the wind.", "Above it, the birds were already building elsewhere.", "Preserving a trace of something is different from keeping its life unchanged. Grief and new beginnings need not cancel one another."),
      scene("The borrowed snow", "A child carried snow indoors to save the morning.", "By noon, the bowl held water reflecting the same sky.", "The snow loses its familiar form without becoming nothing. The image invites attention to transformation, not denial of loss.")
    ],
    perfection: [
      scene("The crooked flute", "A maker put aside a flute because its grain was crooked.", "The apprentice played it; the straight ruler made no music.", "A ruler measures one quality; music reveals another. Consider whether the standard you are using measures what matters here."),
      scene("The unfinished circle", "A painter left a small gap in a circle and reached for more ink.", "Through the gap, a child drew a path into the picture.", "A gap can be an invitation rather than a failure. That possibility does not mean every defect should be ignored.")
    ],
    time: [
      scene("The hurried bell", "A keeper rang tomorrow's bell before today's visitors arrived.", "The sound faded; the doorway remained empty.", "Trying to finish the future cannot make it arrive. The bell invites you to distinguish preparation from missing the present."),
      scene("The waiting kettle", "A cook watched the clock to hurry the kettle.", "A bird sang once; when the cook listened, the water was still warming.", "Attention cannot force a process to finish, but waiting need not contain only impatience.")
    ],
    identity: [
      scene("The nameless coat", "A traveller lost the label sewn inside a coat.", "The next cold morning, the coat was just as warm.", "A label can help describe a thing without creating all its value. What qualities remain when a familiar description is missing?"),
      scene("The mirror's task", "An apprentice asked a mirror which face was the true one.", "The mirror returned each expression and kept none.", "An expression need not be the whole of a person. This image invites curiosity about identities without declaring them meaningless.")
    ],
    relationships: [
      scene("The second chair", "Two neighbours each brought a speech to an empty table.", "When one set the paper down, the other finally sat.", "Putting down a prepared answer can create space for contact. Listening is not the same as agreeing or abandoning boundaries."),
      scene("The shared umbrella", "Two walkers argued over whose umbrella should face the rain.", "They moved closer; both shoulders grew dry.", "A shared practical need can be missed when a conversation becomes only a contest. Not every disagreement, however, has a simple compromise.")
    ],
    uncertainty: [
      scene("The fog's edge", "A walker waited for the fog to reveal the mountain.", "A nearby stone was clear enough to rest a foot upon.", "Limited knowledge may still permit a small reversible step. This is not encouragement to take unsafe risks."),
      scene("The unopened seed", "A gardener demanded to see the flower inside a seed.", "The unopened seed offered no picture, only a place to begin.", "Some knowledge arrives through careful participation rather than advance certainty. The metaphor cannot guarantee success.")
    ]
  };

  // Concrete motifs help with prompts outside the abstract theme vocabulary.
  // These are vocabulary rules, NOT an understanding of a sentence or its truth.
  const MOTIFS = [
    { id: "sky", words: ["moon", "sun", "star", "stars", "sky", "cow", "jumped", "flying", "flight"], scenes: [
      scene("The moon's fence", "A calf leapt a fence beneath the moon.", "Its shadow cleared the moon in the pond, but its hooves landed in grass.", "An extraordinary image and an ordinary landing can coexist. The scene asks how imagination and lived limits illuminate each other, rather than whether a fanciful statement is literally true."),
      scene("A ladder for moonlight", "A child leaned a ladder against the moon's reflection.", "The first rung touched water; the moon remained within reach of the eye.", "A reflected destination may not be reached by the tools used for a physical one. Ask whether you are confusing an image, a wish and an attainable action."),
      scene("The unheld star", "An astronomer closed a fist around a star seen through the window.", "Opening the hand lost nothing; the room was still full of darkness and light.", "Seeing something does not require possessing it. The star offers a way to explore wonder without turning it into ownership.")
    ] },
    { id: "animals", words: ["cat", "dog", "bird", "birds", "horse", "animal", "animals", "fish"], scenes: [
      scene("The bird's lesson", "A scholar explained the sky to a bird on the sill.", "Before the explanation ended, the bird had crossed it.", "An account of an experience is not the experience itself. Words can help without replacing participation."),
      scene("The patient cat", "A cat sat beside the door while its keeper searched for a key.", "When the door opened, the cat stayed to watch a leaf.", "What someone appears to want may be an assumption made by the observer. The image invites curiosity before certainty."),
      scene("The fish's map", "A mapmaker drew every bend of a river for a fish.", "The fish passed beneath the paper without becoming lost.", "A map serves a particular traveller. A useful explanation for one perspective need not be necessary for every other.")
    ] },
    { id: "water", words: ["water", "sea", "ocean", "river", "rain", "lake", "pond"], scenes: [
      scene("The divided rain", "Two buckets argued about which held the true rain.", "A child poured both into the garden.", "Separate containers can make a shared source look divided. Consider which distinctions help and which only harden a boundary."),
      scene("The wave's address", "A messenger searched the shore for yesterday's wave.", "Every arriving wave gave the same address and a different shape.", "Continuity and change can be visible at once. The image asks what you mean when you call something the same."),
      scene("The dry crossing", "A walker rehearsed crossing a stream until sunset.", "The stones grew cool, but the rehearsed feet had never become wet.", "Preparation and action are different experiences. Consider when preparation helps and when it quietly replaces a manageable attempt.")
    ] },
    { id: "paths", words: ["road", "path", "journey", "travel", "bicycle", "bike", "train", "car", "walk"], scenes: [
      scene("The resting wheel", "A cyclist lifted a wheel and spun it toward the distant hills.", "It travelled quickly and went nowhere until it touched the road.", "Activity and progress are not identical. Contact with actual conditions may matter more than speed."),
      scene("The folded road", "A traveller folded the map until home touched the destination.", "Outside the paper, the road still asked for footsteps.", "A plan can connect ideas instantly while the lived journey still takes effort. Neither fact makes planning useless."),
      scene("The signpost's journey", "A walker asked a signpost how often it had visited the village.", "The arrow pointed faithfully; its feet remained in stone.", "Guidance can be useful without being lived experience. Ask what the sign can tell you and what you must discover yourself.")
    ] },
    { id: "work", words: ["work", "job", "code", "coding", "computer", "money", "meeting", "build"], scenes: [
      scene("The silent hammer", "A builder polished a hammer until it reflected the whole house.", "The evening rain still fell through the unfinished roof.", "Perfecting a tool is different from using it toward the need at hand. Which activity serves the actual purpose?"),
      scene("The erased line", "A programmer removed a line and waited for the program to complain.", "The machine ran; the programmer listened to the newly quiet room.", "Adding more is not always the same as contributing more. Absence can reveal what was unnecessary."),
      scene("The empty ledger", "A merchant counted every coin earned during the day.", "A neighbour returned a borrowed chair, and no column knew where to put it.", "A measurement may be accurate while leaving out something valuable. Ask what your chosen accounting makes visible or invisible.")
    ] },
    { id: "plants", words: ["tree", "trees", "flower", "flowers", "garden", "seed", "leaf", "plant"], scenes: [
      scene("The instructed seed", "A gardener drew a flower beside a seed to explain its task.", "The seed opened underground, where it could not see the drawing.", "A living process can unfold without matching the picture made for it. A plan may orient attention without controlling development."),
      scene("The borrowed shade", "A child tried to carry a tree's shade home in a basket.", "The basket grew warm; the tree kept offering shade to strangers.", "Some benefits are encountered through relationship to a place, not stored as possessions. What changes when you stay with their source?"),
      scene("The unnamed blossom", "A visitor forgot the name of a flower and apologised to it.", "A bee arrived without asking for an introduction.", "Naming can enrich attention, but lack of a name need not prevent encounter. Knowledge and direct noticing can support one another.")
    ] }
  ];

  /** FNV-style 32-bit hash: all characters influence the starting composition.
   * Math.imul keeps multiplication in 32-bit arithmetic. This is NOT encryption
   * or semantic understanding, and different texts can share the same hash. */
  function hashText(text) {
    let hash = 2166136261;
    for (const character of text) {
      hash = Math.imul(hash ^ character.codePointAt(0), 16777619) >>> 0;
    }
    return hash;
  }

  function choosePool(context, theme, matched) {
    const tokens = new Set(context.toLowerCase().match(/[\p{L}\p{N}]+/gu) || []);
    let motif = null;
    let best = 0;
    for (const candidate of MOTIFS) {
      const score = candidate.words.filter(word => tokens.has(word)).length;
      if (score > best) { motif = candidate; best = score; }
    }
    if (motif) return { scenes: motif.scenes, motif: motif.id };
    if (matched) {
      const original = scene(`The image ${theme.place}`,
        `Someone ${theme.place} held ${theme.object}.`,
        `They ${theme.action}. ${theme.response}`,
        `The scene invites reflection on ${theme.tension}.`);
      return { scenes: [original, ...EXTRA_SCENES[theme.id]], motif: null };
    }
    // Unknown subjects no longer all become a stone at a garden gate.
    return { scenes: MOTIFS.flatMap(item => item.scenes), motif: null };
  }

  /** Pure composition remains deterministic for tests. Freshness belongs to
   * createSession below, which remembers what the reader has actually seen. */
  function generate(input, variant = 0) {
    const context = normalizeInput(input);
    if (!Number.isSafeInteger(variant) || variant < 0) {
      throw new RangeError("variant must be a nonnegative safe integer");
    }
    const { theme, score } = selectTheme(context);
    const pool = choosePool(context, theme, score > 0);
    const variantCount = pool.scenes.length * ENDINGS.length;
    const index = variant % variantCount;
    // Reduce before adding so even MAX_SAFE_INTEGER cannot lose precision.
    const offset = (hashText(context.toLowerCase()) % variantCount + index) % variantCount;
    // Visit every scene before repeating one with a different final question.
    const selected = pool.scenes[offset % pool.scenes.length];
    const ending = ENDINGS[Math.floor(offset / pool.scenes.length)];
    return {
      context, theme: theme.id, themeName: theme.name, matched: score > 0,
      motif: pool.motif, variant: index, variantCount,
      title: selected.title, lines: [selected.opening, selected.turn, ending],
      // Neither the poem nor its gloss repeats the user's question. The gloss
      // explains THIS image rather than assigning every scene the same moral.
      reading: `One possible reading: ${selected.reading} This is an invitation to investigate, not a verdict about you; another reading may fit better.`,
      questions: [theme.question, "Which part of this image fits your situation, and which part does not?", "What other reading could challenge this first interpretation?"],
      practice: theme.practice
    };
  }

  /** A session remembers exact rendered stories, across DIFFERENT inputs too.
   * No random retry loop can promise non-repetition: scan the finite pool once.
   * Once exhausted, say so honestly rather than quietly serving an old poem. */
  function createSession() {
    const seen = new Set();
    return {
      next(input) {
        const first = generate(input);
        for (let variant = 0; variant < first.variantCount; variant++) {
          const story = variant === 0 ? first : generate(first.context, variant);
          const key = JSON.stringify([story.title, story.lines]);
          if (!seen.has(key)) {
            seen.add(key);
            return story;
          }
        }
        throw new RangeError("All available tellings for this subject have been shown. Try a different subject or Clear to start a new session.");
      },
      clear() { seen.clear(); }
    };
  }

  // One export for browsers, one for Node's test runner. Neither needs a build.
  const api = Object.freeze({ MAX_LENGTH, normalizeInput, generate, createSession });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else globalThis.KoanGarden = api;
})();
