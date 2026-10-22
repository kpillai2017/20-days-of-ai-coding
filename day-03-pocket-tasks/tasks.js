// Keep helpers private; only PocketTasks is exported.
(() => {
  "use strict";
  /**
   * PocketTasks - A lightweight, immutable task management system
   * Exposes globalThis.PocketTasks with core task operations
   *
   * API Constants:
   * - MAX_TEXT_LENGTH: 200 UTF16 units per task
   * - MAX_TASKS: 500 maximum tasks in array
   */

  const MAX_TEXT_LENGTH = 200;
  const MAX_TASKS = 500;

  /**
   * Validates a task object structure and constraints
   * @private
   * @param {object} task - Task object to validate
   * @param {string} taskId - Expected task ID
   * @returns {boolean} True if valid
   * @throws {Error} If validation fails
   */
  function validateTask(task, taskId) {
    if (!task || typeof task !== 'object' || Array.isArray(task)) {
      throw new Error('Task must be an object');
    }

    // Check required properties
    if (typeof task.id !== 'string' || !task.id.trim()) {
      throw new Error('Task id must be a non-empty string');
    }
    if (task.id !== taskId) {
      throw new Error(`Task id mismatch: expected ${taskId}, got ${task.id}`);
    }
    if (task.id.length > 100) {
      throw new Error('Task id exceeds 100 character limit');
    }

    if (typeof task.text !== 'string' || !task.text.trim()) {
      throw new Error('Task text must be a non-empty string');
    }
    if (task.text.length > MAX_TEXT_LENGTH) {
      throw new Error(`Task text exceeds ${MAX_TEXT_LENGTH} UTF16 unit limit`);
    }

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
   */
  function validateTasks(tasks) {
    if (!Array.isArray(tasks)) {
      throw new Error('Tasks must be an array');
    }

    if (tasks.length > MAX_TASKS) {
      throw new Error(`Tasks array exceeds ${MAX_TASKS} task limit`);
    }

    // Check for duplicate IDs
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
   */
  function addTask(tasks, text, id) {
    validateTasks(tasks);
    // Validate inputs
    if (typeof text !== 'string' || !text.trim()) {
      throw new Error('Task text must be a non-empty string');
    }
    if (typeof id !== 'string' || !id.trim()) {
      throw new Error('Task id must be a non-empty string');
    }

    const trimmedText = text.trim();
    const trimmedId = id.trim();

    if (trimmedText.length > MAX_TEXT_LENGTH) {
      throw new Error(`Task text exceeds ${MAX_TEXT_LENGTH} UTF16 unit limit`);
    }
    if (trimmedId.length > 100) {
      throw new Error('Task id exceeds 100 character limit');
    }

    // Check for duplicate ID
    if (tasks.some(t => t.id === trimmedId)) {
      throw new Error(`Task id already exists: ${trimmedId}`);
    }

    // Check capacity
    if (tasks.length >= MAX_TASKS) {
      throw new Error(`Cannot add task: array at maximum capacity (${MAX_TASKS})`);
    }

    // Create new task
    const newTask = { id: trimmedId, text: trimmedText, completed: false };

    // Return new array and new task
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
   */
  function toggleTask(tasks, id) {
    validateTasks(tasks);
    const foundIndex = tasks.findIndex(t => t.id === id);
    if (foundIndex === -1) {
      // Return a new array even when the ID is absent.
      return [...tasks];
    }

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
   */
  function deleteTask(tasks, id) {
    validateTasks(tasks);
    const hasTask = tasks.some(t => t.id === id);
    if (!hasTask) {
      // Return a new array even when the ID is absent.
      return [...tasks];
    }

    return tasks.filter(t => t.id !== id);
  }

  /**
   * Clears all completed tasks (immutable)
   * @param {array} tasks - Current tasks array
   * @returns {array} New tasks array with completed tasks removed
   */
  function clearCompleted(tasks) {
    validateTasks(tasks);
    return tasks.filter(t => !t.completed);
  }

  /**
   * Filters tasks by status
   * @param {array} tasks - Current tasks array
   * @param {string} filter - Filter mode: 'all', 'active', 'completed'
   * @returns {array} Filtered tasks array
   * @throws {Error} If filter value invalid
   */
  function filterTasks(tasks, filter = 'all') {
    validateTasks(tasks);
    if (!['all', 'active', 'completed'].includes(filter)) {
      throw new Error(`Invalid filter: ${filter}. Must be 'all', 'active', or 'completed'`);
    }

    switch (filter) {
      case 'active':
        return tasks.filter(t => !t.completed);
      case 'completed':
        return tasks.filter(t => t.completed);
      default:
        return [...tasks];
    }
  }

  /**
   * Counts the number of active (incomplete) tasks
   * @param {array} tasks - Current tasks array
   * @returns {number} Count of active tasks
   */
  function countActive(tasks) {
    validateTasks(tasks);
    return tasks.filter(t => !t.completed).length;
  }

  /**
   * Serializes tasks array to JSON string with version metadata
   * @param {array} tasks - Tasks array to serialize
   * @returns {string} JSON string with {version:1, tasks: validatedArray}
   * @throws {Error} If tasks validation fails
   */
  function serializeTasks(tasks) {
    validateTasks(tasks);
    return JSON.stringify({ version: 1, tasks });
  }

  /**
   * Parses and validates a serialized tasks JSON string
   * @param {string|null} raw - Raw JSON string to parse
   * @returns {array} Parsed and validated tasks array
   * @throws {Error} If JSON malformed, version unsupported, or schema invalid
   */
  function parseTasks(raw) {
    // Null or undefined returns empty array
    if (raw == null) {
      return [];
    }

    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      throw new Error(`Malformed JSON in saved tasks: ${err.message}`);
    }

    // Validate structure
    if (!parsed || typeof parsed !== 'object') {
      throw new Error('Parsed tasks must be an object');
    }

    if (typeof parsed.version !== 'number' || parsed.version !== 1) {
      throw new Error(`Unsupported tasks version: ${parsed.version}. Expected version 1`);
    }

    if (!Array.isArray(parsed.tasks)) {
      throw new Error('Parsed tasks.tasks must be an array');
    }

    // Validate and normalize tasks array
    const tasks = parsed.tasks.map((item, index) => {
      if (!item || typeof item !== 'object') {
        throw new Error(`Task at index ${index} must be an object`);
      }

      // Extract only id, text, completed properties
      const { id, text, completed } = item;

      if (typeof id !== 'string' || !id.trim()) {
        throw new Error(`Task at index ${index}: id must be non-empty string`);
      }
      if (id.length > 100) {
        throw new Error(`Task at index ${index}: id exceeds 100 character limit`);
      }

      if (typeof text !== 'string' || !text.trim()) {
        throw new Error(`Task at index ${index}: text must be non-empty string`);
      }
      if (text.length > MAX_TEXT_LENGTH) {
        throw new Error(`Task at index ${index}: text exceeds ${MAX_TEXT_LENGTH} UTF16 unit limit`);
      }

      if (typeof completed !== 'boolean') {
        throw new Error(`Task at index ${index}: completed must be boolean, got ${typeof completed}`);
      }

      return { id: id.trim(), text: text.trim(), completed };
    });

    // Final validation including duplicate check
    validateTasks(tasks);

    return tasks;
  }

  /**
   * PocketTasks module export
   * Provides immutable task management API
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

  // Export for Node.js/CommonJS
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = PocketTasks;
  }

  // Export to globalThis for browser
  if (typeof globalThis !== 'undefined') {
    globalThis.PocketTasks = PocketTasks;
  }

})();
