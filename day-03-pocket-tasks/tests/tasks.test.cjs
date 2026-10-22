/**
 * PocketTasks Test Suite
 * Built with Node.js node:test and assert for strict validation
 * Covers immutability, constraints, duplicates, edge cases, and serialization
 */

// Node is a JavaScript runtime outside the browser. require() imports a module.
// Both tools below ship with Node: there is no npm package to install.
const test = require('node:test');
const assert = require('node:assert/strict');
const PocketTasks = require('../tasks.js');

// A test normally has three stages: Arrange (prepare input), Act (call the
// function), Assert (check the result). A failed assertion makes Node report
// a failure. Passing tests are examples and regression protection, not proof
// that every possible input or browser interaction is correct.
//
// Destructuring pulls named properties out of the exported model object.
const {
  MAX_TEXT_LENGTH,
  MAX_TASKS,
  addTask,
  toggleTask,
  deleteTask,
  clearCompleted,
  filterTasks,
  countActive,
  serializeTasks,
  parseTasks
} = PocketTasks;

// ============================================================================
// API Constants
// ============================================================================

test('API constants are correct', () => {
  assert.equal(MAX_TEXT_LENGTH, 200, 'MAX_TEXT_LENGTH should be 200');
  assert.equal(MAX_TASKS, 500, 'MAX_TASKS should be 500');
});

// ============================================================================
// addTask - Basic Functionality
// ============================================================================

// Representative Arrange–Act–Assert example:
// [] is our arranged starting list; addTask is the action; assertions below
// compare the returned array/object to the expected result.
test('addTask creates new task with correct structure', () => {
  const tasks = [];
  const result = addTask(tasks, 'Buy milk', 'task-1');

  assert.ok(result.tasks, 'Result should have tasks property');
  assert.ok(result.task, 'Result should have task property');
  assert.equal(result.task.id, 'task-1', 'Task id should match');
  assert.equal(result.task.text, 'Buy milk', 'Task text should match');
  assert.equal(result.task.completed, false, 'New task should be incomplete');
});

// Equal contents do not imply identical objects. notStrictEqual checks that
// the result is a different array reference; checking original.length also
// proves that adding did not append into the caller's original array.
test('addTask returns new array (immutability)', () => {
  const original = [];
  const result = addTask(original, 'Task 1', 'id-1');

  assert.notStrictEqual(result.tasks, original, 'Should return new array');
  assert.equal(original.length, 0, 'Original array should not be modified');
  assert.equal(result.tasks.length, 1, 'New array should contain 1 task');
});

test('addTask trims whitespace from text and id', () => {
  const result = addTask([], '  Buy milk  ', '  task-1  ');

  assert.equal(result.task.text, 'Buy milk', 'Text should be trimmed');
  assert.equal(result.task.id, 'task-1', 'ID should be trimmed');
});

test('addTask builds on existing tasks', () => {
  let tasks = [];
  const r1 = addTask(tasks, 'Task 1', 'id-1');
  const r2 = addTask(r1.tasks, 'Task 2', 'id-2');

  assert.equal(r2.tasks.length, 2, 'Should have 2 tasks');
  assert.equal(r2.tasks[0].text, 'Task 1', 'First task preserved');
  assert.equal(r2.tasks[1].text, 'Task 2', 'Second task added');
});

// ============================================================================
// addTask - Validation & Constraints
// ============================================================================

test('addTask rejects empty text', () => {
  assert.throws(
    () => addTask([], '', 'id-1'),
    /Task text must be a non-empty string/,
    'Should reject empty text'
  );
  assert.throws(
    () => addTask([], '   ', 'id-1'),
    /Task text must be a non-empty string/,
    'Should reject whitespace-only text'
  );
});

test('addTask rejects empty id', () => {
  assert.throws(
    () => addTask([], 'Task', ''),
    /Task id must be a non-empty string/,
    'Should reject empty id'
  );
  assert.throws(
    () => addTask([], 'Task', '   '),
    /Task id must be a non-empty string/,
    'Should reject whitespace-only id'
  );
});

test('addTask rejects non-string text', () => {
  assert.throws(
    () => addTask([], 123, 'id-1'),
    /Task text must be a non-empty string/
  );
  assert.throws(
    () => addTask([], null, 'id-1'),
    /Task text must be a non-empty string/
  );
});

test('addTask rejects non-string id', () => {
  assert.throws(
    () => addTask([], 'Task', 123),
    /Task id must be a non-empty string/
  );
  assert.throws(
    () => addTask([], 'Task', null),
    /Task id must be a non-empty string/
  );
});

