# Pocket Tasks: a guided first reading

You do not need to understand every line before running the app. Work through one small experiment at a time. Keep [the README](README.md) open for setup and storage limitations.

## 1. A 30-minute reading route

1. **Run and use it (5 minutes).** Add two tasks, complete one, switch filters, and reload. Predict what will survive a reload.
2. **Read HTML (5 minutes).** Find `task-form`, `task-input` and `task-list` in `index.html`. These IDs are the bridge from HTML to JavaScript.
3. **Read one model operation (5 minutes).** Find `addTask()` in `tasks.js`. Follow validation, trimming, object creation and the returned result.
4. **Trace one submission (10 minutes).** Follow the `submit` listener in `app.js` into `commit()`, `save()` and `render()`.
5. **Read its test (5 minutes).** Find `addTask creates new task with correct structure` in `tests/tasks.test.cjs`. Compare the input and expected output.

The code contains section comments and explanations at the point where each idea is used. You can skip detailed validation on your first pass and return to it after understanding the happy path.

## 2. The three representations of your list

The same information appears in three different forms:

```text
JavaScript objects             JSON string                  HTML elements
(tasks in memory)              (localStorage)               (DOM on screen)
       |                             ^                            ^
       +------ serialize/save ------+                            |
       +-------------------- render -----------------------------+
       ^
       +------ read/parse from storage on startup
```

- **State:** `tasks` is an array of objects in memory. It is the source of truth while the page is open.
- **Persistence:** `localStorage` contains a string. `JSON.stringify` converts data to that string; parsing converts it back to data, then validation checks it.
- **View:** `render()` creates checkbox, text and button elements from state. The DOM is not our database.

A checked checkbox alone is not enough to persist a change. Its event handler must update state and save that state.

## 3. Trace “Read a chapter” end to end

Start with an empty list:

```js
[]
```

1. You enter text and press Enter. The form emits a **submit event**.
2. `event.preventDefault()` stops the browser's normal form navigation.
3. The listener creates an ID. For illustration, imagine it is `example-1`; real IDs vary.
4. The model receives `addTask([], "Read a chapter", "example-1")`.
5. It returns:

```js
{
  tasks: [{ id: "example-1", text: "Read a chapter", completed: false }],
  task: { id: "example-1", text: "Read a chapter", completed: false }
}
```

The two displayed task objects above describe the same new task; the implementation shares that task object between `result.task` and the array entry.

6. `commit(result.tasks, "Task added.")` replaces the in-memory list.
7. `save()` writes a string like this under the app's storage key:

```json
{"version":1,"tasks":[{"id":"example-1","text":"Read a chapter","completed":false}]}
```

8. `render()` creates a list item and an unchecked checkbox. `textContent` displays the task text literally.
9. An accessible status message announces the action. The input is cleared and focused for your next task.

If step 7 fails, steps 8–9 still happen: the page remains usable, but the warning says the changes are unsaved. A successful-looking screen is not proof of a successful save.

## 4. Why the model is separate

`tasks.js` doesn't know about browsers, HTML, events or storage. Its inputs and outputs are ordinary data. That means Node can run its tests without opening a window.

```js
// Try in the page's Developer Tools Console; this does NOT change the app's list.
const example = PocketTasks.addTask([], "Read a chapter", "example-1");
const completed = PocketTasks.toggleTask(example.tasks, "example-1");
console.log(example.tasks[0].completed); // false: original was not changed
console.log(completed[0].completed);    // true: changed task is a new object
console.log(PocketTasks.countActive(completed)); // 0
```

These arrays aren't deep-frozen. Unchanged task objects may be shared between results; treat them as read-only and use the model functions instead of assigning properties yourself.

**Why not use the array position as the ID?** Delete the first item and every later index shifts. A stable ID keeps identity independent of position, filtering and deletion.

## 5. Tiny syntax glossary

| Syntax or term | Meaning here |
| --- | --- |
| `const name = value` | The binding cannot be reassigned; an object it refers to may still be mutable. |
| `let tasks = []` | A binding whose value can be replaced when state changes. |
| `{ id, text, completed }` | An object with named fields; shorthand reads variables with those names. |
| `[...tasks, newTask]` | A new array containing the old entries followed by one new entry. |
| `{ ...task, completed: true }` | A shallow copy of a task with one field replaced. |
| `task => !task.completed` | An arrow function; `!` negates a value's truthiness. |
| `map()` | Produce one output entry for each input entry. |
| `filter()` | Keep entries whose predicate returns true. |
| `find()` / `findIndex()` | Find the first matching item / its position; absent results are `undefined` / `-1`. |
| `===` | Strict equality without automatic type conversion. |
| `condition ? a : b` | Choose one of two expressions. |
| `` `${count} tasks` `` | A template literal inserts an expression into a string. |
| `?.` | Optional chaining: skip a property/call if its receiver is null or undefined. |
| `try / catch` | Attempt an operation and handle a thrown exception. |
| IIFE | A function expression called immediately to create a private scope. |
| DOM | The browser's tree of document elements. |
| Origin | Scheme + hostname + port; it determines which pages share localStorage. |

