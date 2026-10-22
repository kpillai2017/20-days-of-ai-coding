// IIFE (Immediately Invoked Function Expression) Pattern
// ============================================================================
// This function executes immediately: (() => { ... })()
//
// Benefits:
// - Creates a private scope: internal helpers (such as validateTask) are not
//   exposed globally or to require() callers; public methods are exported
// - Only PocketTasks object is exported via module.exports or globalThis
// - Prevents namespace pollution and accidental variable overwriting
// - Allows "use strict" directive to apply only to this module
//
// Dual Export Strategy:
// - Node.js/CommonJS: module.exports for require() calls
// - Browser: globalThis.PocketTasks for <script> tags
// ============================================================================

(() => {
  "use strict";

  /**
   * PocketTasks - A lightweight, immutable task management system
   * Exposes globalThis.PocketTasks with core task operations
   *
   * Design Principles:
   * - Immutability: Task-changing functions return new arrays/objects, never mutate inputs
   * - Validation: Strict type checking using typeof and Array.isArray()
   * - Constraints: Text/ID length limits, max task count enforced everywhere
   * - UTF16 Counting: JavaScript .length counts UTF16 code units, not characters
   *   Example: '🎯'.length === 2 (emoji uses 2 UTF16 units)
   *
   * API Constants:
   * - MAX_TEXT_LENGTH: 200 UTF16 units per task text property
   * - MAX_TASKS: 500 maximum tasks in array
   */

  const MAX_TEXT_LENGTH = 200;
  const MAX_TASKS = 500;

  /**
   * Validates a task object structure and constraints
   * @private
   * @param {object} task - Task object to validate
   * @param {string} taskId - Expected task ID (for mismatch detection)
   * @returns {boolean} True if valid
   * @throws {Error} If validation fails
   *
   * Type Checking Specifics:
   * - typeof null === 'object' (JavaScript quirk!), so we check !task first
   * - Array.isArray(task) prevents arrays passing the object check
   * - typeof task.id === 'string' ensures exact type (not truthy/falsy)
   * - task.id.trim() ensures id is non-empty after whitespace removal
   */
  function validateTask(task, taskId) {
    // Reject null, undefined, primitives, and arrays
    if (!task || typeof task !== 'object' || Array.isArray(task)) {
      throw new Error('Task must be an object');
    }

    // Check required id property
    if (typeof task.id !== 'string' || !task.id.trim()) {
      throw new Error('Task id must be a non-empty string');
    }
    if (task.id !== taskId) {
      throw new Error(`Task id mismatch: expected ${taskId}, got ${task.id}`);
    }
    // ID length limit: 100 characters
    if (task.id.length > 100) {
      throw new Error('Task id exceeds 100 character limit');
    }

    // Check required text property
    if (typeof task.text !== 'string' || !task.text.trim()) {
      throw new Error('Task text must be a non-empty string');
    }
    // Text length limit: 200 UTF16 units
    // UTF16 limit applies even if text contains emoji or multi-byte characters
    if (task.text.length > MAX_TEXT_LENGTH) {
      throw new Error(`Task text exceeds ${MAX_TEXT_LENGTH} UTF16 unit limit`);
    }

    // Completed must be EXACT boolean, not truthy (e.g., "true" string fails)
    // Truthiness check (if (task.completed)) would incorrectly accept "true" strings
    if (typeof task.completed !== 'boolean') {
      throw new Error('Task completed must be a boolean');
    }

    return true;
  }

  /**
   * Validates entire tasks array
   * @private
   * @param {array} tasks - Tasks array to validate
   * @throws {Error} If array invalid or constraints violated
   *
   * Enforces:
   * - Must be Array (not object with length property)
   * - Cannot exceed MAX_TASKS
   * - All task objects must be valid
   * - No duplicate IDs (Set for O(n) uniqueness check)
   *
   * Set Uniqueness:
   * Sets store unique values using ===. A new Set() has no duplicates by design.
   * ids.has(task.id) is O(1) lookup vs array.some() O(n), more efficient.
   */
  function validateTasks(tasks) {
    // Must be array: Array.isArray rejects objects with .length property
    if (!Array.isArray(tasks)) {
      throw new Error('Tasks must be an array');
    }

    // Enforce capacity constraint
    if (tasks.length > MAX_TASKS) {
      throw new Error(`Tasks array exceeds ${MAX_TASKS} task limit`);
    }

    // Check for duplicate IDs using Set (immutable operation)
    // Set automatically maintains uniqueness; adding existing ID has no effect
    const ids = new Set();
    for (const task of tasks) {
      validateTask(task, task?.id);
      if (ids.has(task.id)) {
        throw new Error(`Duplicate task id: ${task.id}`);
      }
      ids.add(task.id);
    }
  }

  /**
   * Adds a new task to the tasks array (immutable)
   * @param {array} tasks - Current tasks array
   * @param {string} text - Task text (will be trimmed)
   * @param {string} id - Unique task identifier (will be trimmed)
   * @returns {object} Object with {tasks: newArray, task: newTaskObject}
   * @throws {Error} If text/id invalid or capacity exceeded
   *
   * Immutability Pattern:
   * - Input `tasks` array is never modified
   * - Returns NEW array using spread syntax: [...tasks, newTask]
   * - Spread operator (...) creates shallow copy, immutable for task operations
   *
   * Constraint Checks:
   * - Text/ID trimmed, then validated
   * - UTF16 length enforced (not character count)
   * - Duplicate ID detection
   * - Capacity limit enforced
   */
  function addTask(tasks, text, id) {
    // Validate incoming array
    validateTasks(tasks);

    // Validate inputs: typeof checks for exact type
    if (typeof text !== 'string' || !text.trim()) {
      throw new Error('Task text must be a non-empty string');
    }
    if (typeof id !== 'string' || !id.trim()) {
      throw new Error('Task id must be a non-empty string');
    }

    // Trim whitespace (spaces, tabs, newlines, etc.)
    // trim() uses UTF16 definitions; some unicode whitespace may not be trimmed
    const trimmedText = text.trim();
    const trimmedId = id.trim();

    // Validate trimmed values against limits
    if (trimmedText.length > MAX_TEXT_LENGTH) {
      throw new Error(`Task text exceeds ${MAX_TEXT_LENGTH} UTF16 unit limit`);
    }
    if (trimmedId.length > 100) {
      throw new Error('Task id exceeds 100 character limit');
    }

    // Check for duplicate ID before adding
    // some() returns true if ANY task matches condition, false otherwise
    if (tasks.some(t => t.id === trimmedId)) {
      throw new Error(`Task id already exists: ${trimmedId}`);
    }

    // Enforce capacity before adding
    if (tasks.length >= MAX_TASKS) {
      throw new Error(`Cannot add task: array at maximum capacity (${MAX_TASKS})`);
    }

    // Create new task object (always starts with completed: false)
    const newTask = { id: trimmedId, text: trimmedText, completed: false };

    // Return object containing:
    // - tasks: NEW array with new task appended (spread creates new array)
    // - task: reference to the newly created task object
    return {
      tasks: [...tasks, newTask],
      task: newTask
    };
  }

  /**
   * Toggles the completed status of a task (immutable)
   * @param {array} tasks - Current tasks array
   * @param {string} id - ID of task to toggle
   * @returns {array} New tasks array with toggled task, or unchanged if id not found
   *
   * Immutability & findIndex:
   * - findIndex returns -1 if no match (not undefined, not null, exactly -1)
   * - Truthiness check (if (foundIndex)) would incorrectly treat index 0 as false!
   * - Correct: if (foundIndex === -1)
   *
   * No-op for Unknown ID:
   * When ID not found, returns new array [...tasks] not the original tasks
   * This maintains consistency: every operation returns new array
   */
  function toggleTask(tasks, id) {
    // Validate incoming array
    validateTasks(tasks);

    // findIndex returns -1 if no match (not undefined)
    // index 0 is truthy, so must use === -1, not if (!foundIndex)
    const foundIndex = tasks.findIndex(t => t.id === id);
    if (foundIndex === -1) {
      // Unknown ID: still return new array, not original
      // Maintains contract that all operations return new arrays
      return [...tasks];
    }

    // map() creates new array with transformed elements
    // spread operator {...task} creates shallow copy of task object
    // Only the task at foundIndex is modified (completed negated)
    const newTasks = tasks.map((task, index) => {
      if (index === foundIndex) {
        return { ...task, completed: !task.completed };
      }
      return task;
    });

    return newTasks;
  }

  /**
   * Deletes a task from the tasks array (immutable)
   * @param {array} tasks - Current tasks array
   * @param {string} id - ID of task to delete
   * @returns {array} New tasks array without the deleted task, or unchanged if id not found
   *
   * Immutability & filter:
   * - filter() creates new array with elements passing test
   * - Predicate t => t.id !== id includes all tasks EXCEPT the target
   *
   * No-op for Unknown ID:
   * When ID not found, returns [...tasks] (new array, same content)
   */
  function deleteTask(tasks, id) {
    // Validate incoming array
    validateTasks(tasks);

    // Check if task exists before filtering (for clarity)
    const hasTask = tasks.some(t => t.id === id);
    if (!hasTask) {
      // Unknown ID: return new array, not original
      return [...tasks];
    }

    // filter() creates new array excluding task where id matches
    // Every element not matching the predicate is kept
    return tasks.filter(t => t.id !== id);
  }

  /**
   * Clears all completed tasks (immutable)
   * @param {array} tasks - Current tasks array
   * @returns {array} New tasks array with completed tasks removed
   *
   * Immutability & filter:
   * - !t.completed keeps only tasks where completed is false
   * - Returns new array even if nothing was removed
   */
  function clearCompleted(tasks) {
    // Validate incoming array
    validateTasks(tasks);

    // filter() creates new array keeping only tasks where completed is false
    // If no tasks completed, returns new array with all tasks
    return tasks.filter(t => !t.completed);
  }

  /**
   * Filters tasks by status
   * @param {array} tasks - Current tasks array
   * @param {string} filter - Filter mode: 'all', 'active', 'completed'
   * @returns {array} Filtered tasks array
   * @throws {Error} If filter value invalid
   *
   * Allowlist Pattern:
   * Valid filters are explicitly listed in allowlist array
   * includes() checks if value is in allowlist, rejects unknown values
   * This prevents logic errors from typos or unexpected values
   */
  function filterTasks(tasks, filter = 'all') {
    // Validate incoming array
    validateTasks(tasks);

    // Allowlist pattern: only allow specific known values
    // includes() returns true if array contains value (===)
    if (!['all', 'active', 'completed'].includes(filter)) {
      throw new Error(`Invalid filter: ${filter}. Must be 'all', 'active', or 'completed'`);
    }

    // Use switch for explicit handling of each valid state
    switch (filter) {
      case 'active':
        // Keep tasks where completed is false (using !t.completed)
        return tasks.filter(t => !t.completed);
      case 'completed':
        // Keep tasks where completed is true
        return tasks.filter(t => t.completed);
      default:
        // 'all': return new array with all tasks (immutability maintained)
        return [...tasks];
    }
  }

  /**
   * Counts the number of active (incomplete) tasks
   * @param {array} tasks - Current tasks array
   * @returns {number} Count of active tasks
   *
   * Active means completed === false (exact boolean check)
   */
  function countActive(tasks) {
    // Validate incoming array
    validateTasks(tasks);

    // filter() returns array of active tasks, .length gives count
    // !t.completed only matches exact false boolean, not falsy values
    return tasks.filter(t => !t.completed).length;
  }

  /**
   * Serializes tasks array to JSON string with version metadata
   * @param {array} tasks - Tasks array to serialize
   * @returns {string} JSON string with {version:1, tasks: validatedArray}
   * @throws {Error} If tasks validation fails
   *
   * Version Strategy:
   * Envelope includes version number for future schema evolution
   * Version 1 = current format with id, text, completed properties
   * A future schema needs a new version and explicit parser support; this
   * implementation accepts only version 1, not future versions.
   *
   * JSON.stringify:
   * Converts a JavaScript object to JSON text (not HTML-safe markup)
   * Handles escaping of special characters automatically
   */
  function serializeTasks(tasks) {
    // Validate array first (will throw if invalid)
    validateTasks(tasks);

    // Return JSON string with version envelope
    // JSON.stringify automatically escapes quotes, newlines, etc.
    // Version field lets a parser identify the schema; compatibility is not automatic.
    return JSON.stringify({ version: 1, tasks });
  }

  /**
   * Parses and validates a serialized tasks JSON string
   * @param {string|null} raw - Raw JSON string to parse
   * @returns {array} Parsed and validated tasks array
   * @throws {Error} If JSON malformed, version unsupported, or schema invalid
   *
   * Parse & Validate Strategy:
   * 1. null/undefined → empty array (no-op for missing storage)
   * 2. JSON.parse() → throws if malformed
   * 3. Schema validation → check structure (version, tasks array)
   * 4. Normalize → extract only expected properties (not HTML sanitization)
   * 5. Final validation → full constraint check
   *
   * Normalization:
   * Extracts ONLY {id, text, completed} from parsed objects
   * Ignores unknown properties (allowlist approach)
   * Trims id and text again (defensive programming)
   *
   * Truthiness vs Exact Boolean:
   * parsed.version !== 1 rejects any non-1 version
   * typeof completed !== 'boolean' rejects truthy values like "true"
   */
  function parseTasks(raw) {
    // Null/undefined returns empty array (no-op)
    // Uses == null (loose equality) which matches both null and undefined
    if (raw == null) {
      return [];
    }

    // Parse JSON string to JavaScript object
    // Throws SyntaxError if malformed
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      throw new Error(`Malformed JSON in saved tasks: ${err.message}`);
    }

    // Validate structure: must be object (typeof === 'object' and not null)
    // null is typeof 'object' (quirk!), so check !parsed first
    if (!parsed || typeof parsed !== 'object') {
      throw new Error('Parsed tasks must be an object');
    }

    // Validate version: must be EXACT number 1 (not 1.0, not "1", not 1n)
    // typeof parsed.version !== 'number' ensures exact type
    if (typeof parsed.version !== 'number' || parsed.version !== 1) {
      throw new Error(`Unsupported tasks version: ${parsed.version}. Expected version 1`);
    }

    // Validate tasks property exists and is array
    if (!Array.isArray(parsed.tasks)) {
      throw new Error('Parsed tasks.tasks must be an array');
    }

    // Normalize tasks array: extract and validate each item
    // map() creates new array with normalized/validated objects
    const tasks = parsed.tasks.map((item, index) => {
      // Each item must be object (not null, not array, not primitive)
      if (!item || typeof item !== 'object') {
        throw new Error(`Task at index ${index} must be an object`);
      }

      // Extract only id, text, completed properties (allowlist)
      // Ignores any extra properties in JSON (defensive)
      const { id, text, completed } = item;

      // Validate id: must be non-empty string
      if (typeof id !== 'string' || !id.trim()) {
        throw new Error(`Task at index ${index}: id must be non-empty string`);
      }
      // ID length limit: 100 characters
      if (id.length > 100) {
        throw new Error(`Task at index ${index}: id exceeds 100 character limit`);
      }

      // Validate text: must be non-empty string
      if (typeof text !== 'string' || !text.trim()) {
        throw new Error(`Task at index ${index}: text must be non-empty string`);
      }
      // Text length limit: 200 UTF16 units
      if (text.length > MAX_TEXT_LENGTH) {
        throw new Error(`Task at index ${index}: text exceeds ${MAX_TEXT_LENGTH} UTF16 unit limit`);
      }

      // Validate completed: must be EXACT boolean
      // typeof check rejects truthy strings like "true" or "false"
      if (typeof completed !== 'boolean') {
        throw new Error(`Task at index ${index}: completed must be boolean, got ${typeof completed}`);
      }

      // Return normalized object with trimmed id and text
      return { id: id.trim(), text: text.trim(), completed };
    });

    // Final validation: check duplicates and constraints on normalized array
    validateTasks(tasks);

    return tasks;
  }

  /**
   * PocketTasks module export
   * Provides immutable task management API
   *
   * API Shape:
   * {
   *   MAX_TEXT_LENGTH: number,
   *   MAX_TASKS: number,
   *   addTask: function,
   *   toggleTask: function,
   *   deleteTask: function,
   *   clearCompleted: function,
   *   filterTasks: function,
   *   countActive: function,
   *   serializeTasks: function,
   *   parseTasks: function
   * }
   */
  const PocketTasks = {
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
  };

  // Export for Node.js/CommonJS environments
  // typeof module !== 'undefined' checks if module object exists
  // module.exports is the CommonJS export mechanism
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = PocketTasks;
  }

  // Export to globalThis for browser environments
  // Browser code uses globalThis.PocketTasks to access the API
  // globalThis works in browsers (window), Node.js, and Web Workers
  if (typeof globalThis !== 'undefined') {
    globalThis.PocketTasks = PocketTasks;
  }

})();