test('addTask text respects MAX_TEXT_LENGTH limit', () => {
  const validText = 'a'.repeat(MAX_TEXT_LENGTH);
  const overText = 'a'.repeat(MAX_TEXT_LENGTH + 1);

  const result = addTask([], validText, 'id-1');
  assert.equal(result.task.text.length, MAX_TEXT_LENGTH, 'Should accept max length');

  assert.throws(
    () => addTask([], overText, 'id-1'),
    /exceeds.*UTF16 unit limit/,
    'Should reject text over limit'
  );
});

test('addTask id respects 100 character limit', () => {
  const validId = 'a'.repeat(100);
  const overId = 'a'.repeat(101);

  const result = addTask([], 'Task', validId);
  assert.equal(result.task.id.length, 100, 'Should accept max id length');

  assert.throws(
    () => addTask([], 'Task', overId),
    /exceeds 100 character limit/,
    'Should reject id over limit'
  );
});

test('addTask rejects duplicate id', () => {
  const tasks = [{ id: 'dup-id', text: 'Task 1', completed: false }];

  assert.throws(
    () => addTask(tasks, 'Task 2', 'dup-id'),
    /already exists/,
    'Should reject duplicate id'
  );
});

test('addTask enforces MAX_TASKS capacity limit', () => {
  let tasks = [];

  // Fill to capacity
  for (let i = 0; i < MAX_TASKS; i++) {
    tasks = addTask(tasks, `Task ${i}`, `id-${i}`).tasks;
  }

  assert.equal(tasks.length, MAX_TASKS, 'Should reach capacity');

  assert.throws(
    () => addTask(tasks, 'Over capacity', 'id-over'),
    /at maximum capacity/,
    'Should reject adding beyond capacity'
  );
});

// ============================================================================
// toggleTask - Functionality & Immutability
// ============================================================================

test('toggleTask toggles completed status', () => {
  const tasks = [{ id: 'id-1', text: 'Task', completed: false }];
  const toggled = toggleTask(tasks, 'id-1');

  assert.equal(toggled[0].completed, true, 'Should toggle to true');
  assert.equal(tasks[0].completed, false, 'Original should not change');

  const toggled2 = toggleTask(toggled, 'id-1');
  assert.equal(toggled2[0].completed, false, 'Should toggle back to false');
});

test('toggleTask returns new array', () => {
  const original = [{ id: 'id-1', text: 'Task', completed: false }];
  const result = toggleTask(original, 'id-1');

  assert.notStrictEqual(result, original, 'Should return new array');
});

test('toggleTask with unknown id returns new array unchanged', () => {
  const tasks = [{ id: 'id-1', text: 'Task', completed: false }];
  const result = toggleTask(tasks, 'unknown-id');

  assert.notStrictEqual(result, tasks, 'Should return new array');
  assert.deepEqual(result, tasks, 'New array should have same content');
  assert.equal(result[0].completed, false, 'No changes made');
});

test('toggleTask preserves other task properties', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: true }
  ];
  const toggled = toggleTask(tasks, 'id-1');

  assert.equal(toggled[0].id, 'id-1', 'ID preserved');
  assert.equal(toggled[0].text, 'Task 1', 'Text preserved');
  assert.equal(toggled[1].completed, true, 'Other tasks unchanged');
});

// ============================================================================
// deleteTask - Functionality & Immutability
// ============================================================================

test('deleteTask removes task by id', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: false }
  ];
  const result = deleteTask(tasks, 'id-1');

  assert.equal(result.length, 1, 'Should have 1 task remaining');
  assert.equal(result[0].id, 'id-2', 'Correct task remains');
});

test('deleteTask returns new array', () => {
  const original = [{ id: 'id-1', text: 'Task', completed: false }];
  const result = deleteTask(original, 'id-1');

  assert.notStrictEqual(result, original, 'Should return new array');
});

test('deleteTask with unknown id returns new array unchanged', () => {
  const tasks = [{ id: 'id-1', text: 'Task', completed: false }];
  const result = deleteTask(tasks, 'unknown-id');

  assert.notStrictEqual(result, tasks, 'Should return new array');
  assert.deepEqual(result, tasks, 'Content unchanged');
  assert.equal(result.length, 1, 'Task still present');
});

test('deleteTask removes only matching id', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: false },
    { id: 'id-3', text: 'Task 3', completed: false }
  ];
  const result = deleteTask(tasks, 'id-2');

  assert.equal(result.length, 2, 'Should have 2 tasks');
  assert.equal(result[0].id, 'id-1', 'First task preserved');
  assert.equal(result[1].id, 'id-3', 'Third task preserved');
});

