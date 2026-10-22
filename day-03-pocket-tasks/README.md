# Day 03 · Pocket Tasks

A tiny to-do list in **HTML, CSS and JavaScript**. Add tasks, tick them off, filter your list and reload without losing it—provided your browser allows local storage.

No accounts, backend, AI API, runtime dependencies or build tools. AI assisted with coding; the app itself doesn't use AI.

## 1. Run it

Download and extract the repository or update your clone with `git pull`. From the repository root:

```sh
cd day-03-pocket-tasks
python3 -m http.server 8000 --bind 127.0.0.1
```

On Windows use `py` instead of `python3`. Open **http://localhost:8000** in a modern browser. Keep the terminal running; Ctrl+C stops the server. Python just serves files; JavaScript runs the app in your browser.

You can open `index.html` directly, but `file://` storage behavior is browser-dependent. **Use the local server for reliable persistence testing.** Keep using the same browser, host and port: `localhost:8000`, `127.0.0.1:8000` and `localhost:8001` are different storage origins.

If port 8000 is occupied, use 8001 and adjust the URL. No Python available? Install it from [python.org](https://www.python.org/downloads/) or use an editor's local static-file server.

## 2. Use it

- Type a task and press **Enter** or **Add task**. Surrounding whitespace is removed; blank tasks are rejected.
- Tick a checkbox to complete a task; untick it to undo. Use Tab and Space with a keyboard.
- Use **All / Active / Completed** to filter. Filtering does not change stored tasks.
- **Delete** removes one task. **Clear completed** removes all completed tasks, including those hidden by a filter. These actions have no undo.
- The counter shows unfinished tasks across the whole list, not just the selected filter.
- Adding a task switches to All so the new task is visible. Duplicate text is allowed; stable IDs distinguish tasks.

Limit: **500 tasks**, each up to **200 UTF-16 code units**. The interface calls these characters for simplicity; some emoji use two units or more. There is no editing or reordering in this first version: delete and re-add if needed.

## 3. What saving does—and does not—mean

The browser's `localStorage` stores a JSON string under:

```text
20-days-of-ai-coding:pocket-tasks:v1
```

Only this key is written. The app never calls `localStorage.clear()` or touches another project's saved data.

- Data stays in the same browser profile and origin. It does not sync between devices or upload to GitHub.
- Clearing site data removes it. Private browsing may discard it when the private session ends.
- Storage isn't a backup or encrypted vault. Do not store passwords or sensitive data. Other scripts served from the same origin can access it.
- Use **one tab at a time**. Concurrent tabs use last-write-wins and can overwrite changes; live cross-tab sync isn't implemented.
- A blocked or full storage area produces a visible warning. You can keep working in memory, but those changes may disappear on reload. Later edits retry saving.
- Invalid JSON, unsupported schema versions or invalid task records are **not silently overwritten**. The app shows an empty temporary list and blocks saves. You may inspect/back up the original value in Developer Tools → Application/Storage → Local Storage, then explicitly choose **Discard invalid saved list** and confirm. This replaces it with the currently displayed list only if storage succeeds.

“Saved on this browser” means the browser accepted the last write (or the initial saved value was read); it does not guarantee permanent retention.

## 4. Read the code

```text
day-03-pocket-tasks/
├── index.html          # Semantic form, buttons, status and list container
├── style.css           # Responsive layout and visible keyboard focus
├── tasks.js            # Data rules and JSON validation; no DOM or storage
├── app.js              # Events, safe rendering, focus and persistence
├── tests/
│   └── tasks.test.cjs  # Node's built-in test runner; no install needed
└── README.md
```

### The model: `tasks.js`

A task is an object:

```js
{ id: "unique-id", text: "Take a walk", completed: false }
```

An **array** holds the objects in creation order. `id` is identity, not the array index: deleting one task must not change another's identity.

The script exposes `globalThis.PocketTasks` in a browser and `module.exports` for Node. The same implementation is used in tests and the app.

| API | Result |
| --- | --- |
| `addTask(tasks, text, id)` | `{tasks, task}` containing a new array and the new task |
| `toggleTask(tasks, id)` | New array; selected task has a new object with inverted completion |
| `deleteTask(tasks, id)` | New array excluding that ID |
| `clearCompleted(tasks)` | New array containing active tasks only |
| `filterTasks(tasks, filter)` | New array for `all`, `active` or `completed` |
| `countActive(tasks)` | Number of unfinished tasks |
| `serializeTasks(tasks)` | JSON string with `{version: 1, tasks: [...]}` |
| `parseTasks(raw)` | Validated task array; absent data returns `[]`; invalid data throws |

`MAX_TEXT_LENGTH` and `MAX_TASKS` define limits. Private validation helpers check object shapes, unique nonempty IDs, boolean completion, lengths and capacity. Parsing picks only the known fields and trims text/IDs; unsupported versions are rejected rather than guessed at.

**Immutable operations** return arrays rather than changing their input. Unchanged task objects can be shared, so don't mutate returned objects yourself. Unknown IDs are harmless no-ops. The add function returns both the new array and new task to make the result explicit:

```js
const result = PocketTasks.addTask([], "Read a chapter", "example-1");
const updated = PocketTasks.toggleTask(result.tasks, result.task.id);
console.log(PocketTasks.countActive(updated)); // 0
```

### The interface: `app.js`

- `load()` reads storage, validates JSON, and distinguishes invalid data from inaccessible storage.
- `save()` catches quota/security errors and never claims success after failure.
- `render()` derives the visible list and counters from state.
- `commit()` updates state, saves, renders, then announces the action.
- `focusTask()` restores keyboard focus after rebuilding list controls. If a filtered task disappears, focus goes to the add field.
- Form submission validates input, creates a stable ID using `crypto.randomUUID()` (with a timestamp/random fallback), and adds the task.
- **Event delegation** attaches change/click handlers to the list, not a separate handler to every checkbox and button.

Follow one action: **submit → validate/add → update state → save JSON → render → announce**.

### Safe DOM construction

Task text is assigned using `textContent`, not `innerHTML`. If you enter `<b>Hello</b>`, you see those literal characters, not bold HTML. `createElement`, `append` and `replaceChildren` build actual elements. Data IDs are compared as strings rather than inserted into CSS selectors.

### Accessibility and layout

Native labelled inputs/buttons provide standard keyboard behavior. Filters use `aria-pressed`; actions use a polite status announcement and errors use alerts. Focus is restored when rerendering removes a control. CSS keeps visible focus outlines and stacks controls on narrow screens. No remote fonts, images or analytics are loaded.

## 5. Test it

With Node.js 20+ installed, from the repository root:

```sh
node --check day-03-pocket-tasks/tasks.js
node --check day-03-pocket-tasks/app.js
node --test day-03-pocket-tasks/tests/tasks.test.cjs
```

Or from this project folder: `node --test tests/tasks.test.cjs`. Node is needed only for tests, not normal use. GitHub Actions runs the suite on every push/pull request.

Unit tests exercise the model, not browser behavior. Manual browser checklist:

1. Add two tasks, complete one, reload: both tasks and completion persist.
2. Try every filter and verify the unfinished count stays global.
3. Delete a task; reload and confirm it's gone.
4. Enter `<img src=x onerror=alert(1)>`: it appears as text; no image or alert.
5. Use only Tab, Enter and Space to add, complete, filter and delete.
6. Clear completed tasks; verify active tasks remain after reload.
7. In Developer Tools change this app's storage value to invalid JSON, then reload: a warning appears and the value is preserved until explicit reset.
8. Disable site storage: confirm a warning appears and the page remains usable.
9. Try a narrow/mobile screen; text should wrap without horizontal scrolling.

## 6. Troubleshooting and exercises

- **Tasks disappeared:** check browser profile, private mode, host and port. Read the storage warning. Site-data deletion cannot be undone by this app.
- **Nothing happens:** enable JavaScript, keep all app files together, and inspect Developer Tools → Console.
- **Can't add a task:** remove whitespace, shorten it, or delete tasks if you've reached 500.
- **Python command missing:** use `py` on Windows or install Python; the server command must run in the right folder.

Try adding an edit action, a JSON export/import backup, or a cross-tab conflict warning. Decide the behavior and write model tests before changing the interface. Keep imported text subject to the same validation and safe rendering.

## References and licence

Original educational implementation, created with AI coding assistance. No third-party runtime libraries or assets are bundled.

- [MDN: Your first form](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Your_first_form)
- [MDN: localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
- [MDN: JSON](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON)
- [MDN: textContent](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent)
- [MDN: crypto.randomUUID](https://developer.mozilla.org/en-US/docs/Web/API/Crypto/randomUUID)
- [Node.js test runner](https://nodejs.org/api/test.html)

Own code and documentation: [MIT licence](../LICENSE). References retain their authors' rights; see [third-party notices](../THIRD_PARTY_NOTICES.md).