## 6. Things that are easy to get wrong

### A string isn't a boolean

`"false"` is a nonempty string, so it is **truthy**. A checkbox should use the boolean `false`, not text pretending to be a boolean. Saved-data validation requires the exact type.

### JSON parsing isn't validation

`JSON.parse('{"version":1,"tasks":"oops"}')` is valid JSON, but not a valid task list. Parsing checks syntax; model validation checks shape, types, limits and unique IDs.

### Text isn't HTML

Enter `<b>Hello</b>`. You should see the angle brackets, not bold text. Changing `textContent` to `innerHTML` would interpret user input as markup and create a security risk. Do not make that change as a cosmetic shortcut.

### Filtering isn't deleting

`visible` is a derived array. The whole `tasks` array still exists, so Active/Completed filters must not replace your saved list. The unfinished count deliberately uses all tasks.

### Rebuilding elements affects focus

After a checkbox changes, `render()` removes and recreates the list's children. The focused checkbox would vanish. `focusTask()` locates its replacement, or focuses the input when the task is no longer visible.

### Recovery must be explicit

The nested `try/catch` in `load()` distinguishes unreadable data from blocked storage. Invalid data blocks saving until the user confirms replacement. This is deliberately different from silently treating every failure as an empty list.

## 7. Use a debugger without changing code

1. Open Developer Tools → Sources (called Debugger in some browsers).
2. Open `app.js` and click the line number beside the submit handler's `const result = model.addTask(...)` statement.
3. Add a task. The browser pauses at your **breakpoint**.
4. Inspect `input.value`, `tasks` and `filter` in scope. Step over the call to see `result`.
5. Continue into `commit()` or set a second breakpoint there. Inspect how `tasks` is replaced before rendering.
6. Resume execution and remove the breakpoints when finished.

Don't paste code into the console unless you understand and trust it. The examples here operate on a separate sample array; storage experiments should use disposable data.

## 8. Learn from a test

The tests use **Arrange → Act → Assert**:

```js
// Arrange: prepare an independent starting value.
const before = [];
// Act: call the behavior under test.
const result = PocketTasks.addTask(before, "Learn testing", "test-1");
// Assert: check both the result and the unchanged input.
assert.equal(result.tasks.length, 1);
assert.equal(before.length, 0);
assert.notStrictEqual(result.tasks, before);
```

`assert` comes from Node's built-in `node:assert/strict`; it is available inside the test file, not automatically in the browser console. Equal array contents and identical array references are different questions.

Run `node --test day-03-pocket-tasks/tests/tasks.test.cjs` from the repository root. Unit tests check model behavior; the README's browser checklist covers the interface and storage failures. Syntax checks only establish that code can be parsed, not that it behaves correctly.

## 9. Three exercises with observable outcomes

1. **Change the empty-state message.** Edit the literal message in `render()`, reload, and clear your disposable list. Your new message should appear; saving and counters should be unchanged.
2. **Try a standalone model experiment.** Add two tasks in the Console using a separate array, complete one, and filter for active tasks. Expect one active result and an unchanged original array. Reload should not add these sample tasks to the real app.
3. **Design editing before implementing it.** Write down rules: preserve ID and completion state, trim text, reject blank/overlong text, leave unknown IDs unchanged. Add a model test for each rule, implement an `editTask` function, then connect an accessible edit control. Do not add the UI first and hope validation follows.

After a change: run the tests, try the interface, read the warnings, and explain in your own words where state lives.

## Further reading

- [MDN: JavaScript first steps](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting)
- [MDN: Event bubbling](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/Event_bubbling)
- [MDN: Using the Web Storage API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API/Using_the_Web_Storage_API)
- [MDN: Array methods](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array)

Own code and documentation: [MIT licence](../LICENSE). Linked references retain their authors' rights; see [third-party notices](../THIRD_PARTY_NOTICES.md).