// ============================================================================
// clearCompleted - Functionality
// ============================================================================

test('clearCompleted removes all completed tasks', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: true },
    { id: 'id-2', text: 'Task 2', completed: false },
    { id: 'id-3', text: 'Task 3', completed: true }
  ];
  const result = clearCompleted(tasks);

  assert.equal(result.length, 1, 'Should have 1 task remaining');
  assert.equal(result[0].id, 'id-2', 'Only active task remains');
});

test('clearCompleted returns new array with no completed tasks', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: false }
  ];
  const result = clearCompleted(tasks);

  assert.notStrictEqual(result, tasks, 'Should return new array');
  assert.deepEqual(result, tasks, 'All tasks remain if none completed');
});

test('clearCompleted on empty array returns empty', () => {
  const result = clearCompleted([]);
  assert.deepEqual(result, [], 'Empty array stays empty');
});

// ============================================================================
// filterTasks - All Filters
// ============================================================================

test('filterTasks default filter returns all tasks', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: true }
  ];
  const result = filterTasks(tasks);

  assert.deepEqual(result, tasks, 'Default should return all');
});

test('filterTasks all returns all tasks', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: true }
  ];
  const result = filterTasks(tasks, 'all');

  assert.deepEqual(result, tasks, 'All filter returns all tasks');
});

test('filterTasks active returns only incomplete tasks', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: true },
    { id: 'id-3', text: 'Task 3', completed: false }
  ];
  const result = filterTasks(tasks, 'active');

  assert.equal(result.length, 2, 'Should have 2 active tasks');
  assert.ok(result.every(t => !t.completed), 'All should be incomplete');
});

test('filterTasks completed returns only completed tasks', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: true },
    { id: 'id-3', text: 'Task 3', completed: true }
  ];
  const result = filterTasks(tasks, 'completed');

  assert.equal(result.length, 2, 'Should have 2 completed tasks');
  assert.ok(result.every(t => t.completed), 'All should be completed');
});

test('filterTasks rejects invalid filter', () => {
  assert.throws(
    () => filterTasks([], 'invalid'),
    /Invalid filter/,
    'Should reject invalid filter'
  );
  assert.throws(
    () => filterTasks([], 'todo'),
    /Invalid filter/
  );
});

test('filterTasks returns new array', () => {
  const tasks = [{ id: 'id-1', text: 'Task', completed: false }];
  const result = filterTasks(tasks, 'all');

  assert.notStrictEqual(result, tasks, 'Should return new array');
});

// ============================================================================
// countActive - Functionality
// ============================================================================

test('countActive counts incomplete tasks', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: true },
    { id: 'id-3', text: 'Task 3', completed: false }
  ];

  assert.equal(countActive(tasks), 2, 'Should count 2 active tasks');
});

test('countActive returns 0 for empty array', () => {
  assert.equal(countActive([]), 0, 'Empty array has 0 active');
});

test('countActive returns 0 when all completed', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: true },
    { id: 'id-2', text: 'Task 2', completed: true }
  ];

  assert.equal(countActive(tasks), 0, 'No active tasks');
});

test('countActive returns count when all active', () => {
  const tasks = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: false },
    { id: 'id-3', text: 'Task 3', completed: false }
  ];

  assert.equal(countActive(tasks), 3, 'All tasks are active');
});

// ============================================================================
// serializeTasks - Functionality & Validation
// ============================================================================

test('serializeTasks produces valid JSON with version', () => {
  const tasks = [{ id: 'id-1', text: 'Task', completed: false }];
  const json = serializeTasks(tasks);
  const parsed = JSON.parse(json);

  assert.equal(parsed.version, 1, 'Should have version 1');
  assert.deepEqual(parsed.tasks, tasks, 'Tasks should match');
});

test('serializeTasks validates before serializing', () => {
  assert.throws(
    () => serializeTasks([{ id: 'id-1', text: 'Task', completed: 'not-bool' }]),
    /completed must be a boolean/,
    'Should validate before serializing'
  );
});

test('serializeTasks with empty array', () => {
  const json = serializeTasks([]);
  const parsed = JSON.parse(json);

  assert.deepEqual(parsed.tasks, [], 'Empty array serialized correctly');
});

test('serializeTasks with special characters in text', () => {
  const tasks = [{ id: 'id-1', text: 'Task with <html> & "quotes"', completed: false }];
  const json = serializeTasks(tasks);
  const parsed = JSON.parse(json);

  assert.equal(parsed.tasks[0].text, 'Task with <html> & "quotes"', 'Special chars preserved');
});

// ============================================================================
// parseTasks - Functionality & Error Handling
// ============================================================================

test('parseTasks null returns empty array', () => {
  const result = parseTasks(null);
  assert.deepEqual(result, [], 'null should return empty array');
});

test('parseTasks undefined returns empty array', () => {
  const result = parseTasks(undefined);
  assert.deepEqual(result, [], 'undefined should return empty array');
});

test('parseTasks parses valid JSON', () => {
  const original = [{ id: 'id-1', text: 'Task', completed: false }];
  const json = JSON.stringify({ version: 1, tasks: original });
  const result = parseTasks(json);

  assert.deepEqual(result, original, 'Should parse valid JSON');
});

test('parseTasks trims text and id', () => {
  const json = JSON.stringify({
    version: 1,
    tasks: [{ id: '  id-1  ', text: '  Task  ', completed: false }]
  });
  const result = parseTasks(json);

  assert.equal(result[0].id, 'id-1', 'ID should be trimmed');
  assert.equal(result[0].text, 'Task', 'Text should be trimmed');
});

test('parseTasks ignores unknown properties', () => {
  const json = JSON.stringify({
    version: 1,
    tasks: [{ id: 'id-1', text: 'Task', completed: false, unknown: 'prop', extra: 123 }]
  });
  const result = parseTasks(json);

  assert.equal(result[0].id, 'id-1', 'Should have id');
  assert.equal(result[0].text, 'Task', 'Should have text');
  assert.equal(result[0].completed, false, 'Should have completed');
  assert.equal(Object.keys(result[0]).length, 3, 'Should only have 3 properties');
});

test('parseTasks rejects malformed JSON', () => {
  assert.throws(
    () => parseTasks('not json'),
    /Malformed JSON/,
    'Should reject invalid JSON'
  );
  assert.throws(
    () => parseTasks('{ invalid }'),
    /Malformed JSON/
  );
});

test('parseTasks rejects missing version', () => {
  const json = JSON.stringify({ tasks: [] });
  assert.throws(
    () => parseTasks(json),
    /Unsupported tasks version/,
    'Should reject missing version'
  );
});

test('parseTasks rejects wrong version', () => {
  const json = JSON.stringify({ version: 2, tasks: [] });
  assert.throws(
    () => parseTasks(json),
    /Unsupported tasks version/,
    'Should reject version 2'
  );
});

test('parseTasks rejects non-array tasks property', () => {
  const json = JSON.stringify({ version: 1, tasks: 'not-array' });
  assert.throws(
    () => parseTasks(json),
    /tasks must be an array/,
    'Should reject non-array tasks'
  );
});

test('parseTasks rejects task with invalid id', () => {
  const json = JSON.stringify({ version: 1, tasks: [{ text: 'Task', completed: false }] });
  assert.throws(
    () => parseTasks(json),
    /id must be non-empty string/,
    'Should reject missing id'
  );
});

test('parseTasks rejects task with invalid text', () => {
  const json = JSON.stringify({ version: 1, tasks: [{ id: 'id-1', completed: false }] });
  assert.throws(
    () => parseTasks(json),
    /text must be non-empty string/,
    'Should reject missing text'
  );
});

test('parseTasks rejects task with invalid completed boolean', () => {
  const json = JSON.stringify({ version: 1, tasks: [{ id: 'id-1', text: 'Task', completed: 'yes' }] });
  assert.throws(
    () => parseTasks(json),
    /completed must be boolean/,
    'Should reject non-boolean completed'
  );
});

test('parseTasks rejects text exceeding MAX_TEXT_LENGTH', () => {
  const longText = 'a'.repeat(MAX_TEXT_LENGTH + 1);
  const json = JSON.stringify({ version: 1, tasks: [{ id: 'id-1', text: longText, completed: false }] });
  assert.throws(
    () => parseTasks(json),
    /exceeds.*UTF16 unit limit/,
    'Should reject text over limit'
  );
});

test('parseTasks rejects id exceeding 100 character limit', () => {
  const longId = 'a'.repeat(101);
  const json = JSON.stringify({ version: 1, tasks: [{ id: longId, text: 'Task', completed: false }] });
  assert.throws(
    () => parseTasks(json),
    /exceeds 100 character limit/,
    'Should reject id over limit'
  );
});

test('parseTasks rejects duplicate ids', () => {
  const json = JSON.stringify({
    version: 1,
    tasks: [
      { id: 'dup', text: 'Task 1', completed: false },
      { id: 'dup', text: 'Task 2', completed: false }
    ]
  });
  assert.throws(
    () => parseTasks(json),
    /Duplicate task id/,
    'Should reject duplicate ids'
  );
});

// ============================================================================
// Round-trip Serialization & Deserialization
// ============================================================================

test('Round-trip serialization preserves data', () => {
  const original = [
    { id: 'id-1', text: 'Task 1', completed: false },
    { id: 'id-2', text: 'Task 2', completed: true },
    { id: 'id-3', text: 'Task 3 with <html> & "quotes"', completed: false }
  ];

  const json = serializeTasks(original);
  const restored = parseTasks(json);

  assert.deepEqual(restored, original, 'Should round-trip correctly');
});

test('Round-trip with empty array', () => {
  const json = serializeTasks([]);
  const restored = parseTasks(json);

  assert.deepEqual(restored, [], 'Empty array round-trip');
});

// ============================================================================
// Immutability Tests
// ============================================================================

test('Operations do not mutate input array', () => {
  const original = [{ id: 'id-1', text: 'Task', completed: false }];
  const copy = JSON.parse(JSON.stringify(original));

  // Test each operation
  toggleTask(original, 'id-1');
  deleteTask(original, 'id-1');
  clearCompleted(original);
  filterTasks(original, 'active');

  assert.deepEqual(original, copy, 'Original should not be mutated by any operation');
});

test('Operations do not mutate task objects within array', () => {
  const task = { id: 'id-1', text: 'Task', completed: false };
  const tasks = [task];

  const toggled = toggleTask(tasks, 'id-1');

  assert.equal(tasks[0].completed, false, 'Original task not mutated');
  assert.equal(toggled[0].completed, true, 'New task is toggled');
});

// ============================================================================
// Edge Cases & Integration
// ============================================================================

test('Complex workflow scenario', () => {
  let tasks = [];

  // Add multiple tasks
  const r1 = addTask(tasks, 'Buy milk', 'task-1');
  tasks = r1.tasks;

  const r2 = addTask(tasks, 'Walk dog', 'task-2');
  tasks = r2.tasks;

  const r3 = addTask(tasks, 'Read book', 'task-3');
  tasks = r3.tasks;

  assert.equal(countActive(tasks), 3, 'All 3 tasks should be active');

  // Toggle one
  tasks = toggleTask(tasks, 'task-2');
  assert.equal(countActive(tasks), 2, 'Should have 2 active after toggle');

  // Filter
  const active = filterTasks(tasks, 'active');
  assert.equal(active.length, 2, 'Should have 2 active when filtered');

  const completed = filterTasks(tasks, 'completed');
  assert.equal(completed.length, 1, 'Should have 1 completed when filtered');

  // Serialize and restore
  const json = serializeTasks(tasks);
  const restored = parseTasks(json);
  assert.deepEqual(restored, tasks, 'Restored should match');
});

test('Text treated as literal HTML (not parsed)', () => {
  const result = addTask([], '<script>alert("xss")</script>', 'id-1');
  assert.equal(result.task.text, '<script>alert("xss")</script>', 'HTML should be literal');
});

test('Very long text at exact limit', () => {
  const maxText = 'a'.repeat(MAX_TEXT_LENGTH);
  const result = addTask([], maxText, 'id-1');
  assert.equal(result.task.text.length, MAX_TEXT_LENGTH);
});

test('Very long id at exact limit', () => {
  const maxId = 'a'.repeat(100);
  const result = addTask([], 'Task', maxId);
  assert.equal(result.task.id.length, 100);
});

test('Unicode handling in text', () => {
  const unicodeText = '🎯 Task with emoji and 中文 and ñ';
  const result = addTask([], unicodeText, 'id-1');
  assert.equal(result.task.text, unicodeText, 'Unicode should be preserved');
});

// Shared validation must protect every operation, not only loading JSON.
// A sparse array has an empty slot, not a valid task. Test every public
// operation against the same invalid inputs so validation stays consistent.
// assert.throws expects an exception; unexpected success would fail the test.
test('all operations reject malformed and sparse task arrays', () => {
  const operations = [
    value => addTask(value, 'new', 'new-id'),
    value => toggleTask(value, 'id'),
    value => deleteTask(value, 'id'),
    value => clearCompleted(value),
    value => filterTasks(value),
    value => countActive(value),
    value => serializeTasks(value)
  ];
  for (const operation of operations) {
    for (const invalid of [null, {}, [null], new Array(1), [{id:'id',text:'x',completed:'false'}]]) {
      assert.throws(() => operation(invalid));
    }
  }
});
